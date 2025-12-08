import streamlit as st
import pandas as pd
import time
import numpy as np
import io

# Sayfa config

import streamlit as st
import pandas as pd
import time
import numpy as np
import io
from datetime import datetime
import sqlite3
import hashlib
import zipfile
from zipfile import ZipFile

# ============================================
# TOKEN SİSTEMİ
# ============================================
def check_authentication():
    """Token sistemini kontrol et"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'tokens' not in st.session_state:
        st.session_state.tokens = 0
    
    return st.session_state.authenticated

def deduct_tokens(amount):
    """Token düş"""
    if st.session_state.tokens >= amount:
        st.session_state.tokens -= amount
        # DB'ye kaydet (opsiyonel)
        return True
    return False

def get_user_info():
    """Kullanıcı bilgilerini al"""
    return {
        'username': st.session_state.get('username', 'demo'),
        'tokens': st.session_state.get('tokens', 1000)
    }

# ============================================
# SESSION STATE BAŞLANGICI
# ============================================
if not check_authentication():
    st.warning("⚠️ Lütfen giriş yapın!")
    st.stop()

# Token kontrolü - Sadece ilk açılışta
if 'sevkiyat_opened' not in st.session_state:
    st.session_state.sevkiyat_opened = True
    # Token düşüşü: Home.py'da yapılıyor, burada tekrar düşürme!

# ============================================
# SIDEBAR - KULLANICI PROFILI
# ============================================
user_info = get_user_info()
st.sidebar.markdown(f"""
<div style='padding: 1rem; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
            border-radius: 10px; margin-bottom: 1rem; color: white;'>
    <div style='font-size: 0.9em; opacity: 0.9;'>👤 Kullanıcı</div>
    <div style='font-size: 1.1em; font-weight: bold; margin: 0.3rem 0;'>{user_info['username']}</div>
    <div style='font-size: 0.9em;'>🪙 Token: <span style='font-weight: bold;'>{user_info['tokens']}</span></div>
