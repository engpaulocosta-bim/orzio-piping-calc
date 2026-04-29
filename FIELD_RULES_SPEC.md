# Field Rules Spec

## Objetivo

`form_behavior_matrix.yaml` define como a UI deve se comportar por sistema e modo de cálculo. A matriz é consumida por `sidct.ui.form_behavior`.

## Campo

Cada campo pode estar em um dos grupos:

- `visible_fields`: aparece na UI.
- `required_fields`: aparece e recebe asterisco vermelho.
- `optional_fields`: aparece sem obrigatoriedade.
- `disabled_fields`: aparece, mas não pode ser editado.
- `hidden_fields`: não aparece.
- `warning_fields`: aparece, mas pode gerar aviso se preenchido.

## Modos

- `calculate_new`: cálculo de linha nova.
- `check_received`: conferência de linha recebida; exige `DN_received_mm` e `schedule_or_wall_received`.
- `compare_alternative`: reservado para comparação futura.

## Validação

A validação de UI verifica obrigatórios antes de chamar o core. Ela não substitui a validação Pydantic/engine; apenas evita mensagens tardias e vagas.

## Expansão

Para adicionar um sistema:

1. criar entrada em `systems`;
2. definir `base`;
3. opcionalmente sobrescrever em `modes`;
4. adicionar `field_help` e `explanatory_note`.
