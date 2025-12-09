"""
LSTM Autoencoder for Agent Anomaly Detection
=============================================

Unsupervised anomaly detection on agent reputation time series.
Reconstructs "normal" agent behavior patterns; high reconstruction
error indicates anomalous activity (gaming, sybil attacks, etc.)

Architecture:
- LSTM Encoder: Compresses agent activity sequences
- LSTM Decoder: Reconstructs sequences
- Anomaly score: Mean squared reconstruction error

Integration:
- Training data: Neo4j agent/claim graph
- Inference: Real-time during /ai/verify-proof
- zkML: Export to ONNX → DeepProve for verifiable inference

Usage:
    from ml.autoencoder import AgentAutoencoder, get_autoencoder

    model = get_autoencoder()
    anomaly_score = model.detect_anomaly(agent_features)
    # Returns 0.0-1.0 (higher = more anomalous)
"""

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# Try to import PyTorch
try:
    import torch
    import torch.nn as nn
    from torch.utils.data import DataLoader, TensorDataset

    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logger.warning("PyTorch not available, using statistical fallback")

# Try to import numpy
try:
    import numpy as np  # noqa: F401

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


@dataclass
class AnomalyResult:
    """Result of autoencoder anomaly detection."""

    anomaly_score: float  # 0.0 (normal) to 1.0 (anomalous)
    reconstruction_error: float  # Raw MSE
    threshold: float  # Current anomaly threshold
    is_anomalous: bool
    latent_vector: Optional[List[float]] = None  # Compressed representation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "anomaly_score": round(self.anomaly_score, 4),
            "reconstruction_error": round(self.reconstruction_error, 6),
            "threshold": round(self.threshold, 4),
            "is_anomalous": self.is_anomalous,
        }


