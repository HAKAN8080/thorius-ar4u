import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import hashlib

st.set_page_config(page_title="Depo Birleştirme - Proje Yönetimi", layout="wide", page_icon="📦")

# ==============================================
# KULLANICI YETKİLENDİRME SİSTEMİ
# ==============================================

# ==============================================
# TOKEN YÖNETİMİ - SABITLER
# ==============================================

# OMS Projesi için token maliyeti
MODULE_TOKEN_COST = 1  # Her giriş için 1 token

# Kullanıcı veritabanı (şifreler SHA256 ile hash'lenmiş)
USERS = {
    "ertugrul": {
        "password": hashlib.sha256("lojistik2025".encode()).hexdigest(),
        "role": "sponsor",
        "name": "Ertuğrul Bey",
        "title": "Lojistik GMY",
        "initial_tokens": 100
    },
    "gokhan": {
        "password": hashlib.sha256("ecom2025".encode()).hexdigest(),
        "role": "sponsor",
        "name": "Gökhan Bey",
        "title": "ECOM GMY",
        "initial_tokens": 100
    },
    "volkan": {
        "password": hashlib.sha256("magaza2025".encode()).hexdigest(),
        "role": "manager",
        "name": "Volkan Bey",
        "title": "Mağazacılık GMY",
        "initial_tokens": 100
    },
    "ferhat": {
        "password": hashlib.sha256("stok2025".encode()).hexdigest(),
        "role": "manager",
        "name": "Ferhat Bey",
        "title": "Stok Yönetimi Direktörü",
        "initial_tokens": 100
    },
    "tayfun": {
        "password": hashlib.sha256("eve2025".encode()).hexdigest(),
        "role": "manager",
        "name": "Tayfun Bey",
        "title": "EVE GM",
        "initial_tokens": 100
    },
    "aliakcay": {
        "password": hashlib.sha256("tzy2025".encode()).hexdigest(),
        "role": "user",
        "name": "Ali Akçay",
        "title": "EVE TZY Direktörü",
        "initial_tokens": 100
    },
    "ozcan": {
        "password": hashlib.sha256("it2025".encode()).hexdigest(),
        "role": "admin",
        "name": "Özcan Bey",
        "title": "IT GMY",
        "initial_tokens": 100
    },
    "demo": {
        "password": hashlib.sha256("demo2025".encode()).hexdigest(),
        "role": "viewer",
        "name": "Demo Kullanıcı",
        "title": "Misafir",
        "initial_tokens": 100
    }
}

# ==============================================
# TOKEN YÖNETİM FONKSİYONLARI
# ==============================================

def init_token_system():
    """Token sistemini başlat"""
    if "token_data" not in st.session_state:
        st.session_state.token_data = {}
    
    # Kullanıcının token bilgilerini yükle
    username = st.session_state.get("username")
    if username and username not in st.session_state.token_data:
        st.session_state.token_data[username] = {
            "remaining_tokens": USERS[username]["initial_tokens"],
            "total_tokens": USERS[username]["initial_tokens"],
            "last_login": None,
            "last_login_date": None,
            "login_count_today": 0,
            "tokens_used_today": 0
        }

def check_token_charge():
    """Token düşürme kararı - 6 saat kuralı"""
    username = st.session_state.username
    now = datetime.now()
    
    token_info = st.session_state.token_data[username]
    last_login = token_info["last_login"]
    last_date = token_info["last_login_date"]
    
    # İlk giriş
    if last_login is None:
        return True
    
    # Bugünün tarihi
    today = now.date()
    
    # Yeni gün mü?
    if last_date != today:
        # Gün değişti, token düşecek
        token_info["login_count_today"] = 0
        token_info["tokens_used_today"] = 0
        return True
    
    # Aynı gün içinde - 6 saat kontrolü
    hours_since_login = (now - last_login).total_seconds() / 3600
    
    if hours_since_login >= 6:
        # 6 saat geçmiş, token düşer
        return True
    
    # 6 saat dolmamış, token düşmez
    return False

def charge_token():
    """Token düş"""
    username = st.session_state.username
    now = datetime.now()
    
    token_info = st.session_state.token_data[username]
    
    # Token düş
    if token_info["remaining_tokens"] > 0:
        token_info["remaining_tokens"] -= MODULE_TOKEN_COST
        token_info["tokens_used_today"] += MODULE_TOKEN_COST
        token_info["login_count_today"] += 1
        token_info["last_login"] = now
        token_info["last_login_date"] = now.date()
        return True
    else:
        return False

def get_token_balance():
    """Token bakiyesini getir"""
    username = st.session_state.username
    return st.session_state.token_data[username]["remaining_tokens"]

def get_token_usage_percent():
    """Token kullanım yüzdesini hesapla"""
    username = st.session_state.username
    token_info = st.session_state.token_data[username]
    used = token_info["total_tokens"] - token_info["remaining_tokens"]
    return int((used / token_info["total_tokens"]) * 100)

