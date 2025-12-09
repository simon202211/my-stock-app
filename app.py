import streamlit as st
import pandas as pd
import requests
import plotly.graph_objects as go
from datetime import datetime

# --- 1. 页面配置 (清爽白底风格) ---
st.set_page_config(page_title="风格罗盘", layout="wide", page_icon="🧭")

# 注入CSS：强制白色背景，卡片化设计，优化字体
st.markdown("""
<style>
    /* 全局背景设为白色 */
    .stApp {
        background-color: #FFFFFF;
        color: #000000;
    }
    /* 标题颜色 */
    h1, h2, h3 {
        color: #1f77b4 !important;
        font-family: "Microsoft YaHei", sans-serif;
    }
    /* 指标卡片样式 */
    .metric-card {
        background-color: #F0F2F6;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .big-number {
        font-size: 26px !important;
        font-weight: bold;
        color: #000000;
    }
    .label-text {
        font-size: 14px;
        color: #555555;
    }
    /* 隐藏Streamlit默认的菜单 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 2. 核心数据函数 (极速直连) ---
@st.cache_data(ttl=600)
def get_data_stable():
    try:
        def fetch_one(secid):
            # 东方财富接口
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
    except Exception as e:
        return pd.DataFrame()

# --- 3. 主界面逻辑 ---
st.title("🧭 沪深300 风格罗盘")
st.caption("数据来源：东方财富实时接口 | 针对 600026 策略优化")

with st.spinner('正在获取最新数据...'):
    df = get_data_stable()

if df.empty:
    st.error("网络连接超时，请点击右上角菜单 Rerun 重试")
    st.stop()

# 计算最新数据
last = df.iloc[-1]
prev = df.iloc[-2]
change = last['Ratio'] - prev['Ratio']
ma20 = last['MA20']
is_bull = last['Ratio'] > ma20 # 蓝线在黄线之上 (成长强)

# --- 4. 关键指标展示区 (使用自定义HTML卡片) ---
col1, col2 = st.columns(2)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label-text">当前强弱比值 (Ratio)</div>
        <div class="big-number" style="color: {'#d62728' if change>0 else '#2ca02c'};">
            {last['Ratio']:.4f}
        </div>
        <div class="label-text">较昨日: {'⬆️' if change>0 else '⬇️'} {abs(change):.4f}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="label-text">20日生命线</div>
        <div class="big-number" style="color: #ff7f0e;">
            {ma20:.4f}
        </div>
        <div class="label-text">{'🔥 成长进攻区' if is_bull else '🛡️ 价值防守区'}</div>
    </div>
    """, unsafe_allow_html=True)

st.write("") # 空一行

# --- 5. 600026 策略卡片 (红绿灯模式) ---
# 使用 Streamlit 原生容器，在白色背景下更清晰
if is_bull:
    # 逆风局
    with st.container():
        st.error("⚠️ **逆风局 (成长主导)**")
        st.markdown("""
        **市场风向：** 资金正在抢筹科技/新能源，冷落价值股。
        
        **🚢 600026 操作建议：**
        * **不要追涨：** 容易冲高回落。
        * **逢高做T：** 拉升是卖点。
        """)
else:
    # 顺风局
    with st.container():
        st.success("✅ **顺风局 (价值主导)**")
        st.markdown("""
        **市场风向：** 资金避险，回流红利/银行/航运。
        
        **🚢 600026 操作建议：**
        * **敢于低吸：** 它是资金避风港。
        * **持股待涨：** 耐心持有。
        """)

# --- 6. 趋势图形 (已锁定，防止误触) ---
st.write("---")
st.subheader("📊 2024年至今走势图")

fig = go.Figure()

# 画蓝线 (Ratio)
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['Ratio'], 
    mode='lines', name='强弱比率 (Ratio)',
    line=dict(color='#1f77b4', width=3) # 深蓝色
))

# 画黄线 (MA20)
fig.add_trace(go.Scatter(
    x=df['Date'], y=df['MA20'], 
    mode='lines', name='20日生命线',
    line=dict(color='#ff7f0e', width=2, dash='dash') # 橙色虚线
))

# 优化图表布局 (白底)
fig.update_layout(
    plot_bgcolor='white',   # 图表区域背景白
    paper_bgcolor='white',  # 外围背景白
    font=dict(color='black'), # 字体黑
    margin=dict(l=10, r=10, t=30, b=10), # 边距紧凑
    height=400,
    xaxis=dict(
        showgrid=True, 
        gridcolor='#eeeeee', # 浅灰网格
        tickformat='%Y-%m'
    ),
    yaxis=dict(
        showgrid=True, 
        gridcolor='#eeeeee',
        zeroline=False
    ),
    legend=dict(
        orientation="h", # 图例横向排布
        y=1.1, x=0
    )
)

# 关键配置：禁用交互，防止手机误触！
st.plotly_chart(fig, use_container_width=True, config={'staticPlot': True})

st.caption("注：图形已锁定，防止手机滑动时误触缩放。")
