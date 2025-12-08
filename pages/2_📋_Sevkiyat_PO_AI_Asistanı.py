import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import time
import zipfile
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="Retail Analytics", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

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

# ============================================
# TOKEN SİSTEMİ
# ============================================
def check_authentication():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("⛔ Bu modüle erişim için lütfen giriş yapın!")
        st.info("👉 Ana sayfaya dönüp giriş yapınız.")
        st.stop()
    return True

def get_user_info():
    if 'username' in st.session_state:
        return {'username': st.session_state.username, 'role': st.session_state.get('user_role', 'user')}
    return None

def deduct_tokens(amount=10):
    if 'tokens_deducted' not in st.session_state:
        st.session_state.tokens_deducted = False
    if not st.session_state.tokens_deducted and 'username' in st.session_state:
        try:
            import sqlite3
            conn = sqlite3.connect('tokens.db')
            cursor = conn.cursor()
            cursor.execute('SELECT tokens FROM tokens WHERE username = ?', (st.session_state.username,))
            result = cursor.fetchone()
            if result and result[0] >= amount:
                cursor.execute('UPDATE tokens SET tokens = tokens - ? WHERE username = ?', (amount, st.session_state.username))
                conn.commit()
                st.session_state.tokens_deducted = True
                st.session_state.current_tokens = result[0] - amount
                conn.close()
                return True
            else:
                conn.close()
                st.error(f"⚠️ Yetersiz token! Bu modül {amount} token gerektirir.")
                st.stop()
        except Exception as e:
            st.error(f"Token kontrolü hatası: {str(e)}")
            st.stop()
    return st.session_state.tokens_deducted

check_authentication()
deduct_tokens(10)

# ============================================
# SESSION STATE - TÜM VERİLER
# ============================================
for key in ['inventory_df', 'urun_master', 'magaza_master', 'yasak_master', 'depo_stok', 
            'anlik_stok_satis', 'haftalik_trend', 'kpi', 'po_yasak', 'po_detay_kpi', 
            'alim_siparis_sonuc', 'sevkiyat_sonuc']:
    if key not in st.session_state:
        st.session_state[key] = None

if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))],
        'store_ranges': [(0, 4), (5, 8), (9, 12), (12, 15), (15, 20), (20, float('inf'))]
    }
if 'cover_segment_matrix' not in st.session_state:
    st.session_state.cover_segment_matrix = None

