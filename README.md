# Calculadora de viabilidade: consórcio x financiamento

Código de apoio do Projeto Aplicado do curso **IA para Negócios (USP)**, de Norberto Sampa, outubro de 2026.

O script `calc_v2.py` refaz em código os números de dois estudos de crédito que tinham sido gerados por ferramentas construídas com IA generativa (Abacus.ai e Poe, com Claude Opus 4.6). Os clientes estão anonimizados como Cliente A e Cliente B, e nenhum dado pessoal aparece no código.

## O que o script calcula

- **Cliente A.** Consórcio Porto contra financiamento SAC, a partir da simulação oficial da administradora. Calcula a TIR real do consórcio, o custo da operação sobre o dinheiro novo e a análise diferencial mês a mês, com aluguel durante a espera e aplicações líquidas de IR.
- **Cliente B.** Recalcula, na mesma régua, os cenários de uma conversa de análise feita com IA: consórcio para quitar o financiamento contra amortização.

## Premissas

- Correção anual das parcelas do consórcio de 4% a.a., a cada 12 meses.
- Aluguel do Cliente A de R$ 10.000 por mês até a contemplação.
- IR de 15% sobre as aplicações.

## Como rodar

```
pip install numpy scipy matplotlib
python calc_v2.py
```

O script gera `resultados_v2.json`, `posicao169.json` e os gráficos usados no trabalho.

Estudo informativo, não constitui recomendação de produto financeiro.
