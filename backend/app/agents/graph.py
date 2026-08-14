"""
Pulse — Main LangGraph Orchestration (§7.2)
Persona-named nodes: Scout, Strategist, Copywriter, Guardrail, Sentinel.
Same execution model as a functional pipeline, persona naming for demo narrative.
"""

from typing import TypedDict, Optional, List, Annotated
from datetime import datetime
import json


class PipelineState(TypedDict, total=False):
    """State that flows through the LangGraph pipeline."""
    # Input
    trigger_type: str  # new_post_request, comment_received, scheduled_tick, trend_scan
    brand_id: str
    topic: Optional[str]
    platform: str
    tone: Optional[str]
    additional_context: Optional[str]
    
    # Brand context (loaded by retrieval node)
    brand_name: str
    few_shot_posts: List[dict]
    structural_profile: dict
    brand_guidelines: List[str]
    voice_centroid: Optional[List[float]]
    
    # Content generation output
    hooks: List[str]
    variants: List[dict]
    guardrail_results: List[dict]
    
    # Scheduling
    recommended_time: Optional[dict]
    heatmap: List[dict]
    
    # Comment triage
    comment_text: Optional[str]
    comment_author: Optional[str]
    comment_is_verified: bool
    triage_result: Optional[dict]
    auto_reply: Optional[str]
    
    # Trends
    trends: List[dict]
    
    # Circuit breaker
    circuit_breaker_status: Optional[dict]
    
    # Pipeline trace
    trace: List[dict]
    status: str
    error: Optional[str]
    started_at: str
    completed_at: Optional[str]


