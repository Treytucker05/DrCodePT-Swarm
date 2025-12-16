# Program Status Report

## Table of Contents
- [Summary](#summary)
- [Components](#components)
  - [fastmcp-server](#fastmcp-server)
  - [blackboard-automation](#blackboard-automation)
  - [anki-integration](#anki-integration)
  - [other](#other)
- [Startup and Config](#startup-and-config-scripts)

## Summary
- Total programs/files: 1806
- Working: 4 | Partial: 8 | Broken: 0 | Planned: 0 | Unknown: 1794
- Critical dependencies: Python 3.x, Uvicorn, ngrok (for public access), AnkiConnect (for Anki tools).
- Integration blockers: ChatGPT client caching (tools list), ensure AnkiConnect running for deck ops.

## Components
### fastmcp-server
| Path | Status | Last Modified | Description | Dependencies | Known Issues/TODOs |
| - | - | - | - | - | - |
| `fastmcp-server/_client_call_listAnkiDecks.py` | ❓ UNKNOWN | 2025-11-12 14:35 |  | asyncio, fastmcp |  |
| `fastmcp-server/_client_list_tools.py` | ❓ UNKNOWN | 2025-11-12 14:33 |  | asyncio, fastmcp |  |
| `fastmcp-server/_client_list_tools_ngrok.py` | ❓ UNKNOWN | 2025-11-12 14:34 |  | asyncio, fastmcp |  |
| `fastmcp-server/_client_list_tools2.py` | ❓ UNKNOWN | 2025-11-12 14:34 |  | asyncio, fastmcp |  |
| `fastmcp-server/_introspect_tools.py` | ❓ UNKNOWN | 2025-11-12 14:32 |  | server, sys |  |
| `fastmcp-server/adapters/__init__.py` | ❓ UNKNOWN | 2025-11-10 11:17 | Subject-agnostic adapters for ingesting study materials.
Each adapter converts raw content into normalized records. |  |  |
| `fastmcp-server/adapters/csv_adapter.py` | ⚠️ PARTIAL | 2025-11-10 11:17 | Parse CSV files into raw records.
Treats each row as structured data. | csv, pathlib |  |
| `fastmcp-server/adapters/pdf.py` | ⚠️ PARTIAL | 2025-11-10 11:17 | Parse PDF files into raw records.
Requires pypdf library. | pathlib, pypdf |  |
| `fastmcp-server/adapters/pptx.py` | ⚠️ PARTIAL | 2025-11-10 11:24 | Parse PowerPoint (PPTX) files into raw records.
Extracts text from slides including titles, shapes, and notes.
Requires python-pptx library. | pathlib, pptx |  |
| `fastmcp-server/adapters/txt.py` | ⚠️ PARTIAL | 2025-11-10 11:17 | Parse plain text files into raw records.
Splits by headings and markers. | pathlib |  |
| `fastmcp-server/addcardtodeck.py` | ❓ UNKNOWN | 2025-11-12 10:52 | addCardToDeck - Hybrid Anki Bridge (AnkiConnect API + File Fallback + Queue Retry)

Implements the HALF B specification with:
- Primary: AnkiConnect API (live Anki desktop update)
- Secondary: Fallback to deck.json file writes
- Tertiary: Queue to pending.json for retry if storage fails

Duplicate detection is PER-MODULE (not global). | datetime, hashlib, json, logging, os, pathlib, requests | L263: logger.debug(f"DUPLICATE_FOUND: {card_hash} in {deck_path}")
L306: logger.debug(f"ANKI_CONNECT_SUCCESS: noteId={result.get('result')}") |
| `fastmcp-server/aligner.py` | ⚠️ PARTIAL | 2025-11-10 11:35 | Align slide text to transcript windows using two-pass strategy:
1. Hard anchors: exact slide title strings in transcript
2. Fuzzy anchors: TF-IDF + cosine similarity on rolling window | collections, math |  |
| `fastmcp-server/anki_bridge.py` | ✅ WORKING | 2025-11-12 13:07 | Utility module that encapsulates Anki connectivity (AnkiConnect +
optional AnkiWeb placeholder) and telemetry logging for addCardToDeck. | __future__, dataclasses, datetime, json, os, pathlib, requests, time, typing |  |
| `fastmcp-server/config/courses.json` | ❓ UNKNOWN | 2025-11-10 11:16 | Configuration file |  |  |
| `fastmcp-server/entities.py` | ⚠️ PARTIAL | 2025-11-10 11:34 | Entity detection for anatomy materials.
Hybrid: whitelist + role patterns + context scoring. | dataclasses, re, typing |  |
| `fastmcp-server/index/__init__.py` | ❓ UNKNOWN | 2025-11-10 11:17 | Simple SQLite-based index for storing normalized records. | json, pathlib, sqlite3 |  |
| `fastmcp-server/manifest.yaml` | ❓ UNKNOWN | 2025-11-10 12:52 | Configuration file |  |  |
| `fastmcp-server/manifest_loader.py` | ⚠️ PARTIAL | 2025-11-10 12:52 | Load and resolve manifest.yaml with folder-based file discovery. | pathlib, typing, yaml |  |
| `fastmcp-server/modules/wk09_glute_postthigh/coverage.json` | ❓ UNKNOWN | 2025-11-10 12:55 | Configuration file |  |  |
| `fastmcp-server/ngrok.yml` | ✅ WORKING | 2025-11-12 14:09 | Configuration file |  |  |
| `fastmcp-server/normalizer/__init__.py` | ❓ UNKNOWN | 2025-11-10 11:17 | Normalize raw records into universal data model:
- Concept
- Fact
- Relation
- Figure
- Card | json, uuid |  |
| `fastmcp-server/server.py` | ✅ WORKING | 2025-11-12 13:51 | Advanced course-agnostic MCP Study Server with:
- Manifest-driven file discovery
- Entity detection from anatomy materials
- Transcript-to-slide alignment
- Two-source verification
- Multi-format export (Anki, JSONL, Markdown) | adapters, aligner, anki_bridge, dataclasses, entities, fastmcp, hashlib, index, json, manifest_loader, normalizer, os, pathlib, sqlite3, tempfile, uuid, verifier |  |
| `fastmcp-server/START_DRCODEPT.bat` | ✅ WORKING | 2025-11-12 14:16 | Windows startup script | Python, Uvicorn, Virtualenv |  |
| `fastmcp-server/test_addcardtodeck.py` | ❓ UNKNOWN | 2025-11-12 10:53 | Test suite for addCardToDeck hybrid bridge

Run with: pytest test_addcardtodeck.py -v -s | addcardtodeck, asyncio, json, os, pytest, shutil, sys |  |
| `fastmcp-server/test_anki_debug.py` | ❓ UNKNOWN | 2025-11-12 13:46 | Test script to debug Anki sync and verify card creation | json, server, sys | L3: Test script to debug Anki sync and verify card creation
L12: print("ANKI DEBUG TEST")
L32: print("[2] Creating test card in NEW deck: 'TestDeck_DrCodePT_Debug'")
L36: "course": "DEBUG",
L38: "deck": "TestDeck_DrCodePT_Debug",
L43: "source": "debug_test"
L59: print("[3] Retrieving cards from 'TestDeck_DrCodePT_Debug'")
L62: retrieve_result = _getCardsFromDeck_impl("TestDeck_DrCodePT_Debug")
L68: print(f"\nFound {card_count} card(s) in TestDeck_DrCodePT_Debug")
L78: print("\n⚠️  No cards found in TestDeck_DrCodePT_Debug")
L82: print("    This could be a bug in AnkiConnect or Anki sync issue.")
L87: print("END DEBUG TEST") |
| `fastmcp-server/test_app_structure.py` | ❓ UNKNOWN | 2025-11-12 14:20 |  | server, sys, traceback |  |
| `fastmcp-server/test_direct.py` | ❓ UNKNOWN | 2025-11-12 13:30 | Direct test of addCardToDeck function without MCP layer | json, server, sys, traceback |  |
| `fastmcp-server/test_minimal_app.py` | ❓ UNKNOWN | 2025-11-12 14:21 | Minimal test to see if @app.tool() decorator works"""
from fastmcp import FastMCP

app = FastMCP("TestApp")

@app.tool()
def test_tool_one() -> str: | fastmcp |  |
| `fastmcp-server/test_phase2c.py` | ❓ UNKNOWN | 2025-11-11 16:05 | Test script to verify Phase 2C: ChatGPT Bridge implementation
Tests all helper functions and the addCardToDeck tool | json, pathlib, server, sys |  |
| `fastmcp-server/test_tools_check.py` | ❓ UNKNOWN | 2025-11-12 14:12 |  | server, sys |  |
| `fastmcp-server/verifier.py` | ⚠️ PARTIAL | 2025-11-10 11:35 | Two-source verification: Fact must appear in BOTH slide + transcript
to be marked "verified". Four deterministic tiers. | dataclasses, typing |  |

### blackboard-automation
(none)

### anki-integration
(none)

### other
| Path | Status | Last Modified | Description | Dependencies | Known Issues/TODOs |
| - | - | - | - | - | - |
| `blackboard-agent/.env` | ❓ UNKNOWN | 2025-11-09 21:20 | Configuration file |  | L16: # MICROSOFT_TODO_TOKEN= |
| `blackboard-agent/agent.py` | ❓ UNKNOWN | 2025-11-10 07:56 | TREY'S PERSONAL AGENT v3.0 - Claude Tool Use Architecture
Conversational AI that knows what tools to use
You talk naturally. Claude figures out what to do. | datetime, handlers, json, os, pathlib, sys |  |
| `blackboard-agent/claude_tools.py` | ❓ UNKNOWN | 2025-11-10 00:01 | Claude Tool Definitions for Dr. CodePT
Provides tool wrappers around BlackboardHandler for Claude to call | datetime, handlers, json, sys, typing |  |
| `blackboard-agent/computer_use/__init__.py` | ❓ UNKNOWN | 2025-11-10 10:31 |  |  |  |
| `blackboard-agent/computer_use/computer_automation.py` | ❓ UNKNOWN | 2025-11-10 08:04 | Computer Use Automation - Direct pyautogui control for Microsoft To Do
Simple automation without Computer Use API - just direct mouse/keyboard control | datetime, os, pyautogui, time | L26: def add_tasks_to_microsoft_todo(self, tasks, list_name="PT School"): |
| `blackboard-agent/computer_use/file_manager.py` | ❓ UNKNOWN | 2025-11-10 07:30 | File Manager - Handles file download and organization for PT School materials | datetime, json, os, pathlib, re, shutil |  |
| `blackboard-agent/computer_use/microsoft_integration.py` | ❓ UNKNOWN | 2025-11-10 14:26 | Microsoft To Do automation - robust attach/launch with retry"""
import re
import time
import subprocess
import json
import sqlite3
import threading
from pathlib import Path
from pywinauto import Application, Desktop
from pywinauto.keyboard import send_keys
from pywinauto.timings import wait_until, TimeoutError

CONFIG_PATH = Path(__file__).parent.parent / "config" / "todo_selectors.json"
with open(CONFIG_PATH) as f:
    CONFIG = json.load(f)

AUMID = CONFIG.get("aumid", "Microsoft.Todos_8wekyb3d8bbwe!App")
HOST_CLASS = "ApplicationFrameWindow"
# Prefer repo-configured matcher; fall back to a broad pattern
TITLE_RE = CONFIG.get("window_title_re") or r"^(Microsoft )?To Do.*\\|.*- To Do$"


class OpStore:
    def __init__(self, db_path="opstore.db"):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._init_db()
    
    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute( | json, pathlib, pywinauto, re, sqlite3, subprocess, threading, time | L13: CONFIG_PATH = Path(__file__).parent.parent / "config" / "todo_selectors.json"
L17: AUMID = CONFIG.get("aumid", "Microsoft.Todos_8wekyb3d8bbwe!App")
L57: def _find_todo_window(timeout=45):
L85: def _get_todo_window():
L119: return _find_todo_window(timeout=15)
L137: frame = _get_todo_window() |
| `blackboard-agent/config/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:06 | Empty __init__.py for config package |  |  |
| `blackboard-agent/config/settings.py` | ❓ UNKNOWN | 2025-11-09 19:06 | Configuration for Agent | dotenv, os |  |
| `blackboard-agent/config/todo_selectors.json` | ❓ UNKNOWN | 2025-11-10 10:43 | Configuration file |  | L6: "aumid": "Microsoft.Todos_8wekyb3d8bbwe!App" |
| `blackboard-agent/handlers/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:23 | Handlers for Agent |  |  |
| `blackboard-agent/handlers/blackboard_handler.py` | ❓ UNKNOWN | 2025-11-09 23:35 | Blackboard Handler - Web scraping with Selenium
Handles login, course access, announcements, modules, and file downloads | datetime, dotenv, json, os, pathlib, selenium, time, webdriver_manager | L144: # Take screenshot for debugging |
| `blackboard-agent/handlers/claude_handler.py` | ❓ UNKNOWN | 2025-11-10 16:05 | Claude Handler v2 - Tool Use Architecture
Claude as the core brain, orchestrating all handlers via Tool Use API | , anthropic, computer_use, datetime, dotenv, json, os, sys, typing | L302: "name": "placeholder_todo",
L338: # TODO: These will be connected to real handlers in later phases |
| `blackboard-agent/handlers/file_handler.py` | ❓ UNKNOWN | 2025-11-09 19:07 | File System Handler - Handle all file operations | datetime, json, os, pathlib, shutil, typing |  |
| `blackboard-agent/handlers/process_handler.py` | ❓ UNKNOWN | 2025-11-09 19:08 | Process Handler - Handle command execution and process management | datetime, os, subprocess, sys, typing |  |
| `blackboard-agent/handlers/state_manager.py` | ❓ UNKNOWN | 2025-11-09 20:07 | State Manager - Handle agent state and history persistence | datetime, json, pathlib, typing |  |
| `blackboard-agent/handlers/web_handler.py` | ❓ UNKNOWN | 2025-11-09 20:04 | Web Handler - Handle web search and URL fetching | bs4, datetime, os, requests, typing |  |
| `blackboard-agent/venv/Lib/site-packages/annotated_types/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Base class for all metadata.

    This exists mainly so that implementers
    can do `isinstance(..., BaseMetadata)` while traversing field annotations. | dataclasses, datetime, math, sys, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/annotated_types/test_cases.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A test case for `annotated_types`. | annotated_types, datetime, decimal, math, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_base_client.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Stores the necessary information to build the request to retrieve the next page.

    Either `url` or `params` must be set. | , __future__, anyio, asyncio, distro, email, httpx, inspect, json, logging, platform, pydantic, random, socket, sys, time, types, typing, typing_extensions, uuid | L94: # TODO: make base page type vars covariant
L197: # TODO: do we have to preprocess params here?
L492: if log.isEnabledFor(logging.DEBUG):
L493: log.debug("Request options: %s", model_dump(options, exclude_unset=True)) |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_client.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Construct a new synchronous Anthropic client instance.

        This automatically infers the following arguments from their corresponding environment variables if they are not provided:
        - `api_key` from `ANTHROPIC_API_KEY`
        - `auth_token` from `ANTHROPIC_AUTH_TOKEN` | , __future__, httpx, os, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_compat.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, datetime, functools, pydantic, pydantic_core, typing, typing_extensions | L73: # TODO: provide an error message here? |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_constants.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | httpx |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_decoders/jsonl.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A decoder for [JSON Lines](https://jsonlines.org) format.

    This class provides an iterator over a byte-iterator that parses each JSON Line
    into a given type. | , __future__, httpx, json, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The API response body.

    If the API responded with a valid JSON structure then this property will be the
    decoded result.

    If it isn't a valid JSON structure then this will be the raw response.

    If there was no response associated with this error then it will be `None`. | __future__, httpx, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_files.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, anyio, io, os, pathlib, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_legacy_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This is a legacy class as it will be replaced by `APIResponse`
    and `AsyncAPIResponse` in the `_response.py` file in the next major
    release.

    For the sync client this will mostly be the same with the exception
    of `content` & `text` will be methods instead of properties. In the
    async client, all methods will be async.

    A migration script will be provided & the migration in general should
    be smooth. | , __future__, anthropic, anyio, datetime, functools, httpx, inspect, logging, os, pydantic, typing, typing_extensions | L335: log.debug("Could not read JSON from response data due to %s - %s", type(exc), exc)
L466: "Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used instead"
L497: "Due to a bug, this method doesn't actually stream the response content, `.with_streaming_response.method()` should be used instead" |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_models.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The ID of the request, returned via the `request-id` header. Useful for debugging requests and reporting issues to Anthropic.
        This will **only** be set for the top-level response object, it will not be defined for nested objects. For example:
        
        ```py
        message = await client.messages.create(...)
        message._request_id  # req_xxx
        message.usage._request_id  # raises `AttributeError`
        ```

        Note: unlike other properties that use an `_` prefix, this property
        *is* public. Unless documented otherwise, all other `_` prefix properties,
        methods and modules are *private*. | , __future__, datetime, inspect, os, pydantic, pydantic_core, typing, typing_extensions | L101: """The ID of the request, returned via the `request-id` header. Useful for debugging requests and reporting issues to Anthropic.
L401: # TODO |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_qs.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions, urllib | L81: # TODO: error if unknown format |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_resource.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, anyio, time |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The number of retries made. If no retries happened this will be `0`"""

    def __init__(
        self,
        *,
        raw: httpx.Response,
        cast_to: type[R],
        client: BaseClient[Any, Any],
        stream: bool,
        stream_cls: type[Stream[Any]] \\| type[AsyncStream[Any]] \\| None,
        options: FinalRequestOptions,
        retries_taken: int = 0,
    ) -> None:
        self._cast_to = cast_to
        self._client = client
        self._parsed_by_type = {}
        self._is_sse_stream = stream
        self._stream_cls = stream_cls
        self._options = options
        self.http_response = raw
        self.retries_taken = retries_taken

    @property
    def headers(self) -> httpx.Headers:
        return self.http_response.headers

    @property
    def http_request(self) -> httpx.Request: | , __future__, anyio, datetime, functools, httpx, inspect, logging, os, pydantic, types, typing, typing_extensions | L269: log.debug("Could not read JSON from response data due to %s - %s", type(exc), exc) |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_streaming.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Provides the core interface to iterate over a synchronous stream response."""

    response: httpx.Response

    _decoder: SSEBytesDecoder

    def __init__(
        self,
        *,
        cast_to: type[_T],
        response: httpx.Response,
        client: Anthropic,
    ) -> None:
        self.response = response
        self._cast_to = cast_to
        self._client = client
        self._decoder = client._make_sse_decoder()
        self._iterator = self.__stream__()

    def __next__(self) -> _T:
        return self._iterator.__next__()

    def __iter__(self) -> Iterator[_T]:
        for item in self._iterator:
            yield item

    def _iter_events(self) -> Iterator[ServerSentEvent]:
        yield from self._decoder.iter_bytes(self.response.iter_bytes())

    def __stream__(self) -> Iterator[_T]:
        cast_to = cast(Any, self._cast_to)
        response = self.response
        process_data = self._client._process_response_data
        iterator = self._iter_events()

        for sse in iterator:
            if sse.event == "completion":
                yield process_data(data=sse.json(), cast_to=cast_to, response=response)

            if (
                sse.event == "message_start"
                or sse.event == "message_delta"
                or sse.event == "message_stop"
                or sse.event == "content_block_start"
                or sse.event == "content_block_delta"
                or sse.event == "content_block_stop"
            ):
                data = sse.json()
                if is_dict(data) and "type" not in data:
                    data["type"] = sse.event

                yield process_data(data=data, cast_to=cast_to, response=response)

            if sse.event == "ping":
                continue

            if sse.event == "error":
                body = sse.data

                try:
                    body = sse.json()
                    err_msg = f"{body}"
                except Exception:
                    err_msg = sse.data or f"Error code: {response.status_code}"

                raise self._client._make_status_error(
                    err_msg,
                    body=body,
                    response=self.response,
                )

        # Ensure the entire stream is consumed
        for _sse in iterator:
            ...

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] \\| None,
        exc: BaseException \\| None,
        exc_tb: TracebackType \\| None,
    ) -> None:
        self.close()

    def close(self) -> None: | , __future__, abc, httpx, inspect, json, types, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | For parameters with a meaningful None value, we need to distinguish between
    the user explicitly passing None, and the user not passing the parameter at
    all.

    User code shouldn't need to use not_given directly.

    For example:

    ```py
    def create(timeout: Timeout \\| None \\| NotGiven = not_given): ...


    create(timeout=1)  # 1s timeout
    create(timeout=None)  # No timeout
    create()  # Default timeout behavior
    ``` | , __future__, httpx, os, pydantic, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_compat.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, datetime, sys, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_datetime_parse.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This file contains code from https://github.com/pydantic/pydantic/blob/main/pydantic/v1/datetime_parse.py
without the Pydantic v1 specific errors. | , __future__, datetime, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_httpx.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This file includes code adapted from HTTPX's utility module
(https://github.com/encode/httpx/blob/336204f0121a9aefdebac5cacd81f912bafe8057/httpx/_utils.py).
We implement custom proxy handling to support configurations like `socket_options`,
which are not currently configurable through the HTTPX client.
For more context, see: https://github.com/encode/httpx/discussions/3514 | __future__, ipaddress, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_logs.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | logging, os | L9: # e.g. [2023-10-05 14:12:26 - anthropic._base_client:818 - DEBUG] HTTP Request: POST http://127.0.0.1:4010/foo/bar "200 OK"
L18: if env == "debug":
L20: logger.setLevel(logging.DEBUG)
L21: httpx_logger.setLevel(logging.DEBUG) |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_proxy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Implements data methods to pretend that an instance is another instance.

    This includes forwarding attribute access and other methods. | __future__, abc, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_reflection.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Returns whether or not the given function has a specific parameter"""
    sig = inspect.signature(func)
    return arg_name in sig.parameters


def assert_signatures_in_sync(
    source_func: Callable[..., Any],
    check_func: Callable[..., Any],
    *,
    exclude_params: set[str] = set(),
) -> None: | __future__, inspect, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_resources_proxy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A proxy for the `anthropic.resources` module.

    This is used so that we can lazily import `anthropic.resources` only when
    needed *and* so that users can just import `anthropic` and reference `anthropic.resources` | , __future__, importlib, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_streams.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_sync.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Asynchronously run function *func* in a separate thread.

        Any *args and **kwargs supplied for this function are directly passed
        to *func*. Also, the current :class:`contextvars.Context` is propagated,
        allowing context variables from the main thread to be accessed in the
        separate thread.

        Returns a coroutine that can be awaited to get the eventual result of *func*. | __future__, anyio, asyncio, contextvars, functools, sniffio, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_transform.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Metadata class to be used in Annotated types to provide information about a given type.

    For example:

    class MyParams(TypedDict):
        account_holder_name: Annotated[str, PropertyInfo(alias='accountHolderName')]

    This means that {'account_holder_name': 'Robert'} will be transformed to {'accountHolderName': 'Robert'} before being sent to the API. | , __future__, anyio, base64, datetime, io, pathlib, pydantic, typing, typing_extensions | L37: # TODO: support for drilling globals() and locals()
L38: # TODO: ensure works correctly with forward references in all cases
L214: # TODO: there may be edge cases where the same normalized field name will transform to two different names
L380: # TODO: there may be edge cases where the same normalized field name will transform to two different names |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_typing.py` | ❓ UNKNOWN | 2025-11-09 21:03 | If the given type is `typing.Iterable[T]`"""
    origin = get_origin(typ) or typ
    return origin == Iterable or origin == _c_abc.Iterable


def is_union_type(typ: type) -> bool:
    return _is_union(get_origin(typ))


def is_required_type(typ: type) -> bool:
    return get_origin(typ) == Required


def is_typevar(typ: type) -> bool:
    # type ignore is required because type checkers
    # think this expression will always return False
    return type(typ) == TypeVar  # type: ignore


_TYPE_ALIAS_TYPES: tuple[type[typing_extensions.TypeAliasType], ...] = (typing_extensions.TypeAliasType,)
if sys.version_info >= (3, 12):
    _TYPE_ALIAS_TYPES = (*_TYPE_ALIAS_TYPES, typing.TypeAliasType)


def is_type_alias_type(tp: Any, /) -> TypeIs[typing_extensions.TypeAliasType]: | , __future__, collections, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_utils/_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Recursively extract files from the given dictionary based on specified paths.

    A path may look like this ['foo', 'files', '<array>', 'data'].

    Note: this mutates the given dictionary. | , __future__, datetime, functools, inspect, os, pathlib, re, sniffio, typing, typing_extensions | L38: # TODO: this needs to take Dict but variance issues.....
L275: # TODO: this error message is not deterministic |
| `blackboard-agent/venv/Lib/site-packages/anthropic/_version.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/_extras/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/_extras/_common.py` | ❓ UNKNOWN | 2025-11-09 21:03 | class MissingDependencyError(AnthropicError):
    def __init__(self, *, library: str, extra: str) -> None:
        super().__init__(INSTRUCTIONS.format(library=library, extra=extra)) |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/_extras/_google_auth.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, google, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/_files.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, anyio, os, pathlib |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/_auth.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, boto3, botocore, httpx, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/_beta.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return the
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/_beta_messages.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return the
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/_client.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Infer the AWS region from the environment variables or
    from the boto3 session if available. | , __future__, boto3, httpx, logging, os, typing, typing_extensions, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/_stream.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, httpx, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/bedrock/_stream_decoder.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Given an iterator that yields lines, iterate over it & yield every event encountered"""
        from botocore.eventstream import EventStreamBuffer

        event_stream_buffer = EventStreamBuffer()
        for chunk in iterator:
            event_stream_buffer.add_data(chunk)
            for event in event_stream_buffer:
                message = self._parse_message_from_event(event)
                if message:
                    yield ServerSentEvent(data=message, event="completion")

    async def aiter_bytes(self, iterator: AsyncIterator[bytes]) -> AsyncIterator[ServerSentEvent]: | , __future__, botocore, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/streaming/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/streaming/_beta_messages.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Iterator over just the text deltas in the stream.

    ```py
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()
    ``` | , __future__, anthropic, httpx, pydantic, types, typing, typing_extensions | L432: # TODO: check index |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/streaming/_beta_types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The text delta"""

    snapshot: str | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/streaming/_messages.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Iterator over just the text deltas in the stream.

    ```py
    for text in stream.text_stream:
        print(text, end="", flush=True)
    print()
    ``` | , __future__, anthropic, httpx, pydantic, types, typing, typing_extensions | L427: # TODO: check index |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/streaming/_types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The text delta"""

    snapshot: str | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/tools/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/tools/_beta_builtin_memory_tool.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Abstract base class for memory tool implementations.

    This class provides the interface for implementing a custom memory backend for Claude.

    Subclass this to create your own memory storage solution (e.g., database, cloud storage, encrypted files, etc.).

    Example usage:

    ```py
    class MyMemoryTool(BetaAbstractMemoryTool):
        def view(self, command: BetaMemoryTool20250818ViewCommand) -> BetaFunctionToolResultType:
            ...
            return "view result"

        def create(self, command: BetaMemoryTool20250818CreateCommand) -> BetaFunctionToolResultType:
            ...
            return "created successfully"

        # ... implement other abstract methods


    client = Anthropic()
    memory_tool = MyMemoryTool()
    message = client.beta.messages.run_tools(
        model="claude-sonnet-4-5",
        messages=[{"role": "user", "content": "Remember that I like coffee"}],
        tools=[memory_tool],
    ).until_done()
    ``` | , __future__, abc, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/tools/_beta_functions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The function this tool is wrapping"""

    name: str | , __future__, abc, docstring_parser, inspect, logging, pydantic, pydantic_core, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/tools/_beta_runner.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Update the parameters for the next API call. This invalidates any cached tool responses.

        Args:
            params (MessageCreateParamsBase \\| Callable): Either new parameters or a function to mutate existing parameters | , __future__, abc, httpx, logging, typing, typing_extensions | L156: log.debug("Returning cached tool call response.")
L225: log.debug("Tool call was not requested, exiting from tool runner loop.")
L250: log.debug("Tool call was not requested, exiting from tool runner loop.")
L310: log.debug("Returning cached tool call response.")
L380: log.debug("Tool call was not requested, exiting from tool runner loop.")
L404: log.debug("Tool call was not requested, exiting from tool runner loop.") |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/vertex/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/vertex/_auth.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, google, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/vertex/_beta.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return the
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/vertex/_beta_messages.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return the
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/lib/vertex/_client.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a new client instance re-using the same options given to the current client with optional overriding. | , __future__, google, httpx, os, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/pagination.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/beta.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/files.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/messages/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/messages/batches.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/messages/messages.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, functools, httpx, itertools, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/models.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/skills/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/skills/skills.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/beta/skills/versions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/completions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/messages/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/messages/batches.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/messages/messages.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, functools, httpx, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/resources/models.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/anthropics/anthropic-sdk-python#accessing-raw-response-data-eg-headers | , __future__, httpx, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/anthropic_beta_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/base64_image_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/base64_pdf_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_all_thinking_turns_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_base64_image_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_base64_pdf_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_base64_pdf_source.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_base64_pdf_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_output_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_output_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_tool_result_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_bash_code_execution_tool_result_error_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_cache_control_ephemeral_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The time-to-live for the cache control breakpoint.

    This may be one the following values:

    - `5m`: 5 minutes
    - `1h`: 1 hour

    Defaults to `5m`. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_cache_creation.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The number of input tokens used to create the 1 hour cache entry."""

    ephemeral_5m_input_tokens: int |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_char_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_char_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_config.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_content_block_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_content_block_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_page_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_page_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_search_result_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_search_result_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citation_web_search_result_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citations_config_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citations_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_citations_web_search_result_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_clear_thinking_20251015_edit_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of most recent assistant turns to keep thinking blocks for.

    Older turns will have their thinking blocks removed. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_clear_thinking_20251015_edit_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of input tokens cleared by this edit."""

    cleared_thinking_turns: int | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_clear_tool_uses_20250919_edit_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Minimum number of tokens that must be cleared when triggered.

    Context will only be modified if at least this many tokens can be removed. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_clear_tool_uses_20250919_edit_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of input tokens cleared by this edit."""

    cleared_tool_uses: int | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_output_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_output_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_20250522_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_20250825_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_block_content.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_block_param_content_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_error_code.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_code_execution_tool_result_error_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_container.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Identifier for the container used in this request"""

    expires_at: datetime | , datetime, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_container_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Container id"""

    skills: Optional[Iterable[BetaSkillParams]] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_container_upload_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_container_upload_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_content_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_content_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_content_block_source_content_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_content_block_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_context_management_config_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | List of context management edits to apply""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_context_management_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | List of context management edits that were applied.""" | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_count_tokens_context_management_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The original token count before context management was applied""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_document_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Citation configuration for the document"""

    source: Source

    title: Optional[str] = None | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_file_document_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_file_image_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_image_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_input_json_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_input_tokens_clear_at_least_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_input_tokens_trigger_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_mcp_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_mcp_tool_use_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The name of the MCP tool"""

    server_name: str | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_mcp_tool_use_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The name of the MCP server"""

    type: Required[Literal["mcp_tool_use"]]

    cache_control: Optional[BetaCacheControlEphemeralParam] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_create_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Command type identifier"""

    file_text: str | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_delete_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Command type identifier"""

    path: str | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_insert_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Command type identifier"""

    insert_line: int | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_rename_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Command type identifier"""

    new_path: str | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_str_replace_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Command type identifier"""

    new_str: str | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_memory_tool_20250818_view_command.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Command type identifier"""

    path: str | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_message.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique object identifier.

    The format and length of IDs may change over time. | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_message_delta_usage.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The cumulative number of input tokens used to create the cache entry."""

    cache_read_input_tokens: Optional[int] = None | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_message_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_message_tokens_count.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Information about context management applied to the message."""

    input_tokens: int | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_metadata_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An external identifier for the user who is associated with the request.

    This should be a uuid, hash value, or other opaque identifier. Anthropic may use
    this id to help detect abuse. Do not include any identifying information such as
    name, email address, or phone number. | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_model_info.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique model identifier."""

    created_at: datetime | , datetime, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_plain_text_source.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_plain_text_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_content_block_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_content_block_delta_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_content_block_start_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Response model for a file uploaded to the container."""

    index: int

    type: Literal["content_block_start"] | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_content_block_stop_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_message_delta_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Information about the container used in the request (for the code execution
    tool) | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_message_start_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_message_stop_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_raw_message_stream_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_redacted_thinking_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_redacted_thinking_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_request_document_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    citations: Optional[BetaCitationsConfigParam]

    context: Optional[str]

    title: Optional[str] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_request_mcp_server_tool_configuration_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_request_mcp_server_url_definition_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_request_mcp_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    content: Union[str, Iterable[BetaTextBlockParam]]

    is_error: bool | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_search_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    citations: BetaCitationsConfigParam | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_server_tool_usage.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The number of web fetch tool requests."""

    web_search_requests: int |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_server_tool_use_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_server_tool_use_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_signature_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_skill.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Skill ID"""

    type: Literal["anthropic", "custom"] | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_skill_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Skill ID"""

    type: Required[Literal["anthropic", "custom"]] | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_stop_reason.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Citations supporting the text block.

    The type of citation returned will depend on the type of document being cited.
    Citing a PDF results in `page_location`, plain text results in `char_location`,
    and content document results in `content_block_location`. | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    citations: Optional[Iterable[BetaTextCitationParam]] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_citation.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_citation_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_create_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_create_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_str_replace_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_str_replace_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_tool_result_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_tool_result_error_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_view_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_text_editor_code_execution_view_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_config_disabled_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_config_enabled_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Determines how many tokens Claude can use for its internal reasoning process.

    Larger budgets can enable more thorough analysis for complex problems, improving
    response quality.

    Must be ≥1024 and less than `max_tokens`.

    See
    [extended thinking](https://docs.claude.com/en/docs/build-with-claude/extended-thinking)
    for details. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_config_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_thinking_turns_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_bash_20241022_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_bash_20250124_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_choice_any_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output exactly one tool
    use. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_choice_auto_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output at most one tool
    use. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_choice_none_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_choice_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_choice_tool_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The name of the tool to use."""

    type: Required[Literal["tool"]]

    disable_parallel_tool_use: bool | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_computer_use_20241022_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The height of the display in pixels."""

    display_width_px: Required[int] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_computer_use_20250124_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The height of the display in pixels."""

    display_width_px: Required[int] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | [JSON schema](https://json-schema.org/draft/2020-12) for this tool's input.

    This defines the shape of the `input` that your tool accepts and that the model
    will produce. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    content: Union[str, Iterable[Content]]

    is_error: bool | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_text_editor_20241022_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_text_editor_20250124_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_text_editor_20250429_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_text_editor_20250728_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_union_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_use_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_use_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_uses_keep_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_tool_uses_trigger_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_url_image_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_url_pdf_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_usage.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Breakdown of cached tokens by TTL"""

    cache_creation_input_tokens: Optional[int] = None | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ISO 8601 timestamp when the content was retrieved"""

    type: Literal["web_fetch_result"]

    url: str | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Fetched content URL"""

    retrieved_at: Optional[str] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_tool_20250910_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_tool_result_error_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_tool_result_error_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_fetch_tool_result_error_code.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_20250305_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The city of the user."""

    country: Optional[str] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_request_error_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_result_block_content.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_result_block_param_content_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_result_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/beta_web_search_tool_result_error_code.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/deleted_file.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the deleted file."""

    type: Optional[Literal["file_deleted"]] = None | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/file_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the object to use as a cursor for pagination.

    When provided, returns the page of results immediately after this object. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/file_metadata.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique object identifier.

    The format and length of IDs may change over time. | , datetime, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/file_upload_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The file to upload"""

    betas: Annotated[List[AnthropicBetaParam], PropertyInfo(alias="anthropic-beta")] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/message_count_tokens_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Input messages.

    Our models are trained to operate on alternating `user` and `assistant`
    conversational turns. When creating a new `Message`, you specify the prior
    conversational turns with the `messages` parameter, and the model then generates
    the next `Message` in the conversation. Consecutive `user` or `assistant` turns
    in your request will be combined into a single turn.

    Each input message must be an object with a `role` and `content`. You can
    specify a single `user`-role message, or you can include multiple `user` and
    `assistant` messages.

    If the final message uses the `assistant` role, the response content will
    continue immediately from the content in that message. This can be used to
    constrain part of the model's response.

    Example with a single `user` message:

    ```json
    [{ "role": "user", "content": "Hello, Claude" }]
    ```

    Example with multiple conversational turns:

    ```json
    [
      { "role": "user", "content": "Hello there." },
      { "role": "assistant", "content": "Hi, I'm Claude. How can I help you?" },
      { "role": "user", "content": "Can you explain LLMs in plain English?" }
    ]
    ```

    Example with a partially-filled response from Claude:

    ```json
    [
      {
        "role": "user",
        "content": "What's the Greek name for Sun? (A) Sol (B) Helios (C) Sun"
      },
      { "role": "assistant", "content": "The best answer is (" }
    ]
    ```

    Each input message `content` may be either a single `string` or an array of
    content blocks, where each block has a specific `type`. Using a `string` for
    `content` is shorthand for an array of one content block of type `"text"`. The
    following input messages are equivalent:

    ```json
    { "role": "user", "content": "Hello, Claude" }
    ```

    ```json
    { "role": "user", "content": [{ "type": "text", "text": "Hello, Claude" }] }
    ```

    See [input examples](https://docs.claude.com/en/api/messages-examples).

    Note that if you want to include a
    [system prompt](https://docs.claude.com/en/docs/system-prompts), you can use the
    top-level `system` parameter — there is no `"system"` role for input messages in
    the Messages API.

    There is a limit of 100,000 messages in a single request. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/message_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The maximum number of tokens to generate before stopping.

    Note that our models may stop _before_ reaching this maximum. This parameter
    only specifies the absolute maximum number of tokens to generate.

    Different models have different maximum values for this parameter. See
    [models](https://docs.claude.com/en/docs/models-overview) for details. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/batch_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | List of requests for prompt completion.

    Each is an individual request to create a Message. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/batch_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the object to use as a cursor for pagination.

    When provided, returns the page of results immediately after this object. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_deleted_message_batch.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the Message Batch."""

    type: Literal["message_batch_deleted"] | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique object identifier.

    The format and length of IDs may change over time. | , datetime, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_canceled_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_errored_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_expired_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_individual_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Developer-provided ID created for each request in a Message Batch.

    Useful for matching results to requests, as results may be given out of request
    order.

    Must be unique for each request within the Message Batch. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_request_counts.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of requests in the Message Batch that have been canceled.

    This is zero until processing of the entire Message Batch has ended. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/messages/beta_message_batch_succeeded_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/model_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the object to use as a cursor for pagination.

    When provided, returns the page of results immediately after this object. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skill_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Display title for the skill.

    This is a human-readable label that is not included in the prompt sent to the
    model. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skill_create_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill.

    The format and length of IDs may change over time. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skill_delete_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill.

    The format and length of IDs may change over time. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skill_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of results to return per page.

    Maximum value is 100. Defaults to 20. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skill_list_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill.

    The format and length of IDs may change over time. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skill_retrieve_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill.

    The format and length of IDs may change over time. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/version_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Files to upload for the skill.

    All files must be in the same top-level directory and must include a SKILL.md
    file at the root of that directory. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/version_create_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill version.

    The format and length of IDs may change over time. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/version_delete_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Version identifier for the skill.

    Each version is identified by a Unix epoch timestamp (e.g., "1759178010641129"). |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/version_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of items to return per page.

    Defaults to `20`. Ranges from `1` to `1000`. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/version_list_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill version.

    The format and length of IDs may change over time. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta/skills/version_retrieve_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique identifier for the skill version.

    The format and length of IDs may change over time. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_api_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_authentication_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_billing_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_error_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_gateway_timeout_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_invalid_request_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_not_found_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_overloaded_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_permission_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/beta_rate_limit_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/cache_control_ephemeral_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The time-to-live for the cache control breakpoint.

    This may be one the following values:

    - `5m`: 5 minutes
    - `1h`: 1 hour

    Defaults to `5m`. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/cache_creation.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The number of input tokens used to create the 1 hour cache entry."""

    ephemeral_5m_input_tokens: int |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_char_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_char_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_content_block_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_content_block_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_page_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_page_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_search_result_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citation_web_search_result_location_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citations_config_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citations_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citations_search_result_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/citations_web_search_result_location.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/completion.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique object identifier.

    The format and length of IDs may change over time. | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/completion_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The maximum number of tokens to generate before stopping.

    Note that our models may stop _before_ reaching this maximum. This parameter
    only specifies the absolute maximum number of tokens to generate. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block_delta_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawContentBlockDeltaEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block_source_content_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block_start_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawContentBlockStartEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/content_block_stop_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawContentBlockStopEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/document_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    citations: Optional[CitationsConfigParam]

    context: Optional[str]

    title: Optional[str] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/image_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/input_json_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique object identifier.

    The format and length of IDs may change over time. | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_count_tokens_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Input messages.

    Our models are trained to operate on alternating `user` and `assistant`
    conversational turns. When creating a new `Message`, you specify the prior
    conversational turns with the `messages` parameter, and the model then generates
    the next `Message` in the conversation. Consecutive `user` or `assistant` turns
    in your request will be combined into a single turn.

    Each input message must be an object with a `role` and `content`. You can
    specify a single `user`-role message, or you can include multiple `user` and
    `assistant` messages.

    If the final message uses the `assistant` role, the response content will
    continue immediately from the content in that message. This can be used to
    constrain part of the model's response.

    Example with a single `user` message:

    ```json
    [{ "role": "user", "content": "Hello, Claude" }]
    ```

    Example with multiple conversational turns:

    ```json
    [
      { "role": "user", "content": "Hello there." },
      { "role": "assistant", "content": "Hi, I'm Claude. How can I help you?" },
      { "role": "user", "content": "Can you explain LLMs in plain English?" }
    ]
    ```

    Example with a partially-filled response from Claude:

    ```json
    [
      {
        "role": "user",
        "content": "What's the Greek name for Sun? (A) Sol (B) Helios (C) Sun"
      },
      { "role": "assistant", "content": "The best answer is (" }
    ]
    ```

    Each input message `content` may be either a single `string` or an array of
    content blocks, where each block has a specific `type`. Using a `string` for
    `content` is shorthand for an array of one content block of type `"text"`. The
    following input messages are equivalent:

    ```json
    { "role": "user", "content": "Hello, Claude" }
    ```

    ```json
    { "role": "user", "content": [{ "type": "text", "text": "Hello, Claude" }] }
    ```

    See [input examples](https://docs.claude.com/en/api/messages-examples).

    Note that if you want to include a
    [system prompt](https://docs.claude.com/en/docs/system-prompts), you can use the
    top-level `system` parameter — there is no `"system"` role for input messages in
    the Messages API.

    There is a limit of 100,000 messages in a single request. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_count_tokens_tool_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The maximum number of tokens to generate before stopping.

    Note that our models may stop _before_ reaching this maximum. This parameter
    only specifies the absolute maximum number of tokens to generate.

    Different models have different maximum values for this parameter. See
    [models](https://docs.claude.com/en/docs/models-overview) for details. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_delta_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawMessageDeltaEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_delta_usage.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The cumulative number of input tokens used to create the cache entry."""

    cache_read_input_tokens: Optional[int] = None | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_start_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawMessageStartEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_stop_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawMessageStopEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_stream_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The RawMessageStreamEvent type should be used instead""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/message_tokens_count.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The total number of tokens across the provided list of messages, system prompt,
    and tools. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/batch_create_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | List of requests for prompt completion.

    Each is an individual request to create a Message. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/batch_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the object to use as a cursor for pagination.

    When provided, returns the page of results immediately after this object. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/deleted_message_batch.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the Message Batch."""

    type: Literal["message_batch_deleted"] | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique object identifier.

    The format and length of IDs may change over time. | , datetime, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_canceled_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_errored_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_expired_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_individual_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Developer-provided ID created for each request in a Message Batch.

    Useful for matching results to requests, as results may be given out of request
    order.

    Must be unique for each request within the Message Batch. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_request_counts.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Number of requests in the Message Batch that have been canceled.

    This is zero until processing of the entire Message Batch has ended. |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/messages/message_batch_succeeded_result.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/metadata_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An external identifier for the user who is associated with the request.

    This should be a uuid, hash value, or other opaque identifier. Anthropic may use
    this id to help detect abuse. Do not include any identifying information such as
    name, email address, or phone number. | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/model.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/model_info.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Unique model identifier."""

    created_at: datetime | , datetime, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/model_list_params.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ID of the object to use as a cursor for pagination.

    When provided, returns the page of results immediately after this object. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/model_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/plain_text_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_content_block_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_content_block_delta_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_content_block_start_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_content_block_stop_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_message_delta_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Billing and rate-limit usage.

    Anthropic's API bills and rate-limits by token counts, as tokens represent the
    underlying cost to our systems.

    Under the hood, the API transforms requests into a format suitable for the
    model. The model's output then goes through a parsing stage before becoming an
    API response. As a result, the token counts in `usage` will not match one-to-one
    with the exact visible content of an API request or response.

    For example, `output_tokens` will be non-zero, even for an empty string response
    from Claude.

    Total input tokens in a request is the summation of `input_tokens`,
    `cache_creation_input_tokens`, and `cache_read_input_tokens`. | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_message_start_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_message_stop_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/raw_message_stream_event.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/redacted_thinking_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/redacted_thinking_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/search_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    citations: CitationsConfigParam | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/server_tool_usage.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The number of web search tool requests.""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/server_tool_use_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/server_tool_use_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/api_error_object.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/authentication_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/billing_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/error_object.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/error_response.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/gateway_timeout_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/invalid_request_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/not_found_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/overloaded_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/permission_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/shared/rate_limit_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/signature_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/stop_reason.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/text_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Citations supporting the text block.

    The type of citation returned will depend on the type of document being cited.
    Citing a PDF results in `page_location`, plain text results in `char_location`,
    and content document results in `content_block_location`. | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/text_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    citations: Optional[Iterable[TextCitationParam]] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/text_citation.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/text_citation_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/text_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/thinking_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/thinking_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/thinking_config_disabled_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/thinking_config_enabled_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Determines how many tokens Claude can use for its internal reasoning process.

    Larger budgets can enable more thorough analysis for complex problems, improving
    response quality.

    Must be ≥1024 and less than `max_tokens`.

    See
    [extended thinking](https://docs.claude.com/en/docs/build-with-claude/extended-thinking)
    for details. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/thinking_config_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/thinking_delta.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_bash_20250124_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_choice_any_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output exactly one tool
    use. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_choice_auto_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Whether to disable parallel tool use.

    Defaults to `false`. If set to `true`, the model will output at most one tool
    use. | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_choice_none_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_choice_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_choice_tool_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The name of the tool to use."""

    type: Required[Literal["tool"]]

    disable_parallel_tool_use: bool | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | [JSON schema](https://json-schema.org/draft/2020-12) for this tool's input.

    This defines the shape of the `input` that your tool accepts and that the model
    will produce. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block."""

    content: Union[str, Iterable[Content]]

    is_error: bool | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_text_editor_20250124_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_text_editor_20250429_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_text_editor_20250728_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Name of the tool.

    This is how the tool will be called by the model and in `tool_use` blocks. | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_union_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_use_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/tool_use_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/url_image_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/url_pdf_source_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/usage.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Breakdown of cached tokens by TTL"""

    cache_creation_input_tokens: Optional[int] = None | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_20250305_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The city of the user."""

    country: Optional[str] | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_request_error_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_result_block.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_result_block_content.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_result_block_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a cache control breakpoint at this content block.""" | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_result_block_param_content_param.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anthropic/types/web_search_tool_result_error.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Support deprecated aliases."""
    if attr == "BrokenWorkerIntepreter":
        import warnings

        warnings.warn(
            "The 'BrokenWorkerIntepreter' alias is deprecated, use 'BrokenWorkerInterpreter' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return BrokenWorkerInterpreter

    raise AttributeError(f"module {__name__!r} has no attribute {attr!r}") | , __future__, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_backends/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_backends/_asyncio.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Shutdown and close event loop."""
            if self._state is not _State.INITIALIZED:
                return
            try:
                loop = self._loop
                _cancel_all_tasks(loop)
                loop.run_until_complete(loop.shutdown_asyncgens())
                if hasattr(loop, "shutdown_default_executor"):
                    loop.run_until_complete(loop.shutdown_default_executor())
                else:
                    loop.run_until_complete(_shutdown_default_executor(loop))
            finally:
                if self._set_event_loop:
                    events.set_event_loop(None)
                loop.close()
                self._loop = None
                self._state = _State.CLOSED

        def get_loop(self) -> AbstractEventLoop: | , __future__, _typeshed, array, asyncio, collections, concurrent, contextlib, contextvars, dataclasses, enum, exceptiongroup, functools, inspect, io, math, os, queue, signal, sniffio, socket, sys, threading, types, typing, typing_extensions, weakref | L137: debug: bool \\| None = None,
L141: self._debug = debug
L246: if self._debug is not None:
L247: self._loop.set_debug(self._debug)
L365: # task coro is async_genenerator_asend https://bugs.python.org/issue37771 |
| `blackboard-agent/venv/Lib/site-packages/anyio/_backends/_trio.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, _typeshed, array, collections, concurrent, contextlib, dataclasses, exceptiongroup, functools, io, math, os, outcome, signal, socket, sys, trio, types, typing, typing_extensions, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_asyncio_selector_thread.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, _typeshed, asyncio, collections, selectors, socket, threading, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_contextmanagers.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Mixin class providing context manager functionality via a generator-based
    implementation.

    This class allows you to implement a context manager via :meth:`__contextmanager__`
    which should return a generator. The mechanics are meant to mirror those of
    :func:`@contextmanager <contextlib.contextmanager>`.

    .. note:: Classes using this mix-in are not reentrant as context managers, meaning
        that once you enter it, you can't re-enter before first exiting it.

    .. seealso:: :doc:`contextmanagers` | __future__, abc, contextlib, inspect, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_eventloop.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Run the given coroutine function in an asynchronous event loop.

    The current thread must not be already running an event loop.

    :param func: a coroutine function
    :param args: positional arguments to ``func``
    :param backend: name of the asynchronous event loop implementation – currently
        either ``asyncio`` or ``trio``
    :param backend_options: keyword arguments to call the backend ``run()``
        implementation with (documented :ref:`here <backend options>`)
    :return: the return value of the coroutine function
    :raises RuntimeError: if an asynchronous event loop is already running in this
        thread
    :raises LookupError: if the named backend is not found | , __future__, collections, contextlib, importlib, math, sniffio, sys, threading, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Raised when trying to use a resource that has been rendered unusable due to external
    causes (e.g. a send stream whose peer has disconnected). | __future__, collections, exceptiongroup, sys, textwrap, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_fileio.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An asynchronous file object.

    This class wraps a standard file object and provides async friendly versions of the
    following blocking methods (where available on the original file object):

    * read
    * read1
    * readline
    * readlines
    * readinto
    * readinto1
    * write
    * writelines
    * truncate
    * seek
    * tell
    * flush

    All other methods are directly passed through.

    This class supports the asynchronous context manager protocol which closes the
    underlying file at the end of the context block.

    This class also supports asynchronous iteration::

        async with await open_file(...) as f:
            async for line in f:
                print(line) | , __future__, _typeshed, collections, dataclasses, functools, os, pathlib, sys, types, typing | L416: def info(self) -> Any:  # TODO: add return type annotation when Typeshed gets it |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_resources.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Close an asynchronous resource in a cancelled scope.

    Doing this closes the resource without waiting on anything.

    :param resource: the resource to close | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_signals.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Start receiving operating system signals.

    :param signals: signals to receive (e.g. ``signal.SIGINT``)
    :return: an asynchronous context manager for an asynchronous iterator which yields
        signal numbers

    .. warning:: Windows does not support signals natively so it is best to avoid
        relying on this in cross-platform applications.

    .. warning:: On asyncio, this permanently replaces any previous signal handler for
        the given signals, as set via :meth:`~asyncio.loop.add_signal_handler`. | , __future__, collections, contextlib, signal |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_sockets.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Connect to a host using the TCP protocol.

    This function implements the stateless version of the Happy Eyeballs algorithm (RFC
    6555). If ``remote_host`` is a host name that resolves to multiple IP addresses,
    each one is tried until one connection attempt succeeds. If the first attempt does
    not connected within 250 milliseconds, a second attempt is started using the next
    address in the list, and so on. On IPv6 enabled systems, an IPv6 address (if
    available) is tried first.

    When the connection has been established, a TLS handshake will be done if either
    ``ssl_context`` or ``tls_hostname`` is not ``None``, or if ``tls`` is ``True``.

    :param remote_host: the IP address or host name to connect to
    :param remote_port: port on the target host to connect to
    :param local_host: the interface address or name to bind the socket to before
        connecting
    :param tls: ``True`` to do a TLS handshake with the connected stream and return a
        :class:`~anyio.streams.tls.TLSStream` instead
    :param ssl_context: the SSL context object to use (if omitted, a default context is
        created)
    :param tls_standard_compatible: If ``True``, performs the TLS shutdown handshake
        before closing the stream and requires that the server does this as well.
        Otherwise, :exc:`~ssl.SSLEOFError` may be raised during reads from the stream.
        Some protocols, such as HTTP, require this option to be ``False``.
        See :meth:`~ssl.SSLContext.wrap_socket` for details.
    :param tls_hostname: host name to check the server certificate against (defaults to
        the value of ``remote_host``)
    :param happy_eyeballs_delay: delay (in seconds) before starting the next connection
        attempt
    :return: a socket stream object if no TLS handshake was done, otherwise a TLS stream
    :raises ConnectionFailed: if the connection fails | , __future__, _typeshed, collections, dataclasses, errno, exceptiongroup, ipaddress, os, socket, ssl, stat, sys, typing, typing_extensions, warnings | L54: IPPROTO_IPV6 = getattr(socket, "IPPROTO_IPV6", 41)  # https://bugs.python.org/issue29515
L348: # We passing type=0 on non-Windows platforms as a workaround for a uvloop bug
L360: # The set comprehension is here to work around a glibc bug:
L361: # https://sourceware.org/bugzilla/show_bug.cgi?id=14969 |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_streams.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a memory object stream.

    The stream's item type can be annotated like
    :func:`create_memory_object_stream[T_Item]`.

    :param max_buffer_size: number of items held in the buffer until ``send()`` starts
        blocking
    :param item_type: old way of marking the streams with the right generic type for
        static typing (does nothing on AnyIO 4)

        .. deprecated:: 4.0
          Use ``create_memory_object_stream[YourItemType](...)`` instead.
    :return: a tuple of (send stream, receive stream) | , __future__, math, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_subprocesses.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Run an external command in a subprocess and wait until it completes.

    .. seealso:: :func:`subprocess.run`

    :param command: either a string to pass to the shell, or an iterable of strings
        containing the executable name or path and its arguments
    :param input: bytes passed to the standard input of the subprocess
    :param stdin: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        a file-like object, or `None`; ``input`` overrides this
    :param stdout: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        a file-like object, or `None`
    :param stderr: one of :data:`subprocess.PIPE`, :data:`subprocess.DEVNULL`,
        :data:`subprocess.STDOUT`, a file-like object, or `None`
    :param check: if ``True``, raise :exc:`~subprocess.CalledProcessError` if the
        process terminates with a return code other than 0
    :param cwd: If not ``None``, change the working directory to this before running the
        command
    :param env: if not ``None``, this mapping replaces the inherited environment
        variables from the parent process
    :param startupinfo: an instance of :class:`subprocess.STARTUPINFO` that can be used
        to specify process startup parameters (Windows only)
    :param creationflags: flags that can be used to control the creation of the
        subprocess (see :class:`subprocess.Popen` for the specifics)
    :param start_new_session: if ``true`` the setsid() system call will be made in the
        child process prior to the execution of the subprocess. (POSIX only)
    :param pass_fds: sequence of file descriptors to keep open between the parent and
        child processes. (POSIX only)
    :param user: effective user to run the process as (Python >= 3.9, POSIX only)
    :param group: effective group to run the process as (Python >= 3.9, POSIX only)
    :param extra_groups: supplementary groups to set in the subprocess (Python >= 3.9,
        POSIX only)
    :param umask: if not negative, this umask is applied in the child process before
        running the given command (Python >= 3.9, POSIX only)
    :return: an object representing the completed process
    :raises ~subprocess.CalledProcessError: if ``check`` is ``True`` and the process
        exits with a nonzero return code | , __future__, collections, io, os, subprocess, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_synchronization.py` | ❓ UNKNOWN | 2025-11-09 21:03 | :ivar int tasks_waiting: number of tasks waiting on :meth:`~.Event.wait` | , __future__, collections, dataclasses, math, sniffio, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_tasks.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Wraps a unit of work that can be made separately cancellable.

    :param deadline: The time (clock value) when this scope is cancelled automatically
    :param shield: ``True`` to shield the cancel scope from external cancellation | , __future__, collections, contextlib, math, types |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_tempfile.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An asynchronous temporary file that is automatically created and cleaned up.

    This class provides an asynchronous context manager interface to a temporary file.
    The file is created using Python's standard `tempfile.TemporaryFile` function in a
    background thread, and is wrapped as an asynchronous file using `AsyncFile`.

    :param mode: The mode in which the file is opened. Defaults to "w+b".
    :param buffering: The buffering policy (-1 means the default buffering).
    :param encoding: The encoding used to decode or encode the file. Only applicable in
        text mode.
    :param newline: Controls how universal newlines mode works (only applicable in text
        mode).
    :param suffix: The suffix for the temporary file name.
    :param prefix: The prefix for the temporary file name.
    :param dir: The directory in which the temporary file is created.
    :param errors: The error handling scheme used for encoding/decoding errors. | , __future__, _typeshed, collections, io, os, sys, tempfile, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_testing.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Represents an asynchronous task.

    :ivar int id: the unique identifier of the task
    :ivar parent_id: the identifier of the parent task, if any
    :vartype parent_id: Optional[int]
    :ivar str name: the description of the task (if any)
    :ivar ~collections.abc.Coroutine coro: the coroutine object of the task | , __future__, collections, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/_core/_typedattr.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Return a unique object, used to mark typed attributes."""
    return object()


class TypedAttributeSet: | , __future__, collections, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_eventloop.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Run the given coroutine function in an asynchronous event loop.

        The current thread must not be already running an event loop.

        :param func: a coroutine function
        :param args: positional arguments to ``func``
        :param kwargs: positional arguments to ``func``
        :param options: keyword arguments to call the backend ``run()`` implementation
            with
        :return: the return value of the coroutine function | , __future__, _typeshed, abc, collections, contextlib, math, os, signal, socket, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_resources.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Abstract base class for all closeable asynchronous resources.

    Works as an asynchronous context manager which returns the instance itself on enter,
    and calls :meth:`aclose` on exit. | __future__, abc, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_sockets.py` | ❓ UNKNOWN | 2025-11-09 21:03 | .. attribute:: family
        :type: socket.AddressFamily

        the address family of the underlying socket

    .. attribute:: local_address
        :type: tuple[str, int] \\| str

        the local address the underlying socket is connected to

    .. attribute:: local_port
        :type: int

        for IP based sockets, the local port the underlying socket is bound to

    .. attribute:: raw_socket
        :type: socket.socket

        the underlying stdlib socket object

    .. attribute:: remote_address
        :type: tuple[str, int] \\| str

        the remote address the underlying socket is connected to

    .. attribute:: remote_port
        :type: int

        for IP based sockets, the remote port the underlying socket is connected to | , __future__, abc, collections, contextlib, errno, io, ipaddress, socket, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_streams.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An interface for receiving objects.

    This interface makes no guarantees that the received messages arrive in the order in
    which they were sent, or that no messages are missed.

    Asynchronously iterating over objects of this type will yield objects matching the
    given type parameter. | , __future__, abc, collections, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_subprocesses.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An asynchronous version of :class:`subprocess.Popen`."""

    @abstractmethod
    async def wait(self) -> int: | , __future__, abc, signal |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_tasks.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Signal that the task has started.

        :param value: object passed back to the starter of the task | , __future__, abc, collections, sys, types, typing, typing_extensions | L70: :param name: name of the task, for the purposes of introspection and debugging
L96: :param name: an optional name for the task, for introspection and debugging |
| `blackboard-agent/venv/Lib/site-packages/anyio/abc/_testing.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Encapsulates a running event loop. Every call made through this object will use the
    same event loop. | __future__, abc, collections, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/from_thread.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Call a coroutine function from a worker thread.

    :param func: a coroutine function
    :param args: positional arguments for the callable
    :param token: an event loop token to use to get back to the event loop thread
        (required if calling this function from outside an AnyIO worker thread)
    :return: the return value of the coroutine function
    :raises MissingTokenError: if no token was provided and called from outside an
        AnyIO worker thread
    :raises RunFinishedError: if the event loop tied to ``token`` is no longer running

    .. versionchanged:: 4.11.0
        Added the ``token`` parameter. | , __future__, collections, concurrent, contextlib, dataclasses, inspect, sys, threading, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/lowlevel.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Check for cancellation and allow the scheduler to switch to another task.

    Equivalent to (but more efficient than)::

        await checkpoint_if_cancelled()
        await cancel_shielded_checkpoint()


    .. versionadded:: 3.0 | , __future__, dataclasses, enum, typing, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/pytest_plugin.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Manages port generation based on specified socket kind, ensuring no duplicate
    ports are generated.

    This class provides functionality for generating available free ports on the
    system. It is initialized with a specific socket kind and can generate ports
    for given address families while avoiding reuse of previously generated ports.

    Users should not instantiate this class directly, but use the
    ``free_tcp_port_factory`` and ``free_udp_port_factory`` fixtures instead. For simple
    uses cases, ``free_tcp_port`` and ``free_udp_port`` can be used instead. | , __future__, _pytest, collections, contextlib, exceptiongroup, inspect, pytest, sniffio, socket, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/buffered.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Wraps any bytes-based receive stream and uses a buffer to provide sophisticated
    receiving capabilities in the form of a byte stream. | , __future__, collections, dataclasses, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/file.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A byte stream that reads from a file in the file system.

    :param file: a file that has been opened for reading in binary mode

    .. versionadded:: 3.0 | , __future__, collections, io, os, pathlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/memory.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Receive the next item if it can be done without waiting.

        :return: the received item
        :raises ~anyio.ClosedResourceError: if this send stream has been closed
        :raises ~anyio.EndOfStream: if the buffer is empty and this stream has been
            closed from the sending end
        :raises ~anyio.WouldBlock: if there are no items in the buffer and no tasks
            waiting to send | , __future__, collections, dataclasses, types, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/stapled.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Combines two byte streams into a single, bidirectional byte stream.

    Extra attributes will be provided from both streams, with the receive stream
    providing the values in case of a conflict.

    :param ByteSendStream send_stream: the sending byte stream
    :param ByteReceiveStream receive_stream: the receiving byte stream | , __future__, collections, dataclasses, typing |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/text.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Stream wrapper that decodes bytes to strings using the given encoding.

    Decoding is done using :class:`~codecs.IncrementalDecoder` which returns any
    completely received unicode characters as soon as they come in.

    :param transport_stream: any bytes-based receive stream
    :param encoding: character encoding to use for decoding bytes to strings (defaults
        to ``utf-8``)
    :param errors: handling scheme for decoding errors (defaults to ``strict``; see the
        `codecs module documentation`_ for a comprehensive list of options)

    .. _codecs module documentation:
        https://docs.python.org/3/library/codecs.html#codec-objects | , __future__, codecs, collections, dataclasses, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/streams/tls.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Contains Transport Layer Security related attributes."""

    #: the selected ALPN protocol
    alpn_protocol: str \\| None = typed_attribute()
    #: the channel binding for type ``tls-unique``
    channel_binding_tls_unique: bytes = typed_attribute()
    #: the selected cipher
    cipher: tuple[str, str, int] = typed_attribute()
    #: the peer certificate in dictionary form (see :meth:`ssl.SSLSocket.getpeercert`
    # for more information)
    peer_certificate: None \\| (dict[str, str \\| _PCTRTTT \\| _PCTRTT]) = typed_attribute()
    #: the peer certificate in binary form
    peer_certificate_binary: bytes \\| None = typed_attribute()
    #: ``True`` if this is the server side of the connection
    server_side: bool = typed_attribute()
    #: ciphers shared by the client during the TLS handshake (``None`` if this is the
    #: client side)
    shared_ciphers: list[tuple[str, str, int]] \\| None = typed_attribute()
    #: the :class:`~ssl.SSLObject` used for encryption
    ssl_object: ssl.SSLObject = typed_attribute()
    #: ``True`` if this stream does (and expects) a closing TLS handshake when the
    #: stream is being closed
    standard_compatible: bool = typed_attribute()
    #: the TLS protocol version (e.g. ``TLSv1.2``)
    tls_version: str = typed_attribute()


@dataclass(eq=False)
class TLSStream(ByteStream): | , __future__, collections, dataclasses, functools, logging, re, ssl, sys, typing, typing_extensions | L331: # issue because it works around the CPython bug. |
| `blackboard-agent/venv/Lib/site-packages/anyio/to_interpreter.py` | ❓ UNKNOWN | 2025-11-09 21:03 | import _interpqueues
from _interpreters import NotShareableError
from pickle import loads, dumps, HIGHEST_PROTOCOL

QUEUE_PICKLE_ARGS = (1, 2)
QUEUE_UNPICKLE_ARGS = (0, 2)

item = _interpqueues.get(queue_id)[0]
try:
    func, args = loads(item)
    retval = func(*args)
except BaseException as exc:
    is_exception = True
    retval = exc
else:
    is_exception = False

try:
    _interpqueues.put(queue_id, (retval, is_exception), *QUEUE_UNPICKLE_ARGS)
except NotShareableError:
    retval = dumps(retval, HIGHEST_PROTOCOL)
    _interpqueues.put(queue_id, (retval, is_exception), *QUEUE_PICKLE_ARGS) | , __future__, _interpqueues, _interpreters, atexit, collections, concurrent, os, pickle, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/to_process.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Call the given function with the given arguments in a worker process.

    If the ``cancellable`` option is enabled and the task waiting for its completion is
    cancelled, the worker process running it will be abruptly terminated using SIGKILL
    (or ``terminateProcess()`` on Windows).

    :param func: a callable
    :param args: positional arguments for the callable
    :param cancellable: ``True`` to allow cancellation of the operation while it's
        running
    :param limiter: capacity limiter to use to limit the total amount of processes
        running (if omitted, the default limiter is used)
    :return: an awaitable that yields the return value of the function. | , __future__, collections, importlib, os, pickle, subprocess, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/anyio/to_thread.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Call the given function with the given arguments in a worker thread.

    If the ``cancellable`` option is enabled and the task waiting for its completion is
    cancelled, the thread will still run its course but its return value (or any raised
    exception) will be ignored.

    :param func: a callable
    :param args: positional arguments for the callable
    :param abandon_on_cancel: ``True`` to abandon the thread (leaving it to run
        unchecked on own) if the host task is cancelled, ``False`` to ignore
        cancellations in the host task until the operation has completed in the worker
        thread
    :param cancellable: deprecated alias of ``abandon_on_cancel``; will override
        ``abandon_on_cancel`` if both parameters are passed
    :param limiter: capacity limiter to use to limit the total amount of threads running
        (if omitted, the default limiter is used)
    :return: an awaitable that yields the return value of the function. | , __future__, collections, sys, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/attr/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Classes Without Boilerplate | , functools, importlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/attr/_cmp.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Create a class that can be passed into `attrs.field`'s ``eq``, ``order``,
    and ``cmp`` arguments to customize field comparison.

    The resulting class will have a full set of ordering methods if at least
    one of ``{lt, le, gt, ge}`` and ``eq``  are provided.

    Args:
        eq (typing.Callable \\| None):
            Callable used to evaluate equality of two objects.

        lt (typing.Callable \\| None):
            Callable used to evaluate whether one object is less than another
            object.

        le (typing.Callable \\| None):
            Callable used to evaluate whether one object is less than or equal
            to another object.

        gt (typing.Callable \\| None):
            Callable used to evaluate whether one object is greater than
            another object.

        ge (typing.Callable \\| None):
            Callable used to evaluate whether one object is greater than or
            equal to another object.

        require_same_type (bool):
            When `True`, equality and ordering methods will return
            `NotImplemented` if objects are not of the same type.

        class_name (str \\| None): Name of class. Defaults to "Comparable".

    See `comparison` for more details.

    .. versionadded:: 21.1.0 | , functools, types |  |
| `blackboard-agent/venv/Lib/site-packages/attr/_compat.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Get annotations for *cls*. | annotationlib, collections, inspect, platform, sys, threading, typing |  |
| `blackboard-agent/venv/Lib/site-packages/attr/_config.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Set whether or not validators are run.  By default, they are run.

    .. deprecated:: 21.3.0 It will not be removed, but it also will not be
        moved to new ``attrs`` namespace. Use `attrs.validators.set_disabled()`
        instead. |  |  |
| `blackboard-agent/venv/Lib/site-packages/attr/_funcs.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Return the *attrs* attribute values of *inst* as a dict.

    Optionally recurse into other *attrs*-decorated classes.

    Args:
        inst: Instance of an *attrs*-decorated class.

        recurse (bool): Recurse into classes that are also *attrs*-decorated.

        filter (~typing.Callable):
            A callable whose return code determines whether an attribute or
            element is included (`True`) or dropped (`False`).  Is called with
            the `attrs.Attribute` as the first argument and the value as the
            second argument.

        dict_factory (~typing.Callable):
            A callable to produce dictionaries from.  For example, to produce
            ordered dictionaries instead of normal Python dictionaries, pass in
            ``collections.OrderedDict``.

        retain_collection_types (bool):
            Do not convert to `list` when encountering an attribute whose type
            is `tuple` or `set`.  Only meaningful if *recurse* is `True`.

        value_serializer (typing.Callable \\| None):
            A hook that is called for every attribute or dict key/value.  It
            receives the current instance, field and value and must return the
            (updated) value.  The hook is run *after* the optional *filter* has
            been applied.

    Returns:
        Return type of *dict_factory*.

    Raises:
        attrs.exceptions.NotAnAttrsClassError:
            If *cls* is not an *attrs* class.

    ..  versionadded:: 16.0.0 *dict_factory*
    ..  versionadded:: 16.1.0 *retain_collection_types*
    ..  versionadded:: 20.3.0 *value_serializer*
    ..  versionadded:: 21.3.0
        If a dict has a collection for a key, it is serialized as a tuple. | , copy |  |
| `blackboard-agent/venv/Lib/site-packages/attr/_make.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sentinel to indicate the lack of a value when `None` is ambiguous.

    If extending attrs, you can use ``typing.Literal[NOTHING]`` to show
    that a value may be ``NOTHING``.

    .. versionchanged:: 21.1.0 ``bool(NOTHING)`` is now False.
    .. versionchanged:: 22.2.0 ``NOTHING`` is now an ``enum.Enum`` variant. | , __future__, abc, collections, contextlib, copy, enum, functools, inspect, itertools, linecache, sys, types, typing, unicodedata, weakref | L242: # In order of debuggers like PDB being able to step through the code,
L298: The string comparison hack is used to avoid evaluating all string
L360: leads to the buggy behavior reported in #428. |
| `blackboard-agent/venv/Lib/site-packages/attr/_next_gen.py` | ❓ UNKNOWN | 2025-11-09 21:21 | These are keyword-only APIs that call `attr.s` and `attr.ib` with different
default values. | , functools |  |
| `blackboard-agent/venv/Lib/site-packages/attr/_version_info.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A version object that can be compared to tuple of length 1--4:

    >>> attr.VersionInfo(19, 1, 0, "final")  <= (19, 2)
    True
    >>> attr.VersionInfo(19, 1, 0, "final") < (19, 1, 1)
    True
    >>> vi = attr.VersionInfo(19, 2, 0, "final")
    >>> vi < (19, 1, 1)
    False
    >>> vi < (19,)
    False
    >>> vi == (19, 2,)
    True
    >>> vi == (19, 2, 1)
    False

    .. versionadded:: 19.2 | , functools |  |
| `blackboard-agent/venv/Lib/site-packages/attr/converters.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Commonly useful converters. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/attr/exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A frozen/immutable instance or attribute have been attempted to be
    modified.

    It mirrors the behavior of ``namedtuples`` by using the same error message
    and subclassing `AttributeError`.

    .. versionadded:: 20.1.0 | __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/attr/filters.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Commonly useful filters for `attrs.asdict` and `attrs.astuple`. |  |  |
| `blackboard-agent/venv/Lib/site-packages/attr/setters.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Commonly used hooks for on_setattr. |  |  |
| `blackboard-agent/venv/Lib/site-packages/attr/validators.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Commonly useful validators. | , contextlib, operator, re |  |
| `blackboard-agent/venv/Lib/site-packages/attrs/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , attr |  |
| `blackboard-agent/venv/Lib/site-packages/attrs/converters.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | attr |  |
| `blackboard-agent/venv/Lib/site-packages/attrs/exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | attr |  |
| `blackboard-agent/venv/Lib/site-packages/attrs/filters.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | attr |  |
| `blackboard-agent/venv/Lib/site-packages/attrs/setters.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | attr |  |
| `blackboard-agent/venv/Lib/site-packages/attrs/validators.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | attr |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Beautiful Soup Elixir and Tonic - "The Screen-Scraper's Friend".

http://www.crummy.com/software/BeautifulSoup/

Beautiful Soup uses a pluggable XML or HTML parser to parse a
(possibly invalid) document into a tree representation. Beautiful Soup
provides methods and Pythonic idioms that make it easy to navigate,
search, and modify the parse tree.

Beautiful Soup works with Python 3.6 and up. It works better if lxml
and/or html5lib is installed.

For more than you ever wanted to know about Beautiful Soup, see the
documentation: http://www.crummy.com/software/BeautifulSoup/bs4/doc/ | , collections, os, re, sys, traceback, warnings | L401: TODO: warnings.warn had this problem back in 2010 but it might not |
| `blackboard-agent/venv/Lib/site-packages/bs4/builder/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The warning issued when an HTML parser is used to parse
    XML that is not XHTML. | bs4, collections, itertools, re, sys, warnings | L417: # TODO: Arguably <noscript> could go here but it seems |
| `blackboard-agent/venv/Lib/site-packages/bs4/builder/_html5lib.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Use html5lib to build a tree.

    Note that this TreeBuilder does not support some features common
    to HTML TreeBuilders. Some of these features could theoretically
    be implemented, but at the very least it's quite difficult,
    because html5lib moves the parse tree around as it's being built.

    * This TreeBuilder doesn't use different subclasses of NavigableString
      based on the name of the tag in which the string was found.

    * You can't use a SoupStrainer to parse only part of a document. | bs4, html5lib, re, warnings | L136: # TODO: Why is the parser 'html.parser' here? To avoid an
L142: # TODO: What are **kwargs exactly? Should they be passed in
L182: # TODO: Why is the parser 'html.parser' here? To avoid an
L310: # TODO This has O(n^2) performance, for input like
L436: # TODO: This code has no test coverage and I'm not sure |
| `blackboard-agent/venv/Lib/site-packages/bs4/builder/_htmlparser.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Use the HTMLParser library to parse HTML files that aren't too bad."""

# Use of this source code is governed by the MIT license.
__license__ = "MIT"

__all__ = [
    'HTMLParserTreeBuilder',
    ]

from html.parser import HTMLParser

import sys
import warnings

from bs4.element import (
    CData,
    Comment,
    Declaration,
    Doctype,
    ProcessingInstruction,
    )
from bs4.dammit import EntitySubstitution, UnicodeDammit

from bs4.builder import (
    DetectsXMLParsedAsHTML,
    ParserRejectedMarkup,
    HTML,
    HTMLTreeBuilder,
    STRICT,
    )


HTMLPARSER = 'html.parser'

class BeautifulSoupHTMLParser(HTMLParser, DetectsXMLParsedAsHTML): | bs4, html, sys, warnings | L189: # TODO: This was originally a workaround for a bug in
L190: # HTMLParser. (http://bugs.python.org/issue13633) The bug has |
| `blackboard-agent/venv/Lib/site-packages/bs4/builder/_lxml.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Let the BeautifulSoup object know about the standard namespace
        mapping.

        :param soup: A `BeautifulSoup`. | bs4, collections, io, lxml | L66: # See: https://bugs.launchpad.net/lxml/+bug/1846906
L130: # TODO: Issue a warning if parser is present but not a
L190: # TODO: This is a workaround for
L191: # https://bugs.launchpad.net/lxml/+bug/1948551. |
| `blackboard-agent/venv/Lib/site-packages/bs4/css.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Integration code for CSS selectors using Soup Sieve (pypi: soupsieve)."""

import warnings
try:
    import soupsieve
except ImportError as e:
    soupsieve = None
    warnings.warn(
        'The soupsieve package is not installed. CSS selectors cannot be used.'
    )


class CSS(object): | bs4, soupsieve, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/dammit.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Beautiful Soup bonus library: Unicode, Dammit

This library converts a bytestream to Unicode through any means
necessary. It is heavily based on code from Mark Pilgrim's Universal
Feed Parser. It works best on XML and HTML, but it does not rewrite the
XML or HTML to reflect a new encoding; that's the tree builder's job. | cchardet, chardet, charset_normalizer, codecs, collections, html, logging, re, string |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/diagnose.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Diagnostic functions, mainly for use when doing tech support."""

# Use of this source code is governed by the MIT license.
__license__ = "MIT"

import cProfile
from io import BytesIO
from html.parser import HTMLParser
import bs4
from bs4 import BeautifulSoup, __version__
from bs4.builder import builder_registry

import os
import pstats
import random
import tempfile
import time
import traceback
import sys
import cProfile

def diagnose(data): | bs4, cProfile, html, html5lib, io, lxml, os, pstats, random, sys, tempfile, time, traceback |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/element.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Alias one attribute name to another for backward compatibility"""
    @property
    def alias(self):
        return getattr(self, attr)

    @alias.setter
    def alias(self):
        return setattr(self, attr)
    return alias


# These encodings are recognized by Python (so PageElement.encode
# could theoretically support them) but XML and HTML don't recognize
# them (so they should not show up in an XML or HTML document as that
# document's encoding).
#
# If an XML document is encoded in one of these encodings, no encoding
# will be mentioned in the XML declaration. If an HTML document is
# encoded in one of these encodings, and the HTML document has a
# <meta> tag that mentions an encoding, the encoding will be given as
# the empty string.
#
# Source:
# https://docs.python.org/3/library/codecs.html#python-specific-encodings
PYTHON_SPECIFIC_ENCODINGS = set([
    "idna",
    "mbcs",
    "oem",
    "palmos",
    "punycode",
    "raw_unicode_escape",
    "undefined",
    "unicode_escape",
    "raw-unicode-escape",
    "unicode-escape",
    "string-escape",
    "string_escape",
])


class NamespacedAttribute(str): | bs4, collections, re, sys, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/formatter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Describes a strategy to use when outputting a parse tree to a string.

    Some parts of this strategy come from the distinction between
    HTML4, HTML5, and XML. Others are configurable by the user.

    Formatters are passed in as the `formatter` argument to methods
    like `PageElement.encode`. Most people won't need to think about
    formatters, and most people who need to think about them can pass
    in one of these predefined strings as `formatter` rather than
    making a new Formatter object:

    For HTML documents:
     * 'html' - HTML entity substitution for generic HTML documents. (default)
     * 'html5' - HTML entity substitution for HTML5 documents, as
                 well as some optimizations in the way tags are rendered.
     * 'minimal' - Only make the substitutions necessary to guarantee
                   valid HTML.
     * None - Do not perform any substitution. This will be faster
              but may result in invalid markup.

    For XML documents:
     * 'html' - Entity substitution for XHTML documents.
     * 'minimal' - Only make the substitutions necessary to guarantee
                   valid XML. (default)
     * None - Do not perform any substitution. This will be faster
              but may result in invalid markup. | , bs4 |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Helper classes for tests."""

# Use of this source code is governed by the MIT license.
__license__ = "MIT"

import pickle
import copy
import functools
import warnings
import pytest
from bs4 import BeautifulSoup
from bs4.element import (
    CharsetMetaAttributeValue,
    Comment,
    ContentMetaAttributeValue,
    Doctype,
    PYTHON_SPECIFIC_ENCODINGS,
    SoupStrainer,
    Script,
    Stylesheet,
    Tag
)

from bs4.builder import (
    DetectsXMLParsedAsHTML,
    HTMLParserTreeBuilder,
    XMLParsedAsHTMLWarning,
)
default_builder = HTMLParserTreeBuilder

# Some tests depend on specific third-party libraries. We use
# @pytest.mark.skipIf on the following conditionals to skip them
# if the libraries are not installed.
try:
    from soupsieve import SelectorSyntaxError
    SOUP_SIEVE_PRESENT = True
except ImportError:
    SOUP_SIEVE_PRESENT = False

try:
    import html5lib
    HTML5LIB_PRESENT = True
except ImportError:
    HTML5LIB_PRESENT = False

try:
    import lxml.etree
    LXML_PRESENT = True
    LXML_VERSION = lxml.etree.LXML_VERSION
except ImportError:
    LXML_PRESENT = False
    LXML_VERSION = (0,)

BAD_DOCUMENT = | bs4, copy, functools, html5lib, lxml, pickle, pytest, soupsieve, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_builder.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | bs4, pytest, unittest |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_builder_registry.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests of the builder registry."""

import pytest
import warnings

from bs4 import BeautifulSoup
from bs4.builder import (
    builder_registry as registry,
    HTMLParserTreeBuilder,
    TreeBuilderRegistry,
)

from . import (
    HTML5LIB_PRESENT,
    LXML_PRESENT,
)

if HTML5LIB_PRESENT:
    from bs4.builder import HTML5TreeBuilder

if LXML_PRESENT:
    from bs4.builder import (
        LXMLTreeBuilderForXML,
        LXMLTreeBuilder,
        )


# TODO: Split out the lxml and html5lib tests into their own classes
# and gate with pytest.mark.skipIf.
class TestBuiltInRegistry(object): | , bs4, pytest, warnings | L28: # TODO: Split out the lxml and html5lib tests into their own classes |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_css.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Test basic CSS selector functionality.

    This functionality is implemented in soupsieve, which has a much
    more comprehensive test suite, so this is basically an extra check
    that soupsieve works as expected. | , bs4, pytest, soupsieve, types, unittest |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_dammit.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Standalone tests of UnicodeDammit."""

    def test_unicode_input(self):
        markup = "I'm already Unicode! \N{SNOWMAN}"
        dammit = UnicodeDammit(markup)
        assert dammit.unicode_markup == markup

    @pytest.mark.parametrize(
        "smart_quotes_to,expect_converted",
        [(None, "\u2018\u2019\u201c\u201d"),
         ("xml", "&#x2018;&#x2019;&#x201C;&#x201D;"),
         ("html", "&lsquo;&rsquo;&ldquo;&rdquo;"),
         ("ascii", "''" + '""'),
        ]
    )
    def test_smart_quotes_to(self, smart_quotes_to, expect_converted): | bs4, logging, pytest |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_docs.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | atexit, doctest, os, unittest | L3: # TODO: Pretty sure this isn't used and should be deleted. |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_element.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests of classes in element.py.

The really big classes -- Tag, PageElement, and NavigableString --
are tested in separate files. | , bs4 |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_formatter.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , bs4, pytest |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_fuzz.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This file contains test cases reported by third parties using
fuzzing tools, primarily from Google's oss-fuzz project. Some of these
represent real problems with Beautiful Soup, but many are problems in
libraries that Beautiful Soup depends on, and many of the test cases
represent different ways of triggering the same problem.

Grouping these test cases together makes it easy to see which test
cases represent the same problem, and puts the test cases in close
proximity to code that can trigger the problems. | bs4, os, pytest | L40: # as part of [bug=1471755]. |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_html5lib.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests to ensure that the html5lib tree builder generates good trees."""

import pytest
import warnings

from bs4 import BeautifulSoup
from bs4.element import SoupStrainer
from . import (
    HTML5LIB_PRESENT,
    HTML5TreeBuilderSmokeTest,
    SoupTest,
)

@pytest.mark.skipif(
    not HTML5LIB_PRESENT,
    reason="html5lib seems not to be present, not testing its tree builder."
)
class TestHTML5LibBuilder(SoupTest, HTML5TreeBuilderSmokeTest): | , bs4, pytest, warnings | L134: https://bugs.launchpad.net/beautifulsoup/+bug/1782928
L152: https://bugs.launchpad.net/beautifulsoup/+bug/1806598 |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_htmlparser.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests to ensure that the html.parser tree builder generates good
trees. | , bs4, pdb, pickle, pytest, warnings | L27: # https://bugs.chromium.org/p/oss-fuzz/issues/detail?id=28873 |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_lxml.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests to ensure that the lxml tree builder generates good trees."""

import pickle
import pytest
import re
import warnings
from . import LXML_PRESENT, LXML_VERSION

if LXML_PRESENT:
    from bs4.builder import LXMLTreeBuilder, LXMLTreeBuilderForXML

from bs4 import (
    BeautifulSoup,
    BeautifulStoneSoup,
    )
from bs4.element import Comment, Doctype, SoupStrainer
from . import (
    HTMLTreeBuilderSmokeTest,
    XMLTreeBuilderSmokeTest,
    SOUP_SIEVE_PRESENT,
    SoupTest,
)

@pytest.mark.skipif(
    not LXML_PRESENT,
    reason="lxml seems not to be present, not testing its tree builder."
)
class TestLXMLTreeBuilder(SoupTest, HTMLTreeBuilderSmokeTest): | , bs4, pickle, pytest, re, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_navigablestring.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Text inside a CData object is passed into the formatter.

        But the return value is ignored. | , bs4, pytest |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_pageelement.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests of the bs4.element.PageElement class"""
import copy
import pickle
import pytest
import sys

from bs4 import BeautifulSoup
from bs4.element import (
    Comment,
    ResultSet,
    SoupStrainer,
)
from . import (
    SoupTest,
)

class TestEncoding(SoupTest): | , bs4, copy, pickle, pytest, sys |  |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_soup.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests of Beautiful Soup as a whole."""

from pdb import set_trace
import logging
import os
import pickle
import pytest
import sys
import tempfile

from bs4 import (
    BeautifulSoup,
    BeautifulStoneSoup,
    GuessedAtParserWarning,
    MarkupResemblesLocatorWarning,
    dammit,
)
from bs4.builder import (
    builder_registry,
    TreeBuilder,
    ParserRejectedMarkup,
)
from bs4.element import (
    Comment,
    SoupStrainer,
    PYTHON_SPECIFIC_ENCODINGS,
    Tag,
    NavigableString,
)

from . import (
    default_builder,
    LXML_PRESENT,
    SoupTest,
)
import warnings
    
class TestConstructor(SoupTest):

    def test_short_unicode_input(self):
        data = "<h1>éé</h1>"
        soup = self.soup(data)
        assert "éé" == soup.h1.string

    def test_embedded_null(self):
        data = "<h1>foo\0bar</h1>"
        soup = self.soup(data)
        assert "foo\0bar" == soup.h1.string

    def test_exclude_encodings(self):
        utf8_data = "Räksmörgås".encode("utf-8")
        soup = self.soup(utf8_data, exclude_encodings=["utf-8"])
        assert "windows-1252" == soup.original_encoding

    def test_custom_builder_class(self):
        # Verify that you can pass in a custom Builder class and
        # it'll be instantiated with the appropriate keyword arguments.
        class Mock(object):
            def __init__(self, **kwargs):
                self.called_with = kwargs
                self.is_xml = True
                self.store_line_numbers = False
                self.cdata_list_attributes = []
                self.preserve_whitespace_tags = []
                self.string_containers = {}
            def initialize_soup(self, soup):
                pass
            def feed(self, markup):
                self.fed = markup
            def reset(self):
                pass
            def ignore(self, ignore):
                pass
            set_up_substitutions = can_be_empty_element = ignore
            def prepare_markup(self, *args, **kwargs):
                yield "prepared markup", "original encoding", "declared encoding", "contains replacement characters"
                
        kwargs = dict(
            var="value",
            # This is a deprecated BS3-era keyword argument, which
            # will be stripped out.
            convertEntities=True,
        )
        with warnings.catch_warnings(record=True):
            soup = BeautifulSoup('', builder=Mock, **kwargs)
        assert isinstance(soup.builder, Mock)
        assert dict(var="value") == soup.builder.called_with
        assert "prepared markup" == soup.builder.fed
        
        # You can also instantiate the TreeBuilder yourself. In this
        # case, that specific object is used and any keyword arguments
        # to the BeautifulSoup constructor are ignored.
        builder = Mock(**kwargs)
        with warnings.catch_warnings(record=True) as w:
            soup = BeautifulSoup(
                '', builder=builder, ignored_value=True,
            )
        msg = str(w[0].message)
        assert msg.startswith("Keyword arguments to the BeautifulSoup constructor will be ignored.")
        assert builder == soup.builder
        assert kwargs == builder.called_with

    def test_parser_markup_rejection(self):
        # If markup is completely rejected by the parser, an
        # explanatory ParserRejectedMarkup exception is raised.
        class Mock(TreeBuilder):
            def feed(self, *args, **kwargs):
                raise ParserRejectedMarkup("Nope.")

        def prepare_markup(self, *args, **kwargs):
            # We're going to try two different ways of preparing this markup,
            # but feed() will reject both of them.
            yield markup, None, None, False
            yield markup, None, None, False
            

        import re
        with pytest.raises(ParserRejectedMarkup) as exc_info:
            BeautifulSoup('', builder=Mock)
        assert "The markup you provided was rejected by the parser. Trying a different parser or a different encoding may help." in str(exc_info.value)
        
    def test_cdata_list_attributes(self):
        # Most attribute values are represented as scalars, but the
        # HTML standard says that some attributes, like 'class' have
        # space-separated lists as values.
        markup = '<a id=" an id " class=" a class "></a>'
        soup = self.soup(markup)

        # Note that the spaces are stripped for 'class' but not for 'id'.
        a = soup.a
        assert " an id " == a['id']
        assert ["a", "class"] == a['class']

        # TreeBuilder takes an argument called 'multi_valued_attributes'  which lets
        # you customize or disable this. As always, you can customize the TreeBuilder
        # by passing in a keyword argument to the BeautifulSoup constructor.
        soup = self.soup(markup, builder=default_builder, multi_valued_attributes=None)
        assert " a class " == soup.a['class']

        # Here are two ways of saying that `id` is a multi-valued
        # attribute in this context, but 'class' is not.
        for switcheroo in ({'*': 'id'}, {'a': 'id'}):
            with warnings.catch_warnings(record=True) as w:
                # This will create a warning about not explicitly
                # specifying a parser, but we'll ignore it.
                soup = self.soup(markup, builder=None, multi_valued_attributes=switcheroo)
            a = soup.a
            assert ["an", "id"] == a['id']
            assert " a class " == a['class']

    def test_replacement_classes(self):
        # Test the ability to pass in replacements for element classes
        # which will be used when building the tree.
        class TagPlus(Tag):
            pass

        class StringPlus(NavigableString):
            pass

        class CommentPlus(Comment):
            pass
        
        soup = self.soup(
            "<a><b>foo</b>bar</a><!--whee-->",
            element_classes = {
                Tag: TagPlus,
                NavigableString: StringPlus,
                Comment: CommentPlus,
            }
        )

        # The tree was built with TagPlus, StringPlus, and CommentPlus objects,
        # rather than Tag, String, and Comment objects.
        assert all(
            isinstance(x, (TagPlus, StringPlus, CommentPlus))
            for x in soup.recursiveChildGenerator()
        )

    def test_alternate_string_containers(self):
        # Test the ability to customize the string containers for
        # different types of tags.
        class PString(NavigableString):
            pass

        class BString(NavigableString):
            pass

        soup = self.soup(
            "<div>Hello.<p>Here is <b>some <i>bolded</i></b> text",
            string_containers = {
                'b': BString,
                'p': PString,
            }
        )

        # The string before the <p> tag is a regular NavigableString.
        assert isinstance(soup.div.contents[0], NavigableString)
        
        # The string inside the <p> tag, but not inside the <i> tag,
        # is a PString.
        assert isinstance(soup.p.contents[0], PString)

        # Every string inside the <b> tag is a BString, even the one that
        # was also inside an <i> tag.
        for s in soup.b.strings:
            assert isinstance(s, BString)

        # Now that parsing was complete, the string_container_stack
        # (where this information was kept) has been cleared out.
        assert [] == soup.string_container_stack


class TestOutput(SoupTest):

    @pytest.mark.parametrize(
        "eventual_encoding,actual_encoding", [
            ("utf-8", "utf-8"),
            ("utf-16", "utf-16"),
        ]
    )
    def test_decode_xml_declaration(self, eventual_encoding, actual_encoding):
        # Most of the time, calling decode() on an XML document will
        # give you a document declaration that mentions the encoding
        # you intend to use when encoding the document as a
        # bytestring.
        soup = self.soup("<tag></tag>")
        soup.is_xml = True
        assert (f'<?xml version="1.0" encoding="{actual_encoding}"?>\n<tag></tag>'
                == soup.decode(eventual_encoding=eventual_encoding))

    @pytest.mark.parametrize(
        "eventual_encoding", [x for x in PYTHON_SPECIFIC_ENCODINGS] + [None]
    )
    def test_decode_xml_declaration_with_missing_or_python_internal_eventual_encoding(self, eventual_encoding):
        # But if you pass a Python internal encoding into decode(), or
        # omit the eventual_encoding altogether, the document
        # declaration won't mention any particular encoding.
        soup = BeautifulSoup("<tag></tag>", "html.parser")
        soup.is_xml = True
        assert (f'<?xml version="1.0"?>\n<tag></tag>'
                == soup.decode(eventual_encoding=eventual_encoding))

    def test(self):
        # BeautifulSoup subclasses Tag and extends the decode() method.
        # Make sure the other Tag methods which call decode() call
        # it correctly.
        soup = self.soup("<tag></tag>")
        assert b"<tag></tag>" == soup.encode(encoding="utf-8")
        assert b"<tag></tag>" == soup.encode_contents(encoding="utf-8")
        assert "<tag></tag>" == soup.decode_contents()
        assert "<tag>\n</tag>\n" == soup.prettify()

        
class TestWarnings(SoupTest):
    # Note that some of the tests in this class create BeautifulSoup
    # objects directly rather than using self.soup(). That's
    # because SoupTest.soup is defined in a different file,
    # which will throw off the assertion in _assert_warning
    # that the code that triggered the warning is in the same
    # file as the test.

    def _assert_warning(self, warnings, cls):
        for w in warnings:
            if isinstance(w.message, cls):
                assert w.filename == __file__
                return w
        raise Exception("%s warning not found in %r" % (cls, warnings))
    
    def _assert_no_parser_specified(self, w):
        warning = self._assert_warning(w, GuessedAtParserWarning)
        message = str(warning.message)
        assert message.startswith(BeautifulSoup.NO_PARSER_SPECIFIED_WARNING[:60])

    def test_warning_if_no_parser_specified(self):
        with warnings.catch_warnings(record=True) as w:
            soup = BeautifulSoup("<a><b></b></a>")
        self._assert_no_parser_specified(w)

    def test_warning_if_parser_specified_too_vague(self):
        with warnings.catch_warnings(record=True) as w:
            soup = BeautifulSoup("<a><b></b></a>", "html")
        self._assert_no_parser_specified(w)

    def test_no_warning_if_explicit_parser_specified(self):
        with warnings.catch_warnings(record=True) as w:
            soup = self.soup("<a><b></b></a>")
        assert [] == w

    def test_parseOnlyThese_renamed_to_parse_only(self):
        with warnings.catch_warnings(record=True) as w:
            soup = BeautifulSoup(
                "<a><b></b></a>", "html.parser",
                parseOnlyThese=SoupStrainer("b"),
            )
        warning = self._assert_warning(w, DeprecationWarning)
        msg = str(warning.message)
        assert "parseOnlyThese" in msg
        assert "parse_only" in msg
        assert b"<b></b>" == soup.encode() | , bs4, logging, os, pdb, pickle, pytest, re, sys, tempfile, warnings | L448: # We had a bug that prevented pickling from working if |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_tag.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Test various methods of Tag which aren't so complicated they
    need their own classes. | , bs4, warnings | L216: # TODO: This code is in the builder and should be tested there. |
| `blackboard-agent/venv/Lib/site-packages/bs4/tests/test_tree.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Tests for Beautiful Soup's tree traversal methods.

The tree traversal methods are the main advantage of using Beautiful
Soup over just using a parser.

Different parsers will build different Beautiful Soup trees given the
same markup, but all Beautiful Soup trees can be traversed with the
methods tested here. | , bs4, pdb, pytest, re, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/certifi/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/certifi/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | argparse, certifi |  |
| `blackboard-agent/venv/Lib/site-packages/certifi/core.py` | ❓ UNKNOWN | 2025-11-09 19:12 | certifi.py
~~~~~~~~~~

This module returns the installation location of cacert.pem or its contents. | atexit, importlib, sys |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/_imp_emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | _imp, imp, importlib, os, sys, tokenize |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/_shimmed_dist_utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Temporary shim module to indirect the bits of distutils we need from setuptools/distutils while providing useful
error messages beyond `No module named 'distutils' on Python >= 3.12, or when setuptools' vendored distutils is broken.

This is a compromise to avoid a hard-dep on setuptools for Python >= 3.12, since many users don't need runtime compilation support from CFFI. | distutils, setuptools, sys |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/api.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The main top-level class that you instantiate once, or once per module.

    Example usage:

        ffi = FFI()
        ffi.cdef("""
            int printf(const char *, ...);
        """)

        C = ffi.dlopen(None)   # standard library
        -or-
        C = ffi.verify()  # use a C compiler: verify the decl above is right

        C.printf("hello, %s!\n", ffi.new("char[]", "world")) | , _cffi_backend, collections, sys |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/backend_ctypes.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , ctypes |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/cffi_opcode.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/commontypes.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , _cffi_backend, sys |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/cparser.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , _thread, pycparser, thread, warnings, weakref | L209: # BIG HACK: replace WINAPI or __stdcall with "volatile const".
L212: # Hack number 2 is that "int(volatile *fptr)();" is not valid C
L332: csourcelines.append('')   # see test_missing_newline_bug
L343: # csource will be used to find buggy source text |
| `blackboard-agent/venv/Lib/site-packages/cffi/error.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An error raised when verification fails |  |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/ffiplatform.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Compile a C extension module using distutils."""

    saved_environ = os.environ.copy()
    try:
        outputfilename = _build(tmpdir, ext, compiler_verbose, debug)
        outputfilename = os.path.abspath(outputfilename)
    finally:
        # workaround for a distutils bugs where some env vars can
        # become longer and longer every time it is used
        for key, value in saved_environ.items():
            if os.environ.get(key) != value:
                os.environ[key] = value
    return outputfilename

def _build(tmpdir, ext, compiler_verbose=0, debug=None):
    # XXX compact but horrible :-(
    from cffi._shimmed_dist_utils import Distribution, CompileError, LinkError, set_threshold, set_verbosity

    dist = Distribution({'ext_modules': [ext]})
    dist.parse_config_files()
    options = dist.get_option_dict('build_ext')
    if debug is None:
        debug = sys.flags.debug
    options['debug'] = ('ffiplatform', debug)
    options['force'] = ('ffiplatform', True)
    options['build_lib'] = ('ffiplatform', tmpdir)
    options['build_temp'] = ('ffiplatform', tmpdir)
    #
    try:
        old_level = set_threshold(0) or 0
        try:
            set_verbosity(compiler_verbose)
            dist.run_command('build_ext')
            cmd_obj = dist.get_command_obj('build_ext')
            [soname] = cmd_obj.get_outputs()
        finally:
            set_threshold(old_level)
    except (CompileError, LinkError) as e:
        raise VerificationError('%s: %s' % (e.__class__.__name__, e))
    #
    return soname

try:
    from os.path import samefile
except ImportError:
    def samefile(f1, f2):
        return os.path.abspath(f1) == os.path.abspath(f2)

def maybe_relative_path(path):
    if not os.path.isabs(path):
        return path      # already relative
    dir = path
    names = []
    while True:
        prevdir = dir
        dir, name = os.path.split(prevdir)
        if dir == prevdir or not dir:
            return path     # failed to make it relative
        names.append(name)
        try:
            if samefile(dir, os.curdir):
                names.reverse()
                return os.path.join(*names)
        except OSError:
            pass

# ____________________________________________________________

try:
    int_or_long = (int, long)
    import cStringIO
except NameError:
    int_or_long = int      # Python 3
    import io as cStringIO

def _flatten(x, f):
    if isinstance(x, str):
        f.write('%ds%s' % (len(x), x))
    elif isinstance(x, dict):
        keys = sorted(x.keys())
        f.write('%dd' % len(keys))
        for key in keys:
            _flatten(key, f)
            _flatten(x[key], f)
    elif isinstance(x, (list, tuple)):
        f.write('%dl' % len(x))
        for value in x:
            _flatten(value, f)
    elif isinstance(x, int_or_long):
        f.write('%di' % (x,))
    else:
        raise TypeError(
            "the keywords to verify() contains unsupported object %r" % (x,))

def flatten(x):
    f = cStringIO.StringIO()
    _flatten(x, f)
    return f.getvalue() | , cffi, cStringIO, io, os, sys | L15: def compile(tmpdir, ext, compiler_verbose=0, debug=None):
L20: outputfilename = _build(tmpdir, ext, compiler_verbose, debug)
L23: # workaround for a distutils bugs where some env vars can
L30: def _build(tmpdir, ext, compiler_verbose=0, debug=None):
L37: if debug is None:
L38: debug = sys.flags.debug
L39: options['debug'] = ('ffiplatform', debug) |
| `blackboard-agent/venv/Lib/site-packages/cffi/lock.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | _dummy_thread, _thread, dummy_thread, sys, thread |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/model.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , types, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/pkgconfig.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Merge values from cffi config flags cfg2 to cf1

    Example:
        merge_flags({"libraries": ["one"]}, {"libraries": ["two"]})
        {"libraries": ["one", "two"]} | , sys |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/recompiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , io |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/setuptools_ext.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Add py_limited_api to kwds if setuptools >= 26 is in use.
    Do not alter the setting if it already exists.
    Setuptools takes care of ignoring the flag on Python 2 and PyPy.

    CPython itself should ignore the flag in a debugging version
    (by not listing .abi3.so in the extensions it supports), but
    it doesn't so far, creating troubles.  That's why we check
    for "not hasattr(sys, 'gettotalrefcount')" (the 2.7 compatible equivalent
    of 'd' not in sys.abiflags). (http://bugs.python.org/issue28401)

    On Windows, with CPython <= 3.4, it's better not to use py_limited_api
    because virtualenv *still* doesn't copy PYTHON3.DLL on these versions.
    Recently (2020) we started shipping only >= 3.5 wheels, though.  So
    we'll give it another try and set py_limited_api on Windows >= 3.5. | cffi, os, setuptools, sys, sysconfig | L80: CPython itself should ignore the flag in a debugging version
L84: of 'd' not in sys.abiflags). (http://bugs.python.org/issue28401)
L203: # Then we need to hack more in get_source_files(); see above. |
| `blackboard-agent/venv/Lib/site-packages/cffi/vengine_cpy.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , sys, warnings | L45: # a KeyError here is a bug.  please report it! :-) |
| `blackboard-agent/venv/Lib/site-packages/cffi/vengine_gen.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , sys, types |  |
| `blackboard-agent/venv/Lib/site-packages/cffi/verifier.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Write the C source code.  It is produced in 'self.sourcefilename',
        which can be tweaked beforehand. | , _cffi_backend, imp, importlib, sys | L113: # and the _d added in Python 2 debug builds --- but try to be |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Charset-Normalizer
~~~~~~~~~~~~~~
The Real First Universal Charset Detector.
A library that helps you read text from an unknown charset encoding.
Motivated by chardet, This package is trying to resolve the issue by taking a new approach.
All IANA character set names for which the Python core library provides codecs are supported.

Basic usage:
   >>> from charset_normalizer import from_bytes
   >>> results = from_bytes('Bсеки човек има право на образование. Oбразованието!'.encode('utf_8'))
   >>> best_guess = results.best()
   >>> str(best_guess)
   'Bсеки човек има право на образование. Oбразованието!'

Others methods and usages are available - see the full documentation
at <https://github.com/Ousret/charset_normalizer>.
:copyright: (c) 2021 by Ahmed TAHRI
:license: MIT, see LICENSE for more details. | , __future__, logging |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/api.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Given a raw bytes sequence, return the best possibles charset usable to render str objects.
    If there is no results, it is a strong indicator that the source is binary/not text.
    By default, the process will extract 5 blocks of 512o each to assess the mess and coherence of a given sequence.
    And will give up a particular code page after 20% of measured mess. Those criteria are customizable at will.

    The preemptive behavior DOES NOT replace the traditional detection workflow, it prioritize a particular code page
    but never take it for granted. Can improve the performance.

    You may want to focus your attention to some code page or/and not others, use cp_isolation and cp_exclusion for that
    purpose.

    This function will strip the SIG in the payload/sequence every time except on UTF-16, UTF-32.
    By default the library does not setup any handler other than the NullHandler, if you choose to set the 'explain'
    toggle to True it will alter the logger configuration to add a StreamHandler that is suitable for debugging.
    Custom logging format and handler can be set manually. | , __future__, logging, os, typing | L59: toggle to True it will alter the logger configuration to add a StreamHandler that is suitable for debugging.
L78: logger.debug("Encoding detection on empty bytes, assuming utf_8 intention.")
L87: "cp_isolation is set. use this flag for debugging purpose. "
L98: "cp_exclusion is set. use this flag for debugging purpose. "
L462: logger.debug(
L480: logger.debug(
L491: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/cd.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Return associated unicode ranges in a single byte code page. | , __future__, codecs, collections, functools, importlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/cli/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/cli/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Ask a yes/no question via input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".

    Credit goes to (c) https://stackoverflow.com/questions/3041986/apt-command-line-interface-like-yes-no-input | __future__, argparse, charset_normalizer, json, os, platform, sys, typing, unicodedata |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/constant.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | __future__, codecs, encodings, re | L86: "Buginese": range(6656, 6688), |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/legacy.py` | ❓ UNKNOWN | 2025-11-09 19:11 | chardet legacy method
    Detect the encoding of the given byte string. It should be mostly backward-compatible.
    Encoding name will match Chardet own writing whenever possible. (Not on encoding name unsupported by it)
    This function is deprecated and should be used to migrate your project easily, consult the documentation for
    further information. Not planned for removal.

    :param byte_str:     The byte sequence to examine.
    :param should_rename_legacy:  Should we rename legacy encodings
                                  to their more modern equivalents? | , __future__, typing, typing_extensions, warnings | L9: # TODO: remove this check when dropping Python 3.7 support |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/md.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Base abstract class used for mess detection plugins.
    All detectors MUST extend and implement given methods. | , __future__, functools, logging |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/models.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Implemented to make sorted available upon CharsetMatches items. | , __future__, charset_normalizer, encodings, hashlib, json, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/utils.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Retrieve the Unicode range official name from a single character. | , __future__, _multibytecodec, codecs, encodings, functools, importlib, logging, re, typing, unicodedata | L220: and character != "\ufeff"  # bug discovered in Python, |
| `blackboard-agent/venv/Lib/site-packages/charset_normalizer/version.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Expose version | __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/distro/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/distro/__main__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/distro/distro.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The ``distro`` package (``distro`` stands for Linux Distribution) provides
information about the Linux distribution it runs on, such as a reliable
machine-readable distro ID, or version information.

It is the recommended replacement for Python's original
:py:func:`platform.linux_distribution` function, but it provides much more
functionality. An alternative implementation became necessary because Python
3.5 deprecated this function, and Python 3.8 removed it altogether. Its
predecessor function :py:func:`platform.dist` was already deprecated since
Python 2.6 and removed in Python 3.8. Still, there are many cases in which
access to OS distribution information is needed. See `Python issue 1322
<https://bugs.python.org/issue1322>`_ for more information. | argparse, json, logging, os, re, shlex, subprocess, sys, typing, warnings | L28: <https://bugs.python.org/issue1322>`_ for more information. |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Parse docstrings as per Sphinx notation."""

from .common import (
    Docstring,
    DocstringDeprecated,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)
from .parser import compose, parse, parse_from_object
from .util import combine_docstrings

Style = DocstringStyle  # backwards compatibility

__all__ = [
    "parse",
    "parse_from_object",
    "combine_docstrings",
    "compose",
    "ParseError",
    "Docstring",
    "DocstringMeta",
    "DocstringParam",
    "DocstringRaises",
    "DocstringReturns",
    "DocstringDeprecated",
    "DocstringStyle",
    "RenderingStyle",
    "Style",
] |  |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/attrdoc.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Attribute docstrings parsing.

.. seealso:: https://peps.python.org/pep-0257/#what-is-a-docstring | , ast, inspect, textwrap, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/common.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Common methods for parsing."""

import enum
import typing as T

PARAM_KEYWORDS = {
    "param",
    "parameter",
    "arg",
    "argument",
    "attribute",
    "key",
    "keyword",
}
RAISES_KEYWORDS = {"raises", "raise", "except", "exception"}
DEPRECATION_KEYWORDS = {"deprecation", "deprecated"}
RETURNS_KEYWORDS = {"return", "returns"}
YIELDS_KEYWORDS = {"yield", "yields"}
EXAMPLES_KEYWORDS = {"example", "examples"}


class ParseError(RuntimeError): | enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/epydoc.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Epyoc-style docstring parsing.

.. seealso:: http://epydoc.sourceforge.net/manual-fields.html | , inspect, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/google.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Google-style docstring parsing."""

import inspect
import re
import typing as T
from collections import OrderedDict, namedtuple
from enum import IntEnum

from .common import (
    EXAMPLES_KEYWORDS,
    PARAM_KEYWORDS,
    RAISES_KEYWORDS,
    RETURNS_KEYWORDS,
    YIELDS_KEYWORDS,
    Docstring,
    DocstringExample,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)


class SectionType(IntEnum): | , collections, enum, inspect, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/numpydoc.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Numpydoc-style docstring parsing.

:see: https://numpydoc.readthedocs.io/en/latest/format.html | , inspect, itertools, re, textwrap, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/parser.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The main parsing routine."""

import inspect
import typing as T

from docstring_parser import epydoc, google, numpydoc, rest
from docstring_parser.attrdoc import add_attribute_docstrings
from docstring_parser.common import (
    Docstring,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)

_STYLE_MAP = {
    DocstringStyle.REST: rest,
    DocstringStyle.GOOGLE: google,
    DocstringStyle.NUMPYDOC: numpydoc,
    DocstringStyle.EPYDOC: epydoc,
}


def parse(text: str, style: DocstringStyle = DocstringStyle.AUTO) -> Docstring: | docstring_parser, inspect, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/rest.py` | ❓ UNKNOWN | 2025-11-09 21:03 | ReST-style docstring parsing."""

import inspect
import re
import typing as T

from .common import (
    DEPRECATION_KEYWORDS,
    PARAM_KEYWORDS,
    RAISES_KEYWORDS,
    RETURNS_KEYWORDS,
    YIELDS_KEYWORDS,
    Docstring,
    DocstringDeprecated,
    DocstringMeta,
    DocstringParam,
    DocstringRaises,
    DocstringReturns,
    DocstringStyle,
    ParseError,
    RenderingStyle,
)


def _build_meta(args: T.List[str], desc: str) -> DocstringMeta:
    key = args[0]

    if key in PARAM_KEYWORDS:
        if len(args) == 3:
            key, type_name, arg_name = args
            if type_name.endswith("?"):
                is_optional = True
                type_name = type_name[:-1]
            else:
                is_optional = False
        elif len(args) == 2:
            key, arg_name = args
            type_name = None
            is_optional = None
        else:
            raise ParseError(
                f"Expected one or two arguments for a {key} keyword."
            )

        match = re.match(r".*defaults to (.+)", desc, flags=re.DOTALL)
        default = match.group(1).rstrip(".") if match else None

        return DocstringParam(
            args=args,
            description=desc,
            arg_name=arg_name,
            type_name=type_name,
            is_optional=is_optional,
            default=default,
        )

    if key in RETURNS_KEYWORDS \\| YIELDS_KEYWORDS:
        if len(args) == 2:
            type_name = args[1]
        elif len(args) == 1:
            type_name = None
        else:
            raise ParseError(
                f"Expected one or no arguments for a {key} keyword."
            )

        return DocstringReturns(
            args=args,
            description=desc,
            type_name=type_name,
            is_generator=key in YIELDS_KEYWORDS,
        )

    if key in DEPRECATION_KEYWORDS:
        match = re.search(
            r"^(?P<version>v?((?:\d+)(?:\.[0-9a-z\.]+))) (?P<desc>.+)",
            desc,
            flags=re.I,
        )
        return DocstringDeprecated(
            args=args,
            version=match.group("version") if match else None,
            description=match.group("desc") if match else desc,
        )

    if key in RAISES_KEYWORDS:
        if len(args) == 2:
            type_name = args[1]
        elif len(args) == 1:
            type_name = None
        else:
            raise ParseError(
                f"Expected one or no arguments for a {key} keyword."
            )
        return DocstringRaises(
            args=args, description=desc, type_name=type_name
        )

    return DocstringMeta(args=args, description=desc)


def parse(text: str) -> Docstring: | , inspect, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for docstring parser.""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/_pydoctor.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Private pydoctor customization code in order to exclude the package
docstring_parser.tests from the API documentation. Based on Twisted code. | pydoctor |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_epydoc.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for epydoc-style docstring routines."""

import typing as T

import pytest
from docstring_parser.common import ParseError, RenderingStyle
from docstring_parser.epydoc import compose, parse


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None: | docstring_parser, pytest, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_google.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for Google-style docstring routines."""

import typing as T

import pytest
from docstring_parser.common import ParseError, RenderingStyle
from docstring_parser.google import (
    GoogleParser,
    Section,
    SectionType,
    compose,
    parse,
)


def test_google_parser_unknown_section() -> None: | docstring_parser, pytest, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_numpydoc.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for numpydoc-style docstring routines."""

import typing as T

import pytest
from docstring_parser.numpydoc import compose, parse


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None: | docstring_parser, pytest, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_parse_from_object.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for parse_from_object function and attribute docstrings."""

from unittest.mock import patch

from docstring_parser import parse_from_object

module_attr: int = 1 | , docstring_parser, unittest |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_parser.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for generic docstring routines."""

import pytest
from docstring_parser.common import DocstringStyle, ParseError
from docstring_parser.parser import parse


def test_rest() -> None: | docstring_parser, pytest |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_rest.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tests for ReST-style docstring routines."""

import typing as T

import pytest
from docstring_parser.common import ParseError, RenderingStyle
from docstring_parser.rest import compose, parse


@pytest.mark.parametrize(
    "source, expected",
    [
        ("", None),
        ("\n", None),
        ("Short description", "Short description"),
        ("\nShort description\n", "Short description"),
        ("\n   Short description\n", "Short description"),
    ],
)
def test_short_description(source: str, expected: str) -> None: | docstring_parser, pytest, typing |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/tests/test_util.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Test for utility functions."""

from docstring_parser.common import DocstringReturns
from docstring_parser.util import combine_docstrings


def test_combine_docstrings() -> None: | docstring_parser |  |
| `blackboard-agent/venv/Lib/site-packages/docstring_parser/util.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Utility functions for working with docstrings."""

import typing as T
from collections import ChainMap
from inspect import Signature
from itertools import chain

from .common import (
    DocstringMeta,
    DocstringParam,
    DocstringReturns,
    DocstringStyle,
    RenderingStyle,
)
from .parser import compose, parse

_Func = T.Callable[..., T.Any]

assert DocstringReturns  # used in docstring


def combine_docstrings(
    *others: _Func,
    exclude: T.Iterable[T.Type[DocstringMeta]] = (),
    style: DocstringStyle = DocstringStyle.AUTO,
    rendering_style: RenderingStyle = RenderingStyle.COMPACT,
) -> _Func: | , collections, inspect, itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Returns a string suitable for running as a shell script.

    Useful for converting a arguments passed to a fabric task
    to be passed to a `local` or `run` command. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Entry point for cli, enables execution with `python -m dotenv`"""

from .cli import cli

if __name__ == "__main__":
    cli() |  |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/cli.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Return a path for the ${pwd}/.env file.

    If pwd does not exist, return None. | , click, contextlib, json, os, shlex, subprocess, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/ipython.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Register the %dotenv magic."""
    ipython.register_magics(IPythonDotEnv) | , IPython |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/main.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Return dotenv as dict"""
        if self._dict:
            return self._dict

        raw_values = self.parse()

        if self.interpolate:
            self._dict = OrderedDict(resolve_variables(raw_values, override=self.override))
        else:
            self._dict = OrderedDict(raw_values)

        return self._dict

    def parse(self) -> Iterator[Tuple[str, Optional[str]]]:
        with self._get_stream() as stream:
            for mapping in with_warn_for_invalid_lines(parse_stream(stream)):
                if mapping.key is not None:
                    yield mapping.key, mapping.value

    def set_as_environment_variables(self) -> bool: | , collections, contextlib, io, logging, os, shutil, sys, tempfile, typing |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/parser.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | codecs, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/variables.py` | ❓ UNKNOWN | 2025-11-09 19:11 | \$\{
        (?P<name>[^\}:]*)
        (?::-
            (?P<default>[^\}]*)
        )?
    \} | abc, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/dotenv/version.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/h11/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | h11 |  |
| `blackboard-agent/venv/Lib/site-packages/h11/_abnf.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/h11/_connection.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An object encapsulating the state of an HTTP connection.

    Args:
        our_role: If you're implementing a client, pass :data:`h11.CLIENT`. If
            you're implementing a server, pass :data:`h11.SERVER`.

        max_incomplete_event_size (int):
            The maximum number of bytes we're willing to buffer of an
            incomplete event. In practice this mostly sets a limit on the
            maximum size of the request/response line + headers. If this is
            exceeded, then :meth:`next_event` will raise
            :exc:`RemoteProtocolError`. | , typing | L470: then that's a bug -- if it happens please file a bug report! |
| `blackboard-agent/venv/Lib/site-packages/h11/_events.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Base class for h11 events. | , abc, dataclasses, re, typing | L310: # XX FIXME: "A recipient MUST ignore (or consider as an error) any fields that |
| `blackboard-agent/venv/Lib/site-packages/h11/_headers.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A list-like interface that allows iterating over headers as byte-pairs
    of (lowercased-name, value).

    Internally we actually store the representation as three-tuples,
    including both the raw original casing, in order to preserve casing
    over-the-wire, and the lowercased name, for case-insensitive comparisions.

    r = Request(
        method="GET",
        target="/",
        headers=[("Host", "example.org"), ("Connection", "keep-alive")],
        http_version="1.1",
    )
    assert r.headers == [
        (b"host", b"example.org"),
        (b"connection", b"keep-alive")
    ]
    assert r.headers.raw_items() == [
        (b"Host", b"example.org"),
        (b"Connection", b"keep-alive")
    ] | , re, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/h11/_readers.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , re, typing | L186: # XX FIXME: we discard chunk extensions. Does anyone care? |
| `blackboard-agent/venv/Lib/site-packages/h11/_receivebuffer.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Extract a fixed number of bytes from the buffer. | re, sys, typing | L27: #     https://bugs.python.org/issue19087 |
| `blackboard-agent/venv/Lib/site-packages/h11/_state.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/h11/_util.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Exception indicating a violation of the HTTP/1.1 protocol.

    This as an abstract base class, with two concrete base classes:
    :exc:`LocalProtocolError`, which indicates that you tried to do something
    that HTTP/1.1 says is illegal, and :exc:`RemoteProtocolError`, which
    indicates that the remote peer tried to do something that HTTP/1.1 says is
    illegal. See :ref:`error-handling` for details.

    In addition to the normal :exc:`Exception` features, it has one attribute:

    .. attribute:: error_status_hint

       This gives a suggestion as to what status code a server might use if
       this error occurred as part of a request.

       For a :exc:`RemoteProtocolError`, this is useful as a suggestion for
       how you might want to respond to a misbehaving peer, if you're
       implementing a server.

       For a :exc:`LocalProtocolError`, this can be taken as a suggestion for
       how your peer might have responded to *you* if h11 had allowed you to
       continue.

       The default is 400 Bad Request, a generic catch-all for protocol
       violations. | typing |  |
| `blackboard-agent/venv/Lib/site-packages/h11/_version.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/h11/_writers.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , typing | L54: # XX FIXME: could at least make an effort to pull out the status message |
| `blackboard-agent/venv/Lib/site-packages/httpcore/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_api.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Sends an HTTP request, returning the response.

    ```
    response = httpcore.request("GET", "https://www.example.com/")
    ```

    Arguments:
        method: The HTTP method for the request. Typically one of `"GET"`,
            `"OPTIONS"`, `"HEAD"`, `"POST"`, `"PUT"`, `"PATCH"`, or `"DELETE"`.
        url: The URL of the HTTP request. Either as an instance of `httpcore.URL`,
            or as str/bytes.
        headers: The HTTP request headers. Either as a dictionary of str/bytes,
            or as a list of two-tuples of str/bytes.
        content: The content of the request body. Either as bytes,
            or as a bytes iterator.
        extensions: A dictionary of optional extra information included on the request.
            Possible keys include `"timeout"`.

    Returns:
        An instance of `httpcore.Response`. | , __future__, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/connection.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Generate a geometric sequence that has a ratio of 2 and starts with 0.

    For example:
    - `factor = 2`: `0, 2, 4, 8, 16, 32, 64, ...`
    - `factor = 3`: `0, 3, 6, 12, 24, 48, 96, ...` | , __future__, itertools, logging, ssl, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/connection_pool.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A connection pool for making HTTP requests. | , __future__, ssl, sys, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/http_proxy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Append default_headers and override_headers, de-duplicating if a key exists
    in both cases. | , __future__, base64, logging, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/http11.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, enum, h11, logging, ssl, time, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/http2.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The HTTP/2 connection requires some initial setup before we can start
        using individual request/response streams on it. | , __future__, enum, h2, logging, time, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/interfaces.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Return `True` if the connection is currently able to accept an
        outgoing request.

        An HTTP/1.1 connection will only be available if it is currently idle.

        An HTTP/2 connection will be available so long as the stream ID space is
        not yet exhausted, and the connection is not in an error state.

        While the connection is being established we may not yet know if it is going
        to result in an HTTP/1.1 or HTTP/2 connection. The connection should be
        treated as being available, but might ultimately raise `NewConnectionRequired`
        required exceptions if multiple requests are attempted over a connection
        that ends up being established as HTTP/1.1. | , __future__, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_async/socks_proxy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A connection pool that sends requests via an HTTP proxy. | , __future__, logging, socksio, ssl |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/anyio.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, anyio, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/auto.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/base.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, ssl, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/mock.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/sync.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Because the standard `SSLContext.wrap_socket` method does
    not work for `SSLSocket` objects, we need this class
    to implement TLS stream using an underlying `SSLObject`
    instance in order to support TLS on top of TLS. | , __future__, functools, socket, ssl, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_backends/trio.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, ssl, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_models.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Any arguments that are ultimately represented as bytes can be specified
    either as bytes or as strings.

    However we enforce that any string arguments must only contain characters in
    the plain ASCII range. chr(0)...chr(127). If you need to use characters
    outside that range then be precise, and use a byte-wise argument. | __future__, base64, ssl, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_ssl.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | certifi, ssl |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/connection.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Generate a geometric sequence that has a ratio of 2 and starts with 0.

    For example:
    - `factor = 2`: `0, 2, 4, 8, 16, 32, 64, ...`
    - `factor = 3`: `0, 3, 6, 12, 24, 48, 96, ...` | , __future__, itertools, logging, ssl, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/connection_pool.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A connection pool for making HTTP requests. | , __future__, ssl, sys, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/http_proxy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Append default_headers and override_headers, de-duplicating if a key exists
    in both cases. | , __future__, base64, logging, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/http11.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, enum, h11, logging, ssl, time, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/http2.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The HTTP/2 connection requires some initial setup before we can start
        using individual request/response streams on it. | , __future__, enum, h2, logging, time, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/interfaces.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Return `True` if the connection is currently able to accept an
        outgoing request.

        An HTTP/1.1 connection will only be available if it is currently idle.

        An HTTP/2 connection will be available so long as the stream ID space is
        not yet exhausted, and the connection is not in an error state.

        While the connection is being established we may not yet know if it is going
        to result in an HTTP/1.1 or HTTP/2 connection. The connection should be
        treated as being available, but might ultimately raise `NewConnectionRequired`
        required exceptions if multiple requests are attempted over a connection
        that ends up being established as HTTP/1.1. | , __future__, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_sync/socks_proxy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A connection pool that sends requests via an HTTP proxy. | , __future__, logging, socksio, ssl |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_synchronization.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This is a standard lock.

    In the sync case `Lock` provides thread locking.
    In the async case `AsyncLock` provides async locking. | , __future__, anyio, sniffio, threading, trio, types |  |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_trace.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, inspect, logging, types, typing | L24: self.debug = self.logger.isEnabledFor(logging.DEBUG)
L27: self.should_trace = self.debug or self.trace_extension is not None
L41: if self.debug:
L47: self.logger.debug(message)
L81: if self.debug:
L87: self.logger.debug(message) |
| `blackboard-agent/venv/Lib/site-packages/httpcore/_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Return whether a socket, as identifed by its file descriptor, is readable.
    "A socket is readable" means that the read buffer isn't empty, i.e. that calling
    .recv() on it would immediately return some data. | __future__, select, socket, sys |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , sys |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/__version__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_api.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Sends an HTTP request.

    **Parameters:**

    * **method** - HTTP method for the new `Request` object: `GET`, `OPTIONS`,
    `HEAD`, `POST`, `PUT`, `PATCH`, or `DELETE`.
    * **url** - URL for the new `Request` object.
    * **params** - *(optional)* Query parameters to include in the URL, as a
    string, dictionary, or sequence of two-tuples.
    * **content** - *(optional)* Binary content to include in the body of the
    request, as bytes or a byte iterator.
    * **data** - *(optional)* Form data to include in the body of the request,
    as a dictionary.
    * **files** - *(optional)* A dictionary of upload files to include in the
    body of the request.
    * **json** - *(optional)* A JSON serializable object to include in the body
    of the request.
    * **headers** - *(optional)* Dictionary of HTTP headers to include in the
    request.
    * **cookies** - *(optional)* Dictionary of Cookie items to include in the
    request.
    * **auth** - *(optional)* An authentication class to use when sending the
    request.
    * **proxy** - *(optional)* A proxy URL where all the traffic should be routed.
    * **timeout** - *(optional)* The timeout configuration to use when sending
    the request.
    * **follow_redirects** - *(optional)* Enables or disables HTTP redirects.
    * **verify** - *(optional)* Either `True` to use an SSL context with the
    default CA bundle, `False` to disable verification, or an instance of
    `ssl.SSLContext` to use a custom context.
    * **trust_env** - *(optional)* Enables or disables usage of environment
    variables for configuration.

    **Returns:** `Response`

    Usage:

    ```
    >>> import httpx
    >>> response = httpx.request('GET', 'https://httpbin.org/get')
    >>> response
    <Response [200 OK]>
    ``` | , __future__, contextlib, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_auth.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Base class for all authentication schemes.

    To implement a custom authentication scheme, subclass `Auth` and override
    the `.auth_flow()` method.

    If the authentication scheme does I/O such as disk access or network calls, or uses
    synchronization primitives such as locks, you should override `.sync_auth_flow()`
    and/or `.async_auth_flow()` instead of `.auth_flow()` to provide specialized
    implementations that will be used by `Client` and `AsyncClient` respectively. | , __future__, base64, hashlib, netrc, os, re, time, typing, urllib | L267: # TODO: implement auth-int |
| `blackboard-agent/venv/Lib/site-packages/httpx/_client.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Return 'True' if 'location' is a HTTPS upgrade of 'url' | , __future__, contextlib, datetime, enum, logging, ssl, time, types, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_config.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Timeout configuration.

    **Usage**:

    Timeout(None)               # No timeouts.
    Timeout(5.0)                # 5s timeout on all operations.
    Timeout(None, connect=5.0)  # 5s timeout on connect, no other timeouts.
    Timeout(5.0, connect=10.0)  # 10s timeout on connect. 5s timeout elsewhere.
    Timeout(5.0, pool=None)     # No timeout on acquiring connection from pool.
                                # 5s timeout elsewhere. | , __future__, certifi, os, ssl, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_content.py` | ❓ UNKNOWN | 2025-11-09 21:03 | If a request or response is serialized using pickle, then it is no longer
    attached to a stream for I/O purposes. Any stream operations should result
    in `httpx.StreamClosed`. | , __future__, inspect, json, typing, urllib, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_decoders.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Handlers for Content-Encoding.

See: https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Content-Encoding | , __future__, brotli, brotlicffi, codecs, io, typing, zlib, zstandard |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Our exception hierarchy:

* HTTPError
  x RequestError
    + TransportError
      - TimeoutException
        · ConnectTimeout
        · ReadTimeout
        · WriteTimeout
        · PoolTimeout
      - NetworkError
        · ConnectError
        · ReadError
        · WriteError
        · CloseError
      - ProtocolError
        · LocalProtocolError
        · RemoteProtocolError
      - ProxyError
      - UnsupportedProtocol
    + DecodingError
    + TooManyRedirects
  x HTTPStatusError
* InvalidURL
* CookieConflict
* StreamError
  x StreamConsumed
  x StreamClosed
  x ResponseNotRead
  x RequestNotRead | , __future__, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_main.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, click, functools, httpcore, json, pygments, rich, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_models.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Return `True` if `encoding` is a known codec. | , __future__, codecs, collections, datetime, email, http, json, re, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_multipart.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Encode a name/value pair within a multipart form. | , __future__, io, mimetypes, os, pathlib, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_status_codes.py` | ❓ UNKNOWN | 2025-11-09 21:03 | HTTP status codes and reason phrases

    Status codes from the following RFCs are all observed:

        * RFC 7231: Hypertext Transfer Protocol (HTTP/1.1), obsoletes 2616
        * RFC 6585: Additional HTTP Status Codes
        * RFC 3229: Delta encoding in HTTP
        * RFC 4918: HTTP Extensions for WebDAV, obsoletes 2518
        * RFC 5842: Binding Extensions to WebDAV
        * RFC 7238: Permanent Redirect
        * RFC 2295: Transparent Content Negotiation in HTTP
        * RFC 2774: An HTTP Extension Framework
        * RFC 7540: Hypertext Transfer Protocol Version 2 (HTTP/2)
        * RFC 2324: Hyper Text Coffee Pot Control Protocol (HTCPCP/1.0)
        * RFC 7725: An HTTP Status Code to Report Legal Obstacles
        * RFC 8297: An HTTP Status Code for Indicating Hints
        * RFC 8470: Using Early Data in HTTP | __future__, enum |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_transports/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_transports/asgi.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A custom AsyncTransport that handles sending requests directly to an ASGI app.

    ```python
    transport = httpx.ASGITransport(
        app=app,
        root_path="/submount",
        client=("1.2.3.4", 123)
    )
    client = httpx.AsyncClient(transport=transport)
    ```

    Arguments:

    * `app` - The ASGI application.
    * `raise_app_exceptions` - Boolean indicating if exceptions in the application
       should be raised. Default to `True`. Can be set to `False` for use cases
       such as testing the content of a client 500 response.
    * `root_path` - The root path on which the ASGI application should be mounted.
    * `client` - A two-tuple indicating the client IP and port of incoming requests.
    ``` | , __future__, asyncio, sniffio, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_transports/base.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Send a single HTTP request and return a response.

        Developers shouldn't typically ever need to call into this API directly,
        since the Client class provides all the higher level user-facing API
        niceties.

        In order to properly release any network resources, the response
        stream should *either* be consumed immediately, with a call to
        `response.stream.read()`, or else the `handle_request` call should
        be followed with a try/finally block to ensuring the stream is
        always closed.

        Example usage:

            with httpx.HTTPTransport() as transport:
                req = httpx.Request(
                    method=b"GET",
                    url=(b"https", b"www.example.com", 443, b"/"),
                    headers=[(b"Host", b"www.example.com")],
                )
                resp = transport.handle_request(req)
                body = resp.stream.read()
                print(resp.status_code, resp.headers, body)


        Takes a `Request` instance as the only argument.

        Returns a `Response` instance. | , __future__, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_transports/default.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Custom transports, with nicely configured defaults.

The following additional keyword arguments are currently supported by httpcore...

* uds: str
* local_address: str
* retries: int

Example usages...

# Disable HTTP/2 on a single specific domain.
mounts = {
    "all://": httpx.HTTPTransport(http2=True),
    "all://*example.org": httpx.HTTPTransport()
}

# Using advanced httpcore configuration, with connection retries.
transport = httpx.HTTPTransport(retries=1)
client = httpx.Client(transport=transport)

# Using advanced httpcore configuration, with unix domain sockets.
transport = httpx.HTTPTransport(uds="socket.uds")
client = httpx.Client(transport=transport) | , __future__, contextlib, httpcore, httpx, socksio, ssl, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_transports/mock.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_transports/wsgi.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A custom transport that handles sending requests directly to an WSGI app.
    The simplest way to use this functionality is to use the `app` argument.

    ```
    client = httpx.Client(app=app)
    ```

    Alternatively, you can setup the transport instance explicitly.
    This allows you to include any additional configuration arguments specific
    to the WSGITransport class:

    ```
    transport = httpx.WSGITransport(
        app=app,
        script_name="/submount",
        remote_addr="1.2.3.4"
    )
    client = httpx.Client(transport=transport)
    ```

    Arguments:

    * `app` - The WSGI application.
    * `raise_app_exceptions` - Boolean indicating if exceptions in the application
       should be raised. Default to `True`. Can be set to `False` for use cases
       such as testing the content of a client 500 response.
    * `script_name` - The root path on which the WSGI application should be mounted.
    * `remote_addr` - A string indicating the client IP of incoming requests.
    ``` | , __future__, _typeshed, io, itertools, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Type definitions for type checking purposes. | , http, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_urlparse.py` | ❓ UNKNOWN | 2025-11-09 21:03 | An implementation of `urlparse` that provides URL validation and normalization
as described by RFC3986.

We rely on this implementation rather than the one in Python's stdlib, because:

* It provides more complete URL validation.
* It properly differentiates between an empty querystring and an absent querystring,
  to distinguish URLs with a trailing '?'.
* It handles scheme, hostname, port, and path normalization.
* It supports IDNA hostnames, normalizing them to their encoded form.
* The API supports passing individual components, as well as the complete URL string.

Previously we relied on the excellent `rfc3986` package to handle URL parsing and
validation, but this module provides a simpler alternative, with less indirection
required. | , __future__, idna, ipaddress, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_urls.py` | ❓ UNKNOWN | 2025-11-09 21:03 | url = httpx.URL("HTTPS://jo%40email.com:a%20secret@müller.de:1234/pa%20th?search=ab#anchorlink")

    assert url.scheme == "https"
    assert url.username == "jo@email.com"
    assert url.password == "a secret"
    assert url.userinfo == b"jo%40email.com:a%20secret"
    assert url.host == "müller.de"
    assert url.raw_host == b"xn--mller-kva.de"
    assert url.port == 1234
    assert url.netloc == b"xn--mller-kva.de:1234"
    assert url.path == "/pa th"
    assert url.query == b"?search=ab"
    assert url.raw_path == b"/pa%20th?search=ab"
    assert url.fragment == "anchorlink"

    The components of a URL are broken down like this:

       https://jo%40email.com:a%20secret@müller.de:1234/pa%20th?search=ab#anchorlink
    [scheme]   [  username  ] [password] [ host ][port][ path ] [ query ] [fragment]
               [       userinfo        ] [   netloc   ][    raw_path    ]

    Note that:

    * `url.scheme` is normalized to always be lowercased.

    * `url.host` is normalized to always be lowercased. Internationalized domain
      names are represented in unicode, without IDNA encoding applied. For instance:

      url = httpx.URL("http://中国.icom.museum")
      assert url.host == "中国.icom.museum"
      url = httpx.URL("http://xn--fiqs8s.icom.museum")
      assert url.host == "中国.icom.museum"

    * `url.raw_host` is normalized to always be lowercased, and is IDNA encoded.

      url = httpx.URL("http://中国.icom.museum")
      assert url.raw_host == b"xn--fiqs8s.icom.museum"
      url = httpx.URL("http://xn--fiqs8s.icom.museum")
      assert url.raw_host == b"xn--fiqs8s.icom.museum"

    * `url.port` is either None or an integer. URLs that include the default port for
      "http", "https", "ws", "wss", and "ftp" schemes have their port
      normalized to `None`.

      assert httpx.URL("http://example.com") == httpx.URL("http://example.com:80")
      assert httpx.URL("http://example.com").port is None
      assert httpx.URL("http://example.com:80").port is None

    * `url.userinfo` is raw bytes, without URL escaping. Usually you'll want to work
      with `url.username` and `url.password` instead, which handle the URL escaping.

    * `url.raw_path` is raw bytes of both the path and query, without URL escaping.
      This portion is used as the target when constructing HTTP requests. Usually you'll
      want to work with `url.path` instead.

    * `url.query` is raw bytes, without URL escaping. A URL query string portion can
      only be properly URL escaped when decoding the parameter names and values
      themselves. | , __future__, idna, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/httpx/_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Coerce a primitive data type into a string value.

    Note that we prefer JSON-style 'true'/'false' for boolean values here. | , __future__, ipaddress, os, re, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/idna/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/idna/codec.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , codecs, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/idna/compat.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/idna/core.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Base exception for all IDNA-encoding related problems"""

    pass


class IDNABidiError(IDNAError): | , bisect, re, typing, unicodedata |  |
| `blackboard-agent/venv/Lib/site-packages/idna/idnadata.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/idna/intranges.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Given a list of integers, made up of (hopefully) a small number of long runs
of consecutive integers, compute a representation of the form
((start1, end1), (start2, end2) ...). Then answer the question "was x present
in the original list?" in time O(log(# runs)). | bisect, typing |  |
| `blackboard-agent/venv/Lib/site-packages/idna/package_data.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/idna/uts46data.py` | ❓ UNKNOWN | 2025-11-09 19:11 | IDNA Mapping Table from UTS46."""


__version__ = "16.0.0"


def _seg_0() -> List[Union[Tuple[int, str], Tuple[int, str, str]]]:
    return [
        (0x0, "V"),
        (0x1, "V"),
        (0x2, "V"),
        (0x3, "V"),
        (0x4, "V"),
        (0x5, "V"),
        (0x6, "V"),
        (0x7, "V"),
        (0x8, "V"),
        (0x9, "V"),
        (0xA, "V"),
        (0xB, "V"),
        (0xC, "V"),
        (0xD, "V"),
        (0xE, "V"),
        (0xF, "V"),
        (0x10, "V"),
        (0x11, "V"),
        (0x12, "V"),
        (0x13, "V"),
        (0x14, "V"),
        (0x15, "V"),
        (0x16, "V"),
        (0x17, "V"),
        (0x18, "V"),
        (0x19, "V"),
        (0x1A, "V"),
        (0x1B, "V"),
        (0x1C, "V"),
        (0x1D, "V"),
        (0x1E, "V"),
        (0x1F, "V"),
        (0x20, "V"),
        (0x21, "V"),
        (0x22, "V"),
        (0x23, "V"),
        (0x24, "V"),
        (0x25, "V"),
        (0x26, "V"),
        (0x27, "V"),
        (0x28, "V"),
        (0x29, "V"),
        (0x2A, "V"),
        (0x2B, "V"),
        (0x2C, "V"),
        (0x2D, "V"),
        (0x2E, "V"),
        (0x2F, "V"),
        (0x30, "V"),
        (0x31, "V"),
        (0x32, "V"),
        (0x33, "V"),
        (0x34, "V"),
        (0x35, "V"),
        (0x36, "V"),
        (0x37, "V"),
        (0x38, "V"),
        (0x39, "V"),
        (0x3A, "V"),
        (0x3B, "V"),
        (0x3C, "V"),
        (0x3D, "V"),
        (0x3E, "V"),
        (0x3F, "V"),
        (0x40, "V"),
        (0x41, "M", "a"),
        (0x42, "M", "b"),
        (0x43, "M", "c"),
        (0x44, "M", "d"),
        (0x45, "M", "e"),
        (0x46, "M", "f"),
        (0x47, "M", "g"),
        (0x48, "M", "h"),
        (0x49, "M", "i"),
        (0x4A, "M", "j"),
        (0x4B, "M", "k"),
        (0x4C, "M", "l"),
        (0x4D, "M", "m"),
        (0x4E, "M", "n"),
        (0x4F, "M", "o"),
        (0x50, "M", "p"),
        (0x51, "M", "q"),
        (0x52, "M", "r"),
        (0x53, "M", "s"),
        (0x54, "M", "t"),
        (0x55, "M", "u"),
        (0x56, "M", "v"),
        (0x57, "M", "w"),
        (0x58, "M", "x"),
        (0x59, "M", "y"),
        (0x5A, "M", "z"),
        (0x5B, "V"),
        (0x5C, "V"),
        (0x5D, "V"),
        (0x5E, "V"),
        (0x5F, "V"),
        (0x60, "V"),
        (0x61, "V"),
        (0x62, "V"),
        (0x63, "V"),
    ]


def _seg_1() -> List[Union[Tuple[int, str], Tuple[int, str, str]]]:
    return [
        (0x64, "V"),
        (0x65, "V"),
        (0x66, "V"),
        (0x67, "V"),
        (0x68, "V"),
        (0x69, "V"),
        (0x6A, "V"),
        (0x6B, "V"),
        (0x6C, "V"),
        (0x6D, "V"),
        (0x6E, "V"),
        (0x6F, "V"),
        (0x70, "V"),
        (0x71, "V"),
        (0x72, "V"),
        (0x73, "V"),
        (0x74, "V"),
        (0x75, "V"),
        (0x76, "V"),
        (0x77, "V"),
        (0x78, "V"),
        (0x79, "V"),
        (0x7A, "V"),
        (0x7B, "V"),
        (0x7C, "V"),
        (0x7D, "V"),
        (0x7E, "V"),
        (0x7F, "V"),
        (0x80, "X"),
        (0x81, "X"),
        (0x82, "X"),
        (0x83, "X"),
        (0x84, "X"),
        (0x85, "X"),
        (0x86, "X"),
        (0x87, "X"),
        (0x88, "X"),
        (0x89, "X"),
        (0x8A, "X"),
        (0x8B, "X"),
        (0x8C, "X"),
        (0x8D, "X"),
        (0x8E, "X"),
        (0x8F, "X"),
        (0x90, "X"),
        (0x91, "X"),
        (0x92, "X"),
        (0x93, "X"),
        (0x94, "X"),
        (0x95, "X"),
        (0x96, "X"),
        (0x97, "X"),
        (0x98, "X"),
        (0x99, "X"),
        (0x9A, "X"),
        (0x9B, "X"),
        (0x9C, "X"),
        (0x9D, "X"),
        (0x9E, "X"),
        (0x9F, "X"),
        (0xA0, "M", " "),
        (0xA1, "V"),
        (0xA2, "V"),
        (0xA3, "V"),
        (0xA4, "V"),
        (0xA5, "V"),
        (0xA6, "V"),
        (0xA7, "V"),
        (0xA8, "M", " ̈"),
        (0xA9, "V"),
        (0xAA, "M", "a"),
        (0xAB, "V"),
        (0xAC, "V"),
        (0xAD, "I"),
        (0xAE, "V"),
        (0xAF, "M", " ̄"),
        (0xB0, "V"),
        (0xB1, "V"),
        (0xB2, "M", "2"),
        (0xB3, "M", "3"),
        (0xB4, "M", " ́"),
        (0xB5, "M", "μ"),
        (0xB6, "V"),
        (0xB7, "V"),
        (0xB8, "M", " ̧"),
        (0xB9, "M", "1"),
        (0xBA, "M", "o"),
        (0xBB, "V"),
        (0xBC, "M", "1⁄4"),
        (0xBD, "M", "1⁄2"),
        (0xBE, "M", "3⁄4"),
        (0xBF, "V"),
        (0xC0, "M", "à"),
        (0xC1, "M", "á"),
        (0xC2, "M", "â"),
        (0xC3, "M", "ã"),
        (0xC4, "M", "ä"),
        (0xC5, "M", "å"),
        (0xC6, "M", "æ"),
        (0xC7, "M", "ç"),
    ]


def _seg_2() -> List[Union[Tuple[int, str], Tuple[int, str, str]]]:
    return [
        (0xC8, "M", "è"),
        (0xC9, "M", "é"),
        (0xCA, "M", "ê"),
        (0xCB, "M", "ë"),
        (0xCC, "M", "ì"),
        (0xCD, "M", "í"),
        (0xCE, "M", "î"),
        (0xCF, "M", "ï"),
        (0xD0, "M", "ð"),
        (0xD1, "M", "ñ"),
        (0xD2, "M", "ò"),
        (0xD3, "M", "ó"),
        (0xD4, "M", "ô"),
        (0xD5, "M", "õ"),
        (0xD6, "M", "ö"),
        (0xD7, "V"),
        (0xD8, "M", "ø"),
        (0xD9, "M", "ù"),
        (0xDA, "M", "ú"),
        (0xDB, "M", "û"),
        (0xDC, "M", "ü"),
        (0xDD, "M", "ý"),
        (0xDE, "M", "þ"),
        (0xDF, "D", "ss"),
        (0xE0, "V"),
        (0xE1, "V"),
        (0xE2, "V"),
        (0xE3, "V"),
        (0xE4, "V"),
        (0xE5, "V"),
        (0xE6, "V"),
        (0xE7, "V"),
        (0xE8, "V"),
        (0xE9, "V"),
        (0xEA, "V"),
        (0xEB, "V"),
        (0xEC, "V"),
        (0xED, "V"),
        (0xEE, "V"),
        (0xEF, "V"),
        (0xF0, "V"),
        (0xF1, "V"),
        (0xF2, "V"),
        (0xF3, "V"),
        (0xF4, "V"),
        (0xF5, "V"),
        (0xF6, "V"),
        (0xF7, "V"),
        (0xF8, "V"),
        (0xF9, "V"),
        (0xFA, "V"),
        (0xFB, "V"),
        (0xFC, "V"),
        (0xFD, "V"),
        (0xFE, "V"),
        (0xFF, "V"),
        (0x100, "M", "ā"),
        (0x101, "V"),
        (0x102, "M", "ă"),
        (0x103, "V"),
        (0x104, "M", "ą"),
        (0x105, "V"),
        (0x106, "M", "ć"),
        (0x107, "V"),
        (0x108, "M", "ĉ"),
        (0x109, "V"),
        (0x10A, "M", "ċ"),
        (0x10B, "V"),
        (0x10C, "M", "č"),
        (0x10D, "V"),
        (0x10E, "M", "ď"),
        (0x10F, "V"),
        (0x110, "M", "đ"),
        (0x111, "V"),
        (0x112, "M", "ē"),
        (0x113, "V"),
        (0x114, "M", "ĕ"), | typing |  |
| `blackboard-agent/venv/Lib/site-packages/jiter/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/outcome/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Top-level package for outcome."""

from ._impl import (
    Error as Error,
    Maybe as Maybe,
    Outcome as Outcome,
    Value as Value,
    acapture as acapture,
    capture as capture,
)
from ._util import AlreadyUsedError as AlreadyUsedError, fixup_module_metadata
from ._version import __version__ as __version__

__all__ = (
    'Error', 'Outcome', 'Value', 'Maybe', 'acapture', 'capture',
    'AlreadyUsedError'
)

fixup_module_metadata(__name__, globals())
del fixup_module_metadata |  |  |
| `blackboard-agent/venv/Lib/site-packages/outcome/_impl.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Run ``sync_fn(*args, **kwargs)`` and capture the result.

    Returns:
      Either a :class:`Value` or :class:`Error` as appropriate. | , __future__, abc, attr, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/outcome/_util.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An Outcome can only be unwrapped once."""
    pass


def fixup_module_metadata(
        module_name: str,
        namespace: Dict[str, object],
) -> None:
    def fix_one(obj: object) -> None:
        mod = getattr(obj, "__module__", None)
        if mod is not None and mod.startswith("outcome."):
            obj.__module__ = module_name
            if isinstance(obj, type):
                for attr_value in obj.__dict__.values():
                    fix_one(attr_value)

    all_list = namespace["__all__"]
    assert isinstance(all_list, (tuple, list)), repr(all_list)
    for objname in all_list:
        obj = namespace[objname]
        fix_one(obj)


def remove_tb_frames(exc: BaseException, n: int) -> BaseException:
    tb = exc.__traceback__
    for _ in range(n):
        assert tb is not None
        tb = tb.tb_next
    return exc.with_traceback(tb) | typing |  |
| `blackboard-agent/venv/Lib/site-packages/outcome/_version.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/_elffile.py` | ❓ UNKNOWN | 2025-11-09 21:21 | ELF file parser.

This provides a class ``ELFFile`` that parses an ELF executable in a similar
interface to ``ZipFile``. Only the read interface is implemented.

Based on: https://gist.github.com/lyssdod/f51579ae8d93c8657a5564aefc2ffbca
ELF header: https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html | __future__, enum, os, struct, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/_manylinux.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Primary implementation of glibc_version_string using os.confstr. | , __future__, _manylinux, collections, contextlib, ctypes, functools, os, re, sys, typing, warnings | L238: # https://sourceware.org/bugzilla/show_bug.cgi?id=24636 |
| `blackboard-agent/venv/Lib/site-packages/packaging/_musllinux.py` | ❓ UNKNOWN | 2025-11-09 21:21 | PEP 656 support.

This module implements logic to detect if the currently running Python is
linked against musl, and what musl version is used. | , __future__, functools, re, subprocess, sys, sysconfig, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/_parser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Handwritten parser of dependency specifiers.

The docstring for each __parse_* function contains EBNF-inspired grammar representing
the implementation. | , __future__, ast, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/_structures.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/_tokenizer.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The provided source text could not be parsed correctly."""

    def __init__(
        self,
        message: str,
        *,
        source: str,
        span: tuple[int, int],
    ) -> None:
        self.span = span
        self.message = message
        self.source = source

        super().__init__()

    def __str__(self) -> str:
        marker = " " * self.span[0] + "~" * (self.span[1] - self.span[0]) + "^"
        return "\n    ".join([self.message, self.source, marker])


DEFAULT_RULES: dict[str, str \\| re.Pattern[str]] = {
    "LEFT_PARENTHESIS": r"\(",
    "RIGHT_PARENTHESIS": r"\)",
    "LEFT_BRACKET": r"\[",
    "RIGHT_BRACKET": r"\]",
    "SEMICOLON": r";",
    "COMMA": r",",
    "QUOTED_STRING": re.compile(
        r | , __future__, contextlib, dataclasses, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/licenses/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Raised when a license-expression string is invalid

    >>> canonicalize_license_expression("invalid")
    Traceback (most recent call last):
        ...
    packaging.licenses.InvalidLicenseExpression: Invalid license expression: 'invalid' | __future__, packaging, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/licenses/_spdx.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/markers.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An invalid marker was found, users should refer to PEP 508. | , __future__, operator, os, platform, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/metadata.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A minimal implementation of :external:exc:`ExceptionGroup` from Python 3.11.

        If :external:exc:`ExceptionGroup` is already defined by Python itself,
        that version is used instead. | , __future__, email, pathlib, sys, typing | L204: # TODO: The spec doesn't say anything about if the keys should be |
| `blackboard-agent/venv/Lib/site-packages/packaging/requirements.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An invalid requirement was found, users should refer to PEP 508. | , __future__, typing | L29: # TODO: Can we test whether something is contained within a requirement?
L32: # TODO: Can we normalize the name and extra name? |
| `blackboard-agent/venv/Lib/site-packages/packaging/specifiers.py` | ❓ UNKNOWN | 2025-11-09 21:21 | .. testsetup::

    from packaging.specifiers import Specifier, SpecifierSet, InvalidSpecifier
    from packaging.version import Version | , __future__, abc, itertools, packaging, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/tags.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A representation of the tag triple for a wheel.

    Instances are considered immutable and thus are hashable. Equality checking
    is also supported. | , __future__, importlib, logging, platform, re, struct, subprocess, sys, sysconfig, typing | L115: logger.debug(
L155: threading = debug = pymalloc = ucs4 = ""
L156: with_debug = _get_config_var("Py_DEBUG", warn)
L158: # Windows doesn't set Py_DEBUG, so checking for support of debug-compiled
L162: if with_debug or (with_debug is None and (has_refcount or has_ext)):
L163: debug = "d"
L176: elif debug:
L177: # Debug builds can also load "normal" extension modules.
L180: abis.insert(0, f"cp{version}{threading}{debug}{pymalloc}{ucs4}")
L378: # TODO: Need to care about 32-bit PPC for ppc64 through 10.2? |
| `blackboard-agent/venv/Lib/site-packages/packaging/utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An invalid distribution name; users should refer to the packaging user guide. | , __future__, functools, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/packaging/version.py` | ❓ UNKNOWN | 2025-11-09 21:21 | .. testsetup::

    from packaging.version import parse, Version | , __future__, itertools, packaging, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This is an internal API only meant for use by pip's own console scripts.

    For additional details, see https://github.com/pypa/pip/issues/7498. | __future__, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | os, pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/__pip-runner__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Execute exactly this copy of pip, within a different environment.

This file is named as it is, to ensure that this module can't be imported via
an import statement. | importlib, os, runpy, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This is preserved for old console scripts that may still be referencing
    it.

    For additional details, see https://github.com/pypa/pip/issues/7498. | __future__, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/build_env.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Build Environment used for isolation during sdist building"""

from __future__ import annotations

import logging
import os
import pathlib
import site
import sys
import textwrap
from collections import OrderedDict
from collections.abc import Iterable
from types import TracebackType
from typing import TYPE_CHECKING, Protocol, TypedDict

from pip._vendor.packaging.version import Version

from pip import __file__ as pip_location
from pip._internal.cli.spinners import open_spinner
from pip._internal.locations import get_platlib, get_purelib, get_scheme
from pip._internal.metadata import get_default_environment, get_environment
from pip._internal.utils.deprecation import deprecated
from pip._internal.utils.logging import VERBOSE
from pip._internal.utils.packaging import get_requirement
from pip._internal.utils.subprocess import call_subprocess
from pip._internal.utils.temp_dir import TempDirectory, tempdir_kinds

if TYPE_CHECKING:
    from pip._internal.index.package_finder import PackageFinder
    from pip._internal.req.req_install import InstallRequirement

    class ExtraEnviron(TypedDict, total=False):
        extra_environ: dict[str, str]


logger = logging.getLogger(__name__)


def _dedup(a: str, b: str) -> tuple[str] \\| tuple[str, str]:
    return (a, b) if a != b else (a,)


class _Prefix:
    def __init__(self, path: str) -> None:
        self.path = path
        self.setup = False
        scheme = get_scheme("", prefix=path)
        self.bin_dir = scheme.scripts
        self.lib_dirs = _dedup(scheme.purelib, scheme.platlib)


def get_runnable_pip() -> str: | __future__, collections, logging, os, pathlib, pip, site, sys, textwrap, types, typing | L178: if logger.getEffectiveLevel() <= logging.DEBUG:
L370: # FIXME: Consider direct URL? |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cache.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Cache Management"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any

from pip._vendor.packaging.tags import Tag, interpreter_name, interpreter_version
from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.exceptions import InvalidWheelFilename
from pip._internal.models.direct_url import DirectUrl
from pip._internal.models.link import Link
from pip._internal.models.wheel import Wheel
from pip._internal.utils.temp_dir import TempDirectory, tempdir_kinds
from pip._internal.utils.urls import path_to_url

logger = logging.getLogger(__name__)

ORIGIN_JSON_NAME = "origin.json"


def _hash_dict(d: dict[str, str]) -> str: | __future__, hashlib, json, logging, os, pathlib, pip, typing | L147: logger.debug(
L280: # TODO: use DirectUrl.equivalent when
L285: "%s. This is likely a pip bug or a cache corruption issue. " |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Subpackage containing all of pip's command line interface related code"""

# This file intentionally does not import submodules |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/autocompletion.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Logic that powers autocompletion installed by ``pip completion``."""

from __future__ import annotations

import optparse
import os
import sys
from collections.abc import Iterable
from itertools import chain
from typing import Any

from pip._internal.cli.main_parser import create_main_parser
from pip._internal.commands import commands_dict, create_command
from pip._internal.metadata import get_default_environment


def autocomplete() -> None: | __future__, collections, itertools, optparse, os, pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/base_command.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base Command class, and related routines"""

from __future__ import annotations

import logging
import logging.config
import optparse
import os
import sys
import traceback
from optparse import Values
from typing import Callable

from pip._vendor.rich import reconfigure
from pip._vendor.rich import traceback as rich_traceback

from pip._internal.cli import cmdoptions
from pip._internal.cli.command_context import CommandContextMixIn
from pip._internal.cli.parser import ConfigOptionParser, UpdatingDefaultsHelpFormatter
from pip._internal.cli.status_codes import (
    ERROR,
    PREVIOUS_BUILD_DIR_ERROR,
    UNKNOWN_ERROR,
    VIRTUALENV_NOT_FOUND,
)
from pip._internal.exceptions import (
    BadCommand,
    CommandError,
    DiagnosticPipError,
    InstallationError,
    NetworkConnectionError,
    PreviousBuildDirError,
)
from pip._internal.utils.filesystem import check_path_owner
from pip._internal.utils.logging import BrokenStdoutLoggingError, setup_logging
from pip._internal.utils.misc import get_prog, normalize_path
from pip._internal.utils.temp_dir import TempDirectoryTypeRegistry as TempDirRegistry
from pip._internal.utils.temp_dir import global_tempdir_manager, tempdir_registry
from pip._internal.utils.virtualenv import running_under_virtualenv

__all__ = ["Command"]

logger = logging.getLogger(__name__)


class Command(CommandContextMixIn):
    usage: str = ""
    ignore_require_venv: bool = False

    def __init__(self, name: str, summary: str, isolated: bool = False) -> None:
        super().__init__()

        self.name = name
        self.summary = summary
        self.parser = ConfigOptionParser(
            usage=self.usage,
            prog=f"{get_prog()} {name}",
            formatter=UpdatingDefaultsHelpFormatter(),
            add_help_option=False,
            name=name,
            description=self.__doc__,
            isolated=isolated,
        )

        self.tempdir_registry: TempDirRegistry \\| None = None

        # Commands should add options to this option group
        optgroup_name = f"{self.name.capitalize()} Options"
        self.cmd_opts = optparse.OptionGroup(self.parser, optgroup_name)

        # Add the general options
        gen_opts = cmdoptions.make_option_group(
            cmdoptions.general_group,
            self.parser,
        )
        self.parser.add_option_group(gen_opts)

        self.add_options()

    def add_options(self) -> None:
        pass

    def handle_pip_version_check(self, options: Values) -> None: | __future__, logging, optparse, os, pip, sys, traceback, typing | L102: if options.debug_mode:
L112: logger.debug("Exception information:", exc_info=True)
L117: logger.debug("Exception information:", exc_info=True)
L126: logger.debug("Exception information:", exc_info=True)
L131: logger.debug("Exception information:", exc_info=True)
L138: if level_number <= logging.DEBUG:
L144: logger.debug("Exception information:", exc_info=True)
L176: if options.debug_mode:
L209: # TODO: Try to get these passing down from the command? |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/cmdoptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | shared options and groups

The principle here is to define options once, but *not* instantiate them
globally. One reason being that options with action='append' can carry state
between parses. pip parses general options twice internally, and shouldn't
pass on state. To be consistent, all options will follow this design. | __future__, functools, logging, optparse, os, pathlib, pip, textwrap, typing | L154: debug_mode: Callable[..., Option] = partial(
L156: "--debug",
L157: dest="debug_mode", |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/command_context.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | collections, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/index_command.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Contains command classes which may interact with an index / the network.

Unlike its sister module, req_command, this module still uses lazy imports
so commands which don't always hit the network (e.g. list w/o --outdated or
--uptodate) don't need waste time importing PipSession and friends. | __future__, functools, logging, optparse, os, pip, ssl, sys, typing | L34: logger.debug("Disabling truststore because Python version isn't 3.10+")
L175: logger.debug("See below for error", exc_info=True) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/main.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Primary application entrypoint."""

from __future__ import annotations

import locale
import logging
import os
import sys
import warnings

from pip._internal.cli.autocompletion import autocomplete
from pip._internal.cli.main_parser import parse_command
from pip._internal.commands import create_command
from pip._internal.exceptions import PipError
from pip._internal.utils import deprecation

logger = logging.getLogger(__name__)


# Do not import and use main() directly! Using it directly is actively
# discouraged by pip's maintainers. The name, location and behavior of
# this function is subject to change, so calling it directly is not
# portable across different pip versions.

# In addition, running pip in-process is unsupported and unsafe. This is
# elaborated in detail at
# https://pip.pypa.io/en/stable/user_guide/#using-pip-from-your-program.
# That document also provides suggestions that should work for nearly
# all users that are considering importing and using main() directly.

# However, we know that certain users will still want to invoke pip
# in-process. If you understand and accept the implications of using pip
# in an unsupported manner, the best approach is to use runpy to avoid
# depending on the exact location of this entry point.

# The following example shows how to use runpy to invoke pip in that
# case:
#
#     sys.argv = ["pip", your, args, here]
#     runpy.run_module("pip", run_name="__main__")
#
# Note that this will exit the process after running, unlike a direct
# call to main. As it is not safe to do any processing after calling
# main, this should not be an issue in practice.


def main(args: list[str] \\| None = None) -> int:
    if args is None:
        args = sys.argv[1:]

    # Suppress the pkg_resources deprecation warning
    # Note - we use a module of .*pkg_resources to cover
    # the normal case (pip._vendor.pkg_resources) and the
    # devendored case (a bare pkg_resources)
    warnings.filterwarnings(
        action="ignore", category=DeprecationWarning, module=".*pkg_resources"
    )

    # Configure our deprecation warnings to be sent through loggers
    deprecation.install_warning_logger()

    autocomplete()

    try:
        cmd_name, cmd_args = parse_command(args)
    except PipError as exc:
        sys.stderr.write(f"ERROR: {exc}")
        sys.stderr.write(os.linesep)
        sys.exit(1)

    # Needed for locale.getpreferredencoding(False) to work
    # in pip._internal.utils.encoding.auto_decode
    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error as e:
        # setlocale can apparently crash if locale are uninitialized
        logger.debug("Ignoring error %s when setting locale", e)
    command = create_command(cmd_name, isolated=("--isolated" in cmd_args))

    return command.main(cmd_args) | __future__, locale, logging, os, pip, sys, warnings | L77: logger.debug("Ignoring error %s when setting locale", e) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/main_parser.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A single place for constructing and exposing the main parser"""

from __future__ import annotations

import os
import subprocess
import sys

from pip._internal.build_env import get_runnable_pip
from pip._internal.cli import cmdoptions
from pip._internal.cli.parser import ConfigOptionParser, UpdatingDefaultsHelpFormatter
from pip._internal.commands import commands_dict, get_similar_commands
from pip._internal.exceptions import CommandError
from pip._internal.utils.misc import get_pip_version, get_prog

__all__ = ["create_main_parser", "parse_command"]


def create_main_parser() -> ConfigOptionParser: | __future__, os, pip, subprocess, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/parser.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base option parser setup"""

from __future__ import annotations

import logging
import optparse
import shutil
import sys
import textwrap
from collections.abc import Generator
from contextlib import suppress
from typing import Any, NoReturn

from pip._internal.cli.status_codes import UNKNOWN_ERROR
from pip._internal.configuration import Configuration, ConfigurationError
from pip._internal.utils.misc import redact_auth_from_url, strtobool

logger = logging.getLogger(__name__)


class PrettyHelpFormatter(optparse.IndentedHelpFormatter): | __future__, collections, contextlib, logging, optparse, pip, shutil, sys, textwrap, typing | L196: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/progress_bars.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get an object that can be used to render the download progress.

    Returns a callable, that takes an iterable to "wrap". | __future__, collections, functools, pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/req_command.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Contains the RequirementCommand base class.

This class is in a separate module so the commands that do not always
need PackageFinder capability don't unnecessarily import the
PackageFinder machinery and all its vendored dependencies, etc. | __future__, functools, logging, optparse, os, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/spinners.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Custom rich spinner that matches the style of the legacy spinners.

    (*) Updates will be handled in a background thread by a rich live panel
        which will call render() automatically at the appropriate time. | __future__, collections, contextlib, itertools, logging, pip, sys, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/cli/status_codes.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Package containing all pip commands | __future__, collections, difflib, importlib, pip, typing | L103: "debug": CommandInfo(
L104: "pip._internal.commands.debug",
L105: "DebugCommand",
L106: "Show information useful for debugging.", |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/cache.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Inspect and manage pip's wheel cache.

    Subcommands:

    - dir: Show the cache directory.
    - info: Show information about the cache.
    - list: List filenames of packages stored in the cache.
    - remove: Remove one or more package from the cache.
    - purge: Remove all items from the cache.

    ``<pattern>`` can be a glob expression or a package name. | optparse, os, pip, textwrap, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/check.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Verify installed packages have compatible dependencies."""

    ignore_require_venv = True
    usage = | logging, optparse, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/completion.py` | ❓ UNKNOWN | 2025-11-09 19:12 | COMPLETION_SCRIPTS = { | optparse, pip, sys, textwrap |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/configuration.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Manage local and global configuration.

    Subcommands:

    - list: List the active configuration (or from the file specified)
    - edit: Edit the configuration file in an editor
    - get: Get the value associated with command.option
    - set: Set the command.option=value
    - unset: Unset the value associated with command.option
    - debug: List the configuration files and values defined under them

    Configuration keys should be dot separated command and option name,
    with the special prefix "global" affecting any command. For example,
    "pip config set global.index-url https://example.org/" would configure
    the index url for all commands, but "pip config set download.timeout 10"
    would configure a 10 second timeout only for "pip download" commands.

    If none of --user, --global and --site are passed, a virtual
    environment configuration file is used if one is active and the file
    exists. Otherwise, all modifications happen to the user file by
    default. | __future__, logging, optparse, os, pip, subprocess, typing | L35: - debug: List the configuration files and values defined under them
L57: %prog [<file-option>] debug
L105: "debug": self.list_config_values,
L203: self._get_n_args(args, "debug", n=0)
L276: "Unable to save configuration. Please report this as a bug." |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/debug.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Log the actual version and print extra info if there is
    a conflict or if the actual version could not be imported. | __future__, locale, logging, optparse, os, pip, sys, types, typing | L160: class DebugCommand(Command):
L162: Display debug information.
L176: "This command is only meant for debugging. " |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/download.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Download packages from:

    - PyPI (and other indexes) using requirement specifiers.
    - VCS project urls.
    - Local project directories.
    - Local or remote source archives.

    pip also supports downloading from "requirements files", which provide
    an easy way to specify a whole environment to be downloaded. | logging, optparse, os, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/freeze.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Output installed packages in requirements format.

    packages are listed in a case-insensitive sorted order. | optparse, pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/hash.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Compute a hash of a local package archive.

    These can be used with --hash in a requirements file to do repeatable
    installs. | hashlib, logging, optparse, pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/help.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Show help for commands"""

    usage = | optparse, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/index.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Inspect information available from package indexes. | __future__, collections, json, logging, optparse, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/inspect.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Inspect the content of a Python environment and produce a report in JSON format. | logging, optparse, pip, typing | L60: # TODO tags? scheme? |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/install.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Install packages from:

    - PyPI (and other indexes) using requirement specifiers.
    - VCS project urls.
    - Local project directories.
    - Local or remote source archives.

    pip also supports installing from "requirements files", which provide
    an easy way to specify a whole environment to be installed. | __future__, errno, json, operator, optparse, os, pathlib, pip, shutil, site |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/list.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Give the distribution object a couple of extra fields.

        These will be populated during ``get_outdated()``. This is dirty but
        makes the rest of the code much cleaner. | __future__, collections, email, json, logging, optparse, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/lock.py` | ❓ UNKNOWN | 2025-11-09 19:12 | EXPERIMENTAL - Lock packages and their dependencies from:

    - PyPI (and other indexes) using requirement specifiers.
    - VCS project urls.
    - Local project directories.
    - Local or remote source archives.

    pip also supports locking from "requirements files", which provide an easy
    way to specify a whole environment to be installed.

    The generated lock file is only guaranteed to be valid for the current
    python version and platform. | optparse, pathlib, pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/search.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Search for PyPI packages whose name or summary contains <query>."""

    usage = | __future__, collections, logging, optparse, pip, shutil, sys, textwrap, typing, xmlrpc |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/show.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Show information about one or more installed packages.

    The output is in RFC-compliant mail header format. | __future__, collections, logging, optparse, pip, string, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/uninstall.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Uninstall packages.

    pip is able to uninstall most installed packages. Known exceptions are:

    - Pure distutils packages installed with ``python setup.py install``, which
      leave behind no metadata to determine what files were installed.
    - Script wrappers installed by ``python setup.py develop``. | logging, optparse, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/commands/wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Build Wheel archives for your requirements and dependencies.

    Wheel is a built-package format, and offers the advantage of not
    recompiling your software during every install. For more details, see the
    wheel docs: https://wheel.readthedocs.io/en/latest/

    'pip wheel' uses the build system interface as described here:
    https://pip.pypa.io/en/stable/reference/build-system/ | logging, optparse, os, pip, shutil |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/configuration.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Configuration management setup

Some terminology:
- name
  As written in config files.
- value
  Value associated with a name
- key
  Name combined with it's section (section.name)
- variant
  A single word describing where the configuration key-value pair came from | __future__, collections, configparser, locale, os, pip, sys, typing | L202: "Fatal Internal error [id=1]. Please report as a bug."
L241: logger.debug("Will be working with %s variant only", self.load_only)
L259: logger.debug(
L270: logger.debug("Skipping file '%s' (variant: %s)", fname, variant)
L383: "Fatal Internal error [id=2]. Please report as a bug." |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/distributions/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Returns a Distribution for the given InstallRequirement"""
    # Editable requirements will always be source distributions. They use the
    # legacy logic until we create a modern standard for them.
    if install_req.editable:
        return SourceDistribution(install_req)

    # If it's a wheel, it's a WheelDistribution
    if install_req.is_wheel:
        return WheelDistribution(install_req)

    # Otherwise, a SourceDistribution
    return SourceDistribution(install_req) | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/distributions/base.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A base class for handling installable artifacts.

    The requirements for anything installable are as follows:

     - we must be able to determine the requirement name
       (or we can't correctly handle the non-upgrade case).

     - for packages with setup requirements, we must also be able
       to determine their requirements without installing additional
       packages (for the same reason as run-time dependencies)

     - we must be able to create a Distribution object exposing the
       above metadata.

     - if we need to do work in the build tracker, we must be able to generate a unique
       string to identify the requirement in the build tracker. | __future__, abc, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/distributions/installed.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents an installed package.

    This does not need any preparation as the required information has already
    been computed. | __future__, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/distributions/sdist.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents a source distribution.

    The preparation step for these needs metadata for the packages to be
    generated. | __future__, collections, logging, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/distributions/wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents a wheel distribution.

    This does not need any preparation as wheels can be directly unpacked. | __future__, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Exceptions used throughout package.

This module MUST NOT try to import from anything within `pip._internal` to
operate. This is expected to be importable from any/all files within the
subpackage and, thus, should not depend on them. | __future__, collections, configparser, contextlib, hashlib, itertools, locale, logging, pathlib, pip, re, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/index/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Index interaction code""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/index/collector.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The main purpose of this module is to expose LinkCollector.collect_sources(). | , __future__, collections, dataclasses, email, functools, html, itertools, json, logging, optparse, os, pip, typing, urllib | L124: logger.debug("Getting page %s", redact_auth_from_url(url))
L162: logger.debug(
L302: meth = logger.debug
L339: # TODO: In the future, it would be nice if pip supported PEP 691
L344: logger.debug(" file: URL is directory, getting %s", url)
L415: logger.debug(
L474: if logger.isEnabledFor(logging.DEBUG):
L484: logger.debug("\n".join(lines)) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/index/package_finder.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Routines related to PyPI, indexes"""

from __future__ import annotations

import enum
import functools
import itertools
import logging
import re
from collections.abc import Iterable
from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Optional,
    Union,
)

from pip._vendor.packaging import specifiers
from pip._vendor.packaging.tags import Tag
from pip._vendor.packaging.utils import NormalizedName, canonicalize_name
from pip._vendor.packaging.version import InvalidVersion, _BaseVersion
from pip._vendor.packaging.version import parse as parse_version

from pip._internal.exceptions import (
    BestVersionAlreadyInstalled,
    DistributionNotFound,
    InvalidWheelFilename,
    UnsupportedWheel,
)
from pip._internal.index.collector import LinkCollector, parse_links
from pip._internal.models.candidate import InstallationCandidate
from pip._internal.models.format_control import FormatControl
from pip._internal.models.link import Link
from pip._internal.models.search_scope import SearchScope
from pip._internal.models.selection_prefs import SelectionPreferences
from pip._internal.models.target_python import TargetPython
from pip._internal.models.wheel import Wheel
from pip._internal.req import InstallRequirement
from pip._internal.utils._log import getLogger
from pip._internal.utils.filetypes import WHEEL_EXTENSION
from pip._internal.utils.hashes import Hashes
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import build_netloc
from pip._internal.utils.packaging import check_requires_python
from pip._internal.utils.unpacking import SUPPORTED_EXTENSIONS

if TYPE_CHECKING:
    from typing_extensions import TypeGuard

__all__ = ["FormatControl", "BestCandidateResult", "PackageFinder"]


logger = getLogger(__name__)

BuildTag = Union[tuple[()], tuple[int, str]]
CandidateSortingKey = tuple[int, int, int, _BaseVersion, Optional[int], BuildTag]


def _check_link_requires_python(
    link: Link,
    version_info: tuple[int, int, int],
    ignore_requires_python: bool = False,
) -> bool: | __future__, collections, dataclasses, enum, functools, itertools, logging, pip, re, typing, typing_extensions | L79: logger.debug(
L96: logger.debug(
L215: f"(run pip debug --verbose to show compatible tags)"
L266: logger.debug("Found link %s, version: %s", link, version)
L292: logger.debug(
L331: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/index/sources.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Returns the underlying link, if there's one."""
        raise NotImplementedError()

    def page_candidates(self) -> FoundCandidates: | __future__, collections, logging, mimetypes, os, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/locations/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This function determines the value of _USE_SYSCONFIG.

    By default, pip uses sysconfig on Python 3.10+.
    But Python distributors can override this decision by setting:
        sysconfig._PIP_USE_SYSCONFIG = True / False
    Rationale in https://github.com/pypa/pip/issues/10647

    This is a function for testability, but should be constant during any one
    run. | , __future__, distutils, functools, logging, os, pathlib, pip, sys, sysconfig, typing | L75: _MISMATCH_LEVEL = logging.DEBUG
L81: See <https://bugs.python.org/issue44860>.
L254: # directory name to be ``pypy`` instead. So we treat this as a bug fix
L269: # CPython decide whether this is a bug or feature. See bpo-43948.
L326: skip_msys2_mingw_bug = (
L329: if skip_msys2_mingw_bug:
L402: do the same. This is similar to the bug worked around in ``get_scheme()``,
L404: we can't do anything about this Debian bug, and this detection allows us to |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/locations/_distutils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Locations where we look for configs, install stuff, etc"""

# The following comment should be removed at some point in the future.
# mypy: strict-optional=False

# If pip's going to use distutils, it should not be using the copy that setuptools
# might have injected into the environment. This is done by removing the injected
# shim, if it's injected.
#
# See https://github.com/pypa/pip/issues/8761 for the original discussion and
# rationale for why this is done within pip.
from __future__ import annotations

try:
    __import__("_distutils_hack").remove_shim()
except (ImportError, AttributeError):
    pass

import logging
import os
import sys
from distutils.cmd import Command as DistutilsCommand
from distutils.command.install import SCHEME_KEYS
from distutils.command.install import install as distutils_install_command
from distutils.sysconfig import get_python_lib

from pip._internal.models.scheme import Scheme
from pip._internal.utils.compat import WINDOWS
from pip._internal.utils.virtualenv import running_under_virtualenv

from .base import get_major_minor_version

logger = logging.getLogger(__name__)


def distutils_scheme(
    dist_name: str,
    user: bool = False,
    home: str \\| None = None,
    root: str \\| None = None,
    isolated: bool = False,
    prefix: str \\| None = None,
    *,
    ignore_config_files: bool = False,
) -> dict[str, str]: | , __future__, distutils, logging, os, pip, sys | L15: __import__("_distutils_hack").remove_shim() |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/locations/_sysconfig.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Check for Apple's ``osx_framework_library`` scheme.

    Python distributed by Apple's Command Line Tools has this special scheme
    that's used when:

    * This is a framework build.
    * We are installing into the system prefix.

    This does not account for ``pip install --prefix`` (also means we're not
    installing to the system prefix), which should use ``posix_prefix``, but
    logic here means ``_infer_prefix()`` outputs ``osx_framework_library``. But
    since ``prefix`` is not available for ``sysconfig.get_default_scheme()``,
    which is the stdlib replacement for ``_infer_prefix()``, presumably Apple
    wouldn't be able to magically switch between ``osx_framework_library`` and
    ``posix_prefix``. ``_infer_prefix()`` returning ``osx_framework_library``
    means its behavior is consistent whether we use the stdlib implementation
    or our own, and we deal with this special case in ``get_scheme()`` instead. | , __future__, logging, os, pip, sys, sysconfig |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/locations/base.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Return the major-minor version of the current Python as a string, e.g.
    "3.7" or "3.10". | __future__, functools, os, pip, site, sys, sysconfig | L16: # FIXME doesn't account for venv linked to global site-packages
L60: # FIXME: keep src in cwd for now (it is not a temporary folder) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/main.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This is preserved for old console scripts that may still be referencing
    it.

    For additional details, see https://github.com/pypa/pip/issues/7498. | __future__, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Whether to use the ``importlib.metadata`` or ``pkg_resources`` backend.

    By default, pip uses ``importlib.metadata`` on Python 3.11+, and
    ``pkg_resources`` otherwise. Up to Python 3.13, This can be
    overridden by a couple of ways:

    * If environment variable ``_PIP_USE_IMPORTLIB_METADATA`` is set, it
      dictates whether ``importlib.metadata`` is used, for Python <3.14.
    * On Python 3.11, 3.12 and 3.13, Python distributors can patch
      ``importlib.metadata`` to add a global constant
      ``_PIP_USE_IMPORTLIB_METADATA = False``. This makes pip use
      ``pkg_resources`` (unless the user set the aforementioned environment
      variable to *True*).

    On Python 3.14+, the ``pkg_resources`` backend cannot be used. | , __future__, contextlib, functools, importlib, os, pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/_json.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert a Message object into a JSON-compatible dictionary."""

    def sanitise_header(h: Header \\| str) -> str:
        if isinstance(h, Header):
            chunks = []
            for bytes, encoding in decode_header(h):
                if encoding == "unknown-8bit":
                    try:
                        # See if UTF-8 works
                        bytes.decode("utf-8")
                        encoding = "utf-8"
                    except UnicodeDecodeError:
                        # If not, latin1 at least won't fail
                        encoding = "latin1"
                chunks.append((bytes, encoding))
            return str(make_header(chunks))
        return str(h)

    result = {}
    for field, multi in METADATA_FIELDS:
        if field not in msg:
            continue
        key = json_name(field)
        if multi:
            value: str \\| list[str] = [
                sanitise_header(v) for v in msg.get_all(field)  # type: ignore
            ]
        else:
            value = sanitise_header(msg.get(field))  # type: ignore
            if key == "keywords":
                # Accept both comma-separated and space-separated
                # forms, for better compatibility with old data.
                if "," in value:
                    value = [v.strip() for v in value.split(",")]
                else:
                    value = value.split()
        result[key] = value

    payload = cast(str, msg.get_payload())
    if payload:
        result["description"] = payload

    return result | __future__, email, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/base.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert a legacy installed-files.txt path into modern RECORD path.

    The legacy format stores paths relative to the info directory, while the
    modern format stores paths relative to the package root, e.g. the
    site-packages directory.

    :param entry: Path parts of the installed-files.txt entry.
    :param info: Path parts of the egg-info directory relative to package root.
    :returns: The converted entry.

    For best compatibility with symlinks, this does not use ``abspath()`` or
    ``Path.resolve()``, but tries to work with path parts:

    1. While ``entry`` starts with ``..``, remove the equal amounts of parts
       from ``info``; if ``info`` is empty, start appending ``..`` instead.
    2. Join the two directly. | , __future__, collections, csv, email, functools, json, logging, pathlib, pip, re, typing, zipfile | L32: from pip._internal.utils.compat import stdlib_pkgs  # TODO: Move definition here.
L162: # TODO: this property is relatively costly to compute, memoize it ?
L172: # TODO: get project location from second line of egg_link file |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/importlib/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/importlib/_compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A protocol that various path objects conform.

    This exists because importlib.metadata uses both ``pathlib.Path`` and
    ``zipfile.Path``, and we need a common base for type hints (Union does not
    work well since ``zipfile.Path`` is too new for our linter setup).

    This does not mean to be exhaustive, but only contains things that present
    in both classes *that we need*. | __future__, importlib, os, pip, typing | L42: HACK: This relies on importlib.metadata's private ``_path`` attribute. Not |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/importlib/_dists.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An ``importlib.metadata.Distribution`` read from a wheel.

    Although ``importlib.metadata.PathDistribution`` accepts ``zipfile.Path``,
    its implementation is too "lazy" for pip's needs (we can't keep the ZipFile
    handle open for the entire lifetime of the distribution object).

    This implementation eagerly reads the entire metadata directory into the
    memory instead, and operates from that. | , __future__, collections, email, importlib, os, pathlib, pip, typing, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/importlib/_envs.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Finder to locate distributions.

    The main purpose of this class is to memoize found distributions' names, so
    only one distribution is returned for each package name. At lot of pip code
    assumes this (because it is setuptools's behavior), and not doing the same
    can potentially cause a distribution in lower precedence path to override a
    higher precedence one if the caller is not careful.

    Eventually we probably want to make it possible to see lower precedence
    installations as well. It's useful feature, after all. | , __future__, collections, importlib, logging, os, pathlib, pip, sys, typing, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/metadata/pkg_resources.py` | ❓ UNKNOWN | 2025-11-09 19:12 | IMetadataProvider that reads metadata files from a dictionary.

    This also maps metadata decoding exceptions to our internal exception type. | , __future__, collections, email, logging, os, pip, typing, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A package that contains models that represent entities.""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/candidate.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents a potential "candidate" for installation."""

    __slots__ = ["name", "version", "link"]

    name: str
    version: Version
    link: Link

    def __init__(self, name: str, version: str, link: Link) -> None:
        object.__setattr__(self, "name", name)
        object.__setattr__(self, "version", parse_version(version))
        object.__setattr__(self, "link", link)

    def __str__(self) -> str:
        return f"{self.name!r} candidate (version {self.version} at {self.link})" | dataclasses, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/direct_url.py` | ❓ UNKNOWN | 2025-11-09 19:12 | PEP 610"""

from __future__ import annotations

import json
import re
import urllib.parse
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar, Union

__all__ = [
    "DirectUrl",
    "DirectUrlValidationError",
    "DirInfo",
    "ArchiveInfo",
    "VcsInfo",
]

T = TypeVar("T")

DIRECT_URL_METADATA_NAME = "direct_url.json"
ENV_VAR_RE = re.compile(r"^\$\{[A-Za-z0-9-_]+\}(:\$\{[A-Za-z0-9-_]+\})?$")


class DirectUrlValidationError(Exception):
    pass


def _get(
    d: dict[str, Any], expected_type: type[T], key: str, default: T \\| None = None
) -> T \\| None: | __future__, collections, dataclasses, json, re, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/format_control.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Helper for managing formats from which a package can be installed."""

    __slots__ = ["no_binary", "only_binary"]

    def __init__(
        self,
        no_binary: set[str] \\| None = None,
        only_binary: set[str] \\| None = None,
    ) -> None:
        if no_binary is None:
            no_binary = set()
        if only_binary is None:
            only_binary = set()

        self.no_binary = no_binary
        self.only_binary = only_binary

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, self.__class__):
            return NotImplemented

        if self.__slots__ != other.__slots__:
            return False

        return all(getattr(self, k) == getattr(other, k) for k in self.__slots__)

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.no_binary}, {self.only_binary})"

    @staticmethod
    def handle_mutual_excludes(value: str, target: set[str], other: set[str]) -> None:
        if value.startswith("-"):
            raise CommandError(
                "--no-binary / --only-binary option requires 1 argument."
            )
        new = value.split(",")
        while ":all:" in new:
            other.clear()
            target.clear()
            target.add(":all:")
            del new[: new.index(":all:") + 1]
            # Without a none, we want to discard everything as :all: covers it
            if ":none:" not in new:
                return
        for name in new:
            if name == ":none:":
                target.clear()
                continue
            name = canonicalize_name(name)
            other.discard(name)
            target.add(name)

    def get_allowed_formats(self, canonical_name: str) -> frozenset[str]:
        result = {"binary", "source"}
        if canonical_name in self.only_binary:
            result.discard("source")
        elif canonical_name in self.no_binary:
            result.discard("binary")
        elif ":all:" in self.only_binary:
            result.discard("source")
        elif ":all:" in self.no_binary:
            result.discard("binary")
        return frozenset(result)

    def disallow_binaries(self) -> None:
        self.handle_mutual_excludes(
            ":all:",
            self.no_binary,
            self.only_binary,
        ) | __future__, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/index.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents a Package Index and provides easier access to endpoints"""

    __slots__ = ["url", "netloc", "simple_url", "pypi_url", "file_storage_domain"]

    def __init__(self, url: str, file_storage_domain: str) -> None:
        super().__init__()
        self.url = url
        self.netloc = urllib.parse.urlsplit(url).netloc
        self.simple_url = self._url_for_path("simple")
        self.pypi_url = self._url_for_path("pypi")

        # This is part of a temporary hack used to block installs of PyPI
        # packages which depend on external urls only necessary until PyPI can
        # block such packages themselves
        self.file_storage_domain = file_storage_domain

    def _url_for_path(self, path: str) -> str:
        return urllib.parse.urljoin(self.url, path)


PyPI = PackageIndex("https://pypi.org/", file_storage_domain="files.pythonhosted.org")
TestPyPI = PackageIndex(
    "https://test.pypi.org/", file_storage_domain="test-files.pythonhosted.org"
) | urllib | L16: # This is part of a temporary hack used to block installs of PyPI |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/installation_report.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | collections, pip, typing | L51: # TODO: currently, the resolver uses the default environment to evaluate |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/link.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Links to content may have embedded hash values. This class parses those.

    `name` must be any member of `_SUPPORTED_HASHES`.

    This class can be converted to and from `ArchiveInfo`. While ArchiveInfo intends to
    be JSON-serializable to conform to PEP 610, this class contains the logic for
    parsing a hash name and value for correctness, and then checking whether that hash
    conforms to a schema with `.is_hash_allowed()`. | __future__, collections, dataclasses, functools, itertools, logging, os, pip, posixpath, re, typing, urllib | L57: # against Hashes when hash-checking is needed. This is easier to debug than
L368: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/pylock.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | __future__, collections, dataclasses, pathlib, pip, re, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/scheme.py` | ❓ UNKNOWN | 2025-11-09 19:12 | For types associated with installation schemes.

For a general overview of available schemes and their context, see
https://docs.python.org/3/install/index.html#alternate-installation. | dataclasses |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/search_scope.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Encapsulates the locations that pip is configured to search. | dataclasses, itertools, logging, os, pip, posixpath, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/selection_prefs.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Encapsulates the candidate selection preferences for downloading
    and installing files. | __future__, pip | L6: # TODO: This needs Python 3.10's improved slots support for dataclasses |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/target_python.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Encapsulates the properties of a Python interpreter one is targeting
    for a package install, download, etc. | __future__, pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/models/wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents a wheel file and provides access to the various parts of the
name that have meaning. | __future__, collections, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Contains purely network-related utilities.""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/auth.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Network Authentication Helpers

Contains interface (MultiDomainBasicAuth) and associated glue code for
providing credentials in the context of network requests. | __future__, abc, functools, keyring, logging, os, pathlib, pip, shutil, subprocess, sysconfig, typing, urllib | L86: logger.debug("Getting credentials from keyring for %s", url)
L93: logger.debug("Getting password from keyring for %s", url)
L182: logger.warning(msg, exc, exc_info=logger.isEnabledFor(logging.DEBUG))
L274: # Log the full exception (with stacktrace) at debug, so it'll only
L276: logger.debug("Keyring is skipped due to an exception", exc_info=True)
L351: logger.debug("Found credentials in url for %s", netloc)
L361: logger.debug("Found index url %s", index_url)
L367: logger.debug("Found credentials in index url for %s", netloc)
L374: logger.debug("Found credentials in netrc for %s", netloc)
L387: logger.debug("Found credentials in keyring for %s", netloc) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/cache.py` | ❓ UNKNOWN | 2025-11-09 19:12 | HTTP cache implementation."""

from __future__ import annotations

import os
import shutil
from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime
from typing import Any, BinaryIO, Callable

from pip._vendor.cachecontrol.cache import SeparateBodyBaseCache
from pip._vendor.cachecontrol.caches import SeparateBodyFileCache
from pip._vendor.requests.models import Response

from pip._internal.utils.filesystem import (
    adjacent_tmp_file,
    copy_directory_permissions,
    replace,
)
from pip._internal.utils.misc import ensure_dir


def is_from_cache(response: Response) -> bool:
    return getattr(response, "from_cache", False)


@contextmanager
def suppressed_cache_errors() -> Generator[None, None, None]: | __future__, collections, contextlib, datetime, os, pip, shutil, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/download.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Download files with progress indicators."""

from __future__ import annotations

import email.message
import logging
import mimetypes
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from http import HTTPStatus
from typing import BinaryIO

from pip._vendor.requests import PreparedRequest
from pip._vendor.requests.models import Response
from pip._vendor.urllib3 import HTTPResponse as URLlib3Response
from pip._vendor.urllib3._collections import HTTPHeaderDict
from pip._vendor.urllib3.exceptions import ReadTimeoutError

from pip._internal.cli.progress_bars import BarType, get_download_progress_renderer
from pip._internal.exceptions import IncompleteDownloadError, NetworkConnectionError
from pip._internal.models.index import PyPI
from pip._internal.models.link import Link
from pip._internal.network.cache import SafeFileCache, is_from_cache
from pip._internal.network.session import CacheControlAdapter, PipSession
from pip._internal.network.utils import HEADERS, raise_for_status, response_chunks
from pip._internal.utils.misc import format_size, redact_auth_from_url, splitext

logger = logging.getLogger(__name__)


def _get_http_response_size(resp: Response) -> int \\| None:
    try:
        return int(resp.headers["content-length"])
    except (ValueError, KeyError, TypeError):
        return None


def _get_http_response_etag_or_last_modified(resp: Response) -> str \\| None: | __future__, collections, dataclasses, email, http, logging, mimetypes, os, pip, typing | L277: logger.debug(
L313: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/lazy_wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Lazy ZIP over HTTP"""

from __future__ import annotations

__all__ = ["HTTPRangeRequestUnsupported", "dist_from_wheel_url"]

from bisect import bisect_left, bisect_right
from collections.abc import Generator
from contextlib import contextmanager
from tempfile import NamedTemporaryFile
from typing import Any
from zipfile import BadZipFile, ZipFile

from pip._vendor.packaging.utils import NormalizedName
from pip._vendor.requests.models import CONTENT_CHUNK_SIZE, Response

from pip._internal.metadata import BaseDistribution, MemoryWheel, get_wheel_distribution
from pip._internal.network.session import PipSession
from pip._internal.network.utils import HEADERS, raise_for_status, response_chunks


class HTTPRangeRequestUnsupported(Exception):
    pass


def dist_from_wheel_url(
    name: NormalizedName, url: str, session: PipSession
) -> BaseDistribution: | __future__, bisect, collections, contextlib, pip, tempfile, typing, zipfile | L179: # TODO: Get range requests to be correctly cached |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/session.py` | ❓ UNKNOWN | 2025-11-09 19:12 | PipSession and supporting code, containing all pip-specific
network request configuration and behavior. | __future__, _ssl, collections, email, functools, io, ipaddress, json, logging, mimetypes, os, pip, platform, shutil, ssl, subprocess, sys, typing, urllib, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/utils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Given a requests Response, provide the data chunks."""
    try:
        # Special case for urllib3.
        for chunk in response.raw.stream(
            chunk_size,
            # We use decode_content=False here because we don't
            # want urllib3 to mess with the raw bytes we get
            # from the server. If we decompress inside of
            # urllib3 then we cannot verify the checksum
            # because the checksum will be of the compressed
            # file. This breakage will only occur if the
            # server adds a Content-Encoding header, which
            # depends on how the server was configured:
            # - Some servers will notice that the file isn't a
            #   compressible file and will leave the file alone
            #   and with an empty Content-Encoding
            # - Some servers will notice that the file is
            #   already compressed and will leave the file
            #   alone and will add a Content-Encoding: gzip
            #   header
            # - Some servers won't notice anything at all and
            #   will take a file that's already been compressed
            #   and compress it again and set the
            #   Content-Encoding: gzip header
            #
            # By setting this not to decode automatically we
            # hope to eliminate problems with the second case.
            decode_content=False,
        ):
            yield chunk
    except AttributeError:
        # Standard file-like object.
        while True:
            chunk = response.raw.read(chunk_size)
            if not chunk:
                break
            yield chunk | collections, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/network/xmlrpc.py` | ❓ UNKNOWN | 2025-11-09 19:12 | xmlrpclib.Transport implementation"""

import logging
import urllib.parse
import xmlrpc.client
from typing import TYPE_CHECKING

from pip._internal.exceptions import NetworkConnectionError
from pip._internal.network.session import PipSession
from pip._internal.network.utils import raise_for_status

if TYPE_CHECKING:
    from xmlrpc.client import _HostType, _Marshallable

    from _typeshed import SizedBuffer

logger = logging.getLogger(__name__)


class PipXmlrpcTransport(xmlrpc.client.Transport): | _typeshed, logging, pip, typing, urllib, xmlrpc |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/build/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/build/build_tracker.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Uniquely identifying string provided to the build tracker."""


class BuildTracker: | __future__, collections, contextlib, hashlib, logging, os, pip, types | L49: logger.debug("Initialized build tracking at %s", root)
L71: logger.debug("Created build tracker: %s", self._root)
L74: logger.debug("Entered build tracker: %s", self._root)
L114: logger.debug("Added %s to build tracker %r", req, self._root)
L123: logger.debug("Removed %s from build tracker %r", req, self._root)
L129: logger.debug("Removed build tracker: %r", self._root) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/build/metadata.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Metadata generation logic for source distributions."""

import os

from pip._vendor.pyproject_hooks import BuildBackendHookCaller

from pip._internal.build_env import BuildEnvironment
from pip._internal.exceptions import (
    InstallationSubprocessError,
    MetadataGenerationFailed,
)
from pip._internal.utils.subprocess import runner_with_spinner_message
from pip._internal.utils.temp_dir import TempDirectory


def generate_metadata(
    build_env: BuildEnvironment, backend: BuildBackendHookCaller, details: str
) -> str: | os, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/build/metadata_editable.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Metadata generation logic for source distributions."""

import os

from pip._vendor.pyproject_hooks import BuildBackendHookCaller

from pip._internal.build_env import BuildEnvironment
from pip._internal.exceptions import (
    InstallationSubprocessError,
    MetadataGenerationFailed,
)
from pip._internal.utils.subprocess import runner_with_spinner_message
from pip._internal.utils.temp_dir import TempDirectory


def generate_editable_metadata(
    build_env: BuildEnvironment, backend: BuildBackendHookCaller, details: str
) -> str: | os, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/build/wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Build one InstallRequirement using the PEP 517 build process.

    Returns path to wheel if successfully built. Otherwise, returns None. | __future__, logging, os, pip | L25: logger.debug("Destination directory: %s", wheel_directory) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/build/wheel_editable.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Build one InstallRequirement using the PEP 660 build process.

    Returns path to wheel if successfully built. Otherwise, returns None. | __future__, logging, os, pip | L25: logger.debug("Destination directory: %s", wheel_directory) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/check.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Validation of dependencies of packages"""

from __future__ import annotations

import logging
from collections.abc import Generator, Iterable
from contextlib import suppress
from email.parser import Parser
from functools import reduce
from typing import (
    Callable,
    NamedTuple,
)

from pip._vendor.packaging.requirements import Requirement
from pip._vendor.packaging.tags import Tag, parse_tag
from pip._vendor.packaging.utils import NormalizedName, canonicalize_name
from pip._vendor.packaging.version import Version

from pip._internal.distributions import make_distribution_for_install_requirement
from pip._internal.metadata import get_default_environment
from pip._internal.metadata.base import BaseDistribution
from pip._internal.req.req_install import InstallRequirement

logger = logging.getLogger(__name__)


class PackageDetails(NamedTuple):
    version: Version
    dependencies: list[Requirement]


# Shorthands
PackageSet = dict[NormalizedName, PackageDetails]
Missing = tuple[NormalizedName, Requirement]
Conflicting = tuple[NormalizedName, Version, Requirement]

MissingDict = dict[NormalizedName, list[Missing]]
ConflictingDict = dict[NormalizedName, list[Conflicting]]
CheckResult = tuple[MissingDict, ConflictingDict]
ConflictDetails = tuple[PackageSet, CheckResult]


def create_package_set_from_installed() -> tuple[PackageSet, bool]: | __future__, collections, contextlib, email, functools, logging, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/freeze.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Compute and return values (req, comments) for use in
    FrozenRequirement.from_dist(). | __future__, collections, dataclasses, logging, os, pip, typing | L176: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/install/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | For modules related to installing packages.""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/install/wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Support for installing and building the "wheel" binary package format."""

from __future__ import annotations

import collections
import compileall
import contextlib
import csv
import importlib
import logging
import os.path
import re
import shutil
import sys
import textwrap
import warnings
from base64 import urlsafe_b64encode
from collections.abc import Generator, Iterable, Iterator, Sequence
from email.message import Message
from itertools import chain, filterfalse, starmap
from typing import (
    IO,
    Any,
    BinaryIO,
    Callable,
    NewType,
    Protocol,
    Union,
    cast,
)
from zipfile import ZipFile, ZipInfo

from pip._vendor.distlib.scripts import ScriptMaker
from pip._vendor.distlib.util import get_export_entry
from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.exceptions import InstallationError
from pip._internal.locations import get_major_minor_version
from pip._internal.metadata import (
    BaseDistribution,
    FilesystemWheel,
    get_wheel_distribution,
)
from pip._internal.models.direct_url import DIRECT_URL_METADATA_NAME, DirectUrl
from pip._internal.models.scheme import SCHEME_KEYS, Scheme
from pip._internal.utils.filesystem import adjacent_tmp_file, replace
from pip._internal.utils.misc import StreamWrapper, ensure_dir, hash_file, partition
from pip._internal.utils.unpacking import (
    current_umask,
    is_within_directory,
    set_extracted_file_to_default_mode_plus_executable,
    zip_item_is_executable,
)
from pip._internal.utils.wheel import parse_wheel


class File(Protocol):
    src_record_path: RecordPath
    dest_path: str
    changed: bool

    def save(self) -> None:
        pass


logger = logging.getLogger(__name__)

RecordPath = NewType("RecordPath", str)
InstalledCSVRow = tuple[RecordPath, str, Union[int, str]]


def rehash(path: str, blocksize: int = 1 << 20) -> tuple[str, str]: | __future__, base64, collections, compileall, contextlib, csv, email, importlib, itertools, logging, os, pip, re, shutil, sys, textwrap, typing, warnings, zipfile | L293: # To add the level of hack in this section of code, in order to support |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/operations/prepare.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Prepares a distribution for installation"""

# The following comment should be removed at some point in the future.
# mypy: strict-optional=False
from __future__ import annotations

import mimetypes
import os
import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.build_env import BuildEnvironmentInstaller
from pip._internal.distributions import make_distribution_for_install_requirement
from pip._internal.distributions.installed import InstalledDistribution
from pip._internal.exceptions import (
    DirectoryUrlHashUnsupported,
    HashMismatch,
    HashUnpinned,
    InstallationError,
    MetadataInconsistent,
    NetworkConnectionError,
    VcsHashUnsupported,
)
from pip._internal.index.package_finder import PackageFinder
from pip._internal.metadata import BaseDistribution, get_metadata_distribution
from pip._internal.models.direct_url import ArchiveInfo
from pip._internal.models.link import Link
from pip._internal.models.wheel import Wheel
from pip._internal.network.download import Downloader
from pip._internal.network.lazy_wheel import (
    HTTPRangeRequestUnsupported,
    dist_from_wheel_url,
)
from pip._internal.network.session import PipSession
from pip._internal.operations.build.build_tracker import BuildTracker
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils._log import getLogger
from pip._internal.utils.direct_url_helpers import (
    direct_url_for_editable,
    direct_url_from_link,
)
from pip._internal.utils.hashes import Hashes, MissingHashes
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import (
    display_path,
    hash_file,
    hide_url,
    redact_auth_from_requirement,
)
from pip._internal.utils.temp_dir import TempDirectory
from pip._internal.utils.unpacking import unpack_file
from pip._internal.vcs import vcs

if TYPE_CHECKING:
    from pip._internal.cli.progress_bars import BarType

logger = getLogger(__name__)


def _get_prepared_distribution(
    req: InstallRequirement,
    build_tracker: BuildTracker,
    build_env_installer: BuildEnvironmentInstaller,
    build_isolation: bool,
    check_build_deps: bool,
) -> BaseDistribution: | __future__, collections, dataclasses, mimetypes, os, pathlib, pip, shutil, typing | L376: logger.debug(
L381: logger.debug(
L440: logger.debug(
L457: logger.debug("%s does not support range requests", url)
L480: logger.debug("Downloading link %s to %s", link, filepath) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/pyproject.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Load the pyproject.toml file.

    Parameters:
        pyproject_toml - Location of the project's pyproject.toml file
        setup_py - Location of the project's setup.py file
        req_name - The name of the requirement we're processing (for
                   error reporting)

    Returns:
        None if we should use the legacy code path, otherwise a tuple
        (
            requirements from pyproject.toml,
            name of PEP 517 backend,
            requirements we should check are installed after setting
                up the build environment
            directory paths to import the backend from (backend-path),
                relative to the project root.
        ) | __future__, collections, os, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Install everything in the given list.

    (to be called after having downloaded and unpacked the packages) | , __future__, collections, dataclasses, logging, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/constructors.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Backing implementation for InstallRequirement's various constructors

The idea here is that these formed a major chunk of InstallRequirement's size
so, moving them and support code dedicated to them outside of that class
helps creates for better understandability for the rest of the code.

These are meant to be used elsewhere within pip to create instances of
InstallRequirement. | __future__, collections, copy, dataclasses, logging, os, pip, re | L211: logger.debug("Cannot parse '%s' as requirements file", req)
L309: # TODO: The is_installable_dir test here might not be necessary |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/req_dependency_group.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Parse dependency groups data as provided via the CLI, in a `[path:]group` syntax.

    Raises InstallationErrors if anything goes wrong. | collections, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/req_file.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Requirements file parsing | __future__, codecs, collections, dataclasses, locale, logging, optparse, os, pip, re, shlex, sys, typing, urllib | L103: # TODO: replace this with slots=True when dropping Python 3.9 support.
L255: # FIXME: it would be nice to keep track of the source |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/req_install.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Represents something that may be installed later on, may have information
    about where to fetch the relevant requirement and also contains logic for
    installing the said requirement. | __future__, collections, functools, logging, optparse, os, pathlib, pip, shutil, sys, typing, uuid, zipfile | L211: def format_debug(self) -> str:
L212: """An un-tested helper for getting state, for debugging."""
L350: # FIXME: Is there a better place to create the build_dir? (hg and bzr
L353: logger.debug("Creating directory %s", build_dir) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/req_set.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Create a RequirementSet."""

        self.requirements: dict[str, InstallRequirement] = OrderedDict()
        self.check_supported_wheels = check_supported_wheels

        self.unnamed_requirements: list[InstallRequirement] = []

    def __str__(self) -> str:
        requirements = sorted(
            (req for req in self.requirements.values() if not req.comes_from),
            key=lambda req: canonicalize_name(req.name or ""),
        )
        return " ".join(str(req.req) for req in requirements)

    def __repr__(self) -> str:
        requirements = sorted(
            self.requirements.values(),
            key=lambda req: canonicalize_name(req.name or ""),
        )

        format_string = "<{classname} object; {count} requirement(s): {reqs}>"
        return format_string.format(
            classname=self.__class__.__name__,
            count=len(requirements),
            reqs=", ".join(str(req.req) for req in requirements),
        )

    def add_unnamed_requirement(self, install_req: InstallRequirement) -> None:
        assert not install_req.name
        self.unnamed_requirements.append(install_req)

    def add_named_requirement(self, install_req: InstallRequirement) -> None:
        assert install_req.name

        project_name = canonicalize_name(install_req.name)
        self.requirements[project_name] = install_req

    def has_requirement(self, name: str) -> bool:
        project_name = canonicalize_name(name)

        return (
            project_name in self.requirements
            and not self.requirements[project_name].constraint
        )

    def get_requirement(self, name: str) -> InstallRequirement:
        project_name = canonicalize_name(name)

        if project_name in self.requirements:
            return self.requirements[project_name]

        raise KeyError(f"No project with the name {name!r}")

    @property
    def all_requirements(self) -> list[InstallRequirement]:
        return self.unnamed_requirements + list(self.requirements.values())

    @property
    def requirements_to_install(self) -> list[InstallRequirement]: | collections, logging, pip | L74: TODO remove this property together with the legacy resolver, since the new |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/req/req_uninstall.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Create the fully qualified name of the files created by
    {console,gui}_scripts for the given ``dist``.
    Returns the list of file names | __future__, collections, functools, importlib, os, pip, sys, sysconfig, typing | L281: logger.debug("Replacing %s from %s", new_path, path)
L289: logger.debug("Exception: %s", ex)
L483: # FIXME: need a test for this elif block |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/base.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/legacy/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/legacy/resolver.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Dependency Resolution

The dependency resolution in pip is performed as follows:

for top-level requirements:
    a. only one spec allowed per project, regardless of conflicts or not.
       otherwise a "double requirement" exception is raised
    b. they override sub-dependency requirements.
for sub-dependencies
    a. "first found, wins" (where the order is breadth first) | __future__, collections, itertools, logging, pip, sys, typing | L98: logger.debug(
L300: logger.debug(
L429: logger.debug("Using cached wheel link: %s", cache_entry.link) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/base.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The "project name" of a requirement.

        This is different from ``name`` if this requirement contains extras,
        in which case ``name`` would contain the ``[...]`` part, while this
        refers to the name of the project. | __future__, collections, dataclasses, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/candidates.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The runtime version of BaseCandidate."""
    base_candidate_classes = (
        AlreadyInstalledCandidate,
        EditableCandidate,
        LinkCandidate,
    )
    if isinstance(candidate, base_candidate_classes):
        return candidate
    return None


def make_install_req_from_link(
    link: Link, template: InstallRequirement
) -> InstallRequirement:
    assert not template.editable, "template is editable"
    if template.req:
        line = str(template.req)
    else:
        line = link.url
    ireq = install_req_from_line(
        line,
        user_supplied=template.user_supplied,
        comes_from=template.comes_from,
        isolated=template.isolated,
        constraint=template.constraint,
        hash_options=template.hash_options,
        config_settings=template.config_settings,
    )
    ireq.original_link = template.original_link
    ireq.link = link
    ireq.extras = template.extras
    return ireq


def make_install_req_from_editable(
    link: Link, template: InstallRequirement
) -> InstallRequirement:
    assert template.editable, "template not editable"
    if template.name:
        req_string = f"{template.name} @ {link.url}"
    else:
        req_string = link.url
    ireq = install_req_from_editable(
        req_string,
        user_supplied=template.user_supplied,
        comes_from=template.comes_from,
        isolated=template.isolated,
        constraint=template.constraint,
        permit_editable_wheels=template.permit_editable_wheels,
        hash_options=template.hash_options,
        config_settings=template.config_settings,
    )
    ireq.extras = template.extras
    return ireq


def _make_install_req_from_dist(
    dist: BaseDistribution, template: InstallRequirement
) -> InstallRequirement:
    if template.req:
        line = str(template.req)
    elif template.link:
        line = f"{dist.canonical_name} @ {template.link.url}"
    else:
        line = f"{dist.canonical_name}=={dist.version}"
    ireq = install_req_from_line(
        line,
        user_supplied=template.user_supplied,
        comes_from=template.comes_from,
        isolated=template.isolated,
        constraint=template.constraint,
        hash_options=template.hash_options,
        config_settings=template.config_settings,
    )
    ireq.satisfied_by = dist
    return ireq


class _InstallRequirementBackedCandidate(Candidate): | , __future__, collections, logging, pip, sys, typing | L229: # TODO performance: this means we iterate the dependencies at least twice,
L289: logger.debug("Using cached wheel link: %s", cache_entry.link)
L374: # TODO: Supply reason based on force_reinstall and upgrade_strategy. |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/factory.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get the candidate for the currently-installed version."""
            # If --force-reinstall is set, we want the version from the index
            # instead, so we "pretend" there is nothing installed.
            if self._force_reinstall:
                return None
            try:
                installed_dist = self._installed_dists[name]
            except KeyError:
                return None

            try:
                # Don't use the installed distribution if its version
                # does not fit the current dependency graph.
                if not specifier.contains(installed_dist.version, prereleases=True):
                    return None
            except InvalidVersion as e:
                raise InvalidInstalledPackage(dist=installed_dist, invalid_exc=e)

            candidate = self._make_candidate_from_dist(
                dist=installed_dist,
                extras=extras,
                template=template,
            )
            # The candidate is a known incompatibility. Don't use it.
            if id(candidate) in incompatible_ids:
                return None
            return candidate

        def iter_index_candidate_infos() -> Iterator[IndexCandidateInfo]:
            result = self._finder.find_best_candidate( | , __future__, collections, contextlib, functools, logging, pip, typing | L194: # TODO: Check already installed candidate, and use it if the link and
L363: # get a BaseCandidate here, unless there's a bug elsewhere. |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/found_candidates.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Utilities to lazily create and visit candidates found.

Creating and visiting a candidate is a *very* costly operation. It involves
fetching, extracting, potentially building modules from source, and verifying
distribution metadata. It is therefore crucial for performance to keep
everything here lazy all the way down, so we only touch candidates that we
absolutely need, and not "download the world" when we only need one version of
something. | , __future__, collections, logging, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/provider.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get item from a package name lookup mapping with a resolver identifier.

    This extra logic is needed when the target mapping is keyed by package
    name, which cannot be directly looked up with an identifier (which may
    contain requested extras). Additional logic is added to also look up a value
    by "cleaning up" the extras from the identifier. | , __future__, collections, functools, math, pip, typing | L67: # HACK: Theoretically we should check whether this identifier is a valid
L186: * Alphabetical order for consistency (aids debuggability). |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/reporter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Report a candidate being rejected.

        Logs both the rejection count message (if applicable) and details about
        the requirements and constraints that caused the rejection. | , __future__, collections, logging, pip, typing | L70: logger.debug(msg)
L73: class PipDebuggingReporter(BaseReporter[Requirement, Candidate, str]):
L84: logger.debug("Reporter.ending_round(%r, %r)", index, state) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/requirements.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Requirement backed by an install requirement on a base package.
    Trims extras from its install requirement if there are any. | , __future__, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/resolution/resolvelib/resolver.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get order for installation of requirements in RequirementSet.

        The returned list contains a requirement before another that depends on
        it. This helps ensure that the environment is kept consistent as they
        get installed one-by-one.

        The current implementation creates a topological ordering of the
        dependency graph, giving more weight to packages with less
        or no dependencies, while breaking any cycles in the graph at
        arbitrary points. We make no guarantees about where the cycle
        would be broken, other than it *would* be broken. | , __future__, contextlib, functools, logging, os, pip, typing | L24: PipDebuggingReporter,
L87: if "PIP_RESOLVER_DEBUG" in os.environ:
L88: reporter: BaseReporter[Requirement, Candidate, str] = PipDebuggingReporter() |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/self_outdated_check.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert an ISO format string to a date.

    Handles the format 2020-01-22T14:24:01Z (trailing Z)
    which is not supported by older versions of fromisoformat. | __future__, dataclasses, datetime, functools, hashlib, json, logging, optparse, os, pip, sys, typing | L215: logger.debug("No remote pip version found")
L220: logger.debug("Remote version of pip: %s", remote_version)
L221: logger.debug("Local version of pip:  %s", local_version)
L224: logger.debug("Was pip installed by pip? %s", pip_installed_by_pip) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/_jaraco_text.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Functions brought over from jaraco.text.

These functions are not supposed to be used within `pip._internal`. These are
helper functions brought over from `jaraco.text` to enable vendoring newer
copies of `pkg_resources` without having to vendor `jaraco.text` and its entire
dependency cone; something that our vendoring setup is not currently capable of
handling.

License reproduced from original source below:

Copyright Jason R. Coombs

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to
deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE. | functools, itertools |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/_log.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Customize logging

Defines custom logger class for the `logger.verbose(...)` method.

init_logging() must be called before any other modules that call logging.getLogger. | logging, typing | L12: # between DEBUG and INFO
L19: VERBOSE is between INFO and DEBUG. |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/appdirs.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This code wraps the vendored appdirs module to so the return values are
compatible for the current pip code base.

The intention is to rewrite current usages gradually, keeping the tests pass,
and eventually drop this after all usages are changed. | os, pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Stuff that differs in different Python versions and platform
distributions. | _ssl, importlib, logging, os, pip, sys, tomllib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/compatibility_tags.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Generate and work with PEP 425 Compatibility Tags."""

from __future__ import annotations

import re

from pip._vendor.packaging.tags import (
    PythonVersion,
    Tag,
    android_platforms,
    compatible_tags,
    cpython_tags,
    generic_tags,
    interpreter_name,
    interpreter_version,
    ios_platforms,
    mac_platforms,
)

_apple_arch_pat = re.compile(r"(.+)_(\d+)_(\d+)_(.+)")


def version_info_to_nodot(version_info: tuple[int, ...]) -> str:
    # Only use up to the first two numbers.
    return "".join(map(str, version_info[:2]))


def _mac_platforms(arch: str) -> list[str]:
    match = _apple_arch_pat.match(arch)
    if match:
        name, major, minor, actual_arch = match.groups()
        mac_version = (int(major), int(minor))
        arches = [
            # Since we have always only checked that the platform starts
            # with "macosx", for backwards-compatibility we extract the
            # actual prefix provided by the user in case they provided
            # something like "macosxcustom_". It may be good to remove
            # this as undocumented or deprecate it in the future.
            "{}_{}".format(name, arch[len("macosx_") :])
            for arch in mac_platforms(mac_version, actual_arch)
        ]
    else:
        # arch pattern didn't match (?!)
        arches = [arch]
    return arches


def _ios_platforms(arch: str) -> list[str]:
    match = _apple_arch_pat.match(arch)
    if match:
        name, major, minor, actual_multiarch = match.groups()
        ios_version = (int(major), int(minor))
        arches = [
            # Since we have always only checked that the platform starts
            # with "ios", for backwards-compatibility we extract the
            # actual prefix provided by the user in case they provided
            # something like "ioscustom_". It may be good to remove
            # this as undocumented or deprecate it in the future.
            "{}_{}".format(name, arch[len("ios_") :])
            for arch in ios_platforms(ios_version, actual_multiarch)
        ]
    else:
        # arch pattern didn't match (?!)
        arches = [arch]
    return arches


def _android_platforms(arch: str) -> list[str]:
    match = re.fullmatch(r"android_(\d+)_(.+)", arch)
    if match:
        api_level, abi = match.groups()
        return list(android_platforms(int(api_level), abi))
    else:
        # arch pattern didn't match (?!)
        return [arch]


def _custom_manylinux_platforms(arch: str) -> list[str]:
    arches = [arch]
    arch_prefix, arch_sep, arch_suffix = arch.partition("_")
    if arch_prefix == "manylinux2014":
        # manylinux1/manylinux2010 wheels run on most manylinux2014 systems
        # with the exception of wheels depending on ncurses. PEP 599 states
        # manylinux1/manylinux2010 wheels should be considered
        # manylinux2014 wheels:
        # https://www.python.org/dev/peps/pep-0599/#backwards-compatibility-with-manylinux2010-wheels
        if arch_suffix in {"i686", "x86_64"}:
            arches.append("manylinux2010" + arch_sep + arch_suffix)
            arches.append("manylinux1" + arch_sep + arch_suffix)
    elif arch_prefix == "manylinux2010":
        # manylinux1 wheels run on most manylinux2010 systems with the
        # exception of wheels depending on ncurses. PEP 571 states
        # manylinux1 wheels should be considered manylinux2010 wheels:
        # https://www.python.org/dev/peps/pep-0571/#backwards-compatibility-with-manylinux1-wheels
        arches.append("manylinux1" + arch_sep + arch_suffix)
    return arches


def _get_custom_platforms(arch: str) -> list[str]:
    arch_prefix, arch_sep, arch_suffix = arch.partition("_")
    if arch.startswith("macosx"):
        arches = _mac_platforms(arch)
    elif arch.startswith("ios"):
        arches = _ios_platforms(arch)
    elif arch_prefix == "android":
        arches = _android_platforms(arch)
    elif arch_prefix in ["manylinux2014", "manylinux2010"]:
        arches = _custom_manylinux_platforms(arch)
    else:
        arches = [arch]
    return arches


def _expand_allowed_platforms(platforms: list[str] \\| None) -> list[str] \\| None:
    if not platforms:
        return None

    seen = set()
    result = []

    for p in platforms:
        if p in seen:
            continue
        additions = [c for c in _get_custom_platforms(p) if c not in seen]
        seen.update(additions)
        result.extend(additions)

    return result


def _get_python_version(version: str) -> PythonVersion:
    if len(version) > 1:
        return int(version[0]), int(version[1:])
    else:
        return (int(version[0]),)


def _get_custom_interpreter(
    implementation: str \\| None = None, version: str \\| None = None
) -> str:
    if implementation is None:
        implementation = interpreter_name()
    if version is None:
        version = interpreter_version()
    return f"{implementation}{version}"


def get_supported(
    version: str \\| None = None,
    platforms: list[str] \\| None = None,
    impl: str \\| None = None,
    abis: list[str] \\| None = None,
) -> list[Tag]: | __future__, pip, re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/datetime.py` | ❓ UNKNOWN | 2025-11-09 19:12 | For when pip wants to check the date or time."""

import datetime


def today_is_later_than(year: int, month: int, day: int) -> bool:
    today = datetime.date.today()
    given = datetime.date(year, month, day)

    return today > given | datetime |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/deprecation.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A module that implements tooling to enable easy warnings about deprecations. | __future__, logging, pip, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/direct_url_helpers.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert a DirectUrl to a pip requirement string."""
    direct_url.validate()  # if invalid, this is a pip bug
    requirement = name + " @ "
    fragments = []
    if isinstance(direct_url.info, VcsInfo):
        requirement += (
            f"{direct_url.info.vcs}+{direct_url.url}@{direct_url.info.commit_id}"
        )
    elif isinstance(direct_url.info, ArchiveInfo):
        requirement += direct_url.url
        if direct_url.info.hash:
            fragments.append(direct_url.info.hash)
    else:
        assert isinstance(direct_url.info, DirInfo)
        requirement += direct_url.url
    if direct_url.subdirectory:
        fragments.append("subdirectory=" + direct_url.subdirectory)
    if fragments:
        requirement += "#" + "&".join(fragments)
    return requirement


def direct_url_for_editable(source_dir: str) -> DirectUrl:
    return DirectUrl(
        url=path_to_url(source_dir),
        info=DirInfo(editable=True),
    )


def direct_url_from_link(
    link: Link, source_dir: str \\| None = None, link_is_in_wheel_cache: bool = False
) -> DirectUrl:
    if link.is_vcs:
        vcs_backend = vcs.get_backend_for_scheme(link.scheme)
        assert vcs_backend
        url, requested_revision, _ = vcs_backend.get_url_rev_and_auth(
            link.url_without_fragment
        )
        # For VCS links, we need to find out and add commit_id.
        if link_is_in_wheel_cache:
            # If the requested VCS link corresponds to a cached
            # wheel, it means the requested revision was an
            # immutable commit hash, otherwise it would not have
            # been cached. In that case we don't have a source_dir
            # with the VCS checkout.
            assert requested_revision
            commit_id = requested_revision
        else:
            # If the wheel was not in cache, it means we have
            # had to checkout from VCS to build and we have a source_dir
            # which we can inspect to find out the commit id.
            assert source_dir
            commit_id = vcs_backend.get_revision(source_dir)
        return DirectUrl(
            url=url,
            info=VcsInfo(
                vcs=vcs_backend.name,
                commit_id=commit_id,
                requested_revision=requested_revision,
            ),
            subdirectory=link.subdirectory_fragment,
        )
    elif link.is_existing_dir():
        return DirectUrl(
            url=link.url_without_fragment,
            info=DirInfo(),
            subdirectory=link.subdirectory_fragment,
        )
    else:
        hash = None
        hash_name = link.hash_name
        if hash_name:
            hash = f"{hash_name}={link.hash}"
        return DirectUrl(
            url=link.url_without_fragment,
            info=ArchiveInfo(hash=hash),
            subdirectory=link.subdirectory_fragment,
        ) | __future__, pip | L11: direct_url.validate()  # if invalid, this is a pip bug |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/egg_link.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert a Name metadata value to a .egg-link name, by applying
    the same substitution as pkg_resources's safe_name function.
    Note: we cannot use canonicalize_name because it has a different logic.

    We also look for the raw name (without normalization) as setuptools 69 changed
    the way it names .egg-link files (https://github.com/pypa/setuptools/issues/4167). | __future__, os, pip, re, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/entrypoints.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Central wrapper for all old entrypoints.

    Historically pip has had several entrypoints defined. Because of issues
    arising from PATH, sys.path, multiple Pythons, their interactions, and most
    of them having a pip installed, users suffer every time an entrypoint gets
    moved.

    To alleviate this pain, and provide a mechanism for warning users and
    directing them to an appropriate place for help, we now define all of
    our old entrypoints as wrappers for the current one. | __future__, itertools, os, pip, shutil, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/filesystem.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Return a file-like object pointing to a tmp file next to path.

    The file is created securely and is ensured to be written to disk
    after the context reaches its end.

    kwargs will be passed to tempfile.NamedTemporaryFile to control
    the way the temporary file will be opened. | __future__, collections, contextlib, fnmatch, os, pip, random, sys, tempfile, typing | L94: # os.access doesn't work on Windows: http://bugs.python.org/issue2528
L95: # and we can't use tempfile: http://bugs.python.org/issue22107 |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/filetypes.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Filetype information."""

from pip._internal.utils.misc import splitext

WHEEL_EXTENSION = ".whl"
BZ2_EXTENSIONS: tuple[str, ...] = (".tar.bz2", ".tbz")
XZ_EXTENSIONS: tuple[str, ...] = (
    ".tar.xz",
    ".txz",
    ".tlz",
    ".tar.lz",
    ".tar.lzma",
)
ZIP_EXTENSIONS: tuple[str, ...] = (".zip", WHEEL_EXTENSION)
TAR_EXTENSIONS: tuple[str, ...] = (".tar.gz", ".tgz", ".tar")
ARCHIVE_EXTENSIONS = ZIP_EXTENSIONS + BZ2_EXTENSIONS + TAR_EXTENSIONS + XZ_EXTENSIONS


def is_archive_file(name: str) -> bool: | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/glibc.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Try to determine the glibc version

    Returns a tuple of strings (lib, version) which default to empty strings
    in case the lookup fails. | __future__, ctypes, os, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/hashes.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A wrapper that builds multiple hashes at once and checks them against
    known-good values | __future__, collections, hashlib, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/logging.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Raised if BrokenPipeError occurs for the stdout stream while logging. | __future__, collections, contextlib, dataclasses, errno, io, logging, os, pip, sys, threading, typing | L51: # https://bugs.python.org/issue19612
L52: # https://bugs.python.org/issue30418
L254: level_number = logging.DEBUG
L273: root_level = "DEBUG"
L278: # Disable any logging besides WARNING unless we have DEBUG level logging
L280: vendored_log_level = "WARNING" if level in ["INFO", "ERROR"] else "DEBUG"
L348: "level": "DEBUG", |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/misc.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert a tuple of ints representing a Python version to one of length
    three.

    :param py_version_info: a tuple of ints representing a Python version,
        or None to specify no version. The tuple can have any length.

    :return: a tuple of length three if `py_version_info` is non-None.
        Otherwise, return `py_version_info` unchanged (i.e. None). | __future__, collections, dataclasses, errno, functools, getpass, hashlib, io, itertools, logging, os, pathlib, pip, posixpath, shutil, stat, sys, sysconfig, types, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/packaging.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Check if the given Python version matches a "Requires-Python" specifier.

    :param version_info: A 3-tuple of ints representing a Python
        major-minor-micro version to check (e.g. `sys.version_info[:3]`).

    :return: `True` if the given Python version satisfies the requirement.
        Otherwise, return `False`.

    :raises InvalidSpecifier: If `requires_python` has an invalid format. | __future__, functools, logging, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/retry.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Decorator to automatically retry a function on error.

    If the function raises, the function is recalled with the same arguments
    until it returns or the time limit is reached. When the time limit is
    surpassed, the last exception raised is reraised.

    :param wait: The time to wait after an error before retrying, in seconds.
    :param stop_after_delay: The time limit after which retries will cease,
        in seconds. | __future__, functools, time, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/subprocess.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Create a CommandArgs object. | __future__, collections, logging, os, pip, shlex, subprocess, typing | L76: stdout streams.  Otherwise, use DEBUG.  Defaults to False.
L94: # - We log this output to stderr at DEBUG level as it is received.
L95: # - If DEBUG logging isn't enabled (e.g. if --verbose logging wasn't
L103: # If show_stdout=True, then the above is still done, but with DEBUG |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/temp_dir.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Manages temp directory behavior"""

    def __init__(self) -> None:
        self._should_delete: dict[str, bool] = {}

    def set_delete(self, kind: str, value: bool) -> None: | __future__, collections, contextlib, errno, itertools, logging, os, pathlib, pip, tempfile, traceback, typing | L176: logger.debug("Created temporary directory: %s", path)
L198: logger.debug(
L204: logger.debug("%s failed with %s.", func.__qualname__, formatted_exc)
L293: logger.debug("Created temporary directory: %s", path) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/unpacking.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Utilities related archives."""

from __future__ import annotations

import logging
import os
import shutil
import stat
import sys
import tarfile
import zipfile
from collections.abc import Iterable
from zipfile import ZipInfo

from pip._internal.exceptions import InstallationError
from pip._internal.utils.filetypes import (
    BZ2_EXTENSIONS,
    TAR_EXTENSIONS,
    XZ_EXTENSIONS,
    ZIP_EXTENSIONS,
)
from pip._internal.utils.misc import ensure_dir

logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS = ZIP_EXTENSIONS + TAR_EXTENSIONS

try:
    import bz2  # noqa

    SUPPORTED_EXTENSIONS += BZ2_EXTENSIONS
except ImportError:
    logger.debug("bz2 module is not available")

try:
    # Only for Python 3.3+
    import lzma  # noqa

    SUPPORTED_EXTENSIONS += XZ_EXTENSIONS
except ImportError:
    logger.debug("lzma module is not available")


def current_umask() -> int: | __future__, bz2, collections, logging, lzma, os, pip, shutil, stat, sys, tarfile, zipfile | L34: logger.debug("bz2 module is not available")
L42: logger.debug("lzma module is not available")
L353: # FIXME: handle?
L354: # FIXME: magic signatures? |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/urls.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convert a path to a file: URL.  The path will be made absolute and have
    quoted path parts. | , os, string, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/virtualenv.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Checks if sys.base_prefix and sys.prefix match.

    This handles PEP 405 compliant virtual environments. | __future__, logging, os, re, site, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/utils/wheel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Support functions for working with wheel files."""

import logging
from email.message import Message
from email.parser import Parser
from zipfile import BadZipFile, ZipFile

from pip._vendor.packaging.utils import canonicalize_name

from pip._internal.exceptions import UnsupportedWheel

VERSION_COMPATIBLE = (1, 0)


logger = logging.getLogger(__name__)


def parse_wheel(wheel_zip: ZipFile, name: str) -> tuple[str, Message]: | email, logging, pip, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/vcs/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/vcs/bazaar.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Always assume the versions don't match"""
        return False


vcs.register(Bazaar) | __future__, logging, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/vcs/git.py` | ❓ UNKNOWN | 2025-11-09 19:12 | ^
    # Optional user, e.g. 'git@'
    (\w+@)?
    # Server, e.g. 'github.com'.
    ([^/:]+):
    # The server-side path. e.g. 'user/project.git'. Must start with an
    # alphanumeric character so as not to be confusable with a Windows paths
    # like 'C:/foo/bar' or 'C:\foo\bar'.
    (\w[^:]*)
    $ | __future__, dataclasses, logging, os, pathlib, pip, re, typing, urllib | L304: logger.debug("Rev options %s, branch_name %s", rev_options, branch_name) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/vcs/mercurial.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Return the repository-local changeset revision number, as an integer. | __future__, configparser, logging, os, pip | L54: flags = ("--verbose", "--debug")
L175: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/vcs/subversion.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Return the maximum revision for all files under a given location | __future__, logging, os, pip, re | L60: # FIXME: should we warn? |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/vcs/versioncontrol.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Handles all VCS (version control) support"""

from __future__ import annotations

import logging
import os
import shutil
import sys
import urllib.parse
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass, field
from typing import (
    Any,
    Literal,
    Optional,
)

from pip._internal.cli.spinners import SpinnerInterface
from pip._internal.exceptions import BadCommand, InstallationError
from pip._internal.utils.misc import (
    HiddenText,
    ask_path_exists,
    backup_dir,
    display_path,
    hide_url,
    hide_value,
    is_installable_dir,
    rmtree,
)
from pip._internal.utils.subprocess import (
    CommandArgs,
    call_subprocess,
    format_command_args,
    make_command,
)

__all__ = ["vcs"]


logger = logging.getLogger(__name__)

AuthInfo = tuple[Optional[str], Optional[str]]


def is_url(name: str) -> bool: | __future__, collections, dataclasses, logging, os, pip, shutil, sys, typing, urllib | L201: logger.debug("Registered VCS backend: %s", cls.name)
L217: logger.debug("Determine that %s uses VCS: %s", location, vcs_backend.name) |
| `blackboard-agent/venv/Lib/site-packages/pip/_internal/wheel_builder.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Orchestrator for building wheels from InstallRequirements."""

from __future__ import annotations

import logging
import os.path
import re
from collections.abc import Iterable
from tempfile import TemporaryDirectory

from pip._vendor.packaging.utils import canonicalize_name, canonicalize_version
from pip._vendor.packaging.version import InvalidVersion, Version

from pip._internal.cache import WheelCache
from pip._internal.exceptions import InvalidWheelFilename, UnsupportedWheel
from pip._internal.metadata import FilesystemWheel, get_wheel_distribution
from pip._internal.models.link import Link
from pip._internal.models.wheel import Wheel
from pip._internal.operations.build.wheel import build_wheel_pep517
from pip._internal.operations.build.wheel_editable import build_wheel_editable
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import ensure_dir, hash_file
from pip._internal.utils.urls import path_to_url
from pip._internal.vcs import vcs

logger = logging.getLogger(__name__)

_egg_info_re = re.compile(r"([a-z0-9_.]+)-([a-z0-9_.!+-]+)", re.IGNORECASE)

BuildResult = tuple[list[InstallRequirement], list[InstallRequirement]]


def _contains_egg_info(s: str) -> bool: | __future__, collections, logging, os, pip, re, tempfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pip._vendor is for vendoring dependencies of pip to prevent needing pip to
depend on something external.

Files inside of pip._vendor should be considered immutable and should only be
updated to versions from upstream. | __future__, glob, os, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | CacheControl import Interface.

Make it easy to import from cachecontrol without long namespaces. | logging, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/_cmd.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | __future__, argparse, logging, pip, typing | L23: logger.setLevel(logging.DEBUG) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/adapter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Send a request. Use the request information to see if it
        exists in the cache and cache the response if we need to and can. | __future__, functools, pip, types, typing, weakref, zlib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/cache.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The cache object API for implementing caches. The default is a thread
safe in-memory dictionary. | __future__, datetime, threading, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/caches/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/caches/file_cache.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Shared implementation for both FileCache variants."""

    def __init__(
        self,
        directory: str \\| Path,
        forever: bool = False,
        filemode: int = 0o0600,
        dirmode: int = 0o0700,
        lock_class: type[BaseFileLock] \\| None = None,
    ) -> None:
        try:
            if lock_class is None:
                from filelock import FileLock

                lock_class = FileLock
        except ImportError:
            notice = dedent( | __future__, datetime, filelock, hashlib, os, pathlib, pip, tempfile, textwrap, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/caches/redis_cache.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Helper for clearing all the keys in a database. Use with
        caution! | __future__, datetime, pip, redis, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/controller.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The httplib2 algorithms ported for use with requests. | __future__, calendar, email, logging, pip, re, time, typing, weakref | L120: logger.debug("Ignoring unknown cache-control directive: %s", directive)
L130: logger.debug(
L135: logger.debug(
L156: logger.debug("No cache entry available")
L176: logger.debug('Looking up "%s" in the cache', cache_url)
L181: logger.debug('Request header has "no-cache", cache bypassed')
L185: logger.debug('Request header has "max_age" as 0, cache bypassed')
L207: logger.debug(msg)
L215: logger.debug("Purging cached response: no date or etag")
L217: logger.debug("Ignoring cached response: no date")
L225: logger.debug("Current age based on date: %i", current_age)
L227: # TODO: There is an assumption that the result will be a
L240: logger.debug("Freshness lifetime from max-age: %i", freshness_lifetime)
L248: logger.debug("Freshness lifetime from expires: %i", freshness_lifetime)
L255: logger.debug(
L263: logger.debug("Adjusted current age from min-fresh: %i", current_age)
L267: logger.debug('The response is "fresh", returning cached response')
L268: logger.debug("%i > %i", freshness_lifetime, current_age)
L273: logger.debug('The cached response is "stale" with no etag, purging')
L350: logger.debug(
L383: logger.debug('Updating cache with response from "%s"', cache_url)
L389: logger.debug('Response header has "no-store"')
L392: logger.debug('Request header has "no-store"')
L394: logger.debug('Purging existing cache entry to honor "no-store"')
L405: logger.debug('Response header has "Vary: *"')
L418: logger.debug(f"etag object cached for {expires_time} seconds")
L419: logger.debug("Caching due to etag")
L425: logger.debug("Caching permanent redirect")
L438: logger.debug("Caching b/c date exists and max-age > 0")
L458: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/filewrapper.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Small wrapper around a fp object which will tee everything read into a
    buffer, and when that file is closed it will execute a callback with the
    contents of that buffer.

    All attributes are proxied to the underlying file object.

    This class uses members with a double underscore (__) leading prefix so as
    not to accidentally shadow an attribute.

    The data is stored in a temporary file until it is all available.  As long
    as the temporary files directory is disk-based (sometimes it's a
    memory-backed-``tmpfs`` on Linux), data will be unloaded to disk if memory
    pressure is high.  For small files the disk usually won't be used at all,
    it'll all be in the filesystem memory cache, so there should be no
    performance impact. | __future__, http, mmap, tempfile, typing | L67: # TODO: Add some logging here... |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/heuristics.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Return a valid 1xx warning header value describing the cache
        adjustments.

        The response is provided too allow warnings like 113
        http://tools.ietf.org/html/rfc7234#section-5.5.4 where we need
        to explicitly say response is over 24 hours old. | __future__, calendar, datetime, email, pip, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/serialize.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Verify our vary headers match and construct a real urllib3
        HTTPResponse object. | __future__, io, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/cachecontrol/wrapper.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | __future__, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/certifi/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/certifi/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | argparse, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/certifi/core.py` | ❓ UNKNOWN | 2025-11-09 19:12 | certifi.py
~~~~~~~~~~

This module returns the installation location of cacert.pem or its contents. | atexit, importlib, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/dependency_groups/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/dependency_groups/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , argparse, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/dependency_groups/_implementation.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An error representing the detection of a cycle. | __future__, collections, dataclasses, pip, re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/dependency_groups/_lint_dependency_groups.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , __future__, argparse, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/dependency_groups/_pip_wrapper.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , __future__, argparse, subprocess, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/dependency_groups/_toml_compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | pip, tomllib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distlib/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | logging |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distlib/compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Matching according to RFC 6125, section 6.4.3

        http://tools.ietf.org/html/rfc6125#section-6.4.3 | __builtin__, __future__, builtins, ConfigParser, configparser, html, htmlentitydefs, HTMLParser, http, httplib, io, itertools, os, Queue, queue, re, shutil, ssl, StringIO, sys, types, urllib, urllib2, urlparse, xmlrpc, xmlrpclib, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distlib/resources.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Is the cache stale for the given resource?

        :param resource: The :class:`Resource` being cached.
        :param path: The path of the resource in the cache.
        :return: True if the cache is stale. | , __future__, _frozen_importlib, _frozen_importlib_external, bisect, io, logging, os, pkgutil, sys, types, zipimport | L190: todo = [resource]
L191: while todo:
L192: resource = todo.pop(0)
L203: todo.append(child)
L239: logger.debug('_find failed: %r %r', path, self.loader.prefix)
L241: logger.debug('_find worked: %r %r', path, self.loader.prefix) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distlib/scripts.py` | ❓ UNKNOWN | 2025-11-09 19:12 | # Pre-fetch the contents of all executable wrapper stubs.
# This is to address https://github.com/pypa/pip/issues/12666.
# When updating pip, we rename the old pip in place before installing the
# new version. If we try to fetch a wrapper *after* that rename, the finder
# machinery will be confused as the package is no longer available at the
# location where it was imported from. So we load everything into memory in
# advance.

if os.name == 'nt' or (os.name == 'java' and os._name == 'nt'):
    # Issue 31: don't hardcode an absolute package name, but
    # determine it relative to the current package
    DISTLIB_PACKAGE = __name__.rsplit('.', 1)[0]

    WRAPPERS = {
        r.name: r.bytes
        for r in finder(DISTLIB_PACKAGE).iterator("")
        if r.name.endswith(".exe")
    }


def enquote_executable(executable):
    if ' ' in executable:
        # make sure we quote only the executable in case of env
        # for example /usr/bin/env "/dir with spaces/bin/jython"
        # instead of "/usr/bin/env /dir with spaces/bin/jython"
        # otherwise whole
        if executable.startswith('/usr/bin/env '):
            env, _executable = executable.split(' ', 1)
            if ' ' in _executable and not _executable.startswith('"'):
                executable = '%s "%s"' % (env, _executable)
        else:
            if not executable.startswith('"'):
                executable = '"%s"' % executable
    return executable


# Keep the old name around (for now), as there is at least one project using it!
_enquote_executable = enquote_executable


class ScriptMaker(object):
    """
    A class to copy or create scripts from source scripts or callable
    specifications.
    """
    script_template = SCRIPT_TEMPLATE

    executable = None  # for shebangs

    def __init__(self, source_dir, target_dir, add_launchers=True, dry_run=False, fileop=None):
        self.source_dir = source_dir
        self.target_dir = target_dir
        self.add_launchers = add_launchers
        self.force = False
        self.clobber = False
        # It only makes sense to set mode bits on POSIX.
        self.set_mode = (os.name == 'posix') or (os.name == 'java' and os._name == 'posix')
        self.variants = set(('', 'X.Y'))
        self._fileop = fileop or FileOperator(dry_run)

        self._is_nt = os.name == 'nt' or (os.name == 'java' and os._name == 'nt')
        self.version_info = sys.version_info

    def _get_alternate_executable(self, executable, options):
        if options.get('gui', False) and self._is_nt:  # pragma: no cover
            dn, fn = os.path.split(executable)
            fn = fn.replace('python', 'pythonw')
            executable = os.path.join(dn, fn)
        return executable

    if sys.platform.startswith('java'):  # pragma: no cover

        def _is_shell(self, executable):
            """
            Determine if the specified executable is a script
            (contains a #! line)
            """
            try:
                with open(executable) as fp:
                    return fp.read(2) == '#!'
            except (OSError, IOError):
                logger.warning('Failed to open %s', executable)
                return False

        def _fix_jython_executable(self, executable):
            if self._is_shell(executable):
                # Workaround for Jython is not needed on Linux systems.
                import java

                if java.lang.System.getProperty('os.name') == 'Linux':
                    return executable
            elif executable.lower().endswith('jython.exe'):
                # Use wrapper exe for Jython on Windows
                return executable
            return '/usr/bin/env %s' % executable

    def _build_shebang(self, executable, post_interp):
        """
        Build a shebang line. In the simple case (on Windows, or a shebang line
        which is not too long or contains spaces) use a simple formulation for
        the shebang. Otherwise, use /bin/sh as the executable, with a contrived
        shebang which allows the script to run either under Python or sh, using
        suitable quoting. Thanks to Harald Nordgren for his input.

        See also: http://www.in-ulm.de/~mascheck/various/shebang/#length
                  https://hg.mozilla.org/mozilla-central/file/tip/mach
        """
        if os.name != 'posix':
            simple_shebang = True
        elif getattr(sys, "cross_compiling", False):
            # In a cross-compiling environment, the shebang will likely be a
            # script; this *must* be invoked with the "safe" version of the
            # shebang, or else using os.exec() to run the entry script will
            # fail, raising "OSError 8 [Errno 8] Exec format error".
            simple_shebang = False
        else:
            # Add 3 for '#!' prefix and newline suffix.
            shebang_length = len(executable) + len(post_interp) + 3
            if sys.platform == 'darwin':
                max_shebang_length = 512
            else:
                max_shebang_length = 127
            simple_shebang = ((b' ' not in executable) and (shebang_length <= max_shebang_length))

        if simple_shebang:
            result = b'#!' + executable + post_interp + b'\n'
        else:
            result = b'#!/bin/sh\n'
            result += b" | , io, java, logging, os, re, struct, sys, time, zipfile | L297: logger.debug('Able to replace executable using '
L347: logger.debug('not copying %s (up-to-date)', script) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distlib/util.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Parse a marker string and return a dictionary containing a marker expression.

    The dictionary will contain keys "op", "lhs" and "rhs" for non-terminals in
    the expression grammar, or strings. A string contained in quotes is to be
    interpreted as a literal string, and a string not contained in quotes is a
    variable (such as os_name). | , codecs, collections, contextlib, csv, dummy_threading, glob, io, json, logging, os, py_compile, re, socket, ssl, subprocess, sys, tarfile, tempfile, textwrap, threading, time | L401: # TODO check k, v for valid values |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distro/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distro/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/distro/distro.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The ``distro`` package (``distro`` stands for Linux Distribution) provides
information about the Linux distribution it runs on, such as a reliable
machine-readable distro ID, or version information.

It is the recommended replacement for Python's original
:py:func:`platform.linux_distribution` function, but it provides much more
functionality. An alternative implementation became necessary because Python
3.5 deprecated this function, and Python 3.8 removed it altogether. Its
predecessor function :py:func:`platform.dist` was already deprecated since
Python 2.6 and removed in Python 3.8. Still, there are many cases in which
access to OS distribution information is needed. See `Python issue 1322
<https://bugs.python.org/issue1322>`_ for more information. | argparse, json, logging, os, re, shlex, subprocess, sys, typing, warnings | L28: <https://bugs.python.org/issue1322>`_ for more information. |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/codec.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , codecs, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/core.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base exception for all IDNA-encoding related problems"""

    pass


class IDNABidiError(IDNAError): | , bisect, re, typing, unicodedata |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/idnadata.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/intranges.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Given a list of integers, made up of (hopefully) a small number of long runs
of consecutive integers, compute a representation of the form
((start1, end1), (start2, end2) ...). Then answer the question "was x present
in the original list?" in time O(log(# runs)). | bisect, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/package_data.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/idna/uts46data.py` | ❓ UNKNOWN | 2025-11-09 19:12 | IDNA Mapping Table from UTS46."""


__version__ = "15.1.0"


def _seg_0() -> List[Union[Tuple[int, str], Tuple[int, str, str]]]:
    return [
        (0x0, "3"),
        (0x1, "3"),
        (0x2, "3"),
        (0x3, "3"),
        (0x4, "3"),
        (0x5, "3"),
        (0x6, "3"),
        (0x7, "3"),
        (0x8, "3"),
        (0x9, "3"),
        (0xA, "3"),
        (0xB, "3"),
        (0xC, "3"),
        (0xD, "3"),
        (0xE, "3"),
        (0xF, "3"),
        (0x10, "3"),
        (0x11, "3"),
        (0x12, "3"),
        (0x13, "3"),
        (0x14, "3"),
        (0x15, "3"),
        (0x16, "3"),
        (0x17, "3"),
        (0x18, "3"),
        (0x19, "3"),
        (0x1A, "3"),
        (0x1B, "3"),
        (0x1C, "3"),
        (0x1D, "3"),
        (0x1E, "3"),
        (0x1F, "3"),
        (0x20, "3"),
        (0x21, "3"),
        (0x22, "3"),
        (0x23, "3"),
        (0x24, "3"),
        (0x25, "3"),
        (0x26, "3"),
        (0x27, "3"),
        (0x28, "3"),
        (0x29, "3"),
        (0x2A, "3"),
        (0x2B, "3"),
        (0x2C, "3"),
        (0x2D, "V"),
        (0x2E, "V"),
        (0x2F, "3"),
        (0x30, "V"),
        (0x31, "V"),
        (0x32, "V"),
        (0x33, "V"),
        (0x34, "V"),
        (0x35, "V"),
        (0x36, "V"),
        (0x37, "V"),
        (0x38, "V"),
        (0x39, "V"),
        (0x3A, "3"),
        (0x3B, "3"),
        (0x3C, "3"),
        (0x3D, "3"),
        (0x3E, "3"),
        (0x3F, "3"),
        (0x40, "3"),
        (0x41, "M", "a"),
        (0x42, "M", "b"),
        (0x43, "M", "c"),
        (0x44, "M", "d"),
        (0x45, "M", "e"),
        (0x46, "M", "f"),
        (0x47, "M", "g"),
        (0x48, "M", "h"),
        (0x49, "M", "i"),
        (0x4A, "M", "j"),
        (0x4B, "M", "k"),
        (0x4C, "M", "l"),
        (0x4D, "M", "m"),
        (0x4E, "M", "n"),
        (0x4F, "M", "o"),
        (0x50, "M", "p"),
        (0x51, "M", "q"),
        (0x52, "M", "r"),
        (0x53, "M", "s"),
        (0x54, "M", "t"),
        (0x55, "M", "u"),
        (0x56, "M", "v"),
        (0x57, "M", "w"),
        (0x58, "M", "x"),
        (0x59, "M", "y"),
        (0x5A, "M", "z"),
        (0x5B, "3"),
        (0x5C, "3"),
        (0x5D, "3"),
        (0x5E, "3"),
        (0x5F, "3"),
        (0x60, "3"),
        (0x61, "V"),
        (0x62, "V"),
        (0x63, "V"),
    ]


def _seg_1() -> List[Union[Tuple[int, str], Tuple[int, str, str]]]:
    return [
        (0x64, "V"),
        (0x65, "V"),
        (0x66, "V"),
        (0x67, "V"),
        (0x68, "V"),
        (0x69, "V"),
        (0x6A, "V"),
        (0x6B, "V"),
        (0x6C, "V"),
        (0x6D, "V"),
        (0x6E, "V"),
        (0x6F, "V"),
        (0x70, "V"),
        (0x71, "V"),
        (0x72, "V"),
        (0x73, "V"),
        (0x74, "V"),
        (0x75, "V"),
        (0x76, "V"),
        (0x77, "V"),
        (0x78, "V"),
        (0x79, "V"),
        (0x7A, "V"),
        (0x7B, "3"),
        (0x7C, "3"),
        (0x7D, "3"),
        (0x7E, "3"),
        (0x7F, "3"),
        (0x80, "X"),
        (0x81, "X"),
        (0x82, "X"),
        (0x83, "X"),
        (0x84, "X"),
        (0x85, "X"),
        (0x86, "X"),
        (0x87, "X"),
        (0x88, "X"),
        (0x89, "X"),
        (0x8A, "X"),
        (0x8B, "X"),
        (0x8C, "X"),
        (0x8D, "X"),
        (0x8E, "X"),
        (0x8F, "X"),
        (0x90, "X"),
        (0x91, "X"),
        (0x92, "X"),
        (0x93, "X"),
        (0x94, "X"),
        (0x95, "X"),
        (0x96, "X"),
        (0x97, "X"),
        (0x98, "X"),
        (0x99, "X"),
        (0x9A, "X"),
        (0x9B, "X"),
        (0x9C, "X"),
        (0x9D, "X"),
        (0x9E, "X"),
        (0x9F, "X"),
        (0xA0, "3", " "),
        (0xA1, "V"),
        (0xA2, "V"),
        (0xA3, "V"),
        (0xA4, "V"),
        (0xA5, "V"),
        (0xA6, "V"),
        (0xA7, "V"),
        (0xA8, "3", " ̈"),
        (0xA9, "V"),
        (0xAA, "M", "a"),
        (0xAB, "V"),
        (0xAC, "V"),
        (0xAD, "I"),
        (0xAE, "V"),
        (0xAF, "3", " ̄"),
        (0xB0, "V"),
        (0xB1, "V"),
        (0xB2, "M", "2"),
        (0xB3, "M", "3"),
        (0xB4, "3", " ́"),
        (0xB5, "M", "μ"),
        (0xB6, "V"),
        (0xB7, "V"),
        (0xB8, "3", " ̧"),
        (0xB9, "M", "1"),
        (0xBA, "M", "o"),
        (0xBB, "V"),
        (0xBC, "M", "1⁄4"),
        (0xBD, "M", "1⁄2"),
        (0xBE, "M", "3⁄4"),
        (0xBF, "V"),
        (0xC0, "M", "à"),
        (0xC1, "M", "á"),
        (0xC2, "M", "â"),
        (0xC3, "M", "ã"),
        (0xC4, "M", "ä"),
        (0xC5, "M", "å"),
        (0xC6, "M", "æ"),
        (0xC7, "M", "ç"),
    ]


def _seg_2() -> List[Union[Tuple[int, str], Tuple[int, str, str]]]:
    return [
        (0xC8, "M", "è"),
        (0xC9, "M", "é"),
        (0xCA, "M", "ê"),
        (0xCB, "M", "ë"),
        (0xCC, "M", "ì"),
        (0xCD, "M", "í"),
        (0xCE, "M", "î"),
        (0xCF, "M", "ï"),
        (0xD0, "M", "ð"),
        (0xD1, "M", "ñ"),
        (0xD2, "M", "ò"),
        (0xD3, "M", "ó"),
        (0xD4, "M", "ô"),
        (0xD5, "M", "õ"),
        (0xD6, "M", "ö"),
        (0xD7, "V"),
        (0xD8, "M", "ø"),
        (0xD9, "M", "ù"),
        (0xDA, "M", "ú"),
        (0xDB, "M", "û"),
        (0xDC, "M", "ü"),
        (0xDD, "M", "ý"),
        (0xDE, "M", "þ"),
        (0xDF, "D", "ss"),
        (0xE0, "V"),
        (0xE1, "V"),
        (0xE2, "V"),
        (0xE3, "V"),
        (0xE4, "V"),
        (0xE5, "V"),
        (0xE6, "V"),
        (0xE7, "V"),
        (0xE8, "V"),
        (0xE9, "V"),
        (0xEA, "V"),
        (0xEB, "V"),
        (0xEC, "V"),
        (0xED, "V"),
        (0xEE, "V"),
        (0xEF, "V"),
        (0xF0, "V"),
        (0xF1, "V"),
        (0xF2, "V"),
        (0xF3, "V"),
        (0xF4, "V"),
        (0xF5, "V"),
        (0xF6, "V"),
        (0xF7, "V"),
        (0xF8, "V"),
        (0xF9, "V"),
        (0xFA, "V"),
        (0xFB, "V"),
        (0xFC, "V"),
        (0xFD, "V"),
        (0xFE, "V"),
        (0xFF, "V"),
        (0x100, "M", "ā"),
        (0x101, "V"),
        (0x102, "M", "ă"),
        (0x103, "V"),
        (0x104, "M", "ą"),
        (0x105, "V"),
        (0x106, "M", "ć"),
        (0x107, "V"),
        (0x108, "M", "ĉ"),
        (0x109, "V"),
        (0x10A, "M", "ċ"),
        (0x10B, "V"),
        (0x10C, "M", "č"),
        (0x10D, "V"),
        (0x10E, "M", "ď"),
        (0x10F, "V"),
        (0x110, "M", "đ"),
        (0x111, "V"),
        (0x112, "M", "ē"),
        (0x113, "V"),
        (0x114, "M", "ĕ"), | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/msgpack/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Pack object `o` and write it to `stream`

    See :class:`Packer` for options. | , os |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/msgpack/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base class for some exceptions raised while unpacking.

    NOTE: unpack may raise exception other than subclass of
    UnpackException.  If you want to catch all error, catch
    Exception instead. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/msgpack/ext.py` | ❓ UNKNOWN | 2025-11-09 19:12 | ExtType represents ext type in msgpack."""

    def __new__(cls, code, data):
        if not isinstance(code, int):
            raise TypeError("code must be int")
        if not isinstance(data, bytes):
            raise TypeError("data must be bytes")
        if not 0 <= code <= 127:
            raise ValueError("code must be 0~127")
        return super().__new__(cls, code, data)


class Timestamp: | collections, datetime, struct |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/msgpack/fallback.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Fallback pure Python implementation of msgpack"""

import struct
import sys
from datetime import datetime as _DateTime

if hasattr(sys, "pypy_version_info"):
    from __pypy__ import newlist_hint
    from __pypy__.builders import BytesBuilder

    _USING_STRINGBUILDER = True

    class BytesIO:
        def __init__(self, s=b""):
            if s:
                self.builder = BytesBuilder(len(s))
                self.builder.append(s)
            else:
                self.builder = BytesBuilder()

        def write(self, s):
            if isinstance(s, memoryview):
                s = s.tobytes()
            elif isinstance(s, bytearray):
                s = bytes(s)
            self.builder.append(s)

        def getvalue(self):
            return self.builder.build()

else:
    from io import BytesIO

    _USING_STRINGBUILDER = False

    def newlist_hint(size):
        return []


from .exceptions import BufferFull, ExtraData, FormatError, OutOfData, StackError
from .ext import ExtType, Timestamp

EX_SKIP = 0
EX_CONSTRUCT = 1
EX_READ_ARRAY_HEADER = 2
EX_READ_MAP_HEADER = 3

TYPE_IMMEDIATE = 0
TYPE_ARRAY = 1
TYPE_MAP = 2
TYPE_RAW = 3
TYPE_BIN = 4
TYPE_EXT = 5

DEFAULT_RECURSE_LIMIT = 511


def _check_type_strict(obj, t, type=type, tuple=tuple):
    if type(t) is tuple:
        return type(obj) in t
    else:
        return type(obj) is t


def _get_data_from_buffer(obj):
    view = memoryview(obj)
    if view.itemsize != 1:
        raise ValueError("cannot unpack from multi-byte object")
    return view


def unpackb(packed, **kwargs): | , __pypy__, datetime, io, struct, sys | L499: # TODO should we eliminate the recursion? |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/_elffile.py` | ❓ UNKNOWN | 2025-11-09 19:12 | ELF file parser.

This provides a class ``ELFFile`` that parses an ELF executable in a similar
interface to ``ZipFile``. Only the read interface is implemented.

Based on: https://gist.github.com/lyssdod/f51579ae8d93c8657a5564aefc2ffbca
ELF header: https://refspecs.linuxfoundation.org/elf/gabi4+/ch4.eheader.html | __future__, enum, os, struct, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/_manylinux.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Primary implementation of glibc_version_string using os.confstr. | , __future__, _manylinux, collections, contextlib, ctypes, functools, os, re, sys, typing, warnings | L238: # https://sourceware.org/bugzilla/show_bug.cgi?id=24636 |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/_musllinux.py` | ❓ UNKNOWN | 2025-11-09 19:12 | PEP 656 support.

This module implements logic to detect if the currently running Python is
linked against musl, and what musl version is used. | , __future__, functools, re, subprocess, sys, sysconfig, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/_parser.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Handwritten parser of dependency specifiers.

The docstring for each __parse_* function contains EBNF-inspired grammar representing
the implementation. | , __future__, ast, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/_structures.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/_tokenizer.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The provided source text could not be parsed correctly."""

    def __init__(
        self,
        message: str,
        *,
        source: str,
        span: tuple[int, int],
    ) -> None:
        self.span = span
        self.message = message
        self.source = source

        super().__init__()

    def __str__(self) -> str:
        marker = " " * self.span[0] + "~" * (self.span[1] - self.span[0]) + "^"
        return "\n    ".join([self.message, self.source, marker])


DEFAULT_RULES: dict[str, str \\| re.Pattern[str]] = {
    "LEFT_PARENTHESIS": r"\(",
    "RIGHT_PARENTHESIS": r"\)",
    "LEFT_BRACKET": r"\[",
    "RIGHT_BRACKET": r"\]",
    "SEMICOLON": r";",
    "COMMA": r",",
    "QUOTED_STRING": re.compile(
        r | , __future__, contextlib, dataclasses, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/licenses/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Raised when a license-expression string is invalid

    >>> canonicalize_license_expression("invalid")
    Traceback (most recent call last):
        ...
    packaging.licenses.InvalidLicenseExpression: Invalid license expression: 'invalid' | __future__, pip, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/licenses/_spdx.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/markers.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An invalid marker was found, users should refer to PEP 508. | , __future__, operator, os, platform, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/metadata.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A minimal implementation of :external:exc:`ExceptionGroup` from Python 3.11.

        If :external:exc:`ExceptionGroup` is already defined by Python itself,
        that version is used instead. | , __future__, email, pathlib, sys, typing | L204: # TODO: The spec doesn't say anything about if the keys should be |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/requirements.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An invalid requirement was found, users should refer to PEP 508. | , __future__, typing | L29: # TODO: Can we test whether something is contained within a requirement?
L32: # TODO: Can we normalize the name and extra name? |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/specifiers.py` | ❓ UNKNOWN | 2025-11-09 19:12 | .. testsetup::

    from pip._vendor.packaging.specifiers import Specifier, SpecifierSet, InvalidSpecifier
    from pip._vendor.packaging.version import Version | , __future__, abc, itertools, pip, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/tags.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A representation of the tag triple for a wheel.

    Instances are considered immutable and thus are hashable. Equality checking
    is also supported. | , __future__, importlib, logging, platform, re, struct, subprocess, sys, sysconfig, typing | L115: logger.debug(
L155: threading = debug = pymalloc = ucs4 = ""
L156: with_debug = _get_config_var("Py_DEBUG", warn)
L158: # Windows doesn't set Py_DEBUG, so checking for support of debug-compiled
L162: if with_debug or (with_debug is None and (has_refcount or has_ext)):
L163: debug = "d"
L176: elif debug:
L177: # Debug builds can also load "normal" extension modules.
L180: abis.insert(0, f"cp{version}{threading}{debug}{pymalloc}{ucs4}")
L378: # TODO: Need to care about 32-bit PPC for ppc64 through 10.2? |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/utils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An invalid distribution name; users should refer to the packaging user guide. | , __future__, functools, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/packaging/version.py` | ❓ UNKNOWN | 2025-11-09 19:12 | .. testsetup::

    from pip._vendor.packaging.version import parse, Version | , __future__, itertools, pip, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pkg_resources/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Package resource API
--------------------

A resource is a logical file contained within a package, or a logical
subdirectory thereof.  The package resource API expects resource names
to have their path parts separated with ``/``, *not* whatever the local
path separator is.  Do not use os.path operations to manipulate resource
names being passed into the API.

The package resource API is designed to work with normal filesystem packages,
.egg files, and unpacked .egg files.  It can also work in a limited way with
.zip files and with custom PEP 302 loaders that support the ``get_data()``
method.

This module is deprecated. Users are directed to :mod:`importlib.resources`,
:mod:`importlib.metadata` and :pypi:`packaging` instead. | __future__, _imp, _typeshed, collections, email, errno, functools, importlib, inspect, io, ntpath, operator, os, pip, pkgutil, platform, plistlib, posixpath, re, stat, sys, tempfile, textwrap, time, types, typing, typing_extensions, warnings, zipfile, zipimport | L1: # TODO: Add Generic type annotations to initialized collections.
L122: _ResourceStream = Any  # TODO / Incomplete: A readable file-like object
L455: needs some hacks for Linux and macOS. |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Utilities for determining application-specific dirs.

See <https://github.com/platformdirs/platformdirs> for details and usage. | , __future__, os, pathlib, pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Main entry point."""

from __future__ import annotations

from pip._vendor.platformdirs import PlatformDirs, __version__

PROPS = (
    "user_data_dir",
    "user_config_dir",
    "user_cache_dir",
    "user_state_dir",
    "user_log_dir",
    "user_documents_dir",
    "user_downloads_dir",
    "user_pictures_dir",
    "user_videos_dir",
    "user_music_dir",
    "user_runtime_dir",
    "site_data_dir",
    "site_config_dir",
    "site_cache_dir",
    "site_runtime_dir",
)


def main() -> None: | __future__, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/android.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Android."""

from __future__ import annotations

import os
import re
import sys
from functools import lru_cache
from typing import TYPE_CHECKING, cast

from .api import PlatformDirsABC


class Android(PlatformDirsABC): | , __future__, android, functools, jnius, os, re, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/api.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base API."""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator
    from typing import Literal


class PlatformDirsABC(ABC):  # noqa: PLR0904 | __future__, abc, collections, os, pathlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/macos.py` | ❓ UNKNOWN | 2025-11-09 19:12 | macOS."""

from __future__ import annotations

import os.path
import sys
from typing import TYPE_CHECKING

from .api import PlatformDirsABC

if TYPE_CHECKING:
    from pathlib import Path


class MacOS(PlatformDirsABC): | , __future__, os, pathlib, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/unix.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Unix."""

from __future__ import annotations

import os
import sys
from configparser import ConfigParser
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from .api import PlatformDirsABC

if TYPE_CHECKING:
    from collections.abc import Iterator

if sys.platform == "win32":

    def getuid() -> NoReturn:
        msg = "should only be used on Unix"
        raise RuntimeError(msg)

else:
    from os import getuid


class Unix(PlatformDirsABC):  # noqa: PLR0904 | , __future__, collections, configparser, os, pathlib, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/version.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/platformdirs/windows.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Windows."""

from __future__ import annotations

import os
import sys
from functools import lru_cache
from typing import TYPE_CHECKING

from .api import PlatformDirsABC

if TYPE_CHECKING:
    from collections.abc import Callable


class Windows(PlatformDirsABC): | , __future__, collections, ctypes, functools, os, sys, typing, winreg |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Pygments
    ~~~~~~~~

    Pygments is a syntax highlighting package written in Python.

    It is a generic syntax highlighter for general use in all kinds of software
    such as forum systems, wikis or other applications that need to prettify
    source code. Highlights are:

    * a wide range of common languages and markup formats is supported
    * special attention is paid to details, increasing quality by a fair amount
    * support for new languages and formats are added easily
    * a number of output formats, presently HTML, LaTeX, RTF, SVG, all image
      formats that PIL supports, and ANSI sequences
    * it is usable as a command-line tool and as a library
    * ... and it highlights even Brainfuck!

    The `Pygments master branch`_ is installable with ``easy_install Pygments==dev``.

    .. _Pygments master branch:
       https://github.com/pygments/pygments/archive/master.zip#egg=Pygments-dev

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | io, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.__main__
    ~~~~~~~~~~~~~~~~~

    Main entry point for ``python -m pygments``.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | pip, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/console.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.console
    ~~~~~~~~~~~~~~~~

    Format colored console output.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/filter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.filter
    ~~~~~~~~~~~~~~~

    Module that implements the default filter.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/filters/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.filters
    ~~~~~~~~~~~~~~~~

    Module containing filter lookup functions and default
    filters.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | pip, re | L72: highlight ``XXX``, ``TODO``, ``FIXME``, ``BUG`` and ``NOTE``.
L75: Now recognizes ``FIXME`` by default.
L81: ['XXX', 'TODO', 'FIXME', 'BUG', 'NOTE']) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/formatter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.formatter
    ~~~~~~~~~~~~~~~~~~

    Base formatter class.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | codecs, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/formatters/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.formatters
    ~~~~~~~~~~~~~~~~~~~

    Pygments formatters.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | fnmatch, os, pip, re, sys, types |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/formatters/_mapping.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/lexer.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.lexer
    ~~~~~~~~~~~~~~

    Base lexer classes.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | pip, re, sys, time |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/lexers/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.lexers
    ~~~~~~~~~~~~~~~

    Pygments lexers.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | fnmatch, os, pip, re, sys, types |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/lexers/_mapping.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  | L64: 'BugsLexer': ('pip._vendor.pygments.lexers.modeling', 'BUGS', ('bugs', 'winbugs', 'openbugs'), ('*.bug',), ()),
L241: 'JagsLexer': ('pip._vendor.pygments.lexers.modeling', 'JAGS', ('jags',), ('*.jag', '*.bug'), ()), |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/lexers/python.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.lexers.python
    ~~~~~~~~~~~~~~~~~~~~~~

    Lexers for Python and related languages.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | keyword, pip | L185: (r'(=\s*)?'         # debug (https://bugs.python.org/issue36817)
L190: (r'(=\s*)?'         # debug (https://bugs.python.org/issue36817) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/modeline.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.modeline
    ~~~~~~~~~~~~~~~~~

    A simple modeline parser (based on pymodeline).

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/plugin.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.plugin
    ~~~~~~~~~~~~~~~

    Pygments plugin interface.

    lexer plugins::

        [pygments.lexers]
        yourlexer = yourmodule:YourLexer

    formatter plugins::

        [pygments.formatters]
        yourformatter = yourformatter:YourFormatter
        /.ext = yourformatter:YourFormatter

    As you can see, you can define extensions for the formatter
    with a leading slash.

    syntax plugins::

        [pygments.styles]
        yourstyle = yourstyle:YourStyle

    filter plugin::

        [pygments.filter]
        yourfilter = yourfilter:YourFilter


    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | importlib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/regexopt.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.regexopt
    ~~~~~~~~~~~~~~~~~

    An algorithm that generates optimized regexes for matching long lists of
    literal strings.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | itertools, operator, os, re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/scanner.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.scanner
    ~~~~~~~~~~~~~~~~

    This library implements a regex based scanner. Some languages
    like Pascal are easy to parse but have some keywords that
    depend on the context. Because of this it's impossible to lex
    that just by using a regular expression lexer like the
    `RegexLexer`.

    Have a look at the `DelphiLexer` to get an idea of how to use
    this scanner.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/sphinxext.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.sphinxext
    ~~~~~~~~~~~~~~~~~~

    Sphinx extension to generate automatic documentation of lexers,
    formatters and filters.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | docutils, inspect, pathlib, pip, sphinx, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/style.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.style
    ~~~~~~~~~~~~~~

    Basic style object.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/styles/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.styles
    ~~~~~~~~~~~~~~~

    Contains built-in styles.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/styles/_mapping.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/token.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.token
    ~~~~~~~~~~~~~~

    Basic token types and the standard tokens.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/unistring.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.unistring
    ~~~~~~~~~~~~~~~~~~

    Strings of all Unicode characters of a certain category.
    Used for matching in Unicode-aware languages. Run to regenerate.

    Inspired by chartypes_create.py from the MoinMoin project.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | unicodedata | L125: # Hack to avoid combining this combining with the preceding high |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pygments/util.py` | ❓ UNKNOWN | 2025-11-09 19:12 | pygments.util
    ~~~~~~~~~~~~~

    Utility functions.

    :copyright: Copyright 2006-2025 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details. | io, locale, re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pyproject_hooks/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Wrappers to call pyproject.toml-based build backend hooks. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pyproject_hooks/_impl.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A protocol for the subprocess runner."""

        def __call__(
            self,
            cmd: Sequence[str],
            cwd: Optional[str] = None,
            extra_environ: Optional[Mapping[str, str]] = None,
        ) -> None:
            ...


def write_json(obj: Mapping[str, Any], path: str, **kwargs) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, **kwargs)


def read_json(path: str) -> Mapping[str, Any]:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


class BackendUnavailable(Exception): | , contextlib, json, os, subprocess, sys, tempfile, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pyproject_hooks/_in_process/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This is a subpackage because the directory is on sys.path for _in_process.py

The subpackage should stay as empty as possible to avoid shadowing modules that
the backend might import. | importlib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/pyproject_hooks/_in_process/_in_process.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This is invoked in a subprocess to call the build backend hooks.

It expects:
- Command line args: hook_name, control_dir
- Environment variables:
      _PYPROJECT_HOOKS_BUILD_BACKEND=entry.point:spec
      _PYPROJECT_HOOKS_BACKEND_PATH=paths (separated with os.pathsep)
- control_dir/input.json:
  - {"kwargs": {...}}

Results:
- control_dir/output.json
  - {"return_val": ...} | glob, importlib, json, os, re, shutil, sys, traceback, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Requests HTTP Library
~~~~~~~~~~~~~~~~~~~~~

Requests is an HTTP library, written in Python, for human beings.
Basic GET usage:

   >>> import requests
   >>> r = requests.get('https://www.python.org')
   >>> r.status_code
   200
   >>> b'Python is a programming language' in r.content
   True

... or POST:

   >>> payload = dict(key1='value1', key2='value2')
   >>> r = requests.post('https://httpbin.org/post', data=payload)
   >>> print(r.text)
   {
     ...
     "form": {
       "key1": "value1",
       "key2": "value2"
     },
     ...
   }

The other HTTP methods are supported - see `requests.api`. Full documentation
is at <https://requests.readthedocs.io>.

:copyright: (c) 2017 by Kenneth Reitz.
:license: Apache 2.0, see LICENSE for more details. | , cryptography, logging, pip, ssl, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/__version__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/_internal_utils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests._internal_utils
~~~~~~~~~~~~~~

Provides utility functions that are consumed internally by Requests
which depend on extremely few external helpers (such as compat) | , re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/adapters.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.adapters
~~~~~~~~~~~~~~~~~

This module contains the transport adapters that Requests uses to define
and maintain connections. | , os, pip, socket, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/api.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.api
~~~~~~~~~~~~

This module implements the Requests API.

:copyright: (c) 2012 by Kenneth Reitz.
:license: Apache2, see LICENSE for more details. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/auth.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.auth
~~~~~~~~~~~~~

This module contains the authentication handlers for Requests. | , base64, hashlib, os, re, threading, time, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/certs.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.certs
~~~~~~~~~~~~~~

This module returns the preferred default CA certificate bundle. There is
only one — the one from the certifi package.

If you are packaging Requests, e.g., for a Linux distribution or a managed
environment, you can change the definition of where() to return a separately
packaged CA bundle. | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.compat
~~~~~~~~~~~~~~~

This module previously handled import compatibility issues
between Python 2 and Python 3. It remains for backwards
compatibility until the next major version. | collections, http, io, json, pip, sys, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/cookies.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.cookies
~~~~~~~~~~~~~~~~

Compatibility code to be able to use `http.cookiejar.CookieJar` with requests.

requests.utils imports from here, so be careful with imports. | , calendar, copy, dummy_threading, threading, time |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of Requests' exceptions. | , pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/help.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Module containing bug report helper(s)."""

import json
import platform
import ssl
import sys

from pip._vendor import idna
from pip._vendor import urllib3

from . import __version__ as requests_version

charset_normalizer = None
chardet = None

try:
    from pip._vendor.urllib3.contrib import pyopenssl
except ImportError:
    pyopenssl = None
    OpenSSL = None
    cryptography = None
else:
    import cryptography
    import OpenSSL


def _implementation(): | , cryptography, json, OpenSSL, pip, platform, ssl, sys | L1: """Module containing bug report helper(s)."""
L63: """Generate information for a bug report."""
L122: """Pretty-print the bug information as JSON.""" |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/hooks.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.hooks
~~~~~~~~~~~~~~

This module provides the capabilities for the Requests hooks system.

Available hooks:

``response``:
    The response generated from a Request. |  | L19: # TODO: response is the only one |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/models.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.models
~~~~~~~~~~~~~~~

This module contains the primary objects that power Requests. | , datetime, encodings, io, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/packages.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/sessions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.sessions
~~~~~~~~~~~~~~~~~

This module provides a Session object to manage and persist settings across
requests (cookies, auth, proxies). | , collections, datetime, os, sys, time |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/status_codes.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The ``codes`` object defines a mapping from common names for HTTP statuses
to their numerical codes, accessible either as attributes or as dictionary
items.

Example::

    >>> import requests
    >>> requests.codes['temporary_redirect']
    307
    >>> requests.codes.teapot
    418
    >>> requests.codes['\o/']
    200

Some codes have multiple names, and both upper- and lower-case versions of
the names are allowed. For example, ``codes.ok``, ``codes.OK``, and
``codes.okay`` all correspond to the HTTP status code 200. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/structures.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.structures
~~~~~~~~~~~~~~~~~~~

Data structures that power Requests. | , collections |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/requests/utils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.utils
~~~~~~~~~~~~~~

This module provides utility functions that are used within Requests
that are also useful for external consumption. | , codecs, collections, contextlib, io, netrc, os, pip, re, socket, struct, sys, tempfile, warnings, winreg, zipfile | L246: # App Engine hackiness.
L442: # RFC is met will result in bugs with internet explorer and |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/providers.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Delegate class to provide the required interface for the resolver."""

    def identify(self, requirement_or_candidate: RT \\| CT) -> KT: | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/reporters.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Delegate class to provide progress reporting for the resolver."""

    def starting(self) -> None: | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/resolvers/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/resolvers/abstract.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The thing that performs the actual resolution work."""

    base_exception = Exception

    def __init__(
        self,
        provider: AbstractProvider[RT, CT, KT],
        reporter: BaseReporter[RT, CT, KT],
    ) -> None:
        self.provider = provider
        self.reporter = reporter

    def resolve(self, requirements: Iterable[RT], **kwargs: Any) -> Result[RT, CT, KT]: | , __future__, collections, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/resolvers/criterion.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Representation of possible resolution results of a package.

    This holds three attributes:

    * `information` is a collection of `RequirementInformation` pairs.
      Each pair is a requirement contributing to this criterion, and the
      candidate that provides the requirement.
    * `incompatibilities` is a collection of all known not-to-work candidates
      to exclude from consideration.
    * `candidates` is a collection containing all possible candidates deducted
      from the union of contributing requirements and known incompatibilities.
      It should never be empty, except when the criterion is an attribute of a
      raised `RequirementsConflicted` (in which case it is always empty).

    .. note::
        This class is intended to be externally immutable. **Do not** mutate
        any of its attribute containers. | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/resolvers/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A base class for all exceptions raised by this module.

    Exceptions derived by this class should all be handled in this module. Any
    bubbling pass the resolver should be treated as a bug. | , __future__, typing | L15: bubbling pass the resolver should be treated as a bug. |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/resolvers/resolution.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Stateful resolution object.

    This is designed as a one-off object that holds information to kick start
    the resolution process, and holds the results afterwards. | , __future__, collections, itertools, operator, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/resolvelib/structs.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Resolution state in a round."""

        mapping: dict[KT, CT]
        criteria: dict[KT, Criterion[RT, CT]]
        backtrack_causes: list[RequirementInformation[RT, CT]]

else:
    RequirementInformation = namedtuple(
        "RequirementInformation", ["requirement", "parent"]
    )
    State = namedtuple("State", ["mapping", "criteria", "backtrack_causes"])


class DirectedGraph(Generic[KT]): | , __future__, collections, itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Rich text and beautiful formatting in the terminal."""

import os
from typing import IO, TYPE_CHECKING, Any, Callable, Optional, Union

from ._extension import load_ipython_extension  # noqa: F401

__all__ = ["get_console", "reconfigure", "print", "inspect", "print_json"]

if TYPE_CHECKING:
    from .console import Console

# Global console used by alternative print
_console: Optional["Console"] = None

try:
    _IMPORT_CWD = os.path.abspath(os.getcwd())
except FileNotFoundError:
    # Can happen if the cwd has been deleted
    _IMPORT_CWD = ""


def get_console() -> "Console": | , os, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/__main__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get a renderable that demonstrates a number of features."""
    table = Table.grid(padding=1, pad_edge=True)
    table.title = "Rich features"
    table.add_column("Feature", no_wrap=True, justify="center", style="bold red")
    table.add_column("Demonstration")

    color_table = Table(
        box=None,
        expand=False,
        show_header=False,
        show_edge=False,
        pad_edge=False,
    )
    color_table.add_row(
        (
            "✓ [bold green]4-bit color[/]\n"
            "✓ [bold blue]8-bit color[/]\n"
            "✓ [bold magenta]Truecolor (16.7 million)[/]\n"
            "✓ [bold yellow]Dumb terminals[/]\n"
            "✓ [bold cyan]Automatic color conversion"
        ),
        ColorBox(),
    )

    table.add_row("Colors", color_table)

    table.add_row(
        "Styles",
        "All ansi styles: [bold]bold[/], [dim]dim[/], [italic]italic[/italic], [underline]underline[/], [strike]strikethrough[/], [reverse]reverse[/], and even [blink]blink[/].",
    )

    lorem = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. Quisque in metus sed sapien ultricies pretium a at justo. Maecenas luctus velit et auctor maximus."
    lorem_table = Table.grid(padding=1, collapse_padding=True)
    lorem_table.pad_edge = False
    lorem_table.add_row(
        Text(lorem, justify="left", style="green"),
        Text(lorem, justify="center", style="yellow"),
        Text(lorem, justify="right", style="blue"),
        Text(lorem, justify="full", style="red"),
    )
    table.add_row(
        "Text",
        Group(
            Text.from_markup( | colorsys, io, pip, time |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_cell_widths.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_emoji_codes.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_emoji_replace.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Replace emoji code in text."""
    get_emoji = EMOJI.__getitem__
    variants = {"text": "\uFE0E", "emoji": "\uFE0F"}
    get_variant = variants.get
    default_variant_code = variants.get(default_variant, "") if default_variant else ""

    def do_replace(match: Match[str]) -> str:
        emoji_code, emoji_name, variant = match.groups()
        try:
            return get_emoji(emoji_name.lower()) + get_variant(
                variant, default_variant_code
            )
        except KeyError:
            return emoji_code

    return _emoji_sub(do_replace, text) | , re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_export_format.py` | ❓ UNKNOWN | 2025-11-09 19:12 | CONSOLE_SVG_FORMAT = |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_extension.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_fileno.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get fileno() from a file, accounting for poorly implemented file-like objects.

    Args:
        file_like (IO): A file-like object.

    Returns:
        int \\| None: The result of fileno if available, or None if operation failed. | __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_inspect.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get the first paragraph from a docstring."""
    paragraph, _, _ = doc.partition("\n\n")
    return paragraph


class Inspect(JupyterMixin): | , inspect, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_log_render.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , datetime, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_loop.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Iterate and generate a tuple with a flag for first value."""
    iter_values = iter(values)
    try:
        value = next(iter_values)
    except StopIteration:
        return
    yield True, value
    for value in iter_values:
        yield False, value


def loop_last(values: Iterable[T]) -> Iterable[Tuple[bool, T]]: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_null_file.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_palettes.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_pick.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Pick the first non-none bool or return the last value.

    Args:
        *values (bool): Any number of boolean or None values.

    Returns:
        bool: First non-none boolean. | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_ratio.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Any object that defines an edge (such as Layout)."""

    size: Optional[int] = None
    ratio: int = 1
    minimum_size: int = 1


def ratio_resolve(total: int, edges: Sequence[Edge]) -> List[int]: | dataclasses, fractions, math, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_spinners.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Spinners are from:
* cli-spinners:
    MIT License
    Copyright (c) Sindre Sorhus <sindresorhus@gmail.com> (sindresorhus.com)
    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights to
    use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
    the Software, and to permit persons to whom the Software is furnished to do so,
    subject to the following conditions:
    The above copyright notice and this permission notice shall be included
    in all copies or substantial portions of the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
    INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
    PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
    FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
    IN THE SOFTWARE. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_stack.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A small shim over builtin list."""

    @property
    def top(self) -> T: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_timer.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Timer context manager, only used in debug. | contextlib, time, typing | L2: Timer context manager, only used in debug.
L14: """print the elapsed time. (only used in debugging)""" |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_win32_console.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Light wrapper around the Win32 Console API - this module should only be imported on Windows

The API that this module wraps is documented at https://docs.microsoft.com/en-us/windows/console/console-functions | ctypes, pip, sys, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_windows.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Windows features available."""

    vt: bool = False | ctypes, dataclasses, pip, platform, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_windows_renderer.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Makes appropriate Windows Console API calls based on the segments in the buffer.

    Args:
        buffer (Iterable[Segment]): Iterable of Segments to convert to Win32 API calls.
        term (LegacyWindowsTerm): Used to call the Windows Console API. | pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/_wrap.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Yields each word from the text as a tuple
    containing (start_index, end_index, word). A "word" in this context may
    include the actual word and any whitespace to the right. | , __future__, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/abc.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An abstract base class for Rich renderables.

    Note that there is no need to extend this class, the intended use is to check if an
    object supports the Rich renderable protocol. For example::

        if isinstance(my_object, RichRenderable):
            console.print(my_object) | abc, pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/align.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Align a renderable by adding spaces if necessary.

    Args:
        renderable (RenderableType): A console renderable.
        align (AlignMethod): One of "left", "center", or "right""
        style (StyleType, optional): An optional style to apply to the background.
        vertical (Optional[VerticalAlignMethod], optional): Optional vertical align, one of "top", "middle", or "bottom". Defaults to None.
        pad (bool, optional): Pad the right with spaces. Defaults to True.
        width (int, optional): Restrict contents to given width, or None to use default width. Defaults to None.
        height (int, optional): Set height of align renderable, or None to fit to contents. Defaults to None.

    Raises:
        ValueError: if ``align`` is not one of the expected values. | , itertools, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/ansi.py` | ❓ UNKNOWN | 2025-11-09 19:12 | (?:\x1b[0-?])\\|
(?:\x1b\](.*?)\x1b\\)\\|
(?:\x1b([(@-Z\\-_]\\|\[[0-?]*[ -/]*[@-~])) | , contextlib, io, os, pty, re, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/bar.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Renders a solid block bar.

    Args:
        size (float): Value for the end of the bar.
        begin (float): Begin point (between 0 and size, inclusive).
        end (float): End point (between 0 and size, inclusive).
        width (int, optional): Width of the bar, or ``None`` for maximum width. Defaults to None.
        color (Union[Color, str], optional): Color of the bar. Defaults to "default".
        bgcolor (Union[Color, str], optional): Color of bar background. Defaults to "default". | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/box.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Defines characters to render boxes.

    ┌─┬┐ top
    │ ││ head
    ├─┼┤ head_row
    │ ││ mid
    ├─┼┤ row
    ├─┼┤ foot_row
    │ ││ foot
    └─┴┘ bottom

    Args:
        box (str): Characters making up box.
        ascii (bool, optional): True if this box uses ascii characters only. Default is False. | , pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/cells.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Get the number of cells required to display text.

    This method always caches, which may use up a lot of memory. It is recommended to use
    `cell_len` over this method.

    Args:
        text (str): Text to display.

    Returns:
        int: Get the number of cells required to display text. | , __future__, functools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/color.py` | ❓ UNKNOWN | 2025-11-09 19:12 | One of the 3 color system supported by terminals."""

    STANDARD = 1
    EIGHT_BIT = 2
    TRUECOLOR = 3
    WINDOWS = 4

    def __repr__(self) -> str:
        return f"ColorSystem.{self.name}"

    def __str__(self) -> str:
        return repr(self)


class ColorType(IntEnum): | , colorsys, enum, functools, re, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/color_triplet.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The red, green, and blue components of a color."""

    red: int | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/columns.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Display renderables in neat columns.

    Args:
        renderables (Iterable[RenderableType]): Any number of Rich renderables (including str).
        width (int, optional): The desired width of the columns, or None to auto detect. Defaults to None.
        padding (PaddingDimensions, optional): Optional padding around cells. Defaults to (0, 1).
        expand (bool, optional): Expand columns to full width. Defaults to False.
        equal (bool, optional): Arrange in to equal sized columns. Defaults to False.
        column_first (bool, optional): Align items from top to bottom (rather than left to right). Defaults to False.
        right_to_left (bool, optional): Start column from right hand side. Defaults to False.
        align (str, optional): Align value ("left", "right", or "center") or None for default. Defaults to None.
        title (TextType, optional): Optional title for Columns. | , collections, itertools, operator, os, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/console.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Size of the terminal."""

    width: int | , abc, dataclasses, datetime, functools, getpass, html, inspect, itertools, math, os, pip, sys, threading, time, types, typing, zlib |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/constrain.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Constrain the width of a renderable to a given number of characters.

    Args:
        renderable (RenderableType): A renderable object.
        width (int, optional): The maximum width (in characters) to render. Defaults to 80. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/containers.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A list subclass which renders its contents to the console."""

    def __init__(
        self, renderables: Optional[Iterable["RenderableType"]] = None
    ) -> None:
        self._renderables: List["RenderableType"] = (
            list(renderables) if renderables is not None else []
        )

    def __rich_console__(
        self, console: "Console", options: "ConsoleOptions"
    ) -> "RenderResult": | , itertools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/control.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A renderable that inserts a control code (non printable but may move cursor).

    Args:
        *codes (str): Positional arguments are either a :class:`~rich.segment.ControlType` enum or a
            tuple of ControlType and an integer parameter | , pip, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/default_styles.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , argparse, io, pip, typing | L55: "logging.level.debug": Style(color="green"), |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/diagnose.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Print a report to the terminal with debugging information"""
    console = Console()
    inspect(console)
    features = get_windows_console_features()
    inspect(features)

    env_names = (
        "CLICOLOR",
        "COLORTERM",
        "COLUMNS",
        "JPY_PARENT_PID",
        "JUPYTER_COLUMNS",
        "JUPYTER_LINES",
        "LINES",
        "NO_COLOR",
        "TERM_PROGRAM",
        "TERM",
        "TTY_COMPATIBLE",
        "TTY_INTERACTIVE",
        "VSCODE_VERBOSE_LOGGING",
    )
    env = {name: os.getenv(name) for name in env_names}
    console.print(Panel.fit((Pretty(env)), title="[b]Environment Variables"))

    console.print(f'platform="{platform.system()}"')


if __name__ == "__main__":  # pragma: no cover
    report() | os, pip, platform | L11: """Print a report to the terminal with debugging information""" |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/emoji.py` | ❓ UNKNOWN | 2025-11-09 19:12 | No emoji by that name."""


class Emoji(JupyterMixin):
    __slots__ = ["name", "style", "_char", "variant"]

    VARIANTS = {"text": "\uFE0E", "emoji": "\uFE0F"}

    def __init__(
        self,
        name: str,
        style: Union[str, Style] = "none",
        variant: Optional[EmojiVariant] = None,
    ) -> None: | , pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/errors.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An error in console operation."""


class StyleError(Exception): |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/file_proxy.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Wraps a file (e.g. sys.stdout) and redirects writes to a console."""

    def __init__(self, console: "Console", file: IO[str]) -> None:
        self.__console = console
        self.__file = file
        self.__buffer: List[str] = []
        self.__ansi_decoder = AnsiDecoder()

    @property
    def rich_proxied_file(self) -> IO[str]: | , io, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/filesize.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Functions for reporting filesizes. Borrowed from https://github.com/PyFilesystem/pyfilesystem2

The functions declared in this module should cover the different
use cases needed to generate a string representation of a file size
using several different units. Since there are many standards regarding
file size units, three different functions have been implemented.

See Also:
    * `Wikipedia: Binary prefix <https://en.wikipedia.org/wiki/Binary_prefix>`_ | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/highlighter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Combine a number of regexes in to a single regex.

    Returns:
        str: New regex with all regexes ORed together. | , abc, json, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/json.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A renderable which pretty prints JSON.

    Args:
        json (str): JSON encoded data.
        indent (Union[None, int, str], optional): Number of characters to indent by. Defaults to 2.
        highlight (bool, optional): Enable highlighting. Defaults to True.
        skip_keys (bool, optional): Skip keys not of a basic type. Defaults to False.
        ensure_ascii (bool, optional): Escape all non-ascii characters. Defaults to False.
        check_circular (bool, optional): Check for circular references. Defaults to True.
        allow_nan (bool, optional): Allow NaN and Infinity values. Defaults to True.
        default (Callable, optional): A callable that converts values that can not be encoded
            in to something that can be JSON encoded. Defaults to None.
        sort_keys (bool, optional): Sort dictionary keys. Defaults to False. | , argparse, json, pathlib, pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/jupyter.py` | ❓ UNKNOWN | 2025-11-09 19:12 | class JupyterRenderable: | , IPython, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/layout.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An individual layout render."""

    region: Region
    render: List[List[Segment]]


RegionMap = Dict["Layout", Region]
RenderMap = Dict["Layout", LayoutRender]


class LayoutError(Exception): | , abc, itertools, operator, pip, threading, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/live.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A thread that calls refresh() at regular intervals."""

    def __init__(self, live: "Live", refresh_per_second: float) -> None:
        self.live = live
        self.refresh_per_second = refresh_per_second
        self.done = Event()
        super().__init__(daemon=True)

    def stop(self) -> None:
        self.done.set()

    def run(self) -> None:
        while not self.done.wait(1 / self.refresh_per_second):
            with self.live._lock:
                if not self.done.is_set():
                    self.live.refresh()


class Live(JupyterMixin, RenderHook): | , __future__, IPython, ipywidgets, itertools, random, sys, threading, time, types, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/live_render.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Creates a renderable that may be updated.

    Args:
        renderable (RenderableType): Any renderable object.
        style (StyleType, optional): An optional style to apply to the renderable. Defaults to "". | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/logging.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A logging handler that renders output with Rich. The time / level / message and file are displayed in columns.
    The level is color coded, and the message is syntax highlighted.

    Note:
        Be careful when enabling console markup in log messages if you have configured logging for libraries not
        under your control. If a dependency writes messages containing square brackets, it may not produce the intended output.

    Args:
        level (Union[int, str], optional): Log level. Defaults to logging.NOTSET.
        console (:class:`~rich.console.Console`, optional): Optional console instance to write logs.
            Default will use a global console instance writing to stdout.
        show_time (bool, optional): Show a column for the time. Defaults to True.
        omit_repeated_times (bool, optional): Omit repetition of the same time. Defaults to True.
        show_level (bool, optional): Show a column for the level. Defaults to True.
        show_path (bool, optional): Show the path to the original log call. Defaults to True.
        enable_link_path (bool, optional): Enable terminal link of path column to file. Defaults to True.
        highlighter (Highlighter, optional): Highlighter to style log messages, or None to use ReprHighlighter. Defaults to None.
        markup (bool, optional): Enable console markup in log messages. Defaults to False.
        rich_tracebacks (bool, optional): Enable rich tracebacks with syntax highlighting and formatting. Defaults to False.
        tracebacks_width (Optional[int], optional): Number of characters used to render tracebacks, or None for full width. Defaults to None.
        tracebacks_code_width (int, optional): Number of code characters used to render tracebacks, or None for full width. Defaults to 88.
        tracebacks_extra_lines (int, optional): Additional lines of code to render tracebacks, or None for full width. Defaults to None.
        tracebacks_theme (str, optional): Override pygments theme used in traceback.
        tracebacks_word_wrap (bool, optional): Enable word wrapping of long tracebacks lines. Defaults to True.
        tracebacks_show_locals (bool, optional): Enable display of locals in tracebacks. Defaults to False.
        tracebacks_suppress (Sequence[Union[str, ModuleType]]): Optional sequence of modules or paths to exclude from traceback.
        tracebacks_max_frames (int, optional): Optional maximum number of frames returned by traceback.
        locals_max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to 10.
        locals_max_string (int, optional): Maximum length of string before truncating, or None to disable. Defaults to 80.
        log_time_format (Union[str, TimeFormatterCallable], optional): If ``log_time`` is enabled, either string for strftime or callable that formats the time. Defaults to "[%x %X] ".
        keywords (List[str], optional): List of words to highlight instead of ``RichHandler.KEYWORDS``. | , datetime, logging, pathlib, pip, time, types, typing | L265: log.debug(
L275: log.debug(
L287: log.debug("in divide") |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/markup.py` | ❓ UNKNOWN | 2025-11-09 19:12 | ((\\*)\[([a-z#/@][^[]*?)])""",
    re.VERBOSE,
)

RE_HANDLER = re.compile(r"^([\w.]*?)(\(.*?\))?$")


class Tag(NamedTuple): | , ast, operator, pip, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/measure.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Stores the minimum and maximum widths (in characters) required to render an object."""

    minimum: int | , operator, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/padding.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Draw space around content.

    Example:
        >>> print(Padding("Hello", (2, 4), style="on blue"))

    Args:
        renderable (RenderableType): String or other renderable.
        pad (Union[int, Tuple[int]]): Padding for top, right, bottom, and left borders.
            May be specified with 1, 2, or 4 integers (CSS style).
        style (Union[str, Style], optional): Style for padding characters. Defaults to "none".
        expand (bool, optional): Expand padding to fit available width. Defaults to True. | , pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/pager.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base class for a pager."""

    @abstractmethod
    def show(self, content: str) -> None: | , abc, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/palette.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A palette of available colors."""

    def __init__(self, colors: Sequence[Tuple[int, int, int]]):
        self._colors = colors

    def __getitem__(self, number: int) -> ColorTriplet:
        return ColorTriplet(*self._colors[number])

    def __rich__(self) -> "Table":
        from pip._vendor.rich.color import Color
        from pip._vendor.rich.style import Style
        from pip._vendor.rich.text import Text
        from pip._vendor.rich.table import Table

        table = Table(
            "index",
            "RGB",
            "Color",
            title="Palette",
            caption=f"{len(self._colors)} colors",
            highlight=True,
            caption_justify="right",
        )
        for index, color in enumerate(self._colors):
            table.add_row(
                str(index),
                repr(color),
                Text(" " * 16, style=Style(bgcolor=Color.from_rgb(*color))),
            )
        return table

    # This is somewhat inefficient and needs caching
    @lru_cache(maxsize=1024)
    def match(self, color: Tuple[int, int, int]) -> int: | , colorsys, functools, math, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/panel.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A console renderable that draws a border around its contents.

    Example:
        >>> console.print(Panel("Hello, World!"))

    Args:
        renderable (RenderableType): A console renderable object.
        box (Box): A Box instance that defines the look of the border (see :ref:`appendix_box`. Defaults to box.ROUNDED.
        title (Optional[TextType], optional): Optional title displayed in panel header. Defaults to None.
        title_align (AlignMethod, optional): Alignment of title. Defaults to "center".
        subtitle (Optional[TextType], optional): Optional subtitle displayed in panel footer. Defaults to None.
        subtitle_align (AlignMethod, optional): Alignment of subtitle. Defaults to "center".
        safe_box (bool, optional): Disable box characters that don't display on windows legacy terminal with *raster* fonts. Defaults to True.
        expand (bool, optional): If True the panel will stretch to fill the console width, otherwise it will be sized to fit the contents. Defaults to True.
        style (str, optional): The style of the panel (border and contents). Defaults to "none".
        border_style (str, optional): The style of the border. Defaults to "none".
        width (Optional[int], optional): Optional width of panel. Defaults to None to auto-detect.
        height (Optional[int], optional): Optional height of panel. Defaults to None to auto-detect.
        padding (Optional[PaddingDimensions]): Optional padding around renderable. Defaults to 0.
        highlight (bool, optional): Enable automatic highlighting of panel title (if str). Defaults to False. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/pretty.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Check if an object was created with attrs module."""
    return _has_attrs and _attr_module.has(type(obj))


def _get_attr_fields(obj: Any) -> Sequence["_attr_module.Attribute[Any]"]: | , array, attr, builtins, collections, dataclasses, inspect, IPython, itertools, os, pip, reprlib, sys, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/progress.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A thread to periodically update progress."""

    def __init__(self, progress: "Progress", task_id: "TaskID", update_period: float):
        self.progress = progress
        self.task_id = task_id
        self.update_period = update_period
        self.done = Event()

        self.completed = 0
        super().__init__(daemon=True)

    def run(self) -> None:
        task_id = self.task_id
        advance = self.progress.advance
        update_period = self.update_period
        last_completed = 0
        wait = self.done.wait
        while not wait(update_period) and self.progress.live.is_started:
            completed = self.completed
            if last_completed != completed:
                advance(task_id, completed - last_completed)
                last_completed = completed

        self.progress.update(self.task_id, completed=self.completed, refresh=True)

    def __enter__(self) -> "_TrackThread":
        self.start()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self.done.set()
        self.join()


def track(
    sequence: Iterable[ProgressType],
    description: str = "Working...",
    total: Optional[float] = None,
    completed: int = 0,
    auto_refresh: bool = True,
    console: Optional[Console] = None,
    transient: bool = False,
    get_time: Optional[Callable[[], float]] = None,
    refresh_per_second: float = 10,
    style: StyleType = "bar.back",
    complete_style: StyleType = "bar.complete",
    finished_style: StyleType = "bar.finished",
    pulse_style: StyleType = "bar.pulse",
    update_period: float = 0.1,
    disable: bool = False,
    show_speed: bool = True,
) -> Iterable[ProgressType]: | , __future__, abc, collections, dataclasses, datetime, io, math, mmap, operator, os, threading, types, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/progress_bar.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Renders a (progress) bar. Used by rich.progress.

    Args:
        total (float, optional): Number of steps in the bar. Defaults to 100. Set to None to render a pulsing animation.
        completed (float, optional): Number of steps completed. Defaults to 0.
        width (int, optional): Width of the bar, or ``None`` for maximum width. Defaults to None.
        pulse (bool, optional): Enable pulse effect. Defaults to False. Will pulse if a None total was passed.
        style (StyleType, optional): Style for the bar background. Defaults to "bar.back".
        complete_style (StyleType, optional): Style for the completed bar. Defaults to "bar.complete".
        finished_style (StyleType, optional): Style for a finished bar. Defaults to "bar.finished".
        pulse_style (StyleType, optional): Style for pulsing bars. Defaults to "bar.pulse".
        animation_time (Optional[float], optional): Time in seconds to use for animation, or None to use system time. | , functools, math, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/prompt.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Exception base class for prompt related errors."""


class InvalidResponse(PromptError): | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/protocol.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Check if an object may be rendered by Rich."""
    return (
        isinstance(check_object, str)
        or hasattr(check_object, "__rich__")
        or hasattr(check_object, "__rich_console__")
    )


def rich_cast(renderable: object) -> "RenderableType": | inspect, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/region.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Defines a rectangular region of the screen."""

    x: int
    y: int
    width: int
    height: int | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/repr.py` | ❓ UNKNOWN | 2025-11-09 19:12 | An error occurred when attempting to build a repr."""


@overload
def auto(cls: Optional[Type[T]]) -> Type[T]:
    ...


@overload
def auto(*, angular: bool = False) -> Callable[[Type[T]], Type[T]]:
    ...


def auto(
    cls: Optional[Type[T]] = None, *, angular: Optional[bool] = None
) -> Union[Type[T], Callable[[Type[T]], Type[T]]]: | functools, inspect, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/rule.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A console renderable to draw a horizontal rule (line).

    Args:
        title (Union[str, Text], optional): Text to render in the rule. Defaults to "".
        characters (str, optional): Character(s) used to draw the line. Defaults to "─".
        style (StyleType, optional): Style of Rule. Defaults to "rule.line".
        end (str, optional): Character at end of Rule. defaults to "\\\\n"
        align (str, optional): How to align the title, one of "left", "center", or "right". Defaults to "center". | , pip, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/scope.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Render python variables in a given scope.

    Args:
        scope (Mapping): A mapping containing variable names and values.
        title (str, optional): Optional title. Defaults to None.
        sort_keys (bool, optional): Enable sorting of items. Defaults to True.
        indent_guides (bool, optional): Enable indentation guides. Defaults to False.
        max_length (int, optional): Maximum length of containers before abbreviating, or None for no abbreviation.
            Defaults to None.
        max_string (int, optional): Maximum length of string before truncating, or None to disable. Defaults to None.

    Returns:
        ConsoleRenderable: A renderable object. | , collections, pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/screen.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A renderable that fills the terminal screen and crops excess.

    Args:
        renderable (RenderableType): Child renderable.
        style (StyleType, optional): Optional background style. Defaults to None. | , pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/segment.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Non-printable control codes which typically translate to ANSI codes."""

    BELL = 1
    CARRIAGE_RETURN = 2
    HOME = 3
    CLEAR = 4
    SHOW_CURSOR = 5
    HIDE_CURSOR = 6
    ENABLE_ALT_SCREEN = 7
    DISABLE_ALT_SCREEN = 8
    CURSOR_UP = 9
    CURSOR_DOWN = 10
    CURSOR_FORWARD = 11
    CURSOR_BACKWARD = 12
    CURSOR_MOVE_TO_COLUMN = 13
    CURSOR_MOVE_TO = 14
    ERASE_IN_LINE = 15
    SET_WINDOW_TITLE = 16


ControlCode = Union[
    Tuple[ControlType],
    Tuple[ControlType, Union[int, str]],
    Tuple[ControlType, int, int],
]


@rich_repr()
class Segment(NamedTuple): | , enum, functools, itertools, logging, operator, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/spinner.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A spinner animation.

    Args:
        name (str): Name of spinner (run python -m rich.spinner).
        text (RenderableType, optional): A renderable to display at the right of the spinner (str or Text typically). Defaults to "".
        style (StyleType, optional): Style for spinner animation. Defaults to None.
        speed (float, optional): Speed factor for animation. Defaults to 1.0.

    Raises:
        KeyError: If name isn't one of the supported spinner animations. | , time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/status.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Displays a status indicator with a 'spinner' animation.

    Args:
        status (RenderableType): A status renderable (str or Text typically).
        console (Console, optional): Console instance to use, or None for global console. Defaults to None.
        spinner (str, optional): Name of spinner animation (see python -m rich.spinner). Defaults to "dots".
        spinner_style (StyleType, optional): Style of spinner. Defaults to "status.spinner".
        speed (float, optional): Speed factor for spinner animation. Defaults to 1.0.
        refresh_per_second (float, optional): Number of refreshes per second. Defaults to 12.5. | , time, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/style.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A descriptor to get/set a style attribute bit."""

    __slots__ = ["bit"]

    def __init__(self, bit_no: int) -> None:
        self.bit = 1 << bit_no

    def __get__(self, obj: "Style", objtype: Type["Style"]) -> Optional[bool]:
        if obj._set_attributes & self.bit:
            return obj._attributes & self.bit != 0
        return None


@rich_repr
class Style: | , functools, operator, pickle, random, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/styled.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Apply a style to a renderable.

    Args:
        renderable (RenderableType): Any renderable.
        style (StyleType): A style to apply across the entire renderable. | , pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/syntax.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base class for a syntax theme."""

    @abstractmethod
    def get_style_for_token(self, token_type: TokenType) -> Style: | , __future__, abc, os, pathlib, pip, re, sys, textwrap, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/table.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Defines a column within a ~Table.

    Args:
        title (Union[str, Text], optional): The title of the table rendered at the top. Defaults to None.
        caption (Union[str, Text], optional): The table caption rendered below. Defaults to None.
        width (int, optional): The width in characters of the table, or ``None`` to automatically fit. Defaults to None.
        min_width (Optional[int], optional): The minimum width of the table, or ``None`` for no minimum. Defaults to None.
        box (box.Box, optional): One of the constants in box.py used to draw the edges (see :ref:`appendix_box`), or ``None`` for no box lines. Defaults to box.HEAVY_HEAD.
        safe_box (Optional[bool], optional): Disable box characters that don't display on windows legacy terminal with *raster* fonts. Defaults to True.
        padding (PaddingDimensions, optional): Padding for cells (top, right, bottom, left). Defaults to (0, 1).
        collapse_padding (bool, optional): Enable collapsing of padding around cells. Defaults to False.
        pad_edge (bool, optional): Enable padding of edge cells. Defaults to True.
        expand (bool, optional): Expand the table to fit the available space if ``True``, otherwise the table width will be auto-calculated. Defaults to False.
        show_header (bool, optional): Show a header row. Defaults to True.
        show_footer (bool, optional): Show a footer row. Defaults to False.
        show_edge (bool, optional): Draw a box around the outside of the table. Defaults to True.
        show_lines (bool, optional): Draw lines between every row. Defaults to False.
        leading (int, optional): Number of blank lines between rows (precludes ``show_lines``). Defaults to 0.
        style (Union[str, Style], optional): Default style for the table. Defaults to "none".
        row_styles (List[Union, str], optional): Optional list of row styles, if more than one style is given then the styles will alternate. Defaults to None.
        header_style (Union[str, Style], optional): Style of the header. Defaults to "table.header".
        footer_style (Union[str, Style], optional): Style of the footer. Defaults to "table.footer".
        border_style (Union[str, Style], optional): Style of the border. Defaults to None.
        title_style (Union[str, Style], optional): Style of the title. Defaults to None.
        caption_style (Union[str, Style], optional): Style of the caption. Defaults to None.
        title_justify (str, optional): Justify method for title. Defaults to "center".
        caption_justify (str, optional): Justify method for caption. Defaults to "center".
        highlight (bool, optional): Highlight cell contents (if str). Defaults to False. | , dataclasses, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/terminal_theme.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A color theme used when exporting console content.

    Args:
        background (Tuple[int, int, int]): The background color.
        foreground (Tuple[int, int, int]): The foreground (text) color.
        normal (List[Tuple[int, int, int]]): A list of 8 normal intensity colors.
        bright (List[Tuple[int, int, int]], optional): A list of 8 bright colors, or None
            to repeat normal intensity. Defaults to None. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/text.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A plain string or a :class:`Text` instance."""

GetStyleCallable = Callable[[str], Optional[StyleType]]


class Span(NamedTuple): | , functools, math, operator, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/theme.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A container for style information, used by :class:`~rich.console.Console`.

    Args:
        styles (Dict[str, Style], optional): A mapping of style names on to styles. Defaults to None for a theme with no styles.
        inherit (bool, optional): Inherit default styles. Defaults to True. | , configparser, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/themes.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/traceback.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Yield start and end positions per line.

    Args:
        start: Start position.
        end: End position.

    Returns:
        Iterable of (LINE, COLUMN1, COLUMN2). | , dataclasses, inspect, itertools, linecache, os, pip, sys, traceback, types, typing | L193: # replace _showtraceback instead of showtraceback to allow ipython features such as debugging to work |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/rich/tree.py` | ❓ UNKNOWN | 2025-11-09 19:12 | A renderable for a tree structure.

    Attributes:
        ASCII_GUIDES (GuideType): Guide lines used when Console.ascii_only is True.
        TREE_GUIDES (List[GuideType, GuideType, GuideType]): Default guide lines.

    Args:
        label (RenderableType): The renderable or str for the tree label.
        style (StyleType, optional): Style of this tree. Defaults to "tree".
        guide_style (StyleType, optional): Style of the guide lines. Defaults to "tree.line".
        expanded (bool, optional): Also display children. Defaults to True.
        highlight (bool, optional): Highlight renderable (if str). Defaults to False.
        hide_root (bool, optional): Hide the root node. Defaults to False. | , pip, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/tomli/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/tomli/_parser.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Sentinel to be used as default arg during deprecation
    period of TOMLDecodeError's free-form arguments. | , __future__, collections, sys, types, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/tomli/_re.py` | ❓ UNKNOWN | 2025-11-09 19:12 | 0
(?:
    x[0-9A-Fa-f](?:_?[0-9A-Fa-f])*   # hex
    \\|
    b[01](?:_?[01])*                 # bin
    \\|
    o[0-7](?:_?[0-7])*               # oct
)
\\|
[+-]?(?:0\\|[1-9](?:_?[0-9])*)         # dec, integer part
(?P<floatpart>
    (?:\.[0-9](?:_?[0-9])*)?         # optional fractional part
    (?:[eE][+-]?[0-9](?:_?[0-9])*)?  # optional exponent part
) | , __future__, datetime, functools, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/tomli/_types.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/tomli_w/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | pip |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/tomli_w/_writer.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Decides if an object behaves as an array of tables (i.e. a nonempty list
    of dicts). | __future__, collections, datetime, decimal, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/truststore/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Verify certificates using native system trust stores"""

import sys as _sys

if _sys.version_info < (3, 10):
    raise ImportError("truststore requires Python 3.10 or later")

# Detect Python runtimes which don't implement SSLObject.get_unverified_chain() API
# This API only became public in Python 3.13 but was available in CPython and PyPy since 3.10.
if _sys.version_info < (3, 13) and _sys.implementation.name not in ("cpython", "pypy"):
    try:
        import ssl as _ssl
    except ImportError:
        raise ImportError("truststore requires the 'ssl' module")
    else:
        _sslmem = _ssl.MemoryBIO()
        _sslobj = _ssl.create_default_context().wrap_bio(
            _sslmem,
            _sslmem,
        )
        try:
            while not hasattr(_sslobj, "get_unverified_chain"):
                _sslobj = _sslobj._sslobj  # type: ignore[attr-defined]
        except AttributeError:
            raise ImportError(
                "truststore requires peer certificate chain APIs to be available"
            ) from None

        del _ssl, _sslobj, _sslmem  # noqa: F821

from ._api import SSLContext, extract_from_ssl, inject_into_ssl  # noqa: E402

del _api, _sys  # type: ignore[name-defined] # noqa: F821

__all__ = ["SSLContext", "inject_into_ssl", "extract_from_ssl"]
__version__ = "0.10.4" | , ssl, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/truststore/_api.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Injects the :class:`truststore.SSLContext` into the ``ssl``
    module by replacing :class:`ssl.SSLContext`. | , _ssl, contextlib, os, pip, platform, socket, ssl, sys, threading, typing, typing_extensions | L82: # Dirty hack to get around isinstance() checks |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/truststore/_macos.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Loads a CDLL by name, falling back to known path on 10.16+"""
    try:
        # Big Sur is technically 11 but we use 10.16 due to the Big Sur
        # beta being labeled as 10.16.
        path: str \\| None
        if _mac_version_info >= (10, 16):
            path = macos10_16_path
        else:
            path = find_library(name)
        if not path:
            raise OSError  # Caught and reraised as 'ImportError'
        return CDLL(path, use_errno=True)
    except OSError:
        raise ImportError(f"The library {name} failed to load") from None


Security = _load_cdll(
    "Security", "/System/Library/Frameworks/Security.framework/Security"
)
CoreFoundation = _load_cdll(
    "CoreFoundation",
    "/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation",
)

Boolean = c_bool
CFIndex = c_long
CFStringEncoding = c_uint32
CFData = c_void_p
CFString = c_void_p
CFArray = c_void_p
CFMutableArray = c_void_p
CFError = c_void_p
CFType = c_void_p
CFTypeID = c_ulong
CFTypeRef = POINTER(CFType)
CFAllocatorRef = c_void_p

OSStatus = c_int32

CFErrorRef = POINTER(CFError)
CFDataRef = POINTER(CFData)
CFStringRef = POINTER(CFString)
CFArrayRef = POINTER(CFArray)
CFMutableArrayRef = POINTER(CFMutableArray)
CFArrayCallBacks = c_void_p
CFOptionFlags = c_uint32

SecCertificateRef = POINTER(c_void_p)
SecPolicyRef = POINTER(c_void_p)
SecTrustRef = POINTER(c_void_p)
SecTrustResultType = c_uint32
SecTrustOptionFlags = c_uint32

try:
    Security.SecCertificateCreateWithData.argtypes = [CFAllocatorRef, CFDataRef]
    Security.SecCertificateCreateWithData.restype = SecCertificateRef

    Security.SecCertificateCopyData.argtypes = [SecCertificateRef]
    Security.SecCertificateCopyData.restype = CFDataRef

    Security.SecCopyErrorMessageString.argtypes = [OSStatus, c_void_p]
    Security.SecCopyErrorMessageString.restype = CFStringRef

    Security.SecTrustSetAnchorCertificates.argtypes = [SecTrustRef, CFArrayRef]
    Security.SecTrustSetAnchorCertificates.restype = OSStatus

    Security.SecTrustSetAnchorCertificatesOnly.argtypes = [SecTrustRef, Boolean]
    Security.SecTrustSetAnchorCertificatesOnly.restype = OSStatus

    Security.SecPolicyCreateRevocation.argtypes = [CFOptionFlags]
    Security.SecPolicyCreateRevocation.restype = SecPolicyRef

    Security.SecPolicyCreateSSL.argtypes = [Boolean, CFStringRef]
    Security.SecPolicyCreateSSL.restype = SecPolicyRef

    Security.SecTrustCreateWithCertificates.argtypes = [
        CFTypeRef,
        CFTypeRef,
        POINTER(SecTrustRef),
    ]
    Security.SecTrustCreateWithCertificates.restype = OSStatus

    Security.SecTrustGetTrustResult.argtypes = [
        SecTrustRef,
        POINTER(SecTrustResultType),
    ]
    Security.SecTrustGetTrustResult.restype = OSStatus

    Security.SecTrustEvaluate.argtypes = [
        SecTrustRef,
        POINTER(SecTrustResultType),
    ]
    Security.SecTrustEvaluate.restype = OSStatus

    Security.SecTrustRef = SecTrustRef  # type: ignore[attr-defined]
    Security.SecTrustResultType = SecTrustResultType  # type: ignore[attr-defined]
    Security.OSStatus = OSStatus  # type: ignore[attr-defined]

    kSecRevocationUseAnyAvailableMethod = 3
    kSecRevocationRequirePositiveResponse = 8

    CoreFoundation.CFRelease.argtypes = [CFTypeRef]
    CoreFoundation.CFRelease.restype = None

    CoreFoundation.CFGetTypeID.argtypes = [CFTypeRef]
    CoreFoundation.CFGetTypeID.restype = CFTypeID

    CoreFoundation.CFStringCreateWithCString.argtypes = [
        CFAllocatorRef,
        c_char_p,
        CFStringEncoding,
    ]
    CoreFoundation.CFStringCreateWithCString.restype = CFStringRef

    CoreFoundation.CFStringGetCStringPtr.argtypes = [CFStringRef, CFStringEncoding]
    CoreFoundation.CFStringGetCStringPtr.restype = c_char_p

    CoreFoundation.CFStringGetCString.argtypes = [
        CFStringRef,
        c_char_p,
        CFIndex,
        CFStringEncoding,
    ]
    CoreFoundation.CFStringGetCString.restype = c_bool

    CoreFoundation.CFDataCreate.argtypes = [CFAllocatorRef, c_char_p, CFIndex]
    CoreFoundation.CFDataCreate.restype = CFDataRef

    CoreFoundation.CFDataGetLength.argtypes = [CFDataRef]
    CoreFoundation.CFDataGetLength.restype = CFIndex

    CoreFoundation.CFDataGetBytePtr.argtypes = [CFDataRef]
    CoreFoundation.CFDataGetBytePtr.restype = c_void_p

    CoreFoundation.CFArrayCreate.argtypes = [
        CFAllocatorRef,
        POINTER(CFTypeRef),
        CFIndex,
        CFArrayCallBacks,
    ]
    CoreFoundation.CFArrayCreate.restype = CFArrayRef

    CoreFoundation.CFArrayCreateMutable.argtypes = [
        CFAllocatorRef,
        CFIndex,
        CFArrayCallBacks,
    ]
    CoreFoundation.CFArrayCreateMutable.restype = CFMutableArrayRef

    CoreFoundation.CFArrayAppendValue.argtypes = [CFMutableArrayRef, c_void_p]
    CoreFoundation.CFArrayAppendValue.restype = None

    CoreFoundation.CFArrayGetCount.argtypes = [CFArrayRef]
    CoreFoundation.CFArrayGetCount.restype = CFIndex

    CoreFoundation.CFArrayGetValueAtIndex.argtypes = [CFArrayRef, CFIndex]
    CoreFoundation.CFArrayGetValueAtIndex.restype = c_void_p

    CoreFoundation.CFErrorGetCode.argtypes = [CFErrorRef]
    CoreFoundation.CFErrorGetCode.restype = CFIndex

    CoreFoundation.CFErrorCopyDescription.argtypes = [CFErrorRef]
    CoreFoundation.CFErrorCopyDescription.restype = CFStringRef

    CoreFoundation.kCFAllocatorDefault = CFAllocatorRef.in_dll(  # type: ignore[attr-defined]
        CoreFoundation, "kCFAllocatorDefault"
    )
    CoreFoundation.kCFTypeArrayCallBacks = c_void_p.in_dll(  # type: ignore[attr-defined]
        CoreFoundation, "kCFTypeArrayCallBacks"
    )

    CoreFoundation.CFTypeRef = CFTypeRef  # type: ignore[attr-defined]
    CoreFoundation.CFArrayRef = CFArrayRef  # type: ignore[attr-defined]
    CoreFoundation.CFStringRef = CFStringRef  # type: ignore[attr-defined]
    CoreFoundation.CFErrorRef = CFErrorRef  # type: ignore[attr-defined]

except AttributeError as e:
    raise ImportError(f"Error initializing ctypes: {e}") from None

# SecTrustEvaluateWithError is macOS 10.14+
if _is_macos_version_10_14_or_later:
    try:
        Security.SecTrustEvaluateWithError.argtypes = [
            SecTrustRef,
            POINTER(CFErrorRef),
        ]
        Security.SecTrustEvaluateWithError.restype = c_bool
    except AttributeError as e:
        raise ImportError(f"Error initializing ctypes: {e}") from None


def _handle_osstatus(result: OSStatus, _: typing.Any, args: typing.Any) -> typing.Any: | , contextlib, ctypes, platform, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/truststore/_openssl.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Check whether capath exists and contains certs in the expected format."""
    if not os.path.isdir(capath):
        return False
    for name in os.listdir(capath):
        if _HASHED_CERT_FILENAME_RE.match(name):
            return True
    return False


def _verify_peercerts_impl(
    ssl_context: ssl.SSLContext,
    cert_chain: list[bytes],
    server_hostname: str \\| None = None,
) -> None:
    # This is a no-op because we've enabled SSLContext's built-in
    # verification via verify_mode=CERT_REQUIRED, and don't need to repeat it.
    pass | contextlib, os, re, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/truststore/_ssl_constants.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | ssl, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/truststore/_windows.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , contextlib, ctypes, ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Python HTTP library with thread-safe connection pooling, file post support, user friendly, and more | , __future__, logging, urllib3_secure_extra, warnings | L63: def add_stderr_logger(level=logging.DEBUG):
L66: debugging.
L77: logger.debug("Added a stderr logging handler to logger: %s", __name__) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/_collections.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Provides a thread-safe dict-like container which maintains up to
    ``maxsize`` keys while throwing away the least-recently-used keys beyond
    ``maxsize``.

    :param maxsize:
        Maximum number of recent elements to retain.

    :param dispose_func:
        Every time an item is evicted from the container,
        ``dispose_func(value)`` is called.  Callback which will get called | , __future__, collections, threading |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/_version.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/connection.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Based on :class:`http.client.HTTPConnection` but provides an extra constructor
    backwards-compatibility layer between older and newer Pythons.

    Additional keyword parameters are used to configure attributes of the connection.
    Accepted parameters include:

    - ``strict``: See the documentation on :class:`urllib3.connectionpool.HTTPConnectionPool`
    - ``source_address``: Set the source address for the current connection.
    - ``socket_options``: Set specific options on the underlying socket. If not specified, then
      defaults are loaded from ``HTTPConnection.default_socket_options`` which includes disabling
      Nagle's algorithm (sets TCP_NODELAY to 1) unless the connection is behind a proxy.

      For example, if you wish to enable TCP Keep Alive in addition to the defaults,
      you might pass:

      .. code-block:: python

         HTTPConnection.default_socket_options + [
             (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
         ]

      Or you may want to disable the defaults by passing an empty list (e.g., ``[]``). | , __future__, datetime, logging, os, re, socket, ssl, warnings | L199: # TODO: Fix tunnel so it doesn't depend on self.sock state. |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/connectionpool.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base class for all connection pools, such as
    :class:`.HTTPConnectionPool` and :class:`.HTTPSConnectionPool`.

    .. note::
       ConnectionPool.urlopen() does not normalize or percent-encode target URIs
       which is useful if your target server doesn't support percent-encoded
       target URIs. | , __future__, errno, logging, re, socket, sys, warnings, weakref | L217: # These are mostly for testing and debugging purposes.
L246: log.debug(
L291: log.debug("Resetting dropped connection: %s", self.host)
L371: # http://bugs.python.org/issue10272
L427: # https://erickt.github.io/blog/2014/11/19/adventures-in-debugging-a-potential-osx-kernel-bug/
L467: # Otherwise it looks like a bug in the code.
L475: log.debug( |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/_appengine_environ.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This module provides means to detect the App Engine environment. | os |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/_securetransport/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/_securetransport/bindings.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This module uses ctypes to bind a whole bunch of functions and constants from
SecureTransport. The goal here is to provide the low-level API to
SecureTransport. These are essentially the C-level functions and constants, and
they're pretty gross to work with.

This code is a bastardised version of the code found in Will Bond's oscrypto
library. An enormous debt is owed to him for blazing this trail for us. For
that reason, this code should be considered to be covered both by urllib3's
license and by oscrypto's:

    Copyright (c) 2015-2016 Will Bond <will@wbond.net>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE. | , __future__, ctypes, platform |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/_securetransport/low_level.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Low-level helpers for the SecureTransport bindings.

These are Python functions that are not directly related to the high-level APIs
but are necessary to get them to work. They include a whole bunch of low-level
CoreFoundation messing about and memory management. The concerns in this module
are almost entirely about trying to avoid memory leaks and providing
appropriate and useful assistance to the higher-level code. | , base64, ctypes, itertools, os, re, ssl, struct, tempfile |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/appengine.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This module provides a pool manager that uses Google App Engine's
`URLFetch Service <https://cloud.google.com/appengine/docs/python/urlfetch>`_.

Example usage::

    from pip._vendor.urllib3 import PoolManager
    from pip._vendor.urllib3.contrib.appengine import AppEngineManager, is_appengine_sandbox

    if is_appengine_sandbox():
        # AppEngineManager uses AppEngine's URLFetch API behind the scenes
        http = AppEngineManager()
    else:
        # PoolManager uses a socket-level API behind the scenes
        http = PoolManager()

    r = http.request('GET', 'https://google.com/')

There are `limitations <https://cloud.google.com/appengine/docs/python/\
urlfetch/#Python_Quotas_and_limits>`_ to the URLFetch service and it may not be
the best choice for your application. There are three options for using
urllib3 on Google App Engine:

1. You can use :class:`AppEngineManager` with URLFetch. URLFetch is
   cost-effective in many circumstances as long as your usage is within the
   limitations.
2. You can use a normal :class:`~urllib3.PoolManager` by enabling sockets.
   Sockets also have `limitations and restrictions
   <https://cloud.google.com/appengine/docs/python/sockets/\
   #limitations-and-restrictions>`_ and have a lower free quota than URLFetch.
   To use sockets, be sure to specify the following in your ``app.yaml``::

        env_variables:
            GAE_USE_SOCKETS_HTTPLIB : 'true'

3. If you are using `App Engine Flexible
<https://cloud.google.com/appengine/docs/flexible/>`_, you can use the standard
:class:`PoolManager` without any configuration or special environment variables. | , __future__, google, io, logging, pip, warnings | L213: log.debug("Redirecting %s -> %s", url, redirect_location)
L230: log.debug("Retry: %s", url) |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/ntlmpool.py` | ❓ UNKNOWN | 2025-11-09 19:12 | NTLM authenticating pool, contributed by erikcederstran

Issue #10, see: http://code.google.com/p/urllib3/issues/detail?id=10 | , __future__, logging, ntlm, warnings | L52: log.debug(
L69: log.debug("Request headers: %s", headers)
L73: log.debug("Response status: %s %s", res.status, res.reason)
L74: log.debug("Response headers: %s", reshdr)
L75: log.debug("Response data: %s [...]", res.read(100))
L100: log.debug("Request headers: %s", headers)
L103: log.debug("Response status: %s %s", res.status, res.reason)
L104: log.debug("Response headers: %s", dict(res.headers))
L105: log.debug("Response data: %s [...]", res.read()[:100])
L112: log.debug("Connection established") |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/pyopenssl.py` | ❓ UNKNOWN | 2025-11-09 19:12 | TLS with SNI_-support for Python 2. Follow these instructions if you would
like to verify TLS certificates in Python 2. Note, the default libraries do
*not* do certificate checking; you need to do additional work to validate
certificates yourself.

This needs the following packages installed:

* `pyOpenSSL`_ (tested with 16.0.0)
* `cryptography`_ (minimum 1.3.4, from pyopenssl)
* `idna`_ (minimum 2.0, from cryptography)

However, pyopenssl depends on cryptography, which depends on idna, so while we
use all three directly here we end up having relatively few packages required.

You can install them with the following command:

.. code-block:: bash

    $ python -m pip install pyopenssl cryptography idna

To activate certificate checking, call
:func:`~urllib3.contrib.pyopenssl.inject_into_urllib3` from your Python code
before you begin making HTTP requests. This can be done in a ``sitecustomize``
module, or at any other time before your application begins using ``urllib3``,
like this:

.. code-block:: python

    try:
        import pip._vendor.urllib3.contrib.pyopenssl as pyopenssl
        pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

Now you can use :mod:`urllib3` as you normally would, and it will support SNI
when the required modules are installed.

Activating this module also has the positive side effect of disabling SSL/TLS
compression in Python 2 (see `CRIME attack`_).

.. _sni: https://en.wikipedia.org/wiki/Server_Name_Indication
.. _crime attack: https://en.wikipedia.org/wiki/CRIME_(security_exploit)
.. _pyopenssl: https://www.pyopenssl.org
.. _cryptography: https://cryptography.io
.. _idna: https://github.com/kjd/idna | , __future__, cryptography, io, logging, OpenSSL, pip, socket, ssl, sys, warnings | L371: # FIXME rethrow compatible exceptions should we ever use this |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/securetransport.py` | ❓ UNKNOWN | 2025-11-09 19:12 | SecureTranport support for urllib3 via ctypes.

This makes platform-native TLS available to urllib3 users on macOS without the
use of a compiler. This is an important feature because the Python Package
Index is moving to become a TLSv1.2-or-higher server, and the default OpenSSL
that ships with macOS is not capable of doing TLSv1.2. The only way to resolve
this is to give macOS users an alternative solution to the problem, and that
solution is to use SecureTransport.

We use ctypes here because this solution must not require a compiler. That's
because pip is not allowed to require a compiler either.

This is not intended to be a seriously long-term solution to this problem.
The hope is that PEP 543 will eventually solve this issue for us, at which
point we can retire this contrib module. But in the short term, we need to
solve the impending tire fire that is Python on Mac without this kind of
contrib module. So...here we are.

To use this module, simply import and inject it::

    import pip._vendor.urllib3.contrib.securetransport as securetransport
    securetransport.inject_into_urllib3()

Happy TLSing!

This code is a bastardised version of the code found in Will Bond's oscrypto
library. An enormous debt is owed to him for blazing this trail for us. For
that reason, this code should be considered to be covered both by urllib3's
license and by oscrypto's:

.. code-block::

    Copyright (c) 2015-2016 Will Bond <will@wbond.net>

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE. | , __future__, contextlib, ctypes, errno, os, pip, shutil, socket, ssl, struct, threading, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/contrib/socks.py` | ❓ UNKNOWN | 2025-11-09 19:12 | This module contains provisional support for SOCKS proxies from within
urllib3. This module supports SOCKS4, SOCKS4A (an extension of SOCKS4), and
SOCKS5. To enable its functionality, either install PySocks or install this
module with the ``socks`` extra.

The SOCKS implementation supports the full range of urllib3 features. It also
supports the following SOCKS features:

- SOCKS4A (``proxy_url='socks4a://...``)
- SOCKS4 (``proxy_url='socks4://...``)
- SOCKS5 with remote DNS (``proxy_url='socks5h://...``)
- SOCKS5 with local DNS (``proxy_url='socks5://...``)
- Usernames and passwords for the SOCKS proxy

.. note::
   It is recommended to use ``socks5h://`` or ``socks4a://`` schemes in
   your ``proxy_url`` to ensure that DNS resolution is done from the remote
   server instead of client-side when connecting to a domain name.

SOCKS4 supports IPv4 and domain names with the SOCKS4A extension. SOCKS5
supports IPv4, IPv6, and domain names.

When connecting to a SOCKS4 proxy the ``username`` portion of the ``proxy_url``
will be sent as the ``userid`` section of the SOCKS request:

.. code-block:: python

    proxy_url="socks4a://<userid>@proxy-host"

When connecting to a SOCKS5 proxy the ``username`` and ``password`` portion
of the ``proxy_url`` will be sent as the username/password to authenticate
with the proxy:

.. code-block:: python

    proxy_url="socks5h://<username>:<password>@proxy-host" | , __future__, socket, socks, ssl, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Base exception used by this module."""

    pass


class HTTPWarning(Warning): | , __future__ | L289: # TODO(t-8ch): Stop inheriting from AssertionError in v2.0. |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/fields.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Guess the "Content-Type" of a file.

    :param filename:
        The filename to guess the "Content-Type" of using :mod:`mimetypes`.
    :param default:
        If no "Content-Type" can be guessed, default to `default`. | , __future__, email, mimetypes, re |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/filepost.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Our embarrassingly-simple replacement for mimetools.choose_boundary. | , __future__, binascii, codecs, io, os |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/packages/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/packages/backports/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/packages/backports/makefile.py` | ❓ UNKNOWN | 2025-11-09 19:12 | backports.makefile
~~~~~~~~~~~~~~~~~~

Backports the Python 3 ``socket.makefile`` method for use with anything that
wants to create a "fake" socket object. | io, socket |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/packages/backports/weakref_finalize.py` | ❓ UNKNOWN | 2025-11-09 19:12 | backports.weakref_finalize
~~~~~~~~~~~~~~~~~~

Backports the Python 3 ``weakref.finalize`` method. | __future__, atexit, gc, itertools, sys, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/packages/six.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Utilities for writing code that runs on Python 2 and 3"""

from __future__ import absolute_import

import functools
import itertools
import operator
import sys
import types

__author__ = "Benjamin Peterson <benjamin@python.org>"
__version__ = "1.16.0"


# Useful for very coarse version differentiation.
PY2 = sys.version_info[0] == 2
PY3 = sys.version_info[0] == 3
PY34 = sys.version_info[0:2] >= (3, 4)

if PY3:
    string_types = (str,)
    integer_types = (int,)
    class_types = (type,)
    text_type = str
    binary_type = bytes

    MAXSIZE = sys.maxsize
else:
    string_types = (basestring,)
    integer_types = (int, long)
    class_types = (type, types.ClassType)
    text_type = unicode
    binary_type = str

    if sys.platform.startswith("java"):
        # Jython always uses 32 bits.
        MAXSIZE = int((1 << 31) - 1)
    else:
        # It's possible to have sizeof(long) != sizeof(Py_ssize_t).
        class X(object):
            def __len__(self):
                return 1 << 31

        try:
            len(X())
        except OverflowError:
            # 32-bit
            MAXSIZE = int((1 << 31) - 1)
        else:
            # 64-bit
            MAXSIZE = int((1 << 63) - 1)
        del X

if PY34:
    from importlib.util import spec_from_loader
else:
    spec_from_loader = None


def _add_doc(func, doc): | __future__, functools, importlib, itertools, operator, sys, types |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/poolmanager.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Create a pool key out of a request context dictionary.

    According to RFC 3986, both the scheme and host are case-insensitive.
    Therefore, this function normalizes both before constructing the pool
    key for an HTTPS request. If you wish to change this behaviour, provide
    alternate callables to ``key_fn_by_scheme``.

    :param key_class:
        The class to use when constructing the key. This should be a namedtuple
        with the ``scheme`` and ``host`` keys at a minimum.
    :type  key_class: namedtuple
    :param request_context:
        A dictionary-like object that contain the context for a request.
    :type  request_context: dict

    :return: A namedtuple that can be used as a connection pool key.
    :rtype:  PoolKey | , __future__, collections, functools, logging |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/request.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Convenience mixin for classes who implement a :meth:`urlopen` method, such
    as :class:`urllib3.HTTPConnectionPool` and
    :class:`urllib3.PoolManager`.

    Provides behavior for making common types of HTTP request methods and
    decides which type of request field encoding to use.

    Specifically,

    :meth:`.request_encode_url` is for sending requests whose fields are
    encoded in the URL (such as GET, HEAD, DELETE).

    :meth:`.request_encode_body` is for sending requests whose fields are
    encoded in the *body* of the request using multipart or www-form-urlencoded
    (such as for POST, PUT, PATCH).

    :meth:`.request` is for making any kind of request, it will look up the
    appropriate encoding format and use one of the above two methods to make
    the request.

    Initializer parameters:

    :param headers:
        Headers to include with all requests, unless other headers are given
        explicitly. | , __future__, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/response.py` | ❓ UNKNOWN | 2025-11-09 19:12 | From RFC7231:
        If one or more encodings have been applied to a representation, the
        sender that applied the encodings MUST generate a Content-Encoding
        header field that lists the content codings in the order in which
        they were applied. | , __future__, contextlib, io, logging, socket, sys, warnings, zlib | L178: object, it's convenient to include the original for debug purposes. It's
L441: # FIXME: Ideally we'd like to include the url in the ReadTimeoutError but
L446: # FIXME: Is there a better way to differentiate between SSLErrors?
L490: * 3.8 <= CPython < 3.9.7 because of a bug |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/connection.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Returns True if the connection is dropped and should be closed.

    :param conn:
        :class:`http.client.HTTPConnection` object.

    Note: For platforms like AppEngine, this will always return ``False`` to
    let the platform handle connection recycling transparently for us. | , __future__, socket | L136: # https://bugs.python.org/issue658327 |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/proxy.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Returns True if the connection requires an HTTP CONNECT through the proxy.

    :param URL proxy_url:
        URL of the proxy.
    :param ProxyConfig proxy_config:
        Proxy configuration from poolmanager.py
    :param str destination_scheme:
        The scheme of the destination. (i.e https, http, etc) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/queue.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | , collections, Queue |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/request.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Shortcuts for generating request headers.

    :param keep_alive:
        If ``True``, adds 'connection: keep-alive' header.

    :param accept_encoding:
        Can be a boolean, list, or string.
        ``True`` translates to 'gzip,deflate'.
        List will get joined by comma.
        String will be used as provided.

    :param user_agent:
        String representing the user-agent you want, such as
        "python-urllib3/0.6"

    :param basic_auth:
        Colon-separated username:password string for 'authorization: basic ...'
        auth header.

    :param proxy_basic_auth:
        Colon-separated username:password string for 'proxy-authorization: basic ...'
        auth header.

    :param disable_cache:
        If ``True``, adds 'cache-control: no-cache' header.

    Example::

        >>> make_headers(keep_alive=True, user_agent="Batman/1.0")
        {'connection': 'keep-alive', 'user-agent': 'Batman/1.0'}
        >>> make_headers(accept_encoding=True)
        {'accept-encoding': 'gzip,deflate'} | , __future__, base64 |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/response.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Checks whether a given file-like object is closed.

    :param obj:
        The file-like object to check. | , __future__, email | L54: # To make debugging easier add an explicit check.
L103: # FIXME: Can we do this somehow without accessing private httplib _method? |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/retry.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Retry configuration.

    Each retry attempt will create a new Retry object with updated values, so
    they can be safely reused.

    Retries can be defined as a default for a pool::

        retries = Retry(connect=5, read=2, redirect=5)
        http = PoolManager(retries=retries)
        response = http.request('GET', 'http://example.com/')

    Or per-request (which overrides the default for the pool)::

        response = http.request('GET', 'http://example.com/', retries=Retry(10))

    Retries can be disabled by passing ``False``::

        response = http.request('GET', 'http://example.com/', retries=False)

    Errors will be wrapped in :class:`~urllib3.exceptions.MaxRetryError` unless
    retries are disabled, in which case the causing exception will be raised.

    :param int total:
        Total number of retries to allow. Takes precedence over other counts.

        Set to ``None`` to remove this constraint and fall back on other
        counts.

        Set to ``0`` to fail on the first retry.

        Set to ``False`` to disable and imply ``raise_on_redirect=False``.

    :param int connect:
        How many connection-related errors to retry on.

        These are errors raised before the request is sent to the remote server,
        which we assume has not triggered the server to process the request.

        Set to ``0`` to fail on the first retry of this type.

    :param int read:
        How many times to retry on read errors.

        These errors are raised after the request was sent to the server, so the
        request may have side-effects.

        Set to ``0`` to fail on the first retry of this type.

    :param int redirect:
        How many redirects to perform. Limit this to avoid infinite redirect
        loops.

        A redirect is a HTTP response with a status code 301, 302, 303, 307 or
        308.

        Set to ``0`` to fail on the first retry of this type.

        Set to ``False`` to disable and imply ``raise_on_redirect=False``.

    :param int status:
        How many times to retry on bad status codes.

        These are retries made on responses, where status code matches
        ``status_forcelist``.

        Set to ``0`` to fail on the first retry of this type.

    :param int other:
        How many times to retry on other errors.

        Other errors are errors that are not connect, read, redirect or status errors.
        These errors might be raised after the request was sent to the server, so the
        request might have side-effects.

        Set to ``0`` to fail on the first retry of this type.

        If ``total`` is not set, it's a good idea to set this to 0 to account
        for unexpected edge cases and avoid infinite retry loops.

    :param iterable allowed_methods:
        Set of uppercased HTTP method verbs that we should retry on.

        By default, we only retry on methods which are considered to be
        idempotent (multiple requests with the same parameters end with the
        same state). See :attr:`Retry.DEFAULT_ALLOWED_METHODS`.

        Set to a ``False`` value to retry on any verb.

        .. warning::

            Previously this parameter was named ``method_whitelist``, that
            usage is deprecated in v1.26.0 and will be removed in v2.0.

    :param iterable status_forcelist:
        A set of integer HTTP status codes that we should force a retry on.
        A retry is initiated if the request method is in ``allowed_methods``
        and the response status code is in ``status_forcelist``.

        By default, this is disabled with ``None``.

    :param float backoff_factor:
        A backoff factor to apply between attempts after the second try
        (most errors are resolved immediately by a second try without a
        delay). urllib3 will sleep for::

            {backoff factor} * (2 ** ({number of total retries} - 1))

        seconds. If the backoff_factor is 0.1, then :func:`.sleep` will sleep
        for [0.0s, 0.2s, 0.4s, ...] between retries. It will never be longer
        than :attr:`Retry.DEFAULT_BACKOFF_MAX`.

        By default, backoff is disabled (set to 0).

    :param bool raise_on_redirect: Whether, if the number of redirects is
        exhausted, to raise a MaxRetryError, or to return a response with a
        response code in the 3xx range.

    :param bool raise_on_status: Similar meaning to ``raise_on_redirect``:
        whether we should raise an exception, or return a response,
        if status falls in ``status_forcelist`` range and retries have
        been exhausted.

    :param tuple history: The history of the request encountered during
        each call to :meth:`~Retry.increment`. The list is in the order
        the requests occurred. Each list item is of class :class:`RequestHistory`.

    :param bool respect_retry_after_header:
        Whether to respect Retry-After header on status codes defined as
        :attr:`Retry.RETRY_AFTER_STATUS_CODES` or not.

    :param iterable remove_headers_on_redirect:
        Sequence of headers to remove from the request when a response
        indicating a redirect is returned before firing off the redirected
        request. | , __future__, collections, email, itertools, logging, re, time, warnings | L31: # TODO: In v2 we can remove this sentinel and metaclass with deprecated options.
L261: # TODO: Deprecated, remove in v2.0
L323: # TODO: If already given in **kw we use what's given to us
L353: log.debug("Converted retries value: %r -> %r", retries, new_retries)
L454: # TODO: For now favor if the Retry implementation sets its own method_whitelist |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/ssl_.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Compare two digests of equal length in constant time.

    The digests must be of type str/bytes.
    Returns True if the digests match, and False otherwise. | , __future__, binascii, hashlib, hmac, os, pip, ssl, sys, warnings | L328: # See: https://bugs.python.org/issue37428 |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/ssl_match_hostname.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The match_hostname() function from Python 3.3.3, essential when using SSL."""

# Note: This file is under the PSF license as the code comes from the python
# stdlib.   http://docs.python.org/3/license.html

import re
import sys

# ipaddress has been backported to 2.6+ in pypi.  If it is installed on the
# system, use it to handle IPAddress ServerAltnames (this was added in
# python-3.5) otherwise only do DNS matching.  This allows
# util.ssl_match_hostname to continue to be used in Python 2.7.
try:
    import ipaddress
except ImportError:
    ipaddress = None

__version__ = "3.5.0.1"


class CertificateError(ValueError):
    pass


def _dnsname_match(dn, hostname, max_wildcards=1): | ipaddress, re, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/ssltransport.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The SSLTransport wraps an existing socket and establishes an SSL connection.

    Contrary to Python's implementation of SSLSocket, it allows you to chain
    multiple TLS connections together. It's particularly useful if you need to
    implement TLS within TLS.

    The class supports most of the socket API operations. | , io, socket, ssl |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/timeout.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Timeout configuration.

    Timeouts can be defined as a default for a pool:

    .. code-block:: python

       timeout = Timeout(connect=2.0, read=7.0)
       http = PoolManager(timeout=timeout)
       response = http.request('GET', 'http://example.com/')

    Or per-request (which overrides the default for the pool):

    .. code-block:: python

       response = http.request('GET', 'http://example.com/', timeout=Timeout(10))

    Timeouts can be disabled by setting all the parameters to ``None``:

    .. code-block:: python

       no_timeout = Timeout(connect=None, read=None)
       response = http.request('GET', 'http://example.com/, timeout=no_timeout)


    :param total:
        This combines the connect and read timeouts into one; the read timeout
        will be set to the time leftover from the connect attempt. In the
        event that both a connect timeout and a total are specified, or a read
        timeout and a total are specified, the shorter timeout will be applied.

        Defaults to None.

    :type total: int, float, or None

    :param connect:
        The maximum amount of time (in seconds) to wait for a connection
        attempt to a server to succeed. Omitting the parameter will default the
        connect timeout to the system default, probably `the global default
        timeout in socket.py
        <http://hg.python.org/cpython/file/603b4d593758/Lib/socket.py#l535>`_.
        None will set an infinite timeout for connection attempts.

    :type connect: int, float, or None

    :param read:
        The maximum amount of time (in seconds) to wait between consecutive
        read operations for a response from the server. Omitting the parameter
        will default the read timeout to the system default, probably `the
        global default timeout in socket.py
        <http://hg.python.org/cpython/file/603b4d593758/Lib/socket.py#l535>`_.
        None will set an infinite timeout.

    :type read: int, float, or None

    .. note::

        Many factors can affect the total amount of time for urllib3 to return
        an HTTP response.

        For example, Python's DNS resolver does not obey the timeout specified
        on the socket. Other factors that can affect total request time include
        high CPU load, high swap, the program running at a low priority level,
        or other behaviors.

        In addition, the read and total timeouts only measure the time between
        read operations on the socket connecting the client and the server,
        not the total amount of time for the request to return a complete
        response. For most requests, the timeout is raised because the server
        has not sent the first byte in the specified time. This is not always
        the case; if a server streams one byte every fifteen seconds, a timeout
        of 20 seconds will not trigger, even though the request will take
        several minutes to complete.

        If your goal is to cut off any request after a set amount of wall clock
        time, consider having a second "watcher" thread to cut off a slow
        request. | , __future__, socket, time |  |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/url.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Data structure for representing an HTTP URL. Used as a return value for
    :func:`parse_url`. Both the scheme and host are normalized as they are
    both case-insensitive according to RFC 3986. | , __future__, collections, re | L402: # TODO: Remove this when we break backwards compatibility. |
| `blackboard-agent/venv/Lib/site-packages/pip/_vendor/urllib3/util/wait.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Waits for reading to be available on a given socket.
    Returns True if the socket is readable, or False if the timeout expired. | errno, functools, select, sys, time |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Preprocess a file using cpp.

        filename:
            Name of the file you want to preprocess.

        cpp_path:
        cpp_args:
            Refer to the documentation of parse_file for the meaning of these
            arguments.

        When successful, returns the preprocessed file's contents.
        Errors from cpp will be printed out. | , io, subprocess |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/_ast_gen.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Initialize the code generator from a configuration
            file. | string, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/_build_tables.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | _ast_gen, c_ast, importlib, lextab, pycparser, sys, yacctab | L31: yacc_debug=False, |
| `blackboard-agent/venv/Lib/site-packages/pycparser/_c_ast.cfg` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration file |  |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ast_transforms.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The 'case' statements in a 'switch' come out of parsing with one
        child node, so subsequent statements are just tucked to the parent
        Compound. Additionally, consecutive (fall-through) case statements
        come out messy. This is a peculiarity of the C grammar. The following:

            switch (myvar) {
                case 10:
                    k = 10;
                    p = k + 1;
                    return 10;
                case 20:
                case 30:
                    return 20;
                default:
                    break;
            }

        Creates this tree (pseudo-dump):

            Switch
                ID: myvar
                Compound:
                    Case 10:
                        k = 10
                    p = k + 1
                    return 10
                    Case 20:
                        Case 30:
                            return 20
                    Default:
                        break

        The goal of this transform is to fix this mess, turning it into the
        following:

            Switch
                ID: myvar
                Compound:
                    Case 10:
                        k = 10
                        p = k + 1
                        return 10
                    Case 20:
                    Case 30:
                        return 20
                    Default:
                        break

        A fixed AST node is returned. The argument may be modified. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/c_ast.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Get the representation of an object, with dedicated pprint-like format for lists. | sys |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/c_generator.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Uses the same visitor pattern as c_ast.NodeVisitor, but modified to
        return a value from each visit method, using string accumulation in
        generic_visit. |  |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/c_lexer.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A lexer for the C language. After building it, set the
        input text with input(), and call token() to get new
        tokens.

        The public attribute filename can be set to an initial
        filename, but the lexer will update it upon #line
        directives. | , re |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/c_parser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Create a new CParser.

            Some arguments for controlling the debug/optimization
            level of the parser are provided. The defaults are
            tuned for release/performance mode.
            The simple rules for using them are:
            *) When tweaking CParser/CLexer, set these to False
            *) When releasing a stable parser, set to True

            lex_optimize:
                Set to False when you're modifying the lexer.
                Otherwise, changes in the lexer won't be used, if
                some lextab.py file exists.
                When releasing with a stable lexer, set to True
                to save the re-generation of the lexer table on
                each run.

            lexer:
                Set this parameter to define the lexer to use if
                you're not using the default CLexer.

            lextab:
                Points to the lex table that's used for optimized
                mode. Only if you're modifying the lexer and want
                some tests to avoid re-generating the table, make
                this point to a local lex table file (that's been
                earlier generated with lex_optimize=True)

            yacc_optimize:
                Set to False when you're modifying the parser.
                Otherwise, changes in the parser won't be used, if
                some parsetab.py file exists.
                When releasing with a stable parser, set to True
                to save the re-generation of the parser table on
                each run.

            yacctab:
                Points to the yacc table that's used for optimized
                mode. Only if you're modifying the parser, make
                this point to a local yacc table file

            yacc_debug:
                Generate a parser.out file that explains how yacc
                built the parsing table from the grammar.

            taboutputdir:
                Set this parameter to control the location of generated
                lextab and yacctab files. |  | L26: yacc_debug=False,
L30: Some arguments for controlling the debug/optimization
L69: yacc_debug:
L112: debug=yacc_debug,
L130: def parse(self, text, filename='', debug=False):
L140: debug:
L141: Debug flag to YACC
L150: debug=debug) |
| `blackboard-agent/venv/Lib/site-packages/pycparser/lextab.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ply/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ply/cpp.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | copy, os, re, sys, time |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ply/ctokens.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ply/lex.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | copy, inspect, os, re, sys, types | L89: debug = critical |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ply/yacc.py` | ❓ UNKNOWN | 2025-11-09 21:21 | def errok():
    warnings.warn(_warnmsg)
    return _errok()

def restart():
    warnings.warn(_warnmsg)
    return _restart()

def token():
    warnings.warn(_warnmsg)
    return _token()

# Utility function to call the p_error() function with some deprecation hacks
def call_errorfunc(errorfunc, token, parser):
    global _errok, _token, _restart
    _errok = parser.errok
    _token = parser.token
    _restart = parser.restart
    r = errorfunc(token)
    try:
        del _errok, _token, _restart
    except NameError:
        pass
    return r

#-----------------------------------------------------------------------------
#                        ===  LR Parsing Engine ===
#
# The following classes are used for the LR parser itself.  These are not
# used during table construction and are independent of the actual LR
# table generation algorithm
#-----------------------------------------------------------------------------

# This class is used to hold non-terminal grammar symbols during parsing.
# It normally has the following attributes set:
#        .type       = Grammar symbol type
#        .value      = Symbol value
#        .lineno     = Starting line number
#        .endlineno  = Ending line number (optional, set automatically)
#        .lexpos     = Starting lex position
#        .endlexpos  = Ending lex position (optional, set automatically)

class YaccSymbol:
    def __str__(self):
        return self.type

    def __repr__(self):
        return str(self)

# This class is a wrapper around the objects actually passed to each
# grammar rule.   Index lookup and assignment actually assign the
# .value attribute of the underlying YaccSymbol object.
# The lineno() method returns the line number of a given
# item (or 0 if not defined).   The linespan() method returns
# a tuple of (startline,endline) representing the range of lines
# for a symbol.  The lexspan() method returns a tuple (lexpos,endlexpos)
# representing the range of positional information for a symbol.

class YaccProduction:
    def __init__(self, s, stack=None):
        self.slice = s
        self.stack = stack
        self.lexer = None
        self.parser = None

    def __getitem__(self, n):
        if isinstance(n, slice):
            return [s.value for s in self.slice[n]]
        elif n >= 0:
            return self.slice[n].value
        else:
            return self.stack[n].value

    def __setitem__(self, n, v):
        self.slice[n].value = v

    def __getslice__(self, i, j):
        return [s.value for s in self.slice[i:j]]

    def __len__(self):
        return len(self.slice)

    def lineno(self, n):
        return getattr(self.slice[n], 'lineno', 0)

    def set_lineno(self, n, lineno):
        self.slice[n].lineno = lineno

    def linespan(self, n):
        startline = getattr(self.slice[n], 'lineno', 0)
        endline = getattr(self.slice[n], 'endlineno', startline)
        return startline, endline

    def lexpos(self, n):
        return getattr(self.slice[n], 'lexpos', 0)

    def lexspan(self, n):
        startpos = getattr(self.slice[n], 'lexpos', 0)
        endpos = getattr(self.slice[n], 'endlexpos', startpos)
        return startpos, endpos

    def error(self):
        raise SyntaxError

# -----------------------------------------------------------------------------
#                               == LRParser ==
#
# The LR Parsing engine.
# -----------------------------------------------------------------------------

class LRParser:
    def __init__(self, lrtab, errorf):
        self.productions = lrtab.lr_productions
        self.action = lrtab.lr_action
        self.goto = lrtab.lr_goto
        self.errorfunc = errorf
        self.set_defaulted_states()
        self.errorok = True

    def errok(self):
        self.errorok = True

    def restart(self):
        del self.statestack[:]
        del self.symstack[:]
        sym = YaccSymbol() | base64, inspect, os, re, sys, types, warnings | L79: yaccdebug   = True             # Debugging mode.  If set, yacc generates a
L82: debug_file  = 'parser.out'     # Default name of the debugging file
L91: resultlimit = 40               # Size limit of results when running in debug mode.
L113: def debug(self, msg, *args, **kwargs):
L116: info = debug
L124: critical = debug
L138: # Format the result message that the parser produces when running in debug mode.
L148: # Format stack entries when the parser is running in debug mode
L187: # Utility function to call the p_error() function with some deprecation hacks
L323: def parse(self, input=None, lexer=None, debug=False, tracking=False, tokenfunc=None):
L324: if debug or yaccdevel:
L325: if isinstance(debug, int):
L326: debug = PlyLogger(sys.stderr)
L327: return self.parsedebug(input, lexer, debug, tracking, tokenfunc)
L329: return self.parseopt(input, lexer, debug, tracking, tokenfunc)
L331: return self.parseopt_notrack(input, lexer, debug, tracking, tokenfunc)
L335: # parsedebug().
L337: # This is the debugging enabled version of parse().  All changes made to the
L342: #      #--! DEBUG
L344: #      #--! DEBUG
L348: def parsedebug(self, input=None, lexer=None, debug=False, tracking=False, tokenfunc=None):
L349: #--! parsedebug-start
L359: #--! DEBUG
L360: debug.info('PLY: PARSE DEBUG START')
L361: #--! DEBUG
L407: #--! DEBUG
L408: debug.debug('')
L409: debug.debug('State  : %s', state)
L410: #--! DEBUG
L427: #--! DEBUG
L428: debug.debug('Defaulted state %s: Reduce using %d', state, -t)
L429: #--! DEBUG
L431: #--! DEBUG
L432: debug.debug('Stack  : %s',
L434: #--! DEBUG
L442: #--! DEBUG
L443: debug.debug('Action : Shift and goto state %s', t)
L444: #--! DEBUG
L465: #--! DEBUG
L467: debug.info('Action : Reduce rule [%s] with %s and goto state %d', p.str,
L471: debug.info('Action : Reduce rule [%s] with %s and goto state %d', p.str, [],
L474: #--! DEBUG |
| `blackboard-agent/venv/Lib/site-packages/pycparser/ply/ygen.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, shutil | L6: # Users should edit the method LParser.parsedebug() in yacc.py.   The source code
L45: parse_start, parse_end = get_source_range(lines, 'parsedebug')
L52: # Filter the DEBUG sections out
L53: parseopt_lines = filter_section(orig_lines, 'DEBUG') |
| `blackboard-agent/venv/Lib/site-packages/pycparser/plyparser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Coordinates of a syntactic element. Consists of:
            - File name
            - Line number
            - (optional) column number, for the Lexer | warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pycparser/yacctab.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , importlib, pydantic_core, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_config.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Internal wrapper for Config which exposes ConfigDict items as attributes."""

    __slots__ = ('config_dict',)

    config_dict: ConfigDict

    # all annotations are copied directly from ConfigDict, and should be kept up to date, a test will fail if they
    # stop matching
    title: str \\| None
    str_to_lower: bool
    str_to_upper: bool
    str_strip_whitespace: bool
    str_min_length: int
    str_max_length: int \\| None
    extra: ExtraValues \\| None
    frozen: bool
    populate_by_name: bool
    use_enum_values: bool
    validate_assignment: bool
    arbitrary_types_allowed: bool
    from_attributes: bool
    # whether to use the actual key provided in the data (e.g. alias or first alias for "field required" errors) instead of field_names
    # to construct error `loc`s, default `True`
    loc_by_alias: bool
    alias_generator: Callable[[str], str] \\| AliasGenerator \\| None
    model_title_generator: Callable[[type], str] \\| None
    field_title_generator: Callable[[str, FieldInfo \\| ComputedFieldInfo], str] \\| None
    ignored_types: tuple[type, ...]
    allow_inf_nan: bool
    json_schema_extra: JsonDict \\| JsonSchemaExtraCallable \\| None
    json_encoders: dict[type[object], JsonEncoder] \\| None

    # new in V2
    strict: bool
    # whether instances of models and dataclasses (including subclass instances) should re-validate, default 'never'
    revalidate_instances: Literal['always', 'never', 'subclass-instances']
    ser_json_timedelta: Literal['iso8601', 'float']
    ser_json_temporal: Literal['iso8601', 'seconds', 'milliseconds']
    val_temporal_unit: Literal['seconds', 'milliseconds', 'infer']
    ser_json_bytes: Literal['utf8', 'base64', 'hex']
    val_json_bytes: Literal['utf8', 'base64', 'hex']
    ser_json_inf_nan: Literal['null', 'constants', 'strings']
    # whether to validate default values during validation, default False
    validate_default: bool
    validate_return: bool
    protected_namespaces: tuple[str \\| Pattern[str], ...]
    hide_input_in_errors: bool
    defer_build: bool
    plugin_settings: dict[str, object] \\| None
    schema_generator: type[GenerateSchema] \\| None
    json_schema_serialization_defaults_required: bool
    json_schema_mode_override: Literal['validation', 'serialization', None]
    coerce_numbers_to_str: bool
    regex_engine: Literal['rust-regex', 'python-re']
    validation_error_cause: bool
    use_attribute_docstrings: bool
    cache_strings: bool \\| Literal['all', 'keys', 'none']
    validate_by_alias: bool
    validate_by_name: bool
    serialize_by_alias: bool
    url_preserve_empty_path: bool

    def __init__(self, config: ConfigDict \\| dict[str, Any] \\| type[Any] \\| None, *, check: bool = True):
        if check:
            self.config_dict = prepare_config(config)
        else:
            self.config_dict = cast(ConfigDict, config)

    @classmethod
    def for_model(
        cls,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        raw_annotations: dict[str, Any],
        kwargs: dict[str, Any],
    ) -> Self: | , __future__, contextlib, pydantic_core, re, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_core_metadata.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A `TypedDict` for holding the metadata dict of the schema.

    Attributes:
        pydantic_js_functions: List of JSON schema functions that resolve refs during application.
        pydantic_js_annotation_functions: List of JSON schema functions that don't resolve refs during application.
        pydantic_js_prefer_positional_arguments: Whether JSON schema generator will
            prefer positional over keyword arguments for an 'arguments' schema.
            custom validation function. Only applies to before, plain, and wrap validators.
        pydantic_js_updates: key / value pair updates to apply to the JSON schema for a type.
        pydantic_js_extra: WIP, either key/value pair updates to apply to the JSON schema, or a custom callable.
        pydantic_internal_union_tag_key: Used internally by the `Tag` metadata to specify the tag used for a discriminated union.
        pydantic_internal_union_discriminator: Used internally to specify the discriminator value for a discriminated union
            when the discriminator was applied to a `'definition-ref'` schema, and that reference was missing at the time
            of the annotation application.

    TODO: Perhaps we should move this structure to pydantic-core. At the moment, though,
    it's easier to iterate on if we leave it in pydantic until we feel there is a semi-stable API.

    TODO: It's unfortunate how functionally oriented JSON schema generation is, especially that which occurs during
    the core schema generation process. It's inevitable that we need to store some json schema related information
    on core schemas, given that we generate JSON schemas directly from core schemas. That being said, debugging related
    issues is quite difficult when JSON schema information is disguised via dynamically defined functions. | , __future__, typing, warnings | L29: TODO: Perhaps we should move this structure to pydantic-core. At the moment, though,
L32: TODO: It's unfortunate how functionally oriented JSON schema generation is, especially that which occurs during
L34: on core schemas, given that we generate JSON schemas directly from core schemas. That being said, debugging related
L62: We do this here, instead of before / after each call to this function so that this typing hack |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_core_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Produces the ref to be used for this type by pydantic_core's core schemas.

    This `args_override` argument was added for the purpose of creating valid recursive references
    when creating generic models without needing to create a concrete class. | , __future__, collections, inspect, pydantic, pydantic_core, rich, typing, typing_extensions, typing_inspection |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_dataclasses.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Private logic for creating pydantic dataclasses."""

from __future__ import annotations as _annotations

import copy
import dataclasses
import sys
import warnings
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from typing import TYPE_CHECKING, Any, ClassVar, Protocol, cast

from pydantic_core import (
    ArgsKwargs,
    SchemaSerializer,
    SchemaValidator,
    core_schema,
)
from typing_extensions import TypeAlias, TypeIs

from ..errors import PydanticUndefinedAnnotation
from ..fields import FieldInfo
from ..plugin._schema_validator import PluggableSchemaValidator, create_schema_validator
from ..warnings import PydanticDeprecatedSince20
from . import _config, _decorators
from ._fields import collect_dataclass_fields
from ._generate_schema import GenerateSchema, InvalidSchemaError
from ._generics import get_standard_typevars_map
from ._mock_val_ser import set_dataclass_mocks
from ._namespace_utils import NsResolver
from ._signature import generate_pydantic_signature
from ._utils import LazyClassAttribute

if TYPE_CHECKING:
    from _typeshed import DataclassInstance as StandardDataclass

    from ..config import ConfigDict

    class PydanticDataclass(StandardDataclass, Protocol): | , __future__, _typeshed, collections, contextlib, copy, dataclasses, functools, pydantic, pydantic_core, sys, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_decorators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Logic related to validators applied to models etc. via the `@field_validator` and `@model_validator` decorators."""

from __future__ import annotations as _annotations

import sys
import types
from collections import deque
from collections.abc import Iterable
from dataclasses import dataclass, field
from functools import cached_property, partial, partialmethod
from inspect import Parameter, Signature, isdatadescriptor, ismethoddescriptor, signature
from itertools import islice
from typing import TYPE_CHECKING, Any, Callable, ClassVar, Generic, Literal, TypeVar, Union

from pydantic_core import PydanticUndefined, PydanticUndefinedType, core_schema
from typing_extensions import TypeAlias, is_typeddict

from ..errors import PydanticUserError
from ._core_utils import get_type_ref
from ._internal_dataclass import slots_true
from ._namespace_utils import GlobalsNamespace, MappingNamespace
from ._typing_extra import get_function_type_hints
from ._utils import can_be_positional

if TYPE_CHECKING:
    from ..fields import ComputedFieldInfo
    from ..functional_validators import FieldValidatorModes
    from ._config import ConfigWrapper


@dataclass(**slots_true)
class ValidatorDecoratorInfo: | , __future__, collections, dataclasses, functools, inspect, itertools, pydantic_core, sys, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_decorators_v1.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Logic for V1 validators, e.g. `@validator` and `@root_validator`."""

from __future__ import annotations as _annotations

from inspect import Parameter, signature
from typing import Any, Union, cast

from pydantic_core import core_schema
from typing_extensions import Protocol

from ..errors import PydanticUserError
from ._utils import can_be_positional


class V1OnlyValueValidator(Protocol): | , __future__, inspect, pydantic_core, typing, typing_extensions | L160: # ugly hack: to match v1 behaviour, we merge values and model_extra, then split them up based on fields |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_discriminated_union.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Raised when applying a discriminated union discriminator to a schema
    requires a definition that is not yet defined | , __future__, collections, pydantic_core, typing | L75: replaced with a tagged-union, with all the associated debugging and performance benefits.
L102: # debugging challenges for users making subtle mistakes. |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_docs_extraction.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Utilities related to attribute docstring extraction."""

from __future__ import annotations

import ast
import inspect
import sys
import textwrap
from typing import Any


class DocstringVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        super().__init__()

        self.target: str \\| None = None
        self.attrs: dict[str, str] = {}
        self.previous_node_type: type[ast.AST] \\| None = None

    def visit(self, node: ast.AST) -> Any:
        node_result = super().visit(node)
        self.previous_node_type = type(node)
        return node_result

    def visit_AnnAssign(self, node: ast.AnnAssign) -> Any:
        if isinstance(node.target, ast.Name):
            self.target = node.target.id

    def visit_Expr(self, node: ast.Expr) -> Any:
        if (
            isinstance(node.value, ast.Constant)
            and isinstance(node.value.value, str)
            and self.previous_node_type is ast.AnnAssign
        ):
            docstring = inspect.cleandoc(node.value.value)
            if self.target:
                self.attrs[self.target] = docstring
            self.target = None


def _dedent_source_lines(source: list[str]) -> str:
    # Required for nested class definitions, e.g. in a function block
    dedent_source = textwrap.dedent(''.join(source))
    if dedent_source.startswith((' ', '\t')):
        # We are in the case where there's a dedented (usually multiline) string
        # at a lower indentation level than the class itself. We wrap our class
        # in a function as a workaround.
        dedent_source = f'def dedent_workaround():\n{dedent_source}'
    return dedent_source


def _extract_source_from_frame(cls: type[Any]) -> list[str] \\| None:
    frame = inspect.currentframe()

    while frame:
        if inspect.getmodule(frame) is inspect.getmodule(cls):
            lnum = frame.f_lineno
            try:
                lines, _ = inspect.findsource(frame)
            except OSError:  # pragma: no cover
                # Source can't be retrieved (maybe because running in an interactive terminal),
                # we don't want to error here.
                pass
            else:
                block_lines = inspect.getblock(lines[lnum - 1 :])
                dedent_source = _dedent_source_lines(block_lines)
                try:
                    block_tree = ast.parse(dedent_source)
                except SyntaxError:
                    pass
                else:
                    stmt = block_tree.body[0]
                    if isinstance(stmt, ast.FunctionDef) and stmt.name == 'dedent_workaround':
                        # `_dedent_source_lines` wrapped the class around the workaround function
                        stmt = stmt.body[0]
                    if isinstance(stmt, ast.ClassDef) and stmt.name == cls.__name__:
                        return block_lines

        frame = frame.f_back


def extract_docstrings_from_cls(cls: type[Any], use_inspect: bool = False) -> dict[str, str]: | __future__, ast, inspect, sys, textwrap, typing | L103: # TODO remove this implementation when we drop support for Python 3.12: |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_fields.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Private logic related to fields (the `Field()` function and `FieldInfo` class), and arguments to `Annotated`."""

from __future__ import annotations as _annotations

import dataclasses
import warnings
from collections.abc import Mapping
from functools import cache
from inspect import Parameter, ismethoddescriptor, signature
from re import Pattern
from typing import TYPE_CHECKING, Any, Callable, TypeVar

from pydantic_core import PydanticUndefined
from typing_extensions import TypeIs
from typing_inspection.introspection import AnnotationSource

from pydantic import PydanticDeprecatedSince211
from pydantic.errors import PydanticUserError

from ..aliases import AliasGenerator
from . import _generics, _typing_extra
from ._config import ConfigWrapper
from ._docs_extraction import extract_docstrings_from_cls
from ._import_utils import import_cached_base_model, import_cached_field_info
from ._namespace_utils import NsResolver
from ._repr import Representation
from ._utils import can_be_positional, get_first_not_none

if TYPE_CHECKING:
    from annotated_types import BaseMetadata

    from ..fields import FieldInfo
    from ..main import BaseModel
    from ._dataclasses import PydanticDataclass, StandardDataclass
    from ._decorators import DecoratorInfos


class PydanticMetadata(Representation): | , __future__, annotated_types, collections, dataclasses, functools, inspect, pydantic, pydantic_core, re, typing, typing_extensions, typing_inspection, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_forward_ref.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Defining __call__ is necessary for the `typing` module to let you use an instance of
        this class as the result of resolving a standard ForwardRef. | __future__, dataclasses, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_generate_schema.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Convert python types to pydantic-core schema."""

from __future__ import annotations as _annotations

import collections.abc
import dataclasses
import datetime
import inspect
import os
import pathlib
import re
import sys
import typing
import warnings
from collections.abc import Generator, Iterable, Iterator, Mapping
from contextlib import contextmanager
from copy import copy
from decimal import Decimal
from enum import Enum
from fractions import Fraction
from functools import partial
from inspect import Parameter, _ParameterKind, signature
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from itertools import chain
from operator import attrgetter
from types import FunctionType, GenericAlias, LambdaType, MethodType
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Final,
    ForwardRef,
    Literal,
    TypeVar,
    Union,
    cast,
    overload,
)
from uuid import UUID
from zoneinfo import ZoneInfo

import typing_extensions
from pydantic_core import (
    MISSING,
    CoreSchema,
    MultiHostUrl,
    PydanticCustomError,
    PydanticSerializationUnexpectedValue,
    PydanticUndefined,
    Url,
    core_schema,
    to_jsonable_python,
)
from typing_extensions import TypeAlias, TypeAliasType, get_args, get_origin, is_typeddict
from typing_inspection import typing_objects
from typing_inspection.introspection import AnnotationSource, get_literal_values, is_union_origin

from ..aliases import AliasChoices, AliasPath
from ..annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from ..config import ConfigDict, JsonDict, JsonEncoder, JsonSchemaExtraCallable
from ..errors import PydanticSchemaGenerationError, PydanticUndefinedAnnotation, PydanticUserError
from ..functional_validators import AfterValidator, BeforeValidator, FieldValidatorModes, PlainValidator, WrapValidator
from ..json_schema import JsonSchemaValue
from ..version import version_short
from ..warnings import (
    ArbitraryTypeWarning,
    PydanticDeprecatedSince20,
    TypedDictExtraConfigWarning,
    UnsupportedFieldAttributeWarning,
)
from . import _decorators, _discriminated_union, _known_annotated_metadata, _repr, _typing_extra
from ._config import ConfigWrapper, ConfigWrapperStack
from ._core_metadata import CoreMetadata, update_core_metadata
from ._core_utils import (
    get_ref,
    get_type_ref,
    is_list_like_schema_with_items_schema,
)
from ._decorators import (
    Decorator,
    DecoratorInfos,
    FieldSerializerDecoratorInfo,
    FieldValidatorDecoratorInfo,
    ModelSerializerDecoratorInfo,
    ModelValidatorDecoratorInfo,
    RootValidatorDecoratorInfo,
    ValidatorDecoratorInfo,
    get_attribute_from_bases,
    inspect_field_serializer,
    inspect_model_serializer,
    inspect_validator,
)
from ._docs_extraction import extract_docstrings_from_cls
from ._fields import (
    collect_dataclass_fields,
    rebuild_dataclass_fields,
    rebuild_model_fields,
    takes_validated_data_argument,
    update_field_from_config,
)
from ._forward_ref import PydanticRecursiveRef
from ._generics import get_standard_typevars_map, replace_types
from ._import_utils import import_cached_base_model, import_cached_field_info
from ._mock_val_ser import MockCoreSchema
from ._namespace_utils import NamespacesTuple, NsResolver
from ._schema_gather import MissingDefinitionError, gather_schemas_for_cleaning
from ._schema_generation_shared import CallbackGetCoreSchemaHandler
from ._utils import lenient_issubclass, smart_deepcopy

if TYPE_CHECKING:
    from ..fields import ComputedFieldInfo, FieldInfo
    from ..main import BaseModel
    from ..types import Discriminator
    from ._dataclasses import StandardDataclass
    from ._schema_generation_shared import GetJsonSchemaFunction

_SUPPORTS_TYPEDDICT = sys.version_info >= (3, 12)

FieldDecoratorInfo = Union[ValidatorDecoratorInfo, FieldValidatorDecoratorInfo, FieldSerializerDecoratorInfo]
FieldDecoratorInfoType = TypeVar('FieldDecoratorInfoType', bound=FieldDecoratorInfo)
AnyFieldDecorator = Union[
    Decorator[ValidatorDecoratorInfo],
    Decorator[FieldValidatorDecoratorInfo],
    Decorator[FieldSerializerDecoratorInfo],
]

ModifyCoreSchemaWrapHandler: TypeAlias = GetCoreSchemaHandler
GetCoreSchemaFunction: TypeAlias = Callable[[Any, ModifyCoreSchemaWrapHandler], core_schema.CoreSchema]
ParametersCallback: TypeAlias = "Callable[[int, str, Any], Literal['skip'] \\| None]"

TUPLE_TYPES: list[type] = [typing.Tuple, tuple]  # noqa: UP006
LIST_TYPES: list[type] = [typing.List, list, collections.abc.MutableSequence]  # noqa: UP006
SET_TYPES: list[type] = [typing.Set, set, collections.abc.MutableSet]  # noqa: UP006
FROZEN_SET_TYPES: list[type] = [typing.FrozenSet, frozenset, collections.abc.Set]  # noqa: UP006
DICT_TYPES: list[type] = [typing.Dict, dict]  # noqa: UP006
IP_TYPES: list[type] = [IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network]
SEQUENCE_TYPES: list[type] = [typing.Sequence, collections.abc.Sequence]
ITERABLE_TYPES: list[type] = [typing.Iterable, collections.abc.Iterable, typing.Generator, collections.abc.Generator]
TYPE_TYPES: list[type] = [typing.Type, type]  # noqa: UP006
PATTERN_TYPES: list[type] = [typing.Pattern, re.Pattern]
PATH_TYPES: list[type] = [
    os.PathLike,
    pathlib.Path,
    pathlib.PurePath,
    pathlib.PosixPath,
    pathlib.PurePosixPath,
    pathlib.PureWindowsPath,
]
MAPPING_TYPES = [
    typing.Mapping,
    typing.MutableMapping,
    collections.abc.Mapping,
    collections.abc.MutableMapping,
    collections.OrderedDict,
    typing_extensions.OrderedDict,
    typing.DefaultDict,  # noqa: UP006
    collections.defaultdict,
]
COUNTER_TYPES = [collections.Counter, typing.Counter]
DEQUE_TYPES: list[type] = [collections.deque, typing.Deque]  # noqa: UP006

# Note: This does not play very well with type checkers. For example,
# `a: LambdaType = lambda x: x` will raise a type error by Pyright.
ValidateCallSupportedTypes = Union[
    LambdaType,
    FunctionType,
    MethodType,
    partial,
]

VALIDATE_CALL_SUPPORTED_TYPES = get_args(ValidateCallSupportedTypes)
UNSUPPORTED_STANDALONE_FIELDINFO_ATTRIBUTES: list[tuple[str, Any]] = [
    ('alias', None),
    ('validation_alias', None),
    ('serialization_alias', None),
    # will be set if any alias is set, so disable it to avoid double warnings:
    # 'alias_priority',
    ('default', PydanticUndefined),
    ('default_factory', None),
    ('exclude', None),
    ('deprecated', None),
    ('repr', True),
    ('validate_default', None),
    ('frozen', None),
    ('init', None),
    ('init_var', None),
    ('kw_only', None),
] | , __future__, collections, contextlib, copy, dataclasses, datetime, decimal, enum, fractions, functools, inspect, ipaddress, itertools, operator, os, pathlib, pydantic_core, re, sys, types, typing, typing_extensions, typing_inspection, uuid, warnings, zoneinfo | L324: # TODO: in theory we should check that the schema accepts a serialization key
L419: # TODO this is an ugly hack, how do we trigger an Any schema for serialization? |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_generics.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Variant of ChainMap that allows direct updates to inner scopes.

        Taken from https://docs.python.org/3/library/collections.html#collections.ChainMap,
        with some light modifications for this use case. | , __future__, collections, contextlib, contextvars, functools, itertools, operator, pydantic, sys, types, typing, typing_extensions, typing_inspection, weakref | L234: # TODO: This could be unified with `get_standard_typevars_map` if we stored the generic metadata
L275: # TODO remove parentheses when we drop support for Python 3.10: |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_git.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Git utilities, adopted from mypy's git utilities (https://github.com/python/mypy/blob/master/mypy/git.py)."""

from __future__ import annotations

import subprocess
from pathlib import Path


def is_git_repo(dir: Path) -> bool: | __future__, pathlib, subprocess |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_import_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | functools, pydantic, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_internal_dataclass.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | sys |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_known_annotated_metadata.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Expand the annotations.

    Args:
        annotations: An iterable of annotations.

    Returns:
        An iterable of expanded annotations.

    Example:
        ```python
        from annotated_types import Ge, Len

        from pydantic._internal._known_annotated_metadata import expand_grouped_metadata

        print(list(expand_grouped_metadata([Ge(4), Len(5)])))
        #> [Ge(ge=4), MinLen(min_length=5)]
        ``` | , __future__, annotated_types, collections, copy, functools, pydantic, pydantic_core, typing | L83: # TODO: this is a bit redundant, we could probably avoid some of these |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_mock_val_ser.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Mocker for `pydantic_core.CoreSchema` which optionally attempts to
    rebuild the thing it's mocking when one of its methods is accessed and raises an error if that fails. | , __future__, collections, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_model_construction.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Private logic for creating models."""

from __future__ import annotations as _annotations

import operator
import sys
import typing
import warnings
import weakref
from abc import ABCMeta
from functools import cache, partial, wraps
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, NoReturn, TypeVar, cast

from pydantic_core import PydanticUndefined, SchemaSerializer
from typing_extensions import TypeAliasType, dataclass_transform, deprecated, get_args, get_origin
from typing_inspection import typing_objects

from ..errors import PydanticUndefinedAnnotation, PydanticUserError
from ..plugin._schema_validator import create_schema_validator
from ..warnings import GenericBeforeBaseModelWarning, PydanticDeprecatedSince20
from ._config import ConfigWrapper
from ._decorators import DecoratorInfos, PydanticDescriptorProxy, get_attribute_from_bases, unwrap_wrapped_function
from ._fields import collect_model_fields, is_valid_field_name, is_valid_privateattr_name, rebuild_model_fields
from ._generate_schema import GenerateSchema, InvalidSchemaError
from ._generics import PydanticGenericMetadata, get_model_typevars_map
from ._import_utils import import_cached_base_model, import_cached_field_info
from ._mock_val_ser import set_model_mocks
from ._namespace_utils import NsResolver
from ._signature import generate_pydantic_signature
from ._typing_extra import (
    _make_forward_ref,
    eval_type_backport,
    is_classvar_annotation,
    parent_frame_namespace,
)
from ._utils import LazyClassAttribute, SafeGetItemProxy

if TYPE_CHECKING:
    from ..fields import Field as PydanticModelField
    from ..fields import FieldInfo, ModelPrivateAttr
    from ..fields import PrivateAttr as PydanticModelPrivateAttr
    from ..main import BaseModel
else:
    PydanticModelField = object()
    PydanticModelPrivateAttr = object()

object_setattr = object.__setattr__


class _ModelNamespaceDict(dict): | , __future__, abc, annotationlib, functools, operator, pydantic_core, sys, types, typing, typing_extensions, typing_inspection, warnings, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_namespace_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | A global namespace.

In most cases, this is a reference to the `__dict__` attribute of a module.
This namespace type is expected as the `globals` argument during annotations evaluation. | __future__, collections, contextlib, functools, pydantic, sys, typing, typing_extensions | L236: # TODO: should we merge the parent namespace here?
L239: # locals to both parent_ns and the base_ns_tuple, but this is a bit hacky.
L242: #     # Hacky workarounds, see class docstring:
L253: # Hacky workarounds, see class docstring:
L263: # TODO `typ.__type_params__` when we drop support for Python 3.11: |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_repr.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Tools to provide pretty/human-readable display of objects."""

from __future__ import annotations as _annotations

import types
from collections.abc import Callable, Collection, Generator, Iterable
from typing import TYPE_CHECKING, Any, ForwardRef, cast

import typing_extensions
from typing_extensions import TypeAlias
from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin

from . import _typing_extra

if TYPE_CHECKING:
    # TODO remove type error comments when we drop support for Python 3.9
    ReprArgs: TypeAlias = Iterable[tuple[str \\| None, Any]]  # pyright: ignore[reportGeneralTypeIssues]
    RichReprResult: TypeAlias = Iterable[Any \\| tuple[Any] \\| tuple[str, Any] \\| tuple[str, Any, Any]]  # pyright: ignore[reportGeneralTypeIssues]


class PlainRepr(str): | , __future__, collections, types, typing, typing_extensions, typing_inspection | L17: # TODO remove type error comments when we drop support for Python 3.9 |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_schema_gather.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Schema traversing result."""

    collected_references: dict[str, DefinitionReferenceSchema \\| None] | __future__, dataclasses, pydantic_core, typing, typing_extensions | L91: # TODO When we drop 3.9, use a match statement to get better type checking and remove
L170: # TODO duplicate schema types for serializers and validators, needs to be deduplicated.
L176: # TODO duplicate schema types for serializers and validators, needs to be deduplicated. |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_schema_generation_shared.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Types and utility functions used by various other internal tools."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Literal

from pydantic_core import core_schema

from ..annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler

if TYPE_CHECKING:
    from ..json_schema import GenerateJsonSchema, JsonSchemaValue
    from ._core_utils import CoreSchemaOrField
    from ._generate_schema import GenerateSchema
    from ._namespace_utils import NamespacesTuple

    GetJsonSchemaFunction = Callable[[CoreSchemaOrField, GetJsonSchemaHandler], JsonSchemaValue]
    HandlerOverride = Callable[[CoreSchemaOrField], JsonSchemaValue]


class GenerateJsonSchemaHandler(GetJsonSchemaHandler): | , __future__, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_serializers.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | __future__, collections, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_signature.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Extract the correct name to use for the field when generating a signature.

    Assuming the field has a valid alias, this will return the alias. Otherwise, it will return the field name.
    First priority is given to the alias, then the validation_alias, then the field name.

    Args:
        field_name: The name of the field
        field_info: The corresponding FieldInfo object.

    Returns:
        The correct name to use when generating a signature. | , __future__, dataclasses, inspect, itertools, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_typing_extra.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Logic for interacting with type annotations, mostly extensions, shims and hacks to wrap Python's typing module."""

from __future__ import annotations

import collections.abc
import re
import sys
import types
import typing
from functools import partial
from typing import TYPE_CHECKING, Any, Callable, cast

import typing_extensions
from typing_extensions import deprecated, get_args, get_origin
from typing_inspection import typing_objects
from typing_inspection.introspection import is_union_origin

from pydantic.version import version_short

from ._namespace_utils import GlobalsNamespace, MappingNamespace, NsResolver, get_module_ns_of

if sys.version_info < (3, 10):
    NoneType = type(None)
    EllipsisType = type(Ellipsis)
else:
    from types import EllipsisType as EllipsisType
    from types import NoneType as NoneType

if sys.version_info >= (3, 14):
    import annotationlib

if TYPE_CHECKING:
    from pydantic import BaseModel

# As per https://typing-extensions.readthedocs.io/en/latest/#runtime-use-of-types,
# always check for both `typing` and `typing_extensions` variants of a typing construct.
# (this is implemented differently than the suggested approach in the `typing_extensions`
# docs for performance).


_t_annotated = typing.Annotated
_te_annotated = typing_extensions.Annotated


def is_annotated(tp: Any, /) -> bool: | , __future__, annotationlib, collections, functools, pydantic, re, sys, types, typing, typing_extensions, typing_inspection | L1: """Logic for interacting with type annotations, mostly extensions, shims and hacks to wrap Python's typing module."""
L142: # TODO implement `is_finalvar_annotation` as Final can be wrapped with other special forms:
L189: # TODO In 2.12, delete this export. It is currently defined only to not break
L198: # TODO: Ideally, we should avoid relying on the private `typing` constructs:
L471: # TODO ideally recursion errors should be checked in `eval_type` above, but `eval_type_backport` |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Bucket of reusable internal utilities.

This should be reduced as much as possible with functions only used in one place, moved to that place. | , __future__, collections, copy, dataclasses, functools, inspect, itertools, keyword, pydantic, sys, types, typing, typing_extensions, warnings, weakref | L31: # TODO remove type error comments when we drop support for Python 3.9 |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_validate_call.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Extract the name of a `ValidateCallSupportedTypes` object."""
    return f'partial({func.func.__name__})' if isinstance(func, functools.partial) else func.__name__


def extract_function_qualname(func: ValidateCallSupportedTypes) -> str: | , __future__, collections, functools, inspect, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_internal/_validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Validator functions for standard library types.

Import of this module is deferred since it contains imports of many standard library modules. | __future__, collections, decimal, fractions, importlib, ipaddress, math, of, pydantic, pydantic_core, re, typing, typing_extensions, typing_inspection, zoneinfo | L45: # TODO: refactor sequence validation to validate with either a list or a tuple
L134: # todo strict mode |
| `blackboard-agent/venv/Lib/site-packages/pydantic/_migration.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Implement PEP 562 for objects that were either moved or removed on the migration
    to V2.

    Args:
        module: The module name.

    Returns:
        A callable that will raise an error if the object is not found. | , pydantic, sys, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/alias_generators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Alias generators for converting between different capitalization conventions."""

import re

__all__ = ('to_pascal', 'to_camel', 'to_snake')

# TODO: in V3, change the argument names to be more descriptive
# Generally, don't only convert from snake_case, or name the functions
# more specifically like snake_to_camel.


def to_pascal(snake: str) -> str: | re | L7: # TODO: in V3, change the argument names to be more descriptive |
| `blackboard-agent/venv/Lib/site-packages/pydantic/aliases.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Support for alias configurations."""

from __future__ import annotations

import dataclasses
from typing import Any, Callable, Literal

from pydantic_core import PydanticUndefined

from ._internal import _internal_dataclass

__all__ = ('AliasGenerator', 'AliasPath', 'AliasChoices')


@dataclasses.dataclass(**_internal_dataclass.slots_true)
class AliasPath: | , __future__, dataclasses, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/annotated_handlers.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Type annotations to use with `__get_pydantic_core_schema__` and `__get_pydantic_json_schema__`."""

from __future__ import annotations as _annotations

from typing import TYPE_CHECKING, Any, Union

from pydantic_core import core_schema

if TYPE_CHECKING:
    from ._internal._namespace_utils import NamespacesTuple
    from .json_schema import JsonSchemaMode, JsonSchemaValue

    CoreSchemaOrField = Union[
        core_schema.CoreSchema,
        core_schema.ModelField,
        core_schema.DataclassField,
        core_schema.TypedDictField,
        core_schema.ComputedField,
    ]

__all__ = 'GetJsonSchemaHandler', 'GetCoreSchemaHandler'


class GetJsonSchemaHandler: | , __future__, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/class_validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | `class_validators` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/color.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Color definitions are used as per the CSS3
[CSS Color Module Level 3](http://www.w3.org/TR/css3-color/#svg-color) specification.

A few colors have multiple names referring to the sames colors, eg. `grey` and `gray` or `aqua` and `cyan`.

In these cases the _last_ color when sorted alphabetically takes preferences,
eg. `Color((0, 255, 255)).as_named() == 'cyan'` because "cyan" comes after "aqua".

Warning: Deprecated
    The `Color` class is deprecated, use `pydantic_extra_types` instead.
    See [`pydantic-extra-types.Color`](../usage/types/extra_types/color_types.md)
    for more information. | , colorsys, math, pydantic_core, re, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/config.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Configuration for Pydantic models."""

from __future__ import annotations as _annotations

import warnings
from re import Pattern
from typing import TYPE_CHECKING, Any, Callable, Literal, TypeVar, Union, cast, overload

from typing_extensions import TypeAlias, TypedDict, Unpack, deprecated

from ._migration import getattr_migration
from .aliases import AliasGenerator
from .errors import PydanticUserError
from .warnings import PydanticDeprecatedSince211

if TYPE_CHECKING:
    from ._internal._generate_schema import GenerateSchema as _GenerateSchema
    from .fields import ComputedFieldInfo, FieldInfo

__all__ = ('ConfigDict', 'with_config')


JsonValue: TypeAlias = Union[int, float, str, bool, None, list['JsonValue'], 'JsonDict']
JsonDict: TypeAlias = dict[str, JsonValue]

JsonEncoder = Callable[[Any], Any]

JsonSchemaExtraCallable: TypeAlias = Union[
    Callable[[JsonDict], None],
    Callable[[JsonDict, type[Any]], None],
]

ExtraValues = Literal['allow', 'ignore', 'forbid']


class ConfigDict(TypedDict, total=False): | , __future__, enum, pydantic, re, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/dataclasses.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Provide an enhanced dataclass that performs validation."""

from __future__ import annotations as _annotations

import dataclasses
import functools
import sys
import types
from typing import TYPE_CHECKING, Any, Callable, Generic, Literal, NoReturn, TypeVar, overload
from warnings import warn

from typing_extensions import TypeGuard, dataclass_transform

from ._internal import _config, _decorators, _namespace_utils, _typing_extra
from ._internal import _dataclasses as _pydantic_dataclasses
from ._migration import getattr_migration
from .config import ConfigDict
from .errors import PydanticUserError
from .fields import Field, FieldInfo, PrivateAttr

if TYPE_CHECKING:
    from ._internal._dataclasses import PydanticDataclass
    from ._internal._namespace_utils import MappingNamespace

__all__ = 'dataclass', 'rebuild_dataclass'

_T = TypeVar('_T')

if sys.version_info >= (3, 10):

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool = False,
        config: ConfigDict \\| type[object] \\| None = None,
        validate_on_init: bool \\| None = None,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool \\| None = None,
        config: ConfigDict \\| type[object] \\| None = None,
        validate_on_init: bool \\| None = None,
        kw_only: bool = ...,
        slots: bool = ...,
    ) -> type[PydanticDataclass]: ...

else:

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool \\| None = None,
        config: ConfigDict \\| type[object] \\| None = None,
        validate_on_init: bool \\| None = None,
    ) -> Callable[[type[_T]], type[PydanticDataclass]]:  # type: ignore
        ...

    @dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
    @overload
    def dataclass(
        _cls: type[_T],  # type: ignore
        *,
        init: Literal[False] = False,
        repr: bool = True,
        eq: bool = True,
        order: bool = False,
        unsafe_hash: bool = False,
        frozen: bool \\| None = None,
        config: ConfigDict \\| type[object] \\| None = None,
        validate_on_init: bool \\| None = None,
    ) -> type[PydanticDataclass]: ...


@dataclass_transform(field_specifiers=(dataclasses.field, Field, PrivateAttr))
def dataclass(
    _cls: type[_T] \\| None = None,
    *,
    init: Literal[False] = False,
    repr: bool = True,
    eq: bool = True,
    order: bool = False,
    unsafe_hash: bool = False,
    frozen: bool \\| None = None,
    config: ConfigDict \\| type[object] \\| None = None,
    validate_on_init: bool \\| None = None,
    kw_only: bool = False,
    slots: bool = False,
) -> Callable[[type[_T]], type[PydanticDataclass]] \\| type[PydanticDataclass]: | , __future__, dataclasses, functools, sys, types, typing, typing_extensions, warnings | L307: # TODO `parent_namespace` is currently None, but we could do the same thing as Pydantic models: |
| `blackboard-agent/venv/Lib/site-packages/pydantic/datetime_parse.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `datetime_parse` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/decorator.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `decorator` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/class_validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Old `@validator` and `@root_validator` function validators from V1."""

from __future__ import annotations as _annotations

from functools import partial, partialmethod
from types import FunctionType
from typing import TYPE_CHECKING, Any, Callable, Literal, TypeVar, Union, overload
from warnings import warn

from typing_extensions import Protocol, TypeAlias, deprecated

from .._internal import _decorators, _decorators_v1
from ..errors import PydanticUserError
from ..warnings import PydanticDeprecatedSince20

_ALLOW_REUSE_WARNING_MESSAGE = '`allow_reuse` is deprecated and will be ignored; it should no longer be necessary'


if TYPE_CHECKING:

    class _OnlyValueValidatorClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any) -> Any: ...

    class _V1ValidatorWithValuesClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any, values: dict[str, Any]) -> Any: ...

    class _V1ValidatorWithValuesKwOnlyClsMethod(Protocol):
        def __call__(self, __cls: Any, __value: Any, *, values: dict[str, Any]) -> Any: ...

    class _V1ValidatorWithKwargsClsMethod(Protocol):
        def __call__(self, __cls: Any, **kwargs: Any) -> Any: ...

    class _V1ValidatorWithValuesAndKwargsClsMethod(Protocol):
        def __call__(self, __cls: Any, values: dict[str, Any], **kwargs: Any) -> Any: ...

    class _V1RootValidatorClsMethod(Protocol):
        def __call__(
            self, __cls: Any, __values: _decorators_v1.RootValidatorValues
        ) -> _decorators_v1.RootValidatorValues: ...

    V1Validator = Union[
        _OnlyValueValidatorClsMethod,
        _V1ValidatorWithValuesClsMethod,
        _V1ValidatorWithValuesKwOnlyClsMethod,
        _V1ValidatorWithKwargsClsMethod,
        _V1ValidatorWithValuesAndKwargsClsMethod,
        _decorators_v1.V1ValidatorWithValues,
        _decorators_v1.V1ValidatorWithValuesKwOnly,
        _decorators_v1.V1ValidatorWithKwargs,
        _decorators_v1.V1ValidatorWithValuesAndKwargs,
    ]

    V1RootValidator = Union[
        _V1RootValidatorClsMethod,
        _decorators_v1.V1RootValidatorFunction,
    ]

    _PartialClsOrStaticMethod: TypeAlias = Union[classmethod[Any, Any, Any], staticmethod[Any, Any], partialmethod[Any]]

    # Allow both a V1 (assumed pre=False) or V2 (assumed mode='after') validator
    # We lie to type checkers and say we return the same thing we get
    # but in reality we return a proxy object that _mostly_ behaves like the wrapped thing
    _V1ValidatorType = TypeVar('_V1ValidatorType', V1Validator, _PartialClsOrStaticMethod)
    _V1RootValidatorFunctionType = TypeVar(
        '_V1RootValidatorFunctionType',
        _decorators_v1.V1RootValidatorFunction,
        _V1RootValidatorClsMethod,
        _PartialClsOrStaticMethod,
    )
else:
    # See PyCharm issues https://youtrack.jetbrains.com/issue/PY-21915
    # and https://youtrack.jetbrains.com/issue/PY-51428
    DeprecationWarning = PydanticDeprecatedSince20


@deprecated(
    'Pydantic V1 style `@validator` validators are deprecated.'
    ' You should migrate to Pydantic V2 style `@field_validator` validators,'
    ' see the migration guide for more details',
    category=None,
)
def validator(
    __field: str,
    *fields: str,
    pre: bool = False,
    each_item: bool = False,
    always: bool = False,
    check_fields: bool \\| None = None,
    allow_reuse: bool = False,
) -> Callable[[_V1ValidatorType], _V1ValidatorType]: | , __future__, functools, types, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/config.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This class is only retained for backwards compatibility.

    !!! Warning "Deprecated"
        BaseConfig is deprecated. Use the [`pydantic.ConfigDict`][pydantic.ConfigDict] instead. | , __future__, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/copy_internals.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, copy, enum, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/decorator.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Decorator to validate the arguments passed to a function."""
    warnings.warn(
        'The `validate_arguments` method is deprecated; use `validate_call` instead.',
        PydanticDeprecatedSince20,
        stacklevel=2,
    )

    def validate(_func: 'AnyCallable') -> 'AnyCallable':
        vd = ValidatedFunction(_func, config)

        @wraps(_func)
        def wrapper_function(*args: Any, **kwargs: Any) -> Any:
            return vd.call(*args, **kwargs)

        wrapper_function.vd = vd  # type: ignore
        wrapper_function.validate = vd.init_model_instance  # type: ignore
        wrapper_function.raw_function = vd.raw_function  # type: ignore
        wrapper_function.model = vd.model  # type: ignore
        return wrapper_function

    if func:
        return validate(func)
    else:
        return validate


ALT_V_ARGS = 'v__args'
ALT_V_KWARGS = 'v__kwargs'
V_POSITIONAL_ONLY_NAME = 'v__positional_only'
V_DUPLICATE_KWARGS = 'v__duplicate_kwargs'


class ValidatedFunction:
    def __init__(self, function: 'AnyCallable', config: 'ConfigType'):
        from inspect import Parameter, signature

        parameters: Mapping[str, Parameter] = signature(function).parameters

        if parameters.keys() & {ALT_V_ARGS, ALT_V_KWARGS, V_POSITIONAL_ONLY_NAME, V_DUPLICATE_KWARGS}:
            raise PydanticUserError(
                f'"{ALT_V_ARGS}", "{ALT_V_KWARGS}", "{V_POSITIONAL_ONLY_NAME}" and "{V_DUPLICATE_KWARGS}" '
                f'are not permitted as argument names when using the "{validate_arguments.__name__}" decorator',
                code=None,
            )

        self.raw_function = function
        self.arg_mapping: dict[int, str] = {}
        self.positional_only_args: set[str] = set()
        self.v_args_name = 'args'
        self.v_kwargs_name = 'kwargs'

        type_hints = _typing_extra.get_type_hints(function, include_extras=True)
        takes_args = False
        takes_kwargs = False
        fields: dict[str, tuple[Any, Any]] = {}
        for i, (name, p) in enumerate(parameters.items()):
            if p.annotation is p.empty:
                annotation = Any
            else:
                annotation = type_hints[name]

            default = ... if p.default is p.empty else p.default
            if p.kind == Parameter.POSITIONAL_ONLY:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
                fields[V_POSITIONAL_ONLY_NAME] = list[str], None
                self.positional_only_args.add(name)
            elif p.kind == Parameter.POSITIONAL_OR_KEYWORD:
                self.arg_mapping[i] = name
                fields[name] = annotation, default
                fields[V_DUPLICATE_KWARGS] = list[str], None
            elif p.kind == Parameter.KEYWORD_ONLY:
                fields[name] = annotation, default
            elif p.kind == Parameter.VAR_POSITIONAL:
                self.v_args_name = name
                fields[name] = tuple[annotation, ...], None
                takes_args = True
            else:
                assert p.kind == Parameter.VAR_KEYWORD, p.kind
                self.v_kwargs_name = name
                fields[name] = dict[str, annotation], None
                takes_kwargs = True

        # these checks avoid a clash between "args" and a field with that name
        if not takes_args and self.v_args_name in fields:
            self.v_args_name = ALT_V_ARGS

        # same with "kwargs"
        if not takes_kwargs and self.v_kwargs_name in fields:
            self.v_kwargs_name = ALT_V_KWARGS

        if not takes_args:
            # we add the field so validation below can raise the correct exception
            fields[self.v_args_name] = list[Any], None

        if not takes_kwargs:
            # same with kwargs
            fields[self.v_kwargs_name] = dict[Any, Any], None

        self.create_model(fields, takes_args, takes_kwargs, config)

    def init_model_instance(self, *args: Any, **kwargs: Any) -> BaseModel:
        values = self.build_values(args, kwargs)
        return self.model(**values)

    def call(self, *args: Any, **kwargs: Any) -> Any:
        m = self.init_model_instance(*args, **kwargs)
        return self.execute(m)

    def build_values(self, args: tuple[Any, ...], kwargs: dict[str, Any]) -> dict[str, Any]:
        values: dict[str, Any] = {}
        if args:
            arg_iter = enumerate(args)
            while True:
                try:
                    i, a = next(arg_iter)
                except StopIteration:
                    break
                arg_name = self.arg_mapping.get(i)
                if arg_name is not None:
                    values[arg_name] = a
                else:
                    values[self.v_args_name] = [a] + [a for _, a in arg_iter]
                    break

        var_kwargs: dict[str, Any] = {}
        wrong_positional_args = []
        duplicate_kwargs = []
        fields_alias = [
            field.alias
            for name, field in self.model.__pydantic_fields__.items()
            if name not in (self.v_args_name, self.v_kwargs_name)
        ]
        non_var_fields = set(self.model.__pydantic_fields__) - {self.v_args_name, self.v_kwargs_name}
        for k, v in kwargs.items():
            if k in non_var_fields or k in fields_alias:
                if k in self.positional_only_args:
                    wrong_positional_args.append(k)
                if k in values:
                    duplicate_kwargs.append(k)
                values[k] = v
            else:
                var_kwargs[k] = v

        if var_kwargs:
            values[self.v_kwargs_name] = var_kwargs
        if wrong_positional_args:
            values[V_POSITIONAL_ONLY_NAME] = wrong_positional_args
        if duplicate_kwargs:
            values[V_DUPLICATE_KWARGS] = duplicate_kwargs
        return values

    def execute(self, m: BaseModel) -> Any:
        d = {
            k: v
            for k, v in m.__dict__.items()
            if k in m.__pydantic_fields_set__ or m.__pydantic_fields__[k].default_factory
        }
        var_kwargs = d.pop(self.v_kwargs_name, {})

        if self.v_args_name in d:
            args_: list[Any] = []
            in_kwargs = False
            kwargs = {}
            for name, value in d.items():
                if in_kwargs:
                    kwargs[name] = value
                elif name == self.v_args_name:
                    args_ += value
                    in_kwargs = True
                else:
                    args_.append(value)
            return self.raw_function(*args_, **kwargs, **var_kwargs)
        elif self.positional_only_args:
            args_ = []
            kwargs = {}
            for name, value in d.items():
                if name in self.positional_only_args:
                    args_.append(value)
                else:
                    kwargs[name] = value
            return self.raw_function(*args_, **kwargs, **var_kwargs)
        else:
            return self.raw_function(**d, **var_kwargs)

    def create_model(self, fields: dict[str, Any], takes_args: bool, takes_kwargs: bool, config: 'ConfigType') -> None:
        pos_args = len(self.arg_mapping)

        config_wrapper = _config.ConfigWrapper(config)

        if config_wrapper.alias_generator:
            raise PydanticUserError(
                'Setting the "alias_generator" property on custom Config for '
                '@validate_arguments is not yet supported, please remove.',
                code=None,
            )
        if config_wrapper.extra is None:
            config_wrapper.config_dict['extra'] = 'forbid'

        class DecoratorBaseModel(BaseModel):
            @field_validator(self.v_args_name, check_fields=False)
            @classmethod
            def check_args(cls, v: Optional[list[Any]]) -> Optional[list[Any]]:
                if takes_args or v is None:
                    return v

                raise TypeError(f'{pos_args} positional arguments expected but {pos_args + len(v)} given')

            @field_validator(self.v_kwargs_name, check_fields=False)
            @classmethod
            def check_kwargs(cls, v: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
                if takes_kwargs or v is None:
                    return v

                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v.keys()))
                raise TypeError(f'unexpected keyword argument{plural}: {keys}')

            @field_validator(V_POSITIONAL_ONLY_NAME, check_fields=False)
            @classmethod
            def check_positional_only(cls, v: Optional[list[str]]) -> None:
                if v is None:
                    return

                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v))
                raise TypeError(f'positional-only argument{plural} passed as keyword argument{plural}: {keys}')

            @field_validator(V_DUPLICATE_KWARGS, check_fields=False)
            @classmethod
            def check_duplicate_kwargs(cls, v: Optional[list[str]]) -> None:
                if v is None:
                    return

                plural = '' if len(v) == 1 else 's'
                keys = ', '.join(map(repr, v))
                raise TypeError(f'multiple values for argument{plural}: {keys}')

            model_config = config_wrapper.config_dict

        self.model = create_model(to_pascal(self.raw_function.__name__), __base__=DecoratorBaseModel, **fields) | , collections, functools, inspect, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/json.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Encodes a Decimal as int of there's no exponent, otherwise float.

    This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    where a integer (but not int typed) is used. Encoding this as a float
    results in failed round-tripping between encode and parse.
    Our Id type is a prime example of this.

    >>> decimal_encoder(Decimal("1.0"))
    1.0

    >>> decimal_encoder(Decimal("1"))
    1 | , collections, dataclasses, datetime, decimal, enum, ipaddress, pathlib, re, types, typing, typing_extensions, uuid, warnings | L112: # TODO: Add a suggested migration path once there is a way to use custom encoders |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/parse.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , __future__, enum, json, pathlib, pickle, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/deprecated/tools.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Generate a JSON schema (as dict) for the passed model or dynamically generated one."""
    warnings.warn(
        '`schema_of` is deprecated. Use `pydantic.TypeAdapter.json_schema` instead.',
        category=PydanticDeprecatedSince20,
        stacklevel=2,
    )
    res = TypeAdapter(type_).json_schema(
        by_alias=by_alias,
        schema_generator=schema_generator,
        ref_template=ref_template,
    )
    if title is not None:
        if isinstance(title, str):
            res['title'] = title
        else:
            warnings.warn(
                'Passing a callable for the `title` parameter is deprecated and no longer supported',
                DeprecationWarning,
                stacklevel=2,
            )
            res['title'] = title(type_)
    return res


@deprecated(
    '`schema_json_of` is deprecated. Use `pydantic.TypeAdapter.json_schema` instead.',
    category=None,
)
def schema_json_of(
    type_: Any,
    *,
    title: NameFactory \\| None = None,
    by_alias: bool = True,
    ref_template: str = DEFAULT_REF_TEMPLATE,
    schema_generator: type[GenerateJsonSchema] = GenerateJsonSchema,
    **dumps_kwargs: Any,
) -> str: | , __future__, json, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/env_settings.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `env_settings` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/error_wrappers.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `error_wrappers` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/errors.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Pydantic-specific errors."""

from __future__ import annotations as _annotations

import re
from typing import Any, ClassVar, Literal

from typing_extensions import Self
from typing_inspection.introspection import Qualifier

from pydantic._internal import _repr

from ._migration import getattr_migration
from .version import version_short

__all__ = (
    'PydanticUserError',
    'PydanticUndefinedAnnotation',
    'PydanticImportError',
    'PydanticSchemaGenerationError',
    'PydanticInvalidForJsonSchema',
    'PydanticForbiddenQualifier',
    'PydanticErrorCodes',
)

# We use this URL to allow for future flexibility about how we host the docs, while allowing for Pydantic
# code in the while with "old" URLs to still work.
# 'u' refers to "user errors" - e.g. errors caused by developers using pydantic, as opposed to validation errors.
DEV_ERROR_DOCS_URL = f'https://errors.pydantic.dev/{version_short()}/u/'
PydanticErrorCodes = Literal[
    'class-not-fully-defined',
    'custom-json-schema',
    'decorator-missing-field',
    'discriminator-no-field',
    'discriminator-alias-type',
    'discriminator-needs-literal',
    'discriminator-alias',
    'discriminator-validator',
    'callable-discriminator-no-tag',
    'typed-dict-version',
    'model-field-overridden',
    'model-field-missing-annotation',
    'config-both',
    'removed-kwargs',
    'circular-reference-schema',
    'invalid-for-json-schema',
    'json-schema-already-used',
    'base-model-instantiated',
    'undefined-annotation',
    'schema-for-unknown-type',
    'import-error',
    'create-model-field-definitions',
    'validator-no-fields',
    'validator-invalid-fields',
    'validator-instance-method',
    'validator-input-type',
    'root-validator-pre-skip',
    'model-serializer-instance-method',
    'validator-field-config-info',
    'validator-v1-signature',
    'validator-signature',
    'field-serializer-signature',
    'model-serializer-signature',
    'multiple-field-serializers',
    'invalid-annotated-type',
    'type-adapter-config-unused',
    'root-model-extra',
    'unevaluable-type-annotation',
    'dataclass-init-false-extra-allow',
    'clashing-init-and-init-var',
    'model-config-invalid-field-name',
    'with-config-on-model',
    'dataclass-on-model',
    'validate-call-type',
    'unpack-typed-dict',
    'overlapping-unpack-typed-dict',
    'invalid-self-type',
    'validate-by-alias-and-name-false',
]


class PydanticErrorMixin: | , __future__, pydantic, re, typing, typing_extensions, typing_inspection |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/experimental/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The "experimental" module of pydantic contains potential new features that are subject to change.""" |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/experimental/arguments_schema.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Experimental module exposing a function to generate a core schema that validates callable arguments."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic_core import CoreSchema

from pydantic import ConfigDict
from pydantic._internal import _config, _generate_schema, _namespace_utils


def generate_arguments_schema(
    func: Callable[..., Any],
    schema_type: Literal['arguments', 'arguments-v3'] = 'arguments-v3',
    parameters_callback: Callable[[int, str, Any], Literal['skip'] \\| None] \\| None = None,
    config: ConfigDict \\| None = None,
) -> CoreSchema: | __future__, collections, pydantic, pydantic_core, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/experimental/missing_sentinel.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Experimental module exposing a function a `MISSING` sentinel."""

from pydantic_core import MISSING

__all__ = ('MISSING',) | pydantic_core |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/experimental/pipeline.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Experimental pipeline API functionality. Be careful with this API, it's subject to change."""

from __future__ import annotations

import datetime
import operator
import re
import sys
from collections import deque
from collections.abc import Container
from dataclasses import dataclass
from decimal import Decimal
from functools import cached_property, partial
from re import Pattern
from typing import TYPE_CHECKING, Annotated, Any, Callable, Generic, Protocol, TypeVar, Union, overload

import annotated_types

if TYPE_CHECKING:
    from pydantic import GetCoreSchemaHandler

from pydantic_core import PydanticCustomError
from pydantic_core import core_schema as cs

from pydantic import Strict
from pydantic._internal._internal_dataclass import slots_true as _slots_true

if sys.version_info < (3, 10):
    EllipsisType = type(Ellipsis)
else:
    from types import EllipsisType

__all__ = ['validate_as', 'validate_as_deferred', 'transform']

_slots_frozen = {**_slots_true, 'frozen': True}


@dataclass(**_slots_frozen)
class _ValidateAs:
    tp: type[Any]
    strict: bool = False


@dataclass
class _ValidateAsDefer:
    func: Callable[[], type[Any]]

    @cached_property
    def tp(self) -> type[Any]:
        return self.func()


@dataclass(**_slots_frozen)
class _Transform:
    func: Callable[[Any], Any]


@dataclass(**_slots_frozen)
class _PipelineOr:
    left: _Pipeline[Any, Any]
    right: _Pipeline[Any, Any]


@dataclass(**_slots_frozen)
class _PipelineAnd:
    left: _Pipeline[Any, Any]
    right: _Pipeline[Any, Any]


@dataclass(**_slots_frozen)
class _Eq:
    value: Any


@dataclass(**_slots_frozen)
class _NotEq:
    value: Any


@dataclass(**_slots_frozen)
class _In:
    values: Container[Any]


@dataclass(**_slots_frozen)
class _NotIn:
    values: Container[Any]


_ConstraintAnnotation = Union[
    annotated_types.Le,
    annotated_types.Ge,
    annotated_types.Lt,
    annotated_types.Gt,
    annotated_types.Len,
    annotated_types.MultipleOf,
    annotated_types.Timezone,
    annotated_types.Interval,
    annotated_types.Predicate,
    # common predicates not included in annotated_types
    _Eq,
    _NotEq,
    _In,
    _NotIn,
    # regular expressions
    Pattern[str],
]


@dataclass(**_slots_frozen)
class _Constraint:
    constraint: _ConstraintAnnotation


_Step = Union[_ValidateAs, _ValidateAsDefer, _Transform, _PipelineOr, _PipelineAnd, _Constraint]

_InT = TypeVar('_InT')
_OutT = TypeVar('_OutT')
_NewOutT = TypeVar('_NewOutT')


class _FieldTypeMarker:
    pass


# TODO: ultimately, make this public, see https://github.com/pydantic/pydantic/pull/9459#discussion_r1628197626
# Also, make this frozen eventually, but that doesn't work right now because of the generic base
# Which attempts to modify __orig_base__ and such.
# We could go with a manual freeze, but that seems overkill for now.
@dataclass(**_slots_true)
class _Pipeline(Generic[_InT, _OutT]): | __future__, annotated_types, collections, dataclasses, datetime, decimal, functools, operator, pydantic, pydantic_core, re, sys, types, typing | L126: # TODO: ultimately, make this public, see https://github.com/pydantic/pydantic/pull/9459#discussion_r1628197626 |
| `blackboard-agent/venv/Lib/site-packages/pydantic/fields.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Defining fields on models."""

from __future__ import annotations as _annotations

import dataclasses
import inspect
import re
import sys
from collections.abc import Callable, Mapping
from copy import copy
from dataclasses import Field as DataclassField
from functools import cached_property
from typing import TYPE_CHECKING, Annotated, Any, ClassVar, Literal, TypeVar, cast, final, overload
from warnings import warn

import annotated_types
import typing_extensions
from pydantic_core import MISSING, PydanticUndefined
from typing_extensions import Self, TypeAlias, TypedDict, Unpack, deprecated
from typing_inspection import typing_objects
from typing_inspection.introspection import UNKNOWN, AnnotationSource, ForbiddenQualifier, Qualifier, inspect_annotation

from . import types
from ._internal import _decorators, _fields, _generics, _internal_dataclass, _repr, _typing_extra, _utils
from ._internal._namespace_utils import GlobalsNamespace, MappingNamespace
from .aliases import AliasChoices, AliasGenerator, AliasPath
from .config import JsonDict
from .errors import PydanticForbiddenQualifier, PydanticUserError
from .json_schema import PydanticJsonSchemaWarning
from .warnings import PydanticDeprecatedSince20

if TYPE_CHECKING:
    from ._internal._config import ConfigWrapper
    from ._internal._repr import ReprArgs


__all__ = 'Field', 'FieldInfo', 'PrivateAttr', 'computed_field'


_Unset: Any = PydanticUndefined

if sys.version_info >= (3, 13):
    import warnings

    Deprecated: TypeAlias = warnings.deprecated \\| deprecated
else:
    Deprecated: TypeAlias = deprecated


class _FromFieldInfoInputs(TypedDict, total=False): | , __future__, annotated_types, collections, copy, dataclasses, functools, inspect, pydantic_core, re, sys, typing, typing_extensions, typing_inspection, warnings | L53: # TODO PEP 747: use TypeForm:
L99: # TODO PEP 747: use TypeForm:
L151: # TODO PEP 747: use TypeForm:
L361: # TODO check for classvar and error?
L422: # TODO check for classvar and error?
L424: # TODO infer from the default, this can be done in v3 once we treat final fields with
L430: # HACK 1: the order in which the metadata is merged is inconsistent; we need to prepend
L438: # HACK 2: FastAPI is subclassing `FieldInfo` and historically expected the actual
L449: default_copy = default._copy()  # Copy unnecessary when we remove HACK 1.
L455: prepend_metadata = from_field.metadata  # Unnecessary when we remove HACK 1. |
| `blackboard-agent/venv/Lib/site-packages/pydantic/functional_serializers.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This module contains related classes and functions for serialization."""

from __future__ import annotations

import dataclasses
from functools import partial, partialmethod
from typing import TYPE_CHECKING, Annotated, Any, Callable, Literal, TypeVar, overload

from pydantic_core import PydanticUndefined, core_schema
from pydantic_core.core_schema import SerializationInfo, SerializerFunctionWrapHandler, WhenUsed
from typing_extensions import TypeAlias

from . import PydanticUndefinedAnnotation
from ._internal import _decorators, _internal_dataclass
from .annotated_handlers import GetCoreSchemaHandler


@dataclasses.dataclass(**_internal_dataclass.slots_true, frozen=True)
class PlainSerializer: | , __future__, dataclasses, datetime, functools, pydantic, pydantic_core, typing, typing_extensions | L234: # TODO PEP 747 (grep for 'return_type' on the whole code base): |
| `blackboard-agent/venv/Lib/site-packages/pydantic/functional_validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This module contains related classes and functions for validation."""

from __future__ import annotations as _annotations

import dataclasses
import sys
import warnings
from functools import partialmethod
from types import FunctionType
from typing import TYPE_CHECKING, Annotated, Any, Callable, Literal, TypeVar, Union, cast, overload

from pydantic_core import PydanticUndefined, core_schema
from typing_extensions import Self, TypeAlias

from ._internal import _decorators, _generics, _internal_dataclass
from .annotated_handlers import GetCoreSchemaHandler
from .errors import PydanticUserError
from .version import version_short
from .warnings import ArbitraryTypeWarning, PydanticDeprecatedSince212

if sys.version_info < (3, 11):
    from typing_extensions import Protocol
else:
    from typing import Protocol

_inspect_validator = _decorators.inspect_validator


@dataclasses.dataclass(frozen=True, **_internal_dataclass.slots_true)
class AfterValidator: | , __future__, dataclasses, datetime, functools, pydantic, pydantic_core, sys, types, typing, typing_extensions, warnings | L218: # TODO if `schema['serialization']` is one of `'include-exclude-dict/sequence', |
| `blackboard-agent/venv/Lib/site-packages/pydantic/generics.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `generics` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/json.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `json` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/json_schema.py` | ❓ UNKNOWN | 2025-11-09 21:03 | !!! abstract "Usage Documentation"
    [JSON Schema](../concepts/json_schema.md)

The `json_schema` module contains classes and functions to allow the way [JSON Schema](https://json-schema.org/)
is generated to be customized.

In general you shouldn't need to use this module directly; instead, you can use
[`BaseModel.model_json_schema`][pydantic.BaseModel.model_json_schema] and
[`TypeAdapter.json_schema`][pydantic.TypeAdapter.json_schema]. | , __future__, collections, copy, dataclasses, enum, inspect, math, os, pydantic, pydantic_core, re, typing, typing_extensions, typing_inspection, warnings | L158: for _iter in range(100):  # prevent an infinite loop in the case of a bug, 100 iterations should be enough
L452: TODO: the nested function definitions here seem like bad practice, I'd like to unpack these |
| `blackboard-agent/venv/Lib/site-packages/pydantic/main.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Logic for creating models."""

# Because `dict` is in the local namespace of the `BaseModel` class, we use `Dict` for annotations.
# TODO v3 fallback to `dict` when the deprecated `dict` method gets removed.
# ruff: noqa: UP035

from __future__ import annotations as _annotations

import operator
import sys
import types
import warnings
from collections.abc import Generator, Mapping
from copy import copy, deepcopy
from functools import cached_property
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Dict,
    Generic,
    Literal,
    TypeVar,
    Union,
    cast,
    overload,
)

import pydantic_core
import typing_extensions
from pydantic_core import PydanticUndefined, ValidationError
from typing_extensions import Self, TypeAlias, Unpack

from . import PydanticDeprecatedSince20, PydanticDeprecatedSince211
from ._internal import (
    _config,
    _decorators,
    _fields,
    _forward_ref,
    _generics,
    _mock_val_ser,
    _model_construction,
    _namespace_utils,
    _repr,
    _typing_extra,
    _utils,
)
from ._migration import getattr_migration
from .aliases import AliasChoices, AliasPath
from .annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from .config import ConfigDict, ExtraValues
from .errors import PydanticUndefinedAnnotation, PydanticUserError
from .json_schema import DEFAULT_REF_TEMPLATE, GenerateJsonSchema, JsonSchemaMode, JsonSchemaValue, model_json_schema
from .plugin._schema_validator import PluggableSchemaValidator

if TYPE_CHECKING:
    from inspect import Signature
    from pathlib import Path

    from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator

    from ._internal._namespace_utils import MappingNamespace
    from ._internal._utils import AbstractSetIntStr, MappingIntStrAny
    from .deprecated.parse import Protocol as DeprecatedParseProtocol
    from .fields import ComputedFieldInfo, FieldInfo, ModelPrivateAttr


__all__ = 'BaseModel', 'create_model'

# Keep these type aliases available at runtime:
TupleGenerator: TypeAlias = Generator[tuple[str, Any], None, None]
# NOTE: In reality, `bool` should be replaced by `Literal[True]` but mypy fails to correctly apply bidirectional
# type inference (e.g. when using `{'a': {'b': True}}`):
# NOTE: Keep this type alias in sync with the stub definition in `pydantic-core`:
IncEx: TypeAlias = Union[set[int], set[str], Mapping[int, Union['IncEx', bool]], Mapping[str, Union['IncEx', bool]]]

_object_setattr = _model_construction.object_setattr


def _check_frozen(model_cls: type[BaseModel], name: str, value: Any) -> None:
    if model_cls.model_config.get('frozen'):
        error_type = 'frozen_instance'
    elif getattr(model_cls.__pydantic_fields__.get(name), 'frozen', False):
        error_type = 'frozen_field'
    else:
        return

    raise ValidationError.from_exception_data(
        model_cls.__name__, [{'type': error_type, 'loc': (name,), 'input': value}]
    )


def _model_field_setattr_handler(model: BaseModel, name: str, val: Any) -> None:
    model.__dict__[name] = val
    model.__pydantic_fields_set__.add(name)


def _private_setattr_handler(model: BaseModel, name: str, val: Any) -> None:
    if getattr(model, '__pydantic_private__', None) is None:
        # While the attribute should be present at this point, this may not be the case if
        # users do unusual stuff with `model_post_init()` (which is where the  `__pydantic_private__`
        # is initialized, by wrapping the user-defined `model_post_init()`), e.g. if they mock
        # the `model_post_init()` call. Ideally we should find a better way to init private attrs.
        object.__setattr__(model, '__pydantic_private__', {})
    model.__pydantic_private__[name] = val  # pyright: ignore[reportOptionalSubscript]


_SIMPLE_SETATTR_HANDLERS: Mapping[str, Callable[[BaseModel, str, Any], None]] = {
    'model_field': _model_field_setattr_handler,
    'validate_assignment': lambda model, name, val: model.__pydantic_validator__.validate_assignment(model, name, val),  # pyright: ignore[reportAssignmentType]
    'private': _private_setattr_handler,
    'cached_property': lambda model, name, val: model.__dict__.__setitem__(name, val),
    'extra_known': lambda model, name, val: _object_setattr(model, name, val),
}


class BaseModel(metaclass=_model_construction.ModelMetaclass): | , __future__, collections, copy, functools, inspect, operator, pathlib, pydantic_core, sys, types, typing, typing_extensions, warnings | L4: # TODO v3 fallback to `dict` when the deprecated `dict` method gets removed. |
| `blackboard-agent/venv/Lib/site-packages/pydantic/mypy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This module includes classes and functions designed specifically for use with the mypy plugin."""

from __future__ import annotations

import sys
from collections.abc import Iterator
from configparser import ConfigParser
from typing import Any, Callable

from mypy.errorcodes import ErrorCode
from mypy.expandtype import expand_type, expand_type_by_instance
from mypy.nodes import (
    ARG_NAMED,
    ARG_NAMED_OPT,
    ARG_OPT,
    ARG_POS,
    ARG_STAR2,
    INVARIANT,
    MDEF,
    Argument,
    AssignmentStmt,
    Block,
    CallExpr,
    ClassDef,
    Context,
    Decorator,
    DictExpr,
    EllipsisExpr,
    Expression,
    FuncDef,
    IfStmt,
    JsonDict,
    MemberExpr,
    NameExpr,
    PassStmt,
    PlaceholderNode,
    RefExpr,
    Statement,
    StrExpr,
    SymbolTableNode,
    TempNode,
    TypeAlias,
    TypeInfo,
    Var,
)
from mypy.options import Options
from mypy.plugin import (
    CheckerPluginInterface,
    ClassDefContext,
    MethodContext,
    Plugin,
    ReportConfigContext,
    SemanticAnalyzerPluginInterface,
)
from mypy.plugins.common import (
    deserialize_and_fixup_type,
)
from mypy.semanal import set_callable_name
from mypy.server.trigger import make_wildcard_trigger
from mypy.state import state
from mypy.type_visitor import TypeTranslator
from mypy.typeops import map_type_from_supertype
from mypy.types import (
    AnyType,
    CallableType,
    Instance,
    NoneType,
    Type,
    TypeOfAny,
    TypeType,
    TypeVarType,
    UnionType,
    get_proper_type,
)
from mypy.typevars import fill_typevars
from mypy.util import get_unique_redefinition_name
from mypy.version import __version__ as mypy_version

from pydantic._internal import _fields
from pydantic.version import parse_mypy_version

CONFIGFILE_KEY = 'pydantic-mypy'
METADATA_KEY = 'pydantic-mypy-metadata'
BASEMODEL_FULLNAME = 'pydantic.main.BaseModel'
BASESETTINGS_FULLNAME = 'pydantic_settings.main.BaseSettings'
ROOT_MODEL_FULLNAME = 'pydantic.root_model.RootModel'
MODEL_METACLASS_FULLNAME = 'pydantic._internal._model_construction.ModelMetaclass'
FIELD_FULLNAME = 'pydantic.fields.Field'
DATACLASS_FULLNAME = 'pydantic.dataclasses.dataclass'
MODEL_VALIDATOR_FULLNAME = 'pydantic.functional_validators.model_validator'
DECORATOR_FULLNAMES = {
    'pydantic.functional_validators.field_validator',
    'pydantic.functional_validators.model_validator',
    'pydantic.functional_serializers.serializer',
    'pydantic.functional_serializers.model_serializer',
    'pydantic.deprecated.class_validators.validator',
    'pydantic.deprecated.class_validators.root_validator',
}
IMPLICIT_CLASSMETHOD_DECORATOR_FULLNAMES = DECORATOR_FULLNAMES - {'pydantic.functional_serializers.model_serializer'}


MYPY_VERSION_TUPLE = parse_mypy_version(mypy_version)
BUILTINS_NAME = 'builtins'

# Increment version if plugin changes and mypy caches should be invalidated
__version__ = 2


def plugin(version: str) -> type[Plugin]: | __future__, collections, configparser, mypy, pydantic, sys, typing | L168: if 'debug_dataclass_transform' is set to True', for testing purposes.
L170: if self.plugin_config.debug_dataclass_transform:
L185: debug_dataclass_transform: Whether to not reset `dataclass_transform_spec` attribute
L193: 'debug_dataclass_transform',
L198: debug_dataclass_transform: bool  # undocumented |
| `blackboard-agent/venv/Lib/site-packages/pydantic/networks.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The networks module contains types for common network-related fields."""

from __future__ import annotations as _annotations

import dataclasses as _dataclasses
import re
from dataclasses import fields
from functools import lru_cache
from importlib.metadata import version
from ipaddress import IPv4Address, IPv4Interface, IPv4Network, IPv6Address, IPv6Interface, IPv6Network
from typing import TYPE_CHECKING, Annotated, Any, ClassVar

from pydantic_core import (
    MultiHostHost,
    PydanticCustomError,
    PydanticSerializationUnexpectedValue,
    SchemaSerializer,
    core_schema,
)
from pydantic_core import MultiHostUrl as _CoreMultiHostUrl
from pydantic_core import Url as _CoreUrl
from typing_extensions import Self, TypeAlias

from pydantic.errors import PydanticUserError

from ._internal import _repr, _schema_generation_shared
from ._migration import getattr_migration
from .annotated_handlers import GetCoreSchemaHandler
from .json_schema import JsonSchemaValue
from .type_adapter import TypeAdapter

if TYPE_CHECKING:
    import email_validator

    NetworkType: TypeAlias = 'str \\| bytes \\| int \\| tuple[str \\| bytes \\| int, str \\| int]'

else:
    email_validator = None


__all__ = [
    'AnyUrl',
    'AnyHttpUrl',
    'FileUrl',
    'FtpUrl',
    'HttpUrl',
    'WebsocketUrl',
    'AnyWebsocketUrl',
    'UrlConstraints',
    'EmailStr',
    'NameEmail',
    'IPvAnyAddress',
    'IPvAnyInterface',
    'IPvAnyNetwork',
    'PostgresDsn',
    'CockroachDsn',
    'AmqpDsn',
    'RedisDsn',
    'MongoDsn',
    'KafkaDsn',
    'NatsDsn',
    'validate_email',
    'MySQLDsn',
    'MariaDBDsn',
    'ClickHouseDsn',
    'SnowflakeDsn',
]


@_dataclasses.dataclass
class UrlConstraints: | , __future__, dataclasses, email_validator, functools, importlib, ipaddress, pydantic, pydantic_core, re, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/parse.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `parse` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/plugin/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | !!! abstract "Usage Documentation"
    [Build a Plugin](../concepts/plugins.md#build-a-plugin)

Plugin interface for Pydantic plugins, and related types. | __future__, pydantic, pydantic_core, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/plugin/_loader.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Load plugins for Pydantic.

    Inspired by: https://github.com/pytest-dev/pluggy/blob/1.3.0/src/pluggy/_manager.py#L376-L402 | , __future__, collections, importlib, os, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/plugin/_schema_validator.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Pluggable schema validator for pydantic."""

from __future__ import annotations

import functools
from collections.abc import Iterable
from typing import TYPE_CHECKING, Any, Callable, Literal, TypeVar

from pydantic_core import CoreConfig, CoreSchema, SchemaValidator, ValidationError
from typing_extensions import ParamSpec

if TYPE_CHECKING:
    from . import BaseValidateHandlerProtocol, PydanticPluginProtocol, SchemaKind, SchemaTypePath


P = ParamSpec('P')
R = TypeVar('R')
Event = Literal['on_validate_python', 'on_validate_json', 'on_validate_strings']
events: list[Event] = list(Event.__args__)  # type: ignore


def create_schema_validator(
    schema: CoreSchema,
    schema_type: Any,
    schema_type_module: str,
    schema_type_name: str,
    schema_kind: SchemaKind,
    config: CoreConfig \\| None = None,
    plugin_settings: dict[str, Any] \\| None = None,
) -> SchemaValidator \\| PluggableSchemaValidator: | , __future__, collections, functools, pydantic_core, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/root_model.py` | ❓ UNKNOWN | 2025-11-09 21:03 | RootModel class and type definitions."""

from __future__ import annotations as _annotations

from copy import copy, deepcopy
from typing import TYPE_CHECKING, Any, Generic, Literal, TypeVar

from pydantic_core import PydanticUndefined
from typing_extensions import Self, dataclass_transform

from . import PydanticUserError
from ._internal import _model_construction, _repr
from .main import BaseModel, _object_setattr

if TYPE_CHECKING:
    from .fields import Field as PydanticModelField
    from .fields import PrivateAttr as PydanticModelPrivateAttr

    # dataclass_transform could be applied to RootModel directly, but `ModelMetaclass`'s dataclass_transform
    # takes priority (at least with pyright). We trick type checkers into thinking we apply dataclass_transform
    # on a new metaclass.
    @dataclass_transform(kw_only_default=False, field_specifiers=(PydanticModelField, PydanticModelPrivateAttr))
    class _RootModelMetaclass(_model_construction.ModelMetaclass): ...
else:
    _RootModelMetaclass = _model_construction.ModelMetaclass

__all__ = ('RootModel',)

RootModelRootType = TypeVar('RootModelRootType')


class RootModel(BaseModel, Generic[RootModelRootType], metaclass=_RootModelMetaclass): | , __future__, copy, pydantic_core, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/schema.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `schema` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/tools.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `tools` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/type_adapter.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Type adapter specification."""

from __future__ import annotations as _annotations

import sys
import types
from collections.abc import Callable, Iterable
from dataclasses import is_dataclass
from types import FrameType
from typing import (
    Any,
    Generic,
    Literal,
    TypeVar,
    cast,
    final,
    overload,
)

from pydantic_core import CoreSchema, SchemaSerializer, SchemaValidator, Some
from typing_extensions import ParamSpec, is_typeddict

from pydantic.errors import PydanticUserError
from pydantic.main import BaseModel, IncEx

from ._internal import _config, _generate_schema, _mock_val_ser, _namespace_utils, _repr, _typing_extra, _utils
from .config import ConfigDict, ExtraValues
from .errors import PydanticUndefinedAnnotation
from .json_schema import (
    DEFAULT_REF_TEMPLATE,
    GenerateJsonSchema,
    JsonSchemaKeyT,
    JsonSchemaMode,
    JsonSchemaValue,
)
from .plugin._schema_validator import PluggableSchemaValidator, create_schema_validator

T = TypeVar('T')
R = TypeVar('R')
P = ParamSpec('P')
TypeAdapterT = TypeVar('TypeAdapterT', bound='TypeAdapter')


def _getattr_no_parents(obj: Any, attribute: str) -> Any: | , __future__, a, collections, dataclasses, pydantic, pydantic_core, sys, types, typing, typing_extensions | L291: # TODO: we don't go through the rebuild logic here directly because we don't want |
| `blackboard-agent/venv/Lib/site-packages/pydantic/types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The types module contains custom types used by pydantic."""

from __future__ import annotations as _annotations

import base64
import dataclasses as _dataclasses
import re
from collections.abc import Hashable, Iterator
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from re import Pattern
from types import ModuleType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Callable,
    ClassVar,
    Generic,
    Literal,
    TypeVar,
    Union,
    cast,
)
from uuid import UUID

import annotated_types
from annotated_types import BaseMetadata, MaxLen, MinLen
from pydantic_core import CoreSchema, PydanticCustomError, SchemaSerializer, core_schema
from typing_extensions import Protocol, TypeAlias, TypeAliasType, deprecated, get_args, get_origin
from typing_inspection.introspection import is_union_origin

from ._internal import _fields, _internal_dataclass, _utils, _validators
from ._migration import getattr_migration
from .annotated_handlers import GetCoreSchemaHandler, GetJsonSchemaHandler
from .errors import PydanticUserError
from .json_schema import JsonSchemaValue
from .warnings import PydanticDeprecatedSince20

if TYPE_CHECKING:
    from ._internal._core_metadata import CoreMetadata

__all__ = (
    'Strict',
    'StrictStr',
    'SocketPath',
    'conbytes',
    'conlist',
    'conset',
    'confrozenset',
    'constr',
    'ImportString',
    'conint',
    'PositiveInt',
    'NegativeInt',
    'NonNegativeInt',
    'NonPositiveInt',
    'confloat',
    'PositiveFloat',
    'NegativeFloat',
    'NonNegativeFloat',
    'NonPositiveFloat',
    'FiniteFloat',
    'condecimal',
    'UUID1',
    'UUID3',
    'UUID4',
    'UUID5',
    'UUID6',
    'UUID7',
    'UUID8',
    'FilePath',
    'DirectoryPath',
    'NewPath',
    'Json',
    'Secret',
    'SecretStr',
    'SecretBytes',
    'StrictBool',
    'StrictBytes',
    'StrictInt',
    'StrictFloat',
    'PaymentCardNumber',
    'ByteSize',
    'PastDate',
    'FutureDate',
    'PastDatetime',
    'FutureDatetime',
    'condate',
    'AwareDatetime',
    'NaiveDatetime',
    'AllowInfNan',
    'EncoderProtocol',
    'EncodedBytes',
    'EncodedStr',
    'Base64Encoder',
    'Base64Bytes',
    'Base64Str',
    'Base64UrlBytes',
    'Base64UrlStr',
    'GetPydanticSchema',
    'StringConstraints',
    'Tag',
    'Discriminator',
    'JsonValue',
    'OnErrorOmit',
    'FailFast',
)


T = TypeVar('T')


@_dataclasses.dataclass
class Strict(_fields.PydanticMetadata, BaseMetadata): | , __future__, annotated_types, base64, collections, dataclasses, datetime, decimal, enum, pathlib, pydantic, pydantic_core, re, types, typing, typing_extensions, typing_inspection, uuid |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/typing.py` | ❓ UNKNOWN | 2025-11-09 21:03 | `typing` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `utils` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | pydantic, sys, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/_hypothesis_plugin.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Register Hypothesis strategies for Pydantic custom types.

This enables fully-automatic generation of test data for most Pydantic classes.

Note that this module has *no* runtime impact on Pydantic itself; instead it
is registered as a setuptools entry point and Hypothesis will import it if
Pydantic is installed.  See also:

https://hypothesis.readthedocs.io/en/latest/strategies.html#registering-strategies-via-setuptools-entry-points
https://hypothesis.readthedocs.io/en/latest/data.html#hypothesis.strategies.register_type_strategy
https://hypothesis.readthedocs.io/en/latest/strategies.html#interaction-with-pytest-cov
https://docs.pydantic.dev/usage/types/#pydantic-types

Note that because our motivation is to *improve user experience*, the strategies
are always sound (never generate invalid data) but sacrifice completeness for
maintainability (ie may be unable to generate some tricky but valid data).

Finally, this module makes liberal use of `# type: ignore[<code>]` pragmas.
This is because Hypothesis annotates `register_type_strategy()` with
`(T, SearchStrategy[T])`, but in most cases we register e.g. `ConstrainedInt`
to generate instances of the builtin `int` type which match the constraints. | contextlib, datetime, email_validator, fractions, hypothesis, ipaddress, json, math, pydantic, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/annotated_types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Create a `BaseModel` based on the fields of a `TypedDict`.
    Since `typing.TypedDict` in Python 3.8 does not store runtime information about optional keys,
    we raise an error if this happens (see https://bugs.python.org/issue38834). | pydantic, sys, typing, typing_extensions | L23: # Mypy bug: `Type[TypedDict]` is resolved as `Any` https://github.com/python/mypy/issues/11030
L30: we raise an error if this happens (see https://bugs.python.org/issue38834). |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/class_validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Decorate methods on the class indicating that they should be used to validate fields
    :param fields: which field(s) the method should be called on
    :param pre: whether or not this validator should be called before the standard validators (else after)
    :param each_item: for complex objects (sets, lists etc.) whether to validate individual elements rather than the
      whole object
    :param always: whether this method and other validators should be called even if the value is missing
    :param check_fields: whether to check that the fields actually exist on the model
    :param allow_reuse: whether to track and raise an error if another validator refers to the decorated function | collections, functools, inspect, itertools, pydantic, types, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/color.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Color definitions are  used as per CSS3 specification:
http://www.w3.org/TR/css3-color/#svg-color

A few colors have multiple names referring to the sames colors, eg. `grey` and `gray` or `aqua` and `cyan`.

In these cases the LAST color when sorted alphabetically takes preferences,
eg. Color((0, 255, 255)).as_named() == 'cyan' because "cyan" comes after "aqua". | colorsys, math, pydantic, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/config.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Get properties of FieldInfo from the `fields` property of the config class. | enum, json, pydantic, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/dataclasses.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The main purpose is to enhance stdlib dataclasses by adding validation
A pydantic dataclass can be generated from scratch or from a stdlib one.

Behind the scene, a pydantic dataclass is just like a regular one on which we attach
a `BaseModel` and magic methods to trigger the validation of the data.
`__init__` and `__post_init__` are hence overridden and have extra logic to be
able to validate input data.

When a pydantic dataclass is generated from scratch, it's just a plain dataclass
with validation triggered at initialization

The tricky part if for stdlib dataclasses that are converted after into pydantic ones e.g.

```py
@dataclasses.dataclass
class M:
    x: int

ValidatedM = pydantic.dataclasses.dataclass(M)
```

We indeed still want to support equality, hashing, repr, ... as if it was the stdlib one!

```py
assert isinstance(ValidatedM(x=1), M)
assert ValidatedM(x=1) == M(x=1)
```

This means we **don't want to create a new dataclass that inherits from it**
The trick is to create a wrapper around `M` that will act as a proxy to trigger
validation without altering default `M` behaviour. | contextlib, copy, dataclasses, functools, pydantic, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/datetime_parse.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Functions to parse datetime objects.

We're using regular expressions rather than time.strptime because:
- They provide both validation and parsing.
- They're more flexible for datetimes.
- The date/datetime/time constructors produce friendlier error messages.

Stolen from https://raw.githubusercontent.com/django/django/main/django/utils/dateparse.py at
9718fa2e8abe430c3526a9278dd976443d4ae3c6

Changed to:
* use standard python datetime types not django.utils.timezone
* raise ValueError when regex doesn't match rather than returning None
* support parsing unix timestamps for dates and datetimes | datetime, pydantic, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/decorator.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Decorator to validate the arguments passed to a function. | functools, inspect, pydantic, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/env_settings.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Base class for settings, allowing values to be overridden by environment variables.

    This is useful in production for secrets you do not wish to save in code, it plays nicely with docker(-compose),
    Heroku and any 12 factor app design. | os, pathlib, pydantic, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/error_wrappers.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | json, pydantic, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/errors.py` | ❓ UNKNOWN | 2025-11-09 21:03 | For built-in exceptions like ValueError or TypeError, we need to implement
    __reduce__ to override the default behaviour (instead of __getstate__/__setstate__)
    By default pickle protocol 2 calls `cls.__new__(cls, *args)`.
    Since we only use kwargs, we need a little constructor to change that.
    Note: the callable can't be a lambda as pickle looks in the namespace to find it | decimal, pathlib, pydantic, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/fields.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Captures extra information about a field. | collections, copy, pydantic, re, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/generics.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Instantiates a new class from a generic class `cls` and type variables `params`.

        :param params: Tuple of types the class . Given a generic class
            `Model` with 2 type variables and a concrete model `Model[str, int]`,
            the value `(str, int)` would be passed to `params`.
        :return: New model class inheriting from `cls` with instantiated
            types described by `params`. If no parameters are given, `cls` is
            returned as is. | pydantic, sys, types, typing, typing_extensions, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/json.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Encodes a Decimal as int of there's no exponent, otherwise float

    This is useful when we use ConstrainedDecimal to represent Numeric(x,0)
    where a integer (but not int typed) is used. Encoding this as a float
    results in failed round-tripping between encode and parse.
    Our Id type is a prime example of this.

    >>> decimal_encoder(Decimal("1.0"))
    1.0

    >>> decimal_encoder(Decimal("1"))
    1 | collections, dataclasses, datetime, decimal, enum, ipaddress, pathlib, pydantic, re, types, typing, uuid |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/main.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | abc, copy, enum, functools, inspect, pathlib, pydantic, types, typing, typing_extensions, warnings | L114: # (somewhat hacky) boolean to keep track of whether we've created the `BaseModel` class yet, and therefore whether it's |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/mypy.py` | ❓ UNKNOWN | 2025-11-09 21:03 | `version` is the mypy version string

    We might want to use this to print a warning if the mypy version being used is
    newer, or especially older, than we expect (or need). | configparser, mypy, pydantic, sys, typing | L162: if 'debug_dataclass_transform' is set to True', for testing purposes.
L164: if self.plugin_config.debug_dataclass_transform:
L231: 'debug_dataclass_transform',
L237: debug_dataclass_transform: bool  # undocumented |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/networks.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Compiled multi host url regex.

    Additionally to `url_regex` it allows to match multiple hosts.
    E.g. host1.db.net,host2.db.net | email_validator, ipaddress, pydantic, re, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/parse.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | enum, json, pathlib, pickle, pydantic, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/schema.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Process a list of models and generate a single JSON Schema with all of them defined in the ``definitions``
    top-level JSON key, including their sub-models.

    :param models: a list of models to include in the generated JSON Schema
    :param by_alias: generate the schemas using the aliases defined, if any
    :param title: title for the generated schema that includes the definitions
    :param description: description for the generated schema
    :param ref_prefix: the JSON Pointer prefix for schema references with ``$ref``, if None, will be set to the
      default of ``#/definitions/``. Update it if you want the schemas to reference the definitions somewhere
      else, e.g. for OpenAPI use ``#/components/schemas/``. The resulting generated schemas will still be at the
      top-level key ``definitions``, so you can extract them from there. But all the references will have the set
      prefix.
    :param ref_template: Use a ``string.format()`` template for ``$ref`` instead of a prefix. This can be useful
      for references that cannot be represented by ``ref_prefix`` such as a definition stored in another file. For
      a sibling json file in a ``/schemas`` directory use ``"/schemas/${model}.json#"``.
    :return: dict with the JSON Schema with a ``definitions`` top-level key including the schema definitions for
      the models and sub-models passed in ``models``. | collections, dataclasses, datetime, decimal, enum, inspect, ipaddress, pathlib, pydantic, re, typing, typing_extensions, uuid, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/tools.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Generate a JSON schema (as dict) for the passed model or dynamically generated one"""
    return _get_parsing_type(type_, type_name=title).schema(**schema_kwargs)


def schema_json_of(type_: Any, *, title: Optional[NameFactory] = None, **schema_json_kwargs: Any) -> str: | functools, json, pathlib, pydantic, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/types.py` | ❓ UNKNOWN | 2025-11-09 21:03 | StrictBool to allow for bools which are not type-coerced. | abc, datetime, decimal, enum, math, pathlib, pydantic, re, types, typing, typing_extensions, uuid, warnings, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/typing.py` | ❓ UNKNOWN | 2025-11-09 21:03 | We can't directly use `typing.get_origin` since we need a fallback to support
        custom generic classes like `ConstrainedList`
        It should be useless once https://github.com/cython/cython/issues/3537 is
        solved and https://github.com/pydantic/pydantic/pull/1753 is merged. | collections, functools, operator, os, pydantic, sys, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/utils.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Stolen approximately from django. Import a dotted module path and return the attribute/class designated by the
    last name in the path. Raise ImportError if the import fails. | collections, copy, importlib, inspect, itertools, keyword, pathlib, pydantic, types, typing, typing_extensions, warnings, weakref | L270: # TODO: replace annotation with actual expected types once #1055 solved
L423: Hack to make object's smell just enough like dicts for validate_model. |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Validate ``const`` fields.

    The value provided for a ``const`` field must be equal to the default value
    of the field. This is to support the keyword of the same name in JSON
    Schema. | collections, datetime, decimal, enum, ipaddress, math, pathlib, pydantic, re, typing, typing_extensions, uuid, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/v1/version.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | cython, importlib, pathlib, platform, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/validate_call_decorator.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Decorator for validating function calls."""

from __future__ import annotations as _annotations

import inspect
from functools import partial
from types import BuiltinFunctionType
from typing import TYPE_CHECKING, Any, Callable, TypeVar, cast, overload

from ._internal import _generate_schema, _typing_extra, _validate_call
from .errors import PydanticUserError

__all__ = ('validate_call',)

if TYPE_CHECKING:
    from .config import ConfigDict

    AnyCallableT = TypeVar('AnyCallableT', bound=Callable[..., Any])


_INVALID_TYPE_ERROR_CODE = 'validate-call-type'


def _check_function_type(function: object) -> None: | , __future__, functools, inspect, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/validators.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `validators` module is a backport module from V1."""

from ._migration import getattr_migration

__getattr__ = getattr_migration(__name__) |  |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/version.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The `version` module holds the version information for Pydantic."""

from __future__ import annotations as _annotations

import sys

from pydantic_core import __version__ as __pydantic_core_version__

__all__ = 'VERSION', 'version_info'

VERSION = '2.12.4' | , __future__, importlib, pathlib, platform, pydantic_core, sys |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic/warnings.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Pydantic-specific warnings."""

from __future__ import annotations as _annotations

from .version import version_short

__all__ = (
    'PydanticDeprecatedSince20',
    'PydanticDeprecatedSince26',
    'PydanticDeprecatedSince29',
    'PydanticDeprecatedSince210',
    'PydanticDeprecatedSince211',
    'PydanticDeprecatedSince212',
    'PydanticDeprecationWarning',
    'PydanticExperimentalWarning',
    'ArbitraryTypeWarning',
    'UnsupportedFieldAttributeWarning',
    'TypedDictExtraConfigWarning',
)


class PydanticDeprecationWarning(DeprecationWarning): | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic_core/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | The type of error that occurred, this is an identifier designed for
    programmatic use that will change rarely or never.

    `type` is unique for each error message, and can hence be used as an identifier to build custom error messages. | , __future__, pydantic, pydantic_core, sys, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/pydantic_core/core_schema.py` | ❓ UNKNOWN | 2025-11-09 21:03 | This module contains definitions to build schemas which `pydantic_core` can
validate and serialize. | __future__, collections, datetime, decimal, pydantic_core, re, sys, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/requests/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Requests HTTP Library
~~~~~~~~~~~~~~~~~~~~~

Requests is an HTTP library, written in Python, for human beings.
Basic GET usage:

   >>> import requests
   >>> r = requests.get('https://www.python.org')
   >>> r.status_code
   200
   >>> b'Python is a programming language' in r.content
   True

... or POST:

   >>> payload = dict(key1='value1', key2='value2')
   >>> r = requests.post('https://httpbin.org/post', data=payload)
   >>> print(r.text)
   {
     ...
     "form": {
       "key1": "value1",
       "key2": "value2"
     },
     ...
   }

The other HTTP methods are supported - see `requests.api`. Full documentation
is at <https://requests.readthedocs.io>.

:copyright: (c) 2017 by Kenneth Reitz.
:license: Apache 2.0, see LICENSE for more details. | , chardet, charset_normalizer, cryptography, logging, ssl, urllib3, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/requests/__version__.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/requests/_internal_utils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests._internal_utils
~~~~~~~~~~~~~~

Provides utility functions that are consumed internally by Requests
which depend on extremely few external helpers (such as compat) | , re |  |
| `blackboard-agent/venv/Lib/site-packages/requests/adapters.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.adapters
~~~~~~~~~~~~~~~~~

This module contains the transport adapters that Requests uses to define
and maintain connections. | , os, socket, urllib3 |  |
| `blackboard-agent/venv/Lib/site-packages/requests/api.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.api
~~~~~~~~~~~~

This module implements the Requests API.

:copyright: (c) 2012 by Kenneth Reitz.
:license: Apache2, see LICENSE for more details. |  |  |
| `blackboard-agent/venv/Lib/site-packages/requests/auth.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.auth
~~~~~~~~~~~~~

This module contains the authentication handlers for Requests. | , base64, hashlib, os, re, threading, time, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/requests/certs.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.certs
~~~~~~~~~~~~~~

This module returns the preferred default CA certificate bundle. There is
only one — the one from the certifi package.

If you are packaging Requests, e.g., for a Linux distribution or a managed
environment, you can change the definition of where() to return a separately
packaged CA bundle. | certifi |  |
| `blackboard-agent/venv/Lib/site-packages/requests/compat.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.compat
~~~~~~~~~~~~~~~

This module previously handled import compatibility issues
between Python 2 and Python 3. It remains for backwards
compatibility until the next major version. | chardet, charset_normalizer, collections, http, io, json, simplejson, sys, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/requests/cookies.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.cookies
~~~~~~~~~~~~~~~~

Compatibility code to be able to use `cookielib.CookieJar` with requests.

requests.utils imports from here, so be careful with imports. | , calendar, copy, dummy_threading, threading, time |  |
| `blackboard-agent/venv/Lib/site-packages/requests/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.exceptions
~~~~~~~~~~~~~~~~~~~

This module contains the set of Requests' exceptions. | , urllib3 |  |
| `blackboard-agent/venv/Lib/site-packages/requests/help.py` | ❓ UNKNOWN | 2025-11-09 19:12 | Module containing bug report helper(s)."""

import json
import platform
import ssl
import sys

import idna
import urllib3

from . import __version__ as requests_version

try:
    import charset_normalizer
except ImportError:
    charset_normalizer = None

try:
    import chardet
except ImportError:
    chardet = None

try:
    from urllib3.contrib import pyopenssl
except ImportError:
    pyopenssl = None
    OpenSSL = None
    cryptography = None
else:
    import cryptography
    import OpenSSL


def _implementation(): | , chardet, charset_normalizer, cryptography, idna, json, OpenSSL, platform, ssl, sys, urllib3 | L1: """Module containing bug report helper(s)."""
L70: """Generate information for a bug report."""
L129: """Pretty-print the bug information as JSON.""" |
| `blackboard-agent/venv/Lib/site-packages/requests/hooks.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.hooks
~~~~~~~~~~~~~~

This module provides the capabilities for the Requests hooks system.

Available hooks:

``response``:
    The response generated from a Request. |  | L19: # TODO: response is the only one |
| `blackboard-agent/venv/Lib/site-packages/requests/models.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.models
~~~~~~~~~~~~~~~

This module contains the primary objects that power Requests. | , datetime, encodings, io, urllib3 |  |
| `blackboard-agent/venv/Lib/site-packages/requests/packages.py` | ❓ UNKNOWN | 2025-11-09 19:12 |  | chardet, charset_normalizer, sys, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/requests/sessions.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.sessions
~~~~~~~~~~~~~~~~~

This module provides a Session object to manage and persist settings across
requests (cookies, auth, proxies). | , collections, datetime, os, sys, time |  |
| `blackboard-agent/venv/Lib/site-packages/requests/status_codes.py` | ❓ UNKNOWN | 2025-11-09 19:12 | The ``codes`` object defines a mapping from common names for HTTP statuses
to their numerical codes, accessible either as attributes or as dictionary
items.

Example::

    >>> import requests
    >>> requests.codes['temporary_redirect']
    307
    >>> requests.codes.teapot
    418
    >>> requests.codes['\o/']
    200

Some codes have multiple names, and both upper- and lower-case versions of
the names are allowed. For example, ``codes.ok``, ``codes.OK``, and
``codes.okay`` all correspond to the HTTP status code 200. |  |  |
| `blackboard-agent/venv/Lib/site-packages/requests/structures.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.structures
~~~~~~~~~~~~~~~~~~~

Data structures that power Requests. | , collections |  |
| `blackboard-agent/venv/Lib/site-packages/requests/utils.py` | ❓ UNKNOWN | 2025-11-09 19:12 | requests.utils
~~~~~~~~~~~~~~

This module provides utility functions that are used within Requests
that are also useful for external consumption. | , codecs, collections, contextlib, io, netrc, os, re, socket, struct, sys, tempfile, urllib3, warnings, winreg, zipfile | L218: # getpwuid fails. See https://bugs.python.org/issue20164 &
L251: # App Engine hackiness.
L447: # RFC is met will result in bugs with internet explorer and |
| `blackboard-agent/venv/Lib/site-packages/selenium/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/common/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/common/exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Exceptions that may happen in all the webdriver code."""

from collections.abc import Sequence
from typing import Any, Optional

SUPPORT_MSG = "For documentation on this error, please visit:"
ERROR_URL = "https://www.selenium.dev/documentation/webdriver/troubleshooting/errors"


class WebDriverException(Exception): | collections, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/types.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Selenium type definitions."""

from collections.abc import Iterable
from typing import IO, Any, Union

AnyKey = Union[str, int, float]
WaitExcTypes = Iterable[type[Exception]]

# Service Types
SubprocessStdAlias = Union[int, str, IO[Any]] | collections, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chrome/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chrome/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chrome/remote_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chrome/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping of
    `chromedriver`.

    Args:
        executable_path: Install path of the chromedriver executable, defaults
            to `chromedriver`.
        port: Port for the service to run on, defaults to 0 where the operating
            system will decide.
        service_args: (Optional) Sequence of args to be passed to the subprocess
            when launching the executable.
        log_output: (Optional) int representation of STDOUT/DEVNULL, any IO
            instance or String path to file.
        env: (Optional) Mapping of environment variables for the new process,
            defaults to `os.environ`. | collections, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chrome/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the ChromeDriver and allows you to drive the browser."""

    def __init__(
        self,
        options: Optional[Options] = None,
        service: Optional[Service] = None,
        keep_alive: bool = True,
    ) -> None: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chromium/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chromium/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Initialize ChromiumOptions with default settings."""
        super().__init__()
        self._binary_location: str = ""
        self._extension_files: list[str] = []
        self._extensions: list[str] = []
        self._experimental_options: dict[str, Union[str, int, dict, list[str]]] = {}
        self._debugger_address: Optional[str] = None
        self._enable_webextensions: bool = False

    @property
    def binary_location(self) -> str: | base64, os, selenium, typing | L36: self._debugger_address: Optional[str] = None
L59: def debugger_address(self) -> Optional[str]:
L64: return self._debugger_address
L66: @debugger_address.setter
L67: def debugger_address(self, value: str) -> None:
L75: raise TypeError("Debugger Address must be a string")
L76: self._debugger_address = value
L161: - --enable-unsafe-extension-debugging
L162: - --remote-debugging-pipe
L165: - Enabling --remote-debugging-pipe makes the connection b/w chromedriver
L172: required_flags = ["--enable-unsafe-extension-debugging", "--remote-debugging-pipe"]
L178: flags_to_remove = ["--enable-unsafe-extension-debugging", "--remote-debugging-pipe"]
L197: if self.debugger_address:
L198: chrome_options["debuggerAddress"] = self.debugger_address |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chromium/remote_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chromium/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping the
    WebDriver instance of the ChromiumDriver.

    Args:
        executable_path: Install path of the executable.
        port: Port for the service to run on, defaults to 0 where the operating
            system will decide.
        service_args: (Optional) Sequence of args to be passed to the subprocess
            when launching the executable.
        log_output: (Optional) int representation of STDOUT/DEVNULL, any IO
            instance or String path to file.
        env: (Optional) Mapping of environment variables for the new process,
            defaults to `os.environ`.
        driver_path_env_key: (Optional) Environment variable to use to get the
            path to the driver executable. | collections, io, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/chromium/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the WebDriver instance of ChromiumDriver and allows you to
    drive the browser. | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/action_chains.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The ActionChains implementation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Union

from selenium.webdriver.common.actions.action_builder import ActionBuilder
from selenium.webdriver.common.actions.key_input import KeyInput
from selenium.webdriver.common.actions.pointer_input import PointerInput
from selenium.webdriver.common.actions.wheel_input import ScrollOrigin, WheelInput
from selenium.webdriver.common.utils import keys_to_typing
from selenium.webdriver.remote.webelement import WebElement

if TYPE_CHECKING:
    from selenium.webdriver.remote.webdriver import WebDriver

AnyDevice = Union[PointerInput, KeyInput, WheelInput]


class ActionChains: | __future__, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/action_builder.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Get the device with the given name.

        Parameters:
        -----------
        name : str
            The name of the device to get.

        Returns:
        --------
        Optional[Union[WheelInput, PointerInput, KeyInput]] : The device with the given name. | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/input_device.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Describes the input device being used for the action."""

    def __init__(self, name: Optional[str] = None):
        self.name = name or uuid.uuid4()
        self.actions: list[Any] = []

    def add_action(self, action: Any) -> None: | typing, uuid |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/interaction.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/key_actions.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/key_input.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/mouse_button.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/pointer_actions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Args:
        - source: PointerInput instance
        - duration: override the default 250 msecs of DEFAULT_MOVE_DURATION in source | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/pointer_input.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/wheel_actions.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/actions/wheel_input.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/alert.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Alert implementation."""

from selenium.webdriver.common.utils import keys_to_typing
from selenium.webdriver.remote.command import Command


class Alert: | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/browser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents a window state."""

    FULLSCREEN = "fullscreen"
    MAXIMIZED = "maximized"
    MINIMIZED = "minimized"
    NORMAL = "normal"

    VALID_STATES = {FULLSCREEN, MAXIMIZED, MINIMIZED, NORMAL}


class ClientWindowInfo: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/browsing_context.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents the stage of document loading at which a navigation command will return."""

    NONE = "none"
    INTERACTIVE = "interactive"
    COMPLETE = "complete"


class UserPromptType: | dataclasses, selenium, threading, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/cdp.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Attempt to load the current latest available devtools into the module
    cache for use later. | collections, contextlib, contextvars, dataclasses, importlib, itertools, json, logging, pathlib, trio, trio_websocket, typing | L73: selenium_logger.debug("Falling back to loading `devtools`: v%s", latest)
L222: if logger.isEnabledFor(logging.DEBUG):
L223: logger.debug(f"Sending CDP message: {cmd_id} {cmd_event}: {request_str}")
L230: if logger.isEnabledFor(logging.DEBUG):
L231: logger.debug(f"Received CDP message: {response}")
L233: if logger.isEnabledFor(logging.DEBUG):
L234: logger.debug(f"Exception raised by {cmd_event} message: {type(response).__name__}")
L311: logger.debug("Received event: %s", event)
L460: logger.debug("Received message %r", data) |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/common.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Build a command iterator to send to the BiDi protocol.

    Parameters:
    -----------
        method: The method to execute.
        params: The parameters to pass to the method. Default is None.

    Returns:
    --------
        The response from the command execution. | collections, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/console.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | enum |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents geolocation coordinates."""

    def __init__(
        self,
        latitude: float,
        longitude: float,
        accuracy: float = 1.0,
        altitude: Optional[float] = None,
        altitude_accuracy: Optional[float] = None,
        heading: Optional[float] = None,
        speed: Optional[float] = None,
    ): | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/input.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents the possible pointer types."""

    MOUSE = "mouse"
    PEN = "pen"
    TOUCH = "touch"

    VALID_TYPES = {MOUSE, PEN, TOUCH}


class Origin: | dataclasses, math, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/log.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents log level."""

    DEBUG = "debug"
    INFO = "info"
    WARN = "warn"
    ERROR = "error" | dataclasses | L75: DEBUG = "debug" |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/network.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents a network event."""

    def __init__(self, event_class, **kwargs):
        self.event_class = event_class
        self.params = kwargs

    @classmethod
    def from_json(cls, json):
        return cls(event_class=json.get("event_class"), **json)


class Network:
    EVENTS = {
        "before_request": "network.beforeRequestSent",
        "response_started": "network.responseStarted",
        "response_completed": "network.responseCompleted",
        "auth_required": "network.authRequired",
        "fetch_error": "network.fetchError",
        "continue_request": "network.continueRequest",
        "continue_auth": "network.continueWithAuth",
    }

    PHASES = {
        "before_request": "beforeRequestSent",
        "response_started": "responseStarted",
        "auth_required": "authRequired",
    }

    def __init__(self, conn):
        self.conn = conn
        self.intercepts = []
        self.callbacks = {}
        self.subscriptions = {}

    def _add_intercept(self, phases=[], contexts=None, url_patterns=None): | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/permissions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents the possible permission states."""

    GRANTED = "granted"
    DENIED = "denied"
    PROMPT = "prompt"


class PermissionDescriptor: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/script.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents the possible result ownership types."""

    NONE = "none"
    ROOT = "root"


class RealmType: | dataclasses, datetime, math, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/session.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents the behavior of the user prompt handler."""

    ACCEPT = "accept"
    DISMISS = "dismiss"
    IGNORE = "ignore"

    VALID_TYPES = {ACCEPT, DISMISS, IGNORE}


class UserPromptHandler: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents the possible same site values for cookies."""

    STRICT = "strict"
    LAX = "lax"
    NONE = "none"
    DEFAULT = "default"


class BytesValue: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/bidi/webextension.py` | ❓ UNKNOWN | 2025-11-09 21:21 | BiDi implementation of the webExtension module. | selenium, typing | L65: f"{str(e)}. If you are using Chrome or Edge, add '--enable-unsafe-extension-debugging' "
L66: "and '--remote-debugging-pipe' arguments or set options.enable_webextensions = True" |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/by.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The By implementation."""

from typing import Literal, Optional

ByType = Literal["id", "xpath", "link text", "partial link text", "name", "tag name", "class name", "css selector"]


class By: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/desired_capabilities.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Desired Capabilities implementation."""


class DesiredCapabilities: | selenium | L45: "moz:debuggerAddress": True, |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  | L17: from . import dom_debugger
L20: from . import debugger |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/accessibility.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique accessibility node identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/animation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Animation instance. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/audits.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Information about a cookie that is affected by an inspector issue. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/autofill.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A list of address fields. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/background_service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Background Service that will be associated with the commands/events.
    Every Background Service operates independently, but they share the same
    API. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/bluetooth_emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Indicates the various states of Central. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/browser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The state of the browser window. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/cache_storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique identifier of the Cache object. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/cast.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Starts observing for sinks that can be used for tab mirroring, and if set,
    sinks compatible with ``presentationUrl`` as well. When sinks are found, a
    ``sinksUpdated`` event is fired.
    Also starts observing for issue messages. When an issue is added or removed,
    an ``issueUpdated`` event is fired.

    :param presentation_url: *(Optional)* | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/console.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Console message. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/css.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Stylesheet type: "injected" for stylesheets injected via extension, "user-agent" for user-agent
    stylesheets, "inspector" for stylesheets created by the inspector (i.e. those holding the "via
    inspector" rules), "regular" for regular stylesheets. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/debugger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Breakpoint identifier. | , __future__, dataclasses, enum, typing | L6: # CDP domain: Debugger
L50: #: Script identifier as reported in the ``Debugger.scriptParsed``.
L142: #: sent ``Debugger.scriptParsed`` event.
L159: #: guarantee that Debugger#restartFrame with this CallFrameId will be
L265: #: Script identifier as reported in the ``Debugger.scriptParsed``.
L334: class DebugSymbols:
L336: Debug symbols available for a wasm script.
L338: #: Type of the debug symbols.
L396: 'method': 'Debugger.continueToLocation',
L404: Disables debugger for given page.
L407: 'method': 'Debugger.disable',
L414: ) -> typing.Generator[T_JSON_DICT,T_JSON_DICT,runtime.UniqueDebuggerId]:
L416: Enables debugger for the given page. Clients should not assume that the debugging has been
L419: :param max_scripts_cache_size: **(EXPERIMENTAL)** *(Optional)* The maximum size in bytes of collected scripts (not referenced by other heap objects) the debugger can hold. Puts no limit if parameter is omitted.
L420: :returns: Unique identifier of the debugger.
L426: 'method': 'Debugger.enable',
L430: return runtime.UniqueDebuggerId.from_json(json['debuggerId'])
L479: 'method': 'Debugger.evaluateOnCallFrame', |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/device_access.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Device request id. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/device_orientation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Clears the overridden Device Orientation. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/dom.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique DOM node identifier. | , __future__, dataclasses, enum, typing | L293: #: Deprecated, as the HTML Imports API has been removed (crbug.com/937746). |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/dom_debugger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | DOM breakpoint type. | , __future__, dataclasses, enum, typing | L6: # CDP domain: DOMDebugger
L135: 'method': 'DOMDebugger.getEventListeners',
L156: 'method': 'DOMDebugger.removeDOMBreakpoint',
L177: 'method': 'DOMDebugger.removeEventListenerBreakpoint',
L196: 'method': 'DOMDebugger.removeInstrumentationBreakpoint',
L213: 'method': 'DOMDebugger.removeXHRBreakpoint',
L232: 'method': 'DOMDebugger.setBreakOnCSPViolation',
L252: 'method': 'DOMDebugger.setDOMBreakpoint',
L273: 'method': 'DOMDebugger.setEventListenerBreakpoint',
L292: 'method': 'DOMDebugger.setInstrumentationBreakpoint',
L309: 'method': 'DOMDebugger.setXHRBreakpoint', |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/dom_snapshot.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Node in the DOM tree. | , __future__, dataclasses, enum, typing | L13: from . import dom_debugger
L98: event_listeners: typing.Optional[typing.List[dom_debugger.EventListener]] = None
L193: event_listeners=[dom_debugger.EventListener.from_json(i) for i in json['eventListeners']] if 'eventListeners' in json else None, |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/dom_storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | DOM Storage identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Screen orientation. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/event_breakpoints.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sets breakpoint on particular native event.

    :param event_name: Instrumentation name to stop on. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/extensions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Storage areas. | , __future__, dataclasses, enum, typing | L37: --remote-debugging-pipe flag and the --enable-unsafe-extension-debugging
L58: Available if the client is connected using the --remote-debugging-pipe flag
L59: and the --enable-unsafe-extension-debugging. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/fed_cm.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Whether this is a sign-up or sign-in action for this account, i.e.
    whether this account has ever been used to sign in to this RP before. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/fetch.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique request identifier.
    Note that this does not identify individual HTTP requests that are part of
    a network request. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/file_system.py` | ❓ UNKNOWN | 2025-11-09 21:21 | :param bucket_file_system_locator:
    :returns: Returns the directory object at the path. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/headless_experimental.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Encoding options for a screenshot. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/heap_profiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Heap snapshot object id. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/indexed_db.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Database with an array of object stores. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/input_.py` | ❓ UNKNOWN | 2025-11-09 21:21 | UTC time in seconds, counted from January 1, 1970. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/inspector.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Disables inspector domain notifications. | , __future__, dataclasses, enum, typing | L37: Fired when remote debugging connection is about to be terminated. Contains detach reason.
L53: Fired when debugging target has crashed
L68: Fired when debugging target has reloaded after crash |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/io.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This is either obtained from another method or specified as ``blob:<uuid>`` where
    ``<uuid>`` is an UUID of a Blob. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/layer_tree.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique Layer identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/log.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Log entry. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/media.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Players will get an ID that is unique within the agent context. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/memory.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Memory pressure level. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/network.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Resource type as it was perceived by the rendering engine. | , __future__, dataclasses, enum, typing | L12: from . import debugger |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/overlay.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration data for drawing the source order of an elements children. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/page.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique frame identifier. | , __future__, dataclasses, enum, typing | L12: from . import debugger
L98: #: Id of scriptId's debugger.
L99: debugger_id: runtime.UniqueDebuggerId
L104: json['debuggerId'] = self.debugger_id.to_json()
L111: debugger_id=runtime.UniqueDebuggerId.from_json(json['debuggerId']), |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/performance.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Run-time execution metric. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/performance_timeline.py` | ❓ UNKNOWN | 2025-11-09 21:21 | See https://github.com/WICG/LargestContentfulPaint and largest_contentful_paint.idl | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/preload.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique id | , __future__, dataclasses, enum, typing | L71: #: TODO(https://crbug.com/1425354): Replace this property with structured error.
L349: TODO(https://crbug.com/1384419): revisit the list of PrefetchStatus and |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/profiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Profile node. Holds callsite information, execution statistics and child nodes. | , __future__, dataclasses, enum, typing | L12: from . import debugger
L358: location: debugger.Location
L367: location=debugger.Location.from_json(json['location']),
L381: location: debugger.Location
L389: location=debugger.Location.from_json(json['location']), |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/pwa.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The following types are the replica of
    https://crsrc.org/c/chrome/browser/web_applications/proto/web_app_os_integration_state.proto;drc=9910d3be894c8f142c977ba1023f30a656bc13fc;l=67 | , __future__, dataclasses, enum, typing | L209: TODO(crbug.com/339454034): Check the existences of the input files.
L262: :param link_capturing: *(Optional)* If user allows the links clicked on by the user in the app's scope, or extended scope if the manifest has scope extensions and the flags ```DesktopPWAsLinkCapturingWithScopeExtensions```` and ````WebAppEnableScopeExtensions``` are enabled.  Note, the API does not support resetting the linkCapturing to the initial value, uninstalling and installing the web app again will reset it.  TODO(crbug.com/339453269): Setting this value on ChromeOS is not supported yet. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/runtime.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique script identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/schema.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Description of the protocol domain. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/security.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An internal certificate ID value. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/service_worker.py` | ❓ UNKNOWN | 2025-11-09 21:21 | ServiceWorker registration. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enum of possible storage types. | , __future__, dataclasses, enum, typing | L403: #: TODO(crbug.com/401011862): Consider updating this parameter to binary. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/system_info.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Describes a single graphics processor (GPU). | , __future__, dataclasses, enum, typing | L239: #: An optional array of GPU driver bug workarounds.
L240: driver_bug_workarounds: typing.List[str]
L260: json['driverBugWorkarounds'] = [i for i in self.driver_bug_workarounds]
L274: driver_bug_workarounds=[str(i) for i in json['driverBugWorkarounds']], |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/target.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique identifier of attached debugging session. | , __future__, dataclasses, enum, typing | L30: Unique identifier of attached debugging session.
L215: :param flatten: *(Optional)* Enables "flat" access to the session via specifying sessionId attribute in the commands. We plan to make this the default, deprecate non-flattened mode, and eventually retire it. See crbug.com/991325.
L276: - ``binding.send(json)`` - a method to send messages over the remote debugging protocol
L308: :param dispose_on_detach: **(EXPERIMENTAL)** *(Optional)* If specified, disposes this context when debugging session disconnects.
L497: and crbug.com/991325. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/tethering.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Request browser port binding.

    :param port: Port number to bind. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/tracing.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration for memory dump. Used only when "memory-infra" category is enabled. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/util.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A decorator that registers a class as an event class. '''
    def decorate(cls):
        _event_parsers[method] = cls
        cls.event_class = method
        return cls
    return decorate


def parse_json_event(json: T_JSON_DICT) -> typing.Any: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/web_audio.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An unique ID for a graph object (AudioContext, AudioNode, AudioParam) in Web Audio API | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v140/web_authn.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enable the WebAuthn domain and start intercepting credential storage and
    retrieval with a virtual authenticator.

    :param enable_ui: *(Optional)* Whether to enable the WebAuthn user interface. Enabling the UI is recommended for debugging and demo purposes, as it is closer to the real experience. Disabling the UI is recommended for automated testing. Supported at the embedder's discretion if UI is available. Defaults to false. | , __future__, dataclasses, enum, typing | L255: :param enable_ui: *(Optional)* Whether to enable the WebAuthn user interface. Enabling the UI is recommended for debugging and demo purposes, as it is closer to the real experience. Disabling the UI is recommended for automated testing. Supported at the embedder's discretion if UI is available. Defaults to false. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  | L17: from . import dom_debugger
L20: from . import debugger |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/accessibility.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique accessibility node identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/animation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Animation instance. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/audits.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Information about a cookie that is affected by an inspector issue. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/autofill.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A list of address fields. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/background_service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Background Service that will be associated with the commands/events.
    Every Background Service operates independently, but they share the same
    API. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/bluetooth_emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Indicates the various states of Central. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/browser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The state of the browser window. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/cache_storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique identifier of the Cache object. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/cast.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Starts observing for sinks that can be used for tab mirroring, and if set,
    sinks compatible with ``presentationUrl`` as well. When sinks are found, a
    ``sinksUpdated`` event is fired.
    Also starts observing for issue messages. When an issue is added or removed,
    an ``issueUpdated`` event is fired.

    :param presentation_url: *(Optional)* | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/console.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Console message. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/css.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Stylesheet type: "injected" for stylesheets injected via extension, "user-agent" for user-agent
    stylesheets, "inspector" for stylesheets created by the inspector (i.e. those holding the "via
    inspector" rules), "regular" for regular stylesheets. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/debugger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Breakpoint identifier. | , __future__, dataclasses, enum, typing | L6: # CDP domain: Debugger
L50: #: Script identifier as reported in the ``Debugger.scriptParsed``.
L142: #: sent ``Debugger.scriptParsed`` event.
L159: #: guarantee that Debugger#restartFrame with this CallFrameId will be
L265: #: Script identifier as reported in the ``Debugger.scriptParsed``.
L334: class DebugSymbols:
L336: Debug symbols available for a wasm script.
L338: #: Type of the debug symbols.
L396: 'method': 'Debugger.continueToLocation',
L404: Disables debugger for given page.
L407: 'method': 'Debugger.disable',
L414: ) -> typing.Generator[T_JSON_DICT,T_JSON_DICT,runtime.UniqueDebuggerId]:
L416: Enables debugger for the given page. Clients should not assume that the debugging has been
L419: :param max_scripts_cache_size: **(EXPERIMENTAL)** *(Optional)* The maximum size in bytes of collected scripts (not referenced by other heap objects) the debugger can hold. Puts no limit if parameter is omitted.
L420: :returns: Unique identifier of the debugger.
L426: 'method': 'Debugger.enable',
L430: return runtime.UniqueDebuggerId.from_json(json['debuggerId'])
L479: 'method': 'Debugger.evaluateOnCallFrame', |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/device_access.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Device request id. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/device_orientation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Clears the overridden Device Orientation. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/dom.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique DOM node identifier. | , __future__, dataclasses, enum, typing | L294: #: Deprecated, as the HTML Imports API has been removed (crbug.com/937746). |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/dom_debugger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | DOM breakpoint type. | , __future__, dataclasses, enum, typing | L6: # CDP domain: DOMDebugger
L135: 'method': 'DOMDebugger.getEventListeners',
L156: 'method': 'DOMDebugger.removeDOMBreakpoint',
L177: 'method': 'DOMDebugger.removeEventListenerBreakpoint',
L196: 'method': 'DOMDebugger.removeInstrumentationBreakpoint',
L213: 'method': 'DOMDebugger.removeXHRBreakpoint',
L232: 'method': 'DOMDebugger.setBreakOnCSPViolation',
L252: 'method': 'DOMDebugger.setDOMBreakpoint',
L273: 'method': 'DOMDebugger.setEventListenerBreakpoint',
L292: 'method': 'DOMDebugger.setInstrumentationBreakpoint',
L309: 'method': 'DOMDebugger.setXHRBreakpoint', |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/dom_snapshot.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Node in the DOM tree. | , __future__, dataclasses, enum, typing | L13: from . import dom_debugger
L98: event_listeners: typing.Optional[typing.List[dom_debugger.EventListener]] = None
L193: event_listeners=[dom_debugger.EventListener.from_json(i) for i in json['eventListeners']] if 'eventListeners' in json else None, |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/dom_storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | DOM Storage identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Screen orientation. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/event_breakpoints.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sets breakpoint on particular native event.

    :param event_name: Instrumentation name to stop on. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/extensions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Storage areas. | , __future__, dataclasses, enum, typing | L37: --remote-debugging-pipe flag and the --enable-unsafe-extension-debugging
L58: Available if the client is connected using the --remote-debugging-pipe flag
L59: and the --enable-unsafe-extension-debugging. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/fed_cm.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Whether this is a sign-up or sign-in action for this account, i.e.
    whether this account has ever been used to sign in to this RP before. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/fetch.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique request identifier.
    Note that this does not identify individual HTTP requests that are part of
    a network request. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/file_system.py` | ❓ UNKNOWN | 2025-11-09 21:21 | :param bucket_file_system_locator:
    :returns: Returns the directory object at the path. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/headless_experimental.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Encoding options for a screenshot. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/heap_profiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Heap snapshot object id. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/indexed_db.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Database with an array of object stores. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/input_.py` | ❓ UNKNOWN | 2025-11-09 21:21 | UTC time in seconds, counted from January 1, 1970. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/inspector.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Disables inspector domain notifications. | , __future__, dataclasses, enum, typing | L37: Fired when remote debugging connection is about to be terminated. Contains detach reason.
L53: Fired when debugging target has crashed
L68: Fired when debugging target has reloaded after crash |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/io.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This is either obtained from another method or specified as ``blob:<uuid>`` where
    ``<uuid>`` is an UUID of a Blob. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/layer_tree.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique Layer identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/log.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Log entry. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/media.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Players will get an ID that is unique within the agent context. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/memory.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Memory pressure level. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/network.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Resource type as it was perceived by the rendering engine. | , __future__, dataclasses, enum, typing | L12: from . import debugger |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/overlay.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration data for drawing the source order of an elements children. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/page.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique frame identifier. | , __future__, dataclasses, enum, typing | L12: from . import debugger
L98: #: Id of scriptId's debugger.
L99: debugger_id: runtime.UniqueDebuggerId
L104: json['debuggerId'] = self.debugger_id.to_json()
L111: debugger_id=runtime.UniqueDebuggerId.from_json(json['debuggerId']), |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/performance.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Run-time execution metric. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/performance_timeline.py` | ❓ UNKNOWN | 2025-11-09 21:21 | See https://github.com/WICG/LargestContentfulPaint and largest_contentful_paint.idl | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/preload.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique id | , __future__, dataclasses, enum, typing | L71: #: TODO(https://crbug.com/1425354): Replace this property with structured error.
L349: TODO(https://crbug.com/1384419): revisit the list of PrefetchStatus and |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/profiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Profile node. Holds callsite information, execution statistics and child nodes. | , __future__, dataclasses, enum, typing | L12: from . import debugger
L358: location: debugger.Location
L367: location=debugger.Location.from_json(json['location']),
L381: location: debugger.Location
L389: location=debugger.Location.from_json(json['location']), |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/pwa.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The following types are the replica of
    https://crsrc.org/c/chrome/browser/web_applications/proto/web_app_os_integration_state.proto;drc=9910d3be894c8f142c977ba1023f30a656bc13fc;l=67 | , __future__, dataclasses, enum, typing | L209: TODO(crbug.com/339454034): Check the existences of the input files.
L262: :param link_capturing: *(Optional)* If user allows the links clicked on by the user in the app's scope, or extended scope if the manifest has scope extensions and the flags ```DesktopPWAsLinkCapturingWithScopeExtensions```` and ````WebAppEnableScopeExtensions``` are enabled.  Note, the API does not support resetting the linkCapturing to the initial value, uninstalling and installing the web app again will reset it.  TODO(crbug.com/339453269): Setting this value on ChromeOS is not supported yet. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/runtime.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique script identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/schema.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Description of the protocol domain. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/security.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An internal certificate ID value. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/service_worker.py` | ❓ UNKNOWN | 2025-11-09 21:21 | ServiceWorker registration. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enum of possible storage types. | , __future__, dataclasses, enum, typing | L403: #: TODO(crbug.com/401011862): Consider updating this parameter to binary. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/system_info.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Describes a single graphics processor (GPU). | , __future__, dataclasses, enum, typing | L239: #: An optional array of GPU driver bug workarounds.
L240: driver_bug_workarounds: typing.List[str]
L260: json['driverBugWorkarounds'] = [i for i in self.driver_bug_workarounds]
L274: driver_bug_workarounds=[str(i) for i in json['driverBugWorkarounds']], |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/target.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique identifier of attached debugging session. | , __future__, dataclasses, enum, typing | L30: Unique identifier of attached debugging session.
L221: :param flatten: *(Optional)* Enables "flat" access to the session via specifying sessionId attribute in the commands. We plan to make this the default, deprecate non-flattened mode, and eventually retire it. See crbug.com/991325.
L282: - ``binding.send(json)`` - a method to send messages over the remote debugging protocol
L314: :param dispose_on_detach: **(EXPERIMENTAL)** *(Optional)* If specified, disposes this context when debugging session disconnects. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/tethering.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Request browser port binding.

    :param port: Port number to bind. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/tracing.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration for memory dump. Used only when "memory-infra" category is enabled. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/util.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A decorator that registers a class as an event class. '''
    def decorate(cls):
        _event_parsers[method] = cls
        cls.event_class = method
        return cls
    return decorate


def parse_json_event(json: T_JSON_DICT) -> typing.Any: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/web_audio.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An unique ID for a graph object (AudioContext, AudioNode, AudioParam) in Web Audio API | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v141/web_authn.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enable the WebAuthn domain and start intercepting credential storage and
    retrieval with a virtual authenticator.

    :param enable_ui: *(Optional)* Whether to enable the WebAuthn user interface. Enabling the UI is recommended for debugging and demo purposes, as it is closer to the real experience. Disabling the UI is recommended for automated testing. Supported at the embedder's discretion if UI is available. Defaults to false. | , __future__, dataclasses, enum, typing | L255: :param enable_ui: *(Optional)* Whether to enable the WebAuthn user interface. Enabling the UI is recommended for debugging and demo purposes, as it is closer to the real experience. Disabling the UI is recommended for automated testing. Supported at the embedder's discretion if UI is available. Defaults to false. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  | L17: from . import dom_debugger
L20: from . import debugger |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/accessibility.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique accessibility node identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/animation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Animation instance. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/audits.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Information about a cookie that is affected by an inspector issue. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/autofill.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A list of address fields. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/background_service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Background Service that will be associated with the commands/events.
    Every Background Service operates independently, but they share the same
    API. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/bluetooth_emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Indicates the various states of Central. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/browser.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The state of the browser window. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/cache_storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique identifier of the Cache object. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/cast.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Starts observing for sinks that can be used for tab mirroring, and if set,
    sinks compatible with ``presentationUrl`` as well. When sinks are found, a
    ``sinksUpdated`` event is fired.
    Also starts observing for issue messages. When an issue is added or removed,
    an ``issueUpdated`` event is fired.

    :param presentation_url: *(Optional)* | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/console.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Console message. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/css.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Stylesheet type: "injected" for stylesheets injected via extension, "user-agent" for user-agent
    stylesheets, "inspector" for stylesheets created by the inspector (i.e. those holding the "via
    inspector" rules), "regular" for regular stylesheets. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/debugger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Breakpoint identifier. | , __future__, dataclasses, enum, typing | L6: # CDP domain: Debugger
L50: #: Script identifier as reported in the ``Debugger.scriptParsed``.
L142: #: sent ``Debugger.scriptParsed`` event.
L159: #: guarantee that Debugger#restartFrame with this CallFrameId will be
L265: #: Script identifier as reported in the ``Debugger.scriptParsed``.
L334: class DebugSymbols:
L336: Debug symbols available for a wasm script.
L338: #: Type of the debug symbols.
L396: 'method': 'Debugger.continueToLocation',
L404: Disables debugger for given page.
L407: 'method': 'Debugger.disable',
L414: ) -> typing.Generator[T_JSON_DICT,T_JSON_DICT,runtime.UniqueDebuggerId]:
L416: Enables debugger for the given page. Clients should not assume that the debugging has been
L419: :param max_scripts_cache_size: **(EXPERIMENTAL)** *(Optional)* The maximum size in bytes of collected scripts (not referenced by other heap objects) the debugger can hold. Puts no limit if parameter is omitted.
L420: :returns: Unique identifier of the debugger.
L426: 'method': 'Debugger.enable',
L430: return runtime.UniqueDebuggerId.from_json(json['debuggerId'])
L479: 'method': 'Debugger.evaluateOnCallFrame', |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/device_access.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Device request id. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/device_orientation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Clears the overridden Device Orientation. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/dom.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique DOM node identifier. | , __future__, dataclasses, enum, typing | L294: #: Deprecated, as the HTML Imports API has been removed (crbug.com/937746). |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/dom_debugger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | DOM breakpoint type. | , __future__, dataclasses, enum, typing | L6: # CDP domain: DOMDebugger
L135: 'method': 'DOMDebugger.getEventListeners',
L156: 'method': 'DOMDebugger.removeDOMBreakpoint',
L177: 'method': 'DOMDebugger.removeEventListenerBreakpoint',
L196: 'method': 'DOMDebugger.removeInstrumentationBreakpoint',
L213: 'method': 'DOMDebugger.removeXHRBreakpoint',
L232: 'method': 'DOMDebugger.setBreakOnCSPViolation',
L252: 'method': 'DOMDebugger.setDOMBreakpoint',
L273: 'method': 'DOMDebugger.setEventListenerBreakpoint',
L292: 'method': 'DOMDebugger.setInstrumentationBreakpoint',
L309: 'method': 'DOMDebugger.setXHRBreakpoint', |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/dom_snapshot.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Node in the DOM tree. | , __future__, dataclasses, enum, typing | L13: from . import dom_debugger
L98: event_listeners: typing.Optional[typing.List[dom_debugger.EventListener]] = None
L193: event_listeners=[dom_debugger.EventListener.from_json(i) for i in json['eventListeners']] if 'eventListeners' in json else None, |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/dom_storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | DOM Storage identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/emulation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Screen orientation. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/event_breakpoints.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sets breakpoint on particular native event.

    :param event_name: Instrumentation name to stop on. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/extensions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Storage areas. | , __future__, dataclasses, enum, typing | L37: --remote-debugging-pipe flag and the --enable-unsafe-extension-debugging
L58: Available if the client is connected using the --remote-debugging-pipe flag
L59: and the --enable-unsafe-extension-debugging. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/fed_cm.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Whether this is a sign-up or sign-in action for this account, i.e.
    whether this account has ever been used to sign in to this RP before. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/fetch.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique request identifier.
    Note that this does not identify individual HTTP requests that are part of
    a network request. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/file_system.py` | ❓ UNKNOWN | 2025-11-09 21:21 | :param bucket_file_system_locator:
    :returns: Returns the directory object at the path. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/headless_experimental.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Encoding options for a screenshot. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/heap_profiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Heap snapshot object id. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/indexed_db.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Database with an array of object stores. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/input_.py` | ❓ UNKNOWN | 2025-11-09 21:21 | UTC time in seconds, counted from January 1, 1970. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/inspector.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Disables inspector domain notifications. | , __future__, dataclasses, enum, typing | L37: Fired when remote debugging connection is about to be terminated. Contains detach reason.
L53: Fired when debugging target has crashed
L68: Fired when debugging target has reloaded after crash |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/io.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This is either obtained from another method or specified as ``blob:<uuid>`` where
    ``<uuid>`` is an UUID of a Blob. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/layer_tree.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique Layer identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/log.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Log entry. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/media.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Players will get an ID that is unique within the agent context. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/memory.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Memory pressure level. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/network.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Resource type as it was perceived by the rendering engine. | , __future__, dataclasses, enum, typing | L12: from . import debugger |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/overlay.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration data for drawing the source order of an elements children. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/page.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique frame identifier. | , __future__, dataclasses, enum, typing | L12: from . import debugger
L98: #: Id of scriptId's debugger.
L99: debugger_id: runtime.UniqueDebuggerId
L104: json['debuggerId'] = self.debugger_id.to_json()
L111: debugger_id=runtime.UniqueDebuggerId.from_json(json['debuggerId']), |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/performance.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Run-time execution metric. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/performance_timeline.py` | ❓ UNKNOWN | 2025-11-09 21:21 | See https://github.com/WICG/LargestContentfulPaint and largest_contentful_paint.idl | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/preload.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique id | , __future__, dataclasses, enum, typing | L71: #: TODO(https://crbug.com/1425354): Replace this property with structured error.
L356: TODO(https://crbug.com/1384419): revisit the list of PrefetchStatus and |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/profiler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Profile node. Holds callsite information, execution statistics and child nodes. | , __future__, dataclasses, enum, typing | L12: from . import debugger
L358: location: debugger.Location
L367: location=debugger.Location.from_json(json['location']),
L381: location: debugger.Location
L389: location=debugger.Location.from_json(json['location']), |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/pwa.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The following types are the replica of
    https://crsrc.org/c/chrome/browser/web_applications/proto/web_app_os_integration_state.proto;drc=9910d3be894c8f142c977ba1023f30a656bc13fc;l=67 | , __future__, dataclasses, enum, typing | L210: TODO(crbug.com/339454034): Check the existences of the input files.
L263: :param link_capturing: *(Optional)* If user allows the links clicked on by the user in the app's scope, or extended scope if the manifest has scope extensions and the flags ```DesktopPWAsLinkCapturingWithScopeExtensions```` and ````WebAppEnableScopeExtensions``` are enabled.  Note, the API does not support resetting the linkCapturing to the initial value, uninstalling and installing the web app again will reset it.  TODO(crbug.com/339453269): Setting this value on ChromeOS is not supported yet. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/runtime.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique script identifier. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/schema.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Description of the protocol domain. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/security.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An internal certificate ID value. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/service_worker.py` | ❓ UNKNOWN | 2025-11-09 21:21 | ServiceWorker registration. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/storage.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enum of possible storage types. | , __future__, dataclasses, enum, typing | L403: #: TODO(crbug.com/401011862): Consider updating this parameter to binary. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/system_info.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Describes a single graphics processor (GPU). | , __future__, dataclasses, enum, typing | L239: #: An optional array of GPU driver bug workarounds.
L240: driver_bug_workarounds: typing.List[str]
L260: json['driverBugWorkarounds'] = [i for i in self.driver_bug_workarounds]
L274: driver_bug_workarounds=[str(i) for i in json['driverBugWorkarounds']], |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/target.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Unique identifier of attached debugging session. | , __future__, dataclasses, enum, typing | L30: Unique identifier of attached debugging session.
L221: :param flatten: *(Optional)* Enables "flat" access to the session via specifying sessionId attribute in the commands. We plan to make this the default, deprecate non-flattened mode, and eventually retire it. See crbug.com/991325.
L282: - ``binding.send(json)`` - a method to send messages over the remote debugging protocol
L314: :param dispose_on_detach: **(EXPERIMENTAL)** *(Optional)* If specified, disposes this context when debugging session disconnects. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/tethering.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Request browser port binding.

    :param port: Port number to bind. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/tracing.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration for memory dump. Used only when "memory-infra" category is enabled. | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/util.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A decorator that registers a class as an event class. '''
    def decorate(cls):
        _event_parsers[method] = cls
        cls.event_class = method
        return cls
    return decorate


def parse_json_event(json: T_JSON_DICT) -> typing.Any: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/web_audio.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An unique ID for a graph object (AudioContext, AudioNode, AudioParam) in Web Audio API | , __future__, dataclasses, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/devtools/v142/web_authn.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enable the WebAuthn domain and start intercepting credential storage and
    retrieval with a virtual authenticator.

    :param enable_ui: *(Optional)* Whether to enable the WebAuthn user interface. Enabling the UI is recommended for debugging and demo purposes, as it is closer to the real experience. Disabling the UI is recommended for automated testing. Supported at the embedder's discretion if UI is available. Defaults to false. | , __future__, dataclasses, enum, typing | L255: :param enable_ui: *(Optional)* Whether to enable the WebAuthn user interface. Enabling the UI is recommended for debugging and demo purposes, as it is closer to the real experience. Disabling the UI is recommended for automated testing. Supported at the embedder's discretion if UI is available. Defaults to false. |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/driver_finder.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Driver finding class responsible for obtaining the correct driver and
    associated browser.

    Args:
        service: instance of the driver service class.
        options: instance of the browser options class. | logging, pathlib, selenium | L61: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/fedcm/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/fedcm/account.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents an account displayed in a FedCM account list.

    See: https://w3c-fedid.github.io/FedCM/#dictdef-identityprovideraccount
         https://w3c-fedid.github.io/FedCM/#webdriver-accountlist | enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/fedcm/dialog.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents a FedCM dialog that can be interacted with."""

    DIALOG_TYPE_ACCOUNT_LIST = "AccountChooser"
    DIALOG_TYPE_AUTO_REAUTH = "AutoReauthn"

    def __init__(self, driver) -> None:
        self._driver = driver

    @property
    def type(self) -> Optional[str]: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/keys.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Keys implementation."""


class Keys: |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/log.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This class allows access to logging APIs that use the new WebDriver Bidi
    protocol.

    This class is not to be used directly and should be used from the
    webdriver base classes. | collections, contextlib, importlib, json, pkgutil, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Enum of possible page load strategies.

    Selenium support following strategies:
        * normal (default) - waits for all resources to download
        * eager - DOM access is ready, but other resources like images may still be loading
        * none - does not block `WebDriver` at all

    Docs: https://www.selenium.dev/documentation/webdriver/drivers/options/#pageloadstrategy. | abc, enum, selenium, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/print_page_options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Descriptor which validates `height` and 'width' of page."""

    def __init__(self, name):
        self.name = name

    def __get__(self, obj, cls) -> Optional[float]:
        return obj._page.get(self.name, None)

    def __set__(self, obj, value) -> None:
        getattr(obj, "_validate_num_property")(self.name, value)
        obj._page[self.name] = value
        obj._print_options["page"] = obj._page


class _MarginSettingsDescriptor: | typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/proxy.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Proxy implementation."""

import warnings


class ProxyTypeFactory: | warnings | L70: # TODO: Remove ftpProxy in future version and remove deprecation warning
L88: ftpProxy = ""  # TODO: Remove ftpProxy in future version and remove deprecation warning
L102: # TODO: Remove ftpProxy in future version and remove deprecation warning
L139: # TODO: Remove ftpProxy in future version and remove deprecation warning
L190: # TODO: Remove ftpProxy in future version and remove deprecation warning |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/selenium_manager.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Wrapper for getting information from the Selenium Manager binaries.

    This implementation is still in beta, and may change. | json, logging, os, pathlib, platform, selenium, subprocess, sys, sysconfig, typing | L49: if logger.getEffectiveLevel() == logging.DEBUG:
L50: args.append("--debug")
L77: logger.debug("Selenium Manager set by env SE_MANAGER_PATH to: %s", env_path)
L104: logger.debug("Selenium Manager binary found at: %s", path)
L119: logger.debug("Executing process: %s", command)
L144: elif item["level"] in ["DEBUG", "INFO"]:
L145: logger.debug(item["message"]) |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The abstract base class for all service objects.  Services typically
    launch a child program in a new process as an interim process to
    communicate with a browser.

    Args:
        executable: install path of the executable.
        port: Port for the service to run on, defaults to 0 where the operating system will decide.
        log_output: (Optional) int representation of STDOUT/DEVNULL, any IO instance or String path to file.
        env: (Optional) Mapping of environment variables for the new process, defaults to `os.environ`.
        driver_path_env_key: (Optional) Environment variable to use to get the path to the driver executable. | abc, collections, errno, io, logging, os, selenium, subprocess, sys, time, typing, urllib | L229: logger.debug( |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/timeouts.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Get or set the value of the attributes listed below.

    _implicit_wait _page_load _script

    This does not set the value on the remote end. | typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Utility functions."""

import socket
import urllib.request
from collections.abc import Iterable
from typing import Optional, Union

from selenium.types import AnyKey
from selenium.webdriver.common.keys import Keys

_is_connectable_exceptions = (socket.error, ConnectionResetError)


def free_port() -> int: | collections, selenium, socket, typing, urllib | L161: # Todo: Does this even work? |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/virtual_authenticator.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Protocol to communicate with the authenticator."""

    CTAP2 = "ctap2"
    U2F = "ctap1/u2f"


class Transport(str, Enum): | base64, enum, functools, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/common/window.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The WindowTypes implementation."""


class WindowTypes: |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/edge/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/edge/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Initialize EdgeOptions with default settings."""
        super().__init__()
        self._use_webview = False

    @property
    def use_webview(self) -> bool: | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/edge/remote_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/edge/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping of
    `msedgedriver`.

    Args:
        executable_path: Install path of the msedgedriver executable, defaults to `msedgedriver`.
        port: Port for the service to run on, defaults to 0 where the operating system will decide.
        log_output: (Optional) int representation of STDOUT/DEVNULL, any IO instance or String path to file.
        service_args: (Optional) Sequence of args to be passed to the subprocess when launching the executable.
        env: (Optional) Mapping of environment variables for the new process, defaults to `os.environ`.
        driver_path_env_key: (Optional) Environment variable to use to get the path to the driver executable. | collections, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/edge/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the MSEdgeDriver and allows you to drive the browser."""

    def __init__(
        self,
        options: Optional[Options] = None,
        service: Optional[Service] = None,
        keep_alive: bool = True,
    ) -> None: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/firefox_binary.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Creates a new instance of Firefox binary.

        Args:
            firefox_path: Path to the Firefox executable. By default, it will be detected from the standard locations.
            log_file: A file object to redirect the firefox process output to. It can be sys.stdout.
                Please note that with parallel run the output won't be synchronous.
                By default, it will be redirected to /dev/null. | _winreg, os, selenium, shlex, shutil, subprocess, sys, time, typing_extensions, winreg |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/firefox_profile.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Exception for not well-formed add-on manifest files."""


class FirefoxProfile:
    DEFAULT_PREFERENCES = None

    def __init__(self, profile_directory=None): | base64, copy, io, json, os, re, selenium, shutil, sys, tempfile, typing_extensions, warnings, xml, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Returns the FirefoxBinary instance."""
        return FirefoxBinary(self._binary_location)

    @binary.setter
    @deprecated("use binary_location instead")
    def binary(self, new_binary: Union[str, FirefoxBinary]) -> None: | selenium, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/remote_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping of
    `geckodriver`.

    Args:
        executable_path: install path of the geckodriver executable, defaults to `geckodriver`.
        port: Port for the service to run on, defaults to 0 where the operating system will decide.
        service_args: (Optional) Sequence of args to be passed to the subprocess when launching the executable.
        log_output: (Optional) int representation of STDOUT/DEVNULL, any IO instance or String path to file.
        env: (Optional) Mapping of environment variables for the new process, defaults to `os.environ`.
        driver_path_env_key: (Optional) Environment variable to use to get the path to the driver executable. | collections, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the GeckoDriver and allows you to drive the browser."""

    CONTEXT_CHROME = "chrome"
    CONTEXT_CONTENT = "content"

    def __init__(
        self,
        options: Optional[Options] = None,
        service: Optional[Service] = None,
        keep_alive: bool = True,
    ) -> None: | base64, contextlib, io, os, selenium, typing, warnings, zipfile | L132: driver.install_addon("/path/to/firebug.xpi") |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/firefox/webdriver_prefs.json` | ❓ UNKNOWN | 2025-11-09 21:21 | Configuration file |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/ie/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/ie/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _IeOptionsDescriptor is an implementation of Descriptor Protocol.

    Any look-up or assignment to the below attributes in `Options` class will be intercepted
    by `__get__` and `__set__` method respectively.

    - `browser_attach_timeout`
    - `element_scroll_behavior`
    - `ensure_clean_session`
    - `file_upload_dialog_timeout`
    - `force_create_process_api`
    - `force_shell_windows_api`
    - `full_page_screenshot`
    - `ignore_protected_mode_settings`
    - `ignore_zoom_level`
    - `initial_browser_url`
    - `native_events`
    - `persistent_hover`
    - `require_window_focus`
    - `use_per_process_proxy`
    - `use_legacy_file_upload_dialog_handling`
    - `attach_to_edge_chrome`
    - `edge_executable_path`

    When an attribute lookup happens:

    Example:
        `self. browser_attach_timeout`
        `__get__` method does a dictionary look up in the dictionary `_options` in `Options` class
        and returns the value of key `browserAttachTimeout`

    When an attribute assignment happens:

    Example:
        `self.browser_attach_timeout` = 30
        `__set__` method sets/updates the value of the key `browserAttachTimeout` in `_options`
        dictionary in `Options` class. | enum, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/ie/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Object that manages the starting and stopping of the IEDriver."""

    def __init__(
        self,
        executable_path: Optional[str] = None,
        port: int = 0,
        host: Optional[str] = None,
        service_args: Optional[Sequence[str]] = None,
        log_level: Optional[str] = None,
        log_output: Optional[SubprocessStdAlias] = None,
        driver_path_env_key: Optional[str] = None,
        **kwargs,
    ) -> None: | collections, selenium, typing | L46: log_level: (Optional) Level of logging of service, may be "FATAL", "ERROR", "WARN", "INFO", "DEBUG", |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/ie/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the IEServerDriver and allows you to drive Internet
    Explorer. | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/bidi_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/client_config.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Gets and Sets Remote Server."""
    keep_alive = _ClientConfigDescriptor("_keep_alive") | base64, certifi, enum, os, selenium, socket, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/command.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Defines constants for the standard WebDriver commands.

    While these constants have no meaning in and of themselves, they are
    used to marshal commands through a service that implements WebDriver's
    remote wire protocol:

        https://w3c.github.io/webdriver/ |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/errorhandler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Maps each errorcode in ErrorCode object to corresponding exception.

    Please refer to https://www.w3.org/TR/webdriver2/#errors for w3c specification. | json, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/fedcm.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Gets the title of the dialog."""
        return self._driver.execute(Command.GET_FEDCM_TITLE)["value"].get("title")

    @property
    def subtitle(self) -> Optional[str]: | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/file_detector.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Used for identifying whether a sequence of chars represents the path to
    a file. | abc, contextlib, pathlib, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/locator_converter.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/mobile.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Set the network connection for the remote device.

        Example of setting airplane mode::

            driver.mobile.set_network_connection(driver.mobile.AIRPLANE_MODE) | selenium, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/remote_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A connection with the Remote WebDriver server.

    Communicates with the server using the WebDriver wire protocol:
    https://github.com/SeleniumHQ/selenium/wiki/JsonWireProtocol | base64, certifi, logging, os, selenium, socket, string, sys, typing, urllib, urllib3, warnings | L406: LOGGER.debug("%s %s %s", command_info[0], url, str(trimmed))
L439: LOGGER.debug("Remote response: status=%s \\| data=%s \\| headers=%s", response.status, data, response.headers)
L468: LOGGER.debug("Finished Request") |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/script_key.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | uuid |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/server.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Manage a Selenium Grid (Remote) Server in standalone mode.

    This class contains functionality for downloading the server and starting/stopping it.

    For more information on Selenium Grid, see:
        - https://www.selenium.dev/documentation/grid/getting_started/

    Parameters:
    -----------
    host : str
        Hostname or IP address to bind to (determined automatically if not specified)
    port : int or str
        Port to listen on (4444 if not specified)
    path : str
        Path/filename of existing server .jar file (Selenium Manager is used if not specified)
    version : str
        Version of server to download (latest version if not specified)
    log_level : str
        Logging level to control logging output ("INFO" if not specified)
        Available levels: "SEVERE", "WARNING", "INFO", "CONFIG", "FINE", "FINER", "FINEST"
    env: collections.abc.Mapping
        Mapping that defines the environment variables for the server process | collections, os, re, selenium, shutil, socket, subprocess, time, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/shadowroot.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Find an element inside a shadow root given a By strategy and
        locator.

        Parameters:
        -----------
        by : selenium.webdriver.common.by.By
            The locating strategy to use. Default is `By.ID`. Supported values include:
            - By.ID: Locate by element ID.
            - By.NAME: Locate by the `name` attribute.
            - By.XPATH: Locate by an XPath expression.
            - By.CSS_SELECTOR: Locate by a CSS selector.
            - By.CLASS_NAME: Locate by the `class` attribute.
            - By.TAG_NAME: Locate by the tag name (e.g., "input", "button").
            - By.LINK_TEXT: Locate a link element by its exact text.
            - By.PARTIAL_LINK_TEXT: Locate a link element by partial text match.
            - RelativeBy: Locate elements relative to a specified root element.

        Example:
        --------
        element = driver.find_element(By.ID, 'foo')

        Returns:
        -------
        WebElement
            The first matching `WebElement` found on the page. | hashlib, selenium | L26: # TODO: We should look and see  how we can create a search context like Java/.NET |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/switch_to.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Returns the element with focus, or BODY if nothing has focus.

        Example:
            element = driver.switch_to.active_element | selenium, typing, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | json, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The WebDriver implementation."""

import base64
import contextlib
import copy
import os
import pkgutil
import tempfile
import types
import warnings
import zipfile
from abc import ABCMeta
from base64 import b64decode, urlsafe_b64encode
from contextlib import asynccontextmanager, contextmanager
from importlib import import_module
from typing import Any, Optional, Union, cast

from selenium.common.exceptions import (
    InvalidArgumentException,
    JavascriptException,
    NoSuchCookieException,
    NoSuchElementException,
    WebDriverException,
)
from selenium.webdriver.common.bidi.browser import Browser
from selenium.webdriver.common.bidi.browsing_context import BrowsingContext
from selenium.webdriver.common.bidi.emulation import Emulation
from selenium.webdriver.common.bidi.input import Input
from selenium.webdriver.common.bidi.network import Network
from selenium.webdriver.common.bidi.permissions import Permissions
from selenium.webdriver.common.bidi.script import Script
from selenium.webdriver.common.bidi.session import Session
from selenium.webdriver.common.bidi.storage import Storage
from selenium.webdriver.common.bidi.webextension import WebExtension
from selenium.webdriver.common.by import By
from selenium.webdriver.common.fedcm.dialog import Dialog
from selenium.webdriver.common.options import ArgOptions, BaseOptions
from selenium.webdriver.common.print_page_options import PrintOptions
from selenium.webdriver.common.timeouts import Timeouts
from selenium.webdriver.common.virtual_authenticator import (
    Credential,
    VirtualAuthenticatorOptions,
    required_virtual_authenticator,
)
from selenium.webdriver.remote.bidi_connection import BidiConnection
from selenium.webdriver.remote.client_config import ClientConfig
from selenium.webdriver.remote.command import Command
from selenium.webdriver.remote.errorhandler import ErrorHandler
from selenium.webdriver.remote.fedcm import FedCM
from selenium.webdriver.remote.file_detector import FileDetector, LocalFileDetector
from selenium.webdriver.remote.locator_converter import LocatorConverter
from selenium.webdriver.remote.mobile import Mobile
from selenium.webdriver.remote.remote_connection import RemoteConnection
from selenium.webdriver.remote.script_key import ScriptKey
from selenium.webdriver.remote.shadowroot import ShadowRoot
from selenium.webdriver.remote.switch_to import SwitchTo
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.remote.websocket_connection import WebSocketConnection
from selenium.webdriver.support.relative_locator import RelativeBy

cdp = None


def import_cdp():
    global cdp
    if not cdp:
        cdp = import_module("selenium.webdriver.common.bidi.cdp")


def _create_caps(caps): | abc, base64, contextlib, copy, importlib, os, pkgutil, selenium, tempfile, types, typing, warnings, zipfile | L149: # https://bugs.python.org/issue38210 |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/webelement.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Abstract Base Class for WebElement.

    ABC's will allow custom types to be registered as a WebElement to
    pass type checks. | __future__, abc, base64, hashlib, io, os, pkgutil, selenium, warnings, zipfile | L34: # TODO: When moving to supporting python 3.9 as the minimum version we can |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/remote/websocket_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | json, logging, selenium, ssl, threading, time, websocket | L67: logger.debug(f"-> {data}"[: self._max_log_message_size])
L124: logger.debug(f"error: {error}")
L139: logger.debug(f"<- {message}"[: self._max_log_message_size]) |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/safari/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/safari/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _SafariOptionsDescriptor is an implementation of Descriptor protocol:

    : Any look-up or assignment to the below attributes in `Options` class will be intercepted
    by `__get__` and `__set__` method respectively.

    - `automatic_inspection`
    - `automatic_profiling`
    - `use_technology_preview`

    : When an attribute lookup happens,
    Example:
        `self.automatic_inspection`
        `__get__` method does a dictionary look up in the dictionary `_caps` of `Options` class
        and returns the value of key `safari:automaticInspection`
    : When an attribute assignment happens,
    Example:
        `self.automatic_inspection` = True
        `__set__` method sets/updates the value of the key `safari:automaticInspection` in `_caps`
        dictionary in `Options` class. | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/safari/permissions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The Permission implementation."""


class Permission: |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/safari/remote_connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium, typing | L45: self._commands["ATTACH_DEBUGGER"] = ("POST", "/session/$sessionId/apple/attach_debugger") |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/safari/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping of
    `safaridriver`  This is only supported on MAC OSX.

    Args:
        executable_path: install path of the safaridriver executable, defaults to `/usr/bin/safaridriver`.
        port: Port for the service to run on, defaults to 0 where the operating system will decide.
        service_args: (Optional) Sequence of args to be passed to the subprocess when launching the executable.
        env: (Optional) Mapping of environment variables for the new process, defaults to `os.environ`.
        enable_logging: (Optional) Enable logging of the service. Logs can be located at
            `~/Library/Logs/com.apple.WebDriver/`
        driver_path_env_key: (Optional) Environment variable to use to get the path to the driver executable. | collections, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/safari/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the SafariDriver and allows you to drive the browser."""

    def __init__(
        self,
        keep_alive=True,
        options: Optional[Options] = None,
        service: Optional[Service] = None,
    ) -> None: | selenium, typing | L107: def debug(self):
L108: self.execute("ATTACH_DEBUGGER")
L109: self.execute_script("debugger;") |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/abstract_event_listener.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Event listener must subclass and implement this fully or partially."""

    def before_navigate_to(self, url: str, driver) -> None:
        pass

    def after_navigate_to(self, url: str, driver) -> None:
        pass

    def before_navigate_back(self, driver) -> None:
        pass

    def after_navigate_back(self, driver) -> None:
        pass

    def before_navigate_forward(self, driver) -> None:
        pass

    def after_navigate_forward(self, driver) -> None:
        pass

    def before_find(self, by, value, driver) -> None:
        pass

    def after_find(self, by, value, driver) -> None:
        pass

    def before_click(self, element, driver) -> None:
        pass

    def after_click(self, element, driver) -> None:
        pass

    def before_change_value_of(self, element, driver) -> None:
        pass

    def after_change_value_of(self, element, driver) -> None:
        pass

    def before_execute_script(self, script, driver) -> None:
        pass

    def after_execute_script(self, script, driver) -> None:
        pass

    def before_close(self, driver) -> None:
        pass

    def after_close(self, driver) -> None:
        pass

    def before_quit(self, driver) -> None:
        pass

    def after_quit(self, driver) -> None:
        pass

    def on_exception(self, exception, driver) -> None:
        pass |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/color.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Color conversion support class.

    Example:

    ::

        from selenium.webdriver.support.color import Color

        print(Color.from_string("#00ff33").rgba)
        print(Color.from_string("rgb(1, 255, 3)").hex)
        print(Color.from_string("blue").rgba) | __future__, collections, re, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/event_firing_webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A wrapper around an arbitrary WebDriver instance which supports firing
    events. | selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/events.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/expected_conditions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | * Canned "Expected Conditions" which are generally useful within webdriver
 * tests. | collections, re, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/relative_locator.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Start searching for relative objects using a tag name.

    Args:
        tag_name: The DOM tag of element to start searching.

    Returns:
        RelativeBy: Use this object to create filters within a `find_elements` call.

    Raises:
        WebDriverException: If `tag_name` is None.

    Note:
        This method is deprecated and may be removed in future versions.
        Please use `locate_with` instead. | selenium, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/select.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Constructor. A check is made that the given element is, indeed, a
        SELECT tag. If it is not, then an UnexpectedTagNameException is thrown.

        Args:
            webelement: SELECT element to wrap

        Example:
            from selenium.webdriver.support.ui import Select \n
            Select(driver.find_element(By.TAG_NAME, "select")).select_by_index(2) | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/ui.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/support/wait.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Constructor, takes a WebDriver instance and timeout in seconds.

        Attributes:
        -----------
        driver
            - Instance of WebDriver (Ie, Firefox, Chrome or Remote) or
            a WebElement

        timeout
            - Number of seconds before timing out

        poll_frequency
            - Sleep interval between calls
            - By default, it is 0.5 second.

        ignored_exceptions
            - Iterable structure of exception classes ignored during calls.
            - By default, it contains NoSuchElementException only.

        Example:
        --------
        >>> from selenium.webdriver.common.by import By
        >>> from selenium.webdriver.support.wait import WebDriverWait
        >>> from selenium.common.exceptions import ElementNotVisibleException
        >>>
        >>> # Wait until the element is no longer visible
        >>> is_disappeared = WebDriverWait(driver, 30, 1, (ElementNotVisibleException))
        ...     .until_not(lambda x: x.find_element(By.ID, "someId").is_displayed()) | selenium, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/webkitgtk/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/webkitgtk/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Returns:
            The location of the browser binary, otherwise an empty string. | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/webkitgtk/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping of
    `WebKitWebDriver`.

    Args:
        executable_path: Install path of the WebKitWebDriver executable,
            defaults to the first `WebKitWebDriver` in `$PATH`.
        port: Port for the service to run on, defaults to 0 where the
            operating system will decide.
        service_args: (Optional) Sequence of args to be passed to the
            subprocess when launching the executable.
        log_output: (Optional) File path for the file to be opened and passed
            as the subprocess stdout/stderr handler.
        env: (Optional) Mapping of environment variables for the new process,
            defaults to `os.environ`. | collections, selenium, shutil, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/webkitgtk/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the WebKitGTKDriver and allows you to drive the browser."""

    def __init__(
        self,
        options=None,
        service: Optional[Service] = None,
    ): | http, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/wpewebkit/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/wpewebkit/options.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Returns the location of the browser binary otherwise an empty
        string. | selenium |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/wpewebkit/service.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A Service class that is responsible for the starting and stopping of
    `WPEWebDriver`.

    Args:
        executable_path: Install path of the WPEWebDriver executable, defaults
            to the first `WPEWebDriver` in `$PATH`.
        port: Port for the service to run on, defaults to 0 where the
            operating system will decide.
        service_args: (Optional) Sequence of args to be passed to the
            subprocess when launching the executable.
        log_output: (Optional) File path for the file to be opened and passed
            as the subprocess stdout/stderr handler.
        env: (Optional) Mapping of environment variables for the new process,
            defaults to `os.environ`. | collections, selenium, shutil, typing |  |
| `blackboard-agent/venv/Lib/site-packages/selenium/webdriver/wpewebkit/webdriver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Controls the WPEWebKitDriver and allows you to drive the browser."""

    def __init__(
        self,
        options=None,
        service: Optional[Service] = None,
    ): | http, selenium, typing |  |
| `blackboard-agent/venv/Lib/site-packages/sniffio/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Top-level package for sniffio."""

__all__ = [
    "current_async_library",
    "AsyncLibraryNotFoundError",
    "current_async_library_cvar",
    "thread_local",
]

from ._version import __version__

from ._impl import (
    current_async_library,
    AsyncLibraryNotFoundError,
    current_async_library_cvar,
    thread_local,
) |  |  |
| `blackboard-agent/venv/Lib/site-packages/sniffio/_impl.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Detect which async library is currently running.

    The following libraries are currently supported:

    ================   ===========  ============================
    Library             Requires     Magic string
    ================   ===========  ============================
    **Trio**            Trio v0.6+   ``"trio"``
    **Curio**           -            ``"curio"``
    **asyncio**                      ``"asyncio"``
    **Trio-asyncio**    v0.8.2+     ``"trio"`` or ``"asyncio"``,
                                    depending on current mode
    ================   ===========  ============================

    Returns:
      A string like ``"trio"``.

    Raises:
      AsyncLibraryNotFoundError: if called from synchronous context,
        or if the current async library was not recognized.

    Examples:

        .. code-block:: python3

           from sniffio import current_async_library

           async def generic_sleep(seconds):
               library = current_async_library()
               if library == "trio":
                   import trio
                   await trio.sleep(seconds)
               elif library == "asyncio":
                   import asyncio
                   await asyncio.sleep(seconds)
               # ... and so on ...
               else:
                   raise RuntimeError(f"Unsupported library {library!r}") | asyncio, contextvars, curio, sniffio, sys, threading, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/sniffio/_tests/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/sniffio/_tests/test_sniffio.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  | , asyncio, curio, os, pytest, sys |  |
| `blackboard-agent/venv/Lib/site-packages/sniffio/_version.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/socks.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Socket_err contains original socket.error exception."""
    def __init__(self, msg, socket_err=None):
        self.msg = msg
        self.socket_err = socket_err

        if socket_err:
            self.msg += ": {}".format(socket_err)

    def __str__(self):
        return self.msg


class GeneralProxyError(ProxyError):
    pass


class ProxyConnectionError(ProxyError):
    pass


class SOCKS5AuthError(ProxyError):
    pass


class SOCKS5Error(ProxyError):
    pass


class SOCKS4Error(ProxyError):
    pass


class HTTPError(ProxyError):
    pass

SOCKS4_ERRORS = {
    0x5B: "Request rejected or failed",
    0x5C: ("Request rejected because SOCKS server cannot connect to identd on"
           " the client"),
    0x5D: ("Request rejected because the client program and identd report"
           " different user-ids")
}

SOCKS5_ERRORS = {
    0x01: "General SOCKS server failure",
    0x02: "Connection not allowed by ruleset",
    0x03: "Network unreachable",
    0x04: "Host unreachable",
    0x05: "Connection refused",
    0x06: "TTL expired",
    0x07: "Command not supported, or protocol error",
    0x08: "Address type not supported"
}

DEFAULT_PORTS = {SOCKS4: 1080, SOCKS5: 1080, HTTP: 8080}


def set_default_proxy(proxy_type=None, addr=None, port=None, rdns=True,
                      username=None, password=None): | base64, collections, errno, functools, io, logging, os, socket, struct, sys, win_inet_pton |  |
| `blackboard-agent/venv/Lib/site-packages/sockshandler.py` | ❓ UNKNOWN | 2025-11-09 21:21 | SocksiPy + urllib2 handler

version: 0.3
author: e<e@tr0ll.in>

This module provides a Handler which you can use with urllib2 to allow it to tunnel your connection through a socks.sockssocket socket, with out monkey patching the original socket... | http, httplib, socket, socks, ssl, sys, urllib, urllib2 |  |
| `blackboard-agent/venv/Lib/site-packages/sortedcontainers/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sorted Containers -- Sorted List, Sorted Dict, Sorted Set

Sorted Containers is an Apache2 licensed containers library, written in
pure-Python, and fast as C-extensions.

Python's standard library is great until you need a sorted collections
type. Many will attest that you can get really far without one, but the moment
you **really need** a sorted list, dict, or set, you're faced with a dozen
different implementations, most using C-extensions without great documentation
and benchmarking.

In Python, we can do better. And we can do it in pure-Python!

::

    >>> from sortedcontainers import SortedList
    >>> sl = SortedList(['e', 'a', 'c', 'd', 'b'])
    >>> sl
    SortedList(['a', 'b', 'c', 'd', 'e'])
    >>> sl *= 1000000
    >>> sl.count('c')
    1000000
    >>> sl[-3:]
    ['e', 'e', 'e']
    >>> from sortedcontainers import SortedDict
    >>> sd = SortedDict({'c': 3, 'a': 1, 'b': 2})
    >>> sd
    SortedDict({'a': 1, 'b': 2, 'c': 3})
    >>> sd.popitem(index=-1)
    ('c', 3)
    >>> from sortedcontainers import SortedSet
    >>> ss = SortedSet('abracadabra')
    >>> ss
    SortedSet(['a', 'b', 'c', 'd', 'r'])
    >>> ss.bisect_left('c')
    2

Sorted Containers takes all of the work out of Python sorted types - making
your deployment and use of Python easy. There's no need to install a C compiler
or pre-build and distribute custom extensions. Performance is a feature and
testing has 100% coverage with unit tests and hours of stress.

:copyright: (c) 2014-2019 by Grant Jenks.
:license: Apache 2.0, see LICENSE for more details. |  |  |
| `blackboard-agent/venv/Lib/site-packages/sortedcontainers/sorteddict.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sorted Dict
==============

:doc:`Sorted Containers<index>` is an Apache2 licensed Python sorted
collections library, written in pure-Python, and fast as C-extensions. The
:doc:`introduction<introduction>` is the best way to get started.

Sorted dict implementations:

.. currentmodule:: sortedcontainers

* :class:`SortedDict`
* :class:`SortedKeysView`
* :class:`SortedItemsView`
* :class:`SortedValuesView` | , collections, itertools, sys, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/sortedcontainers/sortedlist.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sorted List
==============

:doc:`Sorted Containers<index>` is an Apache2 licensed Python sorted
collections library, written in pure-Python, and fast as C-extensions. The
:doc:`introduction<introduction>` is the best way to get started.

Sorted list implementations:

.. currentmodule:: sortedcontainers

* :class:`SortedList`
* :class:`SortedKeyList` | __future__, _dummy_thread, _thread, bisect, collections, dummy_thread, functools, itertools, math, operator, sys, textwrap, thread, traceback |  |
| `blackboard-agent/venv/Lib/site-packages/sortedcontainers/sortedset.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sorted Set
=============

:doc:`Sorted Containers<index>` is an Apache2 licensed Python sorted
collections library, written in pure-Python, and fast as C-extensions. The
:doc:`introduction<introduction>` is the best way to get started.

Sorted set implementations:

.. currentmodule:: sortedcontainers

* :class:`SortedSet` | , collections, itertools, operator, textwrap |  |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Soup Sieve.

A CSS selector filter for BeautifulSoup4.

MIT License

Copyright (c) 2018 Isaac Muse

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE. | , __future__, bs4, typing | L33: from .util import DEBUG, SelectorSyntaxError  # noqa: F401
L38: 'DEBUG', 'SelectorSyntaxError', 'SoupSieve', |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/__meta__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Meta related things."""
from __future__ import annotations
from collections import namedtuple
import re

RE_VER = re.compile(
    r'''(?x)
    (?P<major>\d+)(?:\.(?P<minor>\d+))?(?:\.(?P<micro>\d+))?
    (?:(?P<type>a\\|b\\|rc)(?P<pre>\d+))?
    (?:\.post(?P<post>\d+))?
    (?:\.dev(?P<dev>\d+))?
    '''
)

REL_MAP = {
    ".dev": "",
    ".dev-alpha": "a",
    ".dev-beta": "b",
    ".dev-candidate": "rc",
    "alpha": "a",
    "beta": "b",
    "candidate": "rc",
    "final": ""
}

DEV_STATUS = {
    ".dev": "2 - Pre-Alpha",
    ".dev-alpha": "2 - Pre-Alpha",
    ".dev-beta": "2 - Pre-Alpha",
    ".dev-candidate": "2 - Pre-Alpha",
    "alpha": "3 - Alpha",
    "beta": "4 - Beta",
    "candidate": "4 - Beta",
    "final": "5 - Production/Stable"
}

PRE_REL_MAP = {"a": 'alpha', "b": 'beta', "rc": 'candidate'}


class Version(namedtuple("Version", ["major", "minor", "micro", "release", "pre", "post", "dev"])): | __future__, collections, re |  |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/css_match.py` | ❓ UNKNOWN | 2025-11-09 19:11 | CSS matcher."""
from __future__ import annotations
from datetime import datetime
from . import util
import re
from . import css_types as ct
import unicodedata
import bs4
from typing import Iterator, Iterable, Any, Callable, Sequence, Any, cast  # noqa: F401, F811

# Empty tag pattern (whitespace okay)
RE_NOT_EMPTY = re.compile('[^ \t\r\n\f]')

RE_NOT_WS = re.compile('[^ \t\r\n\f]+')

# Relationships
REL_PARENT = ' '
REL_CLOSE_PARENT = '>'
REL_SIBLING = '~'
REL_CLOSE_SIBLING = '+'

# Relationships for :has() (forward looking)
REL_HAS_PARENT = ': '
REL_HAS_CLOSE_PARENT = ':>'
REL_HAS_SIBLING = ':~'
REL_HAS_CLOSE_SIBLING = ':+'

NS_XHTML = 'http://www.w3.org/1999/xhtml'
NS_XML = 'http://www.w3.org/XML/1998/namespace'

DIR_FLAGS = ct.SEL_DIR_LTR \\| ct.SEL_DIR_RTL
RANGES = ct.SEL_IN_RANGE \\| ct.SEL_OUT_OF_RANGE

DIR_MAP = {
    'ltr': ct.SEL_DIR_LTR,
    'rtl': ct.SEL_DIR_RTL,
    'auto': 0
}

RE_NUM = re.compile(r"^(?P<value>-?(?:[0-9]{1,}(\.[0-9]+)?\\|\.[0-9]+))$")
RE_TIME = re.compile(r'^(?P<hour>[0-9]{2}):(?P<minutes>[0-9]{2})$')
RE_MONTH = re.compile(r'^(?P<year>[0-9]{4,})-(?P<month>[0-9]{2})$')
RE_WEEK = re.compile(r'^(?P<year>[0-9]{4,})-W(?P<week>[0-9]{2})$')
RE_DATE = re.compile(r'^(?P<year>[0-9]{4,})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})$')
RE_DATETIME = re.compile(
    r'^(?P<year>[0-9]{4,})-(?P<month>[0-9]{2})-(?P<day>[0-9]{2})T(?P<hour>[0-9]{2}):(?P<minutes>[0-9]{2})$'
)
RE_WILD_STRIP = re.compile(r'(?:(?:-\*-)(?:\*(?:-\\|$))*\\|-\*$)')

MONTHS_30 = (4, 6, 9, 11)  # April, June, September, and November
FEB = 2
SHORT_MONTH = 30
LONG_MONTH = 31
FEB_MONTH = 28
FEB_LEAP_MONTH = 29
DAYS_IN_WEEK = 7


class _FakeParent: | , __future__, bs4, datetime, re, typing, unicodedata |  |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/css_parser.py` | ❓ UNKNOWN | 2025-11-09 19:11 | CSS selector parser."""
from __future__ import annotations
import re
from functools import lru_cache
from . import util
from . import css_match as cm
from . import css_types as ct
from .util import SelectorSyntaxError
import warnings
from typing import Match, Any, Iterator, cast

UNICODE_REPLACEMENT_CHAR = 0xFFFD

# Simple pseudo classes that take no parameters
PSEUDO_SIMPLE = {
    ":any-link",
    ":empty",
    ":first-child",
    ":first-of-type",
    ":in-range",
    ":open",
    ":out-of-range",
    ":last-child",
    ":last-of-type",
    ":link",
    ":only-child",
    ":only-of-type",
    ":root",
    ':checked',
    ':default',
    ':disabled',
    ':enabled',
    ':indeterminate',
    ':optional',
    ':placeholder-shown',
    ':read-only',
    ':read-write',
    ':required',
    ':scope',
    ':defined',
    ':muted'
}

# Supported, simple pseudo classes that match nothing in the Soup Sieve environment
PSEUDO_SIMPLE_NO_MATCH = {
    ':active',
    ':autofill',
    ':buffering',
    ':current',
    ':focus',
    ':focus-visible',
    ':focus-within',
    ':fullscreen',
    ':future',
    ':host',
    ':hover',
    ':local-link',
    ':past',
    ':paused',
    ':picture-in-picture',
    ':playing',
    ':popover-open',
    ':seeking',
    ':stalled',
    ':target',
    ':target-within',
    ':user-invalid',
    ':volume-locked',
    ':visited'
}

# Complex pseudo classes that take selector lists
PSEUDO_COMPLEX = {
    ':contains',
    ':-soup-contains',
    ':-soup-contains-own',
    ':has',
    ':is',
    ':matches',
    ':not',
    ':where'
}

PSEUDO_COMPLEX_NO_MATCH = {
    ':current',
    ':host',
    ':host-context'
}

# Complex pseudo classes that take very specific parameters and are handled special
PSEUDO_SPECIAL = {
    ':dir',
    ':lang',
    ':nth-child',
    ':nth-last-child',
    ':nth-last-of-type',
    ':nth-of-type'
}

PSEUDO_SUPPORTED = PSEUDO_SIMPLE \\| PSEUDO_SIMPLE_NO_MATCH \\| PSEUDO_COMPLEX \\| PSEUDO_COMPLEX_NO_MATCH \\| PSEUDO_SPECIAL

# Sub-patterns parts
# Whitespace
NEWLINE = r'(?:\r\n\\|(?!\r\n)[\n\f\r])'
WS = fr'(?:[ \t]\\|{NEWLINE})'
# Comments
COMMENTS = r'(?:/\*[^*]*\*+(?:[^/*][^*]*\*+)*/)'
# Whitespace with comments included
WSC = fr'(?:{WS}\\|{COMMENTS})'
# CSS escapes
CSS_ESCAPES = fr'(?:\\(?:[a-f0-9]{{1,6}}{WS}?\\|[^\r\n\f]\\|$))'
CSS_STRING_ESCAPES = fr'(?:\\(?:[a-f0-9]{{1,6}}{WS}?\\|[^\r\n\f]\\|$\\|{NEWLINE}))'
# CSS Identifier
IDENTIFIER = fr'''
(?:(?:-?(?:[^\x00-\x2f\x30-\x40\x5B-\x5E\x60\x7B-\x9f]\\|{CSS_ESCAPES})+\\|--)
(?:[^\x00-\x2c\x2e\x2f\x3A-\x40\x5B-\x5E\x60\x7B-\x9f]\\|{CSS_ESCAPES})*)
'''
# `nth` content
NTH = fr'(?:[-+])?(?:[0-9]+n?\\|n)(?:(?<=n){WSC}*(?:[-+]){WSC}*(?:[0-9]+))?'
# Value: quoted string or identifier
VALUE = fr'''(?:"(?:\\(?:.\\|{NEWLINE})\\|[^\\"\r\n\f]+)*?"\\|'(?:\\(?:.\\|{NEWLINE})\\|[^\\'\r\n\f]+)*?'\\|{IDENTIFIER}+)'''
# Attribute value comparison. `!=` is handled special as it is non-standard.
ATTR = fr'(?:{WSC}*(?P<cmp>[!~^\\|*$]?=){WSC}*(?P<value>{VALUE})(?:{WSC}*(?P<case>[is]))?)?{WSC}*\]'

# Selector patterns
# IDs (`#id`)
PAT_ID = fr'\#{IDENTIFIER}'
# Classes (`.class`)
PAT_CLASS = fr'\.{IDENTIFIER}'
# Prefix:Tag (`prefix\\|tag`)
PAT_TAG = fr'(?P<tag_ns>(?:{IDENTIFIER}\\|\*)?\\\|)?(?P<tag_name>{IDENTIFIER}\\|\*)'
# Attributes (`[attr]`, `[attr=value]`, etc.)
PAT_ATTR = fr'\[{WSC}*(?P<attr_ns>(?:{IDENTIFIER}\\|\*)?\\\|)?(?P<attr_name>{IDENTIFIER}){ATTR}'
# Pseudo class (`:pseudo-class`, `:pseudo-class(`)
PAT_PSEUDO_CLASS = fr'(?P<name>:{IDENTIFIER})(?P<open>\({WSC}*)?'
# Pseudo class special patterns. Matches `:pseudo-class(` for special case pseudo classes.
PAT_PSEUDO_CLASS_SPECIAL = fr'(?P<name>:{IDENTIFIER})(?P<open>\({WSC}*)'
# Custom pseudo class (`:--custom-pseudo`)
PAT_PSEUDO_CLASS_CUSTOM = fr'(?P<name>:(?=--){IDENTIFIER})'
# Nesting ampersand selector. Matches `&`
PAT_AMP = r'&'
# Closing pseudo group (`)`)
PAT_PSEUDO_CLOSE = fr'{WSC}*\)'
# Pseudo element (`::pseudo-element`)
PAT_PSEUDO_ELEMENT = fr':{PAT_PSEUDO_CLASS}'
# At rule (`@page`, etc.) (not supported)
PAT_AT_RULE = fr'@P{IDENTIFIER}'
# Pseudo class `nth-child` (`:nth-child(an+b [of S]?)`, `:first-child`, etc.)
PAT_PSEUDO_NTH_CHILD = fr'''
(?P<pseudo_nth_child>{PAT_PSEUDO_CLASS_SPECIAL}
(?P<nth_child>{NTH}\\|even\\|odd))(?:{WSC}*\)\\|(?P<of>{COMMENTS}*{WS}{WSC}*of{COMMENTS}*{WS}{WSC}*))
'''
# Pseudo class `nth-of-type` (`:nth-of-type(an+b)`, `:first-of-type`, etc.)
PAT_PSEUDO_NTH_TYPE = fr'''
(?P<pseudo_nth_type>{PAT_PSEUDO_CLASS_SPECIAL}
(?P<nth_type>{NTH}\\|even\\|odd)){WSC}*\)
'''
# Pseudo class language (`:lang("*-de", en)`)
PAT_PSEUDO_LANG = fr'{PAT_PSEUDO_CLASS_SPECIAL}(?P<values>{VALUE}(?:{WSC}*,{WSC}*{VALUE})*){WSC}*\)'
# Pseudo class direction (`:dir(ltr)`)
PAT_PSEUDO_DIR = fr'{PAT_PSEUDO_CLASS_SPECIAL}(?P<dir>ltr\\|rtl){WSC}*\)'
# Combining characters (`>`, `~`, ` `, `+`, `,`)
PAT_COMBINE = fr'{WSC}*?(?P<relation>[,+>~]\\|{WS}(?![,+>~])){WSC}*'
# Extra: Contains (`:contains(text)`)
PAT_PSEUDO_CONTAINS = fr'{PAT_PSEUDO_CLASS_SPECIAL}(?P<values>{VALUE}(?:{WSC}*,{WSC}*{VALUE})*){WSC}*\)'

# Regular expressions
# CSS escape pattern
RE_CSS_ESC = re.compile(fr'(?:(\\[a-f0-9]{{1,6}}{WSC}?)\\|(\\[^\r\n\f])\\|(\\$))', re.I)
RE_CSS_STR_ESC = re.compile(fr'(?:(\\[a-f0-9]{{1,6}}{WS}?)\\|(\\[^\r\n\f])\\|(\\$)\\|(\\{NEWLINE}))', re.I)
# Pattern to break up `nth` specifiers
RE_NTH = re.compile(fr'(?P<s1>[-+])?(?P<a>[0-9]+n?\\|n)(?:(?<=n){WSC}*(?P<s2>[-+]){WSC}*(?P<b>[0-9]+))?', re.I)
# Pattern to iterate multiple values.
RE_VALUES = re.compile(fr'(?:(?P<value>{VALUE})\\|(?P<split>{WSC}*,{WSC}*))', re.X)
# Whitespace checks
RE_WS = re.compile(WS)
RE_WS_BEGIN = re.compile(fr'^{WSC}*')
RE_WS_END = re.compile(fr'{WSC}*$')
RE_CUSTOM = re.compile(fr'^{PAT_PSEUDO_CLASS_CUSTOM}$', re.X)

# Constants
# List split token
COMMA_COMBINATOR = ','
# Relation token for descendant
WS_COMBINATOR = " "

# Parse flags
FLG_PSEUDO = 0x01
FLG_NOT = 0x02
FLG_RELATIVE = 0x04
FLG_DEFAULT = 0x08
FLG_HTML = 0x10
FLG_INDETERMINATE = 0x20
FLG_OPEN = 0x40
FLG_IN_RANGE = 0x80
FLG_OUT_OF_RANGE = 0x100
FLG_PLACEHOLDER_SHOWN = 0x200
FLG_FORGIVE = 0x400

# Maximum cached patterns to store
_MAXCACHE = 500


@lru_cache(maxsize=_MAXCACHE)
def _cached_css_compile(
    pattern: str,
    namespaces: ct.Namespaces \\| None,
    custom: ct.CustomSelectors \\| None,
    flags: int
) -> cm.SoupSieve: | , __future__, functools, re, typing, warnings | L469: self.debug = self.flags & util.DEBUG |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/css_types.py` | ❓ UNKNOWN | 2025-11-09 19:11 | CSS selector structure items."""
from __future__ import annotations
import copyreg
from .pretty import pretty
from typing import Any, Iterator, Hashable, Pattern, Iterable, Mapping

__all__ = (
    'Selector',
    'SelectorNull',
    'SelectorTag',
    'SelectorAttribute',
    'SelectorContains',
    'SelectorNth',
    'SelectorLang',
    'SelectorList',
    'Namespaces',
    'CustomSelectors'
)


SEL_EMPTY = 0x1
SEL_ROOT = 0x2
SEL_DEFAULT = 0x4
SEL_INDETERMINATE = 0x8
SEL_SCOPE = 0x10
SEL_DIR_LTR = 0x20
SEL_DIR_RTL = 0x40
SEL_IN_RANGE = 0x80
SEL_OUT_OF_RANGE = 0x100
SEL_DEFINED = 0x200
SEL_PLACEHOLDER_SHOWN = 0x400


class Immutable: | , __future__, copyreg, typing |  |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/pretty.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Format a pretty string of a `SoupSieve` object for easy debugging.

This won't necessarily support all types and such, and definitely
not support custom outputs.

It is mainly geared towards our types as the `SelectorList`
object is a beast to look at without some indentation and newlines.
The format and various output types is fairly known (though it
hasn't been tested extensively to make sure we aren't missing corners).

Example:
-------
```
>>> import soupsieve as sv
>>> sv.compile('this > that.class[name=value]').selectors.pretty()
SelectorList(
    selectors=(
        Selector(
            tag=SelectorTag(
                name='that',
                prefix=None),
            ids=(),
            classes=(
                'class',
                ),
            attributes=(
                SelectorAttribute(
                    attribute='name',
                    prefix='',
                    pattern=re.compile(
                        '^value$'),
                    xml_type_pattern=None),
                ),
            nth=(),
            selectors=(),
            relation=SelectorList(
                selectors=(
                    Selector(
                        tag=SelectorTag(
                            name='this',
                            prefix=None),
                        ids=(),
                        classes=(),
                        attributes=(),
                        nth=(),
                        selectors=(),
                        relation=SelectorList(
                            selectors=(),
                            is_not=False,
                            is_html=False),
                        rel_type='>',
                        contains=(),
                        lang=(),
                        flags=0),
                    ),
                is_not=False,
                is_html=False),
            rel_type=None,
            contains=(),
            lang=(),
            flags=0),
        ),
    is_not=False,
    is_html=False)
``` | __future__, re, typing | L2: Format a pretty string of a `SoupSieve` object for easy debugging. |
| `blackboard-agent/venv/Lib/site-packages/soupsieve/util.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Utility."""
from __future__ import annotations
from functools import wraps, lru_cache
import warnings
import re
from typing import Callable, Any

DEBUG = 0x00001

RE_PATTERN_LINE_SPLIT = re.compile(r'(?:\r\n\\|(?!\r\n)[\n\r])\\|$')

UC_A = ord('A')
UC_Z = ord('Z')


@lru_cache(maxsize=512)
def lower(string: str) -> str: | __future__, functools, re, typing, warnings | L8: DEBUG = 0x00001 |
| `blackboard-agent/venv/Lib/site-packages/trio/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Trio - A friendly Python library for async concurrency and I/O"""

from __future__ import annotations

from typing import TYPE_CHECKING

# General layout:
#
# trio/_core/... is the self-contained core library. It does various
# shenanigans to export a consistent "core API", but parts of the core API are
# too low-level to be recommended for regular use.
#
# trio/*.py define a set of more usable tools on top of this. They import from
# trio._core and from each other.
#
# This file pulls together the friendly public API, by re-exporting the more
# innocuous bits of the _core API + the higher-level tools from trio/*.py.
#
# Uses `from x import y as y` for compatibility with `pyright --verifytypes` (#2625)
#
# must be imported early to avoid circular import
from ._core import TASK_STATUS_IGNORED as TASK_STATUS_IGNORED  # isort: split

# Submodules imported by default
from . import abc, from_thread, lowlevel, socket, to_thread
from ._channel import (
    MemoryChannelStatistics as MemoryChannelStatistics,
    MemoryReceiveChannel as MemoryReceiveChannel,
    MemorySendChannel as MemorySendChannel,
    as_safe_channel as as_safe_channel,
    open_memory_channel as open_memory_channel,
)
from ._core import (
    BrokenResourceError as BrokenResourceError,
    BusyResourceError as BusyResourceError,
    Cancelled as Cancelled,
    CancelScope as CancelScope,
    ClosedResourceError as ClosedResourceError,
    EndOfChannel as EndOfChannel,
    Nursery as Nursery,
    RunFinishedError as RunFinishedError,
    TaskStatus as TaskStatus,
    TrioInternalError as TrioInternalError,
    WouldBlock as WouldBlock,
    current_effective_deadline as current_effective_deadline,
    current_time as current_time,
    open_nursery as open_nursery,
    run as run,
)
from ._deprecate import TrioDeprecationWarning as TrioDeprecationWarning
from ._dtls import (
    DTLSChannel as DTLSChannel,
    DTLSChannelStatistics as DTLSChannelStatistics,
    DTLSEndpoint as DTLSEndpoint,
)
from ._file_io import open_file as open_file, wrap_file as wrap_file
from ._highlevel_generic import (
    StapledStream as StapledStream,
    aclose_forcefully as aclose_forcefully,
)
from ._highlevel_open_tcp_listeners import (
    open_tcp_listeners as open_tcp_listeners,
    serve_tcp as serve_tcp,
)
from ._highlevel_open_tcp_stream import open_tcp_stream as open_tcp_stream
from ._highlevel_open_unix_stream import open_unix_socket as open_unix_socket
from ._highlevel_serve_listeners import serve_listeners as serve_listeners
from ._highlevel_socket import (
    SocketListener as SocketListener,
    SocketStream as SocketStream,
)
from ._highlevel_ssl_helpers import (
    open_ssl_over_tcp_listeners as open_ssl_over_tcp_listeners,
    open_ssl_over_tcp_stream as open_ssl_over_tcp_stream,
    serve_ssl_over_tcp as serve_ssl_over_tcp,
)
from ._path import Path as Path, PosixPath as PosixPath, WindowsPath as WindowsPath
from ._signals import open_signal_receiver as open_signal_receiver
from ._ssl import (
    NeedHandshakeError as NeedHandshakeError,
    SSLListener as SSLListener,
    SSLStream as SSLStream,
)
from ._subprocess import Process as Process, run_process as run_process
from ._sync import (
    CapacityLimiter as CapacityLimiter,
    CapacityLimiterStatistics as CapacityLimiterStatistics,
    Condition as Condition,
    ConditionStatistics as ConditionStatistics,
    Event as Event,
    EventStatistics as EventStatistics,
    Lock as Lock,
    LockStatistics as LockStatistics,
    Semaphore as Semaphore,
    StrictFIFOLock as StrictFIFOLock,
)
from ._timeouts import (
    TooSlowError as TooSlowError,
    fail_after as fail_after,
    fail_at as fail_at,
    move_on_after as move_on_after,
    move_on_at as move_on_at,
    sleep as sleep,
    sleep_forever as sleep_forever,
    sleep_until as sleep_until,
)
from ._version import __version__ as __version__

# Not imported by default, but mentioned here so static analysis tools like
# pylint will know that it exists.
if TYPE_CHECKING:
    from . import testing

from . import _deprecate as _deprecate

_deprecate.deprecate_attributes(__name__, {})

# Having the public path in .__module__ attributes is important for:
# - exception names in printed tracebacks
# - sphinx :show-inheritance:
# - deprecation warnings
# - pickle
# - probably other stuff
from ._util import fixup_module_metadata

fixup_module_metadata(__name__, globals())
fixup_module_metadata(lowlevel.__name__, lowlevel.__dict__)
fixup_module_metadata(socket.__name__, socket.__dict__)
fixup_module_metadata(abc.__name__, abc.__dict__)
fixup_module_metadata(from_thread.__name__, from_thread.__dict__)
fixup_module_metadata(to_thread.__name__, to_thread.__dict__)
del fixup_module_metadata
del TYPE_CHECKING | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/__main__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_abc.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The interface for custom run loop clocks."""

    __slots__ = ()

    @abstractmethod
    def start_clock(self) -> None: | , __future__, abc, socket, trio, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_channel.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Open a channel for passing objects between tasks within a process.

    Memory channels are lightweight, cheap to allocate, and entirely
    in-memory. They don't involve any operating-system resources, or any kind
    of serialization. They just pass Python objects directly between tasks
    (with a possible stop in an internal buffer along the way).

    Channel objects can be closed by calling `~trio.abc.AsyncResource.aclose`
    or using ``async with``. They are *not* automatically closed when garbage
    collected. Closing memory channels isn't mandatory, but it is generally a
    good idea, because it helps avoid situations where tasks get stuck waiting
    on a channel when there's no-one on the other side. See
    :ref:`channel-shutdown` for details.

    Memory channel operations are all atomic with respect to
    cancellation, either `~trio.abc.ReceiveChannel.receive` will
    successfully return an object, or it will raise :exc:`Cancelled`
    while leaving the channel unchanged.

    Args:
      max_buffer_size (int or math.inf): The maximum number of items that can
        be buffered in the channel before :meth:`~trio.abc.SendChannel.send`
        blocks. Choosing a sensible value here is important to ensure that
        backpressure is communicated promptly and avoid unnecessary latency;
        see :ref:`channel-buffering` for more details. If in doubt, use 0.

    Returns:
      A pair ``(send_channel, receive_channel)``. If you have
      trouble remembering which order these go in, remember: data
      flows from left → right.

    In addition to the standard channel methods, all memory channel objects
    provide a ``statistics()`` method, which returns an object with the
    following fields:

    * ``current_buffer_used``: The number of items currently stored in the
      channel buffer.
    * ``max_buffer_size``: The maximum number of items allowed in the buffer,
      as passed to :func:`open_memory_channel`.
    * ``open_send_channels``: The number of open
      :class:`MemorySendChannel` endpoints pointing to this channel.
      Initially 1, but can be increased by
      :meth:`MemorySendChannel.clone`.
    * ``open_receive_channels``: Likewise, but for open
      :class:`MemoryReceiveChannel` endpoints.
    * ``tasks_waiting_send``: The number of tasks blocked in ``send`` on this
      channel (summing over all clones).
    * ``tasks_waiting_receive``: The number of tasks blocked in ``receive`` on
      this channel (summing over all clones). | , __future__, attrs, collections, contextlib, exceptiongroup, functools, math, outcome, sys, trio, types, typing, typing_extensions | L37: elif "sphinx.ext.autodoc" in sys.modules: |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This namespace represents the core functionality that has to be built-in
and deal with private internal data structures. Things in this namespace
are publicly available in either trio, trio.lowlevel, or trio.testing. | , sys, typing | L78: not _t.TYPE_CHECKING and "sphinx.ext.autodoc" in sys.modules
L90: not _t.TYPE_CHECKING and "sphinx.ext.autodoc" in sys.modules |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_asyncgens.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, logging, sys, types, typing, typing_extensions, warnings, weakref | L189: # versions due to https://bugs.python.org/issue32526.) |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_concat_tb.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, types |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_entry_queue.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An opaque object representing a single call to :func:`trio.run`.

    It has no public constructor; instead, see :func:`current_trio_token`.

    This object has two uses:

    1. It lets you re-enter the Trio run loop from external threads or signal
       handlers. This is the low-level primitive that :func:`trio.to_thread`
       and `trio.from_thread` use to communicate with worker threads, that
       `trio.open_signal_receiver` uses to receive notifications about
       signals, and so forth.

    2. Each call to :func:`trio.run` has exactly one associated
       :class:`TrioToken` object, so you can use it to identify a particular
       call. | , __future__, attrs, collections, threading, typing, typing_extensions | L55: #     https://bugs.python.org/issue13697#msg237140
L78: # TODO(2020-06): this is a gross hack and should |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Raised by :func:`run` if we encounter a bug in Trio, or (possibly) a
    misuse of one of the low-level :mod:`trio.lowlevel` APIs.

    This should never happen! If you get this error, please file a bug.

    Unfortunately, if you get this error it also means that all bets are off –
    Trio doesn't know what is going on and its normal invariants may be void.
    (For example, we might have "lost track" of a task. Or lost track of all
    tasks.) Again, though, this shouldn't happen. | __future__, attrs, collections, functools, trio, typing, typing_extensions | L26: """Raised by :func:`run` if we encounter a bug in Trio, or (possibly) a
L29: This should never happen! If you get this error, please file a bug.
L125: already using, and this would lead to bugs and nonsense. |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_generated_instrumentation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Start instrumenting the current run loop with the given instrument.

    Args:
      instrument (trio.abc.Instrument): The instrument to activate.

    If ``instrument`` is already active, does nothing. | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_generated_io_epoll.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Block until the kernel reports that the given object is readable.

    On Unix systems, ``fd`` must either be an integer file descriptor,
    or else an object with a ``.fileno()`` method which returns an
    integer file descriptor. Any kind of file descriptor can be passed,
    though the exact semantics will depend on your kernel. For example,
    this probably won't do anything useful for on-disk files.

    On Windows systems, ``fd`` must either be an integer ``SOCKET``
    handle, or else an object with a ``.fileno()`` method which returns
    an integer ``SOCKET`` handle. File descriptors aren't supported,
    and neither are handles that refer to anything besides a
    ``SOCKET``.

    :raises trio.BusyResourceError:
        if another task is already waiting for the given socket to
        become readable.
    :raises trio.ClosedResourceError:
        if another task calls :func:`notify_closing` while this
        function is still working. | , __future__, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_generated_io_kqueue.py` | ❓ UNKNOWN | 2025-11-09 21:21 | TODO: these are implemented, but are currently more of a sketch than
    anything real. See `#26
    <https://github.com/python-trio/trio/issues/26>`__. | , __future__, collections, contextlib, select, sys, typing | L36: """TODO: these are implemented, but are currently more of a sketch than
L50: """TODO: these are implemented, but are currently more of a sketch than
L64: """TODO: these are implemented, but are currently more of a sketch than |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_generated_io_windows.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Block until the kernel reports that the given object is readable.

    On Unix systems, ``sock`` must either be an integer file descriptor,
    or else an object with a ``.fileno()`` method which returns an
    integer file descriptor. Any kind of file descriptor can be passed,
    though the exact semantics will depend on your kernel. For example,
    this probably won't do anything useful for on-disk files.

    On Windows systems, ``sock`` must either be an integer ``SOCKET``
    handle, or else an object with a ``.fileno()`` method which returns
    an integer ``SOCKET`` handle. File descriptors aren't supported,
    and neither are handles that refer to anything besides a
    ``SOCKET``.

    :raises trio.BusyResourceError:
        if another task is already waiting for the given socket to
        become readable.
    :raises trio.ClosedResourceError:
        if another task calls :func:`notify_closing` while this
        function is still working. | , __future__, contextlib, sys, typing, typing_extensions | L119: """TODO: these are implemented, but are currently more of a sketch than
L132: """TODO: these are implemented, but are currently more of a sketch than
L149: """TODO: these are implemented, but are currently more of a sketch than
L166: """TODO: these are implemented, but are currently more of a sketch than
L181: """TODO: these are implemented, but are currently more of a sketch than
L196: """TODO: these are implemented, but are currently more of a sketch than |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_generated_run.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Returns ``RunStatistics``, which contains run-loop-level debugging information.

    Currently, the following fields are defined:

    * ``tasks_living`` (int): The number of tasks that have been spawned
      and not yet exited.
    * ``tasks_runnable`` (int): The number of tasks that are currently
      queued on the run queue (as opposed to blocked waiting for something
      to happen).
    * ``seconds_to_next_deadline`` (float): The time until the next
      pending cancel scope deadline. May be negative if the deadline has
      expired but we haven't yet processed cancellations. May be
      :data:`~math.inf` if there are no pending deadlines.
    * ``run_sync_soon_queue_size`` (int): The number of
      unprocessed callbacks queued via
      :meth:`trio.lowlevel.TrioToken.run_sync_soon`.
    * ``io_statistics`` (object): Some statistics from Trio's I/O
      backend. This always has an attribute ``backend`` which is a string
      naming which operating-system-specific I/O backend is in use; the
      other attributes vary between backends. | , __future__, collections, contextvars, outcome, typing, typing_extensions | L37: """Returns ``RunStatistics``, which contains run-loop-level debugging information.
L172: name: The name for this task. Only used for debugging/introspection
L177: make debugging easier. |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_generated_windows_ffi.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | _cffi_backend | L7: _globals = (b'\x00\x00\x2F\x23CancelIoEx',0,b'\x00\x00\x2C\x23CloseHandle',0,b'\x00\x00\x52\x23CreateEventA',0,b'\x00\x00\x58\x23CreateFileW',0,b'\x00\x00\x61\x23CreateIoCompletionPort',0,b'\x00\x00\x12\x23DeviceIoControl',0,b'\x00\x00\x33\x23GetQueuedCompletionStatusEx',0,b'\x00\x00\x3F\x23PostQueuedCompletionStatus',0,b'\x00\x00\x1C\x23ReadFile',0,b'\x00\x00\x0B\x23ResetEvent',0,b'\x00\x00\x45\x23RtlNtStatusToDosError',0,b'\x00\x00\x3B\x23SetConsoleCtrlHandler',0,b'\x00\x00\x0B\x23SetEvent',0,b'\x00\x00\x0E\x23SetFileCompletionNotificationModes',0,b'\x00\x00\x2A\x23WSAGetLastError',0,b'\x00\x00\x00\x23WSAIoctl',0,b'\x00\x00\x48\x23WaitForMultipleObjects',0,b'\x00\x00\x4E\x23WaitForSingleObject',0,b'\x00\x00\x23\x23WriteFile',0), |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_instrumentation.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A collection of `trio.abc.Instrument` organized by hook.

    Instrumentation calls are rather expensive, and we don't want a
    rarely-used instrument (like before_run()) to slow down hot
    operations (like before_task_step()). Thus, we cache the set of
    instruments to be called for each hook, and skip the instrumentation
    call if there's nothing currently installed for that hook. | , __future__, collections, logging, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_io_common.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, copy, outcome, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_io_epoll.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, contextlib, select, sys, typing | L132: # sometimes user code has bugs. So if this does happen, we'd like to degrade
L253: # Clever hack stolen from selectors.EpollSelector: an event |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_io_kqueue.py` | ❓ UNKNOWN | 2025-11-09 21:21 | TODO: these are implemented, but are currently more of a sketch than
        anything real. See `#26
        <https://github.com/python-trio/trio/issues/26>`__. | , __future__, attrs, collections, contextlib, errno, outcome, select, sys, typing | L82: else:  # TODO: test this line
L94: if event.flags & select.KQ_EV_ONESHOT:  # TODO: test this branch
L99: receiver.put_nowait(event)  # TODO: test this line
L114: """TODO: these are implemented, but are currently more of a sketch than
L127: """TODO: these are implemented, but are currently more of a sketch than
L150: """TODO: these are implemented, but are currently more of a sketch than
L163: if r is _core.Abort.SUCCEEDED:  # TODO: test this branch |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_io_windows.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, contextlib, enum, itertools, outcome, socket, sys, typing, typing_extensions | L148: # Unfortunately, the Windows kernel seems to have bugs if you try to issue
L380: "return a different socket. Please file a bug at "
L404: # might be visible in some debug tools, and is otherwise arbitrary?)
L487: "Please file a bug at " |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_ki.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Check whether the calling code has :exc:`KeyboardInterrupt` protection
    enabled.

    It's surprisingly easy to think that one's :exc:`KeyboardInterrupt`
    protection is enabled when it isn't, or vice-versa. This function tells
    you what Trio thinks of the matter, which makes it useful for ``assert``\s
    and unit tests.

    Returns:
      bool: True if protection is enabled, and False otherwise. | , __future__, attrs, collections, signal, sys, types, typing, typing_extensions, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_local.py` | ❓ UNKNOWN | 2025-11-09 21:21 | The run-local variant of a context variable.

    :class:`RunVar` objects are similar to context variable objects,
    except that they are shared across a single call to :func:`trio.run`
    rather than a single task. | , __future__, attrs, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_mock_clock.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A user-controllable clock suitable for writing tests.

    Args:
      rate (float): the initial :attr:`rate`.
      autojump_threshold (float): the initial :attr:`autojump_threshold`.

    .. attribute:: rate

       How many seconds of clock time pass per second of real time. Default is
       0.0, i.e. the clock only advances through manuals calls to :meth:`jump`
       or when the :attr:`autojump_threshold` is triggered. You can assign to
       this attribute to change it.

    .. attribute:: autojump_threshold

       The clock keeps an eye on the run loop, and if at any point it detects
       that all tasks have been blocked for this many real seconds (i.e.,
       according to the actual clock, not this clock), then the clock
       automatically jumps ahead to the run loop's next scheduled
       timeout. Default is :data:`math.inf`, i.e., to never autojump. You can
       assign to this attribute to change it.

       Basically the idea is that if you have code or tests that use sleeps
       and timeouts, you can use this to make it run much faster, totally
       automatically. (At least, as long as those sleeps/timeouts are
       happening inside Trio; if your test involves talking to external
       service and waiting for it to timeout then obviously we can't help you
       there.)

       You should set this to the smallest value that lets you reliably avoid
       "false alarms" where some I/O is in flight (e.g. between two halves of
       a socketpair) but the threshold gets triggered and time gets advanced
       anyway. This will depend on the details of your tests and test
       environment. If you aren't doing any I/O (like in our sleeping example
       above) then just set it to zero, and the clock will jump whenever all
       tasks are blocked.

       .. note:: If you use ``autojump_threshold`` and
          `wait_all_tasks_blocked` at the same time, then you might wonder how
          they interact, since they both cause things to happen after the run
          loop goes idle for some time. The answer is:
          `wait_all_tasks_blocked` takes priority. If there's a task blocked
          in `wait_all_tasks_blocked`, then the autojump feature treats that
          as active task and does *not* jump the clock. | , math, time |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_parking_lot.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Register a task as a breaker for a lot. See :meth:`ParkingLot.break_lot`.

    raises:
      trio.BrokenResourceError: if the task has already exited. | , __future__, attrs, collections, inspect, math, outcome, typing | L124: """An object containing debugging information for a ParkingLot.
L309: """Return an object containing debugging information. |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_run.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sentinel for unset TaskStatus._value."""


# Decorator to mark methods public. This does nothing by itself, but
# trio/_tools/gen_exports.py looks for it.
def _public(fn: RetT) -> RetT:
    return fn


# When running under Hypothesis, we want examples to be reproducible and
# shrinkable.  We therefore register `_hypothesis_plugin_setup()` as a
# plugin, so that importing *Hypothesis* will make Trio's task
# scheduling loop deterministic.  We have a test for that, of course.
# Before Hypothesis supported entry-point plugins this integration was
# handled by pytest-trio, but we want it to work in e.g. unittest too.
_ALLOW_DETERMINISTIC_SCHEDULING: Final = False
_r = random.Random()


# no cover because we don't check the hypothesis plugin works with hypothesis
def _hypothesis_plugin_setup() -> None:  # pragma: no cover
    from hypothesis import register_random

    global _ALLOW_DETERMINISTIC_SCHEDULING
    _ALLOW_DETERMINISTIC_SCHEDULING = True  # type: ignore
    register_random(_r)

    # monkeypatch repr_callable to make repr's way better
    # requires importing hypothesis (in the test file or in conftest.py)
    try:
        from hypothesis.internal.reflection import get_pretty_function_description

        import trio.testing._raises_group

        def repr_callable(fun: Callable[[BaseExcT], bool]) -> str:
            # add quotes around the signature
            return repr(get_pretty_function_description(fun))

        trio.testing._raises_group.repr_callable = repr_callable
    except ImportError:
        pass


def _count_context_run_tb_frames() -> int: | , __future__, attrs, collections, contextlib, contextvars, enum, exceptiongroup, functools, gc, heapq, hypothesis, itertools, math, outcome, random, select, sniffio, sortedcontainers, sys, time, trio, types, typing, typing_extensions, warnings | L195: # between different runs, then they'll notice the bug quickly:
L482: todo = [self]
L483: while todo:
L484: current = todo.pop() |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_run_context.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, threading, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_asyncgen.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, contextlib, math, pytest, sys, types, typing, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_cancelled.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , math, pickle, pytest, re, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_exceptiongroup_gc.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, exceptiongroup, gc, pytest, sys, traceback, types, typing | L86: old_flags = gc.get_debug()
L92: gc.set_debug(gc.DEBUG_SAVEALL)
L95: # TODO: is the above comment true anymore? as this no longer uses MultiError.catch
L102: gc.set_debug(old_flags) |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_guest_mode.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Wait for all in_host() calls issued so far to complete."""
            evt = trio.Event()
            in_host(evt.set)
            await evt.wait()

        # Host and guest have separate sniffio_library contexts
        in_host(partial(setattr, sniffio_library, "name", "nullio"))
        await synchronize()
        assert current_async_library() == "trio"

        record = []
        in_host(lambda: record.append(current_async_library()))
        await synchronize()
        assert record == ["nullio"]
        assert current_async_library() == "trio"

        return "ok"

    try:
        assert trivial_guest_run(trio_main) == "ok"
    finally:
        sniffio_library.name = None


def test_guest_mode_trio_context_detection() -> None:
    def check(thing: bool) -> None:
        assert thing

    assert not trio.lowlevel.in_trio_run()
    assert not trio.lowlevel.in_trio_task()

    async def trio_main(in_host: InHost) -> None:
        for _ in range(2):
            assert trio.lowlevel.in_trio_run()
            assert trio.lowlevel.in_trio_task()

            in_host(lambda: check(trio.lowlevel.in_trio_run()))
            in_host(lambda: check(not trio.lowlevel.in_trio_task()))

    trivial_guest_run(trio_main)
    assert not trio.lowlevel.in_trio_run()
    assert not trio.lowlevel.in_trio_task()


def test_warn_set_wakeup_fd_overwrite() -> None:
    assert signal.set_wakeup_fd(-1) == -1

    async def trio_main(in_host: InHost) -> str:
        return "ok"

    a, b = socket.socketpair()
    with a, b:
        a.setblocking(False)

        # Warn if there's already a wakeup fd
        signal.set_wakeup_fd(a.fileno())
        try:
            with pytest.warns(RuntimeWarning, match="signal handling code.*collided"):
                assert trivial_guest_run(trio_main) == "ok" | , __future__, asyncio, collections, contextlib, functools, math, outcome, pytest, queue, signal, sniffio, socket, sys, threading, time, traceback, trio, typing, warnings, weakref | L58: todo: queue.Queue[tuple[str, Outcome[T] \\| Callable[[], object]]] = queue.Queue()
L63: nonlocal todo
L69: todo.put(("run", crash))
L70: todo.put(("run", fn))
L73: nonlocal todo
L79: todo.put(("run", crash))
L80: todo.put(("run", fn))
L83: nonlocal todo
L84: todo.put(("unwrap", outcome))
L103: op, obj = todo.get()
L116: del todo, run_sync_soon_threadsafe, done_callback
L450: # also hack start_guest_run so that it does 'global W; W = |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_instrumentation.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, pytest, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_io.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, contextlib, pytest, random, select, socket, sys, trio, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_ki.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, async_generator, collections, contextlib, inspect, outcome, pytest, signal, sys, threading, traceback, trio, typing, weakref | L113: #   https://bugs.python.org/issue29590
L143: #   https://bugs.python.org/issue29590
L242: #   https://bugs.python.org/issue29590 |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_local.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , pytest, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_mock_clock.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , math, pytest, time, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_parking_lot.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Test basic functionality for breaking lots."""
    lot = ParkingLot()
    task = current_task()

    # defaults to current task
    lot.break_lot()
    assert lot.broken_by == [task]

    # breaking the lot again with the same task appends another copy in `broken_by`
    lot.break_lot()
    assert lot.broken_by == [task, task]

    # trying to park in broken lot errors
    broken_by_str = re.escape(str([task, task]))
    with pytest.raises(
        _core.BrokenResourceError,
        match=f"^Attempted to park in parking lot broken by {broken_by_str}$",
    ):
        await lot.park()


async def test_parking_lot_break_parking_tasks() -> None: | , __future__, pytest, re, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_run.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Assert that this object is not None.

    This is just to satisfy type checkers, if this ever fails the test is broken. | , __future__, collections, contextlib, contextvars, exceptiongroup, functools, gc, math, outcome, pytest, sniffio, sys, threading, time, types, typing, unittest, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_thread_cache.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, contextlib, coverage, os, outcome, pytest, queue, threading, time, typing | L174: # to see it in debug output. |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_tutil.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , pytest |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_unbounded_queue.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, itertools, pytest |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/test_windows.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, asyncio, collections, contextlib, io, msvcrt, os, pytest, sys, tempfile, time, typing, unittest |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/tutil.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, asyncio, collections, contextlib, gc, os, pytest, socket, sys, trio, typing, warnings | L105: # https://bugs.freebsd.org/bugzilla/show_bug.cgi?id=246350
L111: reason="hangs on FreeBSD 12.1 and earlier, due to FreeBSD bug #246350", |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/type_tests/nursery_start.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Test variadic generic typing for Nursery.start[_soon]()."""

from typing import TYPE_CHECKING

from trio import TASK_STATUS_IGNORED, Nursery, TaskStatus

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable


async def task_0() -> None: ...


async def task_1a(value: int) -> None: ...


async def task_1b(value: str) -> None: ...


async def task_2a(a: int, b: str) -> None: ...


async def task_2b(a: str, b: int) -> None: ...


async def task_2c(a: str, b: int, optional: bool = False) -> None: ...


async def task_requires_kw(a: int, *, b: bool) -> None: ...


async def task_startable_1(
    a: str,
    *,
    task_status: TaskStatus[bool] = TASK_STATUS_IGNORED,
) -> None: ...


async def task_startable_2(
    a: str,
    b: float,
    *,
    task_status: TaskStatus[bool] = TASK_STATUS_IGNORED,
) -> None: ...


async def task_requires_start(*, task_status: TaskStatus[str]) -> None: | collections, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_tests/type_tests/run.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, collections, trio, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_thread_cache.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Runs ``deliver(outcome.capture(fn))`` in a worker thread.

    Generally ``fn`` does some blocking work, and ``deliver`` delivers the
    result back to whoever is interested.

    This is a low-level, no-frills interface, very similar to using
    `threading.Thread` to spawn a thread directly. The main difference is
    that this function tries to reuse threads when possible, so it can be
    a bit faster than `threading.Thread`.

    Worker threads have the `~threading.Thread.daemon` flag set, which means
    that if your main thread exits, worker threads will automatically be
    killed. If you want to make sure that your ``fn`` runs to completion, then
    you should make sure that the main thread remains alive until ``deliver``
    is called.

    It is safe to call this function simultaneously from multiple threads.

    Args:

        fn (sync function): Performs arbitrary blocking work.

        deliver (sync function): Takes the `outcome.Outcome` of ``fn``, and
          delivers it. *Must not block.*

    Because worker threads are cached and reused for multiple calls, neither
    function should mutate thread-level state, like `threading.local` objects
    – or if they do, they should be careful to revert their changes before
    returning.

    Note:

        The split between ``fn`` and ``deliver`` serves two purposes. First,
        it's convenient, since most callers need something like this anyway.

        Second, it avoids a small race condition that could cause too many
        threads to be spawned. Consider a program that wants to run several
        jobs sequentially on a thread, so the main thread submits a job, waits
        for it to finish, submits another job, etc. In theory, this program
        should only need one worker thread. But what could happen is:

        1. Worker thread: First job finishes, and calls ``deliver``.

        2. Main thread: receives notification that the job finished, and calls
           ``start_thread_soon``.

        3. Main thread: sees that no worker threads are marked idle, so spawns
           a second worker thread.

        4. Original worker thread: marks itself as idle.

        To avoid this, threads mark themselves as idle *before* calling
        ``deliver``.

        Is this potential extra thread a major problem? Maybe not, but it's
        easy enough to avoid, and we figure that if the user is trying to
        limit how many threads they're using then it's polite to respect that. | __future__, collections, ctypes, functools, itertools, os, outcome, sys, threading, traceback, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_traps.py` | ❓ UNKNOWN | 2025-11-09 21:21 | These are the only functions that ever yield back to the task runner."""

from __future__ import annotations

import enum
import types

# typing.Callable is necessary because collections.abc.Callable breaks
# test_static_tool_sees_all_symbols in 3.10.
from typing import (  # noqa: UP035
    TYPE_CHECKING,
    Any,
    Callable,
    NoReturn,
    TypeAlias,
    cast,
)

import attrs
import outcome

from . import _run

if TYPE_CHECKING:
    from collections.abc import Awaitable, Generator

    from ._run import Task

RaiseCancelT: TypeAlias = Callable[[], NoReturn]


# This class object is used as a singleton.
# Not exported in the trio._core namespace, but imported directly by _run.
class CancelShieldedCheckpoint:
    __slots__ = ()


# Not exported in the trio._core namespace, but imported directly by _run.
@attrs.frozen(slots=False)
class WaitTaskRescheduled:
    abort_func: Callable[[RaiseCancelT], Abort]


# Not exported in the trio._core namespace, but imported directly by _run.
@attrs.frozen(slots=False)
class PermanentlyDetachCoroutineObject:
    final_outcome: outcome.Outcome[object]


MessageType: TypeAlias = (
    type[CancelShieldedCheckpoint]
    \\| WaitTaskRescheduled
    \\| PermanentlyDetachCoroutineObject
    \\| object
)


# Helper for the bottommost 'yield'. You can't use 'yield' inside an async
# function, but you can inside a generator, and if you decorate your generator
# with @types.coroutine, then it's even awaitable. However, it's still not a
# real async function: in particular, it isn't recognized by
# inspect.iscoroutinefunction, and it doesn't trigger the unawaited coroutine
# tracking machinery. Since our traps are public APIs, we make them real async
# functions, and then this helper takes care of the actual yield:
@types.coroutine
def _real_async_yield(
    obj: MessageType,
) -> Generator[MessageType, None, None]:
    return (yield obj)


# Real yield value is from trio's main loop, but type checkers can't
# understand that, so we cast it to make type checkers understand.
_async_yield = cast(
    "Callable[[MessageType], Awaitable[outcome.Outcome[object]]]",
    _real_async_yield,
)


async def cancel_shielded_checkpoint() -> None: | , __future__, attrs, collections, enum, outcome, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_unbounded_queue.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An object containing debugging information.

    Currently, the following fields are defined:

    * ``qsize``: The number of items currently in the queue.
    * ``tasks_waiting``: The number of tasks blocked on this queue's
      :meth:`get_batch` method. | , __future__, attrs, typing, typing_extensions | L19: """An object containing debugging information.
L153: """Return an :class:`UnboundedQueueStatistics` object containing debugging information.""" |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_wakeup_socketpair.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, contextlib, signal, socket, warnings | L65: "Otherwise, file a bug on Trio and we'll help you figure " |
| `blackboard-agent/venv/Lib/site-packages/trio/_core/_windows_cffi.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Statically typed version of the kernel32.dll functions we use."""

    def CreateIoCompletionPort(
        self,
        FileHandle: Handle,
        ExistingCompletionPort: CData \\| AlwaysNull,
        CompletionKey: int,
        NumberOfConcurrentThreads: int,
        /,
    ) -> Handle: ...

    def CreateEventA(
        self,
        lpEventAttributes: AlwaysNull,
        bManualReset: bool,
        bInitialState: bool,
        lpName: AlwaysNull,
        /,
    ) -> Handle: ...

    def SetFileCompletionNotificationModes(
        self,
        handle: Handle,
        flags: CompletionModes,
        /,
    ) -> int: ...

    def PostQueuedCompletionStatus(
        self,
        CompletionPort: Handle,
        dwNumberOfBytesTransferred: int,
        dwCompletionKey: int,
        lpOverlapped: CData \\| AlwaysNull,
        /,
    ) -> bool: ...

    def CancelIoEx(
        self,
        hFile: Handle,
        lpOverlapped: CData \\| AlwaysNull,
        /,
    ) -> bool: ...

    def WriteFile(
        self,
        hFile: Handle,
        # not sure about this type
        lpBuffer: CData,
        nNumberOfBytesToWrite: int,
        lpNumberOfBytesWritten: AlwaysNull,
        lpOverlapped: _Overlapped,
        /,
    ) -> bool: ...

    def ReadFile(
        self,
        hFile: Handle,
        # not sure about this type
        lpBuffer: CData,
        nNumberOfBytesToRead: int,
        lpNumberOfBytesRead: AlwaysNull,
        lpOverlapped: _Overlapped,
        /,
    ) -> bool: ...

    def GetQueuedCompletionStatusEx(
        self,
        CompletionPort: Handle,
        lpCompletionPortEntries: CData,
        ulCount: int,
        ulNumEntriesRemoved: CData,
        dwMilliseconds: int,
        fAlertable: bool \\| int,
        /,
    ) -> CData: ...

    def CreateFileW(
        self,
        lpFileName: CData,
        dwDesiredAccess: FileFlags,
        dwShareMode: FileFlags,
        lpSecurityAttributes: AlwaysNull,
        dwCreationDisposition: FileFlags,
        dwFlagsAndAttributes: FileFlags,
        hTemplateFile: AlwaysNull,
        /,
    ) -> Handle: ...

    def WaitForSingleObject(self, hHandle: Handle, dwMilliseconds: int, /) -> CData: ...

    def WaitForMultipleObjects(
        self,
        nCount: int,
        lpHandles: HandleArray,
        bWaitAll: bool,
        dwMilliseconds: int,
        /,
    ) -> ErrorCodes: ...

    def SetEvent(self, handle: Handle, /) -> None: ...

    def CloseHandle(self, handle: Handle, /) -> bool: ...

    def DeviceIoControl(
        self,
        hDevice: Handle,
        dwIoControlCode: int,
        # this is wrong (it's not always null)
        lpInBuffer: AlwaysNull,
        nInBufferSize: int,
        # this is also wrong
        lpOutBuffer: AlwaysNull,
        nOutBufferSize: int,
        lpBytesReturned: AlwaysNull,
        lpOverlapped: CData,
        /,
    ) -> bool: ...


class _Nt(Protocol): | , __future__, cffi, enum, typing | L150: def RtlNtStatusToDosError(self, status: int, /) -> ErrorCodes: ...
L298: # assert sys.platform == "win32"  # TODO: make this work in MyPy |
| `blackboard-agent/venv/Lib/site-packages/trio/_deprecate.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Warning emitted if you use deprecated Trio functionality.

    While a relatively mature project, Trio remains committed to refining its
    design and improving usability. As part of this, we occasionally deprecate
    or remove functionality that proves suboptimal. If you use Trio, we
    recommend `subscribing to issue #1
    <https://github.com/python-trio/trio/issues/1>`__ to get information about
    upcoming deprecations and other backwards compatibility breaking changes.

    Despite the name, this class currently inherits from
    :class:`FutureWarning`, not :class:`DeprecationWarning`, because until a
    1.0 release, we want these warnings to be visible by default. You can hide
    them by installing a filter or with the ``-W`` switch: see the
    :mod:`warnings` documentation for details. | __future__, attrs, collections, functools, sys, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_dtls.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, contextlib, enum, errno, hmac, itertools, OpenSSL, os, struct, trio, types, typing, typing_extensions, warnings, weakref | L56: return 1280 - packet_header_overhead(sock)  # TODO: test this line
L220: except struct.error as exc:  # TODO: test this line
L421: if mtu - len(packet) - len(encoded) <= 0:  # TODO: test this line
L428: if space <= 0:  # TODO: test this line |
| `blackboard-agent/venv/Lib/site-packages/trio/_file_io.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A generic :class:`~io.IOBase` wrapper that implements the :term:`asynchronous
    file object` interface. Wrapped methods that could block are executed in
    :meth:`trio.to_thread.run_sync`.

    All properties and methods defined in :mod:`~io` are exposed by this
    wrapper, if they exist in the wrapped file object. | , __future__, _typeshed, collections, functools, io, trio, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_generic.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Close an async resource or async generator immediately, without
    blocking to do any graceful cleanup.

    :class:`~trio.abc.AsyncResource` objects guarantee that if their
    :meth:`~trio.abc.AsyncResource.aclose` method is cancelled, then they will
    still close the resource (albeit in a potentially ungraceful
    fashion). :func:`aclose_forcefully` is a convenience function that
    exploits this behavior to let you force a resource to be closed without
    blocking: it works by calling ``await resource.aclose()`` and then
    cancelling it immediately.

    Most users won't need this, but it may be useful on cleanup paths where
    you can't afford to block, or if you want to close a resource and don't
    care about handling it gracefully. For example, if
    :class:`~trio.SSLStream` encounters an error and cannot perform its
    own graceful close, then there's no point in waiting to gracefully shut
    down the underlying transport either, so it calls ``await
    aclose_forcefully(self.transport_stream)``.

    Note that this function is async, and that it acts as a checkpoint, but
    unlike most async functions it cannot block indefinitely (at least,
    assuming the underlying resource object is correctly implemented). | , __future__, attrs, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_open_tcp_listeners.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Create :class:`SocketListener` objects to listen for TCP connections.

    Args:

      port (int): The port to listen on.

          If you use 0 as your port, then the kernel will automatically pick
          an arbitrary open port. But be careful: if you use this feature when
          binding to multiple IP addresses, then each IP address will get its
          own random port, and the returned listeners will probably be
          listening on different ports. In particular, this will happen if you
          use ``host=None`` – which is the default – because in this case
          :func:`open_tcp_listeners` will bind to both the IPv4 wildcard
          address (``0.0.0.0``) and also the IPv6 wildcard address (``::``).

      host (str, bytes, or None): The local interface to bind to. This is
          passed to :func:`~socket.getaddrinfo` with the ``AI_PASSIVE`` flag
          set.

          If you want to bind to the wildcard address on both IPv4 and IPv6,
          in order to accept connections on all available interfaces, then
          pass ``None``. This is the default.

          If you have a specific interface you want to bind to, pass its IP
          address or hostname here. If a hostname resolves to multiple IP
          addresses, this function will open one listener on each of them.

          If you want to use only IPv4, or only IPv6, but want to accept on
          all interfaces, pass the family-specific wildcard address:
          ``"0.0.0.0"`` for IPv4-only and ``"::"`` for IPv6-only.

      backlog (int or None): The listen backlog to use. If you leave this as
          ``None`` then Trio will pick a good default. (Currently: whatever
          your system has configured as the maximum backlog.)

    Returns:
      list of :class:`SocketListener`

    Raises:
      :class:`TypeError` if invalid arguments. | , __future__, collections, errno, exceptiongroup, sys, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_open_tcp_stream.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Connect to the given host and port over TCP.

    If the given ``host`` has multiple IP addresses associated with it, then
    we have a problem: which one do we use?

    One approach would be to attempt to connect to the first one, and then if
    that fails, attempt to connect to the second one ... until we've tried all
    of them. But the problem with this is that if the first IP address is
    unreachable (for example, because it's an IPv6 address and our network
    discards IPv6 packets), then we might end up waiting tens of seconds for
    the first connection attempt to timeout before we try the second address.

    Another approach would be to attempt to connect to all of the addresses at
    the same time, in parallel, and then use whichever connection succeeds
    first, abandoning the others. This would be fast, but create a lot of
    unnecessary load on the network and the remote server.

    This function strikes a balance between these two extremes: it works its
    way through the available addresses one at a time, like the first
    approach; but, if ``happy_eyeballs_delay`` seconds have passed and it's
    still waiting for an attempt to succeed or fail, then it gets impatient
    and starts the next connection attempt in parallel. As soon as any one
    connection attempt succeeds, all the other attempts are cancelled. This
    avoids unnecessary load because most connections will succeed after just
    one or two attempts, but if one of the addresses is unreachable then it
    doesn't slow us down too much.

    This is known as a "happy eyeballs" algorithm, and our particular variant
    is modelled after how Chrome connects to webservers; see `RFC 6555
    <https://tools.ietf.org/html/rfc6555>`__ for more details.

    Args:
      host (str or bytes): The host to connect to. Can be an IPv4 address,
          IPv6 address, or a hostname.

      port (int): The port to connect to.

      happy_eyeballs_delay (float or None): How many seconds to wait for each
          connection attempt to succeed or fail before getting impatient and
          starting another one in parallel. Set to `None` if you want
          to limit to only one connection attempt at a time (like
          :func:`socket.create_connection`). Default: 0.25 (250 ms).

      local_address (None or str): The local IP address or hostname to use as
          the source for outgoing connections. If ``None``, we let the OS pick
          the source IP.

          This is useful in some exotic networking configurations where your
          host has multiple IP addresses, and you want to force the use of a
          specific one.

          Note that if you pass an IPv4 ``local_address``, then you won't be
          able to connect to IPv6 hosts, and vice-versa. If you want to take
          advantage of this to force the use of IPv4 or IPv6 without
          specifying an exact source address, you can use the IPv4 wildcard
          address ``local_address="0.0.0.0"``, or the IPv6 wildcard address
          ``local_address="::"``.

    Returns:
      SocketStream: a :class:`~trio.abc.Stream` connected to the given server.

    Raises:
      OSError: if the connection fails.

    See also:
      open_ssl_over_tcp_stream | __future__, collections, contextlib, exceptiongroup, socket, sys, trio, typing | L106: # But I guess other versions of windows messed this up, judging from these bug
L108: # https://bugs.chromium.org/p/chromium/issues/detail?id=5234
L109: # https://bugs.chromium.org/p/chromium/issues/detail?id=32522#c50
L180: # XX TODO: implement bind address support |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_open_unix_stream.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Opens a connection to the specified
    `Unix domain socket <https://en.wikipedia.org/wiki/Unix_domain_socket>`__.

    You must have read/write permission on the specified file to connect.

    Args:
      filename (str or bytes): The filename to open the connection to.

    Returns:
      SocketStream: a :class:`~trio.abc.Stream` connected to the given file.

    Raises:
      OSError: If the socket file could not be connected to.
      RuntimeError: If AF_UNIX sockets are not supported. | __future__, collections, contextlib, os, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_serve_listeners.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Listen for incoming connections on ``listeners``, and for each one
    start a task running ``handler(stream)``.

    .. warning::

       If ``handler`` raises an exception, then this function doesn't do
       anything special to catch it – so by default the exception will
       propagate out and crash your server. If you don't want this, then catch
       exceptions inside your ``handler``, or use a ``handler_nursery`` object
       that responds to exceptions in some other way.

    Args:

      handler: An async callable, that will be invoked like
          ``handler_nursery.start_soon(handler, stream)`` for each incoming
          connection.

      listeners: A list of :class:`~trio.abc.Listener` objects.
          :func:`serve_listeners` takes responsibility for closing them.

      handler_nursery: The nursery used to start handlers, or any object with
          a ``start_soon`` method. If ``None`` (the default), then
          :func:`serve_listeners` will create a new nursery internally and use
          that.

      task_status: This function can be used with ``nursery.start``, which
          will return ``listeners``.

    Returns:

      This function never returns unless cancelled.

    Resource handling:

      If ``handler`` neglects to close the ``stream``, then it will be closed
      using :func:`trio.aclose_forcefully`.

    Error handling:

      Most errors coming from :meth:`~trio.abc.Listener.accept` are allowed to
      propagate out (crashing the server in the process). However, some errors –
      those which indicate that the server is temporarily overloaded – are
      handled specially. These are :class:`OSError`\s with one of the following
      errnos:

      * ``EMFILE``: process is out of file descriptors
      * ``ENFILE``: system is out of file descriptors
      * ``ENOBUFS``, ``ENOMEM``: the kernel hit some sort of memory limitation
        when trying to create a socket object

      When :func:`serve_listeners` gets one of these errors, then it:

      * Logs the error to the standard library logger ``trio.serve_listeners``
        (level = ERROR, with exception information included). By default this
        causes it to be printed to stderr.
      * Waits 100 ms before calling ``accept`` again, in hopes that the
        system will recover. | __future__, collections, errno, logging, os, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An implementation of the :class:`trio.abc.HalfCloseableStream`
    interface based on a raw network socket.

    Args:
      socket: The Trio socket object to wrap. Must have type ``SOCK_STREAM``,
          and be connected.

    By default for TCP sockets, :class:`SocketStream` enables ``TCP_NODELAY``,
    and (on platforms where it's supported) enables ``TCP_NOTSENT_LOWAT`` with
    a reasonable buffer size (currently 16 KiB) – see `issue #72
    <https://github.com/python-trio/trio/issues/72>`__ for discussion. You can
    of course override these defaults by calling :meth:`setsockopt`.

    Once a :class:`SocketStream` object is constructed, it implements the full
    :class:`trio.abc.HalfCloseableStream` interface. In addition, it provides
    a few extra features:

    .. attribute:: socket

       The Trio socket object that this stream wraps. | , __future__, collections, contextlib, errno, sys, trio, typing, typing_extensions | L29: # XX TODO: this number was picked arbitrarily. We should do experiments to
L163: # TODO: rename `length` to `optlen` |
| `blackboard-agent/venv/Lib/site-packages/trio/_highlevel_ssl_helpers.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Make a TLS-encrypted Connection to the given host and port over TCP.

    This is a convenience wrapper that calls :func:`open_tcp_stream` and
    wraps the result in an :class:`~trio.SSLStream`.

    This function does not perform the TLS handshake; you can do it
    manually by calling :meth:`~trio.SSLStream.do_handshake`, or else
    it will be performed automatically the first time you send or receive
    data.

    Args:
      host (bytes or str): The host to connect to. We require the server
          to have a TLS certificate valid for this hostname.
      port (int): The port to connect to.
      https_compatible (bool): Set this to True if you're connecting to a web
          server. See :class:`~trio.SSLStream` for details. Default:
          False.
      ssl_context (:class:`~ssl.SSLContext` or None): The SSL context to
          use. If None (the default), :func:`ssl.create_default_context`
          will be called to create a context.
      happy_eyeballs_delay (float): See :func:`open_tcp_stream`.

    Returns:
      trio.SSLStream: the encrypted connection to the server. | , __future__, collections, ssl, trio, typing | L24: # objects can't be copied: https://bugs.python.org/issue33023. |
| `blackboard-agent/venv/Lib/site-packages/trio/_path.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An async :class:`pathlib.Path` that executes blocking methods in :meth:`trio.to_thread.run_sync`.

    Instantiating :class:`Path` returns a concrete platform-specific subclass, one of :class:`PosixPath` or
    :class:`WindowsPath`. | __future__, _typeshed, collections, functools, inspect, io, os, pathlib, sys, trio, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_repl.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, ast, code, collections, contextlib, fcntl, inspect, outcome, readline, signal, sys, termios, trio, types, typing, warnings | L28: def terminal_newline() -> None:  # TODO: test this line
L78: if sys.platform == "win32":  # TODO: test this line
L100: ) -> None:  # TODO: test this line
L113: if self.interrupted:  # TODO: test this line
L117: if self.interrupted:  # TODO: test this line |
| `blackboard-agent/venv/Lib/site-packages/trio/_signals.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Helper for tests, not public or otherwise used."""
    # open_signal_receiver() always produces SignalReceiver, this should not fail.
    assert isinstance(rec, SignalReceiver)
    return len(rec._pending)


@contextmanager
def open_signal_receiver(
    *signals: signal.Signals \\| int,
) -> Generator[AsyncIterator[int], None, None]: | , __future__, collections, contextlib, signal, trio, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Set a custom hostname resolver.

    By default, Trio's :func:`getaddrinfo` and :func:`getnameinfo` functions
    use the standard system resolver functions. This function allows you to
    customize that behavior. The main intended use case is for testing, but it
    might also be useful for using third-party resolvers like `c-ares
    <https://c-ares.haxx.se/>`__ (though be warned that these rarely make
    perfect drop-in replacements for the system resolver). See
    :class:`trio.abc.HostnameResolver` for more details.

    Setting a custom hostname resolver affects all future calls to
    :func:`getaddrinfo` and :func:`getnameinfo` within the enclosing call to
    :func:`trio.run`. All other hostname resolution in Trio is implemented in
    terms of these functions.

    Generally you should call this function just once, right at the beginning
    of your program.

    Args:
      hostname_resolver (trio.abc.HostnameResolver or None): The new custom
          hostname resolver, or None to restore the default behavior.

    Returns:
      The previous hostname resolver (which may be None). | , __future__, collections, idna, operator, os, select, socket, sys, trio, types, typing, typing_extensions | L200: <https://bugs.python.org/issue17305>`__.)
L422: #   https://bugs.python.org/issue21327 |
| `blackboard-agent/venv/Lib/site-packages/trio/_ssl.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Some :class:`SSLStream` methods can't return any meaningful data until
    after the handshake. If you call them before the handshake, they raise
    this error. | , __future__, collections, contextlib, enum, operator, ssl, trio, typing, typing_extensions | L71: # Python's ssl module. OpenSSL's renegotiation support is pretty buggy [1].
L165: # - this is also interesting: https://bugs.python.org/issue8108#msg102867
L208: # There appears to be a bug on Python 3.10, where SSLErrors |
| `blackboard-agent/venv/Lib/site-packages/trio/_subprocess.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents any file-like object that has a file descriptor."""

    def fileno(self) -> int: ...


@final
class Process(metaclass=NoPublicConstructor):
    r | , __future__, collections, contextlib, ctypes, functools, io, os, signal, subprocess, sys, trio, typing, typing_extensions, warnings | L287: graceful termination, but a misbehaving or buggy process might
L373: # TODO: how do paths and sequences thereof play with `shell=True`? |
| `blackboard-agent/venv/Lib/site-packages/trio/_subprocess_platform/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Block until the child process managed by ``process`` is exiting.

    It is invalid to call this function if the process has already
    been waited on; that is, ``process.returncode`` must be None.

    When this function returns, it indicates that a call to
    :meth:`subprocess.Popen.wait` will immediately be able to
    return the process's exit status. The actual exit status is not
    consumed by this call, since :class:`~subprocess.Popen` wants
    to be able to do that itself. | , __future__, asyncio, msvcrt, os, sys, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_subprocess_platform/kqueue.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, select, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_subprocess_platform/waitid.py` | ❓ UNKNOWN | 2025-11-09 21:21 | typedef struct siginfo_s {
    int si_signo;
    int si_errno;
    int si_code;
    int si_pid;
    int si_uid;
    int si_status;
    int pad[26];
} siginfo_t;
int waitid(int idtype, int id, siginfo_t* result, int options); | , cffi, errno, math, os, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_subprocess_platform/windows.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_sync.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An object containing debugging information.

    Currently the following fields are defined:

    * ``tasks_waiting``: The number of tasks blocked on this event's
      :meth:`trio.Event.wait` method. | , __future__, attrs, collections, math, trio, types, typing, typing_extensions | L48: """An object containing debugging information.
L123: """Return an object containing debugging information.
L173: """An object containing debugging information.
L414: """Return an object containing debugging information. |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/check_type_completeness.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This is a file that wraps calls to `pyright --verifytypes`, achieving two things:
1. give an error if docstrings are missing.
    pyright will give a number of missing docstrings, and error messages, but not exit with a non-zero value.
2. filter out specific errors we don't care about.
    this is largely due to 1, but also because Trio does some very complex stuff and --verifytypes has few to no ways of ignoring specific errors.

If this check is giving you false alarms, you can ignore them by adding logic to `has_docstring_at_runtime`, in the main loop in `check_type`, or by updating the json file. | __future__, argparse, json, pathlib, subprocess, sys, trio | L27: # TODO: consider checking manually without `--ignoreexternal`, and/or
L70: # export shenanigans. TODO: actually manually confirm that.
L95: # TODO: these are erroring on all platforms, why?
L241: help="Use this for debugging, it will dump the output of all three pyright runs by platform into this file.", |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/module_with_deprecations.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , sys |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/pytest_plugin.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, inspect, pytest, typing | L40: # FIXME: split off into a package (or just make part of Trio's public |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_abc.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, pytest |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_channel.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, exceptiongroup, pytest, sys, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_contextvars.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, contextvars |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_deprecate.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Hello!"""


@deprecated("2.1", issue=None, instead="hi")
def docstring_test2() -> None:  # pragma: no cover | , __future__, inspect, pytest, types, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_deprecate_strict_exception_groups_false.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , collections, pytest, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_dtls.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, contextlib, itertools, OpenSSL, pytest, random, trio, trustme, typing | L169: # openssl has a bug in the following scenario:
L208: fn.route_packet = route_packet_wrapper  # type: ignore[assignment]  # TODO: Fix FakeNet typing |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_exports.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Check if a class cannot be subclassed."""
    try:
        # new_class() handles metaclasses properly, type(...) does not.
        types.new_class("SubclassTester", (cls,))
    except TypeError:
        return True
    else:
        return False


def iter_modules(
    module: types.ModuleType,
    only_public: bool,
) -> Iterator[types.ModuleType]:
    yield module
    for name, class_ in module.__dict__.items():
        if name.startswith("_") and only_public:
            continue
        if not isinstance(class_, ModuleType):
            continue
        if not class_.__name__.startswith(module.__name__):  # pragma: no cover
            continue
        if class_ is module:  # pragma: no cover
            continue
        yield from iter_modules(class_, only_public)


PUBLIC_MODULES = list(iter_modules(trio, only_public=True))
ALL_MODULES = list(iter_modules(trio, only_public=False))
PUBLIC_MODULE_NAMES = [m.__name__ for m in PUBLIC_MODULES]


# It doesn't make sense for downstream redistributors to run this test, since
# they might be using a newer version of Python with additional symbols which
# won't be reflected in trio.socket, and this shouldn't cause downstream test
# runs to start failing.
@pytest.mark.redistributors_should_skip
@pytest.mark.skipif(
    sys.version_info[:4] == (3, 14, 0, "beta"),
    # 12 pass, 16 fail
    reason="several tools don't support 3.14",
)
# Static analysis tools often have trouble with alpha releases, where Python's
# internals are in flux, grammar may not have settled down, etc.
@pytest.mark.skipif(
    sys.version_info.releaselevel == "alpha",
    reason="skip static introspection tools on Python dev/alpha releases",
)
@pytest.mark.parametrize("modname", PUBLIC_MODULE_NAMES)
@pytest.mark.parametrize("tool", ["pylint", "jedi", "mypy", "pyright_verifytypes"])
@pytest.mark.filterwarnings(
    # https://github.com/pypa/setuptools/issues/3274
    "ignore:module 'sre_constants' is deprecated:DeprecationWarning",
)
def test_static_tool_sees_all_symbols(tool: str, modname: str, tmp_path: Path) -> None:
    module = importlib.import_module(modname)

    def no_underscores(symbols: Iterable[str]) -> set[str]:
        return {symbol for symbol in symbols if not symbol.startswith("_")}

    runtime_names = no_underscores(dir(module))

    # ignore deprecated module `tests` being invisible
    if modname == "trio":
        runtime_names.discard("tests")

    # Ignore any __future__ feature objects, if imported under that name.
    for name in __future__.all_feature_names:
        if getattr(module, name, None) is getattr(__future__, name):
            runtime_names.remove(name)

    if tool == "pylint":
        try:
            from pylint.lint import PyLinter
        except ImportError as error:
            skip_if_optional_else_raise(error)

        linter = PyLinter()
        assert module.__file__ is not None
        ast = linter.get_ast(module.__file__, modname)
        static_names = no_underscores(ast)  # type: ignore[arg-type]
    elif tool == "jedi":
        if sys.implementation.name != "cpython":
            pytest.skip("jedi does not support pypy")

        try:
            import jedi
        except ImportError as error:
            skip_if_optional_else_raise(error)

        # Simulate typing "import trio; trio.<TAB>"
        script = jedi.Script(f"import {modname}; {modname}.")
        completions = script.complete()
        static_names = no_underscores(c.name for c in completions)
    elif tool == "mypy":
        if not RUN_SLOW:  # pragma: no cover
            pytest.skip("use --run-slow to check against mypy")

        cache = Path.cwd() / ".mypy_cache"

        _ensure_mypy_cache_updated()

        trio_cache = next(cache.glob("*/trio"))
        _, modname = (modname + ".").split(".", 1)
        modname = modname[:-1]
        mod_cache = trio_cache / modname if modname else trio_cache
        if mod_cache.is_dir():  # pragma: no coverage
            mod_cache = mod_cache / "__init__.data.json"
        else:
            mod_cache = trio_cache / (modname + ".data.json")

        assert mod_cache.exists()
        assert mod_cache.is_file()
        with mod_cache.open() as cache_file:
            cache_json = json.loads(cache_file.read())
            static_names = no_underscores(
                key
                for key, value in cache_json["names"].items()
                if not key.startswith(".") and value["kind"] == "Gdef"
            )
    elif tool == "pyright_verifytypes":
        if not RUN_SLOW:  # pragma: no cover
            pytest.skip("use --run-slow to check against pyright")

        try:
            import pyright  # noqa: F401
        except ImportError as error:
            skip_if_optional_else_raise(error)
        import subprocess

        res = subprocess.run(
            ["pyright", f"--verifytypes={modname}", "--outputjson"],
            capture_output=True,
        )
        current_result = json.loads(res.stdout)

        static_names = {
            x["name"][len(modname) + 1 :]
            for x in current_result["typeCompleteness"]["symbols"]
            if x["name"].startswith(modname)
        }
    else:  # pragma: no cover
        raise AssertionError()

    # It's expected that the static set will contain more names than the
    # runtime set:
    # - static tools are sometimes sloppy and include deleted names
    # - some symbols are platform-specific at runtime, but always show up in
    #   static analysis (e.g. in trio.socket or trio.lowlevel)
    # So we check that the runtime names are a subset of the static names.
    missing_names = runtime_names - static_names

    # ignore warnings about deprecated module tests
    missing_names -= {"tests"}

    if missing_names:  # pragma: no cover
        print(f"{tool} can't see the following names in {modname}:")
        print()
        for name in sorted(missing_names):
            print(f"    {name}")
        raise AssertionError()


@slow
# see comment on test_static_tool_sees_all_symbols
@pytest.mark.redistributors_should_skip
# Static analysis tools often have trouble with alpha releases, where Python's
# internals are in flux, grammar may not have settled down, etc.
@pytest.mark.skipif(
    sys.version_info.releaselevel == "alpha",
    reason="skip static introspection tools on Python dev/alpha releases",
)
@pytest.mark.parametrize("module_name", PUBLIC_MODULE_NAMES)
@pytest.mark.parametrize("tool", ["jedi", "mypy"])
def test_static_tool_sees_class_members(
    tool: str,
    module_name: str,
    tmp_path: Path,
) -> None:
    module = PUBLIC_MODULES[PUBLIC_MODULE_NAMES.index(module_name)]

    # ignore hidden, but not dunder, symbols
    def no_hidden(symbols: Iterable[str]) -> set[str]:
        return {
            symbol
            for symbol in symbols
            if (not symbol.startswith("_")) or symbol.startswith("__")
        }

    if tool == "jedi" and sys.implementation.name != "cpython":
        pytest.skip("jedi does not support pypy")

    if tool == "mypy":
        cache = Path.cwd() / ".mypy_cache"

        _ensure_mypy_cache_updated()

        trio_cache = next(cache.glob("*/trio"))
        modname = module_name
        _, modname = (modname + ".").split(".", 1)
        modname = modname[:-1]
        mod_cache = trio_cache / modname if modname else trio_cache
        if mod_cache.is_dir():
            mod_cache = mod_cache / "__init__.data.json"
        else:
            mod_cache = trio_cache / (modname + ".data.json")

        assert mod_cache.exists()
        assert mod_cache.is_file()
        with mod_cache.open() as cache_file:
            cache_json = json.loads(cache_file.read())

        # skip a bunch of file-system activity (probably can un-memoize?)
        @functools.lru_cache
        def lookup_symbol(symbol: str) -> dict[str, Any]:  # type: ignore[misc, explicit-any]
            topname, *modname, name = symbol.split(".")
            version = next(cache.glob("3.*/"))
            mod_cache = version / topname | , __future__, attrs, collections, enum, functools, importlib, inspect, jedi, json, mypy, pathlib, pylint, pyright, pytest, socket, subprocess, sys, trio, types, typing, typing_extensions | L452: # TODO: this *should* be visible via `dir`!!
L479: # TODO: why is this? Is it a problem? |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_fakenet.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Test all recv methods for codecov"""
    fn()
    s1 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
    s2 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)

    # receiving on an unbound socket is a bad idea (I think?)
    with pytest.raises(NotImplementedError, match="code will most likely hang"):
        await s2.recv(10)

    await s1.bind(("127.0.0.1", 0))
    ip, port = s1.getsockname()
    assert ip == "127.0.0.1"
    assert port != 0

    # recvfrom
    await s2.sendto(b"abc", s1.getsockname())
    data, addr = await s1.recvfrom(10)
    assert data == b"abc"
    assert addr == s2.getsockname()

    # recv
    await s1.sendto(b"def", s2.getsockname())
    data = await s2.recv(10)
    assert data == b"def"

    # recvfrom_into
    assert await s1.sendto(b"ghi", s2.getsockname()) == 3
    buf = bytearray(10)

    with pytest.raises(NotImplementedError, match=r"^partial recvfrom_into$"):
        (nbytes, addr) = await s2.recvfrom_into(buf, nbytes=2)

    (nbytes, addr) = await s2.recvfrom_into(buf)
    assert nbytes == 3
    assert buf == b"ghi" + b"\x00" * 7
    assert addr == s1.getsockname()

    # recv_into
    assert await s1.sendto(b"jkl", s2.getsockname()) == 3
    buf2 = bytearray(10)
    nbytes = await s2.recv_into(buf2)
    assert nbytes == 3
    assert buf2 == b"jkl" + b"\x00" * 7

    if sys.platform == "linux" and sys.implementation.name == "cpython":
        flags: int = socket.MSG_MORE
    else:
        flags = 1

    # Send seems explicitly non-functional
    with pytest.raises(OSError, match=ENOTCONN_MSG) as exc:
        await s2.send(b"mno")
    assert exc.value.errno == errno.ENOTCONN
    with pytest.raises(
        NotImplementedError, match=r"^FakeNet send flags must be 0, not"
    ):
        await s2.send(b"mno", flags)

    # sendto errors
    # it's successfully used earlier
    with pytest.raises(
        NotImplementedError, match=r"^FakeNet send flags must be 0, not"
    ):
        await s2.sendto(b"mno", flags, s1.getsockname())
    with pytest.raises(TypeError, match=r"wrong number of arguments$"):
        await s2.sendto(b"mno", flags, s1.getsockname(), "extra arg")  # type: ignore[call-overload]


@pytest.mark.skipif(
    sys.platform == "win32",
    reason="functions not in socket on windows",
)
async def test_nonwindows_functionality() -> None:
    # mypy doesn't support a good way of aborting typechecking on different platforms
    if sys.platform != "win32":  # pragma: no branch
        fn()
        s1 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
        s2 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
        await s2.bind(("127.0.0.1", 0))

        # sendmsg
        with pytest.raises(OSError, match=ENOTCONN_MSG) as exc:
            await s2.sendmsg([b"mno"])
        assert exc.value.errno == errno.ENOTCONN

        assert await s1.sendmsg([b"jkl"], (), 0, s2.getsockname()) == 3
        (data, ancdata, msg_flags, addr) = await s2.recvmsg(10)
        assert data == b"jkl"
        assert ancdata == []
        assert msg_flags == 0
        assert addr == s1.getsockname()

        # TODO: recvmsg

        # recvmsg_into
        assert await s1.sendto(b"xyzw", s2.getsockname()) == 4
        buf1 = bytearray(2)
        buf2 = bytearray(3)
        ret = await s2.recvmsg_into([buf1, buf2])
        (nbytes, ancdata, msg_flags, addr) = ret
        assert nbytes == 4
        assert buf1 == b"xy"
        assert buf2 == b"zw" + b"\x00"
        assert ancdata == []
        assert msg_flags == 0
        assert addr == s1.getsockname()

        # recvmsg_into with MSG_TRUNC set
        assert await s1.sendto(b"xyzwv", s2.getsockname()) == 5
        buf1 = bytearray(2)
        ret = await s2.recvmsg_into([buf1])
        (nbytes, ancdata, msg_flags, addr) = ret
        assert nbytes == 2
        assert buf1 == b"xy"
        assert ancdata == []
        assert msg_flags == socket.MSG_TRUNC
        assert addr == s1.getsockname()

        with pytest.raises(
            AttributeError,
            match=r"^'FakeSocket' object has no attribute 'share'$",
        ):
            await s1.share(0)  # type: ignore[attr-defined]


@pytest.mark.skipif(
    sys.platform != "win32",
    reason="windows-specific fakesocket testing",
)
async def test_windows_functionality() -> None:
    # mypy doesn't support a good way of aborting typechecking on different platforms
    if sys.platform == "win32":  # pragma: no branch
        fn()
        s1 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
        s2 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
        await s1.bind(("127.0.0.1", 0))
        with pytest.raises(
            AttributeError,
            match=r"^'FakeSocket' object has no attribute 'sendmsg'$",
        ):
            await s1.sendmsg([b"jkl"], (), 0, s2.getsockname())  # type: ignore[attr-defined]
        with pytest.raises(
            AttributeError,
            match=r"^'FakeSocket' object has no attribute 'recvmsg'$",
        ):
            s2.recvmsg(0)  # type: ignore[attr-defined]
        with pytest.raises(
            AttributeError,
            match=r"^'FakeSocket' object has no attribute 'recvmsg_into'$",
        ):
            s2.recvmsg_into([])  # type: ignore[attr-defined]
        with pytest.raises(NotImplementedError):
            s1.share(0)


async def test_basic_tcp() -> None:
    fn()
    with pytest.raises(NotImplementedError):
        trio.socket.socket()


async def test_not_implemented_functions() -> None:
    fn()
    s1 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)

    # getsockopt
    with pytest.raises(
        OSError,
        match=r"^FakeNet doesn't implement getsockopt\(\d, \d\)$",
    ):
        s1.getsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY)

    # setsockopt
    with pytest.raises(
        NotImplementedError,
        match=r"^FakeNet always has IPV6_V6ONLY=True$",
    ):
        s1.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, False)
    with pytest.raises(
        OSError,
        match=r"^FakeNet doesn't implement setsockopt\(\d+, \d+, \.\.\.\)$",
    ):
        s1.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, True)
    with pytest.raises(
        OSError,
        match=r"^FakeNet doesn't implement setsockopt\(\d+, \d+, \.\.\.\)$",
    ):
        s1.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # set_inheritable
    s1.set_inheritable(False)
    with pytest.raises(
        NotImplementedError,
        match=r"^FakeNet can't make inheritable sockets$",
    ):
        s1.set_inheritable(True)

    # get_inheritable
    assert not s1.get_inheritable()


async def test_getpeername() -> None:
    fn()
    s1 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
    with pytest.raises(OSError, match=ENOTCONN_MSG) as exc:
        s1.getpeername()
    assert exc.value.errno == errno.ENOTCONN

    await s1.bind(("127.0.0.1", 0))

    with pytest.raises(
        AssertionError,
        match=r"^This method seems to assume that self._binding has a remote UDPEndpoint$",
    ):
        s1.getpeername()


async def test_init() -> None:
    fn()
    with pytest.raises(
        NotImplementedError,
        match=re.escape(
            f"FakeNet doesn't (yet) support type={trio.socket.SOCK_STREAM}",
        ),
    ):
        s1 = trio.socket.socket()

    # getsockname on unbound ipv4 socket
    s1 = trio.socket.socket(type=trio.socket.SOCK_DGRAM)
    assert s1.getsockname() == ("0.0.0.0", 0) | errno, pytest, re, socket, sys, trio | L163: # TODO: recvmsg |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_file_io.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Check the manual stubs match the list of wrapped methods."""
    # Fetch the module's source code.
    assert _file_io.__spec__ is not None
    loader = _file_io.__spec__.loader
    assert isinstance(loader, importlib.abc.SourceLoader)
    source = io.StringIO(loader.get_source("trio._file_io"))

    # Find the class, then find the TYPE_CHECKING block.
    for line in source:
        if "class AsyncIOWrapper" in line:
            break
    else:  # pragma: no cover - should always find this
        pytest.fail("No class definition line?")

    for line in source:
        if "if TYPE_CHECKING" in line:
            break
    else:  # pragma: no cover - should always find this
        pytest.fail("No TYPE CHECKING line?")

    # Now we should be at the type checking block.
    found: list[tuple[str, str]] = []
    for line in source:  # pragma: no branch - expected to break early
        if line.strip() and not line.startswith(" " * 8):
            break  # Dedented out of the if TYPE_CHECKING block.
        match = re.match(r"\s*(async )?def ([a-zA-Z0-9_]+)\(", line)
        if match is not None:
            kind = "async" if match.group(1) is not None else "sync"
            found.append((match.group(2), kind))

    # Compare two lists so that we can easily see duplicates, and see what is different overall.
    expected = [(fname, "async") for fname in _FILE_ASYNC_METHODS]
    expected += [(fname, "sync") for fname in _FILE_SYNC_ATTRS]
    # Ignore order, error if duplicates are present.
    found.sort()
    expected.sort()
    assert found == expected


def test_sync_attrs_forwarded(
    async_file: AsyncIOWrapper[mock.Mock],
    wrapped: mock.Mock,
) -> None:
    for attr_name in _FILE_SYNC_ATTRS:
        if attr_name not in dir(async_file):
            continue

        assert getattr(async_file, attr_name) is getattr(wrapped, attr_name)


def test_sync_attrs_match_wrapper(
    async_file: AsyncIOWrapper[mock.Mock],
    wrapped: mock.Mock,
) -> None:
    for attr_name in _FILE_SYNC_ATTRS:
        if attr_name in dir(async_file):
            continue

        with pytest.raises(AttributeError):
            getattr(async_file, attr_name)

        with pytest.raises(AttributeError):
            getattr(wrapped, attr_name)


def test_async_methods_generated_once(async_file: AsyncIOWrapper[mock.Mock]) -> None:
    for meth_name in _FILE_ASYNC_METHODS:
        if meth_name not in dir(async_file):
            continue

        assert getattr(async_file, meth_name) is getattr(async_file, meth_name)


# I gave up on typing this one
def test_async_methods_signature(async_file: AsyncIOWrapper[mock.Mock]) -> None:
    # use read as a representative of all async methods
    assert async_file.read.__name__ == "read"
    assert async_file.read.__qualname__ == "AsyncIOWrapper.read"

    assert async_file.read.__doc__ is not None
    assert "io.StringIO.read" in async_file.read.__doc__


async def test_async_methods_wrap(
    async_file: AsyncIOWrapper[mock.Mock],
    wrapped: mock.Mock,
) -> None:
    for meth_name in _FILE_ASYNC_METHODS:
        if meth_name not in dir(async_file):
            continue

        meth = getattr(async_file, meth_name)
        wrapped_meth = getattr(wrapped, meth_name)

        value = await meth(sentinel.argument, keyword=sentinel.keyword)

        wrapped_meth.assert_called_once_with(
            sentinel.argument,
            keyword=sentinel.keyword,
        )
        assert value == wrapped_meth()

        wrapped.reset_mock()


def test_async_methods_match_wrapper(
    async_file: AsyncIOWrapper[mock.Mock],
    wrapped: mock.Mock,
) -> None:
    for meth_name in _FILE_ASYNC_METHODS:
        if meth_name in dir(async_file):
            continue

        with pytest.raises(AttributeError):
            getattr(async_file, meth_name)

        with pytest.raises(AttributeError):
            getattr(wrapped, meth_name)


async def test_open(path: pathlib.Path) -> None:
    f = await trio.open_file(path, "w")

    assert isinstance(f, AsyncIOWrapper)

    await f.aclose()


async def test_open_context_manager(path: pathlib.Path) -> None:
    async with await trio.open_file(path, "w") as f:
        assert isinstance(f, AsyncIOWrapper)
        assert not f.closed

    assert f.closed


async def test_async_iter() -> None:
    async_file = trio.wrap_file(io.StringIO("test\nfoo\nbar"))
    expected = list(async_file.wrapped)
    async_file.wrapped.seek(0)

    result = [line async for line in async_file]

    assert result == expected


async def test_aclose_cancelled(path: pathlib.Path) -> None:
    with _core.CancelScope() as cscope:
        f = await trio.open_file(path, "w")
        cscope.cancel()

        with pytest.raises(_core.Cancelled):
            await f.write("a")

        with pytest.raises(_core.Cancelled):
            await f.aclose()

    assert f.closed


async def test_detach_rewraps_asynciobase(tmp_path: pathlib.Path) -> None:
    tmp_file = tmp_path / "filename"
    tmp_file.touch()
    # flake8-async does not like opening files in async mode
    with open(tmp_file, mode="rb", buffering=0) as raw:  # noqa: ASYNC230
        buffered = io.BufferedReader(raw)

        async_file = trio.wrap_file(buffered)

        detached = await async_file.detach()

        assert isinstance(detached, AsyncIOWrapper)
        assert detached.wrapped is raw | __future__, importlib, io, os, pathlib, pytest, re, trio, typing, unittest |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_generic.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, pytest, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_open_tcp_listeners.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, errno, exceptiongroup, pytest, socket, sys, trio, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_open_tcp_stream.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, attrs, collections, exceptiongroup, pytest, socket, sys, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_open_unix_stream.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, pytest, socket, sys, tempfile, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_serve_listeners.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, attrs, collections, errno, functools, pytest, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, errno, pytest, socket, sys, typing | L36: # TODO: does not raise an error? |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_highlevel_ssl_helpers.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, functools, pytest, socket, ssl, trio, typing | L82: # TODO: this function wraps an SSLListener around a SocketListener, this is illegal |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_path.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, collections, os, pathlib, pytest, trio, typing | L79: # upstream python3.8 bug: we should also test (pathlib.Path, trio.Path), but |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_repl.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Pass in a list of strings.
    Returns a callable that returns each string, each time its called
    When there are not more strings to return, raise EOFError | __future__, functools, os, pathlib, pty, pytest, signal, subprocess, sys, trio, typing | L257: def test_ki_newline_injection() -> None:  # TODO: test this line
L258: # TODO: we want to remove this functionality, eg by using vendored
L327: # TODO: consider making run_process stdout have some universal newlines thing |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_scheduler_determinism.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Returns a scheduler-dependent value we can use to check determinism."""
    trace = []

    async def tracer(name: str) -> None:
        for i in range(50):
            trace.append((name, i))
            await trio.lowlevel.checkpoint()

    async with trio.open_nursery() as nursery:
        for i in range(5):
            nursery.start_soon(tracer, str(i))

    return tuple(trace)


def test_the_trio_scheduler_is_not_deterministic() -> None:
    # At least, not yet.  See https://github.com/python-trio/trio/issues/32
    traces = [trio.run(scheduler_trace) for _ in range(10)]
    assert len(set(traces)) == len(traces)


def test_the_trio_scheduler_is_deterministic_if_seeded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(trio._core._run, "_ALLOW_DETERMINISTIC_SCHEDULING", True)
    traces = []
    for _ in range(10):
        state = trio._core._run._r.getstate()
        try:
            trio._core._run._r.seed(0)
            traces.append(trio.run(scheduler_trace))
        finally:
            trio._core._run._r.setstate(state)

    assert len(traces) == 10
    assert len(set(traces)) == 1 | __future__, pytest, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_signals.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, pytest, signal, traceback, trio, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, attrs, collections, errno, inspect, os, pathlib, pytest, socket, sys, tempfile, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_ssl.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, contextlib, cryptography, functools, OpenSSL, os, pytest, socket, ssl, sys, threading, trio, trustme, typing | L133: # This is an obscure workaround for an openssl bug. In server mode, in
L141: # hiding any (other) real bugs. For more details see:
L303: # PyOpenSSL bug: doesn't accept bytearray
L343: # PyOpenSSLEchoStream, so this makes sure that if we do have a bug then |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_subprocess.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, contextlib, functools, gc, os, pathlib, pytest, random, signal, subprocess, sys, trio, types, typing, unittest |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_sync.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, math, pytest, re, trio, typing, weakref |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_testing.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, pytest, tempfile, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_testing_raisesgroup.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, exceptiongroup, pytest, re, sys, trio, types |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_threads.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, contextvars, ctypes, functools, outcome, pytest, queue, re, sniffio, sys, threading, time, typing, weakref | L268: # used for debugging when testing via CI
L471: #   https://bugs.python.org/issue30744 |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_timeouts.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, collections, outcome, pytest, time, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_tracing.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, collections, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_trio.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | sys, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_unix_pipes.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Makes a new pair of pipes."""
    (r, w) = os.pipe()
    return FdStream(w), FdStream(r)


async def make_clogged_pipe() -> tuple[FdStream, FdStream]:
    s, r = await make_pipe()
    try:
        while True:
            # We want to totally fill up the pipe buffer.
            # This requires working around a weird feature that POSIX pipes
            # have.
            # If you do a write of <= PIPE_BUF bytes, then it's guaranteed
            # to either complete entirely, or not at all. So if we tried to
            # write PIPE_BUF bytes, and the buffer's free space is only
            # PIPE_BUF/2, then the write will raise BlockingIOError... even
            # though a smaller write could still succeed! To avoid this,
            # make sure to write >PIPE_BUF bytes each time, which disables
            # the special behavior.
            # For details, search for PIPE_BUF here:
            #   http://pubs.opengroup.org/onlinepubs/9699919799/functions/write.html

            # for the getattr:
            # https://bitbucket.org/pypy/pypy/issues/2876/selectpipe_buf-is-missing-on-pypy3
            buf_size = getattr(select, "PIPE_BUF", 8192)
            os.write(s.fileno(), b"x" * buf_size * 2)
    except BlockingIOError:
        pass
    return s, r


async def test_send_pipe() -> None:
    r, w = os.pipe()
    async with FdStream(w) as send:
        assert send.fileno() == w
        await send.send_all(b"123")
        assert (os.read(r, 8)) == b"123"

        os.close(r)


async def test_receive_pipe() -> None:
    r, w = os.pipe()
    async with FdStream(r) as recv:
        assert (recv.fileno()) == r
        os.write(w, b"123")
        assert (await recv.receive_some(8)) == b"123"

        os.close(w)


async def test_pipes_combined() -> None:
    write, read = await make_pipe()
    count = 2**20

    async def sender() -> None:
        big = bytearray(count)
        await write.send_all(big)

    async def reader() -> None:
        await wait_all_tasks_blocked()
        received = 0
        while received < count:
            received += len(await read.receive_some(4096))

        assert received == count

    async with _core.open_nursery() as n:
        n.start_soon(sender)
        n.start_soon(reader)

    await read.aclose()
    await write.aclose()


async def test_pipe_errors() -> None:
    with pytest.raises(TypeError):
        FdStream(None)

    r, w = os.pipe()
    os.close(w)
    async with FdStream(r) as s:
        with pytest.raises(ValueError, match=r"^max_bytes must be integer >= 1$"):
            await s.receive_some(0)


async def test_del() -> None:
    w, r = await make_pipe()
    f1, f2 = w.fileno(), r.fileno()
    del w, r
    gc_collect_harder()

    with pytest.raises(OSError, match=r"Bad file descriptor$") as excinfo:
        os.close(f1)
    assert excinfo.value.errno == errno.EBADF

    with pytest.raises(OSError, match=r"Bad file descriptor$") as excinfo:
        os.close(f2)
    assert excinfo.value.errno == errno.EBADF


async def test_async_with() -> None:
    w, r = await make_pipe()
    async with w, r:
        pass

    assert w.fileno() == -1
    assert r.fileno() == -1

    with pytest.raises(OSError, match=r"Bad file descriptor$") as excinfo:
        os.close(w.fileno())
    assert excinfo.value.errno == errno.EBADF

    with pytest.raises(OSError, match=r"Bad file descriptor$") as excinfo:
        os.close(r.fileno())
    assert excinfo.value.errno == errno.EBADF


async def test_misdirected_aclose_regression() -> None:
    # https://github.com/python-trio/trio/issues/661#issuecomment-456582356
    w, r = await make_pipe()
    old_r_fd = r.fileno()

    # Close the original objects
    await w.aclose()
    await r.aclose()

    # Do a little dance to get a new pipe whose receive handle matches the old
    # receive handle.
    r2_fd, w2_fd = os.pipe()
    if r2_fd != old_r_fd:  # pragma: no cover
        os.dup2(r2_fd, old_r_fd)
        os.close(r2_fd)
    async with FdStream(old_r_fd) as r2:
        assert r2.fileno() == old_r_fd

        # And now set up a background task that's working on the new receive
        # handle
        async def expect_eof() -> None:
            assert await r2.receive_some(10) == b""

        async with _core.open_nursery() as nursery:
            nursery.start_soon(expect_eof)
            await wait_all_tasks_blocked()

            # Here's the key test: does calling aclose() again on the *old*
            # handle, cause the task blocked on the *new* handle to raise
            # ClosedResourceError?
            await r.aclose()
            await wait_all_tasks_blocked()

            # Guess we survived! Close the new write handle so that the task
            # gets an EOF and can exit cleanly.
            os.close(w2_fd)


async def test_close_at_bad_time_for_receive_some(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # We used to have race conditions where if one task was using the pipe,
    # and another closed it at *just* the wrong moment, it would give an
    # unexpected error instead of ClosedResourceError:
    # https://github.com/python-trio/trio/issues/661
    #
    # This tests what happens if the pipe gets closed in the moment *between*
    # when receive_some wakes up, and when it tries to call os.read
    async def expect_closedresourceerror() -> None:
        with pytest.raises(_core.ClosedResourceError):
            await r.receive_some(10)

    orig_wait_readable = _core._run.TheIOManager.wait_readable

    async def patched_wait_readable(
        self: _core._run.TheIOManager,
        fd: int \\| _HasFileNo,
    ) -> None:
        await orig_wait_readable(self, fd)
        await r.aclose()

    monkeypatch.setattr(_core._run.TheIOManager, "wait_readable", patched_wait_readable)
    s, r = await make_pipe()
    async with s, r:
        async with _core.open_nursery() as nursery:
            nursery.start_soon(expect_closedresourceerror)
            await wait_all_tasks_blocked()
            # Trigger everything by waking up the receiver
            await s.send_all(b"x")


async def test_close_at_bad_time_for_send_all(monkeypatch: pytest.MonkeyPatch) -> None:
    # We used to have race conditions where if one task was using the pipe,
    # and another closed it at *just* the wrong moment, it would give an
    # unexpected error instead of ClosedResourceError:
    # https://github.com/python-trio/trio/issues/661
    #
    # This tests what happens if the pipe gets closed in the moment *between*
    # when send_all wakes up, and when it tries to call os.write
    async def expect_closedresourceerror() -> None:
        with pytest.raises(_core.ClosedResourceError):
            await s.send_all(b"x" * 100)

    orig_wait_writable = _core._run.TheIOManager.wait_writable

    async def patched_wait_writable(
        self: _core._run.TheIOManager,
        fd: int \\| _HasFileNo,
    ) -> None:
        await orig_wait_writable(self, fd)
        await s.aclose()

    monkeypatch.setattr(_core._run.TheIOManager, "wait_writable", patched_wait_writable)
    s, r = await make_clogged_pipe()
    async with s, r:
        async with _core.open_nursery() as nursery:
            nursery.start_soon(expect_closedresourceerror)
            await wait_all_tasks_blocked()
            # Trigger everything by waking up the sender. On ppc64el, PIPE_BUF
            # is 8192 but make_clogged_pipe() ends up writing a total of
            # 1048576 bytes before the pipe is full, and then a subsequent
            # receive_some(10000) isn't sufficient for orig_wait_writable() to
            # return for our subsequent aclose() call. It's necessary to empty
            # the pipe further before this happens. So we loop here until the
            # pipe is empty to make sure that the sender wakes up even in this
            # case. Otherwise patched_wait_writable() never gets to the
            # aclose(), so expect_closedresourceerror() never returns, the
            # nursery never finishes all tasks and this test hangs.
            received_data = await r.receive_some(10000)
            while received_data:
                received_data = await r.receive_some(10000)


# On FreeBSD, directories are readable, and we haven't found any other trick
# for making an unreadable fd, so there's no way to run this test. Fortunately
# the logic this is testing doesn't depend on the platform, so testing on
# other platforms is probably good enough.
@pytest.mark.skipif(
    sys.platform.startswith("freebsd"),
    reason="no way to make read() return a bizarro error on FreeBSD",
)
async def test_bizarro_OSError_from_receive() -> None:
    # Make sure that if the read syscall returns some bizarro error, then we
    # get a BrokenResourceError. This is incredibly unlikely; there's almost
    # no way to trigger a failure here intentionally (except for EBADF, but we
    # exploit that to detect file closure, so it takes a different path). So
    # we set up a strange scenario where the pipe fd somehow transmutes into a
    # directory fd, causing os.read to raise IsADirectoryError (yes, that's a
    # real built-in exception type).
    s, r = await make_pipe()
    async with s, r:
        dir_fd = os.open("/", os.O_DIRECTORY, 0)
        try:
            os.dup2(dir_fd, r.fileno())
            with pytest.raises(_core.BrokenResourceError):
                await r.receive_some(10)
        finally:
            os.close(dir_fd)


@skip_if_fbsd_pipes_broken
async def test_pipe_fully() -> None:
    await check_one_way_stream(make_pipe, make_clogged_pipe) | , __future__, errno, os, pytest, select, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_util.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Test that subclassing a @final-annotated class is not allowed.

    This checks both runtime results, and verifies that type checkers detect
    the error statically through the type-ignore comment. | , __future__, asyncio, collections, exceptiongroup, pytest, sys, trio, types, typing | L299: match=r"^Attempted to unwrap exceptiongroup with multiple non-cancelled exceptions. This is often caused by a bug in the caller.$", |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_wait_for_object.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , os, pytest, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/test_windows_pipes.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Makes a new pair of pipes."""
    (r, w) = pipe()
    return PipeSendStream(w), PipeReceiveStream(r)


def test_pipe_typecheck() -> None:
    with pytest.raises(TypeError):
        PipeSendStream(1.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        PipeReceiveStream(None)  # type: ignore[arg-type]


async def test_pipe_error_on_close() -> None:
    # Make sure we correctly handle a failure from kernel32.CloseHandle
    r, w = pipe()

    send_stream = PipeSendStream(w)
    receive_stream = PipeReceiveStream(r)

    assert kernel32.CloseHandle(_handle(r))
    assert kernel32.CloseHandle(_handle(w))

    with pytest.raises(OSError, match=r"^\[WinError 6\] The handle is invalid$"):
        await send_stream.aclose()
    with pytest.raises(OSError, match=r"^\[WinError 6\] The handle is invalid$"):
        await receive_stream.aclose()


async def test_pipes_combined() -> None:
    write, read = await make_pipe()
    count = 2**20
    replicas = 3

    async def sender() -> None:
        async with write:
            big = bytearray(count)
            for _ in range(replicas):
                await write.send_all(big)

    async def reader() -> None:
        async with read:
            await wait_all_tasks_blocked()
            total_received = 0
            while True:
                # 5000 is chosen because it doesn't evenly divide 2**20
                received = len(await read.receive_some(5000))
                if not received:
                    break
                total_received += received

            assert total_received == count * replicas

    async with _core.open_nursery() as n:
        n.start_soon(sender)
        n.start_soon(reader)


async def test_async_with() -> None:
    w, r = await make_pipe()
    async with w, r:
        pass

    with pytest.raises(_core.ClosedResourceError):
        await w.send_all(b"")
    with pytest.raises(_core.ClosedResourceError):
        await r.receive_some(10)


async def test_close_during_write() -> None:
    w, _r = await make_pipe()
    async with _core.open_nursery() as nursery:

        async def write_forever() -> None:
            with pytest.raises(_core.ClosedResourceError) as excinfo:
                while True:
                    await w.send_all(b"x" * 4096)
            assert "another task" in str(excinfo.value)

        nursery.start_soon(write_forever)
        await wait_all_tasks_blocked(0.1)
        await w.aclose()


async def test_pipe_fully() -> None:
    # passing make_clogged_pipe tests wait_send_all_might_not_block, and we
    # can't implement that on Windows
    await check_one_way_stream(make_pipe, None) | , __future__, asyncio, pytest, sys, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/tools/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/tools/test_gen_exports.py` | ❓ UNKNOWN | 2025-11-09 21:21 | With doc string"""

    @ignore_this
    @_public
    @another_decorator
    async def public_async_func(self) -> Counter:
        pass  # no doc string

    def not_public(self):
        pass

    async def not_public_async(self):
        pass
'''

IMPORT_1 = | , ast, astor, black, collections, isort, os, pathlib, pytest, ruff, sys, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/tools/test_mypy_annotate.py` | ❓ UNKNOWN | 2025-11-09 21:21 | result_file = tmp_path / "dump.dat"
    assert not result_file.exists()
    with monkeypatch.context():
        monkeypatch.setattr(sys, "stdin", io.StringIO(inp_text))

        mypy_annotate.main(
            ["--dumpfile", str(result_file), "--platform", "SomePlatform"],
        )

    std = capsys.readouterr()
    assert std.err == ""
    assert std.out == inp_text  # Echos the original.

    assert result_file.exists()

    main(["--dumpfile", str(result_file)])

    std = capsys.readouterr()
    assert std.err == ""
    assert std.out == (
        "::error file=trio/core.py,line=15,title=Mypy-SomePlatform::trio/core.py:15: Bad types here [misc]\n"
        "::warning file=trio/package/module.py,line=48,col=4,endLine=56,endColumn=18,"
        "title=Mypy-SomePlatform::trio/package/module.py:(48:4 - 56:18): Missing "
        "annotations  [no-untyped-def]\n"
    ) | __future__, io, pathlib, pytest, sys, trio, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/tools/test_sync_requirements.py` | ❓ UNKNOWN | 2025-11-09 21:21 | results = tuple(yield_pre_commit_version_data(text))
    assert results == (
        ("ruff-pre-commit", "0.11.0"),
        ("black-pre-commit-mirror", "25.1.0"),
    )


def test_update_requirements(
    tmp_path: Path,
) -> None:
    requirements_file = tmp_path / "requirements.txt"
    assert not requirements_file.exists()
    requirements_file.write_text( | __future__, pathlib, trio, typing, yaml |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/type_tests/check_wraps.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | trio, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/type_tests/open_memory_channel.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/type_tests/path.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Path wrapping is quite complex, ensure all methods are understood as wrapped correctly."""

import io
import os
import pathlib
import sys
from typing import IO, Any, BinaryIO

import trio
from trio._file_io import AsyncIOWrapper
from typing_extensions import assert_type


def operator_checks(text: str, tpath: trio.Path, ppath: pathlib.Path) -> None: | io, os, pathlib, sys, trio, typing, typing_extensions | L87: # TODO: Path.walk() in 3.12
L139: # TODO: report mypy bug: equiv to https://github.com/microsoft/pyright/issues/6833 |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/type_tests/raisesgroup.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Check type narrowing on the `check` argument to `RaisesGroup`.
    All `type: ignore`s are correctly pointing out type errors. | __future__, collections, exceptiongroup, sys, trio, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/type_tests/subprocesses.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | sys, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tests/type_tests/task_status.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Check that started() can only be called for TaskStatus[None]."""

from trio import TaskStatus
from typing_extensions import assert_type


def check_status(
    none_status_explicit: TaskStatus[None],
    none_status_implicit: TaskStatus,
    int_status: TaskStatus[int],
) -> None:
    assert_type(none_status_explicit, TaskStatus[None])
    assert_type(none_status_implicit, TaskStatus[None])  # Default typevar
    assert_type(int_status, TaskStatus[int])

    # Omitting the parameter is only allowed for None.
    none_status_explicit.started()
    none_status_implicit.started()
    int_status.started()  # type: ignore

    # Explicit None is allowed.
    none_status_explicit.started(None)
    none_status_implicit.started(None)
    int_status.started(None)  # type: ignore

    none_status_explicit.started(42)  # type: ignore
    none_status_implicit.started(42)  # type: ignore
    int_status.started(42)
    int_status.started(True) | trio, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_threads.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Global due to Threading API, thread local storage for data related to the
    parent task of native Trio threads. | , __future__, attrs, collections, contextlib, contextvars, inspect, itertools, outcome, queue, sniffio, threading, trio, typing, typing_extensions | L334: IO-bound threads <https://bugs.python.org/issue7946>`__, so using
L454: else:  # pragma: no cover, internal debugging guard TODO: use assert_never |
| `blackboard-agent/venv/Lib/site-packages/trio/_timeouts.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Use as a context manager to create a cancel scope with the given
    absolute deadline.

    Args:
      deadline (float): The deadline.
      shield (bool): Initial value for the `~trio.CancelScope.shield` attribute
          of the newly created cancel scope.

    Raises:
      ValueError: if deadline is NaN. | __future__, collections, contextlib, inspect, math, sys, trio, typing | L193: if "sphinx.ext.autodoc" in sys.modules: |
| `blackboard-agent/venv/Lib/site-packages/trio/_tools/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tools/gen_exports.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Code generation script for class methods
to be exported as public API | , __future__, argparse, ast, astor, attrs, black, collections, os, pathlib, ruff, subprocess, sys, textwrap, typing | L293: if not matches_disk:  # TODO: test this branch |
| `blackboard-agent/venv/Lib/site-packages/trio/_tools/mypy_annotate.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Translates Mypy's output into GitHub's error/warning annotation syntax.

See: https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions

This first is run with Mypy's output piped in, to collect messages in
mypy_annotate.dat. After all platforms run, we run this again, which prints the
messages in GitHub's format but with cross-platform failures deduplicated. | __future__, argparse, attrs, pickle, re, sys |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tools/sync_requirements.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Sync Requirements - Automatically upgrade test requirements pinned
versions from pre-commit config file. | __future__, collections, pathlib, sys, typing, yaml |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_tools/windows_ffi_build.py` | ❓ UNKNOWN | 2025-11-09 21:21 | # cribbed from pywincffi
# programmatically strips out those annotations MSDN likes, like _In_
LIB = re.sub(r"\b(_In_\\|_Inout_\\|_Out_\\|_Outptr_\\|_Reserved_)(opt_)?\b", " ", LIB)

# Other fixups:
# - get rid of FAR, cffi doesn't like it
LIB = re.sub(r"\bFAR\b", " ", LIB)
# - PASCAL is apparently an alias for __stdcall (on modern compilers - modern
#   being _MSC_VER >= 800)
LIB = re.sub(r"\bPASCAL\b", "__stdcall", LIB)

ffibuilder = cffi.FFI()
# a bit hacky but, it works
ffibuilder.set_source("trio._core._generated_windows_ffi", None)
ffibuilder.cdef(LIB)

if __name__ == "__main__":
    ffibuilder.compile("src") | cffi, re | L152: ULONG RtlNtStatusToDosError(
L215: # a bit hacky but, it works |
| `blackboard-agent/venv/Lib/site-packages/trio/_unix_pipes.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents a stream given the file descriptor to a pipe, TTY, etc.

    *fd* must refer to a file that is open for reading and/or writing and
    supports non-blocking I/O (pipes and TTYs will work, on-disk files probably
    not).  The returned stream takes ownership of the fd, so closing the stream
    will close the fd too.  As with `os.fdopen`, you should not directly use
    an fd after you have wrapped it in a stream using this function.

    To be used as a Trio stream, an open file must be placed in non-blocking
    mode.  Unfortunately, this impacts all I/O that goes through the
    underlying open file, including I/O that uses a different
    file descriptor than the one that was passed to Trio. If other threads
    or processes are using file descriptors that are related through `os.dup`
    or inheritance across `os.fork` to the one that Trio is using, they are
    unlikely to be prepared to have non-blocking I/O semantics suddenly
    thrust upon them.  For example, you can use
    ``FdStream(os.dup(sys.stdin.fileno()))`` to obtain a stream for reading
    from standard input, but it is only safe to do so with heavy caveats: your
    stdin must not be shared by any other processes, and you must not make any
    calls to synchronous methods of `sys.stdin` until the stream returned by
    `FdStream` is closed. See `issue #174
    <https://github.com/python-trio/trio/issues/174>`__ for a discussion of the
    challenges involved in relaxing this restriction.

    .. warning:: one specific consequence of non-blocking mode
      applying to the entire open file description is that when
      your program is run with multiple standard streams connected to
      a TTY (as in a terminal emulator), all of the streams become
      non-blocking when you construct an `FdStream` for any of them.
      For example, if you construct an `FdStream` for standard input,
      you might observe Python loggers begin to fail with
      `BlockingIOError`.

    Args:
      fd (int): The fd to be wrapped.

    Returns:
      A new `FdStream` object. | , __future__, errno, os, sys, trio, typing | L15: # XX TODO: is this a good number? who knows... it does match the default Linux |
| `blackboard-agent/venv/Lib/site-packages/trio/_util.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Attempt to reliably check if we are in the main thread."""
    try:
        signal.signal(signal.SIGINT, signal.getsignal(signal.SIGINT))
        return True
    except (TypeError, ValueError):
        return False


######
# Call the function and get the coroutine object, while giving helpful
# errors for common mistakes. Returns coroutine object.
######
def coroutine_or_error(
    async_fn: Callable[[Unpack[PosArgsT]], Awaitable[RetT]],
    *args: Unpack[PosArgsT],
) -> collections.abc.Coroutine[object, NoReturn, RetT]:
    def _return_value_looks_like_wrong_library(value: object) -> bool:
        # Returned by legacy @asyncio.coroutine functions, which includes
        # a surprising proportion of asyncio builtins.
        if isinstance(value, collections.abc.Generator):
            return True
        # The protocol for detecting an asyncio Future-like object
        if getattr(value, "_asyncio_future_blocking", None) is not None:
            return True
        # This janky check catches tornado Futures and twisted Deferreds.
        # By the time we're calling this function, we already know
        # something has gone wrong, so a heuristic is pretty safe.
        return value.__class__.__name__ in ("Future", "Deferred")

    # Make sure a sync-fn-that-returns-coroutine still sees itself as being
    # in trio context
    prev_loop, sniffio_loop.name = sniffio_loop.name, "trio"

    try:
        coro = async_fn(*args)

    except TypeError:
        # Give good error for: nursery.start_soon(trio.sleep(1))
        if isinstance(async_fn, collections.abc.Coroutine):
            # explicitly close coroutine to avoid RuntimeWarning
            async_fn.close()

            raise TypeError(
                "Trio was expecting an async function, but instead it got "
                f"a coroutine object {async_fn!r}\n"
                "\n"
                "Probably you did something like:\n"
                "\n"
                f"  trio.run({async_fn.__name__}(...))            # incorrect!\n"
                f"  nursery.start_soon({async_fn.__name__}(...))  # incorrect!\n"
                "\n"
                "Instead, you want (notice the parentheses!):\n"
                "\n"
                f"  trio.run({async_fn.__name__}, ...)            # correct!\n"
                f"  nursery.start_soon({async_fn.__name__}, ...)  # correct!",
            ) from None

        # Give good error for: nursery.start_soon(future)
        if _return_value_looks_like_wrong_library(async_fn):
            raise TypeError(
                "Trio was expecting an async function, but instead it got "
                f"{async_fn!r} – are you trying to use a library written for "
                "asyncio/twisted/tornado or similar? That won't work "
                "without some sort of compatibility shim.",
            ) from None

        raise

    finally:
        sniffio_loop.name = prev_loop

    # We can't check iscoroutinefunction(async_fn), because that will fail
    # for things like functools.partial objects wrapping an async
    # function. So we have to just call it and then check whether the
    # return value is a coroutine object.
    # Note: will not be necessary on python>=3.8, see https://bugs.python.org/issue34890
    # TODO: python3.7 support is now dropped, so the above can be addressed.
    if not isinstance(coro, collections.abc.Coroutine):
        # Give good error for: nursery.start_soon(func_returning_future)
        if _return_value_looks_like_wrong_library(coro):
            raise TypeError(
                f"Trio got unexpected {coro!r} – are you trying to use a "
                "library written for asyncio/twisted/tornado or similar? "
                "That won't work without some sort of compatibility shim.",
            )

        if inspect.isasyncgen(coro):
            raise TypeError(
                "start_soon expected an async function but got an async "
                f"generator {coro!r}",
            )

        # Give good error for: nursery.start_soon(some_sync_fn)
        raise TypeError(
            "Trio expected an async function, but {!r} appears to be "
            "synchronous".format(getattr(async_fn, "__qualname__", async_fn)),
        )

    return coro


class ConflictDetector: | __future__, abc, collections, exceptiongroup, inspect, signal, sniffio, sys, trio, types, typing, typing_extensions | L122: # Note: will not be necessary on python>=3.8, see https://bugs.python.org/issue34890
L123: # TODO: python3.7 support is now dropped, so the above can be addressed.
L378: "Attempted to unwrap exceptiongroup with multiple non-cancelled exceptions. This is often caused by a bug in the caller." |
| `blackboard-agent/venv/Lib/site-packages/trio/_version.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_wait_for_object.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Async and cancellable variant of WaitForSingleObject. Windows only.

    Args:
      handle: A Win32 handle, as a Python integer.

    Raises:
      OSError: If the handle is invalid, e.g. when it is already closed. | , __future__, math, trio |  |
| `blackboard-agent/venv/Lib/site-packages/trio/_windows_pipes.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Represents a send stream over a Windows named pipe that has been
    opened in OVERLAPPED mode. | , __future__, sys, typing | L13: # XX TODO: don't just make this up based on nothing. |
| `blackboard-agent/venv/Lib/site-packages/trio/abc.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/from_thread.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This namespace represents special functions that can call back into Trio from
an external thread by means of a Trio Token present in Thread Local Storage |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/lowlevel.py` | ❓ UNKNOWN | 2025-11-09 21:21 | This namespace represents low-level functionality not intended for daily use,
but useful for extending Trio's functionality. | , select, sys, typing | L63: not _t.TYPE_CHECKING and "sphinx.ext.autodoc" in sys.modules
L80: not _t.TYPE_CHECKING and "sphinx.ext.autodoc" in sys.modules
L88: ) or (not _t.TYPE_CHECKING and "sphinx.ext.autodoc" in sys.modules): |
| `blackboard-agent/venv/Lib/site-packages/trio/socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | , __future__, contextlib, socket, sys, typing | L470: SO_DEBUG as SO_DEBUG, |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_check_streams.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Perform a number of generic tests on a custom one-way stream
    implementation.

    Args:
      stream_maker: An async (!) function which returns a connected
          (:class:`~trio.abc.SendStream`, :class:`~trio.abc.ReceiveStream`)
          pair.
      clogged_stream_maker: Either None, or an async function similar to
          stream_maker, but with the extra property that the returned stream
          is in a state where ``send_all`` and
          ``wait_send_all_might_not_block`` will block until ``receive_some``
          has been called. This allows for more thorough testing of some edge
          cases, especially around ``wait_send_all_might_not_block``.

    Raises:
      AssertionError: if a test fails. | , __future__, collections, contextlib, exceptiongroup, random, sys, types, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_checkpoints.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Check if checkpoints are executed in a block of code."""
    __tracebackhide__ = True
    task = _core.current_task()
    orig_cancel = task._cancel_points
    orig_schedule = task._schedule_points
    try:
        yield
        if expected and (
            task._cancel_points == orig_cancel or task._schedule_points == orig_schedule
        ):
            raise AssertionError("assert_checkpoints block did not yield!")
    finally:
        if not expected and (
            task._cancel_points != orig_cancel or task._schedule_points != orig_schedule
        ):
            raise AssertionError("assert_no_checkpoints block yielded!")


def assert_checkpoints() -> AbstractContextManager[None]: | , __future__, collections, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_fake_net.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | __future__, attrs, builtins, collections, contextlib, errno, ipaddress, os, socket, sys, trio, types, typing, typing_extensions | L4: # TODO:
L285: assert _ == [], "TODO: handle other values?"
L402: # TODO: This method is not tested, and seems to make incorrect assumptions. It should maybe raise NotImplementedError. |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_memory_streams.py` | ❓ UNKNOWN | 2025-11-09 21:21 | An in-memory :class:`~trio.abc.SendStream`.

    Args:
      send_all_hook: An async function, or None. Called from
          :meth:`send_all`. Can do whatever you like.
      wait_send_all_might_not_block_hook: An async function, or None. Called
          from :meth:`wait_send_all_might_not_block`. Can do whatever you
          like.
      close_hook: A synchronous function, or None. Called from :meth:`close`
          and :meth:`aclose`. Can do whatever you like.

    .. attribute:: send_all_hook
                   wait_send_all_might_not_block_hook
                   close_hook

       All of these hooks are also exposed as attributes on the object, and
       you can change them at any time. | , __future__, collections, operator, typing | L128: # buggy user code that calls this twice at the same time.
L142: # buggy user code that calls this twice at the same time.
L238: # buggy user code that calls this twice at the same time.
L279: # TODO: investigate why this is necessary for the docs |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_network.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Connect to the given :class:`~trio.SocketListener`.

    This is particularly useful in tests when you want to let a server pick
    its own port, and then connect to it::

        listeners = await trio.open_tcp_listeners(0)
        client = await trio.testing.open_stream_to_socket_listener(listeners[0])

    Args:
      socket_listener (~trio.SocketListener): The
          :class:`~trio.SocketListener` to connect to.

    Returns:
      SocketStream: a stream connected to the given listener. |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_raises_group.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Minimal re-implementation of pytest.ExceptionInfo, only used if pytest is not available. Supports a subset of its features necessary for functionality of :class:`trio.testing.RaisesGroup` and :class:`trio.testing.Matcher`."""

    _excinfo: tuple[type[MatchE], MatchE, types.TracebackType] \\| None

    def __init__(
        self,
        excinfo: tuple[type[MatchE], MatchE, types.TracebackType] \\| None,
    ) -> None:
        self._excinfo = excinfo

    def fill_unfilled(
        self,
        exc_info: tuple[type[MatchE], MatchE, types.TracebackType],
    ) -> None: | __future__, _pytest, abc, builtins, collections, exceptiongroup, pytest, re, sys, textwrap, trio, types, typing, typing_extensions | L248: # TODO: when transitioning to pytest, harmonize Matcher and RaisesGroup |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_sequencer.py` | ❓ UNKNOWN | 2025-11-09 21:21 | A convenience class for forcing code in different tasks to run in an
    explicit linear order.

    Instances of this class implement a ``__call__`` method which returns an
    async context manager. The idea is that you pass a sequence number to
    ``__call__`` to say where this block of code should go in the linear
    sequence. Block 0 starts immediately, and then block N doesn't start until
    block N-1 has finished.

    Example:
      An extremely elaborate way to print the numbers 0-5, in order::

         async def worker1(seq):
             async with seq(0):
                 print(0)
             async with seq(4):
                 print(4)

         async def worker2(seq):
             async with seq(2):
                 print(2)
             async with seq(5):
                 print(5)

         async def worker3(seq):
             async with seq(1):
                 print(1)
             async with seq(3):
                 print(3)

         async def main():
            seq = trio.testing.Sequencer()
            async with trio.open_nursery() as nursery:
                nursery.start_soon(worker1, seq)
                nursery.start_soon(worker2, seq)
                nursery.start_soon(worker3, seq) | , __future__, attrs, collections, contextlib, typing |  |
| `blackboard-agent/venv/Lib/site-packages/trio/testing/_trio_test.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Converts an async test function to be synchronous, running via Trio.

    Usage::

        @trio_test
        async def test_whatever():
            await ...

    If a pytest fixture is passed in that subclasses the :class:`~trio.abc.Clock` or
    :class:`~trio.abc.Instrument` ABCs, then those are passed to :meth:`trio.run()`. | , __future__, collections, functools, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/trio/to_thread.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio_websocket/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/trio_websocket/_impl.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Raised as a fallback when open_websocket is unable to unwind an exceptiongroup
    into a single preferred exception. This should never happen, if it does then
    underlying assumptions about the internal code are incorrect. | __future__, collections, contextlib, exceptiongroup, functools, importlib, ipaddress, itertools, logging, outcome, random, ssl, struct, sys, trio, types, typing, typing_extensions, urllib, wsproto | L294: "Please report this as a bug to "
L362: logger.debug('Connecting to ws%s://%s:%d%s', |
| `blackboard-agent/venv/Lib/site-packages/trio_websocket/_version.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/typing_extensions.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Special type indicating an unconstrained type.
        - Any is compatible with every type.
        - Any assumed to have all methods.
        - All values assumed to be instances of Any.
        Note that all the above statements are true from the point of view of
        static type checkers. At runtime, Any should not be used with instance
        checks. | abc, annotationlib, builtins, collections, contextlib, enum, functools, inspect, io, keyword, operator, sys, types, typing, warnings | L292: # See https://bugs.python.org/issue46342
L356: # A Literal bug was fixed in 3.11.0, 3.10.1 and 3.9.8 |
| `blackboard-agent/venv/Lib/site-packages/typing_inspection/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:03 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/typing_inspection/introspection.py` | ❓ UNKNOWN | 2025-11-09 21:03 | High-level introspection utilities, used to inspect type annotations."""

from __future__ import annotations

import sys
import types
from collections.abc import Generator
from dataclasses import InitVar
from enum import Enum, IntEnum, auto
from typing import Any, Literal, NamedTuple, cast

from typing_extensions import TypeAlias, assert_never, get_args, get_origin

from . import typing_objects

__all__ = (
    'AnnotationSource',
    'ForbiddenQualifier',
    'InspectedAnnotation',
    'Qualifier',
    'get_literal_values',
    'inspect_annotation',
    'is_union_origin',
)

if sys.version_info >= (3, 14) or sys.version_info < (3, 10):

    def is_union_origin(obj: Any, /) -> bool: | , __future__, collections, dataclasses, enum, sys, types, typing, typing_extensions, typing_inspection | L221: # TODO at some point, we could switch to an enum flag, so that multiple sources
L224: # TODO if/when https://peps.python.org/pep-0767/ is accepted, add 'read_only'
L319: # TODO use a match statement when Python 3.9 support is dropped. |
| `blackboard-agent/venv/Lib/site-packages/typing_inspection/typing_objects.py` | ❓ UNKNOWN | 2025-11-09 21:03 | Low-level introspection utilities for [`typing`][] members.

The provided functions in this module check against both the [`typing`][] and [`typing_extensions`][]
variants, if they exists and are different. | collections, contextlib, re, sys, textwrap, types, typing, typing_extensions, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Python HTTP library with thread-safe connection pooling, file post support, user friendly, and more | , __future__, logging, ssl, sys, typing, warnings | L75: level: int = logging.DEBUG,
L79: debugging.
L90: logger.debug("Added a stderr logging handler to logger: %s", __name__) |
| `blackboard-agent/venv/Lib/site-packages/urllib3/_base_connection.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Whether the connection either is brand new or has been previously closed.
            If this property is True then both ``is_connected`` and ``has_connected_to_proxy``
            properties must be False. | , __future__, ssl, typing | L20: # TODO: Remove this in favor of a better |
| `blackboard-agent/venv/Lib/site-packages/urllib3/_collections.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Provides a thread-safe dict-like container which maintains up to
    ``maxsize`` keys while throwing away the least-recently-used keys beyond
    ``maxsize``.

    :param maxsize:
        Maximum number of recent elements to retain.

    :param dispose_func:
        Every time an item is evicted from the container,
        ``dispose_func(value)`` is called.  Callback which will get called | __future__, collections, enum, threading, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/_request_methods.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Convenience mixin for classes who implement a :meth:`urlopen` method, such
    as :class:`urllib3.HTTPConnectionPool` and
    :class:`urllib3.PoolManager`.

    Provides behavior for making common types of HTTP request methods and
    decides which type of request field encoding to use.

    Specifically,

    :meth:`.request_encode_url` is for sending requests whose fields are
    encoded in the URL (such as GET, HEAD, DELETE).

    :meth:`.request_encode_body` is for sending requests whose fields are
    encoded in the *body* of the request using multipart or www-form-urlencoded
    (such as for POST, PUT, PATCH).

    :meth:`.request` is for making any kind of request, it will look up the
    appropriate encoding format and use one of the above two methods to make
    the request.

    Initializer parameters:

    :param headers:
        Headers to include with all requests, unless other headers are given
        explicitly. | , __future__, json, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/_version.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/connection.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Based on :class:`http.client.HTTPConnection` but provides an extra constructor
    backwards-compatibility layer between older and newer Pythons.

    Additional keyword parameters are used to configure attributes of the connection.
    Accepted parameters include:

    - ``source_address``: Set the source address for the current connection.
    - ``socket_options``: Set specific options on the underlying socket. If not specified, then
      defaults are loaded from ``HTTPConnection.default_socket_options`` which includes disabling
      Nagle's algorithm (sets TCP_NODELAY to 1) unless the connection is behind a proxy.

      For example, if you wish to enable TCP Keep Alive in addition to the defaults,
      you might pass:

      .. code-block:: python

         HTTPConnection.default_socket_options + [
             (socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1),
         ]

      Or you may want to disable the defaults by passing an empty list (e.g., ``[]``). | , __future__, datetime, http, logging, os, re, socket, ssl, sys, threading, typing, warnings | L282: if self.debuglevel > 0:
L311: if self.debuglevel > 0:
L330: # TODO: Fix tunnel so it doesn't depend on self.sock state.
L436: # object later. TODO: Remove this in favor of a real |
| `blackboard-agent/venv/Lib/site-packages/urllib3/connectionpool.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Base class for all connection pools, such as
    :class:`.HTTPConnectionPool` and :class:`.HTTPSConnectionPool`.

    .. note::
       ConnectionPool.urlopen() does not normalize or percent-encode target URIs
       which is useful if your target server doesn't support percent-encoded
       target URIs. | , __future__, errno, logging, queue, socket, ssl, sys, types, typing, typing_extensions, warnings, weakref | L212: # These are mostly for testing and debugging purposes.
L241: log.debug(
L289: log.debug("Resetting dropped connection: %s", self.host) |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/emscripten/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , __future__, urllib3 |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/emscripten/connection.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Whether the connection either is brand new or has been previously closed.
        If this property is True then both ``is_connected`` and ``has_connected_to_proxy``
        properties must be False. | , __future__, http, os, typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/emscripten/fetch.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Support for streaming http requests in emscripten.

A few caveats -

If your browser (or Node.js) has WebAssembly JavaScript Promise Integration enabled
https://github.com/WebAssembly/js-promise-integration/blob/main/proposals/js-promise-integration/Overview.md
*and* you launch pyodide using `pyodide.runPythonAsync`, this will fetch data using the
JavaScript asynchronous fetch api (wrapped via `pyodide.ffi.call_sync`). In this case
timeouts and streaming should just work.

Otherwise, it uses a combination of XMLHttpRequest and a web-worker for streaming.

This approach has several caveats:

Firstly, you can't do streaming http in the main UI thread, because atomics.wait isn't allowed.
Streaming only works if you're running pyodide in a web worker.

Secondly, this uses an extra web worker and SharedArrayBuffer to do the asynchronous fetch
operation, so it requires that you have crossOriginIsolation enabled, by serving over https
(or from localhost) with the two headers below set:

    Cross-Origin-Opener-Policy: same-origin
    Cross-Origin-Embedder-Policy: require-corp

You can tell if cross origin isolation is successfully enabled by looking at the global crossOriginIsolated variable in
JavaScript console. If it isn't, streaming requests will fallback to XMLHttpRequest, i.e. getting the whole
request into a buffer and then returning it. it shows a warning in the JavaScript console in this case.

Finally, the webworker which does the streaming fetch is created on initial import, but will only be started once
control is returned to javascript. Call `await wait_for_streaming_ready()` to wait for streaming fetch.

NB: in this code, there are a lot of JavaScript objects. They are named js_*
to make it clear what type of object they are. | , __future__, email, importlib, io, js, json, pyodide, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/emscripten/request.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , __future__, dataclasses |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/emscripten/response.py` | ❓ UNKNOWN | 2025-11-09 19:11 | A generator wrapper for the read() method. A call will block until
        ``amt`` bytes have been read from the connection or until the
        connection is closed.

        :param amt:
            How much of the content to read. The generator will return up to
            much data per iteration, but may return less. This is particularly
            likely when using compressed data. However, the empty string will
            never be returned.

        :param decode_content:
            If True, will attempt to decode the body based on the
            'content-encoding' header. | , __future__, contextlib, dataclasses, http, io, json, logging, typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/pyopenssl.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Module for using pyOpenSSL as a TLS backend. This module was relevant before
the standard library ``ssl`` module supported SNI, but now that we've dropped
support for Python 2.7 all relevant Python versions support SNI so
**this module is no longer recommended**.

This needs the following packages installed:

* `pyOpenSSL`_ (tested with 16.0.0)
* `cryptography`_ (minimum 1.3.4, from pyopenssl)
* `idna`_ (minimum 2.0)

However, pyOpenSSL depends on cryptography, so while we use all three directly here we
end up having relatively few packages required.

You can install them with the following command:

.. code-block:: bash

    $ python -m pip install pyopenssl cryptography idna

To activate certificate checking, call
:func:`~urllib3.contrib.pyopenssl.inject_into_urllib3` from your Python code
before you begin making HTTP requests. This can be done in a ``sitecustomize``
module, or at any other time before your application begins using ``urllib3``,
like this:

.. code-block:: python

    try:
        import urllib3.contrib.pyopenssl
        urllib3.contrib.pyopenssl.inject_into_urllib3()
    except ImportError:
        pass

.. _pyopenssl: https://www.pyopenssl.org
.. _cryptography: https://cryptography.io
.. _idna: https://github.com/kjd/idna | , __future__, cryptography, idna, io, logging, OpenSSL, socket, ssl, typing, urllib3 |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/contrib/socks.py` | ❓ UNKNOWN | 2025-11-09 19:11 | This module contains provisional support for SOCKS proxies from within
urllib3. This module supports SOCKS4, SOCKS4A (an extension of SOCKS4), and
SOCKS5. To enable its functionality, either install PySocks or install this
module with the ``socks`` extra.

The SOCKS implementation supports the full range of urllib3 features. It also
supports the following SOCKS features:

- SOCKS4A (``proxy_url='socks4a://...``)
- SOCKS4 (``proxy_url='socks4://...``)
- SOCKS5 with remote DNS (``proxy_url='socks5h://...``)
- SOCKS5 with local DNS (``proxy_url='socks5://...``)
- Usernames and passwords for the SOCKS proxy

.. note::
   It is recommended to use ``socks5h://`` or ``socks4a://`` schemes in
   your ``proxy_url`` to ensure that DNS resolution is done from the remote
   server instead of client-side when connecting to a domain name.

SOCKS4 supports IPv4 and domain names with the SOCKS4A extension. SOCKS5
supports IPv4, IPv6, and domain names.

When connecting to a SOCKS4 proxy the ``username`` portion of the ``proxy_url``
will be sent as the ``userid`` section of the SOCKS request:

.. code-block:: python

    proxy_url="socks4a://<userid>@proxy-host"

When connecting to a SOCKS5 proxy the ``username`` and ``password`` portion
of the ``proxy_url`` will be sent as the username/password to authenticate
with the proxy:

.. code-block:: python

    proxy_url="socks5h://<username>:<password>@proxy-host" | , __future__, socket, socks, ssl, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/exceptions.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Base exception used by this module."""


class HTTPWarning(Warning): | , __future__, email, http, socket, typing, warnings | L306: # TODO(t-8ch): Stop inheriting from AssertionError in v2.0. |
| `blackboard-agent/venv/Lib/site-packages/urllib3/fields.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Guess the "Content-Type" of a file.

    :param filename:
        The filename to guess the "Content-Type" of using :mod:`mimetypes`.
    :param default:
        If no "Content-Type" can be guessed, default to `default`. | __future__, email, mimetypes, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/filepost.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Our embarrassingly-simple replacement for mimetools.choose_boundary. | , __future__, binascii, codecs, io, os, typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/http2/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , __future__, importlib, typing | L38: # TODO: Offer 'http/1.1' as well, but for testing purposes this is handy. |
| `blackboard-agent/venv/Lib/site-packages/urllib3/http2/connection.py` | ❓ UNKNOWN | 2025-11-09 19:11 | "An implementation that validates fields according to the definitions in Sections
    5.1 and 5.5 of [HTTP] only needs an additional check that field names do not
    include uppercase characters." (https://httpwg.org/specs/rfc9113.html#n-field-validity)

    `http.client._is_legal_header_name` does not validate the field name according to the
    HTTP 1.1 spec, so we do that here, in addition to checking for uppercase characters.

    This does not allow for the `:` character in the header name, so should not
    be used to validate pseudo-headers. | , __future__, h2, logging, re, threading, types, typing | L144: # TODO SKIPPABLE_HEADERS from urllib3 are ignored.
L234: # TODO: Arbitrary read value.
L282: # TODO this is often present from upstream.
L325: # TODO: This is a woefully incomplete response object, but works for non-streaming.
L332: decode_content: bool = False,  # TODO: support decoding |
| `blackboard-agent/venv/Lib/site-packages/urllib3/http2/probe.py` | ❓ UNKNOWN | 2025-11-09 19:11 | This function is for testing purposes only. Gets the current state of the probe cache"""
        with self._lock:
            return {k: v for k, v in self._cache_values.items()}

    def _reset(self) -> None: | __future__, threading |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/poolmanager.py` | ❓ UNKNOWN | 2025-11-09 19:11 | All known keyword arguments that could be provided to the pool manager, its
    pools, or the underlying connections.

    All custom key schemes should include the fields in this key at a minimum. | , __future__, functools, logging, ssl, types, typing, typing_extensions, urllib, urllib3, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/response.py` | ❓ UNKNOWN | 2025-11-09 19:11 | From RFC7231:
        If one or more encodings have been applied to a representation, the
        sender that applied the encodings MUST generate a Content-Encoding
        header field that lists the content codings in the order in which
        they were applied. | , __future__, brotli, brotlicffi, collections, compression, contextlib, http, io, json, logging, re, socket, sys, typing, warnings, zlib, zstandard |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | , __future__ |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/connection.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Returns True if the connection is dropped and should be closed.
    :param conn: :class:`urllib3.connection.HTTPConnection` object. | , __future__, socket, typing | L124: # https://bugs.python.org/issue658327 |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/proxy.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Returns True if the connection requires an HTTP CONNECT through the proxy.

    :param URL proxy_url:
        URL of the proxy.
    :param ProxyConfig proxy_config:
        Proxy configuration from poolmanager.py
    :param str destination_scheme:
        The scheme of the destination. (i.e https, http, etc) | , __future__, typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/request.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Shortcuts for generating request headers.

    :param keep_alive:
        If ``True``, adds 'connection: keep-alive' header.

    :param accept_encoding:
        Can be a boolean, list, or string.
        ``True`` translates to 'gzip,deflate'.  If the dependencies for
        Brotli (either the ``brotli`` or ``brotlicffi`` package) and/or Zstandard
        (the ``zstandard`` package) algorithms are installed, then their encodings are
        included in the string ('br' and 'zstd', respectively).
        List will get joined by comma.
        String will be used as provided.

    :param user_agent:
        String representing the user-agent you want, such as
        "python-urllib3/0.6"

    :param basic_auth:
        Colon-separated username:password string for 'authorization: basic ...'
        auth header.

    :param proxy_basic_auth:
        Colon-separated username:password string for 'proxy-authorization: basic ...'
        auth header.

    :param disable_cache:
        If ``True``, adds 'cache-control: no-cache' header.

    Example:

    .. code-block:: python

        import urllib3

        print(urllib3.util.make_headers(keep_alive=True, user_agent="Batman/1.0"))
        # {'connection': 'keep-alive', 'user-agent': 'Batman/1.0'}
        print(urllib3.util.make_headers(accept_encoding=True))
        # {'accept-encoding': 'gzip,deflate'} | , __future__, base64, brotli, brotlicffi, compression, enum, io, typing, urllib3, zstandard | L229: # File-like object, TODO: use seek() and tell() for length? |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/response.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Checks whether a given file-like object is closed.

    :param obj:
        The file-like object to check. | , __future__, email, http | L54: # To make debugging easier add an explicit check.
L99: # FIXME: Can we do this somehow without accessing private httplib _method? |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/retry.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Retry configuration.

    Each retry attempt will create a new Retry object with updated values, so
    they can be safely reused.

    Retries can be defined as a default for a pool:

    .. code-block:: python

        retries = Retry(connect=5, read=2, redirect=5)
        http = PoolManager(retries=retries)
        response = http.request("GET", "https://example.com/")

    Or per-request (which overrides the default for the pool):

    .. code-block:: python

        response = http.request("GET", "https://example.com/", retries=Retry(10))

    Retries can be disabled by passing ``False``:

    .. code-block:: python

        response = http.request("GET", "https://example.com/", retries=False)

    Errors will be wrapped in :class:`~urllib3.exceptions.MaxRetryError` unless
    retries are disabled, in which case the causing exception will be raised.

    :param int total:
        Total number of retries to allow. Takes precedence over other counts.

        Set to ``None`` to remove this constraint and fall back on other
        counts.

        Set to ``0`` to fail on the first retry.

        Set to ``False`` to disable and imply ``raise_on_redirect=False``.

    :param int connect:
        How many connection-related errors to retry on.

        These are errors raised before the request is sent to the remote server,
        which we assume has not triggered the server to process the request.

        Set to ``0`` to fail on the first retry of this type.

    :param int read:
        How many times to retry on read errors.

        These errors are raised after the request was sent to the server, so the
        request may have side-effects.

        Set to ``0`` to fail on the first retry of this type.

    :param int redirect:
        How many redirects to perform. Limit this to avoid infinite redirect
        loops.

        A redirect is a HTTP response with a status code 301, 302, 303, 307 or
        308.

        Set to ``0`` to fail on the first retry of this type.

        Set to ``False`` to disable and imply ``raise_on_redirect=False``.

    :param int status:
        How many times to retry on bad status codes.

        These are retries made on responses, where status code matches
        ``status_forcelist``.

        Set to ``0`` to fail on the first retry of this type.

    :param int other:
        How many times to retry on other errors.

        Other errors are errors that are not connect, read, redirect or status errors.
        These errors might be raised after the request was sent to the server, so the
        request might have side-effects.

        Set to ``0`` to fail on the first retry of this type.

        If ``total`` is not set, it's a good idea to set this to 0 to account
        for unexpected edge cases and avoid infinite retry loops.

    :param Collection allowed_methods:
        Set of uppercased HTTP method verbs that we should retry on.

        By default, we only retry on methods which are considered to be
        idempotent (multiple requests with the same parameters end with the
        same state). See :attr:`Retry.DEFAULT_ALLOWED_METHODS`.

        Set to a ``None`` value to retry on any verb.

    :param Collection status_forcelist:
        A set of integer HTTP status codes that we should force a retry on.
        A retry is initiated if the request method is in ``allowed_methods``
        and the response status code is in ``status_forcelist``.

        By default, this is disabled with ``None``.

    :param float backoff_factor:
        A backoff factor to apply between attempts after the second try
        (most errors are resolved immediately by a second try without a
        delay). urllib3 will sleep for::

            {backoff factor} * (2 ** ({number of previous retries}))

        seconds. If `backoff_jitter` is non-zero, this sleep is extended by::

            random.uniform(0, {backoff jitter})

        seconds. For example, if the backoff_factor is 0.1, then :func:`Retry.sleep` will
        sleep for [0.0s, 0.2s, 0.4s, 0.8s, ...] between retries. No backoff will ever
        be longer than `backoff_max`.

        By default, backoff is disabled (factor set to 0).

    :param bool raise_on_redirect: Whether, if the number of redirects is
        exhausted, to raise a MaxRetryError, or to return a response with a
        response code in the 3xx range.

    :param bool raise_on_status: Similar meaning to ``raise_on_redirect``:
        whether we should raise an exception, or return a response,
        if status falls in ``status_forcelist`` range and retries have
        been exhausted.

    :param tuple history: The history of the request encountered during
        each call to :meth:`~Retry.increment`. The list is in the order
        the requests occurred. Each list item is of class :class:`RequestHistory`.

    :param bool respect_retry_after_header:
        Whether to respect Retry-After header on status codes defined as
        :attr:`Retry.RETRY_AFTER_STATUS_CODES` or not.

    :param Collection remove_headers_on_redirect:
        Sequence of headers to remove from the request when a response
        indicating a redirect is returned before firing off the redirected
        request. | , __future__, email, itertools, logging, random, re, time, types, typing, typing_extensions | L286: log.debug("Converted retries value: %r -> %r", retries, new_retries) |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/ssl_.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Return True for CPython 3.9.3+ or 3.10+ and PyPy 7.3.8+ where
    setting SSLContext.hostname_checks_common_name to False works.

    Outside of CPython and PyPy we don't know which implementations work
    or not so we conservatively use our hostname matching as we know that works
    on all implementations.

    https://github.com/urllib3/urllib3/issues/2192#issuecomment-821832963
    https://foss.heptapod.net/pypy/pypy/-/issues/3539 | , __future__, binascii, hashlib, hmac, os, socket, ssl, sys, typing, warnings |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/ssl_match_hostname.py` | ❓ UNKNOWN | 2025-11-09 19:11 | The match_hostname() function from Python 3.5, essential when using SSL."""

# Note: This file is under the PSF license as the code comes from the python
# stdlib.   http://docs.python.org/3/license.html
# It is modified to remove commonName support.

from __future__ import annotations

import ipaddress
import re
import typing
from ipaddress import IPv4Address, IPv6Address

if typing.TYPE_CHECKING:
    from .ssl_ import _TYPE_PEER_CERT_RET_DICT

__version__ = "3.5.0.1"


class CertificateError(ValueError):
    pass


def _dnsname_match(
    dn: typing.Any, hostname: str, max_wildcards: int = 1
) -> typing.Match[str] \\| None \\| bool: | , __future__, ipaddress, re, typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/ssltransport.py` | ❓ UNKNOWN | 2025-11-09 19:11 | The SSLTransport wraps an existing socket and establishes an SSL connection.

    Contrary to Python's implementation of SSLSocket, it allows you to chain
    multiple TLS connections together. It's particularly useful if you need to
    implement TLS within TLS.

    The class supports most of the socket API operations. | , __future__, io, socket, ssl, typing, typing_extensions |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/timeout.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Timeout configuration.

    Timeouts can be defined as a default for a pool:

    .. code-block:: python

        import urllib3

        timeout = urllib3.util.Timeout(connect=2.0, read=7.0)

        http = urllib3.PoolManager(timeout=timeout)

        resp = http.request("GET", "https://example.com/")

        print(resp.status)

    Or per-request (which overrides the default for the pool):

    .. code-block:: python

       response = http.request("GET", "https://example.com/", timeout=Timeout(10))

    Timeouts can be disabled by setting all the parameters to ``None``:

    .. code-block:: python

       no_timeout = Timeout(connect=None, read=None)
       response = http.request("GET", "https://example.com/", timeout=no_timeout)


    :param total:
        This combines the connect and read timeouts into one; the read timeout
        will be set to the time leftover from the connect attempt. In the
        event that both a connect timeout and a total are specified, or a read
        timeout and a total are specified, the shorter timeout will be applied.

        Defaults to None.

    :type total: int, float, or None

    :param connect:
        The maximum amount of time (in seconds) to wait for a connection
        attempt to a server to succeed. Omitting the parameter will default the
        connect timeout to the system default, probably `the global default
        timeout in socket.py
        <http://hg.python.org/cpython/file/603b4d593758/Lib/socket.py#l535>`_.
        None will set an infinite timeout for connection attempts.

    :type connect: int, float, or None

    :param read:
        The maximum amount of time (in seconds) to wait between consecutive
        read operations for a response from the server. Omitting the parameter
        will default the read timeout to the system default, probably `the
        global default timeout in socket.py
        <http://hg.python.org/cpython/file/603b4d593758/Lib/socket.py#l535>`_.
        None will set an infinite timeout.

    :type read: int, float, or None

    .. note::

        Many factors can affect the total amount of time for urllib3 to return
        an HTTP response.

        For example, Python's DNS resolver does not obey the timeout specified
        on the socket. Other factors that can affect total request time include
        high CPU load, high swap, the program running at a low priority level,
        or other behaviors.

        In addition, the read and total timeouts only measure the time between
        read operations on the socket connecting the client and the server,
        not the total amount of time for the request to return a complete
        response. For most requests, the timeout is raised because the server
        has not sent the first byte in the specified time. This is not always
        the case; if a server streams one byte every fifteen seconds, a timeout
        of 20 seconds will not trigger, even though the request will take
        several minutes to complete. | , __future__, enum, socket, time, typing, urllib3 |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/url.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Data structure for representing an HTTP URL. Used as a return value for
    :func:`parse_url`. Both the scheme and host are normalized as they are
    both case-insensitive according to RFC 3986. | , __future__, re, typing, urllib3 | L454: # TODO: Remove this when we break backwards compatibility. |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/util.py` | ❓ UNKNOWN | 2025-11-09 19:11 |  | __future__, types, typing |  |
| `blackboard-agent/venv/Lib/site-packages/urllib3/util/wait.py` | ❓ UNKNOWN | 2025-11-09 19:11 | Waits for reading to be available on a given socket.
    Returns True if the socket is readable, or False if the timeout expired. | __future__, functools, select, socket |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/chrome.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, typing, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/archive.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Class for extract files in linux with right permissions"""

    def extract(self, member, path=None, pwd=None):
        if not isinstance(member, zipfile.ZipInfo):
            member = self.getinfo(member)

        if path is None:
            path = os.getcwd()

        ret_val = self._extract_member(member, path, pwd)  # noqa
        attr = member.external_attr >> 16
        os.chmod(ret_val, attr)
        return ret_val


class Archive(object):
    def __init__(self, path: str):
        self.file_path = path | os, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/config.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | dotenv, os |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/constants.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, sys |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/download_manager.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | abc, os, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/driver.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Downloads version from parameter if version not None or "latest".
        Downloads latest, if version is "latest" or browser could not been determined.
        Downloads determined browser version driver in all other ways as a bonus fallback for lazy users. | webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/driver_cache.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Find driver by '{os_type}_{driver_name}_{driver_version}_{browser_version}'."""
        os_type = self.get_os_type()
        driver_name = driver.get_name()
        browser_type = driver.get_browser_type()
        browser_version = self._os_system_manager.get_browser_version_from_os(browser_type)
        if not browser_version:
            return None

        driver_version = self.get_cache_key_driver_version(driver)
        metadata = self.load_metadata_content()

        key = self.__get_metadata_key(driver)
        if key not in metadata:
            log(f'There is no [{os_type}] {driver_name} "{driver_version}" for browser {browser_type} '
                f'"{browser_version}" in cache')
            return None

        driver_info = metadata[key]
        path = driver_info["binary_path"]
        if not os.path.exists(path):
            return None

        if not self.__is_valid(driver_info):
            return None

        path = driver_info["binary_path"]
        log(f"Driver [{path}] found in cache")
        return path

    def __is_valid(self, driver_info):
        dates_diff = get_date_diff(
            driver_info["timestamp"], datetime.date.today(), self._date_format
        )
        return dates_diff < self._cache_valid_days_range

    def load_metadata_content(self):
        if os.path.exists(self._drivers_json_path):
            with open(self._drivers_json_path, "r") as outfile:
                return json.load(outfile)
        return {}

    def __get_metadata_key(self, driver: Driver):
        if self._metadata_key:
            return self._metadata_key

        driver_version = self.get_cache_key_driver_version(driver)
        browser_version = driver.get_browser_version_from_os()
        browser_version = browser_version if browser_version else ""
        self._metadata_key = f"{self.get_os_type()}_{driver.get_name()}_{driver_version}" \
                             f"_for_{browser_version}"
        return self._metadata_key

    def get_cache_key_driver_version(self, driver: Driver):
        if self._cache_key_driver_version:
            return self._cache_key_driver_version
        return driver.get_driver_version_to_download()

    def __get_path(self, driver: Driver):
        if self._driver_binary_path is None:
            self._driver_binary_path = os.path.join(
                self._drivers_directory,
                driver.get_name(),
                self.get_os_type(),
                driver.get_driver_version_to_download(),
            )
        return self._driver_binary_path | datetime, json, os, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/file_manager.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, re, tarfile, webdriver_manager, zipfile |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/http.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | requests, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/logger.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Emitting the log message."""
    __logger.log(wdm_log_level(), text)


def set_logger(logger): | logging, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/manager.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/os_manager.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Return installed browser version."""
        cmd_mapping = {
            ChromeType.GOOGLE: {
                OSType.LINUX: linux_browser_apps_to_cmd(
                    "google-chrome",
                    "google-chrome-stable",
                    "google-chrome-beta",
                    "google-chrome-dev",
                ),
                OSType.MAC: r"/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version",
                OSType.WIN: windows_browser_apps_to_cmd(
                    r'(Get-Item -Path "$env:PROGRAMFILES\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Google\Chrome\BLBeacon").version',
                    r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Google Chrome").version',
                ),
            },
            ChromeType.CHROMIUM: {
                OSType.LINUX: linux_browser_apps_to_cmd("chromium", "chromium-browser"),
                OSType.MAC: r"/Applications/Chromium.app/Contents/MacOS/Chromium --version",
                OSType.WIN: windows_browser_apps_to_cmd(
                    r'(Get-Item -Path "$env:PROGRAMFILES\Chromium\Application\chrome.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Chromium\Application\chrome.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:LOCALAPPDATA\Chromium\Application\chrome.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Chromium\BLBeacon").version',
                    r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Chromium").version',
                ),
            },
            ChromeType.BRAVE: {
                OSType.LINUX: linux_browser_apps_to_cmd(
                    "brave-browser", "brave-browser-beta", "brave-browser-nightly"
                ),
                OSType.MAC: r"/Applications/Brave\ Browser.app/Contents/MacOS/Brave\ Browser --version",
                OSType.WIN: windows_browser_apps_to_cmd(
                    r'(Get-Item -Path "$env:PROGRAMFILES\BraveSoftware\Brave-Browser\Application\brave.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\BraveSoftware\Brave-Browser\Application\brave.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:LOCALAPPDATA\BraveSoftware\Brave-Browser\Application\brave.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\BraveSoftware\Brave-Browser\BLBeacon").version',
                    r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\BraveSoftware Brave-Browser").version',
                ),
            },
            ChromeType.MSEDGE: {
                OSType.LINUX: linux_browser_apps_to_cmd(
                    "microsoft-edge",
                    "microsoft-edge-stable",
                    "microsoft-edge-beta",
                    "microsoft-edge-dev",
                ),
                OSType.MAC: r"/Applications/Microsoft\ Edge.app/Contents/MacOS/Microsoft\ Edge --version",
                OSType.WIN: windows_browser_apps_to_cmd(
                    # stable edge
                    r'(Get-Item -Path "$env:PROGRAMFILES\Microsoft\Edge\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Microsoft\Edge\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge\BLBeacon").version',
                    r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Microsoft\EdgeUpdate\Clients\{56EB18F8-8008-4CBD-B6D2-8C97FE7E9062}").pv',
                    # beta edge
                    r'(Get-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge Beta\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES\Microsoft\Edge Beta\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Microsoft\Edge Beta\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge Beta\BLBeacon").version',
                    # dev edge
                    r'(Get-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge Dev\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES\Microsoft\Edge Dev\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Microsoft\Edge Dev\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge Dev\BLBeacon").version',
                    # canary edge
                    r'(Get-Item -Path "$env:LOCALAPPDATA\Microsoft\Edge SxS\Application\msedge.exe").VersionInfo.FileVersion',
                    r'(Get-ItemProperty -Path Registry::"HKCU\SOFTWARE\Microsoft\Edge SxS\BLBeacon").version',
                    # highest edge
                    r"(Get-Item (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe').'(Default)').VersionInfo.ProductVersion",
                    r"[System.Diagnostics.FileVersionInfo]::GetVersionInfo((Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\msedge.exe').'(Default)').ProductVersion",
                    r"Get-AppxPackage -Name *MicrosoftEdge.* \\| Foreach Version",
                    r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Wow6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Microsoft Edge").version',
                ),
            },
            "firefox": {
                OSType.LINUX: linux_browser_apps_to_cmd("firefox"),
                OSType.MAC: r"/Applications/Firefox.app/Contents/MacOS/firefox --version",
                OSType.WIN: windows_browser_apps_to_cmd(
                    r'(Get-Item -Path "$env:PROGRAMFILES\Mozilla Firefox\firefox.exe").VersionInfo.FileVersion',
                    r'(Get-Item -Path "$env:PROGRAMFILES (x86)\Mozilla Firefox\firefox.exe").VersionInfo.FileVersion',
                    r"(Get-Item (Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\firefox.exe').'(Default)').VersionInfo.ProductVersion",
                    r'(Get-ItemProperty -Path Registry::"HKLM\SOFTWARE\Mozilla\Mozilla Firefox").CurrentVersion',
                ),
            },
        }

        try:
            cmd_mapping = cmd_mapping[browser_type][OperationSystemManager.get_os_name()]
            pattern = PATTERN[browser_type]
            version = read_version_from_cmd(cmd_mapping, pattern)
            return version
        except Exception:
            return None
            # raise Exception("Can not get browser version from OS") | platform, sys, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/core/utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Create 'browser --version' command from browser app names.

    Result command example:
        chromium --version \\|\\| chromium-browser --version | datetime, os, re, subprocess |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/drivers/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/drivers/chrome.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | json, packaging, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/drivers/edge.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Stable driver version when browser version was not determined."""
        stable_url = self._latest_release_url.replace("LATEST_RELEASE", "LATEST_STABLE")
        resp = self._http_client.get(url=stable_url)
        return resp.text.rstrip()

    def get_latest_release_version(self) -> str:
        determined_browser_version = self.get_browser_version_from_os()
        log(f"Get LATEST {self._name} version for Edge {determined_browser_version}")

        edge_driver_version_to_download = (
            self.get_stable_release_version()
            if (determined_browser_version is None)
            else determined_browser_version
        )
        major_edge_version = edge_driver_version_to_download.split(".")[0]
        os_type = self._os_system_manager.get_os_type()
        latest_release_url = {
            OSType.WIN
            in os_type: f"{self._latest_release_url}_{major_edge_version}_WINDOWS",
            OSType.MAC
            in os_type: f"{self._latest_release_url}_{major_edge_version}_MACOS",
            OSType.LINUX
            in os_type: f"{self._latest_release_url}_{major_edge_version}_LINUX",
        }[True]
        resp = self._http_client.get(url=latest_release_url)
        return resp.text.rstrip()

    def get_browser_type(self):
        return ChromeType.MSEDGE | webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/drivers/firefox.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Like https://github.com/mozilla/geckodriver/releases/download/v0.11.1/geckodriver-v0.11.1-linux64.tar.gz"""
        driver_version_to_download = self.get_driver_version_to_download()
        log(f"Getting latest mozilla release info for {driver_version_to_download}")
        resp = self._http_client.get(
            url=self.tagged_release_url(driver_version_to_download),
            headers=self.auth_header
        )
        assets = resp.json()["assets"]
        name = f"{self.get_name()}-{driver_version_to_download}-{os_type}."
        output_dict = [
            asset for asset in assets if asset["name"].startswith(name)]
        return output_dict[0]["browser_download_url"]

    @property
    def latest_release_url(self):
        return self._latest_release_url

    def tagged_release_url(self, version):
        return self._mozila_release_tag.format(version)

    def get_browser_type(self):
        return "firefox" | webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/drivers/ie.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Like https://github.com/seleniumhq/selenium/releases/download/3.141.59/IEDriverServer_Win32_3.141.59.zip"""
        driver_version_to_download = self.get_driver_version_to_download()
        log(f"Getting latest ie release info for {driver_version_to_download}")
        resp = self._http_client.get(
            url=self.tagged_release_url(driver_version_to_download),
            headers=self.auth_header
        )

        assets = resp.json()["assets"]

        name = f"{self._name}_{os_type}_{driver_version_to_download}" + "."
        output_dict = [
            asset for asset in assets if asset["name"].startswith(name)]
        return output_dict[0]["browser_download_url"]

    @property
    def latest_release_url(self):
        return self._latest_release_url

    def tagged_release_url(self, version):
        version = self.__get_divided_version(version)
        return self._ie_release_tag.format(version)

    def __get_divided_version(self, version):
        divided_version = version.split(".")
        if len(divided_version) == 2:
            return f"{version}.0"
        elif len(divided_version) == 3:
            return version
        else:
            raise ValueError(
                "Version must consist of major, minor and/or patch, "
                "but given was: '{version}'".format(version=version)
            )

    def get_browser_type(self):
        return "msie" | webdriver_manager | L26: # todo: for 'browser_version' implement installed IE version detection |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/drivers/opera.py` | ❓ UNKNOWN | 2025-11-09 21:21 | Like https://github.com/operasoftware/operachromiumdriver/releases/download/v.2.45/operadriver_linux64.zip"""
        driver_version_to_download = self.get_driver_version_to_download()
        log(f"Getting latest opera release info for {driver_version_to_download}")
        resp = self._http_client.get(
            url=self.tagged_release_url(driver_version_to_download),
            headers=self.auth_header
        )
        assets = resp.json()["assets"]
        name = "{0}_{1}".format(self.get_name(), os_type)
        output_dict = [
            asset for asset in assets if asset["name"].startswith(name)]
        return output_dict[0]["browser_download_url"]

    @property
    def latest_release_url(self):
        return self._latest_release_url

    def tagged_release_url(self, version):
        return self.opera_release_tag.format(version)

    def get_browser_type(self):
        return "opera" | webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/firefox.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, typing, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/microsoft.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, typing, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/webdriver_manager/opera.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | os, typing, webdriver_manager |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | __init__.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. |  |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_abnf.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _abnf.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , array, os, struct, sys, threading, typing, wsaccel |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_app.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _app.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , inspect, socket, threading, time, typing | L248: _logging.debug("Sending ping")
L251: _logging.debug(f"Failed to send ping: {e}") |
| `blackboard-agent/venv/Lib/site-packages/websocket/_cookiejar.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _cookiejar.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | http, typing |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_core.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _core.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , socket, struct, threading, time, typing | L16: from ._logging import debug, error, trace, isEnabledForError, isEnabledForTrace |
| `blackboard-agent/venv/Lib/site-packages/websocket/_dispatcher.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _dispatcher.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , inspect, selectors, socket, time, typing |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_exceptions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _exceptions.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. |  |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_handshake.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _handshake.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , base64, hashlib, hmac, http, os |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_http.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _http.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , base64, errno, os, python_socks, socket | L30: from ._logging import debug, dump, trace
L129: # TODO: Use python-socks for http protocol also, to standardize flow
L351: debug("Connecting proxy...")
L355: # TODO: support digest auth. |
| `blackboard-agent/venv/Lib/site-packages/websocket/_logging.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _logging.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | logging | L41: "debug",
L44: "isEnabledForDebug",
L52: level: str = "DEBUG",
L71: _logger.debug(f"--- {title} ---")
L72: _logger.debug(message)
L73: _logger.debug("-----------------------")
L84: def debug(msg: str) -> None:
L85: _logger.debug(msg)
L94: _logger.debug(msg)
L101: def isEnabledForDebug() -> bool:
L102: return _logger.isEnabledFor(logging.DEBUG) |
| `blackboard-agent/venv/Lib/site-packages/websocket/_socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _socket.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , errno, selectors, socket, typing |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_ssl_compat.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _ssl_compat.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | ssl, typing |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_url.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _url.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | , ipaddress, os, typing, urllib |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _utils.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | typing, wsaccel |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/_wsdump.py` | ❓ UNKNOWN | 2025-11-09 21:21 | _wsdump.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | argparse, code, gzip, readline, ssl, sys, threading, time, urllib, websocket, zlib |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  |  |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/echo-server.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | asyncio, os, websockets |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_abnf.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_abnf.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_app.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_app.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | os, ssl, threading, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_cookiejar.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_cookiejar.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_dispatcher.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_dispatcher.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | socket, threading, time, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_handshake_large_response.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_handshake_large_response.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_http.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_http.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | os, python_socks, socket, ssl, unittest, websocket | L288: # TODO: Test SOCKS4 and SOCK5 proxies with unit tests |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_large_payloads.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_large_payloads.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | struct, unittest, websocket | L224: """Test frame buffer with edge cases that could trigger bugs""" |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_socket.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_socket.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | errno, socket, sys, time, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_socket_bugs.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_socket_bugs.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | errno, socket, sys, unittest, websocket | L15: test_socket_bugs.py
L33: class SocketBugsTest(unittest.TestCase):
L34: """Test bugs found in socket handling logic"""
L36: def test_bug_implicit_none_return_from_ssl_want_read_fixed(self):
L38: BUG #5 FIX VERIFICATION: Test SSLWantReadError timeout now raises correct exception
L40: Bug was in _socket.py:100-101 - SSLWantReadError except block returned None implicitly
L58: def test_bug_implicit_none_return_from_socket_error_fixed(self):
L60: BUG #5 FIX VERIFICATION: Test that socket.error with EAGAIN now handles timeout correctly
L62: Bug was in _socket.py:102-105 - socket.error except block returned None implicitly
L85: def test_bug_wrong_exception_for_selector_timeout_fixed(self):
L87: BUG #6 FIX VERIFICATION: Test that selector timeout now raises correct exception type
L89: Bug was in _socket.py:115 returning None for timeout, treated as connection error |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_ssl_compat.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_ssl_compat.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | builtins, sys, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_ssl_edge_cases.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_ssl_edge_cases.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | socket, ssl, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_url.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_url.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | os, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_utils.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_utils.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | builtins, sys, unittest, websocket |  |
| `blackboard-agent/venv/Lib/site-packages/websocket/tests/test_websocket.py` | ❓ UNKNOWN | 2025-11-09 21:21 | test_websocket.py
websocket - WebSocket client library for Python

Copyright 2025 engn33r

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License. | base64, os, socket, ssl, unittest, websocket | L179: # TODO: add longer frame data
L198: # TODO: add longer frame data |
| `blackboard-agent/venv/Lib/site-packages/wsproto/__init__.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto
~~~~~~~

A WebSocket implementation. | , typing |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/connection.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto/connection
~~~~~~~~~~~~~~~~~~

An implementation of a WebSocket connection. | , collections, enum, typing |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/events.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto/events
~~~~~~~~~~~~~~

Events that result from processing data on a WebSocket connection. | , abc, dataclasses, typing |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/extensions.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto/extensions
~~~~~~~~~~~~~~~~~~

WebSocket extensions. | , typing, zlib |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/frame_protocol.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto/frame_protocol
~~~~~~~~~~~~~~~~~~~~~~

WebSocket frame protocol implementation. | , codecs, enum, os, struct, typing |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/handshake.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto/handshake
~~~~~~~~~~~~~~~~~~

An implementation of WebSocket handshakes. | , collections, h11, typing |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/typing.py` | ❓ UNKNOWN | 2025-11-09 21:21 |  | typing |  |
| `blackboard-agent/venv/Lib/site-packages/wsproto/utilities.py` | ❓ UNKNOWN | 2025-11-09 21:21 | wsproto/utilities
~~~~~~~~~~~~~~~~~

Utility functions that do not belong in a separate module. | , base64, h11, hashlib, os, typing | L74: # commas. XX FIXME |
| `blackboard-agent/venv/pyvenv.cfg` | ❓ UNKNOWN | 2025-11-09 19:11 | Configuration file |  |  |
| `blackboard-agent/venv/Scripts/activate.bat` | ❓ UNKNOWN | 2025-11-09 19:11 | Windows startup script | Python, Uvicorn, Virtualenv |  |
| `blackboard-agent/venv/Scripts/deactivate.bat` | ❓ UNKNOWN | 2025-10-07 12:16 | Windows startup script | Python, Uvicorn, Virtualenv |  |
| `card-generator/core/__init__.py` | ❓ UNKNOWN | 2025-11-09 07:53 |  |  |  |
| `card-generator/core/anythingllm_client.py` | ❓ UNKNOWN | 2025-11-09 07:52 | AnythingLLM API Client
Connects to AnythingLLM at localhost:3001 | json, requests, typing |  |
| `card-generator/core/rag_handler.py` | ❓ UNKNOWN | 2025-11-09 07:52 | RAG Handler - Query with Citations
Extracts exact page references from AnythingLLM responses | , re, typing |  |
| `card-generator/drcodept.py` | ❓ UNKNOWN | 2025-11-09 07:53 | DR. CODEPT v0.1 — Your Personal AI Study Partner for PT School

Main CLI Application
Usage: python drcodept.py | core, generators, os, pathlib, sys, time |  |
| `card-generator/generators/__init__.py` | ❓ UNKNOWN | 2025-11-09 07:53 |  |  |  |
| `card-generator/generators/anki_generator.py` | ❓ UNKNOWN | 2025-11-09 07:53 | Anki Deck Generator
Creates .apkg files for spaced repetition with page references | , datetime, json, os, typing |  |
| `card-generator/generators/npte_generator.py` | ❓ UNKNOWN | 2025-11-09 07:52 | NPTE Question Generator
Creates board-style exam questions from textbooks with citations | , json, re, typing |  |
| `card-generator/utils/__init__.py` | ❓ UNKNOWN | 2025-11-09 07:53 |  |  |  |

## Startup and Config Scripts
| Path | Status | Last Modified | Description |
| - | - | - | - |
| `blackboard-agent/config/__init__.py` | ❓ UNKNOWN | 2025-11-09 19:06 | Empty __init__.py for config package |
| `blackboard-agent/config/settings.py` | ❓ UNKNOWN | 2025-11-09 19:06 | Configuration for Agent |
| `blackboard-agent/config/todo_selectors.json` | ❓ UNKNOWN | 2025-11-10 10:43 | Configuration file |
| `fastmcp-server/config/courses.json` | ❓ UNKNOWN | 2025-11-10 11:16 | Configuration file |
