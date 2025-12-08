# Operational Resilience and Decentralized Deployment Guide

This document provides comprehensive guidance for ensuring the long-term resilience, availability, and censorship-resistance of the "honestly" platform through decentralized infrastructure.

## Table of Contents

1. [Decentralized Frontend Hosting](#decentralized-frontend-hosting)
2. [Multi-Domain Strategy](#multi-domain-strategy)
3. [ENS Domain Registration](#ens-domain-registration)
4. [On-Chain Proof Publishing](#on-chain-proof-publishing)
5. [Backup and Recovery](#backup-and-recovery)
6. [Monitoring and Maintenance](#monitoring-and-maintenance)

---

## Decentralized Frontend Hosting

### IPFS Deployment

IPFS (InterPlanetary File System) provides content-addressed, permanent storage for web applications.

#### Prerequisites
```bash
# Install IPFS
# Visit: https://docs.ipfs.tech/install/

# Or using npm
npm install -g ipfs

# Initialize IPFS
ipfs init
```

#### Build and Deploy Frontend

```bash
# Navigate to frontend directory
cd frontend-app

# Install dependencies
npm install

# Build production bundle
npm run build

# The build artifacts will be in the 'dist' directory
```

#### Upload to IPFS

```bash
# Add the build directory to IPFS
ipfs add -r dist/

# The output will include a hash (CID) for the root directory
# Example: QmXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX

# Pin the content to ensure it persists
ipfs pin add QmYourHashHere

# Make it available on the network
ipfs daemon
```

#### Access Your Deployment

Your site will be accessible via:
- IPFS Gateway: `https://ipfs.io/ipfs/QmYourHashHere`
- Cloudflare Gateway: `https://cloudflare-ipfs.com/ipfs/QmYourHashHere`
- Local Gateway: `http://localhost:8080/ipfs/QmYourHashHere`

#### Pinning Services

To ensure your content remains available, use pinning services:

1. **Pinata** (https://pinata.cloud)
   ```bash
   # Install Pinata SDK
   npm install @pinata/sdk
   
   # Upload via API
   # See: https://docs.pinata.cloud/
   ```

2. **Web3.Storage** (https://web3.storage)
   ```bash
   # Install web3.storage client
   npm install web3.storage
   
   # Upload programmatically
   # See: https://web3.storage/docs/
   ```

3. **Fleek** (https://fleek.co)
   - Offers automated IPFS deployment from GitHub
   - Includes CDN and custom domains
   - See: https://docs.fleek.co/

### Arweave Deployment

Arweave provides permanent, immutable storage with a one-time payment model.

#### Prerequisites
```bash
# Install Arweave Deploy CLI
npm install -g arweave-deploy

# Or use bundlr for better performance
npm install -g @bundlr-network/client
```

#### Deploy to Arweave

```bash
# Navigate to your build directory
cd frontend-app/dist

# Deploy using arweave-deploy
arweave-deploy --key-file /path/to/wallet.json

# Or using bundlr
bundlr upload-dir dist/ \
  --index-file index.html \
  --wallet /path/to/wallet.json
```

#### Using ArDrive

For GUI-based deployment:

1. Visit https://app.ardrive.io
2. Create a drive
3. Upload your build folder
4. Make the folder public
5. Get the permanent URL: `https://arweave.net/YourTransactionID`

#### Arweave Gateways

Your content will be accessible via:
- Official Gateway: `https://arweave.net/TxId`
- ar.io Gateway: `https://arweave.ar-io.dev/TxId`
- ViewBlock: `https://viewblock.io/arweave/tx/TxId`

---

## Multi-Domain Strategy

Resilience requires multiple access points to prevent single points of failure.

### Recommended Domain Registrars

Choose multiple registrars in different jurisdictions:

1. **Privacy-Focused**
   - Njalla (https://njal.la) - Anonymous registration
   - OrangeWebsite (https://www.orangewebsite.com) - Iceland-based
   - Joker.com (https://joker.com) - Privacy-friendly

2. **Traditional + Reliable**
   - Namecheap (https://www.namecheap.com) - DNSSEC support
   - Porkbun (https://porkbun.com) - Low cost, good features
   - Gandi (https://www.gandi.net) - European, strong privacy

3. **Decentralized DNS**
   - Handshake (HNS) domains via Namebase
   - ENS domains (see below)
   - Unstoppable Domains

### Domain Configuration Strategy

```
Primary Domains:
- honestly.app (main)
- honestly.io (alternate)
- honestly.xyz (backup)

IPFS Mirrors:
- ipfs.honestly.app → IPFS hash
- web3.honestly.io → IPFS hash

Decentralized:
- honestly.eth (ENS)
- honestly/ (HNS)
```

### DNS Configuration

For IPFS-backed domains:

```dns
# A Record pointing to IPFS gateway
@ A 209.94.90.1

# Or CNAME to gateway
@ CNAME gateway.pinata.cloud

# DNSLink for IPFS
_dnslink TXT "dnslink=/ipfs/QmYourHashHere"
```

### Cloudflare Configuration

1. Add your domain to Cloudflare
2. Enable IPFS gateway:
   - Go to Web3 section
   - Enable IPFS gateway
   - Configure DNSLink
3. Set up page rules for caching
4. Enable Always Online feature

---

## ENS Domain Registration

Ethereum Name Service provides censorship-resistant, blockchain-based domain names.

### Prerequisites

```bash
# Install ENS tools
npm install @ensdomains/ensjs

# Or use web interface
# Visit: https://app.ens.domains
```

### Registering an ENS Name

1. **Via ENS Web App** (Recommended for beginners)
   - Visit https://app.ens.domains
   - Connect MetaMask or WalletConnect
   - Search for "honestly.eth" or desired name
   - Click "Request to Register"
   - Complete the 2-transaction process
   - Annual fee: ~$5-50 depending on name length

2. **Via Etherscan** (Advanced)
   - Navigate to ENS Registry contract
   - Call registration functions directly
   - See: https://ethers.org/ens/

### Configuring ENS Records

```javascript
// Using ensjs library
import { ENS } from '@ensdomains/ensjs'

const ens = new ENS({ provider, ensAddress: getEnsAddress('1') })

// Set content hash to IPFS
await ens.name('honestly.eth').setContenthash(
  'ipfs://QmYourHashHere'
)

// Set text records
await ens.name('honestly.eth').setText('url', 'https://honestly.app')
await ens.name('honestly.eth').setText('description', 'Truth Engine')
await ens.name('honestly.eth').setText('github', 'aresforblue-ai/honestly')
```

### Via ENS Web Interface

1. Go to https://app.ens.domains
2. Search for your domain
3. Click "Records" tab
4. Add records:
   - **Content**: Set to IPFS hash
   - **Text Records**:
     - url: https://honestly.app
     - email: contact@honestly.eth
     - description: Project description
     - github: aresforblue-ai/honestly
     - twitter: @honestly

### Accessing ENS Domains

Users can access your site via:
- IPFS-enabled browsers: `honestly.eth`
- ENS gateways: `https://honestly.eth.limo`
- eth.link: `https://honestly.eth.link`
- Brave browser: Native ENS support
- MetaMask: Automatic resolution

---

## On-Chain Proof Publishing

Publishing deployment proofs on-chain ensures transparency and compliance with license requirements.

### Ethereum Mainnet

#### Using a Smart Contract

```solidity
// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.0;

contract DeploymentRegistry {
    struct Deployment {
        string repositoryUrl;
        string commitHash;
        string ipfsHash;
        uint256 timestamp;
        address deployer;
    }
    
    mapping(bytes32 => Deployment) public deployments;
    
    event DeploymentRegistered(
        bytes32 indexed deploymentId,
        address deployer,
        string repositoryUrl,
        string commitHash
    );
    
    function registerDeployment(
        string memory _repositoryUrl,
        string memory _commitHash,
        string memory _ipfsHash
    ) public returns (bytes32) {
        bytes32 deploymentId = keccak256(
            abi.encodePacked(msg.sender, block.timestamp, _commitHash)
        );
        
        deployments[deploymentId] = Deployment({
            repositoryUrl: _repositoryUrl,
            commitHash: _commitHash,
            ipfsHash: _ipfsHash,
            timestamp: block.timestamp,
            deployer: msg.sender
        });
        
        emit DeploymentRegistered(
            deploymentId,
            msg.sender,
            _repositoryUrl,
            _commitHash
        );
        
        return deploymentId;
    }
}
```

Deploy this contract and call `registerDeployment()` with:
- Repository URL: `https://github.com/aresforblue-ai/honestly`
- Commit hash: Your git commit SHA
- IPFS hash: Your deployment CID

#### Using a Simple Transaction

```javascript
// Using ethers.js
import { ethers } from 'ethers'

const provider = new ethers.providers.JsonRpcProvider('YOUR_RPC_URL')
const wallet = new ethers.Wallet('YOUR_PRIVATE_KEY', provider)

const message = JSON.stringify({
  project: 'honestly',
  repository: 'https://github.com/aresforblue-ai/honestly',
  commit: 'abc123...',
  ipfs: 'QmXXX...',
  timestamp: Date.now()
})

// Send transaction with data
const tx = await wallet.sendTransaction({
  to: wallet.address, // Send to self
  value: 0,
  data: ethers.utils.hexlify(ethers.utils.toUtf8Bytes(message))
})

console.log('Proof transaction:', tx.hash)
```

### Base Network

Base offers lower fees while maintaining Ethereum security:

```javascript
// Connect to Base
const provider = new ethers.providers.JsonRpcProvider(
  'https://mainnet.base.org'
)

// Same code as above, but on Base
// Transaction fees will be much lower (~$0.01 vs ~$5)
```

### Arbitrum

Similar to Base, Arbitrum offers lower fees:

```javascript
// Connect to Arbitrum
const provider = new ethers.providers.JsonRpcProvider(
  'https://arb1.arbitrum.io/rpc'
)
```

### Using NFTs as Proof

Deploy an ERC-721 token representing your deployment:

```solidity
// SPDX-License-Identifier: AGPL-3.0-only
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";

contract DeploymentNFT is ERC721URIStorage {
    uint256 private _tokenIdCounter;
    
    constructor() ERC721("Honestly Deployment", "HONEST") {}
    
    function mintDeployment(string memory metadataUri) public {
        uint256 tokenId = _tokenIdCounter++;
        _safeMint(msg.sender, tokenId);
        _setTokenURI(tokenId, metadataUri);
    }
}
```

Metadata format (upload to IPFS):
```json
{
  "name": "Honestly Deployment #1",
  "description": "Production deployment of honestly truth engine",
  "attributes": [
    {
      "trait_type": "Repository",
      "value": "https://github.com/aresforblue-ai/honestly"
    },
    {
      "trait_type": "Commit",
      "value": "abc123..."
    },
    {
      "trait_type": "IPFS",
      "value": "QmXXX..."
    },
    {
      "trait_type": "Deployment Date",
      "value": "2025-12-05"
    }
  ]
}
```

### Reporting Your Proof

After publishing on-chain proof:

1. Create an issue in the repository:
   - Title: "Deployment Proof: [Your Project Name]"
   - Label: "deployment-proof"
   - Include:
     - Blockchain network used
     - Transaction hash or contract address
     - Deployment URL
     - Brief description of your use case

2. Or submit a PR to DEPLOYMENTS.md (if it exists)

---

## Backup and Recovery

### Code Repository Mirrors

Mirror the repository across multiple platforms:

```bash
# Add multiple remotes
git remote add github git@github.com:aresforblue-ai/honestly.git
git remote add gitlab git@gitlab.com:aresforblue-ai/honestly.git
git remote add codeberg git@codeberg.org:aresforblue-ai/honestly.git
git remote add gitea git@gitea.com:aresforblue-ai/honestly.git

# Push to all remotes
git remote | xargs -L1 git push --all
```

Automated mirroring with GitHub Actions:

```yaml
name: Mirror Repository
on: [push]
jobs:
  mirror:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      - name: Mirror to GitLab
        uses: pixta-dev/repository-mirroring-action@v1
        with:
          target_repo_url: ${{ secrets.GITLAB_REPO_URL }}
          ssh_private_key: ${{ secrets.SSH_PRIVATE_KEY }}
```

### Database Backups

For Neo4j and PostgreSQL:

```bash
# Neo4j backup
neo4j-admin dump --database=neo4j --to=/backups/neo4j-$(date +%Y%m%d).dump

# Upload to IPFS
ipfs add /backups/neo4j-$(date +%Y%m%d).dump

# PostgreSQL backup
pg_dump honestly_db > backup-$(date +%Y%m%d).sql
ipfs add backup-$(date +%Y%m%d).sql
```

### Configuration as Code

Store all configurations in version control:

```
configs/
├── nginx/
│   └── honestly.conf
├── docker/
│   └── docker-compose.yml
├── k8s/
│   ├── deployment.yaml
│   └── service.yaml
└── env/
    └── .env.example
```

---

## Monitoring and Maintenance

### Health Checks

Implement health check endpoints:

```javascript
// Express.js health check
app.get('/health', (req, res) => {
  res.json({
    status: 'healthy',
    timestamp: Date.now(),
    version: process.env.APP_VERSION,
    commit: process.env.GIT_COMMIT
  })
})
```

### Uptime Monitoring

Use multiple monitoring services:

1. **UptimeRobot** (https://uptimerobot.com)
   - Free tier: 50 monitors
   - 5-minute intervals

2. **Pingdom** (https://www.pingdom.com)
   - Synthetic monitoring
   - Performance insights

3. **StatusCake** (https://www.statuscake.com)
   - Global monitoring
   - Page speed tests

### Status Page

Create a public status page:

1. **Cachet** (self-hosted)
   ```bash
   docker run -d \
     --name cachet \
     -p 8000:8000 \
     cachethq/docker
   ```

2. **Statuspage.io** (hosted)
   - Visit https://www.atlassian.com/software/statuspage

3. **GitHub-based** (free)
   - Use GitHub Issues or Discussions
   - Create status.honestly.eth subdomain

### Automated Updates

Keep dependencies updated:

```yaml
# Dependabot configuration
version: 2
updates:
  - package-ecosystem: "npm"
    directory: "/frontend-app"
    schedule:
      interval: "weekly"
  
  - package-ecosystem: "npm"
    directory: "/backend-graphql"
    schedule:
      interval: "weekly"
  
  - package-ecosystem: "pip"
    directory: "/backend-python"
    schedule:
      interval: "weekly"
```

---

## Security Considerations

1. **Private Keys**
   - Never commit private keys
   - Use hardware wallets for critical operations
   - Rotate keys regularly

2. **Access Control**
   - Use multi-sig wallets for critical contracts
   - Implement role-based access control
   - Regular security audits

3. **Monitoring**
   - Set up alerts for unusual activity
   - Monitor smart contract interactions
   - Track gas prices and optimize

---

## Resources and References

### IPFS
- Official Docs: https://docs.ipfs.tech
- Awesome IPFS: https://awesome.ipfs.io
- IPFS Forums: https://discuss.ipfs.tech

### Arweave
- Official Docs: https://docs.arweave.org
- ArDrive: https://ardrive.io
- Permaweb Cookbook: https://cookbook.arweave.dev

### ENS
- Official Docs: https://docs.ens.domains
- ENS App: https://app.ens.domains
- ENS Support: https://support.ens.domains

### Blockchain
- Ethereum: https://ethereum.org/developers
- Base: https://docs.base.org
- Arbitrum: https://docs.arbitrum.io

### Web3 Tools
- Fleek: https://fleek.co
- Cloudflare Web3: https://www.cloudflare.com/web3
- Unstoppable Domains: https://unstoppabledomains.com

---

## Quick Start Checklist

- [ ] Build frontend for production
- [ ] Deploy to IPFS via Pinata or Fleek
- [ ] Deploy to Arweave for permanent backup
- [ ] Register 2-3 traditional domains
- [ ] Register ENS domain (honestly.eth)
- [ ] Configure DNSLink on traditional domains
- [ ] Publish on-chain deployment proof
- [ ] Submit proof to repository (issue or PR)
- [ ] Set up uptime monitoring
- [ ] Create repository mirrors
- [ ] Document deployment in DEPLOYMENTS.md
- [ ] Test all access methods

---

**Maintained by**: aresforblue-ai  
**Repository**: https://github.com/aresforblue-ai/honestly  
**License**: AGPL-3.0-only  
**Last Updated**: 2025-12-05
