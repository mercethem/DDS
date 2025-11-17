#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DDS Security Patcher - Cross-Platform PC-Specific PKI System
This script applies security settings using unique certificates for each PC.
Works on Windows and Linux systems.
"""

import os
import re
import glob
import platform
from pathlib import Path
from typing import Tuple

class DDSSecurityPatcher:
    def __init__(self):
        """Initialize the DDS Security Patcher class."""
        
        # Operating system detection
        self.os_type = platform.system().lower()  # 'windows', 'linux', 'darwin'
        
        # Dynamic path detection
        self.project_root = self._detect_project_root()
        self.secure_dds_path = Path(self.project_root) / "secure_dds"
        
        # Detect PC name
        self.pc_name = self._detect_pc_name()
        self.pc_cert_path = self.secure_dds_path / "participants" / self.pc_name
        
        # Cross-platform path handling for C++ escape sequences
        self._setup_security_paths()
        
        # Security plugins
        self.security_plugins = {
            'auth_plugin': 'builtin.PKI-DH',
            'access_plugin': 'builtin.Access-Permissions',
            'crypto_plugin': 'builtin.AES-GCM-GMAC'
        }
        
        # Security properties
        self.security_properties = {
            'auth_plugin': 'dds.sec.auth.plugin',
            'access_plugin': 'dds.sec.access.plugin',
            'crypto_plugin': 'dds.sec.crypto.plugin',
            'identity_ca': 'dds.sec.auth.builtin.PKI-DH.identity_ca',
            'identity_certificate': 'dds.sec.auth.builtin.PKI-DH.identity_certificate',
            'private_key': 'dds.sec.auth.builtin.PKI-DH.private_key',
            'governance': 'dds.sec.access.builtin.Access-Permissions.governance',
            'permissions': 'dds.sec.access.builtin.Access-Permissions.permissions',
            'permissions_ca': 'dds.sec.access.builtin.Access-Permissions.permissions_ca'
        }
        
        # Encryption settings
        self.encryption_properties = {
            'payload_protection': 'rtps.payload_protection',
            'encrypt_value': 'ENCRYPT'
        }
        
        # Processing statistics
        self.stats = {
            'files_processed': 0,
            'participants_secured': 0,
            'writers_secured': 0,
            'readers_secured': 0,
            'errors': []
        }
    
    def _setup_security_paths(self):
        """Cross-platform security path configuration."""
        if self.os_type == 'windows':
            # Windows: Use backslashes and escape for C++
            secure_dds_path_escaped = str(self.secure_dds_path).replace('\\', '\\\\')
            pc_cert_path_escaped = str(self.pc_cert_path).replace('\\', '\\\\')
        else:
            # Linux/Unix: Use forward slashes (no escaping needed)
            secure_dds_path_escaped = str(self.secure_dds_path).replace('\\', '/')
            pc_cert_path_escaped = str(self.pc_cert_path).replace('\\', '/')
        
        self.security_config = {
            'IDENTITY_CA_CERT': f'"file://{secure_dds_path_escaped}/CA/mainca_cert.pem"',
            'PARTICIPANT_CERT': f'"file://{pc_cert_path_escaped}/{self.pc_name}_cert.pem"',
            'PRIVATE_KEY': f'"file://{pc_cert_path_escaped}/{self.pc_name}_key.pem"',
            'GOVERNANCE_DOC': f'"file://{pc_cert_path_escaped}/security/governance.xml"',
            'PERMISSIONS_DOC': f'"file://{pc_cert_path_escaped}/security/permissions.p7s"',
            'PERMISSIONS_CA_CERT': f'"file://{secure_dds_path_escaped}/CA/mainca_cert.pem"'
        }
    
    def _detect_project_root(self) -> str:
        """Dynamically detect project root directory - Cross-platform."""
        current_dir = Path.cwd()
        
        # If in scripts/py folder, go up two directories
        if current_dir.name == 'py' and current_dir.parent.name == 'scripts':
            project_root = current_dir.parent.parent
        # If in scripts/bat or scripts/sh folder, go up two directories
        elif current_dir.name in ['bat', 'sh'] and current_dir.parent.name == 'scripts':
            project_root = current_dir.parent.parent
        # If in scripts folder, go up one directory
        elif current_dir.name == 'scripts':
            project_root = current_dir.parent
        else:
            project_root = current_dir
        
        return str(project_root.absolute())
    
    def _detect_pc_name(self):
        """Automatically detect PC name."""
        try:
            import socket
            return socket.gethostname()
        except:
            return "UNKNOWN_PC"
    
    def check_portability(self) -> bool:
        """Check project portability."""
        print("🔍 Checking portability...")
        
        # Check required folders
        required_dirs = ['secure_dds', 'IDL', 'docs']
        for dir_name in required_dirs:
            dir_path = Path(self.project_root) / dir_name
            if not dir_path.exists():
                print(f"❌ Required folder not found: {dir_name}")
                return False
        
        # Check PC-specific certificate files
        cert_files = [
            f'secure_dds/CA/mainca_cert.pem',
            f'secure_dds/participants/{self.pc_name}/{self.pc_name}_cert.pem',
            f'secure_dds/participants/{self.pc_name}/{self.pc_name}_key.pem',
            f'secure_dds/participants/{self.pc_name}/security/governance.xml',
            f'secure_dds/participants/{self.pc_name}/security/permissions.xml'
        ]
        
        for cert_file in cert_files:
            file_path = Path(self.project_root) / cert_file
            if not file_path.exists():
                print(f"❌ Certificate file not found: {cert_file}")
                return False
        
        print("✅ Project structure is portable")
        return True
    
    def find_generated_folders(self, root_dir: str = "../../IDL") -> list:
        """Find IDL generated folders."""
        folders = []
        search_path = Path(self.project_root) / "IDL"
        
        if search_path.exists():
            for folder in search_path.glob("*_idl_generated"):
                if folder.is_dir():
                    folders.append(str(folder))
        
        return folders
    
    def _remove_access_control_lines(self, content: str) -> str:
        """Clear existing Access Control lines."""
        import re
        
        # Remove Access Control plugin line
        content = re.sub(r'\s*pqos\.properties\(\)\.properties\(\)\.emplace_back\("dds\.sec\.access\.plugin", "builtin\.Access-Permissions"\);\s*\n?', '', content)
        
        # Remove Governance and Permissions lines
        content = re.sub(r'\s*// Governance and Permissions Documents\s*\n', '', content)
        content = re.sub(r'\s*pqos\.properties\(\)\.properties\(\)\.emplace_back\("dds\.sec\.access\.builtin\.Access-Permissions\.governance", "[^"]*"\);\s*\n?', '', content)
        content = re.sub(r'\s*pqos\.properties\(\)\.properties\(\)\.emplace_back\("dds\.sec\.access\.builtin\.Access-Permissions\.permissions", "[^"]*"\);\s*\n?', '', content)
        content = re.sub(r'\s*pqos\.properties\(\)\.properties\(\)\.emplace_back\("dds\.sec\.access\.builtin\.Access-Permissions\.permissions_ca", "[^"]*"\);\s*\n?', '', content)
        
        return content
    
    def _remove_duplicate_dynamic_code(self, content: str) -> Tuple[str, bool]:
        """Cleans duplicate dynamic code blocks."""
        modified = False
        
        # Count resolve_dds_root lambda
        resolve_dds_root_count = content.count("auto resolve_dds_root = []() -> std::filesystem::path {")
        
        # If more than one exists, keep the first and remove others
        if resolve_dds_root_count > 1:
            print(f"    🔧 {resolve_dds_root_count} duplicate dynamic code blocks detected, cleaning...")
            
            # Find end of first block (after dds_root = resolve_dds_root() line)
            # Capture complete dynamic code block: from resolve_dds_root to dds_root variable
            # More flexible pattern: flexible with comment lines, spaces, etc.
            pattern = r'(?:^|\n)\s*(?://\s*Resolve DDS root directory dynamically.*?\n\s*)?auto resolve_dds_root\s*=\s*\[\]\(\)\s*->\s*std::filesystem::path\s*\{[^}]*\};\s*\n\s*\n\s*(?://\s*Detect hostname dynamically.*?\n\s*)?char hostname\[256\]\s*=\s*\{0\};\s*\n\s*if\s*\(gethostname\(hostname[^)]*\)\s*!=\s*0\)\s*\{[^}]*\}\s*\n\s*std::string participant_dir\s*=\s*std::string\(hostname\);\s*\n\s*\n\s*const std::filesystem::path dds_root\s*=\s*resolve_dds_root\(\);\s*\n'
            
            matches = list(re.finditer(pattern, content, re.DOTALL | re.MULTILINE))
            
            if len(matches) > 1:
                # Keep first block, remove others (starting from the end)
                for match in reversed(matches[1:]):  # All except first
                    # Also clean newline at start of match
                    start = match.start()
                    if start > 0 and content[start-1] == '\n':
                        start -= 1
                    content = content[:start] + content[match.end():]
                modified = True
                print(f"    ✓ {len(matches) - 1} duplicate dynamic code blocks cleaned")
        
        return content, modified
    
    def _ensure_dynamic_path_includes(self, content: str) -> Tuple[str, bool]:
        """Adds required includes (filesystem, unistd.h, cstring)."""
        modified = False
        # Check includes
        needs_filesystem = "#include <filesystem>" not in content
        needs_unistd = "#include <unistd.h>" not in content
        needs_cstring = "#include <cstring>" not in content
        
        if needs_filesystem or needs_unistd or needs_cstring:
            # Find last include (usually after fastdds or json includes)
            include_pattern = r'(#include\s+["<][^">]+[">])'
            matches = list(re.finditer(include_pattern, content))
            
            if matches:
                # Add after last include
                last_include_pos = matches[-1].end()
                additional_includes = []
                
                if needs_filesystem:
                    additional_includes.append("#include <filesystem>")
                if needs_unistd:
                    additional_includes.append("#include <unistd.h>")
                if needs_cstring:
                    additional_includes.append("#include <cstring>")
                
                if additional_includes:
                    content = content[:last_include_pos] + "\n" + "\n".join(additional_includes) + content[last_include_pos:]
                    modified = True
                    print("    ➕ Required includes for dynamic path added")
        
        return content, modified
    
    def add_security_to_participant(self, content: str) -> Tuple[str, bool]:
        """Adds or updates security settings to DomainParticipant QoS."""
        modified = False
        
        # Access Control disabled - perform cleanup
        content = self._remove_access_control_lines(content)
        
        # First clean duplicate dynamic code blocks
        content, duplicate_removed = self._remove_duplicate_dynamic_code(content)
        if duplicate_removed:
            modified = True
        
        # Add required includes for dynamic path resolution
        content, includes_modified = self._ensure_dynamic_path_includes(content)
        if includes_modified:
            modified = True
        
        # Add dynamic path resolution code (at constructor start)
        # Add Resolve DDS root and hostname code
        dynamic_path_code = """
    // Resolve DDS root directory dynamically (portable across PCs)
    auto resolve_dds_root = []() -> std::filesystem::path {
        if (const char* env_root = std::getenv("DDS_ROOT")) {
            std::filesystem::path p(env_root);
            if (std::filesystem::exists(p)) return p;
        }
        // Walk upwards from current directory to find repo root (has secure_dds and IDL)
        std::filesystem::path cur = std::filesystem::current_path();
        for (int i = 0; i < 6 && !cur.empty(); ++i) {
            if (std::filesystem::exists(cur / "secure_dds") && std::filesystem::exists(cur / "IDL")) {
                return cur;
            }
            cur = cur.parent_path();
        }
        return std::filesystem::current_path();
    };
    
    // Detect hostname dynamically (portable across PCs)
    char hostname[256] = {0};
    if (gethostname(hostname, sizeof(hostname) - 1) != 0) {
        std::strcpy(hostname, "UNKNOWN_HOST");
    }
    std::string participant_dir = std::string(hostname);
    
    const std::filesystem::path dds_root = resolve_dds_root();
