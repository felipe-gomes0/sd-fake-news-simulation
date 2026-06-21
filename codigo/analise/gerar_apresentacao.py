"""
gerar_apresentacao.py
=====================
Gera a apresentacao em PDF (estilo slides) exigida pelo trabalho, cobrindo
todas as secoes do enunciado, com tabelas e graficos embutidos.

Uso: python gerar_apresentacao.py
(rode antes: benchmark.py e gerar_graficos.py)
"""

import csv
import os
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, HRFlowable,
)

# BASE = analise/ ; a raiz do projeto fica dois niveis acima (analise/ -> codigo/ -> raiz).
BASE = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE, "..", "..", "resultados", "benchmark.csv")
GRAF = os.path.join(BASE, "..", "..", "graficos")
SAIDA = os.path.join(BASE, "..", "..", "Apresentacao_FakeNews.pdf")

AZUL = colors.HexColor("#1d4ed8")
AZUL_CLARO = colors.HexColor("#eff6ff")
ESCURO = colors.HexColor("#1e293b")
CINZA = colors.HexColor("#64748b")

styles = getSampleStyleSheet()
S = {
    "TituloCapa": ParagraphStyle("TituloCapa", parent=styles["Title"],
        fontSize=30, leading=36, textColor=AZUL, alignment=TA_CENTER),
    "SubCapa": ParagraphStyle("SubCapa", parent=styles["Normal"],
        fontSize=14, leading=20, textColor=ESCURO, alignment=TA_CENTER),
    "InfoCapa": ParagraphStyle("InfoCapa", parent=styles["Normal"],
        fontSize=11, leading=16, textColor=CINZA, alignment=TA_CENTER),
    "Secao": ParagraphStyle("Secao", parent=styles["Heading1"],
        fontSize=20, leading=24, textColor=AZUL),
    "Subsecao": ParagraphStyle("Subsecao", parent=styles["Heading2"],
        fontSize=14, leading=18, textColor=ESCURO),
    "Corpo": ParagraphStyle("Corpo", parent=styles["Normal"],
        fontSize=11.5, leading=17, textColor=ESCURO, alignment=TA_LEFT),
    "Bullet": ParagraphStyle("Bullet", parent=styles["Normal"],
        fontSize=11, leading=16, textColor=ESCURO, leftIndent=14, spaceBefore=2),
    "Legenda": ParagraphStyle("Legenda", parent=styles["Normal"],
        fontSize=8.5, leading=11, textColor=CINZA, alignment=TA_CENTER),
    "Cod": ParagraphStyle("Cod", parent=styles["Code"],
        fontSize=8.5, leading=11, textColor=ESCURO, backColor=AZUL_CLARO,
        borderPadding=6),
}


def P(t, s="Corpo"): return Paragraph(t, S[s])
def SP(h=10): return Spacer(1, h)
def HR(): return HRFlowable(width="100%", thickness=1.2, color=AZUL,
                            spaceBefore=4, spaceAfter=8)
def B(t): return Paragraph(f"• {t}", S["Bullet"])


def tabela(cabecalho, linhas, larguras=None):
    dados = [cabecalho] + linhas
    t = Table(dados, colWidths=larguras)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return t


def img(nome, larg=22*cm):
    caminho = os.path.join(GRAF, nome)
    if os.path.exists(caminho):
        return Image(caminho, width=larg, height=larg*0.58)
    return P(f"[grafico ausente: {nome}]")


def carregar_csv():
    if not os.path.exists(CSV_PATH):
        return []
    with open(CSV_PATH) as f:
        return list(csv.DictReader(f))


def tabela_resultados(dados):
    """Monta uma tabela de resultados a partir do maior grid e menor %."""
    if not dados:
        return P("Execute benchmark.py para gerar a tabela de resultados.")
    grids = sorted({(int(r["linhas"]), int(r["colunas"])) for r in dados})
    grid = grids[-1]
    percs = sorted({float(r["perc_espalhadores"]) for r in dados})
    perc = percs[0]
    sel = [r for r in dados if int(r["linhas"]) == grid[0]
           and abs(float(r["perc_espalhadores"]) - perc) < 1e-9]
    sel.sort(key=lambda r: (r["versao"], int(r["unidades"])))
    linhas = []
    for r in sel:
        linhas.append([
            r["versao"].capitalize(), r["unidades"],
            f'{float(r["tempo_s"])*1000:.1f} ms',
            f'{float(r["speedup"]):.2f}', f'{float(r["eficiencia"]):.2f}',
        ])
    cab = ["Versao", "Threads/Workers", "Tempo", "Speedup", "Eficiencia"]
    titulo = f"Grade {grid[0]}x{grid[1]} — {perc*100:.0f}% espalhadores"
    return [P(titulo, "Subsecao"), SP(4),
            tabela(cab, linhas, [4*cm, 4*cm, 3.5*cm, 3*cm, 3.5*cm])]


