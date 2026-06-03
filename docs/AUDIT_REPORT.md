# SIDCT Audit Report

Data da auditoria: 2026-04-29

## Inventario do projeto

O repositório já contém um pacote Python em `src/sidct`, com modelos Pydantic, motores de cálculo, catálogos embutidos, batch CSV, geração de PDF, validação, configuração YAML e testes. O entrypoint de utilizador é `app.py`, que injeta `src` no `PYTHONPATH` e executa a aplicação Streamlit com `exec`.

Componentes encontrados:

- `src/sidct/models.py`: modelos de linha única, resultados, report context e batch.
- `src/sidct/engines/`: hidráulica incompressível, compressível, gravidade, vácuo, espessura interna, pressão externa, suportes, checker e seletor.
- `src/sidct/catalogs/`: dimensões de tubo, tensões admissíveis, propriedades de fluido e K-values.
- `src/sidct/ui/streamlit_app.py`: interface Streamlit.
- `src/sidct/batch/csv_runner.py`: processamento CSV.
- `src/sidct/reports/memorial_pdf.py`: memorial PDF por ReportLab.
- `project_profiles.yaml`, `service_matrix.yaml`, `standards_registry.yaml`, `assumptions.yaml`: configuração técnica.
- `tests/`: 75 testes executados com sucesso em 2026-04-29.

## O que esta funcional

- Os testes existentes passam: `75 passed`.
- O core de cálculo está separado da UI em boa parte.
- Há motores distintos para serviços pressurizados, gases, gravidade, vácuo, espessura, pressão externa, suportes e checker.
- Existem validações de serviço, perfil, declive obrigatório para gravidade e pressão alvo obrigatória para vácuo.
- Há checker com estados `APPROVED`, `CONSERVATIVE`, `INSUFFICIENT`, `CRITICAL`, `DATASET_MISSING` e `OUT_OF_SCOPE`.
- Há geração de memorial PDF auditável.
- Há batch CSV resiliente por linha, sem abortar o ficheiro inteiro quando uma linha falha.
- Há testes unitários e de integração cobrindo motores e casos obrigatórios de aço carbono/inox.

## O que esta parcialmente funcional

- A separação UI/engine existe, mas `app.py` usa bootstrap frágil e a UI Streamlit constrói diretamente `LineInput`.
- O conceito de projeto existe apenas como campos `project_name` e `line_tag`; não existe modelo persistente de projeto com rotas independentes.
- Batch CSV existe, mas não suporta importação XLSX nem integração natural com um projeto persistente.
- Relatórios existem por linha, mas não há relatório de projeto multi-traçado.
- PVC aparece em testes de drenagem, mas ainda é tratado de forma implícita e incompleta, sem catálogo dedicado nem regras de aplicação robustas.
- A documentação declara roadmap e limitações, mas não reflete uma arquitetura desktop comercial.

## O que esta quebrado ou fraco

- `app.py` executa Streamlit via `exec`, alterando `__file__` e mexendo no `sys.path`; isto é frágil para packaging.
- A interface final depende de navegador e Streamlit, incompatível com a meta de produto desktop independente.
- Textos em vários ficheiros apresentam mojibake (`â€”`, `Ã£`, `Â°C`), o que reduz maturidade visual e confiança.
- Não há persistência de projetos; a sessão Streamlit é temporária.
- Não há modelo nativo para múltiplas rotas/traçados independentes.
- Não há camada formal de materiais com família, grau, região, catálogo, limites de pressão/temperatura e adequação por serviço.
- Pressão externa e suportes são corretamente marcados como preliminares, mas ainda não têm datasets normativos completos.
- A UI tem aparência de ferramenta interna: formulários longos, poucos estados visuais de projeto, sem explorer, sem histórico multi-linha e sem workflow de ficheiro.

## Fraquezas técnicas

- Imports/entrypoints orientados ao desenvolvimento local, não ao produto.
- Catálogos dimensionais são embutidos no código, sem mecanismo maduro de datasets externos versionados.
- Materiais plásticos não têm regras próprias.
- Modelo de domínio é linha única, não projeto.
- Não há auto-save, logs locais de aplicação desktop, preferências, nem scripts de build.
- A compatibilidade catálogo-material existe para inox, mas não cobre PVC e regiões EU/EUA.

## Fraquezas visuais

- Streamlit oferece uma UI rápida, mas não transmite produto desktop vendável.
- Layout não tem explorer de projeto, painéis persistentes, histórico ou gestão de documentos.
- A linguagem visual é dominada por inputs e métricas pontuais, sem visão clara de projeto.
- Mojibake nos textos compromete diretamente a apresentação comercial.

## O que impede comercializacao

- Dependência de browser/Streamlit como UI final.
- Ausência de projeto persistente multi-traçado.
- Packaging desktop inexistente.
- Catálogos e materiais incompletos para PVC.
- Estado visual e UX ainda de protótipo.
- Falta de documentação de build e maturidade comercial honesta.

## O que impede uso por engenheiro real

- PVC sem catálogo próprio e sem limites de temperatura/pressão.
- Ausência de rastreabilidade por projeto e alternativas.
- Falta de import/export XLSX integrado ao workflow de projeto.
- Pressão externa e suportes ainda preliminares.
- Dataset parcial de tensões admissíveis e catálogos.
- Mensagens técnicas existem, mas não estão organizadas num painel persistente de warnings/assunções por projeto.

## O que deve ser preservado

- Motores de cálculo existentes e testes.
- Pydantic como camada de validação de domínio.
- `ReportContext` como agregador de resultados.
- Checker e seus estados.
- Geração PDF por ReportLab.
- Batch CSV resiliente.
- Configuração YAML de perfis, serviços, normas e assunções.

## O que deve ser refatorado

- Entry point e bootstrap.
- Modelo de domínio para projeto/rota/linha/caso.
- Catálogos e materiais.
- UI final para PySide6.
- Persistência e import/export.
- Documentação de build desktop.

## O que deve ser removido ou rebaixado

- Streamlit não deve ser removido imediatamente, mas deve ser rebaixado a protótipo/ferramenta interna.
- Bootstrap por `exec` deve ser removido como entrypoint principal.
- Assunção implícita de PVC em catálogos de aço deve ser eliminada.
