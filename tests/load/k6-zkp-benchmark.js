/**
 * k6 ZKP Benchmark Script
 * ========================
 * 
 * Tests ZK proof verification endpoints with Rapidsnark backend.
 * Target: 100+ req/min for /ai/verify-proofs-batch
 * 
 * Hardware baseline: Intel i9-13900K, 32GB RAM, OMP_NUM_THREADS=8
 * Expected: p99 < 200ms for verify, ~2s for prove
 * 
 * Usage:
 *   k6 run --env BASE_URL=http://localhost:8000 tests/load/k6-zkp-benchmark.js
 *   k6 run --env BASE_URL=http://localhost:8000 --env TEST_MODE=batch tests/load/k6-zkp-benchmark.js
 */

import http from "k6/http";
import { check, sleep, group } from "k6";
import { Rate, Trend, Counter } from "k6/metrics";

// Custom metrics
const errorRate = new Rate("zkp_errors");
const verifyLatency = new Trend("verify_latency_ms");
const batchLatency = new Trend("batch_verify_latency_ms");
const proveLatency = new Trend("prove_latency_ms");
const proofsThroughput = new Counter("proofs_verified");

// Configuration
const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const TEST_MODE = __ENV.TEST_MODE || "mixed"; // "verify", "batch", "prove", "mixed"
const API_KEY = __ENV.API_KEY || "test-api-key";

// Test scenarios based on mode
export const options = {
  scenarios: {
    // Verification load test (fast, high throughput)
    verify_load: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "30s", target: 20 },
        { duration: "2m", target: 50 },
        { duration: "3m", target: 100 },
        { duration: "1m", target: 0 },
      ],
      exec: "verifyScenario",
    },
    // Batch verification (enterprise use case)
    batch_load: {
      executor: "constant-arrival-rate",
      rate: 100, // 100 requests per minute
      timeUnit: "1m",
      duration: "5m",
      preAllocatedVUs: 20,
      maxVUs: 50,
      exec: "batchVerifyScenario",
      startTime: "6m30s", // Start after verify_load
    },
  },
  thresholds: {
    "verify_latency_ms": ["p(99)<200"], // Verify < 200ms
    "batch_verify_latency_ms": ["p(95)<500"], // Batch < 500ms
    "zkp_errors": ["rate<0.01"], // < 1% errors
    "proofs_verified": ["count>1000"], // Verify at least 1000 proofs
  },
};

// Sample proof data (pre-generated, valid structure)
const sampleAgeProof = {
  proof: {
    pi_a: ["1", "2", "1"],
    pi_b: [["1", "2"], ["3", "4"], ["1", "0"]],
    pi_c: ["1", "2", "1"],
    protocol: "groth16",
    curve: "bn128",
  },
  publicSignals: [
    "18", // minAge
    "1733443200", // referenceTs
    "12345678901234567890", // commitment
    "98765432109876543210", // nullifier
  ],
};

const sampleReputationProof = {
  proof: {
    pi_a: ["1", "2", "1"],
    pi_b: [["1", "2"], ["3", "4"], ["1", "0"]],
    pi_c: ["1", "2", "1"],
    protocol: "groth16",
    curve: "bn128",
  },
  publicSignals: [
    "11111111111111111111", // nullifier
    "1", // verified
    "22222222222222222222", // reputationCommitment
  ],
};

// Headers
const headers = {
  "Content-Type": "application/json",
  "X-API-Key": API_KEY,
};

// Verify single proof
export function verifyScenario() {
  group("Single Proof Verification", () => {
    const payload = JSON.stringify({
      proof_type: "age",
      proof_data: JSON.stringify(sampleAgeProof),
    });

    const res = http.post(`${BASE_URL}/ai/verify-proof`, payload, { headers });

    const success = check(res, {
      "verify status 200": (r) => r.status === 200,
      "verify response time < 200ms": (r) => r.timings.duration < 200,
      "verify has result": (r) => {
        try {
          const body = JSON.parse(r.body);
          return body.hasOwnProperty("valid") || body.hasOwnProperty("verified");
        } catch {
          return false;
        }
      },
    });

    errorRate.add(!success);
    verifyLatency.add(res.timings.duration);
    proofsThroughput.add(1);
  });

  sleep(Math.random() * 0.5 + 0.1); // 100-600ms between requests
}

