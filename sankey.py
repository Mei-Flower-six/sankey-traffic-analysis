# sankey_traffic_streamlit.py
import pandas as pd
import plotly.graph_objects as go
import logging
import streamlit as st
from datetime import datetime

# ===================== 1. 页面配置 =====================
st.set_page_config(
    page_title="多站点流量-销量桑基图分析",
    page_icon="🌐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== 2. 全局配置 =====================
SITE_CONFIG = {
    "Amazon-US": {"cn_name": "亚马逊美国站", "color": "#87CEEB"},
    "Amazon-JP": {"cn_name": "亚马逊日本站", "color": "#FF6B6B"},
    "Amazon-UK": {"cn_name": "亚马逊英国站", "color": "#4ECDC4"},
    "Shopify": {"cn_name": "Shopify独立站", "color": "#DDA0DD"}
}

TRAFFIC_ORDER = [
    "Amazon站内广告",   # 1
    "Amazon-DSP",       # 2
    "Amazon自然流量",   # 3
    "Amazon-FB",        # 4
    "SP-GG",            # 5
    "SP-FB",            # 6
    "SP-自然",          # 7
    "SP-其他"           # 8
]

TRAFFIC_MAPPING = {
    "Amazon站内广告": {
        "group_id": "组1",
        "site": "Amazon-US",
        "nodes": {
            "exposure": "站内曝光",
            "level2_exposure": "Amazon-US曝光",
            "click": "站内点击",
            "level2_click": "Amazon-US点击",
            "sales": "站内销量",
            "level2_sales": "Amazon-US销量"
        }
    },
    "Amazon-DSP": {
        "group_id": "组2",
        "site": "Amazon-US",
        "nodes": {
            "exposure": "DSP曝光",
            "level2_exposure": "Amazon-US曝光",
            "click": "DSP点击",
            "level2_click": "Amazon-US点击",
            "sales": "DSP销量",
            "level2_sales": "Amazon-US销量"
        }
    },
    "Amazon自然流量": {
        "group_id": "组3",
        "site": "Amazon-US",
        "nodes": {
            "exposure": "Amazon自然曝光",
            "level2_exposure": "Amazon-US曝光",
            "click": "Amazon自然点击",
            "level2_click": "Amazon-US点击",
            "sales": "Amazon自然销量",
            "level2_sales": "Amazon-US销量"
        }
    },
    "Amazon-FB": {
        "group_id": "组4",
        "site": "Amazon-US",
        "nodes": {
            "exposure": "FB曝光",
            "level2_exposure": "Amazon-US曝光",
            "click": "FB点击",
            "level2_click": "Amazon-US点击",
            "sales": "FB销量",
            "level2_sales": "Amazon-US销量"
        }
    },
    "SP-GG": {
        "group_id": "组5",
        "site": "Shopify",
        "nodes": {
            "exposure": "SP-GG曝光",
            "level2_exposure": "Shopify曝光",
            "click": "SP-GG点击",
            "level2_click": "Shopify点击",
            "sales": "SP-GG销量",
            "level2_sales": "Shopify销量"
        }
    },
    "SP-FB": {
        "group_id": "组6",
        "site": "Shopify",
        "nodes": {
            "exposure": "SP-FB曝光",
            "level2_exposure": "Shopify曝光",
            "click": "SP-FB点击",
            "level2_click": "Shopify点击",
            "sales": "SP-FB销量",
            "level2_sales": "Shopify销量"
        }
    },
    "SP-自然": {
        "group_id": "组7",
        "site": "Shopify",
        "nodes": {
            "exposure": "SP-自然曝光",
            "level2_exposure": "Shopify曝光",
            "click": "SP-自然点击",
            "level2_click": "Shopify点击",
            "sales": "SP-自然销量",
            "level2_sales": "Shopify销量"
        }
    },
    "SP-其他": {
        "group_id": "组8",
        "site": "Shopify",
        "nodes": {
            "exposure": "SP-其他曝光",
            "level2_exposure": "Shopify曝光",
            "click": "SP-其他点击",
            "level2_click": "Shopify点击",
            "sales": "SP-其他销量",
            "level2_sales": "Shopify销量"
        }
    }
}

GROUP_COLORS = {
    "组1": "#9290E6",  # 站内广告
    "组2": "#4ECDC4",  # DSP
    "组3": "#45B7D1",  # 自然流量
    "组4": "#96CEB4",  # FB
    "组5": "#FFA726",  # SP-GG
    "组6": "#AB47BC",  # SP-FB
    "组7": "#1C363F",  # SP-自然
    "组8": "#F00B0B",  # SP-其他
    **{site: SITE_CONFIG[site]["color"] for site in SITE_CONFIG},
    "总节点": "lightgray"
}

# 动态生成level2节点列表
LEVEL2_NODES = []
for traffic_type in TRAFFIC_MAPPING:
    cfg = TRAFFIC_MAPPING[traffic_type]
    LEVEL2_NODES.extend([
        cfg["nodes"]["level2_exposure"],
        cfg["nodes"]["level2_click"],
        cfg["nodes"]["level2_sales"]
    ])
LEVEL2_NODES = list(set(LEVEL2_NODES))

# 节点→流量类型映射
NODE_TO_TRAFFIC = {}
for traffic_type in TRAFFIC_MAPPING:
    cfg = TRAFFIC_MAPPING[traffic_type]
    unique_nodes = [
        traffic_type,
        cfg["nodes"]["exposure"],
        cfg["nodes"]["click"],
        cfg["nodes"]["sales"]
    ]
    for node in unique_nodes:
        NODE_TO_TRAFFIC[node] = traffic_type

# 无效流量类型过滤列表
INVALID_TRAFFIC_TYPES = ["Amazon 页面总点击", "总曝光", "总点击", "总销量"]

# ===================== 3. 读取Excel函数 =====================
@st.cache_data
def read_excel_generate_data(excel_path):
    try:
        df = pd.read_excel(excel_path)
        logger.info(f"成功读取Excel文件，数据行数：{len(df)}")
        st.success(f"✅ 成功读取Excel文件，数据行数：{len(df)}")
    except Exception as e:
        logger.error(f"读取Excel失败：{str(e)}")
        st.error(f"❌ 读取Excel失败：{str(e)}")
        return []
    
    # 数据预处理
    df["时间_str"] = df["时间"].astype(str)
    df["date"] = df["时间_str"].str.split(" ").str[0].str.replace("/", "-")
    df["date"] = df["date"].replace(["nan", "NaT", ""], pd.NaT)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    
    data_raw = []
    for _, row in df.iterrows():
        if pd.isna(row["date"]):
            continue
        
        traffic_type = row["流量类型"]
        if traffic_type in INVALID_TRAFFIC_TYPES:
            logger.debug(f"过滤无效流量类型：{traffic_type}")
            continue
        
        if traffic_type not in TRAFFIC_MAPPING:
            logger.warning(f"未配置的流量类型：{traffic_type}（已跳过）")
            continue
        
        cfg = TRAFFIC_MAPPING[traffic_type]
        if cfg["site"] not in SITE_CONFIG:
            logger.warning(f"非法站点：{cfg['site']}（流量类型：{traffic_type}，已跳过）")
            continue
        
        date = row["date"]
        exposure = pd.to_numeric(row["曝光"], errors="coerce") if pd.notna(row["曝光"]) else 0.0
        click = pd.to_numeric(row["点击"], errors="coerce") if pd.notna(row["点击"]) else 0.0
        sales = pd.to_numeric(row["销量"], errors="coerce") if pd.notna(row["销量"]) else 0.0
        
        data_raw.extend([
            [traffic_type, cfg["nodes"]["exposure"], float(exposure), date, cfg["group_id"], traffic_type],
            [cfg["nodes"]["exposure"], cfg["nodes"]["level2_exposure"], float(exposure), date, cfg["group_id"], traffic_type],
            [cfg["nodes"]["level2_exposure"], "总曝光", float(exposure), date, cfg["group_id"], traffic_type],
            ["总曝光", cfg["nodes"]["click"], float(click), date, cfg["group_id"], traffic_type],
            [cfg["nodes"]["click"], cfg["nodes"]["level2_click"], float(click), date, cfg["group_id"], traffic_type],
            [cfg["nodes"]["level2_click"], "总点击", float(click), date, cfg["group_id"], traffic_type],
            ["总点击", cfg["nodes"]["sales"], float(sales), date, cfg["group_id"], traffic_type],
            [cfg["nodes"]["sales"], cfg["nodes"]["level2_sales"], float(sales), date, cfg["group_id"], traffic_type],
            [cfg["nodes"]["level2_sales"], "总销量", float(sales), date, cfg["group_id"], traffic_type]
        ])
    
    logger.info(f"生成链路数据条数：{len(data_raw)}")
    return data_raw

# ===================== 4. 应用标题 =====================
st.title("🌐 多站点流量-销量桑基图分析")
st.markdown("---")

# ===================== 5. 侧边栏控制面板 =====================
with st.sidebar:
    st.header("⚙️ 控制面板")
    
    # 文件上传
    uploaded_file = st.file_uploader("上传Excel文件", type=["xlsx", "xls"])
    
    # 搜索区域
    search_keyword = st.text_input(
        "🔍 链路搜索（支持站点/流量类型关键词）",
        placeholder="输入关键词（如US/Shopify/DSP/站内）",
        help="支持站点、流量类型关键词搜索"
    )
    
    # 清空搜索按钮
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ 清空搜索", type="secondary", use_container_width=True):
            search_keyword = ""
            st.rerun()
    
    st.markdown("---")
    st.subheader("📅 日期范围")
    
    # 日期输入
    default_start = "2026-01-05"
    default_end = "2026-01-19"
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input(
            "开始日期",
            value=datetime.strptime(default_start, "%Y-%m-%d").date()
        )
    
    with col2:
        end_date = st.date_input(
            "结束日期",
            value=datetime.strptime(default_end, "%Y-%m-%d").date()
        )
    
    # 日期验证
    if start_date > end_date:
        st.warning("⚠️ 开始日期不能晚于结束日期，已自动交换")
        start_date, end_date = end_date, start_date
    
    st.markdown("---")
    st.subheader("📏 缩放控制")
    
    # 缩放系数
    col1, col2 = st.columns(2)
    with col1:
        exposure_scale = st.number_input(
            "曝光链路缩放",
            min_value=0.01,
            max_value=10.0,
            value=0.5,
            step=0.05,
            help="调整曝光链路的宽度"
        )
    
    with col2:
        later_scale = st.number_input(
            "后续链路缩放",
            min_value=0.01,
            max_value=50.0,
            value=5.0,
            step=1.0,
            help="调整点击和销量链路的宽度"
        )
    
    st.markdown("---")
    st.info("💡 提示：点击图表节点可以查看详细信息")

# ===================== 6. 数据初始化 =====================
# 确定Excel文件路径
if uploaded_file is not None:
    # 如果有上传的文件，使用上传的文件
    EXCEL_PATH = uploaded_file
    st.success(f"📂 已上传文件: {uploaded_file.name}")
else:
    # 否则使用默认文件（本地测试时）
    EXCEL_PATH = "1.5-1.19流量数据统计.xlsx"

# 加载数据
try:
    data_raw = read_excel_generate_data(EXCEL_PATH)
    
    # 转换为DataFrame
    df = pd.DataFrame(data_raw, columns=["source", "target", "value", "date", "group", "traffic_type"])
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce").fillna(0.0)
    
    # 更新默认日期范围
    if df["date"].notna().any():
        default_start = df["date"].min().strftime("%Y-%m-%d")
        default_end = df["date"].max().strftime("%Y-%m-%d")
    
    logger.info(f"有效日期范围：{default_start} 至 {default_end}")
    
except Exception as e:
    st.error(f"❌ 数据加载失败: {str(e)}")
    st.stop()

# ===================== 7. 数据筛选和处理 =====================
# 显示数据摘要
with st.expander("📊 数据摘要", expanded=True):
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_records = len(df)
        st.metric("总记录数", total_records)
    
    with col2:
        traffic_types = df["traffic_type"].nunique()
        st.metric("流量类型数", traffic_types)
    
    with col3:
        total_exposure = df[df["source"].str.contains("曝光")]["value"].sum()
        st.metric("总曝光量", f"{total_exposure:,.0f}")
    
    with col4:
        total_sales = df[df["source"].str.contains("销量")]["value"].sum()
        st.metric("总销量", f"{total_sales:,.0f}")

# 数据筛选聚合
start_date_dt = pd.Timestamp(start_date)
end_date_dt = pd.Timestamp(end_date)

filtered_df = df[(df["date"] >= start_date_dt) & (df["date"] <= end_date_dt)]
aggregated_df = filtered_df.groupby(["source", "target", "group", "traffic_type"], as_index=False)["value"].sum()
aggregated_df = aggregated_df[aggregated_df["value"] > 0]

# ===================== 8. 生成节点列表 =====================
# 拆分流量类型为Amazon组和Shopify组
Amazon_TRAFFIC = [t for t in TRAFFIC_ORDER if TRAFFIC_MAPPING[t]["site"] == "Amazon-US"]
Shopify_TRAFFIC = [t for t in TRAFFIC_ORDER if TRAFFIC_MAPPING[t]["site"] == "Shopify"]

# 分别生成Amazon组的节点
Amazon_flow_sources = Amazon_TRAFFIC
Amazon_exposure_nodes = [TRAFFIC_MAPPING[t]["nodes"]["exposure"] for t in Amazon_TRAFFIC]
Amazon_level2_exposure = list(set([TRAFFIC_MAPPING[t]["nodes"]["level2_exposure"] for t in Amazon_TRAFFIC]))
Amazon_click_nodes = [TRAFFIC_MAPPING[t]["nodes"]["click"] for t in Amazon_TRAFFIC]
Amazon_level2_click = list(set([TRAFFIC_MAPPING[t]["nodes"]["level2_click"] for t in Amazon_TRAFFIC]))
Amazon_sales_nodes = [TRAFFIC_MAPPING[t]["nodes"]["sales"] for t in Amazon_TRAFFIC]
Amazon_level2_sales = list(set([TRAFFIC_MAPPING[t]["nodes"]["level2_sales"] for t in Amazon_TRAFFIC]))

# 分别生成Shopify组的节点
Shopify_flow_sources = Shopify_TRAFFIC
Shopify_exposure_nodes = [TRAFFIC_MAPPING[t]["nodes"]["exposure"] for t in Shopify_TRAFFIC]
Shopify_level2_exposure = list(set([TRAFFIC_MAPPING[t]["nodes"]["level2_exposure"] for t in Shopify_TRAFFIC]))
Shopify_click_nodes = [TRAFFIC_MAPPING[t]["nodes"]["click"] for t in Shopify_TRAFFIC]
Shopify_level2_click = list(set([TRAFFIC_MAPPING[t]["nodes"]["level2_click"] for t in Shopify_TRAFFIC]))
Shopify_sales_nodes = [TRAFFIC_MAPPING[t]["nodes"]["sales"] for t in Shopify_TRAFFIC]
Shopify_level2_sales = list(set([TRAFFIC_MAPPING[t]["nodes"]["level2_sales"] for t in Shopify_TRAFFIC]))

# 总节点（曝光/点击/销量）
total_nodes = ["总曝光", "总点击", "总销量"]

# 拼接节点列表：先Amazon组，再Shopify组（确保Shopify在下方）
all_nodes = (
    # Amazon组节点
    Amazon_flow_sources + Amazon_exposure_nodes + Amazon_level2_exposure + 
    # 总曝光
    total_nodes[:1] + 
    # Amazon点击相关节点
    Amazon_click_nodes + Amazon_level2_click + 
    # 总点击
    total_nodes[1:2] + 
    # Amazon销量相关节点
    Amazon_sales_nodes + Amazon_level2_sales + 
    # Shopify组节点（放到Amazon之后，显示在下方）
    Shopify_flow_sources + Shopify_exposure_nodes + Shopify_level2_exposure + 
    # Shopify点击相关节点
    Shopify_click_nodes + Shopify_level2_click + 
    # Shopify销量相关节点
    Shopify_sales_nodes + Shopify_level2_sales + 
    # 总销量
    total_nodes[2:]
)

node_ids = {node: idx for idx, node in enumerate(all_nodes)}

# ===================== 9. 节点统计 =====================
node_stats = {}
for node in all_nodes:
    incoming = aggregated_df[aggregated_df["target"] == node]["value"].sum()
    outgoing = aggregated_df[aggregated_df["source"] == node]["value"].sum()
    node_stats[node] = (incoming, outgoing)

# 计算总节点的总流入（用于节点占比计算）
total_node_values = {
    "总曝光": node_stats.get("总曝光", (0, 0))[0],  # 总曝光的总流入
    "总点击": node_stats.get("总点击", (0, 0))[0],  # 总点击的总流入
    "总销量": node_stats.get("总销量", (0, 0))[0]   # 总销量的总流入
}

# 生成节点的customdata（包含占比）
node_customdata = []
for node in all_nodes:
    incoming = node_stats[node][0]
    outgoing = node_stats[node][1]
    ratio = ""
    
    # 排除总曝光、总点击、总销量，不显示它们的占比
    if node in ["总曝光", "总点击", "总销量"]:
        pass  # 这三个节点的占比设为空
    else:
        # 判断节点类型，计算占对应总节点的比例
        if "曝光" in node:
            total = total_node_values["总曝光"]
            if total > 0:
                ratio = f"占总曝光：{round((outgoing / total) * 100, 2)}%"
        elif "点击" in node:
            total = total_node_values["总点击"]
            if total > 0:
                ratio = f"占总点击：{round((outgoing / total) * 100, 2)}%"
        elif "销量" in node:
            total = total_node_values["总销量"]
            if total > 0:
                ratio = f"占总销量：{round((outgoing / total) * 100, 2)}%"
    
    node_customdata.append((incoming, outgoing, ratio))

# ===================== 10. 搜索关键词匹配 =====================
search_keyword = search_keyword.strip().lower() if isinstance(search_keyword, str) else ""
matched_traffic_types = []

if not search_keyword:
    matched_traffic_types = TRAFFIC_ORDER
else:
    matched_sites = []
    for site in SITE_CONFIG:
        if search_keyword in site.lower() or search_keyword in SITE_CONFIG[site]["cn_name"].lower():
            matched_sites.append(site)
    
    if matched_sites:
        matched_traffic_types = [t for t in TRAFFIC_ORDER if TRAFFIC_MAPPING[t]["site"] in matched_sites]
    else:
        matched_traffic_types = [t for t in TRAFFIC_ORDER if search_keyword in t.lower()]

# 生成匹配节点列表
matched_nodes = []
for traffic_type in matched_traffic_types:
    cfg = TRAFFIC_MAPPING[traffic_type]
    matched_nodes.extend([
        traffic_type,
        cfg["nodes"]["exposure"],
        cfg["nodes"]["click"],
        cfg["nodes"]["sales"],
        cfg["nodes"]["level2_exposure"],
        cfg["nodes"]["level2_click"],
        cfg["nodes"]["level2_sales"]
    ])
matched_nodes = list(set(matched_nodes))

# ===================== 11. 生成链路 =====================
total_incoming = aggregated_df.groupby("target")["value"].sum().to_dict()
exposure_link = [
    (s, TRAFFIC_MAPPING[s]["nodes"]["exposure"]) for s in TRAFFIC_ORDER
] + [
    (TRAFFIC_MAPPING[s]["nodes"]["exposure"], TRAFFIC_MAPPING[s]["nodes"]["level2_exposure"]) for s in TRAFFIC_ORDER
] + [
    (TRAFFIC_MAPPING[s]["nodes"]["level2_exposure"], "总曝光") for s in TRAFFIC_ORDER
]

link_sources = []
link_targets = []
link_values = []
link_customdata = []
link_colors = []

for _, row in aggregated_df.iterrows():
    source = row["source"]
    target = row["target"]
    original_val = row["value"]
    group = row["group"]
    traffic_type = row["traffic_type"]
    
    is_matched = traffic_type in matched_traffic_types
    is_exposure = (source, target) in exposure_link
    base_scaled_val = original_val * (exposure_scale if is_exposure else later_scale)
    final_val = base_scaled_val if is_matched else base_scaled_val * 0.05
    
    # 核心：百分比计算（保留2位小数）
    target_total = total_incoming.get(target, 1)
    ratio = round((original_val / target_total) * 100, 2)
    
    final_color = GROUP_COLORS[group] if is_matched else "rgba(200, 200, 200, 0.2)"
    
    link_sources.append(node_ids[source])
    link_targets.append(node_ids[target])
    link_values.append(final_val)
    link_colors.append(final_color)
    link_customdata.append([source, target, original_val, ratio])

# ===================== 12. 节点颜色 =====================
node_color_list = []
for node in all_nodes:
    if node in matched_nodes:
        if node in NODE_TO_TRAFFIC:
            traffic_type = NODE_TO_TRAFFIC[node]
            node_color = GROUP_COLORS[TRAFFIC_MAPPING[traffic_type]["group_id"]]
        else:
            node_color = GROUP_COLORS.get(
                next((site for site in SITE_CONFIG if site in node), "总节点"),
                "lightgray"
            )
    else:
        node_color = "rgba(200, 200, 200, 0.2)"
    node_color_list.append(node_color)

# ===================== 13. 绘制桑基图 =====================
fig = go.Figure(data=[go.Sankey(
    node=dict(
        pad=20,
        thickness=30,
        line=dict(color="black", width=1),
        label=all_nodes,
        color=node_color_list,
        hovertemplate="%{label}<br>流入：%{customdata[0]:.0f}<br>流出：%{customdata[1]:.0f}<br>%{customdata[2]}<extra></extra>",
        customdata=node_customdata
    ),
    link=dict(
        source=link_sources,
        target=link_targets,
        value=link_values,
        color=link_colors,
        hovertemplate="%{customdata[0]}→%{customdata[1]}<br>原始数值：%{customdata[2]:.0f}<br>占%{customdata[1]}总流入：%{customdata[3]:.2f}%<extra></extra>",
        customdata=link_customdata
    )
)])

# 添加标题
title_text = f"多站点流量转化路径（{start_date} 至 {end_date}）"
if search_keyword:
    title_text += f" | 高亮：{search_keyword}"

fig.update_layout(
    title_text=title_text,
    font_size=12,
    autosize=True,
    margin=dict(l=20, r=20, t=50, b=20),
    font=dict(family="Microsoft YaHei"),
    height=800
)

# 显示图表
st.plotly_chart(fig, use_container_width=True, height=800)

# ===================== 14. 数据显示区域 =====================
with st.expander("📋 查看详细数据"):
    tab1, tab2, tab3 = st.tabs(["原始数据", "流量类型统计", "站点统计"])
    
    with tab1:
        st.dataframe(filtered_df.head(100))
    
    with tab2:
        # 按流量类型汇总
        traffic_summary = filtered_df.groupby("traffic_type").agg({
            "value": ["sum", "count"]
        }).round(2)
        traffic_summary.columns = ["总数值", "记录数"]
        st.dataframe(traffic_summary)
    
    with tab3:
        # 站点统计
        st.write("**站点配置:**")
        for site, info in SITE_CONFIG.items():
            st.write(f"- {site}: {info['cn_name']}")
        
        st.write(f"\n**流量类型总数:** {len(TRAFFIC_ORDER)}")
        st.write(f"**匹配的流量类型:** {len(matched_traffic_types)}")

# ===================== 15. 页脚信息 =====================
st.markdown("---")
st.caption(f"📅 数据更新时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
st.caption("💡 提示：修改Excel文件后，重新上传即可更新图表")

# ===================== 16. 运行应用 =====================
if __name__ == '__main__':
    # 在本地运行Streamlit应用
    # 命令行运行: streamlit run sankey_traffic_streamlit.py
    pass
