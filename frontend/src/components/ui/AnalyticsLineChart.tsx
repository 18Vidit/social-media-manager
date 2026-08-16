"use client";

import { useState, useRef, useEffect } from "react";

interface ChartDataPoint {
  label: string;
  value: number;
}

interface AnalyticsLineChartProps {
  data: ChartDataPoint[];
  height?: number;
}

export default function AnalyticsLineChart({ data, height = 200 }: AnalyticsLineChartProps) {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [width, setWidth] = useState(500);

  // Resize listener to make SVG responsive
  useEffect(() => {
    if (!containerRef.current) return;
    const handleResize = () => {
      if (containerRef.current) {
        setWidth(containerRef.current.clientWidth);
      }
    };
    handleResize();
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  if (!data || data.length === 0) return null;

  const paddingLeft = 40;
  const paddingRight = 20;
  const paddingTop = 20;
  const paddingBottom = 30;

  const chartWidth = width - paddingLeft - paddingRight;
  const chartHeight = height - paddingTop - paddingBottom;

  const values = data.map(d => d.value);
  const maxValue = Math.max(...values, 10) * 1.1; // 10% headroom
  const minValue = 0; // standard floor for analytics

  // Compute SVG coordinates
  const points = data.map((d, i) => {
    const x = paddingLeft + (i / (data.length - 1)) * chartWidth;
    const ratio = (d.value - minValue) / (maxValue - minValue);
    const y = paddingTop + chartHeight - ratio * chartHeight;
    return { x, y, label: d.label, value: d.value };
  });

  // Generate Path D string
  const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");

  // Generate Area Path (closing the shape at the bottom)
  const areaPath = points.length > 0 
    ? `${linePath} L ${points[points.length - 1].x} ${paddingTop + chartHeight} L ${points[0].x} ${paddingTop + chartHeight} Z`
    : "";

  // Grid lines
  const yTicks = 4;
  const gridLines = Array.from({ length: yTicks }, (_, i) => {
    const ratio = i / (yTicks - 1);
    const y = paddingTop + chartHeight - ratio * chartHeight;
    const val = minValue + ratio * (maxValue - minValue);
    return { y, val };
  });

  return (
    <div ref={containerRef} style={{ width: "100%", position: "relative" }}>
      <svg width={width} height={height} style={{ overflow: "visible" }}>
        <defs>
          <linearGradient id="chartGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="var(--accent-cyan)" stopOpacity="0.3" />
            <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0.0" />
          </linearGradient>
          <linearGradient id="lineGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="var(--accent-cyan)" />
            <stop offset="100%" stopColor="var(--accent-purple)" />
          </linearGradient>
        </defs>

        {/* Horizontal grid lines */}
        {gridLines.map((gl, i) => (
          <g key={i}>
            <line
              x1={paddingLeft}
              y1={gl.y}
              x2={width - paddingRight}
              y2={gl.y}
              stroke="rgba(255, 255, 255, 0.05)"
              strokeDasharray="4"
              strokeWidth="1"
            />
            <text
              x={paddingLeft - 8}
              y={gl.y + 3}
              fill="var(--text-muted)"
              fontSize="9"
              textAnchor="end"
            >
              {gl.val >= 1000 ? `${(gl.val / 1000).toFixed(1)}k` : gl.val.toFixed(0)}
            </text>
          </g>
        ))}

        {/* Gradient area under trendline */}
        {areaPath && (
          <path
            d={areaPath}
            fill="url(#chartGrad)"
          />
        )}

        {/* Glowing Trendline */}
        <path
          d={linePath}
          fill="none"
          stroke="url(#lineGrad)"
          strokeWidth="3"
          strokeLinecap="round"
          strokeLinejoin="round"
          filter="drop-shadow(0px 2px 4px rgba(0, 212, 255, 0.3))"
        />

        {/* X Axis Labels */}
        {points.map((p, i) => (
          // Render label only for every Nth point to avoid overlaps if data is dense
          (i % Math.ceil(data.length / 7) === 0 || i === data.length - 1) && (
            <text
              key={i}
              x={p.x}
              y={height - 8}
              fill="var(--text-muted)"
              fontSize="9"
              textAnchor="middle"
            >
              {p.label}
            </text>
          )
        ))}

        {/* Interactive hover guides */}
        {hoveredIdx !== null && points[hoveredIdx] && (
          <g>
            <line
              x1={points[hoveredIdx].x}
              y1={paddingTop}
              x2={points[hoveredIdx].x}
              y2={paddingTop + chartHeight}
              stroke="rgba(0, 212, 255, 0.3)"
              strokeWidth="1.5"
              strokeDasharray="2"
            />
            <circle
              cx={points[hoveredIdx].x}
              cy={points[hoveredIdx].y}
              r="7"
              fill="var(--accent-cyan)"
              stroke="var(--bg-primary)"
              strokeWidth="2"
            />
          </g>
        )}

        {/* Transparent hover regions for easy interaction */}
        {points.map((p, i) => {
          const colWidth = chartWidth / (data.length - 1 || 1);
          const activeX = p.x - colWidth / 2;
          return (
            <rect
              key={i}
              x={activeX}
              y={paddingTop}
              width={colWidth}
              height={chartHeight}
              fill="transparent"
              style={{ cursor: "pointer" }}
              onMouseEnter={() => setHoveredIdx(i)}
              onMouseLeave={() => setHoveredIdx(null)}
            />
          );
        })}
      </svg>

      {/* Dynamic Tooltip */}
      {hoveredIdx !== null && points[hoveredIdx] && (
        <div style={{
          position: "absolute",
          top: points[hoveredIdx].y - 50,
          left: Math.min(width - 120, Math.max(10, points[hoveredIdx].x - 60)),
          background: "rgba(15, 15, 15, 0.95)",
          border: "1px solid var(--accent-cyan)",
          borderRadius: "var(--radius-sm)",
          boxShadow: "var(--shadow-glow)",
          padding: "6px 10px",
          zIndex: 50,
          pointerEvents: "none",
          fontSize: "0.75rem",
          minWidth: "110px",
          textAlign: "center"
        }}>
          <div style={{ color: "var(--text-muted)", fontSize: "0.625rem" }}>
            {points[hoveredIdx].label}
          </div>
          <div style={{ color: "var(--accent-green)", fontWeight: 700, marginTop: 2 }}>
            {points[hoveredIdx].value.toLocaleString()} Engagements
          </div>
        </div>
      )}
    </div>
  );
}
