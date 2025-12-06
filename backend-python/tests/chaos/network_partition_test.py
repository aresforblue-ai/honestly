#!/usr/bin/env python3
"""
Network Partition Simulation using ToxiProxy
Tests Neo4j reconnection behavior in distributed setups.
"""
import os
import sys
import time
import requests
import docker
from typing import Dict, Optional

class NetworkPartitionTester:
    """Test network partition scenarios using ToxiProxy."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.client = docker.from_env()
        self.toxiproxy_container = None
    
    def setup_toxiproxy(self) -> bool:
        """Start ToxiProxy container."""
        try:
            print("Starting ToxiProxy...")
            self.toxiproxy_container = self.client.containers.run(
                'ghcr.io/shopify/toxiproxy:2.5.0',
                detach=True,
                ports={'8474/tcp': 8474},
                name='honestly-toxiproxy'
            )
            time.sleep(3)
            print("  ✓ ToxiProxy started")
            return True
        except Exception as e:
            print(f"  ✗ Failed to start ToxiProxy: {e}")
            return False
    
    def create_proxy(self, name: str, upstream: str, listen_port: int) -> bool:
        """Create a ToxiProxy proxy."""
        try:
            proxy_config = {
                "name": name,
                "listen": f"0.0.0.0:{listen_port}",
                "upstream": upstream,
                "enabled": True
            }
            
            resp = requests.post(
                'http://localhost:8474/proxies',
                json=proxy_config,
                timeout=5
            )
            
            if resp.status_code == 201:
                print(f"  ✓ Created proxy: {name}")
                return True
            else:
                print(f"  ✗ Failed to create proxy: {resp.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error creating proxy: {e}")
            return False
    
    def add_toxic(self, proxy_name: str, toxic_type: str, attributes: Dict) -> bool:
        """Add a toxic (network impairment) to a proxy."""
        try:
            resp = requests.post(
                f'http://localhost:8474/proxies/{proxy_name}/toxics',
                json={
                    "name": toxic_type,
                    "type": toxic_type,
                    "attributes": attributes
                },
                timeout=5
            )
            
            if resp.status_code == 200:
                print(f"  ✓ Added toxic: {toxic_type}")
                return True
            else:
                print(f"  ✗ Failed to add toxic: {resp.text}")
                return False
        except Exception as e:
            print(f"  ✗ Error adding toxic: {e}")
            return False
    
    def remove_toxic(self, proxy_name: str, toxic_name: str) -> bool:
        """Remove a toxic from a proxy."""
        try:
            resp = requests.delete(
                f'http://localhost:8474/proxies/{proxy_name}/toxics/{toxic_name}',
                timeout=5
            )
            return resp.status_code == 204
        except Exception as e:
            print(f"  ✗ Error removing toxic: {e}")
            return False
    
    def test_neo4j_partition(self):
        """Test Neo4j network partition."""
        print("\n" + "=" * 70)
        print("NETWORK PARTITION TEST: Neo4j")
        print("=" * 70)
        
        # Setup ToxiProxy
        if not self.setup_toxiproxy():
            print("  ⚠ Skipping network partition test (ToxiProxy not available)")
            return
        
        try:
            # Get Neo4j container info
            try:
                neo4j_container = self.client.containers.get('honestly-neo4j')
                neo4j_ip = neo4j_container.attrs['NetworkSettings']['IPAddress']
                neo4j_port = 7687
                upstream = f"{neo4j_ip}:{neo4j_port}"
            except docker.errors.NotFound:
                print("  ⚠ Neo4j container not found")
                return
            
            # Create proxy
            proxy_name = "neo4j_proxy"
            listen_port = 27687  # Different port to avoid conflicts
            
            if not self.create_proxy(proxy_name, upstream, listen_port):
                return
            
            # Baseline health check
            print("\n[1] Baseline health check")
            import requests as req
            health_before = req.get(f"{self.base_url}/monitoring/health", timeout=5)
            print(f"  Status: {health_before.status_code}")
            
            # Simulate network partition (timeout)
            print("\n[2] Simulating network partition (timeout)")
            self.add_toxic(proxy_name, "timeout", {
                "timeout": 1000  # 1 second timeout
            })
            
            time.sleep(2)
            
            # Check health during partition
            print("\n[3] Health check during partition")
            try:
                health_during = req.get(f"{self.base_url}/monitoring/health", timeout=5)
                print(f"  Status: {health_during.status_code}")
            except Exception as e:
                print(f"  ⚠ Health check failed (expected): {e}")
            
            # Remove partition
            print("\n[4] Removing network partition")
            self.remove_toxic(proxy_name, "timeout")
            time.sleep(5)
            
            # Verify reconnection
            print("\n[5] Verifying reconnection")
            health_after = req.get(f"{self.base_url}/monitoring/health", timeout=5)
            print(f"  Status: {health_after.status_code}")
            
            if health_after.status_code == 200:
                print("  ✓ System recovered after partition")
            else:
                print("  ✗ System did not recover")
            
        finally:
            # Cleanup
            try:
                if self.toxiproxy_container:
                    self.toxiproxy_container.stop()
                    self.toxiproxy_container.remove()
            except:
                pass
    
    def test_latency_injection(self):
        """Test latency injection."""
        print("\n" + "=" * 70)
        print("LATENCY INJECTION TEST")
        print("=" * 70)
        
        if not self.setup_toxiproxy():
            return
        
        try:
            # Create proxy for Neo4j
            try:
                neo4j_container = self.client.containers.get('honestly-neo4j')
                neo4j_ip = neo4j_container.attrs['NetworkSettings']['IPAddress']
                upstream = f"{neo4j_ip}:7687"
            except docker.errors.NotFound:
                print("  ⚠ Neo4j container not found")
                return
            
            proxy_name = "neo4j_latency"
            if not self.create_proxy(proxy_name, upstream, 27688):
                return
            
            # Add latency
            print("\n[1] Injecting 500ms latency")
            self.add_toxic(proxy_name, "latency", {
                "latency": 500,  # 500ms
                "jitter": 100
            })
            
            time.sleep(2)
            
            # Test response time
            print("\n[2] Testing response time with latency")
            import requests as req
            import time as time_module
            start = time_module.time()
            resp = req.get(f"{self.base_url}/monitoring/health", timeout=10)
            duration = (time_module.time() - start) * 1000  # ms
            
            print(f"  Response time: {duration:.2f}ms")
            
            if duration > 400:  # Should be > 400ms due to latency
                print("  ✓ Latency injection working")
            else:
                print("  ⚠ Latency injection may not be working")
            
            # Remove latency
            print("\n[3] Removing latency")
            self.remove_toxic(proxy_name, "latency")
            
        finally:
            try:
                if self.toxiproxy_container:
                    self.toxiproxy_container.stop()
                    self.toxiproxy_container.remove()
            except:
                pass
    
    def cleanup(self):
        """Cleanup ToxiProxy."""
        try:
            if self.toxiproxy_container:
                self.toxiproxy_container.stop()
                self.toxiproxy_container.remove()
        except:
            pass


if __name__ == '__main__':
    base_url = sys.argv[1] if len(sys.argv) > 1 else 'http://localhost:8000'
    
    try:
        tester = NetworkPartitionTester(base_url)
        tester.test_neo4j_partition()
        tester.test_latency_injection()
        tester.cleanup()
    except ImportError:
        print("ERROR: docker and requests libraries required")
        print("Install: pip install docker requests")
        sys.exit(1)


