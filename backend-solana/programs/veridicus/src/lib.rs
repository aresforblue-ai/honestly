use anchor_lang::prelude::*;
use anchor_spl::token::{self, Token, TokenAccount, Transfer, Burn};

mod airdrop;
mod state;
mod governance;
mod liquidity;

use airdrop::*;
use state::{VERIDICUSState, Staking, VERIDICUSError};
use governance::*;
use liquidity::*;

declare_id!("VERIDICUS1111111111111111111111111111111111111");

#[program]
pub mod VERIDICUS {
    use super::*;

    /// Initialize the VERIDICUS program
    pub fn initialize(ctx: Context<Initialize>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        state.authority = ctx.accounts.authority.key();
        state.pending_authority = None;
        state.authority_transfer_timestamp = None;
        state.total_supply = 1_000_000_000_000_000; // 1M VERIDICUS (1,000,000 * 10^9 decimals)
        state.total_burned = 0;
        state.total_jobs = 0;
        state.paused = false; // Start unpaused
        
        msg!("VERIDICUS program initialized");
        Ok(())
    }

    /// Initiate authority transfer with 7-day timelock
    /// This allows the current authority to propose a new authority (e.g., multisig DAO)
    /// The transfer can only be completed after 7 days, giving the community time to react
    pub fn transfer_authority(
        ctx: Context<TransferAuthority>,
        new_authority: Pubkey,
    ) -> Result<()> {
        let state = &mut ctx.accounts.state;
        
        // Check no pending transfer exists
        require!(
            state.pending_authority.is_none(),
            VERIDICUSError::AuthorityTransferPending
        );
        
        // Cannot transfer to same authority
        require!(
            new_authority != state.authority,
            VERIDICUSError::InvalidNewAuthority
        );
        
        // Cannot transfer to zero address
        require!(
            new_authority != Pubkey::default(),
            VERIDICUSError::InvalidNewAuthority
        );
        
        // Set pending authority and timestamp
        state.pending_authority = Some(new_authority);
        state.authority_transfer_timestamp = Some(Clock::get()?.unix_timestamp);
        
        emit!(AuthorityTransferInitiated {
            current_authority: state.authority,
            new_authority,
            timestamp: state.authority_transfer_timestamp.unwrap(),
        });
        
        msg!("Authority transfer initiated. New authority: {}. Timelock: 7 days", new_authority);
        Ok(())
    }

    /// Accept authority transfer (can only be called after timelock expires)
    /// The new authority must call this to complete the transfer
    pub fn accept_authority(ctx: Context<AcceptAuthority>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        
        // Check pending transfer exists
        let pending_authority = state.pending_authority.ok_or(VERIDICUSError::NoAuthorityTransferPending)?;
        let transfer_timestamp = state.authority_transfer_timestamp.ok_or(VERIDICUSError::NoAuthorityTransferPending)?;
        
        // Verify caller is the pending authority
        require!(
            ctx.accounts.new_authority.key() == pending_authority,
            VERIDICUSError::Unauthorized
        );
        
        // Check timelock has expired (7 days)
        let current_time = Clock::get()?.unix_timestamp;
        let elapsed = current_time.checked_sub(transfer_timestamp)
            .ok_or(VERIDICUSError::AuthorityTransferTimelockNotExpired)?;
        
        require!(
            elapsed >= VERIDICUSState::AUTHORITY_TRANSFER_DELAY,
            VERIDICUSError::AuthorityTransferTimelockNotExpired
        );
        
        // Transfer authority
        let old_authority = state.authority;
        state.authority = pending_authority;
        state.pending_authority = None;
        state.authority_transfer_timestamp = None;
        
        emit!(AuthorityTransferred {
            old_authority,
            new_authority: state.authority,
            timestamp: current_time,
        });
        
        msg!("Authority transferred from {} to {}", old_authority, state.authority);
        Ok(())
    }

