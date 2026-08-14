"""
Pulse — Strategist Agent (Peak-Time Prediction §7.6)
Heuristic historical heatmap + LinUCB bandit scaffolding with EQI reward.
"""

import math
import random
# pyrefly: ignore [missing-import]
import numpy as np
from typing import List, Optional, Tuple
from datetime import datetime, timedelta

from app.services.eqi import EQIService


DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


class HeuristicHeatmap:
    """
    Heuristic peak-time recommendation (§7.6 option 1):
    Trivial, interpretable, serves as cold-start fallback.
    """
    
    @staticmethod
    def compute_heatmap(engagement_data: List[dict]) -> List[dict]:
        """
        Build engagement heatmap from historical data.
        Each entry: {hour, day_of_week, engagement_score}
        """
        heatmap = {}
        
        for entry in engagement_data:
            key = (entry["hour_of_day"], entry["day_of_week"])
            if key not in heatmap:
                heatmap[key] = []
            heatmap[key].append(entry.get("engagement_score", 0))
        
        results = []
        for (hour, day), scores in heatmap.items():
            avg_score = sum(scores) / len(scores) if scores else 0
            results.append({
                "hour": hour,
                "day_of_week": day,
                "day_name": DAY_NAMES[day],
                "engagement_score": round(avg_score, 3),
            })
        
        results.sort(key=lambda x: x["engagement_score"], reverse=True)
        return results
    
    @staticmethod
    def get_top_slots(heatmap: List[dict], n: int = 5) -> List[dict]:
        """Get top-n posting slots with reasons."""
        top = heatmap[:n]
        for slot in top:
            hour = slot["hour"]
            day = slot["day_name"]
            score = slot["engagement_score"]
            
            # Generate human-readable reason
            time_str = f"{hour:02d}:00"
            if 6 <= hour <= 9:
                period = "morning"
                why = f"Your audience is most active during {period} hours"
            elif 12 <= hour <= 14:
                period = "lunch break"
                why = f"High engagement during {period} — people scrolling while eating"
            elif 18 <= hour <= 21:
                period = "evening"
                why = f"Peak scroll time — your {slot.get('day_name', '')} evenings see {score:.0%} engagement"
            elif 21 <= hour <= 23:
                period = "night"
                why = f"Strong late-night engagement on {day}s"
            else:
                period = "off-peak"
                why = f"Above-average engagement at {time_str} on {day}s"
            
            slot["reason"] = why
            slot["time_str"] = time_str
        
        return top
    
    @staticmethod
    def recommend_time(
        heatmap: List[dict],
        platform: str = "instagram",
        avoid_hours: Optional[List[int]] = None,
    ) -> dict:
        """Get single best posting time recommendation."""
        available = heatmap
        if avoid_hours:
            available = [s for s in heatmap if s["hour"] not in avoid_hours]
        
        if not available:
            available = heatmap
        
        best = available[0] if available else {"hour": 19, "day_of_week": 5, "day_name": "Saturday", "engagement_score": 0.9}
        
        # Find the next occurrence of this day/hour
        now = datetime.utcnow()
        target_day = best["day_of_week"]
        target_hour = best["hour"]
        
        days_ahead = target_day - now.weekday()
        if days_ahead < 0:
            days_ahead += 7
        if days_ahead == 0 and now.hour >= target_hour:
            days_ahead += 7
        
        recommended_dt = (now + timedelta(days=days_ahead)).replace(
            hour=target_hour, minute=0, second=0, microsecond=0
        )
        
        return {
            "datetime": recommended_dt,
            "hour": target_hour,
            "day_of_week": target_day,
            "day_name": best["day_name"],
            "score": best["engagement_score"],
            "reason": f"Your {best['day_name']} {target_hour:02d}:00 posts see {best['engagement_score']:.0%} "
                      f"of peak engagement — your audience's most active window on this day.",
        }


