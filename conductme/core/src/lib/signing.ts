// Cryptographic signing of user actions (EIP-712 typed data).
// Tie to Trust Bridge identity (Semaphore proof) for identity-bound logs.
import { ethers, TypedDataField, TypedDataDomain } from "ethers";

const domain: TypedDataDomain = {
  name: "ConductMe",
  version: "1",
  chainId: 1, // TODO: make dynamic
  verifyingContract: "0x0000000000000000000000000000000000000000", // TODO: set if on-chain
};

const types: Record<string, TypedDataField[]> = {
  ActionLog: [
    { name: "action", type: "string" },
    { name: "modelId", type: "string" },
    { name: "timestamp", type: "uint256" },
    { name: "humanProof", type: "bytes" }, // Semaphore proof blob
  ],
};

export type ActionLog = {
  action: string;
  modelId: string;
  timestamp: number;
  humanProof: string;
};

export async function signAction(signer: ethers.Signer, action: ActionLog): Promise<string> {
  const message = { ...action, timestamp: action.timestamp.toString() };
  return signer.signTypedData(domain, types, message);
}

