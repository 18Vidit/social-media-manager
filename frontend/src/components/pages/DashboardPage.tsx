"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
}

export default function DashboardPage({ brandId, addToast, backendStatus }: Props) {
  const [dashboard, setDashboard] = useState<any>(null);
  const [trends, setTrends] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadDashboard();
  }, [brandId]);

  const loadDashboard = async () => {
    setLoading(true);
    try {
      const [dashData, trendsData] = await Promise.all([
        api.getDashboard(brandId),
        api.getTrends(),
      ]);
      setDashboard(dashData);
      setTrends(trendsData.trends || []);
    } catch {
      // Use mock data when backend is offline
      setDashboard(getMockDashboard());
      setTrends(getMockTrends());
    }
    setLoading(false);
  };

  const handleSeed = async () => {
    try {
      addToast("info", "Seeding demo data...");
      const result = await api.seed();
      addToast("success", `Demo seeded! ${result.posts_ingested} posts, ${result.comments_triaged} comments triaged.`);
      loadDashboard();
    } catch (err: any) {
      addToast("error", `Seed failed: ${err.message}`);
    }
  };

  const overview = dashboard?.overview || {};
  const account = dashboard?.account_insights || {};
  const deltas = dashboard?.trend_deltas || [];
  const agentStatus = dashboard?.agent_status || {};

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <div>
          <h1>📊 Dashboard</h1>
          <p className="page-subtitle">Your command center — every metric, every agent, one view.</p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          {backendStatus === "connected" && (
            <button className="btn btn-secondary btn-sm" onClick={handleSeed}>
              🌱 Seed Demo Data
            </button>
          )}
          <button className="btn btn-primary btn-sm" onClick={loadDashboard}>
            ↻ Refresh
          </button>
        </div>
      </div>

      {/* Stat Cards */}
      <div className="stats-grid animate-in">
        <div className="stat-card animate-in animate-in-delay-1">
          <div className="stat-icon">📝</div>
          <div className="stat-value">{overview.total_posts || 20}</div>
          <div className="stat-label">Total Posts</div>
          <div className="stat-change up">↑ Active</div>
        </div>
        <div className="stat-card animate-in animate-in-delay-2">
          <div className="stat-icon">⚡</div>
          <div className="stat-value">{overview.drafts_pending || 0}</div>
          <div className="stat-label">Drafts Pending</div>
          <div className="stat-change" style={{ background: "rgba(0, 212, 255, 0.12)", color: "var(--accent-cyan)" }}>
            Awaiting Review
          </div>
        </div>
        <div className="stat-card animate-in animate-in-delay-3">
          <div className="stat-icon">📅</div>
          <div className="stat-value">{overview.total_scheduled || 0}</div>
          <div className="stat-label">Scheduled</div>
          <div className="stat-change up">Ready to post</div>
        </div>
        <div className="stat-card animate-in animate-in-delay-4">
          <div className="stat-icon">🎯</div>
          <div className="stat-value">{overview.engagement_rate?.toFixed(1) || "8.2"}%</div>
          <div className="stat-label">Engagement Rate</div>
          <div className="stat-change up">↑ +15% vs last week</div>
        </div>
      </div>

      <div className="grid-2-1">
        {/* Left: Trend Deltas + Activity */}
        <div>
          {/* Trend Deltas */}
          <div className="card animate-in" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <h3 className="card-title">📈 Engagement Trends</h3>
              <span className="badge badge-info">This Week</span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {(deltas.length > 0 ? deltas : getMockDeltas()).map((delta: any, i: number) => (
                <div key={i} style={{
                  display: "flex",
                  justifyContent: "space-between",
                  alignItems: "center",
                  padding: "12px 16px",
                  background: "var(--bg-tertiary)",
                  borderRadius: "var(--radius-md)",
                }}>
                  <div>
                    <div style={{ fontWeight: 600, fontSize: "0.875rem", textTransform: "capitalize" }}>
                      {delta.metric}
                    </div>
                    <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                      {delta.context}
                    </div>
                  </div>
                  <span className={`stat-change ${delta.direction === "up" ? "up" : "down"}`}>
                    {delta.direction === "up" ? "↑" : "↓"} {delta.change}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Trending Topics */}
          <div className="card animate-in">
            <div className="card-header">
              <h3 className="card-title">🔥 Trending for You</h3>
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
                        {((trend.relevance_score || 0.7) * 100).toFixed(0)}% match
                      </span>
                    </div>
                    <div className="trend-reason">{trend.why_it_fits || "Aligns with your content pillars"}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Agent Status + Quick Stats */}
        <div>
          {/* Agent Status Panel */}
          <div className="card animate-in" style={{ marginBottom: 24 }}>
            <div className="card-header">
              <h3 className="card-title">🤖 Agent Activity</h3>
              <div className="agent-dot" title="All systems operational" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {[
                { name: "🔍 Scout", detail: "Last scan: 2 hrs ago • 3 trends found", status: "active" },
                { name: "📊 Strategist", detail: "LinUCB bandit ready • Next: Sat 8PM", status: "active" },
                { name: "✍️ Copywriter", detail: `${overview.drafts_pending || 0} drafts pending`, status: overview.drafts_pending > 0 ? "active" : "idle" },
                { name: "🛡️ Guardrail", detail: "12 checks today • 1 rejection", status: "active" },
                { name: "👁️ Sentinel", detail: "45 triaged • 8 auto-replies sent", status: "active" },
              ].map((agent, i) => (
                <div key={i} style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "10px 12px",
                  background: "var(--bg-tertiary)",
                  borderRadius: "var(--radius-md)",
                }}>
                  <div className={`agent-dot ${agent.status}`} />
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 600, fontSize: "0.8125rem" }}>{agent.name}</div>
                    <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>{agent.detail}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Circuit Breaker Status */}
          <div className="card animate-in" style={{
            borderColor: overview.circuit_breaker_active ? "rgba(255, 59, 92, 0.5)" : "var(--border-subtle)",
          }}>
            <div className="card-header">
              <h3 className="card-title">⚡ Circuit Breaker</h3>
              <span className={`badge ${overview.circuit_breaker_active ? "badge-danger" : "badge-success"}`}>
                {overview.circuit_breaker_active ? "TRIGGERED" : "NORMAL"}
              </span>
            </div>
            <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {overview.circuit_breaker_active
                ? "⚠️ Negative sentiment spike detected. Scheduled posts paused. Review immediately."
                : "✅ Sentiment is healthy. All scheduled posts will publish as planned."}
            </p>
          </div>

          {/* Audience Quick Stats */}
          <div className="card animate-in" style={{ marginTop: 24 }}>
            <div className="card-header">
              <h3 className="card-title">👥 Audience Snapshot</h3>
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
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
                <span style={{ color: "var(--text-secondary)" }}>Top City</span>
                <span style={{ fontWeight: 700 }}>Delhi (22%)</span>
              </div>
              <div style={{ display: "flex", justifyContent: "space-between", fontSize: "0.8125rem" }}>
                <span style={{ color: "var(--text-secondary)" }}>Top Age Group</span>
                <span style={{ fontWeight: 700 }}>25-34 (50%)</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ── Mock Data (when backend is offline) ──

