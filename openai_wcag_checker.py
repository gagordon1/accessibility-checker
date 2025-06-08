from openai import OpenAI
from pathlib import Path
import os
import json
import base64
from typing import List, Dict, Any, Optional
from type_hints.wcag_types import WCAGCheckResponse, Violation


class OpenAIWCAGClient:
    def __init__(self, api_key: Optional[str] = None):
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        self.client = OpenAI()
        self.model = "gpt-4o"

    def run_check(
        self,
        screenshot_path: Path,
        wcag_vector_id: str,
        elements: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
    ) -> List[Violation]:

        # Encode screenshot as base64
        with open(screenshot_path, "rb") as f:
            base64_image = base64.b64encode(f.read()).decode("utf-8")

        # Prepare input messages
        input_payload = [
            {
                "role": "system",
                "content": (
                    "Use the uploaded WCAG rules JSON to check this page for accessibility violations. "
                    "Focus on visual contrast, alt text, and ARIA roles."
                )
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": "Here are the elements on the page:\n\n" + json.dumps(elements)
                    },
                    {
                        "type": "input_text",
                        "text": "Here is the screenshot of the page:"
                    },
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{base64_image}"
                    }
                ]
            }
        ]


        # Call the Responses API
        response = self.client.responses.parse(
            model=self.model,
            input=input_payload,
            instructions=system_instruction or (
                "You are a strict WCAG 2.2 accessibility auditor. Analyze the image and element list. "
                "Use the uploaded WCAG rules file to guide your audit. "
                "Return a list of violations using this exact schema: "
                "[{id, description, impact?, nodes:[{html, target, failureSummary?}]}]"
            ),
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids" : [wcag_vector_id]
                 
                 },
                
                ],
            tool_choice="auto",
            text_format=WCAGCheckResponse
        )

        # Validate and parse the structured output
        try:
            content = response.output_parsed
            if not content:
                raise RuntimeError("Empty response from OpenAI")
            return content.violations
        except Exception as e:
            raise RuntimeError(f"Failed to parse response: {e}")
