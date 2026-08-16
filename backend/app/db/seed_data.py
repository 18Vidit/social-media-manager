"""
Pulse — Seed Data
Realistic demo data for a fitness/wellness creator brand.
~20 sample posts, sample comments (various intents), engagement metrics.
"""

import uuid
import random
from datetime import datetime, timedelta, date

# Demo Brand: "FitVibe" — a fitness/wellness creator

DEMO_BRAND = {
    "id": "demo-brand-001",
    "name": "FitVibe",
    "handle": "@fitvibe.wellness",
    "platform": "instagram",
    "description": "Fitness & wellness creator sharing workout routines, nutrition tips, and mindful living. Audience: 25-34, primarily Delhi/Mumbai, 85K followers.",
    "weekly_post_limit": 5,
}

DEMO_GUIDELINES = [
    {
        "title": "Core Tone",
        "content": "Warm, encouraging, and real. Never preachy or condescending. Use 'you' and 'we' — talk WITH the audience, not AT them. Light humor is good. Avoid: corporate jargon, generic motivational quotes, anything that sounds like a fitness ad from 2015.",
        "category": "tone",
        "valid_from": "2026-01-01",
    },
    {
        "title": "Emoji Guidelines",
        "content": "Use 1-3 emojis per post, placed naturally within sentences (not dumped at the end). Favorites: 💪🔥✨🌿. Never: 🙏 (overused), 💯 (feels dated).",
        "category": "tone",
        "valid_from": "2026-01-01",
    },
    {
        "title": "Hashtag Strategy",
        "content": "3-5 hashtags max, placed at the very end after a line break. Mix of branded (#FitVibeFlow) and discovery (#MorningRoutine #WellnessJourney). Never more than 5 — it looks desperate.",
        "category": "tone",
        "valid_from": "2026-03-01",
    },
    {
        "title": "Topics to Avoid",
        "content": "No diet culture ('cheat meals', 'guilty pleasures', 'burning off' food). No before/after body transformations. No medical claims. No supplement endorsements without disclosure.",
        "category": "banned",
        "valid_from": "2026-01-01",
    },
    {
        "title": "Content Pillars",
        "content": "1. Workout routines (40%) — quick, equipment-optional, follow-along friendly. 2. Nutrition (25%) — simple meal ideas, not strict diets. 3. Mindfulness (20%) — morning routines, stress management, sleep. 4. Community stories (15%) — follower spotlights, Q&A.",
        "category": "topics",
        "valid_from": "2026-01-01",
    },
]

