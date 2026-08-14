"""
Pulse — Mock Platform API Service (§7.11)
Simulates Instagram Graph API / other platform responses for demo/sandbox mode.
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Optional


class MockPlatformAPI:
    """
    Simulates platform API responses for hackathon demo.
    In production, this would be replaced with real Graph API calls.
    """
    
    @staticmethod
    def publish_post(
        content: str,
        platform: str = "instagram",
        media_url: Optional[str] = None,
    ) -> dict:
        """Simulate publishing a post. Returns mock post ID and status."""
        return {
            "success": True,
            "post_id": f"mock_{platform}_{uuid.uuid4().hex[:12]}",
            "platform": platform,
            "published_at": datetime.utcnow().isoformat(),
            "permalink": f"https://www.instagram.com/p/{uuid.uuid4().hex[:11]}/",
            "status": "published",
        }
    
    @staticmethod
    def get_post_insights(post_id: str) -> dict:
        """Simulate post insights / metrics."""
        base_impressions = random.randint(5000, 50000)
        reach = int(base_impressions * random.uniform(0.7, 0.95))
        
        return {
            "post_id": post_id,
            "impressions": base_impressions,
            "reach": reach,
            "likes": random.randint(100, int(reach * 0.15)),
            "comments": random.randint(10, int(reach * 0.02)),
            "shares": random.randint(5, int(reach * 0.01)),
            "saves": random.randint(20, int(reach * 0.03)),
            "profile_visits": random.randint(10, 200),
            "follows": random.randint(0, 30),
        }
    
    @staticmethod
    def get_account_insights() -> dict:
        """Simulate account-level insights."""
        return {
            "followers_count": 85200,
            "followers_delta_7d": random.randint(50, 300),
            "accounts_reached_7d": random.randint(15000, 45000),
            "accounts_engaged_7d": random.randint(3000, 12000),
            "content_interactions_7d": random.randint(5000, 20000),
            "profile_views_7d": random.randint(800, 3000),
            "website_clicks_7d": random.randint(50, 300),
            "demographics": {
                "age_gender": {
                    "18-24": {"male": 12, "female": 18},
                    "25-34": {"male": 22, "female": 28},
                    "35-44": {"male": 8, "female": 7},
                    "45+": {"male": 2, "female": 3},
                },
                "top_cities": [
                    {"name": "Delhi", "pct": 22},
                    {"name": "Mumbai", "pct": 18},
                    {"name": "Bangalore", "pct": 12},
                    {"name": "Pune", "pct": 8},
                    {"name": "Hyderabad", "pct": 6},
                ],
                "top_countries": [
                    {"name": "India", "pct": 85},
                    {"name": "United States", "pct": 5},
                    {"name": "United Kingdom", "pct": 3},
                    {"name": "Canada", "pct": 2},
                    {"name": "Australia", "pct": 1},
                ],
            },
        }
    
    @staticmethod
    def get_recent_comments(post_id: Optional[str] = None, limit: int = 20) -> List[dict]:
        """Simulate fetching recent comments."""
        from app.db.seed_data import DEMO_COMMENTS
        
        comments = []
        for i, c in enumerate(DEMO_COMMENTS[:limit]):
            comments.append({
                "id": f"comment_{uuid.uuid4().hex[:8]}",
                "post_id": post_id or f"mock_post_{i}",
                "text": c["content"],
                "from": {
                    "id": f"user_{uuid.uuid4().hex[:8]}",
                    "username": c["author"],
                    "is_verified": c.get("is_verified", False),
                },
                "timestamp": (datetime.utcnow() - timedelta(hours=random.randint(1, 48))).isoformat(),
                "like_count": random.randint(0, 20),
            })
        
        return comments
    
    @staticmethod
    def send_reply(comment_id: str, message: str) -> dict:
        """Simulate sending a reply to a comment/DM."""
        return {
            "success": True,
            "reply_id": f"reply_{uuid.uuid4().hex[:8]}",
            "comment_id": comment_id,
            "message": message,
            "sent_at": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def get_trending_hashtags(platform: str = "instagram") -> List[dict]:
        """Simulate trending hashtags/topics."""
        trends = [
            {"tag": "#MorningRoutine", "volume": 2500000, "velocity": "+45%", "category": "wellness"},
            {"tag": "#ProteinRecipes", "volume": 890000, "velocity": "+120%", "category": "nutrition"},
            {"tag": "#5MinWorkout", "volume": 1200000, "velocity": "+80%", "category": "fitness"},
            {"tag": "#MindfulMonday", "volume": 650000, "velocity": "+30%", "category": "mindfulness"},
            {"tag": "#HomeGym", "volume": 3100000, "velocity": "+15%", "category": "fitness"},
            {"tag": "#HealthyMealPrep", "volume": 1800000, "velocity": "+60%", "category": "nutrition"},
            {"tag": "#YogaFlow", "volume": 920000, "velocity": "+25%", "category": "wellness"},
            {"tag": "#RunningCommunity", "volume": 750000, "velocity": "+35%", "category": "fitness"},
            {"tag": "#SleepHacks", "volume": 430000, "velocity": "+200%", "category": "wellness"},
            {"tag": "#FitnessMotivation", "volume": 8500000, "velocity": "+5%", "category": "fitness"},
        ]
        random.shuffle(trends)
        return trends[:5]
