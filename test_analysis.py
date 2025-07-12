import json
import pandas as pd
from analysisMachine import find_best_match, yorum_veritabani_yukle_ve_guncelle, durum_key

# JSON veritabanını yükle
with open('yorum_veritabani.json', 'r', encoding='utf-8') as f:
    yorum_db = json.load(f)

# CSV dosyasını oku
df = pd.read_csv('tahlil_sonuclari.csv')

print("Test eşleştirme sonuçları:")
print("=" * 50)

for _, row in df.iterrows():
    test_adi = row['Tahlil']
    durum = row['Durum']
    
    matched_test = find_best_match(test_adi, yorum_db)
    
    if matched_test:
        print(f"✅ {test_adi} -> {matched_test}")
    else:
        print(f"❌ {test_adi} -> Eşleşme bulunamadı")

print("\n" + "=" * 50)
print("Kritik sonuçlar:")
print("=" * 50)

for _, row in df.iterrows():
    if row['Durum'] != 'Normal':
        test_adi = row['Tahlil']
        matched_test = find_best_match(test_adi, yorum_db)
        
        durum_key_normalized = durum_key(row['Durum'])
        
        if matched_test and durum_key_normalized in yorum_db[matched_test]:
            yorum = yorum_db[matched_test][durum_key_normalized]
            print(f"🔸 {test_adi}")
            print(f"   Sonuç: {row['Sonuç']} {row['Birim']} ({row['Durum']})")
            print(f"   Açıklama: {yorum['aciklama']}")
            print(f"   Öneri: {yorum['oneri']}")
            print(f"   Doktor Kontrolü: {yorum['doktor_kontrolu']}")
            print()
        elif matched_test:
            print(f"🔸 {test_adi}")
            print(f"   Sonuç: {row['Sonuç']} {row['Birim']} ({row['Durum']})")
            print(f"   Açıklama: {test_adi} seviyesi {row['Durum'].lower()} - doktor kontrolü gerekli")
            print(f"   Öneri: Doktorunuza danışınız ve gerekli önlemleri alınız.")
            print(f"   Doktor Kontrolü: Gerekli")
            print(f"   Not: Test eşleşti ama durum bilgisi bulunamadı")
            print(f"   Debug: Durum: '{durum_key_normalized}', Mevcut durumlar: {list(yorum_db[matched_test].keys())}")
            print()
        else:
            print(f"🔸 {test_adi}")
            print(f"   Sonuç: {row['Sonuç']} {row['Birim']} ({row['Durum']})")
            print(f"   Açıklama: {test_adi} seviyesi {row['Durum'].lower()} - doktor kontrolü gerekli")
            print(f"   Öneri: Doktorunuza danışınız ve gerekli önlemleri alınız.")
            print(f"   Doktor Kontrolü: Gerekli")
            print() 