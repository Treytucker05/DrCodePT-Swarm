"""
Skill Library - Stores and retrieves learned procedures.

Inspired by Voyager's skill library, this stores successful procedures
as executable playbooks indexed by description embeddings for fast retrieval.

When the agent successfully completes a new task, it saves the procedure.
Next time a similar task is requested, it retrieves and executes the saved skill.
"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Paths
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = REPO_ROOT / "agent" / "memory" / "skills"
SKILLS_INDEX_PATH = SKILLS_DIR / "skill_index.json"


class SkillStep(BaseModel):
    """A single step in a skill procedure."""
    action: str  # e.g., "click", "type", "goto", "wait", "screenshot", "api_call"
    target: Optional[str] = None  # selector, URL, or API endpoint
    value: Optional[str] = None  # text to type, data to send
    description: str  # human-readable description
    timeout_ms: int = 15000
    optional: bool = False  # if True, failure doesn't stop the skill


class Skill(BaseModel):
    """A learned procedure that can be executed."""
    id: str = Field(default_factory=lambda: f"skill_{uuid4().hex[:8]}")
    name: str  # Short name like "get_outlook_calendar"
    description: str  # Full description for embedding search
    tags: List[str] = Field(default_factory=list)  # e.g., ["calendar", "outlook", "microsoft"]

    # The procedure
    steps: List[SkillStep] = Field(default_factory=list)

    # Prerequisites
    requires_auth: Optional[str] = None  # e.g., "microsoft", "google"
    requires_tools: List[str] = Field(default_factory=list)  # tool names needed

    # Metadata
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    success_count: int = 0
    failure_count: int = 0
    last_used: Optional[str] = None

    # Learning
    source: str = "learned"  # "learned", "manual", "imported"
    learned_from_task: Optional[str] = None  # original user request
    refinement_notes: List[str] = Field(default_factory=list)


class SkillLibrary:
    """
    Stores and retrieves learned skills using embedding-based search.

    Usage:
        library = SkillLibrary()

        # Search for relevant skills
        skills = library.search("access my outlook calendar", k=3)

        # Save a new skill
        library.save(skill)

        # Record success/failure
        library.record_outcome(skill_id, success=True)
    """

    def __init__(self):
        self._skills: Dict[str, Skill] = {}
        self._embeddings: Dict[str, List[float]] = {}
        self._embedder = None
        self._initialized = False

    def initialize(self) -> None:
        """Load skills and initialize embedder."""
        if self._initialized:
            return

        SKILLS_DIR.mkdir(parents=True, exist_ok=True)

        # Load skill index
        if SKILLS_INDEX_PATH.exists():
            try:
                data = json.loads(SKILLS_INDEX_PATH.read_text(encoding="utf-8"))
                for skill_data in data.get("skills", []):
                    skill = Skill.model_validate(skill_data)
                    self._skills[skill.id] = skill
                self._embeddings = data.get("embeddings", {})
                logger.info(f"Loaded {len(self._skills)} skills from library")
            except Exception as e:
                logger.error(f"Failed to load skill index: {e}")

        # Initialize embedder
        self._init_embedder()
        self._initialized = True

    def _init_embedder(self) -> None:
        """Initialize the embedding model."""
        try:
            from sentence_transformers import SentenceTransformer
            self._embedder = SentenceTransformer("all-MiniLM-L6-v2")
            logger.info("Initialized sentence-transformers embedder")
        except ImportError:
            logger.warning("sentence-transformers not available, using hash-based fallback")
            self._embedder = None

    def _embed(self, text: str) -> List[float]:
        """Get embedding vector for text."""
        if self._embedder is not None:
            return self._embedder.encode(text).tolist()
        else:
            # Hash-based fallback
            import hashlib
            h = hashlib.sha256(text.lower().encode()).hexdigest()
            return [int(h[i:i+2], 16) / 255.0 for i in range(0, 64, 2)]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _save_index(self) -> None:
        """Persist the skill index to disk."""
        data = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "skills": [s.model_dump() for s in self._skills.values()],
            "embeddings": self._embeddings,
        }
        SKILLS_INDEX_PATH.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )

    def search(self, query: str, k: int = 5, min_similarity: float = 0.3) -> List[Tuple[Skill, float]]:
        """
        Search for skills similar to the query.

        Returns list of (skill, similarity_score) tuples, sorted by relevance.
        """
        if not self._initialized:
            self.initialize()

        if not self._skills:
            return []

        query_embedding = self._embed(query)

        scored = []
        for skill_id, skill in self._skills.items():
            # Get or compute embedding
            if skill_id not in self._embeddings:
                skill_text = f"{skill.name} {skill.description} {' '.join(skill.tags)}"
                self._embeddings[skill_id] = self._embed(skill_text)

            similarity = self._cosine_similarity(query_embedding, self._embeddings[skill_id])

            # Boost by success rate
            if skill.success_count + skill.failure_count > 0:
                success_rate = skill.success_count / (skill.success_count + skill.failure_count)
                similarity *= (0.8 + 0.2 * success_rate)  # Up to 20% boost

            if similarity >= min_similarity:
                scored.append((skill, similarity))

        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def get(self, skill_id: str) -> Optional[Skill]:
        """Get a skill by ID."""
        if not self._initialized:
            self.initialize()
        return self._skills.get(skill_id)

    def save(self, skill: Skill) -> str:
        """Save a skill to the library."""
        if not self._initialized:
            self.initialize()

        skill.updated_at = datetime.now(timezone.utc).isoformat()
        self._skills[skill.id] = skill

        # Compute embedding
        skill_text = f"{skill.name} {skill.description} {' '.join(skill.tags)}"
        self._embeddings[skill.id] = self._embed(skill_text)

        self._save_index()
        logger.info(f"Saved skill: {skill.name} ({skill.id})")
        return skill.id

    def record_outcome(self, skill_id: str, success: bool, notes: Optional[str] = None) -> None:
        """Record the outcome of executing a skill."""
        if not self._initialized:
            self.initialize()

        skill = self._skills.get(skill_id)
        if not skill:
            return

        if success:
            skill.success_count += 1
        else:
            skill.failure_count += 1
            if notes:
                skill.refinement_notes.append(f"[{datetime.now().isoformat()}] {notes}")

        skill.last_used = datetime.now(timezone.utc).isoformat()
        skill.updated_at = skill.last_used
        self._save_index()

    def delete(self, skill_id: str) -> bool:
        """Delete a skill from the library."""
        if not self._initialized:
            self.initialize()

        if skill_id in self._skills:
            del self._skills[skill_id]
            if skill_id in self._embeddings:
                del self._embeddings[skill_id]
            self._save_index()
            return True
        return False

    def list_skills(self, tag: Optional[str] = None) -> List[Skill]:
        """List all skills, optionally filtered by tag."""
        if not self._initialized:
            self.initialize()

        if tag:
            return [s for s in self._skills.values() if tag in s.tags]
        return list(self._skills.values())

    def create_skill_from_steps(
        self,
        name: str,
        description: str,
        steps: List[Dict[str, Any]],
        tags: List[str] = None,
        requires_auth: Optional[str] = None,
        learned_from_task: Optional[str] = None,
    ) -> Skill:
        """Create a new skill from a list of step dictionaries."""
        skill_steps = []
        for step in steps:
            skill_steps.append(SkillStep(
                action=step.get("action", "unknown"),
                target=step.get("target") or step.get("selector") or step.get("url"),
                value=step.get("value") or step.get("text"),
                description=step.get("description", ""),
                timeout_ms=step.get("timeout_ms", 15000),
                optional=step.get("optional", False),
            ))

        skill = Skill(
            name=name,
            description=description,
            tags=tags or [],
            steps=skill_steps,
            requires_auth=requires_auth,
            source="learned",
            learned_from_task=learned_from_task,
        )

        return skill


# Singleton instance
_library: Optional[SkillLibrary] = None


def get_skill_library() -> SkillLibrary:
    """Get the singleton skill library instance."""
    global _library
    if _library is None:
        _library = SkillLibrary()
    return _library


__all__ = [
    "Skill",
    "SkillStep",
    "SkillLibrary",
    "get_skill_library",
]
