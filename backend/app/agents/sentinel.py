"""
Pulse — Sentinel Agent (Comment Triage §7.8 + Sentiment Circuit Breaker §6.9)
2×2 risk matrix routing populated by dedicated classifiers.
"""

import random
from typing import List, Optional, Tuple
from datetime import datetime


class SentimentClassifier:
    """
    Sentiment classification (§7.8).
    In production: cardiffnlp/twitter-roberta-base-sentiment-latest
    For hackathon demo: rule-based + keyword classifier as fallback.
    """
    
    _model = None
    _tokenizer = None
    _labels = ["negative", "neutral", "positive"]
    
    @classmethod
    def load_model(cls):
        """Try to load the real RoBERTa model; fall back to rules."""
        if cls._model is not None:
            return True
        try:
            # pyrefly: ignore [missing-import]
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
            model_name = "cardiffnlp/twitter-roberta-base-sentiment-latest"
            cls._tokenizer = AutoTokenizer.from_pretrained(model_name)
            cls._model = AutoModelForSequenceClassification.from_pretrained(model_name)
            return True
        except Exception:
            return False
    
    @classmethod
    def classify(cls, text: str) -> Tuple[str, float]:
        """
        Classify sentiment. Returns (label, score).
        label: "positive", "neutral", "negative"
        score: -1 to 1
        """
        # Try real model first
        if cls.load_model() and cls._model is not None:
            try:
                # pyrefly: ignore [missing-import]
                import torch
                inputs = cls._tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
                with torch.no_grad():
                    outputs = cls._model(**inputs)
                scores = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]
                
                # Map to label
                label_idx = scores.argmax().item()
                label = cls._labels[label_idx]
                
                # Convert to -1 to 1 score
                neg, neu, pos = scores.tolist()
                score = pos - neg  # -1 to 1
                
                return label, round(score, 3)
            except Exception:
                pass
        
        # Rule-based fallback
        return cls._rule_based_classify(text)
    
    @staticmethod
    def _rule_based_classify(text: str) -> Tuple[str, float]:
        """Simple keyword-based sentiment for demo."""
        text_lower = text.lower()
        
        positive_words = [
            "love", "great", "amazing", "awesome", "perfect", "best",
            "thank", "helpful", "inspired", "beautiful", "fantastic",
            "❤️", "🔥", "💪", "✨", "😍", "👏", "🙌", "exactly",
            "needed", "crushing", "queen", "king", "legend",
        ]
        negative_words = [
            "hate", "terrible", "worst", "bad", "stupid", "waste",
            "irresponsible", "wrong", "hurt", "injured", "scam",
            "fake", "dangerous", "misleading", "awful", "disgusting",
            "disappointed", "unfollow", "unfollowed", "boring",
        ]
        spam_indicators = [
            "free followers", "link in bio", "check my page",
            "dm me for", "working from home", "$", "💰",
        ]
        
        pos_count = sum(1 for w in positive_words if w in text_lower)
        neg_count = sum(1 for w in negative_words if w in text_lower)
        
        # Check for spam (treat as neutral)
        if any(indicator in text_lower for indicator in spam_indicators):
            return "neutral", 0.0
        
        total = pos_count + neg_count
        if total == 0:
            return "neutral", 0.0
        
        score = (pos_count - neg_count) / max(total, 1)
        
        if score > 0.3:
            return "positive", min(score, 1.0)
        elif score < -0.3:
            return "negative", max(score, -1.0)
        else:
            return "neutral", score


