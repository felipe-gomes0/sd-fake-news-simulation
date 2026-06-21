"""
FakeNews_melhorias.py
=====================
Versao SEQUENCIAL ESTENDIDA com melhorias no modelo. Mantida separada das
versoes de benchmark para que a comparacao de desempenho (seq/par/dist) use
o modelo-base identico. Aqui o foco e a QUALIDADE/REALISMO do modelo.

Melhorias implementadas (com justificativa tecnica):

1) INFLUENCIADORES DIGITAIS
   Uma fracao da populacao representa contas de grande alcance. Quando um
   influenciador esta ESPALHANDO, ele conta com PESO 2 na vizinhanca (alcance
   amplificado). Como IGNORANTE, e mais suscetivel (limiar reduzido em 1),
   refletindo maior exposicao a conteudo. Inspirado em modelos de maximizacao
   de influencia em redes sociais (Kempe, Kleinberg & Tardos, 2003) e na
   nocao de "hubs" em redes livres de escala (Barabasi & Albert, 1999).

2) RESISTENTES A PROPAGACAO
   Uma fracao representa individuos com maior letramento midiatico/ceticismo.
   Possuem limiar de convencimento DOBRADO (mais dificeis de convencer),
   funcionando como freio a propagacao. Inspirado em variantes do modelo SIR
   com "imunidade parcial" e no modelo de rumores de Daley & Kendall (1965),
   onde "stiflers" reduzem a difusao.

3) ESTATISTICAS ADICIONAIS
   Pico de espalhadores e geracao do pico, alcance total (quem chegou a
   acreditar), e taxa de propagacao por geracao.

Papeis (matriz paralela 'papeis'):
   0 = comum | 1 = influenciador | 2 = resistente
"""

import time
import random
import argparse

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
import os as _os, sys as _sys
_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    _sys.path.insert(0, _os.path.join(_RAIZ, _p))

from nucleo import IGNORANTE, ESPALHADOR, INATIVO, contar_estados

COMUM = 0
INFLUENCIADOR = 1
RESISTENTE = 2


def criar_papeis(linhas, colunas, perc_influenciadores=0.01,
                 perc_resistentes=0.10, semente=42):
    """Sorteia papeis para a populacao (independente do estado inicial)."""
    rng = random.Random(semente + 1)
    papeis = [[COMUM] * colunas for _ in range(linhas)]
    total = linhas * colunas
    for _ in range(int(total * perc_influenciadores)):
        papeis[rng.randint(0, linhas-1)][rng.randint(0, colunas-1)] = INFLUENCIADOR
    for _ in range(int(total * perc_resistentes)):
        i, j = rng.randint(0, linhas-1), rng.randint(0, colunas-1)
        if papeis[i][j] == COMUM:
            papeis[i][j] = RESISTENTE
    return papeis


def criar_grade(linhas, colunas, perc_espalhadores=0.05, semente=42):
    rng = random.Random(semente)
    grade = [[IGNORANTE] * colunas for _ in range(linhas)]
    for _ in range(int(linhas * colunas * perc_espalhadores)):
        grade[rng.randint(0, linhas-1)][rng.randint(0, colunas-1)] = ESPALHADOR
    return grade


def peso_vizinhos(grade, papeis, i, j):
    """Soma ponderada de vizinhos espalhadores (influenciador pesa 2)."""
    linhas, colunas = len(grade), len(grade[0])
    total = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue
            ni, nj = i + di, j + dj
            if 0 <= ni < linhas and 0 <= nj < colunas and grade[ni][nj] == ESPALHADOR:
                total += 2 if papeis[ni][nj] == INFLUENCIADOR else 1
    return total


def limiar_efetivo(papeis, i, j, limiar_base):
    if papeis[i][j] == INFLUENCIADOR:
        return max(1, limiar_base - 1)   # mais suscetivel
    if papeis[i][j] == RESISTENTE:
        return limiar_base * 2           # mais resistente
    return limiar_base


def proxima_geracao(grade, papeis, limiar_base):
    linhas, colunas = len(grade), len(grade[0])
    nova = [[0] * colunas for _ in range(linhas)]
    for i in range(linhas):
        for j in range(colunas):
            estado = grade[i][j]
            if estado == IGNORANTE:
                if peso_vizinhos(grade, papeis, i, j) >= limiar_efetivo(papeis, i, j, limiar_base):
                    nova[i][j] = ESPALHADOR
                else:
                    nova[i][j] = IGNORANTE
            else:
                nova[i][j] = INATIVO  # espalhador->inativo, inativo->inativo
    return nova


def executar_simulacao(linhas=100, colunas=100, geracoes=50,
                       perc_espalhadores=0.05, limiar=3,
                       perc_influenciadores=0.01, perc_resistentes=0.10,
                       verbose=True):
    grade = criar_grade(linhas, colunas, perc_espalhadores)
    papeis = criar_papeis(linhas, colunas, perc_influenciadores, perc_resistentes)
    total = linhas * colunas

    if verbose:
        n_inf = sum(r.count(INFLUENCIADOR) for r in papeis)
        n_res = sum(r.count(RESISTENTE) for r in papeis)
        print("=== SIMULACAO COM MELHORIAS (Influenciadores + Resistentes) ===")
        print(f"Grade: {linhas}x{colunas} ({total:,}) | Geracoes: {geracoes} | Limiar base: {limiar}")
        print(f"Influenciadores: {n_inf:,} ({n_inf/total*100:.2f}%) | "
              f"Resistentes: {n_res:,} ({n_res/total*100:.2f}%)\n")

    inicio = time.time()
    pico, geracao_pico, alcance_total = 0, 0, contar_estados(grade)[ESPALHADOR]
    for g in range(geracoes):
        grade = proxima_geracao(grade, papeis, limiar)
        c = contar_estados(grade)
        novos = c[ESPALHADOR]
        alcance_total += novos
        if c[ESPALHADOR] > pico:
            pico, geracao_pico = c[ESPALHADOR], g + 1
        if verbose:
            print(f"Geracao {g+1:03d} | Ign: {c[IGNORANTE]:>9,} | "
                  f"Esp: {c[ESPALHADOR]:>9,} | Ina: {c[INATIVO]:>9,}")
        if c[ESPALHADOR] == 0:
            if verbose:
                print("\nPropagacao encerrada: nao ha mais espalhadores.")
            break
    tempo = time.time() - inicio

    if verbose:
        f = contar_estados(grade)
        nunca = f[IGNORANTE]
        print("\n=== ESTATISTICAS ADICIONAIS ===")
        print(f"Tempo total: {tempo:.4f} s")
        print(f"Pico de espalhadores: {pico:,} (geracao {geracao_pico})")
        print(f"Alcance total (chegaram a acreditar): {total - nunca:,} "
              f"({(total-nunca)/total*100:.2f}%)")
        print(f"Nunca atingidos (resistencia + isolamento): {nunca:,} "
              f"({nunca/total*100:.2f}%)")
    return grade, tempo


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Simulacao com melhorias de modelo")
    p.add_argument("--linhas", type=int, default=100)
    p.add_argument("--colunas", type=int, default=100)
    p.add_argument("--geracoes", type=int, default=50)
    p.add_argument("--espalhadores", type=float, default=0.05)
    p.add_argument("--limiar", type=int, default=3)
    p.add_argument("--influenciadores", type=float, default=0.01)
    p.add_argument("--resistentes", type=float, default=0.10)
    args = p.parse_args()
    executar_simulacao(args.linhas, args.colunas, args.geracoes,
                       args.espalhadores, args.limiar,
                       args.influenciadores, args.resistentes)
