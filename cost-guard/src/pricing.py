"""Model pricing tables and cost estimation."""

PRICING = {
    "claude-sonnet-4-20250514": {"input": 3.00, "output": 15.00},
    "claude-opus-4-20250514": {"input": 15.00, "output": 75.00},
    "claude-haiku-4-5-20251001": {"input": 0.25, "output": 1.25},
    "default": {"input": 3.00, "output": 15.00},
}


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using len/4 heuristic."""
    return max(1, len(text) // 4)


def estimate_cost(input_tokens: int, output_tokens: int, model: str = "default") -> float:
    """Estimate cost in USD."""
    prices = PRICING.get(model, PRICING["default"])
    return (input_tokens * prices["input"] + output_tokens * prices["output"]) / 1_000_000
