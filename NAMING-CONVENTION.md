# Naming Convention

## Protocol vs Token

### Protocol Name: **Honestly**
- The overall project/platform name
- Used in:
  - Documentation
  - GitHub repos
  - Website/branding
  - API endpoints
  - Contract comments

### Token Name: **VERITAS** (Future)
- The governance/value capture token (when we launch it)
- Used in:
  - Token contract: `VeritasToken.sol`
  - Token symbol: `VERITAS`
  - Governance contracts
  - Revenue sharing

### Current Staking Token: **LINK**
- Chainlink token
- Used for:
  - Anomaly reporting stakes
  - Slashing/rewards
  - Dispute bonds

## Examples

✅ **Correct**:
- "Honestly protocol" (project name)
- "VERITAS token" (future governance token)
- "LINK staking" (current staking token)
- `VeritasToken.sol` (future contract)
- `HonestlyStaking.sol` (current - uses LINK)

❌ **Incorrect**:
- "Honestly token" (should be VERITAS)
- `HonestlyToken.sol` (should be VeritasToken.sol)

## File Naming

### Current Contracts (Phase 4)
- `AnomalyStaking.sol` - Uses LINK
- `AnomalyOracle.sol` - Uses LINK
- `AnomalyRegistry.sol` - No token
- `LocalDetector.sol` - No token
- `ZkMLVerifier.sol` - No token

### Future Contracts (Phase 4.5+)
- `VeritasToken.sol` - VERITAS ERC20 token
- `VeritasGovernance.sol` - DAO governance
- `VeritasStaking.sol` - VERITAS staking for bonuses

## Branding

**Protocol**: Honestly  
**Tagline**: "Verifiable AI Agent Identity Protocol"  
**Token**: VERITAS (when launched)  
**Token Symbol**: `VERITAS` or `VTS`

---

**Status**: ✅ Naming convention established