class IntentClassifier:
    """
    Intent classification for comment/DM routing (§7.8).
    Classifies into: faq, spam, collaboration, complaint, positive, neutral, press.
    """
    
    FAQ_PATTERNS = [
        "how", "what", "when", "where", "which", "can i", "do you",
        "how much", "how many", "is it", "does it", "should i",
        "what brand", "what type", "recommend", "suggestion",
        "beginner", "alternative", "calories", "injury",
    ]
    
    SPAM_PATTERNS = [
        "free followers", "check my page", "link in bio",
        "dm me", "working from home", "make money", "crypto",
        "check out my", "visit my", "follow me", "f4f",
        "giveaway", "win a", "earn $", "💰💰",
    ]
    
    COLLAB_PATTERNS = [
        "collaboration", "collab", "partnership", "sponsor",
        "rate card", "work together", "brand deal", "send you",
        "review", "ambassador", "campaign", "pitch",
        "interested in working", "love to discuss",
    ]
    
    PRESS_PATTERNS = [
        "journalist", "magazine", "article", "interview",
        "feature", "story about", "press", "media",
        "publication", "editor", "writing about",
    ]
    
    COMPLAINT_PATTERNS = [
        "hurt", "injured", "dangerous", "irresponsible",
        "wrong", "misleading", "fake", "scam", "sue",
        "report", "stop", "harmful", "not qualified",
        "certified", "credentials",
    ]
    
    @classmethod
    def classify(cls, text: str) -> Tuple[str, float]:
        """
        Classify intent. Returns (intent, confidence).
        """
        text_lower = text.lower()
        
        scores = {}
        
        # Check each pattern category
        for intent, patterns in [
            ("spam", cls.SPAM_PATTERNS),
            ("collaboration", cls.COLLAB_PATTERNS),
            ("press", cls.PRESS_PATTERNS),
            ("complaint", cls.COMPLAINT_PATTERNS),
            ("faq", cls.FAQ_PATTERNS),
        ]:
            matches = sum(1 for p in patterns if p in text_lower)
            if matches > 0:
                scores[intent] = min(matches / 3, 1.0)  # Normalize
        
        if not scores:
            # Default: check if it's a question
            if "?" in text:
                return "faq", 0.5
            
            # Check sentiment for positive/neutral
            sentiment_label, _ = SentimentClassifier._rule_based_classify(text)
            if sentiment_label == "positive":
                return "positive", 0.7
            return "neutral", 0.6
        
        # Return highest scoring intent
        best_intent = max(scores, key=scores.get)
        return best_intent, round(scores[best_intent], 2)


class RiskMatrix:
    """
    2×2 Risk Matrix routing (§7.8 — from Draft B):
    
    ┌─────────────────┬──────────────────┬──────────────────┐
    │                 │ Low Brand Risk   │ High Brand Risk  │
    ├─────────────────┼──────────────────┼──────────────────┤
    │ High Confidence │ AUTO-REPLY       │ HUMAN REVIEW     │
    │                 │ (FAQ, hours)     │ (sales lead)     │
    ├─────────────────┼──────────────────┼──────────────────┤
    │ Low Confidence  │ LOG ONLY         │ ESCALATE         │
    │                 │ (generic comment)│ (possible PR)    │
    └─────────────────┴──────────────────┴──────────────────┘
    """
    
    CONFIDENCE_THRESHOLD = 0.6
    
    # Intent → brand risk mapping
    RISK_MAP = {
        "faq": "low",
        "positive": "low",
        "neutral": "low",
        "spam": "low",
        "collaboration": "high",
        "press": "high",
        "complaint": "high",
    }
    
    @classmethod
    def route(cls, intent: str, confidence: float, sentiment_score: float, is_verified: bool = False) -> dict:
        """
        Route a comment through the risk matrix.
        Returns action + metadata.
        """
        brand_risk = cls.RISK_MAP.get(intent, "low")
        
        # Verified accounts bump to high risk (they matter more)
        if is_verified and brand_risk == "low":
            brand_risk = "high"
        
        # Very negative sentiment bumps risk
        if sentiment_score < -0.5:
            brand_risk = "high"
        
        # Determine confidence level
        high_confidence = confidence >= cls.CONFIDENCE_THRESHOLD
        
        # Route through matrix
        if high_confidence and brand_risk == "low":
            action = "auto_reply"
            cell = "high_conf_low_risk"
            reason = f"Auto-reply eligible: {intent} intent with {confidence:.0%} confidence, low brand risk"
        elif high_confidence and brand_risk == "high":
            action = "human_review"
            cell = "high_conf_high_risk"
            reason = f"Human review needed: {intent} intent with {confidence:.0%} confidence, high brand risk"
        elif not high_confidence and brand_risk == "low":
            action = "log_only"
            cell = "low_conf_low_risk"
            reason = f"Logged: {intent} intent with {confidence:.0%} confidence, low brand risk — no action needed"
        else:  # low confidence, high risk
            action = "escalate_immediate"
            cell = "low_conf_high_risk"
            reason = f"ESCALATE: possible {intent} with only {confidence:.0%} confidence + high brand risk"
        
        return {
            "action": action,
            "cell": cell,
            "brand_risk": brand_risk,
            "intent_confidence": confidence,
            "reason": reason,
        }


