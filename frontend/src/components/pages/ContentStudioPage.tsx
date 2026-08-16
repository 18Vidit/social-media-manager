"use client";

import { useState } from "react";
import { api } from "@/lib/api";
import PhonePreviewMockup from "@/components/ui/PhonePreviewMockup";

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
}

interface Draft {
  id: string;
  variant_index: number;
  hook: string;
  content: string;
  hashtags: string[];
  voice_similarity: number;
  slop_score: number;
  predicted_engagement: number;
  explanation: any;
  recommended_time: string | null;
  recommended_time_reason: string | null;
}

export default function ContentStudioPage({ brandId, addToast, backendStatus }: Props) {
  const [topic, setTopic] = useState("");
  const [platform, setPlatform] = useState("instagram");
  const [generating, setGenerating] = useState(false);
  const [drafts, setDrafts] = useState<Draft[]>([]);
  const [pipelineTrace, setPipelineTrace] = useState<any[]>([]);
  const [recommendedTime, setRecommendedTime] = useState<any>(null);
  const [duration, setDuration] = useState<number>(0);
  
  // Selection & Editing States
  const [selectedDraftIdx, setSelectedDraftIdx] = useState<number>(0);
  const [editingDraftId, setEditingDraftId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState("");
  const [editHook, setEditHook] = useState("");

  const handleGenerate = async () => {
    if (!topic.trim()) {
      addToast("error", "Enter a topic for content generation.");
      return;
    }
    
    setGenerating(true);
    setDrafts([]);
    setPipelineTrace([]);

    try {
      const result = await api.generateContent({
        brand_id: brandId,
        topic: topic.trim(),
        platform,
        num_variants: 3,
      });
      
      setDrafts(result.drafts || []);
      setSelectedDraftIdx(0);
      setEditingDraftId(null);
      setPipelineTrace(result.pipeline_trace || []);
      setRecommendedTime(result.recommended_time);
      setDuration(result.total_duration_ms || 0);
      addToast("success", `Generated ${result.drafts?.length || 0} variants in ${(result.total_duration_ms / 1000).toFixed(1)}s`);
    } catch (err: any) {
      addToast("error", `Generation failed: ${err.message}. Make sure the backend is running.`);
      // Set mock data for demo
      const mockD = getMockDrafts(topic, platform);
      setDrafts(mockD);
      setSelectedDraftIdx(0);
      setEditingDraftId(null);
      setPipelineTrace(getMockTrace());
      setDuration(2340);
      setRecommendedTime({ datetime: new Date().toISOString(), reason: "Saturday 8PM - your audience's peak engagement window", method: "linucb_bandit" });
    }
    
    setGenerating(false);
  };

  const handleApprove = async (draftId: string) => {
    try {
      await api.approveDraft(draftId);
      addToast("success", "Draft approved and scheduled!");
      setDrafts(prev => prev.map(d => d.id === draftId ? { ...d, status: "approved" } : d));
    } catch {
      addToast("info", "Draft approved (demo mode).");
    }
  };

  const handleReject = async (draftId: string) => {
    try {
      await api.rejectDraft(draftId, "Voice doesn't match - try again with more energy");
      addToast("info", "Draft rejected. Feedback sent to Copywriter.");
    } catch {
      addToast("info", "Draft rejected (demo mode).");
    }
  };

  const getScoreClass = (score: number) => score >= 0.7 ? "high" : score >= 0.4 ? "medium" : "low";

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Content Studio</h1>
          <p className="page-subtitle">Generate on-brand content with the Copywriter Agent - hook-then-caption pipeline.</p>
        </div>
      </div>

      {/* Generation Form */}
      <div className="card glass animate-in" style={{ marginBottom: 24 }}>
        <div className="card-header">
          <h3 className="card-title">Generate New Content</h3>
          {duration > 0 && (
            <span className="badge badge-info">{(duration / 1000).toFixed(1)}s pipeline</span>
          )}
        </div>
        
        <div className="grid-2" style={{ marginBottom: 16 }}>
          <div className="form-group">
            <label className="form-label">Topic / Content Idea</label>
            <input
              className="form-input"
              placeholder="e.g., Morning stretching routine for desk workers"
              value={topic}
              onChange={e => setTopic(e.target.value)}
              onKeyDown={e => e.key === "Enter" && handleGenerate()}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Platform</label>
            <select className="form-select" value={platform} onChange={e => setPlatform(e.target.value)}>
              <option value="instagram">Instagram</option>
              <option value="tiktok">TikTok</option>
              <option value="linkedin">LinkedIn</option>
              <option value="youtube">YouTube</option>
              <option value="twitter">Twitter / X</option>
            </select>
          </div>
        </div>
        
        <button
          className="btn btn-primary"
          onClick={handleGenerate}
          disabled={generating}
        >
          {generating ? "Generating..." : "Generate 3 Variants"}
        </button>
      </div>

      {/* Pipeline Trace */}
      {pipelineTrace.length > 0 && (
        <div className="card glass animate-in" style={{ marginBottom: 24 }}>
          <div className="card-header">
            <h3 className="card-title">Pipeline Execution Trace</h3>
            <span className="badge badge-success">Explainability Panel</span>
          </div>
          <div className="pipeline-trace">
            {pipelineTrace.map((node: any, i: number) => (
              <div key={i}>
                <div className={`trace-node ${node.status}`}>
                  <div className="node-icon">{node.persona?.split(" ")[0] || "⚙"}</div>
                  <div className="node-info">
                    <div className="node-name">{node.persona || node.node_name}</div>
                    <div className="node-detail">{node.output_summary}</div>
                  </div>
                  <div className="node-duration">
                    {node.status === "waiting" ? "waiting" : `${node.duration_ms}ms`}
                  </div>
                </div>
                {i < pipelineTrace.length - 1 && <div className="trace-connector" />}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recommended Time */}
      {recommendedTime && (
        <div className="card glass animate-in" style={{ marginBottom: 24, borderColor: "var(--border-accent)" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ fontSize: "2rem" }}> </div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, marginBottom: 4 }}>
                Strategist Recommendation
              </div>
              <div style={{ fontSize: "0.8125rem", color: "var(--text-secondary)" }}>
                {recommendedTime.reason}
              </div>
            </div>
            <span className="badge badge-purple">{recommendedTime.method}</span>
          </div>
        </div>
      )}

      {/* Generated Variants with Live Phone Preview */}
      {drafts.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "1.2fr 0.8fr", gap: 24, alignItems: "start" }} className="grid-2-1">
          {/* Left Column: Variant cards list */}
          <div style={{ display: "flex", flexDirection: "column", gap: 16 }}>
            <h3 style={{ color: "var(--text-secondary)", fontSize: "0.8125rem", textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Generated Variants ({drafts.length})
            </h3>
            {drafts.map((draft, i) => {
              const isSelected = selectedDraftIdx === i;
              const isEditing = editingDraftId === draft.id;
              
              return (
                <div
                  key={draft.id || i}
                  className={`variant-card glass animate-in ${isSelected ? "selected" : ""} ${i === 0 ? "recommended" : ""}`}
                  style={{
                    cursor: "pointer",
                    borderColor: isSelected ? "var(--accent-cyan)" : "var(--border-subtle)",
                    boxShadow: isSelected ? "var(--shadow-glow)" : "none",
                    padding: "var(--space-lg)"
                  }}
                  onClick={() => {
                    setSelectedDraftIdx(i);
                    // Clear other editing states if switching cards
                    if (editingDraftId !== draft.id) {
                      setEditingDraftId(null);
                    }
                  }}
                >
                  {/* Hook highlight */}
                  <div style={{
                    padding: "8px 12px",
                    background: "rgba(0, 212, 255, 0.08)",
                    borderRadius: "var(--radius-sm)",
                    borderLeft: "3px solid var(--accent-cyan)",
                    marginBottom: 12,
                    fontSize: "0.8125rem",
                    fontWeight: 600,
                  }}>
                    Hook: {draft.hook}
                  </div>

                  {isEditing ? (
                    <div onClick={e => e.stopPropagation()} style={{ display: "flex", flexDirection: "column", gap: 12, marginTop: 12 }}>
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: "0.75rem" }}>Edit Hook Phrase</label>
                        <input
                          className="form-input"
                          value={editHook}
                          onChange={e => setEditHook(e.target.value)}
                          style={{ fontSize: "0.8125rem", padding: "6px 10px" }}
                        />
                      </div>
                      <div className="form-group">
                        <label className="form-label" style={{ fontSize: "0.75rem" }}>Edit Caption Text</label>
                        <textarea
                          className="form-textarea"
                          value={editContent}
                          onChange={e => setEditContent(e.target.value)}
                          style={{ fontSize: "0.8125rem", minHeight: 120, padding: "8px 10px" }}
                        />
                      </div>
                      <div style={{ display: "flex", gap: 8 }}>
                        <button
                          className="btn btn-success btn-sm"
                          onClick={() => {
                            setDrafts(prev => prev.map(d => d.id === draft.id ? { ...d, content: editContent, hook: editHook } : d));
                            setEditingDraftId(null);
                            addToast("success", "Draft updated live!");
                          }}
                        >
                          Save changes
                        </button>
                        <button className="btn btn-secondary btn-sm" onClick={() => setEditingDraftId(null)}>
                          Cancel
                        </button>
                      </div>
                    </div>
                  ) : (
                    <>
                      {/* Content */}
                      <div className="variant-content">{draft.content}</div>

                      {/* Hashtags */}
                      {draft.hashtags && draft.hashtags.length > 0 && (
                        <div style={{ display: "flex", gap: 6, marginTop: 8, flexWrap: "wrap" }}>
                          {draft.hashtags.map((tag: string, j: number) => (
                            <span key={j} className="badge badge-info">{tag}</span>
                          ))}
                        </div>
                      )}

                      {/* Scores */}
                      <div className="variant-scores">
                        <div className="score-meter">
                          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Voice Match</span>
                          <div className="score-bar">
                            <div
                              className={`score-fill ${getScoreClass(draft.voice_similarity)}`}
                              style={{ width: `${(draft.voice_similarity || 0.5) * 100}%` }}
                            />
                          </div>
                          <span className="score-value" style={{ color: draft.voice_similarity >= 0.7 ? "var(--accent-green)" : "var(--accent-yellow)" }}>
                            {((draft.voice_similarity || 0.5) * 100).toFixed(0)}%
                          </span>
                        </div>
                        <div className="score-meter">
                          <span style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>Slop Score</span>
                          <div className="score-bar">
                            <div
                              className={`score-fill ${draft.slop_score <= 0.3 ? "high" : "low"}`}
                              style={{ width: `${Math.max(10, (1 - (draft.slop_score || 0)) * 100)}%` }}
                            />
                          </div>
                          <span className="score-value" style={{ color: draft.slop_score <= 0.3 ? "var(--accent-green)" : "var(--accent-red)" }}>
                            {((draft.slop_score || 0) * 100).toFixed(0)}%
                          </span>
                        </div>
                      </div>

                      {/* Explanation */}
                      {draft.explanation && (
                        <div style={{
                          marginTop: 12,
                          padding: "8px 12px",
                          background: "var(--bg-tertiary)",
                          borderRadius: "var(--radius-sm)",
                          fontSize: "0.75rem",
                          color: "var(--text-muted)",
                        }}>
                          Why this ranking: {draft.explanation.why}
                        </div>
                      )}

                      {/* Actions */}
                      <div className="variant-actions">
                        <button className="btn btn-success btn-sm" onClick={() => handleApprove(draft.id)}>
                          Approve & Schedule
                        </button>
                        <button className="btn btn-danger btn-sm" onClick={() => handleReject(draft.id)}>
                          Reject
                        </button>
                        <button
                          className="btn btn-secondary btn-sm"
                          onClick={(e) => {
                            e.stopPropagation();
                            setEditingDraftId(draft.id);
                            setEditContent(draft.content);
                            setEditHook(draft.hook);
                          }}
                        >
                          Quick Edit
                        </button>
                      </div>
                    </>
                  )}
                </div>
              );
            })}
          </div>

          {/* Right Column: Live mobile mockup preview */}
          <div className="card glass animate-in" style={{ position: "sticky", top: 20, display: "flex", flexDirection: "column", alignItems: "center", padding: "20px 10px" }}>
            <div style={{ alignSelf: "flex-start", width: "100%", marginBottom: 12 }} className="card-header">
              <h3 className="card-title">📱 Live Creator Preview</h3>
              <span className="badge badge-info">Format Mockups</span>
            </div>
            <PhonePreviewMockup
              content={drafts[selectedDraftIdx]?.content || ""}
              likes={drafts[selectedDraftIdx]?.predicted_engagement ? drafts[selectedDraftIdx].predicted_engagement * 100 : 7200}
              commentsCount={drafts[selectedDraftIdx]?.predicted_engagement ? Math.floor(drafts[selectedDraftIdx].predicted_engagement * 6.5) : 560}
            />
          </div>
        </div>
      )}

      {/* Empty State */}
      {!generating && drafts.length === 0 && (
        <div className="empty-state glass">
          <div className="empty-icon"></div>
          <h3>Ready to create</h3>
          <p style={{ color: "var(--text-muted)", maxWidth: 400, margin: "8px auto" }}>
            Enter a topic above and the Copywriter agent will generate 3 on-brand variants
            using the hook-then-caption pipeline with voice drift + slop guardrails.
          </p>
        </div>
      )}
    </div>
  );
}

