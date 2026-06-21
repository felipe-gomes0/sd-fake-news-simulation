"""
protocolo.py
============
Protocolo de mensagens sobre TCP para a versao distribuida.

Cada mensagem e enviada como:
    [4 bytes big-endian = tamanho N][N bytes = JSON em UTF-8]

O prefixo de tamanho resolve o problema de "fronteira de mensagem" do TCP
(o TCP e um fluxo de bytes, nao preserva limites de mensagem). Assim o
receptor sabe exatamente quantos bytes ler para montar uma mensagem completa.
"""

import json
import struct


def enviar_msg(sock, objeto):
    """Serializa 'objeto' em JSON e envia com prefixo de tamanho (4 bytes)."""
    dados = json.dumps(objeto).encode("utf-8")
    sock.sendall(struct.pack(">I", len(dados)) + dados)


def _recv_n(sock, n):
    """Le exatamente n bytes do socket (ou None se a conexao fechar)."""
    buf = bytearray()
    while len(buf) < n:
        pedaco = sock.recv(n - len(buf))
        if not pedaco:
            return None
        buf.extend(pedaco)
    return bytes(buf)


def receber_msg(sock):
    """Le uma mensagem completa e retorna o objeto desserializado (ou None)."""
    cabecalho = _recv_n(sock, 4)
    if cabecalho is None:
        return None
    (tamanho,) = struct.unpack(">I", cabecalho)
    corpo = _recv_n(sock, tamanho)
    if corpo is None:
        return None
    return json.loads(corpo.decode("utf-8"))
