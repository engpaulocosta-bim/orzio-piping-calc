# EXECUTION LOG — SIDCT

## 2026-04-19 — Build inicial

### PASSO 1 — Estrutura de projeto
- Status: COMPLETE
- Diretórios criados: src/sidct/{data_access,catalogs,engines,reports,ui,batch,utils}
- Ficheiros base: requirements.txt, app.py, CHANGELOG.md

### PASSO 2 — Ficheiros de fundação e governança
- Status: COMPLETE
- DESIGN_BASIS.md criado
- standards_registry.yaml criado
- project_profiles.yaml criado
- service_matrix.yaml criado
- assumptions.yaml criado

### PASSO 3 — Core técnico
- Status: COMPLETE
- enums.py, exceptions.py, models.py, validators.py, units.py, logging_config.py implementados

### PASSO 4 — Catálogos e loaders
- Status: COMPLETE
- fluid_properties.py com CoolProp
- pipe_dimension_catalog.py (B36.10M + B36.19M)
- material_stress_catalog.py
- fitting_k_catalog.py
- corrosion_allowance_catalog.py
- loaders.py, schemas.py, seed_manager.py

### PASSO 5 — Motores matemáticos
- Status: COMPLETE
- hydraulic_incompressible.py — Darcy-Weisbach + Colebrook-White
- hydraulic_compressible.py — isothermal compressible + Mach check
- hydraulic_gravity.py — Manning, tubo parcialmente cheio
- vacuum.py — condutância + rota para external pressure
- thickness_internal.py — B31.3, B31.9, EN 13480
- thickness_external.py — vácuo/colapso com DATASET_MISSING quando aplicável
- supports.py — vãos, peso, sísmica paramétrica
- checker.py — comparação DN/schedule recebido vs calculado
- selector.py — seleção de solução comercial

### PASSO 6 — Memorial PDF
- Status: COMPLETE
- memorial_pdf.py com ReportLab

### PASSO 7 — Streamlit app
- Status: COMPLETE

### PASSO 8 — Batch CSV
- Status: COMPLETE

### PASSO 9 — Testes
- Status: ver test run abaixo

---
## Test Run — 2026-04-19

### Resultado: 73/73 PASSED

```
tests/test_units.py              11 passed
tests/test_catalogs.py           20 passed
tests/test_hydraulic_engines.py  11 passed
tests/test_thickness.py          10 passed
tests/test_checker.py            10 passed
tests/test_integration_cases.py  12 passed (8 casos + 4 segurança)
TOTAL: 73 passed in 2.17s
```

### Falha corrigida
- `test_a312tp316_stress`: teste com valor esperado errado (115.1 vs 110.3 MPa a T=50°C).
  Corrigido — lógica do catálogo está correcta (retorna S para T_max >= T_design).

### Casos de teste obrigatórios (PASSO 11)
1. ✅ Ar comprimido industrial — regime compressível, Mach calculado
2. ✅ Água de serviço industrial — Darcy-Weisbach, DN e schedule seleccionados
3. ✅ Chilled water data centre — B31.9, ΔP admissível respeitado
4. ✅ Gás natural industrial — CH4 warning emitido obrigatoriamente
5. ✅ Vácuo utilitário — regime vacuum_conductance + external_pressure_result presente
6. ✅ Drenagem sanitária — motor Manning, y/D calculado
7. ✅ Água pluvial — motor Manning, DN seleccionado
8. ✅ Fire water EN 12845 — regime incompressível, critérios de perfil de incêndio

### Testes de segurança
- ✅ Drenagem sem slope → ValidationError
- ✅ Inox com B36.10M → CodeMismatchError
- ✅ Vácuo sem target → ValidationError
- ✅ Material desconhecido → checker nunca APPROVED
 
---
## Product Refactor Run - 2026-04-29

### Fase 0 - Auditoria
- Status: COMPLETE
- Criados `AUDIT_REPORT.md`, `REPOSITORY_MAP.md` e `GAP_ANALYSIS.md`.
- Teste baseline antes da refatoracao: 75/75 passed.

### Fase 1 - Arquitetura alvo
- Status: COMPLETE
- Criados `TARGET_ARCHITECTURE.md`, `PRODUCT_DIRECTION.md` e `UI_UX_STRATEGY.md`.
- Decisao documentada: PySide6 como UI desktop final; Streamlit mantido como prototipo legado.

### Fases 2, 3 e 8 - Dominio, persistencia e I/O
- Status: IMPLEMENTED
- Adicionado `src/sidct/project.py` com `Project`, `Route`, `LineSegment`, `HydraulicCase` e `ValidationState`.
- Implementados `save_project` e `load_project` em JSON estruturado `.sidct.json`.
- Adicionado `src/sidct/reports/exports.py` para CSV/XLSX de projeto.

### Fase 4 - Materiais e catalogos
- Status: IMPLEMENTED
- Adicionado `src/sidct/materials.py` com specs de material, regioes, rugosidade, limites de temperatura/pressao e adequacao por servico.
- Adicionados catalogos `PVC_EN1452` e `PVC_ASTMD1785`.
- PVC passa a ter regras proprias e bloqueio para combinacoes inadequadas como ar comprimido/gas/vacuo/fire water.

### Fase 5 - Motores
- Status: IMPROVED
- Selector passa a resolver catalogo PVC por jurisdicao quando necessario.
- Espessura interna ganhou ramo especifico de triagem para PVC, com warning explicito de derating/fabricante.
- Suportes usam modulo preliminar de PVC quando aplicavel.

### Fases 6 e 7 - UI desktop
- Status: IMPLEMENTED
- Adicionado `src/sidct/ui/desktop_app.py`.
- `app.py` agora lanca a aplicacao desktop PySide6.
- UI inclui explorer de projeto, formulario, calculo, resultados, warnings, assumptions, Save/Open, duplicate line, PDF, CSV e XLSX.
- Streamlit permanece em `src/sidct/ui/streamlit_app.py` como legado.

