"""
DrCodePT Phase 7 - Real Card Generator
Generates cards using Claude API + PERRIO Protocol
"""

import anthropic
from typing import List, Dict, Optional
import json
import re

class CardGenerator:
    """Generates flashcards using Claude and PERRIO Protocol"""
    
    def __init__(self, api_key: str):
        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-opus-4-1-20250805"
    
    def generate_cards_perrio(self, course_name: str, topic: str = None, 
                              num_cards: int = 24) -> List[Dict]:
        """
        Generate cards using PERRIO Protocol
        
        PERRIO = Prime-Encode-Retrieve-Reinforce-Close
        """
        
        if not topic:
            topic = f"General review of {course_name}"
        
        prompt = f"""You are an expert PT educator creating spaced-repetition flashcards.

Course: {course_name}
Topic: {topic}
Number of cards: {num_cards}

Generate {num_cards} high-quality Anki flashcards following the PERRIO Protocol:

P - PRIME: Explain concept simply and deeply (foundation)
E - ENCODE: Create clear, focused questions
R - RETRIEVE: Make answers testable/retrievable
R - REINFORCE: Include clinical significance
O - CLOSE: Add memory hooks and checkpoints

Requirements:
1. Each card tests ONE concept
2. Front side: Clear, concise question (max 100 chars)
3. Back side: Complete answer with clinical context (max 300 chars)
4. Include memory hooks (mnemonics, analogies, clinical applications)
5. Add relevant tags for spaced repetition

Return ONLY valid JSON array with no markdown or code blocks. Each object must have:
{{
    "front": "Question text",
    "back": "Answer with explanation",
    "tags": ["tag1", "tag2"],
    "difficulty": "easy|medium|hard"
}}

Example:
[
  {{"front": "What is the normal range for...?", "back": "Normal range: X-Y. Clinically important because...", "tags": ["anatomy", "normal-values"], "difficulty": "easy"}},
  {{"front": "How do you test...?", "back": "Procedure: 1. Position... 2. Palpate... Clinical significance: Identifies...", "tags": ["exam-skills", "palpation"], "difficulty": "medium"}}
]

Generate cards now:"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            cards = self._parse_json_cards(response_text)
            
            if not cards:
                print(f"⚠️  No cards parsed, generating fallback cards")
                cards = self._generate_fallback_cards(course_name, topic, num_cards)
            
            return cards
            
        except Exception as e:
            print(f"❌ Error generating cards: {e}")
            return self._generate_fallback_cards(course_name, topic, num_cards)
    
    def _parse_json_cards(self, response_text: str) -> List[Dict]:
        """Parse JSON cards from Claude response"""
        cards = []
        
        try:
            # Try to find JSON array in response
            json_match = re.search(r'\[[\s\S]*\]', response_text)
            if json_match:
                json_str = json_match.group()
                cards = json.loads(json_str)
                
                # Validate structure
                valid_cards = []
                for card in cards:
                    if 'front' in card and 'back' in card:
                        valid_cards.append({
                            'front': str(card.get('front', '')),
                            'back': str(card.get('back', '')),
                            'tags': card.get('tags', ['generated']),
                            'difficulty': card.get('difficulty', 'medium')
                        })
                return valid_cards
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"Parse error: {e}")
        
        return []
    
    def _generate_fallback_cards(self, course_name: str, topic: str, 
                                 num_cards: int) -> List[Dict]:
        """Generate fallback cards if Claude fails"""
        fallback_templates = [
            {
                'front': f'What is a key concept in {topic}?',
                'back': f'Key concept from {course_name}: Understanding {topic} is essential for PT practice.',
                'tags': ['fallback', course_name.lower()],
                'difficulty': 'easy'
            },
            {
                'front': f'How do you clinically apply {topic}?',
                'back': f'Clinical application: {topic} is applied by assessing and treating patients using evidence-based methods.',
                'tags': ['fallback', 'clinical', course_name.lower()],
                'difficulty': 'medium'
            },
            {
                'front': f'What is the clinical significance of {topic}?',
                'back': f'Clinical significance: Understanding {topic} improves patient outcomes and treatment effectiveness.',
                'tags': ['fallback', 'clinical', course_name.lower()],
                'difficulty': 'medium'
            }
        ]
        
        # Repeat templates to fill num_cards
        cards = []
        for i in range(num_cards):
            template = fallback_templates[i % len(fallback_templates)]
            cards.append({
                'front': template['front'] + f' ({i+1})',
                'back': template['back'],
                'tags': template['tags'],
                'difficulty': template['difficulty']
            })
        
        return cards
    
    def generate_weak_area_cards(self, weak_areas: List[str], 
                                 cards_per_area: int = 15) -> List[Dict]:
        """Generate focused cards for weak areas"""
        
        areas_text = ", ".join(weak_areas)
        prompt = f"""Generate {cards_per_area * len(weak_areas)} challenging Anki cards for weak PT areas.

Weak areas: {areas_text}
Cards per area: {cards_per_area}

These should be harder than standard prep - focus on:
- Clinical reasoning
- Integration across concepts
- Common mistakes
- Edge cases
- High-yield clinical scenarios

Return ONLY valid JSON array:
[{{"front": "Q", "back": "A", "tags": ["weak-area"], "difficulty": "hard"}}, ...]

Generate cards now:"""
        
        try:
            message = self.client.messages.create(
                model=self.model,
                max_tokens=2500,
                messages=[{"role": "user", "content": prompt}]
            )
            
            response_text = message.content[0].text
            return self._parse_json_cards(response_text)
            
        except Exception as e:
            print(f"Error generating weak-area cards: {e}")
            return []


def get_generator(api_key: str) -> CardGenerator:
    """Get card generator instance"""
    return CardGenerator(api_key)
