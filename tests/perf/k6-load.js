import http from "k6/http";
import { check, sleep } from "k6";

const BASE = __ENV.BASE_URL || "http://localhost:8000";
const TOKEN = __ENV.AUTH || "";

const headers = TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {};

export const options = {
  thresholds: {
    http_req_duration: ["p(99)<200"], // target p99 < 200ms
    http_req_failed: ["rate<0.01"],
  },
  scenarios: {
    ramp: {
      executor: "ramping-vus",
      startVUs: 0,
      stages: [
        { duration: "2m", target: 100 },
        { duration: "5m", target: 100 },
        { duration: "1m", target: 0 },
      ],
      exec: "flow",
    },
    spike: {
      executor: "per-vu-iterations",
      vus: 500,
      iterations: 1,
      startTime: "9m",
      exec: "flow",
    },
  },
};

export function flow() {
  // Adjust endpoints to your staging deployment; bundle is public, graphql may require auth.
  check(http.get(`${BASE}/vault/share/demo-token/bundle`, { headers }), {
    "bundle 200": (r) => r.status === 200 || r.status === 404, // 404 acceptable if token missing
  });
  check(
    http.post(
      `${BASE}/graphql`,
      JSON.stringify({ query: "{ search(query: \"test\", topK: 3) { id } }" }),
      { headers: { ...headers, "Content-Type": "application/json" } }
    ),
    { "graphql ok": (r) => r.status === 200 }
  );
  sleep(1);
}

