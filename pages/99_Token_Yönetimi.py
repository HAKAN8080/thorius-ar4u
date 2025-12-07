"""
🔐 Token Yönetim Paneli
Thorius AR4U - Admin Dashboard
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd

# Page config
st.set_page_config(
    page_title="Token Yonetimi",
    page_icon="🔐",
    layout="wide"
)

# ==================== AUTHENTICATION ====================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Lutfen giris yapin!")
    st.stop()

# Admin kontrolü - Sadece hakan kullanıcısı görebilir
current_user = st.session_state.get('username', '')
if current_user.lower() != 'hakan':
    st.error("❌ Bu sayfaya erişim yetkiniz yok!")
    st.info("💡 Bu sayfa sadece admin kullanıcıları içindir.")
    st.stop()

# ==================== HEADER ====================
st.title("🔐 Token Yonetim Paneli")
st.markdown("---")

# ==================== FUNCTIONS ====================

def get_all_users():
    """Tüm kullanıcıları getir"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    df = pd.read_sql_query('''
        SELECT 
            username,
            name,
            email,
            role,
            remaining_tokens,
            total_tokens
        FROM users
        ORDER BY name
    ''', conn)
    conn.close()
    return df

def get_token_transactions(limit=50):
    """Son token işlemlerini getir"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    df = pd.read_sql_query(f'''
        SELECT 
            username,
            module,
            token_cost,
            remaining_after,
            datetime(timestamp, 'localtime') as timestamp
        FROM token_transactions
        ORDER BY timestamp DESC
        LIMIT {limit}
    ''', conn)
    conn.close()
    return df

def add_tokens(username, amount):
    """Kullanıcıya token ekle"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        # Mevcut bakiyeyi al
        c.execute('SELECT remaining_tokens FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        
        if not result:
            return False, "Kullanıcı bulunamadı"
        
        current = result[0]
        new_balance = current + amount
        
        # Token ekle
        c.execute('''
            UPDATE users 
            SET remaining_tokens = ?,
                total_tokens = total_tokens + ?
            WHERE username = ?
        ''', (new_balance, amount, username))
        
        # İşlemi kaydet
        c.execute('''
            INSERT INTO token_transactions (username, module, token_cost, remaining_after, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, 'ADMIN_ADD', -amount, new_balance, f'admin_{datetime.now().timestamp()}'))
        
        conn.commit()
        return True, f"✅ {amount} token eklendi. Yeni bakiye: {new_balance}"
        
    except Exception as e:
        conn.rollback()
        return False, f"❌ Hata: {str(e)}"
    finally:
        conn.close()

