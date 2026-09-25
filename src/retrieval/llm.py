from __future__ import annotations

from core.config import Settings, normalized_provider, require_llm_credentials


def build_llm(settings: Settings, temperature: float = 0.0):
    provider = normalized_provider(settings)
    require_llm_credentials(settings)

    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=settings.model_name,
            google_api_key=settings.google_api_key,
            temperature=temperature,
        )
    if provider in ("openai", "openrouter", "custom"):
        from langchain_openai import ChatOpenAI

        if provider == "openai":
            return ChatOpenAI(
                model=settings.model_name,
                api_key=settings.openai_api_key,
                temperature=temperature,
            )
        if provider == "openrouter":
            return ChatOpenAI(
                model=settings.model_name,
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                temperature=temperature,
            )
        return ChatOpenAI(
            model=settings.model_name,
            api_key=settings.custom_llm_api_key or "unused",
            base_url=settings.custom_llm_base_url,
            temperature=temperature,
        )
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=settings.model_name,
            api_key=settings.anthropic_api_key,
            temperature=temperature,
        )
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=settings.model_name,
            base_url=settings.ollama_base_url,
            temperature=temperature,
        )
    if provider == "mock":
        try:
            from langchain_core.language_models.fake_chat_models import FakeListChatModel

            return FakeListChatModel(
                responses=["This is a mock response from the scholarly corpus."]
            )
        except Exception:
            # Minimal stub neu thieu langchain_core: _judge_answer se fallback heuristic
            class _Stub:
                def with_structured_output(self, *a, **k):
                    raise RuntimeError("mock LLM unavailable (langchain_core missing)")

            return _Stub()
    raise RuntimeError(f"Unsupported LLM provider: {settings.llm_provider}")
