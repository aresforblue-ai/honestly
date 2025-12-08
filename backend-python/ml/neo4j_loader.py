"""
Neo4j Data Loader for ML Training
=================================

Loads agent activity data from Neo4j for training the LSTM autoencoder.
Extracts time-series features from the agent/claim graph.

Cypher queries pull:
- Agent reputation history
- Claim submission patterns
- Proof generation activity
- Interaction graphs

Usage:
    from ml.neo4j_loader import Neo4jDataLoader

    loader = Neo4jDataLoader(driver)
    train_data = loader.load_agent_sequences(
        days=30,
        seq_len=10,
        min_samples=100,
    )
"""

import logging
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)


class Neo4jDataLoader:
    """
    Loads agent activity data from Neo4j for ML training.
    """

    def __init__(self, neo4j_driver=None):
        """
        Initialize data loader.

        Args:
            neo4j_driver: Neo4j driver instance (or None for mock data)
        """
        self.driver = neo4j_driver

    def load_agent_sequences(
        self,
        days: int = 30,
        seq_len: int = 10,
        min_samples: int = 100,
        agent_ids: Optional[List[str]] = None,
    ) -> List[List[List[float]]]:
        """
        Load agent activity sequences for training.

        Args:
            days: Number of days of history
            seq_len: Sequence length (timesteps)
            min_samples: Minimum samples required
            agent_ids: Specific agents to load (or None for all)

        Returns:
            List of sequences, each sequence is list of feature vectors
        """
        if self.driver is None:
            logger.warning("No Neo4j driver, generating synthetic data")
            return self._generate_synthetic_data(min_samples, seq_len)

        try:
            sequences = []

            with self.driver.session() as session:
                # Query agent activity
                query = """
                MATCH (a:Agent)
                WHERE a.created_at > datetime() - duration({days: $days})
                OPTIONAL MATCH (a)-[:HAS_CLAIM]->(c:Claim)
                WHERE c.created_at > datetime() - duration({days: $days})
                OPTIONAL MATCH (a)-[:HAS_PROOF]->(p:Proof)
                WHERE p.created_at > datetime() - duration({days: $days})
                OPTIONAL MATCH (a)-[:INTERACTS_WITH]->(other:Agent)
                WITH a,
                     collect(DISTINCT c) AS claims,
                     collect(DISTINCT p) AS proofs,
                     count(DISTINCT other) AS interactions
                RETURN a.id AS agent_id,
                       a.reputation AS reputation,
                       size(claims) AS claim_count,
                       size(proofs) AS proof_count,
                       interactions,
                       a.created_at AS created_at
                """

                if agent_ids:
                    query = query.replace(
                        "WHERE a.created_at", f"WHERE a.id IN {agent_ids} AND a.created_at"
                    )

                results = session.run(query, {"days": days})

                for record in results:
                    # Create feature sequence for this agent
                    seq = self._create_sequence(
                        agent_id=record["agent_id"],
                        reputation=record["reputation"] or 50,
                        claim_count=record["claim_count"],
                        proof_count=record["proof_count"],
                        interactions=record["interactions"],
                        seq_len=seq_len,
                    )
                    sequences.append(seq)

            if len(sequences) < min_samples:
                logger.warning(
                    f"Only {len(sequences)} samples from Neo4j, "
                    f"adding synthetic to reach {min_samples}"
                )
                synthetic = self._generate_synthetic_data(
                    min_samples - len(sequences),
                    seq_len,
                )
                sequences.extend(synthetic)

            logger.info(f"Loaded {len(sequences)} agent sequences")
            return sequences

        except Exception as e:
            logger.error(f"Neo4j query failed: {e}")
            return self._generate_synthetic_data(min_samples, seq_len)

    def _create_sequence(
        self,
        agent_id: str,
        reputation: int,
        claim_count: int,
        proof_count: int,
        interactions: int,
        seq_len: int,
    ) -> List[List[float]]:
        """Create feature sequence from agent data."""
        import random

        sequence = []

        # Simulate time series with some variation
        for t in range(seq_len):
            hour = (t * 2) % 24  # Spread across day
            day = t % 7

            features = [
                reputation + random.gauss(0, 5),  # reputation_score
                claim_count / seq_len + random.gauss(0, 1),  # claims per period
                proof_count / seq_len + random.gauss(0, 0.5),  # proofs per period
                interactions / seq_len + random.gauss(0, 0.3),  # interactions
                hour / 24,  # hour_of_day (normalized)
                day / 7,  # day_of_week (normalized)
                random.gauss(100, 20),  # response_time_avg (ms)
                random.gauss(0.02, 0.01),  # error_rate
            ]
            sequence.append(features)

        return sequence

    def _generate_synthetic_data(
        self,
        n_samples: int,
        seq_len: int,
    ) -> List[List[List[float]]]:
        """Generate synthetic training data."""
        import random

        sequences = []

        for _ in range(n_samples):
            # Random agent profile
            base_rep = random.randint(30, 90)
            activity_level = random.choice(["low", "medium", "high"])

            if activity_level == "low":
                claims_per_day = random.uniform(0.1, 1)
                proofs_per_day = random.uniform(0.05, 0.5)
            elif activity_level == "medium":
                claims_per_day = random.uniform(1, 5)
                proofs_per_day = random.uniform(0.5, 2)
            else:
                claims_per_day = random.uniform(5, 20)
                proofs_per_day = random.uniform(2, 10)

            sequence = []
            current_rep = base_rep

            for t in range(seq_len):
                # Slight reputation drift
                current_rep += random.gauss(0, 2)
                current_rep = max(0, min(100, current_rep))

                hour = random.randint(8, 22)  # Normal business hours
                day = random.randint(0, 6)

                features = [
                    current_rep,
                    claims_per_day + random.gauss(0, claims_per_day * 0.2),
                    proofs_per_day + random.gauss(0, proofs_per_day * 0.2),
                    random.uniform(0, 5),  # interactions
                    hour / 24,
                    day / 7,
                    random.gauss(100, 20),  # response time
                    max(0, random.gauss(0.02, 0.01)),  # error rate
                ]
                sequence.append(features)

            sequences.append(sequence)

        return sequences

    def load_anomalous_samples(
        self,
        n_samples: int = 50,
        seq_len: int = 10,
    ) -> List[List[List[float]]]:
        """
        Generate known anomalous samples for testing.

        These represent attack patterns:
        - Reputation manipulation
        - Sybil attacks
        - Proof farming
        """
        anomalies = []

        for i in range(n_samples):
            anomaly_type = i % 4

            if anomaly_type == 0:
                # Sudden reputation spike
                sequence = self._generate_rep_spike(seq_len)
            elif anomaly_type == 1:
                # Burst activity (proof farming)
                sequence = self._generate_burst_activity(seq_len)
            elif anomaly_type == 2:
                # Unusual timing (bot behavior)
                sequence = self._generate_unusual_timing(seq_len)
            else:
                # Low diversity (sybil pattern)
                sequence = self._generate_sybil_pattern(seq_len)

            anomalies.append(sequence)

        return anomalies

    def _generate_rep_spike(self, seq_len: int) -> List[List[float]]:
        """Generate reputation spike anomaly."""
        import random

        sequence = []
        rep = random.randint(30, 50)

        spike_at = seq_len - 3

        for t in range(seq_len):
            if t >= spike_at:
                rep = random.randint(85, 99)  # Sudden spike

            sequence.append(
                [
                    rep,
                    random.uniform(1, 3),
                    random.uniform(0.5, 1.5),
                    random.uniform(0, 2),
                    random.randint(8, 18) / 24,
                    random.randint(0, 4) / 7,
                    random.gauss(100, 20),
                    random.gauss(0.02, 0.01),
                ]
            )

        return sequence

    def _generate_burst_activity(self, seq_len: int) -> List[List[float]]:
        """Generate burst activity anomaly."""
        import random

        sequence = []

        for t in range(seq_len):
            is_burst = t >= seq_len - 2

            sequence.append(
                [
                    random.uniform(50, 70),
                    100 if is_burst else random.uniform(1, 3),  # Huge spike
                    50 if is_burst else random.uniform(0.5, 1.5),
                    random.uniform(0, 2),
                    random.randint(0, 23) / 24,
                    random.randint(0, 6) / 7,
                    random.gauss(50, 10) if is_burst else random.gauss(100, 20),
                    random.gauss(0.02, 0.01),
                ]
            )

        return sequence

    def _generate_unusual_timing(self, seq_len: int) -> List[List[float]]:
        """Generate unusual timing anomaly (bot behavior)."""
        import random

        sequence = []

        for t in range(seq_len):
            # Activity at 3-5 AM, very consistent timing
            sequence.append(
                [
                    random.uniform(50, 70),
                    random.uniform(2, 4),
                    random.uniform(1, 2),
                    random.uniform(0, 1),
                    random.uniform(3, 5) / 24,  # 3-5 AM
                    random.randint(0, 6) / 7,
                    10 + random.gauss(0, 1),  # Very consistent response
                    random.gauss(0.001, 0.0005),  # Almost no errors
                ]
            )

        return sequence

    def _generate_sybil_pattern(self, seq_len: int) -> List[List[float]]:
        """Generate sybil-like pattern (coordinated fake agents)."""
        import random

        # All features nearly identical
        base = [
            60,
            5,
            2,
            0.1,  # Very few real interactions
            12 / 24,
            3 / 7,
            100,
            0.02,
        ]

        sequence = []
        for t in range(seq_len):
            # Minimal variation (coordinated)
            features = [v + random.gauss(0, 0.1) for v in base]
            sequence.append(features)

        return sequence


def create_training_dataset(
    neo4j_driver=None,
    normal_samples: int = 500,
    anomaly_samples: int = 50,
    seq_len: int = 10,
) -> Tuple[List[List[List[float]]], List[int]]:
    """
    Create labeled dataset for autoencoder training.

    Args:
        neo4j_driver: Neo4j driver (or None for synthetic)
        normal_samples: Number of normal samples
        anomaly_samples: Number of anomaly samples
        seq_len: Sequence length

    Returns:
        (data, labels) where labels are 0=normal, 1=anomaly
    """
    loader = Neo4jDataLoader(neo4j_driver)

    # Load normal data
    normal_data = loader.load_agent_sequences(
        min_samples=normal_samples,
        seq_len=seq_len,
    )

    # Load anomalous data
    anomaly_data = loader.load_anomalous_samples(
        n_samples=anomaly_samples,
        seq_len=seq_len,
    )

    # Combine
    data = normal_data + anomaly_data
    labels = [0] * len(normal_data) + [1] * len(anomaly_data)

    return data, labels
