# ==============================================
# MERKEZI TOKEN YÖNETİM SİSTEMİ
# ==============================================
# Bu dosya TÜM modüllerde kullanılacak
# Her modül bu sistemi import edecek

import sqlite3
import hashlib
from datetime import datetime, timedelta
import streamlit as st

# ==============================================
# VERİTABANI YAPISI
# ==============================================

def init_database():
    """Token veritabanını oluştur"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    # Kullanıcı tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password_hash TEXT NOT NULL,
            name TEXT NOT NULL,
            title TEXT NOT NULL,
            role TEXT NOT NULL,
            total_tokens INTEGER DEFAULT 100,
            remaining_tokens INTEGER DEFAULT 100,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Token hareketleri tablosu
    c.execute('''
        CREATE TABLE IF NOT EXISTS token_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            module TEXT NOT NULL,
            token_cost INTEGER NOT NULL,
            remaining_after INTEGER NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            session_id TEXT,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    # Son giriş tablosu (6 saat kuralı için)
    c.execute('''
        CREATE TABLE IF NOT EXISTS last_logins (
            username TEXT PRIMARY KEY,
            module TEXT NOT NULL,
            last_login TIMESTAMP NOT NULL,
            last_login_date DATE NOT NULL,
            login_count_today INTEGER DEFAULT 0,
            FOREIGN KEY (username) REFERENCES users(username)
        )
    ''')
    
    conn.commit()
    conn.close()

def create_default_users():
    """Varsayılan kullanıcıları oluştur"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    users = [
        ("ertugrul", "lojistik2025", "Ertuğrul Bey", "Lojistik GMY", "sponsor"),
        ("gokhan", "ecom2025", "Gökhan Bey", "ECOM GMY", "sponsor"),
        ("volkan", "magaza2025", "Volkan Bey", "Mağazacılık GMY", "manager"),
        ("ferhat", "stok2025", "Ferhat Bey", "Stok Yönetimi Direktörü", "manager"),
        ("tayfun", "eve2025", "Tayfun Bey", "EVE GM", "manager"),
        ("aliakcay", "tzy2025", "Ali Akçay", "EVE TZY Direktörü", "user"),
        ("ozcan", "it2025", "Özcan Bey", "IT GMY", "admin"),
        ("demo", "demo2025", "Demo Kullanıcı", "Misafir", "viewer"),
    ]
    
    for username, password, name, title, role in users:
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        # Kullanıcı zaten varsa güncelle, yoksa ekle
        c.execute('''
            INSERT INTO users (username, password_hash, name, title, role)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(username) DO UPDATE SET
                password_hash = excluded.password_hash,
                name = excluded.name,
                title = excluded.title,
                role = excluded.role
        ''', (username, password_hash, name, title, role))
    
    conn.commit()
    conn.close()

# ==============================================
# MODÜL TOKEN MALİYETLERİ
# ==============================================

MODULE_TOKEN_COSTS = {
    "oms_proje": 1,           # OMS Depo Birleştirme Projesi
    "sevkiyat": 10,           # Sevkiyat Yönetimi
    "sevkiyat_po": 10,        # Sevkiyat & PO Yönetimi
    "budget_forecast": 8,     # Bütçe Forecast Modülü
    "model_budget": 8,        # Model Bütçe Sipariş Modülü
    "kapasite": 5,            # Kapasite Planlama
    "transfer": 5,            # Transfer & İade
    "wssi": 6,                # WSSI Analysis
    "pricing": 7,             # İndirim & Fiyatlandırma
    "clustering": 8,          # Clustering
}

# ==============================================
# TOKEN İŞLEMLERİ
# ==============================================

