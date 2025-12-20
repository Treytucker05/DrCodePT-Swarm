import sys
sys.path.insert(0, '.')

from agent.treys_agent import _infer_intent, _score_intent, _MAIL_KEYWORDS, _MAIL_PHRASES

text = 'Can you help me organize the folders in my yahoo mail?'
mail_score = _score_intent(text, _MAIL_KEYWORDS, _MAIL_PHRASES)
intent = _infer_intent(text)

print(f"Text: {text}")
print(f"Mail score: {mail_score}")
print(f"Intent: {intent}")
