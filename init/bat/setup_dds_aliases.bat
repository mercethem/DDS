@echo off
REM DDS Convenience Aliases - Windows
REM This file is dynamically generated - DO NOT EDIT MANUALLY
REM Run: scripts\bat\setup_environment.bat to regenerate

REM Get script directory dynamically
set "SCRIPT_DIR=%~dp0"

REM Load environment first
call "%SCRIPT_DIR%\export_dds_environment.bat"

REM Build aliases (functions)
goto :main

:dds-build
call "%DDS_SCRIPTS_DIR%\build_idl_modules.bat"
goto :eof

:dds-clean
for /d %%d in ("%DDS_IDL_DIR%\*_idl_generated") do (
    if exist "%%d" rmdir /s /q "%%d" 2>nul
)
goto :eof

:dds-env
call "%DDS_SCRIPTS_DIR%\setup_environment.bat"
goto :eof

:dds-security
cd /d "%DDS_PROJECT_ROOT%\scripts\py"
python apply_security_settings.py
goto :eof

:dds-patch-idl
cd /d "%DDS_PROJECT_ROOT%\scripts\py"
python idl_default_data_patcher.py
goto :eof

:dds-patch-json
cd /d "%DDS_PROJECT_ROOT%\scripts\py"
python json_reading_patcher.py
goto :eof

:dds-demo
cd /d "%DDS_PROJECT_ROOT%\demo"
call npm start
goto :eof

:cd-dds
cd /d "%DDS_PROJECT_ROOT%"
goto :eof

:cd-idl
cd /d "%DDS_IDL_DIR%"
goto :eof

:cd-scripts
cd /d "%DDS_SCRIPTS_DIR%"
goto :eof

:main
echo DDS aliases loaded. Available commands:
echo   dds-build     - Build all IDL modules
echo   dds-clean     - Clean generated files
echo   dds-env       - Refresh environment
echo   dds-security  - Apply security patches
echo   dds-patch-idl - Patch IDL files
echo   dds-patch-json- Patch JSON files
echo   dds-demo      - Start demo server
echo   cd-dds        - Go to project root
echo   cd-idl        - Go to IDL directory
echo   cd-scripts    - Go to scripts directory
echo.
echo Usage: call dds_aliases_windows.bat :command-name
echo Example: call dds_aliases_windows.bat :dds-build

