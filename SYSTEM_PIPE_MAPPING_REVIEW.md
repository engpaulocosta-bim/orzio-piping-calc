# System Pipe Mapping Review

Data: 2026-04-29

## Escopo

Esta revisão analisou a planilha `Pipping Systens.xlsx`, a imagem de cores de tubagens e o estado atual do SIDCT. A planilha foi tratada como ponto de partida, não como verdade normativa. O resultado foi convertido numa matriz técnica consumível pelo software em `system_pipe_mapping.yaml`.

## Leitura da planilha inicial

A planilha tem uma folha (`Folha1`) com blocos por sistemas:

- Água fria e quente.
- Água potável.
- Ar comprimido.
- AVAC.
- Esgoto e águas residuais.
- Gás.
- Prevenção e combate a incêndio.
- Vácuo.

A estrutura da planilha é orientada a `Tipo de tubo`, `Material`, `Aplicações` e `Principais marcas com BIM`. Isto é útil para arranque comercial/BIM, mas mistura disponibilidade de biblioteca BIM com adequação técnica. Uma marca com BIM não torna um material adequado ao sistema; e um material tecnicamente adequado pode não aparecer se não tiver sido pesquisado como biblioteca BIM.

A imagem `Cores de Tubos.png` parece tratar identificação visual/RAL de sistemas. Ela é relevante para sinalização e camada futura de UI/relatórios, mas não resolve compatibilidade material-fluido-serviço.

## Lacunas e simplificações encontradas

### Água potável

A planilha inclui PEX, multicamada, PPR e PEAD para entradas prediais. Isto está correto como base de building services, mas está incompleto:

- falta aço inox 316/304 para água potável em contexto industrial, sala técnica, higiene e baixa manutenção;
- falta a distinção entre água fria e quente;
- falta separar tubagem certificada para contacto com água potável de tubagem genericamente do mesmo material;
- falta bloquear aço carbono preto não revestido/não aprovado.

### Água osmotizada / tratada

Não aparece como sistema próprio. É uma lacuna importante. Água osmotizada pode ser agressiva e contaminar-se por lixiviação/corrosão. A matriz nova trata 316 como preferencial e bloqueia aço carbono para este serviço.

### Água de serviço

Não está tratada com granularidade industrial. A planilha tem “Água” e “Água fria/quente”, mas não distingue água industrial bruta/tratada, enterrada, exterior, sala técnica, corrosão e pressão.

### Chilled water / condenser water

A planilha usa AVAC genericamente e lista multicamada, PEX e cobre. Isto é limitado para data centres e sistemas industriais, onde aço carbono continua comum em grandes diâmetros e HDPE pode ser aplicável em enterrado/district cooling. Condenser water foi acrescentado como sistema próprio por ter risco de corrosão/fouling e água de torre.

### Gás natural

A planilha lista cobre, multicamada gás e aço carbono preto. Isso é útil para interiores/edifícios, mas incompleto:

- falta PE/PEAD gas-grade para ramais/redes enterradas;
- falta separar enterrado, aparente, riser/transição e sala técnica;
- falta bloquear PVC/PPR;
- falta explicitar que multicamada só é aceitável quando for sistema certificado para gás e aprovado localmente.

### Ar comprimido

A planilha lista alumínio, PPR e multicamada. Falta:

- aço carbono para redes industriais robustas;
- inox para ar limpo/instrumentação;
- bloqueio explícito de PVC devido risco de falha frágil;
- distinção entre plástico genericamente “PPR” e sistema explicitamente classificado para ar comprimido.

### Vácuo

A planilha lista PVC/PEAD para aspiração central e inox para vácuo industrial. A matriz nova separa vácuo leve de vácuo industrial e mantém pressão externa/colapso como critério obrigatório.

### Esgoto e águas pluviais

A planilha está razoável como base: PVC, PP e PEAD aparecem. Faltava distinguir:

- drenagem sanitária versus pluvial;
- gravidade comum versus sifónico;
- acústica, fogo, classe SN e enterrado;
- ferro fundido em edifícios com exigência acústica/fogo.

### Anti-incêndio

A planilha lista aço galvanizado, aço carbono revestido, inox pressfit e CPVC especial. A matriz nova torna isto mais rigoroso:

