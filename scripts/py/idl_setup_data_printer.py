#!/usr/bin/env python3
"""
IDL Setup Patcher Script
This script automatically updates Publisher and Subscriber App files in all *_idl_generated folders,
adding code blocks that print object data in JSON format during sample send/receive operations.

Features:
- Does not add any new files
- Does not delete any functions
- Only adds data printing functionality to existing functions
- Automatically updates all *_idl_generated folders
- Does not break the original file structure
"""

import os
import re
import glob
import sys
from pathlib import Path

class IDLSetupPatcher:
    def __init__(self, base_path):
        self.base_path = Path(base_path)
        self.idl_folders = []
        self.processed_files = []
        
    def find_idl_generated_folders(self):
        """Find all *_idl_generated folders"""
        pattern = str(self.base_path / "IDL" / "*_idl_generated")
        self.idl_folders = glob.glob(pattern)
        print(f"Found IDL generated folders: {len(self.idl_folders)}")
        for folder in self.idl_folders:
            print(f"  - {folder}")
        return self.idl_folders
    
    def extract_data_fields_from_header(self, header_file_path):
        """Extract data fields from header file"""
        try:
            with open(header_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Find private member variables
            private_section_match = re.search(r'private:\s*\n(.*?)(?:\n\s*\};|\Z)', content, re.DOTALL)
            if not private_section_match:
                return []
            
            private_content = private_section_match.group(1)
            
            # Extract member variables (starting with m_)
            field_pattern = r'\s*(\w+)\s+m_(\w+)(?:\{[^}]*\})?;'
            matches = re.findall(field_pattern, private_content)
            
            fields = []
            for type_name, field_name in matches:
                fields.append({
                    'name': field_name,
                    'type': type_name,
                    'accessor': field_name  # getter function name
                })
            
            return fields
            
        except Exception as e:
            print(f"Header file read error {header_file_path}: {e}")
            return []
    
    def generate_data_printing_code(self, fields, sample_var_name, namespace_class):
        """Generate data printing code - uses -> for pointer access, prevents adding extra characters"""
        if not fields:
            return f'std::cout << "No data fields found for {namespace_class}" << std::endl;'
        
        code_lines = []
        code_lines.append('std::cout << " - {";')
        
        for i, field in enumerate(fields):
            is_last_field = (i == len(fields) - 1)
            
            if field['type'] in ['std::string']:
                if is_last_field:
                    code_lines.append(f'std::cout << "{field["name"]}: \\"" << {sample_var_name}->{field["accessor"]}() << "\\"";')
                else:
                    code_lines.append(f'std::cout << "{field["name"]}: \\"" << {sample_var_name}->{field["accessor"]}() << "\\", ";')
            elif field['type'] in ['bool']:
                if is_last_field:
                    code_lines.append(f'std::cout << "{field["name"]}: " << ({sample_var_name}->{field["accessor"]}() ? "true" : "false") << "";')
                else:
                    code_lines.append(f'std::cout << "{field["name"]}: " << ({sample_var_name}->{field["accessor"]}() ? "true" : "false") << ", ";')
            else:
                if is_last_field:
                    code_lines.append(f'std::cout << "{field["name"]}: " << {sample_var_name}->{field["accessor"]}() << "";')
                else:
                    code_lines.append(f'std::cout << "{field["name"]}: " << {sample_var_name}->{field["accessor"]}() << ", ";')
        
        code_lines.append('std::cout << "}" << std::endl;')
        
        # Return clean string to prevent adding extra characters
        return '\n            '.join(code_lines)
    
    def patch_publisher_file(self, file_path):
        """Update Publisher file - adds data printing code inside run() function"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract namespace and class name
            namespace_match = re.search(r'#include "(\w+)PubSubTypes\.hpp"', content)
            if not namespace_match:
                print(f"Namespace not found: {file_path}")
                return False
            
            namespace = namespace_match.group(1)
            
            # Find header file
            header_file = file_path.replace('PublisherApp.cxx', '.hpp')
            if not os.path.exists(header_file):
                print(f"Header file not found: {header_file}")
                return False
            
            # Extract data fields
            fields = self.extract_data_fields_from_header(header_file)
            if not fields:
                print(f"Data fields not found: {header_file}")
                return False
            
            # Sample variable is now defined as member variable, extract class name from header file
            # Find sample_ member variable from header file
            try:
                with open(header_file, 'r', encoding='utf-8') as f:
                    header_content = f.read()
                
                sample_var_match = re.search(r'(\w+::\w+)\s+sample_;', header_content)
                if not sample_var_match:
                    print(f"Sample member variable not found: {header_file}")
                    return False
                
                sample_class = sample_var_match.group(1)
                sample_var = "sample_"
            except Exception as e:
                print(f"Header file read error: {e}")
                return False
            
            # 1. First change publish() function to return sample_ instead of bool
            # Change publish() function return type
            publish_signature_pattern = r'bool\s+(\w+PublisherApp::publish\(\))'
            if re.search(publish_signature_pattern, content):
                content = re.sub(publish_signature_pattern, f'{sample_class}* \\1', content)
            
            # Update publish() function content - return sample_
            # First remove samples_sent_++ part because we'll do this in run() function
            publish_return_pattern = r'(ret = \(RETCODE_OK == writer_->write\(&sample_\)\);\s*if \(ret\)\s*\{\s*samples_sent_\+\+;\s*\}\s*)\s*return ret;'
            if re.search(publish_return_pattern, content, re.DOTALL):
                content = re.sub(publish_return_pattern, 'ret = (RETCODE_OK == writer_->write(&sample_));\n        return ret ? &sample_ : nullptr;', content, flags=re.DOTALL)
            
            # Also update publish() function signature in header file
            header_publish_pattern = r'bool\s+publish\(\);'
            if re.search(header_publish_pattern, header_content):
                header_content = re.sub(header_publish_pattern, f'{sample_class}* publish();', header_content)
                
                with open(header_file, 'w', encoding='utf-8') as f:
                    f.write(header_content)
            
            # 2. Add data printing code inside run() function using sample pointer
            data_printing_code = self.generate_data_printing_code(fields, "sample", sample_class)
            
            # Find and update existing "auto sample = publish(); if (sample)" block inside run() function
            existing_sample_pattern = r'(auto sample = publish\(\);\s*if \(sample\)\s*\{\s*)(.*?)(\s*\})'
            
            if re.search(existing_sample_pattern, content, re.DOTALL):
                # Update existing code - prevent adding extra characters
                replacement = f'\\1std::cout << "Sample \'" << std::to_string(samples_sent_) << "\' SENT" << std::endl;\n            {data_printing_code}\n            ++samples_sent_;\\3'
                content = re.sub(existing_sample_pattern, replacement, content, flags=re.DOTALL)
                
                # Clean extra characters
                content = re.sub(r'\+\+samples_sent_;\}" << std::endl;\s*\+\+samples_sent_;', '++samples_sent_;', content)
                
                # Save file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Publisher updated (existing auto sample pattern): {file_path}")
                return True
            else:
                # Search for old if (publish()) pattern
                run_publish_pattern = r'(if \(publish\(\)\)\s*\{\s*)(.*?)(\s*\})'
                
                if re.search(run_publish_pattern, content, re.DOTALL):
                    # New code: auto sample = publish(); if (sample) { ... }
                    replacement = f'auto sample = publish();\n        if (sample)\n        {{\n            std::cout << "Sample \'" << std::to_string(samples_sent_) << "\' SENT" << std::endl;\n            {data_printing_code}\n            ++samples_sent_;\n        }}'
                    content = re.sub(run_publish_pattern, replacement, content, flags=re.DOTALL)
                    
                    # Save file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"Publisher updated (run() function): {file_path}")
                    return True
                else:
                    print(f"Publish pattern not found in run() function: {file_path}")
                    return False
                
        except Exception as e:
            print(f"Publisher file update error {file_path}: {e}")
            return False
    
    def patch_subscriber_file(self, file_path):
        """Updates Subscriber file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract namespace and class name
            namespace_match = re.search(r'#include "(\w+)PubSubTypes\.hpp"', content)
            if not namespace_match:
                print(f"Namespace not found: {file_path}")
                return False
            
            namespace = namespace_match.group(1)
            
            # Find header file
            header_file = file_path.replace('SubscriberApp.cxx', '.hpp')
            if not os.path.exists(header_file):
                print(f"Header file not found: {header_file}")
                return False
            
            # Extract data fields
            fields = self.extract_data_fields_from_header(header_file)
            if not fields:
                print(f"Data fields not found: {header_file}")
                return False
            
            # Find sample variable name (in on_data_available function)
            sample_var_match = re.search(r'(\w+::\w+)\s+(\w+);\s*\n\s*SampleInfo info;', content)
            if not sample_var_match:
                print(f"Sample variable not found: {file_path}")
                return False
            
            sample_class = sample_var_match.group(1)
            sample_var = sample_var_match.group(2)
            
            # Generate data printing code - use . in Subscriber since sample is a variable
            # In Subscriber, sample is not a pointer, it's a direct object
            data_printing_code_lines = []
            data_printing_code_lines.append('std::cout << " - {";')
            
            for i, field in enumerate(fields):
                separator = ", " if i < len(fields) - 1 else ""
                
                if field['type'] in ['std::string']:
                    data_printing_code_lines.append(f'std::cout << "{field["name"]}: \\"" << {sample_var}.{field["accessor"]}() << "\\"{separator}";')
                elif field['type'] in ['bool']:
                    data_printing_code_lines.append(f'std::cout << "{field["name"]}: " << ({sample_var}.{field["accessor"]}() ? "true" : "false") << "{separator}";')
                else:
                    data_printing_code_lines.append(f'std::cout << "{field["name"]}: " << {sample_var}.{field["accessor"]}() << "{separator}";')
            
            data_printing_code_lines.append('std::cout << "}" << std::endl;')
            data_printing_code = '\n            '.join(data_printing_code_lines)
            
            # Find where "Sample 'X' RECEIVED" is printed in Subscriber and add data printing code
            received_pattern = r'(std::cout << "Sample \'" << std::to_string\(\+\+samples_received_\) << "\' RECEIVED" << std::endl;)'
            
            if re.search(received_pattern, content):
                # If data printing code is already added, update it
                existing_data_pattern = r'(std::cout << "Sample \'" << std::to_string\(\+\+samples_received_\) << "\' RECEIVED" << std::endl;)\s*\n(\s*std::cout << " - \{.*?\}" << std::endl;)'
                
                if re.search(existing_data_pattern, content, re.DOTALL):
                    # Update existing data printing code
                    replacement = f'\\1\n            {data_printing_code}'
                    content = re.sub(existing_data_pattern, replacement, content, flags=re.DOTALL)
                else:
                    # Add new data printing code
                    replacement = f'\\1\n            {data_printing_code}'
                    content = re.sub(received_pattern, replacement, content)
                
                # Save file
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Subscriber updated: {file_path}")
                return True
            else:
                print(f"RECEIVED pattern not found: {file_path}")
                return False
                
        except Exception as e:
            print(f"Subscriber file update error {file_path}: {e}")
            return False
    
    def process_idl_folder(self, folder_path):
        """Processes an IDL generated folder"""
        folder_path = Path(folder_path)
        print(f"\nProcessing: {folder_path}")
        
        # Find and update Publisher App file
        publisher_files = list(folder_path.glob("*PublisherApp.cxx"))
        for pub_file in publisher_files:
            if pub_file.name.endswith('.backup'):
                continue
            print(f"  Publisher file: {pub_file}")
            if self.patch_publisher_file(str(pub_file)):
                self.processed_files.append(str(pub_file))
        
        # Find and update Subscriber App file
        subscriber_files = list(folder_path.glob("*SubscriberApp.cxx"))
        for sub_file in subscriber_files:
            if sub_file.name.endswith('.backup'):
                continue
            print(f"  Subscriber file: {sub_file}")
            if self.patch_subscriber_file(str(sub_file)):
                self.processed_files.append(str(sub_file))
    
    def run(self):
        """Main processing function"""
        print("Starting IDL Setup Patcher...")
        print(f"Base directory: {self.base_path}")
        
        # Find IDL generated folders
        folders = self.find_idl_generated_folders()
        if not folders:
            print("No IDL generated folders found!")
            return False
        
        # Process each folder
        for folder in folders:
            self.process_idl_folder(folder)
        
        # Show results
        print(f"\n=== PROCESSING COMPLETED ===")
        print(f"Processed folder count: {len(folders)}")
        print(f"Updated file count: {len(self.processed_files)}")
        
        if self.processed_files:
            print("\nUpdated files:")
            for file_path in self.processed_files:
                print(f"  - {file_path}")
        
        return len(self.processed_files) > 0

def main():
    """Main function"""
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        # Dynamically find DDS root directory from script's location
        script_dir = Path(__file__).parent
        current_dir = script_dir
        
        # Walk up the directory tree to find project root
        while current_dir != current_dir.parent:
            if (current_dir / "IDL").exists() and (current_dir / "scenarios").exists():
                base_path = current_dir
                break
            current_dir = current_dir.parent
        else:
            # Fallback logic
            if script_dir.name == 'py' and script_dir.parent.name == 'scripts':
                base_path = script_dir.parent.parent
            elif script_dir.name in ['bat', 'sh'] and script_dir.parent.name == 'scripts':
                base_path = script_dir.parent.parent
            elif script_dir.name == 'scripts':
                base_path = script_dir.parent
            elif script_dir.name in ['sh', 'bat'] and script_dir.parent.name == 'init':
                base_path = script_dir.parent.parent
            else:
                base_path = Path.cwd()
    
    patcher = IDLSetupPatcher(base_path)
    success = patcher.run()
    
    if success:
        print("\n✅ All files successfully updated!")
        print("\nNow Publisher and Subscriber applications will print sample data")
        print("in JSON format to the screen:")
        print("  - Sample 'X' SENT - {field1: value1, field2: value2, ...}")
        print("  - Sample 'X' RECEIVED - {field1: value1, field2: value2, ...}")
    else:
        print("\n❌ No files could be updated!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())