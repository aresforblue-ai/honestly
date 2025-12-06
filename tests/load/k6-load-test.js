/**
 * k6 Load Testing Script
 * Tests: Ramp-up to 100 concurrent users, spike test to 500 users
 * Target: 99th percentile < 200ms
 */
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const errorRate = new Rate('errors');
const p95Latency = new Trend('p95_latency');
const p99Latency = new Trend('p99_latency');

// Configuration
export const options = {
  stages: [
    // Warm-up
    { duration: '30s', target: 10 },
    // Ramp-up to 100 users
    { duration: '2m', target: 100 },
    // Hold at 100 users for 5 minutes
    { duration: '5m', target: 100 },
    // Spike test: jump to 500 users instantly
    { duration: '1s', target: 500 },
    { duration: '2m', target: 500 },
    // Cool down
    { duration: '1m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(95)<200', 'p(99)<200'], // 95th and 99th percentile < 200ms
    http_req_failed: ['rate<0.01'], // Error rate < 1%
    errors: ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8000';

// Test scenarios
const scenarios = {
  health_check: {
    weight: 20,
    func: () => {
      const res = http.get(`${BASE_URL}/health`);
      check(res, {
        'health check status 200': (r) => r.status === 200,
        'health check response time < 200ms': (r) => r.timings.duration < 200,
      });
      errorRate.add(res.status !== 200);
      p95Latency.add(res.timings.duration);
      p99Latency.add(res.timings.duration);
    },
  },
  share_bundle: {
    weight: 30,
    func: () => {
      // Use a test token (replace with real token in production)
      const token = __ENV.TEST_TOKEN || 'test-token-123';
      const res = http.get(`${BASE_URL}/vault/share/${token}/bundle`);
      check(res, {
        'share bundle status 200 or 404': (r) => r.status === 200 || r.status === 404,
        'share bundle response time < 200ms': (r) => r.timings.duration < 200,
      });
      errorRate.add(res.status >= 500);
      p95Latency.add(res.timings.duration);
      p99Latency.add(res.timings.duration);
    },
  },
  graphql_query: {
    weight: 25,
    func: () => {
      const query = {
        query: `
          query {
            myDocuments {
              id
              documentType
              hash
            }
          }
        `,
      };
      const res = http.post(
        `${BASE_URL}/graphql`,
        JSON.stringify(query),
        { headers: { 'Content-Type': 'application/json' } }
      );
      check(res, {
        'graphql status 200': (r) => r.status === 200,
        'graphql response time < 200ms': (r) => r.timings.duration < 200,
      });
      errorRate.add(res.status >= 500);
      p95Latency.add(res.timings.duration);
      p99Latency.add(res.timings.duration);
    },
  },
  metrics_endpoint: {
    weight: 15,
    func: () => {
      const res = http.get(`${BASE_URL}/health/metrics`);
      check(res, {
        'metrics status 200': (r) => r.status === 200,
        'metrics response time < 200ms': (r) => r.timings.duration < 200,
      });
      errorRate.add(res.status !== 200);
      p95Latency.add(res.timings.duration);
      p99Latency.add(res.timings.duration);
    },
  },
  readiness_check: {
    weight: 10,
    func: () => {
      const res = http.get(`${BASE_URL}/health/ready`);
      check(res, {
        'readiness status 200 or 503': (r) => r.status === 200 || r.status === 503,
        'readiness response time < 200ms': (r) => r.timings.duration < 200,
      });
      errorRate.add(res.status >= 500 && res.status !== 503);
      p95Latency.add(res.timings.duration);
      p99Latency.add(res.timings.duration);
    },
  },
};

// Weighted random scenario selection
function selectScenario() {
  const totalWeight = Object.values(scenarios).reduce((sum, s) => sum + s.weight, 0);
  let random = Math.random() * totalWeight;
  
  for (const [name, scenario] of Object.entries(scenarios)) {
    random -= scenario.weight;
    if (random <= 0) {
      return scenario.func;
    }
  }
  return scenarios.health_check.func;
}

export default function () {
  const scenario = selectScenario();
  scenario();
  sleep(Math.random() * 2 + 0.5); // Random sleep 0.5-2.5s (realistic user behavior)
}

export function handleSummary(data) {
  return {
    'stdout': textSummary(data, { indent: ' ', enableColors: true }),
    'load-test-results.json': JSON.stringify(data),
  };
}

function textSummary(data, options) {
  const { indent = '', enableColors = false } = options;
  let output = '\n';
  
  output += `${indent}Load Test Results\n`;
  output += `${indent}==================\n\n`;
  
  // Response time percentiles
  const httpReqDuration = data.metrics.http_req_duration;
  if (httpReqDuration) {
    output += `${indent}Response Times:\n`;
    output += `${indent}  p50: ${httpReqDuration.values.p50.toFixed(2)}ms\n`;
    output += `${indent}  p95: ${httpReqDuration.values.p95.toFixed(2)}ms\n`;
    output += `${indent}  p99: ${httpReqDuration.values.p99.toFixed(2)}ms\n`;
    output += `${indent}  max: ${httpReqDuration.values.max.toFixed(2)}ms\n\n`;
    
    // Check if targets met
    const p95Target = httpReqDuration.values.p95 < 200;
    const p99Target = httpReqDuration.values.p99 < 200;
    output += `${indent}Targets:\n`;
    output += `${indent}  p95 < 200ms: ${p95Target ? '✅ PASS' : '❌ FAIL'}\n`;
    output += `${indent}  p99 < 200ms: ${p99Target ? '✅ PASS' : '❌ FAIL'}\n\n`;
  }
  
  // Error rate
  const httpReqFailed = data.metrics.http_req_failed;
  if (httpReqFailed) {
    const errorRate = httpReqFailed.values.rate * 100;
    output += `${indent}Error Rate: ${errorRate.toFixed(2)}%\n`;
    output += `${indent}Target < 1%: ${errorRate < 1 ? '✅ PASS' : '❌ FAIL'}\n\n`;
  }
  
  // Request statistics
  const httpReqs = data.metrics.http_reqs;
  if (httpReqs) {
    output += `${indent}Total Requests: ${httpReqs.values.count}\n`;
    output += `${indent}Requests/sec: ${httpReqs.values.rate.toFixed(2)}\n\n`;
  }
  
  return output;
}


