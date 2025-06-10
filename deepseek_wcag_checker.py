from openai import OpenAI
from pathlib import Path
import os
import json
import base64
import logging
from typing import List, Dict, Any, Optional
from type_hints.wcag_types import WCAGCheckResponse, Violation
from type_hints.model_types import MODEL_PRICING_REGISTRY
from model_context.wcag_rules import WCAG_RULES
logger = logging.getLogger(__name__)

class DeepSeekWCAGClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.deepseek.com",
        )
        self.model = "deepseek-chat"

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

        # Prepare system prompt
        system_prompt = system_instruction or (
            "You are a strict WCAG 2.2 accessibility auditor. Analyze the provided image and element list to identify accessibility violations. "
            "Focus on visual contrast, alt text, ARIA roles, and other WCAG 2.2 guidelines. "
            "Return your findings as a JSON object with this exact structure: "
            '{"violations": [{"id": "string", "description": "string", "impact": "string", "nodes": [{"html": "string", "target": ["string"], "failureSummary": "string"}]}], "reference": "string"}. '
            "In the reference field, explain whether you used the HTML elements or the input image to find the violations."
        )
        # system_prompt += f"\n\nHere is the WCAG 2.2 ruleset:\n\n{str(WCAG_RULES)}"
        # Prepare user content
        user_content = f"Here are the elements on the page:\n\n{json.dumps(elements, indent=2)}\n\nPlease analyze this webpage for WCAG 2.2 accessibility violations using both the provided HTML elements and the screenshot below."
        # Prepare messages
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        try:
            # Call DeepSeek API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages, #type: ignore
                response_format={
                    'type': 'json_object'
                },
                temperature=0.1,  # Low temperature for consistent results
                max_tokens=4000
            )

            # Parse the response
            content = response.choices[0].message.content
            if not content:
                raise RuntimeError("Empty response from DeepSeek")
            
            # Parse JSON response
            parsed_response = json.loads(content)
            
            # Convert to WCAGCheckResponse format
            wcag_response = WCAGCheckResponse(**parsed_response)
            
            # Log usage if available
            if hasattr(response, 'usage') and response.usage:
                input_tokens = response.usage.prompt_tokens
                output_tokens = response.usage.completion_tokens
                cost = MODEL_PRICING_REGISTRY[self.model].calculate_cost(input_tokens, output_tokens)
                logger.info(f"Cost: ${cost:.6f}")
            
            return wcag_response.violations
            
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse JSON response: {e}")
        except Exception as e:
            raise RuntimeError(f"Failed to get response from DeepSeek: {e}")