# 🏥 Kan Tahlil Analiz Sistemi

Modern ve kullanıcı dostu bir kan tahlil analiz uygulaması. PDF formatındaki laboratuvar sonuçlarını otomatik olarak analiz eder, kritik değerleri tespit eder ve detaylı raporlar oluşturur.

## 📋 Özellikler

### 🔍 Ana Özellikler

- **PDF Analizi**: Laboratuvar sonuçlarını PDF formatından otomatik okuma
- **Akıllı Test Eşleştirme**: Benzer test isimlerini otomatik birleştirme
- **Kritik Değer Tespiti**: Normal aralık dışındaki sonuçları otomatik tespit
- **Detaylı Raporlama**: Kapsamlı analiz raporları ve öneriler
- **Modern GUI**: Hastane teması ile profesyonel kullanıcı arayüzü
- **Drag & Drop**: Dosya sürükle-bırak desteği

### 📊 Analiz Özellikleri

- **Temel Analiz**: Hızlı sonuç görüntüleme
- **Detaylı Analiz**: Kapsamlı yorum ve öneriler
- **İstatistiksel Özet**: Test sayıları ve durum dağılımı
- **CSV Export**: Sonuçları CSV formatında kaydetme
- **TXT Rapor**: Detaylı analiz raporunu metin dosyası olarak kaydetme

### 🎨 Kullanıcı Arayüzü

- **Hastane Teması**: Profesyonel mavi-beyaz renk paleti
- **Responsive Tasarım**: Farklı ekran boyutlarına uyum
- **Renkli Kodlama**: Durumlara göre renkli gösterim
- **Durum Çubuğu**: İşlem durumu hakkında anlık bilgi

## 🚀 Kurulum

### 🎯 Hızlı Kurulum (Önerilen)

Uygulamanın **exe dosyası** mevcuttur. Kurulum için:

1. **İndirme**: Proje dosyalarını bilgisayarınıza indirin
2. **Çalıştırma**: `KanTahlil.exe` dosyasına çift tıklayın
3. **Kullanım**: Uygulama otomatik olarak açılacaktır

### 🔧 Geliştirici Kurulumu

Eğer kaynak koddan çalıştırmak istiyorsanız:

#### Gereksinimler

- Python 3.7 veya üzeri
- Windows, macOS veya Linux

#### Kütüphane Kurulumu

```bash
# Ana kütüphaneler
pip install PyMuPDF
pip install pandas

# Opsiyonel drag & drop özelliği için
pip install tkinterdnd2
```

#### Kaynak Koddan Çalıştırma

```bash
# Projeyi klonlayın
git clone [repository-url]
cd KanTahlil

# Gerekli kütüphaneleri kurun
pip install -r requirements.txt

# Uygulamayı çalıştırın
python analysisMachine.py
```

## 📖 Kullanım Kılavuzu

### 1. Uygulamayı Başlatma

**Exe Dosyası ile:**

- `KanTahlil.exe` dosyasına çift tıklayın

**Kaynak Koddan:**

```bash
python analysisMachine.py
```

### 2. PDF Dosyası Yükleme

- **Dosya Seçme**: "📁 PDF Dosyası Seç" butonuna tıklayın
- **Sürükle-Bırak**: PDF dosyasını uygulama penceresine sürükleyin

### 3. Analiz Süreci

1. **Temel Analiz**: PDF yüklendikten sonra otomatik olarak temel sonuçlar görüntülenir
2. **Detaylı Analiz**: "🔍 Detaylı Analiz Et" butonuna tıklayarak kapsamlı analiz başlatın

### 4. Sonuçları İnceleme

- **Kritik Sonuçlar**: Normal aralık dışındaki değerler kırmızı ile işaretlenir
- **Normal Sonuçlar**: Normal aralıktaki değerler yeşil ile gösterilir
- **Detaylı Yorumlar**: Her test için açıklama ve öneriler

### 5. Dosya Kaydetme

Analiz tamamlandıktan sonra otomatik olarak şu dosyalar oluşturulur:

- `tahlil_sonuclari.csv`: Tüm test sonuçları
- `tahlil_analiz_raporu.txt`: Detaylı analiz raporu

## 🔧 Teknik Detaylar

### Dosya Yapısı

```
KanTahlil/
├── KanTahlil.exe           # Ana uygulama (exe dosyası)
├── analysisMachine.py      # Ana uygulama dosyası (kaynak kod)
├── test_analysis.py        # Test analiz modülü
├── yorum_veritabani.json  # Test yorumları veritabanı
├── requirements.txt        # Gerekli kütüphaneler
├── tahlil_sonuclari.csv   # Analiz sonuçları (otomatik oluşur)
├── tahlil_analiz_raporu.txt # Detaylı rapor (otomatik oluşur)
└── README.md              # Bu dosya
```

### Ana Fonksiyonlar

#### PDF Analizi

- `extract_tests_from_pdf()`: PDF'den test verilerini çıkarır
- `normalize_test_name()`: Test isimlerini normalize eder
- `merge_similar_tests()`: Benzer testleri birleştirir

