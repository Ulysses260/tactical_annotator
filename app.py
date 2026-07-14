"""
足球视频战术标注工具 - Streamlit 主界面
专业深色主题，Opta/StatsBomb 报告风格
三栏布局：视频播放 | 标注表单 | 标注列表
"""

import streamlit as st
import tempfile
import os
import json

from video_annotator import (
    VideoAnnotator,
    TacticalAnnotation,
    EVENT_TYPES,
    TACTIC_ZONES,
    EVENT_COLORS,
)


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="足球战术标注工具",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 自定义 CSS（深色战术数据风格）
# ============================================================

st.markdown(
    """
    <style>
    /* 全局深色背景微调 */
    .stApp {
        background-color: #0d1117;
    }

    /* 卡片样式 */
    .tac-card {
        background: linear-gradient(135deg, rgba(22, 27, 34, 0.95) 0%, rgba(13, 17, 23, 0.95) 100%);
        border: 1px solid rgba(54, 207, 201, 0.15);
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 16px;
        backdrop-filter: blur(10px);
    }

    .tac-card h3 {
        color: #36CFC9;
        font-size: 16px;
        font-weight: 600;
        margin-bottom: 16px;
        letter-spacing: 1px;
        border-bottom: 1px solid rgba(54, 207, 201, 0.2);
        padding-bottom: 8px;
    }

    /* 标注条目卡片 */
    .ann-item {
        background: rgba(22, 27, 34, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-left: 4px solid #36CFC9;
        border-radius: 8px;
        padding: 12px 14px;
        margin-bottom: 10px;
        transition: all 0.2s ease;
    }
    .ann-item:hover {
        border-color: rgba(54, 207, 201, 0.4);
        background: rgba(30, 41, 59, 0.8);
    }

    /* 时间戳标签 */
    .ann-time {
        display: inline-block;
        background: #1f2937;
        color: #e5e7eb;
        font-family: 'Courier New', monospace;
        font-size: 14px;
        font-weight: 700;
        padding: 2px 10px;
        border-radius: 4px;
        margin-right: 8px;
    }

    /* 事件类型标签 */
    .event-tag {
        display: inline-block;
        font-size: 12px;
        font-weight: 600;
        padding: 2px 10px;
        border-radius: 12px;
        color: #0d1117;
        margin-right: 6px;
    }

    /* 队伍标签 */
    .team-tag {
        display: inline-block;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
        background: rgba(146, 84, 222, 0.2);
        color: #b37feb;
        border: 1px solid rgba(146, 84, 222, 0.3);
        margin-right: 6px;
    }

    /* 场区标签 */
    .zone-tag {
        display: inline-block;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
        background: rgba(54, 207, 201, 0.12);
        color: #5cdbd3;
        border: 1px solid rgba(54, 207, 201, 0.25);
        margin-right: 6px;
    }

    /* 描述文字 */
    .ann-desc {
        color: #d1d5db;
        font-size: 13px;
        margin-top: 6px;
        line-height: 1.5;
    }

    /* 球员标签 */
    .player-chip {
        display: inline-block;
        font-size: 11px;
        padding: 1px 8px;
        border-radius: 10px;
        background: rgba(105, 192, 255, 0.15);
        color: #69c0ff;
        border: 1px solid rgba(105, 192, 255, 0.3);
        margin: 2px 4px 2px 0;
    }

    /* 备注文字 */
    .ann-notes {
        color: #9ca3af;
        font-size: 12px;
        margin-top: 4px;
        font-style: italic;
    }

    /* 主按钮风格 */
    .stButton > button {
        background: linear-gradient(135deg, #08979c 0%, #006d75 100%);
        color: white;
        border: none;
        border-radius: 6px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: linear-gradient(135deg, #36CFC9 0%, #08979c 100%);
        box-shadow: 0 4px 12px rgba(54, 207, 201, 0.3);
    }

    /* 危险按钮 */
    .danger-btn > button {
        background: linear-gradient(135deg, #cf1322 0%, #a8071a 100%) !important;
    }
    .danger-btn > button:hover {
        background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%) !important;
        box-shadow: 0 4px 12px rgba(255, 77, 79, 0.3) !important;
    }

    /* 统计面板 */
    .stats-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 8px;
        margin-bottom: 12px;
    }
    .stat-box {
        background: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 6px;
        padding: 10px;
        text-align: center;
    }
    .stat-num {
        font-size: 22px;
        font-weight: 700;
        color: #36CFC9;
        font-family: 'Courier New', monospace;
    }
    .stat-label {
        font-size: 11px;
        color: #9ca3af;
        margin-top: 2px;
    }

    /* 标题栏 */
    .app-title {
        text-align: center;
        padding: 20px 0 24px;
    }
    .app-title h1 {
        color: #f0f5ff;
        font-size: 28px;
        font-weight: 700;
        margin: 0;
        letter-spacing: 2px;
    }
    .app-title .subtitle {
        color: #36CFC9;
        font-size: 13px;
        margin-top: 4px;
        letter-spacing: 3px;
        opacity: 0.8;
    }

    /* 视频容器 */
    .video-wrapper {
        border-radius: 8px;
        overflow: hidden;
        border: 1px solid rgba(54, 207, 201, 0.2);
        margin-bottom: 12px;
    }

    /* 分隔线 */
    .divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, rgba(54, 207, 201, 0.3), transparent);
        margin: 16px 0;
    }

    /* 空状态 */
    .empty-state {
        text-align: center;
        padding: 30px 20px;
        color: #6b7280;
        font-size: 13px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# Session State 初始化
# ============================================================

def init_state():
    """初始化 session state"""
    if "annotator" not in st.session_state:
        st.session_state.annotator = VideoAnnotator()
    if "video_bytes" not in st.session_state:
        st.session_state.video_bytes = None
    if "current_timestamp" not in st.session_state:
        st.session_state.current_timestamp = 0.0
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0


init_state()
annotator: VideoAnnotator = st.session_state.annotator


# ============================================================
# 标题
# ============================================================

st.markdown(
    """
    <div class="app-title">
        <h1>⚽ 足球战术视频标注工具</h1>
        <div class="subtitle">TACTICAL VIDEO ANNOTATOR · PRO EDITION</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 三栏布局
# ============================================================

col_left, col_mid, col_right = st.columns([4, 3.5, 4.5])


# ============================================================
# 左栏：视频上传 + 播放器 + 时间点捕捉
# ============================================================

with col_left:
    st.markdown('<div class="tac-card"><h3>🎥 视频面板</h3>', unsafe_allow_html=True)

    # 视频上传
    uploaded_file = st.file_uploader(
        "上传比赛视频",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        help="支持 MP4/MOV/AVI/MKV/WEBM 格式",
    )

    if uploaded_file is not None:
        # 保存到临时文件
        if st.session_state.video_bytes != uploaded_file.getvalue():
            st.session_state.video_bytes = uploaded_file.getvalue()
            # 创建临时文件
            tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tfile.write(st.session_state.video_bytes)
            tfile.close()
            annotator.load_video(tfile.name)
            st.session_state.temp_video_path = tfile.name

    # 视频播放器
    if st.session_state.video_bytes is not None:
        st.markdown('<div class="video-wrapper">', unsafe_allow_html=True)
        st.video(st.session_state.video_bytes)
        st.markdown('</div>', unsafe_allow_html=True)

        # 时间点手动输入
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**⏱ 手动设置标注时间点**")

        time_col1, time_col2 = st.columns(2)
        with time_col1:
            minutes = st.number_input("分钟", min_value=0, value=int(st.session_state.current_timestamp // 60), step=1)
        with time_col2:
            seconds = st.number_input("秒", min_value=0, max_value=59, value=int(st.session_state.current_timestamp % 60), step=1)

        if st.button("📌 设定为当前标注时间", use_container_width=True):
            st.session_state.current_timestamp = minutes * 60 + seconds
            st.success(f"已设定时间点：{minutes:02d}:{seconds:02d}")

        # 快捷时间调整
        st.markdown("**⚡ 快捷微调**")
        adj_col1, adj_col2, adj_col3, adj_col4 = st.columns(4)
        with adj_col1:
            if st.button("-5s", use_container_width=True):
                st.session_state.current_timestamp = max(0, st.session_state.current_timestamp - 5)
                st.rerun()
        with adj_col2:
            if st.button("-1s", use_container_width=True):
                st.session_state.current_timestamp = max(0, st.session_state.current_timestamp - 1)
                st.rerun()
        with adj_col3:
            if st.button("+1s", use_container_width=True):
                st.session_state.current_timestamp += 1
                st.rerun()
        with adj_col4:
            if st.button("+5s", use_container_width=True):
                st.session_state.current_timestamp += 5
                st.rerun()

        # 显示当前时间点
        current_min = int(st.session_state.current_timestamp // 60)
        current_sec = int(st.session_state.current_timestamp % 60)
        st.info(f"🎯 当前标注时间点：**{current_min:02d}:{current_sec:02d}**")

    else:
        st.markdown(
            '<div class="empty-state">请上传视频文件开始标注<br><br>支持 MP4 / MOV / AVI / MKV</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # 使用说明卡片
    st.markdown('<div class="tac-card"><h3>📖 使用说明</h3>', unsafe_allow_html=True)
    st.markdown(
        """
        1. **上传视频**：在上方上传比赛录像
        2. **定位时间点**：播放到需要标注的时刻，在左侧设置时间
        3. **填写标注**：在中间栏选择事件类型、队伍等信息
        4. **管理标注**：右侧查看、编辑、删除所有标注
        5. **导出数据**：点击导出按钮生成标准 JSON 文件
        """,
        unsafe_allow_html=True,
    )
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 中栏：标注表单
# ============================================================

with col_mid:
    st.markdown('<div class="tac-card"><h3>📝 标注表单</h3>', unsafe_allow_html=True)

    # 如果是编辑模式，获取当前标注数据
    editing_ann = None
    if st.session_state.editing_id:
        editing_ann = annotator.get_annotation(st.session_state.editing_id)

    form_key = f"ann_form_{st.session_state.form_key}"

    with st.form(key=form_key, clear_on_submit=False):
        # 时间戳显示
        current_min = int(st.session_state.current_timestamp // 60)
        current_sec = int(st.session_state.current_timestamp % 60)
        st.markdown(f"**⏱ 标注时间点：** `{current_min:02d}:{current_sec:02d}`")

        # 事件类型
        event_type = st.selectbox(
            "事件类型 *",
            EVENT_TYPES,
            index=EVENT_TYPES.index(editing_ann.event_type) if editing_ann and editing_ann.event_type in EVENT_TYPES else 0,
            help="选择本次标注的战术事件类型",
        )

        # 队伍
        team = st.text_input(
            "队伍",
            value=editing_ann.team if editing_ann else "",
            placeholder="如：主队 / 客队 / 红队 / 蓝队",
            help="事件所属的队伍",
        )

        # 球员
        players_input = st.text_input(
            "涉及球员（逗号分隔）",
            value=",".join(editing_ann.players) if editing_ann else "",
            placeholder="如：张三,李四,王五",
            help="参与本次事件的球员姓名，用逗号分隔",
        )

        # 场区
        tactic_zone = st.selectbox(
            "场区",
            [""] + TACTIC_ZONES,
            index=(TACTIC_ZONES.index(editing_ann.tactic_zone) + 1) if editing_ann and editing_ann.tactic_zone in TACTIC_ZONES else 0,
            help="事件发生的战术区域",
        )

        # 描述
        description = st.text_area(
            "事件描述",
            value=editing_ann.description if editing_ann else "",
            placeholder="简要描述本次战术事件...",
            height=80,
            help="详细描述事件内容、战术意图等",
        )

        # 备注
        notes = st.text_area(
            "备注",
            value=editing_ann.notes if editing_ann else "",
            placeholder="其他补充说明...",
            height=60,
            help="补充信息、分析备注等",
        )

        # 提交按钮
        submit_label = "✏️ 更新标注" if st.session_state.editing_id else "➕ 添加标注"
        submitted = st.form_submit_button(submit_label, use_container_width=True)

        if submitted:
            players_list = [p.strip() for p in players_input.split(",") if p.strip()]

            if st.session_state.editing_id:
                # 编辑模式
                success = annotator.edit_annotation(
                    st.session_state.editing_id,
                    event_type=event_type,
                    team=team,
                    players=players_list,
                    tactic_zone=tactic_zone,
                    description=description,
                    notes=notes,
                )
                if success:
                    st.success("✅ 标注已更新！")
                    st.session_state.editing_id = None
                    st.session_state.form_key += 1
                    st.rerun()
            else:
                # 新增模式
                ann = annotator.add_annotation(
                    timestamp=st.session_state.current_timestamp,
                    event_type=event_type,
                    team=team,
                    players=players_list,
                    tactic_zone=tactic_zone,
                    description=description,
                    notes=notes,
                )
                st.success(f"✅ 已添加标注（{ann.formatted_time}）")
                st.session_state.form_key += 1
                st.rerun()

    # 取消编辑
    if st.session_state.editing_id:
        if st.button("↩️ 取消编辑", use_container_width=True):
            st.session_state.editing_id = None
            st.session_state.form_key += 1
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # 事件类型图例
    st.markdown('<div class="tac-card"><h3>🎨 事件类型图例</h3>', unsafe_allow_html=True)
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 6px;">'
    for evt, color in EVENT_COLORS.items():
        legend_html += f'<span class="event-tag" style="background: {color};">{evt}</span>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 右栏：标注列表 + 导入导出
# ============================================================

with col_right:
    # 统计面板
    st.markdown('<div class="tac-card"><h3>📊 标注统计</h3>', unsafe_allow_html=True)
    stats = annotator.stats

    stats_html = '<div class="stats-grid">'
    stats_html += f'<div class="stat-box"><div class="stat-num">{stats["total"]}</div><div class="stat-label">总标注数</div></div>'
    stats_html += f'<div class="stat-box"><div class="stat-num">{len(stats["by_event_type"])}</div><div class="stat-label">事件类型</div></div>'
    stats_html += f'<div class="stat-box"><div class="stat-num">{len(stats["by_team"])}</div><div class="stat-label">涉及队伍</div></div>'
    stats_html += f'<div class="stat-box"><div class="stat-num">{len(stats["by_zone"])}</div><div class="stat-label">覆盖场区</div></div>'
    stats_html += '</div>'
    st.markdown(stats_html, unsafe_allow_html=True)

    # 各事件类型数量
    if stats["by_event_type"]:
        st.markdown("**事件分布**")
        for evt, count in stats["by_event_type"].items():
            color = EVENT_COLORS.get(evt, "#8C8C8C")
            pct = int(count / stats["total"] * 100) if stats["total"] > 0 else 0
            st.markdown(
                f'<div style="display: flex; align-items: center; margin-bottom: 4px;">'
                f'<span class="event-tag" style="background: {color}; min-width: 60px; text-align: center;">{evt}</span>'
                f'<div style="flex: 1; margin-left: 8px; background: rgba(255,255,255,0.05); border-radius: 4px; height: 8px;">'
                f'<div style="background: {color}; width: {pct}%; height: 100%; border-radius: 4px;"></div>'
                f'</div>'
                f'<span style="margin-left: 8px; color: #d1d5db; font-size: 12px; min-width: 30px; text-align: right;">{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # 导入导出操作
    st.markdown('<div class="tac-card"><h3>💾 数据管理</h3>', unsafe_allow_html=True)
    io_col1, io_col2 = st.columns(2)

    with io_col1:
        # 导出 JSON
        if st.button("📤 导出 JSON", use_container_width=True):
            if annotator.annotations:
                json_str = annotator.export_json_string()
                st.download_button(
                    label="💾 下载标注文件",
                    data=json_str,
                    file_name=f"tactical_annotations_{annotator.video_name or 'export'}.json",
                    mime="application/json",
                    use_container_width=True,
                )
            else:
                st.warning("暂无标注数据可导出")

    with io_col2:
        # 导入 JSON
        import_file = st.file_uploader(
            "📥 导入 JSON",
            type=["json"],
            label_visibility="collapsed",
            help="导入已有的标注数据",
        )
        if import_file is not None:
            try:
                # 保存临时文件并导入
                content = import_file.read().decode("utf-8")
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
                tfile.write(content)
                tfile.close()
                if annotator.import_json(tfile.name):
                    st.success(f"✅ 成功导入 {len(annotator.annotations)} 条标注")
                    os.unlink(tfile.name)
                else:
                    st.error("❌ 导入失败：文件格式不正确")
                    os.unlink(tfile.name)
            except Exception as e:
                st.error(f"❌ 导入失败：{str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)

    # 标注列表
    st.markdown('<div class="tac-card"><h3>📋 标注列表</h3>', unsafe_allow_html=True)

    if not annotator.annotations:
        st.markdown(
            '<div class="empty-state">暂无标注数据<br>添加第一条标注开始吧！</div>',
            unsafe_allow_html=True,
        )
    else:
        # 筛选器
        filter_col1, filter_col2 = st.columns(2)
        with filter_col1:
            filter_event = st.selectbox(
                "按事件筛选",
                ["全部事件"] + EVENT_TYPES,
                key="filter_event",
            )
        with filter_col2:
            filter_team = st.text_input(
                "按队伍筛选",
                placeholder="输入队伍名",
                key="filter_team",
            )

        # 过滤标注
        filtered = annotator.annotations
        if filter_event != "全部事件":
            filtered = [a for a in filtered if a.event_type == filter_event]
        if filter_team.strip():
            filtered = [a for a in filtered if filter_team.strip() in a.team]

        st.markdown(f"共 **{len(filtered)}** 条标注")
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 逐条渲染标注
        for i, ann in enumerate(filtered):
            color = EVENT_COLORS.get(ann.event_type, "#8C8C8C")

            # 构建标注卡片 HTML
            item_html = f'<div class="ann-item" style="border-left-color: {color};">'
            item_html += f'<span class="ann-time">{ann.formatted_time}</span>'
            item_html += f'<span class="event-tag" style="background: {color};">{ann.event_type}</span>'
            if ann.team:
                item_html += f'<span class="team-tag">{ann.team}</span>'
            if ann.tactic_zone:
                item_html += f'<span class="zone-tag">{ann.tactic_zone}</span>'

            # 球员
            if ann.players:
                item_html += '<div style="margin-top: 6px;">'
                for p in ann.players:
                    item_html += f'<span class="player-chip">👤 {p}</span>'
                item_html += '</div>'

            # 描述
            if ann.description:
                item_html += f'<div class="ann-desc">{ann.description}</div>'

            # 备注
            if ann.notes:
                item_html += f'<div class="ann-notes">📝 {ann.notes}</div>'

            item_html += '</div>'
            st.markdown(item_html, unsafe_allow_html=True)

            # 操作按钮
            btn_col1, btn_col2 = st.columns([1, 1])
            with btn_col1:
                if st.button("✏️ 编辑", key=f"edit_{ann.annotation_id}", use_container_width=True):
                    st.session_state.editing_id = ann.annotation_id
                    st.session_state.current_timestamp = ann.timestamp
                    st.session_state.form_key += 1
                    st.rerun()
            with btn_col2:
                if st.button("🗑 删除", key=f"del_{ann.annotation_id}", use_container_width=True):
                    # 标记确认删除
                    st.session_state[f"confirm_del_{ann.annotation_id}"] = True

            # 删除确认
            if st.session_state.get(f"confirm_del_{ann.annotation_id}"):
                st.warning("确定要删除这条标注吗？")
                del_col1, del_col2 = st.columns(2)
                with del_col1:
                    if st.button("✅ 确认删除", key=f"confirm_{ann.annotation_id}", use_container_width=True):
                        annotator.delete_annotation(ann.annotation_id)
                        if st.session_state.editing_id == ann.annotation_id:
                            st.session_state.editing_id = None
                        st.success("已删除")
                        st.rerun()
                with del_col2:
                    if st.button("❌ 取消", key=f"cancel_{ann.annotation_id}", use_container_width=True):
                        st.session_state[f"confirm_del_{ann.annotation_id}"] = False
                        st.rerun()

            if i < len(filtered) - 1:
                st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 页脚
# ============================================================

st.markdown(
    """
    <div style="text-align: center; padding: 20px 0; color: #4b5563; font-size: 12px;">
        ⚽ Tactical Video Annotator · 专业足球战术分析工具 · 数据格式兼容 AI 战术验证脚本
    </div>
    """,
    unsafe_allow_html=True,
)
