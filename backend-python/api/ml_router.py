"""
ML Anomaly Detection Router
===========================

FastAPI endpoints for ML-based anomaly detection with Kafka streaming.

Endpoints:
- POST /ai/anomaly-detect: Run anomaly detection on agent
- POST /ai/anomaly-batch: Batch anomaly detection
- POST /ai/train-model: Trigger model training
- GET /ai/ml-status: ML system health

Kafka Events:
- anomaly.detected: When agent anomaly_score > threshold
- anomaly.batch: Batch detection results
- model.trained: When model retraining completes

Usage:
    # Single agent detection
    POST /ai/anomaly-detect
    {
        "agent_id": "did:honestly:agent:xyz",
        "include_zkml_proof": true
    }
    
    # Response includes Kafka event ID if anomalous
"""

import asyncio
import json
import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends, status
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["ml-anomaly"])

# Kafka configuration
KAFKA_BOOTSTRAP = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
KAFKA_TOPIC_ANOMALY = os.getenv("KAFKA_TOPIC_ANOMALY", "anomaly.detected")
KAFKA_TOPIC_BATCH = os.getenv("KAFKA_TOPIC_BATCH", "anomaly.batch")
KAFKA_TOPIC_MODEL = os.getenv("KAFKA_TOPIC_MODEL", "model.trained")

# ML configuration
ANOMALY_THRESHOLD = float(os.getenv("ANOMALY_THRESHOLD", "0.7"))
SEQ_LEN = int(os.getenv("ML_SEQ_LEN", "10"))

# Try to import Kafka
try:
    from kafka import KafkaProducer
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logger.warning("kafka-python not installed, events will be logged only")

# Try to import ML modules
try:
    from ml.autoencoder import get_autoencoder
    from ml.anomaly_detector import get_detector
    from ml.neo4j_loader import Neo4jDataLoader
    from ml.zkml_prover import get_zkml_prover
    from ml.deepprove_integration import get_deepprove_zkml
    ML_AVAILABLE = True
except ImportError as e:
    ML_AVAILABLE = False
    logger.warning(f"ML modules not available: {e}")

# Alert service for Slack/Discord
try:
    from api.alerts import get_alert_service, alert_on_anomaly
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False
    async def alert_on_anomaly(anomaly):
        return {"slack": False, "discord": False, "reason": "not_available"}

# WebSocket manager for real-time streaming
try:
    from api.websocket_router import get_connection_manager
    WS_AVAILABLE = True
except ImportError:
    WS_AVAILABLE = False
    get_connection_manager = None

