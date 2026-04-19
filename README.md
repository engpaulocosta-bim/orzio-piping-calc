# SIDCT — Sistema Integrado de Dimensionamento, Conferência e Memorial de Cálculo

**v1.0 | 2026-04-19**

Sistema Python profissional para dimensionamento e conferência de tubagens industriais
e de data centre, com geração de memorial de cálculo PDF auditável.

---

## Visão Geral

O SIDCT é uma ferramenta de engenharia séria, construída para engenheiros MEP que precisam de:

- Dimensionar tubagens novas por regime físico e código aplicável;
- Conferir projectos recebidos de terceiros;
- Gerar memorial de cálculo PDF com citações normativas rastreáveis;
- Operar com perfis técnicos distintos, sem mistura de critérios;
- Processar múltiplas linhas em batch (CSV).

---

## Perfis Suportados

| ID | Descrição |
|----|-----------|
| `glass_factory_industrial_eu` | Fábrica de vidro / utilities industriais (Europa) |
| `glass_factory_industrial_us` | Fábrica de vidro / utilities industriais (EUA) |
| `industrial_utilities_eu` | Utilities industriais genéricos (Europa) |
| `industrial_utilities_brazil` | Utilities industriais (Brasil) |
| `datacentre_building_services_eu` | Data centre / building services (Europa) |
| `datacentre_building_services_us` | Data centre / building services (EUA) |
| `fire_protection_en` | Protecção contra incêndio (EN 12845) |
| `fire_protection_us` | Protecção contra incêndio (NFPA 13) |
| `custom` | Perfil personalizado |

---

## Serviços Suportados

| Serviço | Regime Físico |
|---------|---------------|
| `compressed_air` | Compressível (isotérmico) |
| `natural_gas` | Compressível (isotérmico, CH4 se sem composição) |
| `potable_water` | Incompressível (Darcy-Weisbach) |
| `service_water` | Incompressível |
| `osmotized_water` | Incompressível |
| `chilled_water` | Incompressível |
| `condenser_water` | Incompressível |
| `vacuum_utility` | Condutância viscosa + pressão externa (obrigatório) |
| `sanitary_drainage` | Gravitário (Manning) |
| `rainwater` | Gravitário (Manning) |
| `fire_water` | Incompressível com critérios próprios |

---

## Regimes Físicos Implementados

1. **pressurized_incompressible** — Darcy-Weisbach + Colebrook-White iterativo
2. **compressible_gas** — Modelo isotérmico, verificação Ma < 0.3 e P2/P1 > 0.5
3. **gravity_partially_full** — Manning, tubo parcialmente cheio, auto-limpeza
4. **vacuum_conductance** — Condutância viscosa + encaminhamento obrigatório para pressão externa
5. **external_pressure_check** — Windenburg-Trilling; DATASET_MISSING para método ASME rigoroso
6. **fire_protection_special** — Critérios parametrizados por perfil

---

## Limitações

### Técnicas
- Motor compressível: modelo isotérmico (adequado Ma < 0.3, ΔP/P < 50%)
- Gás natural: modelado como CH4 quando composição não fornecida (warning emitido obrigatoriamente)
- Pressão externa/colapso: Windenburg-Trilling (domínio público); para projecto definitivo usar ASME UG-28 ou FEA
- Suportes: ferramenta preliminar — não substitui análise de flexibilidade e tensões
- Manning: regime permanente uniforme (sem transições hidráulicas)

### Datasets
- Tensões admissíveis: subset de literatura pública (A106 GrB, A53 GrB, A312 TP304/316, A333 Gr6)
- Para outros materiais: fornecer ficheiro `/data/user_supplied/stress_<material>.csv`
- NBR 5580: dataset externo — fornecer `/data/user_supplied/nbr5580_catalog.csv`
- Charts ASME Fig. G (pressão externa): não implementados — status DATASET_MISSING

### Normativas
- Nenhuma tabela proprietária de norma foi reproduzida neste sistema
- Fórmulas de dimensionamento são de domínio público (equações publicadas)
- O utilizador deve verificar com a edição contratual da norma aplicável

---

## Instalação

```bash
# Clonar repositório
git clone <repo>
cd iss-industrial-piping-dc

# Instalar dependências
pip install -r requirements.txt
```

**Dependências principais:**
- `pydantic >= 2.5` — validação de modelos
- `coolprop >= 6.6` — propriedades termodinâmicas
- `numpy`, `scipy` — cálculo numérico
- `reportlab >= 4.0` — geração de PDF
- `streamlit >= 1.30` — interface web
- `pandas`, `openpyxl` — batch CSV/XLSX

---

## Execução

### Interface Web (Streamlit)
```bash
python app.py
# ou directamente:
streamlit run src/sidct/ui/streamlit_app.py
```

