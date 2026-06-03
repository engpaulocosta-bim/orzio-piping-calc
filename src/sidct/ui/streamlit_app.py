"""SIDCT — Streamlit Application."""
from __future__ import annotations
import datetime
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

import streamlit as st

from sidct.materials import available_catalogs_for_material, default_catalog_for_material
from sidct.system_pipe_mapping import get_material_options

# ── Configuração da página ────────────────────────────────────────────────────
st.set_page_config(
    page_title="SIDCT — Dimensionamento de Tubagens",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS (idêntico ao SFSC, adaptado para SIDCT) ───────────────────────────────
st.markdown("""
<style>
    .main-title  {font-size:2rem; font-weight:800; color:#1447E6; margin-bottom:0}
    .sub-title   {font-size:1rem; color:#64748B; margin-top:0}
    .status-pass     {background:#DCFCE7; color:#166534; padding:6px 12px; border-radius:6px; font-weight:600}
    .status-fail     {background:#FEE2E2; color:#991B1B; padding:6px 12px; border-radius:6px; font-weight:600}
    .status-marginal {background:#FEF9C3; color:#713F12; padding:6px 12px; border-radius:6px; font-weight:600}
    .status-info     {background:#DBEAFE; color:#1E40AF; padding:6px 12px; border-radius:6px; font-weight:600}
    .eta-ok   {color:#16A34A; font-weight:600}
    .eta-warn {color:#CA8A04; font-weight:600}
    .eta-fail {color:#DC2626; font-weight:600}
    div[data-testid="stMetricValue"] {font-size:1.3rem}
    .disclaimer {background:#FEE2E2; color:#991B1B; padding:8px 12px; border-radius:6px;
                 border-left:4px solid #DC2626; margin:8px 0; font-size:0.85em}
</style>
""", unsafe_allow_html=True)

# ── Cabeçalho da área principal ───────────────────────────────────────────────
st.markdown('<p class="main-title">SIDCT — Sistema Integrado de Dimensionamento de Tubagens</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-title">Dimensionamento e conferência de tubagens industriais e de data centre, com memorial PDF auditável</p>', unsafe_allow_html=True)
st.divider()

# ── Helpers ────────────────────────────────────────────────────────────────────
GRAVITY_SERVICES     = {"sanitary_drainage", "rainwater"}
COMPRESSIBLE_SERVICES = {"compressed_air", "natural_gas"}
VACUUM_SERVICES      = {"vacuum_utility"}

_STATUS_CSS = {
    "APPROVED":        "status-pass",
    "CONSERVATIVE":    "status-info",
    "INSUFFICIENT":    "status-marginal",
    "CRITICAL":        "status-fail",
    "DATASET_MISSING": "status-fail",
    "OUT_OF_SCOPE":    "status-marginal",
    "WARNING":         "status-marginal",
    "CALCULATED":      "status-pass",
}

def _status_badge(status: str) -> str:
    css = _STATUS_CSS.get(status, "status-info")
    return f'<span class="{css}">{status}</span>'

# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR — entradas
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.header("Configuração")

    # ── 1. Identificação ──────────────────────────────────────────────────────
    st.subheader("1. Identificação")
    project_name = st.text_input("Nome do projecto", value="PROJ-001")
    line_tag     = st.text_input("Tag da linha", value="L-001")
    design_notes = st.text_area("Notas", height=60)

    # ── 2. Modo de Operação ───────────────────────────────────────────────────
    st.subheader("2. Modo de Operação")
    mode_val = st.radio(
        "Modo",
        ["dimension", "verify", "batch"],
        horizontal=True,
        format_func=lambda x: {"dimension": "Dimensionar", "verify": "Conferir", "batch": "Batch CSV"}[x],
    )

    # ── 3. Perfil / Jurisdição ────────────────────────────────────────────────
    st.subheader("3. Perfil / Jurisdição")
    profile_options = {
        "glass_factory_industrial_eu":  "Fábrica Vidro / Industrial (EU)",
        "glass_factory_industrial_us":  "Fábrica Vidro / Industrial (US)",
        "industrial_utilities_eu":      "Utilities Industriais (EU)",
        "industrial_utilities_brazil":  "Utilities Industriais (Brasil)",
        "datacentre_building_services_eu": "Data Centre / Building (EU)",
        "datacentre_building_services_us": "Data Centre / Building (US)",
        "fire_protection_en":           "Protecção Incêndio (EN 12845)",
        "fire_protection_us":           "Protecção Incêndio (NFPA 13)",
        "custom":                       "Personalizado",
    }
    profile = st.selectbox(
        "Perfil de projecto",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x],
    )
    jurisdiction = st.selectbox("Jurisdição", ["EU", "US", "Brazil", "international"])

    # ── 4. Serviço ────────────────────────────────────────────────────────────
    st.subheader("4. Serviço")
    service_options = {
        "compressed_air":    "Ar Comprimido",
        "natural_gas":       "Gás Natural",
        "potable_water":     "Água Potável",
        "service_water":     "Água de Serviço",
        "osmotized_water":   "Água Osmotizada",
        "chilled_water":     "Chilled Water",
        "condenser_water":   "Condenser Water",
        "vacuum_utility":    "Vácuo Utilitário",
        "sanitary_drainage": "Drenagem Sanitária",
        "rainwater":         "Água Pluvial",
        "fire_water":        "Protecção Incêndio",
    }
    service = st.selectbox(
        "Serviço",
        options=list(service_options.keys()),
        format_func=lambda x: service_options[x],
    )

    # ── 5. Material e Catálogo ────────────────────────────────────────────────
    st.subheader("5. Material e Catálogo")
    mapped_materials = [
        opt.sidct_material
        for opt in get_material_options(service, jurisdiction)
        if opt.calculation_ready and opt.sidct_material
    ]
    material_list = mapped_materials or ["A106 GrB", "A53 GrB", "A312 TP304", "A312 TP316"]
    material = st.selectbox("Material", material_list)

    catalog_values = available_catalogs_for_material(material, jurisdiction) or ["ASME_B36_10M"]
    catalog_labels = {
        "ASME_B36_10M":   "B36.10M (Carbono)",
        "ASME_B36_19M":   "B36.19M (Inox)",
        "PVC_EN1452":     "PVC-U EN/ISO 1452",
        "PVC_ASTMD1785":  "PVC-U ASTM D1785",
        "PE_EN12201":     "PE100 EN 12201",
        "PPR_ISO15874":   "PP-R ISO 15874",
    }
    default_cat = default_catalog_for_material(material, jurisdiction) or catalog_values[0]
    catalog = st.selectbox(
        "Catálogo dimensional",
        options=catalog_values,
        format_func=lambda x: catalog_labels.get(x, x),
        index=catalog_values.index(default_cat) if default_cat in catalog_values else 0,
    )

    # ── 6. Condições de Operação ──────────────────────────────────────────────
    st.subheader("6. Condições de Operação")
    P_oper   = st.number_input("P operação [barg]",   value=7.0,  step=0.5)
    T_oper   = st.number_input("T operação [°C]",     value=35.0, step=5.0)
    P_design = st.number_input("P projecto [barg]",   value=10.0, step=0.5)
    T_design = st.number_input("T projecto [°C]",     value=50.0, step=5.0)

    # ── 7. Caudal, Geometria e Opções ─────────────────────────────────────────
    st.subheader("7. Caudal, Geometria e Opções")

    if service in GRAVITY_SERVICES:
        flow_basis_opts = ["L/s", "m3/h"]
    elif service in COMPRESSIBLE_SERVICES:
        flow_basis_opts = ["Nm3/h", "Sm3/h", "m3/h", "kg/s"]
    else:
        flow_basis_opts = ["m3/h", "L/s", "gpm"]
    flow_basis   = st.selectbox("Unidade caudal", flow_basis_opts)
    flow_rate    = st.number_input("Caudal", value=300.0, step=10.0)
    line_length  = st.number_input("Comprimento [m]", value=150.0, step=10.0)
    elev_delta   = st.number_input("Δ elevação [m]", value=0.0, step=1.0)

    ca           = st.number_input("Corrosion allowance [mm]",
                                   value=1.5 if "TP" not in material else 0.0,
                                   step=0.5, min_value=0.0)
    ins_thick    = st.number_input("Espessura isolação [mm]", value=50.0, step=10.0, min_value=0.0)
    ins_density  = st.number_input("Densidade isolação [kg/m³]", value=100.0, step=10.0)
    allowable_dp = st.number_input("ΔP admissível [bar]", value=0.5, step=0.05, min_value=0.0)
    residual_p   = st.number_input("P residual mínima [barg]", value=0.0, step=0.5, min_value=0.0)

    # Campos condicionais por regime
    slope_mm_m     = None
    vacuum_target  = None
    DN_received    = None
    sch_received   = None

    if service in GRAVITY_SERVICES:
        slope_mm_m = st.number_input("Inclinação [mm/m]", value=10.0, step=1.0, min_value=0.1)

    if service in VACUUM_SERVICES:
        vacuum_target = st.number_input("Pressão alvo [mbar abs]", value=10.0, step=1.0, min_value=0.01)

    if mode_val == "verify":
        st.markdown("**Dados recebidos (Conferência)**")
        DN_received  = st.number_input("DN recebido [mm]", value=100.0, step=25.0, min_value=6.0)
        sch_received = st.text_input("Schedule / WT recebido", value="SCH40")

    # Fittings
    st.markdown("**Fittings**")
    n_90lr = st.number_input("Nº cotovelos 90° LR", value=4, step=1, min_value=0)
    n_gate = st.number_input("Nº válvulas de gaveta", value=1, step=1, min_value=0)

    # ── Botão Calcular ─────────────────────────────────────────────────────────
    st.divider()
    calc_btn = st.button("▶ Calcular", type="primary", use_container_width=True)


