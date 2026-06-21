"""
runner_distribuido.py
=====================
Auxiliar que sobe N workers como SUBPROCESSOS e executa o master no processo
atual, retornando (grade_final, tempo, historico). Usado pelo teste de
corretude e pelo benchmark distribuido para automatizar a orquestracao.

(Em producao/apresentacao voce roda master e workers manualmente em terminais
ou maquinas separadas, conforme o README. Aqui automatizamos para medir.)
"""

import sys
import time
import socket
import subprocess
import threading
import os
from pathlib import Path

# Torna as pastas irmas de codigo/ (nucleo/, simulacao/, distribuido/, analise/)
# importaveis ao rodar "python <arquivo>.py" de dentro de qualquer subpasta.
_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
for _p in ("nucleo", "simulacao", "distribuido", "analise"):
    sys.path.insert(0, os.path.join(_RAIZ, _p))

import FakeNews_servidor as servidor

DIR = Path(__file__).resolve().parent


def _porta_livre():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    porta = s.getsockname()[1]
    s.close()
    return porta


def rodar_distribuido(linhas, colunas, geracoes, percentual, limiar,
                      num_workers, verbose=False):
    porta = _porta_livre()

    resultado = {}

    def alvo():
        g, t, h = servidor.executar_simulacao(
            linhas, colunas, geracoes, percentual, limiar,
            num_workers, "127.0.0.1", porta, verbose=verbose
        )
        resultado["grade"] = g
        resultado["tempo"] = t
        resultado["historico"] = h

    thread = threading.Thread(target=alvo)
    thread.start()
    time.sleep(0.4) 

    procs = []
    for _ in range(num_workers):
        p = subprocess.Popen(
            [sys.executable, str(DIR / "FakeNews_worker.py"),
             "--host", "127.0.0.1", "--porta", str(porta)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        procs.append(p)

    thread.join()
    for p in procs:
        p.wait(timeout=10)

    return resultado["grade"], resultado["tempo"], resultado["historico"]
