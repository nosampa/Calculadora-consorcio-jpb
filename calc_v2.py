"""
Projeto Aplicado USP - IA para Negocios
Recalculo dos dois casos usados no diagnostico das calculadoras feitas com IA.
Clientes anonimizados (Cliente A e Cliente B). Nenhum numero estimado a mao.

Premissas declaradas:
- Correcao anual das parcelas do consorcio: 4% a.a., aplicada a cada 12 meses
  (pratica dos grupos informada pelo consultor; regra exata depende do regulamento).
- Aluguel do Cliente A enquanto espera a contemplacao: R$ 10.000/mes.
- IR sobre aplicacoes de longo prazo: 15% (aliquota acima de 720 dias).
"""
import json
import numpy as np
from scipy.optimize import brentq
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

def irr(flows):
    f = lambda r: sum(c / (1 + r) ** t for t, c in enumerate(flows))
    grid = np.linspace(-0.02, 0.10, 1201)
    v = [f(g) for g in grid]
    for i in range(len(grid) - 1):
        if v[i] * v[i + 1] < 0:
            return brentq(f, grid[i], grid[i + 1])
    return None

aa = lambda m: (1 + m) ** 12 - 1
liq = lambda bruta_am, ir=0.15: bruta_am * (1 - ir)

# =========================== CASO A (Cliente A) ===========================
CARTA, PRAZO, C = 3_576_047.49, 169, 12
PRE, POS = 14_140.20, 13_391.09
LANCE, CRED = 1_000_000.00, 2_503_233.24
ADMIN_FR = CARTA * (0.195 + 0.02)
INCC = 0.04
ALUGUEL = 10_000.00
NOVO = 1_500_000.00

