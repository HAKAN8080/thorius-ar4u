import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import io
import time
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="Retail Analytics", page_icon="📊", layout="wide", initial_sidebar_state="expanded")

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
# SESSION STATE
# ============================================
for key in ['inventory_df', 'urun_master', 'magaza_master', 'anlik_stok_satis', 'depo_stok', 'kpi', 'po_yasak', 'po_detay_kpi', 'alim_siparis_sonuc', 'sevkiyat_sonuc']:
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
    - Sevkiyat ve PO verileri yükleme
    - Veri validasyonu ve önizleme
    - Master data yönetimi
    
    #### 🚢 Sevkiyat Planlama
    - KMeans clustering ile store gruplaması
    - Bütçe bazlı sevkiyat optimizasyonu
    - WOS (Weeks of Supply) optimizasyonu
    - Öncelik skorlama sistemi
    
    #### 💵 Purchase Order (PO)
    - Depo bazlı sipariş hesaplama
    - Cover süre optimizasyonu
    - Yasak ürün ve açık sipariş kontrolü
    """)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Sevkiyat Verileri**")
        if st.session_state.inventory_df is not None:
            st.success(f"✅ Envanter verisi yüklü ({len(st.session_state.inventory_df):,} satır)")
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
    
    st.markdown("---")
    st.info("👈 **Sol menüden** istediğiniz modüle geçiş yapabilirsiniz. Token tekrar düşmez!")


# ============================================
# VERİ YÜKLEME MODÜLÜ
# ============================================
elif menu_option == '📂 Veri Yükleme':
    st.title("📂 Veri Yükleme")
    st.markdown("---")
    
    # Session state başlatma
    if 'inventory_df' not in st.session_state:
        st.session_state.inventory_df = None
    if 'urun_master' not in st.session_state:
        st.session_state.urun_master = None
    if 'magaza_master' not in st.session_state:
        st.session_state.magaza_master = None
    if 'anlik_stok_satis' not in st.session_state:
        st.session_state.anlik_stok_satis = None
    if 'depo_stok' not in st.session_state:
        st.session_state.depo_stok = None
    if 'kpi' not in st.session_state:
        st.session_state.kpi = None
    if 'po_yasak' not in st.session_state:
        st.session_state.po_yasak = None
    
    # Tab yapısı
    tab1, tab2, tab3 = st.tabs(["📊 Sevkiyat Verileri", "💵 PO Verileri", "✅ Veri Durumu"])
    
    # ============== TAB 1: SEVKİYAT VERİLERİ ==============
    with tab1:
        st.subheader("📦 Sevkiyat Planlama İçin Veri Yükleme")
        st.markdown("---")
        
        # Inventory data upload
        st.markdown("### 📊 Envanter Verisi (Zorunlu)")
        st.info("""
        **Gerekli kolonlar:**
        - STORE_CODE: Mağaza kodu
        - PRODUCT_CODE: Ürün kodu
        - AVAILABLE_STOCK: Mevcut stok
        - WEEKLY_SALES: Haftalık satış
        - WEEKS_OF_SUPPLY: Haftalık tedarik süresi
        """)
        
        inventory_file = st.file_uploader(
            "Envanter CSV dosyasını yükleyin",
            type=['csv'],
            key='inventory_upload'
        )
        
        if inventory_file is not None:
            try:
                inventory_df = pd.read_csv(inventory_file)
                
                # Kolon kontrolü
                required_cols = ['STORE_CODE', 'PRODUCT_CODE', 'AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY']
                missing_cols = [col for col in required_cols if col not in inventory_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Eksik kolonlar: {', '.join(missing_cols)}")
                else:
                    # Veri tiplerini düzenle
                    inventory_df['STORE_CODE'] = inventory_df['STORE_CODE'].astype(str)
                    inventory_df['PRODUCT_CODE'] = inventory_df['PRODUCT_CODE'].astype(str)
                    
                    # Sayısal kolonları kontrol et
                    for col in ['AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY']:
                        inventory_df[col] = pd.to_numeric(inventory_df[col], errors='coerce').fillna(0)
                    
                    st.session_state.inventory_df = inventory_df
                    
                    st.success(f"✅ {len(inventory_df):,} satır yüklendi!")
                    
                    # Özet istatistikler
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Toplam Mağaza", inventory_df['STORE_CODE'].nunique())
                    
                    with col2:
                        st.metric("Toplam Ürün", inventory_df['PRODUCT_CODE'].nunique())
                    
                    with col3:
                        st.metric("Ortalama WOS", f"{inventory_df['WEEKS_OF_SUPPLY'].mean():.2f}")
                    
                    # Önizleme
                    with st.expander("👁️ Veri Önizleme"):
                        st.dataframe(inventory_df.head(100), use_container_width=True)
            
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
    
    # ============== TAB 2: PO VERİLERİ ==============
    with tab2:
        st.subheader("💵 Purchase Order İçin Veri Yükleme")
        st.markdown("---")
        
        # Anlık Stok/Satış
        st.markdown("### 📊 Anlık Stok/Satış (Zorunlu)")
        anlik_file = st.file_uploader(
            "Anlık Stok/Satış CSV dosyasını yükleyin",
            type=['csv'],
            key='anlik_upload'
        )
        
        if anlik_file is not None:
            try:
                anlik_df = pd.read_csv(anlik_file)
                
                # Kolon kontrolü
                required_cols = ['urun_kod', 'magaza_kod', 'satis', 'stok', 'yol']
                missing_cols = [col for col in required_cols if col not in anlik_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Eksik kolonlar: {', '.join(missing_cols)}")
                else:
                    anlik_df['urun_kod'] = anlik_df['urun_kod'].astype(str)
                    anlik_df['magaza_kod'] = anlik_df['magaza_kod'].astype(str)
                    
                    for col in ['satis', 'stok', 'yol']:
                        anlik_df[col] = pd.to_numeric(anlik_df[col], errors='coerce').fillna(0)
                    
                    st.session_state.anlik_stok_satis = anlik_df
                    st.success(f"✅ Anlık Stok/Satış yüklendi: {len(anlik_df):,} satır")
            
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        
        st.markdown("---")
        
        # Depo Stok
        st.markdown("### 📦 Depo Stok (Zorunlu)")
        depo_file = st.file_uploader(
            "Depo Stok CSV dosyasını yükleyin",
            type=['csv'],
            key='depo_upload'
        )
        
        if depo_file is not None:
            try:
                depo_df = pd.read_csv(depo_file)
                
                required_cols = ['urun_kod', 'depo_kod', 'stok']
                missing_cols = [col for col in required_cols if col not in depo_df.columns]
                
                if missing_cols:
                    st.error(f"❌ Eksik kolonlar: {', '.join(missing_cols)}")
                else:
                    depo_df['urun_kod'] = depo_df['urun_kod'].astype(str)
                    depo_df['depo_kod'] = depo_df['depo_kod'].astype(str)
                    depo_df['stok'] = pd.to_numeric(depo_df['stok'], errors='coerce').fillna(0)
                    
                    st.session_state.depo_stok = depo_df
                    st.success(f"✅ Depo Stok yüklendi: {len(depo_df):,} satır")
            
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        
        st.markdown("---")
        
        # KPI
        st.markdown("### 🎯 KPI (Zorunlu)")
        kpi_file = st.file_uploader(
            "KPI CSV dosyasını yükleyin",
            type=['csv'],
            key='kpi_upload'
        )
        
        if kpi_file is not None:
            try:
                kpi_df = pd.read_csv(kpi_file)
                st.session_state.kpi = kpi_df
                st.success(f"✅ KPI yüklendi: {len(kpi_df):,} satır")
                
                with st.expander("👁️ KPI Önizleme"):
                    st.dataframe(kpi_df.head(50), use_container_width=True)
            
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
        
        st.markdown("---")
        
        # Opsiyonel dosyalar
        st.markdown("### 📋 Opsiyonel Dosyalar")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Ürün Master
            st.markdown("**Ürün Master**")
            urun_master_file = st.file_uploader(
                "Ürün Master CSV",
                type=['csv'],
                key='urun_master_upload'
            )
            
            if urun_master_file is not None:
                try:
                    urun_master = pd.read_csv(urun_master_file)
                    if 'urun_kod' in urun_master.columns:
                        urun_master['urun_kod'] = urun_master['urun_kod'].astype(str)
                    st.session_state.urun_master = urun_master
                    st.success(f"✅ Ürün Master: {len(urun_master):,} satır")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        with col2:
            # Mağaza Master
            st.markdown("**Mağaza Master**")
            magaza_master_file = st.file_uploader(
                "Mağaza Master CSV",
                type=['csv'],
                key='magaza_master_upload'
            )
            
            if magaza_master_file is not None:
                try:
                    magaza_master = pd.read_csv(magaza_master_file)
                    if 'magaza_kod' in magaza_master.columns:
                        magaza_master['magaza_kod'] = magaza_master['magaza_kod'].astype(str)
                    if 'depo_kod' in magaza_master.columns:
                        magaza_master['depo_kod'] = magaza_master['depo_kod'].astype(str)
                    st.session_state.magaza_master = magaza_master
                    st.success(f"✅ Mağaza Master: {len(magaza_master):,} satır")
                except Exception as e:
                    st.error(f"❌ Hata: {str(e)}")
        
        # PO Yasak
        st.markdown("**PO Yasak Listesi**")
        po_yasak_file = st.file_uploader(
            "PO Yasak CSV",
            type=['csv'],
            key='po_yasak_upload'
        )
        
        if po_yasak_file is not None:
            try:
                po_yasak = pd.read_csv(po_yasak_file)
                if 'urun_kodu' in po_yasak.columns:
                    po_yasak['urun_kodu'] = po_yasak['urun_kodu'].astype(str)
                st.session_state.po_yasak = po_yasak
                st.success(f"✅ PO Yasak: {len(po_yasak):,} satır")
            except Exception as e:
                st.error(f"❌ Hata: {str(e)}")
    
    # ============== TAB 3: VERİ DURUMU ==============
    with tab3:
        st.subheader("✅ Yüklü Veri Durumu")
        st.markdown("---")
        
        # Sevkiyat verileri
        st.markdown("### 📦 Sevkiyat Planlama Verileri")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.session_state.inventory_df is not None:
                df = st.session_state.inventory_df
                st.success("✅ Envanter Verisi")
                st.write(f"- Satır sayısı: {len(df):,}")
                st.write(f"- Mağaza sayısı: {df['STORE_CODE'].nunique()}")
                st.write(f"- Ürün sayısı: {df['PRODUCT_CODE'].nunique()}")
            else:
                st.error("❌ Envanter Verisi yüklenmedi")
        
        st.markdown("---")
        
        # PO verileri
        st.markdown("### 💵 Purchase Order Verileri")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Zorunlu Veriler:**")
            
            if st.session_state.anlik_stok_satis is not None:
                df = st.session_state.anlik_stok_satis
                st.success("✅ Anlık Stok/Satış")
                st.write(f"- Satır: {len(df):,}")
            else:
                st.error("❌ Anlık Stok/Satış")
            
            if st.session_state.depo_stok is not None:
                df = st.session_state.depo_stok
                st.success("✅ Depo Stok")
                st.write(f"- Satır: {len(df):,}")
            else:
                st.error("❌ Depo Stok")
            
            if st.session_state.kpi is not None:
                df = st.session_state.kpi
                st.success("✅ KPI")
                st.write(f"- Satır: {len(df):,}")
            else:
                st.error("❌ KPI")
        
        with col2:
            st.markdown("**Opsiyonel Veriler:**")
            
            if st.session_state.urun_master is not None:
                st.success("✅ Ürün Master")
                st.write(f"- Satır: {len(st.session_state.urun_master):,}")
            else:
                st.warning("⚠️ Ürün Master")
            
            if st.session_state.magaza_master is not None:
                st.success("✅ Mağaza Master")
                st.write(f"- Satır: {len(st.session_state.magaza_master):,}")
            else:
                st.warning("⚠️ Mağaza Master")
            
            if st.session_state.po_yasak is not None:
                st.success("✅ PO Yasak")
                st.write(f"- Satır: {len(st.session_state.po_yasak):,}")
            else:
                st.warning("⚠️ PO Yasak")
        
        st.markdown("---")
        
        # Veri temizleme
        if st.button("🗑️ Tüm Verileri Temizle", type="secondary"):
            st.session_state.inventory_df = None
            st.session_state.anlik_stok_satis = None
            st.session_state.depo_stok = None
            st.session_state.kpi = None
            st.session_state.urun_master = None
            st.session_state.magaza_master = None
            st.session_state.po_yasak = None
            st.success("✅ Tüm veriler temizlendi!")
            st.rerun()

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
