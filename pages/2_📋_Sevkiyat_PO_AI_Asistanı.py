import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import time
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

st.set_page_config(page_title="Retail Analytics", page_icon="📊", layout="wide")

# TOKEN SİSTEMİ
def check_auth():
    if 'authenticated' not in st.session_state or not st.session_state.authenticated:
        st.error("⛔ Lütfen giriş yapın!")
        st.stop()

def deduct_tokens(n=10):
    if 'tokens_deducted' not in st.session_state:
        st.session_state.tokens_deducted = False
    if not st.session_state.tokens_deducted and 'username' in st.session_state:
        try:
            import sqlite3
            conn = sqlite3.connect('tokens.db')
            c = conn.cursor()
            c.execute('SELECT tokens FROM tokens WHERE username=?', (st.session_state.username,))
            r = c.fetchone()
            if r and r[0] >= n:
                c.execute('UPDATE tokens SET tokens=tokens-? WHERE username=?', (n, st.session_state.username))
                conn.commit()
                st.session_state.tokens_deducted = True
                st.session_state.current_tokens = r[0] - n
                conn.close()
            else:
                conn.close()
                st.error("⚠️ Yetersiz token!")
                st.stop()
        except:
            pass

check_auth()
deduct_tokens(10)

# SESSION STATE
for k in ['inventory_df', 'anlik_stok_satis', 'depo_stok', 'kpi', 'alim_siparis_sonuc']:
    if k not in st.session_state:
        st.session_state[k] = None

if 'segmentation_params' not in st.session_state:
    st.session_state.segmentation_params = {
        'product_ranges': [(0,4),(5,8),(9,12),(12,15),(15,20),(20,float('inf'))],
        'store_ranges': [(0,4),(5,8),(9,12),(12,15),(15,20),(20,float('inf'))]
    }
if 'cover_segment_matrix' not in st.session_state:
    st.session_state.cover_segment_matrix = None

# SIDEBAR
with st.sidebar:
    st.markdown("### 📊 THORIUS AR4U")
    st.markdown("**Retail Analytics**")
    st.markdown("---")
    if 'username' in st.session_state:
        st.markdown(f"""<div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding:15px; border-radius:10px; color:white;'>
        <div>👤 {st.session_state.username}</div>
        <div style='font-size:11px; margin-top:5px;'>🎫 Token: {st.session_state.get('current_tokens', 'N/A')}</div>
        </div>""", unsafe_allow_html=True)
    st.markdown("---")
    menu = st.radio("📋 Modül", ["🏠 Ana Sayfa", "📂 Veri Yükleme", "🚢 Sevkiyat", "💵 PO"])
    st.markdown("---")
    st.info("✅ Tek token\n📊 4 modül")

# ANA SAYFA
if menu == "🏠 Ana Sayfa":
    st.title("📊 Retail Analytics Platform")
    st.markdown("---")
    st.markdown("""
    ### 🎯 Hoş Geldiniz!
    
    **Tek token** ile tüm modüller:
    
    #### 📂 Veri Yükleme
    - Sevkiyat ve PO verileri
    - CSV yükleme ve validasyon
    
    #### 🚢 Sevkiyat Planlama
    - KMeans clustering
    - Bütçe optimizasyonu
    - WOS optimizasyonu
    
    ####💵 Purchase Order
    - Depo bazlı sipariş
    - Cover optimizasyonu
    - Segment matrisi
    """)
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        if st.session_state.inventory_df is not None:
            st.success(f"✅ Sevkiyat ({len(st.session_state.inventory_df):,} satır)")
        else:
            st.warning("⚠️ Sevkiyat verisi yok")
    with c2:
        if all([st.session_state.anlik_stok_satis, st.session_state.depo_stok, st.session_state.kpi]):
            st.success("✅ PO verileri tamam")
        else:
            st.warning("⚠️ PO verileri eksik")

