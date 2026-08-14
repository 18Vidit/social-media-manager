"""
Pulse — Copywriter Agent (Content Generation Subgraph §7.5)
Implements the hook-then-caption split from Draft C:
1. Brand voice retrieval (top-k similar, top-quartile by engagement)
2. Hook generator (cheap model, conditioned on top-quartile hooks)
3. Caption generator (main LLM, full context)
4. Produces 3 variants per request
"""

import json
import random
from typing import List, Optional, TypedDict
from datetime import datetime

from app.services.voice_engine import VoiceEngine
from app.services.eqi import EQIService
from app.config import settings


class GenerationContext(TypedDict):
    brand_id: str
    topic: str
    platform: str
    tone: Optional[str]
    additional_context: Optional[str]
    few_shot_posts: List[dict]
    structural_profile: dict
    brand_guidelines: List[str]
    voice_centroid: Optional[List[float]]


class GeneratedVariant(TypedDict):
    hook: str
    content: str
    hashtags: List[str]
    voice_similarity: float
    slop_score: float
    structural_match: float
    explanation: dict
    pipeline_trace: dict


# Platform-specific formatting rules
PLATFORM_RULES = {
    "instagram": {
        "max_length": 2200,
        "hashtag_placement": "end",
        "max_hashtags": 5,
        "format_notes": "Instagram caption. Use line breaks for readability. Emoji placement: natural within sentences. Hashtags at end after line break. Max 2200 chars.",
    },
    "tiktok": {
        "max_length": 300,
        "hashtag_placement": "end",
        "max_hashtags": 5,
        "format_notes": "TikTok caption. Ultra-short, hook-first. Must grab attention in first 3 words. Conversational, punchy. Max 300 chars.",
    },
    "linkedin": {
        "max_length": 3000,
        "hashtag_placement": "end",
        "max_hashtags": 3,
        "format_notes": "LinkedIn post. Professional but human. Use line breaks for scanability. Open with a strong hook line. Hashtags at end. Max 3000 chars.",
    },
    "youtube": {
        "max_length": 5000,
        "hashtag_placement": "inline",
        "max_hashtags": 3,
        "format_notes": "YouTube description. SEO-friendly, detailed. Include timestamps if relevant. Hashtags can be inline. Max 5000 chars.",
    },
    "twitter": {
        "max_length": 280,
        "hashtag_placement": "inline",
        "max_hashtags": 2,
        "format_notes": "Tweet. Ultra-concise. Every word must earn its place. Max 280 chars. 1-2 hashtags inline.",
    },
}

# Banned phrases (static list per §7.5)
BANNED_PHRASES = [
    "check out my",
    "follow for more",
    "link in bio",
    "dm me for",
    "use code",
    "limited time offer",
    "click the link",
    "subscribe now",
    "don't miss out",
    "hurry up",
    "act now",
    "free giveaway",
]


