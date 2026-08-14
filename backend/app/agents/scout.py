"""
Pulse — Scout Agent (Trend Radar §7.7)
Periodic relevance-filtered scan surfacing top trending topics.
"""

import random
from typing import List, Optional
from app.services.voice_engine import VoiceEngine
from app.services.mock_platform import MockPlatformAPI


class ScoutAgent:
    """
    Scout persona — Trend detection with relevance filtering.
    Surfaces only trends that match the brand's corpus, not a firehose.
    
    Tier 1 (built): Periodic relevance-filtered scan.
    Tier 2 (roadmap): Event-driven velocity detection via Redis Pub/Sub.
    """
    
    # Brand-relevant category keywords for relevance scoring
    BRAND_CATEGORIES = {
        "fitness": ["workout", "exercise", "gym", "training", "strength", "cardio", "HIIT", "leg day", "upper body"],
        "nutrition": ["protein", "meal", "food", "diet", "recipe", "cooking", "nutrition", "calories", "macros"],
        "wellness": ["wellness", "mindfulness", "sleep", "rest", "mental health", "meditation", "yoga", "breathwork"],
        "community": ["community", "challenge", "together", "support", "motivation", "inspiration"],
    }
    
    @staticmethod
    def scan_trends(
        platform: str = "instagram",
        brand_categories: Optional[List[str]] = None,
        top_n: int = 3,
    ) -> List[dict]:
        """
        Scan and filter trends by relevance to brand's content pillars.
        Returns top-n most relevant trends with "why this fits you" explanations.
        """
        # Get raw trends (from mock API in demo mode)
        raw_trends = MockPlatformAPI.get_trending_hashtags(platform)
        
        if brand_categories is None:
            brand_categories = list(ScoutAgent.BRAND_CATEGORIES.keys())
        
        # Score each trend for brand relevance
        scored_trends = []
        for trend in raw_trends:
            tag = trend["tag"].lower()
            category = trend.get("category", "")
            
            # Relevance scoring
            relevance = 0.0
            matching_pillar = None
            
            for pillar, keywords in ScoutAgent.BRAND_CATEGORIES.items():
                if pillar not in brand_categories:
                    continue
                for keyword in keywords:
                    if keyword.lower() in tag or keyword.lower() in category:
                        relevance = max(relevance, 0.8)
                        matching_pillar = pillar
                        break
            
            # Volume-based bonus
            volume_score = min(trend.get("volume", 0) / 5000000, 1.0) * 0.2
            relevance += volume_score
            
            # Velocity bonus (fast-growing trends are more valuable)
            velocity_str = trend.get("velocity", "+0%")
            try:
                velocity_pct = float(velocity_str.replace("%", "").replace("+", ""))
                velocity_score = min(velocity_pct / 200, 1.0) * 0.3
                relevance += velocity_score
            except ValueError:
                pass
            
            relevance = min(relevance, 1.0)
            
            if relevance > 0.3:  # Only surface if minimally relevant
                # Generate "why this fits you" explanation
                why = ScoutAgent._generate_fit_explanation(
                    trend, matching_pillar, relevance
                )
                
                scored_trends.append({
                    **trend,
                    "relevance_score": round(relevance, 2),
                    "matching_pillar": matching_pillar,
                    "why_it_fits": why,
                })
        
        # Sort by relevance and return top-n
        scored_trends.sort(key=lambda t: t["relevance_score"], reverse=True)
        return scored_trends[:top_n]
    
    @staticmethod
    def _generate_fit_explanation(trend: dict, pillar: Optional[str], relevance: float) -> str:
        """Generate a one-line 'why this fits you' explanation per §6.4."""
        tag = trend["tag"]
        velocity = trend.get("velocity", "growing")
        volume = trend.get("volume", 0)
        
        templates = [
            f"{tag} is {velocity} right now ({volume:,} posts). "
            f"Aligns with your {pillar or 'content'} pillar — your audience is already engaging with this topic.",
            
            f"Trending: {tag} ({velocity} velocity). "
            f"Your past posts about {pillar or 'similar topics'} performed well — this is a natural fit for a timely post.",
            
            f"{tag} is surging ({velocity}). "
            f"Your {pillar or 'content'} focus means your audience would find this relevant and timely.",
        ]
        
        return random.choice(templates)
    
    @staticmethod
    def suggest_content_from_trend(trend: dict, brand_name: str = "FitVibe") -> dict:
        """
        Suggest a content idea based on a trending topic.
        This feeds into the Copywriter agent.
        """
        tag = trend["tag"]
        pillar = trend.get("matching_pillar", "fitness")
        
        suggestions = {
            "fitness": f"Create a quick routine post that hooks into {tag} — your audience loves actionable workout content.",
            "nutrition": f"Do a 'what I actually eat' post tied to {tag} — your meal posts consistently get the highest saves.",
            "wellness": f"Share a personal take on {tag} — your authentic wellness content gets the most shares.",
            "community": f"Run a community spotlight or challenge around {tag} — your engagement posts drive the most comments.",
        }
        
        return {
            "trend": tag,
            "suggested_topic": f"{tag.replace('#', '')} — practical tips from a {pillar} perspective",
            "content_direction": suggestions.get(pillar, f"Create authentic content around {tag}"),
            "urgency": "high" if "+100" in trend.get("velocity", "") else "medium",
        }