class PulseGraph:
    """
    Orchestrates the full pipeline.
    
    In a production build, this would use LangGraph's StateGraph with
    actual interrupt/checkpoint patterns for the human approval gate.
    For the hackathon, we implement the same logic flow as async functions
    that can be called from the API layer, making it runnable without
    a full LangGraph runtime.
    """
    
    @staticmethod
    async def run_content_generation(
        brand_id: str,
        topic: str,
        platform: str = "instagram",
        tone: Optional[str] = None,
        additional_context: Optional[str] = None,
        # Pre-loaded brand context (from DB)
        brand_name: str = "",
        few_shot_posts: Optional[List[dict]] = None,
        structural_profile: Optional[dict] = None,
        brand_guidelines: Optional[List[str]] = None,
        voice_centroid: Optional[List[float]] = None,
        engagement_data: Optional[List[dict]] = None,
    ) -> dict:
        """
        Full content generation pipeline:
        Scout → Strategist → Copywriter → Guardrail → Rank+Explain → Human Approval Gate
        """
        from app.agents.copywriter import CopywriterAgent, GenerationContext
        from app.agents.strategist import StrategistAgent
        from app.agents.scout import ScoutAgent
        
        trace = []
        started_at = datetime.utcnow()
        
        # Node 1: Scout — check trends
        scout_start = datetime.utcnow()
        trends = ScoutAgent.scan_trends(platform=platform)
        trace.append({
            "node_name": "Scout",
            "persona": "🔍 Scout Agent",
            "status": "completed",
            "duration_ms": int((datetime.utcnow() - scout_start).total_seconds() * 1000),
            "input_summary": f"Scanning {platform} trends",
            "output_summary": f"Found {len(trends)} relevant trends",
            "details": {"trends": [t["tag"] for t in trends[:3]]},
        })
        
        # Node 2: Strategist — recommend posting time
        strategist_start = datetime.utcnow()
        strategist = StrategistAgent()
        if engagement_data:
            strategist.seed(engagement_data)
        recommendation = strategist.get_recommendation(platform=platform)
        trace.append({
            "node_name": "Strategist",
            "persona": "📊 Strategist Agent",
            "status": "completed",
            "duration_ms": int((datetime.utcnow() - strategist_start).total_seconds() * 1000),
            "input_summary": f"Analyzing engagement patterns for {platform}",
            "output_summary": f"Recommended: {recommendation['recommended'].get('day_name', 'N/A')} at {recommendation['recommended'].get('hour', 'N/A'):02d}:00",
            "details": {"method": recommendation["method"], "score": recommendation["recommended"].get("score")},
        })
        
        # Node 3: Copywriter — generate content
        copywriter_start = datetime.utcnow()
        context: GenerationContext = {
            "brand_id": brand_id,
            "topic": topic,
            "platform": platform,
            "tone": tone,
            "additional_context": additional_context,
            "few_shot_posts": few_shot_posts or [],
            "structural_profile": structural_profile or {},
            "brand_guidelines": brand_guidelines or [],
            "voice_centroid": voice_centroid,
        }
        variants = await CopywriterAgent.generate_content(context)
        trace.append({
            "node_name": "Copywriter",
            "persona": "✍️ Copywriter Agent",
            "status": "completed",
            "duration_ms": int((datetime.utcnow() - copywriter_start).total_seconds() * 1000),
            "input_summary": f"Topic: '{topic}', Platform: {platform}, {len(few_shot_posts or [])} few-shot posts",
            "output_summary": f"Generated {len(variants)} variants",
            "details": {
                "voice_scores": [v["voice_similarity"] for v in variants],
                "slop_scores": [v["slop_score"] for v in variants],
            },
        })
        
        # Node 4: Guardrail — already applied inside Copywriter, but we log it
        guardrail_passed = sum(1 for v in variants if v["explanation"].get("guardrail_passed", True))
        trace.append({
            "node_name": "Guardrail",
            "persona": "🛡️ Guardrail Agent",
            "status": "completed",
            "duration_ms": 0,  # Done inline
            "input_summary": f"Checking {len(variants)} variants against voice drift + slop rubric",
            "output_summary": f"{guardrail_passed}/{len(variants)} passed guardrail",
            "details": {
                "checks": ["voice_drift", "slop_rubric", "structural_match", "banned_phrases"],
            },
        })
        
        # Node 5: Human Approval Gate (pending)
        trace.append({
            "node_name": "HumanApprovalGate",
            "persona": "👤 Human Approval Gate",
            "status": "waiting",
            "duration_ms": 0,
            "input_summary": f"{len(variants)} variants ready for review",
            "output_summary": "Awaiting human approval",
            "details": {"requires_action": True},
        })
        
        completed_at = datetime.utcnow()
        total_duration = int((completed_at - started_at).total_seconds() * 1000)
        
        return {
            "variants": variants,
            "recommended_time": recommendation["recommended"],
            "recommendation_method": recommendation["method"],
            "trends": trends,
            "trace": trace,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat(),
            "total_duration_ms": total_duration,
            "status": "awaiting_approval",
        }
    
    @staticmethod
    async def run_comment_triage(
        comments: List[dict],
        brand_name: str = "FitVibe",
        brand_guidelines: Optional[List[str]] = None,
    ) -> dict:
        """
        Comment triage pipeline:
        Sentinel → Classification → Risk Matrix → Auto-Reply (if eligible)
        """
        from app.agents.sentinel import SentinelAgent
        
        sentinel = SentinelAgent()
        results = {
            "high_conf_low_risk": [],
            "high_conf_high_risk": [],
            "low_conf_low_risk": [],
            "low_conf_high_risk": [],
            "circuit_breaker": None,
        }
        
        for comment in comments:
            triage = sentinel.triage_comment(
                text=comment.get("content", comment.get("text", "")),
                is_verified=comment.get("is_verified", comment.get("author_is_verified", False)),
            )
            
            entry = {
                **comment,
                **triage,
            }
            
            # Generate auto-reply if eligible
            if triage["triage_action"] == "auto_reply":
                reply = await sentinel.generate_auto_reply(
                    comment_text=comment.get("content", comment.get("text", "")),
                    intent=triage["intent"],
                    brand_name=brand_name,
                    brand_guidelines=brand_guidelines,
                )
                entry["auto_reply"] = reply
            elif triage["triage_action"] == "human_review":
                # Draft a reply for human review
                reply = await sentinel.generate_auto_reply(
                    comment_text=comment.get("content", comment.get("text", "")),
                    intent=triage["intent"],
                    brand_name=brand_name,
                )
                entry["drafted_reply"] = reply
            
            # Route to appropriate bucket
            cell = triage["risk_matrix_cell"]
            if cell in results:
                results[cell].append(entry)
        
        # Check circuit breaker
        all_sentiments = [c.get("sentiment_score", 0) for bucket in [
            results["high_conf_low_risk"], results["high_conf_high_risk"],
            results["low_conf_low_risk"], results["low_conf_high_risk"]
        ] for c in bucket]
        
        results["circuit_breaker"] = sentinel.check_circuit_breaker(all_sentiments)
        
        return results
