# UI Audit

Data: 2026-04-29

## Janelas e widgets existentes

A aplicação desktop está concentrada em `src/sidct/ui/desktop_app.py` e usa uma `QMainWindow` com:

- menu superior: File, Project, Export, Options;
- toolbar com ações de projeto/linha/exportação;
- `QSplitter` horizontal com três zonas;
- painel esquerdo com `QListWidget` para projeto/rotas/linhas;
- painel central com formulário em `QGroupBox` e `QFormLayout`;
- painel direito com `QTabWidget` e tabelas/textos de resultados.

## Estrutura atual do formulário

As secções atuais são:

- Project and Line;
- Service and Material;
- Operating Conditions;
- Flow and Geometry;
- Criteria and Received Line;
- Notes;
- botão principal de cálculo.

## Campos sempre visíveis antes desta refatoração

Todos os campos principais ficavam visíveis para todos os sistemas:

- pressão/temperatura de operação;
- pressão/temperatura de projeto;
- caudal e unidade;
- comprimento;
- desnível;
- declive;
- alvo de vácuo;
- corrosion allowance;
- dP admissível;
- DN recebido;
- schedule recebido;
- cotovelos;
- notas.

## Campos que deveriam ser condicionais

- `slope_mm_m`: obrigatório apenas para esgoto/pluvial; irrelevante para pressurizados.
- `vacuum_target_mbara`: obrigatório apenas para vácuo.
- `DN_received_mm` e `schedule_or_wall_received`: obrigatórios em modo de conferência.
- `allowable_pressure_drop_bar`: relevante para pressurizados, pouco útil para gravidade.
- pressões: relevantes para pressurizados/vácuo, menos centrais para gravidade.
- corrosion allowance: relevante para metais, não para PVC/alguns plásticos.

## Resultados

Os resultados eram apresentados em tabelas simples e abas. O conteúdo técnico existia, mas faltava resumo executivo com DN, material, schedule, critério governante e status em destaque.

## Toolbar

A toolbar tinha ações funcionais, mas sem agrupamento visual forte e ainda parecia uma fila de botões pequenos. O `Calculate` já tinha sido retirado da toolbar, mas ainda faltava separar semanticamente grupos de projeto, linha e exportação.

## Linguagem

Havia mistura de labels em inglês, enums internos (`compressed_air`, `rainwater`) e algum português. A interface precisava de PT-BR técnico como opção coerente e de nomes amigáveis para sistemas.

## Preservar

- Estrutura de três painéis.
- Explorer de projeto.
- Separação core/UI.
- Botão de cálculo no formulário.
- Exportações PDF/CSV/XLSX.
- Filtro dinâmico de materiais por sistema/região.

## Melhorar

- Formulário adaptativo por sistema/modo.
- Campos obrigatórios com asterisco vermelho.
- Tooltips.
- Validação pré-cálculo.
- Painel de requisitos do sistema.
- Resumo executivo de resultados.
- Linguagem técnica amigável.
- Status visual mais informativo no explorer.
