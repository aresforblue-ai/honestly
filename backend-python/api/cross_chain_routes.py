"""
Cross-Chain Anomaly Federation API Routes
=========================================

REST endpoints for Phase 4: Cross-Chain Anomaly Federation.
"""

import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel, Field

from api.cross_chain_reporter import (
    AnomalyResult,
    get_reporter,
)
from api.cross_chain_integration import (
    get_integration,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cross-chain", tags=["cross-chain"])


# Request/Response Models
class ReportAnomalyRequest(BaseModel):
    """Request to report an anomaly cross-chain."""

    agent_id: str = Field(..., description="Agent DID or ID")
    anomaly_score: float = Field(..., ge=0.0, le=1.0, description="Anomaly score (0.0-1.0)")
    threshold: float = Field(..., ge=0.0, le=1.0, description="Detection threshold")
    flags: List[str] = Field(default=[], description="Anomaly flags")
    zkml_proof: str = Field(..., description="Base64 encoded zkML proof")
    zkml_proof_hash: str = Field(..., description="Hash of zkML proof")
    chain_id: int = Field(1, description="Source chain ID")


class VAAStatusRequest(BaseModel):
    """Request to check VAA status."""

    vaa_hash: str = Field(..., description="VAA hash")


# Endpoints
@router.post("/anomaly/report")
async def report_anomaly(request: ReportAnomalyRequest):
    """
    Report an anomaly for cross-chain propagation via Wormhole.

    This packages the anomaly into a Wormhole VAA and submits it
    to the bridge for guardian signatures.
    """
    try:
        reporter = get_reporter(chain_id=request.chain_id)

        # Decode zkML proof
        import base64

        zkml_proof_bytes = base64.b64decode(request.zkml_proof)

        # Create anomaly result
        anomaly = AnomalyResult(
            agent_id=request.agent_id,
            anomaly_score=request.anomaly_score,
            threshold=request.threshold,
            flags=request.flags,
            zkml_proof=zkml_proof_bytes,
            zkml_proof_hash=request.zkml_proof_hash,
        )

        # Report to Wormhole
        result = await reporter.report_anomaly(anomaly, zkml_proof_bytes)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error", "Report failed"))

        return result
    except Exception as e:
        logger.error(f"Error reporting anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/vaa/{vaa_hash}/status")
async def get_vaa_status(vaa_hash: str):
    """
    Get status of a Wormhole VAA.

    Returns guardian signature count and finalization status.
    """
    try:
        reporter = get_reporter()
        status = reporter.get_vaa_status(vaa_hash)
        return status
    except Exception as e:
        logger.error(f"Error getting VAA status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/oracle/validate")
async def validate_anomaly(
    vaa: str = Body(..., description="Base64 encoded VAA"),
    zkml_proof: str = Body(..., description="Base64 encoded zkML proof"),
    public_inputs: List[int] = Body(..., description="Public inputs to zkML circuit"),
):
    """
    Validate a VAA and zkML proof (oracle endpoint).

    This is called by Chainlink oracle nodes to validate anomalies
    before writing to the registry.
    """
    try:
        # In production, this would:
        # 1. Parse VAA
        # 2. Verify guardian signatures
        # 3. Verify zkML proof
        # 4. Vote on oracle consensus

        # For now, return mock validation
        return {
            "success": True,
            "vaa_valid": True,
            "zkml_valid": True,
            "votes": 1,
            "quorum": 3,
        }
    except Exception as e:
        logger.error(f"Error validating anomaly: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/anomaly/detect-and-report")
async def detect_and_report_anomaly(
    agent_id: str = Body(..., description="Agent ID or DID"),
    proof_data: Dict[str, Any] = Body(..., description="Proof data for analysis"),
    proof_type: str = Body("agent_reputation", description="Type of proof"),
):
    """
    Detect anomaly using ML and automatically report cross-chain if anomalous.

    This integrates the existing ML anomaly detection with Phase 4 cross-chain federation.
    """
    try:
        integration = get_integration()
        result = await integration.detect_and_report(
            agent_id=agent_id,
            proof_data=proof_data,
            proof_type=proof_type,
        )
        return result
    except Exception as e:
        logger.error(f"Error in detect_and_report: {e}")
        raise HTTPException(status_code=500, detail=str(e))