class SentinelAgent:
    """
    Sentinel persona — Comment triage + sentiment circuit breaker.
    """
    
    def __init__(self):
        self.sentiment_classifier = SentimentClassifier()
        self.intent_classifier = IntentClassifier()
        self.risk_matrix = RiskMatrix()
        self.sentiment_history: List[float] = []
    
    def triage_comment(self, text: str, is_verified: bool = False) -> dict:
        """
        Full triage pipeline for a single comment:
        1. Sentiment classification
        2. Intent classification
        3. Risk matrix routing
        """
        # Step 1: Sentiment
        sentiment_label, sentiment_score = self.sentiment_classifier.classify(text)
        
        # Step 2: Intent
        intent, intent_confidence = self.intent_classifier.classify(text)
        
        # Step 3: Risk matrix
        routing = self.risk_matrix.route(
            intent=intent,
            confidence=intent_confidence,
            sentiment_score=sentiment_score,
            is_verified=is_verified,
        )
        
        # Track sentiment for circuit breaker
        self.sentiment_history.append(sentiment_score)
        
        return {
            "sentiment_label": sentiment_label,
            "sentiment_score": round(sentiment_score, 3),
            "intent": intent,
            "intent_confidence": round(intent_confidence, 2),
            "brand_risk": routing["brand_risk"],
            "triage_action": routing["action"],
            "risk_matrix_cell": routing["cell"],
            "reason": routing["reason"],
        }
    
    def check_circuit_breaker(
        self,
        recent_sentiments: Optional[List[float]] = None,
        threshold: float = -0.6,
        window_size: int = 10,
        negative_ratio_trigger: float = 0.5,
    ) -> dict:
        """
        Sentiment-spike circuit breaker (§6.9):
        If comment sentiment crosses negative threshold in a short window,
        triggers alert to pause scheduled posts.
        """
        sentiments = recent_sentiments or self.sentiment_history[-window_size:]
        
        if not sentiments:
            return {"triggered": False, "reason": "No sentiment data available"}
        
        # Calculate metrics
        negative_count = sum(1 for s in sentiments if s < threshold)
        negative_ratio = negative_count / len(sentiments)
        avg_sentiment = sum(sentiments) / len(sentiments)
        
        triggered = negative_ratio >= negative_ratio_trigger
        
        return {
            "triggered": triggered,
            "negative_ratio": round(negative_ratio, 2),
            "avg_sentiment": round(avg_sentiment, 3),
            "window_size": len(sentiments),
            "negative_count": negative_count,
            "threshold": threshold,
            "reason": (
                f"CIRCUIT BREAKER TRIGGERED: {negative_count}/{len(sentiments)} comments "
                f"({negative_ratio:.0%}) below sentiment threshold ({threshold}). "
                f"Recommend pausing scheduled posts and reviewing."
                if triggered else
                f"Normal: {negative_count}/{len(sentiments)} negative comments "
                f"({negative_ratio:.0%}), below trigger threshold ({negative_ratio_trigger:.0%})"
            ),
        }
    
    async def generate_auto_reply(
        self,
        comment_text: str,
        intent: str,
        brand_name: str = "FitVibe",
        brand_guidelines: Optional[List[str]] = None,
    ) -> str:
        """
        Generate an auto-reply in brand voice.
        Only called for high-confidence, low-risk comments.
        """
        # Try LLM first
        try:
            # pyrefly: ignore [missing-import]
            from langchain_google_genai import ChatGoogleGenerativeAI
            from app.config import settings
            
            if settings.google_api_key:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=settings.google_api_key,
                    temperature=0.6,
                )
                
                prompt = f"""You are replying to a comment on {brand_name}'s social media post.
Brand voice: warm, encouraging, conversational. Never corporate or robotic.

Comment: "{comment_text}"
Intent: {intent}

Write a brief, on-brand reply (1-2 sentences max). Be helpful and genuine.
Return ONLY the reply text, nothing else."""
                
                response = await llm.ainvoke(prompt)
                return response.content.strip()
        except Exception:
            pass
        
        # Template fallback
        templates = {
            "faq": [
                f"Great question! 🙌 Check out our highlights for more details on that. Let us know if you need anything else!",
                f"Thanks for asking! We've got a guide saved in our highlights that covers this. Hope it helps 💪",
                f"Good one! Short answer: it depends on where you're starting from. Check our latest carousel for a breakdown ✨",
            ],
            "positive": [
                f"This made our day! Thanks for being part of the community 💪✨",
                f"You're amazing! So glad this resonated with you 🙌",
            ],
            "neutral": [
                f"Thanks for stopping by! 🙌",
                f"Appreciate you! ✨",
            ],
        }
        
        options = templates.get(intent, templates["neutral"])
        return random.choice(options)