DEMO_POSTS = [
    {
        "content": "That 6am alarm hits different when you know you've got a 20-minute flow waiting ✨ No gym needed, just your mat and whatever energy you woke up with.\n\nToday's flow: sun salutations → warrior sequence → hip openers → 5 min savasana. Saved it to highlights if you want to follow along.\n\nWhat's your non-negotiable morning move? Drop it below 👇\n\n#MorningRoutine #FitVibeFlow #YogaAtHome",
        "post_type": "carousel",
        "likes": 3420, "comments_count": 187, "shares": 89, "saves": 456,
        "impressions": 28000, "reach": 22000,
        "posted_at": "2026-07-15T06:30:00",
    },
    {
        "content": "Real talk: I skipped my workout yesterday and made pasta at 11pm. And that's fine 🍝\n\nConsistency isn't about perfection — it's about showing up more days than you don't. If you're beating yourself up over one missed session, this is your sign to stop.\n\nYour body doesn't keep score the way your brain does.\n\n#WellnessJourney #FitVibeFlow #RealTalk",
        "post_type": "text",
        "likes": 5200, "comments_count": 342, "shares": 267, "saves": 890,
        "impressions": 45000, "reach": 38000,
        "posted_at": "2026-07-12T19:00:00",
    },
    {
        "content": "3 meals I actually eat on repeat (no, none of them are chicken and rice) 🌿\n\n1. Peanut butter banana smoothie bowl — 5 min, tastes like dessert\n2. Dal tadka with a mountain of rice — comfort food that also happens to be balanced\n3. Greek yogurt + granola + whatever fruit is in the fridge\n\nNothing fancy. Nothing that requires 47 ingredients. Just food that makes you feel good.\n\nSave this for your next 'what should I eat' spiral 💪\n\n#MealIdeas #FitVibeFlow #SimpleNutrition",
        "post_type": "carousel",
        "likes": 4100, "comments_count": 256, "shares": 178, "saves": 1200,
        "impressions": 38000, "reach": 31000,
        "posted_at": "2026-07-08T12:00:00",
    },
    {
        "content": "Your 10-minute no-equipment leg day 🔥\n\nSquats x 15\nLunges x 12 each\nGlute bridges x 15\nWall sit 30 sec\nCalf raises x 20\n\nRepeat 2x. That's it. Done before your coffee gets cold.\n\nTag someone who says they 'don't have time' 😏\n\n#LegDay #HomeWorkout #FitVibeFlow",
        "post_type": "reel",
        "likes": 6800, "comments_count": 410, "shares": 520, "saves": 1500,
        "impressions": 62000, "reach": 51000,
        "posted_at": "2026-07-05T07:00:00",
    },
    {
        "content": "Hot take: rest days are not lazy days. They're the days your muscles actually grow.\n\nIf your rest day guilt is louder than your body asking for a break, we need to talk about that.\n\nMy rest day: walk, stretch, maybe cook something slow, definitely do nothing productive on purpose.\n\nWhat's yours?\n\n#RestDay #FitVibeFlow #WellnessJourney",
        "post_type": "text",
        "likes": 4500, "comments_count": 298, "shares": 189, "saves": 670,
        "impressions": 35000, "reach": 29000,
        "posted_at": "2026-07-01T18:00:00",
    },
    {
        "content": "I tracked my sleep for 30 days. Here's what I learned 😴\n\nWeek 1: Averaging 5.5 hours. Felt like a zombie.\nWeek 2: No phone after 10pm. Jumped to 6.5 hours.\nWeek 3: Added magnesium + 10 min breathwork. Hit 7.5.\nWeek 4: 7-8 hours consistently. Workouts felt 2x easier.\n\nThe biggest cheat code in fitness isn't a supplement — it's sleep.\n\n#SleepBetter #FitVibeFlow #WellnessJourney",
        "post_type": "carousel",
        "likes": 5800, "comments_count": 367, "shares": 445, "saves": 1800,
        "impressions": 52000, "reach": 43000,
        "posted_at": "2026-06-28T20:00:00",
    },
    {
        "content": "Monday morning mobility 🌿 5 moves, 5 minutes, zero excuses.\n\n→ Cat-cow: 10 reps\n→ World's greatest stretch: 5 each side\n→ Shoulder circles: 15 each direction\n→ Deep squat hold: 30 sec\n→ Neck rolls: 10 each way\n\nYour future self thanks you for not skipping this.\n\n#MobilityWork #FitVibeFlow #MorningRoutine",
        "post_type": "reel",
        "likes": 3900, "comments_count": 145, "shares": 210, "saves": 980,
        "impressions": 33000, "reach": 27000,
        "posted_at": "2026-06-24T06:00:00",
    },
    {
        "content": "Community spotlight ✨ Meet @priya.runs — she started with zero running experience 6 months ago. Last weekend she finished her first 10K.\n\nHer advice: 'Stop comparing your chapter 1 to someone else's chapter 20. Just start.'\n\nIf that doesn't hit, I don't know what will 💪\n\nKnow someone crushing it quietly? Tag them. Let's celebrate.\n\n#FitVibeFamily #FitVibeFlow #RunningCommunity",
        "post_type": "text",
        "likes": 4800, "comments_count": 520, "shares": 310, "saves": 420,
        "impressions": 41000, "reach": 34000,
        "posted_at": "2026-06-20T17:00:00",
    },
    {
        "content": "POV: You replaced your afternoon coffee with a 10-minute walk and your energy actually improved 🚶‍♀️\n\nNot saying quit coffee (I would never). But that 3pm crash? Try a walk first. Sunlight + movement > another espresso for sustained energy.\n\nTried it? Tell me honestly 👇\n\n#AfternoonSlump #FitVibeFlow #WellnessHack",
        "post_type": "reel",
        "likes": 3200, "comments_count": 198, "shares": 156, "saves": 780,
        "impressions": 29000, "reach": 24000,
        "posted_at": "2026-06-17T15:00:00",
    },
    {
        "content": "The stretch nobody does but everybody needs: hip flexor stretch 🔥\n\nIf you sit for more than 4 hours a day (guilty 🙋‍♀️), your hip flexors are probably tighter than your deadline schedule.\n\nHold each side for 60 seconds. Do it twice a day. Thank me in a week.\n\nSwipe for the full sequence →\n\n#HipFlexor #DeskWorker #FitVibeFlow #MobilityWork",
        "post_type": "carousel",
        "likes": 4600, "comments_count": 234, "shares": 189, "saves": 1100,
        "impressions": 36000, "reach": 30000,
        "posted_at": "2026-06-14T12:30:00",
    },
    {
        "content": "Unpopular opinion: you don't need a gym membership to be fit. You need consistency and a floor.\n\nEvery workout I post can be done in your living room. That's intentional.\n\nBecause the best workout is the one you actually do. Not the one that requires a 30-minute commute.\n\n#HomeWorkout #FitVibeFlow #NoExcuses",
        "post_type": "text",
        "likes": 5100, "comments_count": 380, "shares": 290, "saves": 650,
        "impressions": 42000, "reach": 35000,
        "posted_at": "2026-06-10T19:00:00",
    },
    {
        "content": "Quick hydration check ✨ Because you've probably scrolled for 20 minutes and haven't had water.\n\nGo. Drink. Come back.\n\nNow here's your reminder: 2-3 liters a day, more if you're training. Your skin, energy, and digestion will thank you.\n\nDrop a 💧 when you've had your glass.\n\n#HydrationCheck #FitVibeFlow #WellnessJourney",
        "post_type": "text",
        "likes": 3800, "comments_count": 890, "shares": 120, "saves": 340,
        "impressions": 31000, "reach": 26000,
        "posted_at": "2026-06-07T14:00:00",
    },
    {
        "content": "Your complete upper body workout — dumbbells only 💪\n\nShoulder press: 3x12\nBent-over rows: 3x12\nBicep curls: 3x15\nTricep dips: 3x12\nPush-ups: 3x failure\n\nRest 60 sec between sets. Total time: ~25 min.\n\nPair with yesterday's leg day for a solid week. Save this for later 🔥\n\n#UpperBody #DumbbellWorkout #FitVibeFlow",
        "post_type": "carousel",
        "likes": 5400, "comments_count": 267, "shares": 340, "saves": 1400,
        "impressions": 44000, "reach": 37000,
        "posted_at": "2026-06-03T07:30:00",
    },
    {
        "content": "I used to think 'wellness' meant green juice and 5am runs.\n\nNow I know wellness is also:\n→ Saying no to plans when you're tired\n→ Not checking your phone for the first hour\n→ Eating the cake at the birthday party\n→ Going to therapy\n→ Sleeping 8 hours without guilt\n\nWellness isn't aesthetic. It's whatever keeps you sane.\n\n#WellnessRedefined #FitVibeFlow #MentalHealth",
        "post_type": "text",
        "likes": 7200, "comments_count": 560, "shares": 680, "saves": 2100,
        "impressions": 68000, "reach": 55000,
        "posted_at": "2026-05-30T18:30:00",
    },
    {
        "content": "Breathwork changed my life and I'm not even being dramatic 🌿\n\n4-7-8 technique:\n• Inhale for 4 seconds\n• Hold for 7 seconds\n• Exhale for 8 seconds\n\nDo 4 rounds before bed. That's it. Free. No app needed.\n\nI went from 45 min to fall asleep → 10 min. Consistently.\n\n#Breathwork #SleepBetter #FitVibeFlow #WellnessJourney",
        "post_type": "reel",
        "likes": 4900, "comments_count": 312, "shares": 390, "saves": 1650,
        "impressions": 47000, "reach": 39000,
        "posted_at": "2026-05-26T21:00:00",
    },
    {
        "content": "Your weekly workout split if you only have 4 days:\n\nMonday: Upper body (push)\nWednesday: Lower body\nFriday: Upper body (pull)\nSunday: Full body + mobility\n\nTues/Thurs/Sat: Walk, stretch, live your life.\n\nMore isn't always better. Smarter > harder.\n\n#WorkoutSplit #FitVibeFlow #TrainSmart",
        "post_type": "carousel",
        "likes": 4300, "comments_count": 210, "shares": 270, "saves": 1300,
        "impressions": 37000, "reach": 31000,
        "posted_at": "2026-05-22T08:00:00",
    },
    {
        "content": "Asked my DMs: 'What's the one thing stopping you from being consistent?'\n\nTop 3 answers:\n1. 'I don't have time' → You have 10 min. I'll prove it.\n2. 'I don't know what to do' → Follow along with my saved routines.\n3. 'I lose motivation after a week' → Motivation is a myth. Build systems instead.\n\nWhich one is yours? Be honest 👇\n\n#ConsistencyTips #FitVibeFlow #WellnessJourney",
        "post_type": "text",
        "likes": 5600, "comments_count": 478, "shares": 230, "saves": 890,
        "impressions": 46000, "reach": 38000,
        "posted_at": "2026-05-18T17:30:00",
    },
    {
        "content": "Protein doesn't have to be boring or expensive.\n\nMy go-to affordable protein sources:\n🥚 Eggs — ₹7/egg, 6g protein each\n🫘 Rajma/Chole — ₹40/can, 15g per cup\n🥛 Paneer — ₹80/200g, 36g protein\n🌰 Peanuts — ₹60/250g, 26g per 100g\n🍶 Curd — ₹30/400g, 11g per cup\n\nYou don't need fancy supplements. Real food works.\n\n#ProteinSources #BudgetNutrition #FitVibeFlow",
        "post_type": "carousel",
        "likes": 6100, "comments_count": 340, "shares": 450, "saves": 2200,
        "impressions": 55000, "reach": 46000,
        "posted_at": "2026-05-14T12:00:00",
    },
    {
        "content": "Just finished a live Q&A and here are the 3 questions that came up the most:\n\n1. 'Should I do cardio or weights?' → Both. But if forced to pick one, weights build more lasting change.\n2. 'How much protein do I actually need?' → 1.6-2g per kg of body weight. Don't overthink it.\n3. 'What's the best time to work out?' → Whenever you'll actually do it. That's the best time.\n\nFull live is saved in highlights 🔥\n\n#FitnessQA #FitVibeFlow #AskMe",
        "post_type": "text",
        "likes": 3600, "comments_count": 290, "shares": 120, "saves": 560,
        "impressions": 30000, "reach": 25000,
        "posted_at": "2026-05-10T20:00:00",
    },
    {
        "content": "Morning routine that actually sticks (tested for 90 days) ☀️\n\n6:00 — Wake up, no phone for 30 min\n6:05 — 5 min stretch (yesterday's mobility reel)\n6:10 — Glass of water + lemon\n6:15 — 20 min workout OR walk\n6:35 — Cold shower (optional but powerful)\n6:45 — Breakfast + journal 3 things you're grateful for\n\nThe secret? Start with just ONE of these. Add one more each week.\n\n#MorningRoutine #FitVibeFlow #HabitBuilding",
        "post_type": "carousel",
        "likes": 5900, "comments_count": 445, "shares": 510, "saves": 2400,
        "impressions": 58000, "reach": 48000,
        "posted_at": "2026-05-06T06:00:00",
    },
]

