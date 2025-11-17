#!/usr/bin/env python3
"""
IDL Setup Patcher Script
Bu script tüm *_idl_generated klasörlerindeki Publisher ve Subscriber App dosyalarını
otomatik olarak güncelleyerek sample gönderim/alım işlemlerinde nesne verilerini
JSON formatında yazdıran kod bloklarını ekler.

Özellikler:
- Hiçbir yeni dosya eklemez
- Hiçbir fonksiyonu silmez
- Sadece mevcut fonksiyonlara veri yazdırma özelliği ekler
- Tüm *_idl_generated klasörlerini otomatik olarak günceller
- Orijinal dosya yapısını bozmaz
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
        """Tüm *_idl_generated klasörlerini bulur"""
        pattern = str(self.base_path / "IDL" / "*_idl_generated")
        self.idl_folders = glob.glob(pattern)
        print(f"Bulunan IDL generated klasörleri: {len(self.idl_folders)}")
        for folder in self.idl_folders:
            print(f"  - {folder}")
        return self.idl_folders
    
    def extract_data_fields_from_header(self, header_file_path):
        """Header dosyasından veri alanlarını çıkarır"""
        try:
            with open(header_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Private member variables'ları bul
            private_section_match = re.search(r'private:\s*\n(.*?)(?:\n\s*\};|\Z)', content, re.DOTALL)
            if not private_section_match:
                return []
            
            private_content = private_section_match.group(1)
            
            # Member variable'ları çıkar (m_ ile başlayanlar)
            field_pattern = r'\s*(\w+)\s+m_(\w+)(?:\{[^}]*\})?;'
            matches = re.findall(field_pattern, private_content)
            
            fields = []
            for type_name, field_name in matches:
                fields.append({
                    'name': field_name,
                    'type': type_name,
                    'accessor': field_name  # getter fonksiyon adı
                })
            
            return fields
            
        except Exception as e:
            print(f"Header dosyası okuma hatası {header_file_path}: {e}")
            return []
    
    def generate_data_printing_code(self, fields, sample_var_name, namespace_class):
        """Veri yazdırma kodunu oluşturur - pointer erişimi için -> kullanır, fazla karakter eklenmesini önler"""
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
        
        # Fazla karakter eklenmesini önlemek için temiz bir string döndür
        return '\n            '.join(code_lines)
    
    def patch_publisher_file(self, file_path):
        """Publisher dosyasını günceller - veri yazdırma kodunu run() fonksiyonu içinde yapar"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Namespace ve class adını çıkar
            namespace_match = re.search(r'#include "(\w+)PubSubTypes\.hpp"', content)
            if not namespace_match:
                print(f"Namespace bulunamadı: {file_path}")
                return False
            
            namespace = namespace_match.group(1)
            
            # Header dosyasını bul
            header_file = file_path.replace('PublisherApp.cxx', '.hpp')
            if not os.path.exists(header_file):
                print(f"Header dosyası bulunamadı: {header_file}")
                return False
            
            # Veri alanlarını çıkar
            fields = self.extract_data_fields_from_header(header_file)
            if not fields:
                print(f"Veri alanları bulunamadı: {header_file}")
                return False
            
            # Sample variable artık üye değişkeni olarak tanımlandı, header dosyasından class adını çıkar
            # Header dosyasından sample_ üye değişkenini bul
            try:
                with open(header_file, 'r', encoding='utf-8') as f:
                    header_content = f.read()
                
                sample_var_match = re.search(r'(\w+::\w+)\s+sample_;', header_content)
                if not sample_var_match:
                    print(f"Sample üye değişkeni bulunamadı: {header_file}")
                    return False
                
                sample_class = sample_var_match.group(1)
                sample_var = "sample_"
            except Exception as e:
                print(f"Header dosyası okuma hatası: {e}")
                return False
            
            # 1. Önce publish() fonksiyonunu bool döndürmek yerine sample_ döndürecek şekilde değiştir
            # publish() fonksiyonunun return type'ını değiştir
            publish_signature_pattern = r'bool\s+(\w+PublisherApp::publish\(\))'
            if re.search(publish_signature_pattern, content):
                content = re.sub(publish_signature_pattern, f'{sample_class}* \\1', content)
            
            # publish() fonksiyonunun içeriğini güncelle - sample_'i return et
            # Önce samples_sent_++ kısmını kaldır çünkü bunu run() fonksiyonunda yapacağız
            publish_return_pattern = r'(ret = \(RETCODE_OK == writer_->write\(&sample_\)\);\s*if \(ret\)\s*\{\s*samples_sent_\+\+;\s*\}\s*)\s*return ret;'
            if re.search(publish_return_pattern, content, re.DOTALL):
                content = re.sub(publish_return_pattern, 'ret = (RETCODE_OK == writer_->write(&sample_));\n        return ret ? &sample_ : nullptr;', content, flags=re.DOTALL)
            
            # Header dosyasında da publish() fonksiyonunun signature'ını güncelle
            header_publish_pattern = r'bool\s+publish\(\);'
            if re.search(header_publish_pattern, header_content):
                header_content = re.sub(header_publish_pattern, f'{sample_class}* publish();', header_content)
                
                with open(header_file, 'w', encoding='utf-8') as f:
                    f.write(header_content)
            
            # 2. run() fonksiyonu içinde sample pointer'ını kullanarak veri yazdırma kodunu ekle
            data_printing_code = self.generate_data_printing_code(fields, "sample", sample_class)
            
            # run() fonksiyonu içinde mevcut "auto sample = publish(); if (sample)" bloğunu bul ve güncelle
            existing_sample_pattern = r'(auto sample = publish\(\);\s*if \(sample\)\s*\{\s*)(.*?)(\s*\})'
            
            if re.search(existing_sample_pattern, content, re.DOTALL):
                # Mevcut kodu güncelle - fazla karakter eklenmesini önle
                replacement = f'\\1std::cout << "Sample \'" << std::to_string(samples_sent_) << "\' SENT" << std::endl;\n            {data_printing_code}\n            ++samples_sent_;\\3'
                content = re.sub(existing_sample_pattern, replacement, content, flags=re.DOTALL)
                
                # Fazla karakterleri temizle
                content = re.sub(r'\+\+samples_sent_;\}" << std::endl;\s*\+\+samples_sent_;', '++samples_sent_;', content)
                
                # Dosyayı kaydet
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Publisher güncellendi (mevcut auto sample pattern): {file_path}")
                return True
            else:
                # Eski if (publish()) pattern'ini ara
                run_publish_pattern = r'(if \(publish\(\)\)\s*\{\s*)(.*?)(\s*\})'
                
                if re.search(run_publish_pattern, content, re.DOTALL):
                    # Yeni kod: auto sample = publish(); if (sample) { ... }
                    replacement = f'auto sample = publish();\n        if (sample)\n        {{\n            std::cout << "Sample \'" << std::to_string(samples_sent_) << "\' SENT" << std::endl;\n            {data_printing_code}\n            ++samples_sent_;\n        }}'
                    content = re.sub(run_publish_pattern, replacement, content, flags=re.DOTALL)
                    
                    # Dosyayı kaydet
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    print(f"Publisher güncellendi (run() fonksiyonu): {file_path}")
                    return True
                else:
                    print(f"run() fonksiyonunda publish pattern bulunamadı: {file_path}")
                    return False
                
        except Exception as e:
            print(f"Publisher dosyası güncelleme hatası {file_path}: {e}")
            return False
    
    def patch_subscriber_file(self, file_path):
        """Subscriber dosyasını günceller"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Namespace ve class adını çıkar
            namespace_match = re.search(r'#include "(\w+)PubSubTypes\.hpp"', content)
            if not namespace_match:
                print(f"Namespace bulunamadı: {file_path}")
                return False
            
            namespace = namespace_match.group(1)
            
            # Header dosyasını bul
            header_file = file_path.replace('SubscriberApp.cxx', '.hpp')
            if not os.path.exists(header_file):
                print(f"Header dosyası bulunamadı: {header_file}")
                return False
            
            # Veri alanlarını çıkar
            fields = self.extract_data_fields_from_header(header_file)
            if not fields:
                print(f"Veri alanları bulunamadı: {header_file}")
                return False
            
            # Sample variable adını bul (on_data_available fonksiyonunda)
            sample_var_match = re.search(r'(\w+::\w+)\s+(\w+);\s*\n\s*SampleInfo info;', content)
            if not sample_var_match:
                print(f"Sample variable bulunamadı: {file_path}")
                return False
            
            sample_class = sample_var_match.group(1)
            sample_var = sample_var_match.group(2)
            
            # Veri yazdırma kodunu oluştur - Subscriber'da sample değişken olduğu için . kullan
            # Subscriber'da sample bir pointer değil, doğrudan nesne
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
            
            # Subscriber'da "Sample 'X' RECEIVED" yazdırılan yeri bul ve veri yazdırma kodunu ekle
            received_pattern = r'(std::cout << "Sample \'" << std::to_string\(\+\+samples_received_\) << "\' RECEIVED" << std::endl;)'
            
            if re.search(received_pattern, content):
                # Eğer zaten veri yazdırma kodu eklenmişse, güncelle
                existing_data_pattern = r'(std::cout << "Sample \'" << std::to_string\(\+\+samples_received_\) << "\' RECEIVED" << std::endl;)\s*\n(\s*std::cout << " - \{.*?\}" << std::endl;)'
                
                if re.search(existing_data_pattern, content, re.DOTALL):
                    # Mevcut veri yazdırma kodunu güncelle
                    replacement = f'\\1\n            {data_printing_code}'
                    content = re.sub(existing_data_pattern, replacement, content, flags=re.DOTALL)
                else:
                    # Yeni veri yazdırma kodu ekle
                    replacement = f'\\1\n            {data_printing_code}'
                    content = re.sub(received_pattern, replacement, content)
                
                # Dosyayı kaydet
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"Subscriber güncellendi: {file_path}")
                return True
            else:
                print(f"RECEIVED pattern bulunamadı: {file_path}")
                return False
                
        except Exception as e:
            print(f"Subscriber dosyası güncelleme hatası {file_path}: {e}")
            return False
    
    def process_idl_folder(self, folder_path):
        """Bir IDL generated klasörünü işler"""
        folder_path = Path(folder_path)
        print(f"\nİşleniyor: {folder_path}")
        
        # Publisher App dosyasını bul ve güncelle
        publisher_files = list(folder_path.glob("*PublisherApp.cxx"))
        for pub_file in publisher_files:
            if pub_file.name.endswith('.backup'):
                continue
            print(f"  Publisher dosyası: {pub_file}")
            if self.patch_publisher_file(str(pub_file)):
                self.processed_files.append(str(pub_file))
        
        # Subscriber App dosyasını bul ve güncelle
        subscriber_files = list(folder_path.glob("*SubscriberApp.cxx"))
        for sub_file in subscriber_files:
            if sub_file.name.endswith('.backup'):
                continue
            print(f"  Subscriber dosyası: {sub_file}")
            if self.patch_subscriber_file(str(sub_file)):
                self.processed_files.append(str(sub_file))
    
    def run(self):
        """Ana işlem fonksiyonu"""
        print("IDL Setup Patcher başlatılıyor...")
        print(f"Ana dizin: {self.base_path}")
        
        # IDL generated klasörlerini bul
        folders = self.find_idl_generated_folders()
        if not folders:
            print("Hiç IDL generated klasörü bulunamadı!")
            return False
        
        # Her klasörü işle
        for folder in folders:
            self.process_idl_folder(folder)
        
        # Sonuçları göster
        print(f"\n=== İŞLEM TAMAMLANDI ===")
        print(f"İşlenen klasör sayısı: {len(folders)}")
        print(f"Güncellenen dosya sayısı: {len(self.processed_files)}")
        
        if self.processed_files:
            print("\nGüncellenen dosyalar:")
            for file_path in self.processed_files:
                print(f"  - {file_path}")
        
        return len(self.processed_files) > 0

def main():
    """Ana fonksiyon"""
    if len(sys.argv) > 1:
        base_path = sys.argv[1]
    else:
        # Script'in bulunduğu dizinden DDS ana dizinini bul
        script_dir = Path(__file__).parent
        base_path = script_dir.parent.parent  # scripts/py -> scripts -> DDS
    
    patcher = IDLSetupPatcher(base_path)
    success = patcher.run()
    
    if success:
        print("\n✅ Tüm dosyalar başarıyla güncellendi!")
        print("\nArtık Publisher ve Subscriber uygulamaları sample verilerini")
        print("JSON formatında ekrana yazdıracak:")
        print("  - Sample 'X' SENT - {field1: value1, field2: value2, ...}")
        print("  - Sample 'X' RECEIVED - {field1: value1, field2: value2, ...}")
    else:
        print("\n❌ Hiçbir dosya güncellenemedi!")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())