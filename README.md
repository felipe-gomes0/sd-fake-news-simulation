# Propagação de Fake News em Sistemas Paralelos e Distribuídos

Simulação da propagação de *fake news* numa população modelada como **autômato
celular** (matriz N×M, vizinhança de Moore). O projeto entrega **três versões**
equivalentes — sequencial, paralela (threads) e distribuída (sockets) — além de
benchmark, gráficos, melhorias de modelo e apresentação em PDF.

> As três versões produzem **resultado idêntico** (verificado por
> `testar_corretude.py`). As versões paralela e distribuída preservam o
> comportamento lógico da sequencial — só mudam *como* o trabalho é dividido.

---

## Estrutura

```
projeto/
├── codigo/
│   ├── nucleo/                       # modelo e comunicação compartilhados
│   │   ├── nucleo.py                 # estados, criação da grade, REGRA DE TRANSIÇÃO (compartilhada)
│   │   └── protocolo.py              # mensagens TCP (JSON + prefixo de 4 bytes)
│   ├── simulacao/                    # as versões da simulação
│   │   ├── FakeNews_sequencial.py    # versão sequencial (baseline)
│   │   ├── FakeNews_paralelo.py      # versão paralela (threads + Barrier, faixas de linhas)
│   │   ├── FakeNews_melhorias.py     # modelo estendido (influenciadores + resistentes)
│   │   └── FakeNews_original_professor.py  # versão original fornecida pelo professor
│   ├── distribuido/                  # versão distribuída (master-worker via sockets)
│   │   ├── FakeNews_servidor.py      # master da versão distribuída (ghost rows)
│   │   ├── FakeNews_worker.py        # worker da versão distribuída
│   │   └── runner_distribuido.py     # sobe workers como subprocessos (automação)
│   └── analise/                      # validação, benchmark, gráficos e apresentação
│       ├── testar_corretude.py       # prova: seq == paralela == distribuída
│       ├── benchmark.py              # mede tempo/speedup/eficiência -> resultados/benchmark.csv
│       ├── gerar_graficos.py         # gráficos PNG a partir do CSV
│       └── gerar_apresentacao.py     # gera Apresentacao_FakeNews.pdf
├── resultados/benchmark.csv
├── graficos/*.png
└── Apresentacao_FakeNews.pdf
```

> Cada script ajusta o `sys.path` no topo para enxergar os módulos das pastas
> irmãs (`nucleo/`, `simulacao/`, `distribuido/`, `analise/`), então os comandos
> abaixo funcionam rodando de dentro de `codigo/`.

Requisitos: **Python 3.8+**, `matplotlib` e `reportlab` (só para gráficos/PDF).
A simulação em si usa apenas a biblioteca padrão (`threading`, `socket`, `json`, `struct`).

```bash
pip install matplotlib reportlab
```

---

## Como executar

Entre na pasta `codigo/` antes de rodar os comandos.

### 1) Sequencial
```bash
python simulacao/FakeNews_sequencial.py --linhas 100 --colunas 100 --geracoes 50 --espalhadores 0.05 --limiar 3
```

### 2) Paralela (threads)
```bash
python simulacao/FakeNews_paralelo.py --linhas 100 --colunas 100 --geracoes 50 --threads 4
```

### 3) Distribuída (sockets) — manual, em terminais/máquinas separados
```bash
# Terminal 1 e 2 (um por worker):
python distribuido/FakeNews_worker.py --host 127.0.0.1 --porta 9099
python distribuido/FakeNews_worker.py --host 127.0.0.1 --porta 9099

# Terminal 3 (master, informando o nº de workers):
python distribuido/FakeNews_servidor.py --workers 2 --porta 9099 --linhas 100 --colunas 100 --geracoes 50
```
Para rodar em **máquinas diferentes**: suba o master em uma máquina e os workers
nas outras com `--host <IP_DO_MASTER>` (libere a porta no firewall).

### 4) Melhorias (modelo estendido)
```bash
python simulacao/FakeNews_melhorias.py --influenciadores 0.01 --resistentes 0.10
```