#### Veri İşleme

- `durum_bul()`: Test sonuçlarının durumunu belirler
- `find_best_match()`: Test isimlerini veritabanıyla eşleştirir
- `genel_analiz_olustur()`: Kapsamlı analiz oluşturur

#### GUI Bileşenleri

- `TahlilApp`: Ana uygulama sınıfı
- `HospitalStyleFrame`: Özel stil çerçevesi
- `create_control_panel()`: Kontrol paneli oluşturur
- `create_result_panel()`: Sonuç paneli oluşturur

### Veri Formatları

#### CSV Çıktısı

```csv
Tahlil,Sonuç,Birim,Referans Alt,Referans Üst,Durum
Hemoglobin,14.8,g/dL,13.5,16.9,Normal
```

#### JSON Veritabanı

```json
{
  "Test Adı": {
    "dusuk": {
      "aciklama": "Açıklama",
      "oneri": "Öneri",
      "doktor_kontrolu": "Gerekli"
    }
  }
}
```

## 🎯 Desteklenen Testler

### Kan Sayımı

- Hemoglobin, Hematokrit, RBC, WBC
- Trombosit (PLT), MCV, MCH, MCHC
- Nötrofil, Lenfosit, Monosit, Eozinofil, Bazofil

### Biyokimya

- Glukoz (Açlık Kan Şekeri)
- Üre, Kreatinin
- ALT, AST, GGT, LDH
- Bilirubin (Total)

### Lipid Profili

- LDL Kolesterol
- HDL Kolesterol
- Trigliserid

### Diğer

- Demir (Serum)
- Kreatin Kinaz
- Ve daha fazlası...

## 🔍 Analiz Özellikleri

### Otomatik Durum Tespiti

- **Normal**: Referans aralığı içinde
- **Düşük**: Referans alt sınırının altında
- **Yüksek**: Referans üst sınırının üstünde

### Akıllı Test Eşleştirme

- Benzer test isimlerini otomatik birleştirme
- Gereksiz ön ekleri temizleme
- Tekrar eden testleri kaldırma

### Detaylı Yorum Sistemi

- Her test için özel açıklamalar
- Duruma göre öneriler
- Doktor kontrolü gerekliliği

## 🛠️ Geliştirme

### Yeni Test Ekleme

`yorum_veritabani.json` dosyasına yeni testler ekleyebilirsiniz:

```json
{
  "Yeni Test Adı": {
    "dusuk": {
      "aciklama": "Düşük değer açıklaması",
      "oneri": "Öneri",
      "doktor_kontrolu": "Gerekli"
    },
    "yuksek": {
      "aciklama": "Yüksek değer açıklaması",
      "oneri": "Öneri",
      "doktor_kontrolu": "Acil"
    },
    "normal": {
      "aciklama": "Normal değer açıklaması",
      "oneri": "Öneri",
      "doktor_kontrolu": "Gerekli değil"
    }
  }
}
```

### Tema Özelleştirme

`COLORS` sözlüğünü değiştirerek renk temasını özelleştirebilirsiniz:

```python
COLORS = {
    'primary': '#1e3a8a',      # Ana renk
    'secondary': '#3b82f6',    # İkincil renk
    'success': '#10b981',      # Başarı rengi
    'warning': '#f59e0b',      # Uyarı rengi
    'danger': '#ef4444',       # Tehlike rengi
    # ...
}
```

## 📝 Lisans

Bu proje açık kaynak kodludur ve eğitim amaçlı kullanım için tasarlanmıştır.

## ⚠️ Önemli Notlar

### Tıbbi Uyarı

- Bu uygulama sadece **bilgilendirme amaçlıdır**
- **Kesinlikle tıbbi tanı yerine geçmez**
- **Her zaman doktorunuza danışın**
- Kritik sonuçlar için mutlaka uzman hekim kontrolü gerekir

### Teknik Sınırlamalar

- PDF formatı laboratuvar raporlarına özel olarak tasarlanmıştır
- Farklı laboratuvar formatları için uyarlama gerekebilir
- İnternet bağlantısı gerektirmez (tamamen yerel çalışır)

## 🤝 Katkıda Bulunma

1. Projeyi fork edin
2. Yeni özellik dalı oluşturun (`git checkout -b feature/yeni-ozellik`)
3. Değişikliklerinizi commit edin (`git commit -am 'Yeni özellik eklendi'`)
4. Dalınızı push edin (`git push origin feature/yeni-ozellik`)
5. Pull Request oluşturun

## 📞 İletişim

Sorularınız veya önerileriniz için:

- GitHub Issues kullanın
- Proje sayfasında tartışma başlatın

## 🔄 Güncellemeler

### v2.0

- Modern GUI tasarımı
- Drag & Drop desteği
- Gelişmiş analiz algoritmaları
- Detaylı raporlama sistemi
- Hastane teması

### v1.0

- Temel PDF analizi
- Basit GUI
- CSV export

---

**🏥 Sağlıklı günler dileriz!**
