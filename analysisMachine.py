import fitz  # PyMuPDF
import re
import pandas as pd
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk
from datetime import datetime
try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# Renk teması - Hastane teması
COLORS = {
    'primary': '#1e3a8a',      # Koyu mavi
    'secondary': '#3b82f6',    # Mavi
    'accent': '#06b6d4',       # Cyan
    'success': '#10b981',      # Yeşil
    'warning': '#f59e0b',      # Turuncu
    'danger': '#ef4444',       # Kırmızı
    'light': '#f8fafc',        # Açık gri
    'white': '#ffffff',        # Beyaz
    'dark': '#1e293b',         # Koyu gri
    'text': '#334155'          # Metin rengi
}

def parse_references(ref):
    try:
        if '-' in ref:
            alt, ust = ref.replace(',', '.').split('-')
            return float(alt.strip()), float(ust.strip())
    except:
        pass
    return None, None

def normalize_test_name(test_name):
    """Test adını normalize eder ve benzer testleri birleştirir"""
    normalized = test_name.strip()
    
    # Tam Kan Sayımı testleri için özel işlem
    if "Tam Kan Sayımı" in normalized or "Hemogram" in normalized:
        # "Tam Kan Sayımı (Hemogram)" kısmını tamamen kaldır
        normalized = normalized.replace("Tam Kan Sayımı (Hemogram)", "").replace("Tam Kan Sayımı", "").replace("(Hemogram)", "")
        # Fazla boşlukları temizle
        normalized = " ".join(normalized.split())
    
    # Diğer gereksiz ön ekleri kaldır
    prefixes_to_remove = [
        "Değeri",
        "Referans"
    ]
    
    for prefix in prefixes_to_remove:
        if normalized.startswith(prefix):
            normalized = normalized[len(prefix):].strip()
    
    # Fazla boşlukları temizle
    normalized = " ".join(normalized.split())
    
    return normalized

def merge_similar_tests(df):
    """Benzer testleri birleştirir"""
    if df.empty:
        return df
    
    # Test adlarını normalize et
    df['Normalized_Name'] = df['Tahlil'].apply(normalize_test_name)
    
    # Normalize edilmiş isimlere göre grupla
    merged_tests = []
    for normalized_name, group in df.groupby('Normalized_Name'):
        if len(group) > 1:
            # Birden fazla aynı test varsa, en kısa ve temiz olanı seç
            best_test = group.iloc[0]
            shortest_name = best_test['Tahlil']
            
            for _, test in group.iterrows():
                current_normalized = normalize_test_name(test['Tahlil'])
                if len(current_normalized) < len(normalize_test_name(shortest_name)):
                    shortest_name = test['Tahlil']
                    best_test = test
            
            merged_tests.append({
                'Tahlil': shortest_name,  # En kısa ve temiz adı kullan
                'Sonuç': best_test['Sonuç'],
                'Birim': best_test['Birim'],
                'Referans Alt': best_test['Referans Alt'],
                'Referans Üst': best_test['Referans Üst']
            })
        else:
            # Tek test ise direkt ekle
            test = group.iloc[0]
            merged_tests.append({
                'Tahlil': test['Tahlil'],
                'Sonuç': test['Sonuç'],
                'Birim': test['Birim'],
                'Referans Alt': test['Referans Alt'],
                'Referans Üst': test['Referans Üst']
            })
    
    return pd.DataFrame(merged_tests)

