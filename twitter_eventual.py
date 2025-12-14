from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional
from collections import defaultdict
import threading
import time
import sys
import uvicorn
import requests

app = FastAPI()

# Estado global
myProcessId = 0
timestamp = 0

posts = {}
replies = defaultdict(list)

processes = [
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8081",
    "http://127.0.0.1:8082",
]

lock = threading.Lock()

# Modelo de evento
class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    timestamp: Optional[int] = None

# Endpoints HTTP
@app.post("/post")
def post(msg: Event):
    """
    Cria um post ou reply localmente e replica para as demais réplicas.
    """
    global timestamp

    with lock:
        if msg.processId == myProcessId:
            timestamp += 1
            msg.timestamp = timestamp

        processMsg(msg)

    for i, proc in enumerate(processes):
        if i != myProcessId:
  
            async_send(f"{proc}/share", msg.model_dump())

    return {"status": "ok", "replica": myProcessId}


@app.post("/share")
def share(msg: Event):
    """
    Recebe um evento de outra réplica.
    """
    with lock:
        processMsg(msg)

    return {"status": "received", "replica": myProcessId}

# Funções auxiliares
def async_send(url: str, payload: dict):
    """
    Envia evento para outra réplica de forma assíncrona.
    """

    def worker():
        try:
            if myProcessId == 0:
                time.sleep(0.5)  
            requests.post(url, json=payload, timeout=2)
        except Exception as e:
            print(f"Falha ao enviar para {url}: {e}")

    threading.Thread(target=worker, daemon=True).start()


def processMsg(msg: Event):
    """
    Aplica evento ao estado local sem checagem de dependências.
    """
    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)

    showFeed()

# Apresentação
def showFeed():
    """
    Imprime o feed local e replies órfãs.
    """
    print("\n----------------------------------------")
    print(f"Replica {myProcessId}")
    print("----------------------------------------")

    # Ordena posts pelo timestamp 
    for evtId, post in sorted(posts.items(), key=lambda x: x[1].timestamp or 0):
        print(f"POST {evtId} | ts={post.timestamp} | {post.author}: {post.text}")

        for r in replies.get(evtId, []):
            print(f"  REPLY {r.evtId} | {r.author}: {r.text}")

    orphan_replies = [
        (pid, rs) for pid, rs in replies.items() if pid not in posts
    ]

    if orphan_replies:
        print("\nReplies órfãs:")
        for pid, rs in orphan_replies:
            for r in rs:
                print(f"  parent={pid} | {r.author}: {r.text}")

    print("----------------------------------------")

# Inicialização
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python twitter_eventual.py <processId>")
        sys.exit(1)

    myProcessId = int(sys.argv[1])
    host, port = processes[myProcessId].replace("http://", "").split(":")

    print(f"Iniciando processo {myProcessId} em {host}:{port}")

    uvicorn.run(app, host=host, port=int(port))
