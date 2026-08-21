"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import AnalyticsLineChart from "@/components/ui/AnalyticsLineChart";

const mockWeeklyTrend = [
  { label: "Mon", value: 1240 },
  { label: "Tue", value: 1850 },
  { label: "Wed", value: 1620 },
  { label: "Thu", value: 2100 },
  { label: "Fri", value: 2450 },
  { label: "Sat", value: 3100 },
  { label: "Sun", value: 2800 },
];

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
  onOpenInstagramModal?: () => void;
  instagramAccount?: any;
  refreshInstagramStatus?: () => void;
}

export default function DashboardPage({
  brandId,
  addToast,
  backendStatus,
  onOpenInstagramModal,
  instagramAccount,
  refreshInstagramStatus,
}: Props) {
  const [dashboard, setDashboard] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => {
    loadDashboard();
  }, [brandId]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const dashData = await api.getDashboard(brandId);
      const trendsData = await api.getTrends("instagram");
      setDashboard(dashData);
      setTrends(trendsData.trends || []);
    } catch {
      setDashboard(getMockDashboard());
      setTrends(getMockTrends());
    }
    setLoading(false);
  };

  const handleSyncInstagram = async () => {
    setSyncing(true);
    try {
      addToast("info", "Syncing real Instagram feed data...");
      const res = await api.syncInstagram(brandId, 25);
      addToast("success", `Instagram data synced! ${res.posts_synced || res.total_posts_processed || 0} posts processed.`);
      await loadDashboard();
      if (refreshInstagramStatus) refreshInstagramStatus();
    } catch (err: any) {
      addToast("error", `Sync failed: ${err.message}`);
    }
    setSyncing(false);
  };

  const handleSeed = async () => {
    try {
      addToast("info", "Seeding demo data...");
      await api.seed();
      addToast("success", "Demo seeded!");
      loadDashboard();
    } catch (err: any) {
      addToast("error", `Seed failed: ${err.message}`);
    }
  };

  const overview = dashboard?.overview || {};
  const account = dashboard?.account_insights || {};
  const deltas = dashboard?.trend_deltas || [];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Dashboard</h1>
          <p className="page-subtitle">Unified performance, AI agent operations, and real-time audience telemetry.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {instagramAccount?.connected ? (
            <button
              className="btn btn-primary btn-sm"
              style={{ background: "linear-gradient(135deg, #e1306c, #833ab4)", border: "none" }}
              onClick={handleSyncInstagram}
              disabled={syncing}
            >
              {syncing ? "Syncing..." : "↻ Sync Instagram"}
            </button>
          ) : (
            <button
              className="btn btn-primary btn-sm"
              style={{ background: "linear-gradient(135deg, #e1306c, #833ab4)", border: "none" }}
              onClick={onOpenInstagramModal}
            >
              Connect Instagram
            </button>
          )}
          {backendStatus === "connected" && !instagramAccount?.connected && (
            <button className="btn btn-secondary btn-sm" onClick={handleSeed}>
              Seed Demo Data
            </button>
          )}
          <button className="btn btn-secondary btn-sm" onClick={loadDashboard}>
            Refresh
          </button>
        </div>
      </div>

      {/* Instagram Live Alert / Banner */}
      {instagramAccount?.connected ? (
        <div
          className="card glass animate-in"
          style={{
            marginBottom: 24,
            padding: "14px 20px",
            background: "linear-gradient(90deg, rgba(225, 48, 108, 0.12), rgba(131, 58, 180, 0.12))",
            border: "1px solid rgba(225, 48, 108, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div
              style={{
                width: 38,
                height: 38,
                borderRadius: "50%",
                background: "linear-gradient(45deg, #f09433, #dc2743, #bc1888)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontWeight: 900,
                fontSize: "0.85rem",
              }}
            >
              IG
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <strong style={{ fontSize: "0.95rem" }}>Connected: @{instagramAccount.username || "account"}</strong>
                <span className="badge badge-success" style={{ fontSize: "0.65rem" }}>LIVE DATA</span>
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                {instagramAccount.followers_count?.toLocaleString() || 0} followers • {overview.total_posts || 0} posts indexed • Sentinel Triage active
              </div>
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button className="btn btn-secondary btn-sm" onClick={onOpenInstagramModal}>
              Settings
            </button>
            <button
              className="btn btn-primary btn-sm"
              onClick={handleSyncInstagram}
              disabled={syncing}
            >
              {syncing ? "Syncing..." : "↻ Refresh Feed"}
            </button>
          </div>
        </div>
      ) : (
        <div
          className="card glass animate-in"
          style={{
            marginBottom: 24,
            padding: "14px 20px",
            background: "rgba(245, 158, 11, 0.08)",
            border: "1px solid rgba(245, 158, 11, 0.3)",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <div style={{ fontSize: "1.5rem" }}>⚡</div>
            <div>
              <div style={{ fontWeight: 700, fontSize: "0.9rem", color: "#f59e0b" }}>
                Currently in Sandbox Demo Mode
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Connect your real Instagram account to run AI agents on your actual audience and live posts.
              </div>
            </div>
          </div>
          <button
            className="btn btn-primary btn-sm"
            style={{ background: "linear-gradient(135deg, #e1306c, #833ab4)", border: "none" }}
            onClick={onOpenInstagramModal}
          >
            Connect My Instagram
          </button>
        </div>
      )}

      <div className="stats-grid animate-in">
        <div className="stat-card animate-in animate-in-delay-1">
          <div className="stat-icon">Posts</div>
          <div className="stat-value">{overview.total_posts || 20}</div>
          <div className="stat-label">Total Posts</div>
          <div className="stat-change up">Active</div>
        </div>
        <div className="stat-card animate-in animate-in-delay-2">
          <div className="stat-icon"></div>
          <div className="stat-value">{overview.drafts_pending || 0}</div>
          <div className="stat-label">Drafts Pending</div>
          <div className="stat-change" style={{ background: "rgba(0, 212, 255, 0.12)", color: "var(--accent-cyan)" }}>
            Awaiting Review
          </div>
        </div>
        <div className="stat-card animate-in animate-in-delay-3">
          <div className="stat-icon">Schedule</div>
          <div className="stat-value">{overview.total_scheduled || 0}</div>
          <div className="stat-label">Scheduled</div>
          <div className="stat-change up">Ready to post</div>
        </div>
        <div className="stat-card animate-in animate-in-delay-4">
          <div className="stat-icon">Engagement</div>
          <div className="stat-value">{overview.engagement_rate?.toFixed(1) || "8.2"}%</div>
          <div className="stat-label">Engagement Rate</div>
          <div className="stat-change up">Plus 15 percent vs last week</div>
        </div>
      </div>

      <div className="grid-2-1">
        <div>
          <div className="card glass animate-in" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <h3 className="card-title">Engagement Trends</h3>
              <span className="badge badge-info">This Week</span>
            </div>
            
            <div style={{ display: "grid", gridTemplateColumns: "1.8fr 1.2fr", gap: 20, alignItems: "center" }}>
              <div style={{ padding: "0 10px" }}>
                <AnalyticsLineChart data={mockWeeklyTrend} height={180} />
              </div>
              <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                {(deltas.length > 0 ? deltas : getMockDeltas()).map((delta: any, i: number) => (
                  <div key={i} style={{
                    display: "flex",
                    justifyContent: "space-between",
                    alignItems: "center",
                    padding: "8px 12px",
                    background: "var(--bg-tertiary)",
                    borderRadius: "var(--radius-sm)",
                    borderLeft: `3px solid ${delta.direction === "up" ? "var(--accent-green)" : "var(--accent-red)"}`
                  }}>
                    <div>
                      <div style={{ fontWeight: 600, fontSize: "0.75rem", textTransform: "capitalize" }}>
                        {delta.metric}
                      </div>
                      <div style={{ fontSize: "0.625rem", color: "var(--text-muted)", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis", maxWidth: 100 }}>
                        {delta.context}
                      </div>
                    </div>
                    <span className={`stat-change ${delta.direction === "up" ? "up" : "down"}`} style={{ fontSize: "0.6875rem", padding: "1px 6px" }}>
                      {delta.change}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="card glass animate-in">
            <div className="card-header">
              <h3 className="card-title">Trending for You</h3>
              <span className="badge badge-success">Scout Agent</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {(trends.length > 0 ? trends : getMockTrends()).slice(0, 3).map((trend: any, i: number) => (
                <div key={i} className="trend-card">
                  <div style={{ flex: 1 }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                      <span className="trend-tag">{trend.tag}</span>
                      <span className="trend-velocity">{trend.velocity}</span>
                      <span className="badge badge-info" style={{ fontSize: "0.5625rem" }}>
                        {`${(trend.relevance_score * 100).toFixed(0)} percent relevance`}
                      </span>
                    </div>
                    <div className="trend-reason">{trend.why_it_fits || "Aligns with your content pillars"}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        <div>
          <div className="card glass animate-in" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <h3 className="card-title">Agent Pipeline Status</h3>
              <div className="agent-dot" title="All systems operational" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {[
                { name: "Scout", detail: "Last scan: 2 hrs ago", status: "active", desc: "Trend Scanning", icon: "🔍" },
                { name: "Strategist", detail: "Optimization Active", status: "active", desc: "Peak-Time Prediction", icon: "📊" },
                { name: "Copywriter", detail: "Subgraphs Loaded", status: "active", desc: "Content Drafting", icon: "✍️" },
                { name: "Guardrail", detail: "Centroid Audit Ready", status: "active", desc: "Voice Alignment", icon: "🛡️" },
                { name: "Sentinel", detail: "Triage Matrix Engaged", status: "active", desc: "Comment Response", icon: "👁️" },
              ].map((agent, i) => (
                <div key={i} style={{
                  position: "relative"
                }}>
                  <div style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 12,
                    padding: "10px 14px",
                    background: "var(--bg-tertiary)",
                    borderRadius: "var(--radius-md)",
                    border: "1px solid var(--border-subtle)",
                    transition: "all var(--transition-normal)",
                  }}
                  className="agent-pipeline-node"
                  >
                    <span style={{ fontSize: "1.15rem" }}>{agent.icon}</span>
                    <div style={{ flex: 1 }}>
                      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                        <span style={{ fontWeight: 700, fontSize: "0.8125rem" }}>{agent.name}</span>
                        <span className={`badge badge-success`} style={{ fontSize: "0.5rem", padding: "1px 4px" }}>{agent.status}</span>
                      </div>
                      <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>{agent.desc} • {agent.detail}</div>
                    </div>
                  </div>
                  {i < 4 && (
                    <div style={{
                      position: "absolute",
                      left: 23,
                      bottom: -12,
                      width: 2,
                      height: 12,
                      background: "linear-gradient(180deg, var(--accent-cyan) 0%, rgba(123, 47, 247, 0.2) 100%)",
                      zIndex: 0
                    }} />
                  )}
                </div>
              ))}
            </div>
          </div>

          <div className="card animate-in" style={{
            borderColor: overview.circuit_breaker_active ? "rgba(255, 59, 92, 0.5)" : "var(--border-subtle)",
          }}>
            <div className="card-header">
              <h3 className="card-title">Circuit Breaker</h3>
              <span className={`badge ${overview.circuit_breaker_active ? "badge-danger" : "badge-success"}`}>
                {overview.circuit_breaker_active ? "TRIGGERED" : "NORMAL"}
              </span>
            </div>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {overview.circuit_breaker_active
                ? "Negative sentiment spike detected. Scheduled posts paused. Review immediately."
                : "Sentiment is healthy. All scheduled posts will publish as planned."}
            </p>
          </div>

          <div className="card animate-in" style={{ marginTop: 24 }}>
            <div className="card-header">
              <h3 className="card-title">Audience Snapshot</h3>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
                <span style={{ color: "var(--text-secondary)" }}>Followers</span>
                <span style={{ fontWeight: 700 }}>{(account.followers_count || 85200).toLocaleString()}</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
                <span style={{ color: "var(--text-secondary)" }}>Growth (7d)</span>
                <span style={{ fontWeight: 700, color: "var(--accent-green)" }}>+{account.followers_delta_7d || 180}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function getMockDashboard() {
  return {
    overview: {
      total_posts: 20,
      drafts_pending: 0,
      total_scheduled: 0,
      engagement_rate: 8.2,
      circuit_breaker_active: false,
    },
    account_insights: {
      followers_count: 85200,
      followers_delta_7d: 180,
    },
    trend_deltas: getMockDeltas(),
  };
}

function getMockDeltas() {
  return [
    { metric: "saves", change: "+42%", context: "on carousel posts this week", direction: "up" },
    { metric: "shares", change: "+28%", context: "on reel content", direction: "up" },
    { metric: "comments", change: "-5%", context: "overall, quality is up", direction: "down" },
    { metric: "reach", change: "+15%", context: "vs last week", direction: "up" },
  ];
}

function getMockTrends() {
  return [
    { tag: "#SleepHacks", velocity: "+200%", relevance_score: 0.92, why_it_fits: "Aligns with your wellness pillar - your sleep posts get 2x more saves" },
    { tag: "#ProteinRecipes", velocity: "+120%", relevance_score: 0.85, why_it_fits: "Your nutrition content consistently ranks in top quartile by EQI" },
    { tag: "#5MinWorkout", velocity: "+80%", relevance_score: 0.78, why_it_fits: "Quick workouts are your most shared content type" },
  ];
}
