"""
Simple tool wrappers for ReAct agent
Bridges autonomous tools (which expect RunContext) to simple callables
"""


def web_search(query: str) -> str:
    """Search the web for information."""
    try:
        # Import the MCP web_search if available
        # (This is the one Claude uses in chat mode)
        import anthropic  # noqa: F401
        # Placeholder: wire real implementation later
        return f"[Would search web for: {query}]"
    except Exception:
        return "Web search not available"


def web_fetch(url: str) -> str:
    """Fetch content from a URL."""
    try:
        import anthropic  # noqa: F401
        return f"[Would fetch: {url}]"
    except Exception:
        return "Web fetch not available"


def read_file(path: str) -> str:
    """Read a file from disk."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as exc:
        return f"Error reading file: {exc}"


def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Wrote {len(content)} chars to {path}"
    except Exception as exc:
        return f"Error writing file: {exc}"

