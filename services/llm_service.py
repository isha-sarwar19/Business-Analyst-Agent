"""
services/llm_service.py — LLM invocation with fallback, retry, and full observability logging.

Extracted from agent/nodes.py. All LLM calls across the project go through here.
"""
import time
from langchain_openai import ChatOpenAI
from core.config import settings
from core.logging_config import get_logger

logger = get_logger(__name__)


def _make_llm(model_name: str) -> ChatOpenAI:
    """Instantiate a ChatOpenAI client pointing to OpenRouter."""
    if not settings.OPENROUTER_API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not set. Add it to your .env file."
        )
    return ChatOpenAI(
        model=model_name,
        api_key=settings.OPENROUTER_API_KEY,
        base_url=settings.OPENROUTER_BASE_URL,
        temperature=settings.TEMPERATURE,
        max_tokens=settings.MAX_TOKENS,
    )


def invoke_llm(messages: list) -> object:
    """
    Directly invoke the configured Llama model via OpenRouter.
    Simplified: No fallback mechanism as per requirements.
    """
    model = settings.MODEL_NAME
    logger.info("Invoking model: %s", model)
    t_start = time.time()

    try:
        llm = _make_llm(model)
        response = llm.invoke(messages)
        latency = time.time() - t_start

        # Extract token usage if available (OpenAI wrapper usually returns response_metadata)
        usage = getattr(response, "response_metadata", {}).get("token_usage", {})
        input_tokens  = usage.get("prompt_tokens", "n/a")
        output_tokens = usage.get("completion_tokens", "n/a")

        logger.info(
            "LLM success | model=%s | latency=%.2fs | input_tokens=%s | output_tokens=%s",
            model, latency, input_tokens, output_tokens
        )
        return response

    except Exception as e:
        latency = time.time() - t_start
        logger.error(
            "LLM error | model=%s | latency=%.2fs | error=%s",
            model, latency, str(e)[:200]
        )
        raise
