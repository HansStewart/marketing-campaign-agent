# config.py

MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0.7

DEFAULT_MAX_REVISIONS = 4
DEFAULT_PLATFORM = "LinkedIn"
DEFAULT_LOCATION = "United States"

SUPPORTED_PLATFORMS = [
    "LinkedIn", "Instagram", "Facebook", "Email",
    "SMS", "Google Ad", "Cold DM", "Twitter/X", "YouTube", "TikTok"
]

PLATFORM_TONE_MAP = {
    "LinkedIn": "Professional, modern, confident, conversion-focused",
    "Instagram": "Conversational, visual, punchy, benefit-driven",
    "Facebook": "Friendly, community-oriented, direct, trust-building",
    "Email": "Direct, personal, value-first, clear CTA",
    "SMS": "Ultra-concise, direct, action-oriented",
    "Google Ad": "Benefit-led, keyword-aware, clear CTA",
    "Cold DM": "Personal, low-friction, curiosity-driven",
    "Twitter/X": "Punchy, opinionated, concise",
    "YouTube": "Engaging, story-driven, value-first",
    "TikTok": "Casual, trend-aware, hook-heavy",
}

PLATFORM_STYLE_MAP = {
    "LinkedIn": """
Write like a polished B2B LinkedIn post.
- 1 short hook line at the top
- 1 to 2 short paragraphs
- Professional, credible tone
- Emphasize business outcomes and efficiency
- No hashtags
- No emojis
- Clear CTA at the end
""",
    "Instagram": """
Write like an Instagram caption for business owners.
- Start with a short, scroll-stopping hook
- Use short lines for readability
- Punchy and visual
- Focus on pain point and transformation
- 1 to 3 relevant hashtags at the end
- No more than 1 emoji total
- Keep it concise
""",
    "Facebook": """
Write like a Facebook post for business owners.
- Conversational and approachable
- Slightly more explanatory than Instagram
- Focus on trust and relatable business pain points
- 2 to 3 short paragraphs
- Optional soft CTA at the end
- No emojis unless highly relevant
""",
    "Email": """
Write like a short outbound marketing email.
- Clear subject-style opening in the first line
- Direct, personal, low-friction language
- Keep body under 150 words
- One clear CTA
- No hashtags
- No emojis
""",
    "SMS": """
Write like a marketing SMS message.
- Under 160 characters
- Lead with value immediately
- One clear CTA
- No emojis
""",
    "Google Ad": """
Write like a Google Search ad.
- Headline under 30 characters
- Description under 90 characters
- Lead with the primary benefit
- Include a clear CTA
""",
    "Cold DM": """
Write like a cold direct message on social media.
- 3 to 5 sentences maximum
- Open with a specific relevant observation
- No generic compliments
- One soft CTA at the end
- Conversational, not salesy
""",
    "Twitter/X": """
Write like a tweet.
- Under 280 characters
- Hook in the first line
- Punchy and opinionated
- Optional CTA at end
""",
    "YouTube": """
Write like a YouTube video description or script hook.
- Start with a strong hook question or statement
- Value-first, educational tone
- Clear CTA at the end
""",
    "TikTok": """
Write like a TikTok video script hook.
- First line must stop the scroll
- Casual, energetic tone
- Short punchy sentences
- CTA at the very end
""",
}