def extract_tests_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    all_text = ""
    for page in doc:
        all_text += page.get_text()
    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
    tests = []
    i = 0
    processed_tests = set()  # Tekrar eden testleri önlemek için
    
    while i < len(lines) - 3:
        # Tarih/saat formatlarını filtrele
        if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', lines[i]) or \
           re.match(r'^\d{1,2}:\d{1,2}:\d{1,2}$', lines[i]) or \
           lines[i].startswith('Tarih') or \
           lines[i].startswith('Adı Soyadı:') or \
           lines[i].startswith('Tahlil') or \
           lines[i].startswith('Sonuç') or \
           lines[i].startswith('Birimi') or \
           lines[i].startswith('Referans') or \
           lines[i].strip() == '-' or \
           lines[i].strip() == '' or \
           re.match(r'^-+$', lines[i]):
            i += 1
            continue
            
        # Test adını birleştir (birden fazla satır olabilir)
        test_name_parts = []
        current_i = i
        
        # Test adının tamamını bul
        while current_i < len(lines) and not re.match(r"^[\d.,]+$", lines[current_i]):
            # Tarih/saat formatlarını atla
            if re.match(r'^\d{1,2}\.\d{1,2}\.\d{4}$', lines[current_i]) or \
               re.match(r'^\d{1,2}:\d{1,2}:\d{1,2}$', lines[current_i]) or \
               lines[current_i].strip() == '-' or \
               lines[current_i].strip() == '' or \
               re.match(r'^-+$', lines[current_i]):
                current_i += 1
                continue
            test_name_parts.append(lines[current_i])
            current_i += 1
        
        if current_i >= len(lines) - 2:
            break
            
        # Test adını birleştir
        test_name = " ".join(test_name_parts).strip()
        
        # Boş test adlarını atla
        if not test_name or test_name.startswith('Tarih') or test_name.startswith('Adı'):
            i += 1
            continue
        
        # Sonuç, birim ve referans değerlerini al
        result = lines[current_i].replace(',', '.')
        unit = lines[current_i + 1]
        ref_line = lines[current_i + 2]
        
        ref_match = re.match(r"(\d+[.,]?\d*)\s*-\s*(\d+[.,]?\d*)", ref_line)
        
        if ref_match and test_name:
            ref_min = ref_match.group(1).replace(',', '.')
            ref_max = ref_match.group(2).replace(',', '.')
            
            # Test adını temizle ve benzersizlik kontrolü yap
            clean_test_name = test_name.strip()
            
            # Eğer bu test daha önce işlenmediyse ekle
            if clean_test_name not in processed_tests:
                try:
                    tests.append({
                        "Tahlil": clean_test_name,
                        "Sonuç": float(result),
                        "Birim": unit,
                        "Referans Alt": float(ref_min),
                        "Referans Üst": float(ref_max),
                    })
                    processed_tests.add(clean_test_name)
                except ValueError as e:
                    print(f"Değer dönüştürme hatası: {clean_test_name}, {result}, {unit}, {ref_line} - {e}")
            
            i = current_i + 3
        else:
            i += 1
    
    # DataFrame oluştur ve benzer testleri birleştir
    df = pd.DataFrame(tests)
    if not df.empty:
        df = merge_similar_tests(df)
        df = df.drop_duplicates(subset=['Tahlil'], keep='first')
    
    return df

def durum_bul(row):
    if row['Sonuç'] < row['Referans Alt']:
        return 'Düşük'
    elif row['Sonuç'] > row['Referans Üst']:
        return 'Yüksek'
    else:
        return 'Normal'

def durum_key(durum):
    """Türkçe karakterleri normalize ederek durum anahtarını oluşturur"""
    return (
        durum.lower()
        .replace("ü", "u")
        .replace("ş", "s")
        .replace("ı", "i")
        .replace("ö", "o")
        .replace("ç", "c")
        .replace("ğ", "g")
    )

def yorum_veritabani_yukle_ve_guncelle(tahliller):
    default = {
        "dusuk": {
            "aciklama": "Bu testin sonucu referans aralığının altında.",
            "oneri": "Doktorunuza danışınız.",
            "doktor_kontrolu": "Gerekli"
        },
        "yuksek": {
            "aciklama": "Bu testin sonucu referans aralığının üstünde.",
            "oneri": "Doktorunuza danışınız.",
            "doktor_kontrolu": "Gerekli"
        },
        "normal": {
            "aciklama": "Bu testin sonucu normal aralıkta.",
            "oneri": "Rutin kontrolleri sürdürünüz.",
            "doktor_kontrolu": "Gerekli değil"
        }
    }
    try:
        if os.path.exists('yorum_veritabani.json'):
            with open('yorum_veritabani.json', 'r', encoding='utf-8') as f:
                yorum_db = json.load(f)
        else:
            yorum_db = {}
    except Exception:
        yorum_db = {}
    degisti = False
    for tahlil in tahliller:
        if tahlil not in yorum_db:
            yorum_db[tahlil] = default
            degisti = True
    if degisti:
        with open('yorum_veritabani.json', 'w', encoding='utf-8') as f:
            json.dump(yorum_db, f, ensure_ascii=False, indent=2)
    return yorum_db

