"""
Agent Configuration System
==========================

YAML/JSON configuration system for AAIP agents, inspired by BMad Method.
Enables defining agent personas, activations, and commands in configuration files.
"""

import yaml
import json
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from identity.swarm_orchestrator import (
    AgentPersona,
    AgentActivation,
    AgentCommand,
    SwarmOrchestrator,
)

logger = logging.getLogger("identity.agent_config")


class AgentConfigLoader:
    """Load agent configurations from YAML/JSON files."""

    @staticmethod
    def load_from_yaml(file_path: str) -> Dict[str, Any]:
        """Load agent configuration from YAML file."""
        with open(file_path, "r") as f:
            return yaml.safe_load(f)

    @staticmethod
    def load_from_json(file_path: str) -> Dict[str, Any]:
        """Load agent configuration from JSON file."""
        with open(file_path, "r") as f:
            return json.load(f)

    @staticmethod
    def parse_persona(config: Dict[str, Any]) -> AgentPersona:
        """Parse persona from configuration."""
        persona_data = config.get("persona", {})

        return AgentPersona(
            role=persona_data.get("role", ""),
            identity=persona_data.get("identity", ""),
            communication_style=persona_data.get("communication_style", ""),
            principles=persona_data.get("principles", []),
            memories=persona_data.get("memories", []),
            icon=persona_data.get("icon", "🤖"),
        )

    @staticmethod
    def parse_activation(config: Dict[str, Any]) -> Optional[AgentActivation]:
        """Parse activation from configuration."""
        if "activation" not in config:
            return None

        activation_data = config.get("activation", {})

        return AgentActivation(
            steps=activation_data.get("steps", []),
            critical_actions=activation_data.get("critical_actions", []),
            menu=activation_data.get("menu", []),
            prompts=activation_data.get("prompts", []),
        )

    @staticmethod
    def parse_commands(config: Dict[str, Any]) -> List[AgentCommand]:
        """Parse commands from configuration."""
        commands = []
        menu = config.get("menu", [])

        for item in menu:
            # Support both BMad-style and simplified formats
            if isinstance(item, dict):
                trigger = item.get("trigger", item.get("cmd", ""))
                action = item.get("action", item.get("exec", item.get("workflow", "")))
                description = item.get("description", "")
                handler_type = item.get("handler_type", "action")
                params = item.get("params", {})

                commands.append(
                    AgentCommand(
                        trigger=trigger,
                        action=action,
                        description=description,
                        handler_type=handler_type,
                        params=params,
                    )
                )

        return commands

    @staticmethod
    def load_and_register(
        config_path: str,
        agent_id: str,
        orchestrator: SwarmOrchestrator,
    ) -> bool:
        """
        Load configuration file and register with orchestrator.

        Args:
            config_path: Path to YAML/JSON config file
            agent_id: AAIP agent ID to register for
            orchestrator: Swarm orchestrator instance

        Returns:
            True if successful
        """
        try:
            # Load config
            if config_path.endswith(".yaml") or config_path.endswith(".yml"):
                config = AgentConfigLoader.load_from_yaml(config_path)
            elif config_path.endswith(".json"):
                config = AgentConfigLoader.load_from_json(config_path)
            else:
                logger.error(f"Unsupported config format: {config_path}")
                return False

            # Parse components
            persona = AgentConfigLoader.parse_persona(config)
            activation = AgentConfigLoader.parse_activation(config)
            commands = AgentConfigLoader.parse_commands(config)

            # Register with orchestrator
            return orchestrator.register_agent_persona(
                agent_id=agent_id,
                persona=persona,
                activation=activation,
                commands=commands if commands else None,
            )
        except Exception as e:
            logger.error(f"Error loading agent config: {e}")
            return False


def load_agent_configs_from_directory(
    directory: str,
    orchestrator: SwarmOrchestrator,
) -> Dict[str, bool]:
    """
    Load all agent configurations from a directory.

    Args:
        directory: Directory containing agent config files
        orchestrator: Swarm orchestrator instance

    Returns:
        Dict mapping agent_id to success status
    """
    results = {}
    dir_path = Path(directory)

    if not dir_path.exists():
        logger.warning(f"Config directory does not exist: {directory}")
        return results

    # Find all YAML/JSON files
    config_files = (
        list(dir_path.glob("*.yaml")) + list(dir_path.glob("*.yml")) + list(dir_path.glob("*.json"))
    )

    for config_file in config_files:
        # Try to extract agent_id from filename or config
        try:
            config = (
                AgentConfigLoader.load_from_yaml(str(config_file))
                if config_file.suffix in [".yaml", ".yml"]
                else AgentConfigLoader.load_from_json(str(config_file))
            )

            # Look for agent_id in config
            agent_id = None
            if "agent" in config and "metadata" in config.get("agent", {}):
                agent_id = config["agent"]["metadata"].get("id")

            # If not found, try to match with registered agents
            if not agent_id:
                # Extract from filename or use registry lookup
                # For now, skip files without explicit agent_id
                logger.warning(f"No agent_id found in {config_file}, skipping")
                continue

            # Load and register
            success = AgentConfigLoader.load_and_register(
                str(config_file),
                agent_id,
                orchestrator,
            )

            results[agent_id] = success
        except Exception as e:
            logger.error(f"Error processing {config_file}: {e}")
            continue

    return results
