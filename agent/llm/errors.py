from __future__ import annotations


class LLMError(RuntimeError):
    pass


class LLMConfigError(LLMError):
    pass


class LLMRetryableError(LLMError):
    pass


class LLMRateLimitError(LLMRetryableError):
    pass


class LLMProviderError(LLMError):
    pass


class LLMOutputError(LLMError):
    pass


class CodexCliError(LLMError):
    pass


class CodexCliNotFoundError(LLMConfigError):
    pass


class CodexCliAuthError(CodexCliError):
    pass


class CodexCliExecutionError(CodexCliError):
    pass


class CodexCliOutputError(CodexCliError, LLMOutputError):
    pass
