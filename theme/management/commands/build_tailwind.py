import os
import subprocess
import sys
import shutil
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

    def _validate_npm_path(self):
        """Validate and get the full path to npm executable"""
        npm_path = shutil.which('npm')
        if not npm_path:
            raise FileNotFoundError('npm not found. Please install Node.js and npm first.')
        return npm_path

    def _run_command(self, cmd, cwd, description):
        """Safely run a command with proper error handling"""
        try:
            # Validate command is safe (only npm commands with specific arguments)
            if not isinstance(cmd, list) or len(cmd) < 2:
                raise ValueError(f"Invalid command structure: {cmd}")
            
            # Only allow npm commands
            if cmd[0] != 'npm':
                raise ValueError(f"Only npm commands are allowed: {cmd}")
            
            # Validate npm subcommands
            allowed_subcommands = ['install', 'run']
            if cmd[1] not in allowed_subcommands:
                raise ValueError(f"Invalid npm subcommand: {cmd[1]}")
            
            # Validate npm run scripts
            if cmd[1] == 'run' and len(cmd) > 2:
                allowed_scripts = ['build', 'build-prod']
                if cmd[2] not in allowed_scripts:
                    raise ValueError(f"Invalid npm script: {cmd[2]}")
            
            # Use absolute path for npm
            npm_path = self._validate_npm_path()
            safe_cmd = [npm_path] + cmd[1:]
            
            result = subprocess.run(
                safe_cmd, 
                cwd=cwd, 
                check=True,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                shell=False  # Explicitly disable shell
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
        except FileNotFoundError as e:
            self.stdout.write(
                self.style.ERROR(f'{e}')
            )
            return None
        except ValueError as e:
            self.stdout.write(
                self.style.ERROR(f'Security validation failed: {e}')
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
                npm_path = self._validate_npm_path()
                subprocess.run([npm_path, 'run', 'build'], cwd=theme_dir, shell=False)
            except KeyboardInterrupt:
                self.stdout.write('\nBuild process interrupted.')
            except FileNotFoundError as e:
                self.stdout.write(self.style.ERROR(f'{e}'))
        elif options['minify']:
            self.stdout.write('Building minified Tailwind CSS...')
            self._run_command(['npm', 'run', 'build-prod'], theme_dir, 'built minified Tailwind CSS')
        else:
            self.stdout.write('Building Tailwind CSS...')
            self._run_command(['npm', 'run', 'build-prod'], theme_dir, 'built Tailwind CSS')
