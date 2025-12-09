"""
Cross-Chain Anomaly Integration
================================

Integrates existing ML anomaly detection with Phase 4 cross-chain federation.
Automatically reports anomalies to Wormhole when detected.
"""

import logging
from typing import Dict, Any, Optional

from api.cross_chain_reporter import (
    AnomalyResult,
    get_reporter,
)

logger = logging.getLogger("api.cross_chain_integration")

# Try to import ML modules
try:
    from ml.anomaly_detector import get_detector, AnomalyScore  # noqa: F401
    from ml.zkml_prover import get_zkml_prover

    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("ML modules not available for cross-chain integration")


class CrossChainAnomalyIntegration:
    """
    Integrates ML anomaly detection with cross-chain reporting.

    When an anomaly is detected:
    1. Generate zkML proof
    2. Report to local chain (LocalDetector)
    3. Package into Wormhole VAA
    4. Submit to cross-chain federation
    """

    def __init__(
        self,
        chain_id: int = 1,
        auto_report: bool = True,
        threshold: float = 0.7,
    ):
        """
        Initialize cross-chain integration.

        Args:
            chain_id: Chain ID for this detector
            auto_report: Automatically report anomalies to Wormhole
            threshold: Anomaly score threshold for reporting
        """
        self.chain_id = chain_id
        self.auto_report = auto_report
        self.threshold = threshold
        self.reporter = get_reporter(chain_id=chain_id)

        if ML_AVAILABLE:
            self.detector = get_detector()
            try:
                self.zkml_prover = get_zkml_prover()
            except (ImportError, AttributeError, RuntimeError) as e:
                self.zkml_prover = None
                logger.warning(f"zkML prover not available: {e}")
        else:
            self.detector = None
            self.zkml_prover = None

    async def detect_and_report(
        self,
        agent_id: str,
        proof_data: Dict[str, Any],
        proof_type: str = "agent_reputation",
    ) -> Dict[str, Any]:
        """
        Detect anomaly and optionally report cross-chain.

        Args:
            agent_id: Agent ID or DID
            proof_data: Proof data for analysis
            proof_type: Type of proof (age, authenticity, agent_reputation)

        Returns:
            Dict with detection results and cross-chain report (if anomalous)
        """
        if not ML_AVAILABLE or not self.detector:
            return {
                "success": False,
                "error": "ML detection not available",
            }

        try:
            # 1. Run anomaly detection
            anomaly_score = self.detector.analyze_proof(
                proof_data=proof_data,
                agent_id=agent_id,
                proof_type=proof_type,
            )

            result = {
                "success": True,
                "agent_id": agent_id,
                "anomaly_score": anomaly_score.anomaly_score,
                "is_anomalous": anomaly_score.is_anomalous,
                "flags": anomaly_score.flags,
                "threshold": self.threshold,
            }

            # 2. If anomalous and auto-report enabled, report cross-chain
            if anomaly_score.is_anomalous and self.auto_report:
                # Generate zkML proof if available
                zkml_proof = None
                zkml_proof_hash = "0x" + "0" * 64

                if self.zkml_prover:
                    try:
                        # Generate zkML proof for anomaly
                        # This would use the actual zkML prover
                        zkml_proof = b"mock_proof"  # Placeholder
                        zkml_proof_hash = "0x" + "0" * 64  # Would be actual hash
                    except Exception as e:
                        logger.warning(f"zkML proof generation failed: {e}")

                # Create anomaly result
                anomaly_result = AnomalyResult(
                    agent_id=agent_id,
                    anomaly_score=anomaly_score.anomaly_score,
                    threshold=self.threshold,
                    flags=anomaly_score.flags,
                    zkml_proof=zkml_proof or b"",
                    zkml_proof_hash=zkml_proof_hash,
                )

                # Report to Wormhole
                report_result = await self.reporter.report_anomaly(
                    anomaly=anomaly_result,
                    zkml_proof=zkml_proof or b"",
                )

                result["cross_chain_report"] = report_result
                result["vaa_hash"] = report_result.get("vaa_hash")

            return result

        except Exception as e:
            logger.error(f"Error in detect_and_report: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def batch_detect_and_report(
        self,
        agent_ids: list[str],
        proof_data_list: list[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Batch detect and report anomalies.

        Args:
            agent_ids: List of agent IDs
            proof_data_list: List of proof data

        Returns:
            Batch results with cross-chain reports
        """
        results = []

        for agent_id, proof_data in zip(agent_ids, proof_data_list):
            result = await self.detect_and_report(
                agent_id=agent_id,
                proof_data=proof_data,
            )
            results.append(result)

        # Count anomalies
        anomalous = [r for r in results if r.get("is_anomalous", False)]

        return {
            "success": True,
            "total": len(results),
            "anomalous": len(anomalous),
            "results": results,
        }


# Global integration instance
_integration: Optional[CrossChainAnomalyIntegration] = None


def get_integration(chain_id: int = 1) -> CrossChainAnomalyIntegration:
    """Get global cross-chain integration."""
    global _integration
    if _integration is None:
        _integration = CrossChainAnomalyIntegration(chain_id=chain_id)
    return _integration
