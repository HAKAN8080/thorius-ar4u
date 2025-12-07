"""
🚢 Sevkiyat ML Modül - EVE Sevkiyat Planlama Sistemi
Thorius AR4U Platform - Token-Based Access
Matris Tabanlı Cover Optimizasyonu
"""
import streamlit as st
import pandas as pd
import numpy as np
import time
import io
import os
import sys

# ==================== TOKEN MANAGER IMPORT ====================
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from token_manager import check_token_and_charge, render_token_widget

# ==================== AUTHENTICATION & TOKEN CONTROL ====================

# Redirect to Home if not authenticated
if 'authenticated' not in st.session_state or not st.session_state.authenticated:
    st.warning("⚠️ Lütfen giriş yapın!")
    st.stop()

# Token kontrolü (10 token)
module_name = "sevkiyat_ml"
required_tokens = 10

if not check_token_and_charge(module_name, required_tokens):
    st.error(f"❌ Bu modül için {required_tokens} token gerekiyor!")
    st.info("💡 Ana sayfaya dönüp token satın alabilirsiniz")
    st.stop()

# ==================== ORIGINAL CODE STARTS HERE ====================


# ==================== SIDEBAR (BEFORE set_page_config) ====================

with st.sidebar:
    # User Profile Card
    user_info = st.session_state.get('user_info', {})
    user_name = user_info.get('name', 'Kullanıcı')
    user_email = user_info.get('email', 'user@example.com')
    
    st.markdown(f"""
    <div style="padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                border-radius: 10px; margin-bottom: 1rem; color: white;">
        <div style="font-size: 1.1rem; font-weight: bold;">👤 {user_name}</div>
        <div style="font-size: 0.8rem; opacity: 0.9;">{user_email}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Token Widget
    render_token_widget()
    
    st.divider()
    
    # Navigation
    st.markdown("### 🧭 Navigasyon")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🏠 Ana Sayfa", use_container_width=True, key="nav_home"):
            st.switch_page("Home.py")
    with col2:
        if st.button("📦 Modüller", use_container_width=True, key="nav_modules"):
            st.switch_page("Home.py")
    
    st.divider()
    
    # Module Info
    st.markdown("### 📊 Modül Bilgisi")
    st.info("""
    **EVE Sevkiyat Planlama**
    
    ✅ Matris tabanlı optimizasyon
    ✅ Cover analizi
    ✅ Alım ihtiyacı hesaplama
    ✅ Detaylı raporlama
    """)
    
    st.divider()
    
    # Logout Button
    if st.button("🚪 Çıkış Yap", use_container_width=True, key="logout_btn"):
        keys_to_keep = []
        keys_to_delete = [key for key in st.session_state.keys() if key not in keys_to_keep]
        for key in keys_to_delete:
            del st.session_state[key]
        st.switch_page("Home.py")

# ==================== ORIGINAL CODE CONTINUES ====================


# -------------------------------
# YARDIMCI FONKSİYONLAR
# -------------------------------

def read_csv_advanced(uploaded_file):
    """Gelişmiş CSV okuma fonksiyonu"""
    try:
        uploaded_file.seek(0)
        return pd.read_csv(uploaded_file, encoding='utf-8')
    except:
        try:
            uploaded_file.seek(0)
            return pd.read_csv(uploaded_file, encoding='iso-8859-9')
        except:
            content = uploaded_file.getvalue().decode('utf-8', errors='ignore')
            delimiters = [',', ';', '\t', '|']
            for delimiter in delimiters:
                try:
                    df = pd.read_csv(io.StringIO(content), delimiter=delimiter)
                    if len(df.columns) > 1:
                        return df
                except:
                    continue
            return pd.read_csv(io.StringIO(content), delimiter=',')

def normalize_columns(df):
    """Kolon isimlerini standardize et"""
    if df.empty:
        return df
    df.columns = df.columns.str.strip().str.lower()
    df.columns = df.columns.str.replace('[^a-z0-9_]', '_', regex=True)
    return df

def get_carpan_from_matrix(magaza_cover_grubu, urun_cover_grubu, carpan_matrisi=None):
    """Matristen çarpan değerini al - GÜVENLİ VERSİYON"""
    try:
        # Eğer carpan_matrisi verilmediyse session state'den al
        if carpan_matrisi is None:
            carpan_matrisi = st.session_state.get('carpan_matrisi', {})
        
        return carpan_matrisi.get(magaza_cover_grubu, {}).get(urun_cover_grubu, 1.0)
    except:
        return 1.0

def calculate_urun_cover(haftalik_satis, mevcut_stok, yolda=0):
    """Ürün cover'ını DOĞRU şekilde hesapla - YOLDA STOĞU ÇIKARMA"""
    try:
        if haftalik_satis is None or haftalik_satis <= 0:
            return 999  # Satış yoksa yüksek cover
        
        # Stok değerlerini kontrol et - YOLDA STOĞU ÇIKARMA (doğru olan bu)
        mevcut_stok = mevcut_stok if mevcut_stok is not None else 0
        
        # DÜZELTME: Yolda stoğu çıkarmıyoruz, çünkü zaten mağazada değil
        total_stok = mevcut_stok
        
        if total_stok <= 0:
            return 0  # Stok yoksa cover 0
        
        cover = total_stok / haftalik_satis
        return round(float(cover), 2)
    except:
        return 999

def get_cover_grubu_adi(cover_value, cover_gruplari):
    """Cover değerine göre grup adını doğru şekilde bul"""
    try:
        cover_value = float(cover_value)
        for grup in cover_gruplari:
            if grup['min'] <= cover_value <= grup['max']:
                return grup['etiket']
        # Varsayılan olarak en yüksek grup
        return "20+"
    except:
        return "20+"

# -------------------------------
# COVER GRUPLARI ve MATRİS YÖNETİMİ (DÜZELTMELİ)
# -------------------------------

def manage_cover_groups_and_matrix():
    st.header("📊 Parametre Ayarları")
    
    # Varsayılan cover grupları
    default_cover_data = [
        {"min": 0, "max": 4, "etiket": "0-4"},
        {"min": 5, "max": 8, "etiket": "5-8"},
        {"min": 9, "max": 12, "etiket": "9-12"},
        {"min": 13, "max": 20, "etiket": "13-20"},
        {"min": 21, "max": 999, "etiket": "20+"}
    ]
    
    # Varsayılan sevkiyat matrisi
    default_matrix = {
        "0-4": {"0-4": 1.2, "5-8": 1.1, "9-12": 1.0, "13-20": 1.0, "20+": 0.9},
        "5-8": {"0-4": 1.1, "5-8": 1.0, "9-12": 1.0, "13-20": 0.9, "20+": 0.8},
        "9-12": {"0-4": 1.0, "5-8": 1.0, "9-12": 0.9, "13-20": 0.8, "20+": 0.7},
        "13-20": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0},
        "20+": {"0-4": 1.0, "5-8": 0.9, "9-12": 0.8, "13-20": 0, "20+": 0}
    }
    
    # Varsayılan ALIM matrisi
    default_alim_matrix = {
        "0-4": {"0-4": 1.2, "5-8": 1.1, "9-12": 1.0, "13-20": 1.0, "20+": 0},
        "5-8": {"0-4": 1.1, "5-8": 1.0, "9-12": 1.0, "13-20": 1.0, "20+": 0},
        "9-12": {"0-4": 1.0, "5-8": 1.0, "9-12": 1.0, "13-20": 0, "20+": 0},
        "13-20": {"0-4": 1.0, "5-8": 1.0, "9-12": 1.0, "13-20": 0, "20+": 0},
        "20+": {"0-4": 1.0, "5-8": 0, "9-12": 0, "13-20": 0, "20+": 0}
    }
    
    # Session state'i kontrol et ve başlat
    if "cover_gruplari" not in st.session_state:
        st.session_state.cover_gruplari = default_cover_data.copy()
    
    if "carpan_matrisi" not in st.session_state:
        st.session_state.carpan_matrisi = default_matrix.copy()
    
    if "alim_carpan_matrisi" not in st.session_state:
        st.session_state.alim_carpan_matrisi = default_alim_matrix.copy()
    
    if "cover_gruplari_edited" not in st.session_state:
        st.session_state.cover_gruplari_edited = st.session_state.cover_gruplari.copy()
    
    if "carpan_matrisi_edited" not in st.session_state:
        st.session_state.carpan_matrisi_edited = st.session_state.carpan_matrisi.copy()
    
    if "alim_carpan_matrisi_edited" not in st.session_state:
        st.session_state.alim_carpan_matrisi_edited = st.session_state.alim_carpan_matrisi.copy()

    # KPI ve Varsayılanlar
    st.subheader("🎯 KPI & Varsayılan Değerler")
    st.info("⚠️ **ÖNEMLİ:** Aşağıdaki değerler SADECE KPI.csv dosyası yüklenmediğinde kullanılacaktır.")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        default_hedef_hafta = st.slider("Varsayılan Hedef Hafta", 1, 12, 4, key="hedef_hafta_slider")
    
    with col2:
        default_min_adet = st.slider("Varsayılan Min Adet", 0, 100, 3, key="min_adet_slider")
    
    with col3:
        default_maks_adet = st.slider("Varsayılan Maks Adet", 0, 200, 20, key="maks_adet_slider")
    
    st.markdown("---")
    
    # Cover Grupları Yönetimi
    st.subheader("📈 Cover Grupları")
    st.info("Mağaza ve ürün cover değerlerinin gruplandırılması - Çarpan matriste ayrıca tanımlanır")
    
    # Mevcut cover gruplarını DataFrame'e dönüştür
    current_df = pd.DataFrame(st.session_state.cover_gruplari_edited)
    
    edited_df = st.data_editor(
        current_df,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "min": st.column_config.NumberColumn("Min Cover", min_value=0, max_value=1000, step=1),
            "max": st.column_config.NumberColumn("Max Cover", min_value=0, max_value=1000, step=1),
            "etiket": st.column_config.TextColumn("Etiket", width="medium")
        },
        key="cover_gruplari_editor"
    )
    
    # Cover grupları değiştiğinde matrisleri otomatik güncelle
    if not edited_df.equals(current_df):
        st.session_state.cover_gruplari_edited = edited_df.to_dict('records')
        
        # Yeni etiketleri al
        new_etiketler = [g['etiket'] for g in st.session_state.cover_gruplari_edited]
        old_etiketler = [g['etiket'] for g in st.session_state.cover_gruplari]
        
        # Yeni matrisler oluştur
        new_matrix = {}
        new_alim_matrix = {}
        
        for magaza_grubu in new_etiketler:
            new_matrix[magaza_grubu] = {}
            new_alim_matrix[magaza_grubu] = {}
            
            for urun_grubu in new_etiketler:
                # Eski matristen değeri al, yoksa varsayılan hesapla
                if magaza_grubu in st.session_state.carpan_matrisi_edited and urun_grubu in st.session_state.carpan_matrisi_edited[magaza_grubu]:
                    new_matrix[magaza_grubu][urun_grubu] = st.session_state.carpan_matrisi_edited[magaza_grubu][urun_grubu]
                else:
                    # Varsayılan değer: gruplar arası mesafe baz alınarak
                    try:
                        magaza_idx = new_etiketler.index(magaza_grubu)
                        urun_idx = new_etiketler.index(urun_grubu)
                        distance = abs(magaza_idx - urun_idx)
                        new_matrix[magaza_grubu][urun_grubu] = max(0.05, 1.2 - distance * 0.2)
                    except:
                        new_matrix[magaza_grubu][urun_grubu] = 1.0
                
                # Alım matrisi için
                if magaza_grubu in st.session_state.alim_carpan_matrisi_edited and urun_grubu in st.session_state.alim_carpan_matrisi_edited[magaza_grubu]:
                    new_alim_matrix[magaza_grubu][urun_grubu] = st.session_state.alim_carpan_matrisi_edited[magaza_grubu][urun_grubu]
                else:
                    # Alım için varsayılan değer: daha yüksek çarpanlar
                    try:
                        magaza_idx = new_etiketler.index(magaza_grubu)
                        urun_idx = new_etiketler.index(urun_grubu)
                        distance = abs(magaza_idx - urun_idx)
                        new_alim_matrix[magaza_grubu][urun_grubu] = max(0.1, 1.5 - distance * 0.2)
                    except:
                        new_alim_matrix[magaza_grubu][urun_grubu] = 1.0
        
        st.session_state.carpan_matrisi_edited = new_matrix
        st.session_state.alim_carpan_matrisi_edited = new_alim_matrix
        st.success("✅ Cover grupları güncellendi! Matrisler otomatik olarak yenilendi.")
        st.rerun()
    
    st.markdown("---")
    
    # Çarpan Matrisleri Yönetimi - SEVKİYAT ve ALIM
    tab1, tab2 = st.tabs(["🚚 Sevkiyat Matrisi", "🛒 Alım Matrisi"])
    
    # Mevcut cover gruplarını al
    cover_gruplari_etiketler = [g['etiket'] for g in st.session_state.cover_gruplari_edited]
    
    with tab1:
        st.subheader("🎯 Sevkiyat Çarpan Matrisi")
        st.info("⚠️ **Bu matris katsayıları ile sevk genişletme işlemi yapılmaktadır!**")
        
        # Sevkiyat matrisini DataFrame'e dönüştür
        matrix_data = {}
        for magaza_grubu in cover_gruplari_etiketler:
            matrix_data[magaza_grubu] = {}
            for urun_grubu in cover_gruplari_etiketler:
                try:
                    matrix_data[magaza_grubu][urun_grubu] = st.session_state.carpan_matrisi_edited.get(
                        magaza_grubu, {}).get(urun_grubu, 1.0)
                except:
                    matrix_data[magaza_grubu][urun_grubu] = 1.0
        
        matrix_df = pd.DataFrame(matrix_data)
        
        # Eksik değerleri tamamla
        for magaza_grubu in cover_gruplari_etiketler:
            if magaza_grubu not in matrix_df.index:
                matrix_df.loc[magaza_grubu] = {urun_grubu: 1.0 for urun_grubu in cover_gruplari_etiketler}
            for urun_grubu in cover_gruplari_etiketler:
                if pd.isna(matrix_df.loc[magaza_grubu, urun_grubu]):
                    matrix_df.loc[magaza_grubu, urun_grubu] = 1.0
        
        # Sütun ve index sıralamasını düzelt
        matrix_df = matrix_df.reindex(columns=cover_gruplari_etiketler)
        matrix_df = matrix_df.reindex(index=cover_gruplari_etiketler)
        
        st.write("**Sevkiyat Çarpan Matrisi Düzenleyici**")
        
        matrix_edited = st.data_editor(
            matrix_df,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                format="%.2f", 
                min_value=0.01, 
                max_value=2.0,
                step=0.1
            ) for col in matrix_df.columns},
            key="carpan_matrisi_editor"
        )
        
        # Matris değişikliklerini kaydet
        if not matrix_edited.equals(matrix_df):
            st.session_state.carpan_matrisi_edited = matrix_edited.to_dict()
            st.success("✅ Sevkiyat matrisi güncellendi!")
            st.rerun()
    
    with tab2:
        st.subheader("🛒 Alım Çarpan Matrisi")
        st.info("💰 **Bu matris katsayıları ile alım sipariş miktarları hesaplanacaktır!**")
        
        # Alım matrisini DataFrame'e dönüştür
        alim_matrix_data = {}
        for magaza_grubu in cover_gruplari_etiketler:
            alim_matrix_data[magaza_grubu] = {}
            for urun_grubu in cover_gruplari_etiketler:
                try:
                    alim_matrix_data[magaza_grubu][urun_grubu] = st.session_state.alim_carpan_matrisi_edited.get(
                        magaza_grubu, {}).get(urun_grubu, 1.0)
                except:
                    alim_matrix_data[magaza_grubu][urun_grubu] = 1.0
        
        alim_matrix_df = pd.DataFrame(alim_matrix_data)
        
        # Eksik değerleri tamamla
        for magaza_grubu in cover_gruplari_etiketler:
            if magaza_grubu not in alim_matrix_df.index:
                alim_matrix_df.loc[magaza_grubu] = {urun_grubu: 1.0 for urun_grubu in cover_gruplari_etiketler}
            for urun_grubu in cover_gruplari_etiketler:
                if pd.isna(alim_matrix_df.loc[magaza_grubu, urun_grubu]):
                    alim_matrix_df.loc[magaza_grubu, urun_grubu] = 1.0
        
        # Sütun ve index sıralamasını düzelt
        alim_matrix_df = alim_matrix_df.reindex(columns=cover_gruplari_etiketler)
        alim_matrix_df = alim_matrix_df.reindex(index=cover_gruplari_etiketler)
        
        st.write("**Alım Çarpan Matrisi Düzenleyici**")
        
        alim_matrix_edited = st.data_editor(
            alim_matrix_df,
            use_container_width=True,
            column_config={col: st.column_config.NumberColumn(
                format="%.2f", 
                min_value=0.01, 
                max_value=3.0,  # Alım için daha yüksek maksimum değer
                step=0.1
            ) for col in alim_matrix_df.columns},
            key="alim_carpan_matrisi_editor"
        )
        
        # Alım matrisi değişikliklerini kaydet
        if not alim_matrix_edited.equals(alim_matrix_df):
            st.session_state.alim_carpan_matrisi_edited = alim_matrix_edited.to_dict()
            st.success("✅ Alım matrisi güncellendi!")
            st.rerun()
    
    # Matris Görselleştirme
    st.markdown("---")
    st.subheader("📊 Matris Görselleştirme")
    
    viz_tab1, viz_tab2 = st.tabs(["🚚 Sevkiyat Matrisi", "🛒 Alım Matrisi"])
    
    with viz_tab1:
        # BASİT TABLO GÖSTERİMİ - En güvenli
        st.write("**Sevkiyat Çarpan Matrisi:**")
        
        # DataFrame'i formatla
        display_df = matrix_edited.copy()
        for col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "1.00")
        
        # Stil uygula
        def color_cells_sevk(val):
            try:
                num_val = float(val)
                if num_val > 1.1:
                    return 'background-color: #ff6b6b; color: white'  # Kırmızı - yüksek
                elif num_val > 0.9:
                    return 'background-color: #4ecdc4; color: white'  # Yeşil - orta
                else:
                    return 'background-color: #45b7d1; color: white'  # Mavi - düşük
            except:
                return ''
        
        styled_df = display_df.style.applymap(color_cells_sevk)
        st.dataframe(styled_df, use_container_width=True)
    
    with viz_tab2:
        # BASİT TABLO GÖSTERİMİ - En güvenli
        st.write("**Alım Çarpan Matrisi:**")
        
        # DataFrame'i formatla
        display_df = alim_matrix_edited.copy()
        for col in display_df.columns:
            display_df[col] = display_df[col].apply(lambda x: f"{float(x):.2f}" if pd.notna(x) else "1.00")
        
        # Stil uygula
        def color_cells_alim(val):
            try:
                num_val = float(val)
                if num_val > 1.3:
                    return 'background-color: #ff6b6b; color: white'  # Kırmızı - yüksek
                elif num_val > 1.0:
                    return 'background-color: #4ecdc4; color: white'  # Yeşil - orta
                else:
                    return 'background-color: #45b7d1; color: white'  # Mavi - düşük
            except:
                return ''
        
        styled_df = display_df.style.applymap(color_cells_alim)
        st.dataframe(styled_df, use_container_width=True)
    
    # Kaydetme butonları
    st.markdown("---")
    st.subheader("💾 Ayarları Kaydet")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("💾 Tüm Değişiklikleri Kaydet", type="primary", use_container_width=True, key="save_all"):
            # Cover gruplarını kaydet
            st.session_state.cover_gruplari = st.session_state.cover_gruplari_edited.copy()
            
            # Matrisleri kaydet
            st.session_state.carpan_matrisi = st.session_state.carpan_matrisi_edited.copy()
            st.session_state.alim_carpan_matrisi = st.session_state.alim_carpan_matrisi_edited.copy()
            
            st.success("✅ Tüm ayarlar kalıcı olarak güncellendi!")
            st.rerun()
    
    with col2:
        if st.button("🔄 Varsayılanlara Dön", use_container_width=True, key="reset_defaults"):
            st.session_state.cover_gruplari = default_cover_data.copy()
            st.session_state.carpan_matrisi = default_matrix.copy()
            st.session_state.alim_carpan_matrisi = default_alim_matrix.copy()
            st.session_state.cover_gruplari_edited = default_cover_data.copy()
            st.session_state.carpan_matrisi_edited = default_matrix.copy()
            st.session_state.alim_carpan_matrisi_edited = default_alim_matrix.copy()
            st.success("✅ Varsayılan değerlere dönüldü!")
            st.rerun()
    
    with col3:
        if st.button("📊 Geçerli Ayarları Göster", use_container_width=True, key="show_current"):
            st.info("🔍 Geçerli Cover Grupları:")
            st.json(st.session_state.cover_gruplari)
            
            st.info("🔍 Geçerli Sevkiyat Matrisi:")
            st.json(st.session_state.carpan_matrisi)
            
            st.info("🔍 Geçerli Alım Matrisi:")
            st.json(st.session_state.alim_carpan_matrisi)
    
    return default_hedef_hafta, default_min_adet, default_maks_adet, edited_df
