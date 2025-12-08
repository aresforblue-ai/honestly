/**
 * Spike Test with k6
 * 
 * Test: Jump from 10 to 500 users instantly
 * Goal: Verify rate limiting and connection pooling handle the shock
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const responseTime = new Trend('response_time');

export const options = {
  stages: [
    { duration: '30s', target: 10 },   // Start with 10 users
    { duration: '1s', target: 500 },    // SPIKE to 500 users instantly
    { duration: '2m', target: 500 },    // Hold spike for 2 minutes
    { duration: '1m', target: 100 },     // Ramp down to 100
    { duration: '1m', target: 0 },      // Ramp down to 0
  ],
  thresholds: {
    http_req_duration: ['p(99)<500'],   // Allow higher latency during spike
    http_req_failed: ['rate<0.05'],     // Allow 5% error rate during spike
    errors: ['rate<0.05'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

export default function() {
  // Test the most critical endpoint during spike
  const res = http.get(`${BASE_URL}/vault/share/test_token/bundle`, {
    headers: {
      'User-Agent': 'k6-spike-test',
    },
  });
  
  const success = check(res, {
    'status is 200, 404, or 429': (r) => [200, 404, 429].includes(r.status),
    'response time acceptable': (r) => r.timings.duration < 1000, // 1s during spike
  });
  
  if (!success && ![404, 429].includes(res.status)) {
    errorRate.add(1);
  }
  
  responseTime.add(res.timings.duration);
  
  sleep(0.1); // Minimal sleep during spike
}


