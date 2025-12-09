# Phase 4 Token Economics - Current vs Options

## 🎯 Current Design: **LINK-Only Staking**

**We're hosting stakes for everyone using LINK** - no native token minting.

### Current Model
- **Staking Token**: LINK (Chainlink token)
- **Rewards**: Paid in LINK from slash pool
- **Slashing**: LINK burned/slashed
- **No Native Token**: We don't mint anything

### Pros of LINK-Only
✅ **Liquidity**: LINK is already liquid, no new token needed  
✅ **Trust**: Established token, people trust it  
✅ **Integration**: Works with Chainlink oracles natively  
✅ **Karak Restaking**: LINK can be restaked for yield  
✅ **No Token Launch**: No regulatory/legal complexity  

### Cons of LINK-Only
❌ **No Protocol Value Capture**: We don't benefit from token appreciation  
❌ **Dependency**: Tied to LINK price volatility  
❌ **No Governance**: Can't use token for voting/DAO  
❌ **Limited Incentives**: Can't airdrop or reward early users with protocol tokens  

---

## 💡 Option: Add Native Token (VERITAS Token)

We could add a native `VERITAS` token for protocol value capture while keeping LINK for staking.

### Hybrid Model (Recommended)

```
┌─────────────────────────────────────────────────┐
│         DUAL TOKEN MODEL                        │
├─────────────────────────────────────────────────┤
│                                                 │
│  LINK (Staking)                                 │
│  ├─ Staking deposits (100-2000 LINK)            │
│  ├─ Slashing (30-50% of stake)                  │
│  ├─ Rewards (10% from slash pool)               │
│  └─ Dispute bonds (5% of stake at risk)         │
│                                                 │
│  VERITAS (Protocol Token)                        │
│  ├─ Governance (voting on parameters)             │
│  ├─ Fee discounts (lower staking requirements)    │
│  ├─ Protocol revenue share (from slash pool)      │
│  ├─ Early adopter rewards (airdrops)             │
│  └─ Oracle node rewards (bonus for validators)   │
│                                                 │
└─────────────────────────────────────────────────┘
```

### Implementation Options

#### Option A: Governance Token Only
- **VERITAS** token for voting on:
  - Staking thresholds
  - Slash percentages
  - Oracle quorum size
  - New chain additions
- **No staking in HONESTLY** - still use LINK

#### Option B: Fee Token
- **HONESTLY** used for:
  - Protocol fees (discounts for HONESTLY holders)
  - Revenue sharing (X% of slash pool to HONESTLY stakers)
  - Early adopter rewards
- **LINK still required** for anomaly reporting stakes

#### Option C: Full Dual Token
- **LINK**: Staking, slashing, rewards (as now)
- **HONESTLY**: Governance + revenue share + fee discounts
- **Hybrid staking**: Can stake LINK + HONESTLY for tier bonuses

---

## 🚀 Recommendation: **Start LINK-Only, Add HONESTLY Later**

### Phase 4.0 (Now): LINK-Only
- Keep current design
- Focus on getting system working
- Build user base
- Prove the model

### Phase 4.5 (Later): Add VERITAS Governance Token
- Launch VERITAS token
- Use for governance only (no staking)
- Airdrop to early reporters
- Revenue share from protocol fees

### Phase 5.0 (Future): Full Dual Token
- VERITAS staking for protocol benefits
- LINK still required for anomaly reporting
- Revenue sharing model

---

## 💰 If We Add VERITAS Token

### Token Distribution (Mission-Driven, No Initial Sale)

```
Total Supply: 1,000,000 VERITAS (1M - Small, Focused)

├─ 60% Community Rewards (600K)
│  ├─ Early reporters (200K)
│  ├─ Oracle nodes (150K)
│  ├─ Protocol contributors (150K)
│  └─ Future community growth (100K)
│
├─ 30% Protocol Treasury (300K)
│  ├─ Development & maintenance (150K)
│  ├─ Open source grants (100K)
│  └─ Emergency reserve (50K)
│
└─ 10% Team (100K)
   ├─ 4-year vesting
   └─ 1-year cliff
   └─ Mission-aligned only

PHASE 4: NO PUBLIC SALE - Pure utility token
PHASE 4: NO SPECULATION - Focus on real value
PHASE 4: NO GREED - Help people, not profit

FUTURE: Option to sell from treasury if needed for growth
FUTURE: Governance decides - community votes on any sale
FUTURE: Funds go to protocol development, not personal gain
```

### Use Cases

1. **Governance**
   - Vote on staking parameters
   - Vote on new chain additions
   - Vote on oracle upgrades

2. **Fee Discounts**
   - Hold 1K VERITAS → 10% discount on staking requirements
   - Hold 5K VERITAS → 25% discount
   - Hold 20K VERITAS → 50% discount (Gold tier at Silver price)
   - **Lower thresholds with 1M supply**

3. **Community Rewards**
   - Contributors earn VERITAS for:
     - Finding bugs (security rewards)
     - Writing documentation
     - Building integrations
     - Helping other users
   - **Reward helpfulness, not speculation**

4. **Oracle Rewards**
   - Oracle nodes earn VERITAS for accurate validations
   - Bonus for high uptime
   - **Incentivize quality, not quantity**

5. **Open Source Grants**
   - Protocol treasury funds open source work
   - Grants for:
     - Circuit improvements
     - Security audits
     - Educational content
     - Tooling development
   - **Support the ecosystem, not ourselves**

---

## 🤔 What Do You Want?

**Option 1: Keep LINK-Only (Current)**
- ✅ Simple, proven model
- ✅ No token launch complexity
- ✅ Focus on tech first

**Option 2: Add VERITAS Governance Token**
- ✅ Protocol value capture
- ✅ Community ownership
- ✅ Future revenue sharing

**Option 3: Full Dual Token Model**
- ✅ Maximum flexibility
- ✅ More complex
- ✅ Best long-term value

---

## 📝 If We Add Token, Here's What We'd Build

### New Contract: `VeritasToken.sol`
```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract VeritasToken is ERC20, ERC20Votes {
    // Mission: Help people verify AI agents
    // No sale, no speculation, pure utility
    
    uint256 public constant MAX_SUPPLY = 1_000_000; // 1M total
    
    constructor() ERC20("Veritas", "VERITAS") ERC20Permit("Veritas") {
        // Mint to treasury for community distribution
        // No public sale - all distributed via:
        // - Community rewards
        // - Contributor grants
        // - Open source funding
    }
    
    // No transfer restrictions (open source, decentralized)
    // No minting after initial distribution
    // Pure utility token
}
```

### Updated: `AnomalyStaking.sol`
```solidity
// Add VERITAS staking for tier bonuses
mapping(address => uint256) public veritasStaked;
uint256 public constant VERITAS_DISCOUNT = 10; // 10% per 10K tokens
```

### New: `Governance.sol`
```solidity
// DAO for protocol parameters
// Voting on changes
// Treasury management
```

---

**Decision**: ✅ **LINK-only for Phase 4** (keep it simple), add **VERITAS token later** for governance and value capture.

**Protocol Name**: Honestly  
**Token Name**: VERITAS (when we launch it)

**Philosophy**: 
- **Phase 4**: No sale, mission-driven, help people
- **Future**: Option to sell if needed for growth (governance decides)
- **Always**: Change the world, not just make money

