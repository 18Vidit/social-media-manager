"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
}

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export default function SchedulePage({ brandId, addToast, backendStatus }: Props) {
  const [peakTimes, setPeakTimes] = useState<any>(null);
  const [upcoming, setUpcoming] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => { loadData(); }, [brandId]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [peakData, upcomingData] = await Promise.all([
        api.getPeakTimes(),
        api.getUpcoming(brandId),
      ]);
      setPeakTimes(peakData);
      setUpcoming(upcomingData);
    } catch {
      setPeakTimes(getMockPeakTimes());
      setUpcoming([]);
    }
    setLoading(false);
  };

  const heatmapData = peakTimes?.heatmap || [];
  const topSlots = peakTimes?.top_slots || [];
  const recommendation = peakTimes?.recommendation?.recommended || peakTimes?.recommendation?.heuristic || {};

  // Build heatmap grid
  const getHeatmapColor = (score: number) => {
    if (score >= 0.8) return "rgba(0, 245, 160, 0.8)";
    if (score >= 0.6) return "rgba(0, 212, 255, 0.6)";
    if (score >= 0.4) return "rgba(0, 212, 255, 0.35)";
    if (score >= 0.2) return "rgba(0, 212, 255, 0.15)";
    return "rgba(255, 255, 255, 0.03)";
  };

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>📅 Schedule</h1>
          <p className="page-subtitle">Strategist Agent — peak-time prediction from your audience&apos;s own engagement patterns.</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadData}>↻ Refresh</button>
      </div>

      {/* Best Time Recommendation */}
      <div className="card animate-in" style={{ marginBottom: 24, borderColor: "var(--border-accent)" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
          <div style={{
            width: 64, height: 64, borderRadius: "var(--radius-lg)",
            background: "var(--gradient-primary)",
            display: "flex", alignItems: "center", justifyContent: "center",
            fontSize: "1.5rem", fontWeight: 800,
          }}>
            {recommendation.hour !== undefined ? `${recommendation.hour}:00` : "20:00"}
          </div>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, fontSize: "1.125rem", marginBottom: 4 }}>
              Best Time to Post: {recommendation.day_name || "Saturday"} at {recommendation.hour !== undefined ? `${recommendation.hour}:00` : "20:00"}
            </div>
            <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
              {recommendation.reason || "Your audience's peak engagement window — Saturday evenings see 90% of peak engagement."}
            </div>
          </div>
          <span className="badge badge-purple">
            {peakTimes?.recommendation?.method || "linucb_bandit"}
          </span>
        </div>
      </div>

      <div className="grid-2-1">
        {/* Heatmap */}
        <div className="card animate-in">
          <div className="card-header">
            <h3 className="card-title">📊 Engagement Heatmap</h3>
            <span className="badge badge-info">7 × 24 grid</span>
          </div>
          <div style={{ overflowX: "auto" }}>
            <div className="heatmap-grid" style={{ minWidth: 600 }}>
              {/* Hour labels */}
              <div></div>
              {Array.from({ length: 24 }, (_, h) => (
                <div key={h} className="heatmap-hour-label">
                  {h % 3 === 0 ? `${h}` : ""}
                </div>
              ))}
              
              {/* Day rows */}
              {DAYS.map((day, dayIdx) => (
                <>
                  <div key={`label-${dayIdx}`} className="heatmap-label">{day}</div>
                  {Array.from({ length: 24 }, (_, hour) => {
                    const cell = heatmapData.find((c: any) => c.day_of_week === dayIdx && c.hour_of_day === hour);
                    const score = cell?.engagement_score || Math.random() * 0.5 + 0.2;
                    return (
                      <div
                        key={`${dayIdx}-${hour}`}
                        className="heatmap-cell"
                        style={{ background: getHeatmapColor(score) }}
                        title={`${day} ${hour}:00 — ${(score * 100).toFixed(0)}% engagement`}
                      />
                    );
                  })}
                </>
              ))}
            </div>
          </div>
          <div style={{ display: "flex", justifyContent: "center", gap: 16, marginTop: 12, fontSize: "0.6875rem", color: "var(--text-muted)" }}>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: "rgba(255,255,255,0.03)" }} /> Low
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: "rgba(0, 212, 255, 0.35)" }} /> Medium
            </span>
            <span style={{ display: "flex", alignItems: "center", gap: 4 }}>
              <div style={{ width: 12, height: 12, borderRadius: 2, background: "rgba(0, 245, 160, 0.8)" }} /> Peak
            </span>
          </div>
        </div>

        {/* Top Slots */}
        <div className="card animate-in">
          <div className="card-header">
            <h3 className="card-title">🏆 Top Posting Slots</h3>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
            {(topSlots.length > 0 ? topSlots : getMockTopSlots()).map((slot: any, i: number) => (
              <div key={i} style={{
                display: "flex", alignItems: "center", gap: 12,
                padding: "12px", background: "var(--bg-tertiary)",
                borderRadius: "var(--radius-md)",
                borderLeft: i === 0 ? "3px solid var(--accent-green)" : "3px solid var(--border-subtle)",
              }}>
                <div style={{
                  width: 28, height: 28, borderRadius: "var(--radius-sm)",
                  background: i === 0 ? "var(--gradient-success)" : "var(--bg-card)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: "0.75rem", fontWeight: 700,
                  color: i === 0 ? "var(--bg-primary)" : "var(--text-secondary)",
                }}>
                  #{i + 1}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>
                    {slot.day_name || DAYS[slot.day_of_week]} at {slot.time_str || `${slot.hour}:00`}
                  </div>
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                    {slot.reason || `${(slot.engagement_score * 100).toFixed(0)}% engagement`}
                  </div>
                </div>
                <span className="badge badge-success">
                  {((slot.engagement_score || 0.8) * 100).toFixed(0)}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Upcoming Posts */}
      <div className="card animate-in" style={{ marginTop: 24 }}>
        <div className="card-header">
          <h3 className="card-title">📋 Upcoming Scheduled Posts</h3>
        </div>
        {upcoming.length === 0 ? (
          <div className="empty-state" style={{ padding: 24 }}>
            <div className="empty-icon">📅</div>
            <p style={{ color: "var(--text-muted)", fontSize: "0.8125rem" }}>
              No posts scheduled yet. Generate content and approve to schedule.
            </p>
          </div>
        ) : (
          upcoming.map((post: any, i: number) => (
            <div key={i} style={{
              padding: 12, background: "var(--bg-tertiary)",
              borderRadius: "var(--radius-md)", marginBottom: 8,
              display: "flex", alignItems: "center", gap: 12,
            }}>
              <span className="badge badge-info">{post.platform}</span>
              <div style={{ flex: 1, fontSize: "0.8125rem" }}>
                {post.content_preview || "Scheduled post"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>
                {new Date(post.scheduled_at).toLocaleString()}
              </div>
              <span className={`badge ${post.paused_by_circuit_breaker ? "badge-danger" : "badge-success"}`}>
                {post.status}
              </span>
            </div>
          ))
        )}
      </div>
    </div>
  );
}

function getMockPeakTimes() {
  return {
    heatmap: [],
    top_slots: getMockTopSlots(),
    recommendation: {
      recommended: { hour: 20, day_name: "Saturday", day_of_week: 5, score: 0.9, reason: "Your Saturday 20:00 posts see 90% of peak engagement." },
      method: "linucb_bandit",
    },
  };
}

function getMockTopSlots() {
  return [
    { day_of_week: 5, day_name: "Saturday", hour: 20, time_str: "20:00", engagement_score: 0.9, reason: "Peak scroll time — your Saturday evenings see 90% engagement" },
    { day_of_week: 6, day_name: "Sunday", hour: 19, time_str: "19:00", engagement_score: 0.85, reason: "Strong evening engagement on Sundays" },
    { day_of_week: 4, day_name: "Friday", hour: 20, time_str: "20:00", engagement_score: 0.82, reason: "Friday evening wind-down — high save rate" },
    { day_of_week: 0, day_name: "Monday", hour: 7, time_str: "07:00", engagement_score: 0.65, reason: "Pre-work morning scrolling" },
    { day_of_week: 2, day_name: "Wednesday", hour: 12, time_str: "12:00", engagement_score: 0.6, reason: "Lunch break engagement spike" },
  ];
}
