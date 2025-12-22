"""Defense against prompt injection attacks."""

import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)


class PromptDefense:
    """Detect and prevent prompt injection attacks.
    
    Identifies suspicious patterns in user input that might be
    attempting to manipulate the agent.
    """
    
    # Patterns that indicate prompt injection attempts
    INJECTION_PATTERNS = [
        r"ignore.*instructions",
        r"forget.*previous",
        r"system.*prompt",
        r"you.*are.*now",
        r"pretend.*you.*are",
        r"act.*as.*if",
        r"disregard.*rules",
        r"bypass.*security",
        r"override.*settings",
    ]
    
    def __init__(self, sensitivity: str = "medium"):
        """Initialize prompt defense.
        
        Args:
            sensitivity: Detection sensitivity (low, medium, high)
        """
        self.sensitivity = sensitivity
        logger.info(f"PromptDefense initialized with sensitivity={sensitivity}")
    
    def detect_injection(self, text: str) -> Dict[str, Any]:
        """Detect prompt injection attempts.
        
        Args:
            text: User input to check
        
        Returns:
            Detection report
        """
        report = {
            "is_injection": False,
            "patterns_found": [],
            "risk_level": "low",
            "message": None,
        }
        
        text_lower = text.lower()
        
        # Check for injection patterns
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                report["patterns_found"].append(pattern)
                report["is_injection"] = True
        
        # Determine risk level
        if len(report["patterns_found"]) == 0:
            report["risk_level"] = "low"
        elif len(report["patterns_found"]) == 1:
            report["risk_level"] = "medium"
        else:
            report["risk_level"] = "high"
        
        if report["is_injection"]:
            logger.warning(f"Potential prompt injection detected: {report['patterns_found']}")
            report["message"] = "Suspicious input pattern detected"
        
        return report
    
    def sanitize_input(self, text: str) -> str:
        """Sanitize user input.
        
        Args:
            text: User input to sanitize
        
        Returns:
            Sanitized input
        """
        # Remove suspicious patterns
        sanitized = text
        
        for pattern in self.INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        
        return sanitized.strip()
    
    def should_block(self, report: Dict[str, Any]) -> bool:
        """Determine if input should be blocked.
        
        Args:
            report: Detection report from detect_injection()
        
        Returns:
            True if input should be blocked
        """
        if self.sensitivity == "low":
            return report["risk_level"] == "high"
        elif self.sensitivity == "medium":
            return report["risk_level"] in ["medium", "high"]
        else:  # high
            return report["is_injection"]
