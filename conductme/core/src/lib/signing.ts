// Cryptographic signing of user actions (EIP-712 typed data).
// Tie to Trust Bridge identity (Semaphore proof) for identity-bound logs.
import { ethers, TypedDataField, TypedDataDomain } from "ethers";

const DEFAULT_CHAIN_ID = Number(process.env.NEXT_PUBLIC_CHAIN_ID || "1");
const DEFAULT_CONTRACT = process.env.NEXT_PUBLIC_VERIFYING_CONTRACT || "0x0000000000000000000000000000000000000000";

const baseDomain: TypedDataDomain = {
  name: "ConductMe",
  version: "1",
  chainId: DEFAULT_CHAIN_ID,
  verifyingContract: DEFAULT_CONTRACT,
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

export function getSigningDomain(overrides?: Partial<TypedDataDomain>): TypedDataDomain {
  return {
    ...baseDomain,
    ...overrides,
  };
}

export async function signAction(
  signer: ethers.Signer,
  action: ActionLog,
  overrides?: Partial<TypedDataDomain>
): Promise<string> {
  const message = { ...action, timestamp: action.timestamp.toString() };
  const domain = getSigningDomain(overrides);
  return signer.signTypedData(domain, types, message);
}

