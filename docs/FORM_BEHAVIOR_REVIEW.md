# Form Behavior Review

## Estado anterior

O formulário era tecnicamente completo, mas genérico. O utilizador via campos que não se aplicavam ao sistema selecionado e precisava inferir quais eram obrigatórios.

## Problema operacional

Um engenheiro que escolhe `rainwater` não deve ver o mesmo fluxo mental de uma linha de ar comprimido. Para pluvial/esgoto, declive e caudal são centrais; pressões e dP admissível não devem dominar o formulário. Para vácuo, alvo de vácuo e pressão externa são centrais. Para conferência, DN e schedule recebidos precisam ser obrigatórios.

## Decisão implementada

Foi criada uma matriz em `form_behavior_matrix.yaml` que define:

- campos visíveis;
- campos obrigatórios;
- campos opcionais;
- campos desativados;
- campos ocultos;
- tooltips;
- notas de regime;
- regras de validação.

## Modos

- `calculate_new`: dimensionar nova linha.
- `check_received`: conferir linha recebida.
- `compare_alternative`: preparado como modo futuro; hoje reutiliza base de cálculo com campos de comparação.

## Campos principais

- Projeto e linha: sempre visíveis.
- Sistema/material: sempre visíveis.
- Pressões: ocultas/desativadas em gravidade, visíveis em pressurizados/vácuo.
- Declive: obrigatório em gravidade.
- Vácuo alvo: obrigatório em vácuo.
- DN/schedule recebidos: obrigatórios em conferência.
- dP admissível: relevante em pressurizados.

## Resultado esperado

O utilizador passa a ver um formulário guiado: menos ruído, mais clareza, e mensagens diretas quando algo falta.
