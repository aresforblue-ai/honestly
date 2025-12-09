import * as anchor from "@coral-xyz/anchor";
import { Program } from "@coral-xyz/anchor";
import { VERIDICUS } from "../target/types/VERIDICUS";
import { PublicKey, Keypair, SystemProgram } from "@solana/web3.js";
import { TOKEN_PROGRAM_ID, createMint, createAccount, mintTo, burn } from "@solana/spl-token";
import { expect } from "chai";

describe("VERIDICUS", () => {
  const provider = anchor.AnchorProvider.env();
  anchor.setProvider(provider);

  const program = anchor.workspace.VERIDICUS as Program<VERIDICUS>;
  const authority = provider.wallet;
  
  let mint: PublicKey;
  let state: PublicKey;
  let userTokenAccount: PublicKey;
  let user = Keypair.generate();

  before(async () => {
    // Airdrop SOL to user
    const signature = await provider.connection.requestAirdrop(
      user.publicKey,
      2 * anchor.web3.LAMPORTS_PER_SOL
    );
    await provider.connection.confirmTransaction(signature);

    // Create mint
    mint = await createMint(
      provider.connection,
      authority.payer,
      authority.publicKey,
      null,
      9
    );

    // Create token account for user
    userTokenAccount = await createAccount(
      provider.connection,
      user,
      mint,
      user.publicKey
    );

    // Mint 1M tokens to user (for testing)
    await mintTo(
      provider.connection,
      authority.payer,
      mint,
      userTokenAccount,
      authority.publicKey,
      1_000_000_000_000_000 // 1M tokens with 9 decimals
    );

    // Initialize program
    [state] = PublicKey.findProgramAddressSync(
      [Buffer.from("VERIDICUS_state")],
      program.programId
    );

    await program.methods
      .initialize()
      .accounts({
        state: state,
        authority: authority.publicKey,
        systemProgram: SystemProgram.programId,
      })
      .rpc();
  });

  it("Initializes program correctly", async () => {
    const stateAccount = await program.account.VERIDICUSState.fetch(state);
    
    expect(stateAccount.authority.toString()).to.equal(authority.publicKey.toString());
    expect(stateAccount.totalSupply.toNumber()).to.equal(1_000_000_000_000_000);
    expect(stateAccount.totalBurned.toNumber()).to.equal(0);
    expect(stateAccount.totalJobs.toNumber()).to.equal(0);
  });

  it("Executes quantum job and burns tokens", async () => {
    const beforeBalance = await provider.connection.getTokenAccountBalance(userTokenAccount);
    const beforeBurned = (await program.account.VERIDICUSState.fetch(state)).totalBurned;

    // Get user state PDA
    const [userState] = PublicKey.findProgramAddressSync(
      [Buffer.from("user_state"), user.publicKey.toBuffer()],
      program.programId
    );

    // Execute job: 10 qubits, ZkmlProof (type 1)
    // Note: Price feed is required but using placeholder for now
    // In production, use actual Pyth price feed account
    await program.methods
      .executeQuantumJob(new anchor.BN(10), new anchor.BN(1))
      .accounts({
        state: state,
        userState: userState,
        user: user.publicKey,
        mint: mint,
        userTokenAccount: userTokenAccount,
        priceFeed: SystemProgram.programId, // Placeholder - use actual Pyth feed in production
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([user])
      .rpc();

    const afterBalance = await provider.connection.getTokenAccountBalance(userTokenAccount);
    const afterBurned = (await program.account.VERIDICUSState.fetch(state)).totalBurned;

    // Note: With oracle-based burns, exact amount depends on SOL price
    // For testing, we verify burn occurred but amount may vary
    // In production, burns are pegged to USD value
    
    expect(beforeBurned.toNumber() + expectedBurn).to.equal(afterBurned.toNumber());
    expect(beforeBalance.value.amount).to.equal(
      (afterBalance.value.amount + expectedBurn).toString()
    );
  });

  it("Stakes VERIDICUS for fee discounts", async () => {
    const stakeAmount = 1_000_000_000_000; // 1K VTS

    // Get staking PDA
    const [stakingPda] = PublicKey.findProgramAddressSync(
      [Buffer.from("staking"), user.publicKey.toBuffer()],
      program.programId
    );

    const [stakingAccount] = PublicKey.findProgramAddressSync(
      [Buffer.from("staking"), user.publicKey.toBuffer()],
      program.programId
    );

    await program.methods
      .stakeVERIDICUS(new anchor.BN(stakeAmount))
      .accounts({
        staking: stakingPda,
        user: user.publicKey,
        userTokenAccount: userTokenAccount,
        stakingAccount: stakingAccount,
        tokenProgram: TOKEN_PROGRAM_ID,
        systemProgram: SystemProgram.programId,
      })
      .signers([user])
      .rpc();

    const stakingData = await program.account.staking.fetch(stakingPda);
    expect(stakingData.amount.toNumber()).to.equal(stakeAmount);

    // Check fee discount
    const discount = await program.methods
      .getFeeDiscount()
      .accounts({
        staking: stakingPda,
        user: user.publicKey,
      })
      .view();

    expect(discount).to.equal(20); // 20% discount for 1K VTS
  });

  it("Calculates dynamic burn correctly", async () => {
    const stateAccount = await program.account.VERIDICUSState.fetch(state);
    const initialJobs = stateAccount.totalJobs.toNumber();

    // Test different job types and qubits
    const testCases = [
      { qubits: 5, jobType: 0, expected: 2 },   // CircuitOptimize: (1+1)*1 = 2
      { qubits: 10, jobType: 1, expected: 6 },   // ZkmlProof: (1+2)*2 = 6
      { qubits: 20, jobType: 2, expected: 18 },  // AnomalyDetect: (1+5)*3 = 18
      { qubits: 20, jobType: 3, expected: 30 },  // SecurityAudit: (1+5)*5 = 30
    ];

    for (const test of testCases) {
      const beforeBurned = (await program.account.VERIDICUSState.fetch(state)).totalBurned;
      
      // Get user state PDA
      const [userState] = PublicKey.findProgramAddressSync(
        [Buffer.from("user_state"), user.publicKey.toBuffer()],
        program.programId
      );

      await program.methods
        .executeQuantumJob(new anchor.BN(test.qubits), new anchor.BN(test.jobType))
        .accounts({
          state: state,
          userState: userState,
          user: user.publicKey,
          mint: mint,
          userTokenAccount: userTokenAccount,
          priceFeed: SystemProgram.programId, // Placeholder
          tokenProgram: TOKEN_PROGRAM_ID,
          systemProgram: SystemProgram.programId,
        })
        .signers([user])
        .rpc();

      const afterBurned = (await program.account.VERIDICUSState.fetch(state)).totalBurned;
      const actualBurn = afterBurned.toNumber() - beforeBurned.toNumber();
      const expectedBurn = test.expected * 1_000_000_000; // Convert to 9 decimals

      expect(actualBurn).to.equal(expectedBurn);
    }

    const finalJobs = (await program.account.VERIDICUSState.fetch(state)).totalJobs.toNumber();
    expect(finalJobs).to.equal(initialJobs + testCases.length);
  });
});

