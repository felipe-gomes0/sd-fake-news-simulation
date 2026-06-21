"""
FakeNews_paralelo.py
====================
Versao PARALELA usando THREADS (threading da biblioteca padrao).

Estrategia de divisao explicita do trabalho:
  - A matriz e dividida em FAIXAS HORIZONTAIS contiguas (uma por thread).
  - Cada thread calcula a proxima geracao APENAS das suas linhas, lendo
    da grade atual (compartilhada, somente leitura nessa fase) e escrevendo
    em sua propria regiao de 'nova_grade'.
  - Como cada thread escreve em linhas DISJUNTAS, nao ha condicao de corrida
    (race condition) mesmo sem lock na escrita.

Sincronizacao:
  - Usamos threading.Barrier(n, action=...). Quando TODAS as threads terminam
    de calcular a geracao, a barreira dispara uma acao unica que troca as
    grades (grade <-> nova_grade), conta os estados e decide se deve parar.
    Isso mantem a consistencia entre geracoes: nenhuma thread comeca a
    proxima geracao antes de todas terminarem a atual.

Threads persistentes:
  - As threads sao criadas UMA vez e processam todas as geracoes em loop,
    evitando o custo de criar/destruir threads a cada geracao.

IMPORTANTE (limitacao analisada no relatorio): em CPython o GIL serializa
bytecode Python, entao para trabalho CPU-bound puro o ganho com threads e
limitado. Esta versao demonstra a divisao correta e a ausencia de races;
o paralelismo real de CPU aparece na versao DISTRIBUIDA (processos).

Uso:
    python FakeNews_paralelo.py --threads 4
"""

import time
import argparse
import threading

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
import os as _os, sys as _sys
_RAIZ = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    _sys.path.insert(0, _os.path.join(_RAIZ, _p))

from nucleo import (
    IGNORANTE, ESPALHADOR, INATIVO,
    criar_grade, proxima_celula, contar_estados, calcular_faixas,
)


class SimuladorParalelo:
    def __init__(self, grade, num_threads, geracoes, limiar):
        self.grade = grade
        self.nova_grade = [linha[:] for linha in grade]
        self.linhas = len(grade)
        self.colunas = len(grade[0])
        self.num_threads = num_threads
        self.geracoes = geracoes
        self.limiar = limiar

        self.faixas = calcular_faixas(self.linhas, num_threads)
        self.geracao_atual = 0
        self.parar = False
        self.historico = []

        # A acao da barreira roda UMA vez quando todas as threads chegam.
        self.barreira = threading.Barrier(num_threads, action=self._fim_de_geracao)

    def _fim_de_geracao(self):
        """Executada por UMA thread quando todas terminam a geracao atual."""
        # Troca de grades: a 'nova' vira a 'atual' da proxima geracao.
        self.grade, self.nova_grade = self.nova_grade, self.grade
        contagem = contar_estados(self.grade)
        self.historico.append(contagem)
        self.geracao_atual += 1
        if contagem[ESPALHADOR] == 0 or self.geracao_atual >= self.geracoes:
            self.parar = True

    def _trabalhador(self, tid):
        """Cada thread processa sempre a mesma faixa de linhas."""
        ini, fim = self.faixas[tid]
        while not self.parar:
            grade = self.grade
            nova = self.nova_grade
            limiar = self.limiar
            colunas = self.colunas
            for i in range(ini, fim):
                linha_nova = nova[i]
                for j in range(colunas):
                    linha_nova[j] = proxima_celula(grade, i, j, limiar)
            try:
                self.barreira.wait()  # dispara _fim_de_geracao quando todas chegam
            except threading.BrokenBarrierError:
                return

    def executar(self):
        threads = [threading.Thread(target=self._trabalhador, args=(t,))
                   for t in range(self.num_threads)]
        inicio = time.time()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        tempo = time.time() - inicio
        return self.grade, tempo, self.historico


def executar_simulacao(linhas=100, colunas=100, geracoes=50,
                       percentual_espalhadores=0.05, limiar_convencimento=3,
                       num_threads=4, verbose=True):
    grade = criar_grade(linhas, colunas, percentual_espalhadores)

    if verbose:
        print("=== SIMULACAO PARALELA (THREADS) DE PROPAGACAO DE FAKE NEWS ===")
        print(f"Grade: {linhas} x {colunas} ({linhas*colunas:,} pessoas) | "
              f"Geracoes: {geracoes} | Threads: {num_threads} | Limiar: {limiar_convencimento}")
        faixas = calcular_faixas(linhas, num_threads)
        print(f"Faixas por thread: {faixas}\n")

    sim = SimuladorParalelo(grade, num_threads, geracoes, limiar_convencimento)
    grade_final, tempo, historico = sim.executar()

    if verbose:
        for g, c in enumerate(historico):
            print(f"Geracao {g+1:03d} | Ignorantes: {c[IGNORANTE]:>10,} | "
                  f"Espalhadores: {c[ESPALHADOR]:>10,} | Inativos: {c[INATIVO]:>10,}")
        total = linhas * colunas
        f = contar_estados(grade_final)
        print("\n=== RESULTADO FINAL ===")
        print(f"Tempo total: {tempo:.4f} s")
        print(f"Ignorantes:  {f[IGNORANTE]:,} ({f[IGNORANTE]/total*100:.2f}%)")
        print(f"Espalhadores:{f[ESPALHADOR]:,} ({f[ESPALHADOR]/total*100:.2f}%)")
        print(f"Inativos:    {f[INATIVO]:,} ({f[INATIVO]/total*100:.2f}%)")

    return grade_final, tempo, historico


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Simulacao paralela (threads) de fake news")
    p.add_argument("--linhas", type=int, default=100)
    p.add_argument("--colunas", type=int, default=100)
    p.add_argument("--geracoes", type=int, default=50)
    p.add_argument("--espalhadores", type=float, default=0.05)
    p.add_argument("--limiar", type=int, default=3)
    p.add_argument("--threads", type=int, default=4)
    args = p.parse_args()
    executar_simulacao(args.linhas, args.colunas, args.geracoes,
                       args.espalhadores, args.limiar, args.threads)