# VERİ YÜKLEME
elif menu == "📂 Veri Yükleme":
    st.title("📂 Veri Yükleme")
    st.markdown("---")
    
    tab1, tab2, tab3 = st.tabs(["📊 Sevkiyat", "💵 PO", "✅ Durum"])
    
    with tab1:
        st.subheader("📦 Sevkiyat Verileri")
        st.info("Kolonlar: STORE_CODE, PRODUCT_CODE, AVAILABLE_STOCK, WEEKLY_SALES, WEEKS_OF_SUPPLY")
        f = st.file_uploader("Envanter CSV", type=['csv'], key='inv')
        if f:
            try:
                df = pd.read_csv(f)
                req = ['STORE_CODE', 'PRODUCT_CODE', 'AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY']
                if all(c in df.columns for c in req):
                    df['STORE_CODE'] = df['STORE_CODE'].astype(str)
                    df['PRODUCT_CODE'] = df['PRODUCT_CODE'].astype(str)
                    for col in ['AVAILABLE_STOCK', 'WEEKLY_SALES', 'WEEKS_OF_SUPPLY']:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                    st.session_state.inventory_df = df
                    st.success(f"✅ {len(df):,} satır yüklendi!")
                    c1,c2,c3 = st.columns(3)
                    c1.metric("Mağaza", df['STORE_CODE'].nunique())
                    c2.metric("Ürün", df['PRODUCT_CODE'].nunique())
                    c3.metric("Ort WOS", f"{df['WEEKS_OF_SUPPLY'].mean():.2f}")
                    with st.expander("Önizleme"):
                        st.dataframe(df.head(100))
                else:
                    st.error("Eksik kolonlar!")
            except Exception as e:
                st.error(f"Hata: {e}")
    
    with tab2:
        st.subheader("💵 PO Verileri")
        c1,c2 = st.columns(2)
        with c1:
            f1 = st.file_uploader("Anlık Stok/Satış", type=['csv'], key='anlik')
            if f1:
                try:
                    df = pd.read_csv(f1)
                    st.session_state.anlik_stok_satis = df
                    st.success(f"✅ {len(df):,} satır")
                except:
                    st.error("Hata!")
        with c2:
            f2 = st.file_uploader("Depo Stok", type=['csv'], key='depo')
            if f2:
                try:
                    df = pd.read_csv(f2)
                    st.session_state.depo_stok = df
                    st.success(f"✅ {len(df):,} satır")
                except:
                    st.error("Hata!")
        
        f3 = st.file_uploader("KPI", type=['csv'], key='kpi')
        if f3:
            try:
                df = pd.read_csv(f3)
                st.session_state.kpi = df
                st.success(f"✅ {len(df):,} satır")
            except:
                st.error("Hata!")
    
    with tab3:
        st.subheader("✅ Veri Durumu")
        c1,c2 = st.columns(2)
        with c1:
            st.markdown("**Sevkiyat**")
            if st.session_state.inventory_df is not None:
                st.success(f"✅ Envanter ({len(st.session_state.inventory_df):,})")
            else:
                st.error("❌ Envanter")
        with c2:
            st.markdown("**PO**")
            if st.session_state.anlik_stok_satis:
                st.success(f"✅ Anlık Stok ({len(st.session_state.anlik_stok_satis):,})")
            else:
                st.error("❌ Anlık Stok")
            if st.session_state.depo_stok:
                st.success(f"✅ Depo ({len(st.session_state.depo_stok):,})")
            else:
                st.error("❌ Depo")
            if st.session_state.kpi:
                st.success(f"✅ KPI ({len(st.session_state.kpi):,})")
            else:
                st.error("❌ KPI")