# -------------------------------
# DOSYA YÜKLEME BÖLÜMÜ
# -------------------------------

def create_file_upload_section():
    st.header("📁 Veri Yükleme")
    
    with st.expander("📋 **Dosya Formatları**", expanded=True):
        st.markdown("""
        **Zorunlu Dosyalar:**
        - **Sevkiyat.csv**: depo_id, urun_id, magaza_id, haftalik_satis, mevcut_stok, yolda, klasmankod
        - **Depo_Stok.csv**: depo_id, urun_id, depo_stok
        
        **Opsiyonel Dosyalar:**
        - **Urunler.csv**: urun_id, urun_adi, klasman_id
        - **Magazalar.csv**: magaza_id, magaza_adi  
        - **Cover.csv**: magaza_id, cover, cluster 
        - **KPI.csv**: klasmankod, hedef_hafta, min_adet, maks_adet
        """)
    
    uploaded_files = st.file_uploader("**CSV dosyalarınızı seçin**", type=["csv"], accept_multiple_files=True)
    
    file_data = {}
    
    if uploaded_files:
        for uploaded_file in uploaded_files:
            try:
                df = read_csv_advanced(uploaded_file)
                file_data[uploaded_file.name] = df
                st.success(f"✅ {uploaded_file.name} - {len(df.columns)} kolon, {len(df)} satır")
                
            except Exception as e:
                st.error(f"❌ {uploaded_file.name} okunamadı: {e}")
    
    return file_data

