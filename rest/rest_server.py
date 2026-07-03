import sys
import time
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.responses import StreamingResponse
from faker import Faker
import uvicorn


class MetricsTracker:
    def __init__(self):
        self.total_packets = 0
        self.total_bytes = 0
        self.latencies = []
        self.start_time = time.time()

    def record(self, latency_s, serialized_size):
        self.total_packets += 1
        self.total_bytes += serialized_size
        self.latencies.append(latency_s)

    def snapshot(self):
        elapsed = time.time() - self.start_time
        if self.total_packets == 0:
            return {
                "total_packets_sent": 0,
                "avg_latency_us": 0,
                "max_latency_us": 0,
                "min_latency_us": 0,
                "bytes_sent": 0,
                "packets_per_second": 0,
                "mb_per_second": 0,
                "tcp_time_complexity": 0,
                "complexity_class": "O(0)",
            }

        avg = sum(self.latencies) / len(self.latencies) * 1e6
        max_l = max(self.latencies) * 1e6
        min_l = min(self.latencies) * 1e6
        pps = self.total_packets / elapsed
        mbps = (self.total_bytes / elapsed) / 1e6

        n = self.total_packets
        tcp_o = n * avg / 1e6 + n * (n - 1) / 2 * avg / 1e6
        cls = "O(n log n)" if n > 1000 else "O(n)"

        return {
            "total_packets_sent": self.total_packets,
            "avg_latency_us": avg,
            "max_latency_us": max_l,
            "min_latency_us": min_l,
            "bytes_sent": self.total_bytes,
            "packets_per_second": pps,
            "mb_per_second": mbps,
            "tcp_time_complexity": tcp_o,
            "complexity_class": cls,
            "protocol": "REST/HTTP+JSON",
        }


def stream_faker_data(seconds: int):
    fake = Faker()
    deadline = time.time() + seconds
    seq = 0
    total_bytes = 0

    while time.time() < deadline:
        t0 = time.perf_counter()

        record = {
            "name": fake.name(),
            "email": fake.email(),
            "address": fake.address().replace("\n", ", "),
            "phone": fake.phone_number(),
            "company": fake.company(),
            "job": fake.job(),
            "text": fake.text(max_nb_chars=200),
            "packet_number": seq,
        }

        t1 = time.perf_counter()
        elapsed_us = (t1 - t0) * 1e6
        record["latency_us"] = elapsed_us

        raw = json.dumps(record, ensure_ascii=False)
        encoded = raw.encode("utf-8")

        metrics.record(t1 - t0, len(encoded))

        chunk = encoded + b"\n"
        total_bytes += len(chunk)
        yield chunk
        seq += 1


@asynccontextmanager
async def lifespan(app: FastAPI):
    global metrics
    metrics = MetricsTracker()
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/stream")
async def stream(
    duration_seconds: int = Query(20, alias="d"),
    chunk_size: int = Query(65536, alias="c"),
):
    return StreamingResponse(
        stream_faker_data(duration_seconds),
        media_type="application/x-ndjson",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "X-Content-Type-Options": "nosniff",
        },
    )


@app.get("/metrics")
async def get_metrics():
    snap = metrics.snapshot()
    return snap


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
    print(f"REST_SERVER_LIVE:{port}")
    sys.stdout.flush()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="error")