def remove_tokens(username, amount):
    """Kullanıcıdan token çıkar"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        # Mevcut bakiyeyi al
        c.execute('SELECT remaining_tokens FROM users WHERE username = ?', (username,))
        result = c.fetchone()
        
        if not result:
            return False, "Kullanıcı bulunamadı"
        
        current = result[0]
        
        if current < amount:
            return False, f"❌ Yetersiz token! Mevcut: {current}, İstenen: {amount}"
        
        new_balance = current - amount
        
        # Token çıkar
        c.execute('''
            UPDATE users 
            SET remaining_tokens = ?
            WHERE username = ?
        ''', (new_balance, username))
        
        # İşlemi kaydet
        c.execute('''
            INSERT INTO token_transactions (username, module, token_cost, remaining_after, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, 'ADMIN_REMOVE', amount, new_balance, f'admin_{datetime.now().timestamp()}'))
        
        conn.commit()
        return True, f"✅ {amount} token çıkarıldı. Yeni bakiye: {new_balance}"
        
    except Exception as e:
        conn.rollback()
        return False, f"❌ Hata: {str(e)}"
    finally:
        conn.close()

def reset_user_tokens(username, amount):
    """Kullanıcı token'ını sıfırla ve yeni değer ata"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    try:
        # Token'ı sıfırla
        c.execute('''
            UPDATE users 
            SET remaining_tokens = ?,
                total_tokens = ?
            WHERE username = ?
        ''', (amount, amount, username))
        
        # İşlemi kaydet
        c.execute('''
            INSERT INTO token_transactions (username, module, token_cost, remaining_after, session_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, 'ADMIN_RESET', 0, amount, f'admin_{datetime.now().timestamp()}'))
        
        conn.commit()
        return True, f"✅ Token sıfırlandı. Yeni bakiye: {amount}"
        
    except Exception as e:
        conn.rollback()
        return False, f"❌ Hata: {str(e)}"
    finally:
        conn.close()

# ==================== TABS ====================
tab1, tab2, tab3 = st.tabs(["👥 Kullanicilar", "📊 Islem Gecmisi", "⚙️ Toplu Islemler"])

# ==================== TAB 1: KULLANICILAR ====================
with tab1:
    st.subheader("👥 Kullanici Token Yonetimi")
    
    # Kullanıcıları getir
    df_users = get_all_users()
    
    # Filtreleme
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Kullanıcı Ara", placeholder="İsim veya email...")
    with col2:
        role_filter = st.selectbox("Rol", ["Tümü"] + df_users['role'].unique().tolist())
    
    # Filtre uygula
    if search:
        df_filtered = df_users[
            df_users['name'].str.contains(search, case=False, na=False) |
            df_users['email'].str.contains(search, case=False, na=False) |
            df_users['username'].str.contains(search, case=False, na=False)
        ]
    else:
        df_filtered = df_users
    
    if role_filter != "Tümü":
        df_filtered = df_filtered[df_filtered['role'] == role_filter]
    
    # Kullanıcı tablosu
    st.dataframe(
        df_filtered[['username', 'name', 'email', 'role', 'remaining_tokens', 'total_tokens']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Token işlemleri
    st.subheader("💰 Token İşlemleri")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### ➕ Token Ekle")
        selected_user_add = st.selectbox("Kullanıcı Seç", df_users['username'].tolist(), key="add_user")
        amount_add = st.number_input("Eklenecek Token", min_value=1, max_value=1000, value=100, key="add_amount")
        
        if st.button("✅ Token Ekle", type="primary"):
            success, message = add_tokens(selected_user_add, amount_add)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col2:
        st.markdown("### ➖ Token Çıkar")
        selected_user_remove = st.selectbox("Kullanıcı Seç", df_users['username'].tolist(), key="remove_user")
        amount_remove = st.number_input("Çıkarılacak Token", min_value=1, max_value=1000, value=10, key="remove_amount")
        
        if st.button("⚠️ Token Çıkar", type="secondary"):
            success, message = remove_tokens(selected_user_remove, amount_remove)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
    with col3:
        st.markdown("### 🔄 Token Sıfırla")
        selected_user_reset = st.selectbox("Kullanıcı Seç", df_users['username'].tolist(), key="reset_user")
        amount_reset = st.number_input("Yeni Token Değeri", min_value=0, max_value=1000, value=100, key="reset_amount")
        
        if st.button("🔄 Sıfırla", type="secondary"):
            success, message = reset_user_tokens(selected_user_reset, amount_reset)
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

# ==================== TAB 2: İŞLEM GEÇMİŞİ ====================
with tab2:
    st.subheader("📊 Token İşlem Geçmişi")
    
    # Filtreleme
    col1, col2, col3 = st.columns(3)
    with col1:
        history_limit = st.selectbox("Göster", [50, 100, 200, 500], index=0)
    with col2:
        user_filter = st.selectbox("Kullanıcı", ["Tümü"] + df_users['username'].tolist())
    with col3:
        module_filter = st.selectbox("Modül", ["Tümü", "oms_proje", "budget_forecast", "sevkiyat_ml", "ADMIN_ADD", "ADMIN_REMOVE", "ADMIN_RESET"])
    
    # İşlemleri getir
    df_transactions = get_token_transactions(history_limit)
    
    # Filtre uygula
    if user_filter != "Tümü":
        df_transactions = df_transactions[df_transactions['username'] == user_filter]
    if module_filter != "Tümü":
        df_transactions = df_transactions[df_transactions['module'] == module_filter]
    
    # Tablo
    st.dataframe(
        df_transactions,
        use_container_width=True,
        hide_index=True,
        column_config={
            "token_cost": st.column_config.NumberColumn("Token", format="%d"),
            "remaining_after": st.column_config.NumberColumn("Kalan", format="%d"),
            "timestamp": st.column_config.DatetimeColumn("Tarih", format="DD/MM/YYYY HH:mm:ss")
        }
    )
    
    # İstatistikler
    st.markdown("---")
    st.subheader("📈 İstatistikler")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_transactions = len(df_transactions)
        st.metric("Toplam İşlem", total_transactions)
    
    with col2:
        total_spent = df_transactions[df_transactions['token_cost'] > 0]['token_cost'].sum()
        st.metric("Harcanan Token", int(total_spent))
    
    with col3:
        total_added = df_transactions[df_transactions['token_cost'] < 0]['token_cost'].sum()
        st.metric("Eklenen Token", int(abs(total_added)))
    
    with col4:
        unique_users = df_transactions['username'].nunique()
        st.metric("Aktif Kullanıcı", unique_users)

# ==================== TAB 3: TOPLU İŞLEMLER ====================
with tab3:
    st.subheader("⚙️ Toplu İşlemler")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🎁 Tüm Kullanıcılara Token Ekle")
        bulk_amount = st.number_input("Her kullanıcıya eklenecek token", min_value=1, max_value=500, value=50)
        
        if st.button("🎁 Toplu Token Ekle", type="primary"):
            success_count = 0
            for username in df_users['username']:
                success, _ = add_tokens(username, bulk_amount)
                if success:
                    success_count += 1
            
            st.success(f"✅ {success_count} kullanıcıya {bulk_amount} token eklendi!")
            st.rerun()
    
    with col2:
        st.markdown("### 🔄 Tüm Kullanıcıları Sıfırla")
        reset_amount = st.number_input("Yeni token değeri", min_value=0, max_value=500, value=100)
        
        st.warning("⚠️ Bu işlem GERİ ALINAMAZ!")
        
        if st.button("🔄 Toplu Sıfırla", type="secondary"):
            success_count = 0
            for username in df_users['username']:
                success, _ = reset_user_tokens(username, reset_amount)
                if success:
                    success_count += 1
            
            st.success(f"✅ {success_count} kullanıcı sıfırlandı! Yeni bakiye: {reset_amount}")
            st.rerun()

# ==================== FOOTER ====================
st.markdown("---")
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🏠 Ana Sayfaya Dön", use_container_width=True):
        st.switch_page("Home.py")