def parc_cons(incc=INCC):
    return [PRE if m <= C else POS * (1 + incc) ** ((m - 1) // 12) for m in range(1, PRAZO + 1)]

def tir_cons(incc=INCC, c_credito=C):
    p = parc_cons(incc)
    f = [0.0] + [-x for x in p]
    f[c_credito] += CRED * (1 + incc) ** ((c_credito - 1) // 12) - LANCE
    return irr(f)

# SAC com os parametros do relatorio do Poe: 0,9919% a.m., 360 meses, sem TR e sem seguro
def sac(principal=NOVO, i=0.009919, n=360):
    amort = principal / n
    saldo, out = principal, []
    for _ in range(n):
        out.append(amort + saldo * i)
        saldo -= amort
    return out

def diferencial_A(r_liq, aluguel=ALUGUEL, incc=INCC, horizonte=360):
    """Carteira do caminho consorcio em relacao ao SAC.
    D_t = desembolso SAC - desembolso consorcio, aplicado a r_liq."""
    s = sac()
    pc = parc_cons(incc)
    cart, serie = 0.0, []
    for t in range(0, horizonte + 1):
        out_sac = 1_000_000.0 if t == 0 else (s[t - 1] if t <= 360 else 0.0)
        out_con = 0.0
        if 1 <= t <= PRAZO:
            out_con += pc[t - 1]
        if 1 <= t <= C:
            out_con += aluguel
        if t == C:
            out_con += LANCE
        cart = cart * (1 + r_liq) + (out_sac - out_con)
        serie.append(cart)
    return serie

tA = {}
for lab, inc in [("incc4", 0.04), ("incc0", 0.0)]:
    m = tir_cons(inc)
    tA[lab] = {"am": m, "aa": aa(m)}
tA["real_incc4_aa"] = (1 + tA["incc4"]["aa"]) / 1.04 - 1

taxas = {"bruta_1.1_am_liq": liq(0.011), "cdi_10.5aa_liq": liq((1.105) ** (1 / 12) - 1)}
difA = {}
for k, r in taxas.items():
    s = diferencial_A(r)
    difA[k] = {"r_liq_am": r, "mes12": s[12], "mes169": s[169], "mes360": s[360]}
s0 = diferencial_A(taxas["cdi_10.5aa_liq"], aluguel=0)
difA["sem_aluguel_cdi"] = {"mes169": s0[169], "mes360": s0[360]}

caseA = {
    "carta_sobre_novo": CARTA / NOVO,
    "admin_fr_nominal": ADMIN_FR,
    "admin_fr_sobre_novo": ADMIN_FR / NOVO,
    "total_parcelas_incc4": sum(parc_cons()),
    "maior_parcela_incc4": max(parc_cons()),
    "maior_parcela_sobre_renda": max(parc_cons()) / 60_000,
    "sac_primeira": sac()[0], "sac_total": sum(sac()),
    "tir_sac_aa": aa(irr([NOVO] + [-x for x in sac()])),
    "tir_consorcio": tA, "diferencial": difA,
    "poe_rendimento_3mi_1.1": 3_000_000 * 0.011,
}

# =========================== CASO B (Cliente B) ===========================
# Numeros da propria resposta do Poe (cenarios A2 e B)
A2 = {"lance": 966_000.0, "pre": 23_543.0, "n_pre": 2, "sobra": 17_855.0, "pos": 9_736.48, "n_pos": 76}
A1 = {"pos": 4_284.76, "n_pos": 174}
B = {"amort": 500_000.0, "resgate": 31_711.0, "parc": 5_854.0, "n": 192}

poe_dash_A1 = A2["lance"] + A1["pos"] * A1["n_pos"]
poe_aba_A1 = A2["lance"] + A2["pre"] * A2["n_pre"] + A1["pos"] * A1["n_pos"]

def diferencial_B(r):
    """Carteira do caminho A2 (consorcio) em relacao a B (amortizar), mesma regua."""
    cart, serie = 0.0, []
    for t in range(0, B["n"] + 1):
        out_b = (B["amort"] - B["resgate"]) if t == 0 else (B["parc"] if t <= B["n"] else 0)
        if t == 0:
            out_a = A2["lance"]
        elif t <= A2["n_pre"]:
            out_a = A2["pre"] - (A2["sobra"] if t == A2["n_pre"] else 0)
        elif t <= A2["n_pre"] + A2["n_pos"]:
            out_a = A2["pos"]
        else:
            out_a = 0.0
        cart = cart * (1 + r) + (out_b - out_a)
        serie.append(cart)
    return serie

rB = {"poe_bruta_1.23": 0.0123, "liq_1.23": liq(0.0123), "cdi_liq": liq((1.105) ** (1 / 12) - 1)}
difB = {k: diferencial_B(r)[-1] for k, r in rB.items()}
# A propria conta do Poe: so o rendimento dos 466 mil por 78 meses a 1,23% bruto
poe_ganho = 466_000 * ((1.0123) ** 78 - 1)

caseB = {"poe_A1_dashboard": poe_dash_A1, "poe_A1_aba": poe_aba_A1,
         "poe_ganho_466k": poe_ganho, "poe_vantagem_B": 550_917,
         "diferencial_A2_vs_B_mes192": difB}

out = {"casoA": caseA, "casoB": caseB}
json.dump(out, open("resultados_v2.json", "w"), indent=2)

# =========================== FIGURAS ===========================
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10})
INK, MUTED, ACC, WARN = "#1f2a37", "#8a94a3", "#1d5fa8", "#b4462f"

sA = diferencial_A(taxas["cdi_10.5aa_liq"])
sA2 = diferencial_A(taxas["bruta_1.1_am_liq"])
fig, ax = plt.subplots(figsize=(7.2, 3.5), dpi=200)
ax.plot(range(361), np.array(sA) / 1e6, color=ACC, label="Aplicação a 100% do CDI (10,5% a.a.), líquida de IR")
ax.plot(range(361), np.array(sA2) / 1e6, color=MUTED, label="Aplicação a 1,1% a.m. (taxa do relatório), líquida de IR")
ax.axhline(0, color=INK, lw=0.8)
ax.axvline(169, color=MUTED, ls=":", lw=1)
ax.text(171, ax.get_ylim()[0] * 0.9 if ax.get_ylim()[0] < 0 else 0.1, "fim do consórcio", fontsize=8, color=MUTED)
ax.set_xlabel("Mês")
ax.set_ylabel("R$ milhões a favor do consórcio")
ax.set_title("Cliente A: quanto sobra no bolso com o consórcio em vez do SAC", loc="left", fontsize=11, color=INK)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
ax.legend(frameon=False, fontsize=8, loc="upper left")
plt.tight_layout()
plt.savefig("v2_fig_diferencial_A.png")
plt.close()

sB = diferencial_B(rB["cdi_liq"])
sBp = diferencial_B(rB["poe_bruta_1.23"])
fig, ax = plt.subplots(figsize=(7.2, 3.5), dpi=200)
ax.plot(range(len(sB)), np.array(sB) / 1e3, color=ACC, label="Aplicação a 100% do CDI, líquida de IR")
ax.plot(range(len(sBp)), np.array(sBp) / 1e3, color=WARN, ls="--", label="1,23% a.m. bruto (taxa usada pelo Poe)")
ax.axhline(0, color=INK, lw=0.8)
ax.axvline(78, color=MUTED, ls=":", lw=1)
ax.set_xlabel("Mês")
ax.set_ylabel("R$ mil a favor do consórcio (A2)")
ax.set_title("Cliente B: consórcio quitando a Caixa contra amortizar R$ 500 mil", loc="left", fontsize=11, color=INK)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
ax.legend(frameon=False, fontsize=8, loc="lower left")
plt.tight_layout()
plt.savefig("v2_fig_diferencial_B.png")
plt.close()

print(json.dumps(out, indent=2, default=float))

# ---- posicao liquida no mes 169 (fim do consorcio), descontando o saldo que o SAC ainda deve ----
saldo169 = NOVO - NOVO / 360 * 169
def difA_sac_n(r, n):
    s = sac(n=n); pc = parc_cons(); cart = 0.0
    for t in range(0, 170):
        o_s = 1_000_000 if t == 0 else (s[t - 1] if t <= n else 0)
        o_c = (pc[t - 1] if 1 <= t <= 169 else 0) + (ALUGUEL if 1 <= t <= 12 else 0) + (LANCE if t == 12 else 0)
        cart = cart * (1 + r) + (o_s - o_c)
    return cart
rC = taxas["cdi_10.5aa_liq"]; rR = taxas["bruta_1.1_am_liq"]
pos = {
    "SAC 360m, CDI líquido": diferencial_A(rC)[169] + saldo169,
    "SAC 360m, 1,1% a.m. líquido": diferencial_A(rR)[169] + saldo169,
    "SAC 360m, CDI, sem aluguel": diferencial_A(rC, aluguel=0)[169] + saldo169,
    "SAC em 169m, CDI líquido": difA_sac_n(rC, 169),
}
json.dump({k: v for k, v in pos.items()}, open("posicao169.json", "w"), indent=2)
fig, ax = plt.subplots(figsize=(7.2, 3.3), dpi=200)
labels = ["SAC 30 anos\nCDI líquido", "SAC 30 anos\n1,1% a.m. líquido", "SAC 30 anos\nsem aluguel", "SAC em 169 meses\nCDI líquido"]
vals = [v / 1e3 for v in pos.values()]
bars = ax.bar(labels, vals, color=[ACC, MUTED, MUTED, INK], width=0.6)
for b_, v in zip(bars, vals):
    ax.text(b_.get_x() + b_.get_width() / 2, v + 15, f"R$ {v:,.0f} mil".replace(",", "."), ha="center", fontsize=9, color=INK)
ax.set_ylabel("R$ mil a favor do consórcio")
ax.set_title("Cliente A: vantagem do consórcio no mês 169, já com aluguel e aplicação", loc="left", fontsize=10.5, color=INK)
ax.set_ylim(0, max(vals) * 1.2)
for sp in ["top", "right"]:
    ax.spines[sp].set_visible(False)
plt.tight_layout()
plt.savefig("v2_fig_diferencial_A.png")
plt.close()
print(pos)
