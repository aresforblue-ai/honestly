import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

const BASE = __ENV.BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.SHARE_TOKEN || 'demo-token';
const CIRCUIT = __ENV.CIRCUIT || 'age';

const bundleTrend = new Trend('bundle');
const vkeyTrend = new Trend('vkey');
const capsTrend = new Trend('caps');

export const options = {
  stages: [
    { duration: '1m', target: 100 }, // ramp to 100 VUs
    { duration: '5m', target: 100 }, // hold
    { duration: '1m', target: 0 },   // ramp down
  ],
  thresholds: {
    bundle: ['p(99)<200'],
    vkey: ['p(99)<200'],
    caps: ['p(99)<200'],
    http_req_failed: ['rate<0.01'],
  },
};

function getBundle() {
  const res = http.get(`${BASE}/vault/share/${TOKEN}/bundle`);
  bundleTrend.add(res.timings.duration);
  check(res, { 'bundle: status 200': (r) => r.status === 200 });
}

function getVkey() {
  const res = http.get(`${BASE}/zkp/artifacts/${CIRCUIT}/verification_key.json`);
  vkeyTrend.add(res.timings.duration);
  check(res, { 'vkey: status 200': (r) => r.status === 200 });
}

function getCaps() {
  const res = http.get(`${BASE}/capabilities`);
  capsTrend.add(res.timings.duration);
  check(res, { 'caps: status 200': (r) => r.status === 200 });
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
  sleep(0.2);
}

