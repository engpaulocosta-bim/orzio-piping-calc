"""Memorial de cálculo PDF — ReportLab.

Gera PDF auditável com:
- Cabeçalho e identificação
- Dados de entrada
- Propriedades do fluido
- Resultados hidráulicos
- Resultados de espessura
- Pressão externa (se vácuo)
- Suportes
- Checker
- Warnings e limitações
- Proveniência dos datasets
- Citações normativas
- Rodapé de uso restrito
"""
from __future__ import annotations
import io
from pathlib import Path
from typing import Optional
from ..models import ReportContext

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import mm, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
        HRFlowable, PageBreak, KeepTogether
    )
    from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False


_STATUS_COLORS = {
    "APPROVED": colors.HexColor("#27ae60"),
    "CONSERVATIVE": colors.HexColor("#2980b9"),
    "INSUFFICIENT": colors.HexColor("#e67e22"),
    "CRITICAL": colors.HexColor("#c0392b"),
    "DATASET_MISSING": colors.HexColor("#8e44ad"),
    "OUT_OF_SCOPE": colors.HexColor("#7f8c8d"),
    "WARNING": colors.HexColor("#f39c12"),
    "CALCULATED": colors.HexColor("#27ae60"),
}


def _fmt(v, decimals: int = 3, unit: str = "") -> str:
    if v is None:
        return "N/A"
    try:
        return f"{float(v):.{decimals}f} {unit}".strip()
    except Exception:
        return str(v)


def _status_color(status: str):
    if not REPORTLAB_OK:
        return None
    return _STATUS_COLORS.get(status, colors.black)


