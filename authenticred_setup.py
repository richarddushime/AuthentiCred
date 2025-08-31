#!/usr/bin/env python3
"""
AuthentiCred Complete Setup and Startup Script
===============================================

This script automates the entire AuthentiCred setup process:
1. Starts Ganache blockchain (or detects if already running)
2. Deploys smart contracts
3. Updates environment variables
4. Starts all required servers (Django, Celery, Redis)

Usage:
    python start_authenticred.py [options]

Options:
    --skip-ganache    Skip starting Ganache (if already running)
    --skip-deploy     Skip contract deployment
    --skip-servers    Skip starting servers
    --ganache-port    Ganache port (default: 7545)
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
    def __init__(self, ganache_port: int = 7545, django_port: int = 8000):
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
        
        # Core dependencies (required)
        required_commands = [
            ('python', 'Python'),
            ('pip', 'pip'),
        ]
        
        # Optional dependencies (with fallbacks)
        optional_commands = [
            ('node', 'Node.js'),
            ('npm', 'npm'),
            ('truffle', 'Truffle'),
        ]
        
        missing_required = []
        missing_optional = []
        
        # Check required dependencies
        for cmd, name in required_commands:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                print(f"  ✅ {name}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  ❌ {name} not found")
                missing_required.append(name)
        
        # Check optional dependencies
        for cmd, name in optional_commands:
            try:
                subprocess.run([cmd, '--version'], capture_output=True, check=True)
                print(f"  ✅ {name}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"  ⚠️  {name} not found (optional)")
                missing_optional.append(name)
        
        # Check Ganache (CLI or GUI)
        ganache_status = self.check_ganache_status()
        if ganache_status == "running":
            print("  ✅ Ganache is running")
        elif ganache_status == "cli_available":
            print("  ✅ Ganache CLI available")
        elif ganache_status == "gui_available":
            print("  ✅ Ganache GUI available")
        else:
            print("  ⚠️  Ganache not found (you can start it manually)")
        
        # Check Redis
        redis_status = self.check_redis_status()
        if redis_status:
            print("  ✅ Redis is running")
        else:
            print("  ⚠️  Redis not running (will try to start)")
        
        if missing_required:
            print(f"\n❌ Missing required dependencies: {', '.join(missing_required)}")
            print("Please install the missing dependencies and try again.")
            return False
            
        if missing_optional:
            print(f"\n⚠️  Missing optional dependencies: {', '.join(missing_optional)}")
            print("Some features may not work without these dependencies.")
        
        return True
    
    def install_truffle_if_needed(self) -> bool:
        """Install Truffle if not available"""
        try:
            # Check if Truffle is already installed
            subprocess.run(['truffle', 'version'], capture_output=True, check=True)
            print("  ✅ Truffle is already installed")
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("  ⚠️  Truffle not found, attempting to install...")
            
            try:
                # Check if npm is available
                subprocess.run(['npm', '--version'], capture_output=True, check=True)
                
                print("  📦 Installing Truffle globally...")
                result = subprocess.run(
                    ['npm', 'install', '-g', 'truffle'],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("  ✅ Truffle installed successfully")
                    return True
                else:
                    print(f"  ❌ Failed to install Truffle: {result.stderr}")
                    print("  📋 Please install Truffle manually:")
                    print("    npm install -g truffle")
                    return False
                    
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("  ❌ npm not found, cannot install Truffle")
                print("  📋 Please install Node.js and npm first:")
                print("    - macOS: brew install node")
                print("    - Ubuntu: sudo apt-get install nodejs npm")
                print("    - Windows: Download from https://nodejs.org/")
                return False
    
    def check_ganache_status(self) -> str:
        """Check Ganache status and availability"""
        # First check if Ganache is already running
        if self.is_ganache_running():
            return "running"
        
        # Check for Ganache CLI
        try:
            subprocess.run(['ganache', '--version'], capture_output=True, check=True)
            return "cli_available"
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Check for Ganache GUI (common installation paths)
        ganache_gui_paths = [
            "/Applications/Ganache.app/Contents/MacOS/Ganache",  # macOS
            "C:\\Program Files\\Ganache\\Ganache.exe",  # Windows
            "/usr/bin/ganache",  # Linux
            "/usr/local/bin/ganache",  # Linux
        ]
        
        for path in ganache_gui_paths:
            if os.path.exists(path):
                return "gui_available"
        
        return "not_found"
    
    def check_redis_status(self) -> bool:
        """Check if Redis is running"""
        try:
            subprocess.run(['redis-cli', 'ping'], capture_output=True, check=True, timeout=2)
            return True
        except:
            return False
    
    def start_ganache(self) -> bool:
        """Start Ganache blockchain"""
        print(f"\n🔗 Starting Ganache on port {self.ganache_port}...")
        
        # Check if Ganache is already running
        if self.is_ganache_running():
            print("  ✅ Ganache is already running")
            return True
        
        # Try to start Ganache CLI
        ganache_status = self.check_ganache_status()
        
        if ganache_status == "cli_available":
            try:
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
                        print("  ✅ Ganache CLI started successfully")
                        return True
                    time.sleep(1)
                
                print("  ❌ Failed to start Ganache CLI")
                return False
                
            except Exception as e:
                print(f"  ❌ Error starting Ganache CLI: {e}")
                return False
        
        elif ganache_status == "gui_available":
            print("  ℹ️  Ganache GUI detected but not running")
            print("  📋 Please start Ganache GUI manually and ensure it's running on port", self.ganache_port)
            print("  🔗 Then press Enter to continue...")
            input()
            
            # Check if Ganache is now running
            if self.is_ganache_running():
                print("  ✅ Ganache GUI is now running")
                return True
            else:
                print("  ❌ Ganache is still not running")
                return False
        
        else:
            print("  ❌ Ganache not found")
            print("  📋 Please install Ganache CLI or GUI:")
            print("    - CLI: npm install -g ganache")
            print("    - GUI: Download from https://trufflesuite.com/ganache/")
            print("  🔗 Then start Ganache and press Enter to continue...")
            input()
            
            if self.is_ganache_running():
                print("  ✅ Ganache is now running")
                return True
            else:
                print("  ❌ Ganache is still not running")
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
        
        # Check and install Truffle if needed
        if not self.install_truffle_if_needed():
            print("  ❌ Cannot deploy contracts without Truffle")
            return False
        
        # Compile contracts with Truffle first
        if not self.compile_contracts():
            print("  ❌ Contract compilation failed")
            return False
        
        # Deploy contracts with Truffle
        if not self.migrate_contracts():
            print("  ❌ Contract migration failed")
            return False
        
        try:
            # Run the deployment command
            cmd = [
                sys.executable, 'manage.py', 'deploy_contracts',
                '--ganache-port', str(self.ganache_port)
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
                if ':' in line and '0x' in line:
                    parts = line.split(':')
                    if len(parts) == 2:
                        contract_name = parts[0].strip()
                        address = parts[1].strip()
                        if address.startswith('0x'):
                            self.contract_addresses[contract_name] = address
            
            print("  ✅ Contracts deployed successfully")
            for name, addr in self.contract_addresses.items():
                print(f"    {name}: {addr}")
            
            return True
            
        except Exception as e:
            print(f"  ❌ Error deploying contracts: {e}")
            return False
    
    def compile_contracts(self) -> bool:
        """Compile smart contracts using Truffle"""
        print("  🔨 Compiling contracts with Truffle...")
        
        try:
            truffle_dir = self.base_dir / 'blockchain' / 'Authenticred_contracts'
            
            if not truffle_dir.exists():
                print(f"  ❌ Truffle project not found at: {truffle_dir}")
                return False
            
            # Run truffle compile
            result = subprocess.run(
                ['truffle', 'compile'],
                cwd=truffle_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Contracts compiled successfully")
                return True
            else:
                print(f"  ❌ Contract compilation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error compiling contracts: {e}")
            return False
    
    def migrate_contracts(self) -> bool:
        """Deploy contracts to blockchain using Truffle migrate"""
        print("  🚀 Deploying contracts with Truffle migrate...")
        
        try:
            truffle_dir = self.base_dir / 'blockchain' / 'Authenticred_contracts'
            
            if not truffle_dir.exists():
                print(f"  ❌ Truffle project not found at: {truffle_dir}")
                return False
            
            # Check if Ganache is running before migration
            if not self.is_ganache_running():
                print("  ❌ Ganache is not running. Please start Ganache first.")
                return False
            
            # Run truffle migrate
            result = subprocess.run(
                ['truffle', 'migrate', '--reset', '--network', 'development'],
                cwd=truffle_dir,
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                print("  ✅ Contracts deployed successfully with Truffle")
                print("  📋 Migration output:")
                print(result.stdout)
                return True
            else:
                print(f"  ❌ Contract migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"  ❌ Error migrating contracts: {e}")
            return False
    
    def start_redis(self) -> bool:
        """Start Redis server"""
        print("\n🔴 Starting Redis...")
        
        try:
            # Check if Redis is already running
            if self.check_redis_status():
                print("  ✅ Redis is already running")
                return True
            
            # Try to start Redis server directly
            try:
                # Try daemonized start first
                cmd = ['redis-server', '--daemonize', 'yes']
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0:
                    # Wait for Redis to start
                    for i in range(10):  # Wait up to 10 seconds
                        if self.check_redis_status():
                            print("  ✅ Redis started successfully (daemonized)")
                            return True
                        time.sleep(1)
                
                # If daemonized start failed, try regular start
                cmd = ['redis-server']
                self.redis_process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )
                
                # Wait for Redis to start
                for i in range(10):  # Wait up to 10 seconds
                    if self.check_redis_status():
                        print("  ✅ Redis started successfully")
                        return True
                    time.sleep(1)
                
                print("  ❌ Failed to start Redis server")
                return False
                
            except FileNotFoundError:
                print("  ℹ️  Redis server not found in PATH")
                print("  📋 Please install Redis:")
                print("    - macOS: brew install redis")
                print("    - Ubuntu: sudo apt-get install redis-server")
                print("    - Windows: Download from https://redis.io/download")
                print("  🔗 Then start Redis and press Enter to continue...")
                input()
                
                if self.check_redis_status():
                    print("  ✅ Redis is now running")
                    return True
                else:
                    print("  ❌ Redis is still not running")
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
        
        # Ensure Redis is running before starting Celery
        if not self.check_redis_status():
            print("  ❌ Redis is not running. Cannot start Celery worker.")
            return False
        
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
            time.sleep(5)
            
            if self.celery_worker_process.poll() is None:
                print("  ✅ Celery worker started successfully")
                return True
            else:
                # Get error output if worker failed
                stdout, stderr = self.celery_worker_process.communicate()
                print(f"  ❌ Failed to start Celery worker")
                if stderr:
                    print(f"  Error: {stderr}")
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
    
    def restore_blockchain_state(self) -> bool:
        """Restore blockchain state after Ganache restart"""
        print("\n🔧 Restoring blockchain state...")
        
        try:
            # Wait a moment for Django to be fully ready
            time.sleep(3)
            
            # Run the blockchain state restoration command
            cmd = [
                sys.executable, 'manage.py', 'quick_fix_blockchain'
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.base_dir,
                timeout=60  # 60 second timeout
            )
            
            if result.returncode == 0:
                print("  ✅ Blockchain state restored successfully")
                return True
            else:
                print(f"  ⚠️  Blockchain state restoration had issues: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("  ⚠️  Blockchain state restoration timed out")
            return False
        except Exception as e:
            print(f"  ⚠️  Error restoring blockchain state: {e}")
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
        print("  🔧 Blockchain State: Restored")
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
            ('Ganache', self.ganache_process),
            ('Redis', self.redis_process)
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
        
        print("  ✅ All services stopped")

def main():
    parser = argparse.ArgumentParser(description='AuthentiCred Complete Setup and Startup')
    parser.add_argument('--skip-ganache', action='store_true', help='Skip starting Ganache')
    parser.add_argument('--skip-deploy', action='store_true', help='Skip contract deployment')
    parser.add_argument('--skip-servers', action='store_true', help='Skip starting servers')
    parser.add_argument('--ganache-port', type=int, default=7545, help='Ganache port (default: 7545)')
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
            
            # Restore blockchain state
            setup.restore_blockchain_state()
        
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

