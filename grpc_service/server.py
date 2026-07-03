import time, struct, sys, os
gr = __import__('grpc')
import faker_service_pb2
import faker_service_pb2_grpc
from concurrent import futures
from faker import Faker


class MetricsTracker:
    def __init__(self):
        self.total_packets = 0
        self.total_bytes = 0
        self.latencies = []
        self.start_time = time.time()

    def record(self, latency_s, packet_size):
        self.total_packets += 1
        self.total_bytes += packet_size
        self.latencies.append(latency_s)

    def snapshot(self):
        elapsed = time.time() - self.start_time
        if self.total_packets == 0:
            return {
                "total_packets_sent": 0, "avg_latency_us": 0,
                "max_latency_us": 0, "min_latency_us": 0,
                "bytes_sent": 0, "packets_per_second": 0,
                "mb_per_second": 0, "tcp_time_complexity": 0,
                "complexity_class": "O(0)",
            }
        avg = sum(self.latencies) / len(self.latencies) * 1e6
        pps = self.total_packets / elapsed
        mbps = (self.total_bytes / elapsed) / 1e6
        n = self.total_packets
        tcp_o = n * avg / 1e6 + n * (n - 1) / 2 * avg / 1e6
        cls = "O(n log n)" if n > 1000 else "O(n)"
        return {
            "total_packets_sent": self.total_packets, "avg_latency_us": avg,
            "max_latency_us": max(self.latencies) * 1e6,
            "min_latency_us": min(self.latencies) * 1e6,
            "bytes_sent": self.total_bytes,
            "packets_per_second": pps, "mb_per_second": mbps,
            "tcp_time_complexity": tcp_o, "complexity_class": cls,
        }


class FakerStreamServicer(faker_service_pb2_grpc.FakerStreamServicer):
    def __init__(self):
        self.metrics = MetricsTracker()
        self.fake = Faker()

    def StreamData(self, request, context):
        deadline = time.time() + request.duration_seconds
        seq = 0
        while time.time() < deadline and context.is_active():
            t0 = time.perf_counter()
            packet = faker_service_pb2.DataPacket(
                name=self.fake.name(), email=self.fake.email(),
                address=self.fake.address().replace("\n", ", "),
                phone=self.fake.phone_number(), company=self.fake.company(),
                job=self.fake.job(), text=self.fake.text(max_nb_chars=200),
                packet_number=seq,
            )
            raw = packet.SerializeToString()
            t1 = time.perf_counter()
            self.metrics.record(t1 - t0, len(raw))
            packet.latency_us = (t1 - t0) * 1e6
            yield packet
            seq += 1

    def GetMetrics(self, request, context):
        snap = self.metrics.snapshot()
        return faker_service_pb2.MetricsResponse(**snap)


def serve(port):
    svr = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    faker_service_pb2_grpc.add_FakerStreamServicer_to_server(FakerStreamServicer(), svr)
    svr.add_insecure_port(f"[::]:{port}")
    svr.start()
    print(f"SERVER_LIVE:{port}"); sys.stdout.flush()
    svr.wait_for_termination()


if __name__ == "__main__":
    serve(int(sys.argv[1]) if len(sys.argv) > 1 else 50051)