"""Intent scoring smoke test."""
from pathlib import Path
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agent.treys_agent import _infer_intent, _score_intent, _MAIL_KEYWORDS, _MAIL_PHRASES

pytestmark = pytest.mark.integration


def run_intent_demo() -> tuple[str, float, str]:
    text = "Can you help me organize the folders in my yahoo mail?"
    mail_score = _score_intent(text, _MAIL_KEYWORDS, _MAIL_PHRASES)
    intent = _infer_intent(text)
    print(f"Text: {text}")
    print(f"Mail score: {mail_score}")
    print(f"Intent: {intent}")
    return text, mail_score, intent


def test_intent_demo():
    _text, mail_score, intent = run_intent_demo()
    assert intent
    assert isinstance(mail_score, (int, float))


if __name__ == "__main__":
    run_intent_demo()
