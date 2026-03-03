"""
services/pdf_service.py — PDF generation service wrapper.

Keeps PDF logic centralized. Converts the raw prd_json dict into a
validated AnalysisReport Pydantic model, then delegates to report_builder.
"""
import os
from schemas.output_schema import (
    AnalysisReport, ProjectOverview, MilestoneItem,
    Deliverables, FunctionalRequirements, NonFunctionalRequirements,
    TechnicalRequirements, Signatory, UserStory
)
from pdf_generator.report_builder import generate_pdf_report
from core.logging_config import get_logger

logger = get_logger(__name__)


def _safe_list(d: dict, key: str) -> list:
    val = d.get(key, [])
    return val if isinstance(val, list) else []


def build_report(prd_json: dict) -> AnalysisReport:
    """
    Convert a raw PRD JSON dict (from LLM) into a validated AnalysisReport.
    Raises ValidationError if required fields are missing.
    """
    from datetime import datetime
    today = datetime.now().strftime("%d-%b-%Y")

    overview_data = prd_json.get("project_overview", {})
    milestones = [
        MilestoneItem(**m) if isinstance(m, dict)
        else MilestoneItem(name=str(m), start_date="", end_date="", acceptance_criteria=[])
        for m in overview_data.get("milestones", [])
    ]
    project_overview = ProjectOverview(
        brief=overview_data.get("brief", ""),
        outcomes=_safe_list(overview_data, "outcomes"),
        stakeholders=_safe_list(overview_data, "stakeholders"),
        timeline_start=overview_data.get("timeline_start", ""),
        timeline_end=overview_data.get("timeline_end", ""),
        milestones=milestones,
    )

    deliverables_data = prd_json.get("deliverables", {})
    deliverables = Deliverables(
        software_modules=_safe_list(deliverables_data, "software_modules"),
        documentation=_safe_list(deliverables_data, "documentation"),
        training_materials=_safe_list(deliverables_data, "training_materials"),
        user_manuals=_safe_list(deliverables_data, "user_manuals"),
        other=_safe_list(deliverables_data, "other"),
    )

    fr_data = prd_json.get("functional_requirements", {})
    functional = FunctionalRequirements(
        user_roles_permissions=_safe_list(fr_data, "user_roles_permissions"),
        ui_ux_specifications=_safe_list(fr_data, "ui_ux_specifications"),
        data_management=_safe_list(fr_data, "data_management"),
        integrations=_safe_list(fr_data, "integrations"),
    )

    nfr_data = prd_json.get("non_functional_requirements", {})
    non_functional = NonFunctionalRequirements(
        performance=_safe_list(nfr_data, "performance"),
        reliability=_safe_list(nfr_data, "reliability"),
        usability=_safe_list(nfr_data, "usability"),
        compatibility=_safe_list(nfr_data, "compatibility"),
        compliance=_safe_list(nfr_data, "compliance"),
        scalability=_safe_list(nfr_data, "scalability"),
        maintainability=_safe_list(nfr_data, "maintainability"),
    )

    tr_data = prd_json.get("technical_requirements", {})
    technical = TechnicalRequirements(
        languages_frameworks=_safe_list(tr_data, "languages_frameworks"),
        database=_safe_list(tr_data, "database"),
        hosting=_safe_list(tr_data, "hosting"),
        security=_safe_list(tr_data, "security"),
        perf_scalability=_safe_list(tr_data, "perf_scalability"),
    )

    sp_data = prd_json.get("service_provider", {})
    client_data = prd_json.get("client", {})
    signatory_fields = list(Signatory.model_fields.keys())

    # Parse user stories
    raw_stories = prd_json.get("user_stories", [])
    user_stories = []
    for s in raw_stories:
        if isinstance(s, dict):
            user_stories.append(UserStory(
                id=s.get("id", ""),
                role=s.get("role", ""),
                action=s.get("action", ""),
                benefit=s.get("benefit", ""),
                acceptance_criteria=_safe_list(s, "acceptance_criteria"),
            ))

    report = AnalysisReport(
        project_name=prd_json.get("project_name", "Untitled Project"),
        version=prd_json.get("version", "V1.0"),
        date=prd_json.get("date", today),
        introduction=prd_json.get("introduction", ""),
        project_overview=project_overview,
        deliverables=deliverables,
        functional_requirements=functional,
        non_functional_requirements=non_functional,
        technical_requirements=technical,
        user_stories=user_stories,
        service_provider=Signatory(**{k: sp_data.get(k, "") for k in signatory_fields}),
        client=Signatory(**{k: client_data.get(k, "") for k in signatory_fields}),
    )
    logger.info("AnalysisReport built | project=%s | version=%s", report.project_name, report.version)
    return report


def generate_pdf(report: AnalysisReport, output_path: str) -> None:
    """Write the PDF file at output_path. Creates parent dirs if needed."""
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    generate_pdf_report(report, output_path)
    logger.info("PDF written | path=%s", output_path)
