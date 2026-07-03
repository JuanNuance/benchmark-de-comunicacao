# Comparação gRPC vs REST — Simulação de Streaming com Faker

Experimentos de benchmark com dados simulados da biblioteca `faker` em 4 terminais locais com duração de 20 segundos cada.

## Estrutura do Projeto

```
grpc-faker-metrics/
├── grpc/
│   ├── __init__.py
│   ├── faker_service.proto    # Contrato gRPC
│   ├── faker_service_pb2.py   # Stubs gerados
│   ├── faker_service_pb2_grpc.py # Stubs gerados
│   ├── server.py              # Servidor gRPC
│   ├── client.py              # Cliente gRPC
│   ├── run.py                 # Script orquestrador Python
│   └── run.sh                 # Script shell orquestrador
├── rest/
│   ├── rest_server.py         # Servidor FastAPI
│   ├── rest_client.py         # Cliente aiohttp
│   └── run.sh                 # Script shell orquestrador
└── RELATORIO.md              # Este relatório
```

## Como Executar

### gRPC

```bash
# Terminal 1-4 (servidores)
cd /home/juanmonte/grpc-faker-metrics
python -m grpc.server 50051

# Terminal 1-4 (clientes)
cd /home/juanmonte/grpc-faker-metrics
python -m grpc.client 50051 20

# Ou tudo de uma vez (bash):
bash grpc/run.sh
```

### REST

```bash
# Terminal 1-4 (servidores)
cd /home/juanmonte/grpc-faker-metrics
python rest/rest_server.py 8001

# Terminal 1-4 (clientes)
cd /home/juanmonte/grpc-faker-metrics
python rest/rest_client.py 8001 20

# Ou tudo de uma vez (bash):
bash rest/run.sh
```

---

## Métricas Agregadas

| Métrica                 | **gRPC**              | **REST (HTTP+JSON)** | Diferença                 |
| ----------------------- | --------------------- | -------------------- | ------------------------- |
| Packets médios/terminal | **20.179**            | **15.153**           | gRPC **+33%**             |
| PPS médio               | **998,6**             | **755,8**            | gRPC **+32%**             |
| MB/s médio              | **0,304**             | **0,324**            | REST +6,6% (JSON é maior) |
| Bytes/packet médio      | **~302 B** (protobuf) | **~428 B** (JSON)    | REST **+42%** maior       |
| Latência média          | **782,5 µs**          | **932,8 µs**         | REST **+19%** mais lento  |
| Latência máxima         | ~3.000 µs             | ~6.200 µs            | REST **+107%**            |
| Classe de complexidade  | O(n log n)            | O(n log n)           | Igual                     |

---

## Resultados por Terminal

### gRPC (Protobuf + HTTP/2)

| Terminal | Porta | Packets | PPS     | MB/s  | Avg Lat. (µs) | Max Lat. (µs) |
| -------- | ----- | ------- | ------- | ----- | ------------- | ------------- |
| 1        | 50051 | 20.584  | 1.028,8 | 0,316 | 769,7         | 2.497,5       |
| 2        | 50052 | 19.860  | 992,6   | 0,304 | 789,5         | 3.736,1       |
| 3        | 50053 | 20.484  | 1.024,0 | 0,314 | 773,0         | 2.663,9       |
| 4        | 50054 | 19.788  | 989,0   | 0,303 | 797,6         | 3.000,5       |

### REST (FastAPI + HTTP/1.1 + NDJSON)

| Terminal | Porta | Packets | PPS   | MB/s  | Avg Lat. (µs) | Max Lat. (µs) |
| -------- | ----- | ------- | ----- | ----- | ------------- | ------------- |
| 1        | 8001  | 15.109  | 753,9 | 0,323 | 941,5         | 5.854,8       |
| 2        | 8002  | 15.158  | 756,4 | 0,325 | 929,0         | 7.261,6       |
| 3        | 8003  | 15.301  | 762,8 | 0,327 | 919,9         | 7.569,5       |
| 4        | 8004  | 15.043  | 750,1 | 0,322 | 940,9         | 4.120,3       |

---

## Detalhamento Técnico

### gRPC (Protobuf + HTTP/2)

```
┌──────────┐   HTTP/2 stream   ┌──────────┐
│  CLIENT  │◄───protobuf─────── │  SERVER  │
│ (sync)   │   DataPacket × N  │ (thread  │
│          │   (bidirecional)  │  pool)   │
└──────────┘   MetricsRequest   └──────────┘
```

- **Schema-first**: `.proto` define contratos tipados. Código gerado via `protoc`.
- **Servidor**: `grpc.server()` com `ThreadPoolExecutor`. Streaming via generator Python (`yield`).
- **Cliente**: `grpc.insecure_channel()` com iterador síncrono sobre `stub.StreamData()`.
- **Serialização**: Protobuf binário. `SerializeToString()`. ~300 bytes/pacote.
- **Transporte**: HTTP/2 com multiplexação de streams. Headers comprimidos (HPACK).

### REST (FastAPI + HTTP/1.1 + NDJSON)

```
┌──────────┐  HTTP/1.1 chunked  ┌──────────┐
│  CLIENT  │◄──NDJSON stream────│  SERVER  │
│ (aiohttp│   {"name":...}      │ (uvicorn │
│  async)  │   line-by-line     │  ASGI)   │
└──────────┘  GET /metrics       └──────────┘
```

- **Code-first**: Rotas FastAPI com type hints. Nenhum schema externo obrigatório.
- **Servidor**: Uvicorn + FastAPI. `StreamingResponse` com generator Python.
- **Cliente**: `aiohttp.ClientSession` com `async for line in resp.content`.
- **Serialização**: `json.dumps()` → UTF-8. ~428 bytes/pacote (chaves textuais).
- **Transporte**: HTTP/1.1 com chunked transfer encoding. Headers textuais.

---

## Resumo e Conclusões

- **gRPC é ~33% mais rápido** em packets/segundo graças à serialização binária eficiente e multiplexação HTTP/2.
- **REST é mais fácil de debugar**, pois as mensagens são texto puro e visíveis em qualquer ferramenta HTTP.
- **Complexidade temporal** foi igual (O(n log n)) em ambos, pois o custo dominante é linear com o número de pacotes.
- **JSON é 42% mais peso** por pacote, o explica o similar MB/s apesar de menos packets.

