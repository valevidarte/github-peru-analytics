"""AI agents for classification and autonomous data collection."""

from __future__ import annotations

import json
import os
import time
from collections import OrderedDict

from loguru import logger
from openai import OpenAI

from ..extraction import GitHubClient, RepoExtractor, UserExtractor


class ClassificationAgent:
    """
    Autonomous agent that classifies repositories using tools.
    The agent decides what information it needs and classifies accordingly.
    """
    
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
    
    def __init__(self, github_client=None):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found")
        
        self.client = OpenAI(api_key=api_key)
        self.github_client = github_client
        self.model = os.getenv("OPENAI_CLASSIFICATION_MODEL", "gpt-4.1-mini")
        
        # Define available tools
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_readme",
                    "description": "Fetch the README content of a repository for more context",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string", "description": "Repository owner"},
                            "repo": {"type": "string", "description": "Repository name"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_languages",
                    "description": "Fetch repository language breakdown as bytes by language",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "owner": {"type": "string", "description": "Repository owner"},
                            "repo": {"type": "string", "description": "Repository name"}
                        },
                        "required": ["owner", "repo"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "classify_industry",
                    "description": "Classify the repository into an industry category",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "industry_code": {
                                "type": "string",
                                "description": "Single letter code (A-U)"
                            },
                            "industry_name": {
                                "type": "string",
                                "description": "Full industry name"
                            },
                            "confidence": {
                                "type": "string",
                                "enum": ["high", "medium", "low"],
                                "description": "Confidence level"
                            },
                            "reasoning": {
                                "type": "string",
                                "description": "Explanation of classification"
                            }
                        },
                        "required": ["industry_code", "industry_name", "confidence", "reasoning"]
                    }
                }
            }
        ]
        
        logger.info("ClassificationAgent initialized")

    @staticmethod
    def _fallback_result(reason: str) -> dict:
        return {
            "industry_code": "J",
            "industry_name": "Information and communication",
            "confidence": "low",
            "reasoning": reason,
        }

    @staticmethod
    def _to_message_dict(message) -> dict:
        """Normalize SDK message object to a dict for follow-up turns."""
        tool_calls = []
        if message.tool_calls:
            for call in message.tool_calls:
                tool_calls.append(
                    {
                        "id": call.id,
                        "type": call.type,
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        },
                    }
                )

        normalized = {
            "role": message.role or "assistant",
            "content": message.content or "",
        }
        if tool_calls:
            normalized["tool_calls"] = tool_calls
        return normalized

    @staticmethod
    def _parse_tool_arguments(raw_arguments: str) -> dict:
        try:
            return json.loads(raw_arguments or "{}")
        except json.JSONDecodeError:
            logger.warning("Tool arguments were not valid JSON: {}", raw_arguments)
            return {}

    def _create_completion(self, messages: list[dict]):
        """Create completion with small retry budget for transient API failures."""
        last_error = None
        for attempt in range(1, 4):
            try:
                return self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=self.tools,
                    tool_choice="auto",
                )
            except Exception as exc:
                last_error = exc
                logger.warning(
                    "OpenAI completion failed (attempt {}/3): {}", attempt, exc
                )
                if attempt < 3:
                    time.sleep(1.5 * attempt)

        raise RuntimeError(f"OpenAI completion failed after retries: {last_error}")
    
    def run(self, repository: dict) -> dict:
        """
        Run the classification agent on a repository.
        The agent decides what information it needs and classifies the repo.
        
        Args:
            repository: Repository data dictionary
            
        Returns:
            Classification result
        """
        repo_name = repository.get("name", "unknown")
        logger.info(f"Agent classifying: {repo_name}")
        
        messages = [
            {
                "role": "system",
                "content": f"""You are an AI agent that classifies GitHub repositories into industry categories.

Your task is to analyze a repository and determine which industry it serves.
You have access to tools to get more information if needed.

Industry codes available:
{json.dumps(self.INDUSTRIES, indent=2)}

Steps:
1. Review the basic repository information provided
2. If the description and topics are insufficient, fetch the README for more context
3. Use get_languages when language/domain is ambiguous
4. Make your classification using the classify_industry tool
5. Always provide reasoning for your decision
"""
            },
            {
                "role": "user",
                "content": f"""Please classify this repository:

Name: {repository.get('name', 'Unknown')}
Full Name: {repository.get('full_name', 'Unknown')}
Description: {repository.get('description') or 'No description'}
Primary Language: {repository.get('language') or 'Unknown'}
Topics: {', '.join(repository.get('topics', [])) or 'None'}
Stars: {repository.get('stargazers_count', 0)}
Forks: {repository.get('forks_count', 0)}

Classify this repository into the appropriate industry category.
"""
            }
        ]
        
        max_iterations = 5
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            
            try:
                response = self._create_completion(messages)
            except Exception as exc:
                logger.error("Agent failed during completion call: {}", exc)
                return self._fallback_result(
                    "Agent failed due to API/completion error, defaulted to tech"
                )
            
            message = response.choices[0].message
            
            # Check if agent wants to use tools
            if message.tool_calls:
                messages.append(self._to_message_dict(message))
                
                for tool_call in message.tool_calls:
                    function_name = tool_call.function.name
                    arguments = self._parse_tool_arguments(tool_call.function.arguments)

                    if not arguments:
                        logger.warning(
                            "Empty/invalid tool arguments for {}. Returning fallback.",
                            function_name,
                        )
                        return self._fallback_result(
                            "Invalid tool-call arguments produced by model"
                        )
                    
                    logger.debug(f"Agent calling tool: {function_name} with {arguments}")
                    
                    # Execute the requested tool
                    if function_name == "get_readme":
                        result = self._execute_get_readme(
                            arguments.get("owner"),
                            arguments.get("repo")
                        )
                    elif function_name == "get_languages":
                        result = self._execute_get_languages(
                            arguments.get("owner"),
                            arguments.get("repo")
                        )
                    elif function_name == "classify_industry":
                        # Agent has made its classification
                        arguments.setdefault("industry_name", self.INDUSTRIES.get(arguments.get("industry_code", "J"), self.INDUSTRIES["J"]))
                        arguments.setdefault("confidence", "low")
                        arguments.setdefault("reasoning", "No reasoning provided by model")

                        if arguments.get("industry_code") not in self.INDUSTRIES:
                            arguments["industry_code"] = "J"
                            arguments["industry_name"] = self.INDUSTRIES["J"]
                            arguments["confidence"] = "low"
                            arguments["reasoning"] = (
                                "Agent produced an invalid code and was normalized to J"
                            )

                        logger.info(f"Agent classified {repo_name} as {arguments['industry_code']}")
                        return arguments
                    else:
                        result = {"error": f"Unknown tool: {function_name}"}
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
            else:
                # No tool calls - agent finished without classification (shouldn't happen)
                logger.warning(f"Agent finished without classification for {repo_name}")
                break
        
        # Fallback if agent doesn't classify
        logger.error(f"Agent failed to classify {repo_name}, using fallback")
        return self._fallback_result(
            "Agent failed to complete classification, defaulted to tech"
        )
    
    def _execute_get_readme(self, owner: str, repo: str) -> dict:
        """Execute the get_readme tool."""
        if not self.github_client:
            return {"error": "GitHub client not available", "readme": ""}
        
        try:
            from ..extraction.repo_extractor import RepoExtractor
            extractor = RepoExtractor(self.github_client)
            readme = extractor.get_repo_readme(owner, repo)
            return {"readme": readme[:2000], "success": True}
        except Exception as e:
            logger.error(f"Error fetching README: {e}")
            return {"error": str(e), "readme": ""}

    def _execute_get_languages(self, owner: str, repo: str) -> dict:
        """Execute the get_languages tool."""
        if not self.github_client:
            return {"error": "GitHub client not available", "languages": {}}

        try:
            from ..extraction.repo_extractor import RepoExtractor

            extractor = RepoExtractor(self.github_client)
            languages = extractor.get_repo_languages(owner, repo)
            return {"languages": languages, "success": True}
        except Exception as e:
            logger.error(f"Error fetching languages: {e}")
            return {"error": str(e), "languages": {}}