# -------------------------------
# ALIM SIPARIŞ İHTİYACI HESAPLAMA (DÜZELTMELİ)
# -------------------------------
def calculate_purchase_need(sevk_df, total_sevk, original_sevkiyat_df, depo_stok_df):
    """
    Karşılanamayan ihtiyaçları hesapla - BASİT VERSİYON
    """
    try:
        if original_sevkiyat_df.empty:
            return pd.DataFrame()
        
        # Orijinal sevkiyat verisini kopyala
        sevkiyat_df = original_sevkiyat_df.copy()
        
        # Sevkiyat miktarını birleştir
        if not sevk_df.empty and 'sevk_miktar' in sevk_df.columns:
            sevk_toplam = sevk_df.groupby(['depo_id', 'magaza_id', 'urun_id'])['sevk_miktar'].sum().reset_index()
            sevkiyat_df = pd.merge(
                sevkiyat_df,
                sevk_toplam,
                on=['depo_id', 'magaza_id', 'urun_id'],
                how='left'
            )
            sevkiyat_df['sevk_miktar'] = sevkiyat_df['sevk_miktar'].fillna(0)
        else:
            sevkiyat_df['sevk_miktar'] = 0
        
        # İhtiyaç hesapla (eğer yoksa)
        if 'ihtiyac' not in sevkiyat_df.columns:
            sevkiyat_df['ihtiyac'] = (
                (sevkiyat_df['haftalik_satis'] * sevkiyat_df.get('hedef_hafta', 4)) - 
                (sevkiyat_df['mevcut_stok'] + sevkiyat_df.get('yolda', 0))
            ).clip(lower=0)
        
        # Kalan ihtiyaç = ihtiyaç - sevk_miktar
        sevkiyat_df["kalan_ihtiyac"] = (sevkiyat_df["ihtiyac"] - sevkiyat_df["sevk_miktar"]).clip(lower=0)
        
        # Depo stok bilgilerini ekle
        if not depo_stok_df.empty:
            depo_stok_toplam = depo_stok_df.groupby(['depo_id', 'urun_id'])['depo_stok'].sum().reset_index()
            sevkiyat_df = pd.merge(
                sevkiyat_df,
                depo_stok_toplam,
                on=['depo_id', 'urun_id'],
                how='left'
            )
            sevkiyat_df['depo_stok'] = sevkiyat_df['depo_stok'].fillna(0)
        else:
            sevkiyat_df['depo_stok'] = 0

        # Karşılanamayan ve depoda stok olmayanları filtrele
        alim_siparis_df = sevkiyat_df[
            (sevkiyat_df["kalan_ihtiyac"] > 0) & (sevkiyat_df["depo_stok"] <= 0)
        ].copy()

        if alim_siparis_df.empty:
            st.info("ℹ️ Alım ihtiyacı bulunmamaktadır.")
            return pd.DataFrame()

        # BASİT HESAP: Alım miktarı = kalan ihtiyaç
        alim_siparis_df['alim_siparis_miktari'] = alim_siparis_df['kalan_ihtiyac']

        # Ürün bazında toplam alım siparişi
        alim_siparis_toplam = alim_siparis_df.groupby(
            ["depo_id", "urun_id", "klasmankod"], as_index=False
        ).agg({
            'alim_siparis_miktari': 'sum',
            'kalan_ihtiyac': 'sum',
            'ihtiyac': 'first',
            'depo_stok': 'first',
            'haftalik_satis': 'first'
        })

        # Ürün adını ekle
        if 'urunler_df' in st.session_state and not st.session_state.urunler_df.empty:
            urunler_df = st.session_state.urunler_df.copy()
            urunler_df['urun_id'] = urunler_df['urun_id'].astype(str).str.strip()
            alim_siparis_toplam['urun_id'] = alim_siparis_toplam['urun_id'].astype(str).str.strip()
            if 'urun_adi' in urunler_df.columns:
                alim_siparis_toplam = pd.merge(
                    alim_siparis_toplam,
                    urunler_df[['urun_id', 'urun_adi']],
                    on='urun_id',
                    how='left'
                )
        
        if 'urun_adi' not in alim_siparis_toplam.columns:
            alim_siparis_toplam['urun_adi'] = "Ürün " + alim_siparis_toplam['urun_id'].astype(str)
        
        # Cover bilgilerini ekle
        alim_siparis_toplam['toplam_ihtiyac_cover'] = (
            alim_siparis_toplam['alim_siparis_miktari'] / alim_siparis_toplam['haftalik_satis']
        ).round(1)
        
        # Sıralama
        alim_siparis_toplam = alim_siparis_toplam.sort_values('alim_siparis_miktari', ascending=False)
        
        return alim_siparis_toplam
    
    except Exception as e:
        st.error(f"Alım ihtiyacı hesaplanırken hata: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return pd.DataFrame()


# -------------------------------
# ANA HESAPLAMA FONKSİYONU (DÜZELTMELİ YENİ SİSTEM)
# -------------------------------

def calculate_shipment_optimized(file_data, params, cover_gruplari):
    # Dosyaları yükle
    sevk_df, depo_stok_df, urunler_df, magazalar_df, cover_df, kpi_df = None, None, None, None, None, None
    
    for name, df in file_data.items():
        name_lower = name.lower()
        if "sevkiyat" in name_lower:
            sevk_df = df.copy()
            st.info(f"📊 Sevkiyat dosyası: {len(sevk_df)} satır")
        elif "depo" in name_lower and "stok" in name_lower:
            depo_stok_df = df.copy()
            st.info(f"📦 Depo stok dosyası: {len(depo_stok_df)} satır")
        elif "urun" in name_lower:
            urunler_df = df.copy()
            st.info(f"🏷️ Ürünler dosyası: {len(urunler_df)} satır")
            st.session_state.urunler_df = urunler_df
        elif "magaza" in name_lower:
            magazalar_df = df.copy()
            st.info(f"🏪 Mağazalar dosyası: {len(magazalar_df)} satır")
            st.session_state.magazalar_df = magazalar_df
        elif "cover" in name_lower:
            cover_df = df.copy()
            st.info(f"📈 Cover dosyası: {len(cover_df)} satır")
        elif "kpi" in name_lower:
            kpi_df = df.copy()
            st.info(f"🎯 KPI dosyası: {len(kpi_df)} satır")
    
    if sevk_df is None or depo_stok_df is None:
        raise Exception("Zorunlu dosyalar (Sevkiyat.csv, Depo_Stok.csv) eksik!")
    
    # Orijinal sevkiyat df'ini kaydet (alım ihtiyacı için)
    original_sevkiyat_df = sevk_df.copy()
    
    # Kolon normalizasyonu
    sevk_df = normalize_columns(sevk_df)
    depo_stok_df = normalize_columns(depo_stok_df)
    original_sevkiyat_df = normalize_columns(original_sevkiyat_df)
    
    # Zorunlu kolon kontrolü
    required_sevk = ['depo_id', 'urun_id', 'magaza_id', 'haftalik_satis', 'mevcut_stok', 'klasmankod']
    missing_cols = [col for col in required_sevk if col not in sevk_df.columns]
    if missing_cols:
        raise Exception(f"Sevkiyat.csv'de eksik kolonlar: {missing_cols}")
    
    # yolda kolonu kontrolü
    if 'yolda' not in sevk_df.columns:
        sevk_df['yolda'] = 0
        original_sevkiyat_df['yolda'] = 0
        st.info("ℹ️ 'yolda' kolonu eklenerek 0 değeri atandı")
    
    # VERİ TİPLERİNİ KESİNLİKLE DÖNÜŞTÜR
    st.info("🔄 Veri tipleri kontrol ediliyor...")
    numeric_cols = ['haftalik_satis', 'mevcut_stok', 'yolda', 'cover', 'hedef_hafta', 'min_adet', 'maks_adet']
    for col in numeric_cols:
        if col in sevk_df.columns:
            sevk_df[col] = pd.to_numeric(sevk_df[col], errors='coerce').fillna(0).astype(float)
        if col in original_sevkiyat_df.columns:
            original_sevkiyat_df[col] = pd.to_numeric(original_sevkiyat_df[col], errors='coerce').fillna(0).astype(float)
    
    # ÖNEMLİ: Sıfır ve negatif satış değerlerini düzelt
    sevk_df['haftalik_satis'] = sevk_df['haftalik_satis'].apply(lambda x: max(0.1, x))  # En az 0.1
    original_sevkiyat_df['haftalik_satis'] = original_sevkiyat_df['haftalik_satis'].apply(lambda x: max(0.1, x))
    
    # Cover dosyasını işle
    if cover_df is not None and not cover_df.empty:
        cover_df = normalize_columns(cover_df)
        if 'magaza_id' in cover_df.columns and 'cover' in cover_df.columns:
            cover_df = cover_df[['magaza_id', 'cover']].drop_duplicates()
            cover_df['magaza_id'] = cover_df['magaza_id'].astype(str).str.strip()
            sevk_df['magaza_id'] = sevk_df['magaza_id'].astype(str).str.strip()
            original_sevkiyat_df['magaza_id'] = original_sevkiyat_df['magaza_id'].astype(str).str.strip()
            
            sevk_df = sevk_df.merge(cover_df, on='magaza_id', how='left')
            original_sevkiyat_df = original_sevkiyat_df.merge(cover_df, on='magaza_id', how='left')
            st.success("✅ Mağaza cover verileri eklendi")
        else:
            st.warning("⚠️ Cover dosyasında gerekli kolonlar bulunamadı")
            sevk_df['cover'] = 999
            original_sevkiyat_df['cover'] = 999
    else:
        st.warning("⚠️ Cover dosyası bulunamadı, varsayılan cover=999")
        sevk_df['cover'] = 999
        original_sevkiyat_df['cover'] = 999
    
    # Cover değerlerini temizle
    sevk_df['cover'] = pd.to_numeric(sevk_df['cover'], errors='coerce').fillna(999)
    original_sevkiyat_df['cover'] = pd.to_numeric(original_sevkiyat_df['cover'], errors='coerce').fillna(999)
    
    # KPI dosyasını işle - EĞER KPI DOSYASI YOKSA PARAMETRELERDEN KULLAN
    kpi_loaded = False
    if kpi_df is not None and not kpi_df.empty:
        kpi_df = normalize_columns(kpi_df)
        if 'klasmankod' in kpi_df.columns:
            kpi_df['klasmankod'] = kpi_df['klasmankod'].astype(str).str.strip()
            sevk_df['klasmankod'] = sevk_df['klasmankod'].astype(str).str.strip()
            original_sevkiyat_df['klasmankod'] = original_sevkiyat_df['klasmankod'].astype(str).str.strip()
            
            kpi_cols = ['klasmankod']
            for col in ['hedef_hafta', 'min_adet', 'maks_adet']:
                if col in kpi_df.columns:
                    kpi_cols.append(col)
            
            sevk_df = sevk_df.merge(kpi_df[kpi_cols], on='klasmankod', how='left')
            original_sevkiyat_df = original_sevkiyat_df.merge(kpi_df[kpi_cols], on='klasmankod', how='left')
            st.success("✅ KPI verileri eklendi (KPI.csv kullanılıyor)")
            kpi_loaded = True
        else:
            st.warning("⚠️ KPI dosyasında klasmankod bulunamadı")
    else:
        st.warning("⚠️ KPI dosyası bulunamadı, parametrelerden alınan değerler kullanılacak")
    
    # Eksik KPI değerlerini doldur
    if not kpi_loaded:
        sevk_df['hedef_hafta'] = params['hedef_hafta']
        sevk_df['min_adet'] = params['min_adet']
        sevk_df['maks_adet'] = params['maks_adet']
        
        original_sevkiyat_df['hedef_hafta'] = params['hedef_hafta']
        original_sevkiyat_df['min_adet'] = params['min_adet']
        original_sevkiyat_df['maks_adet'] = params['maks_adet']
        st.info("ℹ️ Parametrelerden alınan değerler kullanılıyor")
    else:
        sevk_df['hedef_hafta'] = sevk_df.get('hedef_hafta', params['hedef_hafta'])
        sevk_df['min_adet'] = sevk_df.get('min_adet', params['min_adet'])
        sevk_df['maks_adet'] = sevk_df.get('maks_adet', params['maks_adet'])
        
        original_sevkiyat_df['hedef_hafta'] = original_sevkiyat_df.get('hedef_hafta', params['hedef_hafta'])
        original_sevkiyat_df['min_adet'] = original_sevkiyat_df.get('min_adet', params['min_adet'])
        original_sevkiyat_df['maks_adet'] = original_sevkiyat_df.get('maks_adet', params['maks_adet'])
    
    # YENİ: Ürün cover'ını HATA KONTROLLÜ hesapla - YOLDA STOĞU ÇIKARMA
    st.info("🔄 Ürün cover değerleri hesaplanıyor...")
    
    # Hata kontrolü ile ürün cover hesaplama - YOLDA STOĞU ÇIKARMA
    def safe_urun_cover(row):
        try:
            return calculate_urun_cover(
                row.get('haftalik_satis', 0), 
                row.get('mevcut_stok', 0), 
                row.get('yolda', 0)
            )
        except:
            return 999
    
    sevk_df['urun_cover'] = sevk_df.apply(safe_urun_cover, axis=1)
    original_sevkiyat_df['urun_cover'] = original_sevkiyat_df.apply(safe_urun_cover, axis=1)
    
    # Cover gruplarını detaylı şekilde belirle
    def detailed_cover_group(cover_value, gruplar):
        try:
            cover_value = float(cover_value)
            for i, grup in enumerate(gruplar):
                if grup['min'] <= cover_value <= grup['max']:
                    return grup['etiket']
            return "20+"
        except:
            return "20+"
    
    sevk_df['magaza_cover_grubu'] = sevk_df['cover'].apply(
        lambda x: detailed_cover_group(x, cover_gruplari)
    )
    sevk_df['urun_cover_grubu'] = sevk_df['urun_cover'].apply(
        lambda x: detailed_cover_group(x, cover_gruplari)
    )
    
    # Cover 30'dan küçük olanları filtrele
    df_filtered = sevk_df[sevk_df['cover'] <= 50].copy()
    st.info(f"ℹ️ Mağaza cover ≤ 50 olan {len(df_filtered)} satır işlenecek (toplam: {len(sevk_df)})")
    
    # İhtiyaç hesabı - YOLDA STOĞU EKLE (doğru olan bu)
    df_filtered["ihtiyac"] = (
        (df_filtered["haftalik_satis"] * df_filtered["hedef_hafta"]) - 
        (df_filtered["mevcut_stok"] + df_filtered["yolda"])
    ).clip(lower=0)
    
    # Orijinal df'e ihtiyaç ekle - YOLDA STOĞU EKLE (doğru olan bu)
    original_sevkiyat_df["ihtiyac"] = (
        (original_sevkiyat_df["haftalik_satis"] * original_sevkiyat_df['hedef_hafta']) - 
        (original_sevkiyat_df["mevcut_stok"] + original_sevkiyat_df['yolda'])
    ).clip(lower=0)
    
    # Sıralama - YENİ: Önce ürün cover'a göre sırala
    df_sorted = df_filtered.sort_values(by=["urun_id", "urun_cover", "haftalik_satis"], ascending=[True, True, False]).copy()
    
    sevk_listesi = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Cover gruplarını PARAMETRELERDEN AL
    cover_gruplari_sirali = sorted(cover_gruplari, key=lambda x: x['min'])
    cover_gruplari_etiketler = [g['etiket'] for g in cover_gruplari_sirali]
    
    st.info(f"ℹ️ Kullanılan cover grupları: {cover_gruplari_etiketler}")
    
    # Tüm olası kombinasyonları oluştur
    all_combinations = []
    for magaza_grubu in cover_gruplari_etiketler:
        for urun_grubu in cover_gruplari_etiketler:
            all_combinations.append((magaza_grubu, urun_grubu))
    
    st.info(f"ℹ️ Toplam {len(all_combinations)} kombinasyon işlenecek")
    
    # Debug: Her kombinasyon için veri sayısını göster - TÜM GRUPLARI GÖSTER
    st.write("🔍 Kombinasyon Dağılımı:")
    dagilim_df = pd.DataFrame(columns=['Mağaza Grubu', 'Ürün Grubu', 'Kayıt Sayısı'])
    
    for magaza_grubu in cover_gruplari_etiketler:
        for urun_grubu in cover_gruplari_etiketler:
            count = len(df_sorted[
                (df_sorted['magaza_cover_grubu'] == magaza_grubu) & 
                (df_sorted['urun_cover_grubu'] == urun_grubu)
            ])
            dagilim_df = pd.concat([dagilim_df, pd.DataFrame({
                'Mağaza Grubu': [magaza_grubu],
                'Ürün Grubu': [urun_grubu],
                'Kayıt Sayısı': [count]
            })], ignore_index=True)
    
    # Tüm kombinasyonları tablo olarak göster
    pivot_dagilim = dagilim_df.pivot(index='Mağaza Grubu', columns='Ürün Grubu', values='Kayıt Sayısı').fillna(0)
    st.dataframe(pivot_dagilim, use_container_width=True)
    
    depo_urun_gruplari = list(df_sorted.groupby(["depo_id", "urun_id"]))
    total_groups = len(depo_urun_gruplari) * len(all_combinations)
    processed_groups = 0
    
    # Matrisi güvenli şekilde kullan
    def safe_get_carpan(magaza_cover_grubu, urun_cover_grubu):
        try:
            # Session state'den matrisi al
            carpan_matrisi = st.session_state.get('carpan_matrisi', {})
            return carpan_matrisi.get(magaza_cover_grubu, {}).get(urun_cover_grubu, 1.0)
        except:
            return 1.0
    
    # YENİ: Matris tabanlı işleme - TÜM GRUPLARI İŞLE
    for magaza_cover_grubu in cover_gruplari_etiketler:
        status_text.text(f"⏳ Mağaza {magaza_cover_grubu} Grubu İşleniyor...")
        magaza_grup_df = df_sorted[df_sorted["magaza_cover_grubu"] == magaza_cover_grubu]
        
        if magaza_grup_df.empty:
            processed_groups += len(depo_urun_gruplari) * len(cover_gruplari_etiketler)
            progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
            continue
        
        for urun_cover_grubu in cover_gruplari_etiketler:
            status_text.text(f"⏳ Mağaza {magaza_cover_grubu} × Ürün {urun_cover_grubu}...")
            grup_df = magaza_grup_df[magaza_grup_df["urun_cover_grubu"] == urun_cover_grubu]
            
            if grup_df.empty:
                processed_groups += len(depo_urun_gruplari)
                progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
                continue
            
            for (depo, urun), tum_grup in depo_urun_gruplari:
                grup = tum_grup[
                    (tum_grup["magaza_cover_grubu"] == magaza_cover_grubu) & 
                    (tum_grup["urun_cover_grubu"] == urun_cover_grubu)
                ]
                
                if grup.empty:
                    processed_groups += 1
                    progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
                    continue
                
                # Depo stok kontrolü
                stok_idx = (depo_stok_df["depo_id"] == depo) & (depo_stok_df["urun_id"] == urun)
                stok = int(depo_stok_df.loc[stok_idx, "depo_stok"].sum()) if stok_idx.any() else 0
                
                if stok <= 0:
                    processed_groups += 1
                    progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
                    continue
                
                # YENİ: Matristen çarpan al - GÜVENLİ VERSİYON
                carpan = safe_get_carpan(magaza_cover_grubu, urun_cover_grubu)
                
                # TUR 1: İhtiyaç bazlı sevkiyat
                for _, row in grup.iterrows():
                    min_adet = row["min_adet"]
                    MAKS_SEVK = row["maks_adet"]
                    ihtiyac = row["ihtiyac"]
                    
                    ihtiyac_carpanli = ihtiyac * carpan
                    
                    sevk = int(min(ihtiyac_carpanli, stok, MAKS_SEVK)) if stok > 0 and ihtiyac_carpanli > 0 else 0
                    
                    if sevk > 0:
                        stok -= sevk
                        sevk_listesi.append({
                            "depo_id": depo, "magaza_id": row["magaza_id"], "urun_id": urun,
                            "klasmankod": row["klasmankod"], "tur": 1, 
                            "magaza_cover_grubu": magaza_cover_grubu,
                            "urun_cover_grubu": urun_cover_grubu,
                            "ihtiyac": ihtiyac, "ihtiyac_carpanli": ihtiyac_carpanli, 
                            "carpan": carpan, "yolda": row["yolda"], "sevk_miktar": sevk,
                            "haftalik_satis": row["haftalik_satis"], "mevcut_stok": row["mevcut_stok"],
                            "cover": row["cover"], "urun_cover": row["urun_cover"],
                            "min_adet": min_adet, "maks_adet": MAKS_SEVK, "hedef_hafta": row["hedef_hafta"]
                        })
                
                # TUR 2: Min stok tamamlama (düşük cover olanlar için)
                if stok > 0:
                    for _, row in grup.iterrows():
                        if row["cover"] >= 12 and row["urun_cover"] >= 12:
                            continue
                            
                        min_adet = row["min_adet"]
                        MAKS_SEVK = row["maks_adet"]
                        mevcut = row["mevcut_stok"] + row["yolda"]
                        eksik_min = max(0, min_adet - mevcut)
                        
                        eksik_min_carpanli = eksik_min * carpan
                        
                        sevk2 = int(min(eksik_min_carpanli, stok, MAKS_SEVK)) if eksik_min_carpanli > 0 else 0
                        
                        if sevk2 > 0:
                            stok -= sevk2
                            sevk_listesi.append({
                                "depo_id": depo, "magaza_id": row["magaza_id"], "urun_id": urun,
                                "klasmankod": row["klasmankod"], "tur": 2,
                                "magaza_cover_grubu": magaza_cover_grubu,
                                "urun_cover_grubu": urun_cover_grubu,
                                "ihtiyac": row["ihtiyac"], "ihtiyac_carpanli": row["ihtiyac"] * carpan,
                                "carpan": carpan, "yolda": row["yolda"], "sevk_miktar": sevk2,
                                "haftalik_satis": row["haftalik_satis"], "mevcut_stok": row["mevcut_stok"],
                                "cover": row["cover"], "urun_cover": row["urun_cover"],
                                "min_adet": min_adet, "maks_adet": MAKS_SEVK, "hedef_hafta": row["hedef_hafta"]
                            })
                
                # Depo stok güncelleme
                if stok_idx.any():
                    if stok_idx.sum() == 1:
                        depo_stok_df.loc[stok_idx, "depo_stok"] = stok
                    else:
                        first_match_idx = stok_idx.idxmax()
                        depo_stok_df.loc[first_match_idx, "depo_stok"] = stok
                
                processed_groups += 1
                progress_bar.progress(min(100, int(100 * processed_groups / total_groups)))
            
            st.write(f"✅ {magaza_cover_grubu} × {urun_cover_grubu} kombinasyonu tamamlandı")
    
    progress_bar.progress(100)
    status_text.text("✅ Hesaplama tamamlandı")
    
    # Sonuçları birleştir
    if sevk_listesi:
        sevk_df_result = pd.DataFrame(sevk_listesi)
        
        # Grup bazında toplam sevkiyat
        total_sevk = sevk_df_result.groupby(
            ["depo_id", "magaza_id", "urun_id", "klasmankod", "magaza_cover_grubu", "urun_cover_grubu"], as_index=False
        ).agg({
            "sevk_miktar": "sum", "yolda": "first", "haftalik_satis": "first",
            "ihtiyac": "first", "mevcut_stok": "first", "cover": "first",
            "urun_cover": "first", "carpan": "first", "min_adet": "first", 
            "maks_adet": "first", "hedef_hafta": "first", "tur": "first"
        })
        
        # Min tamamlama (tur2) istatistiklerini hesapla
        min_tamamlama = sevk_df_result[sevk_df_result['tur'] == 2]['sevk_miktar'].sum()
        toplam_sevk = sevk_df_result['sevk_miktar'].sum()
        min_yuzde = (min_tamamlama / toplam_sevk * 100) if toplam_sevk > 0 else 0
        
        st.session_state.min_tamamlama = min_tamamlama
        st.session_state.min_yuzde = min_yuzde
        st.session_state.toplam_sevk = toplam_sevk
        st.session_state.sevk_df_result = sevk_df_result
        
        # Debug: Sonuçları göster - TÜM GRUPLARI GÖSTER
        st.write("🎯 Hesaplama Sonuçları - Grup Dağılımı:")
        grup_dagilim = sevk_df_result.groupby(['magaza_cover_grubu', 'urun_cover_grubu']).agg({
            'sevk_miktar': 'sum',
            'magaza_id': 'nunique'
        }).reset_index()
        
        st.dataframe(grup_dagilim, use_container_width=True)
        
        st.write(f"   - Toplam sevkiyat: {toplam_sevk:,} adet")
        st.write(f"   - Min tamamlama (Tur2): {min_tamamlama:,} adet")
        st.write(f"   - Min yüzdesi: {min_yuzde:.1f}%")
        st.write(f"   - Toplam işlem: {len(sevk_listesi)} sevkiyat kaydı")
        
    else:
        sevk_df_result = pd.DataFrame()
        total_sevk = pd.DataFrame()
        st.session_state.min_tamamlama = 0
        st.session_state.min_yuzde = 0
        st.session_state.toplam_sevk = 0
        st.session_state.sevk_df_result = pd.DataFrame()
        st.warning("⚠️ Hiç sevkiyat kaydı oluşturulamadı!")
    
    return sevk_df_result, total_sevk, depo_stok_df, original_sevkiyat_df
        
# -------------------------------
# RAPORLAR SAYFASI (GÜNCELLENMİŞ VE GENİŞLETİLMİŞ)
# -------------------------------

def show_reports():
    st.title("📊 Raporlar ve Analizler")
    
    if 'total_sevk' not in st.session_state or st.session_state.total_sevk.empty:
        st.warning("ℹ️ Henüz hesaplama yapılmadı. Önce ana sayfadan hesaplama çalıştırın.")
        return
    
    total_sevk = st.session_state.total_sevk.copy()
    sevk_df = st.session_state.get('sevk_df', pd.DataFrame())
    sevk_df_result = st.session_state.get('sevk_df_result', pd.DataFrame())
    original_sevkiyat_df = st.session_state.get('original_sevkiyat_df', pd.DataFrame())
    depo_stok_df = st.session_state.get('depo_stok_df', pd.DataFrame())
    
    # Magazalar_df ve urunler_df'ı session state'den al
    magazalar_df = st.session_state.get('magazalar_df', pd.DataFrame())
    urunler_df = st.session_state.get('urunler_df', pd.DataFrame())
    
    # SEKME TANIMLARI
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "📈 Özet Rapor", "🏪 Mağaza Analizi", "📦 Ürün Analizi", 
        "🛒 Alım İhtiyacı", "🎯 Matris Analizi", "📋 Detaylı Rapor"
    ])
    
    # Tab 1: Özet Rapor
    with tab1:
        st.subheader("📈 Özet Metrikler")
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        total_sevk_adet = st.session_state.toplam_sevk
        magaza_sayisi = total_sevk['magaza_id'].nunique()
        urun_cesidi = total_sevk['urun_id'].nunique()
        ortalama_magaza_cover = total_sevk['cover'].mean()
        ortalama_urun_cover = total_sevk['urun_cover'].mean()
        min_yuzde = st.session_state.min_yuzde
        
        col1.metric("Toplam Sevkiyat", f"{total_sevk_adet:,}")
        col2.metric("Mağaza Sayısı", f"{magaza_sayisi:,}")
        col3.metric("Ürün Çeşidi", f"{urun_cesidi:,}")
        col4.metric("Ort. Mağaza Cover", f"{ortalama_magaza_cover:.1f}")
        col5.metric("Ort. Ürün Cover", f"{ortalama_urun_cover:.1f}")
        col6.metric("Min %", f"{min_yuzde:.1f}%")
        
        # İhtiyaç karşılama oranı
        if 'ihtiyac' in total_sevk.columns:
            toplam_ihtiyac = total_sevk['ihtiyac'].sum()
            ihtiyac_karsilama_orani = (total_sevk_adet / toplam_ihtiyac * 100) if toplam_ihtiyac > 0 else 0
            st.metric("İhtiyaç Karşılama Oranı", f"{ihtiyac_karsilama_orani:.1f}%")
        
        # Matris bazlı analiz
        if not sevk_df_result.empty:
            st.subheader("🎯 Matris Bazlı Dağılım")
            matris_dagilim = sevk_df_result.groupby(['magaza_cover_grubu', 'urun_cover_grubu']).agg({
                'sevk_miktar': 'sum',
                'magaza_id': 'nunique',
                'urun_id': 'nunique',
                'ihtiyac': 'sum'
            }).reset_index()
            
            matris_dagilim['magaza_basi_sevk'] = (matris_dagilim['sevk_miktar'] / matris_dagilim['magaza_id']).round(1)
            matris_dagilim['ihtiyac_karsilama'] = (matris_dagilim['sevk_miktar'] / matris_dagilim['ihtiyac'] * 100).round(1)
            
            st.dataframe(matris_dagilim, use_container_width=True)
    
    # Tab 2: Mağaza Analizi
    with tab2:
        st.subheader("🏪 Mağaza Analizi")
        
        if not total_sevk.empty:
            # Mağaza bazlı özet
            magaza_analiz = total_sevk.groupby(['magaza_id', 'magaza_cover_grubu']).agg({
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'cover': 'first',
                'haftalik_satis': 'first'
            }).reset_index()
            
            # Mağaza adı ekle
            if not magazalar_df.empty:
                magazalar_df_copy = magazalar_df.copy()
                magazalar_df_copy['magaza_id'] = magazalar_df_copy['magaza_id'].astype(str).str.strip()
                magaza_analiz['magaza_id'] = magaza_analiz['magaza_id'].astype(str).str.strip()
                if 'magaza_adi' in magazalar_df_copy.columns:
                    magaza_analiz = pd.merge(
                        magaza_analiz,
                        magazalar_df_copy[['magaza_id', 'magaza_adi']],
                        on='magaza_id',
                        how='left'
                    )
            
            # Hesaplamalar
            magaza_analiz['ihtiyac_karsilama_orani'] = (magaza_analiz['sevk_miktar'] / magaza_analiz['ihtiyac'] * 100).round(1)
            magaza_analiz['sevk_satis_orani'] = (magaza_analiz['sevk_miktar'] / magaza_analiz['haftalik_satis']).round(2)
            
            st.write(f"**Toplam {len(magaza_analiz)} mağaza analizi:**")
            st.dataframe(magaza_analiz, use_container_width=True)
            
            # Mağaza Cover Grubu bazlı analiz
            st.subheader("🏪 Mağaza Cover Grubu Bazlı Analiz")
            magaza_grup_analiz = magaza_analiz.groupby('magaza_cover_grubu').agg({
                'magaza_id': 'nunique',
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'haftalik_satis': 'sum',
                'cover': 'mean'
            }).reset_index()
            
            magaza_grup_analiz['magaza_basi_sevk'] = (magaza_grup_analiz['sevk_miktar'] / magaza_grup_analiz['magaza_id']).round(1)
            magaza_grup_analiz['ihtiyac_karsilama'] = (magaza_grup_analiz['sevk_miktar'] / magaza_grup_analiz['ihtiyac'] * 100).round(1)
            magaza_grup_analiz['sevk_satis_orani'] = (magaza_grup_analiz['sevk_miktar'] / magaza_grup_analiz['haftalik_satis']).round(2)
            
            st.dataframe(magaza_grup_analiz, use_container_width=True)
    
    # Tab 3: Ürün Analizi
    with tab3:
        st.subheader("📦 Ürün Analizi")
        
        if not total_sevk.empty:
            # Ürün bazlı özet
            urun_analiz = total_sevk.groupby(['urun_id', 'urun_cover_grubu']).agg({
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'magaza_id': 'nunique',
                'haftalik_satis': 'first',
                'urun_cover': 'first'
            }).reset_index()
            
            # Ürün adı ekle
            if not urunler_df.empty:
                urunler_df_copy = urunler_df.copy()
                urunler_df_copy['urun_id'] = urunler_df_copy['urun_id'].astype(str).str.strip()
                urun_analiz['urun_id'] = urun_analiz['urun_id'].astype(str).str.strip()
                if 'urun_adi' in urunler_df_copy.columns:
                    urun_analiz = pd.merge(
                        urun_analiz,
                        urunler_df_copy[['urun_id', 'urun_adi']],
                        on='urun_id',
                        how='left'
                    )
            
            # Hesaplamalar
            urun_analiz['magaza_basi_sevk'] = (urun_analiz['sevk_miktar'] / urun_analiz['magaza_id']).round(1)
            urun_analiz['ihtiyac_karsilama_orani'] = (urun_analiz['sevk_miktar'] / urun_analiz['ihtiyac'] * 100).round(1)
            urun_analiz['sevk_satis_orani'] = (urun_analiz['sevk_miktar'] / urun_analiz['haftalik_satis']).round(2)
            
            st.write(f"**Toplam {len(urun_analiz)} ürün analizi (ilk 100):**")
            st.dataframe(urun_analiz.head(100), use_container_width=True)
            
            # Ürün Cover Grubu bazlı analiz
            st.subheader("📦 Ürün Cover Grubu Bazlı Analiz")
            urun_grup_analiz = urun_analiz.groupby('urun_cover_grubu').agg({
                'urun_id': 'nunique',
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'magaza_id': 'sum',
                'haftalik_satis': 'sum'
            }).reset_index()
            
            urun_grup_analiz['magaza_basi_sevk'] = (urun_grup_analiz['sevk_miktar'] / urun_grup_analiz['magaza_id']).round(1)
            urun_grup_analiz['ihtiyac_karsilama'] = (urun_grup_analiz['sevk_miktar'] / urun_grup_analiz['ihtiyac'] * 100).round(1)
            urun_grup_analiz['ortalama_cover'] = urun_analiz.groupby('urun_cover_grubu')['urun_cover'].mean().round(1).values
            
            st.dataframe(urun_grup_analiz, use_container_width=True)
    
    # Tab 4: Alım İhtiyacı
    with tab4:
        st.subheader("🛒 Alım Sipariş İhtiyacı")
        
        # Alım ihtiyacını hesapla
        alim_ihtiyaci = calculate_purchase_need(sevk_df, total_sevk, original_sevkiyat_df, depo_stok_df)
        
        if not alim_ihtiyaci.empty:
            # Basit özet göster
            toplam_ihtiyac = alim_ihtiyaci['alim_siparis_miktari'].sum()
            urun_cesidi = len(alim_ihtiyaci)
            ortalama_cover = alim_ihtiyaci['toplam_ihtiyac_cover'].mean()
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Toplam Alım İhtiyacı", f"{toplam_ihtiyac:,.0f} adet")
            col2.metric("Ürün Çeşidi", f"{urun_cesidi}")
            col3.metric("Ort. Cover İhtiyacı", f"{ortalama_cover:.1f} hafta")
            col4.metric("En Yüksek İhtiyaç", f"{alim_ihtiyaci['alim_siparis_miktari'].max():,.0f} adet")
            
            st.success(f"✅ {urun_cesidi} ürün için toplam {toplam_ihtiyac:,.0f} adet alım sipariş talebi oluştu")
            
            # YENİ: Ürün × Depo Pivot Tablosu
            st.subheader("📊 Ürün Bazlı Depo Dağılımı")
            
            # Pivot tablo oluştur: Ürünler satırda, depolar sütunda
            pivot_alim = alim_ihtiyaci.pivot_table(
                index=['urun_id', 'urun_adi'],
                columns='depo_id',
                values='alim_siparis_miktari',
                aggfunc='sum',
                fill_value=0
            ).reset_index()
            
            # Toplam sütunu ekle
            pivot_alim['TOPLAM'] = pivot_alim.select_dtypes(include=[np.number]).sum(axis=1)
            
            # Sütun isimlerini düzenle
            depo_columns = [col for col in pivot_alim.columns if str(col).isdigit()]
            pivot_alim.columns = [f"Depo_{col}" if str(col).isdigit() else str(col) for col in pivot_alim.columns]
            
            # Toplam satırı ekle
            toplam_row = {'urun_id': 'TOPLAM', 'urun_adi': 'TOPLAM'}
            for depo_col in depo_columns:
                toplam_row[f"Depo_{depo_col}"] = pivot_alim[f"Depo_{depo_col}"].sum()
            toplam_row['TOPLAM'] = pivot_alim['TOPLAM'].sum()
            
            pivot_with_totals = pd.concat([pivot_alim, pd.DataFrame([toplam_row])], ignore_index=True)
            
            # Tabloyu göster
            def highlight_totals(row):
                if row['urun_id'] == 'TOPLAM':
                    return ['background-color: #2E86AB; color: white; font-weight: bold'] * len(row)
                return [''] * len(row)
            
            numeric_columns = [col for col in pivot_with_totals.columns if col not in ['urun_id', 'urun_adi']]
            styled_pivot = pivot_with_totals.style.format(
                "{:,.0f}", 
                subset=numeric_columns
            ).apply(highlight_totals, axis=1)
            
            st.dataframe(styled_pivot, use_container_width=True)
            
            # Depo bazlı toplamları da göster
            st.write("**Depo Bazlı Toplamlar:**")
            depo_toplam_df = pd.DataFrame([
                {'Depo': f"Depo {depo_id}", 'Toplam İhtiyaç': pivot_alim[f"Depo_{depo_id}"].sum()}
                for depo_id in depo_columns
            ])
            st.dataframe(depo_toplam_df, use_container_width=True)
                
        else:
            st.info("ℹ️ Alım ihtiyacı bulunmamaktadır.")

    
    # Tab 5: Matris Analizi
    with tab5:
        st.subheader("🎯 Matris Performans Analizi")
        
        if not sevk_df_result.empty:
            # Cover grupları karşılaştırması
            st.write("**Cover Grupları Karşılaştırması:**")
            cover_karsilastirma = sevk_df_result.groupby(['magaza_cover_grubu', 'urun_cover_grubu']).agg({
                'sevk_miktar': 'sum',
                'ihtiyac': 'sum',
                'magaza_id': 'nunique',
                'carpan': 'mean'
            }).reset_index()
            
            cover_karsilastirma['magaza_basi_sevk'] = (cover_karsilastirma['sevk_miktar'] / cover_karsilastirma['magaza_id']).round(1)
            cover_karsilastirma['ihtiyac_karsilama_orani'] = (cover_karsilastirma['sevk_miktar'] / cover_karsilastirma['ihtiyac'] * 100).round(1)
            cover_karsilastirma['ihtiyac_karsilama_orani'] = cover_karsilastirma['ihtiyac_karsilama_orani'].replace([np.inf, -np.inf], 0)
            
            st.dataframe(cover_karsilastirma, use_container_width=True)
    
    # Tab 6: Detaylı Rapor
    with tab6:
        st.subheader("📋 Detaylı Sevkiyat Raporu")
        
        if not total_sevk.empty:
            # Tüm detayları göster
            st.write("**Tüm Sevkiyat Detayları:**")
            st.dataframe(total_sevk, use_container_width=True)
            
            # İndirme butonu
            csv = total_sevk.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                "📥 Detaylı Raporu İndir",
                csv,
                "detayli_sevkiyat_raporu.csv",
                "text/csv",
                use_container_width=True
            )

