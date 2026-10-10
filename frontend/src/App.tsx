import { useEffect, useState } from "react";

const API_BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function apiRequest<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API error ${response.status}: ${await response.text()}`);
  }

  return response.json() as Promise<T>;
}

// ─── Theme context helper ─────────────────────────────────────────────────────

function useTheme() {
  const [dark, setDark] = useState(true);

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
  }, [dark]);

  return { dark, toggle: () => setDark((current) => !current) };
}

// ─── Constants ────────────────────────────────────────────────────────────────

const AUTO_APPROVE = 30;
const FLAG_FOR_REVIEW = 60;
const AUTO_BLOCK = 85;
const NAV_ITEMS = ["Overview", "Review Queue", "Audit History", "Test Action"];

type ActionType = "transfer_money" | "send_email" | "execute_code";
type Decision = "approved" | "approved_with_warning" | "escalated" | "blocked";
type Resolution = "approved" | "rejected";
type ResolveAction = (actionId: number, resolution: Resolution, resolvedBy: string) => Promise<void>;

type Action = {
  id: number;
  timestamp: string;
  action_type: ActionType;
  details: Record<string, unknown>;
  financial_score: number;
  privacy_score: number;
  policy_score: number;
  final_score: number;
  decision: Decision;
  reasons: string[];
  resolved_by: string | null;
  resolution: string | null;
  resolution_time: string | null;
};

const DECISION_META: Record<string, { label: string; risk: string; colorVar: string }> = {
  approved: { label: "Approved", risk: "Low risk", colorVar: "var(--green)" },
  approved_with_warning: { label: "Warning", risk: "Moderate risk", colorVar: "var(--amber)" },
  escalated: { label: "Escalated", risk: "High risk", colorVar: "var(--violet)" },
  blocked: { label: "Blocked", risk: "Critical risk", colorVar: "var(--red)" },
};

const ACTION_LABELS: Record<string, string> = {
  transfer_money: "Money Transfer",
  send_email: "Email Review",
  execute_code: "Code Execution",
};

const ACTION_ICONS: Record<string, string> = {
  transfer_money: "$",
  send_email: "@",
  execute_code: "</>",
};

const NAV_ICONS: Record<string, string> = {
  Overview: "◈",
  "Review Queue": "⚑",
  "Audit History": "≡",
  "Test Action": "⊞",
};

const STATUS_ICONS = {
  approved: "✓",
  blocked: "⊘",
  warning: "⚠",
  clear: "✓",
};

const STAT_ICONS = {
  total: "◈",
  review: "⚑",
  blocked: "⊘",
  score: "◧",
};

// ─── Sample actions ───────────────────────────────────────────────────────────
// These are examples for the Test Action form only. Dashboard records are loaded
// from the backend API, not from this mock array.

const MOCK_ACTIONS: Action[] = [
  {
    id: 1,
    action_type: "transfer_money",
    decision: "approved",
    final_score: 22,
    financial_score: 18,
    privacy_score: 5,
    policy_score: 10,
    timestamp: "2024-01-15T09:00:00",
    details: {
      amount: 50000,
      currency: "PKR",
      recipient: "Verified Vendor",
      description: "Monthly office supplies",
    },
    reasons: [],
    resolved_by: null,
    resolution: null,
    resolution_time: null,
  },
  {
    id: 2,
    action_type: "execute_code",
    decision: "approved_with_warning",
    final_score: 48,
    financial_score: 5,
    privacy_score: 12,
    policy_score: 55,
    timestamp: "2024-01-15T10:30:00",
    details: {
      code: "DROP TABLE temporary_logs;",
      environment: "production",
      language: "SQL",
    },
    reasons: ["Production environment", "Destructive operation"],
    resolved_by: null,
    resolution: null,
    resolution_time: null,
  },
  {
    id: 3,
    action_type: "transfer_money",
    decision: "escalated",
    final_score: 72,
    financial_score: 80,
    privacy_score: 20,
    policy_score: 65,
    timestamp: "2024-01-15T11:15:00",
    details: {
      amount: 250000,
      currency: "PKR",
      recipient: "Unverified Vendor",
      description: "Please call before processing",
    },
    reasons: ["High amount", "Unverified recipient", "Suspicious note"],
    resolved_by: null,
    resolution: null,
    resolution_time: null,
  },
  {
    id: 4,
    action_type: "send_email",
    decision: "escalated",
    final_score: 68,
    financial_score: 0,
    privacy_score: 85,
    policy_score: 40,
    timestamp: "2024-01-15T12:00:00",
    details: {
      to: "unknown@partner.example",
      subject: "Customer verification",
      body: "CNIC: 35202-1234567-1",
    },
    reasons: ["PII detected: CNIC", "External recipient"],
    resolved_by: "Ahmed Khan",
    resolution: "approved",
    resolution_time: "2024-01-15T13:00:00",
  },
  {
    id: 5,
    action_type: "transfer_money",
    decision: "blocked",
    final_score: 91,
    financial_score: 95,
    privacy_score: 70,
    policy_score: 88,
    timestamp: "2024-01-15T13:45:00",
    details: {
      amount: 250000,
      currency: "USD",
      recipient: "Unverified Vendor",
      description: "CNIC: 35202-1234567-1",
    },
    reasons: ["International transfer", "High USD amount", "PII in note", "Unverified recipient"],
    resolved_by: null,
    resolution: null,
    resolution_time: null,
  },
  {
    id: 6,
    action_type: "send_email",
    decision: "approved",
    final_score: 15,
    financial_score: 0,
    privacy_score: 8,
    policy_score: 12,
    timestamp: "2024-01-15T14:20:00",
    details: {
      to: "partner@example.com",
      subject: "Meeting schedule",
      body: "Can we meet Tuesday?",
    },
    reasons: [],
    resolved_by: null,
    resolution: null,
    resolution_time: null,
  },
  {
    id: 7,
    action_type: "execute_code",
    decision: "blocked",
    final_score: 88,
    financial_score: 10,
    privacy_score: 30,
    policy_score: 92,
    timestamp: "2024-01-15T15:00:00",
    details: {
      code: "rm -rf /var/data/customer_records",
      environment: "production",
      language: "Bash",
    },
    reasons: ["Destructive command", "Production env", "Data deletion"],
    resolved_by: null,
    resolution: null,
    resolution_time: null,
  },
];

const SAMPLE_ACTION_LABELS = [
  "Routine PKR transfer (sample)",
  "Production cleanup command (sample)",
  "High-risk transfer (sample)",
  "Email containing a CNIC (sample)",
  "International high-risk transfer (sample)",
];

function normalizeAction(row: any): Action {
  return {
    ...row,
    details: typeof row.details === "string" ? JSON.parse(row.details) : row.details,
    reasons: typeof row.reasons === "string" ? JSON.parse(row.reasons) : row.reasons,
    resolved_by: row.resolved_by ?? null,
    resolution: row.resolution ?? null,
    resolution_time: row.resolution_time ?? null,
  } as Action;
}

// ─── Helpers ──────────────────────────────────────────────────────────────────

function decisionMeta(decision: string) {
  return DECISION_META[decision] ?? {
    label: decision,
    risk: "Unknown",
    colorVar: "var(--text-muted)",
  };
}

function riskMeta(score: number) {
  if (score <= AUTO_APPROVE) return { label: "Low", colorVar: "var(--green)" };
  if (score <= FLAG_FOR_REVIEW) return { label: "Moderate", colorVar: "var(--amber)" };
  if (score < AUTO_BLOCK) return { label: "High", colorVar: "var(--violet)" };
  return { label: "Critical", colorVar: "var(--red)" };
}

function actionTitle(action: Action) {
  const details = action.details;
  if (action.action_type === "transfer_money") {
    return `${String(details.currency ?? "PKR")} ${Number(details.amount ?? 0).toLocaleString()} Transfer`;
  }
  if (action.action_type === "send_email") {
    return String(details.subject ?? "Email Review");
  }
  return `${String(details.language ?? "")} Code Execution`;
}

function actionSummary(action: Action) {
  const details = action.details;
  if (action.action_type === "transfer_money") {
    return `To ${String(details.recipient ?? "Unknown recipient")} · ${String(details.description ?? "")}`;
  }
  if (action.action_type === "send_email") return `To ${String(details.to ?? "Unknown recipient")}`;
  return `Running in ${String(details.environment ?? "unknown environment")}`;
}

function relativeTime(timestamp: string) {
  const diff = Date.now() - new Date(timestamp).getTime();
  if (Number.isNaN(diff)) return timestamp;
  const minutes = Math.floor(diff / 60000);
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

function colorAlpha(cssVar: string, alpha: number) {
  return `color-mix(in srgb, ${cssVar} ${Math.round(alpha * 100)}%, transparent)`;
}

// ─── Animated score bar ───────────────────────────────────────────────────────

function ScoreBar({ score }: { score: number }) {
  const [width, setWidth] = useState(0);
  const meta = riskMeta(score);

  useEffect(() => {
    const timeout = setTimeout(() => setWidth(score), 80);
    return () => clearTimeout(timeout);
  }, [score]);

  return (
    <div className="h-1 rounded-full w-full" style={{ background: "var(--border)" }}>
      <div
        className="h-full rounded-full"
        style={{
          width: `${width}%`,
          background: meta.colorVar,
          transition: "width 0.6s cubic-bezier(.4,0,.2,1)",
        }}
      />
    </div>
  );
}

// ─── Theme toggle ─────────────────────────────────────────────────────────────

function ThemeToggle({ dark, onToggle }: { dark: boolean; onToggle: () => void }) {
  return (
    <button
      onClick={onToggle}
      aria-label="Toggle theme"
      className="relative w-12 h-6 rounded-full transition-all duration-300 flex items-center"
      style={{
        background: dark ? "var(--accent-dim)" : "var(--border)",
        border: "1px solid var(--border-bright)",
      }}
    >
      <span
        className="absolute left-0.5 w-5 h-5 rounded-full flex items-center justify-center text-xs transition-all duration-300"
        style={{
          background: dark ? "var(--accent)" : "var(--surface-2)",
          transform: dark ? "translateX(24px)" : "translateX(0)",
          color: "var(--text)",
        }}
      >
        {dark ? "☾" : "☀"}
      </span>
    </button>
  );
}

// ─── Badge ────────────────────────────────────────────────────────────────────

function Badge({ decision }: { decision: string }) {
  const meta = decisionMeta(decision);
  return (
    <span
      className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold tracking-wide uppercase whitespace-nowrap"
      style={{
        background: colorAlpha(meta.colorVar, 0.12),
        color: meta.colorVar,
        border: `1px solid ${colorAlpha(meta.colorVar, 0.25)}`,
      }}
    >
      {meta.label}
    </span>
  );
}

function RiskBadge({ score }: { score: number }) {
  const meta = riskMeta(score);
  return (
    <span
      className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold whitespace-nowrap"
      style={{
        background: colorAlpha(meta.colorVar, 0.12),
        color: meta.colorVar,
        border: `1px solid ${colorAlpha(meta.colorVar, 0.2)}`,
      }}
    >
      <span className="font-mono font-bold">{score}</span>
      <span style={{ opacity: 0.8 }}>{meta.label}</span>
    </span>
  );
}

// ─── Stat card ────────────────────────────────────────────────────────────────

function StatCard({
  icon,
  label,
  value,
  delta,
  colorVar,
}: {
  icon: string;
  label: string;
  value: string | number;
  delta: string;
  colorVar: string;
}) {
  return (
    <div
      className="rounded-2xl p-5 flex flex-col gap-4 relative overflow-hidden transition-all duration-200 hover:-translate-y-0.5"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <div className="absolute top-0 left-0 right-0 h-0.5 rounded-t-2xl" style={{ background: colorVar }} />
      <div className="flex items-center justify-between">
        <span className="text-2xl">{icon}</span>
        <span className="text-xs font-mono uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>
          {label}
        </span>
      </div>
      <div>
        <div className="text-4xl font-black tracking-tight" style={{ color: "var(--text)" }}>
          {value}
        </div>
        <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>
          {delta}
        </div>
      </div>
    </div>
  );
}

// ─── Decision band card ───────────────────────────────────────────────────────

function DecisionBandCard({ decision, count }: { decision: string; count: number }) {
  const meta = decisionMeta(decision);
  return (
    <div
      className="rounded-xl p-4 text-center transition-all duration-200 hover:-translate-y-0.5"
      style={{
        background: colorAlpha(meta.colorVar, 0.08),
        border: `1px solid ${colorAlpha(meta.colorVar, 0.2)}`,
        boxShadow: "var(--shadow-card)",
      }}
    >
      <div className="text-3xl font-black" style={{ color: meta.colorVar }}>
        {count}
      </div>
      <div className="text-xs font-semibold uppercase tracking-widest mt-1" style={{ color: meta.colorVar, opacity: 0.85 }}>
        {meta.label}
      </div>
    </div>
  );
}

// ─── Action card ──────────────────────────────────────────────────────────────

function ActionCard({
  action,
  allowResolution = false,
  onResolve,
}: {
  action: Action;
  allowResolution?: boolean;
  onResolve?: ResolveAction;
}) {
  const [open, setOpen] = useState(false);
  const [resolving, setResolving] = useState(false);
  const [resolutionError, setResolutionError] = useState("");
  const meta = decisionMeta(action.decision);

  async function handleResolve(resolution: Resolution) {
    if (!onResolve || resolving) return;

    const reviewerName = window.prompt(
      `Enter your name to ${resolution === "approved" ? "approve" : "reject"} action #${action.id}:`,
    )?.trim();

    if (!reviewerName) return;

    setResolving(true);
    setResolutionError("");
    try {
      await onResolve(action.id, resolution, reviewerName);
    } catch (error) {
      setResolutionError(error instanceof Error ? error.message : "Unable to resolve this action.");
    } finally {
      setResolving(false);
    }
  }
  const score = Math.max(0, Math.min(100, action.final_score));

  return (
    <div
      className="rounded-2xl overflow-hidden transition-all duration-200 hover:-translate-y-0.5"
      style={{
        background: "var(--surface)",
        border: "1px solid var(--border)",
        boxShadow: "var(--shadow-card)",
      }}
    >
      <div className="h-0.5 w-full" style={{ background: meta.colorVar }} />
      <div className="p-5">
        <div className="flex items-start justify-between gap-4 mb-3">
          <div>
            <div className="text-base font-bold" style={{ color: "var(--text)" }}>
              {actionTitle(action)}
            </div>
            <div className="text-xs mt-0.5 font-mono" style={{ color: "var(--text-muted)" }}>
              #{action.id} · {ACTION_LABELS[action.action_type]} · {action.timestamp.replace("T", " ")}
            </div>
          </div>
          <div className="flex flex-col items-end gap-1.5 shrink-0">
            <Badge decision={action.decision} />
            <RiskBadge score={score} />
          </div>
        </div>

        <div className="text-sm mb-4" style={{ color: "var(--text-sub)" }}>
          {actionSummary(action)}
        </div>

        <ScoreBar score={score} />
        <div className="text-xs mt-1 mb-4" style={{ color: "var(--text-muted)" }}>
          {meta.risk} · trust score {score}/100
        </div>

        <div className="grid grid-cols-3 gap-3 mb-4">
          {([["Financial", action.financial_score], ["Privacy", action.privacy_score], ["Policy", action.policy_score]] as [string, number][]).map(
            ([label, value]) => (
              <div
                key={String(label)}
                className="rounded-xl p-3 text-center"
                style={{ background: "var(--surface-2)" }}
              >
                <div className="text-xl font-black" style={{ color: riskMeta(Number(value)).colorVar }}>
                  {value}
                </div>
                <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
                  {label}
                </div>
              </div>
            ),
          )}
        </div>

        {action.reasons.length > 0 && (
          <div className="mb-4">
            <div className="text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>
              Risk signals
            </div>
            <div className="flex flex-wrap gap-2">
              {action.reasons.map((reason, index) => (
                <span
                  key={index}
                  className="text-xs px-2.5 py-1 rounded-full font-medium"
                  style={{
                    background: "var(--surface-2)",
                    color: "var(--text-sub)",
                    border: "1px solid var(--border-bright)",
                  }}
                >
                  {reason}
                </span>
              ))}
            </div>
          </div>
        )}

        <button
          onClick={() => setOpen((current) => !current)}
          className="text-xs font-semibold flex items-center gap-1 transition-opacity hover:opacity-70"
          style={{ color: "var(--accent)" }}
        >
          {open ? "Hide details ↑" : "View details ↓"}
        </button>

        {open && (
          <div
            className="mt-3 rounded-xl p-3 font-mono text-xs overflow-auto"
            style={{
              background: "var(--bg)",
              color: "var(--text-sub)",
              boxShadow: "inset 0 0 0 1px var(--border)",
            }}
          >
            {JSON.stringify(action.details, null, 2)}
          </div>
        )}

        {action.resolved_by && (
          <div
            className="mt-3 rounded-xl px-4 py-3 text-xs font-medium"
            style={{
              background: colorAlpha("var(--green)", 0.08),
              border: `1px solid ${colorAlpha("var(--green)", 0.25)}`,
              color: "var(--green)",
            }}
          >
            Resolved as <strong>{action.resolution}</strong> by {action.resolved_by} at {action.resolution_time?.replace("T", " ")}
          </div>
        )}

        {allowResolution && !action.resolved_by && (
          <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border)" }}>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={() => void handleResolve("approved")}
                disabled={resolving}
                className="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-80 disabled:opacity-50"
                style={{
                  background: colorAlpha("var(--green)", 0.15),
                  color: "var(--green)",
                  border: `1px solid ${colorAlpha("var(--green)", 0.3)}`,
                }}
              >
                {resolving ? "Saving..." : `${STATUS_ICONS.approved} Approve`}
              </button>
              <button
                type="button"
                onClick={() => void handleResolve("rejected")}
                disabled={resolving}
                className="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:opacity-80 disabled:opacity-50"
                style={{
                  background: colorAlpha("var(--red)", 0.15),
                  color: "var(--red)",
                  border: `1px solid ${colorAlpha("var(--red)", 0.3)}`,
                }}
              >
                {resolving ? "Saving..." : `${STATUS_ICONS.blocked} Reject`}
              </button>
            </div>
            {resolutionError && (
              <p role="alert" className="mt-3 text-sm" style={{ color: "var(--red)" }}>
                Resolution failed: {resolutionError}
              </p>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// ─── Timeline item ────────────────────────────────────────────────────────────

function TimelineItem({ action }: { action: Action }) {
  const meta = decisionMeta(action.decision);
  return (
    <div className="flex gap-4 py-4" style={{ borderBottom: "1px solid var(--border)" }}>
      <div
        className="shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-lg"
        style={{
          background: colorAlpha(meta.colorVar, 0.1),
          border: `1px solid ${colorAlpha(meta.colorVar, 0.25)}`,
        }}
      >
        {ACTION_ICONS[action.action_type]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="font-semibold text-sm" style={{ color: "var(--text)" }}>
            {actionTitle(action)}
          </span>
          <Badge decision={action.decision} />
        </div>
        <div className="text-xs mt-0.5" style={{ color: "var(--text-muted)" }}>
          {ACTION_LABELS[action.action_type]} · {relativeTime(action.timestamp)} · Score {action.final_score}
        </div>
        <div className="text-xs mt-1" style={{ color: "var(--text-sub)" }}>
          {actionSummary(action)}
        </div>
      </div>
    </div>
  );
}

// ─── Table row with hover ─────────────────────────────────────────────────────

function AuditRow({ action, even }: { action: Action; even: boolean }) {
  const [hovered, setHovered] = useState(false);
  return (
    <tr
      onMouseEnter={() => setHovered(true)}
      onMouseLeave={() => setHovered(false)}
      style={{
        background: hovered ? "var(--surface-2)" : even ? "var(--surface)" : "var(--bg)",
        borderBottom: "1px solid var(--border)",
        transition: "background 0.12s ease",
        cursor: "default",
      }}
    >
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

function PageOverview({ actions }: { actions: Action[] }) {
  const counts: Record<string, number> = {
    approved: 0,
    approved_with_warning: 0,
    escalated: 0,
    blocked: 0,
  };
  actions.forEach((action) => {
    if (counts[action.decision] !== undefined) counts[action.decision]++;
  });

  const openEscalations = actions.filter((action) => action.decision === "escalated" && !action.resolved_by);
  const averageScore = actions.length
    ? Math.round(actions.reduce((sum, action) => sum + action.final_score, 0) / actions.length)
    : 0;

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: "var(--accent)" }}>
          Risk Operations
        </div>
        <h2 className="text-3xl font-black tracking-tight" style={{ color: "var(--text)" }}>Overview</h2>
      </div>

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard icon={STAT_ICONS.total} label="Total Actions" value={actions.length} delta="All time" colorVar="var(--accent)" />
        <StatCard icon={STAT_ICONS.review} label="Needs Review" value={openEscalations.length} delta="Open escalations" colorVar="var(--violet)" />
        <StatCard icon={STAT_ICONS.blocked} label="Blocked" value={counts.blocked} delta="Auto-rejected" colorVar="var(--red)" />
        <StatCard icon={STAT_ICONS.score} label="Avg Risk Score" value={averageScore} delta="Across all actions" colorVar="var(--amber)" />
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Decision Bands</div>
        <div className="grid grid-cols-4 gap-3">
          {Object.keys(counts).map((decision) => (
            <DecisionBandCard key={decision} decision={decision} count={counts[decision]} />
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        <div
          className="lg:col-span-2 rounded-2xl p-5"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}
        >
          <div className="font-bold mb-0.5" style={{ color: "var(--text)" }}>Risk Score Distribution</div>
          <div className="text-xs mb-5" style={{ color: "var(--text-muted)" }}>Final trust scores across all actions</div>
          <div className="space-y-3">
            {actions.map((action) => (
              <div key={action.id} className="flex items-center gap-3">
                <span className="text-xs font-mono w-5 shrink-0 text-right" style={{ color: "var(--text-muted)" }}>#{action.id}</span>
                <div className="flex-1"><ScoreBar score={action.final_score} /></div>
                <span className="text-xs font-black w-6 text-right font-mono" style={{ color: riskMeta(action.final_score).colorVar }}>{action.final_score}</span>
              </div>
            ))}
          </div>
          <div className="mt-4 flex gap-4 text-xs" style={{ color: "var(--text-muted)" }}>
            {[[`≤${AUTO_APPROVE}`, "var(--green)", "Approve"], [`≤${FLAG_FOR_REVIEW}`, "var(--amber)", "Warning"], [`<${AUTO_BLOCK}`, "var(--violet)", "Escalate"], [`≥${AUTO_BLOCK}`, "var(--red)", "Block"]].map(([range, color, label]) => (
              <span key={label} className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                <span>{range} {label}</span>
              </span>
            ))}
          </div>
        </div>

        <div
          className="rounded-2xl p-5"
          style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}
        >
          <div className="font-bold mb-0.5" style={{ color: "var(--text)" }}>By Action Type</div>
          <div className="text-xs mb-5" style={{ color: "var(--text-muted)" }}>Volume breakdown</div>
          <div className="space-y-4">
            {Object.entries(ACTION_LABELS).map(([type, label]) => {
              const count = actions.filter((action) => action.action_type === type).length;
              const percentage = actions.length ? (count / actions.length) * 100 : 0;
              return (
                <div key={type}>
                  <div className="flex justify-between text-sm mb-1.5">
                    <span style={{ color: "var(--text-sub)" }}>{label}</span>
                    <span className="font-mono font-bold" style={{ color: "var(--text)" }}>{count}</span>
                  </div>
                  <div className="h-1.5 rounded-full" style={{ background: "var(--border)" }}>
                    <div className="h-full rounded-full transition-all duration-700" style={{ width: `${percentage}%`, background: "var(--accent)" }} />
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
          {actions.slice(0, 6).map((action) => <TimelineItem key={action.id} action={action} />)}
          {actions.length === 0 && <p className="py-5 text-sm" style={{ color: "var(--text-muted)" }}>No actions recorded yet.</p>}
        </div>
      </div>
    </div>
  );
}

function PageReviewQueue({ actions, onResolve }: { actions: Action[]; onResolve: ResolveAction }) {
  const open = actions.filter((action) => action.decision === "escalated" && !action.resolved_by);
  const resolved = actions.filter((action) => action.resolved_by);

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
          <div className="rounded-xl p-4 text-sm font-medium flex items-center gap-3" style={{ background: colorAlpha("var(--violet)", 0.08), border: `1px solid ${colorAlpha("var(--violet)", 0.25)}`, color: "var(--violet)", boxShadow: "var(--shadow-card)" }}>
            <span className="text-xl">{STATUS_ICONS.warning}</span>
            {open.length} action{open.length !== 1 ? "s" : ""} pending human review
          </div>
          <div className="space-y-4">{open.map((action) => <ActionCard key={action.id} action={action} allowResolution onResolve={onResolve} />)}</div>
        </>
      )}

      {resolved.length > 0 && (
        <div>
          <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Recently Resolved</div>
          <div className="space-y-4">{resolved.slice(0, 3).map((action) => <ActionCard key={action.id} action={action} />)}</div>
        </div>
      )}
    </div>
  );
}

function PageAuditHistory({ actions }: { actions: Action[] }) {
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
              {["ID", "Action", "Financial", "Privacy", "Policy", "Score", "Decision", "Status"].map((heading) => (
                <th key={heading} className="text-left px-4 py-3 text-xs font-semibold uppercase tracking-widest" style={{ color: "var(--text-muted)" }}>{heading}</th>
              ))}
            </tr>
          </thead>
          <tbody>{actions.map((action, index) => <AuditRow key={action.id} action={action} even={index % 2 === 0} />)}</tbody>
        </table>
      </div>

      <div>
        <div className="text-xs font-semibold uppercase tracking-widest mb-3" style={{ color: "var(--text-muted)" }}>Action Details</div>
        <div className="space-y-4">{actions.map((action) => <ActionCard key={action.id} action={action} />)}</div>
      </div>
    </div>
  );
}

// ─── Test Action page ─────────────────────────────────────────────────────────

function PageTestAction({ onActionCreated }: { onActionCreated: () => Promise<void> }) {
  const [mode, setMode] = useState<"sample" | "custom">("sample");
  const [result, setResult] = useState<{ decision: string; score: number; actionId?: number } | null>(null);
  const [sampleIndex, setSampleIndex] = useState(0);
  const [evaluating, setEvaluating] = useState(false);
  const [apiError, setApiError] = useState("");

  const [customActionType, setCustomActionType] = useState<ActionType>("transfer_money");
  const [customAmount, setCustomAmount] = useState("50000");
  const [customCurrency, setCustomCurrency] = useState("PKR");
  const [customRecipient, setCustomRecipient] = useState("");
  const [customDescription, setCustomDescription] = useState("");
  const [customEmailTo, setCustomEmailTo] = useState("");
  const [customEmailSubject, setCustomEmailSubject] = useState("");
  const [customEmailBody, setCustomEmailBody] = useState("");
  const [customCode, setCustomCode] = useState("");
  const [customEnvironment, setCustomEnvironment] = useState("production");
  const [customLanguage, setCustomLanguage] = useState("Python");

  const inputStyle = { background: "var(--surface-2)", color: "var(--text)", border: "1px solid var(--border-bright)" };

  const resultIcon = (decision: string) => {
    if (decision === "approved") return STATUS_ICONS.approved;
    if (decision === "blocked") return STATUS_ICONS.blocked;
    return STATUS_ICONS.warning;
  };

  async function submitAction(actionType: ActionType, details: Record<string, unknown>) {
    setEvaluating(true);
    setApiError("");
    setResult(null);

    try {
      const response = await apiRequest<{
        decision: string;
        final_score: number;
        action_id: number;
      }>("/actions", {
        method: "POST",
        body: JSON.stringify({
          action_type: actionType,
          details,
          triggered_by: "Frontend Dashboard",
        }),
      });

      setResult({
        decision: response.decision,
        score: response.final_score,
        actionId: response.action_id,
      });
      await onActionCreated();
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Unable to evaluate the action.");
    } finally {
      setEvaluating(false);
    }
  }

  async function evaluateSample() {
    const sample = MOCK_ACTIONS[sampleIndex];
    if (!sample) {
      setApiError("No sample action is available.");
      return;
    }
    await submitAction(sample.action_type, sample.details);
  }

  async function evaluateCustom() {
    setApiError("");
    let details: Record<string, unknown>;

    if (customActionType === "transfer_money") {
      const amount = Number(customAmount);
      if (!customAmount.trim() || !Number.isFinite(amount) || amount < 0) {
        setApiError("Enter a valid non-negative transfer amount.");
        return;
      }
      if (!customCurrency.trim() || !customRecipient.trim() || !customDescription.trim()) {
        setApiError("Please fill in currency, recipient, and description.");
        return;
      }
      details = {
        amount,
        currency: customCurrency.trim().toUpperCase(),
        recipient: customRecipient.trim(),
        description: customDescription.trim(),
      };
    } else if (customActionType === "send_email") {
      if (!customEmailTo.trim() || !customEmailSubject.trim() || !customEmailBody.trim()) {
        setApiError("Please fill in the recipient email, subject, and message body.");
        return;
      }
      details = {
        to: customEmailTo.trim(),
        subject: customEmailSubject.trim(),
        body: customEmailBody.trim(),
      };
    } else {
      if (!customCode.trim()) {
        setApiError("Please enter the code or command to evaluate.");
        return;
      }
      details = {
        code: customCode.trim(),
        environment: customEnvironment,
        language: customLanguage,
      };
    }

    await submitAction(customActionType, details);
  }

  return (
    <div className="space-y-8">
      <div>
        <div className="text-xs font-mono uppercase tracking-widest mb-1" style={{ color: "var(--accent)" }}>Risk Operations</div>
        <h2 className="text-3xl font-black tracking-tight" style={{ color: "var(--text)" }}>Test an Action</h2>
        <p className="text-sm mt-1" style={{ color: "var(--text-muted)" }}>Submit through the trust and audit pipeline</p>
      </div>

      {result && (
        <div className="rounded-2xl p-5 flex items-start gap-4" style={{ background: colorAlpha(decisionMeta(result.decision).colorVar, 0.08), border: `1px solid ${colorAlpha(decisionMeta(result.decision).colorVar, 0.25)}`, boxShadow: "var(--shadow-card)" }}>
          <div className="text-3xl mt-0.5" style={{ color: decisionMeta(result.decision).colorVar }}>{resultIcon(result.decision)}</div>
          <div>
            <div className="font-bold text-lg" style={{ color: decisionMeta(result.decision).colorVar }}>{decisionMeta(result.decision).label}</div>
            <div className="text-sm mt-0.5" style={{ color: "var(--text-sub)" }}>
              Trust score <strong style={{ color: "var(--text)" }}>{result.score}</strong> · {decisionMeta(result.decision).risk}
            </div>
            {result.actionId !== undefined && (
              <div className="text-xs mt-1" style={{ color: "var(--text-muted)" }}>Recorded action ID: {result.actionId}</div>
            )}
          </div>
        </div>
      )}

      {apiError && <p role="alert" className="text-sm" style={{ color: "var(--red)" }}>Evaluation failed: {apiError}</p>}

      <div className="flex gap-2">
        {(["sample", "custom"] as const).map((item) => (
          <button
            key={item}
            onClick={() => { setMode(item); setApiError(""); setResult(null); }}
            className="px-4 py-2 rounded-xl text-sm font-semibold capitalize transition-all"
            style={mode === item
              ? { background: "var(--accent)", color: "var(--text)" }
              : { background: "var(--surface)", color: "var(--text-sub)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}
          >
            {item === "sample" ? "Sample action" : "Custom action"}
          </button>
        ))}
      </div>

      <div className="rounded-2xl p-6 space-y-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
        {mode === "sample" ? (
          <>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Sample Action</label>
              <select
                value={sampleIndex}
                onChange={(event) => { setSampleIndex(Number(event.target.value)); setResult(null); setApiError(""); }}
                className="w-full rounded-xl px-4 py-3 text-sm font-medium"
                style={inputStyle}
              >
                {SAMPLE_ACTION_LABELS.map((label, index) => <option key={label} value={index}>{label}</option>)}
              </select>
            </div>
            <button
              onClick={evaluateSample}
              disabled={evaluating}
              className="w-full py-3 rounded-xl font-semibold text-sm transition-all hover:opacity-90 disabled:opacity-50"
              style={{ background: "var(--accent)", color: "var(--text)" }}
            >
              {evaluating ? "Evaluating..." : "Evaluate Sample Action"}
            </button>
          </>
        ) : (
          <>
            <div>
              <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Action Type</label>
              <select
                className="w-full rounded-xl px-4 py-3 text-sm font-medium"
                style={inputStyle}
                value={customActionType}
                onChange={(event) => { setCustomActionType(event.target.value as ActionType); setApiError(""); setResult(null); }}
              >
                <option value="transfer_money">Money Transfer</option>
                <option value="send_email">Send Email</option>
                <option value="execute_code">Execute Code</option>
              </select>
            </div>

            {customActionType === "transfer_money" && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Amount</label>
                    <input type="number" min="0" value={customAmount} onChange={(event) => setCustomAmount(event.target.value)} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Currency</label>
                    <input type="text" value={customCurrency} onChange={(event) => setCustomCurrency(event.target.value)} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Recipient</label>
                  <input type="text" value={customRecipient} onChange={(event) => setCustomRecipient(event.target.value)} placeholder="Vendor name" className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Description</label>
                  <input type="text" value={customDescription} onChange={(event) => setCustomDescription(event.target.value)} placeholder="Purpose of transfer" className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                </div>
              </>
            )}

            {customActionType === "send_email" && (
              <>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Recipient Email</label>
                  <input type="email" value={customEmailTo} onChange={(event) => setCustomEmailTo(event.target.value)} placeholder="recipient@example.com" className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Subject</label>
                  <input type="text" value={customEmailSubject} onChange={(event) => setCustomEmailSubject(event.target.value)} placeholder="Email subject" className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Message Body</label>
                  <textarea value={customEmailBody} onChange={(event) => setCustomEmailBody(event.target.value)} placeholder="Write the message to evaluate" rows={4} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle} />
                </div>
              </>
            )}

            {customActionType === "execute_code" && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Environment</label>
                    <select value={customEnvironment} onChange={(event) => setCustomEnvironment(event.target.value)} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle}>
                      <option value="development">Development</option>
                      <option value="testing">Testing</option>
                      <option value="staging">Staging</option>
                      <option value="production">Production</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Language</label>
                    <select value={customLanguage} onChange={(event) => setCustomLanguage(event.target.value)} className="w-full rounded-xl px-4 py-3 text-sm" style={inputStyle}>
                      <option>Python</option>
                      <option>Bash</option>
                      <option>SQL</option>
                      <option>JavaScript</option>
                    </select>
                  </div>
                </div>
                <div>
                  <label className="block text-xs font-semibold uppercase tracking-widest mb-2" style={{ color: "var(--text-muted)" }}>Code or Command</label>
                  <textarea value={customCode} onChange={(event) => setCustomCode(event.target.value)} placeholder="Enter code or command to evaluate" rows={5} className="w-full rounded-xl px-4 py-3 text-sm font-mono" style={inputStyle} />
                </div>
              </>
            )}

            <button
              type="button"
              onClick={evaluateCustom}
              disabled={evaluating}
              className="w-full py-3 rounded-xl font-semibold text-sm transition-all hover:opacity-90 disabled:opacity-50"
              style={{ background: "var(--accent)", color: "var(--text)" }}
            >
              {evaluating ? "Evaluating..." : "Evaluate Action"}
            </button>
          </>
        )}
      </div>

      <div className="rounded-2xl p-5" style={{ background: "var(--surface)", border: "1px solid var(--border)", boxShadow: "var(--shadow-card)" }}>
        <div className="text-xs font-semibold uppercase tracking-widest mb-4" style={{ color: "var(--text-muted)" }}>Decision Thresholds</div>
        <div className="space-y-3">
          {([
            [`0–${AUTO_APPROVE}`, "Approved", "var(--green)"],
            [`${AUTO_APPROVE + 1}–${FLAG_FOR_REVIEW}`, "Warning", "var(--amber)"],
            [`${FLAG_FOR_REVIEW + 1}–${AUTO_BLOCK - 1}`, "Escalated", "var(--violet)"],
            [`${AUTO_BLOCK}–100`, "Blocked", "var(--red)"],
          ] as [string, string, string][]).map(([range, label, color]) => (
            <div key={range} className="flex items-center justify-between py-2" style={{ borderBottom: "1px solid var(--border)" }}>
              <div className="flex items-center gap-2.5">
                <span className="w-2 h-2 rounded-full shrink-0" style={{ background: color }} />
                <span className="font-mono text-sm" style={{ color: "var(--text-sub)" }}>{range}</span>
              </div>
              <span className="text-sm font-bold" style={{ color }}>{label}</span>
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
  const [actions, setActions] = useState<Action[]>([]);
  const [apiError, setApiError] = useState("");

  const refreshActions = async () => {
    try {
      const rows = await apiRequest<unknown[]>("/actions");
      setActions(rows.map(normalizeAction));
      setApiError("");
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Unable to load actions.");
    }
  };

  useEffect(() => {
    void refreshActions();
  }, []);

  const resolveAction: ResolveAction = async (actionId, resolution, resolvedBy) => {
    await apiRequest<{ action_id: number; resolved_by: string; resolution: Resolution }>(
      `/actions/${actionId}/resolve`,
      {
        method: "POST",
        body: JSON.stringify({ resolved_by: resolvedBy, resolution }),
      },
    );
    await refreshActions();
  };

  const filteredActions = search
    ? actions.filter((action) =>
        actionTitle(action).toLowerCase().includes(search.toLowerCase()) ||
        actionSummary(action).toLowerCase().includes(search.toLowerCase()) ||
        ACTION_LABELS[action.action_type].toLowerCase().includes(search.toLowerCase()),
      )
    : actions;

  const openCount = actions.filter((action) => action.decision === "escalated" && !action.resolved_by).length;

  return (
    <div className="flex h-full" style={{ background: "var(--bg)", transition: "background 0.2s ease" }}>
      <aside
        className="w-60 shrink-0 flex flex-col py-6 px-4"
        style={{ background: "var(--surface)", borderRight: "1px solid var(--border)", transition: "background 0.2s ease, border-color 0.2s ease", boxShadow: "var(--shadow-card)" }}
      >
        <div className="flex items-center gap-3 mb-8 px-2">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center text-lg shrink-0" style={{ background: "var(--accent-dim)", border: "1px solid var(--accent-ring)", color: "var(--accent)" }}>◈</div>
          <div>
            <div className="font-black text-sm leading-tight" style={{ color: "var(--text)" }}>AI Trust Layer</div>
            <div className="text-xs" style={{ color: "var(--text-muted)" }}>Risk Operations</div>
          </div>
        </div>

        <nav className="flex flex-col gap-1 flex-1">
          {NAV_ITEMS.map((item) => {
            const active = nav === item;
            return (
              <button
                key={item}
                onClick={() => setNav(item)}
                className="text-left px-3 py-2.5 rounded-xl text-sm font-medium transition-all flex items-center gap-3 relative"
                style={active
                  ? { background: "var(--accent-dim)", color: "var(--text)", border: "1px solid var(--accent-ring)" }
                  : { color: "var(--text-muted)", border: "1px solid transparent" }}
              >
                {active && <span className="absolute left-0 top-2 bottom-2 w-0.5 rounded-full" style={{ background: "var(--accent)" }} />}
                <span style={{ color: active ? "var(--accent)" : "var(--text-muted)", fontSize: "0.9rem" }}>{NAV_ICONS[item]}</span>
                {item}
                {item === "Review Queue" && openCount > 0 && (
                  <span className="ml-auto text-xs font-black px-1.5 py-0.5 rounded-full" style={{ background: colorAlpha("var(--violet)", 0.2), color: "var(--violet)" }}>
                    {openCount}
                  </span>
                )}
              </button>
            );
          })}
        </nav>

        <div className="mt-4 rounded-xl p-3 text-xs" style={{ background: "var(--surface-2)", border: "1px solid var(--border)", color: "var(--text-muted)" }}>
          <div className="font-semibold mb-2" style={{ color: "var(--text-sub)" }}>Decision bands</div>
          {([[`0–${AUTO_APPROVE}`, "var(--green)"], [`${AUTO_APPROVE + 1}–${FLAG_FOR_REVIEW}`, "var(--amber)"], [`${FLAG_FOR_REVIEW + 1}–${AUTO_BLOCK - 1}`, "var(--violet)"], [`${AUTO_BLOCK}–100`, "var(--red)"]] as [string, string][]).map(([range, color]) => (
            <div key={range} className="flex items-center gap-1.5 mb-1">
              <span className="w-1.5 h-1.5 rounded-full shrink-0" style={{ background: color }} />
              <span>{range}</span>
            </div>
          ))}
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header
          className="flex items-center gap-4 px-6 py-3.5 shrink-0 sticky top-0 z-20"
          style={{ background: "var(--surface)", borderBottom: "1px solid var(--border)", backdropFilter: "blur(12px)", transition: "background 0.2s ease", boxShadow: "var(--shadow-card)" }}
        >
          <input
            value={search}
            onChange={(event: { target: { value: string } }) => setSearch(event.target.value)}
            placeholder="Search actions…"
            className="w-full max-w-xs rounded-xl px-4 py-2 text-sm transition-all"
            style={{ background: "var(--surface-2)", color: "var(--text)", border: "1px solid var(--border-bright)" }}
          />
          <div className="flex-1" />
          <span className="text-xs font-mono" style={{ color: "var(--text-muted)" }}>{filteredActions.length} actions</span>
          <ThemeToggle dark={dark} onToggle={toggle} />
          <div className="w-9 h-9 rounded-full flex items-center justify-center font-bold text-sm" style={{ background: "var(--accent-dim)", border: "1px solid var(--accent-ring)", color: "var(--accent)" }}>R</div>
        </header>

        <main className="flex-1 overflow-auto p-6">
          {apiError && (
            <p role="alert" className="mb-4" style={{ color: "var(--red)" }}>
              API connection failed: {apiError}
            </p>
          )}
          {nav === "Overview" && <PageOverview actions={filteredActions} />}
          {nav === "Review Queue" && <PageReviewQueue actions={filteredActions} onResolve={resolveAction} />}
          {nav === "Audit History" && <PageAuditHistory actions={filteredActions} />}
          {nav === "Test Action" && <PageTestAction onActionCreated={refreshActions} />}
        </main>
      </div>
    </div>
  );
}
