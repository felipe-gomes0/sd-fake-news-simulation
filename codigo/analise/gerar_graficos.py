"""
gerar_graficos.py
=================
Le resultados/benchmark.csv e gera os graficos de desempenho em graficos/.
Tambem desenha um diagrama esquematico da arquitetura distribuida.

Gera:
  g1_speedup.png        - speedup x nº de unidades (paralela vs distribuida)
  g2_eficiencia.png     - eficiencia x nº de unidades
  g3_tempo_barras.png   - tempo: sequencial vs melhor paralela vs melhor distribuida
  g4_escalabilidade.png - tempo x tamanho da grade
  g5_arquitetura.png    - diagrama master-worker com ghost rows

Uso: python gerar_graficos.py
"""

import csv
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

# BASE = analise/ ; a raiz do projeto fica dois niveis acima (analise/ -> codigo/ -> raiz).
BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "..", "..", "resultados", "benchmark.csv")
SAIDA = os.path.join(BASE, "..", "..", "graficos")
os.makedirs(SAIDA, exist_ok=True)

AZUL, VERDE, VERMELHO, CINZA = "#2563eb", "#16a34a", "#dc2626", "#64748b"
NOTA_1NUCLEO = ("Ambiente de build: 1 nucleo. Regenere na maquina multi-core "
                "do grupo para resultados representativos.")


def carregar():
    with open(CSV_PATH) as f:
        return list(csv.DictReader(f))


def num(x):
    return float(x)


def cenario_repr(linhas):
    """Escolhe o maior grid e menor % como cenario de referencia dos graficos."""
    grids = sorted({(int(r["linhas"]), int(r["colunas"])) for r in linhas})
    maior = grids[-1]
    percs = sorted({float(r["perc_espalhadores"]) for r in linhas})
    return maior, percs[0]


def filtra(linhas, versao, grid, perc):
    out = [r for r in linhas
           if r["versao"] == versao
           and int(r["linhas"]) == grid[0] and int(r["colunas"]) == grid[1]
           and abs(float(r["perc_espalhadores"]) - perc) < 1e-9]
    return sorted(out, key=lambda r: int(r["unidades"]))


def g1_speedup(linhas, grid, perc):
    par = filtra(linhas, "paralela", grid, perc)
    dis = filtra(linhas, "distribuida", grid, perc)
    fig, ax = plt.subplots(figsize=(8, 5))
    if par:
        ax.plot([int(r["unidades"]) for r in par], [num(r["speedup"]) for r in par],
                "o-", color=AZUL, lw=2, label="Paralela (threads)")
    if dis:
        ax.plot([int(r["unidades"]) for r in dis], [num(r["speedup"]) for r in dis],
                "s-", color=VERDE, lw=2, label="Distribuida (workers)")
    maxu = max([int(r["unidades"]) for r in par + dis] + [1])
    ax.plot([1, maxu], [1, maxu], "--", color=CINZA, label="Speedup ideal (linear)")
    ax.set_xlabel("Nº de threads / workers")
    ax.set_ylabel("Speedup  S(p) = T_seq / T_p")
    ax.set_title(f"Speedup — grade {grid[0]}x{grid[1]}, {perc*100:.0f}% espalhadores")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.text(0.5, -0.02, NOTA_1NUCLEO, ha="center", fontsize=7, color=CINZA)
    fig.tight_layout(); fig.savefig(os.path.join(SAIDA, "g1_speedup.png"),
                                    dpi=130, bbox_inches="tight"); plt.close(fig)


def g2_eficiencia(linhas, grid, perc):
    par = filtra(linhas, "paralela", grid, perc)
    dis = filtra(linhas, "distribuida", grid, perc)
    fig, ax = plt.subplots(figsize=(8, 5))
    if par:
        ax.plot([int(r["unidades"]) for r in par], [num(r["eficiencia"]) for r in par],
                "o-", color=AZUL, lw=2, label="Paralela (threads)")
    if dis:
        ax.plot([int(r["unidades"]) for r in dis], [num(r["eficiencia"]) for r in dis],
                "s-", color=VERDE, lw=2, label="Distribuida (workers)")
    ax.axhline(1.0, ls="--", color=CINZA, label="Eficiencia ideal = 1,0")
    ax.set_xlabel("Nº de threads / workers")
    ax.set_ylabel("Eficiencia  E(p) = S(p) / p")
    ax.set_title(f"Eficiencia — grade {grid[0]}x{grid[1]}, {perc*100:.0f}% espalhadores")
    ax.set_ylim(0, 1.2); ax.legend(); ax.grid(True, alpha=0.3)
    fig.text(0.5, -0.02, NOTA_1NUCLEO, ha="center", fontsize=7, color=CINZA)
    fig.tight_layout(); fig.savefig(os.path.join(SAIDA, "g2_eficiencia.png"),
                                    dpi=130, bbox_inches="tight"); plt.close(fig)