def find_best_match(test_name, yorum_db):
    """Test adı için en iyi eşleşmeyi bulur"""
    # Fazla boşlukları temizle
    clean_test_name = " ".join(test_name.split())
    
    # Tam eşleşme kontrolü
    if clean_test_name in yorum_db:
        return clean_test_name
    
    # Normalize edilmiş test adı
    normalized_name = normalize_test_name(clean_test_name)
    if normalized_name in yorum_db:
        return normalized_name
    
    # Tam Kan Sayımı testleri için özel kontrol
    if "Tam Kan Sayımı" in clean_test_name or "Hemogram" in clean_test_name:
        # Test adından "Tam Kan Sayımı (Hemogram)" kısmını çıkar
        clean_test_name_only = clean_test_name.replace("Tam Kan Sayımı (Hemogram)", "").replace("Tam Kan Sayımı", "").replace("(Hemogram)", "").strip()
        clean_test_name_only = " ".join(clean_test_name_only.split())  # Fazla boşlukları temizle
        
        if clean_test_name_only in yorum_db:
            return clean_test_name_only
        
        # Temizlenmiş isimle kısmi eşleşme kontrolü
        for db_test in yorum_db.keys():
            if clean_test_name_only.lower() in db_test.lower() or db_test.lower() in clean_test_name_only.lower():
                return db_test
    
    # Kısmi eşleşme kontrolü - daha gelişmiş
    for db_test in yorum_db.keys():
        # Test adının anahtar kelimelerini kontrol et
        test_words = set(clean_test_name.lower().split())
        db_words = set(db_test.lower().split())
        
        # Ortak kelime sayısı
        common_words = test_words.intersection(db_words)
        if len(common_words) >= 2:  # En az 2 ortak kelime
            return db_test
        
        # Tam Kan Sayımı testleri için özel kontrol
        if "Tam Kan Sayımı" in clean_test_name and db_test in ["HEMOGLOBİN", "Hematokrit", "ERİTROSİT", "LÖKOSİT", "TROMBOSİT", "Nötrofil%", "Eozinofil%", "Lenfosit%", "Monosit%", "Bazofil%", "RDW-SD"]:
            if any(word in clean_test_name for word in [db_test, db_test.lower(), db_test.title()]):
                return db_test
    
    # Daha esnek eşleştirme - test adının sonundaki kelimeleri kontrol et
    for db_test in yorum_db.keys():
        # Test adının son kelimelerini al
        test_words = clean_test_name.split()
        if len(test_words) >= 2:
            last_two_words = " ".join(test_words[-2:])
            if last_two_words.lower() in db_test.lower():
                return db_test
    
    # Tek kelime eşleştirme - özellikle yüzde işareti olan testler için
    for db_test in yorum_db.keys():
        test_words = clean_test_name.split()
        for word in test_words:
            if word.lower() in db_test.lower() and len(word) > 2:  # En az 3 karakter
                return db_test
    
    # Yüzde işareti olan testler için özel kontrol
    if '%' in clean_test_name:
        for db_test in yorum_db.keys():
            if '%' in db_test:
                # Yüzde işaretinden önceki kelimeyi al
                test_percent_word = clean_test_name.split('%')[0].strip().split()[-1] if '%' in clean_test_name else ""
                db_percent_word = db_test.split('%')[0].strip().split()[-1] if '%' in db_test else ""
                
                if test_percent_word.lower() == db_percent_word.lower():
                    return db_test
    
    # Tam Kan Sayımı testleri için daha esnek eşleştirme
    if "Tam Kan Sayımı" in clean_test_name or "Hemogram" in clean_test_name:
        for db_test in yorum_db.keys():
            # Test adından "Tam Kan Sayımı" kısmını çıkar
            clean_name = clean_test_name.replace("Tam Kan Sayımı", "").replace("(Hemogram)", "").strip()
            clean_name = " ".join(clean_name.split())
            
            # Temizlenmiş isimle eşleştirme
            if clean_name.lower() in db_test.lower() or db_test.lower() in clean_name.lower():
                return db_test
    
    # "sayısı" kelimesi olan testler için özel kontrol
    if "sayısı" in clean_test_name:
        for db_test in yorum_db.keys():
            if "sayısı" in db_test:
                # "sayısı" kelimesinden önceki kelimeyi al
                test_count_word = clean_test_name.split("sayısı")[0].strip().split()[-1] if "sayısı" in clean_test_name else ""
                db_count_word = db_test.split("sayısı")[0].strip().split()[-1] if "sayısı" in db_test else ""
                
                if test_count_word.lower() == db_count_word.lower():
                    return db_test
    
    # Kısaltma eşleştirme (RBC, WBC, PLT gibi)
    abbreviations = {
        "RBC": "RBC sayısı",
        "WBC": "WBC sayısı", 
        "PLT": "PLT",
        "PCT": "PCT",
        "PDW": "PDW",
        "MPV": "MPV",
        "MCH": "MCH",
        "MCHC": "MCHC",
        "MCV": "MCV",
        "RDW": "RDW"
    }
    
    for abbr, full_name in abbreviations.items():
        if abbr in clean_test_name:
            if full_name in yorum_db:
                return full_name
    
    return None

