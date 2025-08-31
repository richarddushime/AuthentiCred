#!/usr/bin/env python3
"""
Generate API Reference Documentation

This script automatically generates API reference pages from the Django codebase
by analyzing models, views, forms, and other components.
"""

import os
import sys
import inspect
import importlib
from pathlib import Path
from typing import Dict, List, Any
import django
from django.conf import settings

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'AuthentiCred.settings')
django.setup()

def get_app_modules() -> Dict[str, Any]:
    """Get all installed Django app modules."""
    apps = {}
    for app_config in settings.INSTALLED_APPS:
        if isinstance(app_config, str) and not app_config.startswith('django'):
            try:
                app_name = app_config.split('.')[-1]
                module = importlib.import_module(app_config)
                apps[app_name] = module
            except ImportError:
                continue
    return apps

def analyze_models(app_name: str, module: Any) -> Dict[str, Any]:
    """Analyze Django models in an app."""
    models_info = {}
    
    try:
        models_module = importlib.import_module(f"{module.__name__}.models")
        for name, obj in inspect.getmembers(models_module):
            if inspect.isclass(obj) and hasattr(obj, '_meta') and obj._meta.app_label == app_name:
                model_info = {
                    'name': name,
                    'fields': [],
                    'methods': [],
                    'docstring': obj.__doc__ or ''
                }
                
                # Get model fields
                for field in obj._meta.fields:
                    field_info = {
                        'name': field.name,
                        'type': field.__class__.__name__,
                        'null': field.null,
                        'blank': field.blank,
                        'help_text': getattr(field, 'help_text', '')
                    }
                    model_info['fields'].append(field_info)
                
                # Get model methods
                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                    if not method_name.startswith('_'):
                        method_info = {
                            'name': method_name,
                            'docstring': method.__doc__ or '',
                            'signature': str(inspect.signature(method))
                        }
                        model_info['methods'].append(method_info)
                
                models_info[name] = model_info
    except ImportError:
        pass
    
    return models_info

def analyze_management_commands(app_name: str, module: Any) -> Dict[str, Any]:
    """Analyze Django management commands in an app."""
    commands_info = {}
    
    try:
        commands_dir = Path(module.__file__).parent / "management" / "commands"
        if commands_dir.exists():
            for command_file in commands_dir.glob("*.py"):
                if command_file.name != "__init__.py":
                    command_name = command_file.stem
                    try:
                        command_module = importlib.import_module(f"{module.__name__}.management.commands.{command_name}")
                        for name, obj in inspect.getmembers(command_module):
                            if (inspect.isclass(obj) and 
                                issubclass(obj, django.core.management.base.BaseCommand) and
                                obj != django.core.management.base.BaseCommand):
                                
                                command_info = {
                                    'name': command_name,
                                    'help': getattr(obj, 'help', ''),
                                    'docstring': obj.__doc__ or '',
                                    'methods': []
                                }
                                
                                # Get command methods
                                for method_name, method in inspect.getmembers(obj, inspect.isfunction):
                                    if method_name in ['handle', 'add_arguments'] and not method_name.startswith('_'):
                                        method_info = {
                                            'name': method_name,
                                            'docstring': method.__doc__ or '',
                                            'signature': str(inspect.signature(method))
                                        }
                                        command_info['methods'].append(method_info)
                                
                                commands_info[command_name] = command_info
                    except ImportError:
                        continue
    except Exception:
        pass
    
    return commands_info

def analyze_package_json(app_name: str, module: Any) -> Dict[str, Any]:
    """Analyze package.json files for Node.js apps."""
    package_info = {}
    
    try:
        app_dir = Path(module.__file__).parent
        package_file = app_dir / "package.json"
        
        if package_file.exists():
            import json
            with open(package_file, 'r') as f:
                package_data = json.load(f)
            
            package_info = {
                'name': package_data.get('name', ''),
                'version': package_data.get('version', ''),
                'description': package_data.get('description', ''),
                'scripts': package_data.get('scripts', {}),
                'dependencies': package_data.get('dependencies', {}),
                'devDependencies': package_data.get('devDependencies', {})
            }
    except Exception:
        pass
    
    return package_info

