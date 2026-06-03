# Repository Map

## Raiz

- `app.py`: entrypoint atual. Antes da refatoração, lançava Streamlit por `exec` e inserção manual de `src` no path.
- `pyproject.toml`: metadados de pacote e dependências.
- `requirements.txt`: dependências runtime/teste/dev.
- `README.md`: descrição funcional, execução Streamlit e API.
- `EXECUTION_LOG.md`: log anterior de execução.
- `DESIGN_BASIS.md`: base de desenho.
- `assumptions.yaml`: assunções técnicas.
- `project_profiles.yaml`: perfis de projeto.
- `service_matrix.yaml`: serviços suportados.
- `standards_registry.yaml`: normas referenciadas.

## `src/sidct`

- `models.py`: modelos Pydantic principais.
- `enums.py`: enums de serviço, perfil, catálogo, material, status, unidades e jurisdição.
- `validators.py`: validação de entradas e compatibilidade perfil/serviço.
- `units.py`: conversões de unidades.
- `config.py`: carregamento YAML.
- `exceptions.py`: exceções de domínio.
- `logging_config.py`: logging.
- `provenance.py`: proveniência.

## Motores

- `engines/selector.py`: orquestra cálculo completo e monta `ReportContext`.
- `engines/hydraulic_incompressible.py`: Darcy-Weisbach + Colebrook.
- `engines/hydraulic_compressible.py`: gás compressível isotérmico.
- `engines/hydraulic_gravity.py`: Manning parcialmente cheio.
- `engines/vacuum.py`: condutância de vácuo.
- `engines/thickness_internal.py`: espessura por pressão interna.
- `engines/thickness_external.py`: pressão externa/colapso.
- `engines/supports.py`: suportes preliminares.
- `engines/checker.py`: verificação global.
- `engines/colebrook.py`: fator de atrito.

## Catálogos

- `catalogs/pipe_dimension_catalog.py`: dimensões ASME B36.10M/B36.19M.
- `catalogs/material_stress_catalog.py`: tensões admissíveis para materiais metálicos.
- `catalogs/fluid_properties.py`: propriedades de fluido.
- `catalogs/fitting_k_catalog.py`: K-values.

## UI

- `ui/streamlit_app.py`: UI web atual, útil como protótipo.

## Batch e relatórios

- `batch/csv_runner.py`: batch CSV.
- `reports/memorial_pdf.py`: geração PDF.

## Dados

- `data/templates/batch_template.csv`: template CSV.
- `data/templates/material_stress_template.csv`: template de tensões.
- `data/templates/nbr5580_catalog_template.csv`: template NBR.

## Testes

- `tests/test_catalogs.py`: catálogos, tensões e K-values.
- `tests/test_checker.py`: checker e cálculo completo.
- `tests/test_hydraulic_engines.py`: motores hidráulicos.
- `tests/test_integration_cases.py`: casos de integração.
- `tests/test_thickness.py`: espessura e pressão externa.
- `tests/test_units.py`: unidades.