function getMockDrafts(topic: string, platform: string): Draft[] {
  return [
    {
      id: "mock-1",
      variant_index: 0,
      hook: `Real talk: ${topic} isn't what most people think it is`,
      content: `Real talk: ${topic} isn't what most people think it is\n\nHere's what nobody tells you:\n\n1. It's simpler than you think\n2. Consistency beats intensity\n3. Start with just 10 minutes\n\nThe biggest mistake? Overcomplicating it. Keep it simple, show up daily, and results follow\n\nWhat's your experience? Drop it below\n\n#FitVibeFlow #WellnessJourney`,
      hashtags: ["#FitVibeFlow", "#WellnessJourney"],
      voice_similarity: 0.82,
      slop_score: 0.05,
      predicted_engagement: 78,
      explanation: { why: "Generated from 5 similar past posts, voice similarity: 0.82, structural match: 0.85. Strong hook pattern from top-quartile posts." },
      recommended_time: null,
      recommended_time_reason: null,
    },
    {
      id: "mock-2",
      variant_index: 1,
      hook: `I tested ${topic} for 30 days. Here's what actually happened`,
      content: `I tested ${topic} for 30 days. Here's what actually happened\n\nI used to overcomplicate this. Then I simplified everything down to what actually matters:\n\n→ Focus on one thing at a time\n→ Track what works, drop what doesn't\n→ Give it at least 2 weeks before judging\n\nThat's it. No fancy hacks. Just showing up\n\nSave this for when you need the reminder.\n\n#FitVibeFlow #WellnessJourney #RealTalk`,
      hashtags: ["#FitVibeFlow", "#WellnessJourney", "#RealTalk"],
      voice_similarity: 0.76,
      slop_score: 0.10,
      predicted_engagement: 72,
      explanation: { why: "Generated from 5 similar past posts, voice similarity: 0.76, structural match: 0.78. Good personal narrative hook." },
      recommended_time: null,
      recommended_time_reason: null,
    },
    {
      id: "mock-3",
      variant_index: 2,
      hook: `Your no-BS guide to ${topic} - no fluff, just what works`,
      content: `Your no-BS guide to ${topic} - no fluff, just what works\n\nI've been doing this for a while and here's the truth:\n\nIt's not about being perfect. It's about being consistent enough that progress becomes inevitable.\n\nThe people who get results aren't the ones with the best plan. They're the ones who follow through on an okay plan.\n\nWhich part resonates most? Tell me honestly\n\n#FitVibeFlow #WellnessJourney`,
      hashtags: ["#FitVibeFlow", "#WellnessJourney"],
      voice_similarity: 0.71,
      slop_score: 0.15,
      predicted_engagement: 65,
      explanation: { why: "Generated from 5 similar past posts, voice similarity: 0.71, structural match: 0.72. Direct and actionable framing." },
      recommended_time: null,
      recommended_time_reason: null,
    },
  ];
}

function getMockTrace() {
  return [
    { node_name: "Scout", persona: "🔍 Scout Agent", status: "completed", duration_ms: 45, output_summary: "Found 3 relevant trends" },
    { node_name: "Strategist", persona: "📊 Strategist Agent", status: "completed", duration_ms: 120, output_summary: "Recommended: Saturday at 20:00" },
    { node_name: "Copywriter", persona: "✍️ Copywriter Agent", status: "completed", duration_ms: 2100, output_summary: "Generated 3 variants" },
    { node_name: "Guardrail", persona: "🛡️ Guardrail Agent", status: "completed", duration_ms: 50, output_summary: "3/3 passed guardrail" },
    { node_name: "HumanApprovalGate", persona: "👤 Human Approval Gate", status: "waiting", duration_ms: 0, output_summary: "Awaiting human approval" },
  ];
}
