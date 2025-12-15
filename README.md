# Universidade Federal do Rio Grande do Norte (UFRN)

**Disciplina:** Sistemas Distribuídos
**Professor:** Eduardo de Lucena Falcão
**Aluno:** Jundi Takeshi

---

## AV2 – Parte 2

### Twitter com Consistência Eventual e Causal

## 📌 Descrição Geral

Este trabalho tem como objetivo implementar duas versões simplificadas de um sistema semelhante ao **Twitter**, executado de forma distribuída, utilizando múltiplos processos que se comunicam via HTTP.

Cada processo representa uma **réplica** do sistema e mantém seu próprio estado local. A comunicação entre as réplicas é feita de forma assíncrona, simulando atrasos de rede.

As duas versões implementadas são:

* **Twitter com Consistência Eventual**
* **Twitter com Consistência Causal**

---

## 🧩 Parte 1 – Consistência Eventual

### Arquivo

`twitter_eventual.py`

### Ideia Principal

Na consistência eventual, não há garantia de ordem na entrega das mensagens. Isso significa que uma réplica pode receber um **reply antes do post original**.

Quando isso acontece, o sistema imprime o reply como um **reply órfão**, pois o post ao qual ele responde ainda não é conhecido localmente.

### Características

* Utiliza **timestamp lógico simples**
* Não há verificação de dependências causais
* Mensagens são entregues assim que chegam
* Replies podem aparecer antes do post

### Funcionamento

* Um processo cria um post ou reply usando o endpoint `/post`
* O evento é aplicado localmente
* O evento é replicado para os demais processos via `/share`
* Cada réplica atualiza seu estado local imediatamente

### Saída Esperada

* Posts ordenados por timestamp
* Replies associados aos posts, quando possível
* Replies órfãos listados separadamente

---

## 🧠 Parte 2 – Consistência Causal

### Arquivo

`twitter_causal.py`

### Ideia Principal

Na consistência causal, um evento **só pode ser entregue** se todas as suas dependências causais já tiverem sido entregues.

Isso garante que:

* Um reply **nunca aparece antes do post** ao qual responde
* A ordem causal entre eventos é respeitada

### Técnicas Utilizadas

* **Relógios Vetoriais** para controle de causalidade
* **Buffer causal** para armazenar mensagens que ainda não podem ser entregues

### Funcionamento

* Cada processo mantém um **vetor lógico**
* Ao criar um post ou reply:

  * Incrementa sua posição no vetor
  * Anexa o vetor ao evento
* Ao receber um evento:

  * Verifica se ele pode ser entregue (`can_deliver`)
  * Caso não possa, o evento fica no buffer causal
* Eventos no buffer são testados continuamente até que possam ser entregues

### Condições para Entrega de um Evento

* O relógio vetorial do remetente deve estar exatamente no próximo valor esperado
* Nenhuma dependência causal pode estar ausente
* Se for um reply, o post pai **precisa já existir** localmente

### Saída Esperada

* Feed sempre consistente causalmente
* Nenhum reply órfão
* Eventos bloqueados aparecem no buffer causal até serem liberados

---

## ▶️ Como Executar

### Pré-requisitos

* Python 3.10+
* Bibliotecas:

  ```bash
  pip install fastapi uvicorn requests
  ```

### Execução – Consistência Eventual

Abra **três terminais** e execute:

```bash
python twitter_eventual.py 0
python twitter_eventual.py 1
python twitter_eventual.py 2
```

Cada processo escuta em uma porta diferente.

### Execução – Consistência Causal

Abra **três terminais** e execute:

```bash
python twitter_causal.py 0
python twitter_causal.py 1
python twitter_causal.py 2
```

---

## 📬 Enviando Posts e Replies

Exemplo de post:

```bash
curl -X POST http://127.0.0.1:9000/post \
-H "Content-Type: application/json" \
-d '{
  "evtId": "p1",
  "author": "Jundi",
  "text": "Olá mundo!"
}'
```

Exemplo de reply:

```bash
curl -X POST http://127.0.0.1:9001/post \
-H "Content-Type: application/json" \
-d '{
  "evtId": "r1",
  "parentEvtId": "p1",
  "author": "Maria",
  "text": "Oi Jundi!"
}'
```

---

## 📚 Conclusão

Este trabalho demonstra claramente as diferenças entre **consistência eventual** e **consistência causal**:

* A consistência eventual é mais simples, porém permite estados temporariamente inconsistentes
* A consistência causal exige mais controle (relógios vetoriais e buffer), mas garante uma ordem lógica correta dos eventos

---

**Disciplina: Sistemas Distribuídos – UFRN**