def genel_analiz_olustur(df, yorum_db):
    analiz_sonuclari = []
    kritik_sonuclar = []
    normal_sonuclar = []
    eslesmeyen_testler = []  # Debug için
    
    for _, row in df.iterrows():
        test_adi = row['Tahlil']
        durum = row['Durum']
        
        # En iyi eşleşmeyi bul
        matched_test = find_best_match(test_adi, yorum_db)
        
        # Durum anahtarını normalize et
        durum_key_normalized = durum_key(durum)
        
        if matched_test and durum_key_normalized in yorum_db[matched_test]:
            # JSON veritabanından açıklama ve öneri al
            yorum = yorum_db[matched_test][durum_key_normalized]
            sonuc = {
                'Test': test_adi,
                'Sonuç': row['Sonuç'],
                'Birim': row['Birim'],
                'Durum': durum,
                'Açıklama': yorum['aciklama'],
                'Öneri': yorum['oneri'],
                'Doktor Kontrolü': yorum['doktor_kontrolu'],
                'Veritabanında': 'Evet'
            }
        elif matched_test:
            # Test eşleşti ama durum bilgisi yok - varsayılan değerler kullan
            if durum.lower() == 'yüksek':
                aciklama = f"{test_adi} seviyesi yüksek - doktor kontrolü gerekli"
                oneri = "Doktorunuza danışınız ve gerekli önlemleri alınız."
                doktor_kontrolu = "Gerekli"
            elif durum.lower() == 'düşük':
                aciklama = f"{test_adi} seviyesi düşük - doktor kontrolü gerekli"
                oneri = "Doktorunuza danışınız ve gerekli önlemleri alınız."
                doktor_kontrolu = "Gerekli"
            else:
                aciklama = f"{test_adi} seviyesi normal"
                oneri = "Rutin kontrolleri sürdürünüz."
                doktor_kontrolu = "Gerekli değil"
            
            sonuc = {
                'Test': test_adi,
                'Sonuç': row['Sonuç'],
                'Birim': row['Birim'],
                'Durum': durum,
                'Açıklama': aciklama,
                'Öneri': oneri,
                'Doktor Kontrolü': doktor_kontrolu,
                'Veritabanında': 'Kısmi'  # Test eşleşti ama durum bilgisi yok
            }
        else:
            # Debug için eşleşmeyen testleri kaydet
            eslesmeyen_testler.append(test_adi)
            
            # JSON veritabanında bulunmayan testler için varsayılan değerler
            if durum.lower() == 'yüksek':
                aciklama = f"{test_adi} seviyesi yüksek - doktor kontrolü gerekli"
                oneri = "Doktorunuza danışınız ve gerekli önlemleri alınız."
                doktor_kontrolu = "Gerekli"
            elif durum.lower() == 'düşük':
                aciklama = f"{test_adi} seviyesi düşük - doktor kontrolü gerekli"
                oneri = "Doktorunuza danışınız ve gerekli önlemleri alınız."
                doktor_kontrolu = "Gerekli"
            else:
                aciklama = f"{test_adi} seviyesi normal"
                oneri = "Rutin kontrolleri sürdürünüz."
                doktor_kontrolu = "Gerekli değil"
            
            sonuc = {
                'Test': test_adi,
                'Sonuç': row['Sonuç'],
                'Birim': row['Birim'],
                'Durum': durum,
                'Açıklama': aciklama,
                'Öneri': oneri,
                'Doktor Kontrolü': doktor_kontrolu,
                'Veritabanında': 'Hayır'  # JSON'da bulunmayan testler
            }
        if durum != 'Normal':
            kritik_sonuclar.append(sonuc)
        else:
            normal_sonuclar.append(sonuc)
        analiz_sonuclari.append(sonuc)
    
    # Debug: Eşleşmeyen testleri yazdır
    if eslesmeyen_testler:
        print(f"Eşleşmeyen testler: {eslesmeyen_testler}")
    
    return analiz_sonuclari, kritik_sonuclar, normal_sonuclar

