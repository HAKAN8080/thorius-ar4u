"""
MODÜL ŞABLONU
Bu şablon tüm Thorius AR4U modülleri için kullanılır.
Her modül bu yapıyı takip etmelidir.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
from token_manager import (
    check_token_charge,
    charge_token,
    render_token_widget,
    get_token_balance
)

# ==============================================
# SAYFA KONFIGÜRASYONU
# ==============================================

st.set_page_config(
    page_title="[MODÜL ADI] - Thorius AR4U",
    page_icon="[EMOJI]",  # Modül emoji'si
    layout="wide"
)

# ==============================================
# AUTHENTICATION KONTROLÜ
# ==============================================

# Ana sayfadan giriş yapılmış mı kontrol et
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("❌ Bu sayfaya erişmek için giriş yapmalısınız!")
    st.info("👉 Lütfen ana sayfadan giriş yapın.")
    
    if st.button("🏠 Ana Sayfaya Dön"):
        st.switch_page("Home.py")
    
    st.stop()

# ==============================================
# TOKEN KONTROLÜ VE DÜŞÜRME
# ==============================================

username = st.session_state.user_info["username"]
module_name = "[MODULE_KEY]"  # Örnek: "sevkiyat", "budget_forecast", "oms_proje"

# Token düşmesi gerekiyor mu?
should_charge = check_token_charge(username, module_name)

if should_charge:
    success, remaining, message = charge_token(username, module_name)
    
    if not success:
        st.error(f"❌ {message}")
        st.error("Token bakiyeniz tükendi! Lütfen sistem yöneticisi ile iletişime geçin.")
        st.stop()
    else:
        # Token bakiyesini güncelle
        st.session_state.user_info["remaining_tokens"] = remaining
        
        # Uyarılar
        if remaining <= 10:
            st.warning(f"⚠️ Token bakiyeniz azalıyor! Kalan: {remaining} token")
        elif remaining <= 25:
            st.info(f"💡 Kalan token: {remaining}")

# ==============================================
# SIDEBAR
# ==============================================

with st.sidebar:
    # Kullanıcı profili
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
    
    # Token widget
    render_token_widget(username)
    
    st.markdown("---")
    
    # Navigasyon
    st.markdown("### 🧭 Navigasyon")
    
    if st.button("🏠 Ana Sayfa", use_container_width=True):
        st.switch_page("Home.py")
    
    st.markdown("---")
    
    # Çıkış
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.user_info = None
        st.switch_page("Home.py")

# ==============================================
# ANA MODÜL İÇERİĞİ
# ==============================================

# Başlık
st.markdown("""
<div style='text-align: center; padding: 20px 0;'>
    <div style='font-size: 3rem; margin-bottom: 10px;'>[EMOJI]</div>
    <h1 style='font-size: 2.5rem; font-weight: 700;'>[MODÜL ADI]</h1>
    <p style='color: #666; font-size: 1.1rem;'>[MODÜL AÇIKLAMASI]</p>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ==============================================
# MODÜL SPESİFİK KOD BURAYA GELİR
# ==============================================

st.info("🚧 Bu modül aktif geliştirme aşamasındadır.")

# Örnek içerik
tab1, tab2, tab3 = st.tabs(["📊 Dashboard", "📝 Veriler", "⚙️ Ayarlar"])

with tab1:
    st.subheader("Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Metrik 1", "1,234", delta="12%")
    with col2:
        st.metric("Metrik 2", "5,678", delta="-3%")
    with col3:
        st.metric("Metrik 3", "9,012", delta="5%")
    with col4:
        st.metric("Metrik 4", "3,456", delta="8%")

with tab2:
    st.subheader("Veriler")
    
    # Örnek tablo
    df = pd.DataFrame({
        "Tarih": [datetime.now().date()] * 5,
        "Kategori": ["A", "B", "C", "D", "E"],
        "Değer": [100, 200, 150, 300, 250]
    })
    
    st.dataframe(df, use_container_width=True)

with tab3:
    st.subheader("Ayarlar")
    st.info("Modül ayarları buraya gelecek.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666; padding: 20px;'>
    <p>📊 Thorius AR4U - [MODÜL ADI]</p>
    <p style='font-size: 0.85rem;'>Token-Based Module System</p>
</div>
""", unsafe_allow_html=True)