def check_password():
    """Kullanıcı girişi kontrolü"""
    
    # Session state başlat
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.username = None
        st.session_state.user_info = None
    
    # Zaten giriş yaptıysa
    if st.session_state.authenticated:
        return True
    
    # Login ekranı CSS
    st.markdown("""
    <style>
    .login-header {
        text-align: center;
        padding: 40px 0 30px;
    }
    .login-title {
        font-size: 2.5rem;
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
    
    # Login header
    st.markdown("""
    <div class="login-header">
        <div style="font-size: 4rem; margin-bottom: 20px;">📦</div>
        <div class="login-title">OMS Depo Birleştirme Projesi</div>
        <div class="login-subtitle">Proje Yönetim Sistemi - Token Based</div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 1.5, 1])
    
    with col2:
        st.markdown("### 🔐 GİRİŞ YAP")
        st.markdown("---")
        
        username = st.text_input("👤 Kullanıcı Adı", placeholder="örn: ertugrul", key="username_input")
        password = st.text_input("🔑 Şifre", type="password", placeholder="Şifrenizi girin", key="password_input")
        
        st.markdown("")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🚀 Giriş Yap", use_container_width=True, type="primary"):
                if username.lower() in USERS:
                    password_hash = hashlib.sha256(password.encode()).hexdigest()
                    if password_hash == USERS[username.lower()]["password"]:
                        st.session_state.authenticated = True
                        st.session_state.username = username.lower()
                        st.session_state.user_info = USERS[username.lower()]
                        
                        # Token sistemini başlat
                        init_token_system()
                        
                        st.success(f"✅ Hoş geldiniz, {USERS[username.lower()]['name']}!")
                        st.info(f"🪙 {USERS[username.lower()]['initial_tokens']} token bakiyeniz bulunmaktadır.")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Hatalı şifre!")
                else:
                    st.error("❌ Kullanıcı bulunamadı!")
        
        with col_b:
            if st.button("🔄 Temizle", use_container_width=True):
                st.rerun()
        
        st.markdown("---")
        st.markdown("#### 👥 Demo Hesaplar")
        
        with st.expander("📋 Kullanıcı Listesi"):
            demo_users = pd.DataFrame([
                {"👤 Kullanıcı": "ertugrul", "🔑 Şifre": "lojistik2025", "👔 Rol": "Sponsor", "🪙 Token": "100"},
                {"👤 Kullanıcı": "gokhan", "🔑 Şifre": "ecom2025", "👔 Rol": "Sponsor", "🪙 Token": "100"},
                {"👤 Kullanıcı": "volkan", "🔑 Şifre": "magaza2025", "👔 Rol": "Manager", "🪙 Token": "100"},
                {"👤 Kullanıcı": "demo", "🔑 Şifre": "demo2025", "👔 Rol": "Viewer", "🪙 Token": "100"},
            ])
            st.dataframe(demo_users, hide_index=True, use_container_width=True)
        
        st.markdown("---")
        st.markdown("##### 💡 Token Sistemi")
        st.caption("• Her kullanıcıya 100 token verilir")
        st.caption("• Her giriş 1 token harcar")
        st.caption("• Aynı gün içinde < 6 saat: Token düşmez ✅")
        st.caption("• Aynı gün içinde > 6 saat: Token düşer ⚠️")
        st.caption("• Gece 00:00'da otomatik çıkış yapılır")
        st.caption("💡 Giriş sorunları için IT'ye başvurun.")
    
    return False

def logout():
    """Çıkış yap"""
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.user_info = None
    st.rerun()

# ==============================================
# AUTHENTICATION KONTROL
# ==============================================

if not check_password():
    st.stop()

# Token sistemini başlat
init_token_system()

# Token kontrolü yap
should_charge = check_token_charge()

if should_charge:
    # Token düşür
    if not charge_token():
        st.error("❌ Token bakiyeniz tükendi! Lütfen sistem yöneticisi ile iletişime geçin.")
        st.stop()
    else:
        remaining = get_token_balance()
        if remaining <= 10:
            st.warning(f"⚠️ Token bakiyeniz azalıyor! Kalan: {remaining} token")

# ==============================================
# KULLANICI BİLGİLERİ SIDEBAR
# ==============================================