def rapor_olustur(analiz_sonuclari, kritik_sonuclar, normal_sonuclar):
    lines = []
    lines.append("🏥" + "=" * 78 + "🏥")
    lines.append("                    TAHLLİ SONUÇLARI ANALİZ RAPORU")
    lines.append("🏥" + "=" * 78 + "🏥")
    if kritik_sonuclar:
        lines.append(f"\n⚠️  KRİTİK SONUÇLAR ({len(kritik_sonuclar)} adet):")
        lines.append("-" * 80)
        for sonuc in kritik_sonuclar:
            lines.append(f"\n🔸 {sonuc['Test']}")
            lines.append(f"   Sonuç: {sonuc['Sonuç']} {sonuc['Birim']} ({sonuc['Durum']})")
            if sonuc['Açıklama']:
                lines.append(f"   Açıklama: {sonuc['Açıklama']}")
            if sonuc['Öneri']:
                lines.append(f"   Öneri: {sonuc['Öneri']}")
            if sonuc['Doktor Kontrolü']:
                lines.append(f"   Doktor Kontrolü: {sonuc['Doktor Kontrolü']}")
    if normal_sonuclar:
        lines.append(f"\n✅ NORMAL SONUÇLAR ({len(normal_sonuclar)} adet):")
        lines.append("-" * 80)
        for sonuc in normal_sonuclar:
            lines.append(f"\n✓ {sonuc['Test']}")
            lines.append(f"   Sonuç: {sonuc['Sonuç']} {sonuc['Birim']} ({sonuc['Durum']})")
            if sonuc['Açıklama']:
                lines.append(f"   Açıklama: {sonuc['Açıklama']}")
            if sonuc['Öneri']:
                lines.append(f"   Öneri: {sonuc['Öneri']}")
            if sonuc['Doktor Kontrolü']:
                lines.append(f"   Doktor Kontrolü: {sonuc['Doktor Kontrolü']}")
    lines.append("\n" + "🏥" + "=" * 78 + "🏥")
    lines.append("                           GENEL ÖZET")
    lines.append("🏥" + "=" * 78 + "🏥")
    lines.append(f"Toplam Test Sayısı: {len(analiz_sonuclari)}")
    lines.append(f"Normal Sonuç: {len(normal_sonuclar)}")
    lines.append(f"Anormal Sonuç: {len(kritik_sonuclar)}")
    lines.append(f"Detaylı Yorum Yapılan: {len([s for s in analiz_sonuclari if s['Veritabanında'] == 'Evet'])}")
    lines.append("\n" + "🏥" + "=" * 78 + "🏥")
    return "\n".join(lines)

class HospitalStyleFrame(tk.Frame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=COLORS['light'], **kwargs)
        self.configure(relief='raised', bd=2)

class TahlilApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Kan Tahlil Analiz Sistemi")
        root.iconbitmap("favicon.ico")
        self.root.geometry("1280x720")
        self.root.configure(bg=COLORS['light'])
        
        # Ana container
        main_container = tk.Frame(root, bg=COLORS['light'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        self.create_header(main_container)
        
        # Content area
        content_frame = HospitalStyleFrame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=(20, 0))
        
        # Sol panel - Kontroller
        left_panel = tk.Frame(content_frame, bg=COLORS['white'], width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)
        left_panel.pack_propagate(False)
        
        self.create_control_panel(left_panel)
        
        # Sağ panel - Sonuçlar
        right_panel = tk.Frame(content_frame, bg=COLORS['white'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)
        
        self.create_result_panel(right_panel)
        
        # Status bar
        self.create_status_bar(main_container)
        
        # Drag & Drop
        if DND_AVAILABLE:
            self.root.drop_target_register(DND_FILES)
            self.root.dnd_bind('<<Drop>>', self.on_drop)
    
    def create_header(self, parent):
        header_frame = HospitalStyleFrame(parent, height=80)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        # Logo ve başlık
        title_frame = tk.Frame(header_frame, bg=COLORS['primary'])
        title_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = tk.Label(
            title_frame, 
            text="🏥 Kan Tahlil Analiz Sistemi", 
            font=("Arial", 16, "bold"),
            fg=COLORS['white'],
            bg=COLORS['primary']
        )
        title_label.pack(pady=20)
        
        # Alt başlık
        subtitle_label = tk.Label(
            title_frame,
            text="Laboratuvar Sonuçları Analiz ve Raporlama",
            font=("Arial", 10),
            fg=COLORS['light'],
            bg=COLORS['primary']
        )
        subtitle_label.pack(pady=(0, 10))
    
    def create_control_panel(self, parent):
        # Başlık
        control_title = tk.Label(
            parent,
            text="📋 Kontrol Paneli",
            font=("Arial", 12, "bold"),
            fg=COLORS['primary'],
            bg=COLORS['white']
        )
        control_title.pack(pady=(20, 15))
        
        # Dosya seçme butonu
        self.file_btn = tk.Button(
            parent,
            text="📁 PDF Dosyası Seç",
            command=self.select_file,
            font=("Arial", 10, "bold"),
            bg=COLORS['secondary'],
            fg=COLORS['white'],
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2'
        )
        self.file_btn.pack(pady=10)
        
        # Sürükle-bırak alanı
        drop_frame = tk.Frame(parent, bg=COLORS['light'], relief='solid', bd=2)
        drop_frame.pack(fill=tk.X, padx=20, pady=10)
        
        drop_label = tk.Label(
            drop_frame,
            text="📄 PDF dosyasını buraya sürükleyin",
            font=("Arial", 9),
            fg=COLORS['text'],
            bg=COLORS['light'],
            pady=20
        )
        drop_label.pack()
        
        # Analiz butonu (başlangıçta devre dışı)
        self.analyze_btn = tk.Button(
            parent,
            text="🔍 Detaylı Analiz Et",
            command=self.perform_detailed_analysis,
            font=("Arial", 10, "bold"),
            bg=COLORS['success'],
            fg=COLORS['white'],
            relief='flat',
            padx=20,
            pady=10,
            cursor='hand2',
            state='disabled'
        )
        self.analyze_btn.pack(pady=10)
        
        # Bilgi paneli
        info_frame = tk.Frame(parent, bg=COLORS['light'])
        info_frame.pack(fill=tk.X, padx=10, pady=20)
        
        info_title = tk.Label(
            info_frame,
            text="ℹ️ Bilgi",
            font=("Arial", 10, "bold"),
            fg=COLORS['primary'],
            bg=COLORS['light']
        )
        info_title.pack(anchor='w')
        
        info_text = tk.Label(
            info_frame,
            text="• PDF dosyasını seçin veya sürükleyin\n• Önce temel sonuçlar görünecek\n• 'Detaylı Analiz Et' butonuna basın\n• Detaylı rapor ve öneriler görünecek",
            font=("Arial", 8),
            fg=COLORS['text'],
            bg=COLORS['light'],
            justify='left'
        )
        info_text.pack(anchor='w', pady=5)
    
    def create_result_panel(self, parent):
        # Başlık
        result_title = tk.Label(
            parent,
            text="📊 Analiz Sonuçları",
            font=("Arial", 12, "bold"),
            fg=COLORS['primary'],
            bg=COLORS['white']
        )
        result_title.pack(pady=(20, 10))
        
        # Sonuç metin kutusu
        self.text = scrolledtext.ScrolledText(
            parent,
            wrap=tk.WORD,
            font=("Segoe UI", 10),
            bg=COLORS['white'],
            fg=COLORS['text'],
            relief='flat',
            bd=0,
            padx=15,
            pady=15
        )
        self.text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Başlangıç mesajı
        self.text.insert(tk.END, "🏥 Kan Tahlil Analiz Sistemine Hoş Geldiniz!\n\n")
        self.text.insert(tk.END, "📋 Kullanım:\n")
        self.text.insert(tk.END, "• Sol panelden PDF dosyası seçin\n")
        self.text.insert(tk.END, "• Veya dosyayı sürükleyip bırakın\n")
        self.text.insert(tk.END, "• Analiz sonuçları burada görünecek\n\n")
        self.text.insert(tk.END, "⏳ Analiz bekleniyor...\n")
        
        # Metin kutusu stil ayarları
        self.text.tag_configure("title", font=("Segoe UI", 14, "bold"), foreground=COLORS['primary'])
        self.text.tag_configure("subtitle", font=("Segoe UI", 12, "bold"), foreground=COLORS['secondary'])
        self.text.tag_configure("header", font=("Segoe UI", 11, "bold"), foreground=COLORS['dark'])
        self.text.tag_configure("success", font=("Segoe UI", 10), foreground=COLORS['success'])
        self.text.tag_configure("warning", font=("Segoe UI", 10), foreground=COLORS['warning'])
        self.text.tag_configure("danger", font=("Segoe UI", 10), foreground=COLORS['danger'])
        self.text.tag_configure("normal", font=("Segoe UI", 10), foreground=COLORS['text'])
        self.text.tag_configure("highlight", font=("Segoe UI", 10, "bold"), foreground=COLORS['primary'])
        self.text.tag_configure("info", font=("Segoe UI", 9), foreground=COLORS['accent'])
        self.text.tag_configure("separator", font=("Segoe UI", 10), foreground=COLORS['secondary'])
    
    def format_report_text(self, rapor):
        """Rapor metnini renkli ve formatlı hale getirir"""
        self.text.delete(1.0, tk.END)
        
        lines = rapor.split('\n')
        for line in lines:
            if line.startswith('🏥') and '=' in line:
                # Başlık çizgileri
                self.text.insert(tk.END, line + '\n', "separator")
            elif 'TAHLLİ SONUÇLARI ANALİZ RAPORU' in line:
                # Ana başlık
                self.text.insert(tk.END, line + '\n', "title")
            elif 'GENEL ÖZET' in line:
                # Özet başlığı
                self.text.insert(tk.END, line + '\n', "subtitle")
            elif line.startswith('⚠️  KRİTİK SONUÇLAR'):
                # Kritik sonuçlar başlığı
                self.text.insert(tk.END, line + '\n', "danger")
            elif line.startswith('✅ NORMAL SONUÇLAR'):
                # Normal sonuçlar başlığı
                self.text.insert(tk.END, line + '\n', "success")

            elif line.startswith('🔸'):
                # Test adı
                self.text.insert(tk.END, line + '\n', "highlight")
            elif line.startswith('✓'):
                # Normal test adı
                self.text.insert(tk.END, line + '\n', "success")
            elif line.startswith('   Sonuç:'):
                # Test sonucu
                self.text.insert(tk.END, line + '\n', "normal")
            elif line.startswith('   Açıklama:'):
                # Açıklama
                self.text.insert(tk.END, line + '\n', "info")
            elif line.startswith('   Öneri:'):
                # Öneri
                self.text.insert(tk.END, line + '\n', "warning")
            elif line.startswith('   Doktor Kontrolü:'):
                # Doktor kontrolü
                if 'Gerekli' in line or 'Acil' in line:
                    self.text.insert(tk.END, line + '\n', "danger")
                else:
                    self.text.insert(tk.END, line + '\n', "success")

            elif line.startswith('   📝 Not:'):
                # Not
                self.text.insert(tk.END, line + '\n', "info")
            elif line.startswith('   •'):
                # Liste öğesi
                self.text.insert(tk.END, line + '\n', "normal")
            elif line.startswith('Toplam Test Sayısı:') or line.startswith('Normal Sonuç:') or line.startswith('Anormal Sonuç:'):
                # İstatistikler
                self.text.insert(tk.END, line + '\n', "header")
            elif line.startswith('Detaylı Yorum') or line.startswith('Genel Değerlendirme'):
                # Veritabanı bilgileri
                self.text.insert(tk.END, line + '\n', "info")
            elif line.startswith('-') and len(line) > 10:
                # Ayırıcı çizgiler
                self.text.insert(tk.END, line + '\n', "separator")
            elif line.strip() == '':
                # Boş satırlar
                self.text.insert(tk.END, '\n')
            else:
                # Diğer satırlar
                self.text.insert(tk.END, line + '\n', "normal")
    
    def create_status_bar(self, parent):
        self.status_bar = tk.Label(
            parent,
            text="Hazır - PDF dosyası bekleniyor",
            font=("Arial", 9),
            fg=COLORS['text'],
            bg=COLORS['light'],
            relief='sunken',
            bd=1
        )
        self.status_bar.pack(fill=tk.X, pady=(10, 0))
    
    def update_status(self, message):
        self.status_bar.config(text=message)
        self.root.update()
    
    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="PDF Dosyası Seç",
            filetypes=[("PDF Dosyası", "*.pdf"), ("Tüm Dosyalar", "*.*")]
        )
        if file_path:
            self.analyze_pdf(file_path)
    
    def on_drop(self, event):
        file_path = event.data.strip('{}')
        if file_path.lower().endswith('.pdf'):
            self.analyze_pdf(file_path)
        else:
            messagebox.showerror("Hata", "Lütfen bir PDF dosyası bırakın.")
    
    def analyze_pdf(self, pdf_path):
        try:
            self.update_status("PDF analiz ediliyor...")
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, "🔄 PDF analiz ediliyor...\n\n", "info")
            
            df = extract_tests_from_pdf(pdf_path)
            if df.empty:
                self.text.insert(tk.END, "❌ PDF'den tahlil verisi bulunamadı!\n", "danger")
                self.update_status("Hata: Tahlil verisi bulunamadı")
                return
            
            # Tekrar eden testleri kaldır ve test isimlerini temizle
            original_count = len(df)
            
            # Test isimlerini temizle
            df['Tahlil'] = df['Tahlil'].apply(lambda x: " ".join(x.split()) if isinstance(x, str) else x)
            
            # Tekrar eden testleri kaldır
            df = df.drop_duplicates(subset=['Tahlil'], keep='first')
            unique_count = len(df)
            
            self.update_status("Veriler işleniyor...")
            self.text.insert(tk.END, f"✅ {unique_count} adet benzersiz test bulundu\n", "success")
            if original_count > unique_count:
                self.text.insert(tk.END, f"⚠️  {original_count - unique_count} adet tekrar eden test kaldırıldı\n", "warning")
            
            df['Durum'] = df.apply(durum_bul, axis=1)
            
            # Temel sonuçları göster
            self.show_basic_results(df)
            
            # DataFrame'i sakla
            self.current_df = df
            
            # Analiz butonunu etkinleştir
            self.analyze_btn.config(state='normal')
            
            self.update_status(f"Temel analiz tamamlandı - {unique_count} test bulundu")
            
        except Exception as e:
            self.text.insert(tk.END, f"\n❌ Hata: {e}\n", "danger")
            self.update_status(f"Hata: {e}")
    
    def show_basic_results(self, df):
        """Temel sonuçları gösterir"""
        self.text.insert(tk.END, "\n" + "="*60 + "\n", "separator")
        self.text.insert(tk.END, "📊 TEMEL SONUÇLAR\n", "title")
        self.text.insert(tk.END, "="*60 + "\n\n", "separator")
        
        # İstatistikler
        total_tests = len(df)
        critical_tests = len(df[df['Durum'] != 'Normal'])
        normal_tests = len(df[df['Durum'] == 'Normal'])
        
        self.text.insert(tk.END, f"📈 İSTATİSTİKLER:\n", "header")
        self.text.insert(tk.END, f"• Toplam Test Sayısı: {total_tests}\n", "normal")
        self.text.insert(tk.END, f"• Normal Sonuç: {normal_tests}\n", "success")
        self.text.insert(tk.END, f"• Anormal Sonuç: {critical_tests}\n", "warning")
        self.text.insert(tk.END, "\n")
        
        # Kritik sonuçları göster
        if critical_tests > 0:
            self.text.insert(tk.END, f"⚠️  KRİTİK SONUÇLAR ({critical_tests} adet):\n", "danger")
            self.text.insert(tk.END, "-" * 50 + "\n", "separator")
            
            for _, row in df[df['Durum'] != 'Normal'].iterrows():
                self.text.insert(tk.END, f"🔸 {row['Tahlil']}\n", "highlight")
                self.text.insert(tk.END, f"   Sonuç: {row['Sonuç']} {row['Birim']} ({row['Durum']})\n", "normal")
                self.text.insert(tk.END, f"   Referans: {row['Referans Alt']} - {row['Referans Üst']}\n", "info")
                self.text.insert(tk.END, "\n")
        
        self.text.insert(tk.END, "\n" + "="*60 + "\n", "separator")
        self.text.insert(tk.END, "💡 Detaylı analiz için 'Detaylı Analiz Et' butonuna basın\n", "info")
        self.text.insert(tk.END, "="*60 + "\n", "separator")
    
    def perform_detailed_analysis(self):
        """Detaylı analiz yapar"""
        if not hasattr(self, 'current_df') or self.current_df is None:
            self.text.insert(tk.END, "❌ Önce bir PDF dosyası yükleyin!\n", "danger")
            return
        
        try:
            self.update_status("Detaylı analiz yapılıyor...")
            
            # Mevcut sonuçları temizle
            self.text.delete(1.0, tk.END)
            self.text.insert(tk.END, "🔍 Detaylı analiz yapılıyor...\n\n", "info")
            
            df = self.current_df
            yorum_db = yorum_veritabani_yukle_ve_guncelle(df['Tahlil'].unique())
            
            self.update_status("Analiz tamamlanıyor...")
            analiz_sonuclari, kritik_sonuclar, normal_sonuclar = genel_analiz_olustur(df, yorum_db)
            rapor = rapor_olustur(analiz_sonuclari, kritik_sonuclar, normal_sonuclar)
            
            # Sonuçları formatlı göster
            self.format_report_text(rapor)
            
            # Debug bilgilerini de göster
            self.text.insert(tk.END, "\n\n🔍 DEBUG BİLGİLERİ:\n", "info")
            self.text.insert(tk.END, f"Toplam test sayısı: {len(df)}\n", "info")
            self.text.insert(tk.END, f"Kritik sonuç sayısı: {len(kritik_sonuclar)}\n", "info")
            self.text.insert(tk.END, f"Normal sonuç sayısı: {len(normal_sonuclar)}\n", "info")
            
            # Dosyaları kaydet
            df.to_csv("tahlil_sonuclari.csv", index=False)
            with open("tahlil_analiz_raporu.txt", "w", encoding="utf-8") as f:
                f.write(rapor)
            
            self.update_status(f"Detaylı analiz tamamlandı - {len(df)} test analiz edildi")
            
        except Exception as e:
            self.text.insert(tk.END, f"\n❌ Hata: {e}\n", "danger")
            self.update_status(f"Hata: {e}")

def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    
    # Pencere ikonu ve stil
    root.iconbitmap(default='')  # Varsayılan ikon
    
    app = TahlilApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
