import os
import subprocess
import sys
from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):
    help = 'Build Tailwind CSS for AuthentiCred'

    def add_arguments(self, parser):
        parser.add_argument(
            '--watch',
            action='store_true',
            help='Watch for changes and rebuild automatically',
        )
        parser.add_argument(
            '--minify',
            action='store_true',
            help='Minify the output CSS',
        )

    def _run_command(self, cmd, cwd, description):
        """Safely run a command with proper error handling"""
        try:
            # Validate command is safe (only npm commands)
            if not isinstance(cmd, list) or not cmd or cmd[0] not in ['npm']:
                raise ValueError(f"Invalid command: {cmd}")
            
            result = subprocess.run(
                cmd, 
                cwd=cwd, 
                check=True,
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )
            self.stdout.write(
                self.style.SUCCESS(f'Successfully {description}')
            )
            return result
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to {description}: {e}')
            )
            if e.stdout:
                self.stdout.write(f'STDOUT: {e.stdout}')
            if e.stderr:
                self.stdout.write(f'STDERR: {e.stderr}')
            return None
        except subprocess.TimeoutExpired:
            self.stdout.write(
                self.style.ERROR(f'Command timed out while {description}')
            )
            return None
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR('npm not found. Please install Node.js and npm first.')
            )
            return None

    def handle(self, *args, **options):
        theme_dir = os.path.join(settings.BASE_DIR, 'theme')
        
        if not os.path.exists(theme_dir):
            self.stdout.write(
                self.style.ERROR('Theme directory not found. Please ensure the theme app is properly set up.')
            )
            return

        # Check if node_modules exists
        node_modules_path = os.path.join(theme_dir, 'node_modules')
        if not os.path.exists(node_modules_path):
            self.stdout.write('Installing npm dependencies...')
            result = self._run_command(['npm', 'install'], theme_dir, 'installed npm dependencies')
            if not result:
                return

        # Build Tailwind CSS
        if options['watch']:
            self.stdout.write('Starting Tailwind CSS build in watch mode...')
            try:
                subprocess.run(['npm', 'run', 'build'], cwd=theme_dir)
            except KeyboardInterrupt:
                self.stdout.write('\nBuild process interrupted.')
        elif options['minify']:
            self.stdout.write('Building minified Tailwind CSS...')
            self._run_command(['npm', 'run', 'build-prod'], theme_dir, 'built minified Tailwind CSS')
        else:
            self.stdout.write('Building Tailwind CSS...')
            self._run_command(['npm', 'run', 'build-prod'], theme_dir, 'built Tailwind CSS')
