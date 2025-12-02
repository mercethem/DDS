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
- **Optional**: FUSE library (FUSE3 preferred, FUSE2 fallback)
  - For direct AppImage execution: `libfuse3-tools fuse3` (preferred) or `libfuse2`
  - If FUSE is not available, appimagetool will be extracted automatically

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
- `image/DDS-v1.0.0_beta-x86_64.AppImage`

**No other files needed** - `build.sh` creates everything automatically!

## How It Works

The AppImage is **completely self-contained** and contains:
- **All project files** (IDL, scripts, scenarios, monitoring, demo, init, etc.)
- **All setup scripts** (`init/sh/install_system_dependencies.sh`, `init/sh/post_install_build.sh`, `init/sh/project_setup.sh`, etc.)
- **AppRun** script that:
  1. Extracts project files to `~/.dds-project-runtime` on first run
  2. Uses the extracted files as the project root
  3. **PHASE 1: JavaScript/Node.js Setup** (Priority)
     - Checks and installs FUSE2 (required for AppImage execution)
     - Checks and installs Node.js (Ubuntu repos or NodeSource)
     - Installs demo npm packages automatically
  4. **PHASE 2: System Dependencies**
     - Checks system dependencies (cmake, gcc, python3, java, Fast-DDS, etc.)
     - Installs missing dependencies automatically (via `init/sh/install_system_dependencies.sh`)
  5. **PHASE 3: Fast-DDS and Monitoring Build**
     - Runs Fast-DDS manual installation (via `init/sh/fastdds_and_npm_auto_install.sh`)
     - Builds monitoring application (via `monitoring/build_monitoring/build_monitoring.sh`)
  6. **PHASE 4: System Readiness Check**
     - Comprehensive check of all components:
       - Build tools (CMake, GCC/G++, Python3, Java)
       - Node.js and npm packages
       - Fast-DDS installation
       - IDL generated modules and executables
       - Monitoring executable
       - Security certificates
     - If any component is missing, runs setup automatically (via `init/sh/project_setup.sh`)
     - Re-checks system readiness after setup
  7. **PHASE 5: Start Tests and Demo** (Only if system is ready)
     - **Tests and demo will NOT start if any component is missing**
     - Runs tests and demo automatically only when all components are ready (via `init/sh/run_tests_and_demo.sh`)

**Key Features:**
- ✅ **Portable**: Can be placed anywhere (Desktop, Downloads, etc.)
- ✅ **Self-contained**: No external project directory needed
- ✅ **Automatic**: Setup and run happen automatically
- ✅ **Independent**: Works completely standalone

## Usage

### For End Users

#### Option 1: Using AppImage (Easiest - Recommended)

The AppImage is **completely self-contained** and can be placed **anywhere**!

