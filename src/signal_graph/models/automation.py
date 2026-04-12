from __future__ import annotations

from pydantic import BaseModel, Field


class AutomationArtifact(BaseModel):
    path: str
    kind: str
    purpose: str


class HostAutomationFlow(BaseModel):
    host: str
    contract_version: str
    validated: bool
    managed_file: str
    managed_marker: str
    install_steps: list[str] = Field(default_factory=list)
    audit_checks: list[str] = Field(default_factory=list)
    uninstall_steps: list[str] = Field(default_factory=list)
    active_proof: list[str] = Field(default_factory=list)
    generated_artifacts: list[AutomationArtifact] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    failure_diagnostics: list[str] = Field(default_factory=list)


class OperationalAutomationContract(BaseModel):
    contract_version: str
    hosts: list[HostAutomationFlow] = Field(default_factory=list)
