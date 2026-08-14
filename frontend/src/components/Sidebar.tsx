"use client";

import type { PageId } from "@/app/page";

interface SidebarProps {
  activePage: PageId;
  onNavigate: (page: PageId) => void;
  backendStatus: "connecting" | "connected" | "offline";
}

const navItems: { id: PageId; icon: string; label: string; badge?: number }[] = [
  { id: "dashboard", icon: "📊", label: "Dashboard" },
  { id: "content", icon: "✍️", label: "Content Studio" },
  { id: "schedule", icon: "📅", label: "Schedule" },
  { id: "comments", icon: "💬", label: "Comment Triage", badge: 3 },
  { id: "analytics", icon: "📈", label: "Analytics" },
  { id: "brand", icon: "🎨", label: "Brand Voice" },
  { id: "pipeline", icon: "🔗", label: "Pipeline Trace" },
];

const agents = [
  { name: "Scout", status: "active" as const },
  { name: "Strategist", status: "active" as const },
  { name: "Copywriter", status: "idle" as const },
  { name: "Guardrail", status: "active" as const },
  { name: "Sentinel", status: "active" as const },
];

export default function Sidebar({ activePage, onNavigate, backendStatus }: SidebarProps) {
  return (
    <aside className="sidebar">
      {/* Logo */}
      <div className="sidebar-logo">
        <div className="logo-icon">P</div>
        <div>
          <div className="logo-text">PULSE</div>
          <div className="logo-tag">AI Social Manager</div>
        </div>
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
            <span className="nav-icon">{item.icon}</span>
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
