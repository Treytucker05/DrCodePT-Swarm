from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional


def configure_logging(run_dir: Optional[Path] = None) -> None:
    root = logging.getLogger()
    if root.handlers:
        return
    root.setLevel(logging.DEBUG)

    fmt_file = logging.Formatter(
        "%(asctime)s %(levelname)s [%(name)s] %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )
    fmt_console = logging.Formatter("%(levelname)s %(message)s")

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(fmt_console)
    root.addHandler(console)

    for noisy in ("urllib3", "requests", "httpx", "openai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    if run_dir:
        run_dir.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(run_dir / "agent.log", encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt_file)
        root.addHandler(file_handler)
