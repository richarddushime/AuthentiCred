#!/usr/bin/env python3
"""
AuthentiCred Complete Setup and Startup Script
===============================================

This script automates the entire AuthentiCred setup process:
1. Starts Ganache blockchain
2. Deploys smart contracts
3. Updates environment variables
4. Starts all required servers (Django, Celery, Redis)

Usage:
    python start_authenticred.py [options]

Options:
    --skip-ganache    Skip starting Ganache (if already running)
    --skip-deploy     Skip contract deployment
    --skip-servers    Skip starting servers
    --ganache-port    Ganache port (default: 8545)
    --django-port     Django port (default: 8000)
    --help           Show this help message
"""

import os
import sys
import time
import json
import subprocess
import argparse
import signal
import requests
from pathlib import Path
from typing import Dict, List, Optional

class AuthentiCredSetup:
    def __init__(self, ganache_port: int = 8545, django_port: int = 8000):
        self.ganache_port = ganache_port
        self.django_port = django_port
        self.base_dir = Path(__file__).parent
        self.ganache_process = None
        self.django_process = None
        self.celery_worker_process = None
        self.celery_beat_process = None
        self.redis_process = None
        
        # Contract addresses (will be updated after deployment)
        self.contract_addresses = {}
        
    def print_banner(self):
        """Print startup banner"""
        print("=" * 60)
        print("🚀 AuthentiCred Complete Setup & Startup")
        print("=" * 60)
        print(f"📁 Project Directory: {self.base_dir}")
        print(f"🔗 Ganache Port: {self.ganache_port}")
        print(f"🌐 Django Port: {self.django_port}")
        print("=" * 60)
        
    def check_dependencies(self) -> bool:
        """Check if required dependencies are installed"""
        print("🔍 Checking dependencies...")
        
        required_commands = [
            ('node', 'Node.js'),
            ('npm', 'npm'),
            ('ganache', 'Ganache CLI'),
            ('python', 'Python'),
            ('pip', 'pip'),
            ('docker', 'Docker'),
        ]
        
        missing = []
        for cmd, name in required_commands:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                print(f"  ✅ {name}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  ❌ {name} not found")
                missing.append(name)
        
        if missing:
            print(f"\n❌ Missing dependencies: {', '.join(missing)}")
            print("Please install the missing dependencies and try again.")
            return False
            
        return True
    
    def start_ganache(self) -> bool:
        """Start Ganache blockchain"""
        print(f"\n🔗 Starting Ganache on port {self.ganache_port}...")
        
        try:
            # Check if Ganache is already running
            if self.is_ganache_running():
                print("  ✅ Ganache is already running")
                return True
            
            # Start Ganache
            cmd = [
                'ganache',
                '--port', str(self.ganache_port),
                '--network-id', '5777',
                '--accounts', '10',
                '--default-balance-ether', '1000',
                '--deterministic',
                '--mnemonic', 'test test test test test test test test test test test test junk'
            ]
            
            self.ganache_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for Ganache to start
            for i in range(30):  # Wait up to 30 seconds
                if self.is_ganache_running():
                    print("  ✅ Ganache started successfully")
                    return True
                time.sleep(1)
            
            print("  ❌ Failed to start Ganache")
            return False
            
        except Exception as e:
            print(f"  ❌ Error starting Ganache: {e}")
            return False
    
    def is_ganache_running(self) -> bool:
        """Check if Ganache is running"""
        try:
            response = requests.post(
                f'http://127.0.0.1:{self.ganache_port}',
                json={
                    'jsonrpc': '2.0',
                    'method': 'eth_blockNumber',
                    'params': [],
                    'id': 1
                },
                timeout=2
            )
            return response.status_code == 200
        except:
            return False
    
    def deploy_contracts(self) -> bool:
        """Deploy smart contracts"""
        print("\n📋 Deploying smart contracts...")
        
        try:
            # Run the deploy contracts command
            cmd = [
                sys.executable, 'manage.py', 'deploy_contracts',
                '--skip-abi-update'  # Skip ABI update since we're doing full deployment
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.base_dir
            )
            
            if result.returncode != 0:
                print(f"  ❌ Contract deployment failed: {result.stderr}")
                return False
            
            # Parse contract addresses from output
            output_lines = result.stdout.split('\n')
            for line in output_lines:
                if 'ADDRESS = ' in line:
                    parts = line.split(' = ')
                    if len(parts) == 2:
                        contract_name = parts[0].strip()
                        address = parts[1].strip().strip("'")
                        self.contract_addresses[contract_name] = address
            
            print("  ✅ Contracts deployed successfully")
            for name, addr in self.contract_addresses.items():
                print(f"    {name}: {addr}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error deploying contracts: {e}")
            return False
    
    def update_env_file(self) -> bool:
        """Update .env file with contract addresses and settings"""
        print("\n⚙️  Updating environment configuration...")
        
        try:
            env_file = self.base_dir / '.env'
            env_example = self.base_dir / 'env.example'
            
            # Read existing .env file or create from example
            if env_file.exists():
                with open(env_file, 'r') as f:
                    env_content = f.read()
            elif env_example.exists():
                with open(env_example, 'r') as f:
                    env_content = f.read()
            else:
                env_content = ""
            
            # Add or update contract addresses
            contract_settings = [
                f"DIDREGISTRY_ADDRESS={self.contract_addresses.get('DIDREGISTRY_ADDRESS', '')}",
                f"TRUSTREGISTRY_ADDRESS={self.contract_addresses.get('TRUSTREGISTRY_ADDRESS', '')}",
                f"CREDENTIALANCHOR_ADDRESS={self.contract_addresses.get('CREDENTIALANCHOR_ADDRESS', '')}",
                f"REVOCATIONREGISTRY_ADDRESS={self.contract_addresses.get('REVOCATIONREGISTRY_ADDRESS', '')}",
                f"BLOCKCHAIN_RPC_URL=http://127.0.0.1:{self.ganache_port}",
                f"GANACHE_CHAIN_ID=5777",
                f"BLOCKCHAIN_NETWORK=ganache",
                f"DEBUG=True",
                f"SECRET_KEY=your-secret-key-here-change-in-production",
                f"FIELD_ENCRYPTION_KEY=your-encryption-key-here-change-in-production"
            ]
            
            # Add contract settings to env content
            for setting in contract_settings:
                key = setting.split('=')[0]
                if key in env_content:
                    # Update existing setting
                    lines = env_content.split('\n')
                    for i, line in enumerate(lines):
                        if line.startswith(key + '='):
                            lines[i] = setting
                            break
                    env_content = '\n'.join(lines)
                else:
                    # Add new setting
                    env_content += f"\n{setting}"
            
            # Write updated .env file
            with open(env_file, 'w') as f:
                f.write(env_content.strip() + '\n')
            
            print("  ✅ Environment file updated")
            return True
            
        except Exception as e:
            print(f"  ❌ Error updating environment file: {e}")
            return False
    
    def start_redis(self) -> bool:
        """Start Redis server"""
        print("\n🔴 Starting Redis...")
        
        try:
            # Check if Redis is already running
            try:
                subprocess.run(['redis-cli', 'ping'], capture_output=True, check=True, timeout=2)
                print("  ✅ Redis is already running")
                return True
            except:
                pass
            
            # Start Redis with Docker
            cmd = [
                'docker', 'run', '-d',
                '--name', 'authenticred-redis',
                '-p', '6379:6379',
                'redis:alpine'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print("  ✅ Redis started successfully")
                return True
            else:
                print(f"  ❌ Failed to start Redis: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error starting Redis: {e}")
            return False
    
    def run_migrations(self) -> bool:
        """Run Django migrations"""
        print("\n🗄️  Running database migrations...")
        
        try:
            cmd = [
                sys.executable, 'manage.py', 'migrate'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.base_dir
            )
            
            if result.returncode == 0:
                print("  ✅ Migrations completed successfully")
                return True
            else:
                print(f"  ❌ Migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error running migrations: {e}")
            return False
    
    def start_celery_worker(self) -> bool:
        """Start Celery worker"""
        print("\n🐛 Starting Celery worker...")
        
        try:
            cmd = [
                sys.executable, '-m', 'celery',
                '-A', 'AuthentiCred', 'worker',
                '--loglevel=info',
                '--pool=solo'
            ]
            
            self.celery_worker_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.base_dir
            )
            
            # Wait a moment for worker to start
            time.sleep(3)
            
            if self.celery_worker_process.poll() is None:
                print("  ✅ Celery worker started successfully")
                return True
            else:
                print("  ❌ Failed to start Celery worker")
                return False
                
        except Exception as e:
            print(f"  ❌ Error starting Celery worker: {e}")
            return False
    
    def start_celery_beat(self) -> bool:
        """Start Celery beat scheduler"""
        print("\n⏰ Starting Celery beat scheduler...")
        
        try:
            cmd = [
                sys.executable, '-m', 'celery',
                '-A', 'AuthentiCred', 'beat',
                '--loglevel=info'
            ]
            
            self.celery_beat_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.base_dir
            )
            
            # Wait a moment for beat to start
            time.sleep(3)
            
            if self.celery_beat_process.poll() is None:
                print("  ✅ Celery beat started successfully")
                return True
            else:
                print("  ❌ Failed to start Celery beat")
                return False
                
        except Exception as e:
            print(f"  ❌ Error starting Celery beat: {e}")
            return False
    
    def start_django_server(self) -> bool:
        """Start Django development server"""
        print(f"\n🌐 Starting Django server on port {self.django_port}...")
        
        try:
            cmd = [
                sys.executable, 'manage.py', 'runserver',
                f'127.0.0.1:{self.django_port}'
            ]
            
            self.django_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=self.base_dir
            )
            
            # Wait for Django to start
            for i in range(30):  # Wait up to 30 seconds
                try:
                    response = requests.get(f'http://127.0.0.1:{self.django_port}', timeout=2)
                    if response.status_code == 200:
                        print("  ✅ Django server started successfully")
                        return True
                except:
                    pass
                time.sleep(1)
            
            print("  ❌ Failed to start Django server")
            return False
            
        except Exception as e:
            print(f"  ❌ Error starting Django server: {e}")
            return False
    
    def print_summary(self):
        """Print summary of what was started"""
        print("\n" + "=" * 60)
        print("🎉 AuthentiCred Setup Complete!")
        print("=" * 60)
        print("📋 Services Status:")
        print(f"  🔗 Ganache: http://127.0.0.1:{self.ganache_port}")
        print(f"  🌐 Django: http://127.0.0.1:{self.django_port}")
        print("  🔴 Redis: localhost:6379")
        print("  🐛 Celery Worker: Running")
        print("  ⏰ Celery Beat: Running")
        print("\n📋 Contract Addresses:")
        for name, addr in self.contract_addresses.items():
            print(f"  {name}: {addr}")
        print("\n🔧 Next Steps:")
        print("  1. Open http://127.0.0.1:8000 in your browser")
        print("  2. Create your first user account")
        print("  3. Start issuing and managing credentials!")
        print("\n⚠️  To stop all services, press Ctrl+C")
        print("=" * 60)
    
    def cleanup(self):
        """Cleanup processes on exit"""
        print("\n🛑 Shutting down services...")
        
        processes = [
            ('Django', self.django_process),
            ('Celery Worker', self.celery_worker_process),
            ('Celery Beat', self.celery_beat_process),
            ('Ganache', self.ganache_process)
        ]
        
        for name, process in processes:
            if process and process.poll() is None:
                try:
                    process.terminate()
                    process.wait(timeout=5)
                    print(f"  ✅ {name} stopped")
                except:
                    try:
                        process.kill()
                        print(f"  ⚠️  {name} force killed")
                    except:
                        pass
        
        # Stop Redis container
        try:
            subprocess.run(['docker', 'stop', 'authenticred-redis'], capture_output=True)
            subprocess.run(['docker', 'rm', 'authenticred-redis'], capture_output=True)
            print("  ✅ Redis stopped")
        except:
            pass
        
        print("  ✅ All services stopped")

