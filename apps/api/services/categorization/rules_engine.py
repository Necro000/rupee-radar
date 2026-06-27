import os
import re
import json
from typing import Dict, List, Tuple, Optional
from sqlalchemy.orm import Session
from db.session_store import DBSessionRule

class RulesEngine:
    def __init__(self, rules_path: Optional[str] = None):
        if not rules_path:
            # Default lookup relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            rules_path = os.path.join(current_dir, "..", "..", "rules", "categories.json")
            
        self.rules_path = rules_path
        self.global_rules: Dict[str, List[str]] = {}
        self.load_global_rules()

    def load_global_rules(self):
        """Loads default keyword-category mappings from categories.json."""
        try:
            if os.path.exists(self.rules_path):
                with open(self.rules_path, 'r', encoding='utf-8') as f:
                    self.global_rules = json.load(f)
            else:
                print(f"Warning: Global categories rules file not found at: {self.rules_path}")
        except Exception as e:
            print(f"Error loading global rules: {str(e)}")

    def get_session_rules(self, db: Session, session_id: str) -> Dict[str, str]:
        """Fetches learned override rules for this session from the database."""
        rules = db.query(DBSessionRule).filter(DBSessionRule.session_id == session_id).all()
        # Map: lowercase pattern -> category
        return {rule.pattern.lower().strip(): rule.category for rule in rules}

    def categorize(
        self, 
        db: Session, 
        session_id: str, 
        clean_description: str, 
        merchant: Optional[str] = None
    ) -> Optional[Tuple[str, float, str]]:
        """
        Attempts to categorize a transaction.
        Checks session-specific overrides first, then global keyword rules.
        Returns Tuple of (category, confidence, source) or None if no match.
        """
        desc_lower = clean_description.lower().strip()
        merchant_lower = merchant.lower().strip() if merchant else ""

        # 1. Check Session Overrides first (confidence = 1.0, source = 'user')
        session_rules = self.get_session_rules(db, session_id)
        
        # Match on merchant first
        if merchant_lower and merchant_lower in session_rules:
            return session_rules[merchant_lower], 1.0, "user"
            
        # Match on exact clean description
        if desc_lower in session_rules:
            return session_rules[desc_lower], 1.0, "user"
            
        # Match on substring patterns in session rules
        for pattern, category in session_rules.items():
            if pattern in desc_lower or (merchant_lower and pattern in merchant_lower):
                return category, 1.0, "user"

        # 2. Check Global Rules (confidence = 0.9 for exact/full keyword match, 0.7 for partial)
        for category, keywords in self.global_rules.items():
            for keyword in keywords:
                kw = keyword.lower().strip()
                
                # Check exact merchant match
                if merchant_lower and merchant_lower == kw:
                    return category, 0.9, "rule"
                    
                # Check description substring match
                if kw in desc_lower or (merchant_lower and kw in merchant_lower):
                    # If keyword is very short (like 'dr', 'to', etc.), require word boundaries to avoid false positives
                    if len(kw) <= 3:
                        pattern = rf"\b{re.escape(kw)}\b"
                        if re.search(pattern, desc_lower) or (merchant_lower and re.search(pattern, merchant_lower)):
                            return category, 0.7, "rule"
                    else:
                        return category, 0.7, "rule"
                        
        return None
