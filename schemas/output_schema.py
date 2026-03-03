from pydantic import BaseModel, Field
from typing import List, Optional

# ── 2. Project Overview ──
class MilestoneItem(BaseModel):
    name: str = Field(..., description="e.g. Milestone 1: Data Prep")
    start_date: str
    end_date: str
    acceptance_criteria: List[str]

class ProjectOverview(BaseModel):
    brief: str
    outcomes: List[str]
    stakeholders: List[str]
    timeline_start: str
    timeline_end: str
    milestones: List[MilestoneItem]

# ── 3. Project Deliverables ──
class Deliverables(BaseModel):
    software_modules: List[str]
    documentation: List[str]
    training_materials: List[str]
    user_manuals: List[str]
    other: List[str]

# ── 4. Functional Requirements ──
class FunctionalRequirements(BaseModel):
    user_roles_permissions: List[str]
    ui_ux_specifications: List[str]
    data_management: List[str]
    integrations: List[str]

# ── 5. Non-Functional Requirements ──
class NonFunctionalRequirements(BaseModel):
    performance: List[str]
    reliability: List[str]
    usability: List[str]
    compatibility: List[str] # responsive, browsers, etc.
    compliance: List[str]    # gdpr etc
    scalability: List[str]
    maintainability: List[str]

# ── 6. Tech Stack ──
class TechnicalRequirements(BaseModel):
    languages_frameworks: List[str]
    database: List[str]
    hosting: List[str]
    security: List[str]
    perf_scalability: List[str]

# ── 7. User Stories ──
class UserStory(BaseModel):
    id: str                      # e.g. "US-01"
    role: str                    # e.g. "Admin"
    action: str                  # e.g. "manage user accounts"
    benefit: str                 # e.g. "so that I can control access"
    acceptance_criteria: List[str]

# ── Signatories ──
class Signatory(BaseModel):
    name: str = ""
    address: str = ""
    contact: str = ""
    email: str = ""
    company_name: str = ""
    company_address: str = ""
    company_reg_number: str = ""

# ── Root Report ──
class AnalysisReport(BaseModel):
    project_name: str
    version: str = "V1.0"
    date: str
    
    # 1. Introduction
    introduction: str

    # 2. Project Overview
    project_overview: ProjectOverview

    # 3. Deliverables
    deliverables: Deliverables
    
    # 4. Functional
    functional_requirements: FunctionalRequirements

    # 5. Non-Functional
    non_functional_requirements: NonFunctionalRequirements
    
    # 6. Technical
    technical_requirements: TechnicalRequirements

    # 7. User Stories
    user_stories: List[UserStory] = []

    # Signatories
    service_provider: Signatory
    client: Signatory

    # ── Production additions ───────────────────────────────────────
    version_number: int = 1              # Mirrors PRDVersion.version_number
    session_id: Optional[str] = None    # Links back to ChatSession UUID