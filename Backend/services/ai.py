import base64
import json
import httpx
from typing import List
from utils.config import GEMINI_API_KEY, VISION_MODEL

def encode_image_to_base64(image_path: str) -> str:
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode("utf-8")

async def extract_filters(screenshot_path: str) -> List[str]:
    """Uses Gemini Flash API to dynamically find filter names on the dashboard.."""
    base64_image = encode_image_to_base64(screenshot_path)
    
    prompt = """
    Analyze this Power BI dashboard screenshot. Identify all top-level or side filter controls, slicers, and dropdowns.
    Return ONLY a JSON object containing a list of the exact visible string names under the "filters" key.
    Example: {"filters": ["Time Period", "Relative Time", "Recruiter Name"]}
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/{VISION_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt},
                    {
                        "inline_data": {
                            "mime_type": "image/png",
                            "data": base64_image
                        }
                    }
                ]
            }
        ],
        "generationConfig": {
            "response_mime_type": "application/json",
            "temperature": 0.1
        }
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        
        # Extract text response from Gemini output structure
        raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
        result = json.loads(raw_text)
        return result.get("filters", [])