if TORCH_AVAILABLE:

    class LSTMEncoder(nn.Module):
        """LSTM Encoder - compresses sequences to latent space."""

        def __init__(
            self,
            input_size: int = 8,
            hidden_size: int = 32,
            latent_size: int = 16,
            num_layers: int = 2,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
            )
            self.fc = nn.Linear(hidden_size, latent_size)

        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            # x: (batch, seq_len, input_size)
            _, (hidden, _) = self.lstm(x)
            # hidden: (num_layers, batch, hidden_size)
            latent = self.fc(hidden[-1])  # Use last layer
            return latent, hidden

    class LSTMDecoder(nn.Module):
        """LSTM Decoder - reconstructs sequences from latent space."""

        def __init__(
            self,
            latent_size: int = 16,
            hidden_size: int = 32,
            output_size: int = 8,
            num_layers: int = 2,
            dropout: float = 0.1,
        ):
            super().__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers

            self.fc = nn.Linear(latent_size, hidden_size)
            self.lstm = nn.LSTM(
                input_size=hidden_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout if num_layers > 1 else 0,
            )
            self.output = nn.Linear(hidden_size, output_size)

        def forward(
            self,
            latent: torch.Tensor,
            seq_len: int,
        ) -> torch.Tensor:
            # latent: (batch, latent_size)
            _ = latent.size(0)  # batch_size for validation

            # Expand latent to sequence
            hidden = self.fc(latent)
            hidden = hidden.unsqueeze(1).repeat(1, seq_len, 1)

            # Decode
            output, _ = self.lstm(hidden)
            output = self.output(output)
            return output

    class AgentAutoencoder(nn.Module):
        """
        LSTM Autoencoder for agent activity anomaly detection.

        Input features (per timestep):
        - reputation_score: Current rep (0-100)
        - claim_count: Claims in period
        - proof_count: Proofs generated
        - interaction_count: Agent interactions
        - hour_of_day: Time feature (0-23)
        - day_of_week: Day feature (0-6)
        - response_time_avg: Avg response time
        - error_rate: Error rate in period
        """

        def __init__(
            self,
            input_size: int = 8,
            hidden_size: int = 32,
            latent_size: int = 16,
            num_layers: int = 2,
            dropout: float = 0.1,
            anomaly_threshold: float = 0.1,
        ):
            super().__init__()
            self.input_size = input_size
            self.latent_size = latent_size
            self.anomaly_threshold = anomaly_threshold

            self.encoder = LSTMEncoder(
                input_size=input_size,
                hidden_size=hidden_size,
                latent_size=latent_size,
                num_layers=num_layers,
                dropout=dropout,
            )
            self.decoder = LSTMDecoder(
                latent_size=latent_size,
                hidden_size=hidden_size,
                output_size=input_size,
                num_layers=num_layers,
                dropout=dropout,
            )

            # Running stats for normalization
            self.register_buffer("running_mean", torch.zeros(input_size))
            self.register_buffer("running_std", torch.ones(input_size))
            self.register_buffer("error_mean", torch.tensor(0.0))
            self.register_buffer("error_std", torch.tensor(1.0))

        def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
            """Forward pass - encode and decode."""
            seq_len = x.size(1)
            latent, _ = self.encoder(x)
            reconstructed = self.decoder(latent, seq_len)
            return reconstructed, latent

        def compute_reconstruction_error(
            self,
            x: torch.Tensor,
            reconstructed: torch.Tensor,
        ) -> torch.Tensor:
            """Compute per-sample reconstruction error (MSE)."""
            # MSE per sample
            error = torch.mean((x - reconstructed) ** 2, dim=(1, 2))
            return error

        def normalize_features(self, x: torch.Tensor) -> torch.Tensor:
            """Normalize input features using running stats."""
            return (x - self.running_mean) / (self.running_std + 1e-8)

        def error_to_anomaly_score(self, error: torch.Tensor) -> torch.Tensor:
            """Convert reconstruction error to 0-1 anomaly score."""
            # Z-score normalization of error
            z_score = (error - self.error_mean) / (self.error_std + 1e-8)
            # Sigmoid to bound 0-1
            score = torch.sigmoid(z_score)
            return score

        @torch.no_grad()
        def detect_anomaly(
            self,
            features: List[List[float]],
            return_latent: bool = False,
        ) -> AnomalyResult:
            """
            Detect anomaly in agent activity sequence.

            Args:
                features: List of feature vectors (sequence of timesteps)
                return_latent: Whether to return latent representation

            Returns:
                AnomalyResult with score and metadata
            """
            self.eval()

            # Convert to tensor
            x = torch.tensor([features], dtype=torch.float32)

            # Normalize
            x_norm = self.normalize_features(x)

            # Forward pass
            reconstructed, latent = self.forward(x_norm)

            # Compute error
            error = self.compute_reconstruction_error(x_norm, reconstructed)

            # Convert to anomaly score
            score = self.error_to_anomaly_score(error)

            return AnomalyResult(
                anomaly_score=score.item(),
                reconstruction_error=error.item(),
                threshold=self.anomaly_threshold,
                is_anomalous=score.item() > self.anomaly_threshold,
                latent_vector=latent[0].tolist() if return_latent else None,
            )

        def fit(
            self,
            train_data: List[List[List[float]]],
            epochs: int = 50,
            batch_size: int = 32,
            learning_rate: float = 0.001,
            validation_split: float = 0.1,
        ) -> Dict[str, List[float]]:
            """
            Train the autoencoder on normal agent data.

            Args:
                train_data: List of sequences, each sequence is list of feature vectors
                epochs: Training epochs
                batch_size: Batch size
                learning_rate: Learning rate
                validation_split: Fraction for validation

            Returns:
                Training history (loss per epoch)
            """
            self.train()

            # Convert to tensor
            X = torch.tensor(train_data, dtype=torch.float32)

            # Update running stats
            self.running_mean = X.mean(dim=(0, 1))
            self.running_std = X.std(dim=(0, 1))

            # Normalize
            X_norm = self.normalize_features(X)

            # Split train/val
            n_val = int(len(X_norm) * validation_split)
            indices = torch.randperm(len(X_norm))
            val_indices = indices[:n_val]
            train_indices = indices[n_val:]

            X_train = X_norm[train_indices]
            X_val = X_norm[val_indices] if n_val > 0 else None

            # DataLoader
            train_dataset = TensorDataset(X_train, X_train)
            train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)

            # Optimizer
            optimizer = torch.optim.Adam(self.parameters(), lr=learning_rate)
            criterion = nn.MSELoss()

            history = {"train_loss": [], "val_loss": []}

            for epoch in range(epochs):
                # Training
                self.train()
                train_losses = []
                for batch_x, _ in train_loader:
                    optimizer.zero_grad()
                    reconstructed, _ = self.forward(batch_x)
                    loss = criterion(reconstructed, batch_x)
                    loss.backward()
                    optimizer.step()
                    train_losses.append(loss.item())

                avg_train_loss = sum(train_losses) / len(train_losses)
                history["train_loss"].append(avg_train_loss)

                # Validation
                if X_val is not None:
                    self.eval()
                    with torch.no_grad():
                        reconstructed, _ = self.forward(X_val)
                        val_loss = criterion(reconstructed, X_val).item()
                        history["val_loss"].append(val_loss)

                if (epoch + 1) % 10 == 0:
                    logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {avg_train_loss:.6f}")

            # Compute error statistics on training data
            self.eval()
            with torch.no_grad():
                reconstructed, _ = self.forward(X_train)
                errors = self.compute_reconstruction_error(X_train, reconstructed)
                self.error_mean = errors.mean()
                self.error_std = errors.std()

            return history

        def export_onnx(self, path: Path, seq_len: int = 10) -> None:
            """
            Export model to ONNX format for zkML (DeepProve).

            Args:
                path: Output path for .onnx file
                seq_len: Sequence length for export
            """
            self.eval()
            dummy_input = torch.randn(1, seq_len, self.input_size)

            torch.onnx.export(
                self,
                dummy_input,
                str(path),
                export_params=True,
                opset_version=11,
                do_constant_folding=True,
                input_names=["input"],
                output_names=["reconstructed", "latent"],
                dynamic_axes={
                    "input": {0: "batch_size"},
                    "reconstructed": {0: "batch_size"},
                    "latent": {0: "batch_size"},
                },
            )
            logger.info(f"Exported ONNX model to {path}")