# Sample Comments (various intents for triage demo)

DEMO_COMMENTS = [
    # FAQ — high confidence, low risk → auto-reply eligible
    {"content": "What time do you usually post your workouts?", "author": "fitness_fan_22", "intent": "faq", "sentiment": 0.1},
    {"content": "Do you have a beginner version of this routine?", "author": "newbie.starts", "intent": "faq", "sentiment": 0.2},
    {"content": "How many calories does this burn approximately?", "author": "track.everything", "intent": "faq", "sentiment": 0.0},
    {"content": "Can I do this with a knee injury?", "author": "careful_runner", "intent": "faq", "sentiment": -0.1},
    {"content": "What brand of yoga mat do you use?", "author": "mat.matters", "intent": "faq", "sentiment": 0.3},
    
    # Positive engagement — low confidence, low risk → log
    {"content": "This is exactly what I needed today 🔥🔥🔥", "author": "daily_mover", "intent": "positive", "sentiment": 0.9},
    {"content": "Queen! Been following your routines for 3 months and I can see actual changes", "author": "transformation.real", "intent": "positive", "sentiment": 0.95},
    {"content": "Love this ❤️", "author": "quick.liker", "intent": "positive", "sentiment": 0.8},
    {"content": "Sharing this with my gym buddy right now", "author": "gym.bro.101", "intent": "positive", "sentiment": 0.85},
    {"content": "Your content is the most genuine fitness content on Instagram period.", "author": "honest_review", "intent": "positive", "sentiment": 0.92},
    
    # Collaboration/Brand — high confidence, high risk → human review
    {"content": "Hey! I'm from @fitgear.india — would love to discuss a collaboration. Can we DM?", "author": "fitgear.india", "intent": "collaboration", "sentiment": 0.5, "is_verified": True},
    {"content": "We'd love to send you our new protein powder line for review. Interested?", "author": "proteinplus.co", "intent": "collaboration", "sentiment": 0.4},
    {"content": "Hi, I'm a journalist at HealthToday magazine. Working on a piece about fitness creators. Would you be open to a quick interview?", "author": "sarah.healthtoday", "intent": "press", "sentiment": 0.3, "is_verified": True},
    
    # Complaints — low confidence, high risk → escalate
    {"content": "I tried your routine and hurt my back. Not cool posting exercises without proper form warnings.", "author": "injured_follower", "intent": "complaint", "sentiment": -0.8},
    {"content": "This is irresponsible. You're not a certified trainer, stop giving advice.", "author": "angry_expert", "intent": "complaint", "sentiment": -0.9},
    {"content": "Your protein recommendations are way too high for women. Do some research.", "author": "nutrition_skeptic", "intent": "complaint", "sentiment": -0.7},
    
    # Spam
    {"content": "🔥🔥 Check my page for FREE FOLLOWERS 🔥🔥 link in bio!!", "author": "free.follows.2026", "intent": "spam", "sentiment": 0.0},
    {"content": "I made $5000 working from home!! DM me for details 💰💰", "author": "scam.alert.999", "intent": "spam", "sentiment": 0.0},
    
    # Neutral — low confidence, low risk → log
    {"content": "hmm", "author": "vague.person", "intent": "neutral", "sentiment": 0.0},
    {"content": "👍", "author": "thumbs.upper", "intent": "neutral", "sentiment": 0.3},
]


