# config.py

# LLM settings
MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0.7

# Agent defaults
DEFAULT_MAX_REVISIONS = 4
DEFAULT_PLATFORM = "LinkedIn"
DEFAULT_LOCATION = "Dallas, Texas"

# Supported platforms
SUPPORTED_PLATFORMS = ["LinkedIn", "Instagram", "Facebook", "Email"]

# Platform-specific tone guidance
PLATFORM_TONE_MAP = {
    "LinkedIn": "Professional, modern, confident, conversion-focused",
    "Instagram": "Conversational, visual, punchy, benefit-driven",
    "Facebook": "Friendly, community-oriented, direct, trust-building",
    "Email": "Direct, personal, value-first, clear CTA",
}

# Platform-specific style instructions
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
- Make it feel visual and punchy
- Focus on pain point + transformation
- Can use 1 to 3 relevant hashtags at the end
- No more than 1 emoji total
- Keep it concise
""",
    "Facebook": """
Write like a Facebook post for local business owners.
- Conversational and approachable
- Slightly more explanatory than Instagram
- Focus on trust and relatable business pain points
- 2 to 3 short paragraphs
- Optional soft CTA at the end
- No emojis unless highly relevant
""",
    "Email": """
Write like a short outbound marketing email.
- Clear subject-style opening energy in the first line
- Direct, personal, low-friction language
- Keep body under 150 words
- One clear CTA
- No hashtags
- No emojis
""",
}