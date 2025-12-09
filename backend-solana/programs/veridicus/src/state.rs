use anchor_lang::prelude::*;

#[account]
pub struct VERIDICUSState {
    pub authority: Pubkey,
    pub pending_authority: Option<Pubkey>, // Pending authority transfer (for timelock)
    pub authority_transfer_timestamp: Option<i64>, // When authority transfer was initiated
    pub total_supply: u64,
    pub total_burned: u64,
    pub total_jobs: u64,
    pub paused: bool, // Emergency pause flag
}

impl VERIDICUSState {
    // authority (32) + pending_authority Option<Pubkey> (1 + 32) + authority_transfer_timestamp Option<i64> (1 + 8) + 3 u64s (24) + paused bool (1)
    pub const LEN: usize = 32 + (1 + 32) + (1 + 8) + 8 + 8 + 8 + 1;
    
    // 7 days in seconds (7 * 24 * 60 * 60)
    pub const AUTHORITY_TRANSFER_DELAY: i64 = 604800;
}

#[account]
pub struct Staking {
    pub user: Pubkey,
    pub amount: u64,
    pub timestamp: i64,
}

impl Staking {
    pub const LEN: usize = 32 + 8 + 8; // user + amount + timestamp
}

#[error_code]
pub enum VERIDICUSError {
    #[msg("Insufficient stake")]
    InsufficientStake,
    #[msg("Invalid Merkle proof")]
    InvalidProof,
    #[msg("Already claimed")]
    AlreadyClaimed,
    #[msg("Milestone not reached")]
    MilestoneNotReached,
    #[msg("Invalid milestone")]
    InvalidMilestone,
    #[msg("Already unlocked")]
    AlreadyUnlocked,
    #[msg("Proposal not active")]
    ProposalNotActive,
    #[msg("No votes cast")]
    NoVotes,
    #[msg("Invalid proposal type")]
    InvalidProposalType,
    #[msg("Invalid unlock time")]
    InvalidUnlockTime,
    #[msg("Lock period too short")]
    LockPeriodTooShort,
    #[msg("Liquidity still locked")]
    LiquidityStillLocked,
    #[msg("Liquidity not locked")]
    LiquidityNotLocked,
    #[msg("Program paused")]
    ProgramPaused,
    #[msg("Rate limit exceeded")]
    RateLimitExceeded,
    #[msg("Unauthorized")]
    Unauthorized,
    #[msg("Authority transfer already pending")]
    AuthorityTransferPending,
    #[msg("Authority transfer not pending")]
    NoAuthorityTransferPending,
    #[msg("Authority transfer timelock not expired")]
    AuthorityTransferTimelockNotExpired,
    #[msg("Invalid new authority")]
    InvalidNewAuthority,
}