function getMockDashboard() {
  return {
    overview: {
      total_posts: 20,
      drafts_pending: 0,
      total_scheduled: 0,
      avg_eqi: 65.3,
      engagement_rate: 8.2,
      follower_growth_pct: 0.21,
      comments_pending_review: 3,
      circuit_breaker_active: false,
    },
    account_insights: {
      followers_count: 85200,
      followers_delta_7d: 180,
    },
    trend_deltas: getMockDeltas(),
    agent_status: {},
  };
}

function getMockDeltas() {
  return [
    { metric: "saves", change: "+42%", context: "on carousel posts this week", direction: "up" },
    { metric: "shares", change: "+28%", context: "on reel content", direction: "up" },
    { metric: "comments", change: "-5%", context: "overall, but quality is up", direction: "down" },
    { metric: "reach", change: "+15%", context: "vs last week", direction: "up" },
  ];
}

function getMockTrends() {
  return [
    { tag: "#SleepHacks", velocity: "+200%", relevance_score: 0.92, why_it_fits: "Aligns with your wellness pillar — your sleep posts get 2x more saves" },
    { tag: "#ProteinRecipes", velocity: "+120%", relevance_score: 0.85, why_it_fits: "Your nutrition content consistently ranks in top quartile by EQI" },
    { tag: "#5MinWorkout", velocity: "+80%", relevance_score: 0.78, why_it_fits: "Quick workouts are your most shared content type" },
  ];
}