# ════════════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL — Batch CSV
# ════════════════════════════════════════════════════════════════════════════════
if mode_val == "batch":
    st.subheader("Processamento Batch — CSV")
    st.info(
        "Carregue um ficheiro CSV com múltiplas linhas de tubagem. "
        "Ver template em `data/templates/batch_template.csv`."
    )
    uploaded = st.file_uploader("Carregar CSV", type=["csv"])
    if uploaded and st.button("▶️ Processar Batch"):
        with st.spinner("A processar batch..."):
            try:
                from sidct.batch.csv_runner import run_batch_from_bytes
                result_csv, errors_csv, summary = run_batch_from_bytes(uploaded.read())
                st.success(f"Batch concluído: {summary}")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button("⬇️ Resultados CSV", result_csv, "batch_results.csv", "text/csv",
                                       use_container_width=True)
                with c2:
                    if errors_csv:
                        st.download_button("⬇️ Erros CSV", errors_csv, "batch_errors.csv", "text/csv",
                                           use_container_width=True)
            except Exception as e:
                st.error(f"Erro no batch: {e}")

    template_path = _SRC / "data" / "templates" / "batch_template.csv"
    if template_path.exists():
        st.download_button(
            "⬇️ Descarregar Template Batch",
            template_path.read_bytes(),
            "batch_template.csv",
            "text/csv",
        )

