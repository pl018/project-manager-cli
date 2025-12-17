"""AI tagging service for the project manager CLI."""

import json
import logging
import re
from typing import Dict, Any, Optional, Tuple

import requests
from termcolor import colored

from core.config_manager import config as Config
from core.models import AIGeneratedInfo


class AITaggingService:
    """Service for generating AI tags based on project content."""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        
    def generate_tags(self, file_samples: Optional[Dict[str, str]]) -> Tuple[Optional[AIGeneratedInfo], Optional[Dict[str, Any]]]:
        """Uses OpenAI to generate tags, app name, and description based on file contents."""
        if not Config.OPENAI_API_KEY:
            self.logger.warning(colored("OpenAI API key not found. Set OPENAI_API_KEY in .env file to use AI tagging.", "yellow"))
            return None, None
            
        if not file_samples:
            return None, None
            
        try:
            # Prepare sample data for the API
            file_content_summary = "\n\n".join([f"Filename: {path}\n\n{content[:1000]}" 
                                              for path, content in file_samples.items()])
            
            # Prepare the API request
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {Config.OPENAI_API_KEY}"
            }
            
            payload = {
                "model": Config.OPENAI_MODEL,
                "messages": [
                    {
                        "role": "system", 
                        "content": (
                            "You analyze code repositories and output concise metadata. "
                            "Tag rules: one-word lowercase alphanumeric only (no spaces, hyphens, or punctuation), "
                            "no colon subcategories, keep tags minimal. Include up to one high-level category tag if appropriate "
                            "from this minimal set: app, cli, web, api, library, script, tool, data, ml, devops."
                        )
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Analyze these files and return ONLY a JSON object with:\n"
                            f"1. tags: 2-3 tags (each one word, lowercase alphanumeric), minimal and specific. "
                            f"Optionally include at most one category tag from: app, cli, web, api, library, script, tool, data, ml, devops.\n"
                            f"2. app_name: A suitable application name.\n"
                            f"3. app_description: One short sentence describing what it does.\n\n"
                            f"{file_content_summary}"
                        )
                    }
                ],
                "temperature": Config.OPENAI_MODEL_TEMPERATURE
            }
            
            self.logger.info(colored("Contacting OpenAI for AI-generated project information...", "cyan"))
            response = requests.post(Config.OPENAI_API_URL, headers=headers, json=payload, timeout=30)
            
            if response.status_code != 200:
                self.logger.warning(colored(f"OpenAI API Error: {response.status_code} - {response.text}", "yellow"))
                return None, None
                
            api_response = response.json()
            response_text = api_response["choices"][0]["message"]["content"].strip()
            
            try:
                # Debug the raw response
                self.logger.debug(f"Raw API response text: {response_text}")
                
                # Try to parse as JSON - be more generous with JSON parsing
                # First, try to find if there's a JSON block in the response
                json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                    self.logger.debug(f"Extracted JSON from markdown: {json_str}")
                    json_data = json.loads(json_str)
                else:
                    # Try to parse the whole response as JSON
                    json_data = json.loads(response_text)
                
                # Extract tags, app name and description from the response
                tags = json_data.get("tags", [])
                def _normalize(tag: str) -> str:
                    t = ''.join(ch for ch in str(tag).lower() if ch.isalnum())
                    return t
                if isinstance(tags, str):
                    tags = [t for t in (_normalize(tag) for tag in tags.split(',')) if t]
                else:
                    tags = [t for t in (_normalize(tag) for tag in tags) if t]
                
                # Limit to 3 tags
                tags = tags[:3]
                
                app_name = json_data.get("app_name")
                app_description = json_data.get("app_description")
                
                ai_info = AIGeneratedInfo(
                    tags=tags,
                    app_name=app_name,
                    app_description=app_description
                )
                
                self.logger.info(colored(f"✓ AI generated tags: {', '.join(tags)}", "green"))
                if app_name:
                    self.logger.info(colored(f"✓ AI generated app name: {app_name}", "green"))
                if app_description:
                    self.logger.info(colored(f"✓ AI generated description: {app_description}", "green"))
                    
                return ai_info, api_response
                
            except json.JSONDecodeError as e:
                # Fallback for non-JSON responses
                self.logger.warning(colored(f"AI response was not valid JSON: {str(e)}. Falling back to text parsing.", "yellow"))
                # Clean up the tags: split by comma and normalize to one-word alphanumeric
                def _normalize(tag: str) -> str:
                    t = ''.join(ch for ch in str(tag).lower() if ch.isalnum())
                    return t
                tags = [t for t in (_normalize(tag) for tag in response_text.split(',')) if t]
                
                # Limit to 3 tags
                tags = tags[:3]
                
                ai_info = AIGeneratedInfo(tags=tags)
                self.logger.info(colored(f"✓ AI generated tags: {', '.join(tags)}", "green"))
                
                return ai_info, api_response
                
        except Exception as e:
            self.logger.warning(colored(f"Error generating AI information: {str(e)}", "yellow"))
            return None, None 