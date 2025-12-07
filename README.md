# 📊 Thorius AR4U - Retail Analytics Platform

**Token-Based Monorepo Architecture**

---

## 🎯 Overview

Thorius AR4U, perakende operasyonları için kapsamlı bir analitik platformdur. 11 modül, merkezi token sistemi ve kullanıcı bazlı erişim kontrolü sunar.

---

## 📦 Modüller

### 🔵 IN-SEASON MODÜLLERİ (7 modül)

1. **🚢 Sevkiyat Yönetimi** - 10 token
   - LIVE ✅
   - Sevkiyat planlama ve optimizasyon

2. **📋 Sevkiyat ve PO Yönetimi** - 10 token
   - LIVE ✅
   - Purchase Order & Sevkiyat birleşik modül

3. **🏪 Kapasite Planlama** - 5 token
   - YAKINDA 🔜
   - Mağaza kapasite analizi

4. **🔄 Transfer & İade** - 5 token
   - YAKINDA 🔜
   - Mağazalar arası transfer yönetimi

5. **📊 WSSI Analysis** - 6 token
   - YAKINDA 🔜
   - Weeks Supply & Stock Index

6. **💰 İndirim - Fiyatlandırma** - 7 token
   - YAKINDA 🔜
   - Dinamik fiyatlandırma ve markdown

7. **🧩 Clustering** - 8 token
   - YAKINDA 🔜
   - ML-based mağaza segmentasyonu

### 🔴 PRE-SEASON MODÜLLERİ (3 modül)

8. **📊 Bütçe Forecast Modülü** - 8 token
   - LIVE ✅
   - AI-powered budget forecasting (Prophet)

9. **🏗️ Model Bütçe Sipariş Modülü** - 8 token
   - TEST 🧪
   - Pre-season sipariş planlama

10. **⛓️ Tedarik Zinciri Kokpit** - 6 token
    - YAKINDA 🔜
    - Supply chain dashboard

### 🟡 PROJE YÖNETİMİ (1 modül)

11. **📦 OMS Depo Birleştirme Projesi** - 1 token
    - LIVE ✅
    - Depo konsolidasyonu proje yönetimi

---

## 🪙 Token Sistemi

### Merkezi Token Havuzu
- Her kullanıcıya **100 token** başlangıç
- Tüm modüllerde **ortak bakiye**
- Modül bazlı token maliyeti

### 6 Saat Kuralı
- **İlk giriş** → Token düşer
- **Aynı modül < 6 saat** → Token düşmez ✅
- **Aynı modül > 6 saat** → Token düşer ⚠️
- **Farklı modül** → Her zaman token düşer

### Örnek Senaryo
```
Ertuğrul Bey - Başlangıç: 100 token

09:00 → OMS Proje (1 token) → Kalan: 99
09:30 → Sevkiyat (10 token) → Kalan: 89
11:00 → OMS Proje → Token düşmez (1.5 saat) → Kalan: 89
13:00 → Sevkiyat → Token düşmez (3.5 saat) → Kalan: 89
16:00 → Sevkiyat → Token düşer (7 saat!) → Kalan: 79
16:30 → Bütçe Forecast (8 token) → Kalan: 71
```

---

## 👥 Kullanıcılar

| Kullanıcı | Şifre | Rol | Token |
|-----------|-------|-----|-------|
| ertugrul | lojistik2025 | Sponsor | 100 🪙 |
| gokhan | ecom2025 | Sponsor | 100 🪙 |
| volkan | magaza2025 | Manager | 100 🪙 |
| ferhat | stok2025 | Manager | 100 🪙 |
| tayfun | eve2025 | Manager | 100 🪙 |
| aliakcay | tzy2025 | User | 100 🪙 |
| ozcan | it2025 | Admin | 100 🪙 |
| demo | demo2025 | Viewer | 100 🪙 |

---

## 📁 Proje Yapısı

