"use client";

import { useState, useEffect } from "react";
import { api } from "@/lib/api";
import InteractiveRiskMatrix from "@/components/ui/InteractiveRiskMatrix";

interface Props {
  brandId: string;
  addToast: (type: "success" | "error" | "info", message: string) => void;
  backendStatus: string;
}

export default function CommentsPage({ brandId, addToast, backendStatus }: Props) {
  const [triage, setTriage] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [circuitBreaker, setCircuitBreaker] = useState<any>(null);

  useEffect(() => { loadTriage(); }, [brandId]);

  const loadTriage = async () => {
    setLoading(true);
    try {
      const [triageData, cbData] = await Promise.all([
        api.getTriageView(brandId),
        api.checkCircuitBreaker(brandId),
      ]);
      setTriage(triageData);
      setCircuitBreaker(cbData);
    } catch {
      setTriage(getMockTriage());
      setCircuitBreaker({ triggered: false, negative_ratio: 0.15, avg_sentiment: 0.35 });
    }
    setLoading(false);
  };

  const cells = [
    {
      key: "high_conf_low_risk",
      title: "Auto-Reply Eligible",
      icon: "",
      cssClass: "auto-reply",
      description: "High confidence, low risk - FAQ & simple questions",
      items: triage?.high_conf_low_risk || [],
    },
    {
      key: "high_conf_high_risk",
      title: "Human Review",
      icon: "",
      cssClass: "human-review",
      description: "High confidence, high risk - collabs, press, verified accounts",
      items: triage?.high_conf_high_risk || [],
    },
    {
      key: "low_conf_low_risk",
      title: "Log Only",
      icon: "",
      cssClass: "log-only",
      description: "Your audience's peak engagement window - Saturday evenings see 90% of peak engagement.",
      items: triage?.low_conf_low_risk || [],
    },
    {
      key: "low_conf_high_risk",
      title: "Escalate Immediately",
      icon: "",
      cssClass: "escalate",
      description: "Low confidence, high risk - possible PR issue",
      items: triage?.low_conf_high_risk || [],
    },
  ];

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Comment Triage</h1>
          <p className="page-subtitle">2×2 Risk Matrix - Sentinel Agent classifies by intent confidence × brand risk.</p>
        </div>
        <button className="btn btn-secondary btn-sm" onClick={loadTriage}>↻ Re-scan</button>
      </div>

      {/* Circuit Breaker Banner */}
      {circuitBreaker && (
        <div className="card glass animate-in" style={{
          marginBottom: 24,
          borderColor: circuitBreaker.triggered ? "rgba(255, 59, 92, 0.5)" : "rgba(0, 245, 160, 0.3)",
          background: circuitBreaker.triggered ? "rgba(255, 59, 92, 0.05)" : "var(--bg-card)",
        }}>
          <div style={{ display: "flex", alignItems: "center", gap: 16 }}>
            <div style={{ fontSize: "1.5rem" }}>{circuitBreaker.triggered ? "Alert" : "OK"}</div>
            <div style={{ flex: 1 }}>
              <div style={{ fontWeight: 700, marginBottom: 2 }}>
                Sentiment Circuit Breaker: {circuitBreaker.triggered ? "TRIGGERED" : "Normal"}
              </div>
              <div style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>
                Negative ratio: {circuitBreaker.negative_ratio} •
                Avg sentiment: {circuitBreaker.avg_sentiment?.toFixed(2)} •
                Powered by cardiffnlp/twitter-roberta-base-sentiment-latest
              </div>
            </div>
            <span className={`badge ${circuitBreaker.triggered ? "badge-danger" : "badge-success"}`}>
              {circuitBreaker.triggered ? "Posts Paused" : "All Clear"}
            </span>
          </div>
        </div>
      )}

      {/* Threat mapping layout grid */}
      <div style={{ display: "grid", gridTemplateColumns: "1.1fr 2fr", gap: 24, alignItems: "start" }} className="grid-2-1">
        
        {/* Left column: Visual Coordinate Mapping */}
        <div className="card glass animate-in" style={{ position: "sticky", top: 20 }}>
          <div className="card-header">
            <h3 className="card-title">🎯 Threat Mapping</h3>
            <span className="badge badge-purple">Risk Plot</span>
          </div>
          <p style={{ fontSize: "0.75rem", color: "var(--text-muted)", marginBottom: 12, lineHeight: 1.4 }}>
            Visual plot of intent confidence vs brand risk. Bubbles represent comments. Auto-reply thresholds filter low-threat inputs automatically.
          </p>
          <InteractiveRiskMatrix triageData={triage || getMockTriage()} />
        </div>

        {/* Right column: Risk Matrix Grid */}
        <div className="risk-matrix" style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
          {cells.map((cell) => (
            <div key={cell.key} className={`risk-cell ${cell.cssClass}`} style={{ minHeight: 220 }}>
              <div className="risk-cell-header">
                <span>{cell.icon}</span>
                <div>
                  <div style={{ fontWeight: 700, fontSize: "0.8125rem" }}>{cell.title}</div>
                  <div style={{ fontSize: "0.6875rem", color: "var(--text-muted)" }}>{cell.description}</div>
                </div>
                <span className="cell-count">{cell.items.length}</span>
              </div>
              <div style={{ maxHeight: 260, overflowY: "auto" }}>
                {cell.items.length === 0 ? (
                  <div style={{ padding: 16, textAlign: "center", color: "var(--text-muted)", fontSize: "0.725rem" }}>
                    No comments in this category
                  </div>
                ) : (
                  cell.items.map((comment: any, i: number) => (
                    <div key={i} className="comment-card" style={{ padding: 10 }}>
                      <div className="comment-header">
                        <span className="comment-author">@{comment.author_username || comment.author}</span>
                        {(comment.is_verified || comment.author_is_verified) && (
                          <span className="comment-verified" style={{ fontSize: "0.6875rem" }}>✓</span>
                        )}
                        <span className={`badge ${
                          comment.sentiment_label === "positive" ? "badge-success" :
                          comment.sentiment_label === "negative" ? "badge-danger" : "badge-info"
                        }`} style={{ marginLeft: "auto", fontSize: "0.5rem", padding: "1px 4px" }}>
                          {comment.sentiment_label || "neutral"}
                        </span>
                      </div>
                      <div className="comment-text" style={{ fontSize: "0.75rem" }}>{comment.content || comment.text}</div>
                      <div className="comment-meta" style={{ fontSize: "0.625rem", marginTop: 4 }}>
                        <span>Intent: {comment.intent}</span>
                        <span>Confidence: {((comment.intent_confidence || 0.8) * 100).toFixed(0)}%</span>
                      </div>
                      {(comment.auto_reply || comment.drafted_reply) && (
                        <div style={{
                          marginTop: 6,
                          padding: "6px 8px",
                          background: "rgba(0, 245, 160, 0.05)",
                          borderRadius: "var(--radius-sm)",
                          borderLeft: "2px solid var(--accent-green)",
                          fontSize: "0.6875rem",
                          color: "var(--text-secondary)",
                        }}>
                          <strong>{comment.auto_reply ? "Auto: " : "Draft: "}</strong>
                          {comment.auto_reply || comment.drafted_reply}
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}

function getMockTriage() {
  return {
    high_conf_low_risk: [
      { content: "What time do you usually post your workouts?", author_username: "fitness_fan_22", sentiment_label: "neutral", sentiment_score: 0.1, intent: "faq", intent_confidence: 0.85, auto_reply: "Great question! Check out our highlights for more details on that.", },
      { content: "Do you have a beginner version of this routine?", author_username: "newbie.starts", sentiment_label: "neutral", sentiment_score: 0.2, intent: "faq", intent_confidence: 0.8, auto_reply: "Thanks for asking! We've got a guide saved in our highlights." },
      { content: "How many calories does this burn?", author_username: "track.everything", sentiment_label: "neutral", sentiment_score: 0.0, intent: "faq", intent_confidence: 0.75 },
    ],
    high_conf_high_risk: [
      { content: "Hey! I'm from @fitgear.india - would love to discuss a collaboration. Can we DM?", author_username: "fitgear.india", is_verified: true, sentiment_label: "positive", sentiment_score: 0.5, intent: "collaboration", intent_confidence: 0.92, drafted_reply: "Thanks for reaching out! We'd love to learn more about what you have in mind." },
      { content: "Hi, I'm a journalist at HealthToday. Would you be open to a quick interview?", author_username: "sarah.healthtoday", is_verified: true, sentiment_label: "neutral", sentiment_score: 0.3, intent: "press", intent_confidence: 0.88, drafted_reply: "Thanks for thinking of us! Happy to chat - DM us to coordinate." },
    ],
    low_conf_low_risk: [
      { content: "This is exactly what I needed today", author_username: "daily_mover", sentiment_label: "positive", sentiment_score: 0.9, intent: "positive", intent_confidence: 0.5 },
      { content: "Love this", author_username: "quick.liker", sentiment_label: "positive", sentiment_score: 0.8, intent: "positive", intent_confidence: 0.4 },
      { content: "", author_username: "thumbs.upper", sentiment_label: "neutral", sentiment_score: 0.3, intent: "neutral", intent_confidence: 0.3 },
    ],
    low_conf_high_risk: [
      { content: "I tried your routine and hurt my back. Not cool posting without proper form warnings.", author_username: "injured_follower", sentiment_label: "negative", sentiment_score: -0.8, intent: "complaint", intent_confidence: 0.45 },
      { content: "This is irresponsible. You're not a certified trainer.", author_username: "angry_expert", sentiment_label: "negative", sentiment_score: -0.9, intent: "complaint", intent_confidence: 0.4 },
    ],
    circuit_breaker: { triggered: false, negative_ratio: 0.15, avg_sentiment: 0.3 },
  };
}
