import sys
import time
import json
import asyncio
import aiohttp

async def run(port, duration):
    url = f"http://localhost:{port}/stream?d={duration}"
    metrics_url = f"http://localhost:{port}/metrics"

    received = 0
    total_bytes = 0
    t0 = time.time()
    print(f"REST_CLIENT_START:{port}:{duration}")
    sys.stdout.flush()

    try:
        timeout = aiohttp.ClientTimeout(total=duration + 10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as resp:
                async for line in resp.content:
                    if not line:
                        break
                    received += 1
                    total_bytes += len(line)
    except Exception as e:
        pass

    elapsed = time.time() - t0
    pps = received / elapsed if elapsed > 0 else 0
    mbps = (total_bytes / elapsed) / 1e6 if elapsed > 0 else 0

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(metrics_url) as resp:
                metrics = await resp.json()
    except Exception:
        metrics = None

    print("=" * 60)
    print(f"[REST CLIENT] Port: {port} | Duration: {duration}s")
    print("-" * 60)
    print(f"  Packets received     : {received}")
    print(f"  Bytes received       : {total_bytes}")
    print(f"  Elapsed local        : {elapsed:.3f}s")
    print(f"  Local PPS            : {pps:.1f} packets/s")
    print(f"  Local MB/s           : {mbps:.3f} MB/s")
    if metrics:
        print("-" * 60)
        print(f"  [SERVER METRICS]")
        print(f"  Protocol             : {metrics.get('protocol', 'REST')}")
        print(f"  Total packets sent   : {metrics.get('total_packets_sent', 0)}")
        print(f"  Avg latency (us)     : {metrics.get('avg_latency_us', 0):.1f}")
        print(f"  Max latency (us)     : {metrics.get('max_latency_us', 0):.1f}")
        print(f"  Min latency (us)     : {metrics.get('min_latency_us', 0):.1f}")
        print(f"  Total bytes sent     : {metrics.get('bytes_sent', 0)}")
        print(f"  Server PPS           : {metrics.get('packets_per_second', 0):.1f}")
        print(f"  Server MB/s          : {metrics.get('mb_per_second', 0):.3f}")
        print(f"  TCP time complexity  : {metrics.get('tcp_time_complexity', 0):.3f}")
        print(f"  Complexity class     : {metrics.get('complexity_class', 'N/A')}")
    print("=" * 60)
    sys.stdout.flush()


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python rest_client.py <PORT> <DURATION_SECONDS>")
        sys.exit(1)
    asyncio.run(run(int(sys.argv[1]), int(sys.argv[2])))