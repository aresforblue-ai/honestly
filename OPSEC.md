# Operational Security (OPSEC) and Legal Framework Guide

This document provides comprehensive guidance on maintaining pseudonymity, operational security, and legal entity structures for open-source project maintainers, particularly those working with blockchain, Web3, and decentralized technologies.

## Table of Contents

1. [Maintainer Pseudonymity](#maintainer-pseudonymity)
2. [Legal Entity Structures](#legal-entity-structures)
3. [Jurisdiction Considerations](#jurisdiction-considerations)
4. [Financial Operations](#financial-operations)
5. [Communication Security](#communication-security)
6. [Threat Modeling](#threat-modeling)
7. [Incident Response](#incident-response)

---

## Maintainer Pseudonymity

### Why Pseudonymity Matters

For open-source maintainers working on potentially disruptive technologies:

- **Personal Safety**: Protection from targeted attacks or harassment
- **Legal Protection**: Shield personal identity from jurisdictional overreach
- **Operational Freedom**: Ability to work across borders without restrictions
- **Focus on Work**: Reduced personal attention, more focus on code
- **Privacy Rights**: Fundamental right to privacy in digital spaces

### Establishing a Pseudonymous Identity

#### 1. Choose a Consistent Handle

- Select a memorable, professional pseudonym
- Use it consistently across all platforms
- Avoid names that could be confused with real identities
- Consider trademark searches to avoid conflicts

Example: `aresforblue-ai` (clear, memorable, professional)

#### 2. Create Isolated Accounts

**Email**
```
Option 1: ProtonMail
- Visit: https://proton.me/mail
- Swiss jurisdiction, end-to-end encrypted
- No phone number required for basic accounts

Option 2: Tutanota
- Visit: https://tutanota.com
- German jurisdiction, encrypted
- Privacy-focused, anonymous signup

Best Practice:
- Use email aliasing (SimpleLogin, AnonAddy)
- Never link to personal email
- Use PGP for sensitive communications
```

**GitHub Account**
```bash
# Create new GitHub account with pseudonymous email
# Never use real name in profile
# Use SSH keys generated on isolated environment

# Generate SSH key
ssh-keygen -t ed25519 -C "pseudonym@protonmail.com"

# Configure git to use pseudonym
git config --global user.name "aresforblue-ai"
git config --global user.email "pseudonym@protonmail.com"

# Sign commits with GPG (optional but recommended)
gpg --full-generate-key
git config --global user.signingkey YOUR_KEY_ID
git config --global commit.gpgsign true
```

**Social Media**
```
Twitter/X:
- Create separate account
- Use pseudonym consistently
- Never link personal accounts
- Use VPN/Tor for creation and access

Discord:
- Separate account for project
- Use only for project-related communication
- Enable 2FA with authenticator app (not SMS)

Telegram:
- Create account with pseudonymous number (see below)
- Use username, not phone number for contact
- Enable two-step verification
```

#### 3. Metadata Hygiene

**Image/Document Metadata**
```bash
# Remove EXIF data from images before uploading
exiftool -all= image.jpg

# Or use online tools
# https://www.verexif.com/en/

# For PDFs, use qpdf to clean metadata
qpdf --linearize --object-streams=generate input.pdf output.pdf
```

**Code Commits**
```bash
# Check for accidentally included personal info
git log --all --full-history -- "*password*"
git log --all --full-history -- "*secret*"
git log --all --full-history -- "*email*"

# Use git-filter-repo to remove sensitive history
pip install git-filter-repo
# Remove a sensitive file from history
git filter-repo --path sensitive-file
# Or to keep everything except sensitive files, use:
# git filter-repo --invert-paths --path sensitive-file
```

#### 4. Browser and Network Security

**Browser Configuration**
```
Recommended: Firefox with hardening
- Install uBlock Origin
- Install Privacy Badger
- Install NoScript (optional, advanced)
- Disable WebRTC (about:config → media.peerconnection.enabled = false)
- Use Firefox containers for account isolation

Or: Brave Browser
- Built-in shields
- Tor integration
- Fingerprinting protection
```

**VPN Selection**
```
Recommended VPNs (No logs, crypto payment):
1. Mullvad (https://mullvad.net)
   - €5/month, anonymous account numbers
   - Accept cash and crypto
   - No email required
   - Swedish jurisdiction

2. IVPN (https://www.ivpn.net)
   - Similar privacy features to Mullvad
   - Accept crypto payments
   - Can be paid with cash

3. ProtonVPN (https://protonvpn.com)
   - Swiss jurisdiction
   - Free tier available
   - From makers of ProtonMail

Configuration:
- Always enable kill switch
- Use WireGuard protocol for performance
- Avoid VPN providers that require personal info
```

**Tor Usage**
```bash
# For maximum anonymity on sensitive operations
# Download Tor Browser: https://www.torproject.org

# Or use Tails OS for complete isolation
# https://tails.boum.org

Use Cases for Tor:
- Initial account creation
- Accessing services from restricted locations
- Research on sensitive topics
- Emergency communications
```

#### 5. Phone Numbers and SMS

**Virtual Phone Numbers**
```
Option 1: Silent.link
- https://silent.link
- eSIM with crypto payment
- No KYC required
- Anonymous connectivity

Option 2: JMP.chat
- https://jmp.chat
- XMPP-based
- Accept crypto
- Anonymous registration

Option 3: MySudo
- https://mysudo.com
- Multiple virtual numbers
- Privacy-focused
- US-based but privacy-respecting

For SMS verification only:
- Use SMS-Pool or similar services
- Accept crypto, single-use numbers
- Not for primary communications
```

---

## Legal Entity Structures

### Why You Need a Legal Entity

Benefits of formal legal structures:

1. **Liability Protection**: Separate personal and project liability
2. **Tax Advantages**: Clear business expense treatment
3. **Trademark Protection**: Register project name and logo
4. **Contract Capability**: Sign agreements without exposing personal identity
5. **Banking Access**: Open business accounts for project funds
6. **Credibility**: Professional appearance for partnerships

### Entity Type Options

#### 1. Delaware C-Corporation (USA)

**Pros**:
- Well-established corporate law
- Investor-friendly for future funding
- Strong legal precedents
- Can maintain anonymity through registered agents

**Cons**:
- More expensive (~$500-1000/year)
- Double taxation (corporate + personal)
- More regulatory compliance

**Setup Process**:
```
1. Choose unique company name
2. File Certificate of Incorporation with Delaware Secretary of State
3. Hire registered agent (e.g., Harvard Business Services, $50-150/year)
4. Obtain EIN from IRS (online, free)
5. Draft bylaws and issue stock certificates
6. File annual franchise tax report (~$450/year minimum)

Cost: ~$1000 first year, ~$500-800 annually

Registered Agent Services:
- Harvard Business Services: https://www.delawareinc.com
- Incfile: https://www.incfile.com
- Northwest Registered Agent: https://www.northwestregisteredagent.com
```

#### 2. Wyoming LLC (USA)

**Pros**:
- Strong privacy protections
- No state income tax
- Low annual fees (~$60/year)
- Anonymous member option
- Crypto-friendly jurisdiction

**Cons**:
- Less prestigious than Delaware
- Fewer legal precedents
- May face questions from investors

**Setup Process**:
```
1. File Articles of Organization with Wyoming Secretary of State (~$100)
2. Hire registered agent (~$50-100/year)
3. Obtain EIN from IRS
4. Create Operating Agreement
5. File annual report (~$60/year)

Cost: ~$300 first year, ~$150-200 annually

Wyoming maintains member privacy - names not public record
```

#### 3. Cayman Islands Foundation Company

**Pros**:
- Zero taxation on non-Cayman income
- Strong asset protection
- International recognition
- Purpose-driven structure (good for open-source)

**Cons**:
- Expensive (~$5,000+ setup, $3,000+ annual)
- Requires professional trustees
- Complex compliance
- May be seen as tax avoidance

**Setup Process**:
```
1. Engage Cayman corporate service provider
2. Draft foundation articles and bylaws
3. Appoint officers/directors
4. Register with Cayman Registrar
5. Annual compliance filings

Cost: $5,000-10,000 setup, $3,000-5,000 annually

Recommended Service Providers:
- Ogier: https://www.ogier.com
- Carey Olsen: https://www.careyolsen.com
- Walkers: https://www.walkersglobal.com
```

#### 4. Swiss Foundation (Stiftung)

**Pros**:
- Excellent for non-profit/open-source projects
- Strong privacy laws
- International credibility
- Tax advantages for charitable purposes

**Cons**:
- Expensive (CHF 50,000 minimum capital)
- Strict purpose requirements
- Complex governance rules
- High ongoing costs

**Setup Process**:
```
1. Draft foundation charter
2. Obtain notarization
3. Deposit minimum CHF 50,000 capital
4. Register in Commercial Register
5. Annual audits and filings

Cost: CHF 50,000+ capital, CHF 5,000-10,000 annually

Best for: Established projects with significant resources
```

#### 5. Estonia e-Residency + OÜ

**Pros**:
- Digital-first jurisdiction
- Easy to manage remotely
- EU member state benefits
- Crypto-friendly
- Low costs (~€200/year)

**Cons**:
- Less privacy (director names public)
- EU regulations apply
- May not be recognized as "serious" by some

**Setup Process**:
```
1. Apply for e-Residency (~€100-120)
   https://www.e-resident.gov.ee

2. Receive digital ID card (2-4 weeks)

3. Register OÜ online (~€190)
   Via providers like:
   - LeapIN: https://www.leapin.eu
   - 1Office: https://www.1office.co

4. Open business bank account (can be remote)

5. File annual reports online

Cost: €300-400 first year, €200-300 annually
```

### Recommended Approach by Project Stage

**Early Stage (MVP, no funding)**:
- Wyoming LLC with registered agent
- Cost-effective, private, simple
- Can convert later if needed

**Growth Stage (seeking funding/partnerships)**:
- Delaware C-Corp
- Investor-friendly, well-understood
- Strong legal framework

**Established (international, significant revenue)**:
- Swiss Foundation or Cayman Foundation
- Tax efficient, international presence
- Appropriate for substantial operations

---

## Jurisdiction Considerations

### Key Factors in Jurisdiction Selection

1. **Privacy Laws**
   - GDPR compliance (EU)
   - Data retention requirements
   - Government data access laws

2. **Taxation**
   - Corporate income tax rates
   - International tax treaties
   - Crypto tax treatment

3. **Regulatory Environment**
   - Crypto/blockchain regulations
   - Open source legal clarity
   - Innovation-friendly policies

4. **Political Stability**
   - Rule of law
   - Property rights protection
   - Government predictability

5. **Practical Considerations**
   - Language barriers
   - Time zones
   - Banking access
   - Professional service availability

### Jurisdiction Rankings for Web3/Open Source

#### Tier 1: Best Overall

**1. Wyoming, USA**
- Strong privacy protections
- Crypto-friendly DAO laws
- Low costs
- English language
- Cons: US jurisdiction oversight

**2. Switzerland**
- Excellent privacy
- Crypto hub (Zug "Crypto Valley")
- International respect
- Cons: Expensive

**3. Estonia**
- Digital-first
- EU member benefits
- Easy remote management
- Cons: Less privacy, EU regulations

#### Tier 2: Good Options

**4. Singapore**
- Asia-Pacific hub
- Clear crypto regulations
- English language
- Cons: Expensive, strict compliance

**5. Malta**
- "Blockchain Island"
- EU member
- Crypto-friendly regulations
- Cons: EU oversight, reputation concerns

**6. Portugal**
- Tax-friendly for crypto
- EU member
- Good quality of life
- Cons: Language barrier for some

#### Tier 3: Specialized Use Cases

**7. Cayman Islands**
- Zero tax
- Offshore haven
- International finance hub
- Cons: Very expensive, reputation

**8. BVI (British Virgin Islands)**
- Privacy-focused
- International business center
- Cons: Expensive, offshore stigma

**9. Panama**
- Strong privacy
- No income tax on foreign earnings
- Cons: Reputation concerns, less crypto-specific

### Jurisdictions to Avoid

**Red Flags**:
- Heavy-handed government overreach
- Unclear or hostile crypto regulations
- High risk of asset seizure
- Unstable political situation
- Poor rule of law

**Examples** (situation-dependent):
- Countries with extensive surveillance programs
- Jurisdictions with ambiguous crypto legal status
- Places with history of arbitrary enforcement
- Locations with capital controls

---

## Financial Operations

### Cryptocurrency Wallets

**Hot Wallet (Daily Operations)**
```
MetaMask:
- Browser extension
- Easy to use
- Multi-chain support

Best Practices:
- Keep minimal funds
- Use for routine transactions
- Enable auto-lock
- Never share seed phrase
```

**Cold Storage (Long-term Holdings)**
```
Hardware Wallets:
1. Ledger Nano X
   - https://www.ledger.com
   - Bluetooth + USB
   - $150-200

2. Trezor Model T
   - https://trezor.io
   - Open source firmware
   - Touchscreen
   - $200-250

Setup:
- Purchase directly from manufacturer
- Initialize offline
- Store seed phrase securely (metal backup)
- Use passphrase (25th word) for extra security
```

**Multi-Sig Wallets (Team/DAO)**
```
Gnosis Safe:
- https://safe.global
- Ethereum + L2s
- Configurable thresholds (e.g., 3-of-5)
- Transaction batching
- Team management

Setup:
1. Deploy Safe contract
2. Add owner addresses
3. Set signing threshold
4. Test with small amount first
```

### Banking Solutions

**Traditional Banking**
```
Business Account Options:
1. Mercury (https://mercury.com)
   - For US LLCs/C-Corps
   - Startup-friendly
   - No fees for basic accounts

2. Relay Financial (https://relayfi.com)
   - Multiple accounts/cards
   - For US entities
   - Good for compartmentalization

3. Wise Business (https://wise.com)
   - Multi-currency
   - International transfers
   - Good for remote businesses

Privacy Note: Business accounts require EIN/registration docs
Use entity name, not personal name on accounts
```

**Crypto Banking**
```
Fiat On/Off Ramps:
1. Kraken
   - Reputable exchange
   - Supports wire transfers
   - Various payment methods

2. Coinbase (for entities)
   - Coinbase Prime for institutions
   - Good compliance track record

Privacy-Enhanced:
1. Aztec Network
   - zkMoney for private transfers
   - Ethereum-based
   - https://aztec.network

2. Railgun
   - Privacy system for DeFi
   - Check compliance in your jurisdiction
   - https://railgun.org

**IMPORTANT**: Some privacy-enhancing protocols have faced regulatory actions (e.g., Tornado Cash sanctioned by OFAC in 2022). Always verify the legal status of any privacy tool in your jurisdiction before use. Consult legal counsel for compliance with sanctions and AML/KYC requirements.
```

### Payment Processing

**For Project Funding/Donations**
```
Crypto:
- Direct wallet addresses (ETH, BTC, etc.)
- Gitcoin Grants: https://gitcoin.co
- Giveth: https://giveth.io

Traditional:
- Open Collective: https://opencollective.com
- GitHub Sponsors: https://github.com/sponsors
- Patreon: https://www.patreon.com

Hybrid:
- The Giving Block: https://thegivingblock.com
```

### Tax Considerations

**General Principles**
```
- Keep detailed records of all transactions
- Use accounting software (QuickBooks, Xero)
- Understand tax treatment in your jurisdiction
- Work with crypto-familiar CPA/accountant

US-Specific:
- IRS requires reporting of crypto transactions
- Capital gains treatment for crypto
- Schedule C for LLC, Form 1120 for C-Corp

EU-Specific:
- VAT considerations
- Crypto capital gains treatment varies by country
- Cross-border rules under ATAD
```

---

## Communication Security

### Encrypted Communications

**Email Encryption**
```
PGP/GPG:
# Generate key pair
gpg --full-generate-key

# Export public key
gpg --armor --export your@email.com > publickey.asc

# Share public key (GitHub, keybase, etc.)

# Encrypt message
gpg --encrypt --recipient recipient@email.com message.txt

# Decrypt message
gpg --decrypt message.txt.gpg
```

**Secure Messaging**
```
Recommended Apps:
1. Signal
   - End-to-end encrypted
   - Open source
   - Disappearing messages
   - Desktop + mobile

2. Element (Matrix Protocol)
   - Decentralized
   - End-to-end encrypted
   - Self-hostable
   - Good for communities

3. Session
   - No phone number required
   - Anonymous
   - Decentralized routing
   - Open source

Setup Tips:
- Verify safety numbers/keys
- Enable disappearing messages for sensitive chats
- Use separate device for project comms (if high threat)
```

### Video Conferencing

**Privacy-Focused Options**
```
1. Jitsi Meet
   - Open source
   - Self-hostable
   - No account required
   - End-to-end encryption (with additional setup)

2. Signal Video Calls
   - End-to-end encrypted
   - Up to 40 participants
   - Requires Signal account

3. BigBlueButton
   - Open source
   - Self-hostable
   - Good for webinars/meetings
   - Can integrate with privacy-focused hosting
```

### Operational Security Practices

**Meeting Protocols**
```
1. Never use real names in public/semi-public meetings
2. Disable video if identity protection needed
3. Use virtual backgrounds to hide location
4. Mute when not speaking
5. Record only with explicit consent
6. Share meeting links through secure channels only
```

**Document Sharing**
```
Secure Options:
1. Cryptpad (https://cryptpad.fr)
   - End-to-end encrypted
   - Collaborative editing
   - No account required

2. OnionShare (https://onionshare.org)
   - Share files over Tor
   - No server needed
   - Anonymous

3. Tresorit (https://tresorit.com)
   - Encrypted cloud storage
   - Business plans available
   - Swiss-based

Never:
- Share documents with metadata
- Use personal cloud accounts
- Email sensitive docs unencrypted
```

---

## Threat Modeling

### Identify Your Threats

**Common Threat Actors**:

1. **Malicious Users/Hackers**
   - Seeking to steal project funds
   - Attempting identity doxing
   - Deploying social engineering

2. **Government/Regulators**
   - Jurisdictional overreach
   - Regulatory enforcement
   - Data requests

3. **Competitors**
   - Market intelligence
   - Intellectual property theft
   - Reputation attacks

4. **General Public**
   - Harassment campaigns
   - Unwanted attention
   - Privacy invasion

### Risk Assessment Matrix

```
For each threat, assess:
- Likelihood: Low / Medium / High
- Impact: Low / Medium / High
- Priority: (Likelihood × Impact)

Example:
Threat: Identity doxing by malicious user
- Likelihood: Medium
- Impact: High
- Priority: HIGH

Mitigation:
- Use VPN for all project activity
- Never link personal accounts
- Maintain strict OPSEC practices
```

### Personal Security Levels

**Level 1: Basic Pseudonymity** (Most projects)
- Separate accounts with pseudonym
- VPN usage
- Avoid personal information leaks
- Standard encryption practices

**Level 2: Enhanced Privacy** (Controversial projects)
- Level 1 + 
- Tor for sensitive operations
- Burner devices for project work
- Stricter compartmentalization
- Physical security measures

**Level 3: Operational Security** (High-risk projects)
- Level 2 +
- Air-gapped devices
- Secure locations for work
- Extensive anti-surveillance measures
- Multiple layers of identity separation

Choose level based on realistic threat assessment.

---

## Incident Response

### Preparation

**Before An Incident**:
```
1. Document emergency procedures
2. Establish secure backup communications
3. Identify trusted allies/advisors
4. Keep offline backups of critical data
5. Have legal counsel contact info ready
6. Maintain operational fund reserves
```

### Identity Compromise

**If Your Pseudonymous Identity Is Compromised**:

```
Immediate Actions:
1. Assess scope of compromise
2. Secure remaining accounts (change passwords, enable 2FA)
3. Notify core team through secure channel
4. Document the incident
5. Prepare public statement if necessary

Medium-term:
1. Consider migration to new identity
2. Transfer project ownership/access
3. Review and improve OPSEC practices
4. Consult legal counsel
5. Update security documentation

Long-term:
1. Rebuild trust with community
2. Implement lessons learned
3. Enhanced security measures
4. Regular security audits
```

### Security Breach

**If Project Infrastructure Is Compromised**:

```
1. Immediate Containment
   - Disable compromised access
   - Rotate all credentials
   - Isolate affected systems

2. Assessment
   - Determine scope of breach
   - Identify what was accessed
   - Check for ongoing unauthorized access

3. Communication
   - Notify users if their data affected
   - Transparent disclosure (within reason)
   - Regular status updates

4. Recovery
   - Restore from clean backups
   - Patch vulnerabilities
   - Implement additional security measures

5. Post-Mortem
   - Document incident timeline
   - Root cause analysis
   - Update security procedures
   - Share lessons (if appropriate)
```

### Legal Threat

**If Facing Legal Action**:

```
DO:
- Contact lawyer immediately
- Document everything
- Preserve all communications
- Follow legal counsel advice
- Stay calm and professional

DON'T:
- Panic or make hasty decisions
- Destroy evidence
- Make public statements without counsel
- Engage directly with opposing party
- Ignore legal notices

Resources:
- Electronic Frontier Foundation: https://www.eff.org
- Legal defense funds in crypto space
- Jurisdiction-specific legal aid organizations
```

---

## Additional Resources

### Privacy Tools
- PrivacyTools.io: https://www.privacytools.io
- PRISM Break: https://prism-break.org
- Techlore: https://techlore.tech

### Legal Resources
- EFF (Electronic Frontier Foundation): https://www.eff.org
- IAPP (Privacy professionals): https://iapp.org
- OpenLaw: https://www.openlaw.io

### Security
- Krebs on Security: https://krebsonsecurity.com
- Schneier on Security: https://www.schneier.com
- Trail of Bits: https://blog.trailofbits.com

### Crypto/Web3 Legal
- Coin Center: https://www.coincenter.org
- Blockchain Association: https://theblockchainassociation.org
- DeFi Education Fund: https://www.defieducationfund.org

### Jurisdictional Guides
- Crypto Tax Girl: https://cryptotaxgirl.com
- Ledgermatic: https://www.ledgermatic.com
- Bitcoin Legal Resources: Various by jurisdiction

---

## Checklist: Setting Up Secure Operations

### Identity Setup
- [ ] Choose consistent pseudonym
- [ ] Create encrypted email account
- [ ] Set up VPN subscription
- [ ] Configure browser for privacy
- [ ] Create isolated social media accounts
- [ ] Generate and backup SSH keys
- [ ] Set up GPG encryption

### Legal Structure
- [ ] Assess jurisdiction needs
- [ ] Choose entity type
- [ ] Engage formation service/lawyer
- [ ] File incorporation documents
- [ ] Obtain EIN/tax ID
- [ ] Set up business bank account
- [ ] Register domain names under entity

### Financial Setup
- [ ] Set up hardware wallet
- [ ] Configure multi-sig if needed
- [ ] Establish banking relationships
- [ ] Set up payment processing
- [ ] Implement accounting system
- [ ] Engage tax professional

### Operational Security
- [ ] Document OPSEC procedures
- [ ] Set up secure communications
- [ ] Implement backup strategy
- [ ] Create incident response plan
- [ ] Review and test security regularly
- [ ] Train team members on OPSEC

### Maintenance
- [ ] Regular security audits
- [ ] Update OPSEC documentation
- [ ] Review threat model quarterly
- [ ] Maintain legal compliance
- [ ] Keep backups current
- [ ] Review and update insurance

---

**Important Disclaimer**: This document provides general information and should not be construed as legal, financial, or security advice. Consult with qualified professionals for your specific situation. Laws and regulations vary by jurisdiction and change over time. The maintainers of this document are not responsible for any consequences of following this guidance.

**Maintained by**: aresforblue-ai  
**Repository**: https://github.com/aresforblue-ai/honestly  
**License**: AGPL-3.0-only  
**Last Updated**: 2025-12-05
