"""
Google Tasks integration helper functions.
"""

from typing import Any, Dict, List, Optional
from googleapiclient.discovery import build
from .google_auth import get_google_creds
import time
import hashlib
import json

class TasksHelper:
    """Helper class for Google Tasks operations using real Google API."""

    def __init__(self, mcp_client=None):
        self.creds = get_google_creds()
        self.service = None
        if self.creds:
            self.service = build('tasks', 'v1', credentials=self.creds)

        # Simple in-memory cache
        self._cache = {}
        self._cache_ttl = 60

    def _check_service(self):
        if not self.service:
            self.creds = get_google_creds()
            if self.creds:
                self.service = build('tasks', 'v1', credentials=self.creds)
        if not self.service:
            raise RuntimeError("Google Tasks service not initialized. Run setup_google_calendar.py")

    def _make_cache_key(self, method: str, **kwargs) -> str:
        """Create cache key from method name and args."""
        payload = {"method": method, **kwargs}
        serialized = json.dumps(payload, sort_keys=True)
        return hashlib.md5(serialized.encode()).hexdigest()

    def _get_cached(self, cache_key: str) -> Optional[Any]:
        """Get cached result if still valid."""
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return result
            del self._cache[cache_key]
        return None

    def _set_cache(self, cache_key: str, result: Any) -> None:
        """Store result in cache with current timestamp."""
        self._cache[cache_key] = (result, time.time())

    async def list_tasks(self, tasklist_id: str = "@default") -> List[Dict[str, Any]]:
        # Check cache first
        cache_key = self._make_cache_key("list_tasks", tasklist_id=tasklist_id)
        cached = self._get_cached(cache_key)
        if cached is not None:
            return cached

        self._check_service()
        results = self.service.tasks().list(tasklist=tasklist_id, showCompleted=False).execute()
        tasks = results.get('items', [])

        # Cache the result
        self._set_cache(cache_key, tasks)
        return tasks

    async def list_all_tasks(self, tasklist_id: str = "@default") -> List[Dict[str, Any]]:
        """Backwards-compatible alias for list_tasks."""
        return await self.list_tasks(tasklist_id=tasklist_id)

    async def create_task(self, title: str, tasklist_id: str = "@default", notes: Optional[str] = None, due: Optional[str] = None) -> Dict[str, Any]:
        self._check_service()
        task = {'title': title, 'notes': notes, 'due': due}
        return self.service.tasks().insert(tasklist=tasklist_id, body=task).execute()

    async def complete_task(self, task_id: str, tasklist_id: str = "@default") -> Dict[str, Any]:
        self._check_service()
        task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        task['status'] = 'completed'
        return self.service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()

    async def update_task(self, task_id: str, title: Optional[str] = None, notes: Optional[str] = None, due: Optional[str] = None, tasklist_id: str = "@default") -> Dict[str, Any]:
        self._check_service()
        task = self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()
        if title: task['title'] = title
        if notes: task['notes'] = notes
        if due: task['due'] = due
        return self.service.tasks().update(tasklist=tasklist_id, task=task_id, body=task).execute()

    async def delete_task(self, task_id: str, tasklist_id: str = "@default") -> Dict[str, Any]:
        self._check_service()
        self.service.tasks().delete(tasklist=tasklist_id, task=task_id).execute()
        return {"success": True}

    async def get_task_details(self, task_id: str, tasklist_id: str = "@default") -> Dict[str, Any]:
        self._check_service()
        return self.service.tasks().get(tasklist=tasklist_id, task=task_id).execute()

    async def search_tasks(self, query: str, tasklist_id: str = "@default") -> List[Dict[str, Any]]:
        self._check_service()
        tasks = await self.list_tasks(tasklist_id)
        q = query.lower()
        return [
            t
            for t in tasks
            if q in (t.get("title") or "").lower()
            or q in (t.get("notes") or "").lower()
        ]
