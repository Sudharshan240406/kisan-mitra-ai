import time
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Department(BaseModel):
    id: str
    name: str
    organization_id: str
    created_at: float = Field(default_factory=time.time)

class Team(BaseModel):
    id: str
    name: str
    department_id: str
    created_at: float = Field(default_factory=time.time)

class Operator(BaseModel):
    id: str
    name: str
    team_id: str
    role: str = "Operator"
    created_at: float = Field(default_factory=time.time)

class Organization(BaseModel):
    id: str
    name: str
    tenant_id: str
    departments: List[str] = Field(default_factory=list)
    created_at: float = Field(default_factory=time.time)

class OrganizationManager:
    """
    Manages organization units structure hierarchies and parent lookups.
    """
    def __init__(self) -> None:
        self.organizations: Dict[str, Organization] = {}
        self.departments: Dict[str, Department] = {}
        self.teams: Dict[str, Team] = {}
        self.operators: Dict[str, Operator] = {}

    def create_organization(self, org_id: str, name: str, tenant_id: str) -> Organization:
        org = Organization(id=org_id, name=name, tenant_id=tenant_id)
        self.organizations[org_id] = org
        return org

    def create_department(self, dept_id: str, name: str, org_id: str) -> Optional[Department]:
        if org_id not in self.organizations:
            return None
        dept = Department(id=dept_id, name=name, organization_id=org_id)
        self.departments[dept_id] = dept
        self.organizations[org_id].departments.append(dept_id)
        return dept

    def create_team(self, team_id: str, name: str, dept_id: str) -> Optional[Team]:
        if dept_id not in self.departments:
            return None
        team = Team(id=team_id, name=name, department_id=dept_id)
        self.teams[team_id] = team
        return team

    def create_operator(self, op_id: str, name: str, team_id: str, role: str = "Operator") -> Optional[Operator]:
        if team_id not in self.teams:
            return None
        op = Operator(id=op_id, name=name, team_id=team_id, role=role)
        self.operators[op_id] = op
        return op

    def get_operator_hierarchy(self, op_id: str) -> Optional[Dict[str, Any]]:
        op = self.operators.get(op_id)
        if not op:
            return None
        team = self.teams.get(op.team_id)
        dept = self.departments.get(team.department_id) if team else None
        org = self.organizations.get(dept.organization_id) if dept else None

        return {
            "operator": op.model_dump(),
            "team": team.model_dump() if team else None,
            "department": dept.model_dump() if dept else None,
            "organization": org.model_dump() if org else None
        }
