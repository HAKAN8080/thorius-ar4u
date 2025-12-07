"""
👤 Kullanıcı Paneli
Thorius AR4U - Self-Service Dashboard
Şifre değiştirme, profil yönetimi, token geçmişi
"""

import streamlit as st
import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import hashlib

# Page config
st.set_page_config(
    page_title="Kullanici Paneli",
    page_icon="👤",
    layout="wide"
)

# ==================== AUTHENTICATION ====================
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Lutfen giris yapin!")
    st.stop()

# Get current user
user_info = st.session_state.get('user_info', {})
username = user_info.get('username', '')
user_name = user_info.get('name', 'Kullanıcı')
user_title = user_info.get('title', '')
user_role = user_info.get('role', 'viewer')

# ==================== HEADER ====================
st.title(f"👤 {user_name} - Kullanıcı Paneli")
st.markdown("---")

# ==================== FUNCTIONS ====================

def get_user_info(username):
    """Kullanıcı bilgilerini getir"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    c.execute('''
        SELECT username, name, title, role, remaining_tokens, total_tokens
        FROM users
        WHERE username = ?
    ''', (username,))
    
    result = c.fetchone()
    conn.close()
    
    if result:
        return {
            'username': result[0],
            'name': result[1],
            'title': result[2],
            'role': result[3],
            'remaining_tokens': result[4],
            'total_tokens': result[5]
        }
    return None

def change_password(username, old_password, new_password):
    """Şifre değiştir"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    # Eski şifreyi kontrol et
    old_hash = hashlib.sha256(old_password.encode()).hexdigest()
    
    c.execute('''
        SELECT username FROM users
        WHERE username = ? AND password_hash = ?
    ''', (username, old_hash))
    
    if not c.fetchone():
        conn.close()
        return False, "❌ Eski şifre yanlış!"
    
    # Yeni şifreyi kaydet
    new_hash = hashlib.sha256(new_password.encode()).hexdigest()
    
    c.execute('''
        UPDATE users
        SET password_hash = ?
        WHERE username = ?
    ''', (new_hash, username))
    
    conn.commit()
    conn.close()
    
    return True, "✅ Şifre başarıyla değiştirildi!"

def get_user_transactions(username, limit=20):
    """Kullanıcının token geçmişi"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    
    df = pd.read_sql_query(f'''
        SELECT 
            module,
            token_cost,
            remaining_after,
            datetime(timestamp, 'localtime') as timestamp
        FROM token_transactions
        WHERE username = ?
        ORDER BY timestamp DESC
        LIMIT {limit}
    ''', conn, params=(username,))
    
    conn.close()
    return df

def get_today_usage(username):
    """Bugünkü kullanım"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    c = conn.cursor()
    
    today = datetime.now().date()
    
    c.execute('''
        SELECT SUM(token_cost), COUNT(*)
        FROM token_transactions
        WHERE username = ? AND DATE(timestamp) = ?
    ''', (username, today))
    
    result = c.fetchone()
    conn.close()
    
    total_tokens = result[0] if result[0] else 0
    total_access = result[1] if result[1] else 0
    
    return total_tokens, total_access

def get_weekly_stats(username):
    """Haftalık istatistikler"""
    conn = sqlite3.connect('thorius_tokens.db', check_same_thread=False)
    
    week_ago = datetime.now() - timedelta(days=7)
    
    df = pd.read_sql_query('''
        SELECT 
            DATE(timestamp) as date,
            SUM(token_cost) as tokens
        FROM token_transactions
        WHERE username = ? AND timestamp >= ?
        GROUP BY DATE(timestamp)
        ORDER BY date
    ''', conn, params=(username, week_ago))
    
    conn.close()
    return df

# ==================== TABS ====================
tab1, tab2, tab3, tab4 = st.tabs(["📊 Özet", "🔐 Şifre Değiştir", "📈 İstatistikler", "📋 Geçmiş"])

# ==================== TAB 1: ÖZET ====================
with tab1:
    # Kullanıcı bilgilerini getir
    user_data = get_user_info(username)
    
    if user_data:
        # Kartlar
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "👤 Kullanıcı Adı",
                user_data['username']
            )
        
        with col2:
            st.metric(
                "🎭 Rol",
                user_data['role'].upper()
            )
        
        with col3:
            st.metric(
                "💰 Kalan Token",
                user_data['remaining_tokens']
            )
        
        with col4:
            used = user_data['total_tokens'] - user_data['remaining_tokens']
            st.metric(
                "📊 Kullanılan",
                used
            )
        
        st.markdown("---")
        
        # Bugünkü kullanım
        today_tokens, today_access = get_today_usage(username)
        
        st.subheader("📅 Bugünkü Kullanım")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Token Harcama",
                f"{today_tokens} token"
            )
        
        with col2:
            st.metric(
                "Modül Erişimi",
                f"{today_access} kez"
            )
        
        st.markdown("---")
        
        # Profil bilgileri
        st.subheader("👤 Profil Bilgileri")
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.info(f"**İsim:** {user_data['name']}")
            st.info(f"**Ünvan:** {user_data['title']}")
        
        with info_col2:
            st.info(f"**Rol:** {user_data['role']}")
            st.info(f"**Toplam Token:** {user_data['total_tokens']}")

