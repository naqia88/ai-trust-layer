import { useState, useEffect } from "react";

// ─── Theme context helper ─────────────────────────────────────────────────────

function useTheme() {
  const [dark, setDark] = useState(true);
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, [dark]);
  return { dark, toggle: () => setDark(d => !d) };
}

// ─── Constants ────────────────────────────────────────────────────────────────

const AUTO_APPROVE = 30;
const FLAG_FOR_REVIEW = 60;
const AUTO_BLOCK = 85;
const NAV_ITEMS = ["Overview", "Review Queue", "Audit History", "Test Action"];

const DECISION_META: Record<string, { label: string; risk: string; colorVar: string }> = {
  approved:             { label: "Approved",  risk: "Low risk",      colorVar: "var(--green)"  },
  approved_with_warning:{ label: "Warning",   risk: "Moderate risk", colorVar: "var(--amber)"  },
  escalated:            { label: "Escalated", risk: "High risk",     colorVar: "var(--violet)" },
  blocked:              { label: "Blocked",   risk: "Critical risk", colorVar: "var(--red)"    },
};

const ACTION_LABELS: Record<string, string> = {
  transfer_money: "Money Transfer",
  send_email:     "Email Review",
  execute_code:   "Code Execution",
};

// Clean, consistent unicode iconography (no color emoji)
const ACTION_ICONS: Record<string, string> = {
  transfer_money: "$",
  send_email:     "@",
  execute_code:   "</>",
};

const NAV_ICONS: Record<string, string> = {
  "Overview":      "◈",
  "Review Queue":  "⚑",
  "Audit History": "≡",
  "Test Action":   "⊞",
};

const STATUS_ICONS = {
  approved: "✓",
  blocked:  "⊘",
  warning:  "⚠",
  clear:    "✓",
};

const STAT_ICONS = {
  total:  "◈",
  review: "⚑",
  blocked:"⊘",
  score:  "◧",
};

// ─── Mock data ────────────────────────────────────────────────────────────────

const MOCK_ACTIONS = [
  { id: 1, action_type: "transfer_money", decision: "approved",             final_score: 22, financial_score: 18, privacy_score:  5, policy_score: 10, timestamp: "2024-01-15T09:00:00", details: { amount: 50000,  currency: "PKR", recipient: "Verified Vendor",   description: "Monthly office supplies"           }, reasons: [],                                                        resolved_by: null,        resolution: null,       resolution_time: null },
  { id: 2, action_type: "execute_code",   decision: "approved_with_warning", final_score: 48, financial_score:  5, privacy_score: 12, policy_score: 55, timestamp: "2024-01-15T10:30:00", details: { code: "DROP TABLE temporary_logs;", environment: "production", language: "SQL"    }, reasons: ["Production environment", "Destructive operation"],       resolved_by: null,        resolution: null,       resolution_time: null },
  { id: 3, action_type: "transfer_money", decision: "escalated",            final_score: 72, financial_score: 80, privacy_score: 20, policy_score: 65, timestamp: "2024-01-15T11:15:00", details: { amount: 250000, currency: "PKR", recipient: "Unverified Vendor", description: "Please call before processing"     }, reasons: ["High amount", "Unverified recipient", "Suspicious note"], resolved_by: null,        resolution: null,       resolution_time: null },
  { id: 4, action_type: "send_email",     decision: "escalated",            final_score: 68, financial_score:  0, privacy_score: 85, policy_score: 40, timestamp: "2024-01-15T12:00:00", details: { to: "unknown@partner.example", subject: "Customer verification", body: "CNIC: 35202-1234567-1" }, reasons: ["PII detected: CNIC", "External recipient"],          resolved_by: "Ahmed Khan", resolution: "approved", resolution_time: "2024-01-15T13:00:00" },
  { id: 5, action_type: "transfer_money", decision: "blocked",              final_score: 91, financial_score: 95, privacy_score: 70, policy_score: 88, timestamp: "2024-01-15T13:45:00", details: { amount: 250000, currency: "USD", recipient: "Unverified Vendor", description: "CNIC: 35202-1234567-1"            }, reasons: ["International transfer", "High USD amount", "PII in note", "Unverified recipient"], resolved_by: null, resolution: null, resolution_time: null },
  { id: 6, action_type: "send_email",     decision: "approved",             final_score: 15, financial_score:  0, privacy_score:  8, policy_score: 12, timestamp: "2024-01-15T14:20:00", details: { to: "partner@example.com", subject: "Meeting schedule", body: "Can we meet Tuesday?" }, reasons: [],                                                     resolved_by: null,        resolution: null,       resolution_time: null },
  { id: 7, action_type: "execute_code",   decision: "blocked",              final_score: 88, financial_score: 10, privacy_score: 30, policy_score: 92, timestamp: "2024-01-15T15:00:00", details: { code: "rm -rf /var/data/customer_records", environment: "production", language: "Bash" }, reasons: ["Destructive command", "Production env", "Data deletion"], resolved_by: null, resolution: null, resolution_time: null },
];