with st.sidebar:
    # Kullanıcı profil kartı
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
    username = st.session_state.username
    token_info = st.session_state.token_data[username]
    remaining = token_info["remaining_tokens"]
    total = token_info["total_tokens"]
    used = total - remaining
    usage_percent = get_token_usage_percent()
    
    # Token progress bar rengi
    if usage_percent < 50:
        bar_color = "#00ff88"  # Yeşil
    elif usage_percent < 75:
        bar_color = "#ffa500"  # Turuncu
    else:
        bar_color = "#ff4444"  # Kırmızı
    
    st.markdown(f"""
    <div style='padding: 15px; background: rgba(255,255,255,0.05); border-radius: 10px; margin-bottom: 15px;'>
        <div style='text-align: center; margin-bottom: 10px;'>
            <div style='font-size: 0.9rem; color: #999; margin-bottom: 5px;'>🪙 Token Bakiyesi</div>
            <div style='font-size: 2rem; font-weight: 700; color: {bar_color};'>{remaining}</div>
            <div style='font-size: 0.8rem; color: #666;'>/ {total} token</div>
        </div>
        <div style='background: rgba(255,255,255,0.1); border-radius: 10px; height: 10px; overflow: hidden;'>
            <div style='background: {bar_color}; height: 100%; width: {100-usage_percent}%; transition: width 0.3s;'></div>
        </div>
        <div style='text-align: center; margin-top: 8px; font-size: 0.75rem; color: #888;'>
            Kullanılan: {used} token (%{usage_percent})
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Token bilgileri
    st.markdown("##### 📊 Bugünkü Kullanım")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Giriş Sayısı", token_info["login_count_today"])
    with col2:
        st.metric("Harcanan Token", token_info["tokens_used_today"])
    
    if token_info["last_login"]:
        time_since = datetime.now() - token_info["last_login"]
        hours = int(time_since.total_seconds() / 3600)
        minutes = int((time_since.total_seconds() % 3600) / 60)
        
        st.caption(f"🕐 Son giriş: {hours}s {minutes}dk önce")
        
        if hours < 6:
            remaining_hours = 6 - hours
            st.info(f"⏱️ {remaining_hours} saat içinde token düşmeyecek")
    
    st.markdown("---")
    
    if st.button("🚪 Çıkış Yap", use_container_width=True):
        logout()
    
    st.markdown("---")

# ==============================================
# ANA UYGULAMA BAŞLANGIÇ
# ==============================================

# Session state'de proje verilerini sakla
if 'proje_verileri' not in st.session_state:
    st.session_state.proje_verileri = {
        "FAZ 0: ANALİZ": {
            "baslangic": 0, "sure": 3, "renk": "🔴", "durum": "Planlandı",
            "gorevler": [
                {"id": "0.1", "gorev": "EVE Ürün Portföyü Analizi", "aciklama": "Hangi ürünler paketlenebilir?", 
                 "sure": 1, "baslangic_hafta": 1, "sorumlu": "Ertuğrul + Gökhan + Tayfun", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "0.2", "gorev": "Paket Tipi Belirleme", "aciklama": "Display box tipleri", 
                 "sure": 1, "baslangic_hafta": 2, "sorumlu": "Ertuğrul + Gökhan + Ali Akçay", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "0.3", "gorev": "Ürün Sınıflandırma", "aciklama": "Palet/Koli/Açık adet", 
                 "sure": 1, "baslangic_hafta": 2, "sorumlu": "Ertuğrul + Gökhan + Ferhat", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "0.4", "gorev": "Maliyet Analizi", "aciklama": "Mevcut maliyetler", 
                 "sure": 1, "baslangic_hafta": 3, "sorumlu": "Finans + Ertuğrul + Gökhan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "0.5", "gorev": "ROI Analizi", "aciklama": "Paketleme yatırımı", 
                 "sure": 1, "baslangic_hafta": 3, "sorumlu": "Finans + Ertuğrul + Gökhan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "0.6", "gorev": "Veri Toplama", "aciklama": "6 ay geçmiş veri", 
                 "sure": 2, "baslangic_hafta": 1, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "0.7", "gorev": "Kapasite Analizi", "aciklama": "Ana depo kapasite", 
                 "sure": 1, "baslangic_hafta": 3, "sorumlu": "Ertuğrul + Ferhat", "oncelik": "Orta", "durum": "Planlandı"}
            ]
        },
        "FAZ 1: SİSTEM": {
            "baslangic": 3, "sure": 6, "renk": "🟢", "durum": "Planlandı",
            "gorevler": [
                {"id": "1.1", "gorev": "Simülasyon Modülü", "aciklama": "Ne olurdu analizi", 
                 "sure": 2, "baslangic_hafta": 4, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "1.2", "gorev": "Koli Bozma Algoritması", "aciklama": "Otomatik hesaplama", 
                 "sure": 2, "baslangic_hafta": 4, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "1.3", "gorev": "Transfer Sistemi", "aciklama": "Açık adet transfer", 
                 "sure": 2, "baslangic_hafta": 6, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "1.4", "gorev": "Açık Adet Dashboard", "aciklama": "Görünürlük sistemi", 
                 "sure": 2, "baslangic_hafta": 6, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "1.5", "gorev": "Önceliklendirme", "aciklama": "FIFO/FEFO", 
                 "sure": 2, "baslangic_hafta": 8, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Orta", "durum": "Planlandı"},
                {"id": "1.6", "gorev": "Sevk Kural Motoru", "aciklama": "7 kural sistemi", 
                 "sure": 3, "baslangic_hafta": 6, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "1.7", "gorev": "Sevk Algoritması", "aciklama": "Otomatik öneri", 
                 "sure": 2, "baslangic_hafta": 8, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "1.8", "gorev": "Sevk Dashboard", "aciklama": "Manuel onay", 
                 "sure": 2, "baslangic_hafta": 8, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "1.9", "gorev": "Entegrasyon Test", "aciklama": "Tüm modüller", 
                 "sure": 1, "baslangic_hafta": 9, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"}
            ]
        },
        "FAZ 2: PİLOT": {
            "baslangic": 9, "sure": 15, "renk": "🔵", "durum": "Planlandı",
            "gorevler": [
                {"id": "2.1", "gorev": "Pilot Seçimi", "aciklama": "Kategoriler", 
                 "sure": 1, "baslangic_hafta": 10, "sorumlu": "Ertuğrul + Gökhan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "2.2", "gorev": "EVE Paketleme", "aciklama": "İlk parti", 
                 "sure": 2, "baslangic_hafta": 11, "sorumlu": "Tayfun + Ali Akçay", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "2.3", "gorev": "Stok Transferi", "aciklama": "Ana depoya", 
                 "sure": 1, "baslangic_hafta": 13, "sorumlu": "Ertuğrul + Ferhat", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "2.4", "gorev": "Pilot 1. Ay", "aciklama": "Canlı test", 
                 "sure": 4, "baslangic_hafta": 14, "sorumlu": "Ertuğrul + Gökhan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "2.5", "gorev": "Optimizasyon", "aciklama": "İyileştirmeler", 
                 "sure": 1, "baslangic_hafta": 18, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "2.6", "gorev": "Faz 2A Geçiş", "aciklama": "Orta hacim", 
                 "sure": 3, "baslangic_hafta": 19, "sorumlu": "Ertuğrul + Gökhan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "2.7", "gorev": "EVE %50", "aciklama": "Yaygınlaştırma", 
                 "sure": 6, "baslangic_hafta": 19, "sorumlu": "Tayfun + Ali Akçay", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "2.8", "gorev": "Tam Geçiş", "aciklama": "Tüm kategoriler", 
                 "sure": 2, "baslangic_hafta": 22, "sorumlu": "Ertuğrul + Gökhan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "2.9", "gorev": "Depo Kararı", "aciklama": "Kapat/Küçült", 
                 "sure": 1, "baslangic_hafta": 24, "sorumlu": "Yönetim", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "2.10", "gorev": "Depo Düzenleme", "aciklama": "Tasfiye", 
                 "sure": 1, "baslangic_hafta": 24, "sorumlu": "Ertuğrul", "oncelik": "Orta", "durum": "Planlandı"}
            ]
        },
        "FAZ 3: OMS MAĞAZA OPTİMİZASYONU": {
            "baslangic": 24, "sure": 12, "renk": "🟡", "durum": "Planlandı",
            "gorevler": [
                {"id": "3.1", "gorev": "Mevcut Mağaza Ağı Analizi", "aciklama": "Mağaza sayısı, dağılım, satış performansı analizi", 
                 "sure": 2, "baslangic_hafta": 25, "sorumlu": "Ertuğrul + Gökhan + Volkan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "3.2", "gorev": "Personel ve Kargo Maliyet Modelleme", "aciklama": "Mağaza başına personel maliyeti, kargo vs e-ticaret maliyet karşılaştırması", 
                 "sure": 2, "baslangic_hafta": 25, "sorumlu": "Ertuğrul + Gökhan + Finans", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "3.3", "gorev": "Matematiksel Optimizasyon Modeli", "aciklama": "Mağaza karlılığı, başabaş noktası, ROI hesaplamaları", 
                 "sure": 3, "baslangic_hafta": 27, "sorumlu": "Ertuğrul + Gökhan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "3.4", "gorev": "Bölge Bazlı Talep Analizi", "aciklama": "Hangi bölgelerde mağaza eksik? Pazar potansiyeli nedir?", 
                 "sure": 2, "baslangic_hafta": 27, "sorumlu": "Ertuğrul + Gökhan + Pazarlama", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "3.5", "gorev": "İstisna Mağaza Belirleme", "aciklama": "Hangi mağazalar stratejik? (Franchise, flagship, yüksek trafik)", 
                 "sure": 1, "baslangic_hafta": 29, "sorumlu": "Volkan + Ertuğrul + Gökhan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "3.6", "gorev": "Yeni Mağaza Açılış Senaryoları", "aciklama": "Kaç mağaza, hangi lokasyonlar, yatırım tutarları", 
                 "sure": 2, "baslangic_hafta": 30, "sorumlu": "Ertuğrul + Gökhan + Finans", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "3.7", "gorev": "ISO In-Store Ordering Ürün Segmentasyonu", "aciklama": "Hangi ürünler büyük/pahalı? ISO'ya yönlendirme kriterleri", 
                 "sure": 2, "baslangic_hafta": 30, "sorumlu": "Ertuğrul + Gökhan + Volkan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "3.8", "gorev": "ISO Teşvik Mekanizması Tasarımı", "aciklama": "Mağaza personeline indirim/komisyon, müşteriye özel fırsatlar", 
                 "sure": 2, "baslangic_hafta": 32, "sorumlu": "Volkan + Pazarlama + Finans", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "3.9", "gorev": "OMS Kural Motoru ISO Entegrasyonu", "aciklama": "Büyük ürünlerde otomatik ISO önerisi, stok yönlendirme", 
                 "sure": 2, "baslangic_hafta": 32, "sorumlu": "Ertuğrul + Gökhan + Özcan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "3.10", "gorev": "Mağazacılık ile El Sıkışma Toplantıları", "aciklama": "Veri paylaşımı, itirazlara matematiksel cevaplar, ortak karar", 
                 "sure": 2, "baslangic_hafta": 34, "sorumlu": "Yönetim + Ertuğrul + Gökhan + Volkan", "oncelik": "Kritik", "durum": "Planlandı"},
                {"id": "3.11", "gorev": "Mağaza Açılış Pilot Projesi", "aciklama": "Seçilen 2-3 lokasyonda pilot mağaza açılışı", 
                 "sure": 3, "baslangic_hafta": 34, "sorumlu": "Volkan", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "3.12", "gorev": "ISO Teşvik Pilotu", "aciklama": "Seçili mağazalarda ISO teşvik kampanyası, sonuç ölçümü", 
                 "sure": 2, "baslangic_hafta": 35, "sorumlu": "Volkan + Pazarlama", "oncelik": "Yüksek", "durum": "Planlandı"},
                {"id": "3.13", "gorev": "Sonuç Değerlendirme ve Strateji Finalizasyonu", "aciklama": "Pilot sonuçları, nihai mağaza sayısı kararı, ISO hedefleri", 
                 "sure": 1, "baslangic_hafta": 36, "sorumlu": "Yönetim + Tüm Ekip", "oncelik": "Kritik", "durum": "Planlandı"}
            ]
        }
    }

if 'baslangic_tarihi' not in st.session_state:
    st.session_state.baslangic_tarihi = datetime.now()

st.title("📦 DEPO BİRLEŞTİRME PROJESİ")
st.subheader("İnteraktif Proje Yönetim Sistemi")
st.markdown("---")

fazlar = st.session_state.proje_verileri
toplam_gorev = sum(len(faz['gorevler']) for faz in fazlar.values())
toplam_sure = max(faz['baslangic'] + faz['sure'] for faz in fazlar.values())

col1, col2, col3, col4 = st.columns(4)
col1.metric("Toplam Görev", toplam_gorev)
col2.metric("Proje Süresi", f"{toplam_sure} Hafta")
col3.metric("Faz Sayısı", len(fazlar))

# Durum özeti
tamamlanan = sum(1 for faz in fazlar.values() for g in faz['gorevler'] if g['durum'] == 'Tamamlandı')
devam_eden = sum(1 for faz in fazlar.values() for g in faz['gorevler'] if g['durum'] == 'Devam Ediyor')
col4.metric("Tamamlanan", f"{tamamlanan}/{toplam_gorev}")

st.markdown("---")

# Tarih seçici
col1, col2 = st.columns([3, 1])
with col1:
    yeni_tarih = st.date_input(
        "📅 Proje Başlangıç Tarihi",
        value=st.session_state.baslangic_tarihi
    )
    if yeni_tarih != st.session_state.baslangic_tarihi.date():
        st.session_state.baslangic_tarihi = datetime.combine(yeni_tarih, datetime.min.time())
        st.rerun()

baslangic = st.session_state.baslangic_tarihi
bitis = baslangic + timedelta(weeks=toplam_sure)

with col2:
    st.info(f"**Bitiş:** {bitis.strftime('%d.%m.%Y')}")

# Ana Tabs
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Yönetim", 
    "📊 Gantt Chart", 
    "✏️ Düzenle", 
    "➕ Ekle",
    "📥 Veri"
])

# TAB 1: YÖNETİM
with tab1:
    st.header("🎯 Proje Yönetim Ekranı")
    
    for faz_adi, faz in fazlar.items():
        with st.expander(f"{faz['renk']} **{faz_adi}** - {faz['durum']}", expanded=True):
            col1, col2, col3, col4 = st.columns(4)
            col1.markdown(f"**Başlangıç:** H{faz['baslangic']+1}")
            col2.markdown(f"**Süre:** {faz['sure']} hafta")
            col3.markdown(f"**Görev:** {len(faz['gorevler'])}")
            with col4:
                yeni_durum = st.selectbox(
                    "Faz Durumu",
                    ["Planlandı", "Devam Ediyor", "Tamamlandı", "Beklemede"],
                    index=["Planlandı", "Devam Ediyor", "Tamamlandı", "Beklemede"].index(faz['durum']),
                    key=f"faz_{faz_adi}"
                )
                if yeni_durum != faz['durum']:
                    st.session_state.proje_verileri[faz_adi]['durum'] = yeni_durum
                    st.rerun()
            
            st.progress(faz['sure'] / toplam_sure)
            
            data = []
            for g in faz['gorevler']:
                bas = baslangic + timedelta(weeks=g['baslangic_hafta']-1)
                bit = bas + timedelta(weeks=g['sure'])
                data.append({
                    'ID': g['id'],
                    'Görev': g['gorev'],
                    'Açıklama': g['aciklama'],
                    'Süre': g['sure'],
                    'Başlangıç H': g['baslangic_hafta'],
                    'Başlangıç': bas.strftime('%d.%m'),
                    'Bitiş': bit.strftime('%d.%m'),
                    'Sorumlu': g['sorumlu'],
                    'Öncelik': g['oncelik'],
                    'Durum': g['durum']
                })
            
            df = pd.DataFrame(data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            st.markdown("---")

# TAB 2: GANTT CHART
with tab2:
    st.header("📊 Gantt Chart - Proje Timeline")
    
    # Gantt Chart CSS stilleri
    st.markdown("""
    <style>
    .gantt-container {
        overflow-x: auto;
        margin: 20px 0;
    }
    .gantt-table {
        border-collapse: collapse;
        width: 100%;
        font-size: 12px;
    }
    .gantt-table th {
        background-color: #f0f2f6;
        padding: 8px;
        text-align: left;
        border: 1px solid #ddd;
        position: sticky;
        top: 0;
        z-index: 10;
    }
    .gantt-table td {
        padding: 6px;
        border: 1px solid #ddd;
        text-align: center;
    }
    .gantt-task {
        height: 25px;
        border-radius: 4px;
        display: inline-block;
        position: relative;
        margin: 2px 0;
    }
    .tamamlandi { background-color: #4caf50; color: white; }
    .devam-ediyor { background-color: #ff9800; color: white; }
    .planlandi { background-color: #2196f3; color: white; }
    .beklemede { background-color: #9e9e9e; color: white; }
    .gorev-info {
        font-size: 10px;
        padding: 2px 8px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    .faz-header {
        background-color: #e3f2fd;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Gantt Chart HTML oluştur
    max_hafta = 40  # FAZ 3'ü de kapsayacak şekilde 40 haftaya çıkardık
    
    gantt_html = '<div class="gantt-container"><table class="gantt-table">'
    
    # Header - Haftalar
    gantt_html += '<tr><th style="min-width:200px;">Görev</th><th style="min-width:80px;">ID</th><th style="min-width:100px;">Sorumlu</th><th style="min-width:80px;">Durum</th>'
    for h in range(1, max_hafta + 1):
        gantt_html += f'<th style="min-width:40px;">H{h}</th>'
    gantt_html += '</tr>'
    
    # Her faz ve görev için satır
    for faz_adi, faz in fazlar.items():
        # Faz başlığı
        gantt_html += f'<tr class="faz-header"><td colspan="{max_hafta + 4}">{faz["renk"]} {faz_adi}</td></tr>'
        
        # Görevler
        for gorev in faz['gorevler']:
            durum_class = gorev['durum'].lower().replace(' ', '-').replace('ı', 'i')
            
            gantt_html += f'<tr>'
            gantt_html += f'<td style="text-align:left;">{gorev["gorev"][:40]}</td>'
            gantt_html += f'<td>{gorev["id"]}</td>'
            gantt_html += f'<td>{gorev["sorumlu"]}</td>'
            gantt_html += f'<td><span class="gantt-task {durum_class}" style="width:60px; display:inline-block;">{gorev["durum"][:4]}</span></td>'
            
            # Hafta hücreleri
            bas_h = gorev['baslangic_hafta']
            sure = gorev['sure']
            
            for h in range(1, max_hafta + 1):
                if h >= bas_h and h < bas_h + sure:
                    # Görevin olduğu haftalar
                    if h == bas_h:
                        # İlk hafta - görev çubuğu başlangıcı
                        colspan = min(sure, max_hafta - h + 1)
                        gantt_html += f'<td colspan="{colspan}">'
                        gantt_html += f'<div class="gantt-task {durum_class}" style="width:100%;">'
                        gantt_html += f'<span class="gorev-info">{gorev["id"]}</span>'
                        gantt_html += '</div></td>'
                        # Sonraki hücreleri atla
                        for _ in range(1, colspan):
                            continue
                    # Diğer haftalar zaten colspan ile kapsandı
                elif h < bas_h or h >= bas_h + sure:
                    # Görevin olmadığı haftalar - boş hücre
                    if h not in range(bas_h, bas_h + sure):
                        gantt_html += '<td></td>'
            
            gantt_html += '</tr>'
    
    gantt_html += '</table></div>'
    
    # Gantt'ı göster
    st.markdown(gantt_html, unsafe_allow_html=True)
    
    # Legend
    st.markdown("---")
    st.markdown("### 📌 Durum Göstergeleri")
    col1, col2, col3, col4 = st.columns(4)
    col1.markdown("🟢 **Tamamlandı** - Yeşil")
    col2.markdown("🟠 **Devam Ediyor** - Turuncu")
    col3.markdown("🔵 **Planlandı** - Mavi")
    col4.markdown("⚫ **Beklemede** - Gri")

# TAB 3: DÜZENLE
with tab3:
    st.header("✏️ Görev Düzenleme")
    
    # Faz seç
    faz_sec = st.selectbox("Faz Seçin", list(fazlar.keys()), key="edit_faz_select")
    
    if faz_sec:
        # Görev ID'lerini benzersiz tutarak listele
        gorev_options = {}
        for g in fazlar[faz_sec]['gorevler']:
            gorev_options[g['id']] = f"{g['id']} - {g['gorev']}"
        
        if gorev_options:
            gorev_sec_id = st.selectbox(
                "Düzenlenecek Görevi Seçin",
                options=list(gorev_options.keys()),
                format_func=lambda x: gorev_options[x],
                key="edit_gorev_select"
            )
            
            if gorev_sec_id:
                # ID'ye göre görevi bul
                gorev = next((g for g in fazlar[faz_sec]['gorevler'] if g['id'] == gorev_sec_id), None)
                
                if gorev:
                    st.markdown("---")
                    st.subheader(f"Görev: {gorev['id']} - {gorev['gorev']}")
                    
                    with st.form(f"edit_form_{gorev['id'].replace('.', '_')}"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            yeni_gorev = st.text_input("Görev Adı", value=gorev['gorev'])
                            yeni_aciklama = st.text_area("Açıklama", value=gorev['aciklama'])
                            yeni_sure = st.number_input("Süre (hafta)", min_value=1, value=gorev['sure'])
                            yeni_bas_h = st.number_input("Başlangıç Haftası", min_value=1, value=gorev['baslangic_hafta'])
                        
                        with col2:
                            yeni_sorumlu = st.text_input("Sorumlu", value=gorev['sorumlu'])
                            yeni_oncelik = st.selectbox(
                                "Öncelik",
                                ["Kritik", "Yüksek", "Orta", "Düşük"],
                                index=["Kritik", "Yüksek", "Orta", "Düşük"].index(gorev['oncelik'])
                            )
                            yeni_durum = st.selectbox(
                                "Durum",
                                ["Planlandı", "Devam Ediyor", "Tamamlandı", "Beklemede"],
                                index=["Planlandı", "Devam Ediyor", "Tamamlandı", "Beklemede"].index(gorev['durum'])
                            )
                            yeni_id = st.text_input("ID (dikkatli değiştirin)", value=gorev['id'])
                        
                        col1, col2 = st.columns(2)
                        kaydet = col1.form_submit_button("💾 Kaydet", use_container_width=True)
                        sil = col2.form_submit_button("🗑️ Sil", use_container_width=True)
                        
                        if kaydet:
                            # ID'ye göre index bul
                            idx = next((i for i, g in enumerate(fazlar[faz_sec]['gorevler']) if g['id'] == gorev_sec_id), None)
                            
                            if idx is not None:
                                st.session_state.proje_verileri[faz_sec]['gorevler'][idx] = {
                                    'id': yeni_id,
                                    'gorev': yeni_gorev,
                                    'aciklama': yeni_aciklama,
                                    'sure': yeni_sure,
                                    'baslangic_hafta': yeni_bas_h,
                                    'sorumlu': yeni_sorumlu,
                                    'oncelik': yeni_oncelik,
                                    'durum': yeni_durum
                                }
                                st.success("✅ Görev kaydedildi!")
                                st.rerun()
                        
                        if sil:
                            # ID'ye göre sil
                            st.session_state.proje_verileri[faz_sec]['gorevler'] = [
                                g for g in fazlar[faz_sec]['gorevler'] if g['id'] != gorev_sec_id
                            ]
                            st.success(f"✅ Görev {gorev_sec_id} silindi!")
                            st.rerun()
        else:
            st.info("Bu fazda henüz görev yok.")

# TAB 4: EKLE
with tab4:
    st.header("➕ Yeni Ekle")
    
    tip = st.radio("Ne eklemek istiyorsunuz?", ["Görev", "Faz"])
    
    if tip == "Görev":
        st.subheader("Yeni Görev Ekle")
        
        with st.form("yeni_gorev"):
            hedef = st.selectbox("Hangi Faza Eklenecek?", list(fazlar.keys()))
            
            col1, col2 = st.columns(2)
            with col1:
                yeni_id = st.text_input("Görev ID", placeholder="Örn: 0.8 veya 1.10")
                yeni_gorev = st.text_input("Görev Adı", placeholder="Görev başlığı")
                yeni_aciklama = st.text_area("Açıklama", placeholder="Detaylı açıklama")
                yeni_sure = st.number_input("Süre (hafta)", min_value=1, value=1)
            
            with col2:
                yeni_bas_h = st.number_input("Başlangıç Haftası", min_value=1, value=1)
                yeni_sorumlu = st.text_input("Sorumlu", placeholder="Örn: Ertuğrul + Gökhan")
                yeni_oncelik = st.selectbox("Öncelik", ["Kritik", "Yüksek", "Orta", "Düşük"])
                yeni_durum = st.selectbox("Durum", ["Planlandı", "Devam Ediyor", "Tamamlandı", "Beklemede"])
            
            if st.form_submit_button("➕ Görevi Ekle", use_container_width=True):
                if yeni_id and yeni_gorev:
                    # ID benzersizliğini kontrol et
                    mevcut_idler = [g['id'] for g in fazlar[hedef]['gorevler']]
                    if yeni_id in mevcut_idler:
                        st.error(f"⚠️ {yeni_id} ID'si zaten kullanılıyor! Farklı bir ID seçin.")
                    else:
                        st.session_state.proje_verileri[hedef]['gorevler'].append({
                            'id': yeni_id,
                            'gorev': yeni_gorev,
                            'aciklama': yeni_aciklama,
                            'sure': yeni_sure,
                            'baslangic_hafta': yeni_bas_h,
                            'sorumlu': yeni_sorumlu,
                            'oncelik': yeni_oncelik,
                            'durum': yeni_durum
                        })
                        st.success(f"✅ Yeni görev '{yeni_gorev}' ({yeni_id}) eklendi!")
                        st.rerun()
                else:
                    st.error("⚠️ Görev ID ve Görev Adı zorunludur!")
    
    else:  # Yeni Faz
        st.subheader("Yeni Faz Ekle")
        
        with st.form("yeni_faz"):
            faz_adi = st.text_input("Faz Adı", placeholder="Örn: FAZ 3: YAYINLAMA")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                faz_bas = st.number_input("Başlangıç Haftası", min_value=0, value=toplam_sure)
            with col2:
                faz_sure = st.number_input("Süre (hafta)", min_value=1, value=4)
            with col3:
                faz_renk = st.selectbox("Emoji", ["🔴", "🟢", "🔵", "🟡", "🟣", "⚫", "⚪", "🟤"])
            
            if st.form_submit_button("➕ Faz Ekle", use_container_width=True):
                if faz_adi:
                    if faz_adi in fazlar:
                        st.error(f"⚠️ '{faz_adi}' adında bir faz zaten var!")
                    else:
                        st.session_state.proje_verileri[faz_adi] = {
                            'baslangic': faz_bas,
                            'sure': faz_sure,
                            'renk': faz_renk,
                            'durum': 'Planlandı',
                            'gorevler': []
                        }
                        st.success(f"✅ Yeni faz '{faz_adi}' eklendi!")
                        st.rerun()
                else:
                    st.error("⚠️ Faz adı zorunludur!")

# TAB 5: VERİ İŞLEMLERİ
with tab5:
    st.header("📥 Veri İşlemleri")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📤 Dışa Aktar")
        
        # JSON
        json_data = json.dumps(st.session_state.proje_verileri, ensure_ascii=False, indent=2)
        st.download_button(
            "📥 JSON olarak İndir",
            json_data,
            "proje_verileri.json",
            "application/json",
            use_container_width=True
        )
        
        # CSV
        tum_gorevler = []
        for faz_adi, faz in fazlar.items():
            for g in faz['gorevler']:
                tum_gorevler.append({'Faz': faz_adi, **g})
        
        df_export = pd.DataFrame(tum_gorevler)
        st.download_button(
            "📥 CSV olarak İndir",
            df_export.to_csv(index=False).encode('utf-8'),
            "proje_gorevleri.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        st.subheader("📥 İçe Aktar")
        
        uploaded = st.file_uploader("JSON Dosyası Yükle", type=['json'])
        if uploaded:
            try:
                data = json.loads(uploaded.read())
                st.success("✅ Dosya okundu!")
                
                if st.button("✅ Veriyi Projeye Yükle", use_container_width=True):
                    st.session_state.proje_verileri = data
                    st.success("✅ Proje verileri güncellendi!")
                    st.rerun()
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
    
    st.markdown("---")
    st.subheader("🔄 Sıfırlama")
    
    if st.button("⚠️ Tüm Verileri Sıfırla ve Varsayılanlara Dön", type="secondary", use_container_width=True):
        if 'proje_verileri' in st.session_state:
            del st.session_state.proje_verileri
        st.success("✅ Proje verileri varsayılanlara döndürüldü!")
        st.rerun()

st.markdown("---")
st.caption(f"📦 Depo Birleştirme Projesi | Thorius AR4U | Hakan | {datetime.now().strftime('%d.%m.%Y %H:%M')}")