    /// Cancel pending authority transfer (only current authority can cancel)
    pub fn cancel_authority_transfer(ctx: Context<CancelAuthorityTransfer>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        
        // Check pending transfer exists
        require!(
            state.pending_authority.is_some(),
            VERIDICUSError::NoAuthorityTransferPending
        );
        
        let cancelled_authority = state.pending_authority.unwrap();
        state.pending_authority = None;
        state.authority_transfer_timestamp = None;
        
        emit!(AuthorityTransferCancelled {
            cancelled_authority,
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        msg!("Authority transfer cancelled");
        Ok(())
    }

    /// Emergency pause mechanism
    pub fn pause(ctx: Context<Pause>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        state.paused = true;
        
        emit!(ProgramPaused {
            timestamp: Clock::get()?.unix_timestamp,
            paused_by: ctx.accounts.authority.key(),
        });
        
        msg!("Program paused by authority");
        Ok(())
    }

    /// Unpause program
    pub fn unpause(ctx: Context<Unpause>) -> Result<()> {
        let state = &mut ctx.accounts.state;
        state.paused = false;
        
        emit!(ProgramUnpaused {
            timestamp: Clock::get()?.unix_timestamp,
            unpaused_by: ctx.accounts.authority.key(),
        });
        
        msg!("Program unpaused by authority");
        Ok(())
    }

    /// Execute a quantum job and burn tokens
    pub fn execute_quantum_job(
        ctx: Context<ExecuteJob>,
        qubits: u8,
        job_type: u8,
    ) -> Result<()> {
        let state = &mut ctx.accounts.state;
        
        // Check if program is paused
        require!(!state.paused, VERIDICUSError::ProgramPaused);
        
        // Calculate burn amount (1 VDC base + variable by qubits)
        let base_burn = 1_000_000_000; // 1 VDC (9 decimals)
        let qubit_burn = match qubits {
            5 => 1_000_000_000,   // +1 VDC
            10 => 2_000_000_000, // +2 VDC
            20 => 5_000_000_000, // +5 VDC
            _ => 0,
        };
        
        let complexity_multiplier = match job_type {
            0 => 1,  // CircuitOptimize
            1 => 2,  // ZkmlProof
            2 => 3,  // AnomalyDetect
            3 => 5,  // SecurityAudit
            _ => 1,
        };
        
        let total_burn = (base_burn + qubit_burn) * complexity_multiplier;
        
        // Burn tokens
        let cpi_accounts = Burn {
            mint: ctx.accounts.mint.to_account_info(),
            from: ctx.accounts.user_token_account.to_account_info(),
            authority: ctx.accounts.user.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::burn(cpi_ctx, total_burn)?;
        
        // Update state
        state.total_burned = state.total_burned.checked_add(total_burn).unwrap();
        state.total_jobs = state.total_jobs.checked_add(1).unwrap();
        
        emit!(JobExecuted {
            user: ctx.accounts.user.key(),
            burn_amount: total_burn,
            qubits,
            job_type,
            timestamp: Clock::get()?.unix_timestamp,
        });
        
        msg!("Quantum job executed: {} VERIDICUS burned", total_burn);
        Ok(())
    }

    /// Stake VERIDICUS for fee discounts and governance
    pub fn stake_VERIDICUS(
        ctx: Context<StakeVERIDICUS>,
        amount: u64,
    ) -> Result<()> {
        // Transfer tokens to staking account
        let cpi_accounts = Transfer {
            from: ctx.accounts.user_token_account.to_account_info(),
            to: ctx.accounts.staking_account.to_account_info(),
            authority: ctx.accounts.user.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new(cpi_program, cpi_accounts);
        token::transfer(cpi_ctx, amount)?;
        
        // Update staking record
        let staking = &mut ctx.accounts.staking;
        staking.user = ctx.accounts.user.key();
        staking.amount = staking.amount.checked_add(amount).unwrap();
        staking.timestamp = Clock::get()?.unix_timestamp;
        
        emit!(VERIDICUSStaked {
            user: ctx.accounts.user.key(),
            amount,
            total_staked: staking.amount,
        });
        
        msg!("Staked {} VERIDICUS", amount);
        Ok(())
    }

    /// Unstake VERIDICUS
    pub fn unstake_VERIDICUS(
        ctx: Context<UnstakeVERIDICUS>,
        amount: u64,
    ) -> Result<()> {
        let staking = &mut ctx.accounts.staking;
        
        require!(
            staking.amount >= amount,
            VERIDICUSError::InsufficientStake
        );
        
        // Transfer tokens back
        let seeds = &[
            b"staking",
            ctx.accounts.user.key().as_ref(),
            &[ctx.bumps.staking_account],
        ];
        let signer = &[&seeds[..]];
        
        let cpi_accounts = Transfer {
            from: ctx.accounts.staking_account.to_account_info(),
            to: ctx.accounts.user_token_account.to_account_info(),
            authority: ctx.accounts.staking_account.to_account_info(),
        };
        let cpi_program = ctx.accounts.token_program.to_account_info();
        let cpi_ctx = CpiContext::new_with_signer(cpi_program, cpi_accounts, signer);
        token::transfer(cpi_ctx, amount)?;
        
        staking.amount = staking.amount.checked_sub(amount).unwrap();
        
        emit!(VERIDICUSUnstaked {
            user: ctx.accounts.user.key(),
            amount,
            remaining_staked: staking.amount,
        });
        
        msg!("Unstaked {} VERIDICUS", amount);
        Ok(())
    }

    /// Calculate fee discount based on staked amount
    pub fn get_fee_discount(ctx: Context<GetFeeDiscount>) -> Result<u8> {
        let staking = &ctx.accounts.staking;
        
        let discount = if staking.amount >= 20_000_000_000_000 {
            60  // 60% discount for 20K+ VDC
        } else if staking.amount >= 5_000_000_000_000 {
            40  // 40% discount for 5K+ VDC
        } else if staking.amount >= 1_000_000_000_000 {
            20  // 20% discount for 1K+ VDC
        } else {
            0
        };
        
        Ok(discount)
    }
}

#[derive(Accounts)]
pub struct Initialize<'info> {
    #[account(
        init,
        payer = authority,
        space = 8 + VERIDICUSState::LEN,
        seeds = [b"VERIDICUS_state"],
        bump
    )]
    pub state: Account<'info, VERIDICUSState>,
    
    #[account(mut)]
    pub authority: Signer<'info>,
    
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct Pause<'info> {
    #[account(
        mut,
        seeds = [b"VERIDICUS_state"],
        bump,
        has_one = authority @ VERIDICUSError::Unauthorized
    )]
    pub state: Account<'info, VERIDICUSState>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct Unpause<'info> {
    #[account(
        mut,
        seeds = [b"VERIDICUS_state"],
        bump,
        has_one = authority @ VERIDICUSError::Unauthorized
    )]
    pub state: Account<'info, VERIDICUSState>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct ExecuteJob<'info> {
    #[account(mut, seeds = [b"VERIDICUS_state"], bump)]
    pub state: Account<'info, VERIDICUSState>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(mut)]
    pub mint: Account<'info, anchor_spl::token::Mint>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct StakeVERIDICUS<'info> {
    #[account(
        init_if_needed,
        payer = user,
        space = 8 + Staking::LEN,
        seeds = [b"staking", user.key().as_ref()],
        bump
    )]
    pub staking: Account<'info, Staking>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(
        mut,
        seeds = [b"staking", user.key().as_ref()],
        bump
    )]
    pub staking_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
    pub system_program: Program<'info, System>,
}