# -------------------------------
# ANA SAYFA FONKSİYONU
# -------------------------------

def show_main_page():
    st.markdown("""
    <div style="text-align: center; padding: 25px; background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%); color: white; border-radius: 15px; margin-bottom: 25px;">
        <h1>📦 EVE Sevkiyat Planlama Sistemi</h1>
        <p>YENİ SİSTEM - Matris Tabanlı Cover Optimizasyonu</p>
    </div>
    """, unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Parametreler", "📁 Veri Yükleme", "🚀 Hesaplama"])
    
    with tab1:
        hedef_hafta, min_adet, maks_adet, cover_df = manage_cover_groups_and_matrix()
        st.session_state.params = {
            'hedef_hafta': hedef_hafta,
            'min_adet': min_adet,
            'maks_adet': maks_adet
        }
        st.session_state.cover_gruplari = cover_df.to_dict('records') if not cover_df.empty else []
    
    with tab2:
        file_data = create_file_upload_section()
        st.session_state.file_data = file_data
        
        if file_data:
            selected_file = st.selectbox("Dosya önizleme:", list(file_data.keys()))
            if selected_file and not file_data[selected_file].empty:
                st.dataframe(file_data[selected_file].head(10), use_container_width=True)
    
    with tab3:
        st.header("🚀 Sevkiyat Hesaplama")
        
        if not st.session_state.get('file_data'):
            st.error("❌ Lütfen önce veri yükleme sekmesinden dosyaları yükleyin!")
            return
        
        # DEBUG: Veri önizleme
        with st.expander("🔍 Debug - Veri Önizleme", expanded=False):
            if 'file_data' in st.session_state:
                sevk_df = None
                for name, df in st.session_state.file_data.items():
                    if "sevkiyat" in name.lower():
                        sevk_df = df.copy()
                        break
                
                if sevk_df is not None:
                    sevk_df = normalize_columns(sevk_df)
                    st.write("Sevkiyat verisi önizleme (ilk 5 satır):")
                    st.dataframe(sevk_df.head(5))
                    
                    # Cover değerlerini kontrol et
                    if 'cover' in sevk_df.columns:
                        st.write("Mağaza Cover Değerleri:")
                        st.write(f"Min: {sevk_df['cover'].min()}, Max: {sevk_df['cover'].max()}")
                        st.write(f"Ortalama: {sevk_df['cover'].mean():.2f}")
                    
                    # Ürün cover simülasyonu - YOLDA STOĞU ÇIKARMA
                    if all(col in sevk_df.columns for col in ['haftalik_satis', 'mevcut_stok']):
                        # Veri tiplerini düzelt
                        sevk_df['haftalik_satis'] = pd.to_numeric(sevk_df['haftalik_satis'], errors='coerce').fillna(0.1)
                        sevk_df['mevcut_stok'] = pd.to_numeric(sevk_df['mevcut_stok'], errors='coerce').fillna(0)
                        
                        # DÜZELTME: Yolda stoğu çıkarmadan hesapla
                        sevk_df['urun_cover_sim'] = sevk_df.apply(
                            lambda row: calculate_urun_cover(row['haftalik_satis'], row['mevcut_stok']), 
                            axis=1
                        )
                        st.write("Ürün Cover Simülasyonu (Yolda stoğu çıkarılmadan):")
                        st.write(f"Min: {sevk_df['urun_cover_sim'].min():.2f}, Max: {sevk_df['urun_cover_sim'].max():.2f}")
                        st.write(f"Ortalama: {sevk_df['urun_cover_sim'].mean():.2f}")
                        
                        # Grup dağılımı simülasyonu - FONKSİYON ADI DÜZELTİLDİ
                        if 'cover_gruplari' in st.session_state and st.session_state.cover_gruplari:
                            sevk_df['urun_cover_grubu_sim'] = sevk_df['urun_cover_sim'].apply(
                                lambda x: get_cover_grubu_adi(x, st.session_state.cover_gruplari)
                            )
                            st.write("Ürün Cover Grup Dağılımı (Simülasyon - Tüm Gruplar):")
                            dagilim = sevk_df['urun_cover_grubu_sim'].value_counts().reindex(
                                [g['etiket'] for g in st.session_state.cover_gruplari], fill_value=0
                            )
                            st.write(dagilim)
                        else:
                            st.warning("Cover grupları tanımlı değil")
        
        # Parametre bilgilerini göster
        st.info(f"🔧 Kullanılacak parametreler: Hedef Hafta={st.session_state.params['hedef_hafta']}, Min Adet={st.session_state.params['min_adet']}, Maks Adet={st.session_state.params['maks_adet']}")
        
        # Matris bilgisini göster
        st.info(f"🎯 Kullanılacak çarpan matrisi: {len(st.session_state.carpan_matrisi)}×{len(st.session_state.carpan_matrisi)} boyutunda")
        
        if st.button("🎯 HESAPLAMAYI BAŞLAT", type="primary", use_container_width=True):
            try:
                with st.spinner("Matris tabanlı optimizasyon çalışıyor..."):
                    start_time = time.time()
                    
                    sevk_df, total_sevk, depo_stok_df, original_sevkiyat_df = calculate_shipment_optimized(
                        st.session_state.file_data,
                        st.session_state.params,
                        st.session_state.cover_gruplari
                    )
                    
                    st.session_state.sevk_df = sevk_df
                    st.session_state.total_sevk = total_sevk
                    st.session_state.depo_stok_df = depo_stok_df
                    st.session_state.original_sevkiyat_df = original_sevkiyat_df
                    st.session_state.calculation_done = True
                    st.session_state.sure_sn = time.time() - start_time
                    
                    st.success("🎉 Matris tabanlı hesaplama tamamlandı!")
                    
                    # Özet metrikler
                    if not total_sevk.empty:
                        st.subheader("📊 Özet Metrikler")
                        col1, col2, col3, col4, col5, col6 = st.columns(6)
                        col1.metric("Toplam Sevkiyat", f"{st.session_state.toplam_sevk:,}")
                        col2.metric("Mağaza Sayısı", total_sevk['magaza_id'].nunique())
                        col3.metric("Ürün Çeşidi", total_sevk['urun_id'].nunique())
                        col4.metric("Ort. Mağaza Cover", f"{total_sevk['cover'].mean():.1f}")
                        col5.metric("Ort. Ürün Cover", f"{total_sevk['urun_cover'].mean():.1f}")
                        col6.metric("Min %", f"{st.session_state.min_yuzde:.1f}%")
                    
                    # Detay tablosu - TÜM GRUPLARI GÖSTER
                    st.subheader("📋 Sevkiyat Detayları - Grup Bazında")
                    if not total_sevk.empty:
                        # Grup bazında özet
                        grup_bazli_ozet = total_sevk.groupby(['magaza_cover_grubu', 'urun_cover_grubu']).agg({
                            'sevk_miktar': 'sum',
                            'magaza_id': 'nunique',
                            'urun_id': 'nunique',
                            'carpan': 'mean'
                        }).round(2).reset_index()
                        
                        st.write("**Grup Bazlı Özet:**")
                        st.dataframe(grup_bazli_ozet, use_container_width=True)
                        
                        st.write("**Detaylı Sevkiyat Listesi (İlk 100 satır):**")
                        st.dataframe(total_sevk.head(100), use_container_width=True)
                    
                    # İndirme butonları
                    if not total_sevk.empty:
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            csv_sevk = total_sevk.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                "📥 Sevkiyat Planını İndir", 
                                csv_sevk, 
                                "sevkiyat_planı.csv", 
                                "text/csv",
                                use_container_width=True
                            )
                        with col2:
                            alim_ihtiyaci = calculate_purchase_need(sevk_df, total_sevk, original_sevkiyat_df, depo_stok_df)
                            if not alim_ihtiyaci.empty:
                                csv_alim = alim_ihtiyaci.to_csv(index=False, encoding='utf-8-sig')
                                st.download_button(
                                    "📥 Alım İhtiyacını İndir", 
                                    csv_alim, 
                                    "alim_siparis_ihtiyaci.csv", 
                                    "text/csv",
                                    use_container_width=True
                                )
                        with col3:
                            # Detaylı rapor indirme
                            csv_detay = total_sevk.to_csv(index=False, encoding='utf-8-sig')
                            st.download_button(
                                "📊 Detaylı Raporu İndir",
                                csv_detay,
                                "detayli_sevkiyat_raporu.csv",
                                "text/csv",
                                use_container_width=True
                            )
                    
            except Exception as e:
                st.error(f"❌ Hata oluştu: {str(e)}")
                # Hata detayını göster
                import traceback
                with st.expander("Hata Detayları"):
                    st.code(traceback.format_exc())

# -------------------------------
# ANA UYGULAMA
# -------------------------------

def main():
    st.set_page_config(page_title="EVE Sevkiyat - Matris Sistemi", layout="wide")
    
    # CSS stilleri
    st.markdown("""
    <style>
        .main-header {
            text-align: center;
            padding: 25px;
            background: linear-gradient(135deg, #1E40AF 0%, #1E3A8A 100%);
            color: white;
            border-radius: 15px;
            margin-bottom: 25px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f0f2f6;
            border-radius: 8px 8px 0px 0px;
            gap: 8px;
            padding: 10px 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E40AF;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)
    
    main_tab1, main_tab2 = st.tabs(["🏠 Ana Sayfa", "📈 Raporlar"])
    
    with main_tab1:
        show_main_page()
    
    with main_tab2:
        show_reports()

if __name__ == "__main__":
    main()






















