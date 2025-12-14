from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List
from collections import defaultdict
import threading
import time
import sys
import requests
import uvicorn

app = FastAPI()

processes = [
    "127.0.0.1:9000",
    "127.0.0.1:9001",
    "127.0.0.1:9002",
]

NUM_PROCESSES = len(processes)
myProcessId = 0

vector_clock = [0] * NUM_PROCESSES

posts = {}                  
replies = defaultdict(list)     

causal_buffer: List["Event"] = []

lock = threading.Lock()

class Event(BaseModel):
    processId: int
    evtId: str
    parentEvtId: Optional[str] = None
    author: str
    text: str
    vector: Optional[List[int]] = None

@app.post("/post")
def post(msg: Event):
    global vector_clock

    with lock:
        vector_clock[myProcessId] += 1
        msg.processId = myProcessId
        msg.vector = vector_clock.copy()

        deliver(msg)

    for i, proc in enumerate(processes):
        if i != myProcessId:
            async_send(f"http://{proc}/share", msg.model_dump())

    return {"status": "ok"}

@app.post("/share")
def share(msg: Event):
    with lock:
        causal_buffer.append(msg)
        try_deliver()
    return {"status": "ok"}

def async_send(url: str, payload: dict):
    def send():
        try:
            if myProcessId == 0:
                time.sleep(2)

            requests.post(url, json=payload, timeout=3)
        except Exception as e:
            print(f"[ERRO ENVIO] {url}: {e}")

    threading.Thread(target=send, daemon=True).start()

def can_deliver(msg: Event) -> bool:
    sender = msg.processId
    V = msg.vector

    if V[sender] != vector_clock[sender] + 1:
        return False

    for i in range(NUM_PROCESSES):
        if i != sender and V[i] > vector_clock[i]:
            return False

    if msg.parentEvtId is not None:
        if msg.parentEvtId not in posts:
            return False

    return True

def try_deliver():
    delivered = True

    while delivered:
        delivered = False
        for msg in causal_buffer[:]:
            if can_deliver(msg):
                causal_buffer.remove(msg)
                deliver(msg)
                delivered = True

def deliver(msg: Event):
    global vector_clock

    for i in range(NUM_PROCESSES):
        vector_clock[i] = max(vector_clock[i], msg.vector[i])

    if msg.parentEvtId is None:
        posts[msg.evtId] = msg
    else:
        replies[msg.parentEvtId].append(msg)

    show_feed()

def show_feed():
    print("\n================ FEED =================")
    print(f"Processo {myProcessId} | VC = {vector_clock}")

    for evtId, post in posts.items():
        print(f"\nPOST {evtId} ({post.author}): {post.text}")
        for r in replies.get(evtId, []):
            print(f"   ↳ REPLY {r.evtId} ({r.author}): {r.text}")

    if causal_buffer:
        print("\n--- BUFFER CAUSAL ---")
        for m in causal_buffer:
            print(f"Evento {m.evtId} aguardando dependências")

    print("======================================\n")

if __name__ == "__main__":
    myProcessId = int(sys.argv[1])

    host, port = processes[myProcessId].split(":")

    uvicorn.run(
        app,
        host=host,
        port=int(port),
        log_level="warning"
    )