def main():
    parser = argparse.ArgumentParser(description='AuthentiCred Complete Setup and Startup')
    parser.add_argument('--skip-ganache', action='store_true', help='Skip starting Ganache')
    parser.add_argument('--skip-deploy', action='store_true', help='Skip contract deployment')
    parser.add_argument('--skip-servers', action='store_true', help='Skip starting servers')
    parser.add_argument('--ganache-port', type=int, default=8545, help='Ganache port (default: 8545)')
    parser.add_argument('--django-port', type=int, default=8000, help='Django port (default: 8000)')
    
    args = parser.parse_args()
    
    # Create setup instance
    setup = AuthentiCredSetup(args.ganache_port, args.django_port)
    
    # Setup signal handlers for cleanup
    def signal_handler(signum, frame):
        setup.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        setup.print_banner()
        
        # Check dependencies
        if not setup.check_dependencies():
            sys.exit(1)
        
        # Start Ganache
        if not args.skip_ganache:
            if not setup.start_ganache():
                sys.exit(1)
        
        # Deploy contracts
        if not args.skip_deploy:
            if not setup.deploy_contracts():
                sys.exit(1)
            
            # Update environment file
            if not setup.update_env_file():
                sys.exit(1)
        
        # Start servers
        if not args.skip_servers:
            # Start Redis
            if not setup.start_redis():
                sys.exit(1)
            
            # Run migrations
            if not setup.run_migrations():
                sys.exit(1)
            
            # Start Celery worker
            if not setup.start_celery_worker():
                sys.exit(1)
            
            # Start Celery beat
            if not setup.start_celery_beat():
                sys.exit(1)
            
            # Start Django server
            if not setup.start_django_server():
                sys.exit(1)
        
        # Print summary
        setup.print_summary()
        
        # Keep running until interrupted
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
            
    except Exception as e:
        print(f"\n❌ Setup failed: {e}")
        setup.cleanup()
        sys.exit(1)
    finally:
        setup.cleanup()

if __name__ == '__main__':
    main()