# Try to import Neo4j
try:
    from py2neo import Graph
    NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
    NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
    NEO4J_PASS = os.getenv('NEO4J_PASS', 'test')
    neo4j_graph = Graph(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
    NEO4J_AVAILABLE = True
except Exception as e:
    NEO4J_AVAILABLE = False
    neo4j_graph = None
    logger.warning(f"Neo4j not available: {e}")


# Kafka producer singleton
_kafka_producer: Optional[Any] = None


def get_kafka_producer():
    """Get or create Kafka producer."""
    global _kafka_producer
    if _kafka_producer is None and KAFKA_AVAILABLE:
        try:
            _kafka_producer = KafkaProducer(
                bootstrap_servers=KAFKA_BOOTSTRAP.split(","),
                value_serializer=lambda v: json.dumps(v).encode("utf-8"),
                key_serializer=lambda k: k.encode("utf-8") if k else None,
                acks="all",
                retries=3,
            )
            logger.info(f"Connected to Kafka at {KAFKA_BOOTSTRAP}")
        except Exception as e:
            logger.error(f"Failed to connect to Kafka: {e}")
            _kafka_producer = None
    return _kafka_producer


async def publish_kafka_event(
    topic: str,
    key: str,
    event: Dict[str, Any],
) -> Optional[str]:
    """Publish event to Kafka topic."""
    producer = get_kafka_producer()
    
    # Add metadata
    event["_timestamp"] = datetime.now(timezone.utc).isoformat()
    event["_topic"] = topic
    
    if producer:
        try:
            future = producer.send(topic, key=key, value=event)
            # Don't block - fire and forget with callback
            future.add_callback(
                lambda m: logger.debug(f"Kafka event sent: {topic}:{key}")
            )
            future.add_errback(
                lambda e: logger.error(f"Kafka send failed: {e}")
            )
            return f"{topic}:{key}:{event['_timestamp']}"
        except Exception as e:
            logger.error(f"Kafka publish error: {e}")
    
    # Fallback: log event
    logger.info(f"[KAFKA_EVENT] {topic}:{key} = {json.dumps(event)[:200]}")
    return f"logged:{topic}:{key}"


# Request/Response Models

class AnomalyDetectRequest(BaseModel):
    """Request for single agent anomaly detection."""
    agent_id: str = Field(..., min_length=1, max_length=200)
    include_zkml_proof: bool = Field(default=False, description="Generate zkML proof")
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    seq_len: int = Field(default=10, ge=5, le=50)


class AnomalyBatchRequest(BaseModel):
    """Request for batch anomaly detection."""
    agent_ids: List[str] = Field(..., min_items=1, max_items=100)
    include_zkml_proof: bool = Field(default=False)
    threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class TrainModelRequest(BaseModel):
    """Request for model training."""
    epochs: int = Field(default=50, ge=10, le=500)
    batch_size: int = Field(default=32, ge=8, le=128)
    days: int = Field(default=30, ge=7, le=90)
    min_samples: int = Field(default=500, ge=100, le=10000)


class ZKMLProofRequest(BaseModel):
    """Request for zkML proof generation."""
    agent_id: str = Field(..., min_length=1, max_length=200)
    threshold: float = Field(default=0.8, ge=0.0, le=1.0)
    use_rapidsnark: bool = Field(default=True, description="Use Rapidsnark for faster proving")
    include_sequence_commitment: bool = Field(default=False)


class AnomalyResult(BaseModel):
    """Result of anomaly detection."""
    agent_id: str
    anomaly_score: float
    is_anomalous: bool
    threshold: float
    flags: List[str] = []
    reconstruction_error: Optional[float] = None
    zkml_proof: Optional[Dict[str, Any]] = None
    kafka_event_id: Optional[str] = None
    detection_time_ms: float


class BatchResult(BaseModel):
    """Result of batch anomaly detection."""
    results: List[AnomalyResult]
    summary: Dict[str, Any]
    kafka_event_id: Optional[str] = None


# Helper functions

def fetch_agent_features(
    agent_id: str,
    seq_len: int = 10,
) -> List[List[float]]:
    """
    Fetch agent activity features from Neo4j.
    
    Returns sequence of feature vectors for the agent.
    """
    if not NEO4J_AVAILABLE or neo4j_graph is None:
        # Generate synthetic features for testing
        import random
        return [
            [
                random.uniform(40, 80),  # reputation
                random.uniform(1, 5),     # claims
                random.uniform(0.5, 2),   # proofs
                random.uniform(0, 3),     # interactions
                random.randint(8, 20) / 24,  # hour
                random.randint(0, 6) / 7,    # day
                random.gauss(100, 20),    # response time
                random.gauss(0.02, 0.01), # error rate
            ]
            for _ in range(seq_len)
        ]
    
    try:
        # Query agent's recent activity
        query = """
        MATCH (a:Agent {id: $agent_id})
        OPTIONAL MATCH (a)-[:HAS_ACTIVITY]->(act:Activity)
        WHERE act.timestamp > datetime() - duration({days: 30})
        WITH a, act
        ORDER BY act.timestamp DESC
        LIMIT $seq_len
        RETURN 
            a.reputation AS reputation,
            act.claim_count AS claims,
            act.proof_count AS proofs,
            act.interaction_count AS interactions,
            act.hour AS hour,
            act.day_of_week AS day,
            act.response_time AS response_time,
            act.error_rate AS error_rate
        """
        
        results = neo4j_graph.run(query, {
            "agent_id": agent_id,
            "seq_len": seq_len,
        }).data()
        
        if not results:
            # No activity found, return defaults
            return [[50, 1, 0.5, 1, 12/24, 3/7, 100, 0.02]] * seq_len
        
        features = []
        for r in results:
            features.append([
                float(r.get("reputation") or 50),
                float(r.get("claims") or 1),
                float(r.get("proofs") or 0.5),
                float(r.get("interactions") or 1),
                float(r.get("hour") or 12) / 24,
                float(r.get("day") or 3) / 7,
                float(r.get("response_time") or 100),
                float(r.get("error_rate") or 0.02),
            ])
        
        # Pad if needed
        while len(features) < seq_len:
            features.append(features[-1] if features else [50, 1, 0.5, 1, 0.5, 0.5, 100, 0.02])
        
        return features[:seq_len]
        
    except Exception as e:
        logger.error(f"Neo4j query failed for {agent_id}: {e}")
        # Return synthetic data
        import random
        return [
            [50 + random.gauss(0, 10), 2, 1, 1, 0.5, 0.5, 100, 0.02]
            for _ in range(seq_len)
        ]


async def run_anomaly_detection(
    agent_id: str,
    features: List[List[float]],
    threshold: float,
    include_zkml: bool,
) -> Dict[str, Any]:
    """Run anomaly detection on agent features."""
    result = {
        "agent_id": agent_id,
        "anomaly_score": 0.0,
        "is_anomalous": False,
        "threshold": threshold,
        "flags": [],
        "reconstruction_error": None,
        "zkml_proof": None,
    }
    
    if not ML_AVAILABLE:
        # Fallback: simple heuristic
        avg_rep = sum(f[0] for f in features) / len(features)
        variance = sum((f[0] - avg_rep) ** 2 for f in features) / len(features)
        result["anomaly_score"] = min(1.0, variance / 500)
        result["is_anomalous"] = result["anomaly_score"] > threshold
        if result["is_anomalous"]:
            result["flags"].append("high_variance")
        return result
    
    try:
        # Try autoencoder first
        autoencoder = get_autoencoder()
        ae_result = autoencoder.detect_anomaly(features)
        
        result["anomaly_score"] = ae_result.anomaly_score
        result["reconstruction_error"] = ae_result.reconstruction_error
        result["is_anomalous"] = ae_result.is_anomalous or ae_result.anomaly_score > threshold
        
        # Also run heuristic detector for additional flags
        detector = get_detector()
        proof_data = {"publicSignals": [str(int(features[-1][0]))]}
        heuristic_result = detector.analyze_proof(proof_data, agent_id, "agent_reputation")
        result["flags"] = heuristic_result.flags
        
        # Combine scores (weighted)
        combined_score = 0.6 * ae_result.anomaly_score + 0.4 * heuristic_result.anomaly_score
        result["anomaly_score"] = combined_score
        result["is_anomalous"] = combined_score > threshold
        
        # Generate zkML proof if requested and anomalous
        if include_zkml and result["is_anomalous"]:
            try:
                prover = get_zkml_prover()
                proof = prover.prove_anomaly_threshold(features, threshold)
                result["zkml_proof"] = proof.to_dict()
            except Exception as e:
                logger.warning(f"zkML proof generation failed: {e}")
        
    except Exception as e:
        logger.error(f"Anomaly detection failed: {e}")
        result["flags"].append("detection_error")
    
    return result


# Endpoints

@router.post("/anomaly-detect", response_model=AnomalyResult)
async def detect_anomaly(
    request: AnomalyDetectRequest,
    background_tasks: BackgroundTasks,
):
    """
    Detect anomalies in agent behavior.
    
    Runs LSTM autoencoder + heuristic analysis.
    Publishes to Kafka if anomalous.
    Optionally generates zkML proof.
    """
    start_time = time.perf_counter()
    
    # Fetch agent features from Neo4j
    features = fetch_agent_features(request.agent_id, request.seq_len)
    
    # Run detection
    result = await run_anomaly_detection(
        agent_id=request.agent_id,
        features=features,
        threshold=request.threshold,
        include_zkml=request.include_zkml_proof,
    )
    
    detection_time = (time.perf_counter() - start_time) * 1000
    result["detection_time_ms"] = round(detection_time, 2)
    
    # Publish to Kafka if anomalous
    if result["is_anomalous"]:
        event = {
            "agent_id": request.agent_id,
            "anomaly_score": result["anomaly_score"],
            "threshold": request.threshold,
            "flags": result["flags"],
            "detection_time_ms": result["detection_time_ms"],
            "action": "investigate",
        }
        
        # Add zkML proof hash if available
        if result.get("zkml_proof"):
            event["zkml_proof_hash"] = result["zkml_proof"].get("model_hash")
        
        event_id = await publish_kafka_event(
            topic=KAFKA_TOPIC_ANOMALY,
            key=request.agent_id,
            event=event,
        )
        result["kafka_event_id"] = event_id
        
        # Send Slack/Discord alerts
        if ALERTS_AVAILABLE:
            background_tasks.add_task(alert_on_anomaly, event)
        
        # Broadcast to WebSocket clients
        if WS_AVAILABLE and get_connection_manager:
            ws_manager = get_connection_manager()
            background_tasks.add_task(ws_manager.broadcast_anomaly, event)
        
        logger.warning(
            f"ANOMALY DETECTED: agent={request.agent_id} "
            f"score={result['anomaly_score']:.3f} flags={result['flags']}"
        )
    
    return AnomalyResult(**result)


@router.post("/anomaly-batch", response_model=BatchResult)
async def detect_anomaly_batch(
    request: AnomalyBatchRequest,
    background_tasks: BackgroundTasks,
):
    """
    Batch anomaly detection for multiple agents.
    
    Processes agents in parallel, publishes summary to Kafka.
    """
    start_time = time.perf_counter()
    
    results = []
    anomalous_count = 0
    
    # Process in parallel using asyncio
    async def process_agent(agent_id: str) -> Dict[str, Any]:
        features = fetch_agent_features(agent_id)
        return await run_anomaly_detection(
            agent_id=agent_id,
            features=features,
            threshold=request.threshold,
            include_zkml=request.include_zkml_proof,
        )
    
    # Run all detections concurrently
    tasks = [process_agent(agent_id) for agent_id in request.agent_ids]
    detection_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for i, result in enumerate(detection_results):
        if isinstance(result, Exception):
            results.append({
                "agent_id": request.agent_ids[i],
                "anomaly_score": 0.0,
                "is_anomalous": False,
                "threshold": request.threshold,
                "flags": ["error"],
                "detection_time_ms": 0,
            })
        else:
            result["detection_time_ms"] = 0  # Will set total time
            results.append(result)
            if result["is_anomalous"]:
                anomalous_count += 1
    
    total_time = (time.perf_counter() - start_time) * 1000
    avg_time = total_time / len(request.agent_ids) if request.agent_ids else 0
    
    summary = {
        "total_agents": len(request.agent_ids),
        "anomalous_count": anomalous_count,
        "normal_count": len(request.agent_ids) - anomalous_count,
        "anomaly_rate": anomalous_count / len(request.agent_ids) if request.agent_ids else 0,
        "total_time_ms": round(total_time, 2),
        "avg_time_ms": round(avg_time, 2),
        "threshold": request.threshold,
    }
    
    # Publish batch summary to Kafka
    event_id = None
    if anomalous_count > 0:
        anomalous_agents = [
            {"agent_id": r["agent_id"], "score": r["anomaly_score"]}
            for r in results if r["is_anomalous"]
        ]
        event = {
            "batch_id": f"batch_{int(time.time())}",
            "summary": summary,
            "anomalous_agents": anomalous_agents,
            "action": "batch_investigation",
        }
        event_id = await publish_kafka_event(
            topic=KAFKA_TOPIC_BATCH,
            key=f"batch_{len(request.agent_ids)}",
            event=event,
        )
    
    return BatchResult(
        results=[AnomalyResult(**r) for r in results],
        summary=summary,
        kafka_event_id=event_id,
    )


@router.post("/train-model")
async def train_model(
    request: TrainModelRequest,
    background_tasks: BackgroundTasks,
):
    """
    Trigger model retraining on recent data.
    
    Runs in background, publishes completion to Kafka.
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML modules not available",
        )
    
    async def train_task():
        """Background training task."""
        start_time = time.perf_counter()
        
        try:
            # Load training data
            loader = Neo4jDataLoader(neo4j_graph)
            train_data = loader.load_agent_sequences(
                days=request.days,
                min_samples=request.min_samples,
            )
            
            # Train autoencoder
            autoencoder = get_autoencoder()
            history = autoencoder.fit(
                train_data,
                epochs=request.epochs,
                batch_size=request.batch_size,
            )
            
            train_time = time.perf_counter() - start_time
            
            # Publish completion event
            event = {
                "status": "completed",
                "epochs": request.epochs,
                "samples": len(train_data),
                "final_loss": history["train_loss"][-1] if history.get("train_loss") else None,
                "train_time_seconds": round(train_time, 2),
            }
            await publish_kafka_event(
                topic=KAFKA_TOPIC_MODEL,
                key="autoencoder",
                event=event,
            )
            
            logger.info(f"Model training completed in {train_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            await publish_kafka_event(
                topic=KAFKA_TOPIC_MODEL,
                key="autoencoder",
                event={"status": "failed", "error": str(e)},
            )
    
    # Run training in background
    background_tasks.add_task(train_task)
    
    return {
        "status": "training_started",
        "epochs": request.epochs,
        "batch_size": request.batch_size,
        "days": request.days,
        "kafka_topic": KAFKA_TOPIC_MODEL,
    }


@router.get("/ml-status")
async def ml_status():
    """
    Get ML system health and statistics.
    """
    status_info = {
        "ml_available": ML_AVAILABLE,
        "neo4j_available": NEO4J_AVAILABLE,
        "kafka_available": KAFKA_AVAILABLE,
        "config": {
            "anomaly_threshold": ANOMALY_THRESHOLD,
            "seq_len": SEQ_LEN,
            "kafka_bootstrap": KAFKA_BOOTSTRAP,
        },
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    
    if ML_AVAILABLE:
        try:
            # Get detector stats
            detector = get_detector()
            status_info["heuristic_detector"] = detector.get_stats()
            
            # Check autoencoder
            autoencoder = get_autoencoder()
            status_info["autoencoder"] = {
                "type": type(autoencoder).__name__,
                "ready": True,
            }
            
            # Check zkML prover
            prover = get_zkml_prover()
            status_info["zkml_prover"] = {
                "model_hash": prover.model_hash,
                "circuit_compiled": prover._circuit_compiled,
            }
            
        except Exception as e:
            status_info["error"] = str(e)
    
    return status_info


@router.get("/kafka-health")
async def kafka_health():
    """Check Kafka connectivity."""
    if not KAFKA_AVAILABLE:
        return {
            "status": "unavailable",
            "reason": "kafka-python not installed",
        }
    
    producer = get_kafka_producer()
    if producer is None:
        return {
            "status": "disconnected",
            "bootstrap_servers": KAFKA_BOOTSTRAP,
        }
    
    # Try to get cluster metadata
    try:
        metadata = producer.bootstrap_connected()
        return {
            "status": "connected",
            "bootstrap_servers": KAFKA_BOOTSTRAP,
            "connected": metadata,
            "topics": {
                "anomaly": KAFKA_TOPIC_ANOMALY,
                "batch": KAFKA_TOPIC_BATCH,
                "model": KAFKA_TOPIC_MODEL,
            },
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


# ============================================================================
# zkML Endpoints - Zero-Knowledge Machine Learning Proofs
# ============================================================================

@router.post("/zkml/prove")
async def generate_zkml_proof(request: ZKMLProofRequest):
    """
    Generate a zkML proof of anomaly detection result.
    
    Uses DeepProve to prove "reconstruction_error > threshold"
    without revealing:
    - Agent activity features
    - Model weights
    - Raw anomaly score
    
    Only reveals:
    - Threshold used
    - Boolean: is_above_threshold
    - Model commitment (hash)
    
    Output is Groth16-compatible for on-chain verification.
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML modules not available",
        )
    
    start_time = time.perf_counter()
    
    # Fetch agent features
    features = fetch_agent_features(request.agent_id)
    
    # Generate zkML proof
    try:
        zkml = get_deepprove_zkml()
        proof = zkml.prove_anomaly(
            features=features,
            threshold=request.threshold,
            use_rapidsnark=request.use_rapidsnark,
        )
        
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Publish to Kafka if anomalous
        kafka_event_id = None
        if proof.is_above_threshold:
            event = {
                "agent_id": request.agent_id,
                "threshold": request.threshold,
                "is_anomalous": True,
                "proof_generated": True,
                "model_commitment": proof.model_commitment[:16],
                "action": "zkml_verified_anomaly",
            }
            kafka_event_id = await publish_kafka_event(
                topic=KAFKA_TOPIC_ANOMALY,
                key=f"zkml:{request.agent_id}",
                event=event,
            )
        
        return {
            "agent_id": request.agent_id,
            "proof": proof.to_dict(),
            "is_above_threshold": proof.is_above_threshold,
            "total_time_ms": round(total_time, 2),
            "kafka_event_id": kafka_event_id,
            "verification_command": (
                f"npx snarkjs groth16 verify "
                f"circuits/zkml/verification_key.json "
                f"public.json proof.json"
            ),
        }
        
    except Exception as e:
        logger.error(f"zkML proof generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Proof generation failed: {str(e)}",
        )


