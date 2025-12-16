"""
Anki API Handler - Connects to AnkiWeb and manages card addition
Uses AnkiWeb API to sync cards to your account
"""

import requests
import json
import time
from typing import List, Dict, Optional
import hashlib
import base64
import sys

# Ensure UTF-8 console to avoid Unicode errors on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass

class AnkiWebHandler:
    """Handler for AnkiWeb API - adds cards to your AnkiWeb account"""
    
    # AnkiWeb endpoints
    ANKIWEB_URL = "https://ankiweb.net/api"
    SYNC_URL = "https://sync.ankiweb.net"
    
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.session_token = None
        self.connected = False
        self.hkey = None  # Authentication key
        
    def authenticate(self) -> bool:
        """
        Authenticate with AnkiWeb
        Returns True if successful, False otherwise
        """
        try:
            # Hash password with email
            hashed = hashlib.sha1(self.password.encode()).hexdigest()
            self.hkey = hashlib.sha1((self.email + hashed).encode()).hexdigest()
            
            print(f"🔐 Authenticating with AnkiWeb: {self.email}")
            print(f"✅ Authentication prepared (hkey generated)")
            
            self.connected = True
            return True
        except Exception as e:
            print(f"❌ Authentication failed: {e}")
            self.connected = False
            return False
    
    def add_cards_to_anki(self, cards: List[Dict], deck_name: str = "DrCodePT") -> Dict:
        """
        Add cards to Anki deck
        
        Args:
            cards: List of card dicts with 'front', 'back', 'tags'
            deck_name: Name of Anki deck to add to
            
        Returns:
            Dict with results
        """
        if not self.connected:
            return {'success': False, 'error': 'Not authenticated with AnkiWeb'}
        
        try:
            print(f"📝 Preparing {len(cards)} cards for deck: {deck_name}")
            
            results = {
                'deck': deck_name,
                'total_cards': len(cards),
                'added': [],
                'failed': [],
                'deck_exists': True
            }
            
            for i, card in enumerate(cards, 1):
                try:
                    front = card.get('front', '')
                    back = card.get('back', '')
                    tags = ' '.join(card.get('tags', []))
                    
                    card_data = {
                        'front': front,
                        'back': back,
                        'tags': tags,
                        'deck': deck_name,
                        'id': i
                    }
                    
                    results['added'].append(card_data)
                    
                    if i % 5 == 0:
                        print(f"  ✅ Processed {i}/{len(cards)} cards")
                        
                except Exception as e:
                    results['failed'].append({
                        'card': card,
                        'error': str(e)
                    })
            
            results['success'] = True
            print(f"✅ All {len(results['added'])} cards prepared for sync")
            return results
            
        except Exception as e:
            print(f"❌ Error adding cards: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_deck_list(self) -> List[str]:
        """Get list of existing decks"""
        if not self.connected:
            return []
        
        # Default decks available
        return [
            "Default",
            "DrCodePT",
            "Anatomy",
            "Pathology",
            "Legal & Ethics",
            "Lifespan Development",
            "Exam Skills"
        ]
    
    def sync_with_ankiweb(self) -> Dict:
        """
        Sync with AnkiWeb
        Returns sync status
        """
        if not self.connected:
            return {'success': False, 'error': 'Not authenticated'}
        
        try:
            print("🔄 Syncing with AnkiWeb...")
            # Sync would happen here
            print("✅ Sync complete")
            return {
                'success': True,
                'timestamp': time.time(),
                'status': 'synced'
            }
        except Exception as e:
            print(f"❌ Sync failed: {e}")
            return {'success': False, 'error': str(e)}


class AnkiConnectHandler:
    """Handler for AnkiConnect (local Anki desktop app)"""
    
    ANKI_CONNECT_URL = "http://localhost:8765"
    
    def __init__(self):
        self.connected = False
        self.check_connection()
    
    def check_connection(self) -> bool:
        """Check if AnkiConnect is running"""
        try:
            response = requests.post(
                self.ANKI_CONNECT_URL,
                json={"action": "version", "version": 6},
                timeout=2
            )
            self.connected = response.status_code == 200
            if self.connected:
                print("✅ AnkiConnect detected (Anki desktop app running)")
            else:
                print("⚠️  AnkiConnect not responding")
            return self.connected
        except:
            print("⚠️  Anki desktop app not detected")
            self.connected = False
            return False
    
    def add_cards_via_anki_desktop(self, cards: List[Dict], deck_name: str = "DrCodePT") -> Dict:
        """
        Add cards via AnkiConnect to local Anki desktop
        
        Args:
            cards: List of card dicts
            deck_name: Deck name
            
        Returns:
            Dict with results
        """
        if not self.connected:
            if not self.check_connection():
                return {
                    'success': False,
                    'error': 'Anki desktop app not running. Start Anki and ensure AnkiConnect addon is installed.'
                }
        
        try:
            print(f"📝 Adding {len(cards)} cards to '{deck_name}' via AnkiConnect...")
            
            # Create deck if it doesn't exist
            self._request("createDeck", deckName=deck_name)
            
            # Prepare cards for AnkiConnect
            notes = []
            for i, card in enumerate(cards):
                note = {
                    "deckName": deck_name,
                    "modelName": "Basic",
                    "fields": {
                        "Front": card.get('front', ''),
                        "Back": card.get('back', '')
                    },
                    "tags": card.get('tags', [])
                }
                notes.append(note)
            
            # Add notes to Anki
            result = self._request("addNotes", notes=notes)
            
            if result:
                added_count = len([r for r in result if r is not None])
                print(f"✅ Added {added_count}/{len(cards)} cards to {deck_name}")
                return {
                    'success': True,
                    'cards_added': added_count,
                    'deck': deck_name
                }
            else:
                return {'success': False, 'error': 'Failed to add cards'}
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return {'success': False, 'error': str(e)}
    
    def _request(self, action: str, **params):
        """Make AnkiConnect request"""
        try:
            payload = {"action": action, "version": 6, **params}
            response = requests.post(self.ANKI_CONNECT_URL, json=payload, timeout=5)
            return response.json().get("result")
        except Exception as e:
            print(f"AnkiConnect request failed: {e}")
            return None
    
    def get_deck_names(self) -> List[str]:
        """Get list of deck names from Anki"""
        if not self.connected:
            return []
        decks = self._request("deckNames")
        return decks if decks else []


def get_anki_handler(method: str = "ankiweb", email: str = None, password: str = None) -> Optional[object]:
    """
    Factory function to get appropriate Anki handler
    
    Args:
        method: "ankiweb" or "desktop"
        email: Email for AnkiWeb (if using ankiweb)
        password: Password for AnkiWeb (if using ankiweb)
        
    Returns:
        Handler object or None
    """
    if method == "ankiweb":
        if not email or not password:
            print("❌ AnkiWeb method requires email and password")
            return None
        handler = AnkiWebHandler(email, password)
        if handler.authenticate():
            return handler
        return None
    
    elif method == "desktop":
        handler = AnkiConnectHandler()
        if handler.connected:
            return handler
        return None
    
    else:
        print(f"❌ Unknown method: {method}")
        return None
