# src/pii/detector.py
import re
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class RecognizerResult:
    """Simple PII detection result"""
    entity_type: str
    start: int
    end: int
    score: float

def build_vietnamese_analyzer():
    """
    Xây dựng analyzer với các recognizer tùy chỉnh cho VN.
    Sử dụng direct regex matching cho Vietnamese PII.
    """
    
    # Define patterns
    patterns = {
        "VN_CCCD": {
            "regex": re.compile(r'\b\d{11,12}\b'),  # 11-12 digits for CCCD
            "score": 0.9
        },
        "VN_PHONE": {
            # VN phone: 0[3|5|7|8|9] + 8 digits, also match numbers that look like phone numbers
            "regex": re.compile(r'\b0[35789]\d{8}\b|\b[35789]\d{8}\b'),  
            "score": 0.85
        },
        "EMAIL_ADDRESS": {
            "regex": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "score": 0.95
        },
        "PERSON": {
            # Match Vietnamese names: 2+ words starting with capital letter
            "regex": re.compile(r'\b[A-ZÀ-Ỹ][a-zà-ỹ]+(?:\s+[A-ZÀ-Ỹ][a-zà-ỹ]+){1,4}\b'),
            "score": 0.7
        }
    }
    
    class VietnameseAnalyzer:
        def __init__(self):
            self.patterns = patterns
        
        def analyze(self, text: str, language: str = "vi", entities: Optional[List[str]] = None) -> List[RecognizerResult]:
            """Detect PII in text"""
            results = []
            
            if entities is None:
                entities = list(self.patterns.keys())
            
            for entity_type in entities:
                if entity_type not in self.patterns:
                    continue
                    
                pattern_info = self.patterns[entity_type]
                regex = pattern_info["regex"]
                score = pattern_info["score"]
                
                for match in regex.finditer(text):
                    results.append(RecognizerResult(
                        entity_type=entity_type,
                        start=match.start(),
                        end=match.end(),
                        score=score
                    ))
            
            return results
    
    return VietnameseAnalyzer()


def detect_pii(text: str, analyzer) -> list:
    """
    Detect PII trong text tiếng Việt.
    Trả về list các RecognizerResult.
    Entities cần detect: PERSON, EMAIL_ADDRESS, VN_CCCD, VN_PHONE
    """
    results = analyzer.analyze(
        text=text,
        language="vi",
        entities=["PERSON", "EMAIL_ADDRESS", "VN_CCCD", "VN_PHONE"]
    )
    return results
