# config.py

# LLM settings
MODEL_NAME = "gpt-4o-mini"
MODEL_TEMPERATURE = 0.7

# Agent defaults
DEFAULT_MAX_REVISIONS = 4
DEFAULT_PLATFORM = "LinkedIn"
DEFAULT_LOCATION = "Dallas, Texas"

# Supported platforms for the campaign agent
SUPPORTED_PLATFORMS = ["LinkedIn", "Instagram", "Facebook", "Email"]

# Platform-specific tone guidance
PLATFORM_TONE_MAP = {
    "LinkedIn": "Professional, modern, confident, conversion-focused",
    "Instagram": "Conversational, visual, punchy, benefit-driven",
    "Facebook": "Friendly, community-oriented, direct, trust-building",
    "Email": "Direct, personal, value-first, clear CTA",
}