### 5) Validar corretude (seq == paralela == distribuída)
```bash
python analise/testar_corretude.py
```

### 6) Reproduzir resultados, gráficos e PDF  ⟵ rode na máquina de teste do grupo
```bash
python analise/benchmark.py            # rápido  (ou: python analise/benchmark.py --completo)
python analise/gerar_graficos.py
python analise/gerar_apresentacao.py
```

---

## Protocolo de comunicação (distribuída)

Cada mensagem TCP é `[4 bytes big-endian = tamanho N][N bytes = JSON UTF-8]`.
O prefixo resolve a fronteira de mensagem (o TCP é um fluxo de bytes).

**Master → Worker**
```json
{ "tipo": "processar", "bloco": [[...linhas com ghost...]],
  "ini_real": 1, "fim_real": 26, "limiar": 3 }
```
`bloco` = linhas reais do worker + *ghost rows* (linhas vizinhas emprestadas).
`[ini_real, fim_real)` = índices, dentro do bloco, das linhas que o worker deve calcular.

**Worker → Master**
```json
{ "linhas": [[...linhas reais já atualizadas...]] }
```

**Encerramento:** `{ "tipo": "fim" }`.

As *ghost rows* sincronizam as fronteiras: para calcular a 1ª/última linha da
faixa, o worker precisa enxergar uma linha do vizinho. Workers de borda recebem
ghost de um lado só (a borda global usa recorte, igual à versão sequencial).

---

## Divisão do trabalho

| Aspecto        | Paralela (threads)         | Distribuída (sockets)              |
|----------------|----------------------------|------------------------------------|
| Unidade        | Thread                     | Processo (worker)                  |
| Memória        | Compartilhada              | Isolada (cópia por mensagem)       |
| Fronteiras     | Leitura direta da grade    | Ghost rows via rede                |
| Sincronização  | `threading.Barrier`        | Master remonta as faixas           |
| Limite de CPU  | GIL (CPython)              | Paralelismo real (processos)       |

Particionamento por **faixas horizontais de linhas** (decomposição de domínio 1D)
nas duas versões. Sem condição de corrida na paralela: cada thread escreve em
linhas disjuntas.

---

## Observação importante sobre desempenho

O `benchmark.csv` e os gráficos versionados foram gerados num ambiente de
**1 núcleo** (CI), então mostram a limitação esperada: threads ~1× (GIL) e
distribuída < 1× (comunicação domina). **Regenere na máquina multi-core do
grupo** para obter os números representativos da apresentação — basta repetir o
passo 6.

Comportamento esperado em máquina multi-core:
- **Paralela (threads):** ganho limitado pelo **GIL** do CPython em trabalho
  CPU-bound — esse é, em si, um resultado a ser discutido.
- **Distribuída (processos):** ganho **real** quando o custo de cálculo por
  faixa supera o custo de comunicação (grades grandes / mais gerações).

---

## Configuração experimental (preencher)

| Item                      | Valor                          |
|---------------------------|--------------------------------|
| Processador               | __________________________     |
| Núcleos físicos / lógicos | _____ / _____                  |
| Memória RAM               | _____ GB                       |
| Sistema operacional       | __________________________     |
| Linguagem                 | Python                         |
| Versão do interpretador   | `python --version` → ________  |
| Ambiente de execução      | __________________________     |

---

## Referências

- Daley, D. J.; Kendall, D. G. *Stochastic rumours*. IMA J. Applied Math., 1965.
- Kermack & McKendrick. *A contribution to the mathematical theory of epidemics*, 1927 (SIR).
- Kempe, Kleinberg & Tardos. *Maximizing the spread of influence...*, ACM SIGKDD, 2003.
- Barabási & Albert. *Emergence of scaling in random networks*. Science, 1999.
- Tanenbaum & Van Steen. *Distributed Systems*, 3ª ed., 2017.
- Documentação oficial do Python: `threading`, `socket`.
