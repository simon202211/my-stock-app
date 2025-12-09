import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# --- 1. 页面配置 ---
st.set_page_config(page_title="风格罗盘", layout="wide", page_icon="🧭")

# 注入高级CSS
st.markdown("""
<style>
    .stApp {background-color: #FAFAFA; color: #333333;}
    h1 {color: #000000 !important; font-family: -apple-system, sans-serif; font-weight: 800; font-size: 24px !important; margin-bottom: 0px;}
    .metric-container {display: flex; justify-content: space-between; gap: 10px; margin-top: 10px; margin-bottom: 20px;}
    .metric-card {background-color: #FFFFFF; border-radius: 12px; padding: 16px; flex: 1; text-align: center; box-shadow: 0 2px 8px rgba(0,0,0,0.08); border: 1px solid #EAEAEA;}
    .metric-title {font-size: 13px; color: #888888; margin-bottom: 5px;}
    .metric-value {font-size: 28px; font-weight: 700; font-family: 'Roboto', sans-serif;}
    .metric-delta {font-size: 12px; font-weight: 500; margin-top: 5px;}
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 核心数据函数 (带伪装头+重试机制) ---
@st.cache_data(ttl=300) # 缩短缓存时间，保证新鲜
def get_data_robust():
    # 伪装成正常的浏览器，防止被拦截
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://quote.eastmoney.com/",
        "Accept": "*/*"
    }

    def fetch_one_with_retry(secid):
        url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231"
        
        # 最多重试3次
        for attempt in range(3):
            try:
                res = requests.get(url, headers=headers, timeout=5)
                if res.status_code == 200:
                    data = res.json()
                    rows = []
                    if data and 'data' in data and 'klines' in data['data']:
                        for item in data['data']['klines']:
                            d, c = item.split(',')
                            rows.append({'日期': d, '收盘': float(c)})
                    return pd.DataFrame(rows)
            except Exception as e:
                time.sleep(1) # 休息1秒再试
                continue
        return pd.DataFrame() # 3次都失败返回空

    df_g = fetch_one_with_retry("1.000918") # 成长
    df_v = fetch_one_with_retry("1.000919") # 价值
    
    if df_g.empty or df_v.empty:
        return pd.DataFrame()

    df = pd.merge(df_g, df_v, on='日期', suffixes=('_G', '_V'))
    df['Date'] = pd.to_datetime(df['日期'])
    df['Ratio'] = df['收盘_G'] / df['收盘_V']
    df['MA20'] = df['Ratio'].rolling(window=20).mean()
    return df

# --- 3. 主程序逻辑 ---
st.title("🧭 沪深300 风格罗盘")

beijing_time = (datetime.utcnow() + timedelta(hours=8)).strftime('%H:%M')
st.caption(f"📅 更新时间: {beijing_time} (北京时间) | 🔗 600026 专属策略")

# 加载数据
with st.spinner('正在穿越防火墙连接数据...'):
    df = get_data_robust()

if df.empty:
    st.error("⚠️ 交易所接口拥堵。")
    st.warning("请点击右上角菜单(三个点) -> 'Rerun' 重新加载。")
    st.stop()

# 计算最新数据
last = df.iloc[-1]
prev = df.iloc[-2]
change = last['Ratio'] - prev['Ratio']
ma20 = last['MA20']
is_bull = last['Ratio'] > ma20

# 颜色定义
color_up = "#FF4D4F" # 红
color_down = "#28C840" # 绿
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

# --- 6. 旗舰级图表 ---
st.write("")
st.subheader("📊 趋势走势图 (2024-2025)")

fig = go.Figure()

# 1. 蓝色实线：Ratio
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['Ratio'], 
    mode='lines', name='🔵 强弱比值',
    line=dict(color='#0052D9', width=2.5) 
))

# 2. 橙色虚线：MA20
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['MA20'], 
    mode='lines', name='🟠 20日均线', 
    line=dict(color='#FF9900', width=2, dash='dash') 
))

# 3. 最新点位标注
fig.add_trace(go.Scatter(
    x=[last['Date']], y=[last['Ratio']],
    mode='markers+text', name='最新',
    text=[f"{last['Ratio']:.3f}"], textposition="top center",
    textfont=dict(color='red', size=12, family="Arial Black"),
    marker=dict(color='red', size=8, line=dict(color='white', width=2)),
    showlegend=False
))

# 4. 时间轴格式化
fig.update_layout(
    plot_bgcolor='#FFFFFF', paper_bgcolor='#FFFFFF',
    margin=dict(l=10, r=10, t=10, b=10), height=380,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5, bgcolor="rgba(255,255,255,0.9)", bordercolor="#E0E0E0", borderwidth=1),
    
    xaxis=dict(
        showgrid=True, gridcolor='#F5F5F5',
        tickformat='%Y-%m', 
        dtick="M3", 
        tickfont=dict(size=11, color='#666666'),
        linecolor='#E0E0E0'
    ),
    
    yaxis=dict(
        showgrid=True, gridcolor='#F5F5F5',
        tickfont=dict(size=11, color='#666666'),
        zeroline=False
    ),
    hovermode="x unified"
)

st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})
