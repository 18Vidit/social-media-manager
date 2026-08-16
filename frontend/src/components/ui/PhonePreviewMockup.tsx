"use client";

import { useState } from "react";

interface PhonePreviewMockupProps {
  content: string;
  handle?: string;
  name?: string;
  likes?: number;
  commentsCount?: number;
}

type PlatformTab = "instagram" | "reels" | "twitter";

export default function PhonePreviewMockup({
  content,
  handle = "@fitvibe.wellness",
  name = "FitVibe",
  likes = 7200,
  commentsCount = 560
}: PhonePreviewMockupProps) {
  const [platform, setPlatform] = useState<PlatformTab>("instagram");

  // Format hashtags and tags visually
  const formatContentText = (text: string) => {
    if (!text) return "";
    return text.split(/(\s+)/).map((part, i) => {
      if (part.startsWith("#")) {
        return <span key={i} style={{ color: "var(--accent-cyan)", fontWeight: 500 }}>{part}</span>;
      }
      if (part.startsWith("@")) {
        return <span key={i} style={{ color: "var(--accent-cyan)", fontWeight: 500 }}>{part}</span>;
      }
      return part;
    });
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 16 }}>
      {/* Platform Toggle Tabs */}
      <div style={{
        display: "flex",
        background: "rgba(255, 255, 255, 0.04)",
        padding: 4,
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--border-subtle)",
        gap: 4
      }}>
        {(["instagram", "reels", "twitter"] as PlatformTab[]).map(tab => (
          <button
            key={tab}
            onClick={() => setPlatform(tab)}
            style={{
              padding: "6px 12px",
              borderRadius: "var(--radius-sm)",
              fontSize: "0.75rem",
              fontWeight: 600,
              background: platform === tab ? "rgba(0, 212, 255, 0.15)" : "transparent",
              color: platform === tab ? "var(--accent-cyan)" : "var(--text-secondary)",
              border: "none",
              cursor: "pointer",
              textTransform: "capitalize",
              transition: "all var(--transition-fast)"
            }}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Phone Body Container */}
      <div style={{
        width: 280,
        height: 520,
        borderRadius: 36,
        border: "8px solid #222",
        boxShadow: "0 20px 40px rgba(0,0,0,0.8), inset 0 0 4px rgba(255,255,255,0.2)",
        position: "relative",
        background: "#000",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column"
      }}>
        {/* Dynamic Island Notch */}
        <div style={{
          position: "absolute",
          top: 6,
          left: "50%",
          transform: "translateX(-50%)",
          width: 80,
          height: 18,
          borderRadius: 9,
          background: "#111",
          zIndex: 10,
          border: "1px solid rgba(255,255,255,0.05)"
        }} />

        {/* Dynamic Inner Layout */}
        {platform === "instagram" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "24px 12px 12px" }}>
            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 8, marginTop: 4 }}>
              <div style={{
                width: 28, height: 28, borderRadius: "50%",
                background: "var(--gradient-primary)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 10, fontWeight: 800, color: "#fff"
              }}>{name[0]}</div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: 10, fontWeight: 700, color: "#fff" }}>{name}</span>
                <span style={{ fontSize: 8, color: "var(--text-muted)" }}>Sponsored</span>
              </div>
              <span style={{ marginLeft: "auto", fontSize: 12, color: "#fff" }}>•••</span>
            </div>

            {/* Simulated Post Image Box */}
            <div style={{
              width: "100%",
              aspectRatio: "1/1",
              borderRadius: "var(--radius-md)",
              background: "linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(123, 47, 247, 0.2) 100%)",
              border: "1px solid rgba(255,255,255,0.05)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              overflow: "hidden",
              marginBottom: 8
            }}>
              <div style={{
                position: "absolute", width: "80%", height: "80%", borderRadius: "50%",
                background: "var(--gradient-primary)", filter: "blur(40px)", opacity: 0.5
              }} />
              <div style={{
                zIndex: 2, padding: 12, textAlign: "center",
                fontSize: 14, fontWeight: 800, color: "#fff", textShadow: "0 2px 4px rgba(0,0,0,0.5)"
              }}>
                {name.toUpperCase()}
              </div>
            </div>

            {/* Interaction Icons */}
            <div style={{ display: "flex", gap: 12, marginBottom: 6 }}>
              <span style={{ cursor: "pointer", fontSize: 12 }}>❤️</span>
              <span style={{ cursor: "pointer", fontSize: 12 }}>💬</span>
              <span style={{ cursor: "pointer", fontSize: 12 }}>✈️</span>
              <span style={{ marginLeft: "auto", cursor: "pointer", fontSize: 12 }}>💾</span>
            </div>

            {/* Likes */}
            <div style={{ fontSize: 9, fontWeight: 700, color: "#fff", marginBottom: 4 }}>
              {likes.toLocaleString()} likes
            </div>

            {/* Caption Text Box */}
            <div style={{
              flex: 1, overflowY: "auto", paddingRight: 4,
              fontSize: 9, lineHeight: 1.4, color: "var(--text-secondary)"
            }}>
              <span style={{ fontWeight: 700, color: "#fff", marginRight: 4 }}>{handle}</span>
              {formatContentText(content)}
            </div>
          </div>
        )}

        {platform === "reels" && (
          <div style={{
            flex: 1, position: "relative",
            background: "linear-gradient(180deg, #111 0%, #000 100%)",
            display: "flex", flexDirection: "column", justifyContent: "flex-end",
            padding: "24px 12px 12px"
          }}>
            {/* Reel Mockup Image Backdrop */}
            <div style={{
              position: "absolute", inset: 0,
              background: "linear-gradient(210deg, #1a0826 0%, #081a26 100%)",
              zIndex: 1
            }} />
            <div style={{
              position: "absolute", top: "40%", left: "50%", transform: "translate(-50%, -50%)",
              width: 140, height: 140, borderRadius: "50%", background: "var(--gradient-primary)",
              filter: "blur(50px)", opacity: 0.4, zIndex: 1
            }} />

            {/* Right-aligned floating action buttons */}
            <div style={{
              position: "absolute", right: 8, bottom: 60,
              display: "flex", flexDirection: "column", gap: 14, alignItems: "center",
              zIndex: 3
            }}>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span style={{ fontSize: 14 }}>❤️</span>
                <span style={{ fontSize: 7, color: "#fff", marginTop: 2 }}>{likes >= 1000 ? `${(likes/1000).toFixed(1)}k` : likes}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span style={{ fontSize: 14 }}>💬</span>
                <span style={{ fontSize: 7, color: "#fff", marginTop: 2 }}>{commentsCount}</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span style={{ fontSize: 14 }}>✈️</span>
              </div>
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center" }}>
                <span style={{ fontSize: 14 }}>💾</span>
              </div>
            </div>

            {/* Reel text info */}
            <div style={{ zIndex: 2, marginRight: 40, display: "flex", flexDirection: "column", gap: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{
                  width: 24, height: 24, borderRadius: "50%",
                  background: "var(--gradient-primary)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  fontSize: 8, fontWeight: 800, color: "#fff"
                }}>{name[0]}</div>
                <span style={{ fontSize: 10, fontWeight: 700, color: "#fff" }}>{handle}</span>
                <span style={{
                  padding: "1px 4px", border: "1px solid #fff", borderRadius: 3,
                  fontSize: 7, fontWeight: 600, color: "#fff"
                }}>Follow</span>
              </div>

              {/* Caption text */}
              <div style={{
                maxHeight: 120, overflowY: "auto",
                fontSize: 9, lineHeight: 1.4, color: "#eee",
                textShadow: "0 1px 2px rgba(0,0,0,0.8)"
              }}>
                {formatContentText(content)}
              </div>

              {/* Music indicator */}
              <div style={{ display: "flex", alignItems: "center", gap: 4, fontSize: 8, color: "var(--accent-cyan)" }}>
                <span>🎵</span> Original Audio - {name}
              </div>
            </div>
          </div>
        )}

        {platform === "twitter" && (
          <div style={{ flex: 1, display: "flex", flexDirection: "column", padding: "24px 14px 12px", background: "#000" }}>
            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 10, marginTop: 4 }}>
              <div style={{
                width: 32, height: 32, borderRadius: "50%",
                background: "var(--gradient-primary)",
                display: "flex", alignItems: "center", justifyContent: "center",
                fontSize: 12, fontWeight: 800, color: "#fff"
              }}>{name[0]}</div>
              <div style={{ display: "flex", flexDirection: "column" }}>
                <span style={{ fontSize: 11, fontWeight: 800, color: "#fff", display: "flex", alignItems: "center", gap: 2 }}>
                  {name} <span style={{ color: "var(--accent-cyan)", fontSize: 8 }}>✓</span>
                </span>
                <span style={{ fontSize: 9, color: "var(--text-muted)" }}>{handle}</span>
              </div>
              <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>𝕏</span>
            </div>

            {/* Tweet content */}
            <div style={{
              flex: 1, overflowY: "auto", fontSize: 11,
              lineHeight: 1.5, color: "#e7e9ea", marginBottom: 12
            }}>
              {formatContentText(content)}
            </div>

            {/* Divider */}
            <div style={{ height: "1px", background: "rgba(255,255,255,0.08)", marginBottom: 8 }} />

            {/* Date time */}
            <div style={{ fontSize: 8, color: "var(--text-muted)", marginBottom: 8 }}>
              {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • {new Date().toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' })}
            </div>

            {/* Divider */}
            <div style={{ height: "1px", background: "rgba(255,255,255,0.08)", marginBottom: 8 }} />

            {/* Tweet stats */}
            <div style={{ display: "flex", gap: 14, fontSize: 8, color: "var(--text-muted)", marginBottom: 8 }}>
              <span><strong>12</strong> Reposts</span>
              <span><strong>{likes.toLocaleString()}</strong> Likes</span>
            </div>

            {/* Divider */}
            <div style={{ height: "1px", background: "rgba(255,255,255,0.08)", marginBottom: 8 }} />

            {/* Actions */}
            <div style={{ display: "flex", justifyContent: "space-between", padding: "0 8px", color: "var(--text-muted)", fontSize: 11 }}>
              <span>💬</span>
              <span>🔁</span>
              <span>❤️</span>
              <span>🔖</span>
              <span>📤</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