def analyze_views(app_name: str, module: Any) -> Dict[str, Any]:
    """Analyze Django views in an app."""
    views_info = {}
    
    try:
        views_module = importlib.import_module(f"{module.__name__}.views")
        for name, obj in inspect.getmembers(views_module):
            if inspect.isclass(obj) and issubclass(obj, django.views.generic.base.View):
                view_info = {
                    'name': name,
                    'base_class': obj.__bases__[0].__name__,
                    'docstring': obj.__doc__ or '',
                    'methods': []
                }
                
                # Get view methods
                for method_name in ['get', 'post', 'put', 'delete', 'patch']:
                    if hasattr(obj, method_name):
                        method = getattr(obj, method_name)
                        method_info = {
                            'name': method_name.upper(),
                            'docstring': method.__doc__ or '',
                            'signature': str(inspect.signature(method))
                        }
                        view_info['methods'].append(method_info)
                
                views_info[name] = view_info
            elif inspect.isfunction(obj) and not name.startswith('_'):
                view_info = {
                    'name': name,
                    'type': 'function',
                    'docstring': obj.__doc__ or '',
                    'signature': str(inspect.signature(obj))
                }
                views_info[name] = view_info
    except ImportError:
        pass
    
    return views_info

def analyze_forms(app_name: str, module: Any) -> Dict[str, Any]:
    """Analyze Django forms in an app."""
    forms_info = {}
    
    try:
        forms_module = importlib.import_module(f"{module.__name__}.forms")
        for name, obj in inspect.getmembers(forms_module):
            if inspect.isclass(obj) and issubclass(obj, django.forms.Form):
                form_info = {
                    'name': name,
                    'base_class': obj.__bases__[0].__name__,
                    'docstring': obj.__doc__ or '',
                    'fields': []
                }
                
                # Get form fields
                if hasattr(obj, 'fields'):
                    for field_name, field in obj.fields.items():
                        field_info = {
                            'name': field_name,
                            'type': field.__class__.__name__,
                            'required': field.required,
                            'help_text': getattr(field, 'help_text', '')
                        }
                        form_info['fields'].append(field_info)
                
                forms_info[name] = form_info
    except ImportError:
        pass
    
    return forms_info