class StatisticalAutoencoder:
    """
    Statistical fallback when PyTorch is not available.
    Uses simple reconstruction via PCA-like approach.
    """

    def __init__(self, anomaly_threshold: float = 0.7):
        self.anomaly_threshold = anomaly_threshold
        self.mean: Optional[List[float]] = None
        self.std: Optional[List[float]] = None
        self.components: Optional[List[List[float]]] = None
        self.n_components = 4
        self.error_mean = 0.0
        self.error_std = 1.0

    def detect_anomaly(
        self,
        features: List[List[float]],
        return_latent: bool = False,
    ) -> AnomalyResult:
        """Detect anomaly using statistical methods."""
        if self.mean is None:
            # Not trained - use simple heuristics
            flat = [f for step in features for f in step]
            mean_val = sum(flat) / len(flat) if flat else 0
            variance = sum((x - mean_val) ** 2 for x in flat) / len(flat) if flat else 0

            # High variance = potential anomaly
            score = min(1.0, variance / 100)

            return AnomalyResult(
                anomaly_score=score,
                reconstruction_error=variance,
                threshold=self.anomaly_threshold,
                is_anomalous=score > self.anomaly_threshold,
            )

        # Normalize and compute error
        normalized = []
        for step in features:
            norm_step = [(step[i] - self.mean[i]) / (self.std[i] + 1e-8) for i in range(len(step))]
            normalized.append(norm_step)

        # Simple reconstruction error (distance from mean)
        errors = []
        for step in normalized:
            step_error = sum(x**2 for x in step) / len(step)
            errors.append(step_error)

        avg_error = sum(errors) / len(errors)
        z_score = (avg_error - self.error_mean) / (self.error_std + 1e-8)
        score = 1 / (1 + 2.718 ** (-z_score))  # Sigmoid

        return AnomalyResult(
            anomaly_score=score,
            reconstruction_error=avg_error,
            threshold=self.anomaly_threshold,
            is_anomalous=score > self.anomaly_threshold,
        )

    def fit(
        self,
        train_data: List[List[List[float]]],
        **kwargs,
    ) -> Dict[str, List[float]]:
        """Fit statistical model."""
        if not train_data:
            return {"train_loss": []}

        # Flatten to compute stats
        all_features = []
        for seq in train_data:
            for step in seq:
                all_features.append(step)

        n_features = len(all_features[0]) if all_features else 8

        # Compute mean and std per feature
        self.mean = [0.0] * n_features
        self.std = [1.0] * n_features

        for i in range(n_features):
            values = [f[i] for f in all_features]
            self.mean[i] = sum(values) / len(values)
            variance = sum((x - self.mean[i]) ** 2 for x in values) / len(values)
            self.std[i] = variance**0.5

        # Compute error stats
        errors = []
        for seq in train_data:
            result = self.detect_anomaly(seq)
            errors.append(result.reconstruction_error)

        self.error_mean = sum(errors) / len(errors)
        variance = sum((e - self.error_mean) ** 2 for e in errors) / len(errors)
        self.error_std = variance**0.5

        return {"train_loss": [self.error_mean]}


# Factory function
def create_autoencoder(
    input_size: int = 8,
    hidden_size: int = 32,
    latent_size: int = 16,
    anomaly_threshold: float = 0.7,
) -> Any:
    """Create appropriate autoencoder based on available libraries."""
    if TORCH_AVAILABLE:
        return AgentAutoencoder(
            input_size=input_size,
            hidden_size=hidden_size,
            latent_size=latent_size,
            anomaly_threshold=anomaly_threshold,
        )
    else:
        return StatisticalAutoencoder(anomaly_threshold=anomaly_threshold)


# Singleton
_autoencoder: Optional[Any] = None


def get_autoencoder() -> Any:
    """Get global autoencoder instance."""
    global _autoencoder
    if _autoencoder is None:
        model_path = Path(os.environ.get("AUTOENCODER_MODEL_PATH", ""))

        _autoencoder = create_autoencoder()

        if TORCH_AVAILABLE and model_path.exists():
            try:
                _autoencoder.load_state_dict(torch.load(model_path))
                logger.info(f"Loaded autoencoder from {model_path}")
            except Exception as e:
                logger.error(f"Failed to load autoencoder: {e}")

    return _autoencoder
