"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import ToneRadarChart from "@/components/ui/ToneRadarChart";

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
  onOpenInstagramModal?: () => void;
  instagramAccount?: any;
  refreshInstagramStatus?: () => void;
}

export default function BrandVoicePage({
  brandId,
  addToast,
  backendStatus,
  onOpenInstagramModal,
  instagramAccount,
  refreshInstagramStatus,
}: Props) {
  const [brand, setBrand] = useState<any>(null);
  const [guidelines, setGuidelines] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);

  useEffect(() => { loadBrand(); }, [brandId]);

  const loadBrand = async () => {
    setLoading(true);
    try {
      const [brandData, guidelinesData] = await Promise.all([
        api.getBrand(brandId),
        api.getGuidelines(brandId),
      ]);
      setBrand(brandData);
      setGuidelines(guidelinesData);
    } catch {
      setBrand(getMockBrand());
      setGuidelines(getMockGuidelines());
    }
    setLoading(false);
  };

  const handleSyncInstagram = async () => {
    setSyncing(true);
    try {
      addToast("info", "Syncing real Instagram posts and calibrating voice DNA...");
      const res = await api.syncInstagram(brandId, 25);
      addToast("success", `Synced ${res.posts_synced || res.total_posts_processed || 0} real posts! Voice centroid updated.`);
      await loadBrand();
      if (refreshInstagramStatus) refreshInstagramStatus();
    } catch (err: any) {
      addToast("error", `Sync failed: ${err.message}`);
    }
    setSyncing(false);
  };

  const profile = brand?.structural_profile || getMockBrand().structural_profile;
  const toneKeywords = profile?.tone_keywords || {};

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Brand Voice</h1>
          <p className="page-subtitle">Your voice fingerprint - learned from your real posts, verified on every draft.</p>
        </div>
        <div style={{ display: "flex", gap: 10 }}>
          {instagramAccount?.connected ? (
            <button
              className="btn btn-primary btn-sm"
              style={{ background: "linear-gradient(135deg, #e1306c, #833ab4)", border: "none" }}
              onClick={handleSyncInstagram}
              disabled={syncing}
            >
              {syncing ? "Syncing..." : "↻ Sync Live Instagram Posts"}
            </button>
          ) : (
            <button
              className="btn btn-primary btn-sm"
              style={{ background: "linear-gradient(135deg, #e1306c, #833ab4)", border: "none" }}
              onClick={onOpenInstagramModal}
            >
              Connect Instagram Account
            </button>
          )}
        </div>
      </div>

      {/* Instagram Live Account Callout / Status */}
      <div
        className="card glass animate-in"
        style={{
          marginBottom: 24,
          borderColor: instagramAccount?.connected ? "rgba(225, 48, 108, 0.4)" : "var(--border-accent)",
          background: instagramAccount?.connected
            ? "linear-gradient(135deg, rgba(225, 48, 108, 0.08), rgba(15, 23, 42, 0.6))"
            : undefined,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 16, flexWrap: "wrap" }}>
          {instagramAccount?.profile_picture_url || brand?.instagram_profile_pic ? (
            <img
              src={instagramAccount?.profile_picture_url || brand?.instagram_profile_pic}
              alt="Profile"
              style={{ width: 56, height: 56, borderRadius: "var(--radius-lg)", objectFit: "cover", border: "2px solid #e1306c" }}
            />
          ) : (
            <div style={{
              width: 56, height: 56, borderRadius: "var(--radius-lg)",
              background: "var(--gradient-primary)",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: "1.5rem", fontWeight: 800,
            }}>
              {(brand?.name || "F")[0]}
            </div>
          )}
          <div style={{ flex: 1, minWidth: 200 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <h2 style={{ margin: 0 }}>{brand?.name || "FitVibe"}</h2>
              {instagramAccount?.connected ? (
                <span className="badge badge-success">Instagram Connected</span>
              ) : (
                <span className="badge badge-warning">Demo Mode</span>
              )}
            </div>
            <div style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", marginTop: 4 }}>
              {brand?.handle || "@fitvibe.wellness"} • {brand?.platform || "instagram"} • {brand?.post_count || 20} posts analyzed
              {instagramAccount?.followers_count ? ` • ${instagramAccount.followers_count.toLocaleString()} followers` : ""}
            </div>
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            <button
              className="btn btn-secondary btn-sm"
              onClick={onOpenInstagramModal}
            >
              {instagramAccount?.connected ? "Manage Connection" : "Connect Real IG"}
            </button>
            {instagramAccount?.connected && (
              <button
                className="btn btn-primary btn-sm"
                onClick={handleSyncInstagram}
                disabled={syncing}
              >
                {syncing ? "Calibrating..." : "↻ Recalibrate Voice"}
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Structural Profile */}
        <div className="card glass animate-in">
          <div className="card-header">
            <h3 className="card-title">Structural Profile</h3>
            <span className="badge badge-info">Cached</span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            {[
              { label: "Avg Sentence Length", value: `${profile?.avg_sentence_length?.toFixed(1) || 8.2} words`, icon: "" },
              { label: "Emoji Frequency", value: `${profile?.emoji_frequency?.toFixed(1) || 2.1} per post`, icon: "" },
              { label: "Emoji Placement", value: profile?.emoji_placement || "inline", icon: "" },
              { label: "Hashtag Count", value: `${profile?.hashtag_count_avg?.toFixed(1) || 3.5} avg`, icon: "" },
              { label: "Hashtag Placement", value: profile?.hashtag_placement || "end", icon: "" },
              { label: "Avg Post Length", value: `${profile?.avg_post_length?.toFixed(0) || 520} chars`, icon: "" },
            ].map((item, i) => (
              <div key={i} style={{
                display: "flex", justifyContent: "space-between", alignItems: "center",
                padding: "10px 12px", background: "var(--bg-tertiary)",
                borderRadius: "var(--radius-sm)",
              }}>
                <span style={{ display: "flex", alignItems: "center", gap: 8, color: "var(--text-secondary)", fontSize: "0.8125rem" }}>
                  {item.icon} {item.label}
                </span>
                <span style={{ fontWeight: 700, fontSize: "0.875rem", color: "var(--accent-cyan)" }}>
                  {item.value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Tone Radar */}
        <div className="card glass animate-in">
          <div className="card-header">
            <h3 className="card-title">Tone Profile DNA</h3>
            <span className="badge badge-purple">Voice DNA</span>
          </div>
          
          <div style={{ display: "flex", flexDirection: "column", gap: 20 }}>
            {/* SVG Radar Chart Visualizer */}
            <div style={{ background: "rgba(0,0,0,0.2)", borderRadius: "var(--radius-md)", padding: "10px 0" }}>
              <ToneRadarChart tones={Object.keys(toneKeywords).length > 0 ? toneKeywords : getMockBrand().structural_profile.tone_keywords} />
            </div>

            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {Object.entries(toneKeywords).sort(([, a]: any, [, b]: any) => b - a).map(([tone, score]: any) => (
                <div key={tone} style={{ display: "flex", alignItems: "center", gap: 12 }}>
                  <span style={{
                    fontWeight: 600, fontSize: "0.8125rem", minWidth: 110,
                    textTransform: "capitalize", color: "var(--text-secondary)",
                  }}>
                    {tone}
                  </span>
                  <div style={{ flex: 1 }}>
                    <div className="progress-bar" style={{ height: 6 }}>
                      <div className="progress-fill" style={{
                        width: `${Math.min(score * 100, 100)}%`,
                        background: score > 0.65 ? "var(--gradient-success)" : "var(--gradient-primary)",
                      }} />
                    </div>
                  </div>
                  <span style={{ fontWeight: 700, fontSize: "0.8125rem", minWidth: 45, textAlign: "right" }}>
                    {(score * 100).toFixed(0)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div style={{ marginTop: 16, padding: "10px 12px", background: "var(--bg-tertiary)", borderRadius: "var(--radius-sm)", fontSize: "0.75rem", color: "var(--text-muted)" }}>
            These tone markers are detected from your past posts and used to constrain the Copywriter agent. The Guardrail checks every draft against this profile.
          </div>
        </div>
      </div>

      {/* Guidelines with temporal validity */}
      <div className="card glass animate-in" style={{ marginTop: 24 }}>
        <div className="card-header">
          <h3 className="card-title">Active Brand Guidelines</h3>
          <span className="badge badge-success">valid_from / valid_to filtering</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {(guidelines.length > 0 ? guidelines : getMockGuidelines()).map((gl: any, i: number) => (
            <div key={i} style={{
              padding: "16px", background: "var(--bg-tertiary)",
              borderRadius: "var(--radius-md)",
              borderLeft: `3px solid ${
                gl.category === "banned" ? "var(--accent-red)" :
                gl.category === "tone" ? "var(--accent-cyan)" :
                gl.category === "topics" ? "var(--accent-green)" : "var(--accent-purple)"
              }`,
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 8 }}>
                <span style={{ fontWeight: 700, fontSize: "0.875rem" }}>{gl.title}</span>
                <div style={{ display: "flex", gap: 8 }}>
                  <span className="badge badge-info">{gl.category}</span>
                  <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>
                    Since {gl.valid_from} {gl.valid_to ? `→ ${gl.valid_to}` : "→ current"}
                  </span>
                </div>
              </div>
              <p style={{ fontSize: "0.8125rem", color: "var(--text-secondary)", lineHeight: 1.6 }}>
                {gl.content}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function getMockBrand() {
  return {
    name: "FitVibe",
    handle: "@fitvibe.wellness",
    platform: "instagram",
    post_count: 20,
    structural_profile: {
      avg_sentence_length: 8.2,
      emoji_frequency: 2.1,
      emoji_placement: "inline",
      hashtag_count_avg: 3.5,
      hashtag_placement: "end",
      avg_post_length: 520,
      tone_keywords: {
        conversational: 0.82,
        encouraging: 0.75,
        authentic: 0.68,
        informative: 0.55,
        casual: 0.62,
      },
    },
  };
}

function getMockGuidelines() {
  return [
    { title: "Core Tone", content: "Warm, encouraging, and real. Never preachy or condescending. Use 'you' and 'we' - talk WITH the audience, not AT them.", category: "tone", valid_from: "2026-01-01" },
    { title: "Emoji Guidelines", content: "Use 1-3 emojis per post, placed naturally within sentences. Favorites: strength, fire, sparkle, leaf. Never: prayer (overused), 100 (feels dated).", category: "tone", valid_from: "2026-01-01" },
    { title: "Hashtag Strategy", content: "3-5 hashtags max, placed at the very end after a line break. Mix of branded (#FitVibeFlow) and discovery.", category: "tone", valid_from: "2026-03-01" },
    { title: "Topics to Avoid", content: "No diet culture. No before/after body transformations. No medical claims. No supplement endorsements without disclosure.", category: "banned", valid_from: "2026-01-01" },
    { title: "Content Pillars", content: "1. Workout routines (40%) 2. Nutrition (25%) 3. Mindfulness (20%) 4. Community stories (15%)", category: "topics", valid_from: "2026-01-01" },
  ];
}
