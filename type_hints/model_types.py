from typing import Dict
from pydantic import BaseModel, Field
from typing import Literal


class ProviderPricing(BaseModel):
    input_per_million: float = Field(..., description="Price per 1,000,000 input tokens in USD")
    output_per_million: float = Field(..., description="Price per 1,000,000 output tokens in USD")

    def cost(self, input_tokens: int, output_tokens: int) -> float:
        input_cost = (input_tokens / 1_000_000) * self.input_per_million
        output_cost = (output_tokens / 1_000_000) * self.output_per_million
        return round(input_cost + output_cost, 6)


class ModelPricingInfo(BaseModel):
    model: str
    provider: Literal["openai", "anthropic", "google", "deepseek"]
    pricing: ProviderPricing

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        return self.pricing.cost(input_tokens, output_tokens)

MODEL_PRICING_REGISTRY: Dict[str, ModelPricingInfo] = {
    # --- OpenAI ---
    "gpt-4o": ModelPricingInfo(
        model="gpt-4o",
        provider="openai",
        pricing=ProviderPricing(
            input_per_million=2.50,
            output_per_million=10.00
        )
    ),
    "gpt-4o-mini": ModelPricingInfo(
        model="gpt-4o-mini",
        provider="openai",
        pricing=ProviderPricing(
            input_per_million=0.15,
            output_per_million=0.60
        )
    ),
    "gpt-4.1-mini": ModelPricingInfo(
        model="gpt-4.1-mini",
        provider="openai",
        pricing=ProviderPricing(
            input_per_million=0.40,
            output_per_million=1.60
        )
    ),
    "gpt-4.1": ModelPricingInfo(
        model="gpt-4.1",
        provider="openai",
        pricing=ProviderPricing(
            input_per_million=2.00,
            output_per_million=8.00
        )
    ),
    "gpt-4.1-nano": ModelPricingInfo(
        model="gpt-4.1-nano",
        provider="openai",
        pricing=ProviderPricing(
            input_per_million=0.1,
            output_per_million=0.4
        )
    ),
    # --- DeepSeek ---
    "deepseek-chat": ModelPricingInfo(
        model="deepseek-chat",
        provider="deepseek",
        pricing=ProviderPricing(
            input_per_million=0.27,
            output_per_million=1.1
        )
    ),
    # --- DeepSeek ---
    "deepseek-reasoner": ModelPricingInfo(
        model="deepseek-reasoner",
        provider="deepseek",
        pricing=ProviderPricing(
            input_per_million=0.55,
            output_per_million=2.19
        )
    )
}
