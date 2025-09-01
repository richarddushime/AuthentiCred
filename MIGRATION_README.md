# AuthentiCred Migration to Heroku

This guide explains how to migrate your complete AuthentiCred application from local development to Heroku, including **ALL database data and media files**.

## What Gets Migrated

✅ **Complete Database Data**
- Users and authentication data
- Credentials and verification records
- Wallet information
- Blockchain transaction data
- All relationships and foreign keys

✅ **All Media Files**
- PDF documents (accreditations, credentials)
- Images and other uploaded files
- Maintains file structure and organization

✅ **Application Configuration**
- Environment variables
- Database settings
- Security configurations
- Production-ready settings

## Prerequisites

Before running the migration, ensure you have:

1. **Heroku CLI** installed and configured
   ```bash
   # macOS
   brew install heroku/brew/heroku
   
   # Or download from: https://devcenter.heroku.com/articles/heroku-cli
   ```

2. **Logged in to Heroku**
   ```bash
   heroku login
   ```

3. **Git** installed and configured
   ```bash
   git --version
   ```

4. **Virtual environment activated**
   ```bash
   source .venv/bin/activate
   ```

## Migration Scripts

We provide two migration scripts - choose the one you prefer:

### Option 1: Python Script (Recommended)

**File:** `migrate_to_heroku.py`

**Usage:**
```bash
# Use default app name (authenticred-app)
python migrate_to_heroku.py

# Specify custom app name
python migrate_to_heroku.py my-custom-app-name
```

**Features:**
- More robust error handling
- Better progress reporting
- Automatic cleanup
- Cross-platform compatibility

### Option 2: Shell Script

**File:** `migrate_to_heroku.sh`

**Usage:**
```bash
# Use default app name (authenticred-app)
./migrate_to_heroku.sh

# Specify custom app name
./migrate_to_heroku.sh my-custom-app-name

# Show help
./migrate_to_heroku.sh --help
```

**Features:**
- Faster execution
- Colored output
- Unix/Linux/macOS optimized

## Migration Process

The migration script will automatically:

1. **🔍 Check Prerequisites**
   - Verify Heroku CLI, Git, and virtual environment
   - Ensure you're logged into Heroku

2. **🗃️ Export Database Data**
   - Create JSON fixtures for each Django app
   - Export with proper relationships (`--natural-foreign --natural-primary`)
   - Generate complete backup

3. **📁 Package Media Files**
   - Compress all media files into a ZIP package
   - Preserve directory structure
   - Show file sizes for large files