def generate_engagement_metrics():
    """Generate realistic hourly engagement data for peak-time prediction."""
    metrics = []
    
    # Delhi/Mumbai audience — peak engagement patterns:
    # Morning: 6-9 AM (pre-work)
    # Lunch: 12-2 PM
    # Evening: 6-9 PM (highest)
    # Night: 9-11 PM (declining)
    
    hour_weights = {
        0: 0.05, 1: 0.02, 2: 0.01, 3: 0.01, 4: 0.02, 5: 0.05,
        6: 0.35, 7: 0.55, 8: 0.65, 9: 0.45,
        10: 0.25, 11: 0.30,
        12: 0.60, 13: 0.55, 14: 0.35,
        15: 0.25, 16: 0.20, 17: 0.35,
        18: 0.70, 19: 0.85, 20: 0.90, 21: 0.75,
        22: 0.45, 23: 0.20,
    }
    
    day_weights = {
        0: 0.85,  # Monday
        1: 0.80,  # Tuesday
        2: 0.75,  # Wednesday
        3: 0.80,  # Thursday
        4: 0.90,  # Friday
        5: 1.00,  # Saturday
        6: 0.95,  # Sunday
    }
    
    for day in range(7):
        for hour in range(24):
            base_score = hour_weights[hour] * day_weights[day]
            noise = random.uniform(-0.05, 0.05)
            score = max(0, min(1, base_score + noise))
            
            metrics.append({
                "hour_of_day": hour,
                "day_of_week": day,
                "engagement_score": round(score, 3),
            })
    
    return metrics


ENGAGEMENT_HEATMAP = generate_engagement_metrics()