</div>
""", unsafe_allow_html=True)



st.set_page_config(
    page_title="Retail Sevkiyat Planlama",
    page_icon="📦", 
    layout="wide"
)

# ============================================
# SESSION STATE BAŞLATMA - TEK SEFERDE
# ============================================

# Veri dosyaları
if 'urun_master' not in st.session_state:
    st.session_state.urun_master = None
if 'magaza_master' not in st.session_state:
    st.session_state.magaza_master = None
if 'yasak_master' not in st.session_state:
    st.session_state.yasak_master = None
if 'depo_stok' not in st.session_state:
    st.session_state.depo_stok = None
if 'anlik_stok_satis' not in st.session_state:
    st.session_state.anlik_stok_satis = None
if 'haftalik_trend' not in st.session_state:
    st.session_state.haftalik_trend = None
if 'kpi' not in st.session_state:
    st.session_state.kpi = None

# PO session state'leri
if 'alim_siparis_sonuc' not in st.session_state:
    st.session_state.alim_siparis_sonuc = None
if 'po_yasak' not in st.session_state:
    st.session_state.po_yasak = None
if 'po_detay_kpi' not in st.session_state:
    st.session_state.po_detay_kpi = None
if 'cover_segment_matrix' not in st.session_state:
    st.session_state.cover_segment_matrix = None

# Segmentasyon parametreleri - TEK TANIMLA
if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))],
        'store_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    }

# Matrisler
if 'initial_matris' not in st.session_state:
    st.session_state.initial_matris = None
if 'target_matrix' not in st.session_state:
    st.session_state.target_matrix = None
if 'sisme_orani' not in st.session_state:
    st.session_state.sisme_orani = None
if 'genlestirme_orani' not in st.session_state:
    st.session_state.genlestirme_orani = None
if 'min_oran' not in st.session_state:
    st.session_state.min_oran = None

# Diğer
if 'siralama_data' not in st.session_state:
    st.session_state.siralama_data = None
if 'sevkiyat_sonuc' not in st.session_state:
    st.session_state.sevkiyat_sonuc = None
if 'yeni_urun_listesi' not in st.session_state:
    st.session_state.yeni_urun_listesi = None

# Hedef Matris'ten gelen segmentler (otomatik kaydedilecek)
if 'urun_segment_map' not in st.session_state:
    st.session_state.urun_segment_map = None
if 'magaza_segment_map' not in st.session_state:
    st.session_state.magaza_segment_map = None
if 'prod_segments' not in st.session_state:
    st.session_state.prod_segments = None
if 'store_segments' not in st.session_state:
    st.session_state.store_segments = None

# Sidebar menü 
menu = st.sidebar.radio(
    "Menü",
    ["📂 Veri Yükleme", "🏠 Ana Sayfa", "🫧 Segmentasyon", "🎲 Hedef Matris", 
     "🔢 Sıralama", "📐 Hesaplama", "📈 Raporlar", "💾 Master Data",
     "💵 PO Hesaplama", "📊 PO Raporları", "📦 Depo Bazlı PO"]
)

# ============================================
# 🏠 ANA SAYFA
# ============================================

# ============================================
# 📂 VERİ YÜKLEME MODÜLÜ
# ============================================
if menu == "📂 Veri Yükleme":
    st.title("📂 Veri Yükleme")
    st.markdown("---")

    st.set_page_config(
        page_title="Veri Yükleme",
        page_icon="📤",
        layout="wide"
    )

    # ============================================
    # CSS - YAZI TİPLERİNİ %30 KÜÇÜLT
    # ============================================
    st.markdown("""
    <style>
        html, body, [class*="css"] {
            font-size: 70% !important;
        }
        h1 { font-size: 1.8rem !important; }
        h2 { font-size: 1.4rem !important; }
        h3 { font-size: 1.2rem !important; }
        .stButton>button { font-size: 0.7rem !important; }
        .stSelectbox, .stMultiSelect, .stTextInput { font-size: 0.7rem !important; }
    </style>
    """, unsafe_allow_html=True)

    # Session state başlatma
    if 'urun_master' not in st.session_state:
        st.session_state.urun_master = None
    if 'magaza_master' not in st.session_state:
        st.session_state.magaza_master = None
    if 'yasak_master' not in st.session_state:
        st.session_state.yasak_master = None
    if 'depo_stok' not in st.session_state:
        st.session_state.depo_stok = None
    if 'anlik_stok_satis' not in st.session_state:
        st.session_state.anlik_stok_satis = None
    if 'haftalik_trend' not in st.session_state:
        st.session_state.haftalik_trend = None
    if 'kpi' not in st.session_state:
        st.session_state.kpi = None
    if 'po_yasak' not in st.session_state:
        st.session_state.po_yasak = None
    if 'po_detay_kpi' not in st.session_state:
        st.session_state.po_detay_kpi = None

    # ============================================
    # ANA SAYFA
    # ============================================
    st.title("📤 Ortak Veri Yükleme Merkezi")
    st.markdown("---")

    # CSV okuma fonksiyonu
    def read_csv_safe(file):
        try:
            df = pd.read_csv(file, sep=';', encoding='utf-8-sig', quoting=1, on_bad_lines='warn')
            return df, ';'
        except:
            try:
                file.seek(0)
                df = pd.read_csv(file, sep=',', encoding='utf-8-sig', quoting=1, on_bad_lines='warn')
                return df, ','
            except Exception as e:
                raise Exception(f"CSV okuma hatası: {str(e)}")

    # CSV yazma fonksiyonu
    def write_csv_safe(df):
        return df.to_csv(index=False, sep=';', encoding='utf-8-sig', quoting=1)

    # Örnek CSV'ler
    example_csvs = {
        'urun_master.csv': {
            'data': pd.DataFrame({
                'urun_kod': ['U001', 'U002', 'U003'],
                'satici_kod': ['S001', 'S002', 'S001'],
                'kategori_kod': ['K001', 'K002', 'K001'],
                'umg': ['UMG1', 'UMG2', 'UMG1'],
                'mg': ['MG1', 'MG2', 'MG1'],
                'marka_kod': ['M001', 'M002', 'M001'],
                'klasman_kod': ['K1', 'K2', 'K1'],
                'nitelik': ['Nitelik 1, özellik A', 'Nitelik 2, özellik B', 'Nitelik 1, özellik C'],
                'durum': ['Aktif', 'Aktif', 'Pasif'],
                'ithal': [1, 0, 1],
                'olcu_birimi': ['Adet', 'Adet', 'Kg'],
                'koli_ici': [12, 24, 6],
                'paket_ici': [6, 12, 3]
            }),
            'icon': '📦'
        },
        'magaza_master.csv': {
            'data': pd.DataFrame({
                'magaza_kod': ['M001', 'M002', 'M003'],
                'il': ['İstanbul', 'Ankara', 'İzmir'],
                'bolge': ['Marmara', 'İç Anadolu', 'Ege'],
                'tip': ['Hipermarket', 'Süpermarket', 'Hipermarket'],
                'adres_kod': ['ADR001', 'ADR002', 'ADR003'],
                'sm': [5000, 3000, 4500],
                'bs': ['BS1', 'BS2', 'BS1'],
                'depo_kod': ['D001', 'D001', 'D002']
            }),
            'icon': '🏪'
        },
        'yasak.csv': {
            'data': pd.DataFrame({
                'urun_kod': ['U001', 'U002'],
                'magaza_kod': ['M002', 'M001'],
                'yasak_durum': [1, 1]
            }),
            'icon': '🚫'
        },
        'depo_stok.csv': {
            'data': pd.DataFrame({
                'depo_kod': ['D001', 'D001', 'D002'],
                'urun_kod': ['U001', 'U002', 'U001'],
                'stok': [1000, 1500, 800]
            }),
            'icon': '📦'
        },
        'anlik_stok_satis.csv': {
            'data': pd.DataFrame({
                'magaza_kod': ['M001', 'M001', 'M002'],
                'urun_kod': ['U001', 'U002', 'U001'],
                'stok': [100, 150, 120],
                'yol': [20, 30, 25],
                'satis': [50, 40, 45],
                'ciro': [5000, 6000, 5500],
                'smm': [2.0, 3.75, 2.67]
            }),
            'icon': '📊'
        },
        'haftalik_trend.csv': {
            'data': pd.DataFrame({
                'klasman_kod': ['K1', 'K1', 'K2'],
                'marka_kod': ['M001', 'M001', 'M002'],
                'yil': [2025, 2025, 2025],
                'hafta': [40, 41, 40],
                'stok': [10000, 9500, 15000],
                'satis': [2000, 2100, 1800],
                'ciro': [200000, 210000, 270000],
                'smm': [5.0, 4.52, 8.33],
                'iftutar': [1000000, 950000, 1500000]
            }),
            'icon': '📈'
        },
        'kpi.csv': {
            'data': pd.DataFrame({
                'mg_id': ['MG1', 'MG2', 'MG3'],
                'min_deger': [0, 100, 500],
                'max_deger': [99, 499, 999],
                'forward_cover': [1.5, 2.0, 2.5]
            }),
            'icon': '🎯'
        },
        'po_yasak.csv': {
            'data': pd.DataFrame({
                'urun_kodu': ['U001', 'U002', 'U003'],
                'yasak_durum': [1, 0, 1],
                'acik_siparis': [100, 0, 250]
            }),
            'icon': '🚫'
        },
        'po_detay_kpi.csv': {
            'data': pd.DataFrame({
                'marka_kod': ['M001', 'M002', 'M003'],
                'mg_kod': ['MG1', 'MG2', 'MG1'],
                'cover_hedef': [12.0, 15.0, 10.0],
                'bkar_hedef': [25.0, 30.0, 20.0]
            }),
            'icon': '🎯'
        }
    }

    # Veri tanımları
    data_definitions = {
        'urun_master': {
            'name': 'Ürün Master',
            'required': True,
            'columns': ['urun_kod', 'satici_kod', 'kategori_kod', 'umg', 'mg', 'marka_kod', 
                       'klasman_kod', 'nitelik', 'durum', 'ithal', 'olcu_birimi', 'koli_ici', 'paket_ici'],
            'state_key': 'urun_master',
            'icon': '📦',
            'modules': ['Sevkiyat', 'PO', 'Prepack']
        },
        'magaza_master': {
            'name': 'Mağaza Master',
            'required': True,
            'columns': ['magaza_kod', 'il', 'bolge', 'tip', 'adres_kod', 'sm', 'bs', 'depo_kod'],
            'state_key': 'magaza_master',
            'icon': '🏪',
            'modules': ['Sevkiyat', 'PO']
        },
        'depo_stok': {
            'name': 'Depo Stok',
            'required': True,
            'columns': ['depo_kod', 'urun_kod', 'stok'],
            'state_key': 'depo_stok',
            'icon': '📦',
            'modules': ['Sevkiyat', 'PO']
        },
        'anlik_stok_satis': {
            'name': 'Anlık Stok/Satış',
            'required': True,
            'columns': ['magaza_kod', 'urun_kod', 'stok', 'yol', 'satis', 'ciro', 'smm'],
            'state_key': 'anlik_stok_satis',
            'icon': '📊',
            'modules': ['Sevkiyat', 'PO']
        },
        'kpi': {
            'name': 'KPI',
            'required': True,
            'columns': ['mg_id', 'min_deger', 'max_deger', 'forward_cover'],
            'state_key': 'kpi',
            'icon': '🎯',
            'modules': ['Sevkiyat', 'PO']
        },
        'yasak_master': {
            'name': 'Yasak',
            'required': False,
            'columns': ['urun_kod', 'magaza_kod', 'yasak_durum'],
            'state_key': 'yasak_master',
            'icon': '🚫',
            'modules': ['Sevkiyat']
        },
        'haftalik_trend': {
            'name': 'Haftalık Trend',
            'required': False,
            'columns': ['klasman_kod', 'marka_kod', 'yil', 'hafta', 'stok', 'satis', 'ciro', 'smm', 'iftutar'],
            'state_key': 'haftalik_trend',
            'icon': '📈',
            'modules': ['Sevkiyat']
        },
        'po_yasak': {
            'name': 'PO Yasak',
            'required': False,
            'columns': ['urun_kodu', 'yasak_durum', 'acik_siparis'],
            'state_key': 'po_yasak',
            'icon': '🚫',
            'modules': ['PO']
        },
        'po_detay_kpi': {
            'name': 'PO Detay KPI',
            'required': False,
            'columns': ['marka_kod', 'mg_kod', 'cover_hedef', 'bkar_hedef'],
            'state_key': 'po_detay_kpi',
            'icon': '🎯',
            'modules': ['PO']
        }
    }

    # ============================================
    # 📖 KULLANICI KILAVUZU - İNDİRİLEBİLİR DOKÜMAN
    # ============================================
    st.markdown("---")
    st.subheader("📖 Kullanıcı Kılavuzu")

    # Kılavuz içeriğini hazırla
    kilavuz_metni = """
    ═══════════════════════════════════════════════════════════════
                        📖 VERİ YÜKLEME KILAVUZU
                            Thorius Sistemi
    ═══════════════════════════════════════════════════════════════

    İçindekiler:
    1. Hızlı Başlangıç
    2. Dosya Formatı Gereksinimleri
    3. Zorunlu Dosyalar ve Açıklamaları
    4. Kolon Açıklamaları (Detaylı)
    5. Yaygın Hatalar ve Çözümleri

    ═══════════════════════════════════════════════════════════════
    1. HIZLI BAŞLANGIÇ
    ═══════════════════════════════════════════════════════════════

    ADIM 1: Örnek Dosyaları İndirin
       → Sayfadaki "📥 Örnek CSV Dosyalarını İndir" butonuna tıklayın
       → İndirilen ZIP dosyasını açın
       → İçindeki CSV dosyalarını Excel ile açın ve inceleyin

    ADIM 2: Kendi Verilerinizi Hazırlayın
       → Excel'de örnek dosyaları açın
       → Kendi verilerinizi AYNI FORMATTA girin
       → Kolon adlarını DEĞİŞTİRMEYİN!
       → "Farklı Kaydet" → "CSV UTF-8 (Virgülle ayrılmış)" seçin

    ADIM 3: Dosyaları Yükleyin
       → "CSV dosyalarını seçin" alanına tıklayın
       → Hazırladığınız CSV dosyalarını seçin (birden fazla seçebilirsiniz)
       → "🚀 Tüm Dosyaları Yükle" butonuna basın
       → Durum tablosundan başarılı yüklemeyi kontrol edin

    ═══════════════════════════════════════════════════════════════
    2. DOSYA FORMATI GEREKSİNİMLERİ
    ═══════════════════════════════════════════════════════════════

    ✅ DOĞRU FORMAT:
       • Dosya türü: CSV (Comma Separated Values)
       • Kodlama: UTF-8 (Türkçe karakterler için ZORUNLU)
       • Ayraç: Noktalı virgül (;) veya virgül (,)
       • İlk satır: Kolon başlıkları (küçük harf, alt çizgi ile)
       • Örnek: urun_kod, magaza_kod, stok

    ❌ YANLIŞ FORMAT:
       • Excel dosyaları (.xlsx, .xls) → Mutlaka CSV'ye çevirin!
       • PDF, Word dosyaları → CSV'ye çevirin!
       • Türkçe karakterli kolon adları → İngilizce kullanın
       • Boşluklu kolon adları → Alt çizgi (_) kullanın

    Excel'de CSV Kaydetme:
       1. "Dosya" → "Farklı Kaydet"
       2. "Dosya türü" → "CSV UTF-8 (Virgülle ayrılmış) (*.csv)"
       3. Kaydet

    ═══════════════════════════════════════════════════════════════
    3. ZORUNLU DOSYALAR VE AÇIKLAMALARI
    ═══════════════════════════════════════════════════════════════

    Bu 5 dosya MUTLAKA yüklenmelidir:

    ┌─────────────────────────────────────────────────────────────┐
    │ 📦 ÜRÜN MASTER (urun_master.csv)                            │
    ├─────────────────────────────────────────────────────────────┤
    │ • Tüm ürünlerin temel bilgileri                             │
    │ • Neden gerekli: Ürün kodlarını tanımak ve kategorize etmek│
    │ • Minimum satır sayısı: En az 1 ürün                        │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ 🏪 MAĞAZA MASTER (magaza_master.csv)                        │
    ├─────────────────────────────────────────────────────────────┤
    │ • Tüm mağazaların temel bilgileri                           │
    │ • Neden gerekli: Mağaza kodlarını tanımak ve lokasyon bilgi│
    │ • Minimum satır sayısı: En az 1 mağaza                      │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ 📦 DEPO STOK (depo_stok.csv)                                │
    ├─────────────────────────────────────────────────────────────┤
    │ • Depolardaki mevcut stok miktarları                        │
    │ • Neden gerekli: Sevkiyat için uygun stok kontrolü         │
    │ • Format: Her depo-ürün kombinasyonu için stok miktarı     │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ 📊 ANLIK STOK/SATIŞ (anlik_stok_satis.csv)                 │
    ├─────────────────────────────────────────────────────────────┤
    │ • Mağazalardaki güncel stok ve satış bilgileri              │
    │ • Neden gerekli: İhtiyaç hesaplamak için temel veri        │
    │ • Format: Her mağaza-ürün kombinasyonu için bilgiler       │
    │ • ÖNEMLİ: Büyük dosyalarda parçalı yükleme kullanın!       │
    └─────────────────────────────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────┐
    │ 🎯 KPI (kpi.csv)                                            │
    ├─────────────────────────────────────────────────────────────┤
    │ • Hedef ve limitler (min/max değerler)                     │
    │ • Neden gerekli: Minimum/maksimum stok hedefleri için      │
    │ • Format: Mal grubu bazında hedef değerler                 │
    └─────────────────────────────────────────────────────────────┘

    OPSİYONEL DOSYALAR (İsteğe Bağlı):
       • 🚫 Yasak: Bazı ürünlerin bazı mağazalara gitmemesi
       • 📈 Haftalık Trend: Geçmiş haftalık satış verileri
       • 🚫 PO Yasak: Alım siparişi yasak ürünler
       • 🎯 PO Detay KPI: Alım siparişi detaylı hedefler

    ═══════════════════════════════════════════════════════════════
    Son Güncelleme: 2025
    Versiyon: 1.0
    """

    # İndirme butonları
    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            label="📥 Kılavuzu İndir (.txt)",
            data=kilavuz_metni,
            file_name="veri_yukleme_kilavuzu.txt",
            mime="text/plain",
            use_container_width=True,
            help="Metin formatında indir - Not Defteri ile açılabilir"
        )

    with col2:
        st.download_button(
            label="📥 Kılavuzu İndir (.md)",
            data=kilavuz_metni,
            file_name="veri_yukleme_kilavuzu.md",
            mime="text/markdown",
            use_container_width=True,
            help="Markdown formatında indir - GitHub'da güzel görünür"
        )

    with col3:
        # HTML formatı için
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Veri Yükleme Kılavuzu</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                h1 {{ color: #2c3e50; border-bottom: 3px solid #3498db; }}
                h2 {{ color: #34495e; margin-top: 30px; }}
                pre {{ background: #f4f4f4; padding: 15px; border-left: 4px solid #3498db; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #3498db; color: white; }}
                .success {{ color: #27ae60; }}
                .error {{ color: #e74c3c; }}
                .warning {{ color: #f39c12; }}
            </style>
        </head>
        <body>
            <pre>{kilavuz_metni}</pre>
        </body>
        </html>
        """
    
        st.download_button(
            label="📥 Kılavuzu İndir (.html)",
            data=html_content,
            file_name="veri_yukleme_kilavuzu.html",
            mime="text/html",
            use_container_width=True,
            help="HTML formatında indir - Tarayıcıda açılabilir"
        )

    st.info("💡 **İpucu:** Kılavuzu indirip kaydedin, ihtiyaç duyduğunuzda açın!")

    st.markdown("---")

    # ============================================
    # ÖZEL: ANLIK STOK/SATIŞ PARÇALI YÜKLEME
    # ============================================
    st.subheader("📊 Anlık Stok/Satış - Parçalı Yükleme")
    st.info("💡 **İpucu:** Büyük dosyaları parça parça yükleyebilirsiniz. Sistem otomatik birleştirecek.")

    anlik_parts = st.file_uploader(
        "Anlık Stok/Satış CSV parçalarını seçin (birden fazla)",
        type=['csv'],
        accept_multiple_files=True,
        key="anlik_parts_upload"
    )

    if anlik_parts:
        st.write(f"**{len(anlik_parts)} parça seçildi**")
    
        if st.button("🔗 Parçaları Birleştir ve Yükle", type="primary", use_container_width=True):
            try:
                combined_df = None
                total_rows = 0
                part_info = []
            
                for idx, part_file in enumerate(anlik_parts, 1):
                    # CSV oku
                    df_part, used_sep = read_csv_safe(part_file)
                
                    # Kolon kontrolü
                    expected_cols = set(data_definitions['anlik_stok_satis']['columns'])
                    if not expected_cols.issubset(set(df_part.columns)):
                        st.error(f"❌ {part_file.name}: Eksik kolonlar var!")
                        continue
                
                    # Sadece gerekli kolonları al
                    df_part = df_part[data_definitions['anlik_stok_satis']['columns']].copy()
                
                    # String kolonları temizle
                    string_cols = df_part.select_dtypes(include=['object']).columns
                    for col in string_cols:
                        df_part[col] = df_part[col].str.strip()
                
                    # 🆕 Sayısal kolonları zorla
                    numeric_cols = ['stok', 'yol', 'satis', 'ciro', 'smm']
                    for col in numeric_cols:
                        if col in df_part.columns:
                            df_part[col] = pd.to_numeric(df_part[col], errors='coerce').fillna(0)
                
                    # Birleştir
                    if combined_df is None:
                        combined_df = df_part
                    else:
                        combined_df = pd.concat([combined_df, df_part], ignore_index=True)
                
                    part_info.append(f"✅ Parça {idx}: {len(df_part):,} satır")
                    total_rows += len(df_part)
            
                if combined_df is not None:
                    # Duplicate kontrolü (opsiyonel)
                    before_dedup = len(combined_df)
                    combined_df = combined_df.drop_duplicates(subset=['magaza_kod', 'urun_kod'], keep='last')
                    after_dedup = len(combined_df)
                
                    # Kaydet
                    st.session_state.anlik_stok_satis = combined_df
                
                    # Sonuçları göster
                    st.success(f"🎉 **Başarıyla birleştirildi!**")
                    for info in part_info:
                        st.write(info)
                
                    st.info(f"""
                    **Özet:**
                    - Toplam yüklenen: {total_rows:,} satır
                    - Duplicate temizlendi: {before_dedup - after_dedup:,} satır
                    - Final: {after_dedup:,} satır
                    """)
                
                    time.sleep(1)
                    st.rerun()
        
            except Exception as e:
                st.error(f"❌ Birleştirme hatası: {str(e)}")

    st.markdown("---")

    # ============================================
    # ÇOKLU DOSYA YÜKLEME + ÖRNEK İNDİRME
    # ============================================
    st.subheader("📤 Çoklu Dosya Yükleme")

    col1, col2 = st.columns([2, 1])

    with col1:
        uploaded_files = st.file_uploader(
            "CSV dosyalarını seçin (birden fazla seçebilirsiniz)",
            type=['csv'],
            accept_multiple_files=True,
            key="multi_upload"
        )

    with col2:
        separator_option = st.selectbox(
            "CSV Ayracı:",
            options=['Otomatik Algıla', 'Noktalı Virgül (;)', 'Virgül (,)', 'Tab (\\t)'],
            help="CSV dosyanızdaki alan ayracını seçin"
        )
    
        separator_map = {
            'Otomatik Algıla': 'auto',
            'Noktalı Virgül (;)': ';',
            'Virgül (,)': ',',
            'Tab (\\t)': '\t'
        }
        selected_separator = separator_map[separator_option]

    # Örnek İndirme Butonu - EXPANDER YOK, DİREKT BUTON
    col1, col2 = st.columns(2)

    with col1:
        if uploaded_files:
            if st.button("🚀 Tüm Dosyaları Yükle", type="primary", use_container_width=True):
                upload_results = []
            
                for uploaded_file in uploaded_files:
                    filename = uploaded_file.name.lower()
                
                    matched_key = None
                    for key, definition in data_definitions.items():
                        if key in filename or definition['name'].lower().replace(' ', '_') in filename:
                            matched_key = key
                            break
                
                    if not matched_key:
                        upload_results.append({
                            'Dosya': uploaded_file.name,
                            'Durum': '❌ Eşleştirilemedi'
                        })
                        continue
                
                    definition = data_definitions[matched_key]
                
                    try:
                        if selected_separator == 'auto':
                            df, used_sep = read_csv_safe(uploaded_file)
                        else:
                            df = pd.read_csv(uploaded_file, sep=selected_separator, encoding='utf-8-sig', 
                                           quoting=1, on_bad_lines='warn')
                    
                        existing_cols = set(df.columns)
                        required_cols = set(definition['columns'])
                        missing_cols = required_cols - existing_cols
                    
                        if missing_cols:
                            upload_results.append({
                                'Dosya': uploaded_file.name,
                                'Durum': f"❌ Eksik kolon: {', '.join(list(missing_cols)[:3])}"
                            })
                        else:
                            df_clean = df[definition['columns']].copy()
                        
                            # String kolonları temizle
                            string_columns = df_clean.select_dtypes(include=['object']).columns
                            for col in string_columns:
                                df_clean[col] = df_clean[col].str.strip() if df_clean[col].dtype == 'object' else df_clean[col]
                        
                            # 🆕 SAYISAL KOLONLARI ZORLA (Özel dosyalar için)
                            if matched_key == 'anlik_stok_satis':
                                # Anlık Stok/Satış için sayısal kolonları zorla
                                numeric_cols = ['stok', 'yol', 'satis', 'ciro', 'smm']
                                for col in numeric_cols:
                                    if col in df_clean.columns:
                                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                        
                            elif matched_key == 'depo_stok':
                                # Depo Stok için sayısal kolonları zorla
                                if 'stok' in df_clean.columns:
                                    df_clean['stok'] = pd.to_numeric(df_clean['stok'], errors='coerce').fillna(0)
                        
                            elif matched_key == 'kpi':
                                # KPI için sayısal kolonları zorla
                                numeric_cols = ['min_deger', 'max_deger', 'forward_cover']
                                for col in numeric_cols:
                                    if col in df_clean.columns:
                                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                        
                            st.session_state[definition['state_key']] = df_clean
                            upload_results.append({
                                'Dosya': uploaded_file.name,
                                'Durum': f"✅ {len(df_clean):,} satır"
                            })
                
                    except Exception as e:
                        upload_results.append({
                            'Dosya': uploaded_file.name,
                            'Durum': f"❌ Hata: {str(e)[:30]}"
                        })
            
                st.markdown("---")
                for result in upload_results:
                    if '✅' in result['Durum']:
                        st.success(f"{result['Dosya']}: {result['Durum']}")
                    else:
                        st.error(f"{result['Dosya']}: {result['Durum']}")
            
                time.sleep(1)
                st.rerun()

    with col2:
        # Örnek CSV indirme butonu
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for filename, file_info in example_csvs.items():
                csv_data = write_csv_safe(file_info['data'])
                zip_file.writestr(filename, csv_data)
    
        st.download_button(
            label="📥 Örnek CSV Dosyalarını İndir",
            data=zip_buffer.getvalue(),
            file_name="ornek_csv_dosyalari.zip",
            mime="application/zip",
            type="secondary",
            use_container_width=True
        )

    st.markdown("---")


    # ============================================
    # VERİ YÜKLEME DURUMU TABLOSU - DÜZELTİLMİŞ
    # ============================================
    st.subheader("📊 Veri Yükleme Durumu")

    status_data = []
    for key, definition in data_definitions.items():
        data = st.session_state.get(definition['state_key'])
    
        if data is not None and len(data) > 0:
            status = '✅ Başarılı'
            kolon_sayisi = str(len(data.columns))  # 🆕 String'e çevir (Arrow hatası için)
            boyut_mb = f"{data.memory_usage(deep=True).sum() / 1024**2:.2f}"
        else:
            status = '❌ Yüklenmedi'
            kolon_sayisi = '-'
            boyut_mb = '-'
    
        status_data.append({
            'CSV Adı': f"{definition['icon']} {definition['name']}",
            'Zorunlu': 'Evet ⚠️' if definition['required'] else 'Hayır ℹ️',
            'Kolon Sayısı': kolon_sayisi,
            'Durum': status,
            'Boyut (MB)': boyut_mb
        })

    status_df = pd.DataFrame(status_data)

    st.dataframe(
        status_df,
        use_container_width=True,
        hide_index=True,
        height=350
    )

    # Özet metrikler
    col1, col2, col3 = st.columns(3)
    with col1:
        zorunlu_count = sum(1 for d in data_definitions.values() if d['required'])
        zorunlu_loaded = sum(1 for k, d in data_definitions.items() 
                            if d['required'] and st.session_state.get(d['state_key']) is not None)
        st.metric("Zorunlu Dosyalar", f"{zorunlu_loaded}/{zorunlu_count}")

    with col2:
        opsiyonel_count = sum(1 for d in data_definitions.values() if not d['required'])
        opsiyonel_loaded = sum(1 for k, d in data_definitions.items() 
                              if not d['required'] and st.session_state.get(d['state_key']) is not None)
        st.metric("Opsiyonel Dosyalar", f"{opsiyonel_loaded}/{opsiyonel_count}")

    with col3:
        all_ready = zorunlu_loaded == zorunlu_count
        st.metric("Sistem Durumu", "Hazır ✅" if all_ready else "Eksik ⚠️")

    st.markdown("---")




    # TEK DOSYA DETAYI
    st.subheader("🔍 Detaylı Veri İncelemesi")

    selected_data = st.selectbox(
        "İncelemek istediğiniz veriyi seçin:",
        options=[k for k in data_definitions.keys() if st.session_state.get(data_definitions[k]['state_key']) is not None],
        format_func=lambda x: f"{data_definitions[x]['icon']} {data_definitions[x]['name']}",
        key="detail_select"
    ) if any(st.session_state.get(data_definitions[k]['state_key']) is not None for k in data_definitions.keys()) else None

    if selected_data:
        current_def = data_definitions[selected_data]
        data = st.session_state[current_def['state_key']]
    
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Satır", f"{len(data):,}")
        with col2:
            st.metric("Kolon", len(data.columns))
        with col3:
            st.metric("Bellek", f"{data.memory_usage(deep=True).sum() / 1024**2:.2f} MB")

    st.markdown("---")

    # CSV İNDİR
    st.subheader("📤 Veri Dosyası İndir")

    if any(st.session_state.get(data_definitions[k]['state_key']) is not None for k in data_definitions.keys()):
        export_data = st.selectbox(
            "İndirmek istediğiniz veriyi seçin:",
            options=[k for k in data_definitions.keys() if st.session_state.get(data_definitions[k]['state_key']) is not None],
            format_func=lambda x: f"{data_definitions[x]['icon']} {data_definitions[x]['name']}",
            key="export_select"
        )
    
        if export_data:
            export_def = data_definitions[export_data]
            export_df = st.session_state[export_def['state_key']]
        
            col1, col2, col3 = st.columns([1, 1, 1])
        
            with col1:
                csv_data = write_csv_safe(export_df)
                st.download_button(
                    label=f"📥 CSV İndir (;)",
                    data=csv_data,
                    file_name=f"{export_def['name'].lower().replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
            with col2:
                csv_data_comma = export_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label=f"📥 CSV İndir (,)",
                    data=csv_data_comma,
                    file_name=f"{export_def['name'].lower().replace(' ', '_')}_comma.csv",
                    mime="text/csv",
                    use_container_width=True
                )
        
            with col3:
                if st.button("🗑️ Bu Veriyi Sil", use_container_width=True):
                    st.session_state[export_def['state_key']] = None
                    st.success(f"✅ {export_def['name']} silindi!")
                    time.sleep(0.5)
                    st.rerun()
    else:
        st.info("İndirilebilecek veri yok")

    st.markdown("---")

    # Başarı mesajı ve yönlendirme
    required_loaded_final = sum(1 for k, d in data_definitions.items() 
                               if d['required'] and st.session_state.get(d['state_key']) is not None)
    required_count_final = sum(1 for d in data_definitions.values() if d['required'])

    if required_loaded_final == required_count_final and required_count_final > 0:
        st.success("✅ **Tüm zorunlu veriler yüklendi!** Modüllere geçebilirsiniz.")
    
        col1, col2 = st.columns(2)
        with col1:
            if st.button("➡️ Sevkiyat Modülüne Git", use_container_width=True):
                st.switch_page("pages/2_Sevkiyat.py")
        with col2:
            if st.button("➡️ Alım Sipariş Modülüne Git", use_container_width=True):
                st.switch_page("pages/4_PO.py")


