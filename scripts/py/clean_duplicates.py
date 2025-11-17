#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cleans duplicate dynamic code blocks
"""

import re
from pathlib import Path

def clean_duplicate_dynamic_code(file_path: Path) -> bool:
    """Cleans duplicate dynamic code blocks in the file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Check resolve_dds_root count
        count = content.count("auto resolve_dds_root = []() -> std::filesystem::path {")
        
        if count <= 1:
            return False
        
        print(f"  {file_path.name}: {count} duplicate blocks found, cleaning...")
        
        # Find first block (with line numbers)
        lines = content.split('\n')
        first_block_start = None
        first_block_end = None
        
        for i, line in enumerate(lines):
            if "auto resolve_dds_root = []() -> std::filesystem::path {" in line and first_block_start is None:
                first_block_start = i
            elif first_block_start is not None and "const std::filesystem::path dds_root = resolve_dds_root();" in line:
                first_block_end = i + 1
                break
        
        if first_block_start is None or first_block_end is None:
            return False
        
        # Keep first block, remove all other duplicates
        # Check each line
        new_lines = []
        in_duplicate_block = False
        block_depth = 0
        
        for i, line in enumerate(lines):
            # Are we inside the first block?
            if first_block_start <= i < first_block_end:
                new_lines.append(line)
                continue
            
            # Is this the start of a duplicate block?
            if "auto resolve_dds_root = []() -> std::filesystem::path {" in line:
                in_duplicate_block = True
                block_depth = 1
                continue  # Skip this line
            
            # Are we inside a duplicate block?
            if in_duplicate_block:
                # Track { and } count inside lambda
                block_depth += line.count('{') - line.count('}')
                
                # Is this the end of the block?
                if "const std::filesystem::path dds_root = resolve_dds_root();" in line and block_depth == 0:
                    in_duplicate_block = False
                    continue  # Skip this line too
                
                # If still inside block, skip the line
                continue
            
            # Normal line
            new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
        
        if new_content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"  ✓ {file_path.name}: Cleaned ({count - 1} duplicates removed)")
            return True
        
        return False
        
    except Exception as e:
        print(f"  ✗ {file_path.name}: Error - {e}")
        return False

def main():
    """Clean all PublisherApp and SubscriberApp files."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    idl_dir = project_root / "IDL"
    
    print("Cleaning duplicate dynamic code blocks...")
    print("=" * 60)
    
    cleaned_count = 0
    
    for idl_gen_dir in idl_dir.glob("*_idl_generated"):
        for app_file in idl_gen_dir.glob("*PublisherApp.cxx"):
            if clean_duplicate_dynamic_code(app_file):
                cleaned_count += 1
        
        for app_file in idl_gen_dir.glob("*SubscriberApp.cxx"):
            if clean_duplicate_dynamic_code(app_file):
                cleaned_count += 1
    
    print("=" * 60)
    print(f"Total {cleaned_count} files cleaned.")
    
    return cleaned_count > 0

if __name__ == "__main__":
    import sys
    sys.exit(0 if main() else 1)