// ─── Helpers ──────────────────────────────────────────────────────────────────

function decisionMeta(decision: string) {
  return DECISION_META[decision] ?? { label: decision, risk: "Unknown", colorVar: "var(--text-muted)" };
}

function riskMeta(score: number) {
  if (score <= AUTO_APPROVE)    return { label: "Low",      colorVar: "var(--green)"  };
  if (score <= FLAG_FOR_REVIEW) return { label: "Moderate", colorVar: "var(--amber)"  };
  if (score < AUTO_BLOCK)       return { label: "High",     colorVar: "var(--violet)" };
  return                               { label: "Critical", colorVar: "var(--red)"    };
}

function actionTitle(action: typeof MOCK_ACTIONS[0]) {
  const d = action.details as Record<string, unknown>;
  if (action.action_type === "transfer_money") return `${d.currency} ${Number(d.amount).toLocaleString()} Transfer`;
  if (action.action_type === "send_email")     return String(d.subject ?? "Email Review");
  return `${d.language} Code Execution`;
}

function actionSummary(action: typeof MOCK_ACTIONS[0]) {
  const d = action.details as Record<string, unknown>;
  if (action.action_type === "transfer_money") return `To ${d.recipient} · ${d.description}`;
  if (action.action_type === "send_email")     return `To ${d.to}`;
  return `Running in ${d.environment}`;
}

function relativeTime(ts: string) {
  const diff = Date.now() - new Date(ts).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function colorAlpha(cssVar: string, alpha: number) {
  // Wrap a CSS var in a color-mix for a translucent version
  return `color-mix(in srgb, ${cssVar} ${Math.round(alpha * 100)}%, transparent)`;
}

// ─── Animated score bar ───────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  const [width, setWidth] = useState(0);
  const m = riskMeta(score);
  useEffect(() => {
    const t = setTimeout(() => setWidth(score), 80);
    return () => clearTimeout(t);
  }, [score]);
  return (
    <div className="h-1 rounded-full w-full" style={{ background: "var(--border)" }}>
      <div className="h-full rounded-full" style={{ width: `${width}%`, background: m.colorVar, transition: "width 0.6s cubic-bezier(.4,0,.2,1)" }} />
    </div>
  );
}

// ─── Theme toggle ─────────────────────────────────────────────────────────────

function ThemeToggle({ dark, onToggle }: { dark: boolean; onToggle: () => void }) {
  return (
    <button onClick={onToggle} aria-label="Toggle theme"
      className="relative w-12 h-6 rounded-full transition-all duration-300 flex items-center"
      style={{ background: dark ? "var(--accent-dim)" : "var(--border)", border: "1px solid var(--border-bright)" }}>
      <span className="absolute left-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs transition-all duration-300"
        style={{ background: dark ? "var(--accent)" : "var(--surface-2)", transform: dark ? "translateX(24px)" : "translateX(0)", color: "var(--text)" }}>
        {dark ? "☾" : "☀"}
      </span>
    </button>
  );
}

// ─── Badge ────────────────────────────────────────────────────────────────────

function Badge({ decision }: { decision: string }) {
  const m = decisionMeta(decision);
  return (
    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide uppercase whitespace-nowrap"
      style={{ background: colorAlpha(m.colorVar, 0.12), color: m.colorVar, border: `1px solid ${colorAlpha(m.colorVar, 0.25)}` }}>
      {m.label}
    </span>
  );
}

