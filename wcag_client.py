import os
from typing import Union, Protocol, List, Dict, Any, Optional
from pathlib import Path
from type_hints.wcag_types import Violation
from type_hints.model_types import MODEL_PRICING_REGISTRY
from openai_wcag_checker import OpenAIWCAGClient
from deepseek_wcag_checker import DeepSeekWCAGClient
from dotenv import load_dotenv

load_dotenv()

class WCAGClientProtocol(Protocol):
    """Protocol defining the interface that all WCAG clients must implement."""
    
    def run_check(
        self,
        screenshot_path: Path,
        wcag_vector_id: str,
        elements: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
    ) -> List[Violation]:
        """Run WCAG accessibility check on the provided screenshot and elements."""
        ...


def get_wcag_client(model: str) -> WCAGClientProtocol:
    """
    Factory function to return the appropriate WCAG client based on the model name.
    
    Args:
        model: The model name (e.g., 'gpt-4o', 'deepseek-chat')
        
    Returns:
        An instance of the appropriate WCAG client
        
    Raises:
        ValueError: If the model is not supported
        EnvironmentError: If required API keys are missing
    """
    # Check if model exists in the pricing registry
    if model not in MODEL_PRICING_REGISTRY:
        available_models = list(MODEL_PRICING_REGISTRY.keys())
        raise ValueError(f"Unsupported model '{model}'. Available models: {available_models}")
    
    model_info = MODEL_PRICING_REGISTRY[model]
    
    if model_info.provider == "openai":
        # Validate OpenAI API key
        if not os.getenv("OPENAI_API_KEY"):
            raise EnvironmentError("OPENAI_API_KEY environment variable is required for OpenAI models")
        return OpenAIWCAGClient(model=model)
    
    elif model_info.provider == "deepseek":
        # Validate DeepSeek API key
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if not deepseek_key:
            raise EnvironmentError("DEEPSEEK_API_KEY environment variable is required for DeepSeek models")
        return DeepSeekWCAGClient(api_key=deepseek_key)
    
    else:
        raise ValueError(f"Provider '{model_info.provider}' is not yet supported")


class WCAGAIClient:
    """
    Main WCAG client class that automatically selects the appropriate provider
    based on the model name.
    """
    
    def __init__(self, model: str):
        """
        Initialize the WCAG client with the specified model.
        
        Args:
            model: The model name to use for WCAG checking
        """
        self.model = model
        self._client = get_wcag_client(model)
    
    def run_check(
        self,
        screenshot_path: Path,
        wcag_vector_id: str,
        elements: List[Dict[str, Any]],
        system_instruction: Optional[str] = None,
    ) -> List[Violation]:
        """
        Run WCAG accessibility check on the provided screenshot and elements.
        
        Args:
            screenshot_path: Path to the screenshot image
            wcag_vector_id: Vector store ID for WCAG rules (used by OpenAI)
            elements: List of HTML elements from the page
            system_instruction: Optional custom system instruction
            
        Returns:
            List of accessibility violations found
        """
        return self._client.run_check(
            screenshot_path=screenshot_path,
            wcag_vector_id=wcag_vector_id,
            elements=elements,
            system_instruction=system_instruction
        )
    
    @property
    def provider(self) -> str:
        """Get the provider name for the current model."""
        return MODEL_PRICING_REGISTRY[self.model].provider
    
    @classmethod
    def get_available_models(cls) -> List[str]:
        """Get a list of all available models."""
        return list(MODEL_PRICING_REGISTRY.keys())
    
    @classmethod
    def get_models_by_provider(cls, provider: str) -> List[str]:
        """Get all models for a specific provider."""
        return [
            model for model, info in MODEL_PRICING_REGISTRY.items()
            if info.provider == provider
        ] 