def generate_markdown(app_name: str, app_info: Dict[str, Any]) -> str:
    """Generate markdown documentation for an app."""
    markdown = f"# {app_name.title()} App\n\n"
    
    # Models section
    if app_info.get('models'):
        markdown += "## Models\n\n"
        for model_name, model_info in app_info['models'].items():
            markdown += f"### {model_name}\n\n"
            if model_info['docstring']:
                markdown += f"{model_info['docstring']}\n\n"
            
            markdown += "#### Fields\n\n"
            for field in model_info['fields']:
                markdown += f"- **{field['name']}** (`{field['type']}`)"
                if field['null']:
                    markdown += " - nullable"
                if field['blank']:
                    markdown += " - blank allowed"
                if field['help_text']:
                    markdown += f" - {field['help_text']}"
                markdown += "\n"
            
            if model_info['methods']:
                markdown += "\n#### Methods\n\n"
                for method in model_info['methods']:
                    markdown += f"- **{method['name']}**{method['signature']}\n"
                    if method['docstring']:
                        markdown += f"  {method['docstring']}\n"
            
            markdown += "\n---\n\n"
    
    # Views section
    if app_info.get('views'):
        markdown += "## Views\n\n"
        for view_name, view_info in app_info['views'].items():
            markdown += f"### {view_name}\n\n"
            if view_info['docstring']:
                markdown += f"{view_info['docstring']}\n\n"
            
            if view_info.get('base_class'):
                markdown += f"**Base Class:** {view_info['base_class']}\n\n"
            
            if view_info.get('methods'):
                markdown += "**HTTP Methods:**\n"
                for method in view_info['methods']:
                    markdown += f"- {method['name']}: {method['signature']}\n"
                    if method['docstring']:
                        markdown += f"  {method['docstring']}\n"
            
            markdown += "\n---\n\n"
    
    # Forms section
    if app_info.get('forms'):
        markdown += "## Forms\n\n"
        for form_name, form_info in app_info['forms'].items():
            markdown += f"### {form_name}\n\n"
            if form_info['docstring']:
                markdown += f"{form_info['docstring']}\n\n"
            
            if form_info['fields']:
                markdown += "**Fields:**\n"
                for field in form_info['fields']:
                    markdown += f"- **{field['name']}** (`{field['type']}`)"
                    if field['required']:
                        markdown += " - required"
                    if field['help_text']:
                        markdown += f" - {field['help_text']}"
                    markdown += "\n"
            
            markdown += "\n---\n\n"
    
    # Management Commands section
    if app_info.get('management_commands'):
        markdown += "## Management Commands\n\n"
        for command_name, command_info in app_info['management_commands'].items():
            markdown += f"### {command_name}\n\n"
            if command_info['help']:
                markdown += f"**Help:** {command_info['help']}\n\n"
            if command_info['docstring']:
                markdown += f"{command_info['docstring']}\n\n"
            
            if command_info['methods']:
                markdown += "**Methods:**\n"
                for method in command_info['methods']:
                    markdown += f"- **{method['name']}**{method['signature']}\n"
                    if method['docstring']:
                        markdown += f"  {method['docstring']}\n"
            
            markdown += "\n---\n\n"
    
    # Package.json section (for Node.js apps)
    if app_info.get('package_json') and app_info['package_json']:
        package_data = app_info['package_json']
        markdown += "## Package Configuration\n\n"
        markdown += f"**Name:** {package_data['name']}\n"
        markdown += f"**Version:** {package_data['version']}\n"
        markdown += f"**Description:** {package_data['description']}\n\n"
        
        if package_data['scripts']:
            markdown += "**Scripts:**\n"
            for script_name, script_cmd in package_data['scripts'].items():
                markdown += f"- **{script_name}:** `{script_cmd}`\n"
            markdown += "\n"
        
        if package_data['dependencies']:
            markdown += "**Dependencies:**\n"
            for dep_name, dep_version in package_data['dependencies'].items():
                markdown += f"- **{dep_name}:** {dep_version}\n"
            markdown += "\n"
        
        if package_data['devDependencies']:
            markdown += "**Dev Dependencies:**\n"
            for dep_name, dep_version in package_data['devDependencies'].items():
                markdown += f"- **{dep_name}:** {dep_version}\n"
            markdown += "\n"
        
        markdown += "---\n\n"
    
    return markdown

def main():
    """Main function to generate API reference documentation."""
    print("Generating API Reference Documentation...")
    
    # Get all app modules
    apps = get_app_modules()
    
    # Create docs/api directory
    api_dir = Path(__file__).parent / "api"
    api_dir.mkdir(exist_ok=True)
    
    # Generate documentation for each app
    for app_name, module in apps.items():
        print(f"Analyzing {app_name}...")
        
        app_info = {
            'models': analyze_models(app_name, module),
            'views': analyze_views(app_name, module),
            'forms': analyze_forms(app_name, module),
            'management_commands': analyze_management_commands(app_name, module),
            'package_json': analyze_package_json(app_name, module)
        }
        
        # Generate markdown
        markdown_content = generate_markdown(app_name, app_info)
        
        # Write to file
        output_file = api_dir / f"{app_name}_api.md"
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"Generated {output_file}")
    
    # Generate index file
    index_content = "# API Reference\n\n"
    index_content += "This section contains automatically generated API reference documentation for all Django apps.\n\n"
    
    for app_name in apps.keys():
        index_content += f"- [{app_name.title()} App]({app_name}_api.md)\n"
    
    index_file = api_dir / "index.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"Generated {index_file}")
    print("API Reference generation complete!")

if __name__ == "__main__":
    main()
