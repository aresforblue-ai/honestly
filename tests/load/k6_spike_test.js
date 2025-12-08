/**
 * k6 Spike Test
 * Test 2: Instant spike from 10 to 500 users
 * Tests rate limiting and connection pooling resilience
 */
import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const verificationTime = new Trend("verification_time");
const errorRate = new Rate("errors");
const rateLimitHits = new Rate("rate_limit_hits");

export const options = {
  stages: [
    { duration: "1m", target: 10 },   // Baseline: 10 users
    { duration: "10s", target: 500 },  // SPIKE: Instant jump to 500
    { duration: "2m", target: 500 },   // Hold spike
    { duration: "1m", target: 10 },    // Return to baseline
  ],
  thresholds: {
    "http_req_duration": ["p(99)<500"],  // Allow higher during spike
    "errors": ["rate<0.05"],             // Allow 5% errors during spike
    "rate_limit_hits": ["rate<0.1"],     // Rate limiting should catch most
  },
};

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const testToken = __ENV.TEST_TOKEN || "test_token_123";

export default function () {
  // Test rate-limited endpoint
  const res = http.get(`${BASE_URL}/vault/share/${testToken}/bundle`);
  
  const verificationStart = Date.now();
  const verificationDuration = Date.now() - verificationStart;
  verificationTime.add(verificationDuration);
  
  // Check for rate limiting
  if (res.status === 429) {
    rateLimitHits.add(1);
    check(res, {
      "rate limit has retry-after header": (r) => r.headers["Retry-After"] !== undefined,
    });
  } else {
    rateLimitHits.add(0);
    check(res, {
      "share bundle status 200": (r) => r.status === 200,
    });
  }
  
  if (res.status >= 400 && res.status !== 429) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }
  
  sleep(0.1);
}


