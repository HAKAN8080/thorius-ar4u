import streamlit as st
import hashlib
from token_manager import (
    init_token_system_for_app,
    authenticate_user,
    get_token_balance
)

# Sayfa yapılandırması
st.set_page_config(
    page_title="Thorius AR4U - Retail Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Token sistemini başlat
init_token_system_for_app()

# ==============================================
# AUTHENTICATION
# ==============================================

def check_password():
    """Kullanıcı girişi kontrolü"""
    
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.user_info = None
    
    if st.session_state.authenticated:
        return True
    
    # Login sayfası CSS
    st.markdown("""
    <style>
    .login-container {
        max-width: 500px;
        margin: 100px auto;
        padding: 40px;
        background: white;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
    }
    .login-header {
        text-align: center;
        margin-bottom: 30px;
    }
    .login-logo {
        font-size: 4rem;
        margin-bottom: 20px;
    }
    .login-title {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 10px;
    }
    .login-subtitle {
        color: #666;
        font-size: 1.1rem;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="login-header">
        <div class="login-logo">📊</div>
        <div class="login-title">Thorius AR4U</div>
        <div class="login-subtitle">Retail Analytics Platform</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### 🔐 Giriş Yap")
        st.markdown("---")
        
        username = st.text_input("👤 Kullanıcı Adı", placeholder="Kullanıcı adınızı girin")
        password = st.text_input("🔑 Şifre", type="password", placeholder="Şifrenizi girin")
        
        st.markdown("")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🚀 Giriş Yap", use_container_width=True, type="primary"):
                user_info = authenticate_user(username.lower(), password)
                
                if user_info:
                    st.session_state.authenticated = True
                    st.session_state.user_info = user_info
                    st.success(f"✅ Hoş geldiniz, {user_info['name']}!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("❌ Hatalı kullanıcı adı veya şifre!")
        
        with col_b:
            if st.button("🔄 Temizle", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        
        with st.expander("📋 Demo Hesaplar"):
            st.caption("**Sponsor:** ertugrul / lojistik2025")
            st.caption("**Manager:** volkan / magaza2025")
            st.caption("**Demo:** demo / demo2025")
    
    return False

# Authentication kontrolü
if not check_password():
    st.stop()

# ==============================================
# ANA SAYFA
# ==============================================

# Sidebar kullanıcı bilgisi
with st.sidebar:
    st.markdown(f"""
    <div style='padding: 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 10px; margin-bottom: 20px; text-align: center;'>
        <div style='font-size: 3rem; margin-bottom: 10px;'>👤</div>
        <div style='color: white; font-size: 1.2rem; font-weight: 600;'>{st.session_state.user_info['name']}</div>
        <div style='color: rgba(255,255,255,0.8); font-size: 0.9rem;'>{st.session_state.user_info['title']}</div>
        <div style='margin-top: 10px; padding: 5px 10px; background: rgba(255,255,255,0.2); 
                    border-radius: 20px; display: inline-block; color: white; font-size: 0.85rem;'>
            {st.session_state.user_info['role'].upper()}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Token bakiyesi
    balance = get_token_balance(st.session_state.user_info['username'])
    if balance:
        if balance["percent"] < 50:
            bar_color = "#00ff88"
        elif balance["percent"] < 75:
            bar_color = "#ffa500"
        else:
            bar_color = "#ff4444"
        
        st.markdown(f"""
        <div style='padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; margin-bottom: 15px;'>
            <div style='text-align: center; margin-bottom: 10px;'>
                <div style='font-size: 0.9rem; color: #999; margin-bottom: 5px;'>🪙 Token Bakiyesi</div>
                <div style='font-size: 2rem; font-weight: 700; color: {bar_color};'>{balance["remaining"]}</div>
                <div style='font-size: 0.8rem; color: #666;'>/ {balance["total"]} token</div>
            </div>
            <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; overflow: hidden;'>
                <div style='background: {bar_color}; height: 100%; width: {100-balance["percent"]}%; transition: width 0.3s;'></div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.rerun()

# Ana sayfa içeriği - KÜÇÜLTÜLMÜŞ BAŞLIK
st.markdown("""
<div style='text-align: center; padding: 20px 0 10px 0;'>
    <div style='font-size: 2.5rem; margin-bottom: 10px;'>📊</div>
    <h1 style='font-size: 2rem; font-weight: 700; margin: 10px 0;
               background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
               -webkit-background-clip: text; -webkit-text-fill-color: transparent;'>
        THORIUS AR4U
    </h1>
    <p style='font-size: 1rem; color: #666; margin: 5px 0;'>
        Retail Analytics & Resource 4 U
    </p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# Modül kategorileri - KÜÇÜLTÜLMÜŞ VE LACİVERT
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
    <div style='padding: 25px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                border-radius: 15px; text-align: center; color: white; height: 280px;
                display: flex; flex-direction: column; justify-content: space-between;'>
        <div>
            <div style='font-size: 2.5rem; margin-bottom: 10px;'>🔵</div>
            <h2 style='color: white; margin-bottom: 10px; font-size: 1.5rem;'>IN-SEASON</h2>
            <p style='color: rgba(255,255,255,0.9); font-size: 1rem; margin-bottom: 10px;'>7 Aktif Modül</p>
        </div>
        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem;'>
            Sevkiyat, PO, WSSI, Transfer, Kapasite, Fiyatlandırma, Clustering
        </p>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
    <div style='padding: 25px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                border-radius: 15px; text-align: center; color: white; height: 280px;
                display: flex; flex-direction: column; justify-content: space-between;'>
        <div>
            <div style='font-size: 2.5rem; margin-bottom: 10px;'>🔴</div>
            <h2 style='color: white; margin-bottom: 10px; font-size: 1.5rem;'>PRE-SEASON</h2>
            <p style='color: rgba(255,255,255,0.9); font-size: 1rem; margin-bottom: 10px;'>3 Aktif Modül</p>
        </div>
        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem;'>
            Bütçe Forecast, Model Bütçe, Tedarik Zinciri Kokpit
        </p>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
    <div style='padding: 25px; background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%); 
                border-radius: 15px; text-align: center; color: white; height: 280px;
                display: flex; flex-direction: column; justify-content: space-between;'>
        <div>
            <div style='font-size: 2.5rem; margin-bottom: 10px;'>🟡</div>
            <h2 style='color: white; margin-bottom: 10px; font-size: 1.5rem;'>PROJE YÖNETİMİ</h2>
            <p style='color: rgba(255,255,255,0.9); font-size: 1rem; margin-bottom: 10px;'>1 Aktif Modül</p>
        </div>
        <p style='color: rgba(255,255,255,0.8); font-size: 0.85rem;'>
            OMS Depo Birleştirme Projesi
        </p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# Hızlı erişim
st.markdown("### 🚀 Hızlı Erişim")

col_a, col_b, col_c, col_d = st.columns(4)

with col_a:
    if st.button("🚢 Sevkiyat Yönetimi", use_container_width=True):
        st.switch_page("pages/1_🚢_Sevkiyat_Yönetimi.py")

with col_b:
    if st.button("📊 Bütçe Forecast", use_container_width=True):
        st.switch_page("pages/8_📊_Bütçe_Forecast.py")

with col_c:
    if st.button("📋 Sevkiyat & PO", use_container_width=True):
        st.switch_page("pages/2_📋_Sevkiyat_PO.py")

with col_d:
    if st.button("📦 OMS Projesi", use_container_width=True):
        st.switch_page("pages/11_📦_OMS_Projesi.py")

st.markdown("---")

# İstatistikler
st.markdown("### 📊 Platform İstatistikleri")

stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)

with stat_col1:
    st.metric("Toplam Modül", "11", delta="2 Test Aşamasında")

with stat_col2:
    st.metric("Aktif Kullanıcı", "8", delta="100% Token Kullanımı")

with stat_col3:
    balance = get_token_balance(st.session_state.user_info['username'])
    if balance:
        st.metric("Token Bakiyeniz", f"{balance['remaining']}", delta=f"-%{balance['percent']}")

with stat_col4:
    st.metric("Modül Kategorisi", "3", delta="In-Season, Pre-Season, Proje")

st.markdown("---")

# Footer
st.markdown("""
<div style='text-align: center; padding: 20px; color: #666;'>
    <p>📊 Thorius AR4U - Retail Analytics Platform</p>
    <p style='font-size: 0.85rem;'>Token-Based Access System | Developed with ❤️</p>
</div>
""", unsafe_allow_html=True)
