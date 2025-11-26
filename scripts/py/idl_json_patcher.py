#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDL Patcher - Adds JSON reading capability from IDL files to C++ header files
This script analyzes IDL files and adds JSON file reading capability to C++ Publisher applications.
Revised based on the CoreData example.
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class IDLJSONPatcher:
    def __init__(self):
        """Initialize IDL JSON Patcher class."""
        # Dynamically find project root directory
        self.project_root = self._detect_project_root()
        self.dummy_values = {
            'long': '1730352000L',
            'unsigned long': '0UL', 
            'long long': '9223372036854775807LL',
            'unsigned long long': '18446744073709551615ULL',
            'double': '41.0082',
            'float': '30.5f',
            'long double': '1.234L',
            'short': '135',
            'unsigned short': '85',
            'char': "'A'",
            'wchar': "L'ü'",
            'octet': '0x0A',
            'boolean': 'false',
            'string': '"UAV_MODUL_01"',
            'enum': '::IDLE'
        }
        
        # Dynamically find project root directory
        self.project_root = self._detect_project_root()
        
        # Special coordinate and speed values
        self.special_values = {
            'lat': '41.0082',
            'latitude': '41.0082',
            'lon': '28.9818', 
            'longitude': '28.9818',
            'alt': '30.5f',
            'altitude': '30.5f',
            'speed': '15.2f'
        }
        
        # Optimized dummy values for DDS flow
        self.dds_optimized_values = {
            'long': '1730352000L',  # Meaningful value for timestamp
            'unsigned long': '1730352000UL',  # For nano seconds
            'double': '41.0082',  # For coordinates
            'float': '30.5f',  # For altitude
            'short': '135',  # For orientation
            'string': '"UAV_MODUL_01"',  # For device ID
            'boolean': 'true'  # For system status
        }
        
        # Special values for DDS data flow
        self.dds_flow_values = {
            'seconds': '1730352000L',  # Timestamp seconds
            'nano_seconds': '1730352000UL',  # Timestamp nano seconds
            'latitude': '41.0082',  # GPS latitude
            'longitude': '28.9818',  # GPS longitude
            'altitude': '30.5f',  # GPS altitude
            'speed_mps': '15.2f',  # Speed in m/s
            'orientation_degrees': '135'  # Orientation in degrees
        }

    def find_idl_files(self, root_dir: str = "IDL") -> List[str]:
        """Find all *.idl files in the IDL directory."""
        idl_files = []
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.idl'):
                    idl_files.append(os.path.join(root, file))
        return idl_files

    def find_target_folder(self, idl_file: str) -> Optional[str]:
        """Find target folder for IDL file (with _idl_generated suffix)."""
        idl_name = os.path.splitext(os.path.basename(idl_file))[0]
        target_folder = f"{idl_name}_idl_generated"
        
        # Search in the directory where IDL file is located
        idl_dir = os.path.dirname(idl_file)
        target_path = os.path.join(idl_dir, target_folder)
        
        if os.path.exists(target_path):
            return target_path
        
        # Search in main directory
        main_target_path = os.path.join(".", target_folder)
        if os.path.exists(main_target_path):
            return main_target_path
            
        return None

    def parse_idl_file(self, idl_file: str) -> Dict[str, List[Tuple[str, str]]]:
        """Parse IDL file and extract structs and their members."""
        structs = {}
        
        try:
            with open(idl_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ IDL file could not be read: {idl_file} - {e}")
            return structs

        # Find structs
        struct_pattern = r'struct\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(struct_pattern, content, re.DOTALL)
        
        for match in matches:
            struct_name = match.group(1)
            struct_body = match.group(2)
            
            # Find struct members
            members = []
            # Remove comment lines
            struct_body = re.sub(r'//.*$', '', struct_body, flags=re.MULTILINE)
            
            # Find member definitions
            member_pattern = r'(\w+(?:\s+\w+)*)\s+(\w+);'
            member_matches = re.finditer(member_pattern, struct_body)
            
            for member_match in member_matches:
                member_type = member_match.group(1).strip()
                member_name = member_match.group(2).strip()
                members.append((member_type, member_name))
            
            structs[struct_name] = members
            
        return structs

    def find_header_file(self, target_folder: str, struct_name: str) -> Optional[str]:
        """Find C++ header file for struct in target folder."""
        # Search for main header file
        header_files = glob.glob(os.path.join(target_folder, "*.hpp"))
        if not header_files:
            header_files = glob.glob(os.path.join(target_folder, "*.h"))
        
        if header_files:
            return header_files[0]  # Return first found header file
        
        return None

    def find_app_files(self, target_folder: str) -> Dict[str, str]:
        """Find Publisher/Subscriber application files in target folder."""
        app_files = {}
        
        # Find Publisher file
        publisher_files = glob.glob(os.path.join(target_folder, "*PublisherApp.cxx"))
        if publisher_files:
            app_files['publisher'] = publisher_files[0]
        
        # Find Subscriber file
        subscriber_files = glob.glob(os.path.join(target_folder, "*SubscriberApp.cxx"))
        if subscriber_files:
            app_files['subscriber'] = subscriber_files[0]
        
        return app_files

    def get_dummy_value(self, member_type: str, member_name: str, module_name: str = "") -> str:
        """Return dummy value based on member type and name."""
        # Check special coordinate and speed values
        for keyword, value in self.special_values.items():
            if keyword in member_name.lower():
                return value
        
        # Dummy values for basic types
        for idl_type, dummy_value in self.dummy_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Default constructor call for complex types
        # Use default constructor for struct, enum, etc.
        if module_name:
            return f"{module_name}::{member_type}()"
        else:
            return f"{member_type}()"

    def get_enhanced_dummy_value(self, member_type: str, member_name: str, module_name: str = "") -> str:
        """Return enhanced dummy value for DDS flow."""
        # Check special coordinate and speed values
        for keyword, value in self.special_values.items():
            if keyword in member_name.lower():
                return value
        
        # Dummy values for basic types
        for idl_type, dummy_value in self.dummy_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Default constructor call for complex types
        # Use default constructor for struct, enum, etc.
        if module_name:
            return f"{module_name}::{member_type}()"
        else:
            return f"{member_type}()"

    def get_dds_optimized_dummy_value(self, member_type: str, member_name: str, module_name: str = "") -> str:
        """Return optimized dummy value for DDS data flow."""
        # Check special values for DDS data flow
        for keyword, value in self.dds_flow_values.items():
            if keyword in member_name.lower():
                return value
        
        # Check special coordinate and speed values
        for keyword, value in self.special_values.items():
            if keyword in member_name.lower():
                return value
        
        # Check DDS optimized values
        for idl_type, dummy_value in self.dds_optimized_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Dummy values for basic types
        for idl_type, dummy_value in self.dummy_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Default constructor call for complex types
        # Use default constructor for struct, enum, etc.
        if module_name:
            return f"{module_name}::{member_type}()"
        else:
            return f"{member_type}()"

    def patch_constructor(self, header_file: str, struct_name: str, members: List[Tuple[str, str]], module_name: str = "") -> bool:
        """Patch constructor in C++ header file."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Header file could not be read: {header_file} - {e}")
            return False

        # Find constructor - simpler pattern
        constructor_pattern = rf'eProsima_user_DllExport\s+{re.escape(struct_name)}\(\)\s*\{{([^}}]*)\}}'
        match = re.search(constructor_pattern, content, re.DOTALL)
        
        if not match:
            print(f"⚠️  {struct_name} constructor not found")
            return False

        constructor_body = match.group(1).strip()
        
        # If constructor is already filled, skip patching
        if constructor_body and not constructor_body.isspace():
            print(f"⚠️  {struct_name} constructor already filled, skipping")
            return True

        # Create new constructor content
        new_constructor_body = "        // Assigning dummy values\n"
        for member_type, member_name in members:
            dummy_value = self.get_enhanced_dummy_value(member_type, member_name, module_name)
            new_constructor_body += f"        m_{member_name} = {dummy_value};\n"

        # Update constructor - match actual file format
        old_constructor = match.group(0)  # Exact matching string
        new_constructor = f"eProsima_user_DllExport {struct_name}()\n    {{\n{new_constructor_body}\n    }}"
        
        updated_content = content.replace(old_constructor, new_constructor)
        
        if updated_content == content:
            print(f"     ⚠️  Constructor could not be changed - string mismatch")
            return False
        
        # Update file
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except Exception as e:
            print(f"❌ Header file could not be written: {header_file} - {e}")
            return False

    def process_idl_file(self, idl_file: str) -> bool:
        """Process a single IDL file."""
        print(f"\n🔍 Processing: {idl_file}")
        
        # Find target folder
        target_folder = self.find_target_folder(idl_file)
        if not target_folder:
            print(f"❌ Target folder not found: {os.path.splitext(os.path.basename(idl_file))[0]}_idl_generated")
            return False
        
        print(f"📁 Target folder: {target_folder}")
        
        # Parse IDL file
        structs = self.parse_idl_file(idl_file)
        if not structs:
            print(f"⚠️  No struct found in {idl_file} file")
            return True
        
        print(f"📋 Found structs: {list(structs.keys())}")
        
        # Find module name
        module_name = ""
        try:
            with open(idl_file, 'r', encoding='utf-8') as f:
                content = f.read()
            module_match = re.search(r'module\s+(\w+)', content)
            if module_match:
                module_name = module_match.group(1)
                print(f"📦 Module: {module_name}")
        except:
            pass
        
        success_count = 0
        total_count = len(structs)
        
        # Find header file
        header_file = self.find_header_file(target_folder, "CoreData")  # Main header file
        if not header_file:
            print(f"❌ Header file not found")
            return False
        
        print(f"📄 Header file: {os.path.basename(header_file)}")
        
        # Force patch all struct constructors
        if self.force_patch_all_constructors(header_file, structs, module_name):
            print(f"✅ All constructors successfully patched")
            success_count = total_count
        else:
            print(f"❌ Constructors could not be patched")
        
        # Patch Publisher/Subscriber applications
        app_files = self.find_app_files(target_folder)
        if app_files:
            print(f"\n📱 Application files found: {list(app_files.keys())}")
            
            # Find main struct - special selection based on module
            if module_name == "Intelligence":
                main_struct = "TaskAssignment"
            elif module_name == "Messaging":
                main_struct = "TaskCommand"
            else:
                # Select largest struct for other modules
                main_struct = max(structs.keys(), key=lambda x: len(structs[x]))
            
            if main_struct not in structs:
                print(f"     ⚠️  {main_struct} struct not found, using largest struct")
                main_struct = max(structs.keys(), key=lambda x: len(structs[x]))
            
            main_members = structs[main_struct]
            
            # Patch Publisher header
            publisher_header_file = os.path.join(target_folder, f"{module_name}PublisherApp.hpp")
            if os.path.exists(publisher_header_file):
                print(f"  🔧 Patching Publisher header: {os.path.basename(publisher_header_file)}")
                if self.patch_publisher_header(publisher_header_file, module_name):
                    print(f"     ✅ Publisher header successfully patched")
                else:
                    print(f"     ❌ Publisher header could not be patched")
            
            # Patch Publisher
            if 'publisher' in app_files:
                print(f"  🔧 Patching Publisher: {os.path.basename(app_files['publisher'])}")
                if self.patch_publisher_app(app_files['publisher'], main_struct, main_members, module_name):
                    print(f"     ✅ Publisher successfully patched")
                else:
                    print(f"     ❌ Publisher could not be patched")
            
            # CMakeLists.txt'i patch et
            cmake_file = os.path.join(target_folder, "CMakeLists.txt")
            if os.path.exists(cmake_file):
                print(f"  🔧 Patching CMakeLists.txt")
                if self.patch_cmake_lists(cmake_file):
                    print(f"     ✅ CMakeLists.txt successfully patched")
                else:
                    print(f"     ❌ CMakeLists.txt could not be patched")
            
            # Patch Subscriber
            if 'subscriber' in app_files:
                print(f"  🔧 Patching Subscriber: {os.path.basename(app_files['subscriber'])}")
                if self.patch_subscriber_app(app_files['subscriber'], main_struct, main_members, module_name):
                    print(f"     ✅ Subscriber successfully patched")
                else:
                    print(f"     ❌ Subscriber could not be patched")
        
        print(f"\n📊 Summary: {success_count}/{total_count} structs successfully processed")
        return success_count == total_count

    def patch_all_constructors(self, header_file: str, structs: Dict[str, List[Tuple[str, str]]], module_name: str = "") -> bool:
        """Patch constructors of all structs."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Header file could not be read: {header_file} - {e}")
            return False

        updated_content = content
        success_count = 0
        
        for struct_name, members in structs.items():
            print(f"  🔧 Patching constructor: {struct_name}")
            
            # Find constructor
            constructor_pattern = rf'eProsima_user_DllExport\s+{re.escape(struct_name)}\(\)\s*\{{([^}}]*)\}}'
            match = re.search(constructor_pattern, updated_content, re.DOTALL)
            
            if not match:
                print(f"     ⚠️  {struct_name} constructor not found")
                continue

            constructor_body = match.group(1).strip()
            
            # If constructor is already filled, skip patching
            if constructor_body and not constructor_body.isspace():
                print(f"     ⚠️  {struct_name} constructor already filled, skipping")
                success_count += 1
                continue

            # Create new constructor content
            new_constructor_body = "        // Assigning dummy values\n"
            for member_type, member_name in members:
                dummy_value = self.get_dds_optimized_dummy_value(member_type, member_name, module_name)
                new_constructor_body += f"        m_{member_name} = {dummy_value};\n"

            # Update constructor
            old_constructor = match.group(0)
            new_constructor = f"eProsima_user_DllExport {struct_name}()\n    {{\n{new_constructor_body}\n    }}"
            
            updated_content = updated_content.replace(old_constructor, new_constructor)
            success_count += 1
            print(f"     ✅ {struct_name} constructor patched")

        # Update file
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except Exception as e:
            print(f"❌ Header file could not be written: {header_file} - {e}")
            return False

    def force_patch_all_constructors(self, header_file: str, structs: Dict[str, List[Tuple[str, str]]], module_name: str = "") -> bool:
        """Force patch constructors of all structs (clears existing content)."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Header file could not be read: {header_file} - {e}")
            return False

        updated_content = content
        success_count = 0
        
        for struct_name, members in structs.items():
            print(f"  🔧 Force patching constructor: {struct_name}")
            
            # Find constructor
            constructor_pattern = rf'eProsima_user_DllExport\s+{re.escape(struct_name)}\(\)\s*\{{([^}}]*)\}}'
            match = re.search(constructor_pattern, updated_content, re.DOTALL)
            
            if not match:
                print(f"     ⚠️  {struct_name} constructor not found")
                continue

            # Create new constructor content
            new_constructor_body = "        // Assigning dummy values\n"
            for member_type, member_name in members:
                dummy_value = self.get_dds_optimized_dummy_value(member_type, member_name, module_name)
                new_constructor_body += f"        m_{member_name} = {dummy_value};\n"

            # Update constructor
            old_constructor = match.group(0)
            new_constructor = f"eProsima_user_DllExport {struct_name}()\n    {{\n{new_constructor_body}\n    }}"
            
            updated_content = updated_content.replace(old_constructor, new_constructor)
            success_count += 1
            print(f"     ✅ {struct_name} constructor force patched")

        # Update file
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except Exception as e:
            print(f"❌ Header file could not be written: {header_file} - {e}")
            return False

    def patch_publisher_header(self, header_file: str, module_name: str = "") -> bool:
        """Add required includes and member variables for JSON reading to Publisher header file."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Header file could not be read: {header_file} - {e}")
            return False

        # Check and add includes (with duplicate check)
        includes_to_add = [
            '#include <fstream>',
            '#include <vector>',
            '#include <nlohmann/json.hpp>'
        ]
        
        for include in includes_to_add:
            if include not in content:
                # Add after first include
                first_include_match = re.search(r'#include\s+<[^>]+>', content)
                if first_include_match:
                    insert_pos = first_include_match.end()
                    content = content[:insert_pos] + f'\n{include}' + content[insert_pos:]
                else:
                    # Add to file beginning
                    content = include + '\n' + content

        # Clean duplicate member variables (stronger regex)
        # Clean member variables repeated across multiple lines
        content = re.sub(r'std::vector<nlohmann::json> json_scenarios_;\s*\n\s*size_t current_scenario_index_;\s*\n\s*std::vector<nlohmann::json> json_scenarios_;\s*\n\s*size_t current_scenario_index_;', 
                        'std::vector<nlohmann::json> json_scenarios_;\n    size_t current_scenario_index_;', content)
        
        # Clean duplicates one by one
        content = re.sub(r'std::vector<nlohmann::json> json_scenarios_;\s*\n\s*std::vector<nlohmann::json> json_scenarios_;', 
                        'std::vector<nlohmann::json> json_scenarios_;', content)
        content = re.sub(r'size_t current_scenario_index_;\s*\n\s*size_t current_scenario_index_;', 
                        'size_t current_scenario_index_;', content)
        
        # Clean duplicate loadJsonScenarios functions
        content = re.sub(r'void loadJsonScenarios\(\);\s*\n\s*void loadJsonScenarios\(\);', 
                        'void loadJsonScenarios();', content)
        
        # Clean duplicate period_ms_
        content = re.sub(r'const uint32_t period_ms_ = 1000; // in ms\s*// in ms\s*// in ms', 
                        'const uint32_t period_ms_ = 1000; // in ms', content)
        
        # Clean duplicate period_ms_ (different formats)
        content = re.sub(r'const uint32_t period_ms_ = 1000; // in ms // in ms // 1 saniye', 
                        'const uint32_t period_ms_ = 1000; // in ms', content)
        
        # Clean duplicate loadJsonScenarios functions (different formats)
        content = re.sub(r'//! Load JSON scenarios from file\s*\n\s*void loadJsonScenarios\(\);', 
                        'void loadJsonScenarios();', content)
        
        # Clean duplicate comments for JSON data
        content = re.sub(r'// For JSON data\s*\n\s*std::vector<nlohmann::json> json_scenarios_;\s*\n\s*size_t current_scenario_index_;', 
                        '', content)

        # Add member variables (only if missing)
        member_vars = [
            'std::vector<nlohmann::json> json_scenarios_;',
            'size_t current_scenario_index_;'
        ]
        
        # Find private section and add member variables
        private_pattern = r'(private:\s*\n)'
        private_match = re.search(private_pattern, content)
        
        if private_match:
            private_start = private_match.end()
            # Add only missing ones
            existing_vars = []
            for var in member_vars:
                if var not in content:
                    existing_vars.append(f'    {var}')
            if existing_vars:
                member_vars_text = '\n'.join(existing_vars) + '\n'
                content = content[:private_start] + member_vars_text + content[private_start:]
        else:
            # Private section bulunamazsa, class sonuna ekle
            class_end_pattern = r'(\s*};\s*$)'
            class_end_match = re.search(class_end_pattern, content, re.MULTILINE)
            if class_end_match:
                class_end_pos = class_end_match.start()
                existing_vars = []
                for var in member_vars:
                    if var not in content:
                        existing_vars.append(f'    {var}')
                if existing_vars:
                    member_vars_text = '\nprivate:\n' + '\n'.join(existing_vars) + '\n'
                    content = content[:class_end_pos] + member_vars_text + content[class_end_pos:]

        # Add loadJsonScenarios function (with duplicate check)
        load_function = f'''    void loadJsonScenarios();'''
        
        if load_function not in content:
            # Find public section and add function
            public_pattern = r'(public:\s*\n)'
            public_match = re.search(public_pattern, content)
            
            if public_match:
                public_start = public_match.end()
                content = content[:public_start] + load_function + '\n' + content[public_start:]

        # Update period_ms_ to 1000 (with duplicate cleanup)
        period_pattern = r'const uint32_t period_ms_ = \d+;.*?// in ms'
        content = re.sub(period_pattern, 'const uint32_t period_ms_ = 1000; // in ms', content)
        
        # Clean duplicate period_ms_
        content = re.sub(r'const uint32_t period_ms_ = 1000; // in ms\s*// in ms\s*// in ms', 
                        'const uint32_t period_ms_ = 1000; // in ms', content)

        # Update file
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Header file could not be written: {header_file} - {e}")
            return False

    def patch_publisher_app(self, publisher_file: str, struct_name: str, members: List[Tuple[str, str]], module_name: str = "") -> bool:
        """Patch Publisher application - adds JSON reading capability."""
        try:
            with open(publisher_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Publisher file could not be read: {publisher_file} - {e}")
            return False

        # Clean duplicate loadJsonScenarios functions
        load_function_pattern = rf'void {module_name}PublisherApp::loadJsonScenarios\(\)\s*\{{[^}}]*\}}'
        content = re.sub(load_function_pattern, '', content, flags=re.DOTALL)
        
        # Clean duplicate code blocks (for syntax errors)
        # Clean duplicate nlohmann::json json_data; and file >> json_data; lines
        duplicate_pattern = r'nlohmann::json json_data;\s*\n\s*file >> json_data;\s*\n\s*file\.close\(\);\s*\n\s*json_scenarios_ = json_data\["scenarios"\];\s*\n\s*std::cout << "Loaded " << json_scenarios_\.size\(\) << " scenarios from JSON file\." << std::endl;\s*\n\s*\}\s*\n\s*catch \(const std::exception& e\)\s*\n\s*\{\s*\n\s*std::cerr << "JSON file read error: " << e\.what\(\) << std::endl;\s*\n\s*\}\s*\n\s*\}'
        content = re.sub(duplicate_pattern, '', content, flags=re.DOTALL)
        
        # Clean duplicate try-catch blocks
        duplicate_try_catch = r'try\s*\n\s*\{\s*\n\s*nlohmann::json json_data;\s*\n\s*file >> json_data;\s*\n\s*file\.close\(\);\s*\n\s*json_scenarios_ = json_data\["scenarios"\];\s*\n\s*std::cout << "Loaded " << json_scenarios_\.size\(\) << " scenarios from JSON file\." << std::endl;\s*\n\s*\}\s*\n\s*catch \(const std::exception& e\)\s*\n\s*\{\s*\n\s*std::cerr << "JSON file read error: " << e\.what\(\) << std::endl;\s*\n\s*\}'
        content = re.sub(duplicate_try_catch, '', content, flags=re.DOTALL)

        # Initialize current_scenario_index_ in constructor
        constructor_pattern = rf'{module_name}PublisherApp\(\)\s*:\s*([^}}]*)\{{([^}}]*)\}}'
        constructor_match = re.search(constructor_pattern, content, re.DOTALL)
        
        if constructor_match:
            constructor_body = constructor_match.group(2)
            if 'current_scenario_index_' not in constructor_body:
                init_line = '        current_scenario_index_ = 0;\n        loadJsonScenarios();'
                new_constructor_body = constructor_body.rstrip() + '\n' + init_line + '\n    }'
                content = content.replace(constructor_match.group(0), 
                                        constructor_match.group(0).replace(constructor_body, new_constructor_body))

        # Add loadJsonScenarios function
        load_function = f'''void {module_name}PublisherApp::loadJsonScenarios()
{{
    try
    {{
        std::ifstream file("{self.project_root}\\\\scenarios\\\\{module_name}.json");
        if (!file.is_open())
        {{
            std::cerr << "JSON file could not be opened: {self.project_root}\\\\scenarios\\\\{module_name}.json" << std::endl;
            return;
        }}

        nlohmann::json json_data;
        file >> json_data;
        file.close();

        json_scenarios_ = json_data["scenarios"];
        std::cout << "{module_name} JSON file: " << json_scenarios_.size() << " scenarios loaded." << std::endl;
    }}
    catch (const std::exception& e)
    {{
        std::cerr << "{module_name} JSON file reading error: " << e.what() << std::endl;
    }}
}}'''

        # Fonksiyonu dosya sonuna ekle
        content = content.rstrip() + '\n\n' + load_function

        # Completely replace publish() function
        publish_pattern = r'bool\s+\w+PublisherApp::publish\(\)\s*\{{[^}}]*\}}'
        publish_match = re.search(publish_pattern, content, re.DOTALL)
        
        if publish_match:
            # Special JSON reading code for Intelligence
            if module_name == "Intelligence":
                new_publish_function = f'''bool {module_name}PublisherApp::publish()
{{
    bool ret = false;
    // Wait for the data endpoints discovery
    std::unique_lock<std::mutex> matched_lock(mutex_);
    cv_.wait(matched_lock, [&]()
            {{
                // at least one has been discovered
                return ((matched_ > 0) || is_stopped());
            }});

    if (!is_stopped())
    {{
        // Get data from JSON
        if (current_scenario_index_ < json_scenarios_.size())
        {{
            {module_name}::{struct_name} sample_;
            const auto& scenario = json_scenarios_[current_scenario_index_];
            const auto& location = scenario["location"];
            const auto& coords = location["coords"];
            const auto& time_info = location["time_info"];

            // Set command
            sample_.command(scenario["command"].get<std::string>());

            // Set target location data
            sample_.target_location_data().coords().latitude(coords["latitude"].get<double>());
            sample_.target_location_data().coords().longitude(coords["longitude"].get<double>());
            sample_.target_location_data().coords().altitude(coords["altitude"].get<float>());

            // Set time information
            sample_.target_location_data().time_info().seconds(time_info["seconds"].get<int32_t>());
            sample_.target_location_data().time_info().nano_seconds(time_info["nano_seconds"].get<uint32_t>());

            // Speed and orientation
            sample_.target_location_data().speed_mps(location["speed_mps"].get<float>());
            sample_.target_location_data().orientation_degrees(location["orientation_degrees"].get<int16_t>());

            // Displaying sent data
            std::cout << "Scenario " << scenario["id"].get<int>() << " - " << scenario["description"].get<std::string>() << std::endl;
            std::cout << "  command: " << sample_.command() << std::endl;
            std::cout << "  target_location_data.coords.latitude: " << sample_.target_location_data().coords().latitude() << std::endl;
            std::cout << "  target_location_data.coords.longitude: " << sample_.target_location_data().coords().longitude() << std::endl;
            std::cout << "  target_location_data.coords.altitude: " << sample_.target_location_data().coords().altitude() << std::endl;
            std::cout << "  target_location_data.time_info.seconds: " << sample_.target_location_data().time_info().seconds() << std::endl;
            std::cout << "  target_location_data.time_info.nano_seconds: " << sample_.target_location_data().time_info().nano_seconds() << std::endl;
            std::cout << "  target_location_data.speed_mps: " << sample_.target_location_data().speed_mps() << std::endl;
            std::cout << "  target_location_data.orientation_degrees: " << sample_.target_location_data().orientation_degrees() << std::endl;

            ret = (RETCODE_OK == writer_->write(&sample_));

            // Move to next scenario
            current_scenario_index_++;
            if (current_scenario_index_ >= json_scenarios_.size())
            {{
                current_scenario_index_ = 0; // Return to beginning
            }}
        }}
    }}
    return ret;
}}'''
            elif module_name == "Messaging":
                # Special JSON reading code for Messaging
                new_publish_function = f'''bool {module_name}PublisherApp::publish()
{{
    bool ret = false;
    // Wait for the data endpoints discovery
    std::unique_lock<std::mutex> matched_lock(mutex_);
    cv_.wait(matched_lock, [&]()
            {{
                // at least one has been discovered
                return ((matched_ > 0) || is_stopped());
            }});

    if (!is_stopped())
    {{
        // Get data from JSON
        if (current_scenario_index_ < json_scenarios_.size())
        {{
            {module_name}::{struct_name} sample_;
            const auto& scenario = json_scenarios_[current_scenario_index_];
            const auto& location = scenario["location"];
            const auto& coords = location["coords"];
            const auto& time_info = location["time_info"];
            const auto& header = scenario["header"];
            const auto& assignment = scenario["assignment"];

            // Set header information
            sample_.header().sender_id(header["sender_id"].get<std::string>());
            sample_.header().send_time().seconds(header["send_time"]["seconds"].get<int32_t>());
            sample_.header().send_time().nano_seconds(header["send_time"]["nano_seconds"].get<uint32_t>());

            // Set receiver ID
            sample_.receiver_id(scenario["receiver_id"].get<std::string>());

            // Set assignment information
            sample_.assignment().command(assignment["command"].get<std::string>());
            sample_.assignment().target_location_data().coords().latitude(assignment["target_location_data"]["coords"]["latitude"].get<double>());
            sample_.assignment().target_location_data().coords().longitude(assignment["target_location_data"]["coords"]["longitude"].get<double>());
            sample_.assignment().target_location_data().coords().altitude(assignment["target_location_data"]["coords"]["altitude"].get<float>());
            sample_.assignment().target_location_data().time_info().seconds(assignment["target_location_data"]["time_info"]["seconds"].get<int32_t>());
            sample_.assignment().target_location_data().time_info().nano_seconds(assignment["target_location_data"]["time_info"]["nano_seconds"].get<uint32_t>());
            sample_.assignment().target_location_data().speed_mps(assignment["target_location_data"]["speed_mps"].get<float>());
            sample_.assignment().target_location_data().orientation_degrees(assignment["target_location_data"]["orientation_degrees"].get<int16_t>());

            // Displaying sent data
            std::cout << "Scenario " << scenario["id"].get<int>() << " - " << scenario["description"].get<std::string>() << std::endl;
            std::cout << "  header.sender_id: " << sample_.header().sender_id() << std::endl;
            std::cout << "  receiver_id: " << sample_.receiver_id() << std::endl;
            std::cout << "  assignment.command: " << sample_.assignment().command() << std::endl;

            ret = (RETCODE_OK == writer_->write(&sample_));

            // Move to next scenario
            current_scenario_index_++;
            if (current_scenario_index_ >= json_scenarios_.size())
            {{
                current_scenario_index_ = 0; // Return to beginning
            }}
        }}
    }}
    return ret;
}}'''
            else:
                # Standard JSON reading code for CoreData
                new_publish_function = f'''bool {module_name}PublisherApp::publish()
{{
    bool ret = false;
    // Wait for the data endpoints discovery
    std::unique_lock<std::mutex> matched_lock(mutex_);
    cv_.wait(matched_lock, [&]()
            {{
                // at least one has been discovered
                return ((matched_ > 0) || is_stopped());
            }});

    if (!is_stopped())
    {{
        // Get data from JSON
        if (current_scenario_index_ < json_scenarios_.size())
        {{
            {module_name}::{struct_name} sample_;
            const auto& scenario = json_scenarios_[current_scenario_index_];
            const auto& location = scenario["location"];
            const auto& coords = location["coords"];
            const auto& time_info = location["time_info"];

            // Set coordinates
            sample_.coords().latitude(coords["latitude"].get<double>());
            sample_.coords().longitude(coords["longitude"].get<double>());
            sample_.coords().altitude(coords["altitude"].get<float>());

            // Set time information
            sample_.time_info().seconds(time_info["seconds"].get<int32_t>());
            sample_.time_info().nano_seconds(time_info["nano_seconds"].get<uint32_t>());

            // Speed and orientation
            sample_.speed_mps(location["speed_mps"].get<float>());
            sample_.orientation_degrees(location["orientation_degrees"].get<int16_t>());

            // Displaying sent data
            std::cout << "Scenario " << scenario["id"].get<int>() << " - " << scenario["description"].get<std::string>() << std::endl;
            std::cout << "  coords.latitude: " << sample_.coords().latitude() << std::endl;
            std::cout << "  coords.longitude: " << sample_.coords().longitude() << std::endl;
            std::cout << "  coords.altitude: " << sample_.coords().altitude() << std::endl;
            std::cout << "  time_info.seconds: " << sample_.time_info().seconds() << std::endl;
            std::cout << "  time_info.nano_seconds: " << sample_.time_info().nano_seconds() << std::endl;
            std::cout << "  speed_mps: " << sample_.speed_mps() << std::endl;
            std::cout << "  orientation_degrees: " << sample_.orientation_degrees() << std::endl;

            ret = (RETCODE_OK == writer_->write(&sample_));

            // Move to next scenario
            current_scenario_index_++;
            if (current_scenario_index_ >= json_scenarios_.size())
            {{
                current_scenario_index_ = 0; // Return to beginning
            }}
        }}
    }}
    return ret;
}}'''
            
            # Replace old publish function with new one
            content = content.replace(publish_match.group(0), new_publish_function)
        
        # Update file
        try:
            with open(publisher_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Publisher file could not be written: {publisher_file} - {e}")
            return False

    def patch_cmake_lists(self, cmake_file: str) -> bool:
        """Add nlohmann_json dependency to CMakeLists.txt file."""
        try:
            with open(cmake_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ CMakeLists.txt file could not be read: {cmake_file} - {e}")
            return False

        # Add nlohmann_json find_package
        if 'find_package(nlohmann_json REQUIRED)' not in content:
            # Find and add find_package lines
            find_package_pattern = r'(find_package\([^)]+\))'
            find_package_match = re.search(find_package_pattern, content)
            
            if find_package_match:
                insert_pos = find_package_match.end()
                content = content[:insert_pos] + '\nfind_package(nlohmann_json REQUIRED)' + content[insert_pos:]
            else:
                # Add to file beginning
                content = 'find_package(nlohmann_json REQUIRED)\n' + content

        # Add nlohmann_json to target_link_libraries
        if 'nlohmann_json::nlohmann_json' not in content:
            target_link_pattern = r'(target_link_libraries\([^)]+\))'
            target_link_match = re.search(target_link_pattern, content)
            
            if target_link_match:
                old_target_link = target_link_match.group(1)
                new_target_link = old_target_link.rstrip(')') + '\n            nlohmann_json::nlohmann_json\n            )'
                content = content.replace(old_target_link, new_target_link)

        # Update file
        try:
            with open(cmake_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ CMakeLists.txt file could not be written: {cmake_file} - {e}")
            return False

    def patch_subscriber_app(self, subscriber_file: str, struct_name: str, members: List[Tuple[str, str]], module_name: str = "") -> bool:
        """Patch Subscriber application - displays received data."""
        try:
            with open(subscriber_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Subscriber file could not be read: {subscriber_file} - {e}")
            return False

        # Clean old data display codes - stronger regex
        old_display_pattern = r'            // Displaying received data\n(            std::cout << "[^"]*" << [^;]+;\n)*'
        content = re.sub(old_display_pattern, '', content)
        
        # Clean duplicate codes
        duplicate_pattern = r'            std::cout << "  [^"]*": " << sample_\.[^;]+;\n'
        content = re.sub(duplicate_pattern, '', content)
        
        # Clean all old cout lines
        old_cout_pattern = r'            std::cout << "  [^"]*" << sample_\.[^;]+;\n'
        content = re.sub(old_cout_pattern, '', content)
        
        # Clean empty lines
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Find sample receiving location in Subscriber
        sample_pattern = rf'{module_name}::{struct_name}\s+sample_;'
        match = re.search(sample_pattern, content)
        
        if not match:
            print(f"     ⚠️  {struct_name} sample not found in Subscriber")
            return False

        # Add data display inside while loop
        while_pattern = r'while \(\(!is_stopped\(\)\) && \(RETCODE_OK == reader->take_next_sample\(&sample_, &info\)\)\)\s*\{'
        while_match = re.search(while_pattern, content)
        
        if while_match:
            # Add data display inside while loop
            while_start = while_match.group(0)
            data_display = []
            data_display.append(f"            // Displaying received data")
            for member_type, member_name in members:
                # Detailed display for complex types
                if member_type == 'Coordinates':
                    data_display.append(f"            std::cout << \"  {member_name}.latitude: \" << sample_.{member_name}().latitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.longitude: \" << sample_.{member_name}().longitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.altitude: \" << sample_.{member_name}().altitude() << std::endl;")
                elif member_type == 'Timestamp':
                    data_display.append(f"            std::cout << \"  {member_name}.seconds: \" << sample_.{member_name}().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.nano_seconds: \" << sample_.{member_name}().nano_seconds() << std::endl;")
                elif member_type == 'Location':
                    data_display.append(f"            std::cout << \"  {member_name}.coords.latitude: \" << sample_.{member_name}().coords().latitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.coords.longitude: \" << sample_.{member_name}().coords().longitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.coords.altitude: \" << sample_.{member_name}().coords().altitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.time_info.seconds: \" << sample_.{member_name}().time_info().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.time_info.nano_seconds: \" << sample_.{member_name}().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.speed_mps: \" << sample_.{member_name}().speed_mps() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.orientation_degrees: \" << sample_.{member_name}().orientation_degrees() << std::endl;")
                elif member_type == 'MessageHeader':
                    data_display.append(f"            std::cout << \"  {member_name}.sender_id: \" << sample_.{member_name}().sender_id() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.send_time.seconds: \" << sample_.{member_name}().send_time().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.send_time.nano_seconds: \" << sample_.{member_name}().send_time().nano_seconds() << std::endl;")
                elif member_type == 'TaskAssignment':
                    data_display.append(f"            std::cout << \"  {member_name}.command: \" << sample_.{member_name}().command() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.coords.latitude: \" << sample_.{member_name}().target_location_data().coords().latitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.coords.longitude: \" << sample_.{member_name}().target_location_data().coords().longitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.coords.altitude: \" << sample_.{member_name}().target_location_data().coords().altitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.time_info.seconds: \" << sample_.{member_name}().target_location_data().time_info().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.time_info.nano_seconds: \" << sample_.{member_name}().target_location_data().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.speed_mps: \" << sample_.{member_name}().target_location_data().speed_mps() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.target_location_data.orientation_degrees: \" << sample_.{member_name}().target_location_data().orientation_degrees() << std::endl;")
                elif member_type == 'VehicleStatus':
                    data_display.append(f"            std::cout << \"  {member_name}.task_status: \" << static_cast<int>(sample_.{member_name}().task_status()) << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.battery_percentage: \" << sample_.{member_name}().battery_percentage() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.signal_strength_dbm: \" << sample_.{member_name}().signal_strength_dbm() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.system_error: \" << (sample_.{member_name}().system_error() ? \"true\" : \"false\") << std::endl;")
                elif member_type == 'TargetDetection':
                    data_display.append(f"            std::cout << \"  {member_name}.target_ID: \" << sample_.{member_name}().target_ID() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.type: \" << static_cast<int>(sample_.{member_name}().type()) << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.coords.latitude: \" << sample_.{member_name}().location_data().coords().latitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.coords.longitude: \" << sample_.{member_name}().location_data().coords().longitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.coords.altitude: \" << sample_.{member_name}().location_data().coords().altitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.time_info.seconds: \" << sample_.{member_name}().location_data().time_info().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.time_info.nano_seconds: \" << sample_.{member_name}().location_data().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.speed_mps: \" << sample_.{member_name}().location_data().speed_mps() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.location_data.orientation_degrees: \" << sample_.{member_name}().location_data().orientation_degrees() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.confidence_level: \" << sample_.{member_name}().confidence_level() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.description: \" << sample_.{member_name}().description() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.raw_data_link: \" << sample_.{member_name}().raw_data_link() << std::endl;")
                elif member_type == 'TaskCommand':
                    data_display.append(f"            std::cout << \"  {member_name}.header.sender_id: \" << sample_.{member_name}().header().sender_id() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.header.send_time.seconds: \" << sample_.{member_name}().header().send_time().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.header.send_time.nano_seconds: \" << sample_.{member_name}().header().send_time().nano_seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.receiver_id: \" << sample_.{member_name}().receiver_id() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.command: \" << sample_.{member_name}().assignment().command() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.coords.latitude: \" << sample_.{member_name}().assignment().target_location_data().coords().latitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.coords.longitude: \" << sample_.{member_name}().assignment().target_location_data().coords().longitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.coords.altitude: \" << sample_.{member_name}().assignment().target_location_data().coords().altitude() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.time_info.seconds: \" << sample_.{member_name}().assignment().target_location_data().time_info().seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.time_info.nano_seconds: \" << sample_.{member_name}().assignment().target_location_data().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.speed_mps: \" << sample_.{member_name}().assignment().target_location_data().speed_mps() << std::endl;")
                    data_display.append(f"            std::cout << \"  {member_name}.assignment.target_location_data.orientation_degrees: \" << sample_.{member_name}().assignment().target_location_data().orientation_degrees() << std::endl;")
                else:
                    data_display.append(f"            std::cout << \"  {member_name}: \" << sample_.{member_name}() << std::endl;")
            
            # Create new content
            new_content = content.replace(while_start, while_start + "\n" + "\n".join(data_display))
        else:
            # Fallback: add after sample definition
            sample_line = match.group(0)
            data_display = []
            data_display.append(f"        // Displaying received data")
            for member_type, member_name in members:
                # Detailed display for complex types
                if member_type == 'Coordinates':
                    data_display.append(f"        std::cout << \"  {member_name}.latitude: \" << sample_.{member_name}().latitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.longitude: \" << sample_.{member_name}().longitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.altitude: \" << sample_.{member_name}().altitude() << std::endl;")
                elif member_type == 'Timestamp':
                    data_display.append(f"        std::cout << \"  {member_name}.seconds: \" << sample_.{member_name}().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.nano_seconds: \" << sample_.{member_name}().nano_seconds() << std::endl;")
                elif member_type == 'Location':
                    data_display.append(f"        std::cout << \"  {member_name}.coords.latitude: \" << sample_.{member_name}().coords().latitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.coords.longitude: \" << sample_.{member_name}().coords().longitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.coords.altitude: \" << sample_.{member_name}().coords().altitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.time_info.seconds: \" << sample_.{member_name}().time_info().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.time_info.nano_seconds: \" << sample_.{member_name}().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.speed_mps: \" << sample_.{member_name}().speed_mps() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.orientation_degrees: \" << sample_.{member_name}().orientation_degrees() << std::endl;")
                elif member_type == 'MessageHeader':
                    data_display.append(f"        std::cout << \"  {member_name}.sender_id: \" << sample_.{member_name}().sender_id() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.send_time.seconds: \" << sample_.{member_name}().send_time().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.send_time.nano_seconds: \" << sample_.{member_name}().send_time().nano_seconds() << std::endl;")
                elif member_type == 'TaskAssignment':
                    data_display.append(f"        std::cout << \"  {member_name}.command: \" << sample_.{member_name}().command() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.coords.latitude: \" << sample_.{member_name}().target_location_data().coords().latitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.coords.longitude: \" << sample_.{member_name}().target_location_data().coords().longitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.coords.altitude: \" << sample_.{member_name}().target_location_data().coords().altitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.time_info.seconds: \" << sample_.{member_name}().target_location_data().time_info().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.time_info.nano_seconds: \" << sample_.{member_name}().target_location_data().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.speed_mps: \" << sample_.{member_name}().target_location_data().speed_mps() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.target_location_data.orientation_degrees: \" << sample_.{member_name}().target_location_data().orientation_degrees() << std::endl;")
                elif member_type == 'VehicleStatus':
                    data_display.append(f"        std::cout << \"  {member_name}.task_status: \" << static_cast<int>(sample_.{member_name}().task_status()) << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.battery_percentage: \" << sample_.{member_name}().battery_percentage() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.signal_strength_dbm: \" << sample_.{member_name}().signal_strength_dbm() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.system_error: \" << (sample_.{member_name}().system_error() ? \"true\" : \"false\") << std::endl;")
                elif member_type == 'TargetDetection':
                    data_display.append(f"        std::cout << \"  {member_name}.target_ID: \" << sample_.{member_name}().target_ID() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.type: \" << static_cast<int>(sample_.{member_name}().type()) << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.coords.latitude: \" << sample_.{member_name}().location_data().coords().latitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.coords.longitude: \" << sample_.{member_name}().location_data().coords().longitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.coords.altitude: \" << sample_.{member_name}().location_data().coords().altitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.time_info.seconds: \" << sample_.{member_name}().location_data().time_info().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.time_info.nano_seconds: \" << sample_.{member_name}().location_data().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.speed_mps: \" << sample_.{member_name}().location_data().speed_mps() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.location_data.orientation_degrees: \" << sample_.{member_name}().location_data().orientation_degrees() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.confidence_level: \" << sample_.{member_name}().confidence_level() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.description: \" << sample_.{member_name}().description() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.raw_data_link: \" << sample_.{member_name}().raw_data_link() << std::endl;")
                elif member_type == 'TaskCommand':
                    data_display.append(f"        std::cout << \"  {member_name}.header.sender_id: \" << sample_.{member_name}().header().sender_id() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.header.send_time.seconds: \" << sample_.{member_name}().header().send_time().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.header.send_time.nano_seconds: \" << sample_.{member_name}().header().send_time().nano_seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.receiver_id: \" << sample_.{member_name}().receiver_id() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.command: \" << sample_.{member_name}().assignment().command() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.coords.latitude: \" << sample_.{member_name}().assignment().target_location_data().coords().latitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.coords.longitude: \" << sample_.{member_name}().assignment().target_location_data().coords().longitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.coords.altitude: \" << sample_.{member_name}().assignment().target_location_data().coords().altitude() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.time_info.seconds: \" << sample_.{member_name}().assignment().target_location_data().time_info().seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.time_info.nano_seconds: \" << sample_.{member_name}().assignment().target_location_data().time_info().nano_seconds() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.speed_mps: \" << sample_.{member_name}().assignment().target_location_data().speed_mps() << std::endl;")
                    data_display.append(f"        std::cout << \"  {member_name}.assignment.target_location_data.orientation_degrees: \" << sample_.{member_name}().assignment().target_location_data().orientation_degrees() << std::endl;")
                else:
                    data_display.append(f"        std::cout << \"  {member_name}: \" << sample_.{member_name}() << std::endl;")
            
            # Create new content
            new_content = content.replace(sample_line, sample_line + "\n" + "\n".join(data_display))
        
        # Update file
        try:
            with open(subscriber_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"❌ Subscriber file could not be written: {subscriber_file} - {e}")
            return False

    def run(self):
        """Main processing function."""
        print("🚀 Starting IDL JSON Patcher...")
        print("=" * 50)
        
        # Find IDL files
        idl_files = self.find_idl_files()
        if not idl_files:
            print("❌ No IDL files found!")
            return
        
        print(f"📁 Found IDL files: {len(idl_files)}")
        for idl_file in idl_files:
            print(f"   - {idl_file}")
        
        # Process each IDL file
        total_success = 0
        total_files = len(idl_files)
        
        for idl_file in idl_files:
            if self.process_idl_file(idl_file):
                total_success += 1
        
        print("\n" + "=" * 50)
        print(f"🎉 Operation completed!")
        print(f"📊 Successful file count: {total_success}/{total_files}")
        
        if total_success == total_files:
            print("✅ All files successfully processed!")
        else:
            print("⚠️  Some files could not be processed, check error messages above.")
    
    def _detect_project_root(self) -> str:
        """Dynamically detect project root directory."""
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
    
    def check_portability(self) -> bool:
        """Perform portability check."""
        print("🔍 Running portability check...")
        
        # Check project structure
        required_dirs = ['IDL', 'docs']
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = Path(self.project_root) / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"⚠️  Missing directories: {missing_dirs}")
            return False
        
        # Check IDL files
        idl_files = list(Path(self.project_root).glob('IDL/*.idl'))
        if not idl_files:
            print("⚠️  IDL file not found")
            return False
        
        print("✅ Project structure is portable")
        return True

def main():
    """Main function."""
    patcher = IDLJSONPatcher()
    
    # Portability check
    if not patcher.check_portability():
        print("❌ Portability check failed, stopping operation.")
        return
    
    patcher.run()

if __name__ == "__main__":
    main()