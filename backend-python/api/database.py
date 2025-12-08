"""
Database connection singleton for Neo4j.
Prevents multiple connection instantiation across modules.
"""
import os
import logging
from typing import Optional, TYPE_CHECKING
from functools import lru_cache

if TYPE_CHECKING:
    from py2neo import Graph

logger = logging.getLogger(__name__)

# Configuration
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')

_graph_instance: Optional["Graph"] = None


@lru_cache(maxsize=1)
def get_graph():
    """
    Get singleton Neo4j Graph connection.
    Uses lru_cache to ensure only one instance is created.
    """
    global _graph_instance
    if _graph_instance is None:
        try:
            from py2neo import Graph
            _graph_instance = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
            logger.info(f"Neo4j connection established: {NEO4J_URI}")
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    return _graph_instance


def check_connection() -> bool:
    """Check if Neo4j connection is alive."""
    try:
        graph = get_graph()
        graph.run("RETURN 1").evaluate()
        return True
    except Exception as e:
        logger.error(f"Neo4j health check failed: {e}")
        return False


def close_connection():
    """Close Neo4j connection (for graceful shutdown)."""
    global _graph_instance
    if _graph_instance is not None:
        try:
            # py2neo doesn't have explicit close, but we can clear the reference
            _graph_instance = None
            get_graph.cache_clear()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error(f"Error closing Neo4j connection: {e}")

