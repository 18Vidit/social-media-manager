"use client";

import { useState } from "react";

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
}

export default function PipelineTracePage({ brandId, addToast, backendStatus }: Props) {
  const [selectedTrace, setSelectedTrace] = useState(0);

  const traces = getMockTraces();
  const trace = traces[selectedTrace];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>🔗 Pipeline Trace</h1>
          <p className="page-subtitle">Explainability panel — see exactly how each agent contributed to every decision.</p>
        </div>
      </div>

      {/* Architecture Overview */}
      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3 className="card-title">🏗️ Pipeline Architecture</h3>
          <span className="badge badge-purple">LangGraph</span>
        </div>
        <div style={{
          display: "flex", alignItems: "center", justifyContent: "center",
          gap: 8, padding: "16px 0", flexWrap: "wrap",
        }}>
          {[
            { name: "Trigger", icon: "⚡", color: "var(--accent-cyan)" },
            { name: "→", icon: "", color: "var(--text-muted)" },
            { name: "Scout", icon: "🔍", color: "var(--accent-cyan)" },
            { name: "→", icon: "", color: "var(--text-muted)" },
            { name: "Strategist", icon: "📊", color: "var(--accent-purple)" },
            { name: "→", icon: "", color: "var(--text-muted)" },
            { name: "Copywriter", icon: "✍️", color: "var(--accent-blue)" },
            { name: "→", icon: "", color: "var(--text-muted)" },
            { name: "Guardrail", icon: "🛡️", color: "var(--accent-yellow)" },
            { name: "→", icon: "", color: "var(--text-muted)" },
            { name: "Human Gate", icon: "👤", color: "var(--accent-green)" },
          ].map((node, i) => (
            node.name === "→" ? (
              <span key={i} style={{ color: "var(--text-muted)", fontSize: "1.25rem" }}>→</span>
            ) : (
              <div key={i} style={{
                padding: "8px 16px", background: "var(--bg-tertiary)",
                borderRadius: "var(--radius-md)",
                border: `1px solid ${node.color}33`,
                display: "flex", alignItems: "center", gap: 6,
                fontSize: "0.8125rem", fontWeight: 600,
              }}>
                <span>{node.icon}</span>
                <span>{node.name}</span>
              </div>
            )
          ))}
        </div>
        <div style={{ textAlign: "center", fontSize: "0.75rem", color: "var(--text-muted)", marginTop: 8 }}>
          Content Generation Subgraph: Brand Voice Retrieval → Hook Generator → Caption Generator → Slop Rubric + Voice-Drift Check → Rank + Explain
        </div>
      </div>

      {/* Trace Selector */}
      <div className="tabs">
        {traces.map((t, i) => (
          <div
            key={i}
            className={`tab ${selectedTrace === i ? "active" : ""}`}
            onClick={() => setSelectedTrace(i)}
          >
            {t.name}
          </div>
        ))}
      </div>

      {/* Trace Detail */}
      <div className="card animate-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3 className="card-title">📋 Execution Trace: {trace.name}</h3>
          <div style={{ display: "flex", gap: 8 }}>
            <span className="badge badge-success">{trace.status}</span>
            <span className="badge badge-info">{trace.duration}</span>
          </div>
        </div>

        <div className="pipeline-trace">
          {trace.nodes.map((node: any, i: number) => (
            <div key={i}>
              <div className={`trace-node ${node.status}`}>
                <div className="node-icon">{node.icon}</div>
                <div className="node-info">
                  <div className="node-name">{node.persona}</div>
                  <div className="node-detail">{node.detail}</div>
                  {node.why && (
                    <div style={{
                      marginTop: 6, padding: "6px 10px",
                      background: "rgba(0, 212, 255, 0.06)",
                      borderRadius: "var(--radius-sm)",
                      fontSize: "0.6875rem", color: "var(--accent-cyan)",
                    }}>
                      💡 {node.why}
                    </div>
                  )}
                </div>
                <div className="node-duration">{node.duration}</div>
              </div>
              {i < trace.nodes.length - 1 && <div className="trace-connector" />}
            </div>
          ))}
        </div>
      </div>

      {/* Design Decisions */}
      <div className="card animate-in">
        <div className="card-header">
          <h3 className="card-title">🧠 Architecture Decisions (from §4)</h3>
          <span className="badge badge-purple">Team Synthesis</span>
        </div>
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {[
            { decision: "Orchestration", choice: "LangGraph with persona-named nodes", why: "Same execution model as a functional pipeline, but persona naming makes the explainability panel read like 'the Scout agent found this' instead of 'node_3 output.'" },
            { decision: "Brand Voice Memory", choice: "pgvector + valid_from/valid_to columns", why: "Gets ~80% of Graphiti's benefit with zero new infrastructure. Graphiti is the Phase-2 upgrade." },
            { decision: "Content Generation", choice: "Hook-then-caption split", why: "Splitting hook-from-caption stops the generator from defaulting to a generic opener — a real quality fix backed by a concrete mechanism." },
            { decision: "Guardrail", choice: "Dual check: embedding similarity + slop rubric", why: "A draft can be topically on-brand but still read as generic AI writing — the two failure modes are different." },
            { decision: "Classification", choice: "Dedicated RoBERTa classifiers, not LLM", why: "Materially cheaper and faster at comment volume, plus a citable accuracy story (Barbieri et al. 2020)." },
            { decision: "Peak-Time", choice: "Heuristic heatmap → LinUCB bandit (EQI reward)", why: "Cold-start with heuristic, build the bandit live — same algorithm class as Netflix artwork selection." },
          ].map((item, i) => (
            <div key={i} style={{
              padding: "12px", background: "var(--bg-tertiary)",
              borderRadius: "var(--radius-md)",
              borderLeft: "3px solid var(--accent-purple)",
            }}>
              <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 4 }}>
                <span style={{ fontWeight: 700, fontSize: "0.8125rem" }}>{item.decision}</span>
                <span className="badge badge-info">{item.choice}</span>
              </div>
              <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", lineHeight: 1.5 }}>
                {item.why}
              </p>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function getMockTraces() {
  return [
    {
      name: "Content Generation",
      status: "completed",
      duration: "2.34s",
      nodes: [
        { icon: "🔍", persona: "Scout Agent", status: "completed", detail: "Scanned Instagram trends. Found 3 relevant: #SleepHacks (+200%), #ProteinRecipes (+120%), #5MinWorkout (+80%)", why: "Filtered from 10 trending topics to 3 matching your content pillars (fitness, nutrition, wellness)", duration: "45ms" },
        { icon: "📊", persona: "Strategist Agent", status: "completed", detail: "Analyzed engagement patterns. Recommended: Saturday 20:00 (90% peak engagement)", why: "LinUCB bandit selected this slot — predicted EQI: 72.5, currently exploiting (high confidence)", duration: "120ms" },
        { icon: "📚", persona: "Voice Retrieval", status: "completed", detail: "Retrieved 5 similar posts from top-quartile by EQI. Loaded structural profile + active guidelines.", why: "Top-quartile filter ensures only your best-performing posts train the generator", duration: "30ms" },
        { icon: "🎣", persona: "Hook Generator", status: "completed", detail: "Generated 3 hook variants conditioned on top-quartile hooks only", why: "Separate cheap model call — splitting this out stops generic openers", duration: "800ms" },
        { icon: "✍️", persona: "Caption Generator", status: "completed", detail: "Main LLM call. Inputs: hook, 5 few-shot posts, structural profile, platform rules, banned phrases", why: "Claude Sonnet-class model chosen for tone consistency across long output", duration: "1200ms" },
        { icon: "🛡️", persona: "Guardrail Agent", status: "completed", detail: "Voice-drift check: 0.82 (pass). Slop score: 0.05 (pass). Structural match: 0.85 (pass). 3/3 variants passed.", why: "Dual check: embedding similarity catches topical drift, slop rubric catches generic AI writing patterns", duration: "50ms" },
        { icon: "🏆", persona: "Rank + Explain", status: "completed", detail: "Ranked by voice-similarity (60%) + structural match (40%). Variant 1 scored highest.", why: "Each variant annotated with which past posts and features drove the ranking", duration: "10ms" },
        { icon: "👤", persona: "Human Approval Gate", status: "waiting", detail: "3 variants ready for review. LangGraph interrupt/checkpoint — graph paused until human acts.", why: "Nothing posts publicly without human approval. This is the product decision, not a limitation.", duration: "⏳" },
      ],
    },
    {
      name: "Comment Triage",
      status: "completed",
      duration: "0.85s",
      nodes: [
        { icon: "📥", persona: "Comment Ingestion", status: "completed", detail: "Received 20 new comments from Instagram Graph API", duration: "100ms" },
        { icon: "🧠", persona: "Sentiment Classifier", status: "completed", detail: "cardiffnlp/twitter-roberta-base-sentiment-latest — classified all 20 comments", why: "Dedicated RoBERTa model, not an LLM call. Citable accuracy: Barbieri et al. 2020", duration: "350ms" },
        { icon: "🎯", persona: "Intent Classifier", status: "completed", detail: "Classified: 5 FAQ, 5 positive, 3 neutral, 2 collab, 2 complaint, 2 spam, 1 press", duration: "200ms" },
        { icon: "📊", persona: "Risk Matrix Router", status: "completed", detail: "2×2 routing: 5 auto-reply, 3 human review, 8 log-only, 2 escalate", why: "Intent confidence × brand risk. Verified accounts auto-bump to high risk.", duration: "20ms" },
        { icon: "✅", persona: "Auto-Reply Generator", status: "completed", detail: "Generated 5 on-brand replies for low-risk FAQs. Rate-limited: 5/200 hourly cap.", duration: "180ms" },
        { icon: "⚡", persona: "Circuit Breaker Check", status: "completed", detail: "Negative ratio: 15% (below 50% trigger). All clear — no posts paused.", why: "Continuous monitoring. If threshold crossed → auto-pause scheduled posts.", duration: "5ms" },
      ],
    },
  ];
}