# SEVKİYAT
elif menu == "🚢 Sevkiyat":
    st.title("🚢 Sevkiyat Planlama")
    st.markdown("---")
    
    if st.session_state.inventory_df is None:
        st.warning("⚠️ Önce veri yükleyin!")
        st.stop()
    
    df = st.session_state.inventory_df.copy()
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Optimizasyon", "📊 Matris", "🎯 Clustering"])
    
    with tab1:
        st.subheader("⚙️ Sevkiyat Optimizasyonu")
        c1,c2,c3 = st.columns(3)
        budget = c1.number_input("Bütçe (adet)", value=10000, step=1000)
        target_wos = c2.number_input("Hedef WOS", value=4.0, step=0.5)
        mode = c3.selectbox("Mod", ['balanced', 'sales_focused', 'stock_focused'])
        
        if st.button("🚀 Optimizasyon Çalıştır", type="primary"):
            # Basit optimizasyon
            df['NEED'] = df.apply(lambda x: max(0, (target_wos - x['WEEKS_OF_SUPPLY']) * x['WEEKLY_SALES']) if x['WEEKLY_SALES'] > 0 else 0, axis=1)
            df['SCORE'] = df['NEED'] / (df['NEED'] + 1)
            df = df.sort_values('SCORE', ascending=False)
            
            allocated = 0
            df['ALLOCATED'] = 0
            for idx in df.index:
                if allocated >= budget:
                    break
                need = min(df.loc[idx, 'NEED'], budget - allocated)
                df.loc[idx, 'ALLOCATED'] = need
                allocated += need
            
            df['NEW_WOS'] = np.where(df['WEEKLY_SALES'] > 0, (df['AVAILABLE_STOCK'] + df['ALLOCATED']) / df['WEEKLY_SALES'], df['WEEKS_OF_SUPPLY'])
            st.session_state.sevkiyat_sonuc = df
            st.success("✅ Tamamlandı!")
        
        if 'sevkiyat_sonuc' in st.session_state and st.session_state.sevkiyat_sonuc is not None:
            result = st.session_state.sevkiyat_sonuc
            allocated = result[result['ALLOCATED'] > 0]
            
            c1,c2,c3 = st.columns(3)
            c1.metric("Dağıtılan", f"{allocated['ALLOCATED'].sum():,.0f}")
            c2.metric("Servis", allocated['STORE_CODE'].nunique())
            c3.metric("Ort WOS", f"{allocated['NEW_WOS'].mean():.2f}")
            
            st.dataframe(allocated[['STORE_CODE','PRODUCT_CODE','AVAILABLE_STOCK','WEEKLY_SALES','WEEKS_OF_SUPPLY','ALLOCATED','NEW_WOS']].head(100))
            
            csv = allocated.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 İndir", csv, f"sevkiyat_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    with tab2:
        st.subheader("📊 Sevkiyat Matrisi")
        st.info("⚠️ Önce optimizasyon çalıştırın")
    
    with tab3:
        st.subheader("🎯 Store Clustering")
        n_clusters = st.slider("Cluster Sayısı", 3, 10, 5)
        
        if st.button("🔍 Clustering Yap"):
            summary = df.groupby('STORE_CODE').agg({'AVAILABLE_STOCK':'sum', 'WEEKLY_SALES':'mean', 'WEEKS_OF_SUPPLY':'mean'}).reset_index()
            scaler = StandardScaler()
            features = scaler.fit_transform(summary[['AVAILABLE_STOCK','WEEKLY_SALES','WEEKS_OF_SUPPLY']])
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            summary['CLUSTER'] = kmeans.fit_predict(features)
            
            stats = summary.groupby('CLUSTER').agg({'STORE_CODE':'count', 'AVAILABLE_STOCK':'mean', 'WEEKLY_SALES':'mean', 'WEEKS_OF_SUPPLY':'mean'}).reset_index()
            stats.columns = ['CLUSTER', 'STORES', 'AVG_STOCK', 'AVG_SALES', 'AVG_WOS']
            
            st.dataframe(stats)
            st.dataframe(summary.sort_values('CLUSTER'))

