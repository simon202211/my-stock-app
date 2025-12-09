import streamlit as st
import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import random

# --- 1. 页面配置 ---
st.set_page_config(page_title="风格罗盘", layout="wide", page_icon="🧭")

st.markdown("""
<style>
    .stApp {background-color: #FAFAFA; color: #333333;}
    h1 {color: #000000 !important; font-family: -apple-system, sans-serif; font-weight: 800; font-size: 24px !important; margin-bottom: 0px;}
    .metric-container {display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; margin-bottom: 20px;}
    .metric-card {background-color: #FFFFFF; border-radius: 12px; padding: 16px; flex: 1; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #EAEAEA;}
    .metric-title {font-size: 13px; color: #888888; margin-bottom: 5px;}
    .metric-value {font-size: 28px; font-weight: 700; font-family: 'Roboto', sans-serif;}
    .metric-delta {font-size: 12px; font-weight: 500; margin-top: 5px;}
    .stButton>button {width: 100%; border-radius: 20px; font-weight: bold;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 核心：强力网络请求器 ---
def get_session():
    # 创建一个像浏览器一样的会话
    session = requests.Session()
    # 遇到错误自动重试 5 次
    retry = Retry(connect=5, read=5, redirect=5, backoff_factor=0.5) 
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    # 伪装头
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/",
        "Accept-Language": "zh-CN,zh;q=0.9"
    })
    return session

@st.cache_data(ttl=600) 
def get_data_nuclear():
    session = get_session()
    
    def fetch_one_robust(secid):
        # 增加随机数，防止缓存锁死
        t = int(time.time() * 1000)
        # 备用接口列表 (双保险)
        urls = [
            f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231&_={t}",
            f"http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231&_={t}"
        ]
        
        for url in urls:
            try:
                # verify=False 忽略SSL证书错误，强行连接
                res = session.get(url, timeout=10, verify=False)
                data = res.json()
                if data and 'data' in data and 'klines' in data['data']:
                    rows = []
                    for item in data['data']['klines']:
                        d, c = item.split(',')
                        rows.append({'日期': d, '收盘': float(c)})
                    return pd.DataFrame(rows)
            except Exception as e:
                print(f"线路尝试失败: {e}")
                continue # 试下一个接口
        
        return pd.DataFrame()

    df_g = fetch_one_robust("1.000918") # 成长
    df_v = fetch_one_robust("1.000919") # 价值
    
    if df_g.empty or df_v.empty:
        return pd.DataFrame()

    df = pd.merge(df_g, df_v, on='日期', suffixes=('_G', '_V'))
    df['Date'] = pd.to_datetime(df['日期'])
    df['Ratio'] = df['收盘_G'] / df['收盘_V']
    df['MA20'] = df['Ratio'].rolling(window=20).mean()
    return df

# --- 3. 主程序 ---
st.title("🧭 沪深300 风格罗盘")

# 强制刷新按钮
if st.button("🔄 强制刷新数据"):
    st.cache_data.clear()
    st.rerun()

beijing_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%H:%M')
st.caption(f"📅 更新时间: {beijing_time} (北京时间) | 🔗 600026 专属策略")

with st.spinner('正在建立加密通道连接交易所...'):
    df = get_data_nuclear()

if df.empty:
    st.error("🚨 跨国网络暂时中断。")
    st.warning("建议：请过5分钟再试，或者点击上方的'强制刷新'按钮。")
    st.stop()

# 计算
last = df.iloc[-1]
prev = df.iloc[-2]
change = last['Ratio'] - prev['Ratio']
ma20 = last['MA20']
is_bull = last['Ratio'] > ma20

# 颜色
color_up = "#FF4D4F"
color_down = "#28C840"
val_color = color_up if change > 0 else color_down
arrow = '⬆' if change > 0 else '⬇'

# --- 4. 指标卡片 ---
st.markdown(f"""
<div class="metric-container">
    <div class="metric-card">
        <div class="metric-title">当前强弱比值 (Ratio)</div>
        <div class="metric-value" style="color: {val_color}">{last['Ratio']:.4f}</div>
        <div class="metric-delta">较昨日: {arrow} {abs(change):.4f}</div>
    </div>
    <div class="metric-card">
        <div class="metric-title">20日生命线 (MA20)</div>
        <div class="metric-value" style="color: #FF9900">{ma20:.4f}</div>
        <div class="metric-delta">{'🔥 成长进攻' if is_bull else '🛡️ 价值防守'}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- 5. 策略胶囊 ---
if is_bull:
    st.error("⚠️ **逆风局 (成长强·价值弱)**")
    st.markdown("**🚢 中远海能策略：** 市场处于科技进攻期。**建议逢高减仓/做T，切勿追高。**")
else:
    st.success("✅ **顺风局 (价值强·成长弱)**")
    st.markdown("**🚢 中远海能策略：** 市场处于避险防御期。**建议持股待涨，大跌大买。**")

# --- 6. 图表 ---
st.write("")
st.subheader("📊 趋势走势图 (2024-2025)")

fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Ratio'], mode='lines', name='🔵 强弱比值', line=dict(color='#0052D9', width=2.5)))
fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], mode='lines', name='🟠 20日均线', line=dict(color='#FF990
