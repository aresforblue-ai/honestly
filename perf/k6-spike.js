import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.SHARE_TOKEN || 'demo-token';
const CIRCUIT = __ENV.CIRCUIT || 'age';

const bundleTrend = new Trend('bundle_spike');
const vkeyTrend = new Trend('vkey_spike');
const capsTrend = new Trend('caps_spike');

export const options = {
  stages: [
    { duration: '10s', target: 10 },   // warmup
    { duration: '10s', target: 500 },  // spike to 500 VUs
    { duration: '2m', target: 500 },   // hold
    { duration: '30s', target: 0 },    // ramp down
  ],
  thresholds: {
    bundle_spike: ['p(99)<200'],
    vkey_spike: ['p(99)<200'],
    caps_spike: ['p(99)<200'],
    http_req_failed: ['rate<0.02'],
  },
};

function getBundle() {
  const res = http.get(`${BASE}/vault/share/${TOKEN}/bundle`);
  bundleTrend.add(res.timings.duration);
  check(res, { 'bundle: status 200': (r) => r.status === 200 || r.status === 429 });
}

function getVkey() {
  const res = http.get(`${BASE}/zkp/artifacts/${CIRCUIT}/verification_key.json`);
  vkeyTrend.add(res.timings.duration);
  check(res, { 'vkey: status 200': (r) => r.status === 200 || r.status === 429 });
}

function getCaps() {
  const res = http.get(`${BASE}/capabilities`);
  capsTrend.add(res.timings.duration);
  check(res, { 'caps: status 200': (r) => r.status === 200 || r.status === 429 });
}

export default function () {
  const r = Math.random();
  if (r < 0.4) {
    getBundle();
  } else if (r < 0.7) {
    getVkey();
  } else {
    getCaps();
  }
  sleep(0.1);
}

