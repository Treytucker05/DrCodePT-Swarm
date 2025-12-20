from __future__ import annotations

from agent.modes.execute import find_matching_playbook


def _playbooks() -> dict:
    return {
        "yahoo-clean-spam": {
            "name": "Clean Yahoo Spam",
            "description": "Log into Yahoo Mail and empty the spam folder",
            "dangerous": True,
            "triggers": ["clean yahoo spam", "yahoo spam", "clean my spam", "empty spam"],
            "steps": [
                {"type": "browser", "action": "goto", "url": "https://mail.yahoo.com/d"},
                {"type": "browser", "action": "click_optional", "selector": "button[title='Empty Spam']"},
            ],
        },
        "yahoo-login": {
            "name": "Yahoo Mail: Login",
            "description": "Open Yahoo Mail and ensure you're logged in.",
            "triggers": [
                "log into my yahoo mail",
                "login to yahoo mail",
                "login yahoo mail",
                "open yahoo mail",
                "yahoo mail login",
            ],
            "steps": [{"type": "browser", "action": "goto", "url": "https://mail.yahoo.com/d"}],
        },
    }


def test_playbook_matching_prefers_login_over_clean_spam() -> None:
    pb_id, _ = find_matching_playbook("Can you login to my yahoo mail", _playbooks())
    assert pb_id == "yahoo-login"


def test_playbook_matching_clean_spam() -> None:
    pb_id, _ = find_matching_playbook("clean my yahoo spam", _playbooks())
    assert pb_id == "yahoo-clean-spam"

