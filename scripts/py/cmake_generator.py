#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cross-Platform CMakeLists.txt Generator for DDS IDL Modules
Bu betik tüm IDL modülleri için cross-platform CMakeLists.txt dosyaları oluşturur.
Windows ve Linux sistemlerde çalışır.
"""

import os
import platform
from pathlib import Path
from typing import List, Dict

class CMakeGenerator:
    """Cross-platform CMakeLists.txt generator for IDL modules."""
    
    def __init__(self):
        self.project_root = self._detect_project_root()
        self.idl_dir = Path(self.project_root) / "IDL"
        self.template_path = Path(self.project_root) / "cross-platform" / "templates" / "CMakeLists_template.txt"
        
    def _detect_project_root(self) -> str:
        """Proje kök dizinini dinamik olarak algılar - Cross-platform."""
        current_dir = Path.cwd()
        
        # Scripts/py klasöründeysek, iki üst dizine çık
        if current_dir.name == 'py' and current_dir.parent.name == 'scripts':
            project_root = current_dir.parent.parent
        # Scripts/bat veya scripts/sh klasöründeysek, iki üst dizine çık
        elif current_dir.name in ['bat', 'sh'] and current_dir.parent.name == 'scripts':
            project_root = current_dir.parent.parent
        # Scripts klasöründeysek, bir üst dizine çık
        elif current_dir.name == 'scripts':
            project_root = current_dir.parent
        else:
            project_root = current_dir
        
        return str(project_root.absolute())
    
    def find_idl_modules(self) -> List[str]:
        """IDL modüllerini bulur."""
        modules = []
        if not self.idl_dir.exists():
            print(f"IDL directory not found: {self.idl_dir}")
            return modules
            
        for item in self.idl_dir.iterdir():
            if item.is_dir() and item.name.endswith('_idl_generated'):
                module_name = item.name.replace('_idl_generated', '')
                modules.append(module_name)
                
        return sorted(modules)
    
    def load_template(self) -> str:
        """CMakeLists.txt template'ini yükler."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Template file not found: {self.template_path}")
            
        with open(self.template_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def generate_cmake_file(self, module_name: str) -> str:
        """Belirli bir modül için CMakeLists.txt içeriği oluşturur."""
        template = self.load_template()
        return template.replace('{MODULE_NAME}', module_name)
    
    def write_cmake_file(self, module_name: str, content: str) -> bool:
        """CMakeLists.txt dosyasını yazar."""
        module_dir = self.idl_dir / f"{module_name}_idl_generated"
        cmake_file = module_dir / "CMakeLists.txt"
        
        if not module_dir.exists():
            print(f"Module directory not found: {module_dir}")
            return False
            
        try:
            with open(cmake_file, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✓ Generated CMakeLists.txt for {module_name}")
            return True
        except Exception as e:
            print(f"✗ Failed to write CMakeLists.txt for {module_name}: {e}")
            return False
    
    def generate_all(self) -> Dict[str, bool]:
        """Tüm IDL modülleri için CMakeLists.txt dosyalarını oluşturur."""
        modules = self.find_idl_modules()
        results = {}
        
        if not modules:
            print("No IDL modules found!")
            return results
            
        print(f"Found {len(modules)} IDL modules: {', '.join(modules)}")
        print(f"Generating cross-platform CMakeLists.txt files...")
        print(f"Platform: {platform.system()}")
        
        for module in modules:
            content = self.generate_cmake_file(module)
            results[module] = self.write_cmake_file(module, content)
            
        return results
    
    def create_root_cmake(self) -> bool:
        """Ana CMakeLists.txt dosyasını oluşturur."""
        modules = self.find_idl_modules()
        if not modules:
            return False
            
        root_cmake_content = f"""cmake_minimum_required(VERSION 3.20)

project(DDS_IDL_Project)

set(CMAKE_CXX_STANDARD 11)
set(CMAKE_CXX_EXTENSIONS OFF)

# Cross-platform settings
if(WIN32)
    set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} /W3")
    add_definitions(-DWIN32_LEAN_AND_MEAN)
    add_definitions(-DNOMINMAX)
elseif(UNIX AND NOT APPLE)
    set(CMAKE_CXX_FLAGS "${{CMAKE_CXX_FLAGS}} -Wall -Wextra -fPIC")
    find_package(Threads REQUIRED)
endif()

# Find requirements
find_package(fastcdr REQUIRED)
find_package(fastdds 3 REQUIRED)

# Add subdirectories for each IDL module
"""
        
        for module in modules:
            root_cmake_content += f"add_subdirectory(IDL/{module}_idl_generated)\n"
            
        root_cmake_file = Path(self.project_root) / "cross-platform" / "CMakeLists.txt"
        
        try:
            with open(root_cmake_file, 'w', encoding='utf-8') as f:
                f.write(root_cmake_content)
            print(f"✓ Generated root CMakeLists.txt")
            return True
        except Exception as e:
            print(f"✗ Failed to write root CMakeLists.txt: {e}")
            return False

def main():
    """Ana fonksiyon."""
    print("=== Cross-Platform CMakeLists.txt Generator ===")
    
    generator = CMakeGenerator()
    
    # Tüm modüller için CMakeLists.txt oluştur
    results = generator.generate_all()
    
    # Ana CMakeLists.txt oluştur
    root_result = generator.create_root_cmake()
    
    # Sonuçları göster
    print("\n=== Results ===")
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    
    print(f"Generated {success_count}/{total_count} module CMakeLists.txt files")
    print(f"Root CMakeLists.txt: {'✓' if root_result else '✗'}")
    
    if success_count == total_count and root_result:
        print("\n🎉 All CMakeLists.txt files generated successfully!")
        print("Project is now ready for cross-platform building.")
    else:
        print("\n⚠️  Some files failed to generate. Check the errors above.")
        
    return success_count == total_count and root_result

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)