class LinUCBBandit:
    """
    LinUCB contextual bandit for peak-time optimization (§7.6 option 3):
    Frames slot selection as explore/exploit under uncertainty.
    Reward signal = EQI (§4).
    
    For hackathon: initialized with synthetic/seeded data to demonstrate
    the learning mechanism.
    """
    
    def __init__(self, n_arms: int = 168, n_features: int = 10, alpha: float = 0.5):
        """
        n_arms: 168 = 24 hours × 7 days
        n_features: context features (post type, topic category, etc.)
        alpha: exploration parameter
        """
        self.n_arms = n_arms
        self.n_features = n_features
        self.alpha = alpha
        
        # Per-arm parameters
        self.A = [np.eye(n_features) for _ in range(n_arms)]
        self.b = [np.zeros(n_features) for _ in range(n_arms)]
    
    def arm_index(self, hour: int, day: int) -> int:
        """Convert (hour, day) to arm index."""
        return day * 24 + hour
    
    def get_context_features(
        self,
        post_type: str = "text",
        topic_category: str = "fitness",
        content_length: int = 500,
        has_media: bool = False,
        follower_count: int = 85000,
        is_weekend: bool = False,
    ) -> np.ndarray:
        """Build context feature vector."""
        post_type_map = {"text": 0, "carousel": 1, "reel": 2, "story": 3}
        topic_map = {"fitness": 0, "nutrition": 1, "wellness": 2, "community": 3, "mindfulness": 4}
        
        features = np.array([
            post_type_map.get(post_type, 0) / 3,
            topic_map.get(topic_category, 0) / 4,
            min(content_length, 2200) / 2200,
            1.0 if has_media else 0.0,
            min(follower_count, 1000000) / 1000000,
            1.0 if is_weekend else 0.0,
            0.5,  # placeholder: avg recent engagement rate
            0.5,  # placeholder: content novelty score
            0.5,  # placeholder: audience overlap with topic
            1.0,  # bias term
        ])
        
        return features
    
    def select_arm(self, context: np.ndarray, top_k: int = 5) -> List[dict]:
        """
        Select best arms using UCB scores.
        Returns top-k recommendations with uncertainty estimates.
        """
        ucb_scores = []
        
        for arm in range(self.n_arms):
            A_inv = np.linalg.inv(self.A[arm])
            theta = A_inv @ self.b[arm]
            
            # UCB = predicted reward + exploration bonus
            predicted = float(context @ theta)
            uncertainty = float(self.alpha * np.sqrt(context @ A_inv @ context))
            ucb = predicted + uncertainty
            
            hour = arm % 24
            day = arm // 24
            
            ucb_scores.append({
                "arm": arm,
                "hour": hour,
                "day_of_week": day,
                "day_name": DAY_NAMES[day],
                "predicted_eqi": round(max(0, predicted * 100), 1),
                "uncertainty": round(uncertainty * 100, 1),
                "ucb_score": round(ucb, 4),
                "is_exploring": uncertainty > abs(predicted) * 0.5,
            })
        
        # Sort by UCB score
        ucb_scores.sort(key=lambda x: x["ucb_score"], reverse=True)
        
        return ucb_scores[:top_k]
    
    def update(self, arm: int, context: np.ndarray, reward: float):
        """Update arm with observed reward (EQI score)."""
        normalized_reward = reward / 100  # EQI is 0-100, normalize to 0-1
        self.A[arm] += np.outer(context, context)
        self.b[arm] += normalized_reward * context
    
    def seed_with_heatmap(self, heatmap: List[dict]):
        """
        Seed the bandit with historical heatmap data.
        This initializes the model so it has a starting point.
        """
        default_context = self.get_context_features()
        
        for entry in heatmap:
            arm = self.arm_index(entry["hour_of_day"], entry["day_of_week"])
            reward = entry.get("engagement_score", 0.5) * 100  # Scale to EQI range
            
            # Add some noise to simulate varied observations
            for _ in range(3):
                noisy_reward = reward + random.uniform(-10, 10)
                noisy_reward = max(0, min(100, noisy_reward))
                self.update(arm, default_context, noisy_reward)


class StrategistAgent:
    """
    Strategist persona — combines heuristic heatmap (always available)
    with LinUCB bandit (when sufficient data exists).
    """
    
    def __init__(self):
        self.heatmap_engine = HeuristicHeatmap()
        self.bandit = LinUCBBandit()
        self._seeded = False
    
    def seed(self, engagement_data: List[dict]):
        """Initialize with historical engagement data."""
        self.engagement_data = engagement_data
        self.heatmap = self.heatmap_engine.compute_heatmap(engagement_data)
        self.bandit.seed_with_heatmap(engagement_data)
        self._seeded = True
    
    def get_recommendation(
        self,
        platform: str = "instagram",
        post_type: str = "text",
        use_bandit: bool = True,
    ) -> dict:
        """
        Get posting time recommendation.
        Returns both heuristic and bandit recommendations for comparison.
        """
        # Heuristic recommendation (always available)
        heuristic = self.heatmap_engine.recommend_time(
            self.heatmap if self._seeded else [],
            platform=platform,
        )
        
        result = {
            "heuristic": heuristic,
            "bandit": None,
            "recommended": heuristic,
            "method": "heuristic_heatmap",
        }
        
        # Bandit recommendation (if seeded)
        if use_bandit and self._seeded:
            context = self.bandit.get_context_features(post_type=post_type)
            bandit_picks = self.bandit.select_arm(context, top_k=3)
            
            if bandit_picks:
                best = bandit_picks[0]
                
                # Find next occurrence of this slot
                now = datetime.utcnow()
                target_day = best["day_of_week"]
                target_hour = best["hour"]
                
                days_ahead = target_day - now.weekday()
                if days_ahead < 0:
                    days_ahead += 7
                if days_ahead == 0 and now.hour >= target_hour:
                    days_ahead += 7
                
                recommended_dt = (now + timedelta(days=days_ahead)).replace(
                    hour=target_hour, minute=0, second=0, microsecond=0
                )
                
                result["bandit"] = {
                    "datetime": recommended_dt,
                    "picks": bandit_picks,
                    "reason": f"LinUCB bandit recommends {best['day_name']} at {best['hour']:02d}:00 "
                              f"(predicted EQI: {best['predicted_eqi']}, "
                              f"{'exploring' if best['is_exploring'] else 'exploiting'})",
                }
                result["recommended"] = {
                    "datetime": recommended_dt,
                    "hour": target_hour,
                    "day_of_week": target_day,
                    "day_name": best["day_name"],
                    "score": best["predicted_eqi"] / 100,
                    "reason": result["bandit"]["reason"],
                }
                result["method"] = "linucb_bandit"
        
        return result
    
    def get_heatmap(self) -> List[dict]:
        """Get full engagement heatmap for visualization."""
        if self._seeded:
            return self.heatmap
        return []
    
    def get_top_slots(self, n: int = 5) -> List[dict]:
        """Get top posting slots."""
        if self._seeded:
            return self.heatmap_engine.get_top_slots(self.heatmap, n)
        return []
