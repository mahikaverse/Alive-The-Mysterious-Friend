// Alive – k6 load test
//
// Usage:
//   k6 run scripts/load_test.js
//
// Overrides:
//   k6 run --vus 10 --duration 30s scripts/load_test.js
//   k6 run -e BASE_URL=http://localhost:8000 scripts/load_test.js
//
// Requires: k6 installed (https://k6.io) and the Alive server running.

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate } from "k6/metrics";

const BASE_URL = __ENV.BASE_URL || "http://localhost:8000";
const API_KEY = __ENV.API_KEY || "";

const headers = {
  "Content-Type": "application/json",
};
if (API_KEY) {
  headers["Authorization"] = `Bearer ${API_KEY}`;
}

const errorRate = new Rate("failed_requests");

export const options = {
  stages: [
    { duration: "10s", target: 5 },
    { duration: "20s", target: 20 },
    { duration: "10s", target: 0 },
  ],
  thresholds: {
    http_req_duration: ["p(95)<2000"],
    failed_requests: ["rate<0.01"],
  },
};

export function setup() {
  const res = http.get(`${BASE_URL}/health`);
  check(res, {
    "health endpoint responds": (r) => r.status === 200,
  });
}

export default function () {
  const payload = JSON.stringify({
    model: "alive-v1",
    messages: [
      {
        role: "user",
        content: "Hello! This is a load test message. Please respond briefly.",
      },
    ],
    temperature: 0.7,
    max_tokens: 100,
  });

  const res = http.post(`${BASE_URL}/chat/completions`, payload, {
    headers,
    timeout: "30s",
  });

  errorRate.add(res.status !== 200);

  check(res, {
    "status is 200": (r) => r.status === 200,
    "response is OpenAI-compatible": (r) => {
      if (r.status !== 200) return false;
      const body = r.json();
      return (
        body.object === "chat.completion" &&
        Array.isArray(body.choices) &&
        body.choices.length === 1 &&
        body.choices[0].message.role === "assistant"
      );
    },
  });

  sleep(1);
}