class DataCollectionAgent:
    """Option A agent: autonomous collection of Peru-related users and repositories."""

    def __init__(self, client=None, user_extractor=None, repo_extractor=None):
        self.client = client or GitHubClient()
        self.user_extractor = user_extractor or UserExtractor(self.client)
        self.repo_extractor = repo_extractor or RepoExtractor(self.client)

    def run(
        self,
        target_repositories: int = 1000,
        locations: list[str] | None = None,
        max_users_per_location: int = 250,
        max_repos_per_user: int = 50,
        min_followers_to_dig: int = 5,
        min_public_repos_to_dig: int = 3,
    ) -> dict:
        locations = locations or ["Peru", "Lima", "Arequipa", "Cusco", "Trujillo"]

        logger.info("[Agent] Starting autonomous data collection")
        logger.info(
            "[Agent] Strategy: locations={}, target_repositories={}, max_users_per_location={}",
            locations,
            target_repositories,
            max_users_per_location,
        )

        users_seed = []
        for location in locations:
            logger.info("[Agent] Searching users for location='{}'", location)
            found = self.user_extractor.search_users_by_location(
                location=location,
                max_users=max_users_per_location,
            )
            logger.info("[Agent] Found {} seed users for '{}'", len(found), location)
            users_seed.extend(found)

        unique_seed = list({user["id"]: user for user in users_seed}.values())
        logger.info("[Agent] Unique seed users after deduplication: {}", len(unique_seed))

        collected_users = []
        collected_repos = []

        for seed in unique_seed:
            if len(collected_repos) >= target_repositories:
                logger.info("[Agent] Target repositories reached: {}", target_repositories)
                break

            login = seed.get("login")
            if not login:
                continue

            try:
                user_details = self.user_extractor.get_user_details(login)
            except Exception as exc:
                logger.warning(
                    "[Agent] Could not fetch user details for '{}': {}", login, exc
                )
                continue

            decision, reason = self._should_dig_deeper(
                user_details=user_details,
                min_followers_to_dig=min_followers_to_dig,
                min_public_repos_to_dig=min_public_repos_to_dig,
            )
            logger.info("[Agent] Decision for '{}': dig_deeper={} ({})", login, decision, reason)

            if not decision:
                continue

            try:
                repos = self.user_extractor.get_user_repos(login)
            except Exception as exc:
                logger.warning(
                    "[Agent] Could not fetch repositories for '{}': {}", login, exc
                )
                continue

            if not repos:
                logger.info("[Agent] '{}' has no repositories to process", login)
                continue

            repos = sorted(
                repos,
                key=lambda repo: repo.get("stargazers_count", 0),
                reverse=True,
            )
            repos = repos[:max_repos_per_user]

            logger.info(
                "[Agent] Digging deeper for '{}': enriching {} repositories",
                login,
                len(repos),
            )
            enriched = self.repo_extractor.enrich_repositories(repos)

            collected_users.append(user_details)
            collected_repos.extend(enriched)

        deduped_repos: "OrderedDict[int, dict]" = OrderedDict()
        for repo in collected_repos:
            repo_id = repo.get("id")
            if repo_id is None:
                continue
            previous = deduped_repos.get(repo_id)
            if not previous or repo.get("stargazers_count", 0) >= previous.get(
                "stargazers_count", 0
            ):
                deduped_repos[repo_id] = repo

        final_repos = list(deduped_repos.values())
        final_repos.sort(key=lambda repo: repo.get("stargazers_count", 0), reverse=True)
        final_repos = final_repos[:target_repositories]

        final_owners = {repo.get("owner", {}).get("login") for repo in final_repos}
        final_owners.discard(None)
        final_users = [user for user in collected_users if user.get("login") in final_owners]

        logger.info(
            "[Agent] Collection finished: users={}, repos={}",
            len(final_users),
            len(final_repos),
        )

        return {
            "users": final_users,
            "repositories": final_repos,
            "summary": {
                "seed_users": len(unique_seed),
                "collected_users": len(final_users),
                "collected_repositories": len(final_repos),
            },
        }

    def _should_dig_deeper(
        self,
        user_details: dict,
        min_followers_to_dig: int,
        min_public_repos_to_dig: int,
    ) -> tuple[bool, str]:
        followers = user_details.get("followers", 0)
        public_repos = user_details.get("public_repos", 0)
        location = (user_details.get("location") or "").lower()

        if "peru" in location:
            return True, "location contains Peru"
        if followers >= min_followers_to_dig:
            return True, f"followers >= {min_followers_to_dig}"
        if public_repos >= min_public_repos_to_dig:
            return True, f"public_repos >= {min_public_repos_to_dig}"
        return False, "low followers and low public repo count"