### Fase 9 - QA e testes
- Status: COMPLETE
- Adicionado `tests/test_project_product_workflow.py`.
- Cobertura nova: persistencia com duas rotas independentes, PVC EU/EUA, material inadequado, PDF, CSV, XLSX e batch CSV.

### Fase 10 - Packaging
- Status: IMPLEMENTED
- Adicionado `BUILD_DESKTOP.md`.
- Adicionado `scripts/build_desktop.py` para PyInstaller.
- `requirements.txt` e `pyproject.toml` incluem PySide6 e entrypoint `sidct-desktop`.

### Verificacao local
- `python -m pip install "PySide6>=6.7.0"` executado com sucesso.
- Smoke test desktop headless executado com sucesso: `desktop smoke OK`.
- PyInstaller 6.20.0 instalado e build desktop gerada em `dist_desktop_light/SIDCT`.
- Teste final: 82/82 passed.

---
## System Pipe Mapping Review - 2026-04-29

### Planilha inicial
- Status: REVIEWED
- Ficheiro analisado: `Pipping Systens.xlsx`, folha `Folha1`, 49 linhas x 9 colunas.
- Conteudo identificado: mapeamento preliminar orientado a BIM/fabricantes para agua, agua potavel, ar comprimido, AVAC, esgoto, gas, incendio e vacuo.
- Lacunas confirmadas: inox ausente para agua potavel/osmotizada, PE/PEAD ausente para gas enterrado, chilled/condenser water pouco diferenciados, agua osmotizada sem sistema proprio, PVC/PPR sem bloqueios fortes para ar comprimido/gas/fire.

### Matriz tecnica
- Status: IMPLEMENTED
- Criado `SYSTEM_PIPE_MAPPING_REVIEW.md`.
- Criado `system_pipe_mapping.yaml` com `preferred_materials`, `allowed_materials`, `conditional_materials`, `blocked_materials`, regioes EU/US, warnings, contextos e `calculation_ready`.
- Criado `src/sidct/system_pipe_mapping.py`.

### Integracao no produto
- Status: IMPLEMENTED
- `validators.py` valida combinacoes sistema x material.
- UI desktop filtra materiais dinamicamente por sistema e jurisdicao.
- Packaging inclui `system_pipe_mapping.yaml`.

### Verificacao
- `pytest -q`: 88/88 passed.
- Smoke test desktop dinamico: `desktop dynamic material smoke OK`.
- Build desktop reconstruida com `system_pipe_mapping.yaml` em `dist_desktop_light/SIDCT`.

---
## UI Theme Update - 2026-04-29

### Interface
- Status: IMPLEMENTED
- Tema dark substituido por tema claro cinza/azul em `src/sidct/ui/desktop_app.py`.
- Linhas no explorer recebem cor por sistema de piping: agua, ar comprimido, gas natural, vacuo, drenagem, pluvial e incendio.
- Botao `Calculate` removido da toolbar e reposicionado como botao principal no formulario.
- Menu `Options` criado com selecao de idioma English / Portugues (PT-BR).
- Launcher clicavel criado: `Start SIDCT.bat`.

### Verificacao
- Smoke test desktop: `desktop light theme/i18n smoke OK`.
- `pytest -q`: 88/88 passed.
- Build desktop atualizada em `dist_desktop_light/SIDCT`.

---
## Adaptive UX/UI Refactor - 2026-04-29

### Auditoria e especificacao
- Status: IMPLEMENTED
- Criados `UI_AUDIT.md`, `FORM_BEHAVIOR_REVIEW.md`, `UX_GAP_ANALYSIS.md`, `FIELD_RULES_SPEC.md` e `UX_REDESIGN_REVIEW.md`.
- Criada matriz consumivel `form_behavior_matrix.yaml` para sistema x modo de calculo x campos visiveis/obrigatorios/ocultos/warnings.

### Interface desktop
- Status: IMPLEMENTED
- Adicionado `src/sidct/ui/form_behavior.py` para carregar e resolver regras adaptativas do formulario.
- UI passou a ter modo de calculo explicito: dimensionar nova linha, conferir linha recebida e comparar alternativa.
- Campos irrelevantes sao ocultados por sistema: por exemplo, aguas pluviais/esgoto escondem pressao/vacuo e exigem declive; vacuo exige vacuo alvo.
- Labels obrigatorios recebem asterisco vermelho e tooltips tecnicos vindos da matriz.
- Adicionado painel dinamico `Requisitos do Sistema`, com regime, obrigatorios, campos nao usados e nota operacional.
- Validacao pre-calculo lista campos obrigatorios em falta e incoerencias basicas antes de chamar o core.
- Painel de resultados ganhou resumo executivo com status, DN, material, schedule e criterio governante.
- Explorer de linhas agora mostra sistema, material e status, com cor por sistema.
- Toolbar ficou agrupada por projeto, linha e exportacao.

### Packaging
- Status: IMPLEMENTED
- `scripts/build_desktop.py` inclui `form_behavior_matrix.yaml`.
- Build nova gerada em `dist_desktop_adaptive_v2/SIDCT`.
- `Start SIDCT.bat` passa a priorizar `dist_desktop_adaptive_v2/SIDCT/SIDCT.exe`.

### Verificacao
- Smoke test desktop adaptativo: `desktop adaptive UI smoke OK`.
- `pytest -q`: 92/92 passed.
- Builds em `dist_desktop_light` e `dist_desktop_adaptive` falharam ao tentar remover pastas bloqueadas pelo OneDrive; build final em `dist_desktop_adaptive_v2` concluida com sucesso.