4. **🚀 Setup Heroku App**
   - Create new app (if doesn't exist)
   - Add PostgreSQL database
   - Configure environment variables
   - Set production settings

5. **📦 Deploy Application**
   - Commit all changes to Git
   - Push to Heroku
   - Run database migrations

6. **📥 Import Data**
   - Upload fixture files to Heroku
   - Import all database data
   - Maintain data integrity

7. **📁 Upload Media Files**
   - Upload media package to Heroku
   - Extract files to proper locations
   - Clean up temporary files

8. **👤 Create Superuser**
   - Set up admin access
   - Enable application management

## Running the Migration

### Step 1: Prepare Your Environment

```bash
# Activate virtual environment
source .venv/bin/activate

# Ensure all dependencies are installed
pip install -r requirements.txt
```

### Step 2: Run Migration

```bash
# Using Python script (recommended)
python migrate_to_heroku.py

# Or using shell script
./migrate_to_heroku.sh
```

### Step 3: Monitor Progress

The script will show detailed progress for each step:

```
🚀 Starting AuthentiCred to Heroku Migration
==================================================
🔍 Checking prerequisites...
✅ Heroku CLI: heroku/8.0.0 darwin-x64 node-v20.11.1
✅ Logged in as: your-email@example.com
✅ Git: git version 2.39.2
✅ Virtual environment activated

🗃️ Exporting database data...
📦 Exporting users data...
✅ users: 0.15 MB
📦 Exporting credentials data...
✅ credentials: 0.23 MB
📦 Exporting wallets data...
✅ wallets: 0.08 MB
📦 Exporting blockchain data...
✅ blockchain: 0.12 MB
📦 Exporting complete database backup...
✅ Complete backup: 0.58 MB

📁 Packaging media files...
📦 Added: accreditations/Receivutto.pdf (0.04 MB)
📦 Added: credentials/CV_-_Richard_Dushime.pdf (0.35 MB)
✅ Media package created: 0.39 MB

🚀 Setting up Heroku app: authenticred-app
🏗️ Creating new Heroku app: authenticred-app
🗄️ Adding PostgreSQL add-on...
⏳ Waiting for PostgreSQL to be ready...
🔗 Getting DATABASE_URL...
✅ DATABASE_URL configured: postgres://username:password@host:port/database...
⚙️ Setting environment variables...
✅ Environment variables configured

🚀 Deploying to Heroku...
✅ Deployment successful!

🗃️ Running database migrations...
✅ Migrations completed!

📥 Importing data to Heroku...
📤 Uploading users_data.json...
📤 Uploading credentials_data.json...
📤 Uploading wallets_data.json...
📤 Uploading blockchain_data.json...
📤 Uploading complete_backup.json...
📥 Loading data...
✅ Data import completed!

📁 Uploading media files...
📤 Uploading media package...
📦 Extracting media files...
✅ Media files uploaded successfully!

👤 Creating superuser...
✅ Superuser created!

🎉 Migration completed successfully!
🌐 Your app is available at: https://authenticred-app.herokuapp.com

📊 Useful commands:
   View logs: heroku logs --tail --app authenticred-app
   Access database: heroku pg:psql --app authenticred-app
   Run shell: heroku run python manage.py shell --app authenticred-app
```

## Post-Migration

After successful migration:

### 1. Verify Your Application

Visit your Heroku app URL to ensure everything is working:
```
https://your-app-name.herokuapp.com
```

### 2. Check Data Integrity

```bash
# View application logs
heroku logs --tail --app your-app-name

# Access database
heroku pg:psql --app your-app-name

# Run Django shell
heroku run python manage.py shell --app your-app-name
```

### 3. Test Functionality

- Log in with existing user accounts
- Verify media files are accessible
- Check credential verification processes
- Test blockchain interactions

## Troubleshooting

### Common Issues

**1. Heroku CLI Not Found**
```bash
# Install Heroku CLI
brew install heroku/brew/heroku
# or download from Heroku website
```

**2. Not Logged In**
```bash
heroku login
```

**3. Virtual Environment Not Activated**
```bash
source .venv/bin/activate
```

**4. Database Export Errors**
```bash
# Check Django models
python manage.py check

# Verify database connection
python manage.py dbshell
```

**5. Media File Upload Issues**
```bash
# Check file permissions
ls -la media/

# Verify zip command availability
which zip
```

### Manual Recovery

If the automated migration fails, you can run steps manually:

```bash
# 1. Export data manually
python manage.py dumpdata --indent=2 > fixtures/manual_backup.json

# 2. Setup Heroku manually
heroku create your-app-name
heroku addons:create heroku-postgresql:mini --app your-app-name

# 3. Deploy manually
git push heroku main

# 4. Import data manually
heroku run python manage.py loaddata fixtures/manual_backup.json --app your-app-name
```

## Security Considerations

- **SECRET_KEY**: Automatically generated and set on Heroku
- **Database**: Uses Heroku's managed PostgreSQL with SSL
- **Media Files**: Stored securely on Heroku's filesystem
- **Environment Variables**: All sensitive data stored in Heroku config

## Cost Considerations

- **PostgreSQL Essential 0**: ~$5/month (includes 1GB storage)
- **Dyno**: Free tier available (with limitations)
- **Storage**: Media files count against your dyno storage limit

## Support

If you encounter issues during migration:

1. Check the troubleshooting section above
2. Review Heroku logs: `heroku logs --tail --app your-app-name`
3. Verify your local Django setup works correctly
4. Ensure all prerequisites are met

## Next Steps

After successful migration:

1. **Configure Custom Domain** (if needed)
2. **Set up Monitoring** with Heroku add-ons
3. **Configure CI/CD** for future deployments
4. **Set up Backup Strategies** for production data
5. **Monitor Performance** and optimize as needed

---

**Note**: This migration script is designed to be safe and non-destructive. It creates a complete backup of your local data before proceeding. Your local development environment remains unchanged.
