import json
import logging
import base64
import time
from typing import Optional, Dict, Any
from google import genai
from google.genai import types
from google.genai.errors import APIError

from src.core.entities import SceneContext
from src.core.settings import SettingsManager

logger = logging.getLogger(__name__)

class GeminiClient:
    def __init__(self, settings: SettingsManager):
        self.settings = settings
        self.client = None
        self._init_client()

    def _init_client(self):
        if self.settings.gemini_api_key:
            try:
                self.client = genai.Client(api_key=self.settings.gemini_api_key)
                logger.info("Gemini client initialized successfully.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini client: {e}")
        else:
            logger.warning("GEMINI_API_KEY is not set. Deep AI features will be disabled.")

    def analyze_scene(self, image_bytes: bytes) -> Optional[SceneContext]:
        if not self.client:
            self._init_client()
            if not self.client:
                return None

        # Schema based on contracts/llm_schema.json
        response_schema = {
            "type": "OBJECT",
            "properties": {
                "scene_type": {"type": "STRING"},
                "lighting_condition": {"type": "STRING"},
                "recommended_iso": {"type": "INTEGER"},
                "recommended_shutter": {"type": "STRING"},
                "proactive_advice": {"type": "STRING"}
            },
            "required": [
                "scene_type", "lighting_condition", "recommended_iso", 
                "recommended_shutter", "proactive_advice"
            ]
        }

        try:
            start_time = time.time()
            response = self.client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type='image/jpeg'),
                    "Analyze this scene for photography. What is the context? Focus on lighting and action. Provide recommendations."
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=response_schema,
                    temperature=0.2,
                )
            )
            elapsed = time.time() - start_time
            logger.debug(f"Gemini API call took {elapsed:.2f}s")
            
            data = json.loads(response.text)
            
            return SceneContext(
                scene_type=data.get("scene_type", ""),
                lighting_condition=data.get("lighting_condition", ""),
                recommended_iso=data.get("recommended_iso", 0),
                recommended_shutter=data.get("recommended_shutter", ""),
                proactive_advice=data.get("proactive_advice", ""),
                confidence=0.9, # Mock confidence for now
                timestamp=time.time()
            )
        except APIError as e:
            err_str = str(e)
            import re
            match = re.search(r"Please retry in ([\d\.]+)s", err_str)
            if match:
                backoff_time = float(match.group(1)) + 1.0
                logger.warning(f"SceneContext rate limited. Backing off for {backoff_time:.2f}s...")
                time.sleep(backoff_time)
            elif "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                logger.warning(f"SceneContext rate limited (429). Backing off for 10.0s...")
                time.sleep(10.0)
            else:
                logger.error(f"Gemini API Error: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in analyze_scene: {e}")
        return None
