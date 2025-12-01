# DDS Project AppImage Builder

This directory contains files for building an AppImage package of the DDS Project.

## What is AppImage?

AppImage is a format for distributing portable applications on Linux without needing superuser permissions to install the application. It allows users to download and run applications without installation.

## Files in this Directory

- **build.sh** - **Single script that does everything**: Installs appimagetool and builds the AppImage
- **uninstall.sh** - Script to uninstall DDS Project and optionally remove system dependencies
- **README.md** - This file

**Note**: `build.sh` is the only script you need! It creates all necessary files (AppRun, desktop entry, icon) automatically during the build process.

## Requirements

- **Bash shell**
- **Internet connection** (for downloading appimagetool if needed)
- **Optional**: FUSE library (for direct AppImage execution, otherwise appimagetool will be extracted)

## Building the AppImage

**It's simple - just run one script!**

```bash
cd image
bash build.sh
```

That's it! The `build.sh` script will:
1. ✅ Check if appimagetool is installed, install it if needed
2. ✅ Create AppRun script automatically
3. ✅ Create desktop entry automatically
4. ✅ Create icon automatically (if Python PIL is available)
5. ✅ Copy all project files into AppImage
6. ✅ Build the AppImage package

**Output**: The AppImage will be created in the `image/` directory:
- `image/DDS-Project-v1.0.0_alpha-x86_64.AppImage`

**No other files needed** - `build.sh` creates everything automatically!

## How It Works

The AppImage is **completely self-contained** and contains:
- **All project files** (IDL, scripts, scenarios, monitoring, demo, init, etc.)
- **All setup scripts** (`init/sh/install_system_dependencies.sh`, `init/sh/post_install_build.sh`, `init/sh/project_setup.sh`, etc.)
- **AppRun** script that:
  1. Extracts project files to `~/.dds-project-runtime` on first run
  2. Uses the extracted files as the project root
  3. **Checks system dependencies** (cmake, gcc, python3, java, Fast-DDS, etc.)
  4. **Installs missing dependencies automatically** (via `init/sh/install_system_dependencies.sh`)
  5. **Checks post-install build requirements** (Fast-DDS manual installation, monitoring build)
  6. **Runs post-install build if needed** (via `init/sh/post_install_build.sh`)
  7. Checks if the system is ready (built executables, certificates, etc.)
  8. Runs setup automatically if needed (via `init/sh/project_setup.sh`)
  9. Runs tests and demo automatically (via `init/sh/run_tests_and_demo.sh`)

**Key Features:**
- ✅ **Portable**: Can be placed anywhere (Desktop, Downloads, etc.)
- ✅ **Self-contained**: No external project directory needed
- ✅ **Automatic**: Setup and run happen automatically
- ✅ **Independent**: Works completely standalone

## Usage

### For End Users

#### Option 1: Using AppImage (Easiest - Recommended)

The AppImage is **completely self-contained** and can be placed **anywhere**!

1. **Download** the AppImage file from GitHub releases
2. **Place it anywhere** you want:
   - Desktop
   - Downloads folder
   - Any directory
   - **No need to place it next to project directory** - it's completely independent!

3. **Make executable**:
   ```bash
   chmod +x DDS-Project-v1.0.0_alpha-x86_64.AppImage
   ```

4. **Run**:
   - Double-click the file in your file manager, OR
   - Run from terminal: `./DDS-Project-v1.0.0_alpha-x86_64.AppImage`

5. **First Run**:
   - AppImage extracts project files to `~/.dds-project-runtime`
   - **Automatically checks system dependencies** (cmake, gcc, python3, java, Fast-DDS libraries, fastddsgen, etc.)
   - **Automatically installs missing dependencies** if needed (via `init/sh/install_system_dependencies.sh`)
     - This script installs all required system packages and libraries
     - Automatically calls `init/sh/post_install_build.sh` to complete Fast-DDS manual installation and monitoring build
   - **Checks post-install build requirements** (Fast-DDS manual installation, monitoring application build)
   - **Runs post-install build if needed** (via `init/sh/post_install_build.sh`)
   - Automatically detects if setup is needed
   - Runs setup automatically if needed (via `init/sh/project_setup.sh`)
   - After setup completes, runs tests and demo automatically (via `init/sh/run_tests_and_demo.sh`)
   - Subsequent runs skip setup and run directly

