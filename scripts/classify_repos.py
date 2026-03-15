"""
Repository classification script - Classify repos into industries using GPT-4.
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database.crud import DataStore
from src.database.models import init_db
from src.classification import IndustryClassifier
from loguru import logger


def main():
    """Main classification pipeline."""
    logger.info("Starting repository classification...")
    
    # Load repositories
    repos_path = "data/raw/repos/repositories.json"
    if not os.path.exists(repos_path):
        logger.error(f"Repositories file not found: {repos_path}")
        print("❌ Error: Run extract_data.py first!")
        return
    
    with open(repos_path, "r", encoding="utf-8") as f:
        repos = json.load(f)
    
    logger.info(f"Loaded {len(repos)} repositories")
    
    # Initialize classifier
    classifier = IndustryClassifier()
    
    # Classify repositories
    classifications = classifier.batch_classify(repos)
    
    # Save classifications
    os.makedirs("data/processed", exist_ok=True)
    
    with open("data/processed/classifications.json", "w", encoding="utf-8") as f:
        json.dump(classifications, f, indent=2, ensure_ascii=False)

    pd.DataFrame(classifications).to_csv("data/processed/classifications.csv", index=False)

    engine = init_db()
    store = DataStore(engine)
    try:
        store.save_classifications(classifications)
        logger.info("Persisted classifications to SQLite")
    finally:
        store.close()
    
    logger.info("Classification complete!")
    logger.info("Saved to: data/processed/classifications.json and data/processed/classifications.csv")
    
    # Show summary
    from collections import Counter
    industry_counts = Counter(c["industry_code"] for c in classifications)
    
    print("\n✅ Classification complete!")
    print(f"📊 Classified {len(classifications)} repositories")
    print("\nIndustry Distribution:")
    for code, count in industry_counts.most_common():
        industry_name = classifier.INDUSTRIES.get(code, "Unknown")
        print(f"  {code} - {industry_name}: {count}")
    
    print("\nNext step: Calculate metrics")
    print("python scripts/calculate_metrics.py")


if __name__ == "__main__":
    main()
