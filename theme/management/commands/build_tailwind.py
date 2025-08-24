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
            try:
                subprocess.run(['npm', 'install'], cwd=theme_dir, check=True)
                self.stdout.write(
                    self.style.SUCCESS('Successfully installed npm dependencies')
                )
            except subprocess.CalledProcessError as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to install npm dependencies: {e}')
                )
                return
            except FileNotFoundError:
                self.stdout.write(
                    self.style.ERROR('npm not found. Please install Node.js and npm first.')
                )
                return

        # Build Tailwind CSS
        try:
            if options['watch']:
                self.stdout.write('Starting Tailwind CSS build in watch mode...')
                subprocess.run(['npm', 'run', 'build'], cwd=theme_dir)
            elif options['minify']:
                self.stdout.write('Building minified Tailwind CSS...')
                subprocess.run(['npm', 'run', 'build-prod'], cwd=theme_dir, check=True)
                self.stdout.write(
                    self.style.SUCCESS('Successfully built minified Tailwind CSS')
                )
            else:
                self.stdout.write('Building Tailwind CSS...')
                subprocess.run(['npm', 'run', 'build-prod'], cwd=theme_dir, check=True)
                self.stdout.write(
                    self.style.SUCCESS('Successfully built Tailwind CSS')
                )
        except subprocess.CalledProcessError as e:
            self.stdout.write(
                self.style.ERROR(f'Failed to build Tailwind CSS: {e}')
            )
        except KeyboardInterrupt:
            self.stdout.write('\nBuild process interrupted.')