@router.post("/zkml/verify")
async def verify_zkml_proof(proof_data: Dict[str, Any]):
    """
    Verify a zkML proof.
    
    Accepts a proof in snarkjs/Groth16 format and verifies it
    against the circuit's verification key.
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML modules not available",
        )
    
    try:
        from ml.deepprove_integration import DeepProveProof
        
        # Reconstruct proof object
        proof_obj = proof_data.get("proof", {})
        proof = DeepProveProof(
            pi_a=proof_obj.get("pi_a", []),
            pi_b=proof_obj.get("pi_b", []),
            pi_c=proof_obj.get("pi_c", []),
            public_inputs=proof_data.get("publicInputs", []),
            model_commitment=proof_data.get("metadata", {}).get("model_commitment", ""),
            threshold_scaled=proof_data.get("metadata", {}).get("threshold_scaled", 0),
            is_above_threshold=proof_data.get("metadata", {}).get("is_above_threshold", False),
        )
        
        # Verify
        zkml = get_deepprove_zkml()
        is_valid = zkml.verify(proof)
        
        return {
            "valid": is_valid,
            "public_inputs": proof.public_inputs,
            "model_commitment": proof.model_commitment[:16] if proof.model_commitment else None,
        }
        
    except Exception as e:
        logger.error(f"zkML verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


@router.post("/zkml/setup")
async def setup_zkml_circuit(
    onnx_path: str = "models/autoencoder.onnx",
    background_tasks: BackgroundTasks = None,
):
    """
    Setup zkML circuit from ONNX model.
    
    One-time setup that compiles the model to a ZK circuit
    and generates proving/verification keys.
    
    This is a long-running operation (~5-10 minutes for complex models).
    """
    if not ML_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="ML modules not available",
        )
    
    from pathlib import Path
    
    model_path = Path(onnx_path)
    if not model_path.exists():
        # Try to export current autoencoder
        try:
            autoencoder = get_autoencoder()
            model_path.parent.mkdir(parents=True, exist_ok=True)
            autoencoder.export_onnx(model_path)
            logger.info(f"Exported autoencoder to {model_path}")
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Model not found and export failed: {e}",
            )
    
    async def setup_task():
        """Background setup task."""
        try:
            zkml = get_deepprove_zkml()
            success = zkml.setup(model_path, optimize=True)
            
            event = {
                "status": "completed" if success else "failed",
                "model_path": str(model_path),
                "circuit_stats": zkml.get_circuit_stats(),
            }
            await publish_kafka_event(
                topic=KAFKA_TOPIC_MODEL,
                key="zkml_setup",
                event=event,
            )
        except Exception as e:
            logger.error(f"zkML setup failed: {e}")
            await publish_kafka_event(
                topic=KAFKA_TOPIC_MODEL,
                key="zkml_setup",
                event={"status": "failed", "error": str(e)},
            )
    
    if background_tasks:
        background_tasks.add_task(setup_task)
        return {
            "status": "setup_started",
            "model_path": str(model_path),
            "note": "This may take 5-10 minutes. Check Kafka for completion.",
        }
    else:
        # Run synchronously (for testing)
        zkml = get_deepprove_zkml()
        success = zkml.setup(model_path, optimize=True)
        return {
            "status": "completed" if success else "failed",
            "circuit_stats": zkml.get_circuit_stats(),
        }


@router.get("/zkml/status")
async def zkml_status():
    """Get zkML circuit status and statistics."""
    if not ML_AVAILABLE:
        return {
            "available": False,
            "reason": "ML modules not available",
        }
    
    try:
        zkml = get_deepprove_zkml()
        stats = zkml.get_circuit_stats()
        
        return {
            "available": True,
            "stats": stats,
            "endpoints": {
                "prove": "/ai/zkml/prove",
                "verify": "/ai/zkml/verify",
                "setup": "/ai/zkml/setup",
            },
        }
    except Exception as e:
        return {
            "available": False,
            "error": str(e),
        }

