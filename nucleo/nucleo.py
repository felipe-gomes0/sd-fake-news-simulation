"""
nucleo.py
=========
Modelo computacional compartilhado pela simulacao de Propagacao de Fake News.

Centralizar a REGRA DE TRANSICAO aqui garante que as tres versoes
(sequencial, paralela e distribuida) produzam EXATAMENTE o mesmo resultado.
A divisao do trabalho (entre threads ou processos) e implementada
explicitamente em cada versao; apenas a logica de uma celula e reutilizada.

Estados:
    0 = IGNORANTE : ainda nao acredita na informacao
    1 = ESPALHADOR: acredita e compartilha ativamente
    2 = INATIVO   : recebeu a informacao, mas parou de compartilhar

Vizinhanca de Moore (ate 8 vizinhos), geracoes discretas.
"""

import random

IGNORANTE = 0
ESPALHADOR = 1
INATIVO = 2


def criar_grade(linhas, colunas, percentual_espalhadores=0.02, semente=42):
    """
    Cria a matriz inicial. A maioria comeca IGNORANTE; uma fracao
    'percentual_espalhadores' comeca como ESPALHADOR.

    A semente fixa garante que todas as versoes partam do MESMO estado
    inicial, permitindo comparar resultados celula a celula.
    """
    random.seed(semente)
    grade = [[IGNORANTE for _ in range(colunas)] for _ in range(linhas)]

    total_espalhadores = int(linhas * colunas * percentual_espalhadores)
    for _ in range(total_espalhadores):
        i = random.randint(0, linhas - 1)
        j = random.randint(0, colunas - 1)
        grade[i][j] = ESPALHADOR
    return grade


def contar_vizinhos_espalhadores(grade, i, j):
    """
    Conta quantos dos 8 vizinhos de Moore da celula (i, j) sao ESPALHADORES.
    As bordas da matriz sao tratadas por recorte (clamping): vizinhos fora
    da grade simplesmente nao existem.
    """
    linhas = len(grade)
    colunas = len(grade[0])
    total = 0
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            if di == 0 and dj == 0:
                continue  # a propria celula nao e vizinha de si mesma
            ni, nj = i + di, j + dj
            if 0 <= ni < linhas and 0 <= nj < colunas:
                if grade[ni][nj] == ESPALHADOR:
                    total += 1
    return total


def proxima_celula(grade, i, j, limiar_convencimento=2):
    """
    Retorna o PROXIMO estado de uma unica celula (i, j).

    Regras:
      - IGNORANTE  -> ESPALHADOR  se vizinhos_espalhadores >= limiar
      - ESPALHADOR -> INATIVO     sempre (duracao de 1 geracao)
      - INATIVO    -> INATIVO     permanente

    Esta funcao e o "coracao" do modelo e e identica nas tres versoes.
    """
    estado = grade[i][j]

    if estado == IGNORANTE:
        if contar_vizinhos_espalhadores(grade, i, j) >= limiar_convencimento:
            return ESPALHADOR
        return IGNORANTE
    if estado == ESPALHADOR:
        return INATIVO
    return INATIVO  # INATIVO permanece INATIVO


def contar_estados(grade):
    """Conta quantas celulas existem em cada estado."""
    contagem = {IGNORANTE: 0, ESPALHADOR: 0, INATIVO: 0}
    for linha in grade:
        for celula in linha:
            contagem[celula] += 1
    return contagem


def calcular_faixas(linhas, n_partes):
    """
    Divide 'linhas' em 'n_partes' faixas horizontais contiguas o mais
    equilibradas possivel. Retorna lista de tuplas (inicio, fim) com
    intervalo semiaberto [inicio, fim).

    Exemplo: calcular_faixas(10, 3) -> [(0,4), (4,7), (7,10)]
    Esta e a base da divisao explicita do trabalho entre threads/processos.
    """
    base = linhas // n_partes
    resto = linhas % n_partes
    faixas = []
    inicio = 0
    for k in range(n_partes):
        tamanho = base + (1 if k < resto else 0)
        faixas.append((inicio, inicio + tamanho))
        inicio += tamanho
    return faixas


def imprimir_grade(grade, limite=30):
    """Mostra um recorte da grade no terminal (para demonstracao)."""
    simbolos = {IGNORANTE: ".", ESPALHADOR: "E", INATIVO: "N"}
    for i in range(min(len(grade), limite)):
        print(" ".join(simbolos[grade[i][j]]
                        for j in range(min(len(grade[0]), limite))))
    print()
