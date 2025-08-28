#!/usr/bin/env python3
"""
Django management command for listing blockchain commands
=======================================================

This command lists all available blockchain management commands.

Usage:
    python manage.py list_commands
"""

from django.core.management.base import BaseCommand
from django.core.management import get_commands

class Command(BaseCommand):
    help = 'List all available blockchain management commands'

    def handle(self, *args, **options):
        self.stdout.write("📋 AuthentiCred Blockchain Management Commands")
        self.stdout.write("=" * 60)
        
        # Define blockchain commands with descriptions
        blockchain_commands = {
            'deploy_contracts': {
                'description': 'Comprehensive contract deployment with JSON copying, Truffle/Web3 deployment, and .env updates',
                'usage': 'python manage.py deploy_contracts [--skip-deploy] [--skip-abi-update] [--skip-env-update] [--use-truffle] [--ganache-port PORT]',
                'options': [
                    '--skip-deploy: Skip contract deployment',
                    '--skip-abi-update: Skip ABI update',
                    '--skip-env-update: Skip updating .env file',
                    '--use-truffle: Use Truffle for deployment (default: Web3)',
                    '--ganache-port: Ganache port (default: 7545)',
                    '--network: Network name (default: development)'
                ]
            },
            'create_missing_wallets': {
                'description': 'Create wallets for users without them',
                'usage': 'python manage.py create_missing_wallets [--force] [--dry-run]',
                'options': [
                    '--force: Force recreation of existing wallets',
                    '--dry-run: Show what would be done without making changes'
                ]
            },
            'check_blockchain_status': {
                'description': 'Check blockchain status and contract connectivity',
                'usage': 'python manage.py check_blockchain_status [--detailed] [--ganache-port PORT]',
                'options': [
                    '--detailed: Show detailed contract information',
                    '--ganache-port: Ganache port (default: 7545)'
                ]
            },
            'reset_blockchain': {
                'description': 'Reset blockchain state and clear contract data',
                'usage': 'python manage.py reset_blockchain [--confirm] [--clear-db] [--ganache-port PORT]',
                'options': [
                    '--confirm: Confirm the reset operation',
                    '--clear-db: Also clear database records',
                    '--ganache-port: Ganache port (default: 7545)'
                ]
            },
            'list_commands': {
                'description': 'List all available blockchain management commands',
                'usage': 'python manage.py list_commands',
                'options': []
            }
        }
        
        # Display commands
        for command_name, info in blockchain_commands.items():
            self.stdout.write(f"\n🔧 {command_name}")
            self.stdout.write(f"   Description: {info['description']}")
            self.stdout.write(f"   Usage: {info['usage']}")
            
            if info['options']:
                self.stdout.write("   Options:")
                for option in info['options']:
                    self.stdout.write(f"     {option}")
        
        # Show workflow examples
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("🔄 Common Workflows")
        self.stdout.write("=" * 60)
        
        workflows = [
            {
                'name': 'Complete Setup',
                'description': 'Deploy contracts and set up everything',
                'commands': [
                    'python manage.py deploy_contracts',
                    'python manage.py create_missing_wallets',
                    'python manage.py check_blockchain_status --detailed'
                ]
            },
            {
                'name': 'Quick Deployment',
                'description': 'Just deploy contracts without updating ABIs',
                'commands': [
                    'python manage.py deploy_contracts --skip-abi-update'
                ]
            },
            {
                'name': 'Status Check',
                'description': 'Check if everything is working',
                'commands': [
                    'python manage.py check_blockchain_status --detailed'
                ]
            },
            {
                'name': 'Reset Everything',
                'description': 'Clear all blockchain data and start fresh',
                'commands': [
                    'python manage.py reset_blockchain --confirm --clear-db',
                    'python manage.py deploy_contracts'
                ]
            }
        ]
        
        for workflow in workflows:
            self.stdout.write(f"\n📋 {workflow['name']}")
            self.stdout.write(f"   {workflow['description']}")
            for command in workflow['commands']:
                self.stdout.write(f"   $ {command}")
        
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("💡 Tips:")
        self.stdout.write("=" * 60)
        self.stdout.write("• Always check blockchain status before deploying")
        self.stdout.write("• Use --dry-run to see what commands will do")
        self.stdout.write("• Use --confirm for destructive operations")
        self.stdout.write("• Check Ganache is running before deploying contracts")
        self.stdout.write("• Use the start script for complete automation: ./start.sh")
