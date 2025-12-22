import logging
import re
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PromptDefense:
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
        self.sensitivity = sensitivity
    
    def detect_injection(self, text: str) -> Dict[str, Any]:
        report = {"is_injection": False, "patterns_found": [], "risk_level": "low", "message": None}
        text_lower = text.lower()
        for pattern in self.INJECTION_PATTERNS:
            if re.search(pattern, text_lower):
                report["patterns_found"].append(pattern)
                report["is_injection"] = True
        
        if len(report["patterns_found"]) == 0:
            report["risk_level"] = "low"
        elif len(report["patterns_found"]) == 1:
            report["risk_level"] = "medium"
        else:
            report["risk_level"] = "high"
        
        if report["is_injection"]:
            report["message"] = "Suspicious input pattern detected"
        
        return report
    
    def sanitize_input(self, text: str) -> str:
        sanitized = text
        for pattern in self.INJECTION_PATTERNS:
            sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)
        return sanitized.strip()
    
    def should_block(self, report: Dict[str, Any]) -> bool:
        if self.sensitivity == "low":
            return report["risk_level"] == "high"
        elif self.sensitivity == "medium":
            return report["risk_level"] in ["medium", "high"]
        else:
            return report["is_injection"]
