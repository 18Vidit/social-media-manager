"use client";

import { useState } from "react";

interface ToneData {
  [key: string]: number;
}

interface ToneRadarChartProps {
  tones: ToneData;
}

export default function ToneRadarChart({ tones }: ToneRadarChartProps) {
  const [hoveredPoint, setHoveredPoint] = useState<{
    name: string;
    value: number;
    x: number;
    y: number;
  } | null>(null);

  const keys = Object.keys(tones);
  const totalAxes = keys.length;
  if (totalAxes < 3) return null; // Radar chart needs at least 3 axes

  const width = 340;
  const height = 300;
  const centerX = width / 2;
  const centerY = height / 2;
  const maxRadius = 100;

  // Compute coordinate helper
  const getCoordinates = (index: number, radius: number) => {
    // Offset by -Math.PI / 2 to start at top center
    const angle = (Math.PI * 2 / totalAxes) * index - Math.PI / 2;
    return {
      x: centerX + Math.cos(angle) * radius,
      y: centerY + Math.sin(angle) * radius,
    };
  };

  // 1. Grid levels (concentric polygons)
  const gridLevels = [0.25, 0.5, 0.75, 1.0];
  const gridPaths = gridLevels.map(level => {
    const points = Array.from({ length: totalAxes }, (_, idx) => {
      const { x, y } = getCoordinates(idx, maxRadius * level);
      return `${x},${y}`;
    }).join(" ");
    return points;
  });

  // 2. Axis lines & labels
  const axes = Array.from({ length: totalAxes }, (_, idx) => {
    const toneName = keys[idx];
    const outerPoint = getCoordinates(idx, maxRadius);
    const labelPos = getCoordinates(idx, maxRadius + 22); // extra padding for labels
    
    // Fine-tune label text anchor
    let textAnchor: "start" | "end" | "middle" = "middle";
    if (outerPoint.x > centerX + 10) textAnchor = "start";
    else if (outerPoint.x < centerX - 10) textAnchor = "end";

    return {
      name: toneName,
      line: { x1: centerX, y1: centerY, x2: outerPoint.x, y2: outerPoint.y },
      label: { x: labelPos.x, y: labelPos.y, textAnchor }
    };
  });

  // 3. Brand Voice Polygon
  const polygonPoints = Array.from({ length: totalAxes }, (_, idx) => {
    const value = tones[keys[idx]];
    const { x, y } = getCoordinates(idx, maxRadius * value);
    return `${x},${y}`;
  }).join(" ");

  // 4. Highlight points for hover triggers
  const vertexPoints = Array.from({ length: totalAxes }, (_, idx) => {
    const name = keys[idx];
    const value = tones[name];
    const { x, y } = getCoordinates(idx, maxRadius * value);
    return { name, value, x, y };
  });

  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", position: "relative", width: "100%" }}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} style={{ maxWidth: width }}>
        <defs>
          <radialGradient id="radarGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.4" />
            <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0.0" />
          </radialGradient>
          <linearGradient id="polyGrad" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="rgba(0, 212, 255, 0.4)" />
            <stop offset="100%" stopColor="rgba(123, 47, 247, 0.4)" />
          </linearGradient>
        </defs>

        {/* Concentric grid lines */}
        {gridPaths.map((path, idx) => (
          <polygon
            key={idx}
            points={path}
            fill="none"
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="1"
          />
        ))}

        {/* Level labels (e.g. 50%, 100%) */}
        <text x={centerX} y={centerY - maxRadius * 0.5 + 4} fill="var(--text-muted)" fontSize="8" textAnchor="middle">50%</text>
        <text x={centerX} y={centerY - maxRadius * 1.0 + 4} fill="var(--text-muted)" fontSize="8" textAnchor="middle">100%</text>

        {/* Axial spokes */}
        {axes.map((axis, idx) => (
          <line
            key={idx}
            x1={axis.line.x1}
            y1={axis.line.y1}
            x2={axis.line.x2}
            y2={axis.line.y2}
            stroke="rgba(255, 255, 255, 0.08)"
            strokeWidth="1"
          />
        ))}

        {/* Filled Data Polygon */}
        <polygon
          points={polygonPoints}
          fill="url(#polyGrad)"
          stroke="var(--accent-cyan)"
          strokeWidth="2.5"
          filter="drop-shadow(0px 0px 8px rgba(0, 212, 255, 0.5))"
          style={{ transition: "all 0.5s ease-in-out" }}
        />

        {/* Tone Labels */}
        {axes.map((axis, idx) => (
          <text
            key={idx}
            x={axis.label.x}
            y={axis.label.y + 3} // vertical centering nudge
            fill="var(--text-secondary)"
            fontSize="10"
            fontWeight="600"
            textAnchor={axis.label.textAnchor}
            style={{ textTransform: "capitalize", letterSpacing: "0.05em" }}
          >
            {axis.name}
          </text>
        ))}

        {/* Hover trigger dots */}
        {vertexPoints.map((pt, idx) => (
          <circle
            key={idx}
            cx={pt.x}
            cy={pt.y}
            r={hoveredPoint?.name === pt.name ? 6 : 4}
            fill={hoveredPoint?.name === pt.name ? "var(--accent-green)" : "var(--accent-cyan)"}
            stroke="var(--bg-primary)"
            strokeWidth="1.5"
            style={{ cursor: "pointer", transition: "r 0.15s ease, fill 0.15s ease" }}
            onMouseEnter={() => setHoveredPoint(pt)}
            onMouseLeave={() => setHoveredPoint(null)}
          />
        ))}
      </svg>

      {/* Tooltip Overlay */}
      {hoveredPoint && (
        <div style={{
          position: "absolute",
          top: hoveredPoint.y - 45,
          left: hoveredPoint.x - 50,
          width: 100,
          background: "rgba(10, 10, 10, 0.95)",
          border: "1px solid var(--accent-cyan)",
          boxShadow: "var(--shadow-glow)",
          borderRadius: "var(--radius-sm)",
          padding: "4px 8px",
          textAlign: "center",
          fontSize: "0.6875rem",
          pointerEvents: "none",
          zIndex: 10,
          animation: "fadeIn 0.15s ease"
        }}>
          <div style={{ fontWeight: 700, color: "var(--text-primary)", textTransform: "capitalize" }}>
            {hoveredPoint.name}
          </div>
          <div style={{ color: "var(--accent-green)", fontWeight: 600, marginTop: 2 }}>
            {(hoveredPoint.value * 100).toFixed(0)}% Tone Match
          </div>
        </div>
      )}
    </div>
  );
}
