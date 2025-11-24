#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Period Setter for DDS Publisher Applications
This script modifies the period_ms_ value in all PublisherApp.hpp files.
"""

import os
import re
import glob
import sys
import platform
from pathlib import Path
from typing import List, Optional


class PeriodSetter:
    """
    Sets the period_ms_ value in all PublisherApp.hpp files
    """
    
    def __init__(self, project_root: str = None):
        """Initialize the Period Setter."""
        self.project_root = project_root or self._detect_project_root()
        self.idl_dir = os.path.join(self.project_root, "IDL")
        
    def _detect_project_root(self) -> str:
        """Detect the project root directory."""
        current_dir = os.getcwd()
        
        # Look for characteristic directories
        while current_dir != os.path.dirname(current_dir):  # Not at filesystem root
            if (os.path.exists(os.path.join(current_dir, "IDL")) and 
                os.path.exists(os.path.join(current_dir, "scenarios"))):
                return current_dir
            current_dir = os.path.dirname(current_dir)
        
        # Fallback to current directory
        return os.getcwd()
    
    def find_publisher_header_files(self) -> List[str]:
        """Find all PublisherApp.hpp files in IDL directory."""
        publisher_files = []
        
        if not os.path.exists(self.idl_dir):
            print(f"ERROR: IDL directory not found: {self.idl_dir}")
            return publisher_files
        
        # Find all *_idl_generated directories
        idl_generated_dirs = glob.glob(os.path.join(self.idl_dir, "*_idl_generated"))
        
        for idl_dir in idl_generated_dirs:
            # Find PublisherApp.hpp files in each directory
            pattern = os.path.join(idl_dir, "*PublisherApp.hpp")
            files = glob.glob(pattern)
            publisher_files.extend(files)
        
        return sorted(publisher_files)
    
    def get_current_period(self, file_path: str) -> Optional[int]:
        """Get the current period_ms_ value from a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern to match: const uint32_t period_ms_ = <value>;
            pattern = r'const\s+uint32_t\s+period_ms_\s*=\s*(\d+)\s*;'
            match = re.search(pattern, content)
            
            if match:
                return int(match.group(1))
            return None
        except Exception as e:
            print(f"ERROR reading {file_path}: {e}")
            return None
    
    def set_period(self, file_path: str, new_period: int) -> bool:
        """Set the period_ms_ value in a file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pattern to match: const uint32_t period_ms_ = <value>;
            pattern = r'(const\s+uint32_t\s+period_ms_\s*=\s*)(\d+)(\s*;)'
            
            def replace_func(match):
                return f"{match.group(1)}{new_period}{match.group(3)}"
            
            new_content = re.sub(pattern, replace_func, content)
            
            if new_content == content:
                print(f"  WARNING: No period_ms_ found in {file_path}")
                return False
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
        except Exception as e:
            print(f"ERROR updating {file_path}: {e}")
            return False
    
    def get_file_display_name(self, file_path: str) -> str:
        """Get a short display name for the file."""
        # Extract the IDL name from path like: IDL/CoreData3_idl_generated/CoreData3PublisherApp.hpp
        parts = os.path.normpath(file_path).split(os.sep)
        for part in parts:
            if part.endswith('_idl_generated'):
                return part.replace('_idl_generated', '')
        return os.path.basename(file_path)
    
    def run_interactive(self) -> bool:
        """Run the period setter interactively, asking for each file."""
        print("=" * 60)
        print("INTERACTIVE PERIOD SETTER")
        print("=" * 60)
        print()
        
        publisher_files = self.find_publisher_header_files()
        
        if not publisher_files:
            print("ERROR: No PublisherApp.hpp files found!")
            return False
        
        print(f"Found {len(publisher_files)} PublisherApp.hpp file(s):")
        print()
        
        # Show all files with their current values
        file_info = []
        for idx, file_path in enumerate(publisher_files, 1):
            rel_path = os.path.relpath(file_path, self.project_root)
            display_name = self.get_file_display_name(file_path)
            current_period = self.get_current_period(file_path)
            
            file_info.append({
                'index': idx,
                'path': file_path,
                'rel_path': rel_path,
                'display_name': display_name,
                'current_period': current_period,
                'new_period': None
            })
            
            period_str = f"{current_period} ms" if current_period is not None else "NOT FOUND"
            print(f"  {idx}. {display_name:20s} - Current: {period_str}")
        
        print()
        print("-" * 60)
        print("Enter new period value for each file.")
        print("Press ENTER to keep current value (no change).")
        print("Type 'exit' or 'q' to finish and apply changes.")
        print("-" * 60)
        print()
        
        # Ask for each file's new period value
        for file_item in file_info:
            current_str = f"{file_item['current_period']} ms" if file_item['current_period'] is not None else "NOT FOUND"
            
            while True:
                user_input = input(f"[{file_item['index']}/{len(file_info)}] {file_item['display_name']:20s} "
                                 f"(Current: {current_str}): ").strip().lower()
                
                # Check for exit command
                if user_input in ['exit', 'q', 'quit']:
                    print("\nExit selected. Applying changes...")
                    # Mark remaining files as "skip" (None)
                    for remaining in file_info[file_info.index(file_item):]:
                        if remaining['new_period'] is None:
                            remaining['new_period'] = remaining['current_period']  # Keep current
                    return self._apply_changes(file_info)
                
                # Empty input means keep current value
                if user_input == '':
                    file_item['new_period'] = file_item['current_period']  # Keep current
                    print(f"  -> Keeping current value: {current_str}")
                    break
                
                # Try to parse as integer
                try:
                    new_period = int(user_input)
                    if new_period <= 0:
                        print("  ERROR: Period must be a positive integer! Please try again.")
                        continue
                    file_item['new_period'] = new_period
                    print(f"  -> New value: {new_period} ms")
                    break
                except ValueError:
                    print("  ERROR: Invalid value! Enter a positive integer or press ENTER.")
                    continue
        
        # All files processed, apply changes
        print()
        print("All files processed. Applying changes...")
        return self._apply_changes(file_info)
    
    def _apply_changes(self, file_info: List[dict]) -> bool:
        """Apply the changes to files."""
        print()
        print("=" * 60)
        print("APPLYING CHANGES")
        print("=" * 60)
        print()
        
        success_count = 0
        skipped_count = 0
        
        for file_item in file_info:
            rel_path = file_item['rel_path']
            current_period = file_item['current_period']
            new_period = file_item['new_period']
            
            if new_period is None:
                print(f"SKIPPED: {rel_path} (no value specified)")
                skipped_count += 1
                continue
            
            if new_period == current_period:
                print(f"UNCHANGED: {rel_path} - {current_period} ms (no change)")
                success_count += 1
                continue
            
            if current_period is None:
                print(f"ERROR: {rel_path} - period_ms_ not found!")
                continue
            
            print(f"UPDATING: {rel_path}")
            print(f"  {current_period} ms -> {new_period} ms")
            
            if self.set_period(file_item['path'], new_period):
                print(f"  ✓ Success")
                success_count += 1
            else:
                print(f"  ✗ FAILED")
            print()
        
        print("-" * 60)
        print(f"Result: {success_count} file(s) updated, {skipped_count} file(s) skipped")
        print("-" * 60)
        
        return success_count > 0
    
    def run(self, new_period: int) -> bool:
        """Run the period setter for all publisher files with a single value."""
        print(f"Setting period_ms_ to {new_period} ms")
        print("-" * 60)
        
        publisher_files = self.find_publisher_header_files()
        
        if not publisher_files:
            print("ERROR: No PublisherApp.hpp files found!")
            return False
        
        print(f"Found {len(publisher_files)} PublisherApp.hpp file(s):")
        for f in publisher_files:
            print(f"  - {os.path.relpath(f, self.project_root)}")
        print()
        
        success_count = 0
        for file_path in publisher_files:
            rel_path = os.path.relpath(file_path, self.project_root)
            current_period = self.get_current_period(file_path)
            
            if current_period is not None:
                print(f"Updating {rel_path}:")
                print(f"  Current period: {current_period} ms")
                
                if self.set_period(file_path, new_period):
                    print(f"  New period: {new_period} ms")
                    success_count += 1
                else:
                    print(f"  FAILED to update")
            else:
                print(f"WARNING: Could not find period_ms_ in {rel_path}")
            print()
        
        print("-" * 60)
        print(f"Successfully updated {success_count}/{len(publisher_files)} file(s)")
        
        return success_count == len(publisher_files)


def main():
    """Main entry point."""
    setter = PeriodSetter()
    
    # If period is provided as argument, use non-interactive mode
    if len(sys.argv) >= 2:
        try:
            new_period = int(sys.argv[1])
            if new_period <= 0:
                print("ERROR: Period must be a positive integer!")
                sys.exit(1)
            success = setter.run(new_period)
            sys.exit(0 if success else 1)
        except ValueError:
            print("ERROR: Period must be a valid integer!")
            print("Usage: python3 set_period.py [period_in_ms]")
            print("       (without argument: interactive mode)")
            sys.exit(1)
    else:
        # Interactive mode
        success = setter.run_interactive()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

