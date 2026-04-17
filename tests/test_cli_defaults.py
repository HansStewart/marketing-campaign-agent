import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from main import parse_args  # noqa: E402


def test_cli_defaults():
    args = parse_args()
    assert args.platform is not None
    assert isinstance(args.audience, str)
    assert isinstance(args.offer, str)