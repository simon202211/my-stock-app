import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta

# --- 1. 基础配置 ---
st.set_page_config(page_title="风格罗盘V6", layout="wide")

# --- 2. 双通道数据获取 (核心修复) ---
@st.cache_data(ttl=300)
def get_data_v6():
    # 通道A: 东方财富 (首选)
    url_a = "https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231"
    # 通道B: 备用线路 (HTTP 不加密，成功率更高)
    url_b = "http://push2his.eastmoney.com/api/qt/stock/kline/get?secid={}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231"

    def fetch(secid):
        # 先试通道A
        try:
            res = requests.get(url_a.format(secid), timeout=3)
            if res.status_code == 200: return parse(res.json())
        except:
            pass
        
        # 失败则试通道B
        try:
            res = requests.get(url_b.format(secid), timeout=5)
            if res.status_code == 200: return parse(res.json())
        except:
            return []
        return []

    def parse(data):
        if not data or 'data' not in data or 'klines' not in data['data']: return []
        rows = []
        for item in data['data']['klines']:
            d, c = item.split(',')
            rows.append({'日期': d, '收盘': float(c)})
        return rows

    # 获取数据
    data_g = fetch("1.000918") # 成长
    data_v = fetch("1.000919") # 价值

    if not data_g or not data_v:
        return pd.DataFrame() # 返回空表

    # 合并
    df_g = pd.DataFrame(data_g)
    df_v = pd.DataFrame(data_v)
    df = pd.merge(df_g, df_v, on='日期', suffixes=('_G', '_V'))
    df['Date'] = pd.to_datetime(df['日期'])
    df['Ratio'] = df['收盘_G'] / df['收盘_V']
    df['MA20'] = df['Ratio'].rolling(window=20).mean()
    return df

# --- 3. 界面逻辑 ---
st.title("🧭 风格罗盘 (极简稳定版)")

# 显示北京时间
bj_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%H:%M')
st.write(f"📅 更新时间: {bj_time} (北京时间)")

# 强制刷新按钮
if st.button("🔄 如果数据没出来，点我刷新"):
    st.cache_data.clear()
    st.rerun()

# 获取数据
df = get_data_v6()

# --- 4. 容错处理 (防止红屏) ---
if df.empty:
    st.warning("⚠️ 网络正在穿越防火墙...")
    st.info("请等待 1 分钟后，再次点击上方的'刷新'按钮。")
    st.stop() # 停止运行，防止报错

# 计算指标
last = df.iloc[-1]
change = last['Ratio'] - df.iloc[-2]['Ratio']
ma20 = last['MA20']
is_bull = last['Ratio'] > ma20

# --- 5. 结果显示 ---
col1, col2 = st.columns(2)
with col1:
    st.metric("强弱比值 (Ratio)", f"{last['Ratio']:.4f}", f"{change:.4f}")
with col2:
    st.metric("20日生命线", f"{ma20:.4f}", "进攻" if is_bull else "防守")

# 策略提示
st.markdown("---")
if is_bull:
    st.error("⚠️ **逆风局 (成长强)** -> 600026 建议：**逢高减仓**")
else:
    st.success("✅ **顺风局 (价值强)** -> 600026 建议：**持股待涨**")

# --- 6. 绘图 ---
fig = go.Figure()
fig.add_trace(go.Scatter(x=df['Date'], y=df['Ratio'], name='Ratio', line=dict(color='blue', width=2)))
fig.add_trace(go.Scatter(x=df['Date'], y=df['MA20'], name='MA20', line=dict(color='orange', width=2)))
fig.update_layout(
    height=350, 
    margin=dict(l=10, r=10, t=10, b=10),
    xaxis_tickformat='%Y-%m',
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig, use_container_width=True)