elif menu == "🏠 Ana Sayfa":
    st.title("🌟 Sevkiyat Planlama Sistemi")
    st.markdown("---")
    
    st.info("""
    **📋 Veri Yükleme:** Sol menüden "Veri Yükleme" sayfasına gidin.
    **💵 Alım Sipariş:** Hesaplama sonrası "Alım Sipariş (PO)" sayfasına gidin.
    """)
    
    st.info("""
    💡 **Hızlı Gezinme:**
    - 📂 **Veri Yükleme:** Ana menüden "0_Veri_Yukleme" sayfasına gidin
    - 🫧 **Segmentasyon:** Sol menüden seçin
    - 💵 **PO İşlemleri:** Sol menüden "PO Hesaplama" seçin
    """)
    
    st.markdown("---")
    
# ============================================
# 🫧 SEGMENTASYON AYARLARI - DÜZELTİLMİŞ
# ============================================
elif menu == "🫧 Segmentasyon":
    st.title("🫧 Segmentasyon")
    st.markdown("---")
    
    st.info("**Stok/Satış oranına göre** ürün ve mağazaları gruplandırma (Mağaza Stok / Toplam Satış)")
    
    if st.session_state.anlik_stok_satis is None:
        st.warning("⚠️ Önce 'Veri Yükleme' bölümünden anlık stok/satış verisini yükleyin!")
        st.stop()
    
    # Ürün bazında toplam stok/satış hesapla
    data = st.session_state.anlik_stok_satis.copy()
    
    # Ürün bazında gruplama
    urun_aggregated = data.groupby('urun_kod').agg({
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    urun_aggregated['stok_satis_orani'] = urun_aggregated['stok'] / urun_aggregated['satis'].replace(0, 1)
    
    if st.session_state.urun_master is not None:
        urun_master = st.session_state.urun_master[['urun_kod', 'marka_kod']].copy()
        urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
        urun_aggregated['urun_kod'] = urun_aggregated['urun_kod'].astype(str)
        urun_aggregated = urun_aggregated.merge(urun_master, on='urun_kod', how='left')
    else:
        urun_aggregated['marka_kod'] = 'Bilinmiyor'
    
    # Mağaza bazında gruplama
    magaza_aggregated = data.groupby('magaza_kod').agg({
        'stok': 'sum',
        'yol': 'sum',
        'satis': 'sum',
        'ciro': 'sum'
    }).reset_index()
    magaza_aggregated['stok_satis_orani'] = magaza_aggregated['stok'] / magaza_aggregated['satis'].replace(0, 1)
    
    st.markdown("---")
    
    # Ürün segmentasyonu
    st.subheader("🏷️ Ürün Segmentasyonu")
    
    use_default_product = st.checkbox("Varsayılan aralıkları kullan (Ürün)", value=True, key="seg_use_default_product")
    
    if use_default_product:
        st.write("**Varsayılan Aralıklar**: 0-4, 5-8, 9-12, 12-15, 15-20, 20+")
        product_ranges = [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    else:
        st.write("Özel aralıklar tanımlayın:")
        num_ranges = st.number_input("Kaç aralık?", min_value=2, max_value=10, value=6, key="seg_num_ranges_product")
        
        product_ranges = []
        for i in range(num_ranges):
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"Aralık {i+1} - Min", value=i*5, key=f"prod_min_{i}")
            with col2:
                max_val = st.number_input(f"Aralık {i+1} - Max", value=(i+1)*5 if i < num_ranges-1 else 999, key=f"prod_max_{i}")
            product_ranges.append((min_val, max_val))
    
    # Ürün segment labels
    product_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
    
    # Segmentasyon uygula
    temp_prod = urun_aggregated.copy()
    temp_prod['segment'] = pd.cut(
        temp_prod['stok_satis_orani'], 
        bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
        labels=product_labels,
        include_lowest=True
    )
    
    st.write("**Ürün Dağılımı:**")
    segment_dist = temp_prod['segment'].value_counts().sort_index()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(segment_dist, width='content', height=200)
    with col2:
        st.bar_chart(segment_dist)
    
    st.markdown("---")
    
    # Mağaza segmentasyonu
    st.subheader("🏪 Mağaza Segmentasyonu")
    
    use_default_store = st.checkbox("Varsayılan aralıkları kullan (Mağaza)", value=True, key="seg_use_default_store")
    
    if use_default_store:
        st.write("**Varsayılan Aralıklar**: 0-4, 5-8, 9-12, 12-15, 15-20, 20+")
        store_ranges = [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    else:
        st.write("Özel aralıklar tanımlayın:")
        num_ranges_store = st.number_input("Kaç aralık?", min_value=2, max_value=10, value=6, key="store_ranges")
        
        store_ranges = []
        for i in range(num_ranges_store):
            col1, col2 = st.columns(2)
            with col1:
                min_val = st.number_input(f"Aralık {i+1} - Min", value=i*5, key=f"store_min_{i}")
            with col2:
                max_val = st.number_input(f"Aralık {i+1} - Max", value=(i+1)*5 if i < num_ranges_store-1 else 999, key=f"store_max_{i}")
            store_ranges.append((min_val, max_val))
    
    # Mağaza segment labels
    store_labels = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
    
    # Segmentasyon uygula
    temp_store = magaza_aggregated.copy()
    temp_store['segment'] = pd.cut(
        temp_store['stok_satis_orani'], 
        bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
        labels=store_labels,
        include_lowest=True
    )
    
    st.write("**Mağaza Dağılımı:**")
    segment_dist_store = temp_store['segment'].value_counts().sort_index()
    col1, col2 = st.columns([1, 2])
    with col1:
        st.dataframe(segment_dist_store, width='content', height=200)
    with col2:
        st.bar_chart(segment_dist_store)
    
    st.markdown("---")
    
    # Kaydet butonu
    col1, col2 = st.columns([1, 3])
    with col1:
        if st.button("💾 Segmentasyonu Kaydet", type="primary"):
            st.session_state.segmentation_params = {
                'product_ranges': product_ranges,
                'store_ranges': store_ranges
            }
            st.session_state.prod_segments = product_labels
            st.session_state.store_segments = store_labels
            st.session_state.urun_segment_map = temp_prod.set_index('urun_kod')['segment'].to_dict()
            st.session_state.magaza_segment_map = temp_store.set_index('magaza_kod')['segment'].to_dict()
            st.success("✅ Ayarlar kaydedildi!")
    with col2:
        st.info("ℹ️ Kaydetmeseniz de default değerler kullanılacaktır.")
            
    st.markdown("---")
    
    # ============================================
    # DETAY VERİLERİNİ HAZIRLA (YENİ EKLENEN KISIM)
    # ============================================
    # Ürün detayı
    urun_detail = temp_prod.copy()
    if 'marka_kod' in urun_detail.columns:
        urun_detail = urun_detail[['urun_kod', 'marka_kod', 'stok', 'satis', 'stok_satis_orani', 'segment']]
        urun_detail.columns = ['Ürün Kodu', 'Marka Kodu', 'Toplam Stok', 'Toplam Satış', 'Stok/Satış Oranı', 'Segment']
    else:
        urun_detail = urun_detail[['urun_kod', 'stok', 'satis', 'stok_satis_orani', 'segment']]
        urun_detail.columns = ['Ürün Kodu', 'Toplam Stok', 'Toplam Satış', 'Stok/Satış Oranı', 'Segment']
    
    # Mağaza detayı
    magaza_detail = temp_store.copy()
    magaza_detail = magaza_detail[['magaza_kod', 'stok', 'satis', 'stok_satis_orani', 'segment']]
    magaza_detail.columns = ['Mağaza Kodu', 'Toplam Stok', 'Toplam Satış', 'Stok/Satış Oranı', 'Segment']
    
    # ============================================
    # HER İKİSİNİ BİRLİKTE İNDİR
    # ============================================
    st.subheader("📥 Tüm Segmentasyon Verilerini İndir")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Excel formatında (iki sheet)
        if st.button("📊 Excel İndir (Ürün + Mağaza)", key="seg_export_excel"):
            try:
                from io import BytesIO
                
                # Excel writer oluştur
                output = BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    urun_detail.to_excel(writer, sheet_name='Ürün Segmentasyon', index=False)
                    magaza_detail.to_excel(writer, sheet_name='Mağaza Segmentasyon', index=False)
                
                output.seek(0)
                
                st.download_button(
                    label="⬇️ Excel Dosyasını İndir",
                    data=output.getvalue(),
                    file_name="segmentasyon_tam_detay.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
            except ImportError:
                st.error("❌ Excel export için 'openpyxl' kütüphanesi gerekli. Lütfen yükleyin: pip install openpyxl")
    
    with col2:
        # ZIP formatında (iki CSV)
        if st.button("📦 ZIP İndir (2 CSV)", key="seg_export_zip"):
            import zipfile
            from io import BytesIO
            
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Ürün CSV
                urun_csv = urun_detail.to_csv(index=False, encoding='utf-8-sig')
                zip_file.writestr('urun_segmentasyon.csv', urun_csv)
                
                # Mağaza CSV
                magaza_csv = magaza_detail.to_csv(index=False, encoding='utf-8-sig')
                zip_file.writestr('magaza_segmentasyon.csv', magaza_csv)
            
            zip_buffer.seek(0)
            
            st.download_button(
                label="⬇️ ZIP Dosyasını İndir",
                data=zip_buffer.getvalue(),
                file_name="segmentasyon_detay.zip",
                mime="application/zip"
            )

# ============================================
# 🎲 HEDEF MATRİS 
# ============================================

# ============================================
# 🎲 HEDEF MATRİS - DÜZENLENEBİLİR VERSİYON (ADIM 2)
# ============================================
elif menu == "🎲 Hedef Matris":
    st.title("🎲 Hedef Matris Parametreleri")
    st.markdown("---")
    
    # Segmentleri kontrol et
    if (st.session_state.prod_segments is None or 
        st.session_state.store_segments is None):
        st.warning("⚠️ Önce 'Segmentasyon' bölümüne gidin ve segmentasyonu kaydedin!")
        st.stop()
    
    prod_segments = st.session_state.prod_segments  # Sütunlar
    store_segments = st.session_state.store_segments  # Satırlar
    
    st.info(f"📏 Matris Boyutu: {len(store_segments)} Mağaza Segment × {len(prod_segments)} Ürün Segment")
    st.success("✨ **Artık hücrelere tıklayarak değerleri düzenleyebilirsiniz!**")
    st.markdown("---")
    
    # ============================================
    # 1️⃣ ŞİŞME ORANI MATRİSİ
    # ============================================
    st.subheader("1️⃣ Şişme Oranı Matrisi")
    st.caption("📊 Default: 0.5 | Düzenlemek için hücreye çift tıklayın")
    
    # Matris oluştur veya yükle
    if st.session_state.sisme_orani is not None:
        sisme_df = st.session_state.sisme_orani.copy()
    else:
        sisme_df = pd.DataFrame(0.5, index=store_segments, columns=prod_segments)
    
    # Index'i kolon olarak ekle (data_editor için gerekli)
    sisme_display = sisme_df.reset_index()
    sisme_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    # Düzenlenebilir tablo
    edited_sisme = st.data_editor(
        sisme_display,
        key="editor_sisme_v1",
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]  # İlk sütun düzenlenemez
    )
    
    st.markdown("---")
    
    # ============================================
    # 2️⃣ GENLEŞTİRME ORANI MATRİSİ
    # ============================================
    st.subheader("2️⃣ Genleştirme Oranı Matrisi")
    st.caption("📊 Default: 1.0 | Düzenlemek için hücreye çift tıklayın")
    
    if st.session_state.genlestirme_orani is not None:
        genles_df = st.session_state.genlestirme_orani.copy()
    else:
        genles_df = pd.DataFrame(1.0, index=store_segments, columns=prod_segments)
    
    genles_display = genles_df.reset_index()
    genles_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    edited_genles = st.data_editor(
        genles_display,
        key="editor_genles_v1",
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]
    )
    
    st.markdown("---")
    
    # ============================================
    # 3️⃣ MIN ORAN MATRİSİ
    # ============================================
    st.subheader("3️⃣ Min Oran Matrisi")
    st.caption("📊 Default: 1.0 | Düzenlemek için hücreye çift tıklayın")
    
    if st.session_state.min_oran is not None:
        min_df = st.session_state.min_oran.copy()
    else:
        min_df = pd.DataFrame(1.0, index=store_segments, columns=prod_segments)
    
    min_display = min_df.reset_index()
    min_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    edited_min = st.data_editor(
        min_display,
        key="editor_min_v1",
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]
    )
    
    st.markdown("---")
    
    # ============================================
    # 4️⃣ INITIAL MATRİS
    # ============================================
    st.subheader("4️⃣ Initial Matris")
    st.caption("📊 Default: 1.0 | Düzenlemek için hücreye çift tıklayın")
    
    if st.session_state.initial_matris is not None:
        initial_df = st.session_state.initial_matris.copy()
    else:
        initial_df = pd.DataFrame(1.0, index=store_segments, columns=prod_segments)
    
    initial_display = initial_df.reset_index()
    initial_display.rename(columns={'index': 'Mağaza↓ / Ürün→'}, inplace=True)
    
    edited_initial = st.data_editor(
        initial_display,
        key="editor_initial_v1",
        hide_index=True,
        use_container_width=True,
        num_rows="fixed",
        disabled=["Mağaza↓ / Ürün→"]
    )
    
    st.markdown("---")
    
    # ============================================
    # KAYDET BUTONU
    # ============================================
    st.subheader("💾 Değişiklikleri Kaydet")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("💾 KAYDET", type="primary", use_container_width=True, key="save_matrices_btn"):
            try:
                # Düzenlenmiş dataframe'leri index'e çevir ve kaydet
                st.session_state.sisme_orani = edited_sisme.set_index('Mağaza↓ / Ürün→')
                st.session_state.genlestirme_orani = edited_genles.set_index('Mağaza↓ / Ürün→')
                st.session_state.min_oran = edited_min.set_index('Mağaza↓ / Ürün→')
                st.session_state.initial_matris = edited_initial.set_index('Mağaza↓ / Ürün→')
                
                st.success("✅ Tüm matrisler başarıyla kaydedildi!")
                st.balloons()
                
                # Doğrulama bilgisi
                st.info(f"""
                **Kaydedilen Boyutlar:**
                - Şişme Oranı: {st.session_state.sisme_orani.shape[0]} × {st.session_state.sisme_orani.shape[1]}
                - Genleştirme: {st.session_state.genlestirme_orani.shape[0]} × {st.session_state.genlestirme_orani.shape[1]}
                - Min Oran: {st.session_state.min_oran.shape[0]} × {st.session_state.min_oran.shape[1]}
                - Initial: {st.session_state.initial_matris.shape[0]} × {st.session_state.initial_matris.shape[1]}
                """)
                
            except Exception as e:
                st.error(f"❌ Kaydetme hatası: {str(e)}")
    
    with col2:
        st.info("💡 **İpucu:** Değerleri değiştirdikten sonra 'Kaydet' butonuna basın. Kaydedilmeyen değişiklikler kaybolur!")
    
    st.markdown("---")
    
    # ============================================
    # İNDİRME SEÇENEKLERİ (BONUS)
    # ============================================
    with st.expander("📥 Matrisleri Excel/CSV Olarak İndir"):
        st.write("**Kaydedilmiş matrisleri dışa aktarın:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Excel formatında (tüm matrisler tek dosyada)
            if st.button("📊 Excel İndir (Tüm Matrisler)", key="download_excel"):
                try:
                    from io import BytesIO
                    
                    output = BytesIO()
                    with pd.ExcelWriter(output, engine='openpyxl') as writer:
                        if st.session_state.sisme_orani is not None:
                            st.session_state.sisme_orani.to_excel(writer, sheet_name='Şişme Oranı')
                        if st.session_state.genlestirme_orani is not None:
                            st.session_state.genlestirme_orani.to_excel(writer, sheet_name='Genleştirme')
                        if st.session_state.min_oran is not None:
                            st.session_state.min_oran.to_excel(writer, sheet_name='Min Oran')
                        if st.session_state.initial_matris is not None:
                            st.session_state.initial_matris.to_excel(writer, sheet_name='Initial')
                    
                    output.seek(0)
                    
                    st.download_button(
                        label="⬇️ Excel Dosyasını İndir",
                        data=output.getvalue(),
                        file_name="hedef_matrisler.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                except Exception as e:
                    st.error(f"Excel indirme hatası: {e}")
        
        with col2:
            # CSV formatında (ZIP içinde 4 dosya)
            if st.button("📦 CSV İndir (ZIP)", key="download_csv"):
                try:
                    import zipfile
                    from io import BytesIO
                    
                    zip_buffer = BytesIO()
                    
                    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                        if st.session_state.sisme_orani is not None:
                            csv_data = st.session_state.sisme_orani.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('sisme_orani.csv', csv_data)
                        
                        if st.session_state.genlestirme_orani is not None:
                            csv_data = st.session_state.genlestirme_orani.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('genlestirme_orani.csv', csv_data)
                        
                        if st.session_state.min_oran is not None:
                            csv_data = st.session_state.min_oran.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('min_oran.csv', csv_data)
                        
                        if st.session_state.initial_matris is not None:
                            csv_data = st.session_state.initial_matris.to_csv(encoding='utf-8-sig')
                            zip_file.writestr('initial_matris.csv', csv_data)
                    
                    zip_buffer.seek(0)
                    
                    st.download_button(
                        label="⬇️ ZIP Dosyasını İndir",
                        data=zip_buffer.getvalue(),
                        file_name="hedef_matrisler.zip",
                        mime="application/zip"
                    )
                except Exception as e:
                    st.error(f"CSV indirme hatası: {e}")



# ============================================
# 🔢 SIRALAMA - İHTİYAÇ ÖNCELİKLENDİRME
# ============================================
elif menu == "🔢 Sıralama":
    st.title("🔢 Sıralama Öncelikleri")
    st.markdown("---")
    
    # Session state başlatma
    if 'oncelik_siralama' not in st.session_state:
        st.session_state.oncelik_siralama = None
    
    # Segment kontrolü
    if st.session_state.prod_segments is None:
        st.warning("⚠️ Önce 'Segmentasyon' sayfasına gidin ve segmentasyonu kaydedin!")
        st.stop()
    
    prod_segments = st.session_state.prod_segments
    
    st.info(f"📊 Toplam {len(prod_segments)} ürün segmenti için öncelik sıralaması yapacaksınız")
    st.markdown("---")
    
    # Açıklama
    st.markdown("""
    ### 📋 Nasıl Çalışır?
    
    Her **ürün segmenti** için ihtiyaç türlerinin öncelik sırasını belirleyin:
    
    - **RPT (Replenishment):** Normal stok tamamlama
    - **Initial:** Yeni ürün ilk dağıtımı  
    - **Min:** Minimum stok garantisi
    
    **Örnek:**
    - Segment **0-4** için: `1. RPT → 2. Initial → 3. Min`
    - Segment **5-8** için: `1. Initial → 2. RPT → 3. Min`
    
    **Depo stok dağıtımı** bu sıraya göre yapılacak.
    """)
    
    st.markdown("---")
    
    # Mevcut sıralamayı yükle veya default oluştur
    if st.session_state.oncelik_siralama is not None:
        siralama_dict = st.session_state.oncelik_siralama
        st.success("✅ Kaydedilmiş sıralama yüklendi")
    else:
        # Default: RPT → Initial → Min
        siralama_dict = {segment: ['RPT', 'Initial', 'Min'] for segment in prod_segments}
        st.info("ℹ️ Default sıralama gösteriliyor (RPT → Initial → Min)")
    
    st.markdown("---")
    
    # Sıralama tablosu
    st.subheader("🎯 Öncelik Sıralaması")
    
    # Düzenlenebilir tablo oluştur
    siralama_data = []
    for segment in prod_segments:
        current_order = siralama_dict.get(segment, ['RPT', 'Initial', 'Min'])
        siralama_data.append({
            'Ürün Segmenti': segment,
            '1. Öncelik': current_order[0],
            '2. Öncelik': current_order[1],
            '3. Öncelik': current_order[2]
        })
    
    siralama_df = pd.DataFrame(siralama_data)
    
    # Data editor ile düzenleme
    st.write("**Sıralamayı Düzenleyin:**")
    st.caption("Her segment için öncelik sırasını değiştirin (dropdown'dan seçin)")
    
    edited_df = st.data_editor(
        siralama_df,
        column_config={
            "Ürün Segmenti": st.column_config.TextColumn(
                "Ürün Segmenti",
                disabled=True,
                width="medium"
            ),
            "1. Öncelik": st.column_config.SelectboxColumn(
                "1. Öncelik",
                options=['RPT', 'Initial', 'Min'],
                required=True,
                width="medium"
            ),
            "2. Öncelik": st.column_config.SelectboxColumn(
                "2. Öncelik",
                options=['RPT', 'Initial', 'Min'],
                required=True,
                width="medium"
            ),
            "3. Öncelik": st.column_config.SelectboxColumn(
                "3. Öncelik",
                options=['RPT', 'Initial', 'Min'],
                required=True,
                width="medium"
            )
        },
        hide_index=True,
        use_container_width=True,
        key="siralama_editor"
    )
    
    st.markdown("---")
    
    # Validasyon ve Kaydet
    col1, col2 = st.columns([1, 2])
    
    with col1:
        if st.button("💾 KAYDET", type="primary", use_container_width=True):
            # Validasyon: Her satırda aynı değer tekrar etmemeli
            valid = True
            error_rows = []
            
            for idx, row in edited_df.iterrows():
                values = [row['1. Öncelik'], row['2. Öncelik'], row['3. Öncelik']]
                if len(values) != len(set(values)):
                    valid = False
                    error_rows.append(row['Ürün Segmenti'])
            
            if not valid:
                st.error(f"❌ Hata! Aynı öncelik tekrar ediyor: {', '.join(error_rows)}")
                st.warning("Her segment için RPT, Initial ve Min değerleri farklı olmalı!")
            else:
                # Dictionary formatında kaydet
                yeni_siralama = {}
                for _, row in edited_df.iterrows():
                    yeni_siralama[row['Ürün Segmenti']] = [
                        row['1. Öncelik'],
                        row['2. Öncelik'],
                        row['3. Öncelik']
                    ]
                
                st.session_state.oncelik_siralama = yeni_siralama
                st.success("✅ Sıralama kaydedildi!")
                st.balloons()
    
    with col2:
        st.info("💡 **İpucu:** Her satırda RPT, Initial ve Min farklı sırada olmalı")
    
    st.markdown("---")
    
    # Önizleme
    st.subheader("👁️ Kayıtlı Sıralama Önizlemesi")
    
    if st.session_state.oncelik_siralama is not None:
        import json
        preview_data = []
        for segment, order in st.session_state.oncelik_siralama.items():
            preview_data.append({
                'Segment': segment,
                'Sıralama': ' → '.join(order)
            })
        
        preview_df = pd.DataFrame(preview_data)
        st.dataframe(preview_df, use_container_width=True, hide_index=True, height=250)
        
        # JSON export
        with st.expander("📥 JSON Formatında İndir"):
            json_str = json.dumps(st.session_state.oncelik_siralama, indent=2, ensure_ascii=False)
            st.download_button(
                label="💾 JSON İndir",
                data=json_str,
                file_name="oncelik_siralama.json",
                mime="application/json"
            )
            st.code(json_str, language='json')
    else:
        st.warning("⚠️ Henüz kayıtlı sıralama yok")
    
    st.markdown("---")
    
    # Reset butonu
    if st.button("🔄 Default Sıralamaya Sıfırla"):
        st.session_state.oncelik_siralama = None
        st.success("✅ Sıfırlandı! Sayfa yenileniyor...")
        st.rerun()
    
    st.markdown("---")
    
    # Bilgilendirme
    st.info("""
    **ℹ️ Bu Sıralama Nerede Kullanılır?**
    
    **Hesaplama** bölümünde sevkiyat ihtiyaçları hesaplanırken:
    1. Tüm ürün-mağaza kombinasyonları için ihtiyaç hesaplanır (RPT/Initial/Min)
    2. Bu sıralama bilgisine göre öncelik atanır
    3. Depo stoku **bu öncelik sırasına göre dağıtılır**
    
    **Örnek:**
    - Segment 0-4 ürünü için önce **RPT** ihtiyaçları karşılanır
    - Sonra **Initial** (yeni ürün dağıtımı)
    - En son **Min** (minimum garantisi)
    
    **⚠️ Önemli:** Kaydet butonuna basmazsanız **default sıralama** (RPT → Initial → Min) kullanılır!
    """)
    
    st.markdown("---")
    
    # Kullanım Notu
    st.success("""
    ✅ **Hızlı Kullanım:**
    - Varsayılan sıralamayı kullanmak istiyorsanız → Hiçbir şey yapmanıza gerek yok!
    - Özel sıralama istiyorsanız → Tabloyu düzenleyin ve **Kaydet** butonuna basın
    """)

# ============================================
# 📐 HESAPLAMA - MAX YAKLAŞIMI İLE DÜZELTİLMİŞ
# ============================================
# Bu kodu 2_Sevkiyat.py dosyasında "elif menu == '📐 Hesaplama':" 
# bölümünün TAMAMINI değiştirmek için kullan

elif menu == "📐 Hesaplama":
    st.title("📐 Hesaplama")
    st.markdown("---")
    
    # Veri kontrolü
    required_data = {
        "Ürün Master": st.session_state.urun_master,
        "Mağaza Master": st.session_state.magaza_master,
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.warning("⚠️ Tüm zorunlu verileri yükleyin!")
        st.error(f"**Eksik:** {', '.join(missing_data)}")
        st.stop()
    
    st.success("✅ Tüm zorunlu veriler hazır!")
    
    if st.button("🚀 HESAPLA", type="primary", use_container_width=True):
        baslaangic_zamani = time.time()
        
        with st.spinner("Hesaplanıyor..."):
            try:
                # ============================================
                # 1. VERİ HAZIRLA
                # ============================================
                st.info("📂 Veriler hazırlanıyor...")
                
                df = st.session_state.anlik_stok_satis.copy()
                df['urun_kod'] = df['urun_kod'].astype(str)
                df['magaza_kod'] = df['magaza_kod'].astype(str)
                
                depo_df = st.session_state.depo_stok.copy()
                depo_df['urun_kod'] = depo_df['urun_kod'].astype(str)
                depo_df['depo_kod'] = depo_df['depo_kod'].astype(int)
                
                magaza_df = st.session_state.magaza_master.copy()
                magaza_df['magaza_kod'] = magaza_df['magaza_kod'].astype(str)
                
                kpi_df = st.session_state.kpi.copy()
                
                st.write(f"✅ Anlık stok/satış: {len(df):,} satır")
                st.write(f"✅ Depo stok: {len(depo_df):,} satır")
                
                # ============================================
                # 2. YENİ ÜRÜNLER
                # ============================================
                depo_sum = depo_df.groupby('urun_kod')['stok'].sum()
                yeni_adaylar = depo_sum[depo_sum > 300].index.tolist()
                
                urun_magaza_count = df[df['urun_kod'].isin(yeni_adaylar)].groupby('urun_kod')['magaza_kod'].nunique()
                total_magaza = df['magaza_kod'].nunique()
                yeni_urunler = urun_magaza_count[urun_magaza_count < total_magaza * 0.5].index.tolist()
                
                st.write(f"✅ Yeni ürün adayı: {len(yeni_urunler):,}")



                # 3. SEGMENTASYON - VERİ TİPİ UYUMLU
                if (st.session_state.urun_segment_map and st.session_state.magaza_segment_map):
                    # String key'li dictionary oluştur
                    urun_seg_map_str = {str(k): str(v) for k, v in st.session_state.urun_segment_map.items()}
                    magaza_seg_map_str = {str(k): str(v) for k, v in st.session_state.magaza_segment_map.items()}
                    
                    # String'e çevirip map yap
                    df['urun_segment'] = df['urun_kod'].astype(str).map(urun_seg_map_str).fillna('0-4')
                    df['magaza_segment'] = df['magaza_kod'].astype(str).map(magaza_seg_map_str).fillna('0-4')
                    
                    # Debug
                    urun_eslesen = (df['urun_segment'] != '0-4').sum()
                    magaza_eslesen = (df['magaza_segment'] != '0-4').sum()
                    st.info(f"📊 Segment eşleşme: Ürün {urun_eslesen}/{len(df)} | Mağaza {magaza_eslesen}/{len(df)}")
                else:
                    df['urun_segment'] = '0-4'
                    df['magaza_segment'] = '0-4'
                    st.warning("⚠️ Segment map bulunamadı, default '0-4' kullanılıyor")

                
                # ============================================
                # 4. KPI VE MG BİLGİLERİ
                # ============================================
                default_fc = kpi_df['forward_cover'].mean() if 'forward_cover' in kpi_df.columns else 7.0
                
                df['min_deger'] = 0.0
                df['max_deger'] = 999999.0
                
                # MG bilgisi ekle
                if st.session_state.urun_master is not None and 'mg' in st.session_state.urun_master.columns:
                    urun_m = st.session_state.urun_master[['urun_kod', 'mg']].copy()
                    urun_m['urun_kod'] = urun_m['urun_kod'].astype(str)
                    urun_m['mg'] = urun_m['mg'].fillna('0').astype(str)
                    df = df.merge(urun_m, on='urun_kod', how='left')
                    df['mg'] = df['mg'].fillna('0')
                else:
                    df['mg'] = '0'
                
                # KPI değerlerini uygula
                if not kpi_df.empty and 'mg_id' in kpi_df.columns:
                    kpi_lookup = {}
                    for _, row in kpi_df.iterrows():
                        mg_key = str(row['mg_id'])
                        kpi_lookup[mg_key] = {
                            'min': float(row.get('min_deger', 0)) if pd.notna(row.get('min_deger', 0)) else 0,
                            'max': float(row.get('max_deger', 999999)) if pd.notna(row.get('max_deger', 999999)) else 999999
                        }
                    
                    for mg_val in df['mg'].unique():
                        if mg_val in kpi_lookup:
                            mask = df['mg'] == mg_val
                            df.loc[mask, 'min_deger'] = kpi_lookup[mg_val]['min']
                            df.loc[mask, 'max_deger'] = kpi_lookup[mg_val]['max']
                
                # ============================================
                # 5. DEPO KODU EKLEMESİ
                # ============================================
                if 'depo_kod' in magaza_df.columns:
                    df = df.merge(magaza_df[['magaza_kod', 'depo_kod']], on='magaza_kod', how='left')
                    df['depo_kod'] = df['depo_kod'].fillna(0).astype(int)
                    df['depo_kod'] = df['depo_kod'].replace(0, 1)
                else:
                    df['depo_kod'] = 1
                
                st.write(f"✅ Depo kodları eklendi")
                
                # ============================================
                # 6. MATRİS DEĞERLERİ
                # ============================================
                df['genlestirme'] = 1.0
                df['sisme'] = 0.5
                df['min_oran'] = 1.0
                df['initial_katsayi'] = 1.0
                
                all_matrices_exist = all([
                    st.session_state.genlestirme_orani is not None,
                    st.session_state.sisme_orani is not None,
                    st.session_state.min_oran is not None,
                    st.session_state.initial_matris is not None
                ])
                
                if all_matrices_exist:
                    st.info("🔄 Matris değerleri uygulanıyor...")
                    
                    # Genleştirme
                    genles_long = st.session_state.genlestirme_orani.stack().reset_index()
                    genles_long.columns = ['magaza_segment', 'urun_segment', 'genlestirme_mat']
                    genles_long['magaza_segment'] = genles_long['magaza_segment'].astype(str)
                    genles_long['urun_segment'] = genles_long['urun_segment'].astype(str)
                    df = df.merge(genles_long, on=['magaza_segment', 'urun_segment'], how='left')
                    df['genlestirme'] = df['genlestirme_mat'].fillna(df['genlestirme'])
                    df.drop('genlestirme_mat', axis=1, inplace=True)
                    
                    # Şişme
                    sisme_long = st.session_state.sisme_orani.stack().reset_index()
                    sisme_long.columns = ['magaza_segment', 'urun_segment', 'sisme_mat']
                    sisme_long['magaza_segment'] = sisme_long['magaza_segment'].astype(str)
                    sisme_long['urun_segment'] = sisme_long['urun_segment'].astype(str)
                    df = df.merge(sisme_long, on=['magaza_segment', 'urun_segment'], how='left')
                    df['sisme'] = df['sisme_mat'].fillna(df['sisme'])
                    df.drop('sisme_mat', axis=1, inplace=True)
                    
                    # Min Oran
                    min_long = st.session_state.min_oran.stack().reset_index()
                    min_long.columns = ['magaza_segment', 'urun_segment', 'min_oran_mat']
                    min_long['magaza_segment'] = min_long['magaza_segment'].astype(str)
                    min_long['urun_segment'] = min_long['urun_segment'].astype(str)
                    df = df.merge(min_long, on=['magaza_segment', 'urun_segment'], how='left')
                    df['min_oran'] = df['min_oran_mat'].fillna(df['min_oran'])
                    df.drop('min_oran_mat', axis=1, inplace=True)
                    
                    # Initial
                    initial_long = st.session_state.initial_matris.stack().reset_index()
                    initial_long.columns = ['magaza_segment', 'urun_segment', 'initial_mat']
                    initial_long['magaza_segment'] = initial_long['magaza_segment'].astype(str)
                    initial_long['urun_segment'] = initial_long['urun_segment'].astype(str)
                    df = df.merge(initial_long, on=['magaza_segment', 'urun_segment'], how='left')
                    df['initial_katsayi'] = df['initial_mat'].fillna(df['initial_katsayi'])
                    df.drop('initial_mat', axis=1, inplace=True)
                    
                    st.success("✅ Matris değerleri uygulandı!")
                
                # ============================================
                # 7. İHTİYAÇ HESAPLA - MAX YAKLAŞIMI ✅
                # ============================================
                st.info("📊 İhtiyaçlar hesaplanıyor (MAX yaklaşımı)...")
                
                # Her ürün-mağaza için 3 farklı ihtiyaç hesapla
                df['rpt_ihtiyac'] = (
                    default_fc * df['satis'] * df['genlestirme']
                ) - (df['stok'] + df['yol'])
                
                df['min_ihtiyac'] = (
                    df['min_oran'] * df['min_deger']
                ) - (df['stok'] + df['yol'])
                
                # Initial ihtiyacı (sadece yeni ürünler için)
                df['initial_ihtiyac'] = 0.0
                if yeni_urunler:
                    yeni_mask = df['urun_kod'].isin(yeni_urunler)
                    df.loc[yeni_mask, 'initial_ihtiyac'] = (
                        df.loc[yeni_mask, 'min_deger'] * df.loc[yeni_mask, 'initial_katsayi']
                    ) - (df.loc[yeni_mask, 'stok'] + df.loc[yeni_mask, 'yol'])
                
                # Negatif değerleri sıfırla
                df['rpt_ihtiyac'] = df['rpt_ihtiyac'].clip(lower=0)
                df['min_ihtiyac'] = df['min_ihtiyac'].clip(lower=0)
                df['initial_ihtiyac'] = df['initial_ihtiyac'].clip(lower=0)
                
                # ✅ MAX'I AL - TEK İHTİYAÇ
                df['ihtiyac'] = df[['rpt_ihtiyac', 'min_ihtiyac', 'initial_ihtiyac']].max(axis=1)
                
                # Hangi türden geldiğini belirle
                def belirle_durum(row):
                    if row['ihtiyac'] == 0:
                        return 'Yok'
                    if row['ihtiyac'] == row['rpt_ihtiyac']:
                        return 'RPT'
                    elif row['ihtiyac'] == row['initial_ihtiyac'] and row['initial_ihtiyac'] > 0:
                        return 'Initial'
                    elif row['ihtiyac'] == row['min_ihtiyac']:
                        return 'Min'
                    else:
                        return 'RPT'
                
                df['durum'] = df.apply(belirle_durum, axis=1)
                
                st.success(f"✅ İhtiyaçlar hesaplandı (MAX yaklaşımı)")
                
                             
                # ============================================
                # 8. YASAK KONTROL
                # ============================================
                if (st.session_state.yasak_master is not None and 
                    'urun_kod' in st.session_state.yasak_master.columns and
                    'magaza_kod' in st.session_state.yasak_master.columns):
                    
                    yasak = st.session_state.yasak_master.copy()
                    yasak['urun_kod'] = yasak['urun_kod'].astype(str)
                    yasak['magaza_kod'] = yasak['magaza_kod'].astype(str)
                    
                    if 'yasak_durum' in yasak.columns:
                        df = df.merge(
                            yasak[['urun_kod', 'magaza_kod', 'yasak_durum']], 
                            on=['urun_kod', 'magaza_kod'], how='left'
                        )
                        df.loc[df['yasak_durum'] == 'Yasak', 'ihtiyac'] = 0
                        df.drop('yasak_durum', axis=1, inplace=True, errors='ignore')
                
                # ============================================
                # 9. DEPO STOK DAĞITIMI
                # ============================================
                st.info("🚀 Depo stok dağıtımı yapılıyor...")
                
                # Sadece pozitif ihtiyaçları al
                result = df[df['ihtiyac'] > 0].copy()
                st.write(f"Pozitif ihtiyaç sayısı: {len(result):,}")
                
                if len(result) == 0:
                    st.warning("⚠️ Hiç pozitif ihtiyaç bulunamadı!")
                    st.stop()
                
                # Öncelik sıralaması
                durum_priority = {'RPT': 1, 'Initial': 2, 'Min': 3}
                result['durum_oncelik'] = result['durum'].map(durum_priority).fillna(4)
                result = result.sort_values(['durum_oncelik', 'ihtiyac'], ascending=[True, False])
                result = result.reset_index(drop=True)
                
                # Depo stok dictionary oluştur
                depo_stok_dict = {}
                for _, row in depo_df.iterrows():
                    key = (int(row['depo_kod']), str(row['urun_kod']))
                    depo_stok_dict[key] = float(row['stok'])
                
                # NumPy array'lerle çalış
                depo_kodlar = result['depo_kod'].values.astype(int)
                urun_kodlar = result['urun_kod'].values.astype(str)
                ihtiyaclar = result['ihtiyac'].values.astype(float)
                
                sevkiyat_array = np.zeros(len(result), dtype=float)
                
                # Tek döngü
                progress_bar = st.progress(0)
                total_rows = len(result)
                
                for idx in range(total_rows):
                    key = (depo_kodlar[idx], urun_kodlar[idx])
                    ihtiyac = ihtiyaclar[idx]
                    
                    if key in depo_stok_dict and depo_stok_dict[key] > 0:
                        sevk = min(ihtiyac, depo_stok_dict[key])
                        depo_stok_dict[key] -= sevk
                        sevkiyat_array[idx] = sevk
                    
                    # Progress güncelle (her 10K'da bir)
                    if idx % 10000 == 0:
                        progress_bar.progress(idx / total_rows)
                
                progress_bar.progress(1.0)
                
                result['sevkiyat_miktari'] = sevkiyat_array
                result['stok_yoklugu_satis_kaybi'] = result['ihtiyac'] - result['sevkiyat_miktari']
                
                # Temizlik
                result.drop('durum_oncelik', axis=1, inplace=True, errors='ignore')
                
                st.success("✅ Depo stok dağıtımı tamamlandı!")
                
                # ============================================
                # 10. SONUÇ HAZIRLA
                # ============================================
                final_columns = [
                    'magaza_kod', 'urun_kod', 'magaza_segment', 'urun_segment', 'durum',
                    'stok', 'yol', 'satis', 'ihtiyac', 'sevkiyat_miktari', 'depo_kod', 'stok_yoklugu_satis_kaybi'
                ]
                
                available_columns = [col for col in final_columns if col in result.columns]
                final = result[available_columns].copy()
                
                final = final.rename(columns={
                    'ihtiyac': 'ihtiyac_miktari'
                })
                
                # Integer dönüşüm
                for col in ['stok', 'yol', 'satis', 'ihtiyac_miktari', 'sevkiyat_miktari', 'stok_yoklugu_satis_kaybi']:
                    if col in final.columns:
                        final[col] = final[col].round().fillna(0).astype(int)
                
                # Sıra numaraları
                final.insert(0, 'sira_no', range(1, len(final) + 1))
                final.insert(1, 'oncelik', range(1, len(final) + 1))
                
                # KAYDET
                st.session_state.sevkiyat_sonuc = final
                
                bitis_zamani = time.time()
                algoritma_suresi = bitis_zamani - baslaangic_zamani
                
                st.success(f"✅ Hesaplama tamamlandı! {len(final):,} satır oluşturuldu.")
                st.markdown("---")
                
                # ============================================
                # 📊 ÖZET METRİKLER TABLOSU
                # ============================================
                st.subheader("📊 Hesaplama Özet Metrikleri")
                
                # Metrikleri hesapla
                toplam_magaza_stok = df['stok'].sum()
                toplam_yol = df['yol'].sum()
                toplam_depo_stok = depo_df['stok'].sum()
                toplam_satis = df['satis'].sum()
                toplam_ihtiyac = final['ihtiyac_miktari'].sum()
                toplam_sevkiyat = final['sevkiyat_miktari'].sum()
                performans = (toplam_sevkiyat / toplam_ihtiyac * 100) if toplam_ihtiyac > 0 else 0
                magaza_sayisi = df['magaza_kod'].nunique()
                urun_sayisi = df['urun_kod'].nunique()
                sevk_olan_urun_sayisi = final[final['sevkiyat_miktari'] > 0]['urun_kod'].nunique()
                
                # Özet tablosu oluştur
                
                ozet_data = {
                    'Metrik': [
                        '📦 Toplam Mağaza Stok',
                        '🚚 Toplam Yol',
                        '🏭 Toplam Depo Stok',
                        '💰 Toplam Satış',
                        '✅ Toplam Sevkiyat',
                        '⏱️ Algoritma Süresi (sn)',
                        '🏪 Mağaza Sayısı',
                        '🏷️ Ürün Sayısı',
                        '📤 Sevk Olan Ürün Sayısı'
                    ],
                    'Değer': [
                        str(f"{toplam_magaza_stok:,.0f}"),
                        str(f"{toplam_yol:,.0f}"),
                        str(f"{toplam_depo_stok:,.0f}"),
                        str(f"{toplam_satis:,.0f}"),
                        str(f"{toplam_sevkiyat:,.0f}"),
                        str(f"{algoritma_suresi:.2f} saniye"),
                        str(f"{magaza_sayisi:,}"),
                        str(f"{urun_sayisi:,}"),
                        str(f"{sevk_olan_urun_sayisi:,}")
                    ]
                }             
                ozet_df = pd.DataFrame(ozet_data)
                
                # Tabloyu göster
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.dataframe(
                        ozet_df,
                        use_container_width=True,
                        hide_index=True,
                        height=450
                    )
                
                with col2:
                    # Önemli metrikler
                    st.metric(
                        "🎯 Genel Performans", 
                        f"{performans:.1f}%",
                        delta=f"{performans - 100:.1f}%" if performans < 100 else "Hedef Aşıldı!"
                    )
                    
                    st.metric(
                        "⚡ İşlem Süresi", 
                        f"{algoritma_suresi:.2f} sn"
                    )
                    
                    
                    
                    # Stok durumu özeti
                    toplam_stok_sistemi = toplam_magaza_stok + toplam_yol + toplam_depo_stok
                    st.metric(
                        "💼 Toplam Sistem Stok",
                        f"{toplam_stok_sistemi:,.0f}"
                    )
                
                st.markdown("---")
                
                # İndirme butonları
                col1, col2, col3 = st.columns([1, 1, 2])
                with col1:
                    sap_data = final[['magaza_kod', 'urun_kod', 'depo_kod', 'sevkiyat_miktari']].copy()
                    sap_data = sap_data[sap_data['sevkiyat_miktari'] > 0]
                    
                    st.download_button(
                        label="📥 SAP Dosyası İndir (CSV)",
                        data=sap_data.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="sap_sevkiyat_detay.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="hesaplama_download_sap_csv"
                    )
                
                with col2:
                    st.download_button(
                        label="📥 Tam Detay İndir (CSV)",
                        data=final.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="sevkiyat_tam_detay.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="hesaplama_download_full_csv"
                    )
                
            except Exception as e:
                st.error(f"❌ Hesaplama hatası: {str(e)}")
                import traceback
                st.code(traceback.format_exc())


# ============================================
# 📈 RAPORLAR 
# ============================================
elif menu == "📈 Raporlar":
    st.title("📈 Raporlar ve Analizler")
    st.markdown("---")
    
    # Hata ayıklama için session state kontrolü
    st.write("**🔍 Debug: Session State Kontrolü**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write(f"Sevkiyat Sonucu: {'✅ Var' if st.session_state.sevkiyat_sonuc is not None else '❌ Yok'}")
        if st.session_state.sevkiyat_sonuc is not None:
            st.write(f"Satır: {len(st.session_state.sevkiyat_sonuc)}")
    
    with col2:
        st.write(f"Ürün Master: {'✅ Var' if st.session_state.urun_master is not None else '❌ Yok'}")
    
    with col3:
        st.write(f"Mağaza Master: {'✅ Var' if st.session_state.magaza_master is not None else '❌ Yok'}")
    
    if st.session_state.sevkiyat_sonuc is None:
        st.error("⚠️ Henüz hesaplama yapılmadı!")
        st.info("Lütfen önce 'Hesaplama' menüsünden hesaplama yapın.")
        
    else:
        result_df = st.session_state.sevkiyat_sonuc.copy()
        # Debug: Veri yapısını göster
        with st.expander("🔍 Veri Yapısı (Debug)", expanded=False):
            st.write("**Kolonlar:**", list(result_df.columns))
            st.write("**İlk 5 satır:**")
            st.dataframe(result_df.head(), width='content')
            st.write("**Temel İstatistikler:**")
            st.write(f"- Toplam satır: {len(result_df)}")
                   
            # KOLON ADI DÜZELTMESİ
            sevkiyat_kolon_adi = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon_adi = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon_adi = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_keybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            if sevkiyat_kolon_adi in result_df.columns:
                st.write(f"- Sevkiyat miktarı > 0: {(result_df[sevkiyat_kolon_adi] > 0).sum()}")
            if ihtiyac_kolon_adi in result_df.columns:
                st.write(f"- İhtiyaç miktarı > 0: {(result_df[ihtiyac_kolon_adi] > 0).sum()}")
        
        tab1, tab2, tab3, tab4 = st.tabs([
            "📦 Ürün Analizi",
            "🏪 Mağaza Analizi", 
            "⚠️ Satış Kaybı Analizi",
            "🗺️ İl Bazında Harita"
        ])


        # ============================================
        # ÜRÜN ANALİZİ - SADELEŞTİRİLMİŞ VERSİYON
        # ============================================        
        with tab1:
            st.subheader("📦 Ürün Bazında Analiz")
            
            sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            st.markdown("### 📊 Ürün Cover Grup (Segment) Bazında Özet")
            
            segment_ozet = result_df.groupby('urun_segment').agg({
                'urun_kod': 'nunique',
                ihtiyac_kolon: 'sum',
                sevkiyat_kolon: 'sum',
                kayip_kolon: 'sum'
            }).reset_index()
            
            segment_ozet.columns = ['Ürün Segmenti', 'Ürün Sayısı', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Toplam Kayıp']
            
            segment_ozet['Karşılama %'] = np.where(
                segment_ozet['Toplam İhtiyaç'] > 0,
                (segment_ozet['Toplam Sevkiyat'] / segment_ozet['Toplam İhtiyaç'] * 100),
                0
            ).round(1)
            
            segment_ozet = segment_ozet.sort_values('Ürün Segmenti')
            
            st.dataframe(segment_ozet, width='stretch', hide_index=True, height=250)


            
       
        # ============================================
        # MAĞAZA ANALİZİ - SADELEŞTİRİLMİŞ VERSİYON
        # ============================================
        with tab2:
            st.subheader("🏪 Mağaza Bazında Analiz")
            
            sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            st.markdown("### 📊 Mağaza Cover Grup (Segment) Bazında Özet")
            
            magaza_segment_ozet = result_df.groupby('magaza_segment').agg({
                'magaza_kod': 'nunique',
                ihtiyac_kolon: 'sum',
                sevkiyat_kolon: 'sum',
                kayip_kolon: 'sum'
            }).reset_index()
            
            magaza_segment_ozet.columns = ['Mağaza Segmenti', 'Mağaza Sayısı', 'Toplam İhtiyaç', 'Toplam Sevkiyat', 'Toplam Kayıp']
            
            magaza_segment_ozet['Karşılama %'] = np.where(
                magaza_segment_ozet['Toplam İhtiyaç'] > 0,
                (magaza_segment_ozet['Toplam Sevkiyat'] / magaza_segment_ozet['Toplam İhtiyaç'] * 100),
                0
            ).round(1)
            
            magaza_segment_ozet['Sevkiyat/Mağaza'] = np.where(
                magaza_segment_ozet['Mağaza Sayısı'] > 0,
                (magaza_segment_ozet['Toplam Sevkiyat'] / magaza_segment_ozet['Mağaza Sayısı']),
                0
            ).round(0)
            
            magaza_segment_ozet = magaza_segment_ozet.sort_values('Mağaza Segmenti')
            
            st.dataframe(magaza_segment_ozet, width='stretch', hide_index=True, height=250)
        
        
         
        # ============================================
        # SATIŞ KAYBI ANALİZİ - SEGMENT BAZLI TABLOLAR
        # ============================================
        
        with tab3:
            st.subheader("⚠️ Satış Kaybı Analizi")
            
            sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
            ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
            kayip_kolon = 'stok_yoklugu_satis_kaybi' if 'stok_yoklugu_satis_kaybi' in result_df.columns else 'stok_yoklugu_kaybi'
            
            st.markdown("### 📦 Ürün Cover Grup Bazında Satış Kaybı")
            
            urun_segment_kayip = result_df.groupby('urun_segment').agg({
                'urun_kod': 'nunique',
                kayip_kolon: 'sum',
                ihtiyac_kolon: 'sum',
                sevkiyat_kolon: 'sum'
            }).reset_index()
            
            urun_segment_kayip.columns = ['Ürün Segmenti', 'Ürün Sayısı', 'Toplam Kayıp', 'Toplam İhtiyaç', 'Toplam Sevkiyat']
            
            urun_segment_kayip['Kayıp Oranı %'] = np.where(
                urun_segment_kayip['Toplam İhtiyaç'] > 0,
                (urun_segment_kayip['Toplam Kayıp'] / urun_segment_kayip['Toplam İhtiyaç'] * 100),
                0
            ).round(1)
            
            urun_segment_kayip = urun_segment_kayip.sort_values('Ürün Segmenti')
            
            st.dataframe(urun_segment_kayip, width='stretch', hide_index=True, height=250)
            
            st.markdown("---")
            
            st.markdown("### 🏪 Mağaza Cover Grup Bazında Satış Kaybı")
            
            magaza_segment_kayip = result_df.groupby('magaza_segment').agg({
                'magaza_kod': 'nunique',
                kayip_kolon: 'sum',
                ihtiyac_kolon: 'sum',
                sevkiyat_kolon: 'sum'
            }).reset_index()
            
            magaza_segment_kayip.columns = ['Mağaza Segmenti', 'Mağaza Sayısı', 'Toplam Kayıp', 'Toplam İhtiyaç', 'Toplam Sevkiyat']
            
            magaza_segment_kayip['Kayıp Oranı %'] = np.where(
                magaza_segment_kayip['Toplam İhtiyaç'] > 0,
                (magaza_segment_kayip['Toplam Kayıp'] / magaza_segment_kayip['Toplam İhtiyaç'] * 100),
                0
            ).round(1)
            
            magaza_segment_kayip = magaza_segment_kayip.sort_values('Mağaza Segmenti')
            
            st.dataframe(magaza_segment_kayip, width='stretch', hide_index=True, height=250)
        
        # ============================================
        # İL BAZINDA HARİTA - SEVKİYAT/MAĞAZA BAZLI
        # ============================================
        with tab4:
            st.subheader("🗺️ İl Bazında Sevkiyat Haritası")
            
            # Plotly kontrolü
            try:
                import plotly.express as px
                import plotly.graph_objects as go
                PLOTLY_AVAILABLE = True
            except ImportError:
                st.error("Plotly kütüphanesi yüklü değil! requirements.txt dosyasına 'plotly' ekleyin.")
                PLOTLY_AVAILABLE = False
            
            if not PLOTLY_AVAILABLE:
                st.stop()
                
            if st.session_state.magaza_master is None:
                st.warning("⚠️ Mağaza Master verisi yüklenmemiş! Harita için il bilgisi gerekiyor.")
            else:
                # KOLON ADI DÜZELTMESİ
                sevkiyat_kolon = 'sevkiyat_miktari' if 'sevkiyat_miktari' in result_df.columns else 'sevkiyat_gercek'
                ihtiyac_kolon = 'ihtiyac_miktari' if 'ihtiyac_miktari' in result_df.columns else 'ihtiyac'
                
                # İl bazında verileri hazırla
                il_verileri = result_df.groupby('magaza_kod').agg({
                    sevkiyat_kolon: 'sum',
                    ihtiyac_kolon: 'sum'
                }).reset_index()
                
                # Mağaza master'dan il bilgilerini ekle
                magaza_master = st.session_state.magaza_master[['magaza_kod', 'il']].copy()
                magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                il_verileri['magaza_kod'] = il_verileri['magaza_kod'].astype(str)
                
                il_verileri = il_verileri.merge(magaza_master, on='magaza_kod', how='left')
                
                # İl bazında toplamlar
                il_bazinda = il_verileri.groupby('il').agg({
                    sevkiyat_kolon: 'sum',
                    ihtiyac_kolon: 'sum',
                    'magaza_kod': 'nunique'
                }).reset_index()
                
                il_bazinda.columns = ['İl', 'Toplam Sevkiyat', 'Toplam İhtiyaç', 'Mağaza Sayısı']
                
                # Ortalama sevkiyat/mağaza hesapla
                il_bazinda['Sevkiyat/Mağaza'] = (il_bazinda['Toplam Sevkiyat'] / il_bazinda['Mağaza Sayısı']).round(0)
                
                # Karşılama oranı da ekleyelim
                il_bazinda['Karşılama %'] = np.where(
                    il_bazinda['Toplam İhtiyaç'] > 0,
                    (il_bazinda['Toplam Sevkiyat'] / il_bazinda['Toplam İhtiyaç'] * 100),
                    0
                ).round(1)
                
                # Türkiye il koordinatları
                turkiye_iller = {
                    'İstanbul': (41.0082, 28.9784), 'Ankara': (39.9334, 32.8597), 'İzmir': (38.4237, 27.1428),
                    'Bursa': (40.1885, 29.0610), 'Antalya': (36.8969, 30.7133), 'Adana': (37.0000, 35.3213),
                    'Konya': (37.8667, 32.4833), 'Gaziantep': (37.0662, 37.3833), 'Şanlıurfa': (37.1591, 38.7969),
                    'Mersin': (36.8000, 34.6333), 'Kocaeli': (40.8533, 29.8815), 'Diyarbakır': (37.9144, 40.2306),
                    'Hatay': (36.4018, 36.3498), 'Manisa': (38.6191, 27.4289), 'Kayseri': (38.7312, 35.4787),
                    'Samsun': (41.2928, 36.3313), 'Balıkesir': (39.6484, 27.8826), 'Kahramanmaraş': (37.5858, 36.9371),
                    'Van': (38.4891, 43.4080), 'Aydın': (37.8560, 27.8416), 'Tekirdağ': (40.9781, 27.5117),
                    'Denizli': (37.7765, 29.0864), 'Muğla': (37.2153, 28.3636), 'Eskişehir': (39.7767, 30.5206),
                    'Trabzon': (41.0015, 39.7178), 'Ordu': (40.9833, 37.8833), 'Afyonkarahisar': (38.7638, 30.5403),
                    'Sivas': (39.7477, 37.0179), 'Malatya': (38.3552, 38.3095), 'Erzurum': (39.9000, 41.2700),
                    'Elazığ': (38.6810, 39.2264), 'Batman': (37.8812, 41.1351), 'Kütahya': (39.4167, 29.9833),
                    'Çorum': (40.5506, 34.9556), 'Isparta': (37.7648, 30.5566), 'Osmaniye': (37.2130, 36.1763),
                    'Çanakkale': (40.1553, 26.4142), 'Giresun': (40.9128, 38.3895), 'Aksaray': (38.3687, 34.0370),
                    'Yozgat': (39.8200, 34.8044), 'Edirne': (41.6667, 26.5667), 'Düzce': (40.8433, 31.1565),
                    'Tokat': (40.3167, 36.5500), 'Kastamonu': (41.3767, 33.7765), 'Uşak': (38.6823, 29.4082),
                    'Kırklareli': (41.7333, 27.2167), 'Niğde': (37.9667, 34.6833), 'Rize': (41.0201, 40.5234),
                    'Amasya': (40.6500, 35.8333), 'Bolu': (40.7333, 31.6000), 'Nevşehir': (38.6939, 34.6857),
                    'Bilecik': (40.1500, 29.9833), 'Burdur': (37.7167, 30.2833), 'Kırıkkale': (39.8468, 33.5153),
                    'Karabük': (41.2000, 32.6333), 'Karaman': (37.1759, 33.2287), 'Kırşehir': (39.1500, 34.1667),
                    'Sinop': (42.0231, 35.1531), 'Hakkari': (37.5833, 43.7333), 'Iğdır': (39.9167, 44.0333),
                    'Yalova': (40.6500, 29.2667), 'Bartın': (41.6344, 32.3375), 'Ardahan': (41.1105, 42.7022),
                    'Bayburt': (40.2552, 40.2249), 'Kilis': (36.7164, 37.1156), 'Muş': (38.9462, 41.7539),
                    'Siirt': (37.9333, 41.9500), 'Tunceli': (39.1071, 39.5400), 'Şırnak': (37.5164, 42.4611),
                    'Bitlis': (38.4000, 42.1000), 'Artvin': (41.1667, 41.8333), 'Gümüşhane': (40.4603, 39.4814),
                    'Ağrı': (39.7191, 43.0513), 'Erzincan': (39.7500, 39.5000), 'Adıyaman': (37.7648, 38.2786),
                    'Zonguldak': (41.4564, 31.7987), 'Mardin': (37.3212, 40.7245), 'Sakarya': (40.6937, 30.4358)
                }
                
                # Koordinatları dataframe'e ekle
                il_bazinda['lat'] = il_bazinda['İl'].map(lambda x: turkiye_iller.get(x, (0, 0))[0])
                il_bazinda['lon'] = il_bazinda['İl'].map(lambda x: turkiye_iller.get(x, (0, 0))[1])
                
                # Koordinatı olmayan illeri filtrele
                il_bazinda = il_bazinda[il_bazinda['lat'] != 0]
                
                if len(il_bazinda) > 0:
                    # Interaktif harita oluştur - SEVKİYAT/MAĞAZA BAZLI
                    st.subheader("📍 İl Bazında Ortalama Sevkiyat/Mağaza")
                    
                    fig = px.scatter_mapbox(
                        il_bazinda,
                        lat="lat",
                        lon="lon", 
                        hover_name="İl",
                        hover_data={
                            'Sevkiyat/Mağaza': ':,.0f',
                            'Toplam Sevkiyat': ':,.0f',
                            'Mağaza Sayısı': ':,.0f',
                            'Karşılama %': ':.1f',
                            'lat': False,
                            'lon': False
                        },
                        color="Sevkiyat/Mağaza",
                        color_continuous_scale="RdYlGn",  # Kırmızı -> Sarı -> Yeşil
                        size="Sevkiyat/Mağaza",
                        size_max=30,
                        zoom=4.5,
                        center={"lat": 39.0, "lon": 35.0},
                        height=600,
                        title="Türkiye İl Bazında Ortalama Sevkiyat/Mağaza Dağılımı"
                    )
                    
                    fig.update_layout(
                        mapbox_style="open-street-map",
                        margin={"r": 0, "t": 30, "l": 0, "b": 0},
                        coloraxis_colorbar=dict(
                            title="Sevkiyat/Mağaza",
                            tickformat=",d"
                        )
                    )
                    
                    st.info("🔍 Haritayı mouse tekerleği ile zoom in/out yapabilir, sürükleyerek hareket ettirebilirsiniz. Renk ne kadar yeşile yakınsa sevkiyat/mağaza o kadar yüksek.")
                    
                    st.plotly_chart(fig, use_container_width=True, key="turkey_map")
                    
                    # İl seçimi için dropdown
                    st.markdown("---")
                    st.subheader("🔍 İl Detayları")
                    
                    secilen_il = st.selectbox(
                        "Detayını görmek istediğiniz ili seçin:",
                        options=il_bazinda['İl'].sort_values().tolist(),
                        key="il_secim_dropdown"
                    )
                    
                    if secilen_il:
                        # Seçilen ilin detaylarını göster
                        il_detay = il_bazinda[il_bazinda['İl'] == secilen_il].iloc[0]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            try:
                                val = il_detay['Sevkiyat/Mağaza']
                                val_str = f"{float(val):,.0f}" if pd.notna(val) and val != '' else "0"
                            except:
                                val_str = "0"
                            st.metric("Sevkiyat/Mağaza", val_str)
                        
                        with col2:
                            try:
                                val = il_detay['Toplam Sevkiyat']
                                val_str = f"{float(val):,.0f}" if pd.notna(val) and val != '' else "0"
                            except:
                                val_str = "0"
                            st.metric("Toplam Sevkiyat", val_str)
                        
                        with col3:
                            try:
                                val = il_detay['Mağaza Sayısı']
                                val_str = f"{float(val):,.0f}" if pd.notna(val) and val != '' else "0"
                            except:
                                val_str = "0"
                            st.metric("Mağaza Sayısı", val_str)
                        
                        with col4:
                            try:
                                val = il_detay['Karşılama %']
                                val_str = f"{float(val):.1f}%" if pd.notna(val) and val != '' else "0%"
                            except:
                                val_str = "0%"
                            st.metric("Karşılama %", val_str)
                        
                        # Seçilen ildeki mağaza detayları
                        st.subheader(f"🏪 {secilen_il} İlindeki Mağaza Performansları")
                        
                        try:
                            magaza_detay = result_df[result_df['magaza_kod'].isin(
                                magaza_master[magaza_master['il'] == secilen_il]['magaza_kod'].astype(str)
                            )]
                            
                            if len(magaza_detay) > 0:
                                magaza_ozet = magaza_detay.groupby('magaza_kod').agg({
                                    sevkiyat_kolon: 'sum',
                                    ihtiyac_kolon: 'sum',
                                    'urun_kod': 'nunique'
                                }).reset_index()
                                
                                magaza_ozet.columns = ['Mağaza Kodu', 'Toplam Sevkiyat', 'Toplam İhtiyaç', 'Ürün Sayısı']
                                
                                magaza_ozet['Karşılama %'] = np.where(
                                    magaza_ozet['Toplam İhtiyaç'] > 0,
                                    (magaza_ozet['Toplam Sevkiyat'] / magaza_ozet['Toplam İhtiyaç'] * 100),
                                    0
                                ).round(1)
                                
                                # Sevkiyata göre sırala
                                magaza_ozet = magaza_ozet.sort_values('Toplam Sevkiyat', ascending=False)
                                
                                st.dataframe(
                                    magaza_ozet.style.format({
                                        'Toplam Sevkiyat': '{:,.0f}',
                                        'Toplam İhtiyaç': '{:,.0f}',
                                        'Ürün Sayısı': '{:.0f}',
                                        'Karşılama %': '{:.1f}%'
                                    }),
                                    use_container_width=True,
                                    height=300,
                                    hide_index=True
                                )
                            else:
                                st.info("Bu ilde mağaza verisi bulunamadı.")
                                
                        except Exception as e:
                            st.error(f"Mağaza detayları yüklenirken hata oluştu: {str(e)}")
                    
                    # İl bazında özet tablo
                    st.markdown("---")
                    st.subheader("📊 Tüm İller - Sevkiyat/Mağaza Sıralaması")
                    
                    il_siralama = il_bazinda[['İl', 'Mağaza Sayısı', 'Toplam Sevkiyat', 'Sevkiyat/Mağaza', 'Karşılama %']].copy()
                    il_siralama = il_siralama.sort_values('Sevkiyat/Mağaza', ascending=False)
                    
                    st.dataframe(
                        il_siralama.style.format({
                            'Mağaza Sayısı': '{:,.0f}',
                            'Toplam Sevkiyat': '{:,.0f}',
                            'Sevkiyat/Mağaza': '{:,.0f}',
                            'Karşılama %': '{:.1f}%'
                        }),
                        use_container_width=True,
                        hide_index=True,
                        height=400
                    )
                    
                    # İndirme butonu
                    st.download_button(
                        label="📥 İl Bazında Analiz İndir (CSV)",
                        data=il_bazinda.to_csv(index=False, encoding='utf-8-sig'),
                        file_name="il_bazinda_analiz.csv",
                        mime="text/csv",
                        use_container_width=True,
                        key="download_il_analiz"
                    )
                
                else:
                    st.warning("Harita için yeterli il verisi bulunamadı.")

# ============================================
# 💾 MASTER DATA OLUŞTURMA
# ============================================
elif menu == "💾 Master Data":
    st.title("💾 Master Data Oluşturma")
    st.markdown("---")
    
    st.warning("🚧 **Master Data modülü yakında yayında!** 🚧")



# ============================================
# 💵 PO HESAPLAMA
# ============================================
elif menu == "💵 PO Hesaplama":
    st.title("💵 Alım Sipariş Hesaplama")
    st.markdown("---")
    
    # Veri kontrolleri
    required_data = {
        "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
        "Depo Stok": st.session_state.depo_stok,
        "KPI": st.session_state.kpi,
        "Mağaza Master": st.session_state.magaza_master
    }
    
    missing_data = [name for name, data in required_data.items() if data is None]
    
    if missing_data:
        st.error(f"❌ Eksik veriler: {', '.join(missing_data)}")
        st.info("👉 Lütfen önce veri yükleme sayfasından gerekli verileri yükleyin.")
        st.stop()
    
    st.success("✅ Tüm gerekli veriler hazır!")
    
    # Opsiyonel veri bilgisi
    col1, col2 = st.columns(2)
    with col1:
        if st.session_state.po_yasak is not None:
            st.info("✅ PO Yasak aktif")
        else:
            st.warning("⚠️ PO Yasak yok")
    with col2:
        if st.session_state.urun_master is not None:
            st.info("✅ Ürün Master aktif")
        else:
            st.warning("⚠️ Ürün Master yok")
    
    st.markdown("---")
    
    # Parametreler
    st.subheader("🎯 Hesaplama Parametreleri")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        forward_cover = st.number_input(
            "Forward Cover",
            min_value=1.0,
            max_value=30.0,
            value=5.0,
            step=0.5,
            help="Hedef forward cover değeri (KPI'dan otomatik alınabilir)"
        )
    
    with col2:
        fc_ek = st.number_input(
            "Forward Cover Üretim Süresi (Safety Stock)",
            min_value=0,
            max_value=14,
            value=2,
            step=1,
            help="Forward cover'a eklenecek güvenlik stoğu"
        )
    
    with col3:
        depo_stok_threshold = st.number_input(
            "Min Depo Stok Eşiği",
            min_value=0,
            max_value=1000000,
            value=999,
            step=100,
            help="Bu değerden yüksek depo stoklu ürünler için PO hesaplanmaz"
        )
    
    st.markdown("---")
    
    # Cover Segment Matrix
    st.subheader("📊 Cover Segment Genişletme Katsayıları (Matris)")
    
    product_ranges = st.session_state.segmentation_params['product_ranges']
    store_ranges = st.session_state.segmentation_params['store_ranges']
    
    cover_segments = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in product_ranges]
    store_segments = [f"{int(r[0])}-{int(r[1]) if r[1] != float('inf') else 'inf'}" for r in store_ranges]
    
    def sort_segments(segments):
        def get_sort_key(seg):
            try:
                return int(seg.split('-')[0])
            except:
                return 9999
        return sorted(segments, key=get_sort_key)
    
    cover_segments_sorted = sort_segments(cover_segments)
    store_segments_sorted = sort_segments(store_segments)
    
    # İlk kez oluşturuluyorsa
    if st.session_state.cover_segment_matrix is None or \
       not isinstance(st.session_state.cover_segment_matrix, pd.DataFrame) or \
       len(st.session_state.cover_segment_matrix.columns) < 2:
        
        default_matrix = pd.DataFrame(1.0, index=cover_segments_sorted, columns=store_segments_sorted)
        
        for i, prod_seg in enumerate(cover_segments_sorted):
            prod_start = int(prod_seg.split('-')[0])
            if prod_start < 5:
                default_matrix.loc[prod_seg, :] = 1.2
            elif prod_start < 10:
                default_matrix.loc[prod_seg, :] = 1.1
            elif prod_start < 15:
                default_matrix.loc[prod_seg, :] = 1.05
            else:
                default_matrix.loc[prod_seg, :] = 0.75
        
        st.session_state.cover_segment_matrix = default_matrix
    
    # Editable matris göster
    matrix_display = st.session_state.cover_segment_matrix.reset_index()
    matrix_display.columns = ['Ürün Cover ↓ / Mağaza Cover →'] + list(st.session_state.cover_segment_matrix.columns)
    
    edited_cover_matrix_temp = st.data_editor(
        matrix_display,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            'Ürün Cover ↓ / Mağaza Cover →': st.column_config.TextColumn(
                "Ürün Cover ↓ / Mağaza Cover →",
                disabled=True,
                width="medium"
            )
        }
    )
    
    # Güvenli dönüşüm
    try:
        edited_df = pd.DataFrame(edited_cover_matrix_temp)
        first_col = edited_df.columns[0]
        edited_cover_matrix = edited_df.set_index(first_col)
    except:
        edited_cover_matrix = st.session_state.cover_segment_matrix
    
    if st.button("💾 Matris Kaydet"):
        st.session_state.cover_segment_matrix = edited_cover_matrix
        st.success("✅ Kaydedildi!")
    
    st.markdown("---")
    
    # HESAPLAMA
    if st.button("🚀 PO İhtiyacı Hesapla", type="primary", use_container_width=True):
        try:
            with st.spinner("📊 Hesaplama yapılıyor..."):
                
                start_time = time.time()
                
                # 1. VERİLERİ HAZIRLA
                anlik_df = st.session_state.anlik_stok_satis.copy()
                depo_df = st.session_state.depo_stok.copy()
                magaza_master = st.session_state.magaza_master.copy()
                kpi_df = st.session_state.kpi.copy()
                cover_matrix = st.session_state.cover_segment_matrix.copy()
                
                st.write("**📊 Veri Boyutları:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Anlık Stok/Satış", f"{len(anlik_df):,}")
                with col2:
                    st.metric("Depo Stok", f"{len(depo_df):,}")
                with col3:
                    st.metric("Mağaza Master", f"{len(magaza_master):,}")
                with col4:
                    st.metric("KPI", f"{len(kpi_df):,}")
                
                # Veri tiplerini düzelt
                anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                depo_df['urun_kod'] = depo_df['urun_kod'].astype(str)
                depo_df['depo_kod'] = depo_df['depo_kod'].astype(str)
                magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                magaza_master['depo_kod'] = magaza_master['depo_kod'].astype(str)
                
                # 2. MAĞAZA-DEPO EŞLEŞTİRMESİ
                st.info("🔗 Mağaza-Depo eşleştirmesi yapılıyor...")
                
                df = anlik_df.merge(
                    magaza_master[['magaza_kod', 'depo_kod']],
                    on='magaza_kod',
                    how='left'
                )
                
                eksik_depo = df['depo_kod'].isna().sum()
                if eksik_depo > 0:
                    st.warning(f"⚠️ {eksik_depo} satırda depo kodu bulunamadı (default '1' atanacak)")
                    df['depo_kod'] = df['depo_kod'].fillna('1')
                
                st.write(f"✅ Mağaza-Depo eşleşmesi: {len(df):,} satır")
                
                # 3. DEPO STOK EKLE
                st.info("📦 Depo stokları ekleniyor...")
                
                depo_stok_map = depo_df.groupby(['depo_kod', 'urun_kod'])['stok'].sum().reset_index()
                depo_stok_map.columns = ['depo_kod', 'urun_kod', 'depo_stok']
                
                df = df.merge(
                    depo_stok_map,
                    on=['depo_kod', 'urun_kod'],
                    how='left'
                )
                df['depo_stok'] = df['depo_stok'].fillna(0)
                
                st.write(f"✅ Depo stokları eklendi")
                
                # 4. KPI'DAN MIN DEĞER VE FORWARD COVER EKLE
                st.info("📋 KPI değerleri ekleniyor...")
                
                if st.session_state.urun_master is not None and 'mg' in st.session_state.urun_master.columns:
                    urun_master = st.session_state.urun_master[['urun_kod', 'mg']].copy()
                    urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                    urun_master['mg'] = urun_master['mg'].astype(str)
                    
                    df = df.merge(urun_master, on='urun_kod', how='left')
                    df['mg'] = df['mg'].fillna('0')
                    
                    if 'mg_id' in kpi_df.columns:
                        kpi_lookup = kpi_df.copy()
                        kpi_lookup['mg_id'] = kpi_lookup['mg_id'].astype(str)
                        
                        # Min değer
                        if 'min_deger' in kpi_lookup.columns:
                            df = df.merge(
                                kpi_lookup[['mg_id', 'min_deger']],
                                left_on='mg',
                                right_on='mg_id',
                                how='left'
                            )
                            df['min_deger'] = df['min_deger'].fillna(0)
                            df.drop('mg_id', axis=1, inplace=True, errors='ignore')
                        else:
                            df['min_deger'] = 0
                        
                        # Forward Cover (KPI'dan)
                        if 'forward_cover' in kpi_lookup.columns:
                            fc_kpi = kpi_lookup[['mg_id', 'forward_cover']].copy()
                            fc_kpi.columns = ['mg_id', 'fc_kpi']
                            
                            df = df.merge(
                                fc_kpi,
                                left_on='mg',
                                right_on='mg_id',
                                how='left'
                            )
                            df['forward_cover_final'] = df['fc_kpi'].fillna(forward_cover)
                            df.drop(['mg_id', 'fc_kpi'], axis=1, inplace=True, errors='ignore')
                            
                            kpi_fc_count = (df['forward_cover_final'] != forward_cover).sum()
                            if kpi_fc_count > 0:
                                st.info(f"ℹ️ {kpi_fc_count:,} satır için KPI'dan FC alındı")
                        else:
                            df['forward_cover_final'] = forward_cover
                    else:
                        df['min_deger'] = 0
                        df['forward_cover_final'] = forward_cover
                else:
                    df['mg'] = '0'
                    df['min_deger'] = 0
                    df['forward_cover_final'] = forward_cover
                
                st.write(f"✅ KPI değerleri eklendi")
                
                # 5. PO YASAK KONTROLÜ
                if st.session_state.po_yasak is not None:
                    st.info("🚫 PO Yasak kontrolü yapılıyor...")
                    
                    po_yasak = st.session_state.po_yasak.copy()
                    po_yasak['urun_kodu'] = po_yasak['urun_kodu'].astype(str)
                    
                    df = df.merge(
                        po_yasak[['urun_kodu', 'yasak_durum', 'acik_siparis']],
                        left_on='urun_kod',
                        right_on='urun_kodu',
                        how='left'
                    )
                    
                    df['yasak_durum'] = df['yasak_durum'].fillna(0)
                    df['acik_siparis'] = df['acik_siparis'].fillna(0)
                    
                    yasak_sayisi = (df['yasak_durum'] == 1).sum()
                    df = df[df['yasak_durum'] != 1]
                    
                    if yasak_sayisi > 0:
                        st.warning(f"⚠️ {yasak_sayisi:,} yasak satır çıkarıldı")
                    
                    st.write(f"✅ PO Yasak kontrolü tamamlandı")
                else:
                    df['acik_siparis'] = 0
                
                # 6. SEGMENTASYON VE GENLEŞTİRME KATSAYISI
                st.info("📊 Segment ve genleştirme katsayıları hesaplanıyor...")
                
                # Ürün bazında toplam stok/satış
                urun_agg = anlik_df.groupby('urun_kod').agg({
                    'stok': 'sum',
                    'satis': 'sum'
                }).reset_index()
                urun_agg['urun_stok_satis'] = urun_agg['stok'] / urun_agg['satis'].replace(0, 1)
                
                # Mağaza bazında toplam stok/satış
                magaza_agg = anlik_df.groupby('magaza_kod').agg({
                    'stok': 'sum',
                    'satis': 'sum'
                }).reset_index()
                magaza_agg['magaza_stok_satis'] = magaza_agg['stok'] / magaza_agg['satis'].replace(0, 1)
                
                # Ürün segment ataması
                urun_agg['urun_segment'] = pd.cut(
                    urun_agg['urun_stok_satis'],
                    bins=[r[0] for r in product_ranges] + [product_ranges[-1][1]],
                    labels=cover_segments_sorted,
                    include_lowest=True
                ).astype(str)
                
                # Mağaza segment ataması
                magaza_agg['magaza_segment'] = pd.cut(
                    magaza_agg['magaza_stok_satis'],
                    bins=[r[0] for r in store_ranges] + [store_ranges[-1][1]],
                    labels=store_segments_sorted,
                    include_lowest=True
                ).astype(str)
                
                # Ana dataframe'e segment bilgilerini ekle
                df = df.merge(
                    urun_agg[['urun_kod', 'urun_segment']],
                    on='urun_kod',
                    how='left'
                )
                df['urun_segment'] = df['urun_segment'].fillna('0-4')
                
                df = df.merge(
                    magaza_agg[['magaza_kod', 'magaza_segment']],
                    on='magaza_kod',
                    how='left'
                )
                df['magaza_segment'] = df['magaza_segment'].fillna('0-4')
                
                # Genleştirme katsayısını matristen al
                if isinstance(cover_matrix, pd.DataFrame) and len(cover_matrix.columns) > 1:
                    matrix_long = cover_matrix.stack().reset_index()
                    matrix_long.columns = ['urun_segment', 'magaza_segment', 'genlestirme_katsayisi']
                    matrix_long['urun_segment'] = matrix_long['urun_segment'].astype(str)
                    matrix_long['magaza_segment'] = matrix_long['magaza_segment'].astype(str)
                    
                    df = df.merge(
                        matrix_long,
                        on=['urun_segment', 'magaza_segment'],
                        how='left'
                    )
                    df['genlestirme_katsayisi'] = df['genlestirme_katsayisi'].fillna(1.0)
                else:
                    df['genlestirme_katsayisi'] = 1.0
                
                st.write(f"✅ Genleştirme katsayıları eklendi")
                
                # 7-8. DEPO-ÜRÜN BAZINDA GRUPLA VE PO HESAPLA
                st.info("📊 Depo-Ürün bazında gruplama ve PO hesaplama...")
                
                # SMM bilgisini kontrol et
                if 'smm' not in df.columns:
                    df['smm'] = 0
                
                # Önce depo-ürün bazında topla
                po_sonuc = df.groupby(['depo_kod', 'urun_kod']).agg({
                    'satis': 'sum',
                    'stok': 'sum',
                    'yol': 'sum',
                    'depo_stok': 'first',
                    'min_deger': 'first',
                    'acik_siparis': 'sum',
                    'forward_cover_final': 'first',
                    'genlestirme_katsayisi': 'first',
                    'smm': 'first',
                    'magaza_kod': 'nunique'
                }).reset_index()
                
                po_sonuc.columns = [
                    'depo_kod', 'urun_kod', 'toplam_satis', 'toplam_magaza_stok', 
                    'toplam_yol', 'depo_stok', 'min_deger', 'toplam_acik_siparis',
                    'forward_cover', 'genlestirme', 'smm', 'magaza_sayisi'
                ]
                
                # Brüt ihtiyaç (TOPLAM bazında)
                po_sonuc['brut_ihtiyac'] = (
                    (po_sonuc['forward_cover'] + fc_ek) * 
                    po_sonuc['toplam_satis'] * 
                    po_sonuc['genlestirme']
                )
                
                # Net ihtiyaç = Brüt - Mağaza Stok - Yol - Depo Stok - Açık Sipariş
                po_sonuc['net_ihtiyac'] = (
                    po_sonuc['brut_ihtiyac'] - 
                    po_sonuc['toplam_magaza_stok'] - 
                    po_sonuc['toplam_yol'] - 
                    po_sonuc['depo_stok'] - 
                    po_sonuc['toplam_acik_siparis']
                )
                
                # Min kontrolü (toplam mağaza stoku < min ise)
                po_sonuc['min_ihtiyac'] = np.where(
                    po_sonuc['min_deger'] > po_sonuc['toplam_magaza_stok'],
                    po_sonuc['min_deger'] - po_sonuc['toplam_magaza_stok'],
                    0
                )
                
                # PO ihtiyacı
                po_sonuc['po_ihtiyac'] = np.maximum(po_sonuc['net_ihtiyac'], po_sonuc['min_ihtiyac'])
                po_sonuc['po_ihtiyac'] = po_sonuc['po_ihtiyac'].clip(lower=0)
                
                st.write(f"✅ PO ihtiyacı hesaplandı: {len(po_sonuc):,} depo-ürün kombinasyonu")
                
                # DEPO STOK EŞİĞİ KONTROLÜ
                yuksek_stok_sayisi = (po_sonuc['depo_stok'] > depo_stok_threshold).sum()
                po_sonuc.loc[po_sonuc['depo_stok'] > depo_stok_threshold, 'po_ihtiyac'] = 0
                
                if yuksek_stok_sayisi > 0:
                    st.info(f"ℹ️ {yuksek_stok_sayisi:,} üründe depo stok > {depo_stok_threshold}, PO sıfırlandı")
                
                po_sonuc_pozitif = po_sonuc[po_sonuc['po_ihtiyac'] > 0].copy()
                
                for col in ['po_ihtiyac', 'brut_ihtiyac', 'net_ihtiyac', 'toplam_satis', 'toplam_magaza_stok', 'toplam_yol', 'depo_stok', 'toplam_acik_siparis']:
                    if col in po_sonuc_pozitif.columns:
                        po_sonuc_pozitif[col] = po_sonuc_pozitif[col].round().astype(int)
                
                end_time = time.time()
                
                # 9. KAYDET
                st.session_state.alim_siparis_sonuc = po_sonuc_pozitif.copy()
                
                st.success(f"✅ Hesaplama tamamlandı!")
                st.balloons()
                
                # ============================================
                # 📊 ÖZET METRİKLER TABLOSU
                # ============================================
                st.markdown("---")
                st.subheader("📊 Hesaplama Özet Metrikleri")
                
                # PO Tutarı hesapla (PO Adet × SMM)
                if 'smm' in po_sonuc_pozitif.columns:
                    po_sonuc_pozitif['po_tutar'] = po_sonuc_pozitif['po_ihtiyac'] * po_sonuc_pozitif['smm']
                    toplam_po_tutar = po_sonuc_pozitif['po_tutar'].sum()
                else:
                    toplam_po_tutar = 0
                
                # SMM bilgisini ana veri setinden al (tüm sistem için)
                if 'smm' in po_sonuc.columns:
                    po_sonuc['magaza_stok_tutar'] = po_sonuc['toplam_magaza_stok'] * po_sonuc['smm']
                    po_sonuc['depo_stok_tutar'] = po_sonuc['depo_stok'] * po_sonuc['smm']
                    po_sonuc['yol_tutar'] = po_sonuc['toplam_yol'] * po_sonuc['smm']
                    po_sonuc['acik_siparis_tutar'] = po_sonuc['toplam_acik_siparis'] * po_sonuc['smm']
                    po_sonuc['satis_tutar'] = po_sonuc['toplam_satis'] * po_sonuc['smm']
                    
                    # Tüm sistem tutarları
                    toplam_magaza_stok_tutar = po_sonuc['magaza_stok_tutar'].sum()
                    toplam_depo_stok_tutar = po_sonuc['depo_stok_tutar'].sum()
                    toplam_yol_tutar = po_sonuc['yol_tutar'].sum()
                    toplam_acik_sip_tutar = po_sonuc['acik_siparis_tutar'].sum()
                    toplam_satis_tutar = po_sonuc['satis_tutar'].sum()
                else:
                    toplam_magaza_stok_tutar = 0
                    toplam_depo_stok_tutar = 0
                    toplam_yol_tutar = 0
                    toplam_acik_sip_tutar = 0
                    toplam_satis_tutar = 0
                
                # Metrikleri hesapla - TÜM SİSTEM
                algoritma_suresi = end_time - start_time
                toplam_po_adet = po_sonuc_pozitif['po_ihtiyac'].sum()
                
                toplam_magaza_stok_sistem = po_sonuc['toplam_magaza_stok'].sum()
                toplam_depo_stok_sistem = po_sonuc['depo_stok'].sum()
                toplam_yol_sistem = po_sonuc['toplam_yol'].sum()
                toplam_acik_sip_sistem = po_sonuc['toplam_acik_siparis'].sum()
                toplam_satis_sistem = po_sonuc['toplam_satis'].sum()
                urun_sayisi_sistem = po_sonuc['urun_kod'].nunique()
                
                # PO Hesaplananlar
                urun_sayisi_po = po_sonuc_pozitif['urun_kod'].nunique()
                depo_sayisi = po_sonuc_pozitif['depo_kod'].nunique()
                
                # Özet tablosu oluştur - ADET ve TUTAR kolonları
                ozet_data = {
                    'Metrik': [
                        '📦 PO İhtiyacı',
                        '🏪 Mağaza Stok (Tüm Sistem)',
                        '🏭 Depo Stok (Tüm Sistem)',
                        '🚚 Yol (Tüm Sistem)',
                        '📋 Açık Sipariş (Tüm Sistem)',
                        '💵 Satış / Ciro (Tüm Sistem)',
                        '🏷️ Ürün Sayısı (Tüm Sistem)',
                        '🏷️ Ürün Sayısı (PO Hesaplanan)',
                        '🏪 Depo Sayısı',
                        '📊 Depo-Ürün Kombinasyonu',
                        '⏱️ Algoritma Süresi'
                    ],
                    'Adet': [
                        f"{toplam_po_adet:,.0f}",
                        f"{toplam_magaza_stok_sistem:,.0f}",
                        f"{toplam_depo_stok_sistem:,.0f}",
                        f"{toplam_yol_sistem:,.0f}",
                        f"{toplam_acik_sip_sistem:,.0f}",
                        f"{toplam_satis_sistem:,.0f}",
                        f"{urun_sayisi_sistem:,}",
                        f"{urun_sayisi_po:,}",
                        f"{depo_sayisi}",
                        f"{len(po_sonuc_pozitif):,}",
                        f"{algoritma_suresi:.2f} sn"
                    ],
                    'Tutar (₺)': [
                        f"{toplam_po_tutar:,.2f}",
                        f"{toplam_magaza_stok_tutar:,.2f}",
                        f"{toplam_depo_stok_tutar:,.2f}",
                        f"{toplam_yol_tutar:,.2f}",
                        f"{toplam_acik_sip_tutar:,.2f}",
                        f"{toplam_satis_tutar:,.2f}",
                        "-",
                        "-",
                        "-",
                        "-",
                        "-"
                    ]
                }
                
                ozet_df = pd.DataFrame(ozet_data)
                
                # Tabloyu göster
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.dataframe(
                        ozet_df,
                        use_container_width=True,
                        hide_index=True,
                        height=450
                    )
                
                with col2:
                    st.metric(
                        "🎯 Toplam PO Adet", 
                        f"{toplam_po_adet:,.0f}"
                    )
                    
                    st.metric(
                        "💰 Toplam PO Tutar", 
                        f"₺{toplam_po_tutar:,.0f}"
                    )
                    
                    st.metric(
                        "⚡ İşlem Süresi", 
                        f"{algoritma_suresi:.2f} sn"
                    )
                    
                    toplam_stok_sistemi = toplam_magaza_stok_sistem + toplam_yol_sistem + toplam_depo_stok_sistem
                    st.metric(
                        "💼 Toplam Sistem Stok",
                        f"{toplam_stok_sistemi:,.0f}"
                    )
                    
                    # PO oranı
                    if urun_sayisi_sistem > 0:
                        po_oran = (urun_sayisi_po / urun_sayisi_sistem) * 100
                        st.metric(
                            "📊 PO Gereken Ürün Oranı",
                            f"%{po_oran:.1f}"
                        )
                
                st.markdown("---")
                
                # DEPO BAZINDA ÖZET
                st.subheader("🏪 Depo Bazında Özet")
                
                depo_ozet = po_sonuc_pozitif.groupby('depo_kod').agg({
                    'po_ihtiyac': 'sum',
                    'urun_kod': 'nunique'
                }).reset_index()
                
                if 'po_tutar' in po_sonuc_pozitif.columns:
                    depo_tutar = po_sonuc_pozitif.groupby('depo_kod')['po_tutar'].sum().reset_index()
                    depo_ozet = depo_ozet.merge(depo_tutar, on='depo_kod', how='left')
                    depo_ozet.columns = ['Depo Kodu', 'Toplam PO Adet', 'Ürün Sayısı', 'Toplam PO Tutar']
                else:
                    depo_ozet.columns = ['Depo Kodu', 'Toplam PO Adet', 'Ürün Sayısı']
                
                depo_ozet = depo_ozet.sort_values('Toplam PO Adet', ascending=False)
                
                st.dataframe(depo_ozet, use_container_width=True, hide_index=True)
                
                # DETAY TABLO
                st.markdown("---")
                st.subheader("📋 PO Detayı (Top 1000)")
                
                display_df = po_sonuc_pozitif.sort_values('po_ihtiyac', ascending=False).head(1000)
                st.dataframe(display_df, use_container_width=True, height=400)
                
                # EXPORT
                st.markdown("---")
                col1, col2 = st.columns(2)
                
                with col1:
                    csv_data = po_sonuc_pozitif.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Tüm PO İndir (CSV)",
                        data=csv_data,
                        file_name=f"po_ihtiyac_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    ozet_csv = depo_ozet.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Depo Özeti İndir (CSV)",
                        data=ozet_csv,
                        file_name=f"po_depo_ozet_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        except Exception as e:
            st.error(f"❌ Hata: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

# ============================================
# 📊 ALIM SİPARİŞ RAPORLARI
# ============================================
                    
# ============================================
# 📊 ALIM SİPARİŞ RAPORLARI
# ============================================

# ============================================
# 📊 PO RAPORLARI
# ============================================
elif menu == "📊 PO Raporları":
    st.title("📊 Alım Sipariş Raporları")
    st.markdown("---")
    
    if st.session_state.alim_siparis_sonuc is None:
        st.warning("⚠️ Henüz alım sipariş hesaplaması yapılmadı!")
        st.info("Lütfen önce 'Alım Sipariş Hesaplama' menüsünden hesaplama yapın.")
        st.stop()
    
    sonuc_df = st.session_state.alim_siparis_sonuc.copy()
    
    # PO ihtiyacı kolonu
    if 'po_ihtiyac' in sonuc_df.columns:
        alim_column = 'po_ihtiyac'
    elif 'alim_siparis_final' in sonuc_df.columns:
        alim_column = 'alim_siparis_final'
    else:
        alim_column = 'alim_siparis'
    
    # Sadece alım > 0 olanlar
    alim_df = sonuc_df[sonuc_df[alim_column] > 0].copy()
    
    if len(alim_df) == 0:
        st.info("ℹ️ Alım sipariş ihtiyacı olan ürün bulunamadı.")
        st.stop()
    
    # Genel özet
    st.subheader("📈 Genel Özet")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Toplam PO", f"{alim_df[alim_column].sum():,.0f}")
    
    with col2:
        st.metric("🏷️ Ürün Sayısı", f"{alim_df['urun_kod'].nunique()}")
    
    with col3:
        if 'depo_kod' in alim_df.columns:
            st.metric("🏪 Depo Sayısı", f"{alim_df['depo_kod'].nunique()}")
    
    with col4:
        if 'toplam_acik_siparis' in alim_df.columns:
            acik_dusülen = alim_df['toplam_acik_siparis'].sum()
            st.metric("📋 Açık Sipariş Düşüldü", f"{acik_dusülen:,.0f}")
    
    st.markdown("---")
    
    # Tab'lar
    tab1, tab2, tab3 = st.tabs(["🏪 Depo Analizi", "📊 Detay Tablo", "📈 Özet İstatistikler"])
    
    # DEPO ANALİZİ
    with tab1:
        st.subheader("🏪 Depo Bazında Analiz")
        
        if 'depo_kod' in alim_df.columns:
            depo_analiz = alim_df.groupby('depo_kod').agg({
                alim_column: 'sum',
                'urun_kod': 'nunique',
                'toplam_satis': 'sum',
                'toplam_magaza_stok': 'sum',
                'depo_stok': 'sum'
            }).reset_index()
            
            depo_analiz.columns = ['Depo Kodu', 'Toplam PO', 'Ürün Sayısı', 'Toplam Satış', 'Mağaza Stok', 'Depo Stok']
            depo_analiz = depo_analiz.sort_values('Toplam PO', ascending=False)
            
            st.dataframe(
                depo_analiz.style.format({
                    'Toplam PO': '{:,.0f}',
                    'Ürün Sayısı': '{:.0f}',
                    'Toplam Satış': '{:,.0f}',
                    'Mağaza Stok': '{:,.0f}',
                    'Depo Stok': '{:,.0f}'
                }),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("ℹ️ Depo bilgisi bulunamadı")
    
    # DETAY TABLO
    with tab2:
        st.subheader("📋 PO Detay Tablosu")
        
        display_cols = ['depo_kod', 'urun_kod', alim_column, 'toplam_satis', 
                       'toplam_magaza_stok', 'toplam_yol', 'depo_stok']
        
        if 'toplam_acik_siparis' in alim_df.columns:
            display_cols.append('toplam_acik_siparis')
        
        if 'magaza_sayisi' in alim_df.columns:
            display_cols.append('magaza_sayisi')
        
        # Sadece mevcut kolonları al
        display_cols = [col for col in display_cols if col in alim_df.columns]
        
        display_df = alim_df[display_cols].sort_values(alim_column, ascending=False)
        
        st.dataframe(
            display_df.style.format({
                alim_column: '{:,.0f}',
                'toplam_satis': '{:,.0f}',
                'toplam_magaza_stok': '{:,.0f}',
                'toplam_yol': '{:,.0f}',
                'depo_stok': '{:,.0f}',
                'toplam_acik_siparis': '{:,.0f}',
                'magaza_sayisi': '{:.0f}'
            }),
            use_container_width=True,
            height=500
        )
    
    # ÖZET İSTATİSTİKLER
    with tab3:
        st.subheader("📈 Özet İstatistikler")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**PO İhtiyacı Dağılımı:**")
            st.write(f"- Ortalama: {alim_df[alim_column].mean():,.0f}")
            st.write(f"- Medyan: {alim_df[alim_column].median():,.0f}")
            st.write(f"- Min: {alim_df[alim_column].min():,.0f}")
            st.write(f"- Max: {alim_df[alim_column].max():,.0f}")
        
        with col2:
            st.write("**Stok Durumu:**")
            if 'toplam_magaza_stok' in alim_df.columns:
                st.write(f"- Toplam Mağaza Stok: {alim_df['toplam_magaza_stok'].sum():,.0f}")
            if 'depo_stok' in alim_df.columns:
                st.write(f"- Toplam Depo Stok: {alim_df['depo_stok'].sum():,.0f}")
            if 'toplam_yol' in alim_df.columns:
                st.write(f"- Toplam Yol: {alim_df['toplam_yol'].sum():,.0f}")
    
    # Export
    st.markdown("---")
    csv_data = alim_df.to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        label="📥 Tüm Veriyi İndir (CSV)",
        data=csv_data,
        file_name=f"po_rapor_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )
# ============================================
# 📦 DEPO BAZLI SİPARİŞ
# ============================================

# ============================================
# 📦 DEPO BAZLI PO
# ============================================
elif menu == "📦 Depo Bazlı PO":
    st.title("📦 Depo Bazlı Sipariş Listeleri")
    st.markdown("---")
    
    if st.session_state.alim_siparis_sonuc is None:
        st.warning("⚠️ Henüz alım sipariş hesaplaması yapılmadı!")
        st.info("Lütfen önce 'Alım Sipariş Hesaplama' menüsünden hesaplama yapın.")
        st.stop()
    
    sonuc_df = st.session_state.alim_siparis_sonuc.copy()
    
    # PO ihtiyacı kolonu
    if 'po_ihtiyac' in sonuc_df.columns:
        alim_column = 'po_ihtiyac'
    elif 'alim_siparis_final' in sonuc_df.columns:
        alim_column = 'alim_siparis_final'
    else:
        alim_column = 'alim_siparis'
    
    # Pozitif alımları filtrele
    alim_df = sonuc_df[sonuc_df[alim_column] > 0].copy()
    
    if len(alim_df) == 0:
        st.info("ℹ️ Alım sipariş ihtiyacı olan ürün bulunamadı.")
        st.stop()
    
    # Depo kodu yoksa default ata
    if 'depo_kod' not in alim_df.columns:
        alim_df['depo_kod'] = 'D001'
        st.info("ℹ️ Depo kodu bulunamadı, tüm siparişler D001 olarak gösteriliyor")
    
    # Depo seçimi
    depo_listesi = sorted(alim_df['depo_kod'].dropna().unique())
    
    col1, col2 = st.columns([2, 3])
    with col1:
        selected_depo = st.selectbox(
            "📍 Depo Seçin",
            options=['Tümü'] + list(depo_listesi),
            key="depo_select"
        )
    
    # Seçili depoya göre filtrele
    if selected_depo != 'Tümü':
        display_df = alim_df[alim_df['depo_kod'] == selected_depo].copy()
        st.subheader(f"📦 {selected_depo} Deposu Sipariş Listesi")
    else:
        display_df = alim_df.copy()
        st.subheader("📦 Tüm Depolar Sipariş Listesi")
    
    # Özet metrikler
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        toplam_adet = display_df[alim_column].sum()
        st.metric("📦 Toplam PO", f"{toplam_adet:,.0f}")
    
    with col2:
        urun_sayisi = display_df['urun_kod'].nunique()
        st.metric("🏷️ Ürün Sayısı", f"{urun_sayisi}")
    
    with col3:
        if 'toplam_satis' in display_df.columns:
            toplam_satis = display_df['toplam_satis'].sum()
            st.metric("💰 Toplam Satış", f"{toplam_satis:,.0f}")
    
    with col4:
        if 'magaza_sayisi' in display_df.columns:
            toplam_magaza = display_df['magaza_sayisi'].sum()
            st.metric("🏪 Mağaza-Ürün", f"{toplam_magaza:,}")
    
    st.markdown("---")
    
    # Detaylı tablo
    st.subheader("📋 Sipariş Detayı")
    
    # Gösterilecek sütunları belirle
    display_cols = ['urun_kod', alim_column, 'toplam_satis', 'toplam_magaza_stok', 
                   'toplam_yol', 'depo_stok']
    
    if 'toplam_acik_siparis' in display_df.columns:
        display_cols.append('toplam_acik_siparis')
    
    if 'magaza_sayisi' in display_df.columns:
        display_cols.append('magaza_sayisi')
    
    if 'depo_kod' in display_df.columns and selected_depo == 'Tümü':
        display_cols.insert(0, 'depo_kod')
    
    # Sadece mevcut sütunları göster
    display_cols = [col for col in display_cols if col in display_df.columns]
    
    final_df = display_df[display_cols].sort_values(alim_column, ascending=False)
    
    # Sütun isimlerini düzenle
    column_rename = {
        'depo_kod': 'Depo',
        'urun_kod': 'Ürün Kodu',
        alim_column: 'PO İhtiyacı',
        'toplam_satis': 'Toplam Satış',
        'toplam_magaza_stok': 'Mağaza Stok',
        'toplam_yol': 'Yol',
        'depo_stok': 'Depo Stok',
        'toplam_acik_siparis': 'Açık Sipariş',
        'magaza_sayisi': 'Mağaza Sayısı'
    }
    
    final_df = final_df.rename(columns=column_rename)
    
    # Formatla ve göster
    format_dict = {
        'PO İhtiyacı': '{:,.0f}',
        'Toplam Satış': '{:,.0f}',
        'Mağaza Stok': '{:,.0f}',
        'Yol': '{:,.0f}',
        'Depo Stok': '{:,.0f}',
        'Açık Sipariş': '{:,.0f}',
        'Mağaza Sayısı': '{:.0f}'
    }
    
    # Sadece mevcut sütunları formatla
    format_dict = {k: v for k, v in format_dict.items() if k in final_df.columns}
    
    st.dataframe(
        final_df.style.format(format_dict),
        use_container_width=True,
        height=500
    )
    
    # Export
    st.markdown("---")
    st.subheader("📥 Dışa Aktar")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mevcut görünümü indir
        csv_data = final_df.to_csv(index=False, encoding='utf-8-sig')
        filename = f"po_siparis_{selected_depo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        
        st.download_button(
            label="📥 Bu Listeyi İndir (CSV)",
            data=csv_data,
            file_name=filename,
            mime="text/csv",
            use_container_width=True
        )
    
    with col2:
        # Tüm depoları indir
        if selected_depo != 'Tümü':
            tum_csv = alim_df.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Tüm Depolar (CSV)",
                data=tum_csv,
                file_name=f"po_tum_depolar_{pd.Timestamp.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
