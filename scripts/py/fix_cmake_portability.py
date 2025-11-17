#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Makes existing CMakeLists.txt files portable:
- Finds OpenSSL using find_package (removes hardcoded paths)
- Adds RPATH settings (for portable binaries)
"""

import re
from pathlib import Path

def fix_cmake_file(cmake_file: Path) -> bool:
    """Makes CMakeLists.txt file portable."""
    try:
        with open(cmake_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        modified = False
        
        # 1. Remove hardcoded OpenSSL paths, use find_package
        if 'set(OPENSSL_ROOT_DIR "/usr")' in content or 'set(OPENSSL_LIBRARIES "/usr/lib' in content:
            # Add find_package(OpenSSL) if not present
            if 'find_package(OpenSSL REQUIRED)' not in content:
                # Add to find packages section
                content = re.sub(
                    r'(find_package\(fastdds REQUIRED\))',
                    r'\1\nfind_package(OpenSSL REQUIRED)',
                    content
                )
                modified = True
                print(f"  ➕ find_package(OpenSSL) added")
            
            # Remove hardcoded OpenSSL settings
            content = re.sub(
                r'#\s*OpenSSL configuration.*?set\(OPENSSL_INCLUDE_DIR.*?\n',
                '',
                content,
                flags=re.DOTALL
            )
            content = re.sub(r'set\(OPENSSL_ROOT_DIR[^\n]*\n', '', content)
            content = re.sub(r'set\(OPENSSL_LIBRARIES[^\n]*\n', '', content)
            content = re.sub(r'set\(OPENSSL_INCLUDE_DIR[^\n]*\n', '', content)
            content = re.sub(r'include_directories\([^)]*OPENSSL[^)]*\)\n', '', content)
            
            # Use OpenSSL::SSL and OpenSSL::Crypto
            content = content.replace('${OPENSSL_LIBRARIES}', 'OpenSSL::SSL OpenSSL::Crypto')
            modified = True
            print(f"  🔄 Hardcoded OpenSSL paths removed")
        
        # 2. Add RPATH settings (for portable binaries)
        if 'CMAKE_BUILD_RPATH_USE_ORIGIN' not in content:
            # Add after Set C++ standard
            rpath_settings = """
# Portable binary settings - RPATH for shared libraries
# Use relative RPATH so binaries work when moved to different locations
set(CMAKE_BUILD_RPATH_USE_ORIGIN TRUE)  # Use $ORIGIN for relative paths
set(CMAKE_INSTALL_RPATH_USE_LINK_PATH FALSE)
# Add common library paths to RPATH (relative to executable)
set(CMAKE_BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib:/usr/local/lib")
"""
            
            content = re.sub(
                r'(set\(CMAKE_CXX_STANDARD_REQUIRED ON\))',
                r'\1' + rpath_settings,
                content
            )
            modified = True
            print(f"  ➕ RPATH settings added")
        
        # 3. Add RPATH property to executables
        if 'set_target_properties(${EXEC_NAME}' not in content:
            # Add set_target_properties after add_executable
            rpath_props = """
        
        # Set RPATH for portable binaries (relative to executable location)
        set_target_properties(${EXEC_NAME} PROPERTIES
            BUILD_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
            INSTALL_RPATH "$ORIGIN/../lib:$ORIGIN/../../lib"
            BUILD_WITH_INSTALL_RPATH FALSE
            INSTALL_WITH_INSTALL_RPATH FALSE
        )
"""
            
            content = re.sub(
                r'(add_executable\(\$\{EXEC_NAME\}[^\n]*\n)',
                r'\1' + rpath_props,
                content
            )
            modified = True
            print(f"  ➕ Executable RPATH properties added")
        
        if modified:
            with open(cmake_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ {cmake_file.name}: Made portable")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ❌ {cmake_file.name}: Error - {e}")
        return False

def main():
    """Fixes CMakeLists.txt files for all IDL modules."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    idl_dir = project_root / "IDL"
    
    print("=" * 60)
    print("CMakeLists.txt Portability Fix")
    print("=" * 60)
    print()
    
    fixed_count = 0
    
    for idl_gen_dir in idl_dir.glob("*_idl_generated"):
        cmake_file = idl_gen_dir / "CMakeLists.txt"
        if cmake_file.exists():
            print(f"📝 Processing: {cmake_file.name}")
            if fix_cmake_file(cmake_file):
                fixed_count += 1
            print()
    
    print("=" * 60)
    print(f"Total {fixed_count} files updated.")
    print()
    
    return fixed_count > 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)

