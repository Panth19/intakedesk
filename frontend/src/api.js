async function req(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(opts.headers || {}) },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json();
}

export const api = {
  overview: () => req("/api/overview"),
  catalog: () => req("/api/catalog"),
  jobs: (status) => req(status ? `/api/jobs?status=${status}` : "/api/jobs"),
  job: (id) => req(`/api/jobs/${id}`),
  ingest: (body) => req("/api/ingest", { method: "POST", body: JSON.stringify(body) }),
  review: (id, body) => req(`/api/jobs/${id}/review`, { method: "POST", body: JSON.stringify(body) }),
  quotes: () => req("/api/quotes"),
  setQuoteState: (id, state) =>
    req(`/api/quotes/${id}/state`, { method: "POST", body: JSON.stringify({ state }) }),
  evaluation: () => req("/api/evaluation"),
  audit: () => req("/api/audit"),
  samples: () => req("/api/samples"),
  workflow: () => req("/api/workflow"),
  llmSettings: () => req("/api/settings/llm"),
  saveLlm: (body) => req("/api/settings/llm", { method: "POST", body: JSON.stringify(body) }),
  testLlm: () => req("/api/settings/llm/test", { method: "POST", body: "{}" }),
};
