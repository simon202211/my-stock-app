import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 1. 页面配置 (APP级质感) ---
st.set_page_config(page_title="风格罗盘", layout="wide", page_icon="🧭")

# 注入高级CSS：卡片悬浮感、大字体、护眼白底
st.markdown("""
<style>
    /* 全局背景纯白 */
    .stApp {
        background-color: #FAFAFA;
        color: #333333;
    }
    /* 标题样式 */
    h1 {
        color: #000000 !important;
        font-family: -apple-system, BlinkMacSystemFont, sans-serif;
        font-weight: 800;
        font-size: 24px !important;
        margin-bottom: 0px;
    }
    /* 卡片容器 */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 10px;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    /* 单个卡片样式 */
    .metric-card {
        background-color: #FFFFFF;
        border-radius: 12px;
        padding: 16px;
        flex: 1;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05); /* 柔和阴影 */
        border: 1px solid #F0F0F0;
    }
    .metric-title {
        font-size: 13px;
        color: #888888;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        font-family: 'Roboto', sans-serif;
    }
    .metric-delta {
        font-size: 12px;
        font-weight: 500;
        margin-top: 5px;
    }
    /* 去除默认页脚 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 核心数据函数 ---
@st.cache_data(ttl=600)
def get_data_stable():
    try:
        def fetch_one(secid):
            url = f"https://push2his.eastmoney.com/api/qt/stock/kline/get?secid={secid}&fields1=f1&fields2=f51,f53&klt=101&fqt=1&beg=20240101&end=20991231"
            res = requests.get(url, timeout=10)
            data = res.json()
            rows = []
            for item in data['data']['klines']:
                d, c = item.split(',')
                rows.append({'日期': d, '收盘': float(c)})
            return pd.DataFrame(rows)

        df_g = fetch_one("1.000918") # 成长
        df_v = fetch_one("1.000919") # 价值
        
        df = pd.merge(df_g, df_v, on='日期', suffixes=('_G', '_V'))
        df['Date'] = pd.to_datetime(df['日期'])
        df['Ratio'] = df['收盘_G'] / df['收盘_V']
        df['MA20'] = df['Ratio'].rolling(window=20).mean()
        return df
    except:
        return pd.DataFrame()

# --- 3. 主逻辑 ---
st.title("🧭 沪深300 风格罗盘")
st.caption(f"更新时间: {datetime.now().strftime('%H:%M')} | 600026 专属策略")

df = get_data_stable()

if df.empty:
    st.error("网络波动，请刷新页面")
    st.stop()

# 计算
last = df.iloc[-1]
prev = df.iloc[-2]
change = last['Ratio'] - prev['Ratio']
ma20 = last['MA20']
is_bull = last['Ratio'] > ma20

# 颜色定义
color_up = "#FF4D4F" # 红
color_down = "#28C840" # 绿 (下跌为绿，但在Ratio里下跌代表价值强，是好事)
val_color = color_up if change > 0 else color_down

# --- 4. 漂亮的指标卡片 (HTML) ---
st.markdown(f"""
<div class="metric-container">
    <div class="metric-card">
        <div class="metric-title">当前强弱比值 (Ratio)</div>
        <div class="metric-value" style="color: {val_color}">{last['Ratio']:.4f}</div>
        <div class="metric-delta">较昨日: {'⬆' if change>0 else '⬇'} {abs(change):.4f}</div>
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
    st.markdown("**🚢 中远海能策略：** 资金被科技吸走，容易阴跌。**建议逢高减仓，切勿追涨。**")
else:
    st.success("✅ **顺风局 (价值强·成长弱)**")
    st.markdown("**🚢 中远海能策略：** 资金回流避险，海能抗跌。**建议持股待涨，敢于低吸。**")

# --- 6. 旗舰级图表 (带图例和标注) ---
st.write("")
st.subheader("📊 趋势走势图")

fig = go.Figure()

# 蓝色实线：Ratio
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['Ratio'], 
    mode='lines', 
    name='🔵 强弱比值 (Ratio)', # 加上emoji让图例更显眼
    line=dict(color='#0052D9', width=3) # 科技蓝
))

# 橙色虚线：MA20
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['MA20'], 
    mode='lines', 
    name='🟠 20日均线', 
    line=dict(color='#FF9900', width=2, dash='dash') # 警示橙
))

# 添加最新点位的文字标注 (直接显示在图上)
fig.add_trace(go.Scatter(
    x=[last['Date']], y=[last['Ratio']],
    mode='markers+text',
    name='最新点',
    text=[f"{last['Ratio']:.3f}"],
    textposition="top center",
    marker=dict(color='red', size=8),
    showlegend=False
))

# 布局优化
fig.update_layout(
    plot_bgcolor='#FFFFFF',
    paper_bgcolor='#FFFFFF',
    margin=dict(l=10, r=10, t=10, b=10),
    height=380,
    # 图例设置 (关键优化)
    legend=dict(
        orientation="h",   # 横向排列
        yanchor="bottom", y=1.02, # 放在图表上方
        xanchor="center", x=0.5,  # 居中显示
        bgcolor="rgba(255,255,255,0.9)", # 半透明白底防遮挡
        bordercolor="#E0E0E0", borderwidth=1,
        font=dict(size=14, color="black")
    ),
    xaxis=dict(
        showgrid=True, gridcolor='#F0F0F0',
        tickformat='%m-%d', # 只显示月-日
        tickfont=dict(size=12, color='gray')
    ),
    yaxis=dict(
        showgrid=True, gridcolor='#F0F0F0',
        tickfont=dict(size=12, color='gray')
    )
)

# 锁定图形，禁止交互
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

st.markdown("""
<div style="text-align: center; color: #999; font-size: 12px; margin-top: 10px;">
    🔵 蓝线在橙线之上 = 成长强 | 🔵 蓝线在橙线之下 = 价值强
</div>
""", unsafe_allow_html=True)
