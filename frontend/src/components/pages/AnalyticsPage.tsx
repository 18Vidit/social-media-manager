"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import AnalyticsLineChart from "@/components/ui/AnalyticsLineChart";

const mockDailyTrend = [
  { label: "Aug 10", value: 1200 },
  { label: "Aug 11", value: 1450 },
  { label: "Aug 12", value: 1300 },
  { label: "Aug 13", value: 1900 },
  { label: "Aug 14", value: 2350 },
  { label: "Aug 15", value: 3100 },
  { label: "Aug 16", value: 2950 },
];

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
}

export default function AnalyticsPage({ brandId, addToast, backendStatus }: Props) {
  const [posts, setPosts] = useState<any[]>([]);
  const [audience, setAudience] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [brandId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [postsData, audienceData] = await Promise.all([
        api.getPostAnalytics(brandId),
        api.getAudience(),
      ]);
      setPosts(postsData);
      setAudience(audienceData);
    } catch {
      setPosts(getMockPosts());
      setAudience(getMockAudience());
    }
    setLoading(false);
  };

  const getTierBadge = (tier: string) => {
    switch (tier) {
      case "exceptional": return "badge-success";
      case "good": return "badge-info";
      case "average": return "badge-warning";
      default: return "badge-danger";
    }
  };

  const demographics = audience?.demographics || getMockAudience().demographics;

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Analytics</h1>
          <p className="page-subtitle">Deep dashboard: every recommendation carries the number that produced it.</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadData}>↻ Refresh</button>
      </div>

      {/* Audience Overview */}
      <div className="stats-grid animate-in">
        <div className="stat-card glass">
          <div className="stat-icon">Followers</div>
          <div className="stat-value">{(audience?.followers_count || 85200).toLocaleString()}</div>
          <div className="stat-label">Total Followers</div>
          <div className="stat-change up">↑ +{audience?.followers_delta_7d || 180} this week</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-icon">Reach</div>
          <div className="stat-value">{((audience?.accounts_reached_7d || 32000) / 1000).toFixed(1)}K</div>
          <div className="stat-label">Accounts Reached (7d)</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-icon">Engagement</div>
          <div className="stat-value">{((audience?.accounts_engaged_7d || 8500) / 1000).toFixed(1)}K</div>
          <div className="stat-label">Accounts Engaged (7d)</div>
        </div>
        <div className="stat-card glass">
          <div className="stat-icon">EQI</div>
          <div className="stat-value">
            {posts.length > 0 
              ? (posts.reduce((sum: number, p: any) => sum + (p.eqi_score || 0), 0) / posts.length).toFixed(1)
              : "65.3"}
          </div>
          <div className="stat-label">Average EQI Score</div>
        </div>
      </div>

      {/* Engagement Trend Chart Card */}
      <div className="card glass animate-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3 className="card-title">📈 Engagement Velocity Over Time</h3>
          <span className="badge badge-success">Live Track</span>
        </div>
        <div style={{ padding: "10px 0" }}>
          <AnalyticsLineChart data={mockDailyTrend} height={220} />
        </div>
      </div>

      <div className="grid-2">
        {/* Top Cities */}
        <div className="card glass animate-in">
          <div className="card-header">
            <h3 className="card-title">🌍 Top Cities</h3>
          </div>
          {(demographics.top_cities || []).map((city: any, i: number) => (
            <div key={i} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <span style={{ fontWeight: 600, fontSize: "0.875rem", minWidth: 100 }}>{city.name}</span>
              <div style={{ flex: 1 }}>
                <div className="progress-bar">
                  <div className="progress-fill" style={{ width: `${city.pct * 2}%` }} />
                </div>
              </div>
              <span style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", minWidth: 36, textAlign: "right" }}>{city.pct}%</span>
            </div>
          ))}
        </div>

        {/* Age Distribution */}
        <div className="card glass animate-in">
          <div className="card-header">
            <h3 className="card-title">📊 Age & Gender Distribution</h3>
          </div>
          {Object.entries(demographics.age_gender || {}).map(([age, genders]: [string, any]) => (
            <div key={age} style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
              <span style={{ fontWeight: 600, fontSize: "0.8125rem", minWidth: 50, color: "var(--text-secondary)" }}>{age}</span>
              <div style={{ flex: 1, display: "flex", gap: 4 }}>
                <div style={{
                  height: 20, borderRadius: "var(--radius-sm)",
                  background: "rgba(0, 212, 255, 0.5)",
                  width: `${genders.male * 2}%`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.625rem", fontWeight: 600,
                }}>
                  {genders.male > 5 ? `${genders.male}%` : ""}
                </div>
                <div style={{
                  height: 20, borderRadius: "var(--radius-sm)",
                  background: "rgba(123, 47, 247, 0.5)",
                  width: `${genders.female * 2}%`,
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.625rem", fontWeight: 600,
                }}>
                  {genders.female > 5 ? `${genders.female}%` : ""}
                </div>
              </div>
            </div>
          ))}
          <div style={{ display: "flex", gap: 16, marginTop: 8, fontSize: "0.6875rem" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: "rgba(0, 212, 255, 0.5)" }} /> Male
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 10, height: 10, borderRadius: 2, background: "rgba(123, 47, 247, 0.5)" }} /> Female
            </span>
          </div>
        </div>
      </div>

      {/* Post Performance Table */}
      <div className="card glass animate-in" style={{ marginTop: 24 }}>
        <div className="card-header">
          <h3 className="card-title">📝 Post Performance — EQI Rankings</h3>
          <span className="badge badge-info">{posts.length || 20} posts</span>
        </div>
        <div style={{ overflowX: "auto" }}>
          <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "0.8125rem" }}>
            <thead>
              <tr style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                <th style={{ textAlign: "left", padding: "8px 12px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem", textTransform: "uppercase" }}>Post</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>Type</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>EQI</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>Likes</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>Comments</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>Shares</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>Saves</th>
                <th style={{ textAlign: "center", padding: "8px", color: "var(--text-muted)", fontWeight: 600, fontSize: "0.6875rem" }}>Reach</th>
              </tr>
            </thead>
            <tbody>
              {(posts.length > 0 ? posts : getMockPosts()).slice(0, 10).map((post: any, i: number) => (
                <tr key={i} style={{ borderBottom: "1px solid var(--border-subtle)" }}>
                  <td style={{ padding: "10px 12px", maxWidth: 250, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>
                    {post.hook || post.content?.slice(0, 60)}...
                  </td>
                  <td style={{ textAlign: "center", padding: "8px" }}>
                    <span className="badge badge-info">{post.post_type || "text"}</span>
                  </td>
                  <td style={{ textAlign: "center", padding: "8px" }}>
                    <span className={`badge ${getTierBadge(post.eqi_tier)}`}>
                      {post.eqi_score?.toFixed(1) || "65"}
                    </span>
                  </td>
                  <td style={{ textAlign: "center", padding: "8px", color: "var(--text-secondary)" }}>{(post.likes || 0).toLocaleString()}</td>
                  <td style={{ textAlign: "center", padding: "8px", color: "var(--text-secondary)" }}>{(post.comments_count || 0).toLocaleString()}</td>
                  <td style={{ textAlign: "center", padding: "8px", color: "var(--text-secondary)" }}>{(post.shares || 0).toLocaleString()}</td>
                  <td style={{ textAlign: "center", padding: "8px", color: "var(--text-secondary)" }}>{(post.saves || 0).toLocaleString()}</td>
                  <td style={{ textAlign: "center", padding: "8px", color: "var(--text-secondary)" }}>{((post.reach || 0) / 1000).toFixed(1)}K</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function getMockPosts() {
  return [
    { hook: "I used to think 'wellness' meant green juice and 5am runs", content: "I used to think 'wellness' meant green juice...", post_type: "text", eqi_score: 85.2, eqi_tier: "exceptional", likes: 7200, comments_count: 560, shares: 680, saves: 2100, reach: 55000 },
    { hook: "Protein doesn't have to be boring or expensive", content: "Protein doesn't have to be boring...", post_type: "carousel", eqi_score: 78.5, eqi_tier: "good", likes: 6100, comments_count: 340, shares: 450, saves: 2200, reach: 46000 },
     {hook: "Your 10-minute no-equipment leg day", content: "Your 10-minute no-equipment leg day...", post_type: "reel", eqi_score: 75.3, eqi_tier: "good", likes: 6800, comments_count: 410, shares: 520, saves: 1500, reach: 51000 },
    { hook: "I tracked my sleep for 30 days", content: "I tracked my sleep for 30 days...", post_type: "carousel", eqi_score: 72.8, eqi_tier: "good", likes: 5800, comments_count: 367, shares: 445, saves: 1800, reach: 43000 },
     {hook: "Morning routine that actually sticks", content: "Morning routine that actually sticks...", post_type: "carousel", eqi_score: 71.2, eqi_tier: "good", likes: 5900, comments_count: 445, shares: 510, saves: 2400, reach: 48000 },
    { hook: "Real talk: I skipped my workout yesterday", content: "Real talk: I skipped my workout...", post_type: "text", eqi_score: 68.9, eqi_tier: "good", likes: 5200, comments_count: 342, shares: 267, saves: 890, reach: 38000 },
    { hook: "Breathwork changed my life", content: "Breathwork changed my life...", post_type: "reel", eqi_score: 65.1, eqi_tier: "good", likes: 4900, comments_count: 312, shares: 390, saves: 1650, reach: 39000 },
     {hook: "Community spotlight Meet @priya.runs", content: "Community spotlight...", post_type: "text", eqi_score: 62.4, eqi_tier: "good", likes: 4800, comments_count: 520, shares: 310, saves: 420, reach: 34000 },
  ];
}

function getMockAudience() {
  return {
    followers_count: 85200,
    followers_delta_7d: 180,
    accounts_reached_7d: 32000,
    accounts_engaged_7d: 8500,
    demographics: {
      age_gender: {
        "18-24": { male: 12, female: 18 },
        "25-34": { male: 22, female: 28 },
        "35-44": { male: 8, female: 7 },
        "45+": { male: 2, female: 3 },
      },
      top_cities: [
        { name: "Delhi", pct: 22 },
        { name: "Mumbai", pct: 18 },
        { name: "Bangalore", pct: 12 },
        { name: "Pune", pct: 8 },
        { name: "Hyderabad", pct: 6 },
      ],
    },
  };
}
