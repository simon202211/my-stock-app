import streamlit as st
import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# --- 页面配置 (手机端适配) ---
st.set_page_config(page_title="风格罗盘", layout="wide", page_icon="🧭")

# 强制暗色模式 & 手机字体优化
st.markdown("""
<style>
    .stApp {background-color: #000000;}
    h1 {font-size: 24px !important; color: #FFD700;}
    h3 {font-size: 18px !important;}
    .big-font {font-size: 20px !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 核心函数 ---
@st.cache_data(ttl=600) # 10分钟缓存
def get_data():
    try:
        # 获取沪深300成长与价值
        today = datetime.now().strftime("%Y%m%d")
        # 为了速度，只取最近6个月
        start = (datetime.now() - pd.Timedelta(days=180)).strftime("%Y%m%d")
        
        g = ak.index_zh_a_hist(symbol="000918", period="daily", start_date=start, end_date=today)
        v = ak.index_zh_a_hist(symbol="000919", period="daily", start_date=start, end_date=today)
        
        df = pd.merge(g[['日期', '收盘']], v[['日期', '收盘']], on='日期', suffixes=('_G', '_V'))
        df['Date'] = pd.to_datetime(df['日期'])
        df['Ratio'] = df['收盘_G'] / df['收盘_V']
        df['MA20'] = df['Ratio'].rolling(window=20).mean()
        return df
    except:
        return pd.DataFrame()

# --- 主程序 ---
st.title("🧭 沪深300风格罗盘")

with st.spinner('正在连接交易所...'):
    df = get_data()

if df.empty:
    st.error("数据连接失败，请刷新页面重试")
    st.stop()

# 获取最新数据
last = df.iloc[-1]
prev = df.iloc[-2]
change = last['Ratio'] - prev['Ratio']
ma20 = last['MA20']

# 判断逻辑
is_bull = last['Ratio'] > ma20  # 在黄线之上 (进攻)
is_up = change > 0              # 比昨天高 (趋势向上)

# --- 1. 核心信号区 (模仿小程序卡片) ---
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 当前数值")
    st.markdown(f"<p class='big-font' style='color:#00E5FF'>{last['Ratio']:.4f}</p>", unsafe_allow_html=True)
    if is_up:
        st.caption("📈 较昨日: 上升")
    else:
        st.caption("📉 较昨日: 下降")

with col2:
    st.markdown("### 20日生命线")
    st.markdown(f"<p class='big-font' style='color:yellow'>{ma20:.4f}</p>", unsafe_allow_html=True)
    if is_bull:
        st.caption("🔥 进攻区域")
    else:
        st.caption("🛡️ 防守区域")

st.markdown("---")

# --- 2. 600026 策略卡片 ---
st.subheader("🚢 600026 操盘建议")

if is_bull: # 蓝线在黄线之上，成长强
    st.error("⚠️ 逆风局 (成长主导)")
    st.write("资金正在抢筹科技股，冷落价值股。")
    st.write("👉 **策略：** 不要追涨，逢高做T卖出。")
else: # 蓝线在黄线之下，价值强
    st.success("✅ 顺风局 (价值主导)")
    st.write("资金回流红利避险，海能是避风港。")
    st.write("👉 **策略：** 敢于低吸，持股待涨。")

# --- 3. 交互图形 ---
st.markdown("---")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Ratio'], mode='lines', name='Ratio', line=dict(color='#00E5FF', width=2)))
fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], mode='lines', name='MA20', line=dict(color='yellow', width=1, dash='dot')))
fig.update_layout(
    paper_bgcolor='black', plot_bgcolor='black',
    font=dict(color='white'),
    margin=dict(l=10, r=10, t=10, b=10), # 手机端边距最小化
    height=350,
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig, use_container_width=True)