**Working Directory:**
- Project files are extracted to: `~/.dds-project-runtime`
- This directory is created automatically on first run
- All build outputs and certificates are stored here
- You can delete this directory to reset (AppImage will recreate it)

#### Option 2: Using Manual Setup Scripts

If you prefer using scripts directly (without AppImage):
1. Install dependencies: `bash init/sh/install_system_dependencies.sh`
2. Run setup: `bash init/sh/project_setup.sh`
3. Run demo: `bash init/sh/run_tests_and_demo.sh`

### For Developers

1. Build the AppImage using `build_appimage.sh`
2. Test it locally
3. Upload to GitHub releases as a binary asset

## GitHub Release Integration

When creating a GitHub release:

1. **Build the AppImage** (single command):
   ```bash
   cd image
   bash build.sh
   ```

2. **Upload to release**:
   - Go to GitHub releases page
   - Create a new release (e.g., v1.0.0_alpha)
   - Upload `image/DDS-Project-v1.0.0_alpha-x86_64.AppImage` as a binary asset

3. **Users download and run**:
   - Download the AppImage from releases
   - Place it **anywhere** (Desktop, Downloads, etc.) - it's completely self-contained!
   - Make executable: `chmod +x DDS-Project-v1.0.0_alpha-x86_64.AppImage`
   - Run: `./DDS-Project-v1.0.0_alpha-x86_64.AppImage`
   - On first run, setup will run automatically if needed

## Notes

- The AppImage is **completely self-contained** - it contains all project files
- **Can be placed anywhere** - Desktop, Downloads, any directory (no project directory needed)
- On first run, it will automatically:
  1. Extract project files to `~/.dds-project-runtime`
  2. Check system dependencies (cmake, gcc, python3, java, Fast-DDS, etc.)
  3. Install missing dependencies if needed (via `init/sh/install_system_dependencies.sh`)
  4. Check post-install build requirements (Fast-DDS manual installation, monitoring build)
  5. Run post-install build if needed (via `init/sh/post_install_build.sh`)
  6. Check if system is ready (built executables, certificates, etc.)
  7. Run setup automatically if needed (via `init/sh/project_setup.sh`)
  8. Run tests and demo (via `init/sh/run_tests_and_demo.sh`)
- The AppImage is portable and doesn't require installation
- No root/sudo permissions needed to **run** (but automatic dependency installation requires sudo for installing system packages)
- Setup will only run once - subsequent runs skip setup and run directly
- Working directory (`~/.dds-project-runtime`) can be deleted to reset - AppImage will recreate it

## Uninstalling

To uninstall the DDS Project:

```bash
cd image
bash uninstall.sh
```

The uninstall script will:
- Detect what's installed (project directory, system packages, environment variables)
- Ask what you want to remove:
  - **Project directory** - Removes the entire DDS project folder
  - **System packages** - Removes Fast-DDS, CMake, Python, Java, etc. (⚠ may affect other projects)
  - **Environment variables** - Removes DDS-related variables from ~/.bashrc
- Create backups before making changes
- Provide clear confirmation prompts

### Quick Uninstall

If you only want to remove the project directory:
```bash
rm -rf /path/to/DDS
```

To remove environment variables manually:
```bash
# Edit ~/.bashrc and remove lines between:
# # DDS Project Environment
# ... (until empty line)
```

## Troubleshooting

### AppImage not finding project files
- The AppImage is self-contained and doesn't need a project directory
- If errors occur, try deleting `~/.dds-project-runtime` and running again

### Permission denied
- Make sure the AppImage is executable: `chmod +x DDS-Project-v1.0.0_alpha-x86_64.AppImage`

### Setup fails
- Ensure you have sudo access (setup may require installing dependencies)
- Check that all required files exist in the project directory