# ==================== TAB 2: ŞİFRE DEĞİŞTİR ====================
with tab2:
    st.subheader("🔐 Şifre Değiştir")
    
    st.info("💡 Şifreniz en az 6 karakter olmalıdır.")
    
    with st.form("password_form"):
        old_password = st.text_input("Eski Şifre", type="password")
        new_password = st.text_input("Yeni Şifre", type="password")
        confirm_password = st.text_input("Yeni Şifre (Tekrar)", type="password")
        
        submitted = st.form_submit_button("🔄 Şifreyi Değiştir", type="primary")
        
        if submitted:
            # Validasyon
            if not old_password or not new_password or not confirm_password:
                st.error("❌ Tüm alanları doldurun!")
            elif len(new_password) < 6:
                st.error("❌ Yeni şifre en az 6 karakter olmalı!")
            elif new_password != confirm_password:
                st.error("❌ Yeni şifreler eşleşmiyor!")
            elif old_password == new_password:
                st.warning("⚠️ Yeni şifre eski şifreden farklı olmalı!")
            else:
                # Şifreyi değiştir
                success, message = change_password(username, old_password, new_password)
                
                if success:
                    st.success(message)
                    st.balloons()
                    st.info("💡 Bir sonraki girişte yeni şifrenizi kullanın.")
                else:
                    st.error(message)

# ==================== TAB 3: İSTATİSTİKLER ====================
with tab3:
    st.subheader("📈 Haftalık İstatistikler")
    
    # Haftalık kullanım
    weekly_df = get_weekly_stats(username)
    
    if not weekly_df.empty:
        st.line_chart(weekly_df.set_index('date')['tokens'], use_container_width=True)
        
        st.markdown("---")
        
        # Özet istatistikler
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_week = weekly_df['tokens'].sum()
            st.metric("📊 Haftalık Toplam", f"{int(total_week)} token")
        
        with col2:
            avg_day = weekly_df['tokens'].mean()
            st.metric("📉 Günlük Ortalama", f"{int(avg_day)} token")
        
        with col3:
            max_day = weekly_df['tokens'].max()
            st.metric("🔝 Maksimum (Günlük)", f"{int(max_day)} token")
    else:
        st.info("📊 Henüz bu hafta token kullanımı yok.")

# ==================== TAB 4: GEÇMİŞ ====================
with tab4:
    st.subheader("📋 Token Kullanım Geçmişi")
    
    # Limit seçimi
    limit = st.selectbox("Göster", [10, 20, 50, 100], index=1)
    
    # İşlemleri getir
    df_transactions = get_user_transactions(username, limit)
    
    if not df_transactions.empty:
        # Modül isimlerini düzenle
        module_names = {
            'oms_proje': 'OMS Projesi',
            'sevkiyat_ml': 'Sevkiyat ML',
            'budget_forecast': 'Bütçe Forecast',
            'ADMIN_ADD': 'Token Eklendi',
            'ADMIN_REMOVE': 'Token Çıkarıldı',
            'ADMIN_RESET': 'Token Sıfırlandı'
        }
        
        df_transactions['module'] = df_transactions['module'].map(
            lambda x: module_names.get(x, x)
        )
        
        # Tablo
        st.dataframe(
            df_transactions,
            use_container_width=True,
            hide_index=True,
            column_config={
                "module": st.column_config.TextColumn("Modül"),
                "token_cost": st.column_config.NumberColumn("Token", format="%d"),
                "remaining_after": st.column_config.NumberColumn("Kalan", format="%d"),
                "timestamp": st.column_config.DatetimeColumn("Tarih", format="DD/MM/YYYY HH:mm")
            }
        )
        
        st.markdown("---")
        
        # Modül bazlı özet
        st.subheader("📊 Modül Bazlı Kullanım")
        
        module_summary = df_transactions.groupby('module')['token_cost'].sum().sort_values(ascending=False)
        
        if not module_summary.empty:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.bar_chart(module_summary)
            
            with col2:
                for module, tokens in module_summary.items():
                    st.metric(module, f"{int(tokens)} token")
    else:
        st.info("📋 Henüz token kullanım geçmişiniz yok.")

# ==================== FOOTER ====================
st.markdown("---")
col1, col2 = st.columns(2)

with col1:
    if st.button("🏠 Ana Sayfa", use_container_width=True):
        st.switch_page("Home.py")

with col2:
    if st.button("🚪 Çıkış Yap", use_container_width=True, type="secondary"):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()
