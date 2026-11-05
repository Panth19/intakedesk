import { useEffect, useMemo, useState } from "react";
import { api } from "./api";

const NAV = [
  ["overview", "Overview"],
  ["inbox", "Inbox"],
  ["review", "Review queue"],
  ["quotes", "Odoo quotes"],
  ["eval", "Evaluation"],
  ["workflow", "Workflow"],
  ["ingest", "New document"],
  ["settings", "AI settings"],
];

const STATUS = {
  needs_review: ["amber", "review"],
  draft_in_odoo: ["green", "draft quote"],
  quote_sent: ["blue", "sent"],
  confirmed: ["green", "confirmed"],
  rejected: ["red", "rejected"],
  cancelled: ["red", "cancelled"],
  auto_quoted: ["green", "auto"],
};

function Badge({ status }) {
  const [tone, label] = STATUS[status] || ["", status];
  return <span className={`badge ${tone}`}>{label}</span>;
}

function eur(n) {
  return new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" }).format(n || 0);
}

function pct(n) {
  return `${Math.round((n || 0) * 100)}%`;
}

export default function App() {
  const [tab, setTab] = useState("overview");
  const [overview, setOverview] = useState(null);
  const [jobs, setJobs] = useState([]);
  const [quotes, setQuotes] = useState([]);
  const [catalog, setCatalog] = useState({ products: [], partners: [] });
  const [evaluation, setEvaluation] = useState(null);
  const [workflow, setWorkflow] = useState(null);
  const [audit, setAudit] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [llm, setLlm] = useState(null);
  const [err, setErr] = useState("");

  async function refresh() {
    try {
      const [o, j, q, c, e, w, a, l] = await Promise.all([
        api.overview(),
        api.jobs(),
        api.quotes(),
        api.catalog(),
        api.evaluation(),
        api.workflow(),
        api.audit(),
        api.llmSettings(),
      ]);
      setOverview(o);
      setJobs(j);
      setQuotes(q);
      setCatalog(c);
      setEvaluation(e);
      setWorkflow(w);
      setAudit(a);
      setLlm(l);
      setErr("");
    } catch (e) {
      setErr(e.message);
    }
  }

  useEffect(() => {
    refresh();
  }, []);

  const selected = jobs.find((j) => j.id === selectedId) || jobs[0];

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="mark">NF</div>
          <div>
            <h1>IntakeDesk</h1>
            <p>Nutrifill GmbH · Griesheim</p>
          </div>
        </div>
        <nav className="nav">
          {NAV.map(([id, label]) => (
            <button key={id} className={tab === id ? "active" : ""} onClick={() => setTab(id)}>
              {label}
            </button>
          ))}
        </nav>
        <div className="side-meta">
          Working-student ops desk
          <br />
          Orders · Quotes · Purchasing
          <br />
          DE / EN · n8n · Odoo
          <br />
          {llm ? (llm.enabled ? `AI · ${llm.provider}` : "AI off · rules") : ""}
        </div>
      </aside>
      <main className="main">
        {err && <div className="alert">{err}</div>}
        {tab === "overview" && overview && (
          <Overview overview={overview} jobs={jobs} quotes={quotes} audit={audit} evaluation={evaluation} />
        )}
        {tab === "inbox" && (
          <Inbox
            jobs={jobs}
            selected={selected}
            onSelect={setSelectedId}
            quotes={quotes}
          />
        )}
        {tab === "review" && (
          <Review
            jobs={jobs.filter((j) => j.status === "needs_review")}
            catalog={catalog}
            onDone={refresh}
          />
        )}
        {tab === "quotes" && <Quotes quotes={quotes} onChange={refresh} />}
        {tab === "eval" && evaluation && <Eval evaluation={evaluation} />}
        {tab === "workflow" && workflow && <Workflow workflow={workflow} />}
        {tab === "ingest" && (
          <Ingest catalog={catalog} llm={llm} onDone={() => { refresh(); setTab("inbox"); }} />
        )}
        {tab === "settings" && llm && <Settings llm={llm} onSave={refresh} />}
      </main>
    </div>
  );
}

