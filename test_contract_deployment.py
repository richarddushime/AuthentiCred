#!/usr/bin/env python3
"""
AuthentiCred Contract Deployment Test Script
============================================

This script tests the complete contract deployment workflow:
1. Copies JSON files from Truffle build
2. Updates .env file with addresses
3. Configures Django settings

Usage:
    python test_contract_deployment.py
    python test_contract_deployment.py --help
"""

import os
import sys
import subprocess
from pathlib import Path

def test_deployment_workflow():
    """Test the complete deployment workflow"""
    print("🧪 Testing AuthentiCred Contract Deployment Workflow")
    print("=" * 60)
    
    # Test 1: JSON copying
    print("\n1️⃣ Testing JSON file copying...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'deploy_contracts_complete',
            '--skip-truffle-deploy', '--skip-env-update'
        ], capture_output=True, text=True, check=True)
        print("✅ JSON copying successful")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ JSON copying failed: {e.stderr}")
        return False
    
    # Test 2: Environment file update
    print("\n2️⃣ Testing environment file update...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'deploy_contracts_complete',
            '--skip-truffle-deploy'
        ], capture_output=True, text=True, check=True)
        print("✅ Environment file update successful")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Environment file update failed: {e.stderr}")
        return False
    
    # Test 3: Django settings reading from .env
    print("\n3️⃣ Testing Django settings from .env...")
    try:
        result = subprocess.run([
            sys.executable, 'manage.py', 'shell', '-c',
            "from django.conf import settings; "
            "print('DID Registry:', settings.DIDREGISTRY_ADDRESS); "
            "print('Trust Registry:', settings.TRUSTREGISTRY_ADDRESS); "
            "print('Operator Address:', settings.BLOCKCHAIN_OPERATOR_ADDRESS)"
        ], capture_output=True, text=True, check=True)
        print("✅ Django settings reading successful")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"❌ Django settings reading failed: {e.stderr}")
        return False
    
    # Test 4: Check .env file
    print("\n4️⃣ Checking .env file...")
    env_file = Path('.env')
    if env_file.exists():
        print("✅ .env file exists")
        with open(env_file, 'r') as f:
            content = f.read()
            if 'DIDREGISTRY_ADDRESS=' in content:
                print("✅ Contract addresses found in .env")
            else:
                print("❌ Contract addresses missing from .env")
                return False
    else:
        print("❌ .env file not found")
        return False
    
    print("\n🎉 All tests passed! Contract deployment workflow is working correctly.")
    return True

def show_usage_instructions():
    """Show usage instructions"""
    print("\n📋 AuthentiCred Usage Instructions:")
    print("=" * 40)
    print("🚀 Quick Start:")
    print("  1. Start Ganache (CLI or GUI) on port 8545")
    print("  2. Run: ./start.sh")
    print("  3. Or manually: python authenticred_setup.py")
    print("\n🔧 Manual Deployment:")
    print("  python manage.py deploy_contracts_complete")
    print("\n📋 Available Options:")
    print("  --skip-truffle-deploy  Skip Truffle deployment")
    print("  --skip-json-copy       Skip copying JSON files")
    print("  --skip-env-update      Skip updating .env file")
    print("  --ganache-port PORT    Specify Ganache port")
    print("\n🧪 Testing:")
    print("  python test_contract_deployment.py")

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        show_usage_instructions()
    else:
        success = test_deployment_workflow()
        if success:
            show_usage_instructions()
        else:
            print("\n❌ Some tests failed. Please check the errors above.")
            sys.exit(1)