def g3_tempo_barras(linhas, perc):
    grids = sorted({(int(r["linhas"]), int(r["colunas"])) for r in linhas})
    rotulos, t_seq, t_par, t_dis = [], [], [], []
    for grid in grids:
        seq = filtra(linhas, "sequencial", grid, perc)
        par = filtra(linhas, "paralela", grid, perc)
        dis = filtra(linhas, "distribuida", grid, perc)
        if not seq:
            continue
        rotulos.append(f"{grid[0]}x{grid[1]}")
        t_seq.append(num(seq[0]["tempo_s"]))
        t_par.append(min(num(r["tempo_s"]) for r in par) if par else 0)
        t_dis.append(min(num(r["tempo_s"]) for r in dis) if dis else 0)
    x = range(len(rotulos)); w = 0.26
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - w for i in x], t_seq, w, label="Sequencial", color=CINZA)
    ax.bar(list(x), t_par, w, label="Melhor paralela", color=AZUL)
    ax.bar([i + w for i in x], t_dis, w, label="Melhor distribuida", color=VERDE)
    ax.set_xticks(list(x)); ax.set_xticklabels(rotulos)
    ax.set_xlabel("Tamanho da grade"); ax.set_ylabel("Tempo (s)")
    ax.set_title(f"Tempo de execucao por versao ({perc*100:.0f}% espalhadores)")
    ax.legend(); ax.grid(True, axis="y", alpha=0.3)
    fig.text(0.5, -0.02, NOTA_1NUCLEO, ha="center", fontsize=7, color=CINZA)
    fig.tight_layout(); fig.savefig(os.path.join(SAIDA, "g3_tempo_barras.png"),
                                    dpi=130, bbox_inches="tight"); plt.close(fig)


def g4_escalabilidade(linhas, perc):
    grids = sorted({(int(r["linhas"]), int(r["colunas"])) for r in linhas})
    tam = [g[0] * g[1] for g in grids]
    seq = [num(filtra(linhas, "sequencial", g, perc)[0]["tempo_s"]) for g in grids]
    par = [min((num(r["tempo_s"]) for r in filtra(linhas, "paralela", g, perc)), default=None)
           for g in grids]
    dis = [min((num(r["tempo_s"]) for r in filtra(linhas, "distribuida", g, perc)), default=None)
           for g in grids]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(tam, seq, "o-", color=VERMELHO, lw=2, label="Sequencial")
    if any(v is not None for v in par):
        ax.plot(tam, par, "o-", color=AZUL, lw=2, label="Melhor paralela")
    if any(v is not None for v in dis):
        ax.plot(tam, dis, "s-", color=VERDE, lw=2, label="Melhor distribuida")
    ax.set_xlabel("Nº de celulas (linhas x colunas)")
    ax.set_ylabel("Tempo (s)")
    ax.set_title(f"Escalabilidade — custo cresce com o tamanho ({perc*100:.0f}% esp)")
    ax.legend(); ax.grid(True, alpha=0.3)
    fig.text(0.5, -0.02, NOTA_1NUCLEO, ha="center", fontsize=7, color=CINZA)
    fig.tight_layout(); fig.savefig(os.path.join(SAIDA, "g4_escalabilidade.png"),
                                    dpi=130, bbox_inches="tight"); plt.close(fig)


def g5_arquitetura():
    fig, ax = plt.subplots(figsize=(9, 5.5)); ax.axis("off")
    ax.set_xlim(0, 10); ax.set_ylim(0, 8)

    def caixa(x, y, w, h, texto, cor):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                                    fc=cor, ec="#1e293b", lw=1.5, alpha=0.9))
        ax.text(x + w/2, y + h/2, texto, ha="center", va="center",
                fontsize=9, color="white", weight="bold")

    caixa(3.5, 6.3, 3, 1.1, "MASTER\n(matriz global\n+ ghost rows)", AZUL)
    for k, x in enumerate([0.6, 4, 7.4]):
        caixa(x, 2.2, 2.4, 1.1, f"WORKER {k}\n(faixa de linhas)", VERDE)
        a = FancyArrowPatch((5, 6.3), (x + 1.2, 3.3), arrowstyle="-|>",
                            mutation_scale=14, color="#1e293b", lw=1.2)
        ax.add_patch(a)
        ax.text((5 + x + 1.2)/2 - 0.2, 4.85, "bloco+ghost", fontsize=7,
                color=CINZA, rotation=0)
        a2 = FancyArrowPatch((x + 1.2, 3.3), (5, 6.3), arrowstyle="-|>",
                             mutation_scale=10, color=VERDE, lw=0.8, ls="--",
                             connectionstyle="arc3,rad=0.25")
        ax.add_patch(a2)
    ax.text(8.2, 4.85, "linhas\ncalculadas", fontsize=7, color=VERDE)
    ax.text(5, 0.9, "Comunicacao TCP via sockets — JSON com prefixo de tamanho (4 bytes)",
            ha="center", fontsize=8, color="#1e293b")
    ax.text(5, 7.7, "Arquitetura Distribuida Master-Worker",
            ha="center", fontsize=12, weight="bold", color="#1e293b")
    fig.tight_layout(); fig.savefig(os.path.join(SAIDA, "g5_arquitetura.png"),
                                    dpi=130, bbox_inches="tight"); plt.close(fig)


def main():
    linhas = carregar()
    grid, perc = cenario_repr(linhas)
    g1_speedup(linhas, grid, perc)
    g2_eficiencia(linhas, grid, perc)
    g3_tempo_barras(linhas, perc)
    g4_escalabilidade(linhas, perc)
    g5_arquitetura()
    print(f"Graficos gerados em: {os.path.abspath(SAIDA)}")
    for nome in os.listdir(SAIDA):
        print("  -", nome)


if __name__ == "__main__":
    main()