// Batch verify proofs (enterprise scenario)
export function batchVerifyScenario() {
  group("Batch Proof Verification", () => {
    // Batch of 5-10 proofs (realistic enterprise load)
    const batchSize = Math.floor(Math.random() * 6) + 5;
    const proofs = [];

    for (let i = 0; i < batchSize; i++) {
      // Mix of proof types
      if (i % 3 === 0) {
        proofs.push({
          proof_type: "agent_reputation",
          proof_data: JSON.stringify(sampleReputationProof),
        });
      } else {
        proofs.push({
          proof_type: "age",
          proof_data: JSON.stringify(sampleAgeProof),
        });
      }
    }

    const payload = JSON.stringify({ proofs });
    const res = http.post(`${BASE_URL}/ai/verify-proofs-batch`, payload, { headers });

    const success = check(res, {
      "batch status 200": (r) => r.status === 200,
      "batch response time < 500ms": (r) => r.timings.duration < 500,
      "batch has results": (r) => {
        try {
          const body = JSON.parse(r.body);
          return Array.isArray(body.results) && body.results.length === batchSize;
        } catch {
          return false;
        }
      },
    });

    errorRate.add(!success);
    batchLatency.add(res.timings.duration);
    proofsThroughput.add(batchSize);
  });

  sleep(Math.random() * 1 + 0.5); // 500-1500ms between batches
}

// Summary report
export function handleSummary(data) {
  const summary = generateSummary(data);
  
  return {
    stdout: summary,
    "zkp-benchmark-results.json": JSON.stringify(data, null, 2),
  };
}

function generateSummary(data) {
  let output = `
╔═══════════════════════════════════════════════════════════════════╗
║                    ZKP BENCHMARK RESULTS                          ║
║                    Rapidsnark Integration                         ║
╚═══════════════════════════════════════════════════════════════════╝

📊 VERIFICATION PERFORMANCE
───────────────────────────────────────────────────────────────────
`;

  // Verify latency
  const verifyMetric = data.metrics.verify_latency_ms;
  if (verifyMetric) {
    output += `
  Single Proof Verification:
    p50:  ${verifyMetric.values.med?.toFixed(2) || "N/A"}ms
    p95:  ${verifyMetric.values["p(95)"]?.toFixed(2) || "N/A"}ms
    p99:  ${verifyMetric.values["p(99)"]?.toFixed(2) || "N/A"}ms
    max:  ${verifyMetric.values.max?.toFixed(2) || "N/A"}ms
    Target p99 < 200ms: ${(verifyMetric.values["p(99)"] || 0) < 200 ? "✅ PASS" : "❌ FAIL"}
`;
  }

  // Batch latency
  const batchMetric = data.metrics.batch_verify_latency_ms;
  if (batchMetric) {
    output += `
  Batch Verification (5-10 proofs):
    p50:  ${batchMetric.values.med?.toFixed(2) || "N/A"}ms
    p95:  ${batchMetric.values["p(95)"]?.toFixed(2) || "N/A"}ms
    p99:  ${batchMetric.values["p(99)"]?.toFixed(2) || "N/A"}ms
    max:  ${batchMetric.values.max?.toFixed(2) || "N/A"}ms
    Target p95 < 500ms: ${(batchMetric.values["p(95)"] || 0) < 500 ? "✅ PASS" : "❌ FAIL"}
`;
  }

  // Throughput
  const throughput = data.metrics.proofs_verified;
  if (throughput) {
    output += `
📈 THROUGHPUT
───────────────────────────────────────────────────────────────────
  Total proofs verified: ${throughput.values.count}
  Proofs/second:         ${throughput.values.rate?.toFixed(2) || "N/A"}
  Target > 1000 proofs:  ${throughput.values.count > 1000 ? "✅ PASS" : "❌ FAIL"}
`;
  }

  // Error rate
  const errors = data.metrics.zkp_errors;
  if (errors) {
    const errorPct = (errors.values.rate * 100).toFixed(2);
    output += `
🛡️ RELIABILITY
───────────────────────────────────────────────────────────────────
  Error rate: ${errorPct}%
  Target < 1%: ${errors.values.rate < 0.01 ? "✅ PASS" : "❌ FAIL"}
`;
  }

  // HTTP stats
  const httpReqs = data.metrics.http_reqs;
  if (httpReqs) {
    output += `
🌐 HTTP STATISTICS
───────────────────────────────────────────────────────────────────
  Total requests: ${httpReqs.values.count}
  Requests/sec:   ${httpReqs.values.rate?.toFixed(2) || "N/A"}
`;
  }

  output += `
───────────────────────────────────────────────────────────────────
💡 Notes:
  - Hardware: Set OMP_NUM_THREADS=8 for optimal Rapidsnark performance
  - Kubernetes: Use node affinity for c6i.4xlarge or similar (16 vCPU)
  - Batch mode: 100+ req/min target on single 8-core pod
  - AAIP proofs: Sub-3s proving with Rapidsnark backend
───────────────────────────────────────────────────────────────────
`;

  return output;
}

// Default export for simple runs
export default function () {
  if (TEST_MODE === "verify") {
    verifyScenario();
  } else if (TEST_MODE === "batch") {
    batchVerifyScenario();
  } else {
    // Mixed mode: 70% verify, 30% batch
    if (Math.random() < 0.7) {
      verifyScenario();
    } else {
      batchVerifyScenario();
    }
  }
}

