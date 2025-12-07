"""
🔄 Hızlı Veritabanı Sıfırlama
Eski DB'yi siler, yenisini oluşturur
"""

import os
import sqlite3
from datetime import datetime

def quick_reset():
    """Veritabanını sil ve yeniden oluştur"""
    
    db_path = 'thorius_tokens.db'
    
    # Yedek al
    if os.path.exists(db_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = f"thorius_tokens_backup_{timestamp}.db"
        
        try:
            import shutil
            shutil.copy2(db_path, backup)
            print(f"✅ Yedek: {backup}")
        except:
            print("⚠️ Yedek alınamadı")
        
        # Eski DB'yi sil
        os.remove(db_path)
        print("🗑️ Eski veritabanı silindi")
    
    # Yeni DB oluştur
    print("🔄 Yeni veritabanı oluşturuluyor...")
    
    # token_manager.py'deki init fonksiyonunu çalıştır
    import sys
    sys.path.insert(0, '.')
    
    from token_manager import init_database, create_default_users
    
    init_database()
    create_default_users()
    
    print("✅ Veritabanı hazır!")
    
    # Demo kullanıcısına 300 token ekle
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute('''
        UPDATE users 
        SET remaining_tokens = 300,
            total_tokens = 300
        WHERE username = 'demo'
    ''')
    
    conn.commit()
    conn.close()
    
    print("💰 Demo kullanıcısı: 300 token")
    
    # Kullanıcıları göster
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    print("\n📊 Kullanıcılar:")
    c.execute('SELECT username, name, remaining_tokens FROM users')
    for user in c.fetchall():
        print(f"   • {user[1]}: {user[2]} token")
    
    conn.close()
    
    print("\n" + "="*50)
    print("✅ RESET TAMAMLANDI!")
    print("="*50)
    print("\nŞimdi uygulamayı başlatabilirsiniz:")
    print("  streamlit run Home.py")

if __name__ == "__main__":
    print("="*50)
    print("HIZLI VERITABANI RESET")
    print("="*50)
    print()
    
    response = input("⚠️ Veritabanı sıfırlanacak! Devam? (E/H): ")
    
    if response.upper() == 'E':
        print()
        quick_reset()
    else:
        print("❌ İptal edildi")