function RiskBadge({ score }: { score: number }) {
  const m = riskMeta(score);
  return (
    <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap"
      style={{ background: colorAlpha(m.colorVar, 0.12), color: m.colorVar, border: `1px solid ${colorAlpha(m.colorVar, 0.2)}` }}>
      <span className="font-mono font-bold">{score}</span>
      <span style={{ opacity: 0.8 }}>{m.label}</span>
    </span>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({ icon, label, value, delta, colorVar }: { icon: string; label: string; value: string | number; delta: string; colorVar: string }) {
  return (
    <div className="rounded-2xl p-5 flex flex-col gap-4 relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5"
      style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl" style={{ background: colorVar }} />
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>{label}</span>
      </div>
      <div>
        <div className="text-4xl font-black tracking-tight" style={{ color: "var(--text)" }}>{value}</div>
        <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>{delta}</div>
      </div>
    </div>
  );
}

// ─── Decision band card ───────────────────────────────────────────────────────

function DecisionBandCard({ decision, count }: { decision: string; count: number }) {
  const m = decisionMeta(decision);
  return (
    <div className="rounded-xl p-4 text-center transition-all duration-200 hover:-translate-y-0.5"
      style={{ background: colorAlpha(m.colorVar, 0.08), border: `1px solid ${colorAlpha(m.colorVar, 0.2)}`, boxShadow: "var(--shadow-card)" }}>
      <div className="text-3xl font-black" style={{ color: m.colorVar }}>{count}</div>
      <div className="text-xs font-semibold uppercase tracking-widest mt-1" style={{ color: m.colorVar, opacity: 0.85 }}>{m.label}</div>
    </div>
  );
}

// ─── Action card ──────────────────────────────────────────────────────────────

function ActionCard({ action, allowResolution = false }: { action: typeof MOCK_ACTIONS[0]; allowResolution?: boolean }) {
  const [open, setOpen] = useState(false);
  const meta = decisionMeta(action.decision);
  const score = Math.max(0, Math.min(100, action.final_score));

  return (
    <div className="rounded-2xl overflow-hidden transition-all duration-200 hover:-translate-y-0.5"
      style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
      <div className="h-0.5 w-full" style={{ background: meta.colorVar }} />
      <div className="p-5">
        {/* Header */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <div className="text-base font-bold" style={{ color: "var(--text)" }}>{actionTitle(action)}</div>
            <div className="text-xs mt-0.5 font-mono" style={{ color: "var(--text-muted)" }}>
              #{action.id} · {ACTION_LABELS[action.action_type]} · {action.timestamp.replace("T", " ")}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5 shrink-0">
            <Badge decision={action.decision} />
            <RiskBadge score={score} />
          </div>
        </div>

        <div className="text-sm mb-4" style={{ color: "var(--text-sub)" }}>{actionSummary(action)}</div>

        <ScoreBar score={score} />
        <div className="text-xs mt-1 mb-4" style={{ color: "var(--text-muted)" }}>{meta.risk} · trust score {score}/100</div>

        {/* Sub-scores */}
        <div className="grid grid-cols-3 gap-3 mb-4">
          {([["Financial", action.financial_score], ["Privacy", action.privacy_score], ["Policy", action.policy_score]] as [string, number][]).map(([label, val]) => (
            <div key={label} className="rounded-xl p-3 text-center" style={{ background: "var(--surface-2)" }}>
              <div className="text-xl font-black" style={{ color: riskMeta(val).colorVar }}>{val}</div>
              <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>{label}</div>
            </div>
          ))}
        </div>

        {/* Risk chips */}
        {action.reasons.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Risk signals</div>
            <div className="flex flex-wrap gap-2">
              {action.reasons.map((r, i) => (
                <span key={i} className="text-xs px-2.5 py-1 rounded-full font-medium"
                  style={{ background: "var(--surface-2)", color: "var(--text-sub)", border: "1px solid var(--border-bright)" }}>{r}</span>
              ))}
            </div>
          </div>
        )}

        {/* Details toggle */}
        <button onClick={() => setOpen(!open)}
          className="text-xs font-semibold flex items-center gap-1 transition-opacity hover:opacity-70"
          style={{ color: "var(--accent)" }}>
          {open ? "Hide details ↑" : "View details ↓"}
        </button>

        {open && (
          <div className="mt-3 rounded-xl p-3 font-mono text-xs overflow-auto" style={{ background: "var(--bg)", color: "var(--text-sub)", boxShadow: "inset 0 0 0 1px var(--border)" }}>
            {JSON.stringify(action.details, null, 2)}
          </div>
        )}

        {action.resolved_by && (
          <div className="mt-3 rounded-xl px-4 py-3 text-xs font-medium"
            style={{ background: colorAlpha("var(--green)", 0.08), border: `1px solid ${colorAlpha("var(--green)", 0.25)}`, color: "var(--green)" }}>
            Resolved as <strong>{action.resolution}</strong> by {action.resolved_by} at {action.resolution_time?.replace("T", " ")}
          </div>
        )}

        {allowResolution && !action.resolved_by && (
          <div className="mt-4 pt-4 flex gap-3" style={{ borderTop: "1px solid var(--border)" }}>
            <button className="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-80"
              style={{ background: colorAlpha("var(--green)", 0.15), color: "var(--green)", border: `1px solid ${colorAlpha("var(--green)", 0.3)}` }}>
              {STATUS_ICONS.approved} Approve
            </button>
            <button className="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-80"
              style={{ background: colorAlpha("var(--red)", 0.15), color: "var(--red)", border: `1px solid ${colorAlpha("var(--red)", 0.3)}` }}>
              {STATUS_ICONS.blocked} Reject
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Timeline item ────────────────────────────────────────────────────────────

function TimelineItem({ action }: { action: typeof MOCK_ACTIONS[0] }) {
  const meta = decisionMeta(action.decision);
  return (
    <div className="flex gap-4 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
      <div className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg"
        style={{ background: colorAlpha(meta.colorVar, 0.1), border: `1px solid ${colorAlpha(meta.colorVar, 0.25)}` }}>
        {ACTION_ICONS[action.action_type]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>{actionTitle(action)}</span>
          <Badge decision={action.decision} />
        </div>
        <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {ACTION_LABELS[action.action_type]} · {relativeTime(action.timestamp)} · Score {action.final_score}
        </div>
        <div className="text-xs mt-1" style={{ color: "var(--text-sub)" }}>{actionSummary(action)}</div>
      </div>
    </div>
  );
}

// ─── Table row with hover ─────────────────────────────────────────────────────

function AuditRow({ action, even }: { action: typeof MOCK_ACTIONS[0]; even: boolean }) {
  const [hovered, setHovered] = useState(false);
  return (
    <tr onMouseEnter={() => setHovered(true)} onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "var(--surface-2)" : even ? "var(--surface)" : "var(--bg)",
        borderBottom: "1px solid var(--border)",
        transition: "background 0.12s ease",
        cursor: "default",
      }}>
      <td className="px-4 py-3 font-mono text-xs" style={{ color: "var(--text-muted)" }}>#{action.id}</td>
      <td className="px-4 py-3 font-medium text-sm" style={{ color: "var(--text)" }}>{ACTION_LABELS[action.action_type]}</td>
      <td className="px-4 py-3 font-mono text-sm font-bold" style={{ color: riskMeta(action.financial_score).colorVar }}>{action.financial_score}</td>
      <td className="px-4 py-3 font-mono text-sm font-bold" style={{ color: riskMeta(action.privacy_score).colorVar }}>{action.privacy_score}</td>
      <td className="px-4 py-3 font-mono text-sm font-bold" style={{ color: riskMeta(action.policy_score).colorVar }}>{action.policy_score}</td>
      <td className="px-4 py-3"><RiskBadge score={action.final_score} /></td>
      <td className="px-4 py-3"><Badge decision={action.decision} /></td>
      <td className="px-4 py-3 text-xs font-medium" style={{ color: action.resolved_by ? "var(--green)" : "var(--text-muted)" }}>
        {action.resolved_by ? `${STATUS_ICONS.approved} ${action.resolved_by}` : "Open"}
      </td>
    </tr>
  );
}

// ─── Pages ────────────────────────────────────────────────────────────────────

function PageOverview({ actions }: { actions: typeof MOCK_ACTIONS }) {
  const counts: Record<string, number> = { approved: 0, approved_with_warning: 0, escalated: 0, blocked: 0 };
  actions.forEach(a => { if (counts[a.decision] !== undefined) counts[a.decision]++; });
  const openEscalations = actions.filter(a => a.decision === "escalated" && !a.resolved_by);
  const avgScore = actions.length ? Math.round(actions.reduce((s, a) => s + a.final_score, 0) / actions.length) : 0;

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: "var(--accent)" }}>Risk Operations</div>
        <h2 className="text-3xl font-black tracking-tight" style={{ color: "var(--text)" }}>Overview</h2>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={STAT_ICONS.total}  label="Total Actions"  value={actions.length}           delta="All time"          colorVar="var(--accent)" />
        <StatCard icon={STAT_ICONS.review} label="Needs Review"   value={openEscalations.length}   delta="Open escalations"  colorVar="var(--violet)" />
        <StatCard icon={STAT_ICONS.blocked} label="Blocked"        value={counts.blocked}           delta="Auto-rejected"     colorVar="var(--red)"    />
        <StatCard icon={STAT_ICONS.score}  label="Avg Risk Score" value={avgScore}                 delta="Across all actions" colorVar="var(--amber)"  />
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Decision Bands</div>
        <div className="grid grid-cols-4 gap-3">
          {Object.keys(counts).map(d => <DecisionBandCard key={d} decision={d} count={counts[d]} />)}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Score trend bars */}
        <div className="lg:col-span-2 rounded-2xl p-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
          <div className="font-bold mb-0.5" style={{ color: "var(--text)" }}>Risk Score Distribution</div>
          <div className="text-xs mb-5" style={{ color: "var(--text-muted)" }}>Final trust scores across all actions</div>
          <div className="space-y-3">
            {actions.map(a => (
              <div key={a.id} className="flex items-center gap-3">
                <span className="text-xs font-mono w-5 shrink-0 text-right" style={{ color: "var(--text-muted)" }}>#{a.id}</span>
                <div className="flex-1"><ScoreBar score={a.final_score} /></div>
                <span className="text-xs font-black w-6 text-right font-mono" style={{ color: riskMeta(a.final_score).colorVar }}>{a.final_score}</span>
              </div>
            ))}
          </div>
          {/* Threshold markers */}
          <div className="mt-4 flex gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
            {[["≤" + AUTO_APPROVE, "var(--green)", "Approve"], ["≤" + FLAG_FOR_REVIEW, "var(--amber)", "Warning"], ["<" + AUTO_BLOCK, "var(--violet)", "Escalate"], ["≥" + AUTO_BLOCK, "var(--red)", "Block"]].map(([range, c, label]) => (
              <span key={String(label)} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: String(c) }} />
                <span>{range} {label}</span>
              </span>
            ))}
          </div>
        </div>

        {/* Action type breakdown */}
        <div className="rounded-2xl p-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
          <div className="font-bold mb-0.5" style={{ color: "var(--text)" }}>By Action Type</div>
          <div className="text-xs mb-5" style={{ color: "var(--text-muted)" }}>Volume breakdown</div>
          <div className="space-y-4">
            {Object.entries(ACTION_LABELS).map(([type, label]) => {
              const n = actions.filter(a => a.action_type === type).length;
              const pct = actions.length ? (n / actions.length) * 100 : 0;
              return (
                <div key={type}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span style={{ color: "var(--text-sub)" }}>{label}</span>
                    <span className="font-mono font-bold" style={{ color: "var(--text)" }}>{n}</span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{ background: "var(--border)" }}>
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${pct}%`, background: "var(--accent)" }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Latest Activity</div>
        <div className="rounded-2xl px-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
          {actions.slice(0, 6).map(a => <TimelineItem key={a.id} action={a} />)}
        </div>
      </div>
    </div>
  );
}

function PageReviewQueue({ actions }: { actions: typeof MOCK_ACTIONS }) {
  const open = actions.filter(a => a.decision === "escalated" && !a.resolved_by);
  const resolved = actions.filter(a => a.resolved_by);

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: "var(--accent)" }}>Risk Operations</div>
        <h2 className="text-3xl font-black tracking-tight" style={{ color: "var(--text)" }}>Review Queue</h2>
      </div>

      {open.length === 0 ? (
        <div className="rounded-2xl p-12 text-center" style={{ background: "var(--surface)", border: "1px dashed var(--border-bright)", boxShadow: "var(--shadow-card)" }}>
          <div className="text-4xl mb-3" style={{ color: "var(--green)" }}>{STATUS_ICONS.clear}</div>
          <div className="font-semibold" style={{ color: "var(--text-sub)" }}>Queue is clear</div>
          <div className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>No open escalations right now</div>
        </div>
      ) : (
        <>
          <div className="rounded-xl p-4 text-sm font-medium flex items-center gap-3"
            style={{ background: colorAlpha("var(--violet)", 0.08), border: `1px solid ${colorAlpha("var(--violet)", 0.25)}`, color: "var(--violet)", boxShadow: "var(--shadow-card)" }}>
            <span className="text-xl">{STATUS_ICONS.warning}</span>
            {open.length} action{open.length !== 1 ? "s" : ""} pending human review
          </div>
          <div className="space-y-4">{open.map(a => <ActionCard key={a.id} action={a} allowResolution />)}</div>
        </>
      )}

      {resolved.length > 0 && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Recently Resolved</div>
          <div className="space-y-4">{resolved.slice(0, 3).map(a => <ActionCard key={a.id} action={a} />)}</div>
        </div>
      )}
    </div>
  );
}

function PageAuditHistory({ actions }: { actions: typeof MOCK_ACTIONS }) {
  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: "var(--accent)" }}>Risk Operations</div>
        <h2 className="text-3xl font-black tracking-tight" style={{ color: "var(--text)" }}>Audit History</h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>{actions.length} recorded actions</p>
      </div>

      <div className="rounded-2xl overflow-hidden" style={{ border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
        <table className="w-full text-sm">
          <thead>
            <tr style={{ background: "var(--surface-2)", borderBottom: "1px solid var(--border)" }}>
              {["ID", "Action", "Financial", "Privacy", "Policy", "Score", "Decision", "Status"].map(h => (
                <th key={h} className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {actions.map((a, i) => <AuditRow key={a.id} action={a} even={i % 2 === 0} />)}
          </tbody>
        </table>
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Action Details</div>
        <div className="space-y-4">{actions.map(a => <ActionCard key={a.id} action={a} />)}</div>
      </div>
    </div>
  );
}

function PageTestAction() {
  const [mode, setMode] = useState<"sample" | "custom">("sample");
  const [result, setResult] = useState<{ decision: string; score: number } | null>(null);
  const inputStyle = { background: "var(--surface-2)", color: "var(--text)", border: "1px solid var(--border-bright)" };

  const resultIcon = (decision: string) => {
    if (decision === "approved") return STATUS_ICONS.approved;
    if (decision === "blocked") return STATUS_ICONS.blocked;
    return STATUS_ICONS.warning;
  };

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: "var(--accent)" }}>Risk Operations</div>
        <h2 className="text-3xl font-black tracking-tight" style={{ color: "var(--text)" }}>Test an Action</h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>Submit through the trust and audit pipeline</p>
      </div>

      {result && (
        <div className="rounded-2xl p-5 flex items-start gap-4"
          style={{ background: colorAlpha(decisionMeta(result.decision).colorVar, 0.08), border: `1px solid ${colorAlpha(decisionMeta(result.decision).colorVar, 0.25)}`, boxShadow: "var(--shadow-card)" }}>
          <div className="text-3xl mt-0.5" style={{ color: decisionMeta(result.decision).colorVar }}>{resultIcon(result.decision)}</div>
          <div>
            <div className="font-bold text-lg" style={{ color: decisionMeta(result.decision).colorVar }}>
              {decisionMeta(result.decision).label}
            </div>
            <div className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
              Trust score <strong style={{ color: "var(--text)" }}>{result.score}</strong> · {decisionMeta(result.decision).risk}
            </div>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {(["sample", "custom"] as const).map(m => (
          <button key={m} onClick={() => setMode(m)}
            className="px-4 py-2 rounded-xl text-sm font-semibold capitalize transition-all"
            style={mode === m
              ? { background: "var(--accent)", color: "var(--text)" }
              : { background: "var(--surface)", color: "var(--text-sub)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
            {m === "sample" ? "Sample action" : "Custom action"}
          </button>
        ))}
      </div>

      <div className="rounded-2xl p-6 space-y-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
        {mode === "sample" ? (
          <>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Sample Action</label>
              <select className="w-full rounded-xl px-4 py-3 text-sm font-medium" style={inputStyle}>
                <option>Routine PKR transfer (approved)</option>
                <option>Production cleanup command (warning)</option>
                <option>High-risk transfer (escalated)</option>
                <option>Email containing a CNIC (escalated)</option>
                <option>International high-risk transfer (blocked)</option>
              </select>
            </div>
            <button onClick={() => setResult({ decision: "approved", score: 22 })}
              className="w-full py-3 rounded-xl font-semibold text-sm transition-all hover:opacity-90"
              style={{ background: "var(--accent)", color: "var(--text)" }}>
              Evaluate Sample Action
            </button>
          </>
        ) : (
          <>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Action Type</label>
              <select className="w-full rounded-xl px-4 py-3 text-sm font-medium" style={inputStyle}>
                <option>Money Transfer</option>
                <option>Send Email</option>
                <option>Execute Code</option>
              </select>
            </div>
            <div className="grid grid-cols-2 gap-4">
              {[["Amount", "number", "50000"], ["Currency", "text", "PKR"]].map(([label, type, placeholder]) => (
                <div key={String(label)}>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>{label}</label>
                  <input type={String(type)} placeholder={String(placeholder)} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                </div>
              ))}
            </div>
            {[["Recipient", "Vendor name"], ["Description", "Purpose of transfer"]].map(([label, placeholder]) => (
              <div key={String(label)}>
                <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>{label}</label>
                <input type="text" placeholder={String(placeholder)} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
              </div>
            ))}
            <button onClick={() => setResult({ decision: "escalated", score: 72 })}
              className="w-full py-3 rounded-xl font-semibold text-sm transition-all hover:opacity-90"
              style={{ background: "var(--accent)", color: "var(--text)" }}>
              Evaluate Action
            </button>
          </>
        )}
      </div>

      <div className="rounded-2xl p-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
        <div className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "var(--text-muted)" }}>Decision Thresholds</div>
        <div className="space-y-3">
          {([
            ["0–" + AUTO_APPROVE,                       "Approved",  "var(--green)"  ],
            [(AUTO_APPROVE + 1) + "–" + FLAG_FOR_REVIEW, "Warning",   "var(--amber)"  ],
            [(FLAG_FOR_REVIEW + 1) + "–" + (AUTO_BLOCK - 1), "Escalated","var(--violet)"],
            [AUTO_BLOCK + "–100",                        "Blocked",   "var(--red)"    ],
          ] as [string, string, string][]).map(([range, label, c]) => (
            <div key={range} className="flex items-center justify-between py-2" style={{ borderBottom: "1px solid var(--border)" }}>
              <div className="flex items-center gap-2.5">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: c }} />
                <span className="font-mono text-sm" style={{ color: "var(--text-sub)" }}>{range}</span>
              </div>
              <span className="text-sm font-bold" style={{ color: c }}>{label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// ─── App shell ────────────────────────────────────────────────────────────────

export default function App() {
  const { dark, toggle } = useTheme();
  const [nav, setNav] = useState("Overview");
  const [search, setSearch] = useState("");

  const filteredActions = search
    ? MOCK_ACTIONS.filter(a =>
        actionTitle(a).toLowerCase().includes(search.toLowerCase()) ||
        actionSummary(a).toLowerCase().includes(search.toLowerCase()) ||
        ACTION_LABELS[a.action_type].toLowerCase().includes(search.toLowerCase())
      )
    : MOCK_ACTIONS;

  const openCount = MOCK_ACTIONS.filter(a => a.decision === "escalated" && !a.resolved_by).length;

  return (
    <div className="flex h-full" style={{ background: "var(--bg)", transition: "background 0.2s ease" }}>

      {/* ── Sidebar ── */}
      <aside className="w-60 shrink-0 flex flex-col py-6 px-4"
        style={{ background: "var(--surface)", borderRight: "1px solid var(--border)", transition: "background 0.2s ease, border-color 0.2s ease", boxShadow: "var(--shadow-card)" }}>

        {/* Brand */}
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg shrink-0"
            style={{ background: "var(--accent-dim)", border: "1px solid var(--accent-ring)", color: "var(--accent)" }}>◈</div>
          <div>
            <div className="font-black text-sm leading-tight" style={{ color: "var(--text)" }}>AI Trust Layer</div>
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>Risk Operations</div>
          </div>
        </div>

        {/* Nav */}
        <nav className="flex flex-col gap-1 flex-1">
          {NAV_ITEMS.map(item => {
            const active = nav === item;
            return (
              <button key={item} onClick={() => setNav(item)}
                className="text-left px-3 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-3 relative"
                style={active
                  ? { background: "var(--accent-dim)", color: "var(--text)", border: "1px solid var(--accent-ring)" }
                  : { color: "var(--text-muted)", border: "1px solid transparent" }}>
                {/* Active left bar */}
                {active && <span className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full" style={{ background: "var(--accent)" }} />}
                <span style={{ color: active ? "var(--accent)" : "var(--text-muted)", fontSize: "0.9rem" }}>{NAV_ICONS[item]}</span>
                {item}
                {item === "Review Queue" && openCount > 0 && (
                  <span className="ml-auto text-xs font-black px-1.5 py-0.5 rounded-full"
                    style={{ background: colorAlpha("var(--violet)", 0.2), color: "var(--violet)" }}>
                    {openCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        {/* Threshold legend */}
        <div className="mt-4 rounded-xl p-3 text-xs" style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--text-muted)" }}>
          <div className="font-semibold mb-2" style={{ color: "var(--text-sub)" }}>Decision bands</div>
          {([["0–" + AUTO_APPROVE, "var(--green)"], [(AUTO_APPROVE + 1) + "–" + FLAG_FOR_REVIEW, "var(--amber)"], [(FLAG_FOR_REVIEW + 1) + "–" + (AUTO_BLOCK - 1), "var(--violet)"], [AUTO_BLOCK + "–100", "var(--red)"]] as [string, string][]).map(([r, c]) => (
            <div key={r} className="flex items-center gap-1.5 mb-1">
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: c }} />
              <span>{r}</span>
            </div>
          ))}
        </div>
      </aside>

      {/* ── Main ── */}
      <div className="flex-1 flex flex-col min-w-0">

        {/* Sticky topbar */}
        <header className="flex items-center gap-4 px-6 py-3.5 shrink-0 sticky top-0 z-20"
          style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)", backdropFilter: "blur(12px)", transition: "background 0.2s ease", boxShadow: "var(--shadow-card)" }}>
          <input value={search} onChange={e => setSearch(e.target.value)}
            placeholder="Search actions…"
            className="w-full max-w-xs rounded-xl px-4 py-2 text-sm transition-all"
            style={{ background: "var(--surface-2)", color: "var(--text)", border: "1px solid var(--border-bright)" }} />
          <div className="flex-1" />
          <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{filteredActions.length} actions</span>

          {/* Theme toggle */}
          <ThemeToggle dark={dark} onToggle={toggle} />

          <div className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm"
            style={{ background: "var(--accent-dim)", border: "1px solid var(--accent-ring)", color: "var(--accent)" }}>R</div>
        </header>

        {/* Page */}
        <main className="flex-1 overflow-auto p-6">
          {nav === "Overview"      && <PageOverview     actions={filteredActions} />}
          {nav === "Review Queue"  && <PageReviewQueue  actions={filteredActions} />}
          {nav === "Audit History" && <PageAuditHistory actions={filteredActions} />}
          {nav === "Test Action"   && <PageTestAction />}
        </main>
      </div>
    </div>
  );
}
