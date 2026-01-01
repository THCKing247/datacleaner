# How to Export/Save Data Cleaner Files

## Option 1: Copy Entire Directory

Simply copy the entire `datacleaner` folder to your desired location:

```bash
# Windows
xcopy /E /I datacleaner "C:\Your\New\Location\datacleaner"

# Or use File Explorer to copy the folder
```

## Option 2: Create a ZIP Archive

**Windows:**
1. Right-click on the `datacleaner` folder
2. Select "Send to" > "Compressed (zipped) folder"
3. Name it `datacleaner.zip`

**Command Line (Windows PowerShell):**
```powershell
Compress-Archive -Path "datacleaner" -DestinationPath "datacleaner.zip"
```

**Linux/Mac:**
```bash
zip -r datacleaner.zip datacleaner/
```

## Option 3: List All Files for Manual Copy

All files you need to copy:

### Frontend
- `datacleaner/index.html`
- `datacleaner/dashboard/index.html`

### Backend API
- `datacleaner/API/app.py`
- `datacleaner/API/requirements.txt`
- `datacleaner/API/quick_setup.py`
- `datacleaner/API/create_admin_user.py`
- `datacleaner/API/install_requirements.bat`
- `datacleaner/API/install_requirements.sh`
- `datacleaner/API/database_schema.sql`
- `datacleaner/API/database_integration.md`
- `datacleaner/API/INSTALL_TROUBLESHOOTING.md`

### Documentation
- `datacleaner/README.md`
- `datacleaner/ACCESS.md`
- `datacleaner/QUICK_START.md`
- `datacleaner/FILE_STRUCTURE.md`
- `datacleaner/EXPORT_INSTRUCTIONS.md` (this file)

## Important Notes

1. **Database File**: The `datacleaner.db` file will be created automatically when you run the API for the first time. You don't need to copy it initially.

2. **Dependencies**: The Data Clean Engine requires access to:
   - `Automation Service Python/1_data_clean_engine.py`
   - Make sure this file is accessible from your new location, or update the path in `app.py`

3. **Configuration**: After copying, you may need to:
   - Update paths in `app.py` if moving to a different directory structure
   - Install dependencies: `pip install -r API/requirements.txt`
   - Run `python API/quick_setup.py` to create admin user
   - Start server: `python API/app.py`

## Quick Export Script

Save this as `export_datacleaner.ps1` in your project root:

```powershell
# Export Data Cleaner to separate location
$source = "datacleaner"
$destination = "C:\Your\New\Location\datacleaner"

# Create destination if it doesn't exist
New-Item -ItemType Directory -Force -Path $destination

# Copy all files
Copy-Item -Path $source -Destination $destination -Recurse -Force

# Create ZIP archive
Compress-Archive -Path $source -DestinationPath "datacleaner_export.zip" -Force

Write-Host "Data Cleaner exported to: $destination"
Write-Host "ZIP archive created: datacleaner_export.zip"
```