# ============================================
# SIDEBAR
# ============================================
with st.sidebar:
    st.markdown("### 📊 THORIUS AR4U")
    st.markdown("**Retail Analytics Platform**")
    st.markdown("---")
    
    user_info = get_user_info()
    if user_info:
        st.markdown(f"""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 15px; border-radius: 10px; color: white; margin-bottom: 20px;'>
            <div style='font-size: 12px; opacity: 0.9;'>👤 Kullanıcı</div>
            <div style='font-size: 16px; font-weight: bold;'>{user_info['username']}</div>
            <div style='font-size: 11px; margin-top: 5px; opacity: 0.8;'>
                🎫 Token: {st.session_state.get('current_tokens', 'N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    menu_option = st.radio(
        "📋 Modül Seçin",
        ["🏠 Ana Sayfa", "📂 Veri Yükleme", "🚢 Sevkiyat Planlama", "💵 Purchase Order (PO)"],
        key="main_menu"
    )
    
    st.markdown("---")
    st.info("""
    **Retail Analytics**
    
    ✅ Tek token ile tüm modüller
    📊 4 farklı analiz aracı
    🔄 Anlık veri yükleme
    """)

# ============================================
# ANA SAYFA
# ============================================
if menu_option == "🏠 Ana Sayfa":
    st.title("📊 Retail Analytics Platform")
    st.markdown("---")
    
    st.markdown("""
    ### 🎯 Hoş Geldiniz!
    
    Bu modül **tek token** ile aşağıdaki tüm analiz araçlarına erişim sağlar:
    
    #### 📂 Veri Yükleme
    - Ürün Master, Mağaza Master, KPI
    - Depo Stok, Anlık Stok/Satış
    - Yasak, Haftalık Trend
    - PO Yasak, PO Detay KPI
    
    #### 🚢 Sevkiyat Planlama
    - KMeans clustering
    - Bütçe optimizasyonu
    - WOS optimizasyonu
    
    #### 💵 Purchase Order (PO)
    - Depo bazlı sipariş
    - Cover optimizasyonu
    - Segment matrisi
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Sevkiyat Verileri**")
        if st.session_state.inventory_df is not None:
            st.success(f"✅ Envanter verisi yüklü")
        else:
            st.warning("⚠️ Envanter verisi yüklenmedi")
    
    with col2:
        st.markdown("**PO Verileri**")
        po_loaded = all([
            st.session_state.anlik_stok_satis is not None,
            st.session_state.depo_stok is not None,
            st.session_state.kpi is not None
        ])
        if po_loaded:
            st.success("✅ PO verileri yüklü")
        else:
            st.warning("⚠️ PO verileri eksik")


# ============================================
# VERİ YÜKLEME MODÜLÜ - AYNEN KORUNDU
# ============================================
elif menu_option == "📂 Veri Yükleme":
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
    
    # Örnek CSV'ler - TÜM VERİLER
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
    
    # Veri tanımları - AYNEN
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
    
    # Kullanıcı kılavuzu kısmı - SADECE BUTON KISMI (Tam metin çok uzun)
    st.markdown("---")
    st.subheader("📖 Kullanıcı Kılavuzu")
    st.info("💡 **İpucu:** Kılavuzu indirip kaydedin, ihtiyaç duyduğunuzda açın!")
    
    # PARÇALI YÜKLEME
    st.markdown("---")
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
                    df_part, used_sep = read_csv_safe(part_file)
                    expected_cols = set(data_definitions['anlik_stok_satis']['columns'])
                    if not expected_cols.issubset(set(df_part.columns)):
                        st.error(f"❌ {part_file.name}: Eksik kolonlar var!")
                        continue
                    
                    df_part = df_part[data_definitions['anlik_stok_satis']['columns']].copy()
                    string_cols = df_part.select_dtypes(include=['object']).columns
                    for col in string_cols:
                        df_part[col] = df_part[col].str.strip()
                    
                    numeric_cols = ['stok', 'yol', 'satis', 'ciro', 'smm']
                    for col in numeric_cols:
                        if col in df_part.columns:
                            df_part[col] = pd.to_numeric(df_part[col], errors='coerce').fillna(0)
                    
                    if combined_df is None:
                        combined_df = df_part
                    else:
                        combined_df = pd.concat([combined_df, df_part], ignore_index=True)
                    
                    part_info.append(f"✅ Parça {idx}: {len(df_part):,} satır")
                    total_rows += len(df_part)
                
                if combined_df is not None:
                    before_dedup = len(combined_df)
                    combined_df = combined_df.drop_duplicates(subset=['magaza_kod', 'urun_kod'], keep='last')
                    after_dedup = len(combined_df)
                    st.session_state.anlik_stok_satis = combined_df
                    
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
    
    # ÇOKLU DOSYA YÜKLEME
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
    
    # Örnek İndirme + Yükleme Butonları
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
                        upload_results.append({'Dosya': uploaded_file.name, 'Durum': '❌ Eşleştirilemedi'})
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
                            string_columns = df_clean.select_dtypes(include=['object']).columns
                            for col in string_columns:
                                df_clean[col] = df_clean[col].str.strip() if df_clean[col].dtype == 'object' else df_clean[col]
                            
                            # Sayısal kolonları zorla
                            if matched_key == 'anlik_stok_satis':
                                numeric_cols = ['stok', 'yol', 'satis', 'ciro', 'smm']
                                for col in numeric_cols:
                                    if col in df_clean.columns:
                                        df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce').fillna(0)
                            
                            elif matched_key == 'depo_stok':
                                if 'stok' in df_clean.columns:
                                    df_clean['stok'] = pd.to_numeric(df_clean['stok'], errors='coerce').fillna(0)
                            
                            elif matched_key == 'kpi':
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
        # Örnek CSV indirme
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
    
    # VERİ DURUMU TABLOSU
    st.subheader("📊 Veri Yükleme Durumu")
    
    status_data = []
    for key, definition in data_definitions.items():
        data = st.session_state.get(definition['state_key'])
        
        if data is not None and len(data) > 0:
            status = '✅ Başarılı'
            kolon_sayisi = str(len(data.columns))
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
    st.dataframe(status_df, use_container_width=True, hide_index=True, height=350)
    
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

# ============================================
# SEVKİYAT PLANLAMA MODÜLÜ
# ============================================
elif menu_option == '🚢 Sevkiyat Planlama':
    def load_shipment_data():
        """Sevkiyat verilerini yükle"""
        if 'inventory_df' not in st.session_state:
            st.warning("⚠️ Lütfen önce Veri Yükleme sayfasından verileri yükleyin!")
            return None
        return st.session_state.inventory_df.copy()
    
    def calculate_clusters(df, n_clusters=5):
        """Store'ları clustering ile grupla"""
        # Store bazında özet çıkar
        store_summary = df.groupby('STORE_CODE').agg({
            'AVAILABLE_STOCK': 'sum',
            'WEEKLY_SALES': 'mean',
            'WEEKS_OF_SUPPLY': 'mean'
        }).reset_index()
        
        # Normalize et
        scaler = StandardScaler()
        features = scaler.fit_transform(store_summary[['AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY']])
        
        # KMeans clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        store_summary['CLUSTER'] = kmeans.fit_predict(features)
        
        # Cluster özellikleri
        cluster_stats = store_summary.groupby('CLUSTER').agg({
            'STORE_CODE': 'count',
            'AVAILABLE_STOCK': 'mean',
            'WEEKLY_SALES': 'mean',
            'WEEKS_OF_SUPPLY': 'mean'
        }).reset_index()
        
        cluster_stats.columns = ['CLUSTER', 'STORE_COUNT', 'AVG_STOCK', 'AVG_SALES', 'AVG_WOS']
        
        return store_summary, cluster_stats
    
    def calculate_shipment_need(row, target_wos=4):
        """Her store/product için sevkiyat ihtiyacını hesapla"""
        current_wos = row['WEEKS_OF_SUPPLY']
        weekly_sales = row['WEEKLY_SALES']
        
        if current_wos < target_wos and weekly_sales > 0:
            need = (target_wos - current_wos) * weekly_sales
            return max(0, need)
        return 0
    
    def calculate_priority_score(row, weights={'wos': 0.4, 'sales': 0.4, 'need': 0.2}):
        """Öncelik skorunu hesapla"""
        wos_score = 1 / (row['WEEKS_OF_SUPPLY'] + 0.1)  # Düşük WOS = yüksek skor
        sales_score = row['WEEKLY_SALES'] / (row['WEEKLY_SALES'] + 1)  # Normalize sales
        need_score = row['SHIPMENT_NEED'] / (row['SHIPMENT_NEED'] + 1)  # Normalize need
        
        total_score = (
            wos_score * weights['wos'] +
            sales_score * weights['sales'] +
            need_score * weights['need']
        )
        
        return total_score
    
    def optimize_shipment_plan(df, total_budget, target_wos=4, priority_mode='balanced'):
        """Sevkiyat planını optimize et - bütçe ve öncelik bazlı"""
        # Sevkiyat ihtiyacını hesapla
        df['SHIPMENT_NEED'] = df.apply(lambda x: calculate_shipment_need(x, target_wos), axis=1)
        
        # Öncelik weights'lerini ayarla
        if priority_mode == 'sales_focused':
            weights = {'wos': 0.2, 'sales': 0.6, 'need': 0.2}
        elif priority_mode == 'stock_focused':
            weights = {'wos': 0.6, 'sales': 0.2, 'need': 0.2}
        else:  # balanced
            weights = {'wos': 0.4, 'sales': 0.4, 'need': 0.2}
        
        # Önceliklendirme skoru
        df['PRIORITY_SCORE'] = df.apply(lambda x: calculate_priority_score(x, weights), axis=1)
        
        # Önceliğe göre sırala
        df_sorted = df.sort_values('PRIORITY_SCORE', ascending=False).copy()
        
        # Bütçe dağıt
        allocated_budget = 0
        df_sorted['ALLOCATED_QTY'] = 0
        
        for idx in df_sorted.index:
            if allocated_budget >= total_budget:
                break
            
            need = df_sorted.loc[idx, 'SHIPMENT_NEED']
            remaining_budget = total_budget - allocated_budget
            
            allocated = min(need, remaining_budget)
            df_sorted.loc[idx, 'ALLOCATED_QTY'] = allocated
            allocated_budget += allocated
        
        # Yeni WOS hesapla
        df_sorted['NEW_STOCK'] = df_sorted['AVAILABLE_STOCK'] + df_sorted['ALLOCATED_QTY']
        df_sorted['NEW_WOS'] = np.where(
            df_sorted['WEEKLY_SALES'] > 0,
            df_sorted['NEW_STOCK'] / df_sorted['WEEKLY_SALES'],
            df_sorted['WEEKS_OF_SUPPLY']
        )
        
        return df_sorted
    
    def generate_shipment_matrix(df, stores, products):
        """Store x Product sevkiyat matrisi oluştur"""
        matrix_data = []
        
        for store in stores:
            store_data = df[df['STORE_CODE'] == store]
            row = {'STORE_CODE': store}
            
            for product in products:
                product_data = store_data[store_data['PRODUCT_CODE'] == product]
                if not product_data.empty:
                    row[product] = int(product_data['ALLOCATED_QTY'].iloc[0])
                else:
                    row[product] = 0
            
            # Toplam ekle
            row['TOTAL'] = sum([v for k, v in row.items() if k != 'STORE_CODE'])
            matrix_data.append(row)
        
        matrix_df = pd.DataFrame(matrix_data)
        
        # Toplam satırı ekle
        total_row = {'STORE_CODE': 'TOPLAM'}
        for col in matrix_df.columns:
            if col != 'STORE_CODE':
                total_row[col] = matrix_df[col].sum()
        
        matrix_df = pd.concat([matrix_df, pd.DataFrame([total_row])], ignore_index=True)
        
        return matrix_df
    
    def generate_store_summary(df):
        """Store bazında özet rapor"""
        summary = df.groupby('STORE_CODE').agg({
            'PRODUCT_CODE': 'count',
            'AVAILABLE_STOCK': 'sum',
            'WEEKLY_SALES': 'sum',
            'WEEKS_OF_SUPPLY': 'mean',
            'SHIPMENT_NEED': 'sum',
            'ALLOCATED_QTY': 'sum'
        }).reset_index()
        
        summary.columns = [
            'STORE_CODE', 'PRODUCT_COUNT', 'TOTAL_STOCK', 'TOTAL_WEEKLY_SALES',
            'AVG_WOS', 'TOTAL_NEED', 'TOTAL_ALLOCATED'
        ]
        
        summary['FULFILLMENT_%'] = (summary['TOTAL_ALLOCATED'] / summary['TOTAL_NEED'] * 100).round(1)
        summary['FULFILLMENT_%'] = summary['FULFILLMENT_%'].fillna(0)
        
        return summary
    
    def generate_product_summary(df):
        """Ürün bazında özet rapor"""
        summary = df.groupby('PRODUCT_CODE').agg({
            'STORE_CODE': 'count',
            'AVAILABLE_STOCK': 'sum',
            'WEEKLY_SALES': 'sum',
            'WEEKS_OF_SUPPLY': 'mean',
            'SHIPMENT_NEED': 'sum',
            'ALLOCATED_QTY': 'sum'
        }).reset_index()
        
        summary.columns = [
            'PRODUCT_CODE', 'STORE_COUNT', 'TOTAL_STOCK', 'TOTAL_WEEKLY_SALES',
            'AVG_WOS', 'TOTAL_NEED', 'TOTAL_ALLOCATED'
        ]
        
        summary['FULFILLMENT_%'] = (summary['TOTAL_ALLOCATED'] / summary['TOTAL_NEED'] * 100).round(1)
        summary['FULFILLMENT_%'] = summary['FULFILLMENT_%'].fillna(0)
        
        return summary
    
    def calculate_shipment_costs(df, cost_per_unit=1.0, handling_cost=0.1):
        """Sevkiyat maliyetlerini hesapla"""
        df = df.copy()
        df['UNIT_COST'] = cost_per_unit
        df['HANDLING_COST'] = df['ALLOCATED_QTY'] * handling_cost
        df['TOTAL_COST'] = df['ALLOCATED_QTY'] * cost_per_unit + df['HANDLING_COST']
        
        return df
    
    def simulate_stockout_risk(df, target_wos=4):
        """Stockout riskini simüle et"""
        df = df.copy()
        
        # Risk kategorileri
        df['STOCKOUT_RISK'] = 'Low'
        df.loc[df['NEW_WOS'] < 2, 'STOCKOUT_RISK'] = 'High'
        df.loc[(df['NEW_WOS'] >= 2) & (df['NEW_WOS'] < target_wos), 'STOCKOUT_RISK'] = 'Medium'
        
        # Risk skoru
        df['RISK_SCORE'] = np.where(
            df['NEW_WOS'] < target_wos,
            (target_wos - df['NEW_WOS']) / target_wos * 100,
            0
        )
        
        return df
    
    def main():
        st.title("📦 Sevkiyat Planlama ve Optimizasyon")
        st.markdown("---")
        
        # Veri yükle
        df = load_shipment_data()
        if df is None:
            return
        
        # Tab yapısı
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
            "🎯 Parametreler",
            "📊 Clustering",
            "🚚 Optimizasyon",
            "📋 Matris",
            "📈 Analizler",
            "💰 Maliyet"
        ])
        
        # ============== TAB 1: PARAMETRELER ==============
        with tab1:
            st.subheader("⚙️ Planlama Parametreleri")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("##### 🎯 WOS Hedefleri")
                target_wos = st.number_input("Hedef WOS", value=4.0, min_value=1.0, max_value=12.0, step=0.5)
                min_wos = st.number_input("Minimum WOS", value=2.0, min_value=0.5, max_value=10.0, step=0.5)
                max_wos = st.number_input("Maximum WOS", value=8.0, min_value=2.0, max_value=20.0, step=0.5)
            
            with col2:
                st.markdown("##### 💰 Bütçe ve Kapasite")
                total_budget = st.number_input("Toplam Sevkiyat Bütçesi (Adet)", value=10000, min_value=100, step=100)
                min_shipment = st.number_input("Minimum Sevkiyat Miktarı", value=10, min_value=1, step=5)
                max_shipment_per_store = st.number_input("Store Başına Max Sevkiyat", value=1000, min_value=10, step=50)
            
            with col3:
                st.markdown("##### ⚖️ Strateji")
                n_clusters = st.number_input("Cluster Sayısı", value=5, min_value=2, max_value=10, step=1)
                
                priority_mode = st.selectbox(
                    "Önceliklendirme Stratejisi",
                    options=['balanced', 'sales_focused', 'stock_focused'],
                    format_func=lambda x: {
                        'balanced': '⚖️ Dengeli',
                        'sales_focused': '📊 Satış Odaklı',
                        'stock_focused': '📦 Stok Odaklı'
                    }[x]
                )
                
                include_low_performers = st.checkbox("Düşük Performanslı Store'ları Dahil Et", value=True)
            
            st.markdown("---")
            
            # Veri özeti
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📍 Toplam Store", df['STORE_CODE'].nunique())
            with col2:
                st.metric("📦 Toplam Ürün", df['PRODUCT_CODE'].nunique())
            with col3:
                st.metric("📊 Toplam Satır", len(df))
            with col4:
                avg_wos = df['WEEKS_OF_SUPPLY'].mean()
                st.metric("📈 Ortalama WOS", f"{avg_wos:.2f}")
            
            st.info("""
            **💡 Strateji Açıklamaları:**
            - **Dengeli**: WOS ve satış eşit ağırlıkta
            - **Satış Odaklı**: Yüksek satışlı store'lara öncelik
            - **Stok Odaklı**: Düşük WOS'lu store'lara öncelik
            """)
            
            # Parametreleri session state'e kaydet
            if st.button("💾 Parametreleri Kaydet", type="primary"):
                st.session_state.shipment_params = {
                    'target_wos': target_wos,
                    'min_wos': min_wos,
                    'max_wos': max_wos,
                    'total_budget': total_budget,
                    'min_shipment': min_shipment,
                    'max_shipment_per_store': max_shipment_per_store,
                    'n_clusters': n_clusters,
                    'priority_mode': priority_mode,
                    'include_low_performers': include_low_performers
                }
                st.success("✅ Parametreler kaydedildi!")
        
        # ============== TAB 2: CLUSTERING ==============
        with tab2:
            st.subheader("📊 Store Clustering Analizi")
            
            if 'shipment_params' not in st.session_state:
                st.warning("⚠️ Lütfen önce parametreleri kaydedin!")
                return
            
            params = st.session_state.shipment_params
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if st.button("🔄 Clustering Yap", type="primary", use_container_width=True):
                    with st.spinner("Clustering hesaplanıyor..."):
                        cluster_df, cluster_stats = calculate_clusters(df, n_clusters=params['n_clusters'])
                        st.session_state.cluster_df = cluster_df
                        st.session_state.cluster_stats = cluster_stats
                        st.success("✅ Clustering tamamlandı!")
            
            with col2:
                st.info(f"""
                **Cluster Sayısı:** {params['n_clusters']}
                
                **Kullanılan Özellikler:**
                - Toplam Stok
                - Ortalama Satış
                - WOS
                """)
            
            if 'cluster_df' in st.session_state:
                cluster_df = st.session_state.cluster_df
                cluster_stats = st.session_state.cluster_stats
                
                st.markdown("---")
                st.subheader("Cluster İstatistikleri")
                
                # Cluster stats
                st.dataframe(
                    cluster_stats.style.background_gradient(subset=['AVG_STOCK', 'AVG_SALES'], cmap='YlOrRd'),
                    use_container_width=True
                )
                
                st.markdown("---")
                st.subheader("Store Dağılımı")
                
                # Store detayları
                display_cols = ['STORE_CODE', 'CLUSTER', 'AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY']
                st.dataframe(
                    cluster_df[display_cols].sort_values('CLUSTER').style.background_gradient(
                        subset=['AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY'],
                        cmap='RdYlGn_r'
                    ),
                    use_container_width=True,
                    height=400
                )
                
                # Cluster seçimi için filtre
                st.markdown("---")
                selected_clusters = st.multiselect(
                    "Analiz için Cluster Seç",
                    options=sorted(cluster_df['CLUSTER'].unique()),
                    default=sorted(cluster_df['CLUSTER'].unique())
                )
                
                if selected_clusters:
                    filtered_stores = cluster_df[cluster_df['CLUSTER'].isin(selected_clusters)]['STORE_CODE'].tolist()
                    st.info(f"**Seçilen Cluster'lardaki Store Sayısı:** {len(filtered_stores)}")
                    
                    # Export
                    csv = cluster_df[cluster_df['CLUSTER'].isin(selected_clusters)].to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Seçili Cluster'ları İndir",
                        data=csv,
                        file_name=f"clusters_{datetime.now().strftime('%Y%m%d')}.csv",
                        mime="text/csv"
                    )
        
        # ============== TAB 3: OPTİMİZASYON ==============
        with tab3:
            st.subheader("🚚 Sevkiyat Optimizasyonu")
            
            if 'shipment_params' not in st.session_state:
                st.warning("⚠️ Lütfen önce parametreleri kaydedin!")
                return
            
            params = st.session_state.shipment_params
            
            # Cluster filtresi (opsiyonel)
            use_cluster_filter = st.checkbox("Sadece Belirli Cluster'lara Sevkiyat Yap", value=False)
            
            selected_cluster_filter = []
            if use_cluster_filter and 'cluster_df' in st.session_state:
                cluster_df = st.session_state.cluster_df
                selected_cluster_filter = st.multiselect(
                    "Cluster Seç",
                    options=sorted(cluster_df['CLUSTER'].unique()),
                    default=sorted(cluster_df['CLUSTER'].unique())
                )
            
            col1, col2 = st.columns([3, 1])
            
            with col1:
                if st.button("⚡ Optimizasyon Çalıştır", type="primary", use_container_width=True):
                    with st.spinner("Optimizasyon yapılıyor..."):
                        # DataFrame'i filtrele
                        working_df = df.copy()
                        
                        if use_cluster_filter and selected_cluster_filter and 'cluster_df' in st.session_state:
                            filtered_stores = cluster_df[cluster_df['CLUSTER'].isin(selected_cluster_filter)]['STORE_CODE'].tolist()
                            working_df = working_df[working_df['STORE_CODE'].isin(filtered_stores)]
                            st.info(f"🔍 {len(filtered_stores)} store için optimizasyon yapılıyor...")
                        
                        # Optimizasyon
                        optimized_df = optimize_shipment_plan(
                            working_df,
                            params['total_budget'],
                            params['target_wos'],
                            params['priority_mode']
                        )
                        
                        # Stockout risk analizi
                        optimized_df = simulate_stockout_risk(optimized_df, params['target_wos'])
                        
                        st.session_state.optimized_df = optimized_df
                        st.success("✅ Optimizasyon tamamlandı!")
            
            with col2:
                st.info(f"""
                **Bütçe:** {params['total_budget']:,}
                **Hedef WOS:** {params['target_wos']}
                **Strateji:** {params['priority_mode']}
                """)
            
            if 'optimized_df' in st.session_state:
                optimized_df = st.session_state.optimized_df
                
                st.markdown("---")
                st.subheader("📊 Optimizasyon Sonuçları")
                
                # Ana metrikler
                col1, col2, col3, col4, col5 = st.columns(5)
                
                total_allocated = optimized_df['ALLOCATED_QTY'].sum()
                stores_served = (optimized_df['ALLOCATED_QTY'] > 0).sum()
                total_need = optimized_df['SHIPMENT_NEED'].sum()
                fulfillment_rate = (total_allocated / total_need * 100) if total_need > 0 else 0
                avg_new_wos = optimized_df[optimized_df['ALLOCATED_QTY'] > 0]['NEW_WOS'].mean()
                
                with col1:
                    st.metric(
                        "Dağıtılan Miktar",
                        f"{total_allocated:,.0f}",
                        f"{(total_allocated/params['total_budget'])*100:.1f}% kullanım"
                    )
                
                with col2:
                    st.metric(
                        "Servis Edilen",
                        stores_served,
                        f"{(stores_served/len(optimized_df))*100:.1f}% coverage"
                    )
                
                with col3:
                    avg_allocation = optimized_df[optimized_df['ALLOCATED_QTY'] > 0]['ALLOCATED_QTY'].mean()
                    st.metric("Ort. Sevkiyat", f"{avg_allocation:,.0f}")
                
                with col4:
                    st.metric("Karşılama Oranı", f"{fulfillment_rate:.1f}%")
                
                with col5:
                    st.metric("Yeni Ort. WOS", f"{avg_new_wos:.2f}")
                
                # Risk analizi
                st.markdown("---")
                st.subheader("⚠️ Stockout Risk Analizi")
                
                risk_summary = optimized_df[optimized_df['ALLOCATED_QTY'] > 0]['STOCKOUT_RISK'].value_counts()
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    high_risk = risk_summary.get('High', 0)
                    st.metric("🔴 Yüksek Risk", high_risk)
                with col2:
                    medium_risk = risk_summary.get('Medium', 0)
                    st.metric("🟡 Orta Risk", medium_risk)
                with col3:
                    low_risk = risk_summary.get('Low', 0)
                    st.metric("🟢 Düşük Risk", low_risk)
                
                # Detay tablo
                st.markdown("---")
                st.subheader("📋 Sevkiyat Detayları")
                
                # Filtreler
                col1, col2, col3 = st.columns(3)
                with col1:
                    show_only_allocated = st.checkbox("Sadece Sevkiyat Yapılanları Göster", value=True)
                with col2:
                    risk_filter = st.multiselect("Risk Filtresi", ['High', 'Medium', 'Low'], default=['High', 'Medium', 'Low'])
                with col3:
                    min_allocation_filter = st.number_input("Minimum Sevkiyat", value=0, min_value=0)
                
                # Filtrelenmiş veri
                display_df = optimized_df.copy()
                
                if show_only_allocated:
                    display_df = display_df[display_df['ALLOCATED_QTY'] > 0]
                
                display_df = display_df[display_df['STOCKOUT_RISK'].isin(risk_filter)]
                display_df = display_df[display_df['ALLOCATED_QTY'] >= min_allocation_filter]
                
                # Gösterilecek kolonlar
                display_cols = [
                    'STORE_CODE', 'PRODUCT_CODE', 'AVAILABLE_STOCK', 'WEEKLY_SALES',
                    'WEEKS_OF_SUPPLY', 'SHIPMENT_NEED', 'ALLOCATED_QTY',
                    'NEW_STOCK', 'NEW_WOS', 'STOCKOUT_RISK', 'PRIORITY_SCORE'
                ]
                
                display_df['FULFILLMENT_%'] = (display_df['ALLOCATED_QTY'] / display_df['SHIPMENT_NEED'] * 100).round(1)
                display_df['FULFILLMENT_%'] = display_df['FULFILLMENT_%'].fillna(0)
                
                display_cols.append('FULFILLMENT_%')
                
                st.dataframe(
                    display_df[display_cols].style.background_gradient(
                        subset=['PRIORITY_SCORE', 'FULFILLMENT_%'],
                        cmap='RdYlGn'
                    ).applymap(
                        lambda x: 'background-color: #ffcccc' if x == 'High' else (
                            'background-color: #fff4cc' if x == 'Medium' else ''
                        ),
                        subset=['STOCKOUT_RISK']
                    ),
                    use_container_width=True,
                    height=400
                )
                
                # Export butonları
                col1, col2 = st.columns(2)
                
                with col1:
                    csv = display_df[display_cols].to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Detay Planı İndir (CSV)",
                        data=csv,
                        file_name=f"sevkiyat_detay_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                
                with col2:
                    # Store özet
                    store_summary = generate_store_summary(optimized_df)
                    csv_summary = store_summary.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Store Özet İndir (CSV)",
                        data=csv_summary,
                        file_name=f"store_ozet_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
        
        # ============== TAB 4: MATRİS ==============
        with tab4:
            st.subheader("📋 Sevkiyat Matrisi (Store x Product)")
            
            if 'optimized_df' not in st.session_state:
                st.warning("⚠️ Lütfen önce optimizasyon çalıştırın!")
                return
            
            optimized_df = st.session_state.optimized_df
            allocated_df = optimized_df[optimized_df['ALLOCATED_QTY'] > 0]
            
            # Filtreler
            col1, col2 = st.columns(2)
            
            with col1:
                available_stores = sorted(allocated_df['STORE_CODE'].unique())
                
                store_select_mode = st.radio("Store Seçimi", ["Manuel", "Tümü", "İlk N"])
                
                if store_select_mode == "Manuel":
                    selected_stores = st.multiselect(
                        "Store Seç",
                        options=available_stores,
                        default=available_stores[:min(10, len(available_stores))]
                    )
                elif store_select_mode == "İlk N":
                    n_stores = st.number_input("Kaç Store?", value=10, min_value=1, max_value=len(available_stores))
                    selected_stores = available_stores[:n_stores]
                else:
                    selected_stores = available_stores
            
            with col2:
                available_products = sorted(allocated_df['PRODUCT_CODE'].unique())
                
                product_select_mode = st.radio("Ürün Seçimi", ["Manuel", "Tümü", "İlk N"])
                
                if product_select_mode == "Manuel":
                    selected_products = st.multiselect(
                        "Ürün Seç",
                        options=available_products,
                        default=available_products[:min(10, len(available_products))]
                    )
                elif product_select_mode == "İlk N":
                    n_products = st.number_input("Kaç Ürün?", value=10, min_value=1, max_value=len(available_products))
                    selected_products = available_products[:n_products]
                else:
                    selected_products = available_products
            
            if selected_stores and selected_products:
                if st.button("📊 Matris Oluştur", type="primary"):
                    with st.spinner("Matris oluşturuluyor..."):
                        matrix_df = generate_shipment_matrix(
                            allocated_df,
                            selected_stores,
                            selected_products
                        )
                        st.session_state.matrix_df = matrix_df
                        st.success("✅ Matris oluşturuldu!")
                
                if 'matrix_df' in st.session_state:
                    matrix_df = st.session_state.matrix_df
                    
                    st.info(f"📊 Matris Boyutu: {len(selected_stores)} Store x {len(selected_products)} Ürün")
                    
                    # Matris gösterimi
                    st.dataframe(
                        matrix_df.set_index('STORE_CODE').style.background_gradient(cmap='YlGn'),
                        use_container_width=True,
                        height=600
                    )
                    
                    # Export
                    csv = matrix_df.to_csv(index=False, encoding='utf-8-sig')
                    st.download_button(
                        label="📥 Matrisi İndir (CSV)",
                        data=csv,
                        file_name=f"sevkiyat_matrisi_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv"
                    )
            else:
                st.warning("⚠️ Lütfen en az 1 store ve 1 ürün seçin!")
        
        # ============== TAB 5: ANALİZLER ==============
        with tab5:
            st.subheader("📈 Detaylı Analizler")
            
            if 'optimized_df' not in st.session_state:
                st.warning("⚠️ Lütfen önce optimizasyon çalıştırın!")
                return
            
            optimized_df = st.session_state.optimized_df
            
            analysis_type = st.selectbox(
                "Analiz Türü",
                ["Store Bazlı", "Ürün Bazlı", "WOS Analizi", "Öncelik Analizi"]
            )
            
            if analysis_type == "Store Bazlı":
                st.subheader("🏪 Store Bazlı Analiz")
                
                store_summary = generate_store_summary(optimized_df)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Store", len(store_summary))
                with col2:
                    served_stores = (store_summary['TOTAL_ALLOCATED'] > 0).sum()
                    st.metric("Servis Edilen Store", served_stores)
                with col3:
                    avg_fulfillment = store_summary['FULFILLMENT_%'].mean()
                    st.metric("Ort. Karşılama", f"{avg_fulfillment:.1f}%")
                
                st.dataframe(
                    store_summary.style.background_gradient(
                        subset=['TOTAL_ALLOCATED', 'FULFILLMENT_%'],
                        cmap='RdYlGn'
                    ),
                    use_container_width=True,
                    height=400
                )
                
                csv = store_summary.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Store Analizi İndir",
                    data=csv,
                    file_name=f"store_analiz_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            elif analysis_type == "Ürün Bazlı":
                st.subheader("📦 Ürün Bazlı Analiz")
                
                product_summary = generate_product_summary(optimized_df)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Toplam Ürün", len(product_summary))
                with col2:
                    served_products = (product_summary['TOTAL_ALLOCATED'] > 0).sum()
                    st.metric("Sevk Edilen Ürün", served_products)
                with col3:
                    avg_fulfillment = product_summary['FULFILLMENT_%'].mean()
                    st.metric("Ort. Karşılama", f"{avg_fulfillment:.1f}%")
                
                st.dataframe(
                    product_summary.style.background_gradient(
                        subset=['TOTAL_ALLOCATED', 'FULFILLMENT_%'],
                        cmap='RdYlGn'
                    ),
                    use_container_width=True,
                    height=400
                )
                
                csv = product_summary.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Ürün Analizi İndir",
                    data=csv,
                    file_name=f"urun_analiz_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            elif analysis_type == "WOS Analizi":
                st.subheader("📊 WOS Dağılım Analizi")
                
                allocated_df = optimized_df[optimized_df['ALLOCATED_QTY'] > 0]
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Mevcut WOS Dağılımı**")
                    wos_bins = [0, 2, 4, 6, 8, float('inf')]
                    wos_labels = ['0-2', '2-4', '4-6', '6-8', '8+']
                    allocated_df['WOS_RANGE'] = pd.cut(allocated_df['WEEKS_OF_SUPPLY'], bins=wos_bins, labels=wos_labels)
                    wos_dist = allocated_df['WOS_RANGE'].value_counts().sort_index()
                    st.bar_chart(wos_dist)
                
                with col2:
                    st.markdown("**Yeni WOS Dağılımı**")
                    allocated_df['NEW_WOS_RANGE'] = pd.cut(allocated_df['NEW_WOS'], bins=wos_bins, labels=wos_labels)
                    new_wos_dist = allocated_df['NEW_WOS_RANGE'].value_counts().sort_index()
                    st.bar_chart(new_wos_dist)
                
                st.markdown("---")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_old_wos = allocated_df['WEEKS_OF_SUPPLY'].mean()
                    st.metric("Eski Ort. WOS", f"{avg_old_wos:.2f}")
                with col2:
                    avg_new_wos = allocated_df['NEW_WOS'].mean()
                    delta_wos = avg_new_wos - avg_old_wos
                    st.metric("Yeni Ort. WOS", f"{avg_new_wos:.2f}", f"{delta_wos:+.2f}")
                with col3:
                    improvement = (delta_wos / avg_old_wos * 100) if avg_old_wos > 0 else 0
                    st.metric("İyileşme", f"{improvement:.1f}%")
            
            elif analysis_type == "Öncelik Analizi":
                st.subheader("🎯 Öncelik Skorları Analizi")
                
                allocated_df = optimized_df[optimized_df['ALLOCATED_QTY'] > 0]
                
                # Skor dağılımı
                st.markdown("**Öncelik Skoru Dağılımı**")
                st.bar_chart(allocated_df['PRIORITY_SCORE'].value_counts().sort_index())
                
                st.markdown("---")
                
                # En yüksek ve en düşük skorlar
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔝 En Yüksek Öncelikli (Top 10)**")
                    top_priority = allocated_df.nlargest(10, 'PRIORITY_SCORE')[
                        ['STORE_CODE', 'PRODUCT_CODE', 'PRIORITY_SCORE', 'ALLOCATED_QTY', 'WEEKS_OF_SUPPLY']
                    ]
                    st.dataframe(top_priority, use_container_width=True)
                
                with col2:
                    st.markdown("**📉 En Düşük Öncelikli (Bottom 10)**")
                    bottom_priority = allocated_df.nsmallest(10, 'PRIORITY_SCORE')[
                        ['STORE_CODE', 'PRODUCT_CODE', 'PRIORITY_SCORE', 'ALLOCATED_QTY', 'WEEKS_OF_SUPPLY']
                    ]
                    st.dataframe(bottom_priority, use_container_width=True)
        
        # ============== TAB 6: MALİYET ==============
        with tab6:
            st.subheader("💰 Maliyet Analizi")
            
            if 'optimized_df' not in st.session_state:
                st.warning("⚠️ Lütfen önce optimizasyon çalıştırın!")
                return
            
            optimized_df = st.session_state.optimized_df
            
            # Maliyet parametreleri
            col1, col2, col3 = st.columns(3)
            
            with col1:
                cost_per_unit = st.number_input("Birim Maliyet (₺)", value=10.0, min_value=0.1, step=0.5)
            
            with col2:
                handling_cost = st.number_input("Handling Maliyeti (₺/adet)", value=0.5, min_value=0.0, step=0.1)
            
            with col3:
                transport_cost_per_store = st.number_input("Store Başı Taşıma (₺)", value=100.0, min_value=0.0, step=10.0)
            
            if st.button("💵 Maliyet Hesapla", type="primary"):
                with st.spinner("Maliyetler hesaplanıyor..."):
                    cost_df = calculate_shipment_costs(optimized_df, cost_per_unit, handling_cost)
                    
                    # Store sayısını ekle
                    stores_served = (cost_df['ALLOCATED_QTY'] > 0)['STORE_CODE'].nunique() if 'STORE_CODE' in cost_df.columns else 0
                    total_transport = stores_served * transport_cost_per_store
                    
                    st.session_state.cost_df = cost_df
                    st.session_state.total_transport = total_transport
                    st.success("✅ Maliyetler hesaplandı!")
            
            if 'cost_df' in st.session_state:
                cost_df = st.session_state.cost_df
                total_transport = st.session_state.total_transport
                
                allocated_cost_df = cost_df[cost_df['ALLOCATED_QTY'] > 0]
                
                # Toplam maliyetler
                st.markdown("---")
                st.subheader("📊 Maliyet Özeti")
                
                col1, col2, col3, col4 = st.columns(4)
                
                total_unit_cost = (allocated_cost_df['ALLOCATED_QTY'] * cost_per_unit).sum()
                total_handling = allocated_cost_df['HANDLING_COST'].sum()
                total_cost = total_unit_cost + total_handling + total_transport
                cost_per_allocated = total_cost / allocated_cost_df['ALLOCATED_QTY'].sum() if allocated_cost_df['ALLOCATED_QTY'].sum() > 0 else 0
                
                with col1:
                    st.metric("Birim Maliyeti", f"₺{total_unit_cost:,.2f}")
                
                with col2:
                    st.metric("Handling", f"₺{total_handling:,.2f}")
                
                with col3:
                    st.metric("Taşıma", f"₺{total_transport:,.2f}")
                
                with col4:
                    st.metric("TOPLAM", f"₺{total_cost:,.2f}", f"₺{cost_per_allocated:.2f}/adet")
                
                # Detay tablo
                st.markdown("---")
                st.subheader("📋 Maliyet Detayları")
                
                display_cost_df = allocated_cost_df[[
                    'STORE_CODE', 'PRODUCT_CODE', 'ALLOCATED_QTY',
                    'UNIT_COST', 'HANDLING_COST', 'TOTAL_COST'
                ]].copy()
                
                st.dataframe(
                    display_cost_df.style.background_gradient(subset=['TOTAL_COST'], cmap='YlOrRd'),
                    use_container_width=True,
                    height=400
                )
                
                # Export
                csv = display_cost_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📥 Maliyet Raporu İndir",
                    data=csv,
                    file_name=f"maliyet_raporu_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
    
    if __name__ == "__main__":
        main()

