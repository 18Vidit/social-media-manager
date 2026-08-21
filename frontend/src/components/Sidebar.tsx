"use client";

import type { PageId } from "@/app/page";

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  backendStatus: "connecting" | "connected" | "offline";
  onOpenInstagramModal?: () => void;
  instagramAccount?: any;
}

const navItems: { id: PageId; label: string; badge?: number }[] = [
  { id: "dashboard", label: "Dashboard" },
  { id: "content", label: "Content Studio" },
  { id: "schedule", label: "Schedule" },
  { id: "comments", label: "Comment Triage", badge: 3 },
  { id: "analytics", label: "Analytics" },
  { id: "brand", label: "Brand Voice" },
  { id: "pipeline", label: "Pipeline Trace" },
];

const agents = [
  { name: "Scout", status: "active" as const },
  { name: "Strategist", status: "active" as const },
  { name: "Copywriter", status: "idle" as const },
  { name: "Guardrail", status: "active" as const },
  { name: "Sentinel", status: "active" as const },
];

export default function Sidebar({
  activePage,
  onNavigate,
  backendStatus,
  onOpenInstagramModal,
  instagramAccount,
}: SidebarProps) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div>
          <div className="logo-text">Pulse</div>
          <div className="logo-tag">AI Social Manager</div>
        </div>
      </div>

      {/* Instagram Live Connection Button */}
      <div style={{ padding: "0 16px 12px 16px" }}>
        <button
          onClick={onOpenInstagramModal}
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            gap: 10,
            padding: "8px 12px",
            background: instagramAccount?.connected
              ? "linear-gradient(135deg, rgba(225, 48, 108, 0.15), rgba(131, 58, 180, 0.15))"
              : "var(--bg-tertiary)",
            border: instagramAccount?.connected
              ? "1px solid rgba(225, 48, 108, 0.4)"
              : "1px solid var(--border-color)",
            borderRadius: "var(--radius-sm)",
            cursor: "pointer",
            textAlign: "left",
            transition: "all 0.2s ease",
          }}
        >
          <div
            style={{
              width: 24,
              height: 24,
              borderRadius: 6,
              background: "linear-gradient(45deg, #f09433, #dc2743, #bc1888)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "0.65rem",
              fontWeight: 900,
              color: "#fff",
              flexShrink: 0,
            }}
          >
            IG
          </div>
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ fontSize: "0.75rem", fontWeight: 700, whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
              {instagramAccount?.connected ? `@${instagramAccount.username}` : "Connect Instagram"}
            </div>
            <div style={{ fontSize: "0.65rem", color: instagramAccount?.connected ? "var(--accent-green)" : "var(--text-muted)" }}>
              {instagramAccount?.connected ? "Live Account" : "Demo Mode"}
            </div>
          </div>
        </button>
      </div>

      {/* Navigation */}
      <nav className="sidebar-nav">
        <div className="nav-section-label">Main</div>
        {navItems.map(item => (
          <a
            key={item.id}
            className={`nav-item ${activePage === item.id ? "active" : ""}`}
            onClick={() => onNavigate(item.id)}
          >
            <span>{item.label}</span>
            {item.badge && <span className="nav-badge">{item.badge}</span>}
          </a>
        ))}
      </nav>

      {/* Agent Status */}
      <div className="sidebar-agents">
        <div className="nav-section-label">Agent Status</div>
        {agents.map(agent => (
          <div key={agent.name} className="agent-status-item">
            <div className={`agent-dot ${agent.status}`} />
            <span>{agent.name}</span>
          </div>
        ))}
        <div className="agent-status-item" style={{ marginTop: 8 }}>
          <div className={`agent-dot ${backendStatus === "connected" ? "" : backendStatus === "connecting" ? "warning" : "danger"}`} />
          <span style={{ fontSize: "0.6875rem" }}>
            Backend: {backendStatus}
          </span>
        </div>
      </div>
    </aside>
  );
}
