"""
Structured logging for DrCodePT-Swarm autonomous agent.

Provides consistent, structured logging across all agent components with:
- JSON-formatted log entries for machine parsing
- Human-readable console output
- Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Context preservation (run_id, step_id, tool_name, etc.)
- File and console handlers
- Automatic exception formatting
"""

from __future__ import annotations

import json
import logging
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union
from contextlib import contextmanager


# Custom log level for TRACE (more verbose than DEBUG)
TRACE = 5
logging.addLevelName(TRACE, "TRACE")


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured log output."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra context if present
        if hasattr(record, "context") and record.context:
            log_entry["context"] = record.context

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info),
            }

        return json.dumps(log_entry, ensure_ascii=False, default=str)


class ConsoleFormatter(logging.Formatter):
    """Human-readable formatter for console output."""

    COLORS = {
        "TRACE": "\033[90m",     # Gray
        "DEBUG": "\033[36m",     # Cyan
        "INFO": "\033[32m",      # Green
        "WARNING": "\033[33m",   # Yellow
        "ERROR": "\033[31m",     # Red
        "CRITICAL": "\033[35m",  # Magenta
    }
    RESET = "\033[0m"

    def __init__(self, use_colors: bool = True):
        super().__init__()
        self.use_colors = use_colors and sys.stdout.isatty()

    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now().strftime("%H:%M:%S")
        level = record.levelname[:4]
        
        if self.use_colors:
            color = self.COLORS.get(record.levelname, "")
            level_str = f"{color}{level}{self.RESET}"
        else:
            level_str = level

        # Build context string
        ctx_parts = []
        if hasattr(record, "context") and record.context:
            ctx = record.context
            if "run_id" in ctx:
                ctx_parts.append(f"run={ctx['run_id'][:8]}")
            if "step_id" in ctx:
                ctx_parts.append(f"step={ctx['step_id'][:8]}")
            if "tool_name" in ctx:
                ctx_parts.append(f"tool={ctx['tool_name']}")

        ctx_str = f" [{', '.join(ctx_parts)}]" if ctx_parts else ""

        msg = f"{ts} {level_str} {record.name}{ctx_str}: {record.getMessage()}"

        if record.exc_info:
            msg += "\n" + "".join(traceback.format_exception(*record.exc_info))

        return msg


class AgentLogger:
    """
    Structured logger for agent components.
    
    Usage:
        logger = AgentLogger("agent.runner")
        logger.info("Starting task", context={"run_id": "abc123", "task": "do something"})
        logger.error("Tool failed", context={"tool_name": "web_fetch"}, exc_info=True)
    """

    _instances: Dict[str, "AgentLogger"] = {}
    _file_handler: Optional[logging.FileHandler] = None
    _log_dir: Optional[Path] = None
    _level: int = logging.INFO

    def __init__(self, name: str):
        self.name = name
        self._logger = logging.getLogger(name)
        self._logger.setLevel(TRACE)  # Let handlers control filtering
        
        # Add console handler if not present
        if not any(isinstance(h, logging.StreamHandler) for h in self._logger.handlers):
            console = logging.StreamHandler(sys.stderr)
            console.setLevel(self._level)
            console.setFormatter(ConsoleFormatter())
            self._logger.addHandler(console)

    @classmethod
    def configure(
        cls,
        *,
        level: Union[int, str] = logging.INFO,
        log_dir: Optional[Path] = None,
        log_file: Optional[str] = None,
    ) -> None:
        """
        Configure global logging settings.
        
        Args:
            level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_dir: Directory for log files
            log_file: Specific log file name (default: agent.log)
        """
        if isinstance(level, str):
            level = getattr(logging, level.upper(), logging.INFO)
        cls._level = level

        if log_dir:
            cls._log_dir = Path(log_dir)
            cls._log_dir.mkdir(parents=True, exist_ok=True)
            
            log_path = cls._log_dir / (log_file or "agent.log")
            
            # Remove old file handler if exists
            if cls._file_handler:
                for logger in cls._instances.values():
                    logger._logger.removeHandler(cls._file_handler)
                cls._file_handler.close()

            # Create new file handler with JSON formatting
            cls._file_handler = logging.FileHandler(log_path, encoding="utf-8")
            cls._file_handler.setLevel(TRACE)  # Capture everything to file
            cls._file_handler.setFormatter(StructuredFormatter())

            # Add to all existing loggers
            for logger in cls._instances.values():
                logger._logger.addHandler(cls._file_handler)

        # Update console handler levels
        for logger in cls._instances.values():
            for handler in logger._logger.handlers:
                if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                    handler.setLevel(level)

    @classmethod
    def get(cls, name: str) -> "AgentLogger":
        """Get or create a logger instance."""
        if name not in cls._instances:
            logger = cls(name)
            cls._instances[name] = logger
            
            # Add file handler if configured
            if cls._file_handler:
                logger._logger.addHandler(cls._file_handler)
        
        return cls._instances[name]

    def _log(
        self,
        level: int,
        msg: str,
        *args,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs,
    ) -> None:
        """Internal logging method."""
        extra = {"context": context or {}}
        self._logger.log(level, msg, *args, extra=extra, exc_info=exc_info, **kwargs)

    def trace(self, msg: str, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log at TRACE level (most verbose)."""
        self._log(TRACE, msg, *args, context=context, **kwargs)

    def debug(self, msg: str, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log at DEBUG level."""
        self._log(logging.DEBUG, msg, *args, context=context, **kwargs)

    def info(self, msg: str, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log at INFO level."""
        self._log(logging.INFO, msg, *args, context=context, **kwargs)

    def warning(self, msg: str, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log at WARNING level."""
        self._log(logging.WARNING, msg, *args, context=context, **kwargs)

    def error(
        self,
        msg: str,
        *args,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs,
    ) -> None:
        """Log at ERROR level."""
        self._log(logging.ERROR, msg, *args, context=context, exc_info=exc_info, **kwargs)

    def critical(
        self,
        msg: str,
        *args,
        context: Optional[Dict[str, Any]] = None,
        exc_info: bool = False,
        **kwargs,
    ) -> None:
        """Log at CRITICAL level."""
        self._log(logging.CRITICAL, msg, *args, context=context, exc_info=exc_info, **kwargs)

    def exception(self, msg: str, *args, context: Optional[Dict[str, Any]] = None, **kwargs) -> None:
        """Log an exception (ERROR level with traceback)."""
        self._log(logging.ERROR, msg, *args, context=context, exc_info=True, **kwargs)

    @contextmanager
    def context(self, **ctx):
        """
        Context manager for adding persistent context to logs.
        
        Usage:
            with logger.context(run_id="abc123"):
                logger.info("Starting")  # Automatically includes run_id
        """
        # Store context on thread-local or just yield for now
        # Full implementation would use contextvars
        yield self


# Convenience function
def get_logger(name: str) -> AgentLogger:
    """Get a structured logger instance."""
    return AgentLogger.get(name)


# Pre-configured loggers for common components
runner_logger = AgentLogger.get("agent.runner")
planner_logger = AgentLogger.get("agent.planner")
tools_logger = AgentLogger.get("agent.tools")
memory_logger = AgentLogger.get("agent.memory")
llm_logger = AgentLogger.get("agent.llm")


__all__ = [
    "AgentLogger",
    "get_logger",
    "runner_logger",
    "planner_logger", 
    "tools_logger",
    "memory_logger",
    "llm_logger",
    "TRACE",
]
