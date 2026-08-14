"""
Pulse — Voice Engine Service (§7.4, §7.5)
Brand voice analysis: embeddings, centroid computation, structural profile caching,
voice similarity scoring, and slop rubric checking.
"""

import re
import math
import numpy as np
from typing import List, Optional, Tuple
from app.config import settings


# ──────────────────────────────────────────────
# Lightweight embedding (demo mode — no GPU needed)
# In production, use sentence-transformers
# ──────────────────────────────────────────────

class VoiceEngine:
    """
    Handles brand voice analysis per PRD §7.4:
    - Compute voice centroid embedding from sample posts
    - Cache structural profile (avg sentence length, emoji frequency, hashtag placement)
    - Similarity scoring for guardrail checks
    - Slop rubric for cliché detection
    """
    
    _embedder = None
    
    @classmethod
    def get_embedder(cls):
        """Lazy-load sentence transformer model."""
        if cls._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                cls._embedder = SentenceTransformer(settings.embedding_model)
            except Exception:
                # Fallback: use a simple hash-based embedding for demo
                cls._embedder = None
        return cls._embedder
    
    @staticmethod
    def compute_embedding(text: str) -> List[float]:
        """Compute embedding for a text. Falls back to hash-based if no model available."""
        embedder = VoiceEngine.get_embedder()
        if embedder is not None:
            embedding = embedder.encode(text, normalize_embeddings=True)
            return embedding.tolist()
        else:
            # Deterministic hash-based fallback for demo
            return VoiceEngine._hash_embedding(text)
    
    @staticmethod
    def _hash_embedding(text: str, dim: int = 384) -> List[float]:
        """Simple hash-based embedding fallback for demo mode."""
        import hashlib
        text_bytes = text.encode('utf-8')
        embeddings = []
        for i in range(dim):
            h = hashlib.sha256(text_bytes + i.to_bytes(4, 'big')).hexdigest()
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2 - 1  # normalize to [-1, 1]
            embeddings.append(round(val, 6))
        # L2 normalize
        norm = math.sqrt(sum(x*x for x in embeddings))
        if norm > 0:
            embeddings = [x / norm for x in embeddings]
        return embeddings
    
    @staticmethod
    def compute_centroid(embeddings: List[List[float]]) -> List[float]:
        """Compute voice centroid (mean embedding) from a list of post embeddings."""
        if not embeddings:
            return [0.0] * settings.embedding_dimension
        arr = np.array(embeddings)
        centroid = np.mean(arr, axis=0)
        # L2 normalize
        norm = np.linalg.norm(centroid)
        if norm > 0:
            centroid = centroid / norm
        return centroid.tolist()
    
    @staticmethod
    def cosine_similarity(a: List[float], b: List[float]) -> float:
        """Cosine similarity between two embeddings."""
        a_arr = np.array(a)
        b_arr = np.array(b)
        dot = np.dot(a_arr, b_arr)
        norm_a = np.linalg.norm(a_arr)
        norm_b = np.linalg.norm(b_arr)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return float(dot / (norm_a * norm_b))
    
    @staticmethod
    def compute_structural_profile(posts: List[str]) -> dict:
        """
        Compute cached structural profile per PRD §7.4c:
        - avg sentence length
        - emoji frequency & placement
        - hashtag count & placement
        - avg post length
        - tone keywords
        """
        if not posts:
            return {}
        
        sentence_lengths = []
        emoji_counts = []
        emoji_placements = {"start": 0, "end": 0, "inline": 0, "none": 0}
        hashtag_counts = []
        hashtag_placements = {"end": 0, "inline": 0, "none": 0}
        post_lengths = []
        
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE
        )
        
        for post in posts:
            # Post length
            post_lengths.append(len(post))
            
            # Sentences
            sentences = re.split(r'[.!?]+', post)
            sentences = [s.strip() for s in sentences if s.strip()]
            for s in sentences:
                words = s.split()
                sentence_lengths.append(len(words))
            
            # Emojis
            emojis = emoji_pattern.findall(post)
            emoji_counts.append(len(emojis))
            if emojis:
                lines = post.strip().split('\n')
                first_line = lines[0] if lines else ""
                last_line = lines[-1] if lines else ""
                if emoji_pattern.search(first_line) and len(lines) > 1:
                    emoji_placements["start"] += 1
                if emoji_pattern.search(last_line):
                    emoji_placements["end"] += 1
                emoji_placements["inline"] += 1
            else:
                emoji_placements["none"] += 1
            
            # Hashtags
            hashtags = re.findall(r'#\w+', post)
            hashtag_counts.append(len(hashtags))
            if hashtags:
                lines = post.strip().split('\n')
                last_line = lines[-1] if lines else ""
                if '#' in last_line and len([l for l in lines if '#' in l]) == 1:
                    hashtag_placements["end"] += 1
                else:
                    hashtag_placements["inline"] += 1
            else:
                hashtag_placements["none"] += 1
        
        n = len(posts)
        
        # Determine dominant placements
        emoji_placement = max(emoji_placements, key=emoji_placements.get)
        hashtag_placement = max(hashtag_placements, key=hashtag_placements.get)
        
        return {
            "avg_sentence_length": round(sum(sentence_lengths) / max(len(sentence_lengths), 1), 1),
            "emoji_frequency": round(sum(emoji_counts) / n, 1),
            "emoji_placement": emoji_placement,
            "hashtag_count_avg": round(sum(hashtag_counts) / n, 1),
            "hashtag_placement": hashtag_placement,
            "avg_post_length": round(sum(post_lengths) / n, 0),
            "tone_keywords": VoiceEngine._extract_tone_keywords(posts),
        }
    
    @staticmethod
    def _extract_tone_keywords(posts: List[str]) -> dict:
        """Simple tone analysis based on keyword presence."""
        tone_markers = {
            "casual": ["lol", "tbh", "ngl", "y'all", "gonna", "wanna", "idk", "haha", "😏", "😂", "vibes"],
            "encouraging": ["you can", "you've got", "let's", "keep going", "proud", "amazing", "crush", "strong", "💪"],
            "informative": ["here's", "how to", "step", "tip", "guide", "learn", "research", "studies"],
            "conversational": ["?", "drop", "tell me", "what's your", "thoughts?", "👇", "be honest"],
            "authentic": ["real talk", "honestly", "not gonna lie", "truth", "unpopular opinion", "hot take"],
        }
        
        scores = {}
        total_posts = len(posts)
        all_text = " ".join(posts).lower()
        
        for tone, markers in tone_markers.items():
            count = sum(1 for m in markers if m.lower() in all_text)
            scores[tone] = round(count / len(markers), 2)
        
        return scores
    
    # ──────────────────────────────────────────────
    # Slop Rubric (§6.3 — cliché detection)
    # ──────────────────────────────────────────────
    
    SLOP_PHRASES = [
        "in today's fast-paced world",
        "as we navigate",
        "it's important to remember",
        "at the end of the day",
        "dive deep into",
        "let's unpack",
        "game-changer",
        "paradigm shift",
        "synergy",
        "leverage",
        "holistic approach",
        "unlock your potential",
        "empower yourself",
        "journey of self-discovery",
        "transformative experience",
        "this is a must-read",
        "buckle up",
        "without further ado",
        "in this article",
        "as we all know",
        "it goes without saying",
        "needless to say",
        "the fact of the matter is",
        "when it comes to",
        "here's the thing",
        "in conclusion",
        "to sum up",
        "last but not least",
        "food for thought",
        "think outside the box",
        "take it to the next level",
        "revolutionary",
        "cutting-edge",
        "world-class",
    ]
    
    @staticmethod
    def check_slop(text: str) -> Tuple[float, List[str]]:
        """
        Check text against slop rubric per PRD §6.3.
        Returns (slop_score, list_of_found_phrases).
        Score 0 = no slop, 1 = maximum slop.
        """
        text_lower = text.lower()
        found = []
        
        for phrase in VoiceEngine.SLOP_PHRASES:
            if phrase in text_lower:
                found.append(phrase)
        
        # Score based on density of slop phrases
        word_count = len(text.split())
        if word_count == 0:
            return 0.0, []
        
        slop_score = min(1.0, len(found) * 0.25)  # Each phrase adds 0.25
        
        return round(slop_score, 2), found
    
    @staticmethod
    def check_structural_match(text: str, profile: dict) -> Tuple[float, dict]:
        """
        Check if generated text matches the brand's structural profile.
        Returns (match_score, details).
        """
        if not profile:
            return 1.0, {"note": "No structural profile available"}
        
        details = {}
        scores = []
        
        # Sentence length match
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if s.strip()]
        if sentences and profile.get("avg_sentence_length"):
            avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
            target = profile["avg_sentence_length"]
            diff = abs(avg_len - target) / max(target, 1)
            score = max(0, 1 - diff)
            scores.append(score)
            details["sentence_length"] = {"actual": round(avg_len, 1), "target": target, "score": round(score, 2)}
        
        # Emoji frequency match
        emoji_pattern = re.compile(
            "[\U0001F600-\U0001F64F\U0001F300-\U0001F5FF\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF]+",
            flags=re.UNICODE
        )
        emojis = emoji_pattern.findall(text)
        if profile.get("emoji_frequency") is not None:
            target = profile["emoji_frequency"]
            diff = abs(len(emojis) - target) / max(target, 1)
            score = max(0, 1 - diff * 0.5)
            scores.append(score)
            details["emoji_frequency"] = {"actual": len(emojis), "target": target, "score": round(score, 2)}
        
        # Hashtag count match
        hashtags = re.findall(r'#\w+', text)
        if profile.get("hashtag_count_avg") is not None:
            target = profile["hashtag_count_avg"]
            diff = abs(len(hashtags) - target) / max(target, 1)
            score = max(0, 1 - diff * 0.5)
            scores.append(score)
            details["hashtag_count"] = {"actual": len(hashtags), "target": target, "score": round(score, 2)}
        
        overall = sum(scores) / max(len(scores), 1) if scores else 1.0
        return round(overall, 2), details
    
    @staticmethod
    def full_guardrail_check(
        text: str,
        voice_centroid: Optional[List[float]],
        structural_profile: Optional[dict],
    ) -> dict:
        """
        Combined voice-drift + slop guardrail check (§6.3).
        Returns pass/fail with detailed reasons.
        """
        result = {
            "passed": True,
            "voice_similarity": None,
            "slop_score": None,
            "structural_match": None,
            "reasons": [],
        }
        
        # 1. Voice similarity check
        if voice_centroid:
            text_embedding = VoiceEngine.compute_embedding(text)
            similarity = VoiceEngine.cosine_similarity(text_embedding, voice_centroid)
            result["voice_similarity"] = round(similarity, 3)
            
            if similarity < settings.voice_similarity_threshold:
                result["passed"] = False
                result["reasons"].append(
                    f"Voice similarity ({similarity:.3f}) below threshold ({settings.voice_similarity_threshold}). "
                    "Draft sounds off-brand."
                )
        
        # 2. Slop rubric check
        slop_score, slop_phrases = VoiceEngine.check_slop(text)
        result["slop_score"] = slop_score
        if slop_score > 0.5:
            result["passed"] = False
            result["reasons"].append(
                f"High slop score ({slop_score}). Cliché phrases found: {', '.join(slop_phrases[:3])}"
            )
        
        # 3. Structural match check
        if structural_profile:
            match_score, match_details = VoiceEngine.check_structural_match(text, structural_profile)
            result["structural_match"] = {"score": match_score, "details": match_details}
            if match_score < 0.5:
                result["passed"] = False
                result["reasons"].append(
                    f"Structural mismatch ({match_score:.2f}). Draft doesn't match brand's writing patterns."
                )
        
        return result
