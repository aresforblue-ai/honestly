"""
Alert Service - Slack/Discord Webhooks
=======================================

Sends real-time alerts for anomaly detection events.

Supported channels:
- Slack (incoming webhooks)
- Discord (webhooks)
- Email (SMTP) - optional
- PagerDuty - optional

Configuration via environment variables:
- SLACK_WEBHOOK_URL
- DISCORD_WEBHOOK_URL
- ALERT_THRESHOLD (default: 0.8)
- ALERT_COOLDOWN (default: 300 seconds)

Usage:
    from api.alerts import AlertService, get_alert_service

    alerts = get_alert_service()
    await alerts.send_anomaly_alert(anomaly_data)
"""

import logging
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Optional

import aiohttp

logger = logging.getLogger(__name__)


@dataclass
class AlertConfig:
    """Alert configuration."""

    slack_webhook: Optional[str] = None
    discord_webhook: Optional[str] = None
    threshold: float = 0.8
    cooldown_seconds: int = 300  # 5 minutes between alerts for same agent
    enabled: bool = True


class AlertService:
    """
    Service for sending alerts to Slack/Discord.
    """

    def __init__(self, config: Optional[AlertConfig] = None):
        """Initialize alert service."""
        self.config = config or AlertConfig(
            slack_webhook=os.getenv("SLACK_WEBHOOK_URL"),
            discord_webhook=os.getenv("DISCORD_WEBHOOK_URL"),
            threshold=float(os.getenv("ALERT_THRESHOLD", "0.8")),
            cooldown_seconds=int(os.getenv("ALERT_COOLDOWN", "300")),
            enabled=os.getenv("ALERTS_ENABLED", "true").lower() == "true",
        )

        # Cooldown tracking: agent_id -> last_alert_time
        self._cooldowns: Dict[str, float] = {}
        self._stats = {
            "alerts_sent": 0,
            "alerts_suppressed": 0,
            "slack_errors": 0,
            "discord_errors": 0,
        }

    def _should_alert(self, agent_id: str) -> bool:
        """Check if we should send an alert (cooldown check)."""
        now = time.time()
        last_alert = self._cooldowns.get(agent_id, 0)

        if now - last_alert < self.config.cooldown_seconds:
            self._stats["alerts_suppressed"] += 1
            return False

        self._cooldowns[agent_id] = now
        return True

    def _format_slack_message(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Format anomaly as Slack message."""
        agent_id = anomaly.get("agent_id", "unknown")
        score = anomaly.get("anomaly_score", 0)
        flags = anomaly.get("flags", [])

        # Severity color
        if score > 0.9:
            color = "#FF0000"  # Red
            emoji = "🚨"
            severity = "CRITICAL"
        elif score > 0.8:
            color = "#FFA500"  # Orange
            emoji = "⚠️"
            severity = "WARNING"
        else:
            color = "#FFFF00"  # Yellow
            emoji = "📊"
            severity = "INFO"

        return {
            "attachments": [
                {
                    "color": color,
                    "blocks": [
                        {
                            "type": "header",
                            "text": {
                                "type": "plain_text",
                                "text": f"{emoji} Anomaly Detected - {severity}",
                            },
                        },
                        {
                            "type": "section",
                            "fields": [
                                {"type": "mrkdwn", "text": f"*Agent:*\n`{agent_id[:50]}`"},
                                {"type": "mrkdwn", "text": f"*Score:*\n{score:.2%}"},
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Flags:*\n{', '.join(flags) or 'none'}",
                                },
                                {
                                    "type": "mrkdwn",
                                    "text": f"*Time:*\n{datetime.now(timezone.utc).strftime('%H:%M:%S UTC')}",
                                },
                            ],
                        },
                        {
                            "type": "context",
                            "elements": [
                                {"type": "mrkdwn", "text": "Honestly AAIP | ML Anomaly Detection"}
                            ],
                        },
                    ],
                }
            ]
        }

    def _format_discord_message(self, anomaly: Dict[str, Any]) -> Dict[str, Any]:
        """Format anomaly as Discord message."""
        agent_id = anomaly.get("agent_id", "unknown")
        score = anomaly.get("anomaly_score", 0)
        flags = anomaly.get("flags", [])

        # Severity color (Discord uses decimal)
        if score > 0.9:
            color = 16711680  # Red
            emoji = "🚨"
            severity = "CRITICAL"
        elif score > 0.8:
            color = 16753920  # Orange
            emoji = "⚠️"
            severity = "WARNING"
        else:
            color = 16776960  # Yellow
            emoji = "📊"
            severity = "INFO"

        return {
            "embeds": [
                {
                    "title": f"{emoji} Anomaly Detected - {severity}",
                    "color": color,
                    "fields": [
                        {"name": "Agent", "value": f"`{agent_id[:50]}`", "inline": True},
                        {"name": "Score", "value": f"**{score:.2%}**", "inline": True},
                        {"name": "Flags", "value": ", ".join(flags) or "none", "inline": False},
                    ],
                    "footer": {"text": "Honestly AAIP | ML Anomaly Detection"},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            ]
        }

    async def send_slack(self, message: Dict[str, Any]) -> bool:
        """Send message to Slack webhook."""
        if not self.config.slack_webhook:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.slack_webhook,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status == 200:
                        return True
                    else:
                        logger.warning(f"Slack webhook returned {response.status}")
                        self._stats["slack_errors"] += 1
                        return False
        except Exception as e:
            logger.error(f"Slack webhook error: {e}")
            self._stats["slack_errors"] += 1
            return False

    async def send_discord(self, message: Dict[str, Any]) -> bool:
        """Send message to Discord webhook."""
        if not self.config.discord_webhook:
            return False

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.config.discord_webhook,
                    json=message,
                    timeout=aiohttp.ClientTimeout(total=10),
                ) as response:
                    if response.status in (200, 204):
                        return True
                    else:
                        logger.warning(f"Discord webhook returned {response.status}")
                        self._stats["discord_errors"] += 1
                        return False
        except Exception as e:
            logger.error(f"Discord webhook error: {e}")
            self._stats["discord_errors"] += 1
            return False

    async def send_anomaly_alert(
        self,
        anomaly: Dict[str, Any],
        force: bool = False,
    ) -> Dict[str, bool]:
        """
        Send anomaly alert to all configured channels.

        Args:
            anomaly: Anomaly data dict
            force: Skip cooldown check

        Returns:
            Dict of channel -> success status
        """
        if not self.config.enabled:
            return {"slack": False, "discord": False, "reason": "disabled"}

        score = anomaly.get("anomaly_score", 0)
        agent_id = anomaly.get("agent_id", "unknown")

        # Check threshold
        if score < self.config.threshold:
            return {"slack": False, "discord": False, "reason": "below_threshold"}

        # Check cooldown
        if not force and not self._should_alert(agent_id):
            return {"slack": False, "discord": False, "reason": "cooldown"}

        results = {}

        # Send to Slack
        if self.config.slack_webhook:
            slack_msg = self._format_slack_message(anomaly)
            results["slack"] = await self.send_slack(slack_msg)

        # Send to Discord
        if self.config.discord_webhook:
            discord_msg = self._format_discord_message(anomaly)
            results["discord"] = await self.send_discord(discord_msg)

        if any(results.values()):
            self._stats["alerts_sent"] += 1
            logger.info(f"Alert sent for agent {agent_id}: score={score:.2f}")

        return results

    async def send_batch_summary(
        self,
        summary: Dict[str, Any],
    ) -> Dict[str, bool]:
        """Send batch anomaly summary."""
        anomalous_count = summary.get("anomalous_count", 0)
        total = summary.get("total_agents", 0)

        if anomalous_count == 0:
            return {"slack": False, "discord": False, "reason": "no_anomalies"}

        # Create summary anomaly for alerting
        anomaly = {
            "agent_id": f"batch_{total}",
            "anomaly_score": anomalous_count / total if total > 0 else 0,
            "flags": [f"{anomalous_count}_anomalous"],
        }

        return await self.send_anomaly_alert(anomaly, force=True)

    def get_stats(self) -> Dict[str, Any]:
        """Get alert statistics."""
        return {
            **self._stats,
            "config": {
                "threshold": self.config.threshold,
                "cooldown_seconds": self.config.cooldown_seconds,
                "slack_configured": bool(self.config.slack_webhook),
                "discord_configured": bool(self.config.discord_webhook),
                "enabled": self.config.enabled,
            },
            "active_cooldowns": len(self._cooldowns),
        }

    def clear_cooldowns(self):
        """Clear all cooldowns (for testing)."""
        self._cooldowns.clear()


# Singleton instance
_alert_service: Optional[AlertService] = None


def get_alert_service() -> AlertService:
    """Get the global alert service."""
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service


# Integration with anomaly detection
async def alert_on_anomaly(anomaly: Dict[str, Any]) -> Dict[str, bool]:
    """
    Convenience function to send alert for an anomaly.

    Called from ml_router after anomaly detection.
    """
    alerts = get_alert_service()
    return await alerts.send_anomaly_alert(anomaly)
