// api.js — thin fetch wrappers around the Flask backend endpoints.
// In dev, Vite's proxy (see vite.config.js) forwards /api/* to Flask on :5000.
// In production, set VITE_API_BASE to the deployed backend URL.

const API_BASE = import.meta.env.VITE_API_BASE || '';

async function getJSON(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    throw new Error(`API error ${res.status} for ${path}`);
  }
  return res.json();
}

export function fetchPrices({ start, end, freq = 'D' } = {}) {
  const params = new URLSearchParams();
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  if (freq) params.set('freq', freq);
  return getJSON(`/api/prices?${params.toString()}`);
}

export function fetchEvents({ category, start, end } = {}) {
  const params = new URLSearchParams();
  if (category) params.set('category', category);
  if (start) params.set('start', start);
  if (end) params.set('end', end);
  return getJSON(`/api/events?${params.toString()}`);
}

export function fetchChangepoints() {
  return getJSON('/api/changepoints');
}

export function fetchMetrics() {
  return getJSON('/api/metrics');
}
