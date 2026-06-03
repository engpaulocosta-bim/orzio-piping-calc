# DESIGN BASIS — SIDCT v1.0

## 1. Objetivo do Sistema

SIDCT (Sistema Integrado de Dimensionamento, Conferência e Memorial de Cálculo de Tubagens
Industriais e Data Centre) é uma ferramenta de engenharia profissional para:

- Dimensionar tubagens novas por regime físico e código aplicável;
- Conferir projetos recebidos de terceiros;
- Gerar memorial de cálculo PDF auditável com rastreabilidade normativa;
- Operar por perfis técnicos distintos sem mistura de critérios.

## 2. Escopo Funcional

### 2.1 Serviços suportados
- Ar comprimido (compressed_air)
- Gás natural (natural_gas)
- Água potável (potable_water)
- Água de serviço (service_water)
- Água osmotizada (osmotized_water)
- Água gelada / chilled water (chilled_water)
- Água de condensação (condenser_water)
- Vácuo utilitário (vacuum_utility)
- Drenagem sanitária (sanitary_drainage)
- Água pluvial (rainwater)
- Proteção contra incêndio (fire_water)

### 2.2 Regimes físicos suportados
- pressurized_incompressible: Darcy-Weisbach + Colebrook-White
- compressible_gas: isothermal compressible com verificação de Mach e pressure ratio
- gravity_partially_full: Manning para tubo parcialmente cheio
- vacuum_conductance: condutância + encaminhamento obrigatório para external pressure check
- external_pressure_check: verificação de colapso por pressão externa (vácuo)
- fire_protection_special: critérios de velocidade parametrizados por perfil

### 2.3 Modos de operação
- Calculate new line: dimensionamento de linha nova
- Check received design: conferência de projeto recebido
- Batch CSV: processamento de múltiplas linhas

## 3. Fora de Escopo

- Análise de flexibilidade e tensões (Caesar II / AutoPIPE)
- Análise de waterhammer / transitórios hidráulicos
- Dimensionamento de equipamentos (bombas, compressores, trocadores)
- Gestão de projetos / P&IDs
- Cálculo de separadores, filtros, vasos de pressão
- Análise de fadiga / fratura
- Códigos nucleares (ASME III)
- Códigos offshore (ASME B31.8 subsea, DNV)

## 4. Perfis de Projeto Suportados

| ID | Descrição | Código Primário |
|----|-----------|-----------------|
| glass_factory_industrial_eu | Fábrica de vidro / utilities industriais (Europa) | ASME B31.3 / EN 13480 |
| glass_factory_industrial_us | Fábrica de vidro / utilities industriais (EUA) | ASME B31.3 |
| industrial_utilities_eu | Utilities industriais genéricos (Europa) | ASME B31.3 / EN 13480 |
| industrial_utilities_brazil | Utilities industriais (Brasil) | ASME B31.3 |
| datacentre_building_services_eu | Data centre / building services (Europa) | ASME B31.9 / EN 13480 |
| datacentre_building_services_us | Data centre / building services (EUA) | ASME B31.9 |
| fire_protection_en | Proteção contra incêndio (EN 12845) | EN 12845 |
| fire_protection_us | Proteção contra incêndio (NFPA 13) | NFPA 13 |
| custom | Perfil personalizado | Definido pelo utilizador |

## 5. Matriz Serviço × Regime × Código

| Serviço | Regime | Código Primário |
|---------|--------|-----------------|
| compressed_air | compressible_gas | ASME B31.3 |
| natural_gas | compressible_gas | ASME B31.3 |
| potable_water | pressurized_incompressible | ASME B31.3 / B31.9 |
| service_water | pressurized_incompressible | ASME B31.3 / B31.9 |
| osmotized_water | pressurized_incompressible | ASME B31.3 / B31.9 |
| chilled_water | pressurized_incompressible | ASME B31.9 |
| condenser_water | pressurized_incompressible | ASME B31.9 |
| vacuum_utility | vacuum_conductance + external_pressure_check | ASME B31.3 |
| sanitary_drainage | gravity_partially_full | EN 12056 / local plumbing codes |
| rainwater | gravity_partially_full | EN 12056 / local plumbing codes |
| fire_water | fire_protection_special | EN 12845 / NFPA 13 |

## 6. Política de Dados Normativos

### 6.1 Fontes permitidas
- Dados de domínio público citados nas normas (fórmulas, coeficientes)
- Dados do CoolProp para propriedades de fluidos
- Catálogos dimensionais ASME B36.10M e B36.19M (públicos/reproduzíveis)
- Valores típicos de literatura técnica com declaração explícita de fonte

### 6.2 Fontes proibidas
- Tabelas proprietárias de normas sem licença (e.g., ASME stress tables completas)
- Dados inventados ou estimados sem fonte declarada
- Aproximações não documentadas

### 6.3 Tratamento de datasets ausentes
- Status DATASET_MISSING emitido para o sub-resultado afetado
- Os demais módulos continuam quando tecnicamente possível
- Templates CSV/YAML criados em /data/templates/ para receção de dados pelo utilizador