#[derive(Accounts)]
pub struct UnstakeVERIDICUS<'info> {
    #[account(mut, seeds = [b"staking", user.key().as_ref()], bump)]
    pub staking: Account<'info, Staking>,
    
    #[account(mut)]
    pub user: Signer<'info>,
    
    #[account(mut)]
    pub user_token_account: Account<'info, TokenAccount>,
    
    #[account(
        mut,
        seeds = [b"staking", user.key().as_ref()],
        bump
    )]
    pub staking_account: Account<'info, TokenAccount>,
    
    pub token_program: Program<'info, Token>,
}

#[derive(Accounts)]
pub struct GetFeeDiscount<'info> {
    #[account(seeds = [b"staking", user.key().as_ref()], bump)]
    pub staking: Account<'info, Staking>,
    
    /// CHECK: Just for lookup
    pub user: AccountInfo<'info>,
}

#[derive(Accounts)]
pub struct TransferAuthority<'info> {
    #[account(
        mut,
        seeds = [b"VERIDICUS_state"],
        bump,
        has_one = authority @ VERIDICUSError::Unauthorized
    )]
    pub state: Account<'info, VERIDICUSState>,
    
    pub authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct AcceptAuthority<'info> {
    #[account(
        mut,
        seeds = [b"VERIDICUS_state"],
        bump
    )]
    pub state: Account<'info, VERIDICUSState>,
    
    /// CHECK: Must be the pending authority
    pub new_authority: Signer<'info>,
}

#[derive(Accounts)]
pub struct CancelAuthorityTransfer<'info> {
    #[account(
        mut,
        seeds = [b"VERIDICUS_state"],
        bump,
        has_one = authority @ VERIDICUSError::Unauthorized
    )]
    pub state: Account<'info, VERIDICUSState>,
    
    pub authority: Signer<'info>,
}

// VERIDICUSState and Staking moved to state.rs - remove duplicate definitions

#[event]
pub struct JobExecuted {
    pub user: Pubkey,
    pub burn_amount: u64,
    pub qubits: u8,
    pub job_type: u8,
    pub timestamp: i64,
}

#[event]
pub struct VERIDICUSStaked {
    pub user: Pubkey,
    pub amount: u64,
    pub total_staked: u64,
}

#[event]
pub struct VERIDICUSUnstaked {
    pub user: Pubkey,
    pub amount: u64,
    pub remaining_staked: u64,
}

// Errors moved to state.rs

#[event]
pub struct ProgramPaused {
    pub timestamp: i64,
    pub paused_by: Pubkey,
}

#[event]
pub struct ProgramUnpaused {
    pub timestamp: i64,
    pub unpaused_by: Pubkey,
}

#[event]
pub struct AuthorityTransferInitiated {
    pub current_authority: Pubkey,
    pub new_authority: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct AuthorityTransferred {
    pub old_authority: Pubkey,
    pub new_authority: Pubkey,
    pub timestamp: i64,
}

#[event]
pub struct AuthorityTransferCancelled {
    pub cancelled_authority: Pubkey,
    pub timestamp: i64,
}

