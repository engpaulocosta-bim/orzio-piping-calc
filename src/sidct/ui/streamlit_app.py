"""SIDCT — Streamlit Application."""
from __future__ import annotations
import sys
import io
from pathlib import Path

# Adicionar src ao path
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

# ── CSS customizado ───────────────────────────────────────────────────────────
st.markdown("""
<style>
.status-APPROVED { color: #27ae60; font-weight: bold; }
.status-CONSERVATIVE { color: #2980b9; font-weight: bold; }
.status-INSUFFICIENT { color: #e67e22; font-weight: bold; }
.status-CRITICAL { color: #c0392b; font-weight: bold; }
.status-DATASET_MISSING { color: #8e44ad; font-weight: bold; }
.status-OUT_OF_SCOPE { color: #7f8c8d; font-weight: bold; }
.warning-box { background: #fff3cd; padding: 8px; border-radius: 4px;
               border-left: 4px solid #ffc107; margin: 4px 0; }
.disclaimer { background: #f8d7da; padding: 8px; border-radius: 4px;
              border-left: 4px solid #dc3545; margin: 8px 0; font-size: 0.85em; }
</style>
""", unsafe_allow_html=True)


def _render_status(status: str) -> str:
    colors = {
        "APPROVED": "#27ae60", "CONSERVATIVE": "#2980b9", "INSUFFICIENT": "#e67e22",
        "CRITICAL": "#c0392b", "DATASET_MISSING": "#8e44ad", "OUT_OF_SCOPE": "#7f8c8d",
        "WARNING": "#f39c12", "CALCULATED": "#27ae60",
    }
    c = colors.get(status, "#333")
    return f'<span style="color:{c}; font-weight:bold;">{status}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ SIDCT v1.0")
    st.caption("Sistema Integrado de Dimensionamento de Tubagens Industriais e Data Centre")
    st.divider()

    mode = st.selectbox(
        "Modo de Operação",
        ["Dimensionamento (nova linha)", "Conferência (projecto recebido)", "Batch CSV"],
        key="mode"
    )

    st.divider()

    profile_options = {
        "glass_factory_industrial_eu": "Fábrica Vidro / Industrial (EU)",
        "glass_factory_industrial_us": "Fábrica Vidro / Industrial (US)",
        "industrial_utilities_eu": "Utilities Industriais (EU)",
        "industrial_utilities_brazil": "Utilities Industriais (Brasil)",
        "datacentre_building_services_eu": "Data Centre / Building (EU)",
        "datacentre_building_services_us": "Data Centre / Building (US)",
        "fire_protection_en": "Protecção Incêndio (EN 12845)",
        "fire_protection_us": "Protecção Incêndio (NFPA 13)",
        "custom": "Personalizado",
    }
    profile = st.selectbox(
        "Perfil de Projecto",
        options=list(profile_options.keys()),
        format_func=lambda x: profile_options[x],
        key="profile",
    )

    service_options = {
        "compressed_air": "Ar Comprimido",
        "natural_gas": "Gás Natural",
        "potable_water": "Água Potável",
        "service_water": "Água de Serviço",
        "osmotized_water": "Água Osmotizada",
        "chilled_water": "Chilled Water",
        "condenser_water": "Condenser Water",
        "vacuum_utility": "Vácuo Utilitário",
        "sanitary_drainage": "Drenagem Sanitária",
        "rainwater": "Água Pluvial",
        "fire_water": "Protecção Incêndio",
    }
    service = st.selectbox(
        "Serviço",
        options=list(service_options.keys()),
        format_func=lambda x: service_options[x],
        key="service",
    )

    jurisdiction = st.selectbox("JurisdiÃ§Ã£o", ["EU", "US", "Brazil", "international"], key="jurisdiction")
    mapped_materials = [
        option.sidct_material
        for option in get_material_options(service, jurisdiction)
        if option.calculation_ready and option.sidct_material
    ]
    material_options = mapped_materials or ["A106 GrB", "A53 GrB", "A312 TP304", "A312 TP316"]
    material = st.selectbox("Material", material_options, key="material")

    catalog_values = available_catalogs_for_material(material, jurisdiction) or ["ASME_B36_10M", "ASME_B36_19M"]
    catalog_options = {
        "ASME_B36_10M": "B36.10M (Carbono)",
        "ASME_B36_19M": "B36.19M (Inox)",
        "PVC_EN1452": "PVC-U EN/ISO 1452",
        "PVC_ASTMD1785": "PVC-U ASTM D1785",
        "PE_EN12201": "PE100 EN 12201 / ISO 4427",
        "PPR_ISO15874": "PP-R ISO 15874",
    }
    # Auto-selecção de catálogo
    default_cat = default_catalog_for_material(material, jurisdiction) or catalog_values[0]
    catalog = st.selectbox(
        "Catálogo Dimensional",
        options=catalog_values,
        format_func=lambda x: catalog_options.get(x, x),
        index=catalog_values.index(default_cat) if default_cat in catalog_values else 0,
        key="catalog",
    )

    st.divider()
    st.caption("SIDCT v1.0 — Uso restrito a engenheiros qualificados")


