"""
AAIP Swarm Orchestrator
=======================

A sophisticated orchestration system for AI agent swarms, inspired by BMad Method.
Enables capability-based agent summoning, multi-agent collaboration, and workflow execution.

Key Features:
- Capability-based agent discovery and summoning
- Multi-agent collaboration protocols
- Workflow execution with agent coordination
- Agent persona/activation system
- Party mode (all agents collaborate simultaneously)
"""

import json
import hashlib
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime

from identity.ai_agent_protocol import (
    AIAgentRegistry,
    AgentIdentity,
    get_registry,
)

logger = logging.getLogger("identity.swarm")


class AgentRole(Enum):
    """Agent roles in the swarm."""

    ORCHESTRATOR = "orchestrator"
    EXECUTOR = "executor"
    ANALYST = "analyst"
    ARCHITECT = "architect"
    DEVELOPER = "developer"
    TESTER = "tester"
    WRITER = "writer"
    DESIGNER = "designer"
    REVIEWER = "reviewer"
    COORDINATOR = "coordinator"


class CollaborationMode(Enum):
    """Modes of agent collaboration."""

    SEQUENTIAL = "sequential"  # Agents work one after another
    PARALLEL = "parallel"  # Agents work simultaneously
    PARTY = "party"  # All agents collaborate in group chat
    WORKFLOW = "workflow"  # Agents follow structured workflow


@dataclass
class AgentPersona:
    """Agent persona configuration (inspired by BMad Method)."""

    role: str
    identity: str
    communication_style: str
    principles: List[str] = field(default_factory=list)
    memories: List[str] = field(default_factory=list)
    icon: str = "🤖"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentPersona":
        return cls(**data)


@dataclass
class AgentActivation:
    """Agent activation instructions (how agent initializes)."""

    steps: List[Dict[str, Any]] = field(default_factory=list)
    critical_actions: List[str] = field(default_factory=list)
    menu: List[Dict[str, Any]] = field(default_factory=list)
    prompts: List[Dict[str, str]] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentActivation":
        return cls(**data)


@dataclass
class AgentCommand:
    """A command that an agent can execute."""

    trigger: str
    action: str  # workflow, exec, action, data, tmpl
    description: str
    handler_type: str = "action"  # workflow, exec, action, data, tmpl, validate-workflow
    params: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class SummonRequest:
    """Request to summon agents for a task."""

    task_description: str
    required_capabilities: List[str]
    preferred_agents: List[str] = field(default_factory=list)
    collaboration_mode: CollaborationMode = CollaborationMode.SEQUENTIAL
    max_agents: int = 5
    context: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            **asdict(self),
            "collaboration_mode": self.collaboration_mode.value,
        }


@dataclass
class AgentResponse:
    """Response from an agent."""

    agent_id: str
    agent_name: str
    response: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict:
        return asdict(self)