def authenticate_user(username, password):
    """Kullanıcı doğrulama"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    password_hash = hashlib.sha256(password.encode()).hexdigest()
    
    c.execute('''
        SELECT username, name, title, role, remaining_tokens
        FROM users
        WHERE username = ? AND password_hash = ?
    ''', (username, password_hash))
    
    user = c.fetchone()
    conn.close()
    
    if user:
        return {
            "username": user[0],
            "name": user[1],
            "title": user[2],
            "role": user[3],
            "remaining_tokens": user[4]
        }
    return None

def check_token_charge(username, module):
    """
    Token düşüp düşmeyeceğini kontrol et
    6 saat kuralı:
    - İlk giriş → token düşer
    - Aynı gün < 6 saat → token düşmez
    - Aynı gün > 6 saat → token düşer
    - Yeni gün → token düşer
    """
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    now = datetime.now()
    today = now.date()
    
    # Son giriş bilgisini al
    c.execute('''
        SELECT last_login, last_login_date
        FROM last_logins
        WHERE username = ? AND module = ?
    ''', (username, module))
    
    result = c.fetchone()
    conn.close()
    
    # İlk giriş
    if not result:
        return True
    
    last_login = datetime.fromisoformat(result[0])
    last_date = datetime.fromisoformat(result[1]).date()
    
    # Yeni gün mü?
    if last_date != today:
        return True
    
    # Aynı gün - 6 saat kontrolü
    hours_diff = (now - last_login).total_seconds() / 3600
    
    return hours_diff >= 6

def charge_token(username, module, session_id=None):
    """
    Token düş ve kaydet
    Returns: (success, remaining_tokens, message)
    """
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    # Modül token maliyeti
    token_cost = MODULE_TOKEN_COSTS.get(module, 1)
    
    # Mevcut bakiye
    c.execute('SELECT remaining_tokens FROM users WHERE username = ?', (username,))
    result = c.fetchone()
    
    if not result:
        conn.close()
        return False, 0, "Kullanıcı bulunamadı"
    
    remaining = result[0]
    
    # Yeterli token var mı?
    if remaining < token_cost:
        conn.close()
        return False, remaining, f"Yetersiz token! Gerekli: {token_cost}, Mevcut: {remaining}"
    
    # Token düş
    new_remaining = remaining - token_cost
    
    c.execute('''
        UPDATE users
        SET remaining_tokens = ?
        WHERE username = ?
    ''', (new_remaining, username))
    
    # İşlemi kaydet
    c.execute('''
        INSERT INTO token_transactions (username, module, token_cost, remaining_after, session_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, module, token_cost, new_remaining, session_id))
    
    # Son giriş bilgisini güncelle
    now = datetime.now()
    today = now.date()
    
    c.execute('''
        INSERT INTO last_logins (username, module, last_login, last_login_date, login_count_today)
        VALUES (?, ?, ?, ?, 1)
        ON CONFLICT(username) DO UPDATE SET
            module = excluded.module,
            last_login = excluded.last_login,
            last_login_date = excluded.last_login_date,
            login_count_today = CASE 
                WHEN last_login_date = excluded.last_login_date 
                THEN login_count_today + 1 
                ELSE 1 
            END
    ''', (username, module, now, today))
    
    conn.commit()
    conn.close()
    
    return True, new_remaining, f"{token_cost} token düşüldü"

def get_token_balance(username):
    """Token bakiyesini getir"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''
        SELECT total_tokens, remaining_tokens
        FROM users
        WHERE username = ?
    ''', (username,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            "total": result[0],
            "remaining": result[1],
            "used": result[0] - result[1],
            "percent": int(((result[0] - result[1]) / result[0]) * 100)
        }
    return None

def get_today_stats(username):
    """Bugünkü kullanım istatistikleri"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    today = datetime.now().date()
    
    # Bugünkü işlemler
    c.execute('''
        SELECT COUNT(*), SUM(token_cost)
        FROM token_transactions
        WHERE username = ? AND DATE(timestamp) = ?
    ''', (username, today))
    
    result = c.fetchone()
    
    # Son giriş bilgisi
    c.execute('''
        SELECT last_login, module
        FROM last_logins
        WHERE username = ?
    ''', (username,))
    
    last_login_result = c.fetchone()
    conn.close()
    
    transactions_count = result[0] or 0
    tokens_used = result[1] or 0
    
    last_login = None
    last_module = None
    hours_since = None
    
    if last_login_result:
        last_login = datetime.fromisoformat(last_login_result[0])
        last_module = last_login_result[1]
        hours_since = (datetime.now() - last_login).total_seconds() / 3600
    
    return {
        "transactions_today": transactions_count,
        "tokens_used_today": tokens_used,
        "last_login": last_login,
        "last_module": last_module,
        "hours_since_login": hours_since
    }

def get_transaction_history(username, limit=10):
    """Token işlem geçmişi"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''
        SELECT module, token_cost, remaining_after, timestamp
        FROM token_transactions
        WHERE username = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (username, limit))
    
    transactions = c.fetchall()
    conn.close()
    
    return [
        {
            "module": t[0],
            "cost": t[1],
            "remaining": t[2],
            "timestamp": datetime.fromisoformat(t[3])
        }
        for t in transactions
    ]

def add_tokens(username, amount, admin_username):
    """Token ekle (admin işlemi)"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    # Admin kontrolü
    c.execute('SELECT role FROM users WHERE username = ?', (admin_username,))
    admin = c.fetchone()
    
    if not admin or admin[0] not in ['admin', 'sponsor']:
        conn.close()
        return False, "Yetkiniz yok!"
    
    # Token ekle
    c.execute('''
        UPDATE users
        SET remaining_tokens = remaining_tokens + ?,
            total_tokens = total_tokens + ?
        WHERE username = ?
    ''', (amount, amount, username))
    
    # İşlem kaydı
    c.execute('SELECT remaining_tokens FROM users WHERE username = ?', (username,))
    new_balance = c.fetchone()[0]
    
    c.execute('''
        INSERT INTO token_transactions (username, module, token_cost, remaining_after, session_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (username, f"admin_add_by_{admin_username}", -amount, new_balance, None))
    
    conn.commit()
    conn.close()
    
    return True, f"{amount} token eklendi. Yeni bakiye: {new_balance}"

