"""
Quantum Computing Module
========================

VERIDICUS-powered quantum computing access for Honestly protocol.
"""

from quantum.quantum_gateway import (
    VERIDICUSQuantumGateway,
    QuantumJobRequest,
    QuantumJobResult,
    QuantumProvider,
    get_quantum_gateway,
)

from quantum.zkml_quantum_acceleration import (
    QuantumZKMLProver,
)

__all__ = [
    "VERIDICUSQuantumGateway",
    "QuantumJobRequest",
    "QuantumJobResult",
    "QuantumProvider",
    "get_quantum_gateway",
    "QuantumZKMLProver",
]
