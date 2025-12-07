# 🚀 THORIUS AR4U - DEPLOYMENT GUIDE

## 📋 HIZLI BAŞLANGIÇ

### 1️⃣ GitHub Repository Oluştur

```bash
# GitHub'da yeni repo oluştur: thorius-ar4u
# Lokal klasöre git
cd /path/to/thorius_monorepo

# Git init
git init
git add .
git commit -m "Initial commit: Thorius AR4U monorepo with token system"

# Remote ekle ve push
git remote add origin https://github.com/[USERNAME]/thorius-ar4u.git
git branch -M main
git push -u origin main
```

---

### 2️⃣ Streamlit Cloud Deployment

**Adım 1: Streamlit Cloud'a Git**
- https://share.streamlit.io/
- "New app" tıkla

**Adım 2: Repository Seç**
- Repository: `thorius-ar4u`
- Branch: `main`
- Main file path: `Home.py`

**Adım 3: Advanced Settings (Optional)**
- Python version: `3.11`
- Secrets: (Şimdilik gerekmiyor)

**Adım 4: Deploy!**
- "Deploy!" butonuna tıkla
- 2-3 dakika bekle
- Uygulaman hazır! 🎉

**URL Örneği:**
```
https://thorius-ar4u.streamlit.app/
```

---

## 🔧 MEVCUT MODÜLLERİ EKLEME

### OMS Projesi Entegrasyonu

```bash
# Mevcut OMS_proje.py dosyasını al
# pages/ klasörüne kopyala ve adını değiştir

cp /path/to/OMS_proje.py pages/11_📦_OMS_Projesi.py
```

**Düzenlemeler:**

1. **Import ekle (dosyanın başına):**
```python
from token_manager import (
    check_token_charge,
    charge_token,
    render_token_widget
)
```

2. **Authentication kontrolünü değiştir:**
```python
# ESKİ:
if not check_password():
    st.stop()

# YENİ:
if "authenticated" not in st.session_state or not st.session_state.authenticated:
    st.error("❌ Giriş yapmalısınız!")
    if st.button("🏠 Ana Sayfa"):
        st.switch_page("Home.py")
    st.stop()
```

3. **Token kontrolü ekle:**
```python
username = st.session_state.user_info["username"]
module_name = "oms_proje"

should_charge = check_token_charge(username, module_name)
if should_charge:
    success, remaining, message = charge_token(username, module_name)
    if not success:
        st.error(f"❌ {message}")
        st.stop()
```

4. **Sidebar'ı güncelle:**
```python
# ESKİ token widget kodunu sil
# YENİ: 
render_token_widget(username)
```

---

### Sevkiyat Modülü Entegrasyonu

```bash
# Mevcut sevkiyat.py dosyasını al
cp /path/to/sevkiyat.py pages/1_🚢_Sevkiyat_Yönetimi.py
```

**Aynı düzenlemeleri yap:**
- Import token_manager
- Authentication kontrolü
- Token kontrolü (module_name = "sevkiyat")
- Sidebar güncellemesi

---

### Bütçe Forecast Entegrasyonu

```bash
cp /path/to/budget_forecast.py pages/8_📊_Bütçe_Forecast.py
```

**Düzenlemeler:**
- module_name = "budget_forecast"
- Diğer adımlar aynı

---

## 📊 YAKINDA MODÜLLER İÇİN ŞABLON

Henüz geliştirilmemiş modüller için placeholder oluştur:

```bash
# Örnek: Kapasite modülü
cp _module_template.py pages/3_🏪_Kapasite.py
```

**Düzenle:**
```python
# [MODÜL ADI] → Kapasite Planlama
# [EMOJI] → 🏪
# [MODULE_KEY] → kapasite
# [MODÜL AÇIKLAMASI] → Mağaza kapasite analizi ve planlama
```

Bu modül "🚧 Yakında" mesajı gösterecek ama menüde görünecek.

---

## 🗄️ VERİTABANI YÖNETİMİ

### İlk Çalıştırmada

Token sistemi otomatik olarak:
1. `thorius_tokens.db` oluşturur
2. Tabloları initialize eder
3. 8 kullanıcı ekler (100 token'la)

### Manuel Veritabanı Kontrolü

```python
# Python shell'de
python

>>> from token_manager import *
>>> init_database()
>>> create_default_users()
>>> print("✅ Database hazır!")
```

### Veritabanı Sıfırlama

```bash
# Dikkat: Tüm token geçmişi silinir!
rm thorius_tokens.db
streamlit run Home.py  # Yeniden oluşturur
```

---

## 🧪 LOKAL TEST

```bash
# Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies
pip install -r requirements.txt

# Test
streamlit run Home.py

# Tarayıcıda aç
http://localhost:8501
```

**Test Senaryosu:**

1. Login: `demo / demo2025`
2. Token: 100 görünmeli
3. OMS Proje'ye gir → Token: 99
4. Sevkiyat'a gir → Token: 89
5. Ana sayfaya dön → Token aynı kalmalı
6. Çıkış yap → Tekrar giriş → Token aynı olmalı (DB'de saklı)

---

## 🔐 SECRETS YÖNETİMİ (Gelecek)

Production'da şifreleri `.streamlit/secrets.toml` ile yönet:

```toml
[users]
admin_password = "very_secure_password_here"
db_encryption_key = "encryption_key_here"

[database]
connection_string = "postgresql://..."  # Future: PostgreSQL
```

---

## 📈 PERFORMANS OPTİMİZASYONU

### Cache Kullanımı

```python
@st.cache_data(ttl=300)  # 5 dakika cache
def load_heavy_data():
    # Ağır veri işlemleri
    return data
```

### Database Connection Pool

```python
# Future: PostgreSQL için
from sqlalchemy import create_engine
engine = create_engine(connection_string, pool_size=20)
```

---

## 🚨 TROUBLESHOOTING

### Problem: Token düşmüyor
**Çözüm:** Database dosyasını kontrol et, gerekirse sıfırla

### Problem: Login çalışmıyor
**Çözüm:** 
```python
# SHA256 hash'i kontrol et
import hashlib
print(hashlib.sha256("demo2025".encode()).hexdigest())
```

### Problem: Modüller görünmüyor
**Çözüm:** `pages/` klasör adını kontrol et, dosya adı formatı doğru olmalı

### Problem: Import hatası
**Çözüm:** `token_manager.py` root directory'de olmalı

---

## 📞 DESTEK

**GitHub Issues:** https://github.com/[username]/thorius-ar4u/issues

**Email:** support@thorius.com

---

## ✅ CHECKLIST

Deployment öncesi kontrol:

- [ ] Tüm modüller `pages/` klasöründe
- [ ] `token_manager.py` root'ta
- [ ] `requirements.txt` güncel
- [ ] `.gitignore` eklendi
- [ ] README.md tamamlandı
- [ ] Lokal test başarılı
- [ ] GitHub'a push edildi
- [ ] Streamlit Cloud'da deploy edildi
- [ ] Production test (demo kullanıcı ile)

---

**🎉 HAZIRSIN! Thorius AR4U production'da!**
