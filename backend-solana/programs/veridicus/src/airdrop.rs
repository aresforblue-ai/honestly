use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer};

use crate::state::{VERIDICUSState, VERIDICUSError};

/// Claim airdrop via Merkle proof
pub fn claim_airdrop(
    ctx: Context<ClaimAirdrop>,
    proof: Vec<[u8; 32]>,
    amount: u64,
    leaf: [u8; 32],
) -> Result<()> {
    let airdrop = &mut ctx.accounts.airdrop;
    
    // Verify Merkle proof
    require!(
        verify_merkle_proof(&proof, &leaf, &airdrop.merkle_root),
        VERIDICUSError::InvalidProof
    );
    
    // Check if already claimed (using separate PDA per claim)
    // This prevents unbounded growth - each claim has its own account
    // With init_if_needed, if account exists and claimed=true, reject
    // If account is new (claimed=false by default), allow claim
    if ctx.accounts.claim_record.claimed {
        return Err(VERIDICUSError::AlreadyClaimed.into());
    }
    
    // Calculate immediate unlock (50% at launch)
    let immediate = amount / 2;
    let vested = amount - immediate;
    
    // Transfer immediate portion
    let cpi_accounts = Transfer {
        from: ctx.accounts.airdrop_vault.to_account_info(),
        to: ctx.accounts.user_token_account.to_account_info(),
        authority: ctx.accounts.airdrop_vault.to_account_info(),
    };
    let cpi_program = ctx.accounts.token_program.to_account_info();
    let seeds = &[
        b"airdrop_vault",
        &[ctx.bumps.airdrop_vault],
    ];
    let signer = &[&seeds[..]];
    let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
    token::transfer(cpi_ctx, immediate)?;
    
    // Create vesting schedule for remaining 50%
    let vesting = &mut ctx.accounts.vesting;
    vesting.user = ctx.accounts.user.key();
    vesting.total_amount = vested;
    vesting.unlocked = 0;
    vesting.vesting_period = 6 * 30 * 24 * 60 * 60; // 6 months in seconds
    vesting.start_timestamp = Clock::get()?.unix_timestamp;
    
    // Mark as claimed (using separate PDA)
    ctx.accounts.claim_record.claimed = true;
    ctx.accounts.claim_record.leaf = leaf;
    ctx.accounts.claim_record.claimed_at = Clock::get()?.unix_timestamp;
    
    emit!(AirdropClaimed {
        user: ctx.accounts.user.key(),
        immediate,
        vested,
    });
    
    msg!("Airdrop claimed: {} immediate, {} vested", immediate, vested);
    Ok(())
}

/// Unlock vested tokens based on milestones
pub fn unlock_vested(
    ctx: Context<UnlockVested>,
    milestone: u8,
) -> Result<()> {
    let vesting = &mut ctx.accounts.vesting;
    let state = &ctx.accounts.state;
    
    // Check milestone requirements
    let required_jobs = match milestone {
        0 => 1_000,   // 1K jobs
        1 => 5_000,   // 5K jobs
        2 => 10_000,  // 10K jobs
        3 => 20_000,  // 20K jobs
        _ => return Err(VERIDICUSError::InvalidMilestone.into()),
    };
    
    require!(
        state.total_jobs >= required_jobs,
        VERIDICUSError::MilestoneNotReached
    );
    
    // Calculate unlock percentage
    let unlock_percentage = match milestone {
        0 => 10,  // 10%
        1 => 20,  // 20%
        2 => 30,  // 30%
        3 => 40,  // 40%
        _ => 0,
    };
    
    let unlock_amount = (vesting.total_amount * unlock_percentage as u64) / 100;
    
    require!(
        vesting.unlocked < unlock_amount,
        VERIDICUSError::AlreadyUnlocked
    );
    
    // Transfer unlocked tokens
    let cpi_accounts = Transfer {
        from: ctx.accounts.vesting_vault.to_account_info(),
        to: ctx.accounts.user_token_account.to_account_info(),
        authority: ctx.accounts.vesting_vault.to_account_info(),
    };
    let cpi_program = ctx.accounts.token_program.to_account_info();
    let seeds = &[
        b"vesting_vault",
        &[ctx.bumps.vesting_vault],
    ];
    let signer = &[&seeds[..]];
    let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
    token::transfer(cpi_ctx, unlock_amount)?;
    
    vesting.unlocked = unlock_amount;
    
    emit!(VestedUnlocked {
        user: ctx.accounts.user.key(),
        milestone,
        amount: unlock_amount,
    });
    
    msg!("Unlocked {} VERIDICUS at milestone {}", unlock_amount, milestone);
    Ok(())
}