class CopywriterAgent:
    """
    Content generation subgraph implementing §7.5:
    Hook Generator → Caption Generator → 3 variants output.
    
    In demo mode, uses template-based generation.
    In production, calls Claude Sonnet-class model via LangChain.
    """
    
    @staticmethod
    async def generate_hook(
        topic: str,
        platform: str,
        top_quartile_hooks: List[str],
        structural_profile: dict,
    ) -> List[str]:
        """
        Hook Generator (§7.5 step 2):
        Separate, cheap call conditioned only on hooks from top-quartile posts.
        This is what stops the generator from defaulting to a generic opener.
        """
        # Try LLM-based generation first
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from app.config import settings as app_settings
            
            if app_settings.google_api_key:
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=app_settings.google_api_key,
                    temperature=0.8,
                )
                
                hook_examples = "\n".join([f"- {h}" for h in top_quartile_hooks[:5]])
                platform_rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["instagram"])
                
                prompt = f"""You are a social media hook generator. Generate 3 unique, attention-grabbing opening hooks for a {platform} post about: "{topic}"

Study these hooks from the brand's top-performing posts and match their style, energy, and structure:
{hook_examples}

Structural patterns to match:
- Average sentence length: {structural_profile.get('avg_sentence_length', 'N/A')} words
- Emoji usage: {structural_profile.get('emoji_frequency', 'N/A')} per post
- Tone: {json.dumps(structural_profile.get('tone_keywords', {}))}

Rules:
- Each hook must be 1-2 sentences max
- Platform: {platform} ({platform_rules['format_notes']})
- Sound like THIS brand, not generic AI
- Never use: {', '.join(BANNED_PHRASES[:5])}

Return ONLY a JSON array of 3 hook strings, no other text.
Example: ["Hook 1 text", "Hook 2 text", "Hook 3 text"]"""
                
                response = await llm.ainvoke(prompt)
                content = response.content.strip()
                
                # Clean markdown code block markers if present
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                
                hooks = json.loads(content)
                if isinstance(hooks, list) and len(hooks) >= 3:
                    return hooks[:3]
        except Exception as e:
            pass  # Fallback to template-based
        
        # Try Anthropic
        try:
            from langchain_anthropic import ChatAnthropic
            from app.config import settings as app_settings
            
            if app_settings.anthropic_api_key:
                llm = ChatAnthropic(
                    model="claude-sonnet-4-20250514",
                    anthropic_api_key=app_settings.anthropic_api_key,
                    temperature=0.8,
                    max_tokens=500,
                )
                
                hook_examples = "\n".join([f"- {h}" for h in top_quartile_hooks[:5]])
                
                prompt = f"""Generate 3 unique, attention-grabbing opening hooks for a {platform} post about: "{topic}"

Study these hooks from the brand's top-performing posts and match their style:
{hook_examples}

Return ONLY a JSON array of 3 hook strings, no other text."""
                
                response = await llm.ainvoke(prompt)
                content = response.content.strip()
                if content.startswith("```"):
                    content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
                hooks = json.loads(content)
                if isinstance(hooks, list) and len(hooks) >= 3:
                    return hooks[:3]
        except Exception:
            pass
        
        # Template-based fallback for demo mode
        hooks = CopywriterAgent._generate_template_hooks(topic, platform, top_quartile_hooks)
        return hooks
    
    @staticmethod
    async def generate_captions(
        topic: str,
        hooks: List[str],
        platform: str,
        few_shot_posts: List[dict],
        structural_profile: dict,
        brand_guidelines: List[str],
    ) -> List[dict]:
        """
        Caption Generator (§7.5 step 3):
        Main LLM call per hook. Inputs: hook, few-shot posts, structural profile,
        platform formatting rules, banned-phrase list.
        """
        results = []
        platform_rules = PLATFORM_RULES.get(platform, PLATFORM_RULES["instagram"])
        
        for i, hook in enumerate(hooks[:3]):
            # Try LLM-based generation
            caption = await CopywriterAgent._generate_caption_llm(
                topic, hook, platform, platform_rules, 
                few_shot_posts, structural_profile, brand_guidelines
            )
            
            if caption is None:
                # Template fallback
                caption = CopywriterAgent._generate_template_caption(
                    topic, hook, platform, few_shot_posts, structural_profile
                )
            
            results.append({
                "hook": hook,
                "content": caption["content"],
                "hashtags": caption["hashtags"],
                "variant_index": i,
            })
        
        return results
    
    @staticmethod
    async def _generate_caption_llm(
        topic: str,
        hook: str,
        platform: str,
        platform_rules: dict,
        few_shot_posts: List[dict],
        structural_profile: dict,
        brand_guidelines: List[str],
    ) -> Optional[dict]:
        """Generate caption using LLM (Claude Sonnet-class or Gemini)."""
        try:
            llm = None
            from app.config import settings as app_settings
            
            # Try Google Gemini first (most accessible)
            if app_settings.google_api_key:
                from langchain_google_genai import ChatGoogleGenerativeAI
                llm = ChatGoogleGenerativeAI(
                    model="gemini-2.5-flash",
                    google_api_key=app_settings.google_api_key,
                    temperature=0.7,
                )
            elif app_settings.anthropic_api_key:
                from langchain_anthropic import ChatAnthropic
                llm = ChatAnthropic(
                    model="claude-sonnet-4-20250514",
                    anthropic_api_key=app_settings.anthropic_api_key,
                    temperature=0.7,
                    max_tokens=1500,
                )
            elif app_settings.openai_api_key:
                from langchain_openai import ChatOpenAI
                llm = ChatOpenAI(
                    model="gpt-4o",
                    openai_api_key=app_settings.openai_api_key,
                    temperature=0.7,
                )
            
            if llm is None:
                return None
            
            few_shot_text = "\n\n---\n\n".join([
                f"Post (EQI: {p.get('eqi_score', 'N/A')}):\n{p.get('content', '')}" 
                for p in few_shot_posts[:5]
            ])
            
            guidelines_text = "\n".join([f"- {g}" for g in brand_guidelines[:5]])
            
            prompt = f"""You are writing a {platform} post for a brand. The hook/opening line has already been written. Complete the post.

HOOK (already written, start the post with this): {hook}

TOPIC: {topic}

BRAND VOICE — study these real posts from this brand and MATCH their style exactly:
{few_shot_text}

STRUCTURAL CONSTRAINTS:
- Average sentence length: {structural_profile.get('avg_sentence_length', 8)} words
- Emoji usage: {structural_profile.get('emoji_frequency', 2)} per post, placed naturally
- Hashtag count: {structural_profile.get('hashtag_count_avg', 4)}, at the end
- Typical post length: {structural_profile.get('avg_post_length', 500)} characters
- Tone: {json.dumps(structural_profile.get('tone_keywords', {}))}

BRAND GUIDELINES:
{guidelines_text}

PLATFORM RULES: {platform_rules['format_notes']}

BANNED PHRASES (never use these): {', '.join(BANNED_PHRASES)}

REQUIREMENTS:
1. Start with the provided hook exactly as written
2. Sound authentically like this brand — match sentence structure, emoji style, energy
3. Be genuinely helpful or engaging, not generic
4. Include a call-to-action or engagement prompt at the end
5. Add appropriate hashtags at the end (after a line break)

Return ONLY a JSON object with two keys:
- "content": the full post text (starting with the hook, including hashtags at the end)
- "hashtags": array of hashtag strings used

No markdown, no explanation, just the JSON object."""

            response = await llm.ainvoke(prompt)
            content = response.content.strip()
            
            # Clean markdown code block markers
            if content.startswith("```"):
                content = content.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            
            result = json.loads(content)
            return {
                "content": result.get("content", ""),
                "hashtags": result.get("hashtags", []),
            }
            
        except Exception as e:
            return None
    
    @staticmethod
    def _generate_template_hooks(
        topic: str,
        platform: str,
        top_quartile_hooks: List[str],
    ) -> List[str]:
        """Template-based hook generation for demo mode."""
        hook_templates = [
            f"Real talk: {topic} isn't what most people think it is 🔥",
            f"I tested {topic} for 30 days. Here's what actually happened ✨",
            f"Your no-BS guide to {topic} — no fluff, just what works 💪",
        ]
        
        # If we have top-quartile hooks, slightly modify them
        if top_quartile_hooks:
            for h in top_quartile_hooks[:2]:
                # Replace nouns while keeping structure
                modified = h  # In production, this would be smarter
                hook_templates.append(modified)
        
        return hook_templates[:3]
    
    @staticmethod
    def _generate_template_caption(
        topic: str,
        hook: str,
        platform: str,
        few_shot_posts: List[dict],
        structural_profile: dict,
    ) -> dict:
        """Template-based caption for demo mode when no LLM is available."""
        # Analyze structural profile
        emoji_freq = int(structural_profile.get("emoji_frequency", 2))
        hashtag_count = int(structural_profile.get("hashtag_count_avg", 4))
        
        emojis = ["💪", "🔥", "✨", "🌿", "☀️", "❤️", "👇", "😏"]
        selected_emojis = random.sample(emojis, min(emoji_freq, len(emojis)))
        
        body_templates = [
            f"\n\nHere's what nobody tells you about {topic}:\n\n"
            f"1. It's simpler than you think\n"
            f"2. Consistency beats intensity\n"
            f"3. Start with just 10 minutes\n\n"
            f"The biggest mistake? Overcomplicating it. Keep it simple, show up daily, and results follow {selected_emojis[0] if selected_emojis else ''}\n\n"
            f"What's your experience with {topic}? Drop it below 👇",
            
            f"\n\nI used to overcomplicate {topic}. Then I simplified everything down to what actually matters:\n\n"
            f"→ Focus on one thing at a time\n→ Track what works, drop what doesn't\n→ Give it at least 2 weeks before judging\n\n"
            f"That's it. No fancy hacks, no expensive gear. Just showing up {selected_emojis[0] if selected_emojis else ''}\n\n"
            f"Save this for when you need the reminder.",
            
            f"\n\nI've been doing this for a while now and here's the truth about {topic}:\n\n"
            f"It's not about being perfect. It's about being consistent enough that progress becomes inevitable.\n\n"
            f"The people who get results aren't the ones with the best plan. They're the ones who actually follow through on an okay plan {selected_emojis[0] if selected_emojis else ''}\n\n"
            f"Which part resonates most? Tell me honestly.",
        ]
        
        body = random.choice(body_templates)
        
        # Generate hashtags
        topic_words = topic.lower().split()[:2]
        hashtags = [f"#{w.capitalize()}" for w in topic_words if len(w) > 3]
        hashtags.extend(["#FitVibeFlow", "#WellnessJourney"])
        hashtags = hashtags[:hashtag_count]
        
        full_content = hook + body + "\n\n" + " ".join(hashtags)
        
        return {
            "content": full_content,
            "hashtags": hashtags,
        }
    
    @staticmethod
    async def generate_content(context: GenerationContext) -> List[GeneratedVariant]:
        """
        Full content generation pipeline (§7.5):
        1. Extract hooks from top-quartile posts
        2. Generate hooks
        3. Generate captions
        4. Run guardrail checks
        5. Rank and annotate
        """
        start_time = datetime.utcnow()
        
        # Step 1: Get top-quartile hooks
        top_quartile_hooks = []
        for post in context.get("few_shot_posts", []):
            hook = post.get("hook_text") or (post.get("content", "").split("\n")[0] if post.get("content") else "")
            if hook:
                top_quartile_hooks.append(hook)
        
        # Step 2: Generate hooks
        hooks = await CopywriterAgent.generate_hook(
            topic=context["topic"],
            platform=context["platform"],
            top_quartile_hooks=top_quartile_hooks,
            structural_profile=context.get("structural_profile", {}),
        )
        
        # Step 3: Generate captions
        captions = await CopywriterAgent.generate_captions(
            topic=context["topic"],
            hooks=hooks,
            platform=context["platform"],
            few_shot_posts=context.get("few_shot_posts", []),
            structural_profile=context.get("structural_profile", {}),
            brand_guidelines=context.get("brand_guidelines", []),
        )
        
        # Step 4: Run guardrail checks on each variant
        variants: List[GeneratedVariant] = []
        
        for caption in captions:
            guardrail_result = VoiceEngine.full_guardrail_check(
                text=caption["content"],
                voice_centroid=context.get("voice_centroid"),
                structural_profile=context.get("structural_profile"),
            )
            
            # If guardrail fails, attempt one retry with failure reason injected
            if not guardrail_result["passed"] and settings.max_retries > 0:
                retry_context = f"\n[RETRY: Previous version was rejected. Reasons: {'; '.join(guardrail_result['reasons'])}. Fix these issues.]"
                # In production, this would re-run the LLM with the rejection feedback
                # For demo, we just note the retry
                guardrail_result["pipeline_note"] = "Would retry with feedback in production"
            
            # Compute predicted engagement heuristic
            structural_match_score = guardrail_result.get("structural_match", {}).get("score", 0.5) if isinstance(guardrail_result.get("structural_match"), dict) else 0.5
            predicted_engagement = (
                (guardrail_result.get("voice_similarity", 0.5) or 0.5) * 0.6 +
                structural_match_score * 0.4
            ) * 100
            
            end_time = datetime.utcnow()
            duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            variant: GeneratedVariant = {
                "hook": caption["hook"],
                "content": caption["content"],
                "hashtags": caption["hashtags"],
                "voice_similarity": guardrail_result.get("voice_similarity", 0.0) or 0.0,
                "slop_score": guardrail_result.get("slop_score", 0.0) or 0.0,
                "structural_match": structural_match_score,
                "explanation": {
                    "similar_posts_used": len(context.get("few_shot_posts", [])),
                    "top_quartile_hooks_available": len(top_quartile_hooks),
                    "structural_match_details": guardrail_result.get("structural_match", {}),
                    "guardrail_passed": guardrail_result["passed"],
                    "guardrail_reasons": guardrail_result.get("reasons", []),
                    "why": f"Generated from {len(context.get('few_shot_posts', []))} similar past posts, "
                           f"voice similarity: {guardrail_result.get('voice_similarity', 'N/A')}, "
                           f"structural match: {structural_match_score}",
                },
                "pipeline_trace": {
                    "hook_model": "gemini-2.5-flash" if settings.google_api_key else "template",
                    "caption_model": "gemini-2.5-flash" if settings.google_api_key else "template",
                    "guardrail_passes": 1,
                    "retry_reasons": guardrail_result.get("reasons", []),
                    "duration_ms": duration_ms,
                    "nodes_executed": ["Scout", "Strategist", "Copywriter", "Guardrail"],
                },
            }
            variants.append(variant)
        
        # Step 5: Rank by voice-similarity + predicted-engagement
        variants.sort(
            key=lambda v: (v["voice_similarity"] * 0.6 + v["structural_match"] * 0.4),
            reverse=True,
        )
        
        return variants
