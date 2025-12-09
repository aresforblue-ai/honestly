"""
AAIP Swarm API Routes
=====================

REST endpoints for the AAIP Swarm Orchestration system.
Enables agent summoning, collaboration, and workflow execution.
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from identity.swarm_orchestrator import (
    AgentPersona,
    AgentActivation,
    AgentCommand,
    SummonRequest,
    CollaborationMode,
    get_orchestrator,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/swarm", tags=["swarm"])


# Request/Response Models
class RegisterPersonaRequest(BaseModel):
    """Request to register agent persona."""

    agent_id: str = Field(..., description="AAIP agent ID")
    persona: Dict[str, Any] = Field(..., description="Agent persona configuration")
    activation: Optional[Dict[str, Any]] = Field(None, description="Agent activation instructions")
    commands: Optional[List[Dict[str, Any]]] = Field(None, description="Agent commands")


class SummonAgentsRequest(BaseModel):
    """Request to summon agents."""

    task_description: str = Field(..., description="Task description")
    required_capabilities: List[str] = Field(..., description="Required capabilities")
    preferred_agents: Optional[List[str]] = Field(None, description="Preferred agent IDs")
    collaboration_mode: str = Field("sequential", description="Collaboration mode")
    max_agents: int = Field(5, ge=1, le=20, description="Maximum agents to summon")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    human_identity: Optional[str] = Field(
        None, description="Human Semaphore commitment (for authorization)"
    )


class ExecuteCollaborationRequest(BaseModel):
    """Request to execute collaboration."""

    collaboration_id: str = Field(..., description="Collaboration session ID")
    input_data: Dict[str, Any] = Field(..., description="Input data for collaboration")


# Endpoints
@router.post("/agent/persona/register")
async def register_agent_persona(request: RegisterPersonaRequest):
    """
    Register persona and activation for an AAIP agent.

    This extends the agent's AAIP identity with BMad-style persona/activation.
    """
    try:
        orchestrator = get_orchestrator()

        # Parse persona
        persona = AgentPersona.from_dict(request.persona)

        # Parse activation if provided
        activation = None
        if request.activation:
            activation = AgentActivation.from_dict(request.activation)

        # Parse commands if provided
        commands = None
        if request.commands:
            commands = [AgentCommand(**cmd) for cmd in request.commands]

        success = orchestrator.register_agent_persona(
            agent_id=request.agent_id,
            persona=persona,
            activation=activation,
            commands=commands,
        )

        if not success:
            raise HTTPException(status_code=404, detail="Agent not found in AAIP registry")

        return {
            "success": True,
            "message": f"Persona registered for agent {request.agent_id}",
        }
    except Exception as e:
        logger.error(f"Error registering persona: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agents/summon")
async def summon_agents(request: SummonAgentsRequest):
    """
    Summon agents based on capability requirements.

    This is the core "summoning" mechanism - finds agents that can help
    with the task and coordinates their collaboration.
    """
    try:
        orchestrator = get_orchestrator()

        # Parse collaboration mode
        try:
            mode = CollaborationMode(request.collaboration_mode)
        except ValueError:
            mode = CollaborationMode.SEQUENTIAL

        # Create summon request
        summon_req = SummonRequest(
            task_description=request.task_description,
            required_capabilities=request.required_capabilities,
            preferred_agents=request.preferred_agents or [],
            collaboration_mode=mode,
            max_agents=request.max_agents,
            context=request.context or {},
        )

        result = orchestrator.summon_agents(
            request=summon_req,
            human_identity=request.human_identity,
        )

        return result
    except Exception as e:
        logger.error(f"Error summoning agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/collaboration/execute")
async def execute_collaboration(request: ExecuteCollaborationRequest):
    """
    Execute a collaboration session with summoned agents.
    """
    try:
        orchestrator = get_orchestrator()

        result = orchestrator.execute_collaboration(
            collaboration_id=request.collaboration_id,
            input_data=request.input_data,
        )

        return result
    except Exception as e:
        logger.error(f"Error executing collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/agents/list")
async def list_agents():
    """
    List all available agents with their personas and capabilities.
    """
    try:
        orchestrator = get_orchestrator()
        agents = orchestrator.list_available_agents()

        return {
            "success": True,
            "agents": agents,
            "count": len(agents),
        }
    except Exception as e:
        logger.error(f"Error listing agents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/{collaboration_id}")
async def get_collaboration(collaboration_id: str):
    """
    Get collaboration session details.
    """
    try:
        orchestrator = get_orchestrator()

        if collaboration_id not in orchestrator.active_collaborations:
            raise HTTPException(status_code=404, detail="Collaboration not found")

        collaboration = orchestrator.active_collaborations[collaboration_id]

        return {
            "success": True,
            "collaboration": collaboration,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collaboration: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collaboration/{collaboration_id}/status")
async def get_collaboration_status(collaboration_id: str):
    """
    Get collaboration status.
    """
    try:
        orchestrator = get_orchestrator()

        if collaboration_id not in orchestrator.active_collaborations:
            raise HTTPException(status_code=404, detail="Collaboration not found")

        collaboration = orchestrator.active_collaborations[collaboration_id]

        return {
            "success": True,
            "collaboration_id": collaboration_id,
            "status": collaboration.get("status", "unknown"),
            "agents": collaboration.get("agents", []),
            "created_at": collaboration.get("created_at"),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting collaboration status: {e}")
        raise HTTPException(status_code=500, detail=str(e))