# ==============================================
# STREAMLIT ENTEGRASYONU
# ==============================================

def init_token_system_for_app():
    """Streamlit uygulaması için token sistemi başlat"""
    init_database()
    create_default_users()

def render_token_widget(username):
    """Sidebar token widget'i render et"""
    balance = get_token_balance(username)
    stats = get_today_stats(username)
    
    if not balance:
        return
    
    # Progress bar rengi
    if balance["percent"] < 50:
        bar_color = "#00ff88"  # Yeşil
    elif balance["percent"] < 75:
        bar_color = "#ffa500"  # Turuncu
    else:
        bar_color = "#ff4444"  # Kırmızı
    
    st.sidebar.markdown(f"""
    <div style='padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; margin-bottom: 15px;'>
        <div style='text-align: center; margin-bottom: 10px;'>
            <div style='font-size: 0.9rem; color: #999; margin-bottom: 5px;'>🪙 Token Bakiyesi</div>
            <div style='font-size: 2rem; font-weight: 700; color: {bar_color};'>{balance["remaining"]}</div>
            <div style='font-size: 0.8rem; color: #666;'>/ {balance["total"]} token</div>
        </div>
        <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; overflow: hidden;'>
            <div style='background: {bar_color}; height: 100%; width: {100-balance["percent"]}%; transition: width 0.3s;'></div>
        </div>
        <div style='text-align: center; margin-top: 8px; font-size: 0.75rem; color: #888;'>
            Kullanılan: {balance["used"]} token (%{balance["percent"]})
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Bugünkü istatistikler
    st.sidebar.markdown("##### 📊 Bugünkü Kullanım")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        st.metric("İşlem", stats["transactions_today"])
    with col2:
        st.metric("Token", stats["tokens_used_today"])
    
    # Son giriş
    if stats["last_login"]:
        hours = int(stats["hours_since_login"])
        minutes = int((stats["hours_since_login"] % 1) * 60)
        
        st.sidebar.caption(f"🕐 Son: {stats['last_module']} ({hours}s {minutes}dk)")
        
        if hours < 6:
            remaining_hours = 6 - hours
            st.sidebar.info(f"⏱️ {remaining_hours} saat içinde token düşmeyecek")

# ==============================================
# ÖRNEK KULLANIM
# ==============================================

if __name__ == "__main__":
    # Sistem başlat
    init_database()
    create_default_users()
    
    # Test
    print("✅ Token sistemi hazır!")
    print("\n📊 Kullanıcılar:")
    
    conn = sqlite3.connect('thorius_tokens.db')
    c = conn.cursor()
    c.execute('SELECT username, name, remaining_tokens FROM users')
    for user in c.fetchall():
        print(f"   {user[0]}: {user[1]} - {user[2]} token")
    conn.close()
