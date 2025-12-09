"""
Quantum Computing API Routes
============================

REST endpoints for VERIDICUS-powered quantum computing access.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from quantum.quantum_gateway import (
    QuantumJobRequest,
    QuantumProvider,
    get_quantum_gateway,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/quantum", tags=["quantum"])


# Request/Response Models
class QuantumJobRequestModel(BaseModel):
    """Request for quantum computation."""

    job_type: str = Field(
        ..., description="Type of job: zkml_proof, circuit_optimize, anomaly_detect, security_audit"
    )
    circuit_data: Dict[str, Any] = Field(..., description="Quantum circuit or job specification")
    provider: Optional[str] = Field(None, description="Quantum provider: ibm, google, ionq, auto")
    VERIDICUS_payment: int = Field(..., description="VERIDICUS tokens to pay")
    VERIDICUS_staked: int = Field(0, description="VERIDICUS staked for priority")
    priority: str = Field("standard", description="Priority: standard, high, vip")
    user_address: str = Field(..., description="User's wallet address")


class QuantumJobResponse(BaseModel):
    """Response from quantum computation."""

    job_id: str
    result: Dict[str, Any]
    provider_used: str
    execution_time_ms: float
    VERIDICUS_burned: int
    cost_usd: float
    VERIDICUS_to_usd_rate: float


# Endpoints
@router.post("/execute", response_model=QuantumJobResponse)
async def execute_quantum_job(request: QuantumJobRequestModel):
    """
    Execute a quantum computing job via VERIDICUS payment.

    Job types:
    - zkml_proof: Accelerate zkML proof generation (10 VERIDICUS)
    - circuit_optimize: Optimize Circom circuit (5 VERIDICUS)
    - anomaly_detect: Quantum ML anomaly detection (20 VERIDICUS)
    - security_audit: Quantum security analysis (50 VERIDICUS)
    """
    try:
        gateway = get_quantum_gateway()

        # Convert provider string to enum
        provider = None
        if request.provider:
            try:
                provider = QuantumProvider[request.provider.upper()]
            except KeyError:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {request.provider}")

        # Create job request
        job_request = QuantumJobRequest(
            job_type=request.job_type,
            circuit=request.circuit_data,
            provider=provider,
            VERIDICUS_payment=request.VERIDICUS_payment,
            VERIDICUS_staked=request.VERIDICUS_staked,
            priority=request.priority,
            user_address=request.user_address,
        )

        # Execute job
        result = await gateway.execute_quantum_job(job_request)

        return QuantumJobResponse(
            job_id=result.job_id,
            result=result.result,
            provider_used=result.provider_used,
            execution_time_ms=result.execution_time_ms,
            VERIDICUS_burned=result.VERIDICUS_burned,
            cost_usd=result.cost_usd,
            VERIDICUS_to_usd_rate=result.VERIDICUS_to_usd_rate,
        )
    except Exception as e:
        logger.error(f"Error executing quantum job: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/zkml/accelerate")
async def accelerate_zkml_proof(
    agent_features: list[list[float]] = Body(..., description="Agent feature vectors"),
    threshold: float = Body(0.8, description="Anomaly threshold"),
    VERIDICUS_payment: int = Body(10, description="VERIDICUS tokens to pay"),
    VERIDICUS_staked: int = Body(0, description="VERIDICUS staked for priority"),
    priority: str = Body("standard", description="Priority level"),
    user_address: str = Body(..., description="User's wallet address"),
):
    """
    Generate zkML proof with quantum acceleration.

    Uses quantum computing to accelerate Groth16 proof generation.
    Costs 10 VERIDICUS tokens.
    """
    try:
        from quantum.zkml_quantum_acceleration import QuantumZKMLProver

        prover = QuantumZKMLProver()
        proof = await prover.prove_anomaly_threshold_quantum(
            agent_features=agent_features,
            threshold=threshold,
            VERIDICUS_payment=VERIDICUS_payment,
            VERIDICUS_staked=VERIDICUS_staked,
            priority=priority,
            user_address=user_address,
        )

        return proof
    except Exception as e:
        logger.error(f"Error in quantum zkML acceleration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/providers")
async def list_providers():
    """
    List available quantum computing providers.
    """
    providers = []

    # Check which providers are available
    gateway = get_quantum_gateway()

    if gateway.ibm_provider:
        providers.append(
            {
                "name": "IBM Quantum",
                "id": "ibm_quantum",
                "available": True,
                "description": "IBM Quantum Network access",
            }
        )

    if gateway.google_available:
        providers.append(
            {
                "name": "Google Quantum AI",
                "id": "google_quantum_ai",
                "available": True,
                "description": "Google Sycamore processor access",
            }
        )

    providers.append(
        {
            "name": "Simulator",
            "id": "simulator",
            "available": True,
            "description": "Quantum simulator (for testing)",
        }
    )

    return {"providers": providers, "default": "simulator"}


@router.get("/pricing")
async def get_pricing():
    """
    Get VERIDICUS pricing for quantum compute jobs.
    """
    return {
        "zkml_proof": {
            "cost_VERIDICUS": 10,
            "description": "Accelerate zkML proof generation",
            "estimated_time_ms": 50,
        },
        "circuit_optimize": {
            "cost_VERIDICUS": 5,
            "description": "Optimize Circom circuit",
            "estimated_time_ms": 30,
        },
        "anomaly_detect": {
            "cost_VERIDICUS": 20,
            "description": "Quantum ML anomaly detection",
            "estimated_time_ms": 100,
        },
        "security_audit": {
            "cost_VERIDICUS": 50,
            "description": "Quantum security analysis",
            "estimated_time_ms": 500,
        },
        "VERIDICUS_to_usd_rate": 0.10,  # Example rate
    }