# ============================================
# PURCHASE ORDER MODÜLÜ
# ============================================
elif menu_option == '💵 Purchase Order (PO)':
    st.sidebar.title("💵 Alım Sipariş (Purchase Order)")
    menu = st.sidebar.radio(
        "Menü",
        ["🏠 Ana Sayfa", "💵 Alım Sipariş Hesaplama", "📊 Alım Sipariş Raporları", "📦 Depo Bazlı Sipariş"]
    )
    
    # Veri yükleme fonksiyonu
    def load_po_data():
        """PO için gerekli verileri kontrol et"""
        required = {
            'anlik_stok_satis': st.session_state.anlik_stok_satis,
            'depo_stok': st.session_state.depo_stok,
            'kpi': st.session_state.kpi
        }
        
        missing = [k for k, v in required.items() if v is None]
        return missing
    
    # ============================================
    # 🏠 ANA SAYFA
    # ============================================
    if menu == "🏠 Ana Sayfa":
        st.title("💵 Alım Sipariş (Purchase Order) Sistemi")
        st.markdown("---")
        
        # VERİ KONTROLÜ
        required_data = {
            "Anlık Stok/Satış": st.session_state.anlik_stok_satis,
            "Depo Stok": st.session_state.depo_stok,
            "KPI": st.session_state.kpi
        }
        
        optional_data = {
            "PO Yasak": st.session_state.po_yasak,
            "PO Detay KPI": st.session_state.po_detay_kpi,
            "Ürün Master": st.session_state.urun_master,
            "Mağaza Master": st.session_state.magaza_master
        }
        
        missing_data = [name for name, data in required_data.items() if data is None]
        
        if missing_data:
            st.info("""
            **👉 Lütfen önce veri yükleme sayfasından CSV dosyalarınızı yükleyin.**
            
            **Zorunlu dosyalar:**
            - Anlık Stok/Satış
            - Depo Stok
            - KPI
            
            **Opsiyonel dosyalar (önerilir):**
            - Ürün Master (koli bilgisi, durum, ithal bilgisi için)
            - Mağaza Master (depo eşleştirme için)
            - PO Yasak (yasak ürünler ve açık siparişler için)
            - PO Detay KPI (marka/MG bazında özel hedefler için)
            """)
            
            st.stop()
        
        # Veri durumu
        st.markdown("### 📊 Veri Durumu")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Zorunlu Veriler:**")
            for name, data in required_data.items():
                if data is not None:
                    st.success(f"✅ {name}")
                else:
                    st.error(f"❌ {name}")
        
        with col2:
            st.markdown("**Opsiyonel Veriler:**")
            for name, data in optional_data.items():
                if data is not None:
                    st.success(f"✅ {name}")
                else:
                    st.warning(f"⚠️ {name}")
        
        st.markdown("---")
        
        st.markdown("""
        ### 🎯 Yenilikler ve Özellikler
        
        **🆕 Gelişmiş Özellikler:**
        
        1. **📋 PO Yasak Kontrolü**
           - Yasak ürünleri otomatik filtreleme
           - Açık sipariş miktarlarını düşme
        
        2. **🎯 Detaylı KPI Hedefleri**
           - Marka + Mal Grubu bazında özel cover ve marj hedefleri
           - Dinamik hedef yönetimi
        
        3. **📦 Segmentasyon ve Genleştirme**
           - Ürün ve mağaza segment bazında katsayı matrisi
           - Forward cover optimizasyonu
        
        4. **✅ Ürün Durumu Kontrolü**
           - Pasif ürünleri otomatik çıkarma
           - İthal ürünler için farklı forward cover
        
        5. **🏪 Depo Bazlı Çıktı**
           - Her depo için ayrı sipariş listesi
           - Mağaza-depo eşleştirmesi
        """)
    
    # ============================================
    # 💵 ALIM SİPARİŞ HESAPLAMA
    # ============================================
    elif menu == "💵 Alım Sipariş Hesaplama":
        st.title("💵 Alım Sipariş Hesaplama")
        st.markdown("---")
        
        # Veri kontrolleri
        missing = load_po_data()
        if missing:
            st.error(f"❌ Eksik veriler: {', '.join(missing)}")
            st.info("👉 Lütfen önce veri yükleme sayfasından gerekli verileri yükleyin.")
            st.stop()
        
        st.success("✅ Tüm gerekli veriler hazır!")
        
        # Opsiyonel veri bilgisi
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.session_state.magaza_master is not None:
                st.info("✅ Mağaza Master aktif")
            else:
                st.warning("⚠️ Mağaza Master yok (depo '1' atanacak)")
        with col2:
            if st.session_state.po_yasak is not None:
                st.info("✅ PO Yasak aktif")
            else:
                st.warning("⚠️ PO Yasak yok")
        with col3:
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
            num_rows="fixed"
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
        
        # HESAPLAMA BUTONU
        if st.button("🚀 PO İhtiyacı Hesapla", type="primary", use_container_width=True):
            try:
                with st.spinner("📊 Hesaplama yapılıyor..."):
                    start_time = time.time()
                    
                    # VERİLERİ HAZIRLA
                    anlik_df = st.session_state.anlik_stok_satis.copy()
                    depo_df = st.session_state.depo_stok.copy()
                    kpi_df = st.session_state.kpi.copy()
                    cover_matrix = st.session_state.cover_segment_matrix.copy()
                    
                    # Veri boyutları
                    st.write("**📊 Veri Boyutları:**")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Anlık Stok/Satış", f"{len(anlik_df):,}")
                    with col2:
                        st.metric("Depo Stok", f"{len(depo_df):,}")
                    with col3:
                        st.metric("KPI", f"{len(kpi_df):,}")
                    
                    # Veri tiplerini düzelt
                    anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                    depo_df['urun_kod'] = depo_df['urun_kod'].astype(str)
                    
                    # MAĞAZA-DEPO EŞLEŞTİRMESİ
                    if st.session_state.magaza_master is not None:
                        st.info("🔗 Mağaza-Depo eşleştirmesi yapılıyor...")
                        magaza_master = st.session_state.magaza_master.copy()
                        magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                        magaza_master['depo_kod'] = magaza_master['depo_kod'].astype(str)
                        
                        anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                        
                        df = anlik_df.merge(
                            magaza_master[['magaza_kod', 'depo_kod']],
                            on='magaza_kod',
                            how='left'
                        )
                        
                        eksik_depo = df['depo_kod'].isna().sum()
                        if eksik_depo > 0:
                            st.warning(f"⚠️ {eksik_depo} satırda depo kodu bulunamadı (default '1' atanacak)")
                            df['depo_kod'] = df['depo_kod'].fillna('1')
                    else:
                        df = anlik_df.copy()
                        df['depo_kod'] = '1'
                        st.info("ℹ️ Mağaza Master yok, tüm satırlar depo '1' olarak atandı")
                    
                    # DEPO STOK EKLE
                    st.info("📦 Depo stokları ekleniyor...")
                    
                    depo_df['depo_kod'] = depo_df.get('depo_kod', '1').astype(str)
                    
                    depo_stok_map = depo_df.groupby(['depo_kod', 'urun_kod'])['stok'].sum().reset_index()
                    depo_stok_map.columns = ['depo_kod', 'urun_kod', 'depo_stok']
                    
                    df = df.merge(
                        depo_stok_map,
                        on=['depo_kod', 'urun_kod'],
                        how='left'
                    )
                    df['depo_stok'] = df['depo_stok'].fillna(0)
                    
                    # DEPO-ÜRÜN BAZINDA GRUPLA VE PO HESAPLA
                    st.info("📊 Depo-Ürün bazında gruplama ve PO hesaplama...")
                    
                    # Gerekli kolonları kontrol et
                    required_cols = ['satis', 'stok', 'yol']
                    for col in required_cols:
                        if col not in df.columns:
                            df[col] = 0
                    
                    po_sonuc = df.groupby(['depo_kod', 'urun_kod']).agg({
                        'satis': 'sum',
                        'stok': 'sum',
                        'yol': 'sum',
                        'depo_stok': 'first'
                    }).reset_index()
                    
                    po_sonuc.columns = [
                        'depo_kod', 'urun_kod', 'toplam_satis', 'toplam_magaza_stok', 
                        'toplam_yol', 'depo_stok'
                    ]
                    
                    # Brüt ihtiyaç
                    po_sonuc['brut_ihtiyac'] = (forward_cover + fc_ek) * po_sonuc['toplam_satis']
                    
                    # Net ihtiyaç
                    po_sonuc['net_ihtiyac'] = (
                        po_sonuc['brut_ihtiyac'] - 
                        po_sonuc['toplam_magaza_stok'] - 
                        po_sonuc['toplam_yol'] - 
                        po_sonuc['depo_stok']
                    )
                    
                    # PO ihtiyacı
                    po_sonuc['po_ihtiyac'] = po_sonuc['net_ihtiyac'].clip(lower=0)
                    
                    # DEPO STOK EŞİĞİ KONTROLÜ
                    yuksek_stok_sayisi = (po_sonuc['depo_stok'] > depo_stok_threshold).sum()
                    po_sonuc.loc[po_sonuc['depo_stok'] > depo_stok_threshold, 'po_ihtiyac'] = 0
                    
                    if yuksek_stok_sayisi > 0:
                        st.info(f"ℹ️ {yuksek_stok_sayisi:,} üründe depo stok > {depo_stok_threshold}, PO sıfırlandı")
                    
                    # Sadece pozitif PO'ları al
                    po_sonuc_pozitif = po_sonuc[po_sonuc['po_ihtiyac'] > 0].copy()
                    
                    # Sayıları yuvarla
                    for col in ['po_ihtiyac', 'brut_ihtiyac', 'net_ihtiyac', 'toplam_satis', 'toplam_magaza_stok', 'toplam_yol', 'depo_stok']:
                        if col in po_sonuc_pozitif.columns:
                            po_sonuc_pozitif[col] = po_sonuc_pozitif[col].round().astype(int)
                    
                    end_time = time.time()
                    
                    # KAYDET
                    st.session_state.alim_siparis_sonuc = po_sonuc_pozitif.copy()
                    
                    st.success(f"✅ Hesaplama tamamlandı!")
                    st.balloons()
                    
                    # ÖZET METRİKLER
                    st.markdown("---")
                    st.subheader("📊 Hesaplama Özet Metrikleri")
                    
                    toplam_po_adet = po_sonuc_pozitif['po_ihtiyac'].sum()
                    urun_sayisi_po = po_sonuc_pozitif['urun_kod'].nunique()
                    depo_sayisi = po_sonuc_pozitif['depo_kod'].nunique()
                    algoritma_suresi = end_time - start_time
                    
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("🎯 Toplam PO Adet", f"{toplam_po_adet:,.0f}")
                    
                    with col2:
                        st.metric("🏷️ Ürün Sayısı", f"{urun_sayisi_po:,}")
                    
                    with col3:
                        st.metric("🏪 Depo Sayısı", f"{depo_sayisi}")
                    
                    with col4:
                        st.metric("⏱️ İşlem Süresi", f"{algoritma_suresi:.2f} sn")
                    
                    # DEPO BAZINDA ÖZET
                    st.markdown("---")
                    st.subheader("🏪 Depo Bazında Özet")
                    
                    depo_ozet = po_sonuc_pozitif.groupby('depo_kod').agg({
                        'po_ihtiyac': 'sum',
                        'urun_kod': 'nunique'
                    }).reset_index()
                    
                    depo_ozet.columns = ['Depo Kodu', 'Toplam PO Adet', 'Ürün Sayısı']
                    depo_ozet = depo_ozet.sort_values('Toplam PO Adet', ascending=False)
                    
                    st.dataframe(depo_ozet, use_container_width=True, hide_index=True)
                    
                    # DETAY TABLO
                    st.markdown("---")
                    st.subheader("📋 PO Detayı (Top 100)")
                    
                    display_df = po_sonuc_pozitif.sort_values('po_ihtiyac', ascending=False).head(100)
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
    elif menu == "📊 Alım Sipariş Raporları":
        st.title("📊 Alım Sipariş Raporları")
        st.markdown("---")
        
        if st.session_state.alim_siparis_sonuc is None:
            st.warning("⚠️ Henüz alım sipariş hesaplaması yapılmadı!")
            st.info("Lütfen önce 'Alım Sipariş Hesaplama' menüsünden hesaplama yapın.")
            st.stop()
        
        sonuc_df = st.session_state.alim_siparis_sonuc.copy()
        
        # Genel özet
        st.subheader("📈 Genel Özet")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📦 Toplam PO", f"{sonuc_df['po_ihtiyac'].sum():,.0f}")
        
        with col2:
            st.metric("🏷️ Ürün Sayısı", f"{sonuc_df['urun_kod'].nunique()}")
        
        with col3:
            if 'depo_kod' in sonuc_df.columns:
                st.metric("🏪 Depo Sayısı", f"{sonuc_df['depo_kod'].nunique()}")
        
        st.markdown("---")
        
        # Detay tablo
        st.subheader("📋 PO Detay Tablosu")
        
        display_df = sonuc_df.sort_values('po_ihtiyac', ascending=False)
        
        st.dataframe(display_df, use_container_width=True, height=500)
        
        # Export
        csv_data = display_df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 Tüm Veriyi İndir (CSV)",
            data=csv_data,
            file_name=f"po_rapor_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )
    
    # ============================================
    # 📦 DEPO BAZLI SİPARİŞ
    # ============================================
    elif menu == "📦 Depo Bazlı Sipariş":
        st.title("📦 Depo Bazlı Sipariş Listeleri")
        st.markdown("---")
        
        if st.session_state.alim_siparis_sonuc is None:
            st.warning("⚠️ Henüz alım sipariş hesaplaması yapılmadı!")
            st.info("Lütfen önce 'Alım Sipariş Hesaplama' menüsünden hesaplama yapın.")
            st.stop()
        
        sonuc_df = st.session_state.alim_siparis_sonuc.copy()
        
        # Depo kodu yoksa default ata
        if 'depo_kod' not in sonuc_df.columns:
            sonuc_df['depo_kod'] = '1'
            st.info("ℹ️ Depo kodu bulunamadı, tüm siparişler depo '1' olarak gösteriliyor")
        
        # Depo seçimi
        depo_listesi = sorted(sonuc_df['depo_kod'].dropna().unique())
        
        selected_depo = st.selectbox(
            "📍 Depo Seçin",
            options=['Tümü'] + list(depo_listesi)
        )
        
        # Seçili depoya göre filtrele
        if selected_depo != 'Tümü':
            display_df = sonuc_df[sonuc_df['depo_kod'] == selected_depo].copy()
            st.subheader(f"📦 {selected_depo} Deposu Sipariş Listesi")
        else:
            display_df = sonuc_df.copy()
            st.subheader("📦 Tüm Depolar Sipariş Listesi")
        
        # Özet metrikler
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("📦 Toplam PO", f"{display_df['po_ihtiyac'].sum():,.0f}")
        
        with col2:
            st.metric("🏷️ Ürün Sayısı", f"{display_df['urun_kod'].nunique()}")
        
        with col3:
            if 'toplam_satis' in display_df.columns:
                st.metric("💰 Toplam Satış", f"{display_df['toplam_satis'].sum():,.0f}")
        
        st.markdown("---")
        
        # Detay tablo
        st.subheader("📋 Sipariş Detayı")
        
        final_df = display_df.sort_values('po_ihtiyac', ascending=False)
        
        st.dataframe(final_df, use_container_width=True, height=500)
        
        # Export
        csv_data = final_df.to_csv(index=False, encoding='utf-8-sig')
        filename = f"po_siparis_{selected_depo}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M')}.csv"
        
        st.download_button(
            label="📥 Bu Listeyi İndir (CSV)",
            data=csv_data,
            file_name=filename,
            mime="text/csv"
        )

# ============================================
# FOOTER
# ============================================
st.markdown("---")
st.markdown("""<div style='text-align: center; color: #666; font-size: 12px; padding: 20px;'>
    <strong>THORIUS AR4U</strong> - Retail Analytics Platform v2.0<br>
    🎫 Tek token ile tüm modüllere erişim
</div>""", unsafe_allow_html=True)
