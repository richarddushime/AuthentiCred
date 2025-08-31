# Tailwind CSS Setup Guide for AuthentiCred

This guide explains how Tailwind CSS is set up in the AuthentiCred Django project and how to work with it.

## Current Implementation

The project currently uses **Tailwind CSS CDN** for immediate development and styling. This approach provides:
- Instant styling without build process
- All Tailwind utilities available
- Easy development and iteration
- No build configuration issues


## Local Build Setup (Optional)

For production deployment, you may want to switch to a local build. The project includes a `theme` app with build configuration:

### 1. Install Node.js Dependencies
```bash
cd theme
npm install
```

### 2. Build CSS
```bash
npm run build-prod
```

### 3. Update Template
Replace the CDN link in `users/templates/users/base.html`:
```html
<!-- Replace this: -->
<script src="https://cdn.tailwindcss.com"></script>

<!-- With this: -->
<link rel="stylesheet" href="{% static 'css/styles.css' %}">
```

### 4. Django Settings
Ensure these settings are in `AuthentiCred/settings.py`:
```python
INSTALLED_APPS = [
    # ... other apps
    'tailwind',
    'theme',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

TAILWIND_APP_NAME = 'theme'
NPM_BIN_PATH = "npm"
```

## Resources

- [Tailwind CSS Documentation](https://tailwindcss.com/docs)
- [Bootstrap Icons](https://icons.getbootstrap.com/)
- [Inter Font](https://fonts.google.com/specimen/Inter)
- [Django Static Files](https://docs.djangoproject.com/en/stable/howto/static-files/)