# PO
elif menu == "💵 PO":
    st.title("💵 Purchase Order")
    st.markdown("---")
    
    missing = []
    if st.session_state.anlik_stok_satis is None:
        missing.append("Anlık Stok/Satış")
    if st.session_state.depo_stok is None:
        missing.append("Depo Stok")
    if st.session_state.kpi is None:
        missing.append("KPI")
    
    if missing:
        st.warning(f"⚠️ Eksik: {', '.join(missing)}")
        st.stop()
    
    tab1, tab2, tab3 = st.tabs(["⚙️ Hesaplama", "📊 Raporlar", "📦 Depo Bazlı"])
    
    with tab1:
        st.subheader("⚙️ PO Hesaplama")
        c1,c2,c3 = st.columns(3)
        fc = c1.number_input("Forward Cover", value=5.0, step=0.5)
        fc_ek = c2.number_input("Safety Stock", value=2, step=1)
        threshold = c3.number_input("Depo Eşik", value=999, step=100)
        
        if st.button("🚀 PO Hesapla", type="primary"):
            anlik = st.session_state.anlik_stok_satis.copy()
            depo = st.session_state.depo_stok.copy()
            
            anlik['urun_kod'] = anlik['urun_kod'].astype(str)
            depo['urun_kod'] = depo['urun_kod'].astype(str)
            
            # Basit PO hesaplama
            anlik['depo_kod'] = '1'
            depo_stok_map = depo.groupby(['depo_kod','urun_kod'])['stok'].sum().reset_index()
            depo_stok_map.columns = ['depo_kod','urun_kod','depo_stok']
            
            result = anlik.merge(depo_stok_map, on=['depo_kod','urun_kod'], how='left')
            result['depo_stok'] = result['depo_stok'].fillna(0)
            
            po = result.groupby(['depo_kod','urun_kod']).agg({'satis':'sum','stok':'sum','yol':'sum','depo_stok':'first'}).reset_index()
            po['brut'] = (fc + fc_ek) * po['satis']
            po['net'] = po['brut'] - po['stok'] - po['yol'] - po['depo_stok']
            po['po_ihtiyac'] = po['net'].clip(lower=0)
            po.loc[po['depo_stok'] > threshold, 'po_ihtiyac'] = 0
            
            po_pozitif = po[po['po_ihtiyac'] > 0].copy()
            st.session_state.alim_siparis_sonuc = po_pozitif
            
            st.success("✅ Hesaplama tamamlandı!")
            c1,c2,c3 = st.columns(3)
            c1.metric("Toplam PO", f"{po_pozitif['po_ihtiyac'].sum():,.0f}")
            c2.metric("Ürün", po_pozitif['urun_kod'].nunique())
            c3.metric("Depo", po_pozitif['depo_kod'].nunique())
            
            st.dataframe(po_pozitif.head(100))
            csv = po_pozitif.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 İndir", csv, f"po_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
    
    with tab2:
        st.subheader("📊 PO Raporları")
        if st.session_state.alim_siparis_sonuc is None:
            st.warning("Önce hesaplama yapın!")
        else:
            result = st.session_state.alim_siparis_sonuc
            st.dataframe(result)
    
    with tab3:
        st.subheader("📦 Depo Bazlı")
        if st.session_state.alim_siparis_sonuc is None:
            st.warning("Önce hesaplama yapın!")
        else:
            result = st.session_state.alim_siparis_sonuc
            depo_list = sorted(result['depo_kod'].unique())
            seçili = st.selectbox("Depo", ['Tümü'] + list(depo_list))
            
            if seçili != 'Tümü':
                result = result[result['depo_kod'] == seçili]
            
            st.dataframe(result)
            csv = result.to_csv(index=False, encoding='utf-8-sig')
            st.download_button("📥 İndir", csv, f"po_{seçili}_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

# FOOTER
st.markdown("---")
st.markdown("""<div style='text-align:center; color:#666; font-size:12px;'>
<strong>THORIUS AR4U</strong> - Retail Analytics v2.0<br>
🎫 Tek token ile tüm modüller
</div>""", unsafe_allow_html=True)
