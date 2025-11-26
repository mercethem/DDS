#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Secure DDS Certificate Manager - PC-Specific PKI System
This script creates and manages unique certificates for each PC.
"""

import os
import sys
import subprocess
import socket
import time
from pathlib import Path
from datetime import datetime, timedelta

class SecureCertificateManager:
    def __init__(self):
        """Initialize the Secure Certificate Manager class."""
        
        # Automatically detect PC name
        self.pc_name = self._detect_pc_name()
        print(f"🖥️  PC Name: {self.pc_name}")
        
        # Dynamic path detection
        self.project_root = self._detect_project_root()
        self.secure_dds_path = Path(self.project_root) / "secure_dds"
        # certs folder is no longer used - secure_dds system is used
        # self.certs_path = Path(self.project_root) / "certs"
        
        # PC-specific certificate paths
        self.pc_cert_path = self.secure_dds_path / "participants" / self.pc_name
        self.pc_key_file = self.pc_cert_path / f"{self.pc_name}_key.pem"
        self.pc_cert_file = self.pc_cert_path / f"{self.pc_name}_cert.pem"
        
        # CA paths
        self.ca_cert_file = self.secure_dds_path / "CA" / "mainca_cert.pem"
        self.ca_key_file = self.secure_dds_path / "CA" / "private" / "mainca_key.pem"
        
        # Working in secure_dds/ system - certs/ folder is no longer used
        # Only PC-specific certificates in secure_dds/ folder
        
        # Statistics
        self.stats = {
            'pc_name': self.pc_name,
            'certificate_created': False,
            'certificate_copied': False,
            'errors': []
        }
    
    def _detect_pc_name(self):
        """Automatically detect PC name."""
        try:
            return socket.gethostname()
        except:
            return "UNKNOWN_PC"
    
    def _detect_project_root(self):
        """Dynamically detects the project root directory."""
        try:
            script_dir = Path(__file__).parent
        except NameError:
            script_dir = Path.cwd()
        
        current_dir = script_dir
        
        # Walk up the directory tree to find project root
        # Project root contains both "IDL" and "scenarios" directories
        while current_dir != current_dir.parent:
            if (current_dir / "IDL").exists() and (current_dir / "scenarios").exists():
                return str(current_dir.absolute())
            current_dir = current_dir.parent
        
        # Fallback: if in scripts/py, go up two directories
        if script_dir.name == 'py' and script_dir.parent.name == 'scripts':
            project_root = script_dir.parent.parent
        # If in scripts/bat or scripts/sh, go up two directories
        elif script_dir.name in ['bat', 'sh'] and script_dir.parent.name == 'scripts':
            project_root = script_dir.parent.parent
        # If in scripts folder, go up one directory
        elif script_dir.name == 'scripts':
            project_root = script_dir.parent
        # If in init/sh or init/bat, go up one directory
        elif script_dir.name in ['sh', 'bat'] and script_dir.parent.name == 'init':
            project_root = script_dir.parent.parent
        # Fallback to current directory
        else:
            project_root = Path.cwd()
        
        return str(project_root.absolute())
    
    def _create_root_ca(self):
        """Create Root CA from scratch."""
        try:
            # Create CA configuration file
            ca_config_content = """[ ca ]
default_ca = CA_default

[ CA_default ]
dir               = ./secure_dds/CA
certs             = $dir/certs
crl_dir           = $dir/crl
new_certs_dir     = $dir/newcerts
database          = $dir/index.txt
serial            = $dir/serial
RANDFILE          = $dir/private/.rand

private_key       = $dir/private/mainca_key.pem
certificate       = $dir/mainca_cert.pem

crlnumber         = $dir/crlnumber
crl               = $dir/crl/mainca_crl.pem
crl_extensions    = crl_ext
default_crl_days  = 30

default_md       = sha256
name_opt         = ca_default
cert_opt         = ca_default
default_days     = 99999
preserve         = no
policy           = policy_strict

[ policy_strict ]
countryName             = match
stateOrProvinceName     = match
organizationName        = match
organizationalUnitName = optional
commonName              = supplied
emailAddress            = optional

