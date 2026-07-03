#!/usr/bin/env python3
import subprocess
import sys
import time

if __name__ == "__main__":
    import os
    os.chdir("/home/juanmonte/grpc-faker-metrics")
    
    # Run server 1
    subprocess.Popen([sys.executable, "-m", "grpc.server", "50051"])
    time.sleep(0.5)
    
    # Run server 2
    subprocess.Popen([sys.executable, "-m", "grpc.server", "50052"])
    time.sleep(0.5)
    
    # Run server 3
    subprocess.Popen([sys.executable, "-m", "grpc.server", "50053"])
    time.sleep(0.5)
    
    # Run server 4
    subprocess.Popen([sys.executable, "-m", "grpc.server", "50054"])
    time.sleep(1)
    
    print("=== 4 gRPC SERVERS ONLINE ===")
    
    # Launch 4 clients
    clients = []
    for port in [50051, 50052, 50053, 50054]:
        proc = subprocess.Popen([sys.executable, "-m", "grpc.client", str(port), "20"])
        clients.append(proc)
    
    print("Waiting for clients to finish...")
    for proc in clients:
        proc.wait()
    
    print("=== DONE ===")