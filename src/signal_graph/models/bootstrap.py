from __future__ import annotations

from pydantic import BaseModel, Field


class BootstrapCommand(BaseModel):
    name: str
    command: list[str] = Field(default_factory=list)
    purpose: str


class BootstrapStep(BaseModel):
    id: str
    title: str
    commands: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)


class BootstrapMcpContract(BaseModel):
    transport: str = "stdio"
    launch_command: list[str] = Field(default_factory=list)
    host_agnostic_assumptions: list[str] = Field(default_factory=list)
    proof_methods: list[str] = Field(default_factory=list)
    expected_tools: list[str] = Field(default_factory=list)


class BootstrapContract(BaseModel):
    contract_version: str
    entrypoints: list[BootstrapCommand] = Field(default_factory=list)
    prereqs: list[str] = Field(default_factory=list)
    env: list[str] = Field(default_factory=list)
    project_state: list[str] = Field(default_factory=list)
    smoke_path: list[BootstrapStep] = Field(default_factory=list)
    mcp: BootstrapMcpContract
    proof_outputs: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    drift_checks: list[str] = Field(default_factory=list)
    provenance_rules: list[str] = Field(default_factory=list)