class SwarmOrchestrator:
    """
    Master orchestrator for AAIP agent swarms.

    Inspired by BMad Method's orchestrator pattern, but integrated with AAIP:
    - Agents are registered via AAIP (have DIDs, capabilities, reputation)
    - Summoning is capability-based
    - Collaboration maintains agent identity
    - Human authorization via ConductMe Trust Bridge
    """

    def __init__(
        self,
        registry: Optional[AIAgentRegistry] = None,
        redis_url: Optional[str] = None,
    ):
        """
        Initialize the swarm orchestrator.

        Args:
            registry: AAIP agent registry (uses global if None)
            redis_url: Optional Redis URL for persistence
        """
        self.registry = registry or get_registry(redis_url=redis_url)

        # Agent persona/activation storage
        self.agent_personas: Dict[str, AgentPersona] = {}
        self.agent_activations: Dict[str, AgentActivation] = {}
        self.agent_commands: Dict[str, List[AgentCommand]] = {}

        # Active collaborations
        self.active_collaborations: Dict[str, Dict[str, Any]] = {}

        # Workflow execution state
        self.workflow_state: Dict[str, Any] = {}

        logger.info("Swarm Orchestrator initialized")

    def register_agent_persona(
        self,
        agent_id: str,
        persona: AgentPersona,
        activation: Optional[AgentActivation] = None,
        commands: Optional[List[AgentCommand]] = None,
    ) -> bool:
        """
        Register persona and activation for an AAIP agent.

        This extends the agent's AAIP identity with BMad-style persona/activation.

        Args:
            agent_id: The AAIP agent ID
            persona: Agent persona configuration
            activation: Agent activation instructions
            commands: List of commands the agent can execute

        Returns:
            True if successful
        """
        # Verify agent exists in registry
        agent = self.registry.get_agent(agent_id)
        if not agent:
            logger.error(f"Agent {agent_id} not found in AAIP registry")
            return False

        self.agent_personas[agent_id] = persona
        if activation:
            self.agent_activations[agent_id] = activation
        if commands:
            self.agent_commands[agent_id] = commands

        logger.info(f"Registered persona for agent {agent_id} ({agent.agent_name})")
        return True

    def summon_agents(
        self,
        request: SummonRequest,
        human_identity: Optional[str] = None,  # Semaphore commitment for authorization
    ) -> Dict[str, Any]:
        """
        Summon agents based on capability requirements.

        This is the core "summoning" mechanism - finds agents that can help
        with the task and coordinates their collaboration.

        Args:
            request: Summon request with task and requirements
            human_identity: Optional human Semaphore commitment (for authorization)

        Returns:
            Dict with summoned agents and collaboration setup
        """
        # Find agents with required capabilities
        candidates = self._find_agents_by_capabilities(
            request.required_capabilities,
            request.preferred_agents,
        )

        # Select best agents (consider reputation, availability)
        selected = self._select_agents(
            candidates,
            request.max_agents,
            request.context,
        )

        if not selected:
            return {
                "success": False,
                "error": "No suitable agents found",
                "required_capabilities": request.required_capabilities,
            }

        # Create collaboration session
        collaboration_id = f"collab_{hashlib.sha256(json.dumps({
            'task': request.task_description,
            'agents': [a.agent_id for a in selected],
            'timestamp': datetime.utcnow().isoformat(),
        }).encode()).hexdigest()[:16]}"

        collaboration = {
            "id": collaboration_id,
            "task": request.task_description,
            "agents": [a.agent_id for a in selected],
            "agent_details": [a.to_dict() for a in selected],
            "mode": request.collaboration_mode.value,
            "human_identity": human_identity,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "context": request.context,
        }

        self.active_collaborations[collaboration_id] = collaboration

        logger.info(
            f"Summoned {len(selected)} agents for collaboration {collaboration_id}: "
            f"{[a.agent_name for a in selected]}"
        )

        return {
            "success": True,
            "collaboration_id": collaboration_id,
            "agents": [a.to_dict() for a in selected],
            "collaboration": collaboration,
        }

    def execute_collaboration(
        self,
        collaboration_id: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a collaboration session with summoned agents.

        Args:
            collaboration_id: The collaboration session ID
            input_data: Input data for the collaboration

        Returns:
            Collaboration results
        """
        if collaboration_id not in self.active_collaborations:
            return {
                "success": False,
                "error": f"Collaboration {collaboration_id} not found",
            }

        collaboration = self.active_collaborations[collaboration_id]
        mode = CollaborationMode(collaboration["mode"])
        agents = collaboration["agents"]

        # Execute based on collaboration mode
        if mode == CollaborationMode.SEQUENTIAL:
            return self._execute_sequential(agents, input_data, collaboration)
        elif mode == CollaborationMode.PARALLEL:
            return self._execute_parallel(agents, input_data, collaboration)
        elif mode == CollaborationMode.PARTY:
            return self._execute_party_mode(agents, input_data, collaboration)
        elif mode == CollaborationMode.WORKFLOW:
            return self._execute_workflow(agents, input_data, collaboration)
        else:
            return {
                "success": False,
                "error": f"Unknown collaboration mode: {mode}",
            }

    def _find_agents_by_capabilities(
        self,
        required_capabilities: List[str],
        preferred_agents: List[str] = None,
    ) -> List[AgentIdentity]:
        """Find agents that have the required capabilities."""
        candidates = []

        # Get all agents from registry
        all_agents = self.registry.list_agents()

        for agent in all_agents:
            # Check if agent has required capabilities
            agent_caps = set(agent.capabilities)
            required_caps = set(required_capabilities)

            if required_caps.issubset(agent_caps):
                candidates.append(agent)

        # Prioritize preferred agents
        if preferred_agents:
            preferred = [a for a in candidates if a.agent_id in preferred_agents]
            others = [a for a in candidates if a.agent_id not in preferred_agents]
            candidates = preferred + others

        return candidates

    def _select_agents(
        self,
        candidates: List[AgentIdentity],
        max_agents: int,
        context: Dict[str, Any],
    ) -> List[AgentIdentity]:
        """Select best agents from candidates (consider reputation, availability)."""
        # For now, simple selection (can be enhanced with reputation scoring)
        selected = candidates[:max_agents]

        # TODO: Add reputation-based selection
        # TODO: Add availability checking
        # TODO: Add load balancing

        return selected

    def _execute_sequential(
        self,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        collaboration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute agents sequentially (one after another)."""
        results = []
        current_data = input_data

        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue

            # Get agent persona/activation
            persona = self.agent_personas.get(agent_id)
            _ = self.agent_activations.get(agent_id)  # For future activation handling

            # Execute agent (simulated - in production, would call agent API)
            response = self._call_agent(agent, persona, current_data, collaboration)

            results.append(response)
            # Pass output to next agent
            current_data = {
                **current_data,
                "previous_agent_output": response.response,
                "agent_id": agent_id,
            }

        return {
            "success": True,
            "mode": "sequential",
            "results": [r.to_dict() for r in results],
            "final_output": results[-1].response if results else None,
        }

    def _execute_parallel(
        self,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        collaboration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute agents in parallel (simultaneously)."""
        results = []

        # In production, would use async/threading
        for agent_id in agent_ids:
            agent = self.registry.get_agent(agent_id)
            if not agent:
                continue

            persona = self.agent_personas.get(agent_id)
            response = self._call_agent(agent, persona, input_data, collaboration)
            results.append(response)

        # Combine results
        combined_output = self._combine_parallel_results(results)

        return {
            "success": True,
            "mode": "parallel",
            "results": [r.to_dict() for r in results],
            "combined_output": combined_output,
        }

    def _execute_party_mode(
        self,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        collaboration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute party mode - all agents collaborate in group chat."""
        # Party mode: All agents see each other's responses
        conversation = []
        current_topic = input_data.get("topic", "Collaboration")

        # Initial prompt to all agents (for future use)
        _ = f"Topic: {current_topic}\n\nContext: {json.dumps(input_data, indent=2)}"

        # Simulate group conversation (in production, would use real agent APIs)
        for round_num in range(3):  # 3 rounds of conversation
            round_responses = []

            for agent_id in agent_ids:
                agent = self.registry.get_agent(agent_id)
                if not agent:
                    continue

                persona = self.agent_personas.get(agent_id)

                # Each agent sees previous responses
                context = {
                    "topic": current_topic,
                    "round": round_num,
                    "previous_responses": conversation[-len(agent_ids) :] if conversation else [],
                    "input": input_data,
                }

                response = self._call_agent(agent, persona, context, collaboration)
                round_responses.append(response)
                conversation.append(
                    {
                        "agent": agent.agent_name,
                        "round": round_num,
                        "response": response.response,
                    }
                )

        return {
            "success": True,
            "mode": "party",
            "conversation": conversation,
            "summary": self._summarize_party_conversation(conversation),
        }

    def _execute_workflow(
        self,
        agent_ids: List[str],
        input_data: Dict[str, Any],
        collaboration: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute structured workflow with agent coordination."""
        # Workflow execution (inspired by BMad workflow.xml)
        workflow = input_data.get("workflow", {})
        steps = workflow.get("steps", [])

        results = []
        workflow_state = {
            "current_step": 0,
            "variables": input_data.get("variables", {}),
            "outputs": {},
        }

        for step in steps:
            step_num = step.get("n", workflow_state["current_step"])
            _ = step.get("type", "action")  # For future step type handling
            assigned_agent = step.get("agent_id")

            # Find agent for this step
            agent_id = assigned_agent or self._select_agent_for_step(step, agent_ids)
            agent = self.registry.get_agent(agent_id)

            if not agent:
                continue

            persona = self.agent_personas.get(agent_id)

            # Execute step
            step_context = {
                "step": step,
                "workflow_state": workflow_state,
                "input": input_data,
            }

            response = self._call_agent(agent, persona, step_context, collaboration)

            # Update workflow state
            workflow_state["current_step"] = step_num
            if "output" in step:
                workflow_state["outputs"][
                    step.get("output_key", f"step_{step_num}")
                ] = response.response

            results.append(
                {
                    "step": step_num,
                    "agent": agent.agent_name,
                    "result": response.to_dict(),
                }
            )

        return {
            "success": True,
            "mode": "workflow",
            "results": results,
            "final_state": workflow_state,
        }

    def _call_agent(
        self,
        agent: AgentIdentity,
        persona: Optional[AgentPersona],
        context: Dict[str, Any],
        collaboration: Dict[str, Any],
    ) -> AgentResponse:
        """
        Call an agent (simulated - in production would use agent API).

        This is where we would integrate with actual agent endpoints.
        """
        # Build prompt from persona and context
        prompt = self._build_agent_prompt(agent, persona, context, collaboration)

        # In production, this would call the agent's API
        # For now, simulate response
        response_text = f"[Simulated response from {agent.agent_name}]\n\nPrompt: {prompt[:100]}..."

        return AgentResponse(
            agent_id=agent.agent_id,
            agent_name=agent.agent_name,
            response=response_text,
            metadata={
                "did": agent.get_did(),
                "capabilities": agent.capabilities,
            },
        )

    def _build_agent_prompt(
        self,
        agent: AgentIdentity,
        persona: Optional[AgentPersona],
        context: Dict[str, Any],
        collaboration: Dict[str, Any],
    ) -> str:
        """Build prompt for agent based on persona and context."""
        parts = []

        # Agent identity
        parts.append(f"Agent: {agent.agent_name}")
        parts.append(f"DID: {agent.get_did()}")

        # Persona
        if persona:
            parts.append(f"\nRole: {persona.role}")
            parts.append(f"Identity: {persona.identity}")
            parts.append(f"Communication Style: {persona.communication_style}")
            if persona.principles:
                parts.append("\nPrinciples:")
                for p in persona.principles:
                    parts.append(f"  - {p}")

        # Capabilities
        parts.append(f"\nCapabilities: {', '.join(agent.capabilities)}")

        # Context
        parts.append(f"\nContext: {json.dumps(context, indent=2)}")

        # Collaboration info
        parts.append(f"\nCollaboration: {collaboration.get('task', 'N/A')}")

        return "\n".join(parts)

    def _select_agent_for_step(
        self,
        step: Dict[str, Any],
        available_agents: List[str],
    ) -> str:
        """Select best agent for a workflow step."""
        # Simple selection (can be enhanced with capability matching)
        if available_agents:
            return available_agents[0]
        return ""

    def _combine_parallel_results(self, results: List[AgentResponse]) -> str:
        """Combine results from parallel execution."""
        combined = []
        for r in results:
            combined.append(f"**{r.agent_name}**:\n{r.response}")
        return "\n\n".join(combined)

    def _summarize_party_conversation(self, conversation: List[Dict]) -> str:
        """Summarize party mode conversation."""
        return f"Party mode collaboration with {len(set(c['agent'] for c in conversation))} agents, {len(conversation)} responses"

    def list_available_agents(self) -> List[Dict[str, Any]]:
        """List all available agents with their personas."""
        agents = []
        all_agents = self.registry.list_agents()

        for agent in all_agents:
            persona = self.agent_personas.get(agent.agent_id)
            commands = self.agent_commands.get(agent.agent_id, [])

            agents.append(
                {
                    "agent_id": agent.agent_id,
                    "agent_name": agent.agent_name,
                    "did": agent.get_did(),
                    "capabilities": agent.capabilities,
                    "persona": persona.to_dict() if persona else None,
                    "commands": [c.to_dict() for c in commands],
                }
            )

        return agents


# Global orchestrator instance
_orchestrator: Optional[SwarmOrchestrator] = None


def get_orchestrator(redis_url: Optional[str] = None) -> SwarmOrchestrator:
    """Get the global swarm orchestrator."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = SwarmOrchestrator(redis_url=redis_url)
    return _orchestrator