```
thorius-ar4u/
├── Home.py                          # Ana sayfa (giriş + dashboard)
├── token_manager.py                 # Merkezi token sistemi
├── thorius_tokens.db                # SQLite token veritabanı
├── requirements.txt                 # Python dependencies
├── README.md                        # Bu dosya
│
├── pages/                           # Streamlit multipage modüller
│   ├── 1_🚢_Sevkiyat_Yönetimi.py
│   ├── 2_📋_Sevkiyat_PO.py
│   ├── 3_🏪_Kapasite.py
│   ├── 4_🔄_Transfer_Iade.py
│   ├── 5_📊_WSSI.py
│   ├── 6_💰_Fiyatlandirma.py
│   ├── 7_🧩_Clustering.py
│   ├── 8_📊_Bütçe_Forecast.py
│   ├── 9_🏗️_Model_Bütçe.py
│   ├── 10_⛓️_Tedarik_Zinciri.py
│   └── 11_📦_OMS_Projesi.py
│
└── _module_template.py              # Yeni modüller için şablon
```

---

## 🚀 Kurulum & Deployment

### Lokal Test

```bash
# Repository'yi clone et
git clone https://github.com/[username]/thorius-ar4u.git
cd thorius-ar4u

# Virtual environment oluştur
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies kur
pip install -r requirements.txt

# Uygulamayı başlat
streamlit run Home.py
```

### Streamlit Cloud Deployment

1. GitHub'a push et:
```bash
git add .
git commit -m "Thorius AR4U monorepo"
git push origin main
```

2. Streamlit Cloud'da deploy:
   - https://share.streamlit.io/ → New app
   - Repository: thorius-ar4u
   - Main file: Home.py
   - Deploy!

---

## 🗄️ Veritabanı

**SQLite** (`thorius_tokens.db`)

### Tables

#### users
```sql
username (PRIMARY KEY)
password_hash (SHA256)
name
title
role
total_tokens (default: 100)
remaining_tokens (default: 100)
created_at
```

#### token_transactions
```sql
id (AUTO INCREMENT)
username
module
token_cost
remaining_after
timestamp
session_id
```

#### last_logins
```sql
username + module (COMPOSITE KEY)
last_login
last_login_date
login_count_today
```

---

## 🔧 Yeni Modül Ekleme

1. `_module_template.py` dosyasını kopyala
2. `pages/X_[EMOJI]_[MODUL_ADI].py` olarak adlandır
3. Şablondaki placeholder'ları güncelle:
   - `[MODÜL ADI]`
   - `[EMOJI]`
   - `[MODULE_KEY]`
   - `[MODÜL AÇIKLAMASI]`
4. Modül spesifik kodunu ekle
5. `token_manager.py` içinde `MODULE_TOKEN_COSTS` dict'ine ekle

---

## 📊 Token Yönetimi API

### Functions

```python
# Token sistemini başlat
init_token_system_for_app()

# Kullanıcı doğrulama
user_info = authenticate_user(username, password)

# Token düşmeli mi kontrol
should_charge = check_token_charge(username, module_name)

# Token düş
success, remaining, message = charge_token(username, module_name)

# Bakiye getir
balance = get_token_balance(username)

# Bugünkü istatistikler
stats = get_today_stats(username)

# İşlem geçmişi
history = get_transaction_history(username, limit=10)

# Admin: Token ekle
add_tokens(username, amount, admin_username)

# Sidebar widget render et
render_token_widget(username)
```

---

## 🎨 UI/UX

- **Gradient Backgrounds** → Modern görünüm
- **Renkli Progress Bars** → Token kullanımı görselleştirme
- **Responsive Design** → Mobil uyumlu
- **Dark Mode Ready** → Streamlit tema desteği

---

## 🔐 Güvenlik

- ✅ SHA256 password hashing
- ✅ Session-based authentication
- ✅ Role-based access control
- ✅ Token transaction logging
- ✅ SQL injection prevention

---

## 📈 Gelecek Özellikler

- [ ] Admin dashboard (token yönetimi)
- [ ] Email notifications (token azalınca)
- [ ] PostgreSQL migration (Supabase)
- [ ] 2FA authentication
- [ ] API endpoints (external access)
- [ ] Mobile app (React Native)
- [ ] Real-time collaboration
- [ ] Advanced analytics dashboard

---

## 💡 Destek

**Geliştirici:** Hakan  
**Platform:** Streamlit + Python  
**Veritabanı:** SQLite (production: PostgreSQL)  
**Deployment:** Streamlit Cloud  

---

## 📄 Lisans

Internal Use - Thorius AR4U Platform

---

**🚀 Hazır Kullanıma Hazır Monorepo!**
