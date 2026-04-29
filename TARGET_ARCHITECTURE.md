# Target Architecture

## Decisao de stack

A UI final passa a ser PySide6 / Qt for Python. Streamlit permanece apenas como protótipo interno. A escolha é adequada porque a aplicação alvo precisa de janelas, menus, explorer de projeto, tabelas, painéis de resultados, diálogos de ficheiro, workflows de Save/Open e empacotamento desktop.

## Camadas

- Core de domínio: modelos Pydantic para `Project`, `Route`, `LineSegment`, `HydraulicCase`, `MaterialSpec`, `FittingSet`, `ValveSet`, `Report` e `ValidationState`.
- Serviços de aplicação: criação/duplicação de linhas, cálculo, validação, import/export e persistência.
- Motores de cálculo: manter motores atuais e expor uma interface estável via `run_full_calculation`.
- Catálogos: material family, grade/spec, região, catálogo dimensional, limites de temperatura/pressão, rugosidade e adequação por serviço.
- Persistência: ficheiro JSON estruturado para projetos locais, com versão de schema. É mais simples que SQLite para ficheiros de projeto portáteis e suficiente para a escala atual; SQLite pode ser adicionado depois para bibliotecas multiutilizador.
- Relatórios: PDF por linha e exportação tabular CSV/XLSX.
- UI desktop: main window, project explorer, form contextual, results table, warnings, assumptions, import/export e settings.
- Packaging: PyInstaller como caminho inicial por maturidade e velocidade.

## Entry points

- `app.py`: lança a app desktop.
- `sidct-desktop`: console script futuro.
- `src/sidct/ui/streamlit_app.py`: protótipo legado.

## Testes

- Manter testes existentes de motor.
- Adicionar testes de projeto/persistência.
- Adicionar testes de PVC EU/EUA.
- Adicionar testes de exportação.
- Smoke test opcional da UI quando PySide6 estiver instalado.

## Extensibilidade futura

- Adicionar CPVC, HDPE/PEAD, cobre e PPR via novos registos de material e catálogos.
- Separar datasets em CSV/JSON versionados.
- Adicionar biblioteca de materiais editável pelo utilizador.
- Adicionar relatório de projeto completo.
- Evoluir persistência para SQLite se houver biblioteca local complexa ou multiutilizador.
