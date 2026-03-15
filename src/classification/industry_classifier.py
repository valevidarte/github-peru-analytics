"""
Industry classification using GPT-4.
"""

import os
import json
from dotenv import load_dotenv
from openai import OpenAI
from loguru import logger
from tqdm import tqdm


class IndustryClassifier:
    """Classify repositories into CIIU industry categories using GPT-4."""
    
    # CIIU Industry Categories (Peru)
    INDUSTRIES = {
        "A": "Agriculture, forestry and fishing",
        "B": "Mining and quarrying",
        "C": "Manufacturing",
        "D": "Electricity, gas, steam supply",
        "E": "Water supply; sewerage",
        "F": "Construction",
        "G": "Wholesale and retail trade",
        "H": "Transportation and storage",
        "I": "Accommodation and food services",
        "J": "Information and communication",
        "K": "Financial and insurance activities",
        "L": "Real estate activities",
        "M": "Professional, scientific activities",
        "N": "Administrative and support activities",
        "O": "Public administration and defense",
        "P": "Education",
        "Q": "Human health and social work",
        "R": "Arts, entertainment and recreation",
        "S": "Other service activities",
        "T": "Activities of households",
        "U": "Extraterritorial organizations"
    }

    VALID_CONFIDENCE = {"high", "medium", "low"}
    
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv("OPENAI_CLASSIFICATION_MODEL", "gpt-4.1-mini")
        logger.info("IndustryClassifier initialized")
    
    def classify_repository(
        self,
        name: str,
        description: str,
        readme: str,
        topics: list[str],
        language: str
    ) -> dict:
        """
        Classify a repository into an industry category.
        
        Returns:
            dict with keys: industry_code, industry_name, confidence, reasoning
        """
        prompt = f"""Analyze this GitHub repository and classify it into ONE of the following industry categories based on its potential application or the industry it serves.

REPOSITORY INFORMATION:
- Name: {name}
- Description: {description or 'No description'}
- Primary Language: {language or 'Not specified'}
- Topics: {', '.join(topics) if topics else 'None'}
- README (first 2000 chars): {readme[:2000] if readme else 'No README'}

INDUSTRY CATEGORIES:
{json.dumps(self.INDUSTRIES, indent=2)}

INSTRUCTIONS:
1. Analyze the repository's purpose, functionality, and potential use cases
2. Consider what industry would most benefit from or use this software
3. If it's a general-purpose tool (e.g., utility library), classify based on the most likely industry application
4. If truly generic (e.g., "hello world"), use "J" (Information and communication)

CLASSIFICATION GUIDELINES:
- Mobile banking app -> K (high confidence)
- Hospital management system -> Q (high confidence)
- E-commerce platform -> G (high confidence)
- School LMS -> P (high confidence)
- Mining data analysis -> B (high confidence)

EDGE CASES:
- Generic REST API -> J (or M if clearly consulting/pro-services)
- Machine learning library -> J or M depending on domain specificity
- DevOps tools -> J (or N if mainly administrative operations)
- Game projects -> R (or J if game engine/framework)
- Personal portfolios -> J (or S for broader service business context)

Respond in JSON format:
{{
    "industry_code": "X",
    "industry_name": "Full industry name",
    "confidence": "high|medium|low",
    "reasoning": "Brief explanation of why this classification was chosen"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at classifying software projects by industry. Always respond with valid JSON."
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            raw_result = json.loads(response.choices[0].message.content)
            result = self._normalize_classification(raw_result)
            logger.debug(f"Classified {name} as {result['industry_code']}")
            return result
            
        except Exception as e:
            logger.error(f"Error classifying {name}: {e}")
            return self._fallback_classification(f"Classification failed: {str(e)}")
    
    def batch_classify(
        self,
        repositories: list[dict],
        batch_size: int = 10
    ) -> list[dict]:
        """
        Classify multiple repositories.
        
        Args:
            repositories: List of repository dictionaries
            batch_size: Number of repos to process at once (for progress display)
            
        Returns:
            List of classification results
        """
        results = []
        
        logger.info(f"Classifying {len(repositories)} repositories...")
        
        for i in range(0, len(repositories), batch_size):
            batch = repositories[i : i + batch_size]
            for repo in tqdm(batch, desc=f"Classifying batch {i // batch_size + 1}"):
                classification = self.classify_repository(
                    name=repo.get("name", ""),
                    description=repo.get("description", ""),
                    readme=repo.get("readme", ""),
                    topics=repo.get("topics", []),
                    language=repo.get("language", "")
                )

                results.append({
                    "repo_id": repo["id"],
                    "repo_name": repo["name"],
                    "repo_full_name": repo.get("full_name", ""),
                    **classification
                })
        
        logger.info(f"Classification complete: {len(results)} repositories")
        return results

    def _normalize_classification(self, result: dict) -> dict:
        industry_code = str(result.get("industry_code", "J")).strip().upper()
        if industry_code not in self.INDUSTRIES:
            industry_code = "J"

        confidence = str(result.get("confidence", "low")).strip().lower()
        if confidence not in self.VALID_CONFIDENCE:
            confidence = "low"

        reasoning = str(result.get("reasoning", "")).strip() or "No reasoning provided by model"

        return {
            "industry_code": industry_code,
            "industry_name": self.INDUSTRIES[industry_code],
            "confidence": confidence,
            "reasoning": reasoning,
        }

    def _fallback_classification(self, reason: str) -> dict:
        return {
            "industry_code": "J",
            "industry_name": self.INDUSTRIES["J"],
            "confidence": "low",
            "reasoning": reason,
        }
