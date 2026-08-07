"""
PANDORA Learning Service Neo4j Graph Client
Manages knowledge graph relationships for learning paths
"""
from typing import Any
from uuid import UUID

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, AuthError

from src.core.config import get_settings
from src.core.logging import get_logger

logger = get_logger(__name__)


class Neo4jClient:
    """
    Async Neo4j client wrapper for knowledge graph operations.
    
    Graph Schema:
    - Nodes: User, Content, Concept, LearningPath, Course, Quiz
    - Relationships:
        - User -> [COMPLETED, IN_PROGRESS, BOOKMARKED] -> Content
        - User -> [INTERESTED_IN] -> Concept
        - Content -> [PREREQUISITE_OF, RELATED_TO] -> Content
        - Content -> [TEACHES, REQUIRES_UNDERSTANDING_OF] -> Concept
        - LearningPath -> [CONTAINS] -> Content
        - User -> [ENROLLED_IN] -> LearningPath
    """
    
    def __init__(self):
        """Initialize Neo4j client."""
        self._driver: AsyncDriver | None = None
    
    async def connect(self) -> None:
        """Establish connection to Neo4j."""
        if self._driver is not None:
            return
        
        settings = get_settings()
        
        self._driver = AsyncGraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_username, settings.neo4j_password),
        )
        
        # Verify connection
        try:
            async with self._driver.session(
                database=settings.neo4j_database
            ) as session:
                await session.run("RETURN 1")
            logger.info(
                "neo4j_connected",
                uri=settings.neo4j_uri,
                database=settings.neo4j_database,
            )
        except (ServiceUnavailable, AuthError) as e:
            logger.error("neo4j_connection_failed", error=str(e))
            self._driver = None
            raise
    
    async def disconnect(self) -> None:
        """Close Neo4j connection."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            logger.info("neo4j_disconnected")
    
    @property
    def driver(self) -> AsyncDriver:
        """Get the Neo4j driver."""
        if self._driver is None:
            raise RuntimeError("Neo4j client not connected. Call connect() first.")
        return self._driver
    
    async def execute_query(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> list[dict[str, Any]]:
        """Execute a Cypher query and return results."""
        settings = get_settings()
        
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, parameters or {})
            records = await result.data()
            return records
    
    async def execute_write(
        self,
        query: str,
        parameters: dict | None = None,
    ) -> dict[str, Any]:
        """Execute a write transaction."""
        settings = get_settings()
        
        async with self.driver.session(database=settings.neo4j_database) as session:
            result = await session.run(query, parameters or {})
            summary = await result.consume()
            return {"counters": summary.counters}
    
    # ============ User-Content Relationships ============
    
    async def record_content_completion(
        self,
        user_id: UUID,
        content_id: UUID,
        score: float | None = None,
        time_spent_seconds: int | None = None,
    ) -> bool:
        """Record that a user completed content."""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (c:Content {id: $content_id})
        MERGE (u)-[r:COMPLETED]->(c)
        SET r.completed_at = datetime(),
            r.score = $score,
            r.time_spent_seconds = $time_spent_seconds
        RETURN r
        """
        try:
            await self.execute_write(query, {
                "user_id": str(user_id),
                "content_id": str(content_id),
                "score": score,
                "time_spent_seconds": time_spent_seconds,
            })
            return True
        except Exception as e:
            logger.error("record_completion_failed", error=str(e))
            return False
    
    async def get_user_learning_history(
        self,
        user_id: UUID,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Get user's learning history."""
        query = """
        MATCH (u:User {id: $user_id})-[r]->(c:Content)
        WHERE type(r) IN ['COMPLETED', 'IN_PROGRESS', 'BOOKMARKED']
        RETURN c.id AS content_id, c.title AS title, type(r) AS relationship,
               r.score AS score, r.completed_at AS completed_at
        ORDER BY r.completed_at DESC
        LIMIT $limit
        """
        return await self.execute_query(query, {
            "user_id": str(user_id),
            "limit": limit,
        })
    
    async def bookmark_content(
        self,
        user_id: UUID,
        content_id: UUID,
    ) -> bool:
        """Bookmark content for a user."""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (c:Content {id: $content_id})
        MERGE (u)-[r:BOOKMARKED]->(c)
        SET r.bookmarked_at = datetime()
        """
        try:
            await self.execute_write(query, {
                "user_id": str(user_id),
                "content_id": str(content_id),
            })
            return True
        except Exception as e:
            logger.error("bookmark_failed", error=str(e))
            return False
    
    # ============ Content Relationships ============
    
    async def link_content_prerequisite(
        self,
        content_id: UUID,
        prerequisite_id: UUID,
    ) -> bool:
        """Link content as a prerequisite of another."""
        query = """
        MATCH (c1:Content {id: $content_id})
        MATCH (c2:Content {id: $prerequisite_id})
        MERGE (c2)-[r:PREREQUISITE_OF]->(c1)
        """
        try:
            await self.execute_write(query, {
                "content_id": str(content_id),
                "prerequisite_id": str(prerequisite_id),
            })
            return True
        except Exception as e:
            logger.error("link_prerequisite_failed", error=str(e))
            return False
    
    async def get_content_prerequisites(
        self,
        content_id: UUID,
    ) -> list[dict[str, Any]]:
        """Get prerequisites for content."""
        query = """
        MATCH (c:Content {id: $content_id})<-[:PREREQUISITE_OF]-(prereq)
        RETURN prereq.id AS id, prereq.title AS title
        ORDER BY prereq.title
        """
        return await self.execute_query(query, {
            "content_id": str(content_id),
        })
    
    async def get_related_content(
        self,
        content_id: UUID,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Get content related to the given content."""
        query = """
        MATCH (c:Content {id: $content_id})-[r:RELATED_TO|TEACHES]->(related)
        RETURN DISTINCT related.id AS id, related.title AS title,
               labels(related) AS labels, type(r) AS relationship_type
        LIMIT $limit
        """
        return await self.execute_query(query, {
            "content_id": str(content_id),
            "limit": limit,
        })
    
    # ============ Concept Relationships ============
    
    async def user_interests_in_concept(
        self,
        user_id: UUID,
        concept_id: str,
        weight: float = 1.0,
    ) -> bool:
        """Record user interest in a concept."""
        query = """
        MATCH (u:User {id: $user_id})
        MERGE (c:Concept {id: $concept_id})
        MERGE (u)-[r:INTERESTED_IN]->(c)
        SET r.weight = COALESCE(r.weight, 0) + $weight,
            r.last_updated = datetime()
        """
        try:
            await self.execute_write(query, {
                "user_id": str(user_id),
                "concept_id": concept_id,
                "weight": weight,
            })
            return True
        except Exception as e:
            logger.error("record_interest_failed", error=str(e))
            return False
    
    async def get_user_concept_interests(
        self,
        user_id: UUID,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get user's concept interests."""
        query = """
        MATCH (u:User {id: $user_id})-[r:INTERESTED_IN]->(c:Concept)
        RETURN c.id AS concept_id, c.name AS name, r.weight AS weight
        ORDER BY r.weight DESC
        LIMIT $limit
        """
        return await self.execute_query(query, {
            "user_id": str(user_id),
            "limit": limit,
        })
    
    async def content_teaches_concepts(
        self,
        content_id: UUID,
        concept_ids: list[str],
    ) -> bool:
        """Link content to concepts it teaches."""
        query = """
        MATCH (c:Content {id: $content_id})
        UNWIND $concept_ids AS concept_id
        MERGE (concept:Concept {id: concept_id})
        MERGE (c)-[:TEACHES]->(concept)
        """
        try:
            await self.execute_write(query, {
                "content_id": str(content_id),
                "concept_ids": concept_ids,
            })
            return True
        except Exception as e:
            logger.error("link_concepts_failed", error=str(e))
            return False
    
    # ============ Learning Path Operations ============
    
    async def create_learning_path(
        self,
        path_id: UUID,
        user_id: UUID,
        title: str,
        content_ids: list[UUID],
    ) -> bool:
        """Create a learning path for a user."""
        query = """
        MATCH (u:User {id: $user_id})
        CREATE (lp:LearningPath {id: $path_id, title: $title, created_at: datetime()})
        CREATE (u)-[:CREATED]->(lp)
        WITH lp
        UNWIND $content_ids AS content_id
        MATCH (c:Content {id: content_id})
        CREATE (lp)-[:CONTAINS {order: 0}]->(c)
        RETURN lp
        """
        try:
            await self.execute_write(query, {
                "path_id": str(path_id),
                "user_id": str(user_id),
                "title": title,
                "content_ids": [str(cid) for cid in content_ids],
            })
            return True
        except Exception as e:
            logger.error("create_learning_path_failed", error=str(e))
            return False
    
    async def enroll_in_learning_path(
        self,
        user_id: UUID,
        path_id: UUID,
    ) -> bool:
        """Enroll user in a learning path."""
        query = """
        MATCH (u:User {id: $user_id})
        MATCH (lp:LearningPath {id: $path_id})
        MERGE (u)-[r:ENROLLED_IN]->(lp)
        SET r.enrolled_at = datetime(),
            r.progress = 0.0
        """
        try:
            await self.execute_write(query, {
                "user_id": str(user_id),
                "path_id": str(path_id),
            })
            return True
        except Exception as e:
            logger.error("enroll_failed", error=str(e))
            return False
    
    # ============ Recommendations ============
    
    async def get_similar_users(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Find users with similar learning patterns."""
        query = """
        MATCH (u:User {id: $user_id})-[:COMPLETED]->(c:Content)<-[:COMPLETED]-(similar:User)
        WHERE u <> similar
        WITH similar, count(c) AS common_completed
        ORDER BY common_completed DESC
        LIMIT $limit
        RETURN similar.id AS user_id, common_completed
        """
        return await self.execute_query(query, {
            "user_id": str(user_id),
            "limit": limit,
        })
    
    async def get_collaborative_recommendations(
        self,
        user_id: UUID,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Get content recommendations based on similar users."""
        query = """
        MATCH (u:User {id: $user_id})-[:COMPLETED]->(c:Content)
        WITH u, collect(c.id) AS user_content
        MATCH (similar:User)-[:COMPLETED]->(rec:Content)
        WHERE NOT rec.id IN user_content AND similar <> u
        WITH rec, count(DISTINCT similar) AS similarity_score
        ORDER BY similarity_score DESC
        LIMIT $limit
        RETURN rec.id AS content_id, rec.title AS title, similarity_score
        """
        return await self.execute_query(query, {
            "user_id": str(user_id),
            "limit": limit,
        })


# Global client instance
_neo4j_client: Neo4jClient | None = None


async def get_neo4j_client() -> Neo4jClient:
    """Get or create the global Neo4j client."""
    global _neo4j_client
    if _neo4j_client is None:
        _neo4j_client = Neo4jClient()
        await _neo4j_client.connect()
    return _neo4j_client


async def close_neo4j_client() -> None:
    """Close the global Neo4j client."""
    global _neo4j_client
    if _neo4j_client is not None:
        await _neo4j_client.disconnect()
        _neo4j_client = None
