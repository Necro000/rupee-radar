from typing import List, Dict, Any
from sqlalchemy.orm import Session
from services.categorization.rules_engine import RulesEngine
from services.categorization.llm_categorizer import LLMCategorizer

class CategorizationService:
    def __init__(self):
        self.rules_engine = RulesEngine()
        self.llm_categorizer = LLMCategorizer()

    def categorize_transactions(self, db: Session, session_id: str, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Categorize a list of transactions using a hybrid rules + LLM fallback strategy.
        Utilizes session cache to reduce LLM calls for identical clean descriptions.
        """
        # Description cache mapping cleanDescription -> (category, confidence, source)
        desc_cache: Dict[str, tuple] = {}
        
        categorized_results = []
        to_llm_batch = []
        
        for tx in transactions:
            clean_desc = tx["cleanDescription"]
            desc_key = clean_desc.lower().strip()
            
            # 1. Check description cache first
            if desc_key in desc_cache:
                cat, conf, src = desc_cache[desc_key]
                tx["category"] = cat
                tx["categoryConfidence"] = conf
                tx["categorySource"] = src
                categorized_results.append(tx)
                continue
                
            # 2. Check rules engine (overrides + global triggers)
            rule_match = self.rules_engine.categorize(
                db, 
                session_id, 
                tx["cleanDescription"], 
                tx.get("merchant")
            )
            
            if rule_match:
                cat, conf, src = rule_match
                # Cache the result
                desc_cache[desc_key] = (cat, conf, src)
                
                tx["category"] = cat
                tx["categoryConfidence"] = conf
                tx["categorySource"] = src
                categorized_results.append(tx)
            else:
                # Add to batch for LLM categorization
                to_llm_batch.append(tx)

        # 3. Categorize remaining transactions in batches using Groq LLM
        if to_llm_batch:
            # Group identical descriptions in the LLM batch to prevent redundant calls
            llm_unique_txs = []
            seen_descriptions = set()
            
            for tx in to_llm_batch:
                desc_key = tx["cleanDescription"].lower().strip()
                if desc_key not in seen_descriptions:
                    seen_descriptions.add(desc_key)
                    llm_unique_txs.append(tx)
            
            # Call LLM in chunks of 30 unique transactions
            chunk_size = 30
            llm_mappings = {}
            
            for i in range(0, len(llm_unique_txs), chunk_size):
                chunk = llm_unique_txs[i:i + chunk_size]
                chunk_results = self.llm_categorizer.categorize_batch(chunk)
                llm_mappings.update(chunk_results)
                
            # Distribute LLM results back to all unmatched transactions (including non-unique ones)
            for tx in to_llm_batch:
                desc_key = tx["cleanDescription"].lower().strip()
                # Find corresponding unique transaction mapping
                mapped = llm_mappings.get(tx["id"])
                
                if mapped:
                    cat = mapped["category"]
                    conf = mapped["confidence"]
                    src = "llm"
                    
                    # Update cache
                    desc_cache[desc_key] = (cat, conf, src)
                    
                    tx["category"] = cat
                    tx["categoryConfidence"] = conf
                    tx["categorySource"] = src
                else:
                    # In case of missing mapping, check if cached or fallback
                    if desc_key in desc_cache:
                        cat, conf, src = desc_cache[desc_key]
                    else:
                        cat, conf, src = "Other", 0.3, "llm"
                        desc_cache[desc_key] = (cat, conf, src)
                        
                    tx["category"] = cat
                    tx["categoryConfidence"] = conf
                    tx["categorySource"] = src
                    
                categorized_results.append(tx)
                
        return categorized_results
