#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IDL Patcher - IDL dosyalarından C++ başlık dosyalarına JSON okuma özelliği ekler
Bu betik, IDL dosyalarını analiz ederek C++ Publisher uygulamalarına JSON dosyasından veri okuma özelliği ekler.
CoreData örneği üzerinden revize edilmiştir.
"""

import os
import re
import glob
from pathlib import Path
from typing import Dict, List, Tuple, Optional

class IDLJSONPatcher:
    def __init__(self):
        """IDL JSON Patcher sınıfını başlatır."""
        # Proje kök dizinini dinamik olarak bul
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
        
        # Proje kök dizinini dinamik olarak bul
        self.project_root = self._detect_project_root()
        
        # Özel koordinat ve hız değerleri
        self.special_values = {
            'lat': '41.0082',
            'latitude': '41.0082',
            'lon': '28.9818', 
            'longitude': '28.9818',
            'alt': '30.5f',
            'altitude': '30.5f',
            'speed': '15.2f',
            'hiz': '15.2f'
        }
        
        # DDS akışı için optimize edilmiş dummy değerler
        self.dds_optimized_values = {
            'long': '1730352000L',  # Timestamp için anlamlı değer
            'unsigned long': '1730352000UL',  # Nano seconds için
            'double': '41.0082',  # Koordinat için
            'float': '30.5f',  # Altitude için
            'short': '135',  # Orientation için
            'string': '"UAV_MODUL_01"',  # Device ID için
            'boolean': 'true'  # System status için
        }
        
        # DDS veri akışı için özel değerler
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
        """IDL klasöründeki tüm *.idl dosyalarını bulur."""
        idl_files = []
        for root, dirs, files in os.walk(root_dir):
            for file in files:
                if file.endswith('.idl'):
                    idl_files.append(os.path.join(root, file))
        return idl_files

    def find_target_folder(self, idl_file: str) -> Optional[str]:
        """IDL dosyası için hedef klasörü bulur (_idl_generated sonekli)."""
        idl_name = os.path.splitext(os.path.basename(idl_file))[0]
        target_folder = f"{idl_name}_idl_generated"
        
        # IDL dosyasının bulunduğu dizinde ara
        idl_dir = os.path.dirname(idl_file)
        target_path = os.path.join(idl_dir, target_folder)
        
        if os.path.exists(target_path):
            return target_path
        
        # Ana dizinde ara
        main_target_path = os.path.join(".", target_folder)
        if os.path.exists(main_target_path):
            return main_target_path
            
        return None

    def parse_idl_file(self, idl_file: str) -> Dict[str, List[Tuple[str, str]]]:
        """IDL dosyasını parse ederek struct'ları ve üyelerini çıkarır."""
        structs = {}
        
        try:
            with open(idl_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ IDL dosyası okunamadı: {idl_file} - {e}")
            return structs

        # Struct'ları bul
        struct_pattern = r'struct\s+(\w+)\s*\{([^}]+)\}'
        matches = re.finditer(struct_pattern, content, re.DOTALL)
        
        for match in matches:
            struct_name = match.group(1)
            struct_body = match.group(2)
            
            # Struct üyelerini bul
            members = []
            # Yorum satırlarını temizle
            struct_body = re.sub(r'//.*$', '', struct_body, flags=re.MULTILINE)
            
            # Üye tanımlarını bul
            member_pattern = r'(\w+(?:\s+\w+)*)\s+(\w+);'
            member_matches = re.finditer(member_pattern, struct_body)
            
            for member_match in member_matches:
                member_type = member_match.group(1).strip()
                member_name = member_match.group(2).strip()
                members.append((member_type, member_name))
            
            structs[struct_name] = members
            
        return structs

    def find_header_file(self, target_folder: str, struct_name: str) -> Optional[str]:
        """Hedef klasörde struct için C++ başlık dosyasını bulur."""
        # Ana başlık dosyasını ara
        header_files = glob.glob(os.path.join(target_folder, "*.hpp"))
        if not header_files:
            header_files = glob.glob(os.path.join(target_folder, "*.h"))
        
        if header_files:
            return header_files[0]  # İlk bulunan başlık dosyasını döndür
        
        return None

    def find_app_files(self, target_folder: str) -> Dict[str, str]:
        """Hedef klasörde Publisher/Subscriber uygulama dosyalarını bulur."""
        app_files = {}
        
        # Publisher dosyasını bul
        publisher_files = glob.glob(os.path.join(target_folder, "*PublisherApp.cxx"))
        if publisher_files:
            app_files['publisher'] = publisher_files[0]
        
        # Subscriber dosyasını bul
        subscriber_files = glob.glob(os.path.join(target_folder, "*SubscriberApp.cxx"))
        if subscriber_files:
            app_files['subscriber'] = subscriber_files[0]
        
        return app_files

    def get_dummy_value(self, member_type: str, member_name: str, module_name: str = "") -> str:
        """Üye tipi ve ismine göre dummy değer döndürür."""
        # Özel koordinat ve hız değerlerini kontrol et
        for keyword, value in self.special_values.items():
            if keyword in member_name.lower():
                return value
        
        # Temel tipler için dummy değerler
        for idl_type, dummy_value in self.dummy_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Karmaşık tipler için varsayılan constructor çağrısı
        # Struct, enum, vs. için varsayılan constructor kullan
        if module_name:
            return f"{module_name}::{member_type}()"
        else:
            return f"{member_type}()"

    def get_enhanced_dummy_value(self, member_type: str, member_name: str, module_name: str = "") -> str:
        """DDS akışı için geliştirilmiş dummy değer döndürür."""
        # Özel koordinat ve hız değerlerini kontrol et
        for keyword, value in self.special_values.items():
            if keyword in member_name.lower():
                return value
        
        # Temel tipler için dummy değerler
        for idl_type, dummy_value in self.dummy_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Karmaşık tipler için varsayılan constructor çağrısı
        # Struct, enum, vs. için varsayılan constructor kullan
        if module_name:
            return f"{module_name}::{member_type}()"
        else:
            return f"{member_type}()"

    def get_dds_optimized_dummy_value(self, member_type: str, member_name: str, module_name: str = "") -> str:
        """DDS veri akışı için optimize edilmiş dummy değer döndürür."""
        # DDS veri akışı için özel değerleri kontrol et
        for keyword, value in self.dds_flow_values.items():
            if keyword in member_name.lower():
                return value
        
        # Özel koordinat ve hız değerlerini kontrol et
        for keyword, value in self.special_values.items():
            if keyword in member_name.lower():
                return value
        
        # DDS optimize edilmiş değerleri kontrol et
        for idl_type, dummy_value in self.dds_optimized_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Temel tipler için dummy değerler
        for idl_type, dummy_value in self.dummy_values.items():
            if idl_type in member_type.lower():
                return dummy_value
        
        # Karmaşık tipler için varsayılan constructor çağrısı
        # Struct, enum, vs. için varsayılan constructor kullan
        if module_name:
            return f"{module_name}::{member_type}()"
        else:
            return f"{member_type}()"

    def patch_constructor(self, header_file: str, struct_name: str, members: List[Tuple[str, str]], module_name: str = "") -> bool:
        """C++ başlık dosyasındaki constructor'ı patch eder."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Başlık dosyası okunamadı: {header_file} - {e}")
            return False

        # Constructor'ı bul - daha basit pattern
        constructor_pattern = rf'eProsima_user_DllExport\s+{re.escape(struct_name)}\(\)\s*\{{([^}}]*)\}}'
        match = re.search(constructor_pattern, content, re.DOTALL)
        
        if not match:
            print(f"⚠️  {struct_name} constructor'ı bulunamadı")
            return False

        constructor_body = match.group(1).strip()
        
        # Eğer constructor zaten dolu ise, patch etme
        if constructor_body and not constructor_body.isspace():
            print(f"⚠️  {struct_name} constructor'ı zaten dolu, atlanıyor")
            return True

        # Yeni constructor içeriğini oluştur
        new_constructor_body = "        // Dummy değerler atanıyor\n"
        for member_type, member_name in members:
            dummy_value = self.get_enhanced_dummy_value(member_type, member_name, module_name)
            new_constructor_body += f"        m_{member_name} = {dummy_value};\n"

        # Constructor'ı güncelle - gerçek dosya formatına uygun
        old_constructor = match.group(0)  # Tam eşleşen string
        new_constructor = f"eProsima_user_DllExport {struct_name}()\n    {{\n{new_constructor_body}\n    }}"
        
        updated_content = content.replace(old_constructor, new_constructor)
        
        if updated_content == content:
            print(f"     ⚠️  Constructor değiştirilemedi - string eşleşmedi")
            return False
        
        # Dosyayı güncelle
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except Exception as e:
            print(f"❌ Başlık dosyası yazılamadı: {header_file} - {e}")
            return False

    def process_idl_file(self, idl_file: str) -> bool:
        """Tek bir IDL dosyasını işler."""
        print(f"\n🔍 İşleniyor: {idl_file}")
        
        # Hedef klasörü bul
        target_folder = self.find_target_folder(idl_file)
        if not target_folder:
            print(f"❌ Hedef klasör bulunamadı: {os.path.splitext(os.path.basename(idl_file))[0]}_idl_generated")
            return False
        
        print(f"📁 Hedef klasör: {target_folder}")
        
        # IDL dosyasını parse et
        structs = self.parse_idl_file(idl_file)
        if not structs:
            print(f"⚠️  {idl_file} dosyasında struct bulunamadı")
            return True
        
        print(f"📋 Bulunan struct'lar: {list(structs.keys())}")
        
        # Module adını bul
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
        
        # Başlık dosyasını bul
        header_file = self.find_header_file(target_folder, "CoreData")  # Ana başlık dosyası
        if not header_file:
            print(f"❌ Başlık dosyası bulunamadı")
            return False
        
        print(f"📄 Başlık dosyası: {os.path.basename(header_file)}")
        
        # Tüm struct'ların constructor'larını zorla patch et
        if self.force_patch_all_constructors(header_file, structs, module_name):
            print(f"✅ Tüm constructor'lar başarıyla patch edildi")
            success_count = total_count
        else:
            print(f"❌ Constructor'lar patch edilemedi")
        
        # Publisher/Subscriber uygulamalarını patch et
        app_files = self.find_app_files(target_folder)
        if app_files:
            print(f"\n📱 Uygulama dosyaları bulundu: {list(app_files.keys())}")
            
            # Ana struct'ı bul - modüle göre özel seçim
            if module_name == "Intelligence":
                main_struct = "TaskAssignment"
            elif module_name == "Messaging":
                main_struct = "TaskCommand"
            else:
                # Diğer modüller için en büyük struct'ı seç
                main_struct = max(structs.keys(), key=lambda x: len(structs[x]))
            
            if main_struct not in structs:
                print(f"     ⚠️  {main_struct} struct'ı bulunamadı, en büyük struct kullanılıyor")
                main_struct = max(structs.keys(), key=lambda x: len(structs[x]))
            
            main_members = structs[main_struct]
            
            # Publisher header'ını patch et
            publisher_header_file = os.path.join(target_folder, f"{module_name}PublisherApp.hpp")
            if os.path.exists(publisher_header_file):
                print(f"  🔧 Publisher header patch ediliyor: {os.path.basename(publisher_header_file)}")
                if self.patch_publisher_header(publisher_header_file, module_name):
                    print(f"     ✅ Publisher header başarıyla patch edildi")
                else:
                    print(f"     ❌ Publisher header patch edilemedi")
            
            # Publisher'ı patch et
            if 'publisher' in app_files:
                print(f"  🔧 Publisher patch ediliyor: {os.path.basename(app_files['publisher'])}")
                if self.patch_publisher_app(app_files['publisher'], main_struct, main_members, module_name):
                    print(f"     ✅ Publisher başarıyla patch edildi")
                else:
                    print(f"     ❌ Publisher patch edilemedi")
            
            # CMakeLists.txt'i patch et
            cmake_file = os.path.join(target_folder, "CMakeLists.txt")
            if os.path.exists(cmake_file):
                print(f"  🔧 CMakeLists.txt patch ediliyor")
                if self.patch_cmake_lists(cmake_file):
                    print(f"     ✅ CMakeLists.txt başarıyla patch edildi")
                else:
                    print(f"     ❌ CMakeLists.txt patch edilemedi")
            
            # Subscriber'ı patch et
            if 'subscriber' in app_files:
                print(f"  🔧 Subscriber patch ediliyor: {os.path.basename(app_files['subscriber'])}")
                if self.patch_subscriber_app(app_files['subscriber'], main_struct, main_members, module_name):
                    print(f"     ✅ Subscriber başarıyla patch edildi")
                else:
                    print(f"     ❌ Subscriber patch edilemedi")
        
        print(f"\n📊 Özet: {success_count}/{total_count} struct başarıyla işlendi")
        return success_count == total_count

    def patch_all_constructors(self, header_file: str, structs: Dict[str, List[Tuple[str, str]]], module_name: str = "") -> bool:
        """Tüm struct'ların constructor'larını patch eder."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Başlık dosyası okunamadı: {header_file} - {e}")
            return False

        updated_content = content
        success_count = 0
        
        for struct_name, members in structs.items():
            print(f"  🔧 Constructor patch ediliyor: {struct_name}")
            
            # Constructor'ı bul
            constructor_pattern = rf'eProsima_user_DllExport\s+{re.escape(struct_name)}\(\)\s*\{{([^}}]*)\}}'
            match = re.search(constructor_pattern, updated_content, re.DOTALL)
            
            if not match:
                print(f"     ⚠️  {struct_name} constructor'ı bulunamadı")
                continue

            constructor_body = match.group(1).strip()
            
            # Eğer constructor zaten dolu ise, patch etme
            if constructor_body and not constructor_body.isspace():
                print(f"     ⚠️  {struct_name} constructor'ı zaten dolu, atlanıyor")
                success_count += 1
                continue

            # Yeni constructor içeriğini oluştur
            new_constructor_body = "        // Dummy değerler atanıyor\n"
            for member_type, member_name in members:
                dummy_value = self.get_dds_optimized_dummy_value(member_type, member_name, module_name)
                new_constructor_body += f"        m_{member_name} = {dummy_value};\n"

            # Constructor'ı güncelle
            old_constructor = match.group(0)
            new_constructor = f"eProsima_user_DllExport {struct_name}()\n    {{\n{new_constructor_body}\n    }}"
            
            updated_content = updated_content.replace(old_constructor, new_constructor)
            success_count += 1
            print(f"     ✅ {struct_name} constructor patch edildi")

        # Dosyayı güncelle
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except Exception as e:
            print(f"❌ Başlık dosyası yazılamadı: {header_file} - {e}")
            return False

    def force_patch_all_constructors(self, header_file: str, structs: Dict[str, List[Tuple[str, str]]], module_name: str = "") -> bool:
        """Tüm struct'ların constructor'larını zorla patch eder (mevcut içeriği temizler)."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Başlık dosyası okunamadı: {header_file} - {e}")
            return False

        updated_content = content
        success_count = 0
        
        for struct_name, members in structs.items():
            print(f"  🔧 Constructor zorla patch ediliyor: {struct_name}")
            
            # Constructor'ı bul
            constructor_pattern = rf'eProsima_user_DllExport\s+{re.escape(struct_name)}\(\)\s*\{{([^}}]*)\}}'
            match = re.search(constructor_pattern, updated_content, re.DOTALL)
            
            if not match:
                print(f"     ⚠️  {struct_name} constructor'ı bulunamadı")
                continue

            # Yeni constructor içeriğini oluştur
            new_constructor_body = "        // Dummy değerler atanıyor\n"
            for member_type, member_name in members:
                dummy_value = self.get_dds_optimized_dummy_value(member_type, member_name, module_name)
                new_constructor_body += f"        m_{member_name} = {dummy_value};\n"

            # Constructor'ı güncelle
            old_constructor = match.group(0)
            new_constructor = f"eProsima_user_DllExport {struct_name}()\n    {{\n{new_constructor_body}\n    }}"
            
            updated_content = updated_content.replace(old_constructor, new_constructor)
            success_count += 1
            print(f"     ✅ {struct_name} constructor zorla patch edildi")

        # Dosyayı güncelle
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            return True
        except Exception as e:
            print(f"❌ Başlık dosyası yazılamadı: {header_file} - {e}")
            return False

    def patch_publisher_header(self, header_file: str, module_name: str = "") -> bool:
        """Publisher header dosyasına JSON okuma için gerekli include'ları ve member variable'ları ekler."""
        try:
            with open(header_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Header dosyası okunamadı: {header_file} - {e}")
            return False

        # Include'ları kontrol et ve ekle (duplicate kontrolü ile)
        includes_to_add = [
            '#include <fstream>',
            '#include <vector>',
            '#include <nlohmann/json.hpp>'
        ]
        
        for include in includes_to_add:
            if include not in content:
                # İlk include'dan sonra ekle
                first_include_match = re.search(r'#include\s+<[^>]+>', content)
                if first_include_match:
                    insert_pos = first_include_match.end()
                    content = content[:insert_pos] + f'\n{include}' + content[insert_pos:]
                else:
                    # Dosya başına ekle
                    content = include + '\n' + content

        # Duplicate member variable'ları temizle (daha güçlü regex)
        # Birden fazla satırda tekrarlanan member variable'ları temizle
        content = re.sub(r'std::vector<nlohmann::json> json_scenarios_;\s*\n\s*size_t current_scenario_index_;\s*\n\s*std::vector<nlohmann::json> json_scenarios_;\s*\n\s*size_t current_scenario_index_;', 
                        'std::vector<nlohmann::json> json_scenarios_;\n    size_t current_scenario_index_;', content)
        
        # Tek tek duplicate'ları temizle
        content = re.sub(r'std::vector<nlohmann::json> json_scenarios_;\s*\n\s*std::vector<nlohmann::json> json_scenarios_;', 
                        'std::vector<nlohmann::json> json_scenarios_;', content)
        content = re.sub(r'size_t current_scenario_index_;\s*\n\s*size_t current_scenario_index_;', 
                        'size_t current_scenario_index_;', content)
        
        # Duplicate loadJsonScenarios fonksiyonlarını temizle
        content = re.sub(r'void loadJsonScenarios\(\);\s*\n\s*void loadJsonScenarios\(\);', 
                        'void loadJsonScenarios();', content)
        
        # Duplicate period_ms_ temizle
        content = re.sub(r'const uint32_t period_ms_ = 1000; // in ms\s*// in ms\s*// in ms', 
                        'const uint32_t period_ms_ = 1000; // in ms', content)
        
        # Duplicate period_ms_ temizle (farklı formatlar)
        content = re.sub(r'const uint32_t period_ms_ = 1000; // in ms // in ms // 1 saniye', 
                        'const uint32_t period_ms_ = 1000; // in ms', content)
        
        # Duplicate loadJsonScenarios fonksiyonlarını temizle (farklı formatlar)
        content = re.sub(r'//! Load JSON scenarios from file\s*\n\s*void loadJsonScenarios\(\);', 
                        'void loadJsonScenarios();', content)
        
        # Duplicate JSON verileri için yorumlarını temizle
        content = re.sub(r'// JSON verileri için\s*\n\s*std::vector<nlohmann::json> json_scenarios_;\s*\n\s*size_t current_scenario_index_;', 
                        '', content)

        # Member variable'ları ekle (sadece yoksa)
        member_vars = [
            'std::vector<nlohmann::json> json_scenarios_;',
            'size_t current_scenario_index_;'
        ]
        
        # Private section'ı bul ve member variable'ları ekle
        private_pattern = r'(private:\s*\n)'
        private_match = re.search(private_pattern, content)
        
        if private_match:
            private_start = private_match.end()
            # Sadece eksik olanları ekle
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

        # loadJsonScenarios fonksiyonunu ekle (duplicate kontrolü ile)
        load_function = f'''    void loadJsonScenarios();'''
        
        if load_function not in content:
            # Public section'ı bul ve fonksiyonu ekle
            public_pattern = r'(public:\s*\n)'
            public_match = re.search(public_pattern, content)
            
            if public_match:
                public_start = public_match.end()
                content = content[:public_start] + load_function + '\n' + content[public_start:]

        # period_ms_'i 1000'e güncelle (duplicate temizleme ile)
        period_pattern = r'const uint32_t period_ms_ = \d+;.*?// in ms'
        content = re.sub(period_pattern, 'const uint32_t period_ms_ = 1000; // in ms', content)
        
        # Duplicate period_ms_ temizle
        content = re.sub(r'const uint32_t period_ms_ = 1000; // in ms\s*// in ms\s*// in ms', 
                        'const uint32_t period_ms_ = 1000; // in ms', content)

        # Dosyayı güncelle
        try:
            with open(header_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Header dosyası yazılamadı: {header_file} - {e}")
            return False

    def patch_publisher_app(self, publisher_file: str, struct_name: str, members: List[Tuple[str, str]], module_name: str = "") -> bool:
        """Publisher uygulamasını patch eder - JSON okuma özelliği ekler."""
        try:
            with open(publisher_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Publisher dosyası okunamadı: {publisher_file} - {e}")
            return False

        # Duplicate loadJsonScenarios fonksiyonlarını temizle
        load_function_pattern = rf'void {module_name}PublisherApp::loadJsonScenarios\(\)\s*\{{[^}}]*\}}'
        content = re.sub(load_function_pattern, '', content, flags=re.DOTALL)
        
        # Duplicate kod parçalarını temizle (syntax hataları için)
        # Duplicate nlohmann::json json_data; ve file >> json_data; satırlarını temizle
        duplicate_pattern = r'nlohmann::json json_data;\s*\n\s*file >> json_data;\s*\n\s*file\.close\(\);\s*\n\s*json_scenarios_ = json_data\["scenarios"\];\s*\n\s*std::cout << "JSON dosyasından " << json_scenarios_\.size\(\) << " senaryo yüklendi\." << std::endl;\s*\n\s*\}\s*\n\s*catch \(const std::exception& e\)\s*\n\s*\{\s*\n\s*std::cerr << "JSON dosyası okuma hatası: " << e\.what\(\) << std::endl;\s*\n\s*\}\s*\n\s*\}'
        content = re.sub(duplicate_pattern, '', content, flags=re.DOTALL)
        
        # Duplicate try-catch bloklarını temizle
        duplicate_try_catch = r'try\s*\n\s*\{\s*\n\s*nlohmann::json json_data;\s*\n\s*file >> json_data;\s*\n\s*file\.close\(\);\s*\n\s*json_scenarios_ = json_data\["scenarios"\];\s*\n\s*std::cout << "JSON dosyasından " << json_scenarios_\.size\(\) << " senaryo yüklendi\." << std::endl;\s*\n\s*\}\s*\n\s*catch \(const std::exception& e\)\s*\n\s*\{\s*\n\s*std::cerr << "JSON dosyası okuma hatası: " << e\.what\(\) << std::endl;\s*\n\s*\}'
        content = re.sub(duplicate_try_catch, '', content, flags=re.DOTALL)

        # Constructor'da current_scenario_index_'i initialize et
        constructor_pattern = rf'{module_name}PublisherApp\(\)\s*:\s*([^}}]*)\{{([^}}]*)\}}'
        constructor_match = re.search(constructor_pattern, content, re.DOTALL)
        
        if constructor_match:
            constructor_body = constructor_match.group(2)
            if 'current_scenario_index_' not in constructor_body:
                init_line = '        current_scenario_index_ = 0;\n        loadJsonScenarios();'
                new_constructor_body = constructor_body.rstrip() + '\n' + init_line + '\n    }'
                content = content.replace(constructor_match.group(0), 
                                        constructor_match.group(0).replace(constructor_body, new_constructor_body))

        # loadJsonScenarios fonksiyonunu ekle
        load_function = f'''void {module_name}PublisherApp::loadJsonScenarios()
{{
    try
    {{
        std::ifstream file("{self.project_root}\\\\scenarios\\\\{module_name}.json");
        if (!file.is_open())
        {{
            std::cerr << "JSON dosyası açılamadı: {self.project_root}\\\\scenarios\\\\{module_name}.json" << std::endl;
            return;
        }}

        nlohmann::json json_data;
        file >> json_data;
        file.close();

        json_scenarios_ = json_data["scenarios"];
        std::cout << "{module_name} JSON dosyasından " << json_scenarios_.size() << " senaryo yüklendi." << std::endl;
    }}
    catch (const std::exception& e)
    {{
        std::cerr << "{module_name} JSON dosyası okuma hatası: " << e.what() << std::endl;
    }}
}}'''

        # Fonksiyonu dosya sonuna ekle
        content = content.rstrip() + '\n\n' + load_function

        # publish() fonksiyonunu tamamen değiştir
        publish_pattern = r'bool\s+\w+PublisherApp::publish\(\)\s*\{{[^}}]*\}}'
        publish_match = re.search(publish_pattern, content, re.DOTALL)
        
        if publish_match:
            # Intelligence için özel JSON okuma kodu
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
        // JSON'dan veri al
        if (current_scenario_index_ < json_scenarios_.size())
        {{
            {module_name}::{struct_name} sample_;
            const auto& scenario = json_scenarios_[current_scenario_index_];
            const auto& location = scenario["location"];
            const auto& coords = location["coords"];
            const auto& time_info = location["time_info"];

            // Command'i ayarla
            sample_.command(scenario["command"].get<std::string>());

            // Target location data'yı ayarla
            sample_.target_location_data().coords().latitude(coords["latitude"].get<double>());
            sample_.target_location_data().coords().longitude(coords["longitude"].get<double>());
            sample_.target_location_data().coords().altitude(coords["altitude"].get<float>());

            // Zaman bilgilerini ayarla
            sample_.target_location_data().time_info().seconds(time_info["seconds"].get<int32_t>());
            sample_.target_location_data().time_info().nano_seconds(time_info["nano_seconds"].get<uint32_t>());

            // Hız ve yönelim
            sample_.target_location_data().speed_mps(location["speed_mps"].get<float>());
            sample_.target_location_data().orientation_degrees(location["orientation_degrees"].get<int16_t>());

            // Gönderilen veriler gösteriliyor
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

            // Bir sonraki senaryoya geç
            current_scenario_index_++;
            if (current_scenario_index_ >= json_scenarios_.size())
            {{
                current_scenario_index_ = 0; // Başa dön
            }}
        }}
    }}
    return ret;
}}'''
            elif module_name == "Messaging":
                # Messaging için özel JSON okuma kodu
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
        // JSON'dan veri al
        if (current_scenario_index_ < json_scenarios_.size())
        {{
            {module_name}::{struct_name} sample_;
            const auto& scenario = json_scenarios_[current_scenario_index_];
            const auto& location = scenario["location"];
            const auto& coords = location["coords"];
            const auto& time_info = location["time_info"];
            const auto& header = scenario["header"];
            const auto& assignment = scenario["assignment"];

            // Header bilgilerini ayarla
            sample_.header().sender_id(header["sender_id"].get<std::string>());
            sample_.header().send_time().seconds(header["send_time"]["seconds"].get<int32_t>());
            sample_.header().send_time().nano_seconds(header["send_time"]["nano_seconds"].get<uint32_t>());

            // Receiver ID'yi ayarla
            sample_.receiver_id(scenario["receiver_id"].get<std::string>());

            // Assignment bilgilerini ayarla
            sample_.assignment().command(assignment["command"].get<std::string>());
            sample_.assignment().target_location_data().coords().latitude(assignment["target_location_data"]["coords"]["latitude"].get<double>());
            sample_.assignment().target_location_data().coords().longitude(assignment["target_location_data"]["coords"]["longitude"].get<double>());
            sample_.assignment().target_location_data().coords().altitude(assignment["target_location_data"]["coords"]["altitude"].get<float>());
            sample_.assignment().target_location_data().time_info().seconds(assignment["target_location_data"]["time_info"]["seconds"].get<int32_t>());
            sample_.assignment().target_location_data().time_info().nano_seconds(assignment["target_location_data"]["time_info"]["nano_seconds"].get<uint32_t>());
            sample_.assignment().target_location_data().speed_mps(assignment["target_location_data"]["speed_mps"].get<float>());
            sample_.assignment().target_location_data().orientation_degrees(assignment["target_location_data"]["orientation_degrees"].get<int16_t>());

            // Gönderilen veriler gösteriliyor
            std::cout << "Scenario " << scenario["id"].get<int>() << " - " << scenario["description"].get<std::string>() << std::endl;
            std::cout << "  header.sender_id: " << sample_.header().sender_id() << std::endl;
            std::cout << "  receiver_id: " << sample_.receiver_id() << std::endl;
            std::cout << "  assignment.command: " << sample_.assignment().command() << std::endl;

            ret = (RETCODE_OK == writer_->write(&sample_));

            // Bir sonraki senaryoya geç
            current_scenario_index_++;
            if (current_scenario_index_ >= json_scenarios_.size())
            {{
                current_scenario_index_ = 0; // Başa dön
            }}
        }}
    }}
    return ret;
}}'''
            else:
                # CoreData için standart JSON okuma kodu
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
        // JSON'dan veri al
        if (current_scenario_index_ < json_scenarios_.size())
        {{
            {module_name}::{struct_name} sample_;
            const auto& scenario = json_scenarios_[current_scenario_index_];
            const auto& location = scenario["location"];
            const auto& coords = location["coords"];
            const auto& time_info = location["time_info"];

            // Koordinatları ayarla
            sample_.coords().latitude(coords["latitude"].get<double>());
            sample_.coords().longitude(coords["longitude"].get<double>());
            sample_.coords().altitude(coords["altitude"].get<float>());

            // Zaman bilgilerini ayarla
            sample_.time_info().seconds(time_info["seconds"].get<int32_t>());
            sample_.time_info().nano_seconds(time_info["nano_seconds"].get<uint32_t>());

            // Hız ve yönelim
            sample_.speed_mps(location["speed_mps"].get<float>());
            sample_.orientation_degrees(location["orientation_degrees"].get<int16_t>());

            // Gönderilen veriler gösteriliyor
            std::cout << "Scenario " << scenario["id"].get<int>() << " - " << scenario["description"].get<std::string>() << std::endl;
            std::cout << "  coords.latitude: " << sample_.coords().latitude() << std::endl;
            std::cout << "  coords.longitude: " << sample_.coords().longitude() << std::endl;
            std::cout << "  coords.altitude: " << sample_.coords().altitude() << std::endl;
            std::cout << "  time_info.seconds: " << sample_.time_info().seconds() << std::endl;
            std::cout << "  time_info.nano_seconds: " << sample_.time_info().nano_seconds() << std::endl;
            std::cout << "  speed_mps: " << sample_.speed_mps() << std::endl;
            std::cout << "  orientation_degrees: " << sample_.orientation_degrees() << std::endl;

            ret = (RETCODE_OK == writer_->write(&sample_));

            // Bir sonraki senaryoya geç
            current_scenario_index_++;
            if (current_scenario_index_ >= json_scenarios_.size())
            {{
                current_scenario_index_ = 0; // Başa dön
            }}
        }}
    }}
    return ret;
}}'''
            
            # Eski publish fonksiyonunu yeni ile değiştir
            content = content.replace(publish_match.group(0), new_publish_function)
        
        # Dosyayı güncelle
        try:
            with open(publisher_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ Publisher dosyası yazılamadı: {publisher_file} - {e}")
            return False

    def patch_cmake_lists(self, cmake_file: str) -> bool:
        """CMakeLists.txt dosyasına nlohmann_json bağımlılığını ekler."""
        try:
            with open(cmake_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ CMakeLists.txt dosyası okunamadı: {cmake_file} - {e}")
            return False

        # nlohmann_json find_package'ını ekle
        if 'find_package(nlohmann_json REQUIRED)' not in content:
            # find_package satırlarını bul ve ekle
            find_package_pattern = r'(find_package\([^)]+\))'
            find_package_match = re.search(find_package_pattern, content)
            
            if find_package_match:
                insert_pos = find_package_match.end()
                content = content[:insert_pos] + '\nfind_package(nlohmann_json REQUIRED)' + content[insert_pos:]
            else:
                # Dosya başına ekle
                content = 'find_package(nlohmann_json REQUIRED)\n' + content

        # target_link_libraries'a nlohmann_json ekle
        if 'nlohmann_json::nlohmann_json' not in content:
            target_link_pattern = r'(target_link_libraries\([^)]+\))'
            target_link_match = re.search(target_link_pattern, content)
            
            if target_link_match:
                old_target_link = target_link_match.group(1)
                new_target_link = old_target_link.rstrip(')') + '\n            nlohmann_json::nlohmann_json\n            )'
                content = content.replace(old_target_link, new_target_link)

        # Dosyayı güncelle
        try:
            with open(cmake_file, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"❌ CMakeLists.txt dosyası yazılamadı: {cmake_file} - {e}")
            return False

    def patch_subscriber_app(self, subscriber_file: str, struct_name: str, members: List[Tuple[str, str]], module_name: str = "") -> bool:
        """Subscriber uygulamasını patch eder - alınan verileri gösterir."""
        try:
            with open(subscriber_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Subscriber dosyası okunamadı: {subscriber_file} - {e}")
            return False

        # Eski veri gösterim kodlarını temizle - daha güçlü regex
        old_display_pattern = r'            // Alınan veriler gösteriliyor\n(            std::cout << "[^"]*" << [^;]+;\n)*'
        content = re.sub(old_display_pattern, '', content)
        
        # Duplicate kodları temizle
        duplicate_pattern = r'            std::cout << "  [^"]*": " << sample_\.[^;]+;\n'
        content = re.sub(duplicate_pattern, '', content)
        
        # Tüm eski cout satırlarını temizle
        old_cout_pattern = r'            std::cout << "  [^"]*" << sample_\.[^;]+;\n'
        content = re.sub(old_cout_pattern, '', content)
        
        # Boş satırları temizle
        content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)
        
        # Subscriber'da sample alım yerini bul
        sample_pattern = rf'{module_name}::{struct_name}\s+sample_;'
        match = re.search(sample_pattern, content)
        
        if not match:
            print(f"     ⚠️  Subscriber'da {struct_name} sample bulunamadı")
            return False

        # While döngüsü içinde veri gösterimi ekle
        while_pattern = r'while \(\(!is_stopped\(\)\) && \(RETCODE_OK == reader->take_next_sample\(&sample_, &info\)\)\)\s*\{'
        while_match = re.search(while_pattern, content)
        
        if while_match:
            # While döngüsü içinde veri gösterimi ekle
            while_start = while_match.group(0)
            data_display = []
            data_display.append(f"            // Alınan veriler gösteriliyor")
            for member_type, member_name in members:
                # Karmaşık tipler için detaylı gösterim
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
            
            # Yeni içerik oluştur
            new_content = content.replace(while_start, while_start + "\n" + "\n".join(data_display))
        else:
            # Fallback: sample tanımından sonra ekle
            sample_line = match.group(0)
            data_display = []
            data_display.append(f"        // Alınan veriler gösteriliyor")
            for member_type, member_name in members:
                # Karmaşık tipler için detaylı gösterim
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
            
            # Yeni içerik oluştur
            new_content = content.replace(sample_line, sample_line + "\n" + "\n".join(data_display))
        
        # Dosyayı güncelle
        try:
            with open(subscriber_file, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return True
        except Exception as e:
            print(f"❌ Subscriber dosyası yazılamadı: {subscriber_file} - {e}")
            return False

    def run(self):
        """Ana işlem fonksiyonu."""
        print("🚀 IDL JSON Patcher başlatılıyor...")
        print("=" * 50)
        
        # IDL dosyalarını bul
        idl_files = self.find_idl_files()
        if not idl_files:
            print("❌ Hiç IDL dosyası bulunamadı!")
            return
        
        print(f"📁 Bulunan IDL dosyaları: {len(idl_files)}")
        for idl_file in idl_files:
            print(f"   - {idl_file}")
        
        # Her IDL dosyasını işle
        total_success = 0
        total_files = len(idl_files)
        
        for idl_file in idl_files:
            if self.process_idl_file(idl_file):
                total_success += 1
        
        print("\n" + "=" * 50)
        print(f"🎉 İşlem tamamlandı!")
        print(f"📊 Başarılı dosya sayısı: {total_success}/{total_files}")
        
        if total_success == total_files:
            print("✅ Tüm dosyalar başarıyla işlendi!")
        else:
            print("⚠️  Bazı dosyalar işlenemedi, yukarıdaki hata mesajlarını kontrol edin.")
    
    def _detect_project_root(self) -> str:
        """Proje kök dizinini dinamik olarak algılar."""
        current_dir = Path.cwd()
        
        # Scripts/py klasöründeysek, iki üst dizine çık
        if current_dir.name == 'py' and current_dir.parent.name == 'scripts':
            project_root = current_dir.parent.parent
        # Scripts klasöründeysek, bir üst dizine çık
        elif current_dir.name == 'scripts':
            project_root = current_dir.parent
        else:
            project_root = current_dir
        
        return str(project_root.absolute())
    
    def check_portability(self) -> bool:
        """Taşınabilirlik kontrolü yapar."""
        print("🔍 Taşınabilirlik kontrolü yapılıyor...")
        
        # Proje yapısını kontrol et
        required_dirs = ['IDL', 'docs']
        missing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = Path(self.project_root) / dir_name
            if not dir_path.exists():
                missing_dirs.append(dir_name)
        
        if missing_dirs:
            print(f"⚠️  Eksik klasörler: {missing_dirs}")
            return False
        
        # IDL dosyalarını kontrol et
        idl_files = list(Path(self.project_root).glob('IDL/*.idl'))
        if not idl_files:
            print("⚠️  IDL dosyası bulunamadı")
            return False
        
        print("✅ Proje yapısı taşınabilir durumda")
        return True

def main():
    """Ana fonksiyon."""
    patcher = IDLJSONPatcher()
    
    # Taşınabilirlik kontrolü
    if not patcher.check_portability():
        print("❌ Taşınabilirlik kontrolü başarısız, işlem durduruluyor.")
        return
    
    patcher.run()

if __name__ == "__main__":
    main()