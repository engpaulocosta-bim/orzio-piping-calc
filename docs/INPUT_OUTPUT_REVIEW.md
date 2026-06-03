# Input/Output Review

## Entradas atuais necessárias

- Projeto, tag da linha, serviço, perfil, jurisdição.
- Pressão/temperatura de operação e projeto.
- Caudal e unidade.
- Comprimento e desnível.
- Material e catálogo.
- Corrosão, rugosidade, isolamento.
- Fittings e válvulas.
- Critérios de queda de pressão e pressão residual.
- DN/schedule recebidos em modo de conferência.
- Declive para gravidade.
- Pressão alvo para vácuo.

## Entradas redundantes ou frágeis

- `fluid_name` é muitas vezes derivável de `service`, mas útil para relatórios.
- `jurisdiction`, `project_profile` e `dimensional_catalog` podem entrar em conflito; deve haver seleção assistida.
- `material` é string livre; precisa camada de catálogo/material.

## Entradas em falta

- Identidade formal de projeto e rota.
- Caso hidráulico por linha.
- Região/catalog profile EU/EUA.
- Classe/pressão nominal para PVC.
- Estado de validação por linha.
- Histórico de cálculo.
- Preferências de utilizador.

## Saídas atuais

- Resultado hidráulico.
- Espessura.
- Pressão externa quando aplicável.
- Suportes preliminares.
- Checker.
- Warnings.
- PDF por linha.
- CSV simples por cálculo.

## Saídas profissionais em falta

- Resultado por rota no projeto.
- Comparação entre alternativas.
- Tabela consolidada de projeto.
- Exportação XLSX.
- Painel de critério governante.
- Painel de assunções e limitações.
- Rastreamento do dataset usado.
