"""
FakeNews_sequencial.py
======================
Versao SEQUENCIAL (baseline). Processa a matriz inteira em um unico
fluxo de execucao, uma celula de cada vez. Serve de referencia para
medir speedup e eficiencia das versoes paralela e distribuida.

Uso:
    python FakeNews_sequencial.py
"""

import time
import argparse

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
import os as _os, sys as _sys
_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    _sys.path.insert(0, _os.path.join(_RAIZ, _p))

from nucleo import (
    IGNORANTE, ESPALHADOR, INATIVO,
    criar_grade, proxima_celula, contar_estados, imprimir_grade,
)


def proxima_geracao(grade, limiar):
    """
    Calcula a proxima geracao inteira lendo da grade atual e escrevendo
    em uma NOVA grade (evita atualizacao 'ao vivo').
    """
    linhas = len(grade)
    colunas = len(grade[0])
    nova = [[0] * colunas for _ in range(linhas)]
    for i in range(linhas):
        for j in range(colunas):
            nova[i][j] = proxima_celula(grade, i, j, limiar)
    return nova


def executar_simulacao(linhas=100, colunas=100, geracoes=50,
                       percentual_espalhadores=0.05, limiar_convencimento=3,
                       mostrar_grade=False, verbose=True):
    grade = criar_grade(linhas, colunas, percentual_espalhadores)

    if verbose:
        print("=== SIMULACAO SEQUENCIAL DE PROPAGACAO DE FAKE NEWS ===")
        print(f"Grade: {linhas} x {colunas} ({linhas*colunas:,} pessoas) | "
              f"Geracoes: {geracoes} | Limiar: {limiar_convencimento}")
        ini = contar_estados(grade)
        print(f"Espalhadores iniciais: {ini[ESPALHADOR]:,} "
              f"({percentual_espalhadores*100:.2f}%)\n")

    inicio = time.time()
    historico = []
    for geracao in range(geracoes):
        grade = proxima_geracao(grade, limiar_convencimento)
        c = contar_estados(grade)
        historico.append(c)
        if verbose:
            print(f"Geracao {geracao+1:03d} | Ignorantes: {c[IGNORANTE]:>10,} | "
                  f"Espalhadores: {c[ESPALHADOR]:>10,} | Inativos: {c[INATIVO]:>10,}")
            if mostrar_grade:
                imprimir_grade(grade)
        if c[ESPALHADOR] == 0:
            if verbose:
                print("\nPropagacao encerrada: nao ha mais espalhadores.")
            break
    tempo = time.time() - inicio

    if verbose:
        total = linhas * colunas
        f = contar_estados(grade)
        print("\n=== RESULTADO FINAL ===")
        print(f"Tempo total: {tempo:.4f} s")
        print(f"Ignorantes:  {f[IGNORANTE]:,} ({f[IGNORANTE]/total*100:.2f}%)")
        print(f"Espalhadores:{f[ESPALHADOR]:,} ({f[ESPALHADOR]/total*100:.2f}%)")
        print(f"Inativos:    {f[INATIVO]:,} ({f[INATIVO]/total*100:.2f}%)")

    return grade, tempo, historico


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Simulacao sequencial de fake news")
    p.add_argument("--linhas", type=int, default=100)
    p.add_argument("--colunas", type=int, default=100)
    p.add_argument("--geracoes", type=int, default=50)
    p.add_argument("--espalhadores", type=float, default=0.05)
    p.add_argument("--limiar", type=int, default=3)
    args = p.parse_args()
    executar_simulacao(args.linhas, args.colunas, args.geracoes,
                       args.espalhadores, args.limiar)