def generate_pdf(ctx: ReportContext, output_path: str | Path | None = None) -> bytes:
    """Gera PDF e retorna bytes. Se output_path fornecido, também escreve ficheiro."""
    if not REPORTLAB_OK:
        raise ImportError("ReportLab não instalado. Execute: pip install reportlab")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title=f"SIDCT — {ctx.project_name} — {ctx.line_tag}",
        author="SIDCT v1.0",
    )

    styles = getSampleStyleSheet()
    style_h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=14, spaceAfter=6)
    style_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, spaceAfter=4)
    style_normal = ParagraphStyle("Normal2", parent=styles["Normal"], fontSize=9, spaceAfter=2)
    style_small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, spaceAfter=2,
                                  textColor=colors.HexColor("#555555"))
    style_warning = ParagraphStyle("Warning", parent=styles["Normal"], fontSize=8,
                                    textColor=colors.HexColor("#c0392b"), spaceAfter=2)
    style_center = ParagraphStyle("Center", parent=styles["Normal"], fontSize=9,
                                   alignment=TA_CENTER)
    style_footer = ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7,
                                   textColor=colors.grey, alignment=TA_CENTER)

    def H1(text): return Paragraph(text, style_h1)
    def H2(text): return Paragraph(text, style_h2)
    def P(text): return Paragraph(text, style_normal)
    def Ps(text): return Paragraph(text, style_small)
    def Pw(text): return Paragraph(text, style_warning)
    def HR(): return HRFlowable(width="100%", thickness=0.5, color=colors.grey, spaceAfter=4)

    def table(data, col_widths=None, header=True):
        if col_widths is None:
            col_widths = [80*mm, 90*mm]
        t = Table(data, colWidths=col_widths)
        ts = [
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ]
        if header:
            ts.extend([
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ])
        t.setStyle(TableStyle(ts))
        return t

    story = []

    # ── 1. Capa / Cabeçalho ───────────────────────────────────────────────────
    story.append(H1("SIDCT — Memorial de Cálculo de Tubagens"))
    story.append(HR())
    story.append(table([
        ["Projecto", ctx.project_name],
        ["Linha / Tag", ctx.line_tag],
        ["Revisão", ctx.revision],
        ["Data", ctx.date],
        ["Preparado por", ctx.prepared_by],
    ], header=False))
    story.append(Spacer(1, 8*mm))

    # ── 2. Perfil adoptado ────────────────────────────────────────────────────
    story.append(H2("1. Perfil de Projecto Adoptado"))
    if ctx.profile_used:
        p = ctx.profile_used
        story.append(table([
            ["Parâmetro", "Valor"],
            ["Perfil", ctx.line_input.project_profile if ctx.line_input else "N/A"],
            ["Código primário", p.get("primary_design_code", "N/A")],
            ["Catálogo (carbono)", p.get("default_catalog_carbon", "N/A")],
            ["Catálogo (inox)", p.get("default_catalog_stainless", "N/A")],
            ["Jurisdição", ctx.line_input.jurisdiction if ctx.line_input else "N/A"],
        ]))
    story.append(Spacer(1, 4*mm))

    # ── 3. Dados de Entrada ───────────────────────────────────────────────────
    story.append(H2("2. Dados de Entrada"))
    if ctx.line_input:
        li = ctx.line_input
        story.append(table([
            ["Parâmetro", "Valor"],
            ["Serviço", li.service],
            ["Fluido", li.fluid_name],
            ["P operação", _fmt(li.P_oper_bar, 2, "barg")],
            ["T operação", _fmt(li.T_oper_c, 1, "°C")],
            ["P projecto", _fmt(li.P_design_bar, 2, "barg")],
            ["T projecto", _fmt(li.T_design_c, 1, "°C")],
            ["Caudal", f"{li.flow_rate} {li.flow_rate_basis}"],
            ["Comprimento", _fmt(li.line_length_m, 1, "m")],
            ["Δ elevação", _fmt(li.elevation_delta_m, 1, "m")],
            ["Material", li.material],
            ["Catálogo", li.dimensional_catalog],
            ["CA (corrosão)", _fmt(li.corrosion_allowance_mm, 1, "mm")],
            ["Isolação", _fmt(li.insulation_thickness_mm, 0, "mm")],
        ]))
    story.append(Spacer(1, 4*mm))

    # ── 4. Propriedades do Fluido ─────────────────────────────────────────────
    story.append(H2("3. Propriedades do Fluido"))
    if ctx.fluid_properties:
        fp = ctx.fluid_properties
        story.append(table([
            ["Parâmetro", "Valor"],
            ["Fluido", fp.fluid_name],
            ["T [K]", _fmt(fp.T_K, 2, "K")],
            ["P [Pa]", _fmt(fp.P_pa, 0, "Pa")],
            ["ρ (densidade)", _fmt(fp.rho_kgm3, 3, "kg/m³")],
            ["μ (viscosidade dinâmica)", _fmt(fp.mu_pas, 6, "Pa·s")],
            ["Fonte", fp.source],
        ]))
        for w in (fp.warnings or []):
            story.append(Pw(f"⚠ {w}"))
    story.append(Spacer(1, 4*mm))

    # ── 5. Resultados Hidráulicos ─────────────────────────────────────────────
    story.append(H2("4. Resultados Hidráulicos"))
    if ctx.hydraulic_result:
        hr = ctx.hydraulic_result
        data = [["Parâmetro", "Valor"]]
        data.append(["Regime", hr.regime])
        data.append(["Status", hr.status])
        if hr.velocity_ms is not None:
            data.append(["Velocidade", _fmt(hr.velocity_ms, 3, "m/s")])
        if hr.Re is not None:
            data.append(["Reynolds", _fmt(hr.Re, 0, "")])
        if hr.friction_factor is not None:
            data.append(["Factor de atrito f", _fmt(hr.friction_factor, 5, "")])
        if hr.dp_total_bar is not None:
            data.append(["ΔP total", _fmt(hr.dp_total_bar, 4, "bar")])
        if hr.head_loss_m is not None:
            data.append(["Perda de carga", _fmt(hr.head_loss_m, 2, "m")])
        if hr.DN_governing_mm is not None:
            data.append(["DN governante", f"{hr.DN_governing_mm:.0f} mm"])
        if hr.mach_number is not None:
            data.append(["Número de Mach", _fmt(hr.mach_number, 4, "")])
        if hr.pressure_ratio is not None:
            data.append(["P2/P1", _fmt(hr.pressure_ratio, 4, "")])
        if hr.pipe_used:
            data.append(["Tubo (OD × WT)", f"{hr.pipe_used.OD_mm:.1f} × {hr.pipe_used.wall_thickness_mm:.2f} mm"])
        story.append(table(data))
        for w in (hr.warnings or []):
            story.append(Pw(f"⚠ {w}"))
    story.append(Spacer(1, 4*mm))

    # ── 6. Resultados de Espessura (Pressão Interna) ──────────────────────────
    story.append(H2("5. Espessura Mínima — Pressão Interna"))
    if ctx.thickness_result:
        tr = ctx.thickness_result
        data = [["Parâmetro", "Valor"]]
        data.append(["Código", tr.governing_code or "N/A"])
        data.append(["Cláusula", tr.governing_clause or "N/A"])
        data.append(["Status", tr.status])
        if tr.allowable_stress_mpa is not None:
            data.append(["S (tensão admissível)", _fmt(tr.allowable_stress_mpa, 1, "MPa")])
        if tr.E_factor is not None:
            data.append(["E (eficiência junta)", _fmt(tr.E_factor, 2, "")])
        if tr.Y_factor is not None:
            data.append(["Y", _fmt(tr.Y_factor, 2, "")])
        if tr.corrosion_allowance_mm is not None:
            data.append(["CA (corrosão)", _fmt(tr.corrosion_allowance_mm, 1, "mm")])
        if tr.mill_tolerance_pct is not None:
            data.append(["Tolerância de fabrico", _fmt(tr.mill_tolerance_pct, 1, "%")])
        if tr.t_pressure_only_mm is not None:
            data.append(["t (pressão apenas)", _fmt(tr.t_pressure_only_mm, 3, "mm")])
        if tr.t_plus_ca_mm is not None:
            data.append(["t + CA", _fmt(tr.t_plus_ca_mm, 3, "mm")])
        if tr.t_after_mill_tolerance_mm is not None:
            data.append(["t requerido (após mill tol.)", _fmt(tr.t_after_mill_tolerance_mm, 3, "mm")])
        if tr.selected_wall_mm is not None:
            data.append(["Parede seleccionada", _fmt(tr.selected_wall_mm, 2, "mm")])
        if tr.selected_schedule:
            data.append(["Schedule seleccionado", tr.selected_schedule])
        story.append(table(data))
        for w in (tr.warnings or []):
            story.append(Pw(f"⚠ {w}"))
    story.append(Spacer(1, 4*mm))

    # ── 7. Pressão Externa (Vácuo) ────────────────────────────────────────────
    if ctx.external_pressure_result:
        story.append(H2("6. Verificação — Pressão Externa / Colapso"))
        ep = ctx.external_pressure_result
        data = [["Parâmetro", "Valor"]]
        data.append(["Status", ep.method_status])
        if ep.P_external_design_bar:
            data.append(["P externa de projecto", _fmt(ep.P_external_design_bar, 4, "bar")])
        if ep.P_allow_bar:
            data.append(["P admissível (P_cr/SF)", _fmt(ep.P_allow_bar, 4, "bar")])
        if ep.utilization_ratio:
            data.append(["Utilização P_ext/P_allow", _fmt(ep.utilization_ratio, 3, "")])
        if ep.collapse_warning:
            data.append(["Resultado", ep.collapse_warning])
        story.append(table(data))
        for d in (ep.required_additional_data or []):
            story.append(Ps(f"ℹ Dataset adicional requerido: {d}"))
        for w in (ep.warnings or []):
            story.append(Pw(f"⚠ {w}"))
        story.append(Spacer(1, 4*mm))

    # ── 8. Suportes ────────────────────────────────────────────────────────────
    if ctx.support_result:
        story.append(H2("7. Suportes Preliminares"))
        sr = ctx.support_result
        data = [["Parâmetro", "Valor"]]
        data.append(["Classificação", sr.classification_level])
        if sr.weight_pipe_kgm is not None:
            data.append(["Peso tubo", _fmt(sr.weight_pipe_kgm, 3, "kg/m")])
        if sr.weight_fluid_kgm is not None:
            data.append(["Peso fluido", _fmt(sr.weight_fluid_kgm, 3, "kg/m")])
        if sr.weight_insulation_kgm is not None:
            data.append(["Peso isolação", _fmt(sr.weight_insulation_kgm, 3, "kg/m")])
        if sr.total_weight_kgm is not None:
            data.append(["Peso total", _fmt(sr.total_weight_kgm, 3, "kg/m")])
        if sr.L_max_m is not None:
            data.append(["Vão máximo", _fmt(sr.L_max_m, 2, "m")])
        if sr.seismic_horizontal_kN is not None:
            data.append(["Carga sísmica horiz.", _fmt(sr.seismic_horizontal_kN, 2, "kN")])
        story.append(table(data))
        for w in (sr.warnings or []):
            story.append(Pw(f"⚠ {w}"))
        story.append(Spacer(1, 4*mm))

    # ── 9. Resultado do Checker ────────────────────────────────────────────────
    story.append(H2("8. Resultado do Checker"))
    if ctx.checker_result:
        cr = ctx.checker_result
        status_color = _status_color(cr.overall_status)
        data = [["Parâmetro", "Valor"]]
        data.append(["Status global", cr.overall_status])
        data.append(["Modo", cr.operation_mode])
        if cr.hydraulic_status:
            data.append(["Status hidráulico", cr.hydraulic_status])
        if cr.thickness_status:
            data.append(["Status espessura", cr.thickness_status])
        if cr.external_pressure_status:
            data.append(["Status pressão externa", cr.external_pressure_status])
        if cr.hydraulic_margin_pct is not None:
            data.append(["Margem hidráulica", _fmt(cr.hydraulic_margin_pct, 1, "%")])
        if cr.thickness_margin_pct is not None:
            data.append(["Margem espessura", _fmt(cr.thickness_margin_pct, 1, "%")])
        if cr.overall_governing_margin_pct is not None:
            data.append(["Margem global", _fmt(cr.overall_governing_margin_pct, 1, "%")])
        if cr.governing_issue:
            data.append(["Questão governante", cr.governing_issue])
        story.append(table(data))
        for w in (cr.warnings or []):
            story.append(Pw(f"⚠ {w}"))
    story.append(Spacer(1, 4*mm))

    # ── 10. Warnings ──────────────────────────────────────────────────────────
    story.append(H2("9. Avisos Técnicos"))
    all_w: list[str] = []
    for src in [ctx.fluid_properties, ctx.hydraulic_result, ctx.thickness_result,
                ctx.external_pressure_result, ctx.support_result, ctx.checker_result]:
        if src and hasattr(src, "warnings") and src.warnings:
            all_w.extend(src.warnings)
    if not all_w:
        story.append(P("Sem avisos técnicos adicionais."))
    for w in all_w:
        story.append(Pw(f"⚠ {w}"))
    story.append(Spacer(1, 4*mm))

    # ── 11. Limitações e Simplificações ───────────────────────────────────────
    story.append(H2("10. Limitações e Simplificações"))
    limitacoes = [
        "Colebrook-White: solução iterativa (A-HI-001)",
        "K-values de fittings: Crane TP-410 — literatura pública (A-HI-002)",
        "Modelo compressível: isotérmico — conservativo para gases frios (A-HC-001)",
        "Tensões admissíveis: subset de literatura pública (A-MAT-001)",
        "Suportes: análise preliminar — não substitui análise de flexibilidade (A-SUP-001)",
        "Pressão externa/colapso: Windenburg-Trilling + DATASET_MISSING para método ASME rigoroso (A-TE-001)",
    ]
    for lim in limitacoes:
        story.append(Ps(f"• {lim}"))
    story.append(Spacer(1, 4*mm))

    # ── 12. Proveniência dos Datasets ─────────────────────────────────────────
    story.append(H2("11. Proveniência dos Dados"))
    prov_data = [
        ["Dataset", "Fonte", "Status"],
        ["Propriedades do fluido", "CoolProp 6.x / aproximação", "Público"],
        ["Catálogo dimensional", "ASME B36.10M-2015 / B36.19M-2004", "Dados públicos"],
        ["Tensões admissíveis", "Literatura pública (A106, A53, TP304/316)", "Subset público"],
        ["K-values fittings", "Crane TP-410 (2013)", "Referência pública"],
        ["Equações hidráulicas", "Darcy-Weisbach, Colebrook-White, Manning", "Domínio público"],
        ["Espessura interna", f"ASME B31.3/B31.9/EN 13480 — fórmulas públicas", "Fórmulas públicas"],
    ]
    story.append(table(prov_data, col_widths=[70*mm, 80*mm, 30*mm]))
    story.append(Spacer(1, 4*mm))

    # ── 13. Citações Normativas ───────────────────────────────────────────────
    story.append(H2("12. Citações Normativas"))
    if ctx.citations:
        cit_data = [["Norma", "Edição", "Cláusula", "Descrição"]]
        for c in ctx.citations:
            cit_data.append([c.standard_id, c.edition, c.clause, c.description])
        story.append(table(cit_data, col_widths=[40*mm, 25*mm, 25*mm, 80*mm]))
    story.append(Spacer(1, 4*mm))

    # ── 14. Rodapé de uso restrito ────────────────────────────────────────────
    story.append(HR())
    story.append(Paragraph(
        "AVISO DE USO RESTRITO: Este memorial foi gerado automaticamente pelo SIDCT v1.0. "
        "Os resultados são preliminares e devem ser verificados por engenheiro qualificado "
        "antes de qualquer utilização em projecto. "
        "Tensões admissíveis baseadas em subset de literatura pública — "
        "verificar com Appendix A da norma aplicável na edição contratual. "
        "Não reproduzir tabelas normativas proprietárias.",
        style_footer,
    ))

    doc.build(story)
    pdf_bytes = buffer.getvalue()

    if output_path:
        Path(output_path).write_bytes(pdf_bytes)

    return pdf_bytes
