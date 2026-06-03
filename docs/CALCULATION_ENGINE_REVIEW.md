# Calculation Engine Review

## Hidraulica incompressivel

Estado atual: funcional e testada. Usa Darcy-Weisbach, Colebrook e K-values.

Maturidade: intermédia.

Limitações: rugosidade default de aço se não houver material spec; sem rede malhada; sem transientes.

## Compressivel

Estado atual: funcional para ar/gás natural em envelope conservador.

Maturidade: intermédia-baixa.

Limitações: modelo isotérmico; não substitui Fanno/Rayleigh nem análise avançada para Mach elevado.

## Gravitaria

Estado atual: funcional por Manning parcialmente cheio.

Maturidade: intermédia.

Limitações: regime permanente uniforme; sem singularidades hidráulicas complexas.

## Vacuo

Estado atual: funcional como estimativa de condutância e encaminha para pressão externa.

Maturidade: preliminar.

Limitações: precisa datasets e métodos mais robustos para aprovação final.

## Espessura por pressao interna

Estado atual: funcional para materiais metálicos do subset.

Maturidade: intermédia para pré-dimensionamento.

Limitações: dataset público parcial; PVC precisa tratamento próprio.

## Pressao externa / colapso

Estado atual: preliminar.

Maturidade: baixa para aprovação normativa final.

Limitações: charts/datasets ASME rigorosos ausentes.

## Suportes

Estado atual: preliminar.

Maturidade: baixa-intermédia.

Limitações: não substitui flexibilidade, stress analysis, cargas térmicas ou suportação detalhada.

## Checker

Estado atual: bom como gate de estado e segurança.

Maturidade: intermédia.

Limitações: depende da qualidade dos datasets dos motores.