1. **Download** the AppImage file from [GitHub releases](https://github.com/mercethem/DDS/releases)
2. **Place it anywhere** you want:
   - Desktop
   - Downloads folder
   - Any directory
   - **No need to place it next to project directory** - it's completely independent!

3. **Make executable**:
   ```bash
   chmod +x DDS-v1.0.0_beta-x86_64.AppImage
   ```

4. **Run**:
   - Double-click the file in your file manager, OR
   - Run from terminal: `./DDS-v1.0.0_beta-x86_64.AppImage`

5. **First Run**:
   - AppImage extracts project files to `~/.dds-project-runtime`
   - **PHASE 1: JavaScript/Node.js Setup** (Priority)
     - Checks and installs FUSE2 (required for AppImage execution)
     - Checks and installs Node.js (Ubuntu repos or NodeSource)
     - Installs demo npm packages automatically
   - **PHASE 2: System Dependencies**
     - Automatically checks system dependencies (cmake, gcc, python3, java, Fast-DDS libraries, fastddsgen, etc.)
     - Automatically installs missing dependencies (via `init/sh/install_system_dependencies.sh`)
   - **PHASE 3: Fast-DDS and Monitoring Build**
     - Runs Fast-DDS manual installation (via `init/sh/fastdds_and_npm_auto_install.sh`)
     - Builds monitoring application (via `monitoring/build_monitoring/build_monitoring.sh`)
   - **PHASE 4: System Readiness Check**
     - Comprehensive check of all components:
       - Build tools (CMake, GCC/G++, Python3, Java)
       - Node.js and npm packages
       - Fast-DDS installation
       - IDL generated modules and executables
       - Monitoring executable
       - Security certificates
     - If any component is missing, runs setup automatically (via `init/sh/project_setup.sh`)
     - Re-checks system readiness after setup
   - **PHASE 5: Start Tests and Demo** (Only if system is ready)
     - **Tests and demo will NOT start if any component is missing**
     - Runs tests and demo automatically only when all components are ready (via `init/sh/run_tests_and_demo.sh`)
   - Subsequent runs skip setup and run directly if system is ready

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
   - Go to [GitHub releases page](https://github.com/mercethem/DDS/releases)
   - Create a new release (e.g., v1.0.0_beta)
   - Upload `image/DDS-v1.0.0_beta-x86_64.AppImage` as a binary asset

3. **Users download and run**:
   - Download the AppImage from [releases](https://github.com/mercethem/DDS/releases)
   - Place it **anywhere** (Desktop, Downloads, etc.) - it's completely self-contained!
   - Make executable: `chmod +x DDS-v1.0.0_beta-x86_64.AppImage`
   - Run: `./DDS-v1.0.0_beta-x86_64.AppImage`
   - On first run, setup will run automatically if needed

## Notes

- The AppImage is **completely self-contained** - it contains all project files
- **Can be placed anywhere** - Desktop, Downloads, any directory (no project directory needed)
- On first run, it will automatically:
  1. Extract project files to `~/.dds-project-runtime`
  2. **PHASE 1: JavaScript/Node.js Setup** (Priority)
     - Check and install FUSE2 (required for AppImage execution)
     - Check and install Node.js (Ubuntu repos or NodeSource)
     - Install demo npm packages automatically
  3. **PHASE 2: System Dependencies**
     - Check system dependencies (cmake, gcc, python3, java, Fast-DDS, etc.)
     - Install missing dependencies if needed (via `init/sh/install_system_dependencies.sh`)
  4. **PHASE 3: Fast-DDS and Monitoring Build**
     - Run Fast-DDS manual installation (via `init/sh/fastdds_and_npm_auto_install.sh`)
     - Build monitoring application (via `monitoring/build_monitoring/build_monitoring.sh`)
  5. **PHASE 4: System Readiness Check**
     - Comprehensive check of all components:
       - Build tools (CMake, GCC/G++, Python3, Java)
       - Node.js and npm packages
       - Fast-DDS installation
       - IDL generated modules and executables
       - Monitoring executable
       - Security certificates
     - If any component is missing, run setup automatically (via `init/sh/project_setup.sh`)
     - Re-check system readiness after setup
  6. **PHASE 5: Start Tests and Demo** (Only if system is ready)
     - **Tests and demo will NOT start if any component is missing**
     - Run tests and demo automatically only when all components are ready (via `init/sh/run_tests_and_demo.sh`)
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
- Detect what's installed (project directory, system packages, environment variables, AppImage runtime, Node.js, manual Fast-DDS)
- Ask what you want to remove:
  - **Project directory** - Removes the entire DDS project folder
  - **System packages** - Removes Fast-DDS, CMake, Python, Java, etc. (⚠ may affect other projects)
  - **Environment variables** - Removes DDS-related variables from ~/.bashrc
  - **AppImage runtime directory** - Removes `~/.dds-project-runtime` (created by AppImage)
  - **Node.js and npm** - Removes Node.js, npm, and related files (⚠ may affect other projects)
  - **Manual Fast-DDS installation** - Removes manually installed Fast-DDS from common locations
- Create backups before making changes
- Provide clear confirmation prompts
- Warn about potential impact on other projects

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
- Make sure the AppImage is executable: `chmod +x DDS-v1.0.0_beta-x86_64.AppImage`

### FUSE errors when running AppImage
- **FUSE2 (required)**: The AppImage automatically checks and installs FUSE2 on first run
  - If installation fails, install manually:
    ```bash
    sudo apt-get update
    sudo apt-get install libfuse2
    ```
- Modern Linux distributions usually have FUSE2 pre-installed
- If FUSE2 installation fails, the AppImage will show an error message with manual installation instructions
- If FUSE is not available, the AppImage can still be extracted manually:
  ```bash
  ./DDS-v1.0.0_beta-x86_64.AppImage --appimage-extract
  cd squashfs-root
  ./AppRun
  ```

### Node.js installation issues
- **First run may fail**: Node.js installation may fail on first run (common issue)
  - **Solution**: Simply run the AppImage again - it will retry Node.js installation automatically
  - The AppImage will show clear error messages if Node.js installation fails
  - Manual installation instructions are provided in the error message
- **NodeSource repository**: If Ubuntu repositories fail, NodeSource repository is tried automatically
  - Requires `curl` - automatically installed if missing
  - Node.js v18.x is installed from NodeSource

### System readiness check failures
- **Tests and demo won't start**: If any component is missing, tests and demo will NOT start
  - Missing components are listed clearly in the error message
  - Setup is run automatically to fix missing components
  - After setup, system readiness is re-checked
  - If components are still missing, manual installation instructions are provided

### Setup fails
- Ensure you have sudo access (setup may require installing dependencies)
- Check that all required files exist in the project directory

