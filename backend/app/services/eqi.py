"""
Pulse — EQI (Engagement Quality Index) Service (§4)
Weighted engagement formula used as the reward signal for the LinUCB bandit.
Platform-specific weights favoring high-intent actions (shares, saves, clicks)
over passive engagement (likes).
"""

from typing import Optional


class EQIService:
    """
    Compute Engagement Quality Index per PRD §4:
    - Comments, shares, saves, CTR weighted toward high-intent actions
    - Penalized by negative-sentiment ratio
    - Platform-specific weight profiles
    """
    
    # Platform-specific weights (tuned to weight high-intent actions)
    PLATFORM_WEIGHTS = {
        "instagram": {
            "likes": 0.10,
            "comments": 0.20,
            "shares": 0.30,
            "saves": 0.35,
            "ctr": 0.05,  # link clicks / impressions (if available)
        },
        "tiktok": {
            "likes": 0.10,
            "comments": 0.15,
            "shares": 0.40,  # TikTok shares are the strongest signal
            "saves": 0.30,
            "ctr": 0.05,
        },
        "youtube": {
            "likes": 0.10,
            "comments": 0.25,
            "shares": 0.25,
            "saves": 0.30,  # watch later / playlist adds
            "ctr": 0.10,  # click-through rate from thumbnail
        },
        "linkedin": {
            "likes": 0.15,  # "reactions" on LinkedIn
            "comments": 0.30,
            "shares": 0.35,  # reshares are king on LinkedIn
            "saves": 0.15,
            "ctr": 0.05,
        },
        "twitter": {
            "likes": 0.10,
            "comments": 0.20,  # replies
            "shares": 0.40,  # retweets/reposts
            "saves": 0.20,  # bookmarks
            "ctr": 0.10,
        },
    }
    
    @staticmethod
    def compute_eqi(
        likes: int = 0,
        comments: int = 0,
        shares: int = 0,
        saves: int = 0,
        impressions: int = 0,
        reach: int = 0,
        link_clicks: int = 0,
        negative_sentiment_ratio: float = 0.0,
        platform: str = "instagram",
    ) -> float:
        """
        Compute EQI score for a post.
        
        Returns a 0-100 score where:
        - 0-20: Low engagement
        - 20-40: Below average
        - 40-60: Average
        - 60-80: Good
        - 80-100: Exceptional
        """
        weights = EQIService.PLATFORM_WEIGHTS.get(platform, EQIService.PLATFORM_WEIGHTS["instagram"])
        
        # Normalize by reach (or impressions as fallback)
        denominator = max(reach, impressions, 1)
        
        # Engagement rates per metric
        like_rate = likes / denominator
        comment_rate = comments / denominator
        share_rate = shares / denominator
        save_rate = saves / denominator
        ctr = link_clicks / max(impressions, 1) if impressions > 0 else 0
        
        # Weighted sum (raw engagement rate)
        raw_score = (
            weights["likes"] * like_rate +
            weights["comments"] * comment_rate +
            weights["shares"] * share_rate +
            weights["saves"] * save_rate +
            weights["ctr"] * ctr
        )
        
        # Scale to 0-100 range
        # Typical good engagement rate is 3-6% on Instagram, so scale accordingly
        scaled_score = min(100, raw_score * 1000)  # 10% engagement = 100
        
        # Apply sentiment penalty (§4)
        # negative_sentiment_ratio = fraction of comments that are negative
        sentiment_penalty = 1.0 - (negative_sentiment_ratio * 0.3)  # max 30% penalty
        sentiment_penalty = max(0.5, sentiment_penalty)  # floor at 50% of score
        
        final_score = scaled_score * sentiment_penalty
        
        return round(final_score, 2)
    
    @staticmethod
    def compute_eqi_from_post(post_data: dict, platform: str = "instagram") -> float:
        """Convenience method to compute EQI from a post dict."""
        return EQIService.compute_eqi(
            likes=post_data.get("likes", 0),
            comments=post_data.get("comments_count", 0),
            shares=post_data.get("shares", 0),
            saves=post_data.get("saves", 0),
            impressions=post_data.get("impressions", 0),
            reach=post_data.get("reach", 0),
            platform=platform,
        )
    
    @staticmethod
    def get_engagement_tier(eqi_score: float) -> str:
        """Human-readable engagement tier."""
        if eqi_score >= 80:
            return "exceptional"
        elif eqi_score >= 60:
            return "good"
        elif eqi_score >= 40:
            return "average"
        elif eqi_score >= 20:
            return "below_average"
        else:
            return "low"
    
    @staticmethod
    def compute_trend_delta(current_eqi: float, previous_eqi: float) -> dict:
        """Compute trend delta between periods."""
        if previous_eqi == 0:
            change_pct = 100.0 if current_eqi > 0 else 0.0
        else:
            change_pct = ((current_eqi - previous_eqi) / previous_eqi) * 100
        
        return {
            "current": current_eqi,
            "previous": previous_eqi,
            "change_pct": round(change_pct, 1),
            "direction": "up" if change_pct > 0 else "down" if change_pct < 0 else "flat",
            "tier": EQIService.get_engagement_tier(current_eqi),
        }