# ── Área principal ─────────────────────────────────────────────────────────────
st.title(f"SIDCT — {profile_options.get(profile, profile)}")
st.caption(f"Serviço: {service_options.get(service, service)} | Material: {material} | Catálogo: {catalog}")

# Aviso de uso restrito
st.markdown("""
<div class="disclaimer">
⚠️ <strong>Uso Restrito</strong>: Ferramenta de apoio a engenheiros qualificados.
Resultados devem ser verificados antes de uso em projecto.
Tensões admissíveis de literatura pública (subset) — verificar com edição contratual da norma.
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# MODO: Dimensionamento / Conferência
# ─────────────────────────────────────────────────────────────────────────────
GRAVITY_SERVICES = {"sanitary_drainage", "rainwater"}
COMPRESSIBLE_SERVICES = {"compressed_air", "natural_gas"}
VACUUM_SERVICES = {"vacuum_utility"}

if mode in ("Dimensionamento (nova linha)", "Conferência (projecto recebido)"):
    op_mode = "calculate_new" if "Dimensionamento" in mode else "check_received"

    col1, col2, col3 = st.columns(3)

    with col1:
        st.subheader("Dados de Projecto")
        project_name = st.text_input("Nome do Projecto", value="PROJ-001", key="proj_name")
        line_tag = st.text_input("Tag da Linha", value="L-001", key="line_tag")
        design_notes = st.text_area("Notas", height=60, key="notes")

    with col2:
        st.subheader("Condições de Operação")
        P_oper = st.number_input("P operação [barg]", value=7.0, step=0.5, key="P_oper")
        T_oper = st.number_input("T operação [°C]", value=35.0, step=5.0, key="T_oper")
        P_design = st.number_input("P projecto [barg]", value=10.0, step=0.5, key="P_design")
        T_design = st.number_input("T projecto [°C]", value=50.0, step=5.0, key="T_design")

    with col3:
        st.subheader("Caudal e Geometria")
        # Unidades de caudal adaptativas
        if service in GRAVITY_SERVICES:
            flow_basis_opts = ["L/s", "m3/h"]
        elif service in COMPRESSIBLE_SERVICES:
            flow_basis_opts = ["Nm3/h", "Sm3/h", "m3/h", "kg/s"]
        else:
            flow_basis_opts = ["m3/h", "L/s", "gpm"]
        flow_basis = st.selectbox("Unidade caudal", flow_basis_opts, key="flow_basis")
        flow_rate = st.number_input("Caudal", value=300.0, step=10.0, key="flow_rate")
        line_length = st.number_input("Comprimento [m]", value=150.0, step=10.0, key="line_len")
        elev_delta = st.number_input("Δ elevação [m]", value=0.0, step=1.0, key="elev_delta")

    # Campos condicionais
    col4, col5 = st.columns(2)
    with col4:
        st.subheader("Corrosão e Isolação")
        ca = st.number_input("Corrosion Allowance [mm]", value=1.5 if "TP" not in material else 0.0,
                              step=0.5, min_value=0.0, key="ca")
        ins_thick = st.number_input("Espessura isolação [mm]", value=50.0, step=10.0, min_value=0.0, key="ins_t")
        ins_density = st.number_input("Densidade isolação [kg/m³]", value=100.0, step=10.0, key="ins_d")

    with col5:
        st.subheader("Critérios")
        allowable_dp = st.number_input("ΔP admissível [bar]", value=0.5, step=0.05, min_value=0.0, key="dp_allow")
        residual_p = st.number_input("P residual mínima [barg]", value=0.0, step=0.5, min_value=0.0, key="res_p")

    # Campos específicos por regime
    slope_mm_m = None
    vacuum_target = None

    if service in GRAVITY_SERVICES:
        st.subheader("Escoamento Gravitário (obrigatório)")
        slope_mm_m = st.number_input("Inclinação [mm/m]", value=10.0, step=1.0, min_value=0.1, key="slope")

    if service in VACUUM_SERVICES:
        st.subheader("Vácuo (obrigatório)")
        vacuum_target = st.number_input("Pressão alvo [mbar abs]", value=10.0, step=1.0, min_value=0.01, key="vac")

    # Campos de conferência
    DN_received = None
    sch_received = None
    if op_mode == "check_received":
        st.subheader("Dados Recebidos (Conferência)")
        c1, c2 = st.columns(2)
        with c1:
            DN_received = st.number_input("DN recebido [mm]", value=100.0, step=25.0, min_value=6.0, key="dn_recv")
        with c2:
            sch_received = st.text_input("Schedule / WT recebido", value="SCH40", key="sch_recv")

    # Fittings simplificado
    st.subheader("Fittings (opcional)")
    n_90lr = st.number_input("Nº cotovelos 90° LR", value=4, step=1, min_value=0, key="n_90lr")
    n_gate = st.number_input("Nº válvulas de gaveta", value=1, step=1, min_value=0, key="n_gate")

    # ── Botão de Calcular ──────────────────────────────────────────────────────
    if st.button("🔢 Calcular", type="primary", key="calc_btn"):
        from sidct.models import LineInput, FittingItem, ValveItem
        from sidct.engines.selector import run_full_calculation

        # Construir fittings
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

            with st.spinner("A calcular..."):
                ctx = run_full_calculation(inp)

            st.session_state["last_ctx"] = ctx
            st.success("Cálculo concluído!")

        except Exception as e:
            st.error(f"Erro: {e}")
            st.session_state.pop("last_ctx", None)

    # ── Resultados ─────────────────────────────────────────────────────────────
    if "last_ctx" in st.session_state:
        ctx = st.session_state["last_ctx"]

        st.divider()
        st.subheader("Resultados")

        # Status global
        if ctx.checker_result:
            status = ctx.checker_result.overall_status
            st.markdown(f"**Status Global:** {_render_status(status)}", unsafe_allow_html=True)

        # Tabs de resultados
        tab_hyd, tab_thick, tab_ext, tab_sup, tab_checker, tab_warn = st.tabs([
            "Hidráulica", "Espessura", "Pressão Externa", "Suportes", "Checker", "Avisos"
        ])

        with tab_hyd:
            if ctx.hydraulic_result:
                hr = ctx.hydraulic_result
                col_a, col_b = st.columns(2)
                with col_a:
                    st.metric("DN Governante", f"{hr.DN_governing_mm:.0f} mm" if hr.DN_governing_mm else "N/A")
                    st.metric("Velocidade", f"{hr.velocity_ms:.2f} m/s" if hr.velocity_ms else "N/A")
                with col_b:
                    st.metric("ΔP Total", f"{hr.dp_total_bar:.4f} bar" if hr.dp_total_bar else "N/A")
                    st.metric("Reynolds", f"{hr.Re:.0f}" if hr.Re else "N/A")
                if hr.mach_number:
                    st.metric("Mach", f"{hr.mach_number:.4f}")
                if hr.pressure_ratio:
                    st.metric("P2/P1", f"{hr.pressure_ratio:.4f}")
                st.caption(f"Status: {hr.status} | Regime: {hr.regime}")

        with tab_thick:
            if ctx.thickness_result:
                tr = ctx.thickness_result
                c1, c2, c3 = st.columns(3)
                with c1:
                    st.metric("t pressão", f"{tr.t_pressure_only_mm:.3f} mm" if tr.t_pressure_only_mm else "N/A")
                with c2:
                    st.metric("t + CA", f"{tr.t_plus_ca_mm:.3f} mm" if tr.t_plus_ca_mm else "N/A")
                with c3:
                    st.metric("t requerido (após mill tol.)", f"{tr.t_after_mill_tolerance_mm:.3f} mm" if tr.t_after_mill_tolerance_mm else "N/A")
                st.info(f"Schedule seleccionado: **{tr.selected_schedule or 'N/A'}** | S = {tr.allowable_stress_mpa:.1f} MPa" if tr.allowable_stress_mpa else "")
                st.caption(f"Código: {tr.governing_code} | Cláusula: {tr.governing_clause}")

        with tab_ext:
            if ctx.external_pressure_result:
                ep = ctx.external_pressure_result
                if ep.utilization_ratio:
                    st.metric("Utilização P_ext/P_allow", f"{ep.utilization_ratio:.3f}")
                    st.metric("P admissível", f"{ep.P_allow_bar:.4f} bar" if ep.P_allow_bar else "N/A")
                st.caption(f"Método: {ep.method_status}")
                if ep.collapse_warning:
                    st.warning(ep.collapse_warning)
            else:
                st.info("Verificação de pressão externa não aplicável a este serviço.")

        with tab_sup:
            if ctx.support_result:
                sr = ctx.support_result
                c1, c2 = st.columns(2)
                with c1:
                    st.metric("Vão máximo", f"{sr.L_max_m:.2f} m" if sr.L_max_m else "N/A")
                    st.metric("Peso total", f"{sr.total_weight_kgm:.3f} kg/m" if sr.total_weight_kgm else "N/A")
                with c2:
                    st.metric("Carga sísmica", f"{sr.seismic_horizontal_kN:.2f} kN" if sr.seismic_horizontal_kN else "N/A")
                st.caption(f"Classificação: {sr.classification_level}")
            else:
                st.info("Suportes não calculados.")

        with tab_checker:
            if ctx.checker_result:
                cr = ctx.checker_result
                st.markdown(f"**Status:** {_render_status(cr.overall_status)}", unsafe_allow_html=True)
                if cr.hydraulic_margin_pct is not None:
                    st.metric("Margem hidráulica", f"{cr.hydraulic_margin_pct:.1f}%")
                if cr.thickness_margin_pct is not None:
                    st.metric("Margem espessura", f"{cr.thickness_margin_pct:.1f}%")
                if cr.governing_issue:
                    st.error(f"Questão governante: {cr.governing_issue}")
                if cr.dataset_missing_items:
                    st.warning(f"Datasets ausentes: {', '.join(cr.dataset_missing_items)}")

        with tab_warn:
            all_w: list[str] = []
            for src in [ctx.fluid_properties, ctx.hydraulic_result, ctx.thickness_result,
                        ctx.external_pressure_result, ctx.support_result, ctx.checker_result]:
                if src and hasattr(src, "warnings") and src.warnings:
                    all_w.extend(src.warnings)
            if all_w:
                for w in all_w:
                    st.warning(w)
            else:
                st.success("Sem avisos técnicos.")

        # ── Exportar PDF ──────────────────────────────────────────────────────
        st.divider()
        col_pdf, col_csv = st.columns(2)
        with col_pdf:
            if st.button("📄 Gerar Memorial PDF"):
                try:
                    from sidct.reports.memorial_pdf import generate_pdf
                    pdf_bytes = generate_pdf(ctx)
                    st.download_button(
                        label="⬇️ Descarregar PDF",
                        data=pdf_bytes,
                        file_name=f"SIDCT_{ctx.line_tag}.pdf",
                        mime="application/pdf",
                    )
                except ImportError:
                    st.error("ReportLab não instalado. Execute: pip install reportlab")
                except Exception as e:
                    st.error(f"Erro ao gerar PDF: {e}")
        with col_csv:
            if st.button("📊 Exportar CSV"):
                import csv, io as sio
                buf = sio.StringIO()
                w = csv.writer(buf)
                w.writerow(["Campo", "Valor"])
                if ctx.hydraulic_result:
                    hr = ctx.hydraulic_result
                    w.writerow(["DN_governing_mm", hr.DN_governing_mm])
                    w.writerow(["velocity_ms", hr.velocity_ms])
                    w.writerow(["dp_total_bar", hr.dp_total_bar])
                if ctx.thickness_result:
                    tr = ctx.thickness_result
                    w.writerow(["t_required_mm", tr.t_after_mill_tolerance_mm])
                    w.writerow(["selected_schedule", tr.selected_schedule])
                if ctx.checker_result:
                    cr = ctx.checker_result
                    w.writerow(["overall_status", cr.overall_status])
                st.download_button(
                    "⬇️ Descarregar CSV",
                    buf.getvalue().encode("utf-8"),
                    file_name=f"SIDCT_{ctx.line_tag}.csv",
                    mime="text/csv",
                )

# ─────────────────────────────────────────────────────────────────────────────
# MODO: Batch CSV
# ─────────────────────────────────────────────────────────────────────────────
elif mode == "Batch CSV":
    st.subheader("Processamento Batch — CSV")
    st.info(
        "Carregue um ficheiro CSV com múltiplas linhas. "
        "Ver template em /data/templates/batch_template.csv"
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
                    st.download_button("⬇️ Resultados CSV", result_csv, "batch_results.csv", "text/csv")
                with c2:
                    if errors_csv:
                        st.download_button("⬇️ Erros CSV", errors_csv, "batch_errors.csv", "text/csv")
            except Exception as e:
                st.error(f"Erro no batch: {e}")

    # Template download
    template_path = _SRC / "data" / "templates" / "batch_template.csv"
    if template_path.exists():
        st.download_button(
            "⬇️ Descarregar Template Batch",
            template_path.read_bytes(),
            "batch_template.csv",
            "text/csv",
        )
