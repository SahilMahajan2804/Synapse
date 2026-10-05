import { useEffect, useRef, useState, type FormEvent } from "react";
import {
  Activity,
  AlertTriangle,
  Check,
  ChevronRight,
  FileUp,
  LoaderCircle,
  LockKeyhole,
  RotateCcw,
  Send,
  ShieldCheck,
  Trash2,
  X,
} from "lucide-react";
import "./App.css";

const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:8080";

type Entity = {
  type: string;
  start: number;
  end: number;
  text: string;
  score: number;
  source: string;
};

type Mapping = {
  type: string;
  original: string;
  surrogate: string;
  score: number;
};

type ChatResult = {
  sessionId: string;
  originalText: string;
  entities: Entity[];
  syntheticText: string;
  llmSyntheticResponse: string;
  restoredResponse: string;
  mappings: Mapping[];
  leakGuard: { passed: boolean; leakedCount: number; leakedValues: string[] };
  timingsMs: {
    parse: number;
    detect: number;
    synthesize: number;
    llm: number;
    restore: number;
    total: number;
  };
};

type ApiError = { error?: string; message?: string };
type Health = {
  status: string;
  synapseService: string;
  llmProvider: string;
  llmKeyConfigured: boolean;
};

function App() {
  const [text, setText] = useState("");
  const [sessionId, setSessionId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<ChatResult | null>(null);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);

  useEffect(() => {
    let active = true;
    fetch(`${API_BASE}/api/health`)
      .then((response) =>
        response.ok ? (response.json() as Promise<Health>) : Promise.reject(),
      )
      .then((data) => {
        if (active) setHealth(data);
      })
      .catch(() => {
        if (active)
          setHealth({
            status: "DOWN",
            synapseService: "DOWN",
            llmProvider: "unknown",
            llmKeyConfigured: false,
          });
      });
    return () => {
      active = false;
    };
  }, []);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!text.trim() && !file) {
      setError("Add text or choose a PDF to continue.");
      return;
    }
    setBusy(true);
    setError("");
    const body = new FormData();
    if (sessionId.trim()) body.append("sessionId", sessionId.trim());
    if (text.trim()) body.append("text", text);
    if (file) body.append("file", file);
    try {
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        body,
      });
      if (!response.ok) {
        const problem = (await response.json()) as ApiError;
        throw new Error(
          problem.message ||
            problem.error ||
            "The request could not be completed.",
        );
      }
      const data = (await response.json()) as ChatResult;
      setResult(data);
      setSessionId(data.sessionId);
      if (file) setFile(null);
    } catch (cause) {
      setError(
        cause instanceof Error
          ? cause.message
          : "The request could not be completed.",
      );
    } finally {
      setBusy(false);
    }
  }

  async function clearSession() {
    if (sessionId) {
      try {
        const response = await fetch(
          `${API_BASE}/api/session/${encodeURIComponent(sessionId)}`,
          { method: "DELETE" },
        );
        if (!response.ok && response.status !== 404)
          throw new Error("Session could not be cleared.");
      } catch {
        setError(
          "Session could not be cleared. Check the backend connection and retry.",
        );
        return;
      }
    }
    setSessionId("");
    setText("");
    setFile(null);
    setResult(null);
    setError("");
  }

  const serviceUp = health?.status === "UP" && health.synapseService === "UP";

  return (
    <main className="app-shell">
      <header className="topbar">
        <a className="brand" href="#workspace" aria-label="Synapse workspace">
          <span className="brand-mark">
            <ShieldCheck size={19} strokeWidth={2.2} />
          </span>
          <span className="brand-word">
            synapse<span className="brand-dot">.</span>
          </span>
        </a>
        <div className="topbar-center">
          <span className="topbar-kicker">PRIVACY WORKSPACE</span>
          <ChevronRight size={14} />
          <span>Chat pipeline</span>
        </div>
        <div className="topbar-right">
          <div className={`service-state ${serviceUp ? "is-up" : "is-down"}`}>
            <span className="state-light" />
            <span>
              {health
                ? serviceUp
                  ? "Services online"
                  : "Service unavailable"
                : "Connecting"}
            </span>
          </div>
          <span className="provider-label">
            <span className="provider-key">
              <LockKeyhole size={12} />
            </span>
            {health?.llmProvider ?? "LLM"}
            {health?.llmKeyConfigured ? " · key set" : ""}
          </span>
        </div>
      </header>

      <section className="workspace" id="workspace">
        <div className="workspace-heading">
          <div>
            <div className="eyebrow">
              <span className="eyebrow-line" />
              LIVE REQUEST
            </div>
            <h1>Protected conversation</h1>
          </div>
          <div className="session-tools">
            <label className="session-field">
              <span>SESSION</span>
              <input
                value={sessionId}
                onChange={(event) => setSessionId(event.target.value)}
                placeholder="New session"
                aria-label="Session ID"
              />
            </label>
            <button
              className="icon-button clear-button"
              onClick={clearSession}
              type="button"
              title="Clear session"
              aria-label="Clear session"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </div>

        {error && (
          <div className="error-banner" role="alert">
            <AlertTriangle size={17} />
            <span>{error}</span>
            <button
              type="button"
              onClick={() => setError("")}
              aria-label="Dismiss error"
            >
              <X size={16} />
            </button>
          </div>
        )}

        <form className="pipeline-grid" onSubmit={submit}>
          <section className="stage-card input-stage">
            <div className="stage-heading">
              <div className="stage-title-group">
                <span className="stage-index">01</span>
                <div>
                  <h2>Real payload</h2>
                  <p>Private · backend ingress</p>
                </div>
              </div>
              <span className="stage-icon real-icon">
                <LockKeyhole size={17} />
              </span>
            </div>
            <div className="editor-wrap">
              <textarea
                value={text}
                onChange={(event) => {
                  setText(event.target.value);
                  if (event.target.value) setFile(null);
                }}
                placeholder="Write a message or attach a PDF…"
                aria-label="Real payload"
                spellCheck={false}
              />
              {file && (
                <div className="file-chip">
                  <FileUp size={15} />
                  <span>{file.name}</span>
                  <button
                    type="button"
                    onClick={() => setFile(null)}
                    aria-label="Remove PDF"
                  >
                    <X size={14} />
                  </button>
                </div>
              )}
            </div>
            <div className="stage-footer input-footer">
              <input
                ref={fileInput}
                className="visually-hidden"
                type="file"
                accept="application/pdf,.pdf"
                onChange={(event) => {
                  const selected = event.target.files?.[0] ?? null;
                  setFile(selected);
                  if (selected) setText("");
                }}
              />
              <button
                className="attach-button"
                type="button"
                onClick={() => fileInput.current?.click()}
              >
                <FileUp size={16} />
                Attach PDF
              </button>
              <span className="character-count">
                {text.length.toLocaleString()} chars
              </span>
            </div>
            <div className="submit-row">
              <span className="privacy-note">
                <span className="privacy-dot" />
                Original values stay private
              </span>
              <button
                className="submit-button"
                type="submit"
                disabled={busy || !serviceUp}
              >
                {busy ? (
                  <LoaderCircle className="spin" size={16} />
                ) : (
                  <Send size={15} />
                )}
                {busy ? "Processing" : "Send"}
              </button>
            </div>
          </section>

          <section className="stage-card cloud-stage">
            <div className="stage-heading">
              <div className="stage-title-group">
                <span className="stage-index">02</span>
                <div>
                  <h2>Cloud payload</h2>
                  <p>Synthetic · sent to model</p>
                </div>
              </div>
              <span className="stage-icon cloud-icon">
                <Activity size={17} />
              </span>
            </div>
            <div className={`output-panel ${result ? "has-content" : ""}`}>
              {result ? (
                <>
                  <p className="output-copy">{result.syntheticText}</p>
                  <div className="output-divider" />
                  <div className="response-label">
                    <span>MODEL RESPONSE</span>
                    <span className="response-check">
                      <Check size={12} /> returned
                    </span>
                  </div>
                  <p className="output-copy model-copy">
                    {result.llmSyntheticResponse}
                  </p>
                </>
              ) : (
                <div className="empty-state">
                  <span className="empty-symbol">
                    <Activity size={18} />
                  </span>
                  <p>Protected payload appears here</p>
                  <span>Only synthetic values are sent to the model</span>
                </div>
              )}
            </div>
            <div className="stage-footer cloud-footer">
              {result ? (
                <>
                  <span className="metric">
                    {result.entities.length} <span>entities replaced</span>
                  </span>
                  <span
                    className={`guard-pill ${result.leakGuard.passed ? "guard-pass" : "guard-fail"}`}
                  >
                    <Check size={13} />
                    Leak guard passed
                  </span>
                </>
              ) : (
                <span className="waiting-label">AWAITING REQUEST</span>
              )}
            </div>
          </section>

          <section className="stage-card restored-stage">
            <div className="stage-heading">
              <div className="stage-title-group">
                <span className="stage-index">03</span>
                <div>
                  <h2>Restored response</h2>
                  <p>Private · returned to you</p>
                </div>
              </div>
              <span className="stage-icon restored-icon">
                <RotateCcw size={17} />
              </span>
            </div>
            <div
              className={`output-panel restored-panel ${result ? "has-content" : ""}`}
            >
              {result ? (
                <p className="output-copy">{result.restoredResponse}</p>
              ) : (
                <div className="empty-state">
                  <span className="empty-symbol restored-symbol">
                    <RotateCcw size={18} />
                  </span>
                  <p>Your response will appear here</p>
                  <span>Surrogates are mapped back in your session</span>
                </div>
              )}
            </div>
            <div className="stage-footer restored-footer">
              {result ? (
                <>
                  <span className="metric">
                    {result.timingsMs.total.toFixed(0)} <span>ms total</span>
                  </span>
                  <span className="restored-status">
                    <Check size={13} />
                    Restoration complete
                  </span>
                </>
              ) : (
                <span className="waiting-label">AWAITING RESPONSE</span>
              )}
            </div>
          </section>
        </form>

        {result && (
          <section className="details-strip" aria-label="Request details">
            <div className="details-heading">
              <span className="eyebrow-line" />
              <span>REQUEST DETAILS</span>
            </div>
            <div className="detail-group">
              <span className="detail-label">SESSION ID</span>
              <code>{result.sessionId}</code>
            </div>
            <div className="detail-group entity-group">
              <span className="detail-label">DETECTED</span>
              <div className="entity-list">
                {result.entities.length ? (
                  result.entities.map((entity, index) => (
                    <span
                      className="entity-tag"
                      key={`${entity.type}-${index}`}
                    >
                      {entity.type.toLowerCase().replaceAll("_", " ")}
                      <span>{entity.score.toFixed(2)}</span>
                    </span>
                  ))
                ) : (
                  <span className="none-tag">No PII detected</span>
                )}
              </div>
            </div>
            <div className="detail-group timing-group">
              <span className="detail-label">STAGES</span>
              <span className="timing-values">
                parse {result.timingsMs.parse.toFixed(0)} · detect{" "}
                {result.timingsMs.detect.toFixed(0)} · synth{" "}
                {result.timingsMs.synthesize.toFixed(0)} · model{" "}
                {result.timingsMs.llm.toFixed(0)} · restore{" "}
                {result.timingsMs.restore.toFixed(0)} ms
              </span>
            </div>
          </section>
        )}

        <footer className="workspace-footnote">
          <span className="footnote-mark">
            <ShieldCheck size={14} />
          </span>
          <span>Private ingress</span>
          <span className="footnote-separator">/</span>
          <span>PII detection</span>
          <span className="footnote-separator">/</span>
          <span>Leak check</span>
          <span className="footnote-separator">/</span>
          <span>Restoration</span>
          <span className="footnote-right">
            SYNAPSE <span>PHASE 01</span>
          </span>
        </footer>
      </section>
    </main>
  );
}

export default App;