## 7. Política de Datasets Ausentes

Quando um dataset normativo/licenciado não estiver disponível:
1. Criar template em /data/templates/
2. Criar loader que valida o template
3. Criar schema de validação
4. Emitir erro claro com status DATASET_MISSING
5. Documentar no README
6. NÃO inventar o conteúdo

## 8. Política de Simplificações

Toda simplificação deve aparecer:
- No resultado (campo assumptions_used)
- No log estruturado
- No PDF (secção "Limitações e Simplificações")

Simplificações declaradas nesta versão:
- Colebrook-White: solução iterativa (convergência < 1e-8)
- Gás compressível: modelo isotérmico (conservativo para gases frios)
- Gás natural: modelado como CH4 puro quando composição não fornecida
- Drenagem/pluvial: propriedades de água limpa a 20°C
- Tensões admissíveis de material: subset de literatura pública (ver material_stress_catalog)
- Pressão externa/colapso: encaminhado para verificação manual quando charts ASME ausentes

## 9. Convenções de Unidades

### 9.1 Unidades internas de cálculo (SI base)
- Pressão: Pa (pascal)
- Temperatura: K (kelvin)
- Comprimento: m (metro)
- Velocidade: m/s
- Caudal: m³/s
- Massa: kg
- Densidade: kg/m³
- Viscosidade dinâmica: Pa·s
- Tensão: Pa

### 9.2 Unidades de interface (configurável por perfil)
- EU/BR: bar, °C, m³/h, L/s, mm
- US: psi, °F, gpm, in

### 9.3 Conversão
- Toda conversão é feita em units.py com fator declarado e rastreável

## 10. Convenções de Status

| Status | Significado |
|--------|-------------|
| APPROVED | Calculado, verificado, dentro dos critérios |
| CONSERVATIVE | DN/espessura recebido é maior que o requerido (margem positiva) |
| INSUFFICIENT | DN/espessura recebido é menor que o requerido |
| CRITICAL | Insuficiência com margem negativa significativa (> 10%) |
| CODE_MISMATCH | Catálogo ou código incompatível com o perfil |
| DATASET_MISSING | Dados normativos/técnicos ausentes para concluir o cálculo |
| OUT_OF_SCOPE | Condições fora do envelope validado do modelo |
| WARNING | Resultado válido mas com alertas técnicos |

## 11. Envelopes Validados

### 11.1 Motor incompressível (Darcy-Weisbach)
- Reynolds: 1 × 10³ a 1 × 10⁸
- Rugosidade relativa: 0 a 0.05
- Incompressibilidade válida quando: ΔP/P < 10%

### 11.2 Motor compressível isotérmico
- Mach < 0.3 (regime subsónico validado)
- Pressure ratio P2/P1 > 0.5 (queda de pressão < 50%)
- Fora destes limites: OUT_OF_SCOPE com mensagem técnica

### 11.3 Motor de gravidade (Manning)
- Profundidade relativa y/D: 0.1 a 0.9
- Inclinação: 0.001 a 0.10 m/m
- Velocidade de auto-limpeza verificada (> 0.6 m/s)

### 11.4 Vácuo/pressão externa
- Pressão absoluta mínima modelada: 0.1 mbar abs
- Verificação de colapso encaminhada para método ASME/EN quando dataset disponível

## 12. Limitações por Regime

### 12.1 Gás compressível
- Modelo isotérmico: conservativo, não adequado para gases quentes em expansão rápida
- Efeitos de inércia não modelados (arranque/paragem rápida)
- Mistura de gases não suportada (apenas componente único ou gás natural simplificado)

### 12.2 Pressão externa / colapso
- Requer charts L/D vs Do/t (ASME Fig. G ou equivalente) — dataset externo
- Sem dataset: status DATASET_MISSING; verificação manual obrigatória

### 12.3 Drenagem gravitária
- Manning: regime permanente uniforme
- Não modela transições hidráulicas ou ressaltos
- Chuva: não calcula caudal de projeto (entrada de utilizador)

### 12.4 Suportes
- Classificação: ferramenta preliminar
- Não substitui análise de flexibilidade/stress
- Sísmica: carga horizontal paramétrica (não análise modal)

## 13. Critérios de Aceite

O sistema está conforme quando:
1. Instala sem erro (pip install -r requirements.txt)
2. Todos os testes unitários e de integração passam
3. App Streamlit abre sem erro
4. PDF gerado contém todos os campos obrigatórios
5. Batch CSV processa sem abortar por erro de linha única
6. Perfis estão separados e não se misturam
7. Serviços gravitários usam exclusivamente motor Manning
8. Serviços compressíveis verificam Mach e pressure ratio
9. Inox usa B36.19M; carbono usa B36.10M
10. Vácuo aciona rota de pressão externa
11. Checker não aprova resultado com DATASET_MISSING em campo crítico
12. README reflecte o que foi realmente implementado
