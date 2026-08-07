"""
PANDORA Learning Service - Prerequisite Checker
Knowledge Graph Integration for Learning Prerequisites
"""
import uuid
from typing import Any

from src.graph.neo4j_client import Neo4jClient, get_neo4j_client
from src.core.logging import get_logger

logger = get_logger(__name__)


class PrerequisiteChecker:
    """
    Checks learning prerequisites using the knowledge graph.
    
    Uses Neo4j to track concept relationships and determine
    if a user is ready to progress to new content.
    """

    def __init__(self, neo4j: Neo4jClient | None = None):
        """Initialize with optional Neo4j client."""
        self._neo4j = neo4j

    async def get_neo4j(self) -> Neo4jClient:
        """Get or create Neo4j client."""
        if self._neo4j is None:
            self._neo4j = await get_neo4j_client()
        return self._neo4j

    async def check_prerequisites(
        self,
        user_id: uuid.UUID,
        content_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Check if user has completed prerequisites for content.
        
        Returns:
            {
                "can_access": bool,
                "missing_prerequisites": [...],
                "completed_prerequisites": [...],
                "recommendations": [...]
            }
        """
        neo4j = await self.get_neo4j()

        # Get content prerequisites from graph
        prereqs = await neo4j.get_content_prerequisites(content_id)

        if not prereqs:
            # No prerequisites, content is accessible
            return {
                "can_access": True,
                "missing_prerequisites": [],
                "completed_prerequisites": [],
                "recommendations": [],
            }

        # Check which prerequisites user has completed
        completed = []
        missing = []

        for prereq in prereqs:
            prereq_id = prereq.get("id")
            history = await neo4j.get_user_learning_history(user_id, limit=1000)

            # Check if user completed this prerequisite
            is_completed = any(
                item.get("content_id") == prereq_id and
                item.get("relationship") == "COMPLETED"
                for item in history
            )

            if is_completed:
                completed.append({
                    "content_id": prereq_id,
                    "title": prereq.get("title"),
                })
            else:
                missing.append({
                    "content_id": prereq_id,
                    "title": prereq.get("title"),
                })

        return {
            "can_access": len(missing) == 0,
            "missing_prerequisites": missing,
            "completed_prerequisites": completed,
            "recommendations": [
                {
                    "content_id": m["content_id"],
                    "title": m["title"],
                    "reason": "Complete this prerequisite first",
                }
                for m in missing
            ] if missing else [],
        }

    async def suggest_next_lesson(
        self,
        user_id: uuid.UUID,
        learning_path_id: uuid.UUID,
        current_lesson_id: uuid.UUID | None = None,
    ) -> dict[str, Any] | None:
        """
        Suggest the next lesson for a user based on:
        1. Prerequisites completion
        2. Learning path order
        3. Similar users' paths
        
        Returns next lesson recommendation or None if path is complete.
        """
        neo4j = await self.get_neo4j()

        # Get learning path structure from graph
        path_query = """
        MATCH (lp:LearningPath {id: $path_id})-[:CONTAINS]->(c:Content)
        WHERE NOT (c)-[:PREREQUISITE_OF]->()
        RETURN c.id AS content_id, c.title AS title, c.difficulty AS difficulty
        ORDER BY c.title
        """
        
        try:
            available_content = await neo4j.execute_query(path_query, {
                "path_id": str(learning_path_id),
            })
        except Exception as e:
            logger.warning("neo4j_query_failed", error=str(e))
            return None

        if not available_content:
            return None

        # Get user's completed content
        history = await neo4j.get_user_learning_history(user_id, limit=1000)
        completed_ids = {
            item.get("content_id")
            for item in history
            if item.get("relationship") == "COMPLETED"
        }

        # Find next uncompleted content
        for content in available_content:
            if content.get("content_id") not in completed_ids:
                # Check prerequisites
                prereq_check = await self.check_prerequisites(
                    user_id,
                    uuid.UUID(content["content_id"]),
                )

                if prereq_check["can_access"]:
                    return {
                        "content_id": content["content_id"],
                        "title": content["title"],
                        "difficulty": content.get("difficulty"),
                        "reason": "next_in_sequence",
                    }

        return None

    async def get_learning_sequence(
        self,
        user_id: uuid.UUID,
        content_ids: list[uuid.UUID],
    ) -> list[dict[str, Any]]:
        """
        Get optimized learning sequence for content.
        
        Returns content ordered by prerequisites and user's
        knowledge state.
        """
        neo4j = await self.get_neo4j()

        # Get user's completed content
        history = await neo4j.get_user_learning_history(user_id, limit=1000)
        completed_ids = {
            item.get("content_id")
            for item in history
            if item.get("relationship") == "COMPLETED"
        }

        sequence = []
        remaining = list(content_ids)
        visited = set()

        while remaining and len(sequence) < len(content_ids):
            made_progress = False

            for content_id in list(remaining):
                content_id_str = str(content_id)

                if content_id_str in visited:
                    continue

                # Check prerequisites
                prereqs = await neo4j.get_content_prerequisites(content_id)
                prereq_ids = {str(p.get("id")) for p in prereqs}

                # Can take this content if all prerequisites are completed
                can_take = prereq_ids.issubset(completed_ids | {"", None})

                if can_take:
                    sequence.append({
                        "content_id": content_id_str,
                        "status": "completed" if content_id_str in completed_ids else "available",
                        "order": len(sequence) + 1,
                    })
                    remaining.remove(content_id)
                    visited.add(content_id_str)
                    made_progress = True

            if not made_progress:
                # Circular dependency or unreachable content
                for content_id in remaining:
                    sequence.append({
                        "content_id": str(content_id),
                        "status": "blocked" if str(content_id) not in completed_ids else "completed",
                        "order": len(sequence) + 1,
                        "warning": "prerequisites_unresolved",
                    })
                break

        return sequence

    async def analyze_knowledge_gaps(
        self,
        user_id: uuid.UUID,
        target_content_id: uuid.UUID,
    ) -> dict[str, Any]:
        """
        Analyze knowledge gaps between user and target content.
        
        Identifies what concepts the user needs to learn
        before accessing target content.
        """
        neo4j = await self.get_neo4j()

        # Get concepts taught by target content
        target_query = """
        MATCH (c:Content {id: $content_id})-[:TEACHES]->(concept:Concept)
        RETURN concept.id AS concept_id, concept.name AS name
        """
        
        try:
            target_concepts = await neo4j.execute_query(target_query, {
                "content_id": str(target_content_id),
            })
        except Exception:
            return {
                "target_concepts": [],
                "gaps": [],
                "user_concepts": [],
            }

        # Get user's concept interests (proxy for known concepts)
        user_concepts = await neo4j.get_user_concept_interests(user_id, limit=50)
        user_concept_ids = {c.get("concept_id") for c in user_concepts}

        # Find gaps
        gaps = []
        for concept in target_concepts:
            if concept.get("concept_id") not in user_concept_ids:
                gaps.append({
                    "concept_id": concept.get("concept_id"),
                    "name": concept.get("name"),
                    "priority": "high",  # Could be more sophisticated
                })

        return {
            "target_concepts": [
                {"id": c.get("concept_id"), "name": c.get("name")}
                for c in target_concepts
            ],
            "user_concepts": [
                {"id": c.get("concept_id"), "name": c.get("name"), "weight": c.get("weight")}
                for c in user_concepts[:10]
            ],
            "gaps": gaps,
            "gap_count": len(gaps),
            "readiness_score": max(0, 100 - len(gaps) * 10),
        }

    async def get_related_content(
        self,
        content_id: uuid.UUID,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get content related to the given content."""
        neo4j = await self.get_neo4j()
        return await neo4j.get_related_content(content_id, limit=limit)

    async def record_content_completion(
        self,
        user_id: uuid.UUID,
        content_id: uuid.UUID,
        score: float | None = None,
        time_spent_seconds: int | None = None,
    ) -> bool:
        """Record content completion in the knowledge graph."""
        neo4j = await self.get_neo4j()
        return await neo4j.record_content_completion(
            user_id, content_id, score, time_spent_seconds
        )

    async def record_user_interest(
        self,
        user_id: uuid.UUID,
        concept_id: str,
        weight: float = 1.0,
    ) -> bool:
        """Record user interest in a concept."""
        neo4j = await self.get_neo4j()
        return await neo4j.user_interests_in_concept(user_id, concept_id, weight)


# Global instance
_prerequisite_checker: PrerequisiteChecker | None = None


async def get_prerequisite_checker() -> PrerequisiteChecker:
    """Get or create global prerequisite checker."""
    global _prerequisite_checker
    if _prerequisite_checker is None:
        _prerequisite_checker = PrerequisiteChecker()
    return _prerequisite_checker
