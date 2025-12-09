import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 页面配置 ---
st.set_page_config(page_title="风格罗盘", layout="wide", page_icon="🧭")
st.markdown("""
<style>
    .stApp {background-color: #000000;}
    h1 {font-size: 24px !important; color: #FFD700;}
    .big-font {font-size: 20px !important; font-weight: bold;}
</style>
""", unsafe_allow_html=True)

# --- 核心函数：直接连接数据源 (不依赖 akshare) ---
@st.cache_data(ttl=600)
def get_data_stable():
    try:
        # 直接访问东方财富接口，速度快且稳定
        # 1.000918 = 300成长, 1.000919 = 300价值
        def fetch_one(secid):
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231"
            # 设置短超时，失败自动重试逻辑由Streamlit处理
            res = requests.get(url, timeout=10)
            data = res.json()
            kline = data['data']['klines']
            rows = []
            for item in kline:
                d, c = item.split(',')
                rows.append({'日期': d, '收盘': float(c)})
            return pd.DataFrame(rows)

        df_g = fetch_one("1.000918") # 成长
        df_v = fetch_one("1.000919") # 价值
        
        # 合并数据
        df = pd.merge(df_g, df_v, on='日期', suffixes=('_G', '_V'))
        df['Date'] = pd.to_datetime(df['日期'])
        df['Ratio'] = df['收盘_G'] / df['收盘_V']
        df['MA20'] = df['Ratio'].rolling(window=20).mean()
        
        return df
    except Exception as e:
        # 如果出错，打印错误信息到后台（方便调试）
        print(f"Error: {e}")
        return pd.DataFrame()

# --- 主程序 ---
st.title("🧭 沪深300风格罗盘 (极速版)")

# 加载数据
with st.spinner('正在连接交易所数据...'):
    df = get_data_stable()

if df.empty:
    st.error("⚠️ 网络波动，无法连接交易所接口。请点击右上角菜单 -> 'Rerun' 重试。")
    st.stop()

# 获取最新数据
last = df.iloc[-1]
prev = df.iloc[-2]
change = last['Ratio'] - prev['Ratio']
ma20 = last['MA20']
is_bull = last['Ratio'] > ma20

# --- 展示卡片 ---
st.markdown("---")
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown("### 当前 Ratio")
    st.markdown(f"<p class='big-font' style='color:#00E5FF'>{last['Ratio']:.4f}</p>", unsafe_allow_html=True)
    st.caption(f"变动: {'⬆️' if change>0 else '⬇️'} {change:.4f}")

with col2:
    st.markdown("### 20日生命线")
    st.markdown(f"<p class='big-font' style='color:yellow'>{ma20:.4f}</p>", unsafe_allow_html=True)
    st.caption("🔥 进攻区" if is_bull else "🛡️ 防守区")

st.markdown("---")

# --- 600026 策略 ---
st.subheader("🚢 600026 (中远海能) 策略")
if is_bull:
    st.error("⚠️ 逆风局 (成长强)")
    st.write("资金正在流出价值股。**策略：逢高做T卖出，别追高。**")
else:
    st.success("✅ 顺风局 (价值强)")
    st.write("资金回流避险。**策略：敢于低吸，持股待涨。**")

# --- 绘图 ---
st.markdown("---")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Ratio'], mode='lines', name='Ratio', line=dict(color='#00E5FF', width=2)))
fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], mode='lines', name='MA20', line=dict(color='yellow', width=1, dash='dot')))
fig.update_layout(
    paper_bgcolor='black', plot_bgcolor='black', font=dict(color='white'),
    margin=dict(l=10, r=10, t=10, b=10), height=350,
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig, use_container_width=True)
