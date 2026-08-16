"use client";

import { useState } from "react";

interface CommentItem {
  content?: string;
  text?: string;
  author_username?: string;
  author?: string;
  sentiment_label?: string;
  sentiment_score?: number;
  intent?: string;
  intent_confidence?: number;
  brand_risk?: number;
  triage_action?: string;
  auto_reply?: string;
  drafted_reply?: string;
  is_verified?: boolean;
  author_is_verified?: boolean;
}

interface InteractiveRiskMatrixProps {
  triageData: {
    high_conf_low_risk: CommentItem[];
    high_conf_high_risk: CommentItem[];
    low_conf_low_risk: CommentItem[];
    low_conf_high_risk: CommentItem[];
  };
  onSelectComment?: (comment: CommentItem) => void;
}

export default function InteractiveRiskMatrix({ triageData, onSelectComment }: InteractiveRiskMatrixProps) {
  const [hoveredNode, setHoveredNode] = useState<{
    comment: CommentItem;
    x: number;
    y: number;
    color: string;
  } | null>(null);

  const width = 340;
  const height = 300;
  const padding = 20;

  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;

  // Helper to generate seed-based coordinates within quadrants
  const getCoordinatesForQuadrant = (
    quadrant: "auto-reply" | "review" | "log" | "escalate",
    index: number,
    total: number
  ) => {
    // Generate static spread using index so bubbles don't cluster directly on top of each other
    const seed = (index + 1) * 37.5;
    const jitterX = (seed % 20) - 10; // -10 to 10
    const jitterY = ((seed * 13) % 20) - 10; // -10 to 10

    let basePctX = 25;
    let basePctY = 75;
    let color = "var(--accent-green)";

    switch (quadrant) {
      case "auto-reply": // Top Left (High Conf, Low Risk)
        basePctX = 25;
        basePctY = 75;
        color = "var(--accent-green)";
        break;
      case "review": // Top Right (High Conf, High Risk)
        basePctX = 75;
        basePctY = 75;
        color = "var(--accent-yellow)";
        break;
      case "log": // Bottom Left (Low Conf, Low Risk)
        basePctX = 25;
        basePctY = 25;
        color = "var(--text-muted)";
        break;
      case "escalate": // Bottom Right (Low Conf, High Risk)
        basePctX = 75;
        basePctY = 25;
        color = "var(--accent-red)";
        break;
    }

    const x = padding + (basePctX / 100) * chartWidth + jitterX;
    // SVG y runs top-to-bottom, so invert Y percentage
    const y = padding + ((100 - basePctY) / 100) * chartHeight + jitterY;

    return { x, y, color };
  };

  // Compile all points
  const points: { x: number; y: number; color: string; comment: CommentItem }[] = [];

  triageData.high_conf_low_risk.forEach((c, i) => {
    const coords = getCoordinatesForQuadrant("auto-reply", i, triageData.high_conf_low_risk.length);
    points.push({ ...coords, comment: c });
  });

  triageData.high_conf_high_risk.forEach((c, i) => {
    const coords = getCoordinatesForQuadrant("review", i, triageData.high_conf_high_risk.length);
    points.push({ ...coords, comment: c });
  });

  triageData.low_conf_low_risk.forEach((c, i) => {
    const coords = getCoordinatesForQuadrant("log", i, triageData.low_conf_low_risk.length);
    points.push({ ...coords, comment: c });
  });

  triageData.low_conf_high_risk.forEach((c, i) => {
    const coords = getCoordinatesForQuadrant("escalate", i, triageData.low_conf_high_risk.length);
    points.push({ ...coords, comment: c });
  });

  return (
    <div style={{ position: "relative", width: "100%", display: "flex", flexDirection: "column", alignItems: "center" }}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ maxWidth: width, background: "rgba(255,255,255,0.01)", borderRadius: "var(--radius-lg)", border: "1px solid var(--border-subtle)" }}>
        {/* Quadrant Divider Axes */}
        <line
          x1={width / 2}
          y1={padding}
          x2={width / 2}
          y2={height - padding}
          stroke="rgba(255, 255, 255, 0.15)"
          strokeWidth="1.5"
          strokeDasharray="4"
        />
        <line
          x1={padding}
          y1={height / 2}
          x2={width - padding}
          y2={height / 2}
          stroke="rgba(255, 255, 255, 0.15)"
          strokeWidth="1.5"
          strokeDasharray="4"
        />

        {/* Axis Labels */}
        <text x={width - padding} y={height / 2 + 14} fill="var(--text-muted)" fontSize="8" fontWeight="600" textAnchor="end">BRAND RISK →</text>
        <text x={width / 2 + 6} y={padding + 8} fill="var(--text-muted)" fontSize="8" fontWeight="600" textAnchor="start">CONFIDENCE ↑</text>

        {/* Quadrant Labels */}
        <text x={padding + 8} y={padding + 16} fill="var(--accent-green)" fontSize="9" fontWeight="700" opacity="0.6">AUTO-REPLY</text>
        <text x={width - padding - 8} y={padding + 16} fill="var(--accent-yellow)" fontSize="9" fontWeight="700" opacity="0.6" textAnchor="end">REVIEW</text>
        <text x={padding + 8} y={height - padding - 8} fill="var(--text-muted)" fontSize="9" fontWeight="700" opacity="0.6">LOG ONLY</text>
        <text x={width - padding - 8} y={height - padding - 8} fill="var(--accent-red)" fontSize="9" fontWeight="700" opacity="0.6" textAnchor="end">ESCALATE</text>

        {/* Data Bubbles */}
        {points.map((pt, idx) => {
          const isHovered = hoveredNode?.comment.content === pt.comment.content;
          return (
            <g key={idx} style={{ cursor: "pointer" }} onClick={() => onSelectComment?.(pt.comment)}>
              {/* Pulsing ring for high threat/escalations */}
              {pt.color === "var(--accent-red)" && (
                <circle
                  cx={pt.x}
                  cy={pt.y}
                  r={isHovered ? 12 : 9}
                  fill="none"
                  stroke={pt.color}
                  strokeWidth="1"
                  opacity="0.5"
                  style={{ transformOrigin: `${pt.x}px ${pt.y}px` }}
                >
                  <animate attributeName="r" values="7;14;7" dur="2s" repeatCount="indefinite" />
                  <animate attributeName="opacity" values="0.6;0.1;0.6" dur="2s" repeatCount="indefinite" />
                </circle>
              )}
              <circle
                cx={pt.x}
                cy={pt.y}
                r={isHovered ? 8 : 6}
                fill={pt.color}
                stroke="#0a0a0a"
                strokeWidth="1.5"
                filter={`drop-shadow(0px 0px 4px ${pt.color})`}
                style={{ transition: "all 0.15s ease" }}
                onMouseEnter={() => setHoveredNode(pt)}
                onMouseLeave={() => setHoveredNode(null)}
              />
            </g>
          );
        })}
      </svg>

      {/* Dynamic Tooltip popup */}
      {hoveredNode && (
        <div style={{
          position: "absolute",
          top: hoveredNode.y - 65,
          left: Math.min(width - 150, Math.max(10, hoveredNode.x - 75)),
          width: 150,
          background: "rgba(10, 10, 10, 0.95)",
          border: `1px solid ${hoveredNode.color}`,
          boxShadow: "var(--shadow-glow)",
          borderRadius: "var(--radius-sm)",
          padding: "6px 10px",
          zIndex: 10,
          pointerEvents: "none",
          animation: "fadeIn 0.15s ease",
          fontSize: "0.75rem"
        }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 4 }}>
            <span style={{ fontWeight: 700, color: "var(--text-primary)" }}>
              @{hoveredNode.comment.author_username || hoveredNode.comment.author || "user"}
            </span>
            <span style={{
              fontSize: "0.5625rem",
              padding: "1px 4px",
              borderRadius: "var(--radius-full)",
              background: hoveredNode.comment.sentiment_label === "positive" ? "rgba(0, 245, 160, 0.15)" :
                          hoveredNode.comment.sentiment_label === "negative" ? "rgba(255, 59, 92, 0.15)" : "rgba(255,255,255,0.08)",
              color: hoveredNode.comment.sentiment_label === "positive" ? "var(--accent-green)" :
                     hoveredNode.comment.sentiment_label === "negative" ? "var(--accent-red)" : "var(--text-secondary)"
            }}>
              {hoveredNode.comment.sentiment_label || "neutral"}
            </span>
          </div>
          <p style={{
            color: "var(--text-secondary)",
            fontSize: "0.6875rem",
            textOverflow: "ellipsis",
            whiteSpace: "nowrap",
            overflow: "hidden",
            margin: 0
          }}>
            {hoveredNode.comment.content || hoveredNode.comment.text}
          </p>
          <div style={{ marginTop: 4, display: "flex", justifyContent: "space-between", fontSize: "0.625rem", color: "var(--text-muted)" }}>
            <span>Intent: {hoveredNode.comment.intent}</span>
            <span>Conf: {((hoveredNode.comment.intent_confidence || 0.8) * 100).toFixed(0)}%</span>
          </div>
        </div>
      )}
    </div>
  );
}
