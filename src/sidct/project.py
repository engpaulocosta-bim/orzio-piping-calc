"""Project domain and JSON persistence for SIDCT desktop workflows."""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .engines.selector import run_full_calculation
from .models import LineInput, ReportContext

SCHEMA_VERSION = "1.1"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ValidationState(BaseModel):
    status: str = "DRAFT"
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    dataset_missing: list[str] = Field(default_factory=list)
    out_of_scope: list[str] = Field(default_factory=list)


class AuditEvent(BaseModel):
    timestamp: str = Field(default_factory=_now)
    action: str
    line_id: str | None = None
    line_tag: str | None = None
    message: str = ""
    details: dict[str, Any] = Field(default_factory=dict)


class HydraulicCase(BaseModel):
    case_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str = "Base case"
    operation_mode: str = "calculate_new"
    status: str = "DRAFT"
    created_at: str = Field(default_factory=_now)
    report_context: ReportContext | None = None


class LineSegment(BaseModel):
    line_id: str = Field(default_factory=lambda: str(uuid4()))
    tag: str
    line_input: LineInput
    hydraulic_cases: list[HydraulicCase] = Field(default_factory=list)
    last_report_context: ReportContext | None = None
    validation_state: ValidationState = Field(default_factory=ValidationState)

    def calculate(self, case_name: str = "Base case") -> ReportContext:
        ctx = run_full_calculation(self.line_input)
        self.last_report_context = ctx
        status = ctx.checker_result.overall_status if ctx.checker_result else "CALCULATED"
        self.validation_state.status = status
        self.validation_state.warnings = [w.message for w in ctx.warnings]
        self.validation_state.dataset_missing = (
            ctx.checker_result.dataset_missing_items if ctx.checker_result else []
        )
        self.validation_state.out_of_scope = (
            ctx.checker_result.out_of_scope_items if ctx.checker_result else []
        )
        self.hydraulic_cases.append(
            HydraulicCase(
                name=case_name,
                operation_mode=self.line_input.operation_mode,
                status=status,
                report_context=ctx,
            )
        )
        return ctx

    def duplicate(self, new_tag: str) -> "LineSegment":
        new_input = self.line_input.model_copy(deep=True, update={"line_tag": new_tag})
        return LineSegment(tag=new_tag, line_input=new_input)


class Route(BaseModel):
    route_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: str = ""
    lines: list[LineSegment] = Field(default_factory=list)

    def add_line(self, line_input: LineInput) -> LineSegment:
        line = LineSegment(tag=line_input.line_tag, line_input=line_input)
        self.lines.append(line)
        return line

    def get_line(self, line_id: str) -> LineSegment | None:
        return next((line for line in self.lines if line.line_id == line_id), None)


class Project(BaseModel):
    schema_version: str = SCHEMA_VERSION
    project_id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    client: str = ""
    site: str = ""
    revision: str = "A"
    created_at: str = Field(default_factory=_now)
    updated_at: str = Field(default_factory=_now)
    routes: list[Route] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    audit_log: list[AuditEvent] = Field(default_factory=list)

    def touch(self) -> None:
        self.updated_at = _now()

    def add_route(self, name: str, description: str = "") -> Route:
        route = Route(name=name, description=description)
        self.routes.append(route)
        self.touch()
        self.add_audit("add_route", message=f"Route added: {name}", details={"route_id": route.route_id})
        return route

    def add_line(self, route_id: str, line_input: LineInput) -> LineSegment:
        route = self.get_route(route_id)
        if route is None:
            raise ValueError(f"Route not found: {route_id}")
        line = route.add_line(line_input)
        self.touch()
        self.add_audit("add_line", line.line_id, line.tag, f"Line added: {line.tag}")
        return line

    def get_route(self, route_id: str) -> Route | None:
        return next((route for route in self.routes if route.route_id == route_id), None)

    def all_lines(self) -> list[LineSegment]:
        return [line for route in self.routes for line in route.lines]

    def calculate_line(self, line_id: str) -> ReportContext:
        for line in self.all_lines():
            if line.line_id == line_id:
                ctx = line.calculate()
                self.touch()
                ctx.dataset_provenance = dict(ctx.dataset_provenance or {})
                ctx.dataset_provenance["audit"] = {
                    "calculated_at": _now(),
                    "project_updated_at": self.updated_at,
                    "schema_version": self.schema_version,
                    "catalog": ctx.line_input.dimensional_catalog if ctx.line_input else "",
                    "service": ctx.line_input.service if ctx.line_input else "",
                }
                self.add_audit(
                    "calculate_line",
                    line.line_id,
                    line.tag,
                    f"Line calculated: {line.tag}",
                    {"status": line.validation_state.status},
                )
                return ctx
        raise ValueError(f"Line not found: {line_id}")

    def duplicate_line(self, line_id: str, new_tag: str) -> LineSegment:
        for route in self.routes:
            line = route.get_line(line_id)
            if line is not None:
                duplicated = line.duplicate(new_tag)
                route.lines.append(duplicated)
                self.touch()
                self.add_audit(
                    "duplicate_line",
                    duplicated.line_id,
                    duplicated.tag,
                    f"Line duplicated from {line.tag} to {new_tag}",
                    {"source_line_id": line.line_id},
                )
                return duplicated
        raise ValueError(f"Line not found: {line_id}")

    def remove_line(self, line_id: str) -> LineSegment:
        for route in self.routes:
            for index, line in enumerate(route.lines):
                if line.line_id == line_id:
                    removed = route.lines.pop(index)
                    self.touch()
                    self.add_audit("remove_line", removed.line_id, removed.tag, f"Line removed: {removed.tag}")
                    return removed
        raise ValueError(f"Line not found: {line_id}")

    def add_audit(
        self,
        action: str,
        line_id: str | None = None,
        line_tag: str | None = None,
        message: str = "",
        details: dict[str, Any] | None = None,
    ) -> None:
        self.audit_log.append(
            AuditEvent(
                action=action,
                line_id=line_id,
                line_tag=line_tag,
                message=message,
                details=details or {},
            )
        )


def create_default_project(name: str = "SIDCT Project") -> Project:
    project = Project(name=name)
    project.add_route("Route A")
    return project


def save_project(project: Project, path: str | Path) -> None:
    project.touch()
    Path(path).write_text(project.model_dump_json(indent=2), encoding="utf-8")


def load_project(path: str | Path) -> Project:
    data = Path(path).read_text(encoding="utf-8")
    return Project.model_validate_json(data)