# ════════════════════════════════════════════════════════════════════════════════
# ÁREA PRINCIPAL — Dimensionamento / Conferência
# ════════════════════════════════════════════════════════════════════════════════
else:
    op_mode = "calculate_new" if mode_val == "dimension" else "check_received"

    # ── Cálculo ────────────────────────────────────────────────────────────────
    if calc_btn:
        from sidct.models import LineInput, FittingItem, ValveItem
        from sidct.engines.selector import run_full_calculation

        fittings = []
        if n_90lr > 0:
            fittings.append(FittingItem(fitting_type="90_LR_ELBOW", quantity=n_90lr))
        valves = []
        if n_gate > 0:
            valves.append(ValveItem(valve_type="GATE_VALVE_FULL_OPEN", quantity=n_gate))

        try:
            inp = LineInput(
                project_name=project_name,
                line_tag=line_tag,
                service=service,
                project_profile=profile,
                jurisdiction=jurisdiction,
                fluid_name=service_options.get(service, service),
                P_oper_bar=P_oper,
                T_oper_c=T_oper,
                P_design_bar=P_design,
                T_design_c=T_design,
                flow_rate=flow_rate,
                flow_rate_basis=flow_basis,
                line_length_m=line_length,
                elevation_delta_m=elev_delta,
                material=material,
                dimensional_catalog=catalog,
                corrosion_allowance_mm=ca,
                insulation_thickness_mm=ins_thick,
                insulation_density_kgm3=ins_density,
                fittings=fittings,
                valves=valves,
                allowable_pressure_drop_bar=allowable_dp if allowable_dp > 0 else None,
                required_residual_pressure_bar=residual_p if residual_p > 0 else None,
                DN_received_mm=DN_received,
                schedule_or_wall_received=sch_received,
                slope_mm_m=slope_mm_m,
                vacuum_target_mbara=vacuum_target,
                design_notes=design_notes,
                operation_mode=op_mode,
            )
            with st.spinner("A calcular…"):
                ctx = run_full_calculation(inp)
            st.session_state["last_ctx"] = ctx
        except Exception as e:
            st.error(f"**Erro:** {e}")
            st.exception(e)
            st.session_state.pop("last_ctx", None)

    # ── Resultados ─────────────────────────────────────────────────────────────
    if "last_ctx" in st.session_state:
        ctx = st.session_state["last_ctx"]
        hr  = ctx.hydraulic_result
        tr  = ctx.thickness_result
        cr  = ctx.checker_result
        sr  = ctx.support_result

        # 4 métricas de topo (igual ao SFSC)
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Status",       cr.overall_status if cr else "—")
        col_s2.metric("DN Governante",
                      f"{hr.DN_governing_mm:.0f} mm" if hr and hr.DN_governing_mm else "—")
        col_s3.metric("Velocidade",
                      f"{hr.velocity_ms:.2f} m/s" if hr and hr.velocity_ms else "—")
        col_s4.metric("ΔP Total",
                      f"{hr.dp_total_bar:.4f} bar" if hr and hr.dp_total_bar else "—")

        tabs = st.tabs(["Hidráulica", "Espessura", "Pressão Externa", "Suportes", "Checker", "Avisos", "Citações"])

        # ── Tab 1: Hidráulica ──────────────────────────────────────────────────
        with tabs[0]:
            if hr:
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("DN Governante",
                              f"{hr.DN_governing_mm:.0f} mm" if hr.DN_governing_mm else "N/A")
                    st.metric("Velocidade",
                              f"{hr.velocity_ms:.2f} m/s" if hr.velocity_ms else "N/A")
                    st.metric("Reynolds",
                              f"{hr.Re:.0f}" if hr.Re else "N/A")
                with c2:
                    st.metric("ΔP Total",
                              f"{hr.dp_total_bar:.4f} bar" if hr.dp_total_bar else "N/A")
                    if hr.mach_number:
                        st.metric("Mach", f"{hr.mach_number:.4f}")
                    if hr.pressure_ratio:
                        st.metric("P2/P1", f"{hr.pressure_ratio:.4f}")
                st.caption(f"Regime: {hr.regime} | Status: {hr.status}")

        # ── Tab 2: Espessura ───────────────────────────────────────────────────
        with tabs[1]:
            if tr:
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("t pressão",
                              f"{tr.t_pressure_only_mm:.3f} mm" if tr.t_pressure_only_mm else "N/A")
                with c2:
                    st.metric("t + CA",
                              f"{tr.t_plus_ca_mm:.3f} mm" if tr.t_plus_ca_mm else "N/A")
                with c3:
                    st.metric("t requerido (mill tol.)",
                              f"{tr.t_after_mill_tolerance_mm:.3f} mm" if tr.t_after_mill_tolerance_mm else "N/A")
                st.info(
                    f"Schedule seleccionado: **{tr.selected_schedule or 'N/A'}**"
                    + (f" | S = {tr.allowable_stress_mpa:.1f} MPa" if tr.allowable_stress_mpa else "")
                )
                st.caption(f"Código: {tr.governing_code} | Cláusula: {tr.governing_clause}")

        # ── Tab 3: Pressão Externa ─────────────────────────────────────────────
        with tabs[2]:
            ep = ctx.external_pressure_result
            if ep:
                if ep.utilization_ratio:
                    st.metric("P_ext / P_allow", f"{ep.utilization_ratio:.3f}")
                if ep.P_allow_bar:
                    st.metric("P admissível", f"{ep.P_allow_bar:.4f} bar")
                st.caption(f"Método: {ep.method_status}")
                if ep.collapse_warning:
                    st.warning(ep.collapse_warning)
            else:
                st.info("Verificação de pressão externa não aplicável a este serviço.")

        # ── Tab 4: Suportes ────────────────────────────────────────────────────
        with tabs[3]:
            if sr:
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Vão máximo",
                              f"{sr.L_max_m:.2f} m" if sr.L_max_m else "N/A")
                    st.metric("Peso total",
                              f"{sr.total_weight_kgm:.3f} kg/m" if sr.total_weight_kgm else "N/A")
                with c2:
                    st.metric("Carga sísmica",
                              f"{sr.seismic_horizontal_kN:.2f} kN" if sr.seismic_horizontal_kN else "N/A")
                st.caption(f"Classificação: {sr.classification_level}")
            else:
                st.info("Suportes não calculados.")

        # ── Tab 5: Checker ─────────────────────────────────────────────────────
        with tabs[4]:
            if cr:
                st.markdown(f"**Status:** {_status_badge(cr.overall_status)}", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if cr.hydraulic_margin_pct is not None:
                        st.metric("Margem hidráulica", f"{cr.hydraulic_margin_pct:.1f}%")
                with c2:
                    if cr.thickness_margin_pct is not None:
                        st.metric("Margem espessura", f"{cr.thickness_margin_pct:.1f}%")
                if cr.governing_issue:
                    st.error(f"Questão governante: {cr.governing_issue}")
                if cr.dataset_missing_items:
                    st.warning(f"Datasets ausentes: {', '.join(cr.dataset_missing_items)}")

        # ── Tab 6: Avisos ──────────────────────────────────────────────────────
        with tabs[5]:
            all_warnings: list[str] = []
            for src in [ctx.fluid_properties, hr, tr,
                        ctx.external_pressure_result, sr, cr]:
                if src and hasattr(src, "warnings") and src.warnings:
                    all_warnings.extend(src.warnings)
            if all_warnings:
                for w in all_warnings:
                    st.warning(w)
            else:
                st.success("Sem avisos técnicos.")

            # Disclaimer fixo
            st.markdown("""
<div class="disclaimer">
⚠️ <strong>Uso restrito a engenheiros qualificados.</strong>
Resultados são preliminares. Tensões admissíveis de literatura pública (subset) —
verificar com a edição contratual da norma aplicável. Nenhuma tabela proprietária
foi reproduzida neste sistema.
</div>""", unsafe_allow_html=True)

        # ── Tab 7: Citações ────────────────────────────────────────────────────
        with tabs[6]:
            import pandas as pd
            citations = getattr(ctx, "citations", [])
            if citations:
                rows = [{"Norma": c.standard_id, "Edição": c.edition,
                         "Cláusula": c.clause, "Descrição": c.description}
                        for c in citations]
                st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            else:
                st.info("Sem citações normativas registadas.")

        # ── Exportar ───────────────────────────────────────────────────────────
        st.divider()
        st.subheader("Exportar memorial")
        col_e1, col_e2 = st.columns(2)

        with col_e1:
            try:
                from sidct.reports.memorial_pdf import generate_pdf
                pdf_bytes = generate_pdf(ctx)
                st.download_button(
                    "📄 Download PDF",
                    data=pdf_bytes,
                    file_name=f"sidct_{line_tag}_{datetime.date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Erro ao gerar PDF: {e}")

        with col_e2:
            import csv, io as sio
            buf = sio.StringIO()
            w = csv.writer(buf)
            w.writerow(["Campo", "Valor"])
            if hr:
                w.writerow(["DN_governing_mm", hr.DN_governing_mm])
                w.writerow(["velocity_ms", hr.velocity_ms])
                w.writerow(["dp_total_bar", hr.dp_total_bar])
            if tr:
                w.writerow(["t_required_mm", tr.t_after_mill_tolerance_mm])
                w.writerow(["selected_schedule", tr.selected_schedule])
            if cr:
                w.writerow(["overall_status", cr.overall_status])
            st.download_button(
                "📋 Download CSV",
                data=buf.getvalue().encode("utf-8"),
                file_name=f"sidct_{line_tag}_{datetime.date.today()}.csv",
                mime="text/csv",
                use_container_width=True,
            )

    # ── Estado inicial — guia de uso ───────────────────────────────────────────
    else:
        st.info(
            "Configure os parâmetros na barra lateral e clique **▶ Calcular**.\n\n"
            "**Serviços disponíveis:**\n"
            "- **Ar Comprimido / Gás Natural**: escoamento compressível isotérmico (Ma < 0.3)\n"
            "- **Água Potável / Serviço / Osmotizada / Chilled / Condenser**: Darcy-Weisbach\n"
            "- **Vácuo Utilitário**: condutância viscosa + verificação de colapso\n"
            "- **Drenagem Sanitária / Água Pluvial**: escoamento gravitário (Manning)\n"
            "- **Protecção Incêndio**: critérios EN 12845 / NFPA 13\n\n"
            "**Perfis suportados:** EU industrial, US industrial, Data Centre, Brasil, "
            "Protecção Incêndio (EN / NFPA)\n\n"
            "**Output:** DN + schedule dimensionados, memorial de cálculo PDF auditável, "
            "export CSV"
        )
