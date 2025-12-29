from agent.autonomous.learning_agent import LearningAgent


def test_intent_calendar_tomorrow_fallback():
    agent = LearningAgent(llm=None)
    intent = agent._parse_intent_fallback(
        "Check my Google Calendar and tell me what I have tomorrow"
    )
    assert intent.action == "calendar.list_events"
    assert intent.auth_provider == "google"
    assert intent.parameters.get("time_range") == "tomorrow"
