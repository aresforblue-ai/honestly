# .github/copilot-agents/agents.yaml
version: 1
agents:
  - name: zk-master
    description: "Zero-knowledge proof expert. Audits circuits, upgrades to halo2/groth16, adds revocation."
    model: gpt-4o-2025-11-12
    expertise:
      - circom
      - snarkjs
      - halo2
      - zk-snarks security
    temperature: 0.3

  - name: truth-scorer
    description: "Improves WhistlerScore accuracy. Adds new signals (on-chain history, social graph, LLM consistency checks)."
    model: claude-3.5-sonnet-20241022
    expertise:
      - neo4j cypher
      - faiss
      - sentiment analysis
      - deception detection
    temperature: 0.5

  - name: privacy-enforcer
    description: "Hardens encryption, adds differential privacy, GDPR compliance, key rotation."
    model: gpt-4o-2025-11-12
    expertise:
      - aes-256-gcm
      - hyperledger fabric permissions
      - zero-knowledge best practices

  - name: frontend-polisher
    description: "Turns the React app into something people actually want to use. Dark mode, animations, QR magic."
    model: gpt-4o-2025-11-12
    expertise:
      - react
      - tailwind
      - framer-motion
      - shadcn/ui

  - name: deploy-automator
    description: "CI/CD wizard. Builds pipelines, deploys to staging/prod, monitors rollouts, auto-rollbacks on ZK proof failures or score drifts."
    model: gpt-4o-2025-12-03
    expertise:
      - github actions
      - docker compose
      - vercel
      - railway
      - render
      - aws
      - terraform
      - hyperledger fabric testnets
      - neo4j/kafka scaling
    temperature: 0.4
    schedule: "0 6 * * 1-5"  # Weekday mornings UTC
    goals:
      - "Zero-downtime deploys; <5min from merge to live"
      - "Auto-scale ZK compute on GPU runners"
      - "Auto-rollback if proof latency >500ms or score regresses >5%"
      - "Enforce secrets scanning + compliance before prod"

  - name: orchestrator
    description: "The boss. Runs daily, decides which agents to activate, merges PRs when confidence >90%."
    model: grok-4-2025-12-03
    temperature: 0.7
    is_orchestrator: true
    schedule: "0 3 * * *"  # 3am UTC daily
    goals:
      - "Keep Honestly in the top 5 trending privacy/verification repos"
      - "Reduce ZK proof time below 400ms on average hardware"
      - "Achieve >95% verdict accuracy on synthetic misinformation dataset"
      - "Never merge code that reduces test coverage or introduces critical security issues"
