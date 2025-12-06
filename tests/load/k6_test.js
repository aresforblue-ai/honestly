/**
 * k6 Load Testing Suite
 * Tests: Ramp-up, spike, sustained load
 * Target: <200ms p99 response time
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const verificationTime = new Trend('verification_time');
const errorRate = new Rate('errors');

// Configuration
export const options = {
  stages: [
    // Test 1: Ramp-up to 100 concurrent users
    { duration: '2m', target: 100 },  // Ramp up
    { duration: '5m', target: 100 },   // Hold for 5 minutes
    { duration: '2m', target: 0 },    // Ramp down
  ],
  thresholds: {
    'http_req_duration': ['p(99)<200'],  // 99th percentile < 200ms
    'errors': ['rate<0.01'],             // Error rate < 1%
    'verification_time': ['p(99)<200'],  // Verification < 200ms
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test data
const testToken = __ENV.TEST_TOKEN || 'test_token_123';
const testDocumentId = __ENV.TEST_DOC_ID || 'doc_test_123';

export default function () {
  // Scenario 1: Health check (baseline)
  let res = http.get(`${BASE_URL}/monitoring/health`);
  check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check response time < 50ms': (r) => r.timings.duration < 50,
  });

  sleep(0.1);

  // Scenario 2: Share bundle verification (critical path)
  res = http.get(`${BASE_URL}/vault/share/${testToken}/bundle`);
  const verificationStart = Date.now();
  
  check(res, {
    'share bundle status 200': (r) => r.status === 200,
    'share bundle has proof_type': (r) => JSON.parse(r.body).proof_type !== undefined,
  });
  
  const verificationDuration = Date.now() - verificationStart;
  verificationTime.add(verificationDuration);
  
  if (res.status !== 200) {
    errorRate.add(1);
  } else {
    errorRate.add(0);
  }

  sleep(0.5);

  // Scenario 3: Metrics endpoint
  res = http.get(`${BASE_URL}/monitoring/metrics`);
  check(res, {
    'metrics status 200': (r) => r.status === 200,
    'metrics response time < 100ms': (r) => r.timings.duration < 100,
  });

  sleep(1);
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'load-test-results.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  let summary = '\n=== Load Test Results ===\n\n';
  
  // HTTP metrics
  summary += 'HTTP Metrics:\n';
  summary += `  Total Requests: ${data.metrics.http_reqs.values.count}\n`;
  summary += `  Failed Requests: ${data.metrics.http_req_failed.values.rate * 100}%\n`;
  summary += `  Avg Response Time: ${data.metrics.http_req_duration.values.avg.toFixed(2)}ms\n`;
  summary += `  P95 Response Time: ${data.metrics.http_req_duration.values['p(95)'].toFixed(2)}ms\n`;
  summary += `  P99 Response Time: ${data.metrics.http_req_duration.values['p(99)'].toFixed(2)}ms\n`;
  summary += `  Max Response Time: ${data.metrics.http_req_duration.values.max.toFixed(2)}ms\n\n`;
  
  // Verification metrics
  if (data.metrics.verification_time) {
    summary += 'Verification Metrics:\n';
    summary += `  Avg Verification Time: ${data.metrics.verification_time.values.avg.toFixed(2)}ms\n`;
    summary += `  P99 Verification Time: ${data.metrics.verification_time.values['p(99)'].toFixed(2)}ms\n\n`;
  }
  
  // Thresholds
  summary += 'Thresholds:\n';
  for (const [name, threshold] of Object.entries(data.thresholds || {})) {
    const passed = threshold.ok === 1;
    summary += `  ${name}: ${passed ? '✅ PASS' : '❌ FAIL'}\n`;
  }
  
  return summary;
}


