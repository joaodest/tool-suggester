#!/usr/bin/env python3
"""
Suggester Demo Startup Script

Starts both the Python gateway backend and the React frontend dev server.
Handles graceful shutdown and cross-platform compatibility.
"""

import os
import sys
import signal
import subprocess
import time
import socket
from pathlib import Path


def is_port_in_use(port: int) -> bool:
    """Check if a port is already in use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0


def wait_for_port(port: int, timeout: int = 30) -> bool:
    """Wait for a port to become available."""
    start = time.time()
    while time.time() - start < timeout:
        if is_port_in_use(port):
            return True
        time.sleep(0.5)
    return False


def main():
    """Start backend and frontend servers."""
    print("=" * 60)
    print("Suggester Demo - Starting servers...")
    print("=" * 60)

    # Paths
    root_dir = Path(__file__).parent
    demo_dir = root_dir / "examples" / "react-demo"
    gateway_module = "src.suggester.adapters.react_gateway"

    # Check if demo directory exists
    if not demo_dir.exists():
        print(f"  Error: Demo directory not found: {demo_dir}")
        print("   Make sure you're in the correct directory.")
        sys.exit(1)

    # Check ports
    backend_port = 8000
    frontend_port = 5173

    if is_port_in_use(backend_port):
        print(f"  Warning: Port {backend_port} is already in use")
        print("   Backend might already be running, or another service is using the port.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    if is_port_in_use(frontend_port):
        print(f"  Warning: Port {frontend_port} is already in use")
        print("   Frontend might already be running, or another service is using the port.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    processes = []

    try:
        # Start Python backend
        print("\n Starting Python Gateway (port 8000)...")
        print("   Loading tools and initializing engine...")

        backend_process = subprocess.Popen(
            [sys.executable, "-m", gateway_module],
            cwd=root_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        processes.append(("Backend", backend_process))

        # Wait for backend to be ready
        print("   Waiting for backend to start...", end="", flush=True)
        if wait_for_port(backend_port, timeout=10):
            print(" ✓")
            print(f"   Backend ready at http://127.0.0.1:{backend_port}")
        else:
            print(" ✗")
            print("   Warning: Backend might not be ready yet")

        # Start React frontend
        print(f"\n  Starting React Frontend (port {frontend_port})...")
        print("   Building Vite dev server...")

        # Check if node_modules exists
        node_modules = demo_dir / "node_modules"
        if not node_modules.exists():
            print("\n    Installing dependencies (this may take a moment)...")
            npm_install = subprocess.run(
                ["npm", "install"],
                cwd=demo_dir,
                capture_output=True,
                text=True,
                shell=(sys.platform == "win32")
            )
            if npm_install.returncode != 0:
                print(f"   npm install failed: {npm_install.stderr}")
                raise RuntimeError("Failed to install dependencies")

        frontend_process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=demo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            shell=(sys.platform == "win32")
        )
        processes.append(("Frontend", frontend_process))

        # Wait for frontend to be ready
        time.sleep(2)
        print("   Waiting for frontend to start...", end="", flush=True)
        if wait_for_port(frontend_port, timeout=15):
            print(" ✓")
        else:
            print(" ")

        print("\n" + "=" * 60)
        print(" Suggester Demo is ready!")
        print("=" * 60)
        print(f"\n Frontend:  http://localhost:{frontend_port}")
        print(f"   Backend:   http://localhost:{backend_port}")
        print(f"   WebSocket: ws://localhost:{backend_port}/ws/suggest")
        print("\n  Press Ctrl+C to stop all servers")
        print("=" * 60 + "\n")

        # Keep alive and monitor processes
        while True:
            # Check if processes are still running
            for name, proc in processes:
                if proc.poll() is not None:
                    print(f"\n {name} process terminated unexpectedly")
                    raise RuntimeError(f"{name} crashed")

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n Shutting down servers...")

    except Exception as e:
        print(f"\n\n Error: {e}")
        print("   Shutting down...")

    finally:
        # Graceful shutdown
        for name, proc in processes:
            if proc.poll() is None:
                print(f"   Stopping {name}...", end="", flush=True)
                try:
                    if sys.platform == "win32":
                        # Windows: use taskkill
                        subprocess.run(
                            ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    else:
                        # Unix: send SIGTERM
                        proc.terminate()

                    proc.wait(timeout=5)
                    print(" ✓")
                except subprocess.TimeoutExpired:
                    print(" Force killing...", end="", flush=True)
                    proc.kill()
                    print(" ✓")
                except Exception as e:
                    print(f" Error: {e}")

        print("\n Servers stopped. Goodbye!\n")


if __name__ == "__main__":
    main()
