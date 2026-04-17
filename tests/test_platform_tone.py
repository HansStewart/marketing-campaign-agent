import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from config import PLATFORM_TONE_MAP, SUPPORTED_PLATFORMS  # noqa: E402


def test_platform_tone_map_covers_supported_platforms():
    for platform in SUPPORTED_PLATFORMS:
        assert platform in PLATFORM_TONE_MAP
        assert isinstance(PLATFORM_TONE_MAP[platform], str)
        assert PLATFORM_TONE_MAP[platform]