### Python API
```python
from src.sidct.models import LineInput, FittingItem
from src.sidct.engines.selector import run_full_calculation
from src.sidct.reports.memorial_pdf import generate_pdf

inp = LineInput(
    project_name="PROJ-001",
    line_tag="CA-001",
    service="compressed_air",
    project_profile="glass_factory_industrial_eu",
    jurisdiction="EU",
    fluid_name="Ar comprimido",
    P_oper_bar=7.0, T_oper_c=35.0,
    P_design_bar=10.0, T_design_c=50.0,
    flow_rate=300.0, flow_rate_basis="Nm3/h",
    line_length_m=150.0,
    material="A106 GrB",
    dimensional_catalog="ASME_B36_10M",
    fittings=[FittingItem(fitting_type="90_LR_ELBOW", quantity=4)],
)

ctx = run_full_calculation(inp)
print(f"DN: {ctx.hydraulic_result.DN_governing_mm} mm")
print(f"Schedule: {ctx.thickness_result.selected_schedule}")
print(f"Status: {ctx.checker_result.overall_status}")

# Gerar PDF
pdf = generate_pdf(ctx, "memorial_CA-001.pdf")
```

### Batch CSV
```python
from src.sidct.batch.csv_runner import run_batch_from_csv, write_summary_log

results, errors = run_batch_from_csv("data/templates/batch_template.csv")
write_summary_log(results, errors, "batch_summary.log")
```

---

## Datasets — Como Adicionar

### Material com tensões admissíveis não incluído

1. Copiar template:
   ```bash
   cp data/templates/material_stress_template.csv data/user_supplied/stress_<MATERIAL>.csv
   ```
2. Preencher com valores do Appendix A da norma aplicável
3. O sistema detecta automaticamente o ficheiro

### NBR 5580

1. Copiar template:
   ```bash
   cp data/templates/nbr5580_catalog_template.csv data/user_supplied/nbr5580_catalog.csv
   ```
2. Preencher com dimensões reais da norma
3. Usar `dimensional_catalog="NBR_5580"` com `project_profile="industrial_utilities_brazil"`

---

## Exemplos

Template batch: `data/templates/batch_template.csv`

Casos de teste em `tests/test_integration_cases.py`:
1. Ar comprimido industrial (300 Nm³/h, 7 barg, 150 m, A106 GrB)
2. Água de serviço industrial (50 L/s, 10 barg, 80 m, A53 GrB)
3. Chilled water data centre (120 m³/h, 6 barg, 120 m)
4. Gás natural industrial (500 Nm³/h, 3 barg, 100 m)
5. Vácuo utilitário (10 mbar abs, 30 m) — com verificação de pressão externa
6. Drenagem sanitária (8 L/s, slope 10 mm/m, PVC)
7. Água pluvial (12 L/s, slope 15 mm/m)
8. Fire water EN 12845 (30 L/s, 6 barg)

---

## Interpretação dos Status

| Status | Significado |
|--------|-------------|
| `APPROVED` | Dentro dos critérios |
| `CONSERVATIVE` | Dimensão recebida maior que requerida |
| `INSUFFICIENT` | Dimensão recebida menor que requerida |
| `CRITICAL` | Défice > 10% ou colapso provável |
| `CODE_MISMATCH` | Catálogo/código incompatível com o perfil |
| `DATASET_MISSING` | Dados normativos/técnicos ausentes — **nunca aprovado** |
| `OUT_OF_SCOPE` | Condições fora do envelope do modelo |
| `WARNING` | Resultado válido com alertas técnicos |

---

## Política de Simplificações

Toda simplificação adoptada pelo sistema é:
- Declarada no campo `assumptions_used` do resultado
- Registada no log estruturado
- Incluída explicitamente no PDF (secção "Limitações e Simplificações")
- Identificada por código (ex: A-HI-001, A-HC-002, A-MAT-001)

Ver [`assumptions.yaml`](assumptions.yaml) para listagem completa.

---

## Disclaimers Técnicos

1. **Uso restrito a engenheiros qualificados** — os resultados são preliminares.
2. **Tensões admissíveis** — valores de literatura pública (subset). Verificar com Appendix A da norma aplicável na edição contratual.
3. **Pressão externa/colapso** — Windenburg-Trilling. Para projecto definitivo: ASME UG-28 / FEA.
4. **Suportes** — ferramenta preliminar. Não substitui análise de flexibilidade e tensões.
5. **Fire water** — dimensionamento completo de rede de sprinklers fora de escopo. Apenas verificação de DN e velocidade.
6. **Nenhuma tabela proprietária de norma foi reproduzida** — todas as equações são de domínio público.
7. **API 570** — não é usado como código de projecto. Referenciado apenas para contexto de inspecção/integridade.

---

## Testes

```bash
# Todos os testes
python -m pytest tests/ -v

# Apenas casos de integração obrigatórios
python -m pytest tests/test_integration_cases.py -v

# Com cobertura
python -m pytest tests/ --cov=src/sidct --cov-report=term-missing
```

**Estado actual: 73/73 testes a passar.**

---

## Roadmap

- [ ] Motor de Fanno/Rayleigh para gases compressíveis (Ma > 0.3)
- [ ] Suporte a mistura de gases (composição por cromatografia)
- [ ] Verificação de pressão externa por charts ASME Fig. G (dataset externo)
- [ ] Análise de suportes completa (ASME B31.3 Appendix A stress)
- [ ] Integração com P&ID (import de line tags)
- [ ] NBR 5580 dataset embutido (quando licença disponível)
- [ ] Suporte a materiais plásticos (HDPE, CPVC) com normas dedicadas
- [ ] Export para Excel com formatação profissional
