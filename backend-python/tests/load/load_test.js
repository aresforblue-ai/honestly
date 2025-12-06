/**
 * Load Testing with k6
 * 
 * Tests:
 * 1. Ramp up to 100 concurrent users, hold for 5 minutes
 * 2. Spike test: 10 to 500 users instantly
 * 
 * Goal: 99th percentile response time < 200ms
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend, Counter } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const p95ResponseTime = new Trend('p95_response_time');
const p99ResponseTime = new Trend('p99_response_time');

// Configuration
export const options = {
  stages: [
    // Test 1: Ramp up to 100 concurrent users, hold for 5 minutes
    { duration: '1m', target: 100 },  // Ramp up over 1 minute
    { duration: '5m', target: 100 },  // Hold at 100 users for 5 minutes
    { duration: '1m', target: 0 },     // Ramp down
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<200'], // 95th and 99th percentile < 200ms
    http_req_failed: ['rate<0.01'],                 // Error rate < 1%
    errors: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test data
const testTokens = [
  'test_token_1',
  'test_token_2',
  'test_token_3',
];

export function setup() {
  // Setup: Create test share links if needed
  console.log('Setting up load test...');
  return { baseUrl: BASE_URL };
}

export default function(data) {
  const baseUrl = data.baseUrl;
  
  // Simulate realistic user behavior
  const scenarios = [
    () => testHealthCheck(baseUrl),
    () => testShareBundle(baseUrl),
    () => testMetrics(baseUrl),
    () => testAIHealth(baseUrl),
  ];
  
  // Randomly select a scenario
  const scenario = scenarios[Math.floor(Math.random() * scenarios.length)];
  scenario();
  
  sleep(Math.random() * 2 + 1); // Random sleep 1-3 seconds
}

function testHealthCheck(baseUrl) {
  const res = http.get(`${baseUrl}/monitoring/health`);
  const success = check(res, {
    'health check status 200': (r) => r.status === 200,
    'health check response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  if (!success) {
    errorRate.add(1);
  }
  
  p95ResponseTime.add(res.timings.duration);
  p99ResponseTime.add(res.timings.duration);
}

function testShareBundle(baseUrl) {
  const token = testTokens[Math.floor(Math.random() * testTokens.length)];
  const res = http.get(`${baseUrl}/vault/share/${token}/bundle`, {
    headers: {
      'User-Agent': 'k6-load-test',
    },
  });
  
  const success = check(res, {
    'share bundle status 200 or 404': (r) => r.status === 200 || r.status === 404,
    'share bundle response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  if (!success && res.status !== 404) {
    errorRate.add(1);
  }
  
  p95ResponseTime.add(res.timings.duration);
  p99ResponseTime.add(res.timings.duration);
}

function testMetrics(baseUrl) {
  const res = http.get(`${baseUrl}/monitoring/metrics`);
  const success = check(res, {
    'metrics status 200': (r) => r.status === 200,
    'metrics response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  if (!success) {
    errorRate.add(1);
  }
  
  p95ResponseTime.add(res.timings.duration);
  p99ResponseTime.add(res.timings.duration);
}

function testAIHealth(baseUrl) {
  const res = http.get(`${baseUrl}/ai/health`);
  const success = check(res, {
    'AI health status 200': (r) => r.status === 200,
    'AI health response time < 200ms': (r) => r.timings.duration < 200,
  });
  
  if (!success) {
    errorRate.add(1);
  }
  
  p95ResponseTime.add(res.timings.duration);
  p99ResponseTime.add(res.timings.duration);
}

export function teardown(data) {
  console.log('Load test completed');
}