fn verify_merkle_proof(proof: &[[u8; 32]], leaf: &[u8; 32], root: &[u8; 32]) -> bool {
    use anchor_lang::solana_program::keccak;
    
    let mut computed_hash = *leaf;
    
    for proof_element in proof.iter() {
        if computed_hash < *proof_element {
            computed_hash = keccak::hashv(&[&computed_hash, proof_element]).to_bytes();
        } else {
            computed_hash = keccak::hashv(&[proof_element, &computed_hash]).to_bytes();
        }
    }
    
    computed_hash == *root
}

#[derive(Accounts)]
#[instruction(leaf: [u8; 32])]
pub struct ClaimAirdrop<'info> {
    #[account(mut, seeds = [b"airdrop"], bump)]
    pub airdrop: Account<'info, AirdropState>,
    
    /// Separate PDA per claim - prevents unbounded growth
    /// Each claim gets its own account, so we never hit account size limits
    #[account(
        init_if_needed,
        payer = user,
        space = 8 + ClaimRecord::LEN,
        seeds = [b"claim", leaf.as_ref()],
        bump
    )]
    pub claim_record: Account<'info, ClaimRecord>,
    
    #[account(
        init_if_needed,
        payer = user,
        space = 8 + Vesting::LEN,
        seeds = [b"vesting", user.key().as_ref()],
        bump
    )]
    pub vesting: Account<'info, Vesting>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(
        mut,
        seeds = [b"airdrop_vault"],
        bump
    )]
    pub airdrop_vault: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UnlockVested<'info> {
    #[account(mut, seeds = [b"vesting", user.key().as_ref()], bump)]
    pub vesting: Account<'info, Vesting>,
    
    #[account(seeds = [b"VERIDICUS_state"], bump)]
    pub state: Account<'info, VERIDICUSState>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(
        mut,
        seeds = [b"vesting_vault"],
        bump
    )]
    pub vesting_vault: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
}

#[account]
pub struct AirdropState {
    pub merkle_root: [u8; 32],
    // Removed: pub claimed: Vec<[u8; 32]> - This was unbounded and would break after ~312K claims
    // Solution: Use separate ClaimRecord PDA per claim (see ClaimRecord struct below)
}

impl AirdropState {
    pub const LEN: usize = 8 + 32; // discriminator + merkle_root
}

/// Separate account per claim - prevents unbounded growth
/// Each claim is tracked in its own PDA, so we never hit Solana's 10MB account limit
#[account]
pub struct ClaimRecord {
    pub claimed: bool,
    pub leaf: [u8; 32], // Merkle leaf hash
    pub claimed_at: i64, // Timestamp when claimed
}

impl ClaimRecord {
    pub const LEN: usize = 1 + 32 + 8; // claimed bool + leaf + timestamp
}

#[account]
pub struct Vesting {
    pub user: Pubkey,
    pub total_amount: u64,
    pub unlocked: u64,
    pub vesting_period: i64,
    pub start_timestamp: i64,
}

impl Vesting {
    pub const LEN: usize = 32 + 8 + 8 + 8 + 8; // user + 4 fields
}

#[event]
pub struct AirdropClaimed {
    pub user: Pubkey,
    pub immediate: u64,
    pub vested: u64,
}

#[event]
pub struct VestedUnlocked {
    pub user: Pubkey,
    pub milestone: u8,
    pub amount: u64,
}

// Errors moved to state.rs