"""
        
        # First check if dynamic code block already exists (don't add again if it exists)
        if "resolve_dds_root" in content and "gethostname" in content and "participant_dir" in content:
            # Dynamic code already exists, just check security settings
            if "dds.sec.auth.plugin" in content:
                print("    ✓ Dynamic path code already exists, checking security settings...")
                # Only add security settings if missing, otherwise do nothing
                if "pqos.properties().properties().emplace_back(\"dds.sec.auth.plugin\"" not in content:
                    print("    ⚠️  Security settings appear missing but dynamic code exists - file probably already correct")
                return content, False
        
        # Replace existing certificate paths with dynamic code (if hardcoded paths exist)
        old_security_block_pattern = r'//\s*DDS Security Configuration.*?//\s*Access Control disabled.*?(?=\n\s*pqos\.name\(|$)'
        if re.search(old_security_block_pattern, content, re.DOTALL):
            # Check for hardcoded paths
            if "file:///home/" in content or "file://C:" in content or "file://C:\\\\" in content:
                # Replace existing security block with dynamic code
                new_security_code = dynamic_path_code + """
    // Create the participant
    DomainParticipantQos pqos = PARTICIPANT_QOS_DEFAULT;
    // DDS Security Configuration - Authentication + Encryption Only
    pqos.properties().properties().emplace_back("dds.sec.auth.plugin", "builtin.PKI-DH");
    // Access Control disabled to avoid permissions issues
    pqos.properties().properties().emplace_back("dds.sec.crypto.plugin", "builtin.AES-GCM-GMAC");
    
    // Certificate and Key Paths (dynamic, portable across PCs)
    const std::string uri_prefix = "file://";
    const std::filesystem::path ca_path = dds_root / "secure_dds/CA/mainca_cert.pem";
    const std::filesystem::path cert_path = dds_root / "secure_dds/participants" / participant_dir / (participant_dir + "_cert.pem");
    const std::filesystem::path key_path = dds_root / "secure_dds/participants" / participant_dir / (participant_dir + "_key.pem");
    
    pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.identity_ca", uri_prefix + ca_path.string());
    pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.identity_certificate", uri_prefix + cert_path.string());
    pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.private_key", uri_prefix + key_path.string());
    
    // Access Control disabled - no governance/permissions needed"""
                
                # Find and replace old block (preserve DomainParticipantQos line)
                old_pattern = r'(//\s*Create the participant\s*\n)?\s*DomainParticipantQos\s+pqos\s*=\s*PARTICIPANT_QOS_DEFAULT;.*?//\s*Access Control disabled.*?(?=\n\s*pqos\.name\(|$)'
                if re.search(old_pattern, content, re.DOTALL):
                    content = re.sub(old_pattern, new_security_code, content, flags=re.DOTALL)
                    modified = True
                    print("    🔄 Hardcoded certificate paths replaced with dynamic code")
                    self.stats['participants_secured'] += 1
                    return content, True
            else:
                # Dynamic code already exists but no hardcoded path, do nothing
                print("    ✓ Dynamic code already exists and appears correct")
                return content, False
        
        # If security settings don't exist, add with dynamic code
        if "dds.sec.auth.plugin" not in content:
            # Find DomainParticipantQos creation location
            participant_pattern = r'(\s*//\s*Create the participant\s*\n)?\s*(DomainParticipantQos\s+pqos\s*=\s*PARTICIPANT_QOS_DEFAULT;)'
            match = re.search(participant_pattern, content)
            
            if match:
                # Add dynamic path resolution + security properties
                security_code = dynamic_path_code + """
    // Create the participant
    DomainParticipantQos pqos = PARTICIPANT_QOS_DEFAULT;
    // DDS Security Configuration - Authentication + Encryption Only
    pqos.properties().properties().emplace_back("dds.sec.auth.plugin", "builtin.PKI-DH");
    // Access Control disabled to avoid permissions issues
    pqos.properties().properties().emplace_back("dds.sec.crypto.plugin", "builtin.AES-GCM-GMAC");
    
    // Certificate and Key Paths (dynamic, portable across PCs)
    const std::string uri_prefix = "file://";
    const std::filesystem::path ca_path = dds_root / "secure_dds/CA/mainca_cert.pem";
    const std::filesystem::path cert_path = dds_root / "secure_dds/participants" / participant_dir / (participant_dir + "_cert.pem");
    const std::filesystem::path key_path = dds_root / "secure_dds/participants" / participant_dir / (participant_dir + "_key.pem");
    
    pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.identity_ca", uri_prefix + ca_path.string());
    pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.identity_certificate", uri_prefix + cert_path.string());
    pqos.properties().properties().emplace_back("dds.sec.auth.builtin.PKI-DH.private_key", uri_prefix + key_path.string());
    
    // Access Control disabled - no governance/permissions needed"""
                
                # Add security code
                old_line = match.group(0)
                # If "Create the participant" comment doesn't exist, add it
                if "Create the participant" not in old_line:
                    new_line = security_code
                else:
                    new_line = security_code.replace("// Create the participant", match.group(1).strip() if match.group(1) else "// Create the participant")
                
                content = content.replace(old_line, new_line)
                modified = True
                self.stats['participants_secured'] += 1
        
        return content, modified
    
    def add_encryption_to_writer(self, content: str) -> Tuple[str, bool]:
        """Adds encryption settings to DataWriter QoS."""
        modified = False
        
        # First check existing encryption settings
        if "rtps.payload_protection" in content:
            print("    ⚠️  Encryption settings already exist, skipping...")
            return content, False
        
        # Find DataWriterQos creation location
        writer_pattern = r'(DataWriterQos\s+writer_qos\s*=\s*DATAWRITER_QOS_DEFAULT;)'
        match = re.search(writer_pattern, content)
        
        if match:
            # Add encryption property
            encryption_code = f"""
    // Payload Encryption Configuration
    writer_qos.properties().properties().emplace_back("{self.encryption_properties['payload_protection']}", "{self.encryption_properties['encrypt_value']}");"""
            
            # Add encryption code
            old_line = match.group(1)
            new_line = old_line + encryption_code
            content = content.replace(old_line, new_line)
            modified = True
            self.stats['writers_secured'] += 1
        
        return content, modified
    
    def add_encryption_to_reader(self, content: str) -> Tuple[str, bool]:
        """Adds encryption settings to DataReader QoS."""
        modified = False
        
        # First check existing encryption settings
        if "rtps.payload_protection" in content:
            print("    ⚠️  Encryption settings already exist, skipping...")
            return content, False
        
        # Find DataReaderQos creation location
        reader_pattern = r'(DataReaderQos\s+reader_qos\s*=\s*DATAREADER_QOS_DEFAULT;)'
        match = re.search(reader_pattern, content)
        
        if match:
            # Add encryption property
            encryption_code = f"""
    // Payload Encryption Configuration
    reader_qos.properties().properties().emplace_back("{self.encryption_properties['payload_protection']}", "{self.encryption_properties['encrypt_value']}");"""
            
            # Add encryption code
            old_line = match.group(1)
            new_line = old_line + encryption_code
            content = content.replace(old_line, new_line)
            modified = True
            self.stats['readers_secured'] += 1
        
        return content, modified
    
    def patch_cpp_file(self, file_path: str) -> bool:
        """Patches a single C++ file with security settings."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            modified = False
            
            # DomainParticipant security settings
            content, participant_modified = self.add_security_to_participant(content)
            if participant_modified:
                modified = True
            
            # DataWriter encryption settings
            content, writer_modified = self.add_encryption_to_writer(content)
            if writer_modified:
                modified = True
            
            # DataReader encryption settings
            content, reader_modified = self.add_encryption_to_reader(content)
            if reader_modified:
                modified = True
            
            # Update file
            if modified:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"✅ Security settings added: {Path(file_path).name}")
                return True
            else:
                print(f"⚠️  No changes needed: {Path(file_path).name}")
                return True
                
        except Exception as e:
            error_msg = f"File processing error {file_path}: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def run(self):
        """Run main processing flow."""
        print("🔒 Starting DDS Security Patcher...")
        print("=" * 50)
        
        # Portability check
        if not self.check_portability():
            print("❌ Portability check failed!")
            return False
        
        # Find IDL generated folders
        generated_folders = self.find_generated_folders()
        if not generated_folders:
            print("❌ No _idl_generated folders found!")
            return False
        
        print(f"📁 Found _idl_generated folders: {len(generated_folders)}")
        for folder in generated_folders:
            print(f"   - {folder}")
        
        # Process each folder
        total_files = 0
        successful_files = 0
        
        for folder_path in generated_folders:
            print(f"\n🔍 Processing: {folder_path}")
            
            # Find C++ files
            cpp_files = []
            for pattern in ['*PublisherApp.cxx', '*SubscriberApp.cxx']:
                cpp_files.extend(Path(folder_path).glob(pattern))
            
            if not cpp_files:
                print("   ⚠️  No C++ files found")
                continue
            
            print(f"📁 Found C++ files: {len(cpp_files)}")
            for cpp_file in cpp_files:
                print(f"   - {cpp_file.name}")
            
            # Process each file
            for cpp_file in cpp_files:
                total_files += 1
                if self.patch_cpp_file(str(cpp_file)):
                    successful_files += 1
                self.stats['files_processed'] += 1
        
        # Result report
        print("\n" + "=" * 50)
        print("🎉 Security patching completed!")
        print(f"📊 Successful file count: {successful_files}/{total_files}")
        print(f"🔐 Security Mode: Authentication + Encryption (Access Control disabled)")
        print(f"🏛️  Secured DomainParticipant count: {self.stats['participants_secured']}")
        print(f"📝 Secured DataWriter count: {self.stats['writers_secured']}")
        print(f"📖 Secured DataReader count: {self.stats['readers_secured']}")
        
        if self.stats['errors']:
            print(f"⚠️  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"   - {error}")
        
        return successful_files == total_files

if __name__ == "__main__":
    patcher = DDSSecurityPatcher()
    success = patcher.run()
    exit(0 if success else 1)
