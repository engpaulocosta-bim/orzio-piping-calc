# UI/UX Strategy

## Principios

- A primeira tela deve ser a aplicação de trabalho, não uma landing page.
- O utilizador deve ver projeto, rotas, inputs, resultados e warnings no mesmo contexto.
- A UI deve favorecer revisão técnica: valores principais, critério governante, margem e limitações.
- Erros devem ser humanos e técnicos: explicar o problema e indicar o campo.

## Estrutura proposta

- Menu: New, Open, Save, Save As, Import Batch, Export CSV/XLSX, Export PDF, Settings.
- Sidebar esquerda: project explorer com rotas/linhas.
- Painel central: formulário contextual.
- Painel direito ou inferior: resultados, checker, warnings, assumptions e histórico.
- Status bar: ficheiro atual, estado do projeto, último cálculo.

## Estados visuais

- `CALCULATED`/`APPROVED`: verde controlado.
- `CONSERVATIVE`: azul.
- `WARNING`: amarelo.
- `INSUFFICIENT`/`CRITICAL`: vermelho/laranja.
- `DATASET_MISSING`: roxo/cinza técnico.

## Problemas atuais da UI

- Streamlit é funcional, mas parece ferramenta interna.
- Falta gestão de documentos.
- Falta navegação por projeto.
- Textos com mojibake devem ser corrigidos ao longo da migração.