- aço carbono/listado como preferencial;
- inox só quando listado/aprovado para fire service;
- CPVC apenas listado e com limitações de ocupação/exposição/AHJ;
- HDPE apenas como hipótese condicionada para redes enterradas aprovadas;
- PVC/PPR genéricos bloqueados.

## Critérios técnicos adotados

A matriz usa quatro níveis:

- `preferred_materials`: opção tecnicamente preferencial para o contexto.
- `allowed_materials`: aceitável com verificação normal de projeto.
- `conditional_materials`: dependente de contexto; exige warning e confirmação.
- `blocked_materials`: não oferecer ao utilizador.

Cada entrada pode ter:

- `material_id`;
- `display_name`;
- `sidct_material`;
- `calculation_ready`;
- `contexts`;
- `limitations`;
- `warnings`;
- `selection_rank`.

O campo `calculation_ready` é deliberado: CPVC, HDPE, PPR, cobre, alumínio, PP e ferro fundido aparecem na matriz técnica, mas nem todos têm ainda catálogo dimensional e motor de espessura implementado. O software pode distinguir “tecnicamente mapeado” de “calculável agora”.

## Perspectiva regional

Foram criadas diferenças explícitas para `EU` e `US` quando a prática muda materialmente:

- água potável nos EUA enfatiza NSF/ANSI/CAN 61;
- gás natural nos EUA enfatiza PE para distribuição enterrada, mas não como tubagem interior exposta;
- anti-incêndio nos EUA enfatiza NFPA/AHJ/listed systems;
- Europa mantém lógica similar, mas com approvals locais e prática de mercado diferente.

Regiões não mapeadas caem no perfil `EU` como fallback conservador, até existir dataset regional próprio.

## Referências técnicas usadas como balizas

- NSF descreve NSF/ANSI/CAN 61 como standard de consenso para critérios mínimos de saúde de materiais em contacto com água potável: https://www.nsf.org/water-systems/nsf-ansi-can-61-testing-and-certification
- PHMSA indica em guia de operadores que tubo plástico é comum em redes de distribuição e serviço de gás, com PE como material adequado para gás natural: https://www.phmsa.dot.gov/sites/phmsa.dot.gov/files/docs/Small_Natural_Gas_Operator_Guide_%28January_2017%29.pdf
- ASTM D2513 cobre requisitos de PE para redes e ramais de gás enterrados/relining: https://store.astm.org/d2513-12ae01.html
- Copper Development Association mantém referência específica de fuel gas para cobre, reforçando que cobre pode existir mas depende de tabelas/código/localidade: https://www.copper.org/applications/fuelgas/
- UL explica que tubagem não metálica em sprinklers deve ser investigada/listada para o serviço; CPVC é tratado como produto listado, não como CPVC genérico: https://www.ul.com/news/qa-installation-plastic-fire-sprinkler-pipe-exposed-locations

## Decisão de produto

O SIDCT agora deve funcionar assim:

1. O utilizador seleciona o sistema.
2. A UI carrega materiais compatíveis e calculáveis para aquele sistema/região.
3. Materiais tecnicamente possíveis mas ainda sem dataset ficam na matriz como `calculation_ready: false`.
4. Materiais bloqueados disparam erro de validação se chegarem ao core por import/API.
5. Warnings de aplicação são propagados para a UI e relatórios.

## Mudanças implementadas

- Criado `system_pipe_mapping.yaml`.
- Criado `src/sidct/system_pipe_mapping.py`.
- `validators.py` passou a validar sistema × material antes do cálculo.
- UI desktop passou a filtrar materiais dinamicamente por sistema e jurisdição.
- Packaging inclui a nova matriz.
- Testes adicionados em `tests/test_system_pipe_mapping.py`.

## Limitações honestas

Esta matriz é uma camada de decisão técnica, não substitui norma local, AHJ, utility owner standards, certificações de produto ou catálogo do fabricante. Alguns materiais aparecem como tecnicamente aplicáveis mas ainda não calculáveis pelo SIDCT, porque faltam catálogos dimensionais, curvas pressão-temperatura, regras normativas e datasets de fittings.