[ req ]
default_bits        = 4096
distinguished_name  = req_distinguished_name
string_mask         = utf8only
default_md          = sha256
x509_extensions     = v3_ca

[ req_distinguished_name ]
countryName                     = Country Name (2 letter code) [US]
stateOrProvinceName             = State or Province Name [California]
localityName                    = Locality Name [San Francisco]
0.organizationName              = Organization Name [DDS Security System]
organizationalUnitName          = Organizational Unit Name [Military Applications]
commonName                      = Common Name [DDS Root CA]
emailAddress                     = Email Address [admin@dds-security.local]

[ v3_ca ]
subjectKeyIdentifier = hash
authorityKeyIdentifier = keyid:always,issuer
basicConstraints = critical, CA:true
keyUsage = critical, digitalSignature, cRLSign, keyCertSign
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = DDS Root CA
DNS.2 = dds-security.local
DNS.3 = *.dds-security.local"""
            
            ca_config_file = self.secure_dds_path / "CA" / "maincaconf.cnf"
            with open(ca_config_file, 'w', encoding='utf-8') as f:
                f.write(ca_config_content)
            
            # Create app configuration file
            app_config_content = """[ req ]
default_bits        = 4096
distinguished_name  = req_distinguished_name
string_mask         = utf8only
default_md          = sha256
x509_extensions     = v3_req
prompt              = no

[ req_distinguished_name ]
countryName                     = TR
stateOrProvinceName             = Istanbul
localityName                    = Istanbul
0.organizationName              = DDS Security System
organizationalUnitName          = Military Applications
commonName                      = DDS Participant
emailAddress                     = participant@dds-security.local