def construir():
    dados = carregar_csv()
    doc = SimpleDocTemplate(SAIDA, pagesize=landscape(A4),
                            leftMargin=1.8*cm, rightMargin=1.8*cm,
                            topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []

    # ---- Capa ----
    story += [
        SP(110),
        P("Propagacao de Fake News", "TituloCapa"),
        P("em Sistemas Paralelos e Distribuidos", "TituloCapa"),
        SP(18), HR(), SP(10),
        P("Sequencial &nbsp;·&nbsp; Paralela (Threads) &nbsp;·&nbsp; Distribuida (Sockets)", "SubCapa"),
        SP(8),
        P("Melhorias: Influenciadores Digitais &nbsp;·&nbsp; Resistencia a Propagacao", "InfoCapa"),
        SP(40),
        P("Disciplina: Sistemas Distribuidos", "InfoCapa"),
        P("Integrantes: __________________________  (preencher)", "InfoCapa"),
        PageBreak(),
    ]

    # ---- 1. Problema ----
    story += [
        P("1. Descricao do Problema", "Secao"), HR(),
        P("Simular como uma <b>fake news</b> se propaga numa populacao representada "
          "por uma matriz bidimensional N×M, inspirada em <b>automatos celulares</b> "
          "e na dinamica de difusao de informacao em redes.", "Corpo"), SP(10),
        P("Estados de cada individuo (celula):", "Subsecao"), SP(4),
        tabela(["Estado", "Codigo", "Significado"],
               [["Ignorante", "0", "Ainda nao acredita / nao recebeu"],
                ["Espalhador", "1", "Acredita e compartilha ativamente"],
                ["Inativo", "2", "Recebeu, mas parou de compartilhar"]],
               [6*cm, 3*cm, 13*cm]),
        SP(12),
        P("A propagacao ocorre <b>localmente</b> pela vizinhanca de Moore "
          "(ate 8 vizinhos), em geracoes discretas.", "Corpo"),
        PageBreak(),
    ]

    # ---- 2. Modelo Computacional ----
    story += [
        P("2. Modelo Computacional", "Secao"), HR(),
        P("Regras de transicao (aplicadas a TODAS as celulas a cada geracao):", "Subsecao"),
        SP(4),
        B("<b>Ignorante → Espalhador</b>: se o nº de vizinhos espalhadores ≥ limiar de convencimento"),
        B("<b>Espalhador → Inativo</b>: sempre na geracao seguinte (duracao de 1 geracao)"),
        B("<b>Inativo → Inativo</b>: permanente (nao volta a propagar)"),
        SP(10),
        P("Vizinhanca de Moore (X = celula central):", "Subsecao"), SP(2),
        P("A&nbsp;B&nbsp;C&nbsp;&nbsp;→&nbsp;&nbsp;os 8 vizinhos de X<br/>"
          "D&nbsp;X&nbsp;E<br/>F&nbsp;G&nbsp;H", "Cod"),
        SP(10),
        P("Propriedade-chave: a proxima geracao e calculada em uma <b>nova matriz</b>, "
          "lendo sempre o estado da geracao atual (atualizacao sincrona). Isso torna o "
          "resultado <b>determinista</b> e independente da ordem de processamento — "
          "o que permite paralelizar sem alterar o comportamento logico.", "Corpo"),
        PageBreak(),
    ]

    # ---- 3. Solucao Sequencial ----
    story += [
        P("3. Solucao Sequencial (baseline)", "Secao"), HR(),
        P("Percorre a matriz inteira em um unico fluxo, celula a celula, "
          "gerando a nova matriz. Serve de referencia para speedup/eficiencia.", "Corpo"),
        SP(8),
        P("Nucleo do laco (arquivo FakeNews_sequencial.py):", "Subsecao"), SP(2),
        P("for i in range(linhas):<br/>"
          "&nbsp;&nbsp;for j in range(colunas):<br/>"
          "&nbsp;&nbsp;&nbsp;&nbsp;nova[i][j] = proxima_celula(grade, i, j, limiar)", "Cod"),
        SP(10),
        P("Complexidade por geracao: O(linhas × colunas × 8). O custo cresce "
          "linearmente com o nº de celulas — motivacao para paralelizar.", "Corpo"),
        PageBreak(),
    ]

    # ---- 4. Versao Paralela ----
    story += [
        P("4. Versao Paralela (Threads)", "Secao"), HR(),
        P("Divisao explicita: a matriz e fatiada em <b>faixas horizontais</b> "
          "contiguas, uma por thread (FakeNews_paralelo.py).", "Corpo"), SP(6),
        B("Cada thread calcula apenas SUAS linhas, lendo a grade atual (somente leitura) "
          "e escrevendo na sua regiao de 'nova_grade'."),
        B("Regioes de escrita <b>disjuntas</b> ⇒ sem condicao de corrida (race condition), sem lock."),
        B("Sincronizacao por <b>threading.Barrier</b>: ao fim de cada geracao a barreira "
          "dispara a troca de grades e a verificacao de parada ⇒ consistencia entre geracoes."),
        B("<b>Threads persistentes</b>: criadas uma vez, processam todas as geracoes (evita overhead)."),
        SP(8),
        P("Limitacao fundamental (analisada na secao 8): o <b>GIL</b> do CPython serializa "
          "bytecode Python, limitando o ganho de threads para trabalho CPU-bound puro.", "Corpo"),
        PageBreak(),
    ]

    # ---- 5. Versao Distribuida ----
    story += [
        P("5. Versao Distribuida (Sockets)", "Secao"), HR(),
        P("Arquitetura <b>Master-Worker</b> sobre TCP (FakeNews_servidor.py + FakeNews_worker.py). "
          "Cada worker e um <b>processo independente</b> (sem GIL compartilhado).", "Corpo"), SP(6),
        B("O master divide as linhas em faixas (uma por worker) e, a cada geracao, envia a cada um "
          "o seu bloco + as <b>ghost rows</b> (linhas vizinhas emprestadas)."),
        B("As ghost rows <b>sincronizam as fronteiras</b>: sem elas, a 1ª e a ultima linha de cada "
          "faixa ficariam inconsistentes em relacao a versao sequencial."),
        B("O worker calcula apenas suas linhas reais e devolve; o master remonta a matriz global "
          "⇒ consistencia de geracao garantida."),
        B("Protocolo: JSON com <b>prefixo de tamanho (4 bytes)</b> para delimitar mensagens no fluxo TCP."),
        SP(10), img("g5_arquitetura.png", 17*cm),
        PageBreak(),
    ]

    # ---- 6. Divisao do processamento ----
    story += [
        P("6. Divisao da Matriz / Processamento", "Secao"), HR(),
        P("Ambas as versoes usam <b>particionamento por faixas de linhas</b> "
          "(decomposicao de dominio 1D):", "Corpo"), SP(6),
        tabela(["Aspecto", "Paralela (Threads)", "Distribuida (Sockets)"],
               [["Unidade", "Thread", "Processo (worker)"],
                ["Memoria", "Compartilhada", "Isolada (copia por mensagem)"],
                ["Fronteiras", "Leitura direta da grade", "Ghost rows via rede"],
                ["Sincronizacao", "threading.Barrier", "Master junta as faixas"],
                ["Comunicacao", "Nenhuma (memoria)", "TCP (JSON + prefixo)"],
                ["Limite de CPU", "GIL (CPython)", "Real (processos)"]],
               [5*cm, 8.5*cm, 8.5*cm]),
        SP(8),
        P("A equivalencia foi <b>verificada</b> (testar_corretude.py): grade final e historico "
          "identicos a versao sequencial em 1, 2, 4 e 8 threads e 1, 2, 3 workers, inclusive em "
          "grades com dimensoes nao multiplas do nº de unidades.", "Corpo"),
        PageBreak(),
    ]

    # ---- 7. Resultados ----
    story += [P("7. Resultados Experimentais", "Secao"), HR()]
    story += tabela_resultados(dados)
    story += [
        SP(8),
        P("<b>Atencao:</b> os numeros acima foram gerados em ambiente de build de <b>1 nucleo</b>. "
          "Regenere na maquina multi-core do grupo (benchmark.py → gerar_graficos.py → "
          "gerar_apresentacao.py) para valores representativos.", "Legenda"),
        PageBreak(),
        P("7.1 Speedup e Eficiencia", "Subsecao"), SP(4),
        img("g1_speedup.png", 15*cm),
        PageBreak(),
        img("g2_eficiencia.png", 15*cm),
        PageBreak(),
        P("7.2 Tempo por versao e escalabilidade", "Subsecao"), SP(4),
        img("g3_tempo_barras.png", 15*cm),
        PageBreak(),
        img("g4_escalabilidade.png", 15*cm),
        PageBreak(),
    ]

    # ---- 8. Analise / Dificuldades ----
    story += [
        P("8. Analise de Gargalos e Dificuldades", "Secao"), HR(),
        B("<b>GIL (paralela):</b> em CPython, threads nao executam bytecode Python em paralelo. "
          "Para trabalho CPU-bound, o speedup com threads tende a ~1. A divisao e os resultados "
          "estao corretos, mas o ganho de CPU e limitado pela plataforma — nao pela logica."),
        B("<b>Custo de comunicacao (distribuida):</b> serializar JSON e trafegar a matriz por "
          "geracao domina em grades pequenas. O ganho aparece quando o <b>custo de calculo por "
          "faixa supera o custo de comunicacao</b> (grades grandes / mais geracoes)."),
        B("<b>Sincronizacao de fronteiras:</b> montar e enviar as ghost rows corretamente (e tratar "
          "os workers de borda, que tem ghost de um lado so) foi o ponto mais delicado."),
        B("<b>Barreira e parada:</b> garantir que todas as threads terminem a geracao antes da troca "
          "de grades, e que a condicao de parada seja avaliada uma unica vez por geracao."),
        SP(8),
        P("Conclusao: o paralelismo de CPU real, em Python puro, vem da <b>distribuicao em "
          "processos</b>; threads servem para estruturar a divisao e para I/O. Em linguagens sem "
          "GIL (ou com multiprocessing), a versao por faixas escalaria com os nucleos.", "Corpo"),
        PageBreak(),
    ]

    # ---- 9. Melhorias ----
    story += [
        P("9. Melhorias Implementadas", "Secao"), HR(),
        P("Modelo estendido em FakeNews_melhorias.py (justificativa na secao 10):", "Corpo"), SP(6),
        B("<b>Influenciadores digitais:</b> contas de grande alcance pesam 2 ao espalhar e sao mais "
          "suscetiveis (limiar −1). Inspirado em maximizacao de influencia em redes (Kempe et al., 2003)."),
        B("<b>Resistentes a propagacao:</b> individuos com letramento midiatico tem limiar dobrado, "
          "funcionando como freio. Inspirado em 'stiflers' do modelo de rumores (Daley & Kendall, 1965)."),
        B("<b>Estatisticas adicionais:</b> pico de espalhadores e geracao do pico, alcance total "
          "(quem chegou a acreditar) e nº de nunca-atingidos."),
        B("<b>Visualizacao e benchmark automatizado:</b> geracao de graficos e CSV reprodutiveis."),
        PageBreak(),
    ]

    # ---- 10. Referencias ----
    story += [
        P("10. Referencias Bibliograficas", "Secao"), HR(),
        B("DALEY, D. J.; KENDALL, D. G. Stochastic rumours. <i>IMA Journal of Applied "
          "Mathematics</i>, v. 1, n. 1, p. 42-55, 1965."),
        B("KERMACK, W. O.; McKENDRICK, A. G. A contribution to the mathematical theory of "
          "epidemics. <i>Proc. Royal Society A</i>, v. 115, 1927. (modelo SIR)"),
        B("KEMPE, D.; KLEINBERG, J.; TARDOS, E. Maximizing the spread of influence through a "
          "social network. <i>ACM SIGKDD</i>, 2003."),
        B("BARABASI, A.-L.; ALBERT, R. Emergence of scaling in random networks. <i>Science</i>, "
          "v. 286, 1999."),
        B("WOLFRAM, S. <i>A New Kind of Science</i>. Wolfram Media, 2002. (automatos celulares)"),
        B("TANENBAUM, A. S.; VAN STEEN, M. <i>Distributed Systems: Principles and Paradigms</i>. "
          "3. ed. 2017."),
        B("BEAZLEY, D. Understanding the Python GIL. <i>PyCon</i>, 2010."),
        B("Python Software Foundation. <i>threading</i> e <i>socket</i> — documentacao oficial. "
          "docs.python.org."),
        PageBreak(),
    ]

    # ---- 11. Contribuicao individual ----
    story += [
        P("11. Contribuicao Individual dos Integrantes", "Secao"), HR(),
        P("Preencher com o nome e a contribuicao de cada integrante:", "Corpo"), SP(6),
        tabela(["Integrante", "Principais contribuicoes"],
               [["________________", "________________________________________"],
                ["________________", "________________________________________"],
                ["________________", "________________________________________"],
                ["________________", "________________________________________"]],
               [6*cm, 16*cm]),
        SP(14),
        P("Repositorio GitHub: github.com/________/________  (inserir link)", "InfoCapa"),
    ]

    doc.build(story)
    print(f"PDF gerado: {os.path.abspath(SAIDA)}")


if __name__ == "__main__":
    construir()
