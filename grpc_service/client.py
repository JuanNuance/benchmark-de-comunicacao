import sys, time
import grpc
import faker_service_pb2
import faker_service_pb2_grpc


def run(port, duration):
    channel = grpc.insecure_channel(f"localhost:{port}")
    stub = faker_service_pb2_grpc.FakerStreamStub(channel)
    received = total_bytes = 0
    t0 = time.time()

    print(f"CLIENT_START:{port}:{duration}")
    try:
        for packet in stub.StreamData(faker_service_pb2.StreamRequest(duration_seconds=duration)):
            received += 1
            total_bytes += len(packet.SerializeToString())
    except grpc.RpcError:
        pass

    elapsed = time.time() - t0
    pps = received / elapsed if elapsed > 0 else 0
    mbps = (total_bytes / elapsed) / 1e6 if elapsed > 0 else 0

    try:
        metrics = stub.GetMetrics(faker_service_pb2.MetricsRequest())
    except Exception:
        metrics = None

    print("=" * 60)
    print(f"[CLIENT] Port: {port} | Duration: {duration:.1f}s")
    print("-" * 60)
    print(f"  Packets received     : {received}")
    print(f"  Bytes received       : {total_bytes}")
    print(f"  Elapsed local        : {elapsed:.3f}s")
    print(f"  Local PPS            : {pps:.1f} packets/s")
    print(f"  Local MB/s           : {mbps:.3f} MB/s")
    if metrics:
        print("-" * 60)
        print(f"  [SERVER METRICS]")
        print(f"  Total packets sent   : {metrics.total_packets_sent}")
        print(f"  Avg latency (us)     : {metrics.avg_latency_us:.1f}")
        print(f"  Max latency (us)     : {metrics.max_latency_us:.1f}")
        print(f"  Min latency (us)     : {metrics.min_latency_us:.1f}")
        print(f"  Total bytes sent     : {metrics.bytes_sent}")
        print(f"  Server PPS           : {metrics.packets_per_second:.1f}")
        print(f"  Server MB/s          : {metrics.mb_per_second:.3f}")
        print(f"  TCP time complexity  : {metrics.tcp_time_complexity:.3f}")
        print(f"  Complexity class     : {metrics.complexity_class}")
    print("=" * 60); sys.stdout.flush()
    channel.close()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python server.py <PORT> <DURATION>")
        sys.exit(1)
    run(int(sys.argv[1]), int(sys.argv[2]))