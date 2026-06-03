# Gap Analysis

## Critico

- UI final depende de Streamlit/browser, incompatível com produto desktop independente.
- Não existe modelo persistente de projeto com múltiplos traçados independentes.
- PVC não tem tratamento completo como material próprio com catálogos e limites.
- Entry point e bootstrap são frágeis para packaging.
- Não há build desktop por PyInstaller/Nuitka.

## Alto

- Não há Save/Open project.
- Não há importação XLSX nem exportação XLSX integrada.
- Relatórios são por linha e não por projeto multi-rota.
- UI não tem explorer, histórico de cálculos, painel persistente de warnings/assunções ou gestão de documentos.
- Materiais/catálogos são parcialmente hardcoded e sem camada extensível formal.
- Mojibake nos textos de UI/documentação prejudica demonstração comercial.

## Medio

- Pressão externa é preliminar e depende de datasets não implementados.
- Suportes são preliminares e não substituem flexibilidade/tensões.
- Motor compressível usa modelo isotérmico e comunica limitações, mas não cobre regimes mais avançados.
- Batch CSV não cria projeto persistente nem importa XLSX.
- Testes não cobrem UI desktop nem packaging.

## Baixo

- Documentação atual ainda descreve Streamlit como modo principal.
- Falta ícone/branding.
- Falta estrutura de preferências.
- Falta normalização visual de nomes em português/inglês.