[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = nonRepudiation, digitalSignature, keyEncipherment
subjectAltName = @alt_names

[ alt_names ]
DNS.1 = DDS Participant
DNS.2 = participant.dds-security.local
DNS.3 = *.participant.dds-security.local
IP.1 = 127.0.0.1
IP.2 = ::1"""
            
            app_config_file = self.secure_dds_path / "appconf.cnf"
            with open(app_config_file, 'w', encoding='utf-8') as f:
                f.write(app_config_content)
            
            # Create CA private key
            subprocess.run([
                "openssl", "genrsa", "-out", str(self.ca_key_file), "4096"
            ], check=True, capture_output=True)
            print(f"✅ CA private key created: {self.ca_key_file}")
            
            # Create CA certificate
            # Note: -startdate parameter may be incompatible with openssl req in OpenSSL 3.x
            # System time is used - if system time is incorrect, certificate may be invalid
            # Therefore, we wait a few seconds after creating the certificate (for time synchronization)
            try:
                result = subprocess.run([
                    "openssl", "req", "-new", "-x509", "-days", "99999",
                    "-key", str(self.ca_key_file), "-sha256", "-extensions", "v3_ca",
                    "-out", str(self.ca_cert_file), "-config", str(ca_config_file),
                    "-subj", "/C=TR/ST=Istanbul/L=Istanbul/O=DDS Security System/OU=Military Applications/CN=DDS Root CA/emailAddress=admin@dds-security.local"
                ], check=True, capture_output=True, text=True)
                
                # Short wait after certificate creation (for time synchronization)
                # This helps prevent "certificate is not yet valid" errors
                time.sleep(1)
                
                print(f"    ✓ CA certificate created (start: now, end: 99999 days later)")
            except subprocess.CalledProcessError as e:
                error_detail = e.stderr if e.stderr else str(e)
                print(f"    ❌ CA certificate creation error: {error_detail}")
                if e.stdout:
                    print(f"    STDOUT: {e.stdout}")
                raise
            print(f"✅ CA certificate created: {self.ca_cert_file}")
            
            # Create CA database files
            (self.secure_dds_path / "CA" / "serial").write_text("1000")
            (self.secure_dds_path / "CA" / "index.txt").write_text("")
            
            return True
            
        except Exception as e:
            error_msg = f"Root CA creation error: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def create_pc_specific_certificate(self):
        """Create unique certificate for this PC."""
        print(f"🔐 Creating unique certificate for {self.pc_name}...")
        
        try:
            # Create Secure DDS structure from scratch
            self.secure_dds_path.mkdir(parents=True, exist_ok=True)
            (self.secure_dds_path / "CA").mkdir(parents=True, exist_ok=True)
            (self.secure_dds_path / "CA" / "private").mkdir(parents=True, exist_ok=True)
            (self.secure_dds_path / "participants").mkdir(parents=True, exist_ok=True)
            
            # Create PC folder
            self.pc_cert_path.mkdir(parents=True, exist_ok=True)
            
            # Create Root CA if it doesn't exist
            if not self.ca_cert_file.exists() or not self.ca_key_file.exists():
                print("🏛️  Creating Root CA...")
                self._create_root_ca()
            
            # Create private key
            if not self.pc_key_file.exists():
                print(f"🔑 Creating private key for {self.pc_name}...")
                subprocess.run([
                    "openssl", "genrsa", "-out", str(self.pc_key_file), "4096"
                ], check=True, capture_output=True)
                print(f"✅ Private key created: {self.pc_key_file}")
            
            # Create Certificate Signing Request (CSR)
            csr_file = self.pc_cert_path / f"{self.pc_name}.csr"
            if not csr_file.exists():
                print(f"📝 Creating certificate request for {self.pc_name}...")
                subprocess.run([
                    "openssl", "req", "-new", "-key", str(self.pc_key_file),
                    "-out", str(csr_file), "-config", str(self.secure_dds_path / "appconf.cnf"),
                    "-subj", f"/C=TR/ST=Istanbul/L=Istanbul/O=DDS Security System/OU=Military Applications/CN={self.pc_name}_Participant/emailAddress={self.pc_name.lower()}@dds-security.local"
                ], check=True, capture_output=True)
                print(f"✅ Certificate request created: {csr_file}")
            
            # Create certificate (signed with Root CA)
            if not self.pc_cert_file.exists():
                print(f"📜 Creating certificate for {self.pc_name}...")
                # Create participant certificate
                # Note: -startdate parameter is not compatible with openssl x509 -req, so we don't use it
                # Since CA certificate already starts from valid date, participant certificate will also be valid
                try:
                    result = subprocess.run([
                        "openssl", "x509", "-req", "-in", str(csr_file),
                        "-CA", str(self.ca_cert_file), "-CAkey", str(self.ca_key_file),
                        "-CAcreateserial", "-out", str(self.pc_cert_file),
                        "-days", "99999", "-sha256", "-extensions", "v3_req",
                        "-extfile", str(self.secure_dds_path / "appconf.cnf")
                    ], check=True, capture_output=True, text=True)
                    print(f"✅ Certificate created: {self.pc_cert_file}")
                except subprocess.CalledProcessError as e:
                    print(f"❌ Certificate creation error: {e.stderr if e.stderr else e}")
                    if e.stderr:
                        print(f"   Detail: {e.stderr}")
                    raise
            
            self.stats['certificate_created'] = True
            return True
            
        except subprocess.CalledProcessError as e:
            # Since we use text=True, stderr is already a string, no need to decode
            error_detail = e.stderr if e.stderr else str(e)
            error_msg = f"Certificate creation error: {error_detail}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def create_security_documents_in_secure_dds(self):
        """Create security documents in secure_dds/ system."""
        print(f"📁 Creating security documents for {self.pc_name} in secure_dds/ system...")
        
        try:
            # Create PC-specific security documents
            pc_security_dir = self.pc_cert_path / "security"
            pc_security_dir.mkdir(exist_ok=True)
            
            # Create Governance XML
            governance_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<dds xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
     xsi:noNamespaceSchemaLocation="http://www.omg.org/spec/DDS-SECURITY/20170901/omg_shared_security_governance.xsd">
  <domain_access_rules>
    <domain_rule>
      <domains>
        <id>0</id>
      </domains>
      <allow_unauthenticated_participants>false</allow_unauthenticated_participants>
      <enable_join_access_control>true</enable_join_access_control>
      <discovery_protection_kind>ENCRYPT</discovery_protection_kind>
      <liveliness_protection_kind>ENCRYPT</liveliness_protection_kind>
      <rtps_protection_kind>ENCRYPT</rtps_protection_kind>
      <topic_access_rules>
        <topic_rule>
          <topic_expression>*</topic_expression>
          <enable_discovery_protection>true</enable_discovery_protection>
          <enable_liveliness_protection>true</enable_liveliness_protection>
          <enable_read_access_control>true</enable_read_access_control>
          <enable_write_access_control>true</enable_write_access_control>
          <metadata_protection_kind>ENCRYPT</metadata_protection_kind>
          <data_protection_kind>ENCRYPT</data_protection_kind>
        </topic_rule>
      </topic_access_rules>
    </domain_rule>
  </domain_access_rules>
</dds>"""
            
            governance_file = pc_security_dir / "governance.xml"
            with open(governance_file, 'w', encoding='utf-8') as f:
                f.write(governance_content)
            print(f"✅ Governance XML created: {governance_file}")
            
            # Create Permissions XML
            permissions_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<dds xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:noNamespaceSchemaLocation="http://www.omg.org/spec/DDS-SECURITY/20170901/omg_shared_security_permissions.xsd">
  <permissions>
    <grant name="{self.pc_name}_Permissions">
      <subject_name>CN={self.pc_name}_Participant</subject_name>
      <validity>
        <not_before>2024-01-01T00:00:00</not_before>
        <not_after>2099-12-31T23:59:59</not_after>
      </validity>
      <allow_rule>
        <domains>
          <id>0</id>
        </domains>
        <publish>
          <topics>
            <topic>CoreData</topic>
            <topic>Intelligence</topic>
            <topic>Messaging</topic>
          </topics>
        </publish>
        <subscribe>
          <topics>
            <topic>CoreData</topic>
            <topic>Intelligence</topic>
            <topic>Messaging</topic>
          </topics>
        </subscribe>
      </allow_rule>
    </grant>
  </permissions>
</dds>"""
            
            permissions_file = pc_security_dir / "permissions.xml"
            with open(permissions_file, 'w', encoding='utf-8') as f:
                f.write(permissions_content)
            print(f"✅ Permissions XML created: {permissions_file}")
            
            # Sign security documents
            self.sign_documents()
            
            self.stats['certificate_copied'] = True
            return True
            
        except Exception as e:
            error_msg = f"Security documents creation error: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def generate_security_documents(self):
        """Create security documents (governance.xml, permissions.xml)."""
        print("📋 Creating security documents...")
        
        try:
            # Create Governance XML
            governance_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<dds xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" 
     xsi:noNamespaceSchemaLocation="http://www.omg.org/spec/DDS-SECURITY/20170901/omg_shared_security_governance.xsd">
  <domain_access_rules>
    <domain_rule>
      <domains>
        <id>0</id>
      </domains>
      <allow_unauthenticated_participants>false</allow_unauthenticated_participants>
      <enable_join_access_control>true</enable_join_access_control>
      <discovery_protection_kind>ENCRYPT</discovery_protection_kind>
      <liveliness_protection_kind>ENCRYPT</liveliness_protection_kind>
      <rtps_protection_kind>ENCRYPT</rtps_protection_kind>
      <topic_access_rules>
        <topic_rule>
          <topic_expression>*</topic_expression>
          <enable_discovery_protection>true</enable_discovery_protection>
          <enable_liveliness_protection>true</enable_liveliness_protection>
          <enable_read_access_control>true</enable_read_access_control>
          <enable_write_access_control>true</enable_write_access_control>
          <metadata_protection_kind>ENCRYPT</metadata_protection_kind>
          <data_protection_kind>ENCRYPT</data_protection_kind>
        </topic_rule>
      </topic_access_rules>
    </domain_rule>
  </domain_access_rules>
</dds>"""
            
            governance_file = self.pc_cert_path / "security" / "governance.xml"
            with open(governance_file, 'w', encoding='utf-8') as f:
                f.write(governance_content)
            print(f"✅ Governance XML created: {governance_file}")
            
            # Create Permissions XML
            permissions_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<dds xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
     xsi:noNamespaceSchemaLocation="http://www.omg.org/spec/DDS-SECURITY/20170901/omg_shared_security_permissions.xsd">
  <permissions>
    <grant name="{self.pc_name}_Permissions">
      <subject_name>CN={self.pc_name}_Participant</subject_name>
      <validity>
        <not_before>2024-01-01T00:00:00</not_before>
        <not_after>2099-12-31T23:59:59</not_after>
      </validity>
      <allow_rule>
        <domains>
          <id>0</id>
        </domains>
        <publish>
          <topics>
            <topic>CoreData</topic>
            <topic>Intelligence</topic>
            <topic>Messaging</topic>
          </topics>
        </publish>
        <subscribe>
          <topics>
            <topic>CoreData</topic>
            <topic>Intelligence</topic>
            <topic>Messaging</topic>
          </topics>
        </subscribe>
      </allow_rule>
    </grant>
  </permissions>
</dds>"""
            
            permissions_file = self.pc_cert_path / "security" / "permissions.xml"
            with open(permissions_file, 'w', encoding='utf-8') as f:
                f.write(permissions_content)
            print(f"✅ Permissions XML created: {permissions_file}")
            
            return True
            
        except Exception as e:
            error_msg = f"Security documents creation error: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def sign_documents(self):
        """Sign security documents."""
        print("✍️  Signing security documents...")
        
        try:
            # Sign Governance
            governance_file = self.pc_cert_path / "security" / "governance.xml"
            governance_signed = self.pc_cert_path / "security" / "governance.p7s"
            
            if governance_file.exists():
                subprocess.run([
                    "openssl", "smime", "-sign", "-in", str(governance_file),
                    "-out", str(governance_signed), "-signer", str(self.pc_cert_file),
                    "-inkey", str(self.pc_key_file), "-outform", "DER"
                ], check=True, capture_output=True)
                print(f"✅ Governance signed: {governance_signed}")
            
            # Sign Permissions
            permissions_file = self.pc_cert_path / "security" / "permissions.xml"
            permissions_signed = self.pc_cert_path / "security" / "permissions.p7s"
            
            if permissions_file.exists():
                subprocess.run([
                    "openssl", "smime", "-sign", "-in", str(permissions_file),
                    "-out", str(permissions_signed), "-signer", str(self.pc_cert_file),
                    "-inkey", str(self.pc_key_file), "-outform", "DER"
                ], check=True, capture_output=True)
                print(f"✅ Permissions signed: {permissions_signed}")
            
            return True
            
        except subprocess.CalledProcessError as e:
            error_msg = f"Document signing error: {e.stderr.decode()}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            print(f"❌ {error_msg}")
            self.stats['errors'].append(error_msg)
            return False
    
    def run(self):
        """Run the main process flow."""
        print("🔐 Starting Secure DDS Certificate Manager...")
        print("=" * 60)
        
        # 1. Create PC-specific certificate
        if not self.create_pc_specific_certificate():
            return False
        
        # 2. Create security documents in secure_dds/ system
        if not self.create_security_documents_in_secure_dds():
            return False
        
        # 5. Result report
        print("=" * 60)
        print("🎉 Secure DDS Certificate Manager completed!")
        print(f"🖥️  PC: {self.pc_name}")
        print(f"📁 Certificate path: {self.pc_cert_path}")
        print(f"📁 Secure DDS path: {self.secure_dds_path}")
        print(f"✅ Certificate created: {self.stats['certificate_created']}")
        print(f"✅ Certificate copied: {self.stats['certificate_copied']}")
        
        if self.stats['errors']:
            print(f"⚠️  Errors: {len(self.stats['errors'])}")
            for error in self.stats['errors']:
                print(f"   - {error}")
        
        return True

if __name__ == "__main__":
    manager = SecureCertificateManager()
    success = manager.run()
    sys.exit(0 if success else 1)
