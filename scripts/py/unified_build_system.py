#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified Cross-Platform Build System for DDS Project
This script builds the DDS project on Windows and Linux systems.
Automatic platform detection and uses appropriate build tools.
"""

import os
import sys
import platform
import subprocess
import shutil
from pathlib import Path
from typing import List, Dict, Optional, Tuple

class UnifiedBuilder:
    """Cross-platform build system for DDS project."""
    
    def __init__(self):
        self.system = platform.system().lower()
        self.project_root = self._detect_project_root()
        self.build_dir = Path(self.project_root) / "cross-platform" / "build"
        self.idl_dir = Path(self.project_root) / "IDL"
        
        # Platform-specific settings
        self.is_windows = self.system == 'windows'
        self.is_linux = self.system == 'linux'
        
        print(f"🔧 Unified Builder initialized for {platform.system()}")
        print(f"📁 Project root: {self.project_root}")
        
    def _detect_project_root(self) -> str:
        """Dynamically detects project root directory - Cross-platform."""
        try:
            script_dir = Path(__file__).parent
        except NameError:
            script_dir = Path.cwd()
        
        current_dir = script_dir
        
        # Walk up the directory tree to find project root
        while current_dir != current_dir.parent:
            if (current_dir / "IDL").exists() and (current_dir / "scenarios").exists():
                return str(current_dir.absolute())
            current_dir = current_dir.parent
        
        # Fallback logic
        if script_dir.name == 'py' and script_dir.parent.name == 'scripts':
            project_root = script_dir.parent.parent
        elif script_dir.name in ['bat', 'sh'] and script_dir.parent.name == 'scripts':
            project_root = script_dir.parent.parent
        elif script_dir.name == 'scripts':
            project_root = script_dir.parent
        elif script_dir.name in ['sh', 'bat'] and script_dir.parent.name == 'init':
            project_root = script_dir.parent.parent
        else:
            project_root = Path.cwd()
        
        return str(project_root.absolute())
    
    def check_dependencies(self) -> Dict[str, bool]:
        """Checks required dependencies."""
        deps = {}
        
        # CMake check
        deps['cmake'] = shutil.which('cmake') is not None
        
        # Build system check
        if self.is_windows:
            # MSBuild or Ninja for Windows
            deps['msbuild'] = shutil.which('msbuild') is not None
            deps['ninja'] = shutil.which('ninja') is not None
            deps['build_system'] = deps['msbuild'] or deps['ninja']
        else:
            # Make or Ninja for Linux
            deps['make'] = shutil.which('make') is not None
            deps['ninja'] = shutil.which('ninja') is not None
            deps['build_system'] = deps['make'] or deps['ninja']
        
        # Fast-DDS check
        deps['fastddsgen'] = shutil.which('fastddsgen') is not None
        
        # Compiler check
        if self.is_windows:
            # Visual Studio compiler (cl.exe) usually not in PATH
            deps['compiler'] = True  # If MSBuild exists, compiler also exists
        else:
            deps['gcc'] = shutil.which('gcc') is not None
            deps['g++'] = shutil.which('g++') is not None
            deps['compiler'] = deps['gcc'] and deps['g++']
        
        return deps
    
    def print_dependency_status(self, deps: Dict[str, bool]) -> bool:
        """Prints dependency status."""
        print("\n🔍 Dependency Check:")
        
        all_ok = True
        for dep, status in deps.items():
            if dep in ['msbuild', 'ninja', 'make', 'gcc', 'g++']:
                continue  # Don't show these details
                
            icon = "✅" if status else "❌"
            print(f"  {icon} {dep}: {'OK' if status else 'MISSING'}")
            
            if not status:
                all_ok = False
        
        if not all_ok:
            print("\n❌ Missing dependencies detected!")
            if not deps.get('cmake'):
                print("  - Install CMake: https://cmake.org/download/")
            if not deps.get('fastddsgen'):
                print("  - Install Fast-DDS: https://fast-dds.docs.eprosima.com/")
            if not deps.get('build_system'):
                if self.is_windows:
                    print("  - Install Visual Studio or Build Tools")
                else:
                    print("  - Install build-essential: sudo apt install build-essential")
            if not deps.get('compiler'):
                if self.is_linux:
                    print("  - Install GCC: sudo apt install gcc g++")
        
        return all_ok
    
    def get_cmake_generator(self) -> str:
        """Returns appropriate CMake generator for platform."""
        if self.is_windows:
            if shutil.which('ninja'):
                return "Ninja"
            else:
                return "Visual Studio 17 2022"  # VS 2022
        else:
            if shutil.which('ninja'):
                return "Ninja"
            else:
                return "Unix Makefiles"
    
    def configure_cmake(self, build_type: str = "Release") -> bool:
        """Performs CMake configuration."""
        print(f"\n🔧 Configuring CMake ({build_type})...")
        
        # Create build directory
        self.build_dir.mkdir(exist_ok=True)
        
        generator = self.get_cmake_generator()
        print(f"📋 Using generator: {generator}")
        
        cmd = [
            'cmake',
            '-S', str(Path(self.project_root) / "cross-platform"),
            '-B', str(self.build_dir),
            '-G', generator,
            f'-DCMAKE_BUILD_TYPE={build_type}'
        ]
        
        # Additional settings for Windows
        if self.is_windows and "Visual Studio" in generator:
            cmd.extend(['-A', 'x64'])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root, 
                                  capture_output=True, text=True)
            
            if result.returncode == 0:
                print("✅ CMake configuration successful!")
                return True
            else:
                print("❌ CMake configuration failed!")
                print(f"Error: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ CMake configuration error: {e}")
            return False
    
    def build_project(self, build_type: str = "Release") -> bool:
        """Projeyi build eder."""
        print(f"\n🔨 Building project ({build_type})...")
        
        if not self.build_dir.exists():
            print("❌ Build directory not found. Run configure first.")
            return False
        
        cmd = [
            'cmake',
            '--build', str(self.build_dir),
            '--config', build_type
        ]
        
        # For parallel build
        if self.is_linux:
            cmd.extend(['--parallel', str(os.cpu_count())])
        elif self.is_windows:
            cmd.extend(['--parallel'])
        
        try:
            result = subprocess.run(cmd, cwd=self.project_root)
            
            if result.returncode == 0:
                print("✅ Build successful!")
                return True
            else:
                print("❌ Build failed!")
                return False
                
        except Exception as e:
            print(f"❌ Build error: {e}")
            return False
    
    def find_executables(self) -> List[Path]:
        """Find built executables."""
        executables = []
        
        # Search for executables in build directory
        if self.build_dir.exists():
            for root, dirs, files in os.walk(self.build_dir):
                for file in files:
                    file_path = Path(root) / file
                    
                    # .exe for Windows, executable bit for Linux
                    if self.is_windows and file.endswith('.exe'):
                        if not file.startswith('cmake') and not file.startswith('CompilerIdC'):
                            executables.append(file_path)
                    elif self.is_linux and os.access(file_path, os.X_OK):
                        if not file.startswith('.') and not file.endswith('.so'):
                            executables.append(file_path)
        
        return executables
    
    def clean_build(self) -> bool:
        """Build dizinini temizler."""
        print("\n🧹 Cleaning build directory...")
        
        if self.build_dir.exists():
            try:
                shutil.rmtree(self.build_dir)
                print("✅ Build directory cleaned!")
                return True
            except Exception as e:
                print(f"❌ Failed to clean build directory: {e}")
                return False
        else:
            print("ℹ️  Build directory doesn't exist.")
            return True
    
    def full_build(self, build_type: str = "Release", clean: bool = False) -> bool:
        """Perform full build operation."""
        print(f"\n🚀 Starting full build process...")
        print(f"🎯 Target: {build_type}")
        print(f"🧹 Clean: {'Yes' if clean else 'No'}")
        
        # Dependency check
        deps = self.check_dependencies()
        if not self.print_dependency_status(deps):
            return False
        
        # Cleanup
        if clean and not self.clean_build():
            return False
        
        # Configuration
        if not self.configure_cmake(build_type):
            return False
        
        # Build
        if not self.build_project(build_type):
            return False
        
        # Show results
        executables = self.find_executables()
        print(f"\n🎉 Build completed successfully!")
        print(f"📦 Generated {len(executables)} executables:")
        
        for exe in executables[:10]:  # Show first 10
            print(f"  📄 {exe.name}")
        
        if len(executables) > 10:
            print(f"  ... and {len(executables) - 10} more")
        
        return True

def main():
    """Ana fonksiyon."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Unified Cross-Platform Build System for DDS')
    parser.add_argument('--build-type', choices=['Debug', 'Release'], 
                       default='Release', help='Build type (default: Release)')
    parser.add_argument('--clean', action='store_true', 
                       help='Clean build directory before building')
    parser.add_argument('--configure-only', action='store_true',
                       help='Only configure, do not build')
    parser.add_argument('--build-only', action='store_true',
                       help='Only build, do not configure')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🔧 DDS Unified Cross-Platform Build System")
    print("=" * 60)
    
    builder = UnifiedBuilder()
    
    if args.configure_only:
        success = builder.configure_cmake(args.build_type)
    elif args.build_only:
        success = builder.build_project(args.build_type)
    else:
        success = builder.full_build(args.build_type, args.clean)
    
    if success:
        print("\n🎉 Operation completed successfully!")
    else:
        print("\n❌ Operation failed!")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())