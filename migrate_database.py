"""
Thorius AR4U - Veritabanı Migration
Eski veritabanını yeni yapıya çevirir
"""

import sqlite3
import shutil
from datetime import datetime

def backup_database():
    """Veritabanını yedekle"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"thorius_tokens_backup_{timestamp}.db"
        shutil.copy2('thorius_tokens.db', backup_name)
        print(f"✅ Yedek oluşturuldu: {backup_name}")
        return True
    except Exception as e:
        print(f"⚠️ Yedek oluşturulamadı: {e}")
        return False

def migrate_last_logins():
    """last_logins tablosunu yeni yapıya çevir"""
    
    conn = sqlite3.connect('thorius_tokens.db')
    c = conn.cursor()
    
    try:
        # Eski yapıyı kontrol et
        c.execute("PRAGMA table_info(last_logins)")
        columns = [col[1] for col in c.fetchall()]
        
        print(f"📊 Mevcut sütunlar: {columns}")
        
        # Eski verileri yedekle
        c.execute("SELECT * FROM last_logins")
        old_data = c.fetchall()
        print(f"📦 {len(old_data)} kayıt bulundu")
        
        # Eski tabloyu sil
        c.execute("DROP TABLE IF EXISTS last_logins")
        print("🗑️ Eski tablo silindi")
        
        # Yeni tabloyu oluştur (PRIMARY KEY: username, module)
        c.execute('''
            CREATE TABLE last_logins (
                username TEXT NOT NULL,
                module TEXT NOT NULL,
                last_login TIMESTAMP NOT NULL,
                last_login_date DATE NOT NULL,
                login_count_today INTEGER DEFAULT 0,
                PRIMARY KEY (username, module),
                FOREIGN KEY (username) REFERENCES users(username)
            )
        ''')
        print("✅ Yeni tablo oluşturuldu")
        
        # Verileri geri yükle (sadece username, module kombinasyonları)
        if old_data:
            for row in old_data:
                try:
                    if len(row) >= 5:
                        c.execute('''
                            INSERT OR IGNORE INTO last_logins 
                            (username, module, last_login, last_login_date, login_count_today)
                            VALUES (?, ?, ?, ?, ?)
                        ''', row[:5])
                except Exception as e:
                    print(f"⚠️ Satır atlandı: {e}")
            
            print(f"✅ Veriler geri yüklendi")
        
        conn.commit()
        print("✅ Migration tamamlandı!")
        
    except Exception as e:
        print(f"❌ Hata: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()
    
    return True

def verify_migration():
    """Migration'ı doğrula"""
    conn = sqlite3.connect('thorius_tokens.db')
    c = conn.cursor()
    
    print("\n🔍 Migration Doğrulaması:")
    
    # Tablo yapısını kontrol et
    c.execute("PRAGMA table_info(last_logins)")
    print("\n📋 Yeni tablo yapısı:")
    for col in c.fetchall():
        print(f"   {col[1]} ({col[2]})")
    
    # Primary key kontrolü
    c.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='last_logins'")
    sql = c.fetchone()[0]
    if "PRIMARY KEY (username, module)" in sql:
        print("\n✅ PRIMARY KEY doğru: (username, module)")
    else:
        print("\n❌ PRIMARY KEY yanlış!")
    
    # Veri kontrolü
    c.execute("SELECT COUNT(*) FROM last_logins")
    count = c.fetchone()[0]
    print(f"\n📊 Toplam kayıt: {count}")
    
    # Örnek kayıtlar
    if count > 0:
        print("\n📄 İlk 5 kayıt:")
        c.execute("SELECT username, module, last_login_date FROM last_logins LIMIT 5")
        for row in c.fetchall():
            print(f"   {row[0]} / {row[1]} / {row[2]}")
    
    conn.close()

if __name__ == "__main__":
    print("=" * 60)
    print("THORIUS AR4U - VERITABANI MIGRATION")
    print("=" * 60)
    print()
    
    # 1. Yedek al
    print("1️⃣ Veritabanı yedekleniyor...")
    if not backup_database():
        print("\n⚠️ Yedek alınamadı ama devam ediliyor...")
    
    print()
    
    # 2. Migration yap
    print("2️⃣ Migration başlıyor...")
    if migrate_last_logins():
        print()
        
        # 3. Doğrula
        print("3️⃣ Migration doğrulanıyor...")
        verify_migration()
        
        print()
        print("=" * 60)
        print("✅ MIGRATION BAŞARILI!")
        print("=" * 60)
        print("\nŞimdi uygulamayı başlatabilirsiniz:")
        print("  streamlit run Home.py")
    else:
        print()
        print("=" * 60)
        print("❌ MIGRATION BAŞARISIZ!")
        print("=" * 60)
        print("\nYedek dosyayı geri yükleyin.")
