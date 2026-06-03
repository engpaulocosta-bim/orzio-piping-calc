# Test Strategy

## Camadas

- Unit tests para unidades, catálogos, materiais e validação.
- Engine tests para cada motor.
- Integration tests para cálculo completo.
- Persistence tests para guardar/reabrir projeto.
- Export tests para CSV/XLSX/PDF.
- UI smoke tests quando PySide6 estiver instalado.

## Casos minimos obrigatorios

- Abertura/import da app desktop.
- Criação de projeto.
- Criação de dois traçados independentes.
- Cálculo em aço carbono.
- Cálculo em inox.
- Cálculo em PVC.
- Perfil Europa.
- Perfil EUA.
- Exportação PDF.
- Guardar e reabrir projeto.
- Importação batch.
- Input inválido.
- Material inadequado.
- Dataset ausente.
- Checker com `APPROVED`, `CONSERVATIVE` e `INSUFFICIENT`.
