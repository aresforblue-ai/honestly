"""
Reputation Analyzer
===================

Time series analysis for AI agent reputation proofs.
Tracks reputation history and detects suspicious patterns.

Features:
- Reputation trend analysis
- Sudden jump detection
- Consistency scoring
- Cross-agent comparison

Usage:
    from ml.reputation_analyzer import ReputationAnalyzer
    
    analyzer = ReputationAnalyzer(neo4j_driver)
    analysis = analyzer.analyze_agent("did:honestly:agent:xyz")
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class ReputationTrend:
    """Reputation trend analysis result."""
    agent_id: str
    current_reputation: int
    average_reputation: float
    trend_direction: str  # "rising", "falling", "stable"
    trend_magnitude: float  # Rate of change per day
    volatility: float  # Standard deviation
    proof_count: int
    time_span_days: int
    anomaly_flags: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "current_reputation": self.current_reputation,
            "average_reputation": round(self.average_reputation, 2),
            "trend": {
                "direction": self.trend_direction,
                "magnitude": round(self.trend_magnitude, 4),
            },
            "volatility": round(self.volatility, 4),
            "proof_count": self.proof_count,
            "time_span_days": self.time_span_days,
            "anomaly_flags": self.anomaly_flags,
        }


class ReputationAnalyzer:
    """
    Analyzes AI agent reputation over time.
    
    Stores reputation history in Neo4j and performs
    time series analysis to detect anomalies.
    """
    
    # Thresholds
    SUDDEN_JUMP_THRESHOLD = 20  # Points in 24h
    HIGH_VOLATILITY_THRESHOLD = 15  # Standard deviation
    MIN_PROOFS_FOR_ANALYSIS = 5
    
    def __init__(self, neo4j_driver=None):
        """
        Initialize the reputation analyzer.
        
        Args:
            neo4j_driver: Neo4j driver instance (optional, will use default if None)
        """
        self.driver = neo4j_driver
        self._init_schema()
    
    def _init_schema(self) -> None:
        """Initialize Neo4j schema for reputation tracking."""
        if not self.driver:
            logger.warning("No Neo4j driver, reputation history will not be persisted")
            return
        
        try:
            with self.driver.session() as session:
                # Create constraints and indexes
                session.run("""
                    CREATE CONSTRAINT agent_reputation_id IF NOT EXISTS
                    FOR (r:ReputationProof) REQUIRE r.proof_id IS UNIQUE
                """)
                session.run("""
                    CREATE INDEX agent_reputation_agent IF NOT EXISTS
                    FOR (r:ReputationProof) ON (r.agent_id)
                """)
                session.run("""
                    CREATE INDEX agent_reputation_time IF NOT EXISTS
                    FOR (r:ReputationProof) ON (r.timestamp)
                """)
            logger.info("Initialized reputation tracking schema")
        except Exception as e:
            logger.error(f"Failed to init schema: {e}")
    
    def record_reputation_proof(
        self,
        agent_id: str,
        reputation_score: int,
        threshold: int,
        nullifier: str,
        proof_id: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> bool:
        """
        Record a reputation proof in the history.
        
        Args:
            agent_id: Agent DID or identifier
            reputation_score: Claimed reputation (from proof)
            threshold: Threshold that was proven
            nullifier: Proof nullifier
            proof_id: Unique proof identifier
            metadata: Additional metadata
        
        Returns:
            True if recorded successfully
        """
        if not self.driver:
            return False
        
        proof_id = proof_id or f"rep_{agent_id}_{datetime.utcnow().timestamp()}"
        
        try:
            with self.driver.session() as session:
                session.run("""
                    MERGE (a:Agent {id: $agent_id})
                    CREATE (r:ReputationProof {
                        proof_id: $proof_id,
                        agent_id: $agent_id,
                        reputation_score: $reputation_score,
                        threshold: $threshold,
                        nullifier: $nullifier,
                        timestamp: datetime(),
                        metadata: $metadata
                    })
                    CREATE (a)-[:HAS_REPUTATION_PROOF]->(r)
                """, {
                    "agent_id": agent_id,
                    "proof_id": proof_id,
                    "reputation_score": reputation_score,
                    "threshold": threshold,
                    "nullifier": nullifier,
                    "metadata": metadata or {},
                })
            return True
        except Exception as e:
            logger.error(f"Failed to record reputation proof: {e}")
            return False
    
    def get_reputation_history(
        self,
        agent_id: str,
        days: int = 30,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get reputation history for an agent.
        
        Args:
            agent_id: Agent identifier
            days: Number of days to look back
            limit: Maximum records to return
        
        Returns:
            List of reputation records
        """
        if not self.driver:
            return []
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (r:ReputationProof {agent_id: $agent_id})
                    WHERE r.timestamp > datetime() - duration({days: $days})
                    RETURN r.reputation_score AS score,
                           r.threshold AS threshold,
                           r.timestamp AS timestamp,
                           r.nullifier AS nullifier
                    ORDER BY r.timestamp DESC
                    LIMIT $limit
                """, {
                    "agent_id": agent_id,
                    "days": days,
                    "limit": limit,
                })
                
                return [
                    {
                        "score": record["score"],
                        "threshold": record["threshold"],
                        "timestamp": record["timestamp"].isoformat() if record["timestamp"] else None,
                        "nullifier": record["nullifier"],
                    }
                    for record in result
                ]
        except Exception as e:
            logger.error(f"Failed to get reputation history: {e}")
            return []
    
    def analyze_agent(self, agent_id: str) -> ReputationTrend:
        """
        Analyze reputation trend for an agent.
        
        Args:
            agent_id: Agent identifier
        
        Returns:
            ReputationTrend with analysis results
        """
        history = self.get_reputation_history(agent_id, days=30)
        
        if len(history) < self.MIN_PROOFS_FOR_ANALYSIS:
            return ReputationTrend(
                agent_id=agent_id,
                current_reputation=history[0]["threshold"] if history else 0,
                average_reputation=history[0]["threshold"] if history else 0,
                trend_direction="stable",
                trend_magnitude=0.0,
                volatility=0.0,
                proof_count=len(history),
                time_span_days=0,
                anomaly_flags=["insufficient_data"],
            )
        
        # Extract scores (use threshold as proxy for reputation)
        scores = [h["threshold"] for h in history]
        scores.reverse()  # Oldest first
        
        # Calculate statistics
        import statistics
        current = scores[-1]
        average = statistics.mean(scores)
        volatility = statistics.stdev(scores) if len(scores) > 1 else 0
        
        # Calculate trend (simple linear regression slope)
        n = len(scores)
        x = list(range(n))
        x_mean = sum(x) / n
        y_mean = average
        
        numerator = sum((x[i] - x_mean) * (scores[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Determine trend direction
        if slope > 0.5:
            trend_direction = "rising"
        elif slope < -0.5:
            trend_direction = "falling"
        else:
            trend_direction = "stable"
        
        # Calculate time span
        time_span = 30  # Default assumption
        
        # Detect anomalies
        anomaly_flags = []
        
        # Sudden jump detection
        if len(scores) >= 2:
            recent_delta = abs(scores[-1] - scores[-2])
            if recent_delta > self.SUDDEN_JUMP_THRESHOLD:
                anomaly_flags.append("sudden_jump")
        
        # High volatility
        if volatility > self.HIGH_VOLATILITY_THRESHOLD:
            anomaly_flags.append("high_volatility")
        
        # Suspiciously perfect scores
        if all(s == 100 for s in scores[-5:]) and len(scores) >= 5:
            anomaly_flags.append("perfect_scores")
        
        # Gaming pattern (alternating high/low)
        if len(scores) >= 4:
            diffs = [scores[i+1] - scores[i] for i in range(len(scores)-1)]
            alternating = all(
                diffs[i] * diffs[i+1] < 0
                for i in range(len(diffs)-1)
            )
            if alternating and max(abs(d) for d in diffs) > 10:
                anomaly_flags.append("gaming_pattern")
        
        return ReputationTrend(
            agent_id=agent_id,
            current_reputation=current,
            average_reputation=average,
            trend_direction=trend_direction,
            trend_magnitude=slope,
            volatility=volatility,
            proof_count=len(history),
            time_span_days=time_span,
            anomaly_flags=anomaly_flags,
        )
    
    def compare_agents(
        self,
        agent_ids: List[str],
    ) -> Dict[str, Any]:
        """
        Compare reputation trends across multiple agents.
        
        Args:
            agent_ids: List of agent identifiers
        
        Returns:
            Comparison results with rankings
        """
        analyses = {
            agent_id: self.analyze_agent(agent_id)
            for agent_id in agent_ids
        }
        
        # Rank by current reputation
        ranked_by_reputation = sorted(
            analyses.items(),
            key=lambda x: x[1].current_reputation,
            reverse=True,
        )
        
        # Find most volatile
        most_volatile = max(
            analyses.items(),
            key=lambda x: x[1].volatility,
        )
        
        # Find fastest rising
        fastest_rising = max(
            analyses.items(),
            key=lambda x: x[1].trend_magnitude,
        )
        
        # Agents with anomalies
        anomalous = [
            agent_id for agent_id, analysis in analyses.items()
            if analysis.anomaly_flags and "insufficient_data" not in analysis.anomaly_flags
        ]
        
        return {
            "rankings": [
                {"rank": i+1, "agent_id": agent_id, "reputation": analysis.current_reputation}
                for i, (agent_id, analysis) in enumerate(ranked_by_reputation)
            ],
            "most_volatile": {
                "agent_id": most_volatile[0],
                "volatility": most_volatile[1].volatility,
            },
            "fastest_rising": {
                "agent_id": fastest_rising[0],
                "trend_magnitude": fastest_rising[1].trend_magnitude,
            },
            "anomalous_agents": anomalous,
            "total_analyzed": len(analyses),
        }
    
    def get_global_stats(self) -> Dict[str, Any]:
        """Get global reputation statistics across all agents."""
        if not self.driver:
            return {}
        
        try:
            with self.driver.session() as session:
                result = session.run("""
                    MATCH (r:ReputationProof)
                    WHERE r.timestamp > datetime() - duration({days: 7})
                    WITH count(r) AS total_proofs,
                         count(DISTINCT r.agent_id) AS unique_agents,
                         avg(r.threshold) AS avg_threshold,
                         max(r.threshold) AS max_threshold
                    RETURN total_proofs, unique_agents, avg_threshold, max_threshold
                """)
                
                record = result.single()
                if record:
                    return {
                        "total_proofs_7d": record["total_proofs"],
                        "unique_agents_7d": record["unique_agents"],
                        "average_threshold": round(record["avg_threshold"] or 0, 2),
                        "max_threshold": record["max_threshold"] or 0,
                    }
                return {}
        except Exception as e:
            logger.error(f"Failed to get global stats: {e}")
            return {}