function Overview({ overview, jobs, quotes, audit, evaluation }) {
  return (
    <>
      <div className="page-head">
        <div>
          <h2>Merchandise intake</h2>
          <p>AI extraction of customer emails into Odoo draft quotes. Uncertain cases stay in review.</p>
        </div>
      </div>
      <div className="kpis">
        <div className="kpi">
          <div className="label">Documents</div>
          <div className="value">{overview.documents}</div>
          <div className="hint">seeded DE/EN corpus</div>
        </div>
        <div className="kpi">
          <div className="label">Without review</div>
          <div className="value">{pct(overview.auto_share)}</div>
          <div className="hint">auto draft in Odoo</div>
        </div>
        <div className="kpi">
          <div className="label">Review queue</div>
          <div className="value">{overview.needs_review}</div>
          <div className="hint">needs a person</div>
        </div>
        <div className="kpi">
          <div className="label">SKU recall</div>
          <div className="value">{pct(overview.sku_recall)}</div>
          <div className="hint">vs gold labels</div>
        </div>
        <div className="kpi">
          <div className="label">Cost / doc</div>
          <div className="value">{eur(overview.cost_per_document_eur)}</div>
          <div className="hint">extraction estimate</div>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Latest intake</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Job</th>
                <th>Customer mail</th>
                <th>Status</th>
                <th>Conf.</th>
              </tr>
            </thead>
            <tbody>
              {jobs.slice(0, 8).map((j) => (
                <tr key={j.id}>
                  <td className="mono">{j.id}</td>
                  <td>
                    {j.subject}
                    <div className="muted">{j.from_name}</div>
                  </td>
                  <td>
                    <Badge status={j.status} />
                  </td>
                  <td className="mono">{Math.round((j.extraction?.overall_confidence || 0) * 100)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <h3>Odoo pipeline</h3>
          <p className="muted">Draft quotations waiting to be sent. Volume discount at 30+ units. VAT 19%.</p>
          <table className="table">
            <thead>
              <tr>
                <th>Quote</th>
                <th>Partner</th>
                <th className="right">Total</th>
              </tr>
            </thead>
            <tbody>
              {quotes.slice(0, 6).map((q) => (
                <tr key={q.id}>
                  <td className="mono">{q.id}</td>
                  <td>{q.partner_name}</td>
                  <td className="right mono">{eur(q.amount_total)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div style={{ marginTop: 12 }}>
            <div className="muted">Routing accuracy</div>
            <div className="bar" style={{ marginTop: 6 }}>
              <span style={{ width: pct(evaluation?.routing_accuracy || 0) }} />
            </div>
          </div>
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Audit</h3>
        <table className="table">
          <thead>
            <tr>
              <th>When</th>
              <th>Action</th>
              <th>Detail</th>
            </tr>
          </thead>
          <tbody>
            {audit.slice(0, 6).map((a) => (
              <tr key={a.id}>
                <td className="mono">{a.at.replace("T", " ").replace("Z", "")}</td>
                <td className="mono">{a.action}</td>
                <td>{a.detail}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Inbox({ jobs, selected, onSelect, quotes }) {
  const [filter, setFilter] = useState("all");
  const shown = jobs.filter((j) => filter === "all" || j.status === filter);
  const quote = quotes.find((q) => q.id === selected?.quote_id);

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Inbox</h2>
          <p>n8n drops parsed emails and PDF text here. Extraction runs immediately.</p>
        </div>
      </div>
      <div className="toolbar">
        {["all", "needs_review", "draft_in_odoo", "quote_sent"].map((f) => (
          <button key={f} className={`chip ${filter === f ? "active" : ""}`} onClick={() => setFilter(f)}>
            {f.replaceAll("_", " ")}
          </button>
        ))}
      </div>
      <div className="split">
        <div className="list">
          {shown.map((j) => (
            <button
              key={j.id}
              className={`doc ${selected?.id === j.id ? "selected" : ""}`}
              onClick={() => onSelect(j.id)}
            >
              <div className="top">
                <span className="mono">{j.id}</span>
                <Badge status={j.status} />
              </div>
              <div className="subj">{j.subject}</div>
              <div className="meta">
                {j.from_name} · {j.language?.toUpperCase()} · {j.source}
              </div>
            </button>
          ))}
        </div>
        {selected && (
          <div>
            <div className="paper">
              <h4>
                {selected.from_name} &lt;{selected.from_email}&gt;
              </h4>
              <strong>{selected.subject}</strong>
              <pre style={{ marginTop: 12 }}>{selected.body}</pre>
            </div>
            <div className="card" style={{ marginTop: 12 }}>
              <h3>Extraction</h3>
              <p className="muted">
                Partner {selected.extraction.partner_name || "unknown"} · intent {selected.extraction.intent} ·
                confidence {pct(selected.extraction.overall_confidence)}
              </p>
              {selected.extraction.review_reasons?.length > 0 && (
                <div className="alert">{selected.extraction.review_reasons.join(" · ")}</div>
              )}
              <table className="table">
                <thead>
                  <tr>
                    <th>Raw</th>
                    <th>SKU</th>
                    <th>Qty</th>
                    <th>Conf.</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.extraction.lines.map((ln, i) => (
                    <tr key={i}>
                      <td>{ln.raw}</td>
                      <td className="mono">{ln.sku || "—"}</td>
                      <td>{ln.qty}</td>
                      <td className="mono">{pct(ln.confidence)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {quote && (
              <div className="card" style={{ marginTop: 12 }}>
                <h3>Odoo {quote.id}</h3>
                <p>
                  {quote.partner_name} · {eur(quote.amount_total)} · {quote.state}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </>
  );
}

function Review({ jobs, catalog, onDone }) {
  const [idx, setIdx] = useState(0);
  const job = jobs[idx] || jobs[0];
  const [partnerId, setPartnerId] = useState("");
  const [intent, setIntent] = useState("quote");
  const [lines, setLines] = useState([]);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!job) return;
    setPartnerId(job.extraction.partner_id || "");
    setIntent(job.extraction.intent || "quote");
    setLines(job.extraction.lines.map((ln) => ({ ...ln })));
    setNote("");
  }, [job?.id]);

  if (!job) {
    return (
      <div className="page-head">
        <div>
          <h2>Review queue</h2>
          <p>Empty. All documents cleared the confidence threshold.</p>
        </div>
      </div>
    );
  }

function Settings({ llm, onSave }) {
  const [form, setForm] = useState({
    enabled: llm.enabled,
    provider: llm.provider,
    api_key: "",
    base_url: llm.base_url,
    model: llm.model,
  });
  const [busy, setBusy] = useState(false);
  const [test, setTest] = useState(null);
  const [msg, setMsg] = useState("");

  function applyProvider(id) {
    const p = (llm.providers || []).find((x) => x.id === id);
    setForm((f) => ({
      ...f,
      provider: id,
      base_url: p?.default_base_url || f.base_url,
      model: p?.default_model || f.model,
    }));
  }

  async function save() {
    setBusy(true);
    setMsg("");
    try {
      await api.saveLlm(form);
      setMsg("Saved. New documents in Inbox / New document now use this extractor.");
      await onSave();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function ping() {
    setBusy(true);
    setTest(null);
    try {
      const r = await api.testLlm();
      setTest(r);
    } catch (e) {
      setTest({ ok: false, notes: e.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h2>AI settings</h2>
          <p>
            Use your own Groq (free) or OpenAI key. Keys stay on the server, never in git.
            Seeded corpus still uses rules so evaluation stays cheap and repeatable.
          </p>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Provider</h3>
          <p className="muted">
            Current: {llm.enabled ? `LLM on · ${llm.provider_label}` : "rules fallback"}{" "}
            {llm.api_key_masked ? `· ${llm.api_key_masked}` : "· no key"}
          </p>
          <label>
            Provider
            <select value={form.provider} onChange={(e) => applyProvider(e.target.value)}>
              {(llm.providers || []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label style={{ marginTop: 8 }}>
            API key
            <input
              type="password"
              placeholder={llm.api_key_masked || "paste key"}
              value={form.api_key}
              onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              autoComplete="off"
            />
          </label>
          <label style={{ marginTop: 8 }}>
            Base URL
            <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
          </label>
          <label style={{ marginTop: 8 }}>
            Model
            <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          </label>
          <label style={{ marginTop: 8, flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            Enable LLM for new documents
          </label>
          <div className="row" style={{ marginTop: 14 }}>
            <button className="btn-primary" disabled={busy} onClick={save}>
              Save
            </button>
            <button className="btn" disabled={busy} onClick={ping}>
              Test extraction
            </button>
          </div>
          {msg && <p className="muted">{msg}</p>}
          {test && (
            <div className="alert" style={{ marginTop: 12 }}>
              {test.ok ? `OK · ${test.mode} · ${test.partner_name} · ${test.lines?.length || 0} lines · ${test.cost_eur} EUR` : test.notes}
            </div>
          )}
        </div>
        <div className="card">
          <h3>How to get a free key</h3>
          <ol>
            <li>Open <span className="mono">console.groq.com/keys</span></li>
            <li>Create an account, then Create API Key</li>
            <li>Paste it here, Save, then Test extraction</li>
            <li>Drop a messy German email in New document</li>
          </ol>
          <p className="muted">
            Groq free tier is enough for this demo. Do not commit the key. On Render / Railway, set
            USER_LLM_API_KEY as an environment variable instead of pasting it in the UI.
          </p>
        </div>
      </div>
    </>
  );
}

  function setLine(i, patch) {
    setLines((prev) => prev.map((ln, k) => (k === i ? { ...ln, ...patch } : ln)));
  }

  async function submit(action) {
    setBusy(true);
    try {
      await api.review(job.id, { action, partner_id: partnerId, intent, lines, note });
      await onDone();
      setIdx(0);
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Human review</h2>
          <p>
            Working-student task: confirm customer, SKU and qty, then post a draft quotation to Odoo.
          </p>
        </div>
        <div className="muted">
          {idx + 1} / {jobs.length}
        </div>
      </div>
      <div className="grid-2">
        <div className="paper">
          <h4>
            {job.from_name} · {job.language}
          </h4>
          <strong>{job.subject}</strong>
          <pre style={{ marginTop: 12 }}>{job.body}</pre>
        </div>
        <div className="card">
          <h3>Correct extraction</h3>
          {job.extraction.review_reasons?.map((r) => (
            <div key={r} className="alert">
              {r}
            </div>
          ))}
          <div className="form-grid">
            <label>
              Customer
              <select value={partnerId} onChange={(e) => setPartnerId(e.target.value)}>
                <option value="">— select —</option>
                {catalog.partners.map((p) => (
                  <option key={p.id} value={p.id}>
                    {p.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Intent
              <select value={intent} onChange={(e) => setIntent(e.target.value)}>
                <option value="quote">Quote / Angebot</option>
                <option value="order">Order / Bestellung</option>
              </select>
            </label>
          </div>
          <div style={{ marginTop: 12 }}>
            {lines.map((ln, i) => (
              <div className="line-edit" key={i}>
                <select
                  value={ln.sku || ""}
                  onChange={(e) => {
                    const p = catalog.products.find((x) => x.sku === e.target.value);
                    setLine(i, {
                      sku: e.target.value,
                      product_name: p?.name,
                      unit_price: p?.list_price,
                      uom: p?.uom,
                      issues: [],
                    });
                  }}
                >
                  <option value="">unmatched</option>
                  {catalog.products.map((p) => (
                    <option key={p.sku} value={p.sku}>
                      {p.sku} · {p.name}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  value={ln.qty}
                  onChange={(e) => setLine(i, { qty: Number(e.target.value) })}
                />
                <span className="muted">{ln.raw}</span>
                <span className="mono">{pct(ln.confidence)}</span>
              </div>
            ))}
          </div>
          <label style={{ marginTop: 8 }}>
            Note for Odoo
            <textarea value={note} onChange={(e) => setNote(e.target.value)} />
          </label>
          <div className="row" style={{ marginTop: 12 }}>
            <button className="btn-primary" disabled={busy} onClick={() => submit("approve")}>
              Approve → Odoo draft
            </button>
            <button className="btn danger" disabled={busy} onClick={() => submit("reject")}>
              Reject
            </button>
            {idx < jobs.length - 1 && (
              <button className="btn-ghost" onClick={() => setIdx(idx + 1)}>
                Skip
              </button>
            )}
          </div>
        </div>
      </div>
    </>
  );
}

function Quotes({ quotes, onChange }) {
  const [current, setCurrent] = useState(quotes[0]?.id);
  const q = quotes.find((x) => x.id === current) || quotes[0];

  async function setState(state) {
    if (!q) return;
    await api.setQuoteState(q.id, state);
    await onChange();
  }

  if (!q) return <p className="muted">No quotations yet.</p>;

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Odoo quotations</h2>
          <p>Simulated sale.order documents. Stock-aware. Purchase suggestions when reorder point is hit.</p>
        </div>
      </div>
      <div className="split">
        <div className="list">
          {quotes.map((item) => (
            <button
              key={item.id}
              className={`doc ${q.id === item.id ? "selected" : ""}`}
              onClick={() => setCurrent(item.id)}
            >
              <div className="top">
                <span className="mono">{item.id}</span>
                <span className={`badge ${item.state === "draft" ? "amber" : "green"}`}>{item.state}</span>
              </div>
              <div className="subj">{item.partner_name}</div>
              <div className="meta">{eur(item.amount_total)}</div>
            </button>
          ))}
        </div>
        <div className="quote-sheet">
          <div className="quote-head">
            <div>
              <div className="muted">Nutrifill GmbH · Griesheim</div>
              <h3>
                {q.intent === "order" ? "Sales order" : "Quotation"} {q.id}
              </h3>
              <div>
                {q.partner_name} · {q.payment_terms} · valid {q.validity}
              </div>
            </div>
            <div>
              <button className="btn" onClick={() => setState("sent")}>
                Mark sent
              </button>{" "}
              <button className="btn-primary" onClick={() => setState("sale")}>
                Confirm
              </button>
            </div>
          </div>
          <table>
            <thead>
              <tr>
                <th>SKU</th>
                <th>Description</th>
                <th>Qty</th>
                <th>Price</th>
                <th>Disc.</th>
                <th>Stock</th>
                <th className="right">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {q.lines.map((ln) => (
                <tr key={ln.sku}>
                  <td className="mono">{ln.sku}</td>
                  <td>{ln.description}</td>
                  <td>
                    {ln.qty} {ln.uom}
                  </td>
                  <td>{eur(ln.unit_price)}</td>
                  <td>{ln.discount ? pct(ln.discount) : "—"}</td>
                  <td>
                    {ln.stock} · {ln.stock_status.replaceAll("_", " ")}
                  </td>
                  <td className="right">{eur(ln.subtotal)}</td>
                </tr>
              ))}
            </tbody>
          </table>
          <div className="right" style={{ marginTop: 12 }}>
            <div>Untaxed {eur(q.amount_untaxed)}</div>
            <div>VAT 19% {eur(q.amount_tax)}</div>
            <strong>Total {eur(q.amount_total)}</strong>
          </div>
          {q.purchase_suggestions?.length > 0 && (
            <div style={{ marginTop: 16 }}>
              <strong>Purchasing suggestions</strong>
              {q.purchase_suggestions.map((s) => (
                <div key={s.sku} className="alert" style={{ color: "#243028", background: "#efe4c8", borderColor: "#c4aa6a" }}>
                  Reorder {s.suggested_qty} × {s.product} from {s.supplier}. {s.reason}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );
}

function Eval({ evaluation }) {
  const rows = evaluation.rows || [];
  return (
    <>
      <div className="page-head">
        <div>
          <h2>Evaluation vs gold labels</h2>
          <p>
            Synthetic German and English documents with known answers. Metrics the role actually cares about.
          </p>
        </div>
      </div>
      <div className="kpis">
        <Metric label="SKU recall" value={pct(evaluation.sku_recall)} />
        <Metric label="SKU precision" value={pct(evaluation.sku_precision)} />
        <Metric label="Qty accuracy" value={pct(evaluation.qty_accuracy)} />
        <Metric label="Partner accuracy" value={pct(evaluation.partner_accuracy)} />
        <Metric label="Routing accuracy" value={pct(evaluation.routing_accuracy)} />
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Automation economics</h3>
          <table className="table">
            <tbody>
              <tr>
                <td>Share auto-handled</td>
                <td className="right mono">{pct(evaluation.share_auto)}</td>
              </tr>
              <tr>
                <td>Share auto and correct</td>
                <td className="right mono">{pct(evaluation.share_auto_correct)}</td>
              </tr>
              <tr>
                <td>Cost per document</td>
                <td className="right mono">{eur(evaluation.cost_per_document_eur)}</td>
              </tr>
              <tr>
                <td>Corpus cost</td>
                <td className="right mono">{eur(evaluation.total_cost_eur)}</td>
              </tr>
            </tbody>
          </table>
          <p className="muted">
            Fine-tuning is skipped on purpose: a labelled evaluation set plus confidence routing is cheaper to
            iterate in a working-student week.
          </p>
        </div>
        <div className="card">
          <h3>By difficulty</h3>
          <table className="table">
            <thead>
              <tr>
                <th>Set</th>
                <th>Docs</th>
                <th>Recall</th>
                <th>Auto</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(evaluation.by_difficulty || {}).map(([k, v]) => (
                <tr key={k}>
                  <td>{k}</td>
                  <td>{v.documents}</td>
                  <td className="mono">{pct(v.sku_recall)}</td>
                  <td className="mono">{pct(v.share_auto)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Per document</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Doc</th>
              <th>Partner</th>
              <th>SKU rec.</th>
              <th>Qty</th>
              <th>Auto</th>
              <th>Route</th>
              <th>Cost</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.document_id}>
                <td className="mono">{r.document_id}</td>
                <td>{r.partner_ok ? "ok" : "miss"}</td>
                <td className="mono">{pct(r.sku_recall)}</td>
                <td className="mono">{pct(r.qty_accuracy)}</td>
                <td>{r.auto_handled ? "yes" : "no"}</td>
                <td>{r.routing_ok ? "ok" : "off"}</td>
                <td className="mono">{eur(r.cost_eur)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}

function Metric({ label, value }) {
  return (
    <div className="kpi">
      <div className="label">{label}</div>
      <div className="value">{value}</div>
    </div>
  );
}

function Workflow({ workflow }) {
  return (
    <>
      <div className="page-head">
        <div>
          <h2>{workflow.title}</h2>
          <p>How purchasing and sales automation is wired for a nutritional wholesaler.</p>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="flow">
            {workflow.steps.map((s, i) => (
              <div className="step" key={s.id}>
                <div className="dot">{i + 1}</div>
                <div>
                  <div className="tool">{s.tool}</div>
                  <h4>{s.title}</h4>
                  <p>{s.detail}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="card">
            <h3>KPIs for this role</h3>
            <ul>
              {workflow.kpis.map((k) => (
                <li key={k}>{k}</li>
              ))}
            </ul>
          </div>
          <div className="card" style={{ marginTop: 12 }}>
            <h3>Stack</h3>
            <p>{workflow.stack.join(" · ")}</p>
            <p className="muted">
              Matches the job: merchandise management, n8n-style workflows, Odoo-style ERP, APIs, and
              documented test cases instead of a one-off model fine-tune.
            </p>
          </div>
        </div>
      </div>
    </>
  );
}

function Ingest({ catalog, llm, onDone }) {
  const [form, setForm] = useState({
    source: "email",
    from_name: "Lisa Berger",
    from_email: "einkauf@fitnessfirst-ffm.de",
    subject: "Kurzfristige Nachbestellung",
    body: "Hallo Nutrifill,\nbitte 6 x Molkenprotein Isolat 1kg Vanille und 4 Kreatin 500g für Fitness First Frankfurt.\nDanke",
  });
  const [busy, setBusy] = useState(false);

  function set(k, v) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function send() {
    setBusy(true);
    try {
      await api.ingest(form);
      onDone();
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h2>Drop a document</h2>
          <p>
            Simulate n8n forwarding a parsed email. Extractor: {llm?.enabled ? `LLM (${llm.provider} / ${llm.model})` : "catalog rules (add a Groq key in AI settings)"}.
          </p>
        </div>
      </div>
      <div className="card" style={{ maxWidth: 720 }}>
        <div className="form-grid">
          <label>
            Source
            <select value={form.source} onChange={(e) => set("source", e.target.value)}>
              <option value="email">email</option>
              <option value="pdf">pdf</option>
              <option value="n8n">n8n webhook</option>
            </select>
          </label>
          <label>
            From name
            <input value={form.from_name} onChange={(e) => set("from_name", e.target.value)} />
          </label>
          <label>
            From email
            <input value={form.from_email} onChange={(e) => set("from_email", e.target.value)} />
          </label>
          <label>
            Subject
            <input value={form.subject} onChange={(e) => set("subject", e.target.value)} />
          </label>
        </div>
        <label style={{ marginTop: 10 }}>
          Body
          <textarea value={form.body} onChange={(e) => set("body", e.target.value)} style={{ minHeight: 180 }} />
        </label>
        <div className="row" style={{ marginTop: 12 }}>
          <button className="btn-primary" disabled={busy} onClick={send}>
            Run extraction
          </button>
          <span className="muted">{catalog.partners.length} known customers in master data</span>
        </div>
      </div>
    </>
  );
}

function Settings({ llm, onSave }) {
  const [form, setForm] = useState({
    enabled: llm.enabled,
    provider: llm.provider,
    api_key: "",
    base_url: llm.base_url,
    model: llm.model,
  });
  const [busy, setBusy] = useState(false);
  const [test, setTest] = useState(null);
  const [msg, setMsg] = useState("");

  function applyProvider(id) {
    const p = (llm.providers || []).find((x) => x.id === id);
    setForm((f) => ({
      ...f,
      provider: id,
      base_url: p?.default_base_url || f.base_url,
      model: p?.default_model || f.model,
    }));
  }

  async function save() {
    setBusy(true);
    setMsg("");
    try {
      await api.saveLlm(form);
      setMsg("Saved. New documents now use this extractor.");
      await onSave();
    } catch (e) {
      setMsg(e.message);
    } finally {
      setBusy(false);
    }
  }

  async function ping() {
    setBusy(true);
    setTest(null);
    try {
      const r = await api.testLlm();
      setTest(r);
    } catch (e) {
      setTest({ ok: false, notes: e.message });
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h2>AI settings</h2>
          <p>
            Use your own Groq (free) or OpenAI key. Keys stay on the server, never in git.
            Seeded corpus still uses rules so evaluation stays cheap and repeatable.
          </p>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <h3>Provider</h3>
          <p className="muted">
            Current: {llm.enabled ? `LLM on · ${llm.provider_label}` : "rules fallback"}{" "}
            {llm.api_key_masked ? `· ${llm.api_key_masked}` : "· no key"}
          </p>
          <label>
            Provider
            <select value={form.provider} onChange={(e) => applyProvider(e.target.value)}>
              {(llm.providers || []).map((p) => (
                <option key={p.id} value={p.id}>
                  {p.label}
                </option>
              ))}
            </select>
          </label>
          <label style={{ marginTop: 8 }}>
            API key
            <input
              type="password"
              placeholder={llm.api_key_masked || "paste key"}
              value={form.api_key}
              onChange={(e) => setForm({ ...form, api_key: e.target.value })}
              autoComplete="off"
            />
          </label>
          <label style={{ marginTop: 8 }}>
            Base URL
            <input value={form.base_url} onChange={(e) => setForm({ ...form, base_url: e.target.value })} />
          </label>
          <label style={{ marginTop: 8 }}>
            Model
            <input value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} />
          </label>
          <label style={{ marginTop: 8, flexDirection: "row", alignItems: "center", gap: 8 }}>
            <input
              type="checkbox"
              checked={form.enabled}
              onChange={(e) => setForm({ ...form, enabled: e.target.checked })}
            />
            Enable LLM for new documents
          </label>
          <div className="row" style={{ marginTop: 14 }}>
            <button className="btn-primary" disabled={busy} onClick={save}>
              Save
            </button>
            <button className="btn" disabled={busy} onClick={ping}>
              Test extraction
            </button>
          </div>
          {msg && <p className="muted">{msg}</p>}
          {test && (
            <div className="alert" style={{ marginTop: 12 }}>
              {test.ok
                ? `OK · ${test.mode} · ${test.partner_name} · ${test.lines?.length || 0} lines · ${test.cost_eur} EUR`
                : test.notes}
            </div>
          )}
        </div>
        <div className="card">
          <h3>How to get a free key</h3>
          <ol>
            <li>Open console.groq.com/keys</li>
            <li>Create an account, then Create API Key</li>
            <li>Paste it here, Save, then Test extraction</li>
            <li>Drop a messy German email in New document</li>
          </ol>
          <p className="muted">
            Groq free tier is enough for this demo. Do not commit the key. On Render, set
            USER_LLM_API_KEY as an environment variable instead of pasting it in the UI.
          </p>
        </div>
      </div>
    </>
  );
}
