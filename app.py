"""
足球视频战术标注工具 v2.1 - Streamlit 主界面（重构版）
深色主题，Opta/StatsBomb 报告风格
布局：顶部工具栏 + 左侧大视频 + 右侧标签页面板
"""

import streamlit as st
import streamlit.components.v1 as components
import tempfile
import os
import json
import base64

from video_annotator import (
    VideoAnnotator,
    TacticalAnnotation,
    EVENT_TYPES,
    EVENT_TYPE_KEY_MAP,
    TACTIC_ZONES,
    EVENT_COLORS,
    FRAME_DURATION,
    DEFAULT_HOME_COLOR,
    DEFAULT_AWAY_COLOR,
)

from custom_video_player import render_custom_video_player_html


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="足球战术标注工具 v2.1",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# 自定义 CSS
# ============================================================

CUSTOM_CSS = """
<style>
/* 全局深色背景 */
.stApp {
    background-color: #0d1117;
}

/* 隐藏 Streamlit 默认菜单和页脚 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* 顶部工具栏 */
.top-toolbar {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 16px;
    background: linear-gradient(135deg, rgba(22, 27, 34, 0.98) 0%, rgba(13, 17, 23, 0.98) 100%);
    border-bottom: 1px solid rgba(54, 207, 201, 0.15);
    border-radius: 10px;
    margin-bottom: 16px;
}
.toolbar-title {
    color: #f0f5ff;
    font-size: 18px;
    font-weight: 700;
    letter-spacing: 1px;
    margin: 0;
    display: flex;
    align-items: center;
    gap: 8px;
}
.toolbar-spacer {
    flex: 1;
}
.toolbar-btn {
    background: rgba(54, 207, 201, 0.1);
    border: 1px solid rgba(54, 207, 201, 0.3);
    color: #5cdbd3;
    padding: 6px 14px;
    border-radius: 6px;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
    white-space: nowrap;
}
.toolbar-btn:hover {
    background: rgba(54, 207, 201, 0.2);
    border-color: rgba(54, 207, 201, 0.5);
}

/* 视频容器 - 大而醒目 */
.video-panel {
    background: #000;
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(54, 207, 201, 0.2);
    margin-bottom: 12px;
    position: relative;
}
.video-panel video {
    width: 100%;
    display: block;
    max-height: 600px;
    min-height: 500px;
    object-fit: contain;
    background: #000;
}

/* 空视频占位 */
.video-placeholder {
    width: 100%;
    min-height: 500px;
    background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    color: #6b7280;
    border: 2px dashed rgba(54, 207, 201, 0.15);
    border-radius: 10px;
}
.video-placeholder .icon {
    font-size: 64px;
    margin-bottom: 16px;
    opacity: 0.5;
}
.video-placeholder .title {
    font-size: 18px;
    color: #9ca3af;
    margin-bottom: 8px;
}
.video-placeholder .desc {
    font-size: 13px;
    color: #6b7280;
    text-align: center;
    line-height: 1.6;
}

/* 标注时间轴 */
.timeline-section {
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(54, 207, 201, 0.12);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 12px;
}
.annotation-timeline {
    position: relative;
    height: 28px;
    background: rgba(255,255,255,0.03);
    border-radius: 6px;
    margin: 6px 0;
    border: 1px solid rgba(255,255,255,0.06);
    cursor: pointer;
}
.timeline-dot {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 12px;
    height: 12px;
    border-radius: 50%;
    cursor: pointer;
    transition: transform 0.15s;
    border: 2px solid rgba(0,0,0,0.4);
    z-index: 2;
    box-shadow: 0 1px 3px rgba(0,0,0,0.3);
}
.timeline-dot:hover {
    transform: translate(-50%, -50%) scale(1.5);
    z-index: 3;
}
.timeline-cursor {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #36CFC9;
    z-index: 1;
    pointer-events: none;
    box-shadow: 0 0 6px rgba(54, 207, 201, 0.5);
}
.timeline-label {
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.timeline-label .title {
    color: #e6edf3;
    font-weight: 500;
}

/* 播放控制栏 */
.playback-controls {
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(54, 207, 201, 0.12);
    border-radius: 8px;
    padding: 10px 14px;
    margin-bottom: 12px;
}
.pb-section-title {
    font-size: 12px;
    color: #9ca3af;
    margin-bottom: 6px;
    font-weight: 500;
}
.pb-row {
    display: flex;
    gap: 6px;
    flex-wrap: wrap;
    align-items: center;
}
.pb-time-display {
    font-family: 'Courier New', monospace;
    font-size: 22px;
    font-weight: 700;
    color: #36CFC9;
    text-align: center;
    padding: 0 16px;
    letter-spacing: 2px;
    min-width: 100px;
}

/* 右侧面板 */
.right-panel {
    background: rgba(22, 27, 34, 0.6);
    border-radius: 10px;
    border: 1px solid rgba(54, 207, 201, 0.12);
    overflow: hidden;
}

/* 标注条目卡片 */
.ann-item {
    background: rgba(13, 17, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 4px solid #36CFC9;
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 8px;
    transition: all 0.2s ease;
}
.ann-item:hover {
    border-color: rgba(54, 207, 201, 0.4);
    background: rgba(30, 41, 59, 0.6);
}
.ann-time {
    display: inline-block;
    background: #1f2937;
    color: #e5e7eb;
    font-family: 'Courier New', monospace;
    font-size: 12px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 6px;
}
.event-tag {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    color: #0d1117;
    margin-right: 4px;
}
.team-tag {
    display: inline-block;
    font-size: 10px;
    padding: 1px 7px;
    border-radius: 4px;
    margin-right: 4px;
    font-weight: 500;
}
.zone-tag {
    display: inline-block;
    font-size: 10px;
    padding: 1px 7px;
    border-radius: 4px;
    background: rgba(54, 207, 201, 0.12);
    color: #5cdbd3;
    border: 1px solid rgba(54, 207, 201, 0.25);
    margin-right: 4px;
}
.ann-desc {
    color: #d1d5db;
    font-size: 12px;
    margin-top: 5px;
    line-height: 1.5;
}
.player-chip {
    display: inline-block;
    font-size: 10px;
    padding: 1px 7px;
    border-radius: 10px;
    background: rgba(105, 192, 255, 0.15);
    color: #69c0ff;
    border: 1px solid rgba(105, 192, 255, 0.3);
    margin: 2px 3px 2px 0;
}
.pos-icon {
    display: inline-block;
    width: 12px;
    height: 12px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
    border: 2px solid rgba(255,255,255,0.3);
}
.ann-notes {
    color: #9ca3af;
    font-size: 11px;
    margin-top: 3px;
    font-style: italic;
}

/* 统计面板 */
.stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 8px;
    margin-bottom: 12px;
}
.stat-box {
    background: rgba(13, 17, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 10px 6px;
    text-align: center;
}
.stat-num {
    font-size: 20px;
    font-weight: 700;
    color: #36CFC9;
    font-family: 'Courier New', monospace;
}
.stat-label {
    font-size: 10px;
    color: #9ca3af;
    margin-top: 2px;
}

/* 分隔线 */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(54, 207, 201, 0.2), transparent);
    margin: 10px 0;
}

/* 空状态 */
.empty-state {
    text-align: center;
    padding: 30px 16px;
    color: #6b7280;
    font-size: 13px;
}

/* 迷你球场容器 */
.pitch-container {
    background: rgba(13, 17, 23, 0.8);
    border-radius: 8px;
    padding: 8px;
    margin: 8px 0;
    border: 1px solid rgba(54, 207, 201, 0.15);
}
.pitch-container svg {
    width: 100%;
    display: block;
}
.pitch-info {
    text-align: center;
    font-size: 11px;
    color: #9ca3af;
    margin-top: 6px;
    font-family: monospace;
}

/* 战术模板卡片 */
.template-card {
    background: rgba(13, 17, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 10px 12px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.2s;
}
.template-card:hover {
    border-color: rgba(54, 207, 201, 0.4);
    background: rgba(30, 41, 59, 0.8);
}
.template-name {
    font-size: 13px;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 4px;
}
.template-meta {
    font-size: 11px;
    color: #8b949e;
}

/* 视频段标签 */
.video-tab-bar {
    display: flex;
    gap: 4px;
    margin-bottom: 10px;
    flex-wrap: wrap;
}
.video-tab {
    padding: 5px 12px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    border-bottom: none;
    color: #8b949e;
    transition: all 0.2s;
    background: rgba(22, 27, 34, 0.5);
}
.video-tab.active {
    background: rgba(54, 207, 201, 0.15);
    color: #36CFC9;
    border-color: rgba(54, 207, 201, 0.3);
}
.video-tab:hover {
    color: #e6edf3;
}

/* 球队设置弹窗样式 */
.team-settings-panel {
    background: rgba(22, 27, 34, 0.95);
    border: 1px solid rgba(54, 207, 201, 0.2);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 12px;
}

/* 导出按钮组 */
.export-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-bottom: 10px;
}

/* 滚动条美化 */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: rgba(255,255,255,0.03);
}
::-webkit-scrollbar-thumb {
    background: rgba(54, 207, 201, 0.2);
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover {
    background: rgba(54, 207, 201, 0.4);
}

/* 球员行 */
.player-row {
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 4px 0;
    border-bottom: 1px solid rgba(255,255,255,0.04);
}
.player-row .number {
    width: 28px;
    font-family: monospace;
    font-weight: 600;
    color: #36CFC9;
    text-align: center;
}
.player-row .name {
    flex: 1;
    font-size: 12px;
    color: #d1d5db;
}

/* 表单区域标题 */
.section-title {
    color: #36CFC9;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 12px;
    letter-spacing: 0.5px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(54, 207, 201, 0.2);
}

/* 页脚 */
.app-footer {
    text-align: center;
    padding: 16px 0;
    color: #4b5563;
    font-size: 11px;
    margin-top: 20px;
}

/* 快捷按钮样式统一 */
.stButton > button {
    background: linear-gradient(135deg, #08979c 0%, #006d75 100%);
    color: white;
    border: none;
    border-radius: 6px;
    font-weight: 500;
    transition: all 0.2s ease;
    font-size: 13px;
}
.stButton > button:hover {
    background: linear-gradient(135deg, #36CFC9 0%, #08979c 100%);
    box-shadow: 0 4px 12px rgba(54, 207, 201, 0.3);
}
.stButton > button:active {
    transform: translateY(1px);
}

/* Streamlit tab 样式优化 */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
}
.stTabs [data-baseweb="tab"] {
    height: 38px;
    border-radius: 6px 6px 0 0;
    padding: 0 16px;
    font-size: 13px;
}
.stTabs [aria-selected="true"] {
    background: rgba(54, 207, 201, 0.1) !important;
}
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ============================================================
# Session State 初始化
# ============================================================

def init_state():
    """初始化 session state"""
    if "annotator" not in st.session_state:
        st.session_state.annotator = VideoAnnotator()
    if "current_timestamp" not in st.session_state:
        st.session_state.current_timestamp = 0.0
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
    if "form_key" not in st.session_state:
        st.session_state.form_key = 0
    if "playback_rate" not in st.session_state:
        st.session_state.playback_rate = 1.0
    if "pitch_x" not in st.session_state:
        st.session_state.pitch_x = -1.0
    if "pitch_y" not in st.session_state:
        st.session_state.pitch_y = -1.0
    if "show_team_settings" not in st.session_state:
        st.session_state.show_team_settings = False
    if "active_tab" not in st.session_state:
        st.session_state.active_tab = "标注表单"
    if "pending_template" not in st.session_state:
        st.session_state.pending_template = None
    if "show_json_download" not in st.session_state:
        st.session_state.show_json_download = False
    if "show_csv_download" not in st.session_state:
        st.session_state.show_csv_download = False
    if "show_srt_download" not in st.session_state:
        st.session_state.show_srt_download = False
    if "show_report" not in st.session_state:
        st.session_state.show_report = False


init_state()
annotator: VideoAnnotator = st.session_state.annotator


# ============================================================
# 辅助函数
# ============================================================

def format_time(seconds: float) -> str:
    """秒转 MM:SS 格式"""
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{minutes:02d}:{secs:02d}"


def get_team_color(team_side: str) -> str:
    """获取队伍主色"""
    return annotator.get_team_color(team_side)


def get_team_color_light(team_side: str) -> str:
    """获取队伍浅色"""
    if team_side == "home":
        return annotator.home_color_light if hasattr(annotator, 'home_color_light') else "#69C0FF"
    elif team_side == "away":
        return annotator.away_color_light if hasattr(annotator, 'away_color_light') else "#FF7875"
    return "#8C8C8C"


def render_pitch_html(mark_x: float = -1, mark_y: float = -1, clickable: bool = False) -> str:
    """
    渲染足球场 SVG - 使用完整的 HTML 页面用于 components.html
    确保 SVG 正确渲染为图像而非文本
    """
    # 构建 SVG 内容
    svg_body = ''

    # 场地背景 - 绿色草地
    svg_body += '<rect x="1" y="1" width="398" height="258" fill="#2d5a33" stroke="#1a3d1f" stroke-width="2" rx="4"/>'

    # 草地条纹效果
    for i in range(10):
        x = 1 + i * 39.8
        if i % 2 == 0:
            svg_body += f'<rect x="{x}" y="1" width="39.8" height="258" fill="rgba(255,255,255,0.02)"/>'

    # 中线
    svg_body += '<line x1="200" y1="1" x2="200" y2="259" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>'

    # 中圈
    svg_body += '<circle cx="200" cy="130" r="36" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>'
    svg_body += '<circle cx="200" cy="130" r="4" fill="rgba(255,255,255,0.8)"/>'

    # 左半场大禁区
    svg_body += '<rect x="1" y="65" width="64" height="130" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>'
    # 左半场小禁区
    svg_body += '<rect x="1" y="95" width="28" height="70" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>'
    # 左球门区（点球点等）
    svg_body += '<circle cx="50" cy="130" r="4" fill="rgba(255,255,255,0.6)"/>'
    # 左球门
    svg_body += '<rect x="-3" y="108" width="5" height="44" fill="rgba(255,255,255,0.7)" stroke="rgba(255,255,255,0.9)" stroke-width="1"/>'

    # 右半场大禁区
    svg_body += '<rect x="335" y="65" width="64" height="130" fill="none" stroke="rgba(255,255,255,0.6)" stroke-width="1.5"/>'
    # 右半场小禁区
    svg_body += '<rect x="371" y="95" width="28" height="70" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>'
    # 右点球点
    svg_body += '<circle cx="350" cy="130" r="4" fill="rgba(255,255,255,0.6)"/>'
    # 右球门
    svg_body += '<rect x="398" y="108" width="5" height="44" fill="rgba(255,255,255,0.7)" stroke="rgba(255,255,255,0.9)" stroke-width="1"/>'

    # 禁区弧
    svg_body += '<path d="M 64 100 A 36 36 0 0 1 64 160" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>'
    svg_body += '<path d="M 336 100 A 36 36 0 0 0 336 160" fill="none" stroke="rgba(255,255,255,0.5)" stroke-width="1.5"/>'

    # 角球弧
    corners = [(1, 1), (399, 1), (1, 259), (399, 259)]
    for cx, cy in corners:
        svg_body += f'<circle cx="{cx}" cy="{cy}" r="6" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>'

    # 左右半场标识文字
    svg_body += '<text x="60" y="25" fill="rgba(255,255,255,0.35)" font-size="12" text-anchor="middle" font-weight="500">主队半场</text>'
    svg_body += '<text x="340" y="25" fill="rgba(255,255,255,0.35)" font-size="12" text-anchor="middle" font-weight="500">客队半场</text>'

    # 如果有标记点，绘制标记
    if mark_x >= 0 and mark_y >= 0:
        # 转换为 SVG 坐标（0-100 -> 0-400 / 0-260
        svg_x = mark_x * 4.0
        svg_y = mark_y * 2.6
        svg_body += f'''
        <circle cx="{svg_x}" cy="{svg_y}" r="10" fill="rgba(255, 77, 79, 0.9)" stroke="white" stroke-width="2.5">
            <animate attributeName="r" values="8;12;8" dur="1.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="{svg_x}" cy="{svg_y}" r="3" fill="white"/>
        '''

    # 完整 HTML 页面
    click_script = ''
    if clickable:
        click_script = '''
        <script>
        function handlePitchClick(event) {
            const svg = document.getElementById('pitchSvg');
            const pt = svg.createSVGPoint();
            pt.x = event.clientX;
            pt.y = event.clientY;
            const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
            const x = Math.max(0, Math.min(100, (svgP.x / 400) * 100));
            const y = Math.max(0, Math.min(100, (svgP.y / 260) * 100));
            window.parent.postMessage({
                type: 'pitch_click',
                x: Math.round(x * 10) / 10,
                y: Math.round(y * 10) / 10
            }, '*');
        }
        </script>
        '''

    html = f'''
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{
                margin: 0;
                padding: 0;
                background: transparent;
                overflow: hidden;
                width: 100%;
                height: 100%;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            svg {{
                width: 100%;
                height: 100%;
                max-height: 300px;
                display: block;
                cursor: {'crosshair' if clickable else 'default'};
                object-fit: contain;
            }}
        </style>
    </head>
    <body>
        <svg id="pitchSvg" viewBox="0 0 400 260" xmlns="http://www.w3.org/2000/svg"
             {f'onclick="handlePitchClick(event)"' if clickable else ''}>
            {svg_body}
        </svg>
        {click_script}
    </body>
    </html>
    '''
    return html


def render_timeline_html(video_index: int) -> str:
    """渲染标注时间轴 HTML"""
    annotations = annotator.get_annotations_for_video(video_index)
    duration = max(annotator.video_duration, 1.0)
    current_time = st.session_state.current_timestamp

    dots_html = ""
    for ann in annotations:
        pct = (ann.timestamp / duration) * 100
        color = get_team_color(ann.team_side) if ann.team_side else EVENT_COLORS.get(ann.event_type, "#8C8C8C")
        dots_html += (
            f'<div class="timeline-dot" style="left: {pct}%; background: {color};" '
            f'title="{ann.formatted_time} - {ann.event_type} {ann.team}" '
            f'onclick="event.stopPropagation(); window.parent.postMessage({{type: \'goto_timestamp\', ts: {ann.timestamp}}}, \'*\');">'
            f'</div>'
        )

    cursor_pct = (current_time / duration) * 100

    return f"""
    <div class="timeline-label">
        <span class="title">📌 标注时间轴</span>
        <span>{format_time(current_time)} / {format_time(duration)}</span>
    </div>
    <div class="annotation-timeline" id="ann-timeline"
         onclick="const rect = this.getBoundingClientRect();
                  const pct = (event.clientX - rect.left) / rect.width;
                  window.parent.postMessage({{type: 'goto_timestamp', ts: Math.max(0, pct * {duration})}}, '*');">
        <div class="timeline-cursor" style="left: {cursor_pct}%;"></div>
        {dots_html}
    </div>
    """


# ============================================================
# 顶部工具栏
# ============================================================

def render_top_toolbar():
    """渲染顶部工具栏"""
    toolbar_html = '''
    <div class="top-toolbar">
        <div class="toolbar-title">
            ⚽ 足球战术视频标注工具
        </div>
        <div class="toolbar-spacer"></div>
    </div>
    '''
    st.markdown(toolbar_html, unsafe_allow_html=True)

    # 工具栏按钮 - 使用 Streamlit 列布局
    col_upload, col_team, col_export, col_help = st.columns([1, 1, 1, 1])

    with col_upload:
        uploaded_files = st.file_uploader(
            "📹 上传视频",
            type=["mp4", "mov", "avi", "mkv", "webm"],
            accept_multiple_files=True,
            help="支持 MP4/MOV/AVI/MKV/WEBM，可上传多段视频",
            label_visibility="collapsed",
            key="top_upload",
        )

    with col_team:
        if st.button("👥 球队设置", use_container_width=True, key="btn_team_settings"):
            st.session_state.show_team_settings = not st.session_state.show_team_settings
            st.rerun()

    with col_export:
        if st.button("💾 导出数据", use_container_width=True, key="btn_export_top"):
            st.session_state.active_tab = "数据管理"
            st.rerun()

    with col_help:
        with st.expander("❓ 使用帮助", expanded=False):
            st.markdown("""
            **快速入门：**
            1. 上传比赛视频文件
            2. 播放视频，在关键时间点暂停
            3. 填写右侧标注表单，点击"添加标注"
            4. 在"标注列表"中查看和管理所有标注

            **快捷键：**
            - 空格：播放/暂停
            - ← / →：快退/快进 5秒
            - ↑ / ↓：上一帧/下一帧
            - N：新建标注
            - 1-8：选择事件类型
            """)

    # 处理上传的视频
    if uploaded_files:
        current_count = len(annotator.video_segments)
        for i, uf in enumerate(uploaded_files):
            vid_bytes = uf.getvalue()
            exists = False
            for seg in annotator.video_segments:
                if seg.name == uf.name:
                    exists = True
                    break
            if not exists:
                label_options = ["上半场", "下半场", "加时赛上", "加时赛下", "点球大战"]
                label = label_options[i + current_count] if (i + current_count) < len(label_options) else f"第{i + current_count + 1}段"
                annotator.add_video_segment(uf.name, vid_bytes, label)


render_top_toolbar()


# ============================================================
# 球队设置面板（可折叠）
# ============================================================

def render_team_settings():
    """渲染球队设置面板"""
    if not st.session_state.show_team_settings:
        return

    st.markdown('<div class="team-settings-panel">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">👥 球队设置</div>', unsafe_allow_html=True)

    home_col, away_col = st.columns(2)

    with home_col:
        st.markdown("**🔵 主队设置")
        home_name = st.text_input("主队名称", value=annotator.home_roster.team_name, key="home_name_input_v2")
        if home_name != annotator.home_roster.team_name:
            annotator.set_team_name("home", home_name)

        home_color = st.color_picker("主队颜色", value=annotator.home_color, key="home_color_picker_v2")
        if home_color != annotator.home_color:
            annotator.home_color = home_color

        # 球员列表
        st.markdown("**球员名单**")
        with st.expander(f"查看/编辑（{len(annotator.home_roster.players)}人）", expanded=False):
            h_num_col, h_name_col, h_add_col = st.columns([1, 2, 1])
            with h_num_col:
                h_number = st.text_input("号码", key="home_add_num_v2", label_visibility="collapsed", placeholder="号")
            with h_name_col:
                h_name_p = st.text_input("姓名", key="home_add_name_v2", label_visibility="collapsed", placeholder="姓名")
            with h_add_col:
                if st.button("➕", key="home_add_btn_v2", use_container_width=True):
                    if h_number or h_name_p:
                        annotator.add_player("home", h_number, h_name_p)
                        st.rerun()

            for idx, player in enumerate(annotator.home_roster.players):
                pcol1, pcol2, pcol3 = st.columns([1, 3, 1])
                with pcol1:
                    st.markdown(f'<div class="number">{player.number or "-"}</div>', unsafe_allow_html=True)
                with pcol2:
                    st.markdown(f'<div class="name">{player.name or "未命名"}</div>', unsafe_allow_html=True)
                with pcol3:
                    if st.button("🗑", key=f"home_del_{idx}_v2", use_container_width=True):
                        annotator.remove_player("home", idx)
                        st.rerun()

    with away_col:
        st.markdown("**🔴 客队设置**")
        away_name = st.text_input("客队名称", value=annotator.away_roster.team_name, key="away_name_input_v2")
        if away_name != annotator.away_roster.team_name:
            annotator.set_team_name("away", away_name)

        away_color = st.color_picker("客队颜色", value=annotator.away_color, key="away_color_picker_v2")
        if away_color != annotator.away_color:
            annotator.away_color = away_color

        st.markdown("**球员名单**")
        with st.expander(f"查看/编辑（{len(annotator.away_roster.players)}人）", expanded=False):
            a_num_col, a_name_col, a_add_col = st.columns([1, 2, 1])
            with a_num_col:
                a_number = st.text_input("号码", key="away_add_num_v2", label_visibility="collapsed", placeholder="号")
            with a_name_col:
                a_name_p = st.text_input("姓名", key="away_add_name_v2", label_visibility="collapsed", placeholder="姓名")
            with a_add_col:
                if st.button("➕", key="away_add_btn_v2", use_container_width=True):
                    if a_number or a_name_p:
                        annotator.add_player("away", a_number, a_name_p)
                        st.rerun()

            for idx, player in enumerate(annotator.away_roster.players):
                pcol1, pcol2, pcol3 = st.columns([1, 3, 1])
                with pcol1:
                    st.markdown(f'<div class="number">{player.number or "-"}</div>', unsafe_allow_html=True)
                with pcol2:
                    st.markdown(f'<div class="name">{player.name or "未命名"}</div>', unsafe_allow_html=True)
                with pcol3:
                    if st.button("🗑", key=f"away_del_{idx}_v2", use_container_width=True):
                        annotator.remove_player("away", idx)
                        st.rerun()

    # 名单导入导出
    st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    roster_col1, roster_col2 = st.columns(2)
    with roster_col1:
        roster_json = annotator.export_roster_json_string()
        st.download_button(
            "📤 导出名单",
            data=roster_json,
            file_name="team_rosters.json",
            mime="application/json",
            use_container_width=True,
            key="export_roster_btn_v2",
        )
    with roster_col2:
        roster_file = st.file_uploader(
            "📥 导入名单",
            type=["json"],
            label_visibility="collapsed",
            key="import_roster_uploader_v2",
        )
        if roster_file is not None:
            try:
                content = roster_file.read().decode("utf-8")
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
                tfile.write(content)
                tfile.close()
                if annotator.import_roster_json(tfile.name):
                    st.success("名单导入成功")
                    os.unlink(tfile.name)
                    st.rerun()
            except Exception as e:
                st.error(f"导入失败：{str(e)}")

    st.markdown('</div>', unsafe_allow_html=True)


render_team_settings()


# ============================================================
# 主布局：左侧视频 + 右侧标签页
# ============================================================

current_video = annotator.current_video

# 主布局：左大右小
col_video, col_right = st.columns([3, 2])


# ============================================================
# 左侧：视频播放器 + 时间轴 + 播放控制
# ============================================================

with col_video:
    # 视频段切换标签
    if annotator.video_segments:
        tabs_html = '<div class="video-tab-bar">'
        for i, seg in enumerate(annotator.video_segments):
            is_active = i == annotator.current_video_index
            label = seg.label or f"第{i+1}段"
            tabs_html += (
                f'<span class="video-tab {"active" if is_active else ""}" '
                f'onclick="window.parent.postMessage({{type: \'switch_video\', index: {i}}}, \'*\');">'
                f'{label}'
                f'</span>'
            )
        tabs_html += '</div>'
        st.markdown(tabs_html, unsafe_allow_html=True)

    # 视频播放器（自定义 HTML5 播放器，所有控制通过 JS 实现）
    if current_video and current_video.video_bytes:
        # 将视频字节转换为 base64 data URL
        import base64 as _b64
        vid_b64 = _b64.b64encode(current_video.video_bytes).decode("utf-8")
        # 根据文件扩展名确定 MIME 类型
        _name_lower = current_video.name.lower()
        if _name_lower.endswith('.webm'):
            _mime = 'video/webm'
        elif _name_lower.endswith('.ogg') or _name_lower.endswith('.ogv'):
            _mime = 'video/ogg'
        elif _name_lower.endswith('.mov'):
            _mime = 'video/quicktime'
        elif _name_lower.endswith('.mkv'):
            _mime = 'video/x-matroska'
        elif _name_lower.endswith('.avi'):
            _mime = 'video/x-msvideo'
        else:
            _mime = 'video/mp4'
        video_data_url = f"data:{_mime};base64,{vid_b64}"

        # 构建标注点数据（用于时间轴显示）
        anns_for_timeline = []
        for ann in annotator.get_annotations_for_video(annotator.current_video_index):
            color = get_team_color(ann.team_side) if ann.team_side else EVENT_COLORS.get(ann.event_type, "#8C8C8C")
            anns_for_timeline.append({
                "timestamp": ann.timestamp,
                "timeText": ann.formatted_time,
                "eventType": ann.event_type,
                "team": ann.team,
                "color": color,
            })

        # seek_token - 每次从外部跳转时递增，触发组件重新加载并seek
        if "video_seek_token" not in st.session_state:
            st.session_state.video_seek_token = 0

        # 生成自定义视频播放器 HTML
        player_html = render_custom_video_player_html(
            video_data_url=video_data_url,
            annotations_data=anns_for_timeline,
            initial_time=st.session_state.current_timestamp,
            initial_rate=st.session_state.playback_rate,
            seek_token=st.session_state.video_seek_token,
            duration=max(annotator.video_duration, 0.0),
            mime_type=_mime,
        )

        # 渲染视频播放器组件，并获取返回的时间数据
        video_component_val = components.html(player_html, height=800, scrolling=False)

        # 处理组件返回的时间数据（双向通信）
        if video_component_val and isinstance(video_component_val, dict):
            new_time = video_component_val.get("currentTime")
            new_duration = video_component_val.get("duration", 0)
            new_rate = video_component_val.get("playbackRate", 1.0)
            action = video_component_val.get("action", "")

            # 更新视频时长
            if new_duration and new_duration > 0 and abs(new_duration - annotator.video_duration) > 1:
                annotator.set_video_duration(new_duration)

            # 更新当前时间（仅当差异较大时更新，避免频繁 rerun）
            if new_time is not None and abs(new_time - st.session_state.current_timestamp) > 0.3:
                st.session_state.current_timestamp = float(new_time)

            # 更新倍速
            if new_rate and abs(new_rate - st.session_state.playback_rate) > 0.01:
                st.session_state.playback_rate = float(new_rate)

        # 视频段管理（折叠面板）
        if len(annotator.video_segments) > 1:
            with st.expander("📹 视频段管理", expanded=False):
                for i, seg in enumerate(annotator.video_segments):
                    vcol1, vcol2, vcol3 = st.columns([2, 3, 1])
                    with vcol1:
                        new_label = st.text_input("标签", value=seg.label, key=f"seg_label_{i}_v2", label_visibility="collapsed")
                        if new_label != seg.label:
                            seg.label = new_label
                    with vcol2:
                        st.markdown(f"<small>{seg.name}</small>", unsafe_allow_html=True)
                    with vcol3:
                        if st.button("删除", key=f"del_seg_{i}_v2", use_container_width=True):
                            annotator.remove_video_segment(i)
                            st.rerun()
    else:
        st.markdown('''
        <div class="video-placeholder">
            <div class="icon">🎬</div>
            <div class="title">上传比赛视频开始标注</div>
            <div class="desc">
                支持 MP4 / MOV / AVI / MKV / WEBM 格式<br>
                可上传多段视频（上下半场等）<br>
                点击顶部 "📹 上传视频" 按钮
            </div>
        </div>
        ''', unsafe_allow_html=True)

        st.markdown('<div class="playback-controls">', unsafe_allow_html=True)
        st.markdown('<div class="pb-section-title">⏯ 播放控制</div>', unsafe_allow_html=True)
        st.info("请先上传视频文件以启用播放控制")
        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 右侧：标签页面板
# ============================================================

with col_right:
    st.markdown('<div class="right-panel">', unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs([
        "📝 标注表单",
        "📋 战术模板",
        "📊 标注列表",
        "💾 数据管理",
    ])

    # --------------------------------------------------------
    # Tab 1: 标注表单
    # --------------------------------------------------------
    with tab1:
        st.markdown('<div style="padding: 16px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📝 标注表单</div>', unsafe_allow_html=True)

        # 编辑模式
        editing_ann = None
        if st.session_state.editing_id:
            editing_ann = annotator.get_annotation(st.session_state.editing_id)
            if editing_ann:
                st.session_state.pitch_x = editing_ann.x
                st.session_state.pitch_y = editing_ann.y
        elif st.session_state.pending_template:
            # 从模板创建临时标注对象用于预填充表单
            tpl = st.session_state.pending_template
            editing_ann = TacticalAnnotation(
                timestamp=st.session_state.current_timestamp,
                event_type=tpl.get("event_type", "传球"),
                team=tpl.get("team", ""),
                team_side=tpl.get("team_side", ""),
                description=tpl.get("description", ""),
                tactic_zone=tpl.get("tactic_zone", ""),
                notes=tpl.get("notes", ""),
                video_index=annotator.current_video_index,
            )
            # 用完即清除
            st.session_state.pending_template = None

        form_key = f"ann_form_{st.session_state.form_key}"

        pitch_x = st.session_state.get("pitch_x", -1.0)
        pitch_y = st.session_state.get("pitch_y", -1.0)

        # 战术板 - 使用 components.html 确保 SVG 正确渲染
        st.markdown("**🏟 战术位置**")

        pitch_html_content = render_pitch_html(mark_x=pitch_x, mark_y=pitch_y, clickable=False)
        components.html(pitch_html_content, height=320)

        if pitch_x >= 0:
            st.markdown(
                f'<div class="pitch-info">X: {pitch_x:.1f} &nbsp;&nbsp; Y: {pitch_y:.1f}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown('<div class="pitch-info">未设置位置</div>', unsafe_allow_html=True)

        # 坐标滑块
        if pitch_x < 0:
            if st.button("📍 设置坐标位置", key="enable_position_v2", use_container_width=True):
                st.session_state.pitch_x = 50.0
                st.session_state.pitch_y = 50.0
                st.rerun()
        else:
            new_x = st.slider("横向 X（左→右）", 0.0, 100.0, pitch_x, 0.5, key="pitch_x_slider_v2")
            new_y = st.slider("纵向 Y（上→下）", 0.0, 100.0, pitch_y, 0.5, key="pitch_y_slider_v2")
            if new_x != pitch_x or new_y != pitch_y:
                st.session_state.pitch_x = new_x
                st.session_state.pitch_y = new_y
                st.rerun()

            # 快捷位置按钮
            st.caption("⚡ 快捷位置：")
            qcol1, qcol2, qcol3, qcol4 = st.columns(4)
            with qcol1:
                if st.button("本方禁区", key="qp1_v2", use_container_width=True):
                    st.session_state.pitch_x = 10.0
                    st.session_state.pitch_y = 50.0
                    st.rerun()
            with qcol2:
                if st.button("中场", key="qp2_v2", use_container_width=True):
                    st.session_state.pitch_x = 50.0
                    st.session_state.pitch_y = 50.0
                    st.rerun()
            with qcol3:
                if st.button("对方禁区", key="qp3_v2", use_container_width=True):
                    st.session_state.pitch_x = 90.0
                    st.session_state.pitch_y = 50.0
                    st.rerun()
            with qcol4:
                if st.button("清除", key="qp4_v2", use_container_width=True):
                    st.session_state.pitch_x = -1.0
                    st.session_state.pitch_y = -1.0
                    st.rerun()

        st.markdown('<div style="height: 12px;"></div>', unsafe_allow_html=True)

        # 标注表单
        with st.form(key=form_key, clear_on_submit=False):
            # 时间戳
            current_min = int(st.session_state.current_timestamp // 60)
            current_sec = int(st.session_state.current_timestamp % 60)
            video_label = current_video.label if current_video else "无"
            st.markdown(
                f"**⏱ 时间点：** `{current_min:02d}:{current_sec:02d}` "
                f"<small style='color:#6b7280;'>[{video_label}]</small>",
                unsafe_allow_html=True,
            )

            # 事件类型
            event_type = st.selectbox(
                "事件类型 *",
                EVENT_TYPES,
                index=EVENT_TYPES.index(editing_ann.event_type) if editing_ann and editing_ann.event_type in EVENT_TYPES else 0,
                key="form_event_type_v2",
            )

            # 队伍侧别 + 队伍名
            team_col1, team_col2 = st.columns([1, 2])
            with team_col1:
                team_side_options = ["", "主队", "客队"]
                current_side_label = {"home": "主队", "away": "客队", "": ""}.get(
                    editing_ann.team_side if editing_ann else "", ""
                )
                team_side_label = st.selectbox(
                    "队伍",
                    team_side_options,
                    index=team_side_options.index(current_side_label) if current_side_label in team_side_options else 0,
                    key="form_team_side_v2",
                )
                team_side = {"主队": "home", "客队": "away", "": ""}.get(team_side_label, "")

            with team_col2:
                default_team = editing_ann.team if editing_ann else ""
                if team_side and not default_team:
                    default_team = annotator.home_roster.team_name if team_side == "home" else annotator.away_roster.team_name
                team = st.text_input(
                    "队伍名称",
                    value=default_team,
                    key="form_team_v2",
                )

            # 球员
            st.markdown("**涉及球员**")
            all_players = []
            if team_side == "home":
                all_players = annotator.home_roster.get_player_names()
            elif team_side == "away":
                all_players = annotator.away_roster.get_player_names()
            else:
                all_players = (
                    [f"[主] {p.display}" for p in annotator.home_roster.players] +
                    [f"[客] {p.display}" for p in annotator.away_roster.players]
                )

            if all_players:
                default_players = []
                if editing_ann and editing_ann.players:
                    for p in editing_ann.players:
                        if p in all_players:
                            default_players.append(p)
                        else:
                            for ap in all_players:
                                if p in ap:
                                    default_players.append(ap)
                                    break

                selected_players = st.multiselect(
                    "从名单选择",
                    all_players,
                    default=default_players,
                    key="form_players_select_v2",
                    label_visibility="collapsed",
                )
                players_input_text = st.text_input(
                    "手动补充（逗号分隔）",
                    value="",
                    placeholder="其他球员，用逗号分隔",
                    key="form_players_manual_v2",
                )
                players_list = selected_players + [p.strip() for p in players_input_text.split(",") if p.strip()]
            else:
                players_input_text = st.text_input(
                    "涉及球员（逗号分隔）",
                    value=",".join(editing_ann.players) if editing_ann else "",
                    placeholder="在球队设置中添加球员名单后可下拉选择",
                    key="form_players_v2",
                )
                players_list = [p.strip() for p in players_input_text.split(",") if p.strip()]

            # 场区
            tactic_zone = st.selectbox(
                "场区",
                [""] + TACTIC_ZONES,
                index=(TACTIC_ZONES.index(editing_ann.tactic_zone) + 1) if editing_ann and editing_ann.tactic_zone in TACTIC_ZONES else 0,
                key="form_zone_v2",
            )

            # 描述
            description = st.text_area(
                "事件描述",
                value=editing_ann.description if editing_ann else "",
                placeholder="简要描述本次战术事件...",
                height=65,
                key="form_desc_v2",
            )

            # 备注
            notes = st.text_area(
                "备注",
                value=editing_ann.notes if editing_ann else "",
                placeholder="其他补充说明...",
                height=45,
                key="form_notes_v2",
            )

            # 提交按钮
            submit_label = "✏️ 更新标注" if st.session_state.editing_id else "➕ 添加标注"
            submitted = st.form_submit_button(submit_label, use_container_width=True)

            if submitted:
                if st.session_state.editing_id:
                    success = annotator.edit_annotation(
                        st.session_state.editing_id,
                        event_type=event_type,
                        team=team,
                        team_side=team_side,
                        players=players_list,
                        tactic_zone=tactic_zone,
                        description=description,
                        notes=notes,
                        x=st.session_state.get("pitch_x", -1.0),
                        y=st.session_state.get("pitch_y", -1.0),
                    )
                    if success:
                        st.success("✅ 标注已更新！")
                        st.session_state.editing_id = None
                        st.session_state.form_key += 1
                        st.rerun()
                else:
                    ann = annotator.add_annotation(
                        timestamp=st.session_state.current_timestamp,
                        event_type=event_type,
                        team=team,
                        team_side=team_side,
                        players=players_list,
                        tactic_zone=tactic_zone,
                        description=description,
                        notes=notes,
                        x=st.session_state.get("pitch_x", -1.0),
                        y=st.session_state.get("pitch_y", -1.0),
                        video_index=annotator.current_video_index,
                    )
                    st.success(f"✅ 已添加标注（{ann.formatted_time}）")
                    st.session_state.form_key += 1
                    st.session_state.pitch_x = -1.0
                    st.session_state.pitch_y = -1.0
                    st.rerun()

        # 取消编辑
        if st.session_state.editing_id:
            if st.button("↩️ 取消编辑", use_container_width=True, key="cancel_edit_v2"):
                st.session_state.editing_id = None
                st.session_state.form_key += 1
                st.session_state.pitch_x = -1.0
                st.session_state.pitch_y = -1.0
                st.rerun()

        # 事件类型图例
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**🎨 事件类型图例")
        legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
        for evt, color in EVENT_COLORS.items():
            legend_html += f'<span class="event-tag" style="background: {color};">{evt}</span>'
        legend_html += '</div>'
        st.markdown(legend_html, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------
    # Tab 2: 战术模板
    # --------------------------------------------------------
    with tab2:
        st.markdown('<div style="padding: 16px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📋 战术模板</div>', unsafe_allow_html=True)
        st.caption("点击模板快速填充标注表单")

        default_tpls = [t for t in annotator.templates if not t.is_custom]
        custom_tpls = [t for t in annotator.templates if t.is_custom]

        # 默认模板
        st.markdown("**预设模板")
        for tpl in default_tpls:
            team_color = get_team_color(tpl.team_side) if tpl.team_side else "#8C8C8C"
            team_label = {"home": annotator.home_roster.team_name, "away": annotator.away_roster.team_name, "": "通用"}.get(tpl.team_side, "")

            tpl_html = f'''
            <div class="template-card">
                <div class="template-name">
                    <span class="pos-icon" style="background: {team_color};"></span>
                    {tpl.name}
                </div>
                <div class="template-meta">
                    <span class="event-tag" style="background: {EVENT_COLORS.get(tpl.event_type, '#888')}; font-size: 9px; padding: 0 6px;">
                        {tpl.event_type}
                    </span>
                    {f'<span style="margin-left: 4px; color: #6b7280;">{team_label}</span>' if team_label else ''}
                </div>
            </div>
            '''
            # 用按钮包裹模板卡片
            col_tpl = st.container()
            with col_tpl:
                if st.button(f"🎯 {tpl.name}", key=f"tpl_{tpl.template_id}", use_container_width=True):
                    tpl_data = annotator.apply_template(tpl.template_id)
                    if tpl_data:
                        st.session_state.editing_id = None
                        st.session_state.form_key += 1
                        st.session_state.pitch_x = -1.0
                        st.session_state.pitch_y = -1.0
                        # 将模板数据暂存到 session state
                        st.session_state.pending_template = tpl_data
                        st.success(f"已应用模板：{tpl.name}")
                        st.rerun()
                st.caption(f"{tpl.event_type} · {team_label}")
                if tpl.description:
                    st.caption(tpl.description)
                st.markdown("")

        # 自定义模板
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("**✨ 自定义模板**")

        with st.expander("新建自定义模板", expanded=False):
            new_tpl_name = st.text_input("模板名称", key="new_tpl_name_v2")
            new_tpl_event = st.selectbox("事件类型", EVENT_TYPES, key="new_tpl_event_v2")
            new_tpl_side = st.selectbox(
                "队伍",
                ["通用", "主队", "客队"],
                key="new_tpl_side_v2",
            )
            new_tpl_zone = st.selectbox("场区", [""] + TACTIC_ZONES, key="new_tpl_zone_v2")
            new_tpl_desc = st.text_area("描述", height=60, key="new_tpl_desc_v2")
            if st.button("创建模板", use_container_width=True, key="create_tpl_btn_v2"):
                side_map = {"通用": "", "主队": "home", "客队": "away"}
                annotator.add_template(
                    name=new_tpl_name,
                    event_type=new_tpl_event,
                    team_side=side_map.get(new_tpl_side, ""),
                    description=new_tpl_desc,
                    tactic_zone=new_tpl_zone,
                )
                st.success("模板创建成功！")
                st.rerun()

        if custom_tpls:
            for tpl in custom_tpls:
                tpl_col1, tpl_col2 = st.columns([4, 1])
                with tpl_col1:
                    if st.button(f"⭐ {tpl.name}", key=f"cust_tpl_{tpl.template_id}", use_container_width=True):
                        tpl_data = annotator.apply_template(tpl.template_id)
                        if tpl_data:
                            st.session_state.editing_id = None
                            st.session_state.form_key += 1
                            st.session_state.pending_template = tpl_data
                            st.success(f"已应用模板：{tpl.name}")
                            st.rerun()
                with tpl_col2:
                    if st.button("🗑", key=f"del_cust_tpl_{tpl.template_id}", use_container_width=True):
                        annotator.delete_template(tpl.template_id)
                        st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------
    # Tab 3: 标注列表
    # --------------------------------------------------------
    with tab3:
        st.markdown('<div style="padding: 16px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">📊 标注列表</div>', unsafe_allow_html=True)

        # 统计概览
        stats = annotator.stats
        stats_html = '<div class="stats-grid">'
        stats_html += f'<div class="stat-box"><div class="stat-num">{stats["total"]}</div><div class="stat-label">总数</div></div>'
        stats_html += f'<div class="stat-box"><div class="stat-num">{len(stats["by_event_type"])}</div><div class="stat-label">事件类型</div></div>'
        stats_html += f'<div class="stat-box"><div class="stat-num">{len(stats["by_team"])}</div><div class="stat-label">队伍</div></div>'
        stats_html += f'<div class="stat-box"><div class="stat-num">{len(stats["by_zone"])}</div><div class="stat-label">场区</div></div>'
        stats_html += '</div>'
        st.markdown(stats_html, unsafe_allow_html=True)

        # 筛选器
        if annotator.annotations:
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                filter_event = st.selectbox(
                    "事件筛选",
                    ["全部事件"] + EVENT_TYPES,
                    key="filter_event_v2",
                )
            with filter_col2:
                filter_team_side = st.selectbox(
                    "队伍筛选",
                    ["全部队伍", "主队", "客队"],
                    key="filter_team_side_v2",
                )

            if len(annotator.video_segments) > 1:
                filter_video_opts = ["全部视频"] + [seg.label or f"第{i+1}段" for i, seg in enumerate(annotator.video_segments)]
                filter_video = st.selectbox(
                    "视频段筛选",
                    filter_video_opts,
                    key="filter_video_v2",
                )
            else:
                filter_video_opts = ["全部视频"]
                filter_video = "全部视频"

            # 过滤
            filtered = annotator.annotations
            if filter_event != "全部事件":
                filtered = [a for a in filtered if a.event_type == filter_event]
            if filter_team_side != "全部队伍":
                side = "home" if filter_team_side == "主队" else "away"
                filtered = [a for a in filtered if a.team_side == side]
            if filter_video != "全部视频":
                video_idx = filter_video_opts.index(filter_video) - 1
                filtered = [a for a in filtered if a.video_index == video_idx]

            st.markdown(f"共 **{len(filtered)}** 条标注")
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

            # 逐条渲染
            for i, ann in enumerate(filtered):
                team_color = get_team_color(ann.team_side)
                team_color_light = get_team_color_light(ann.team_side)

                item_html = f'<div class="ann-item" style="border-left-color: {team_color if ann.team_side else EVENT_COLORS.get(ann.event_type, "#8C8C8C")};">'

                if len(annotator.video_segments) > 1:
                    seg_label = (
                        annotator.video_segments[ann.video_index].label
                        if 0 <= ann.video_index < len(annotator.video_segments)
                        else f"第{ann.video_index + 1}段"
                    )
                    item_html += f'<div style="font-size: 10px; color: #6b7280; margin-bottom: 2px;">📹 {seg_label}</div>'

                item_html += f'<span class="ann-time">{ann.formatted_time}</span>'
                item_html += f'<span class="event-tag" style="background: {EVENT_COLORS.get(ann.event_type, "#8C8C8C")};">{ann.event_type}</span>'

                if ann.team:
                    bg_color = f"rgba({int(team_color[1:3], 16)}, {int(team_color[3:5], 16)}, {int(team_color[5:7], 16)}, 0.2)" if ann.team_side else "rgba(146, 84, 222, 0.2)"
                    border_color = f"rgba({int(team_color[1:3], 16)}, {int(team_color[3:5], 16)}, {int(team_color[5:7], 16)}, 0.3)" if ann.team_side else "rgba(146, 84, 222, 0.3)"
                    text_color = team_color_light if ann.team_side else "#b37feb"
                    item_html += f'<span class="team-tag" style="background: {bg_color}; color: {text_color}; border: 1px solid {border_color};">{ann.team}</span>'

                if ann.tactic_zone:
                    item_html += f'<span class="zone-tag">{ann.tactic_zone}</span>'

                if ann.has_coordinates:
                    pos_color = team_color if ann.team_side else EVENT_COLORS.get(ann.event_type, "#8C8C8C")
                    item_html += f'<span class="pos-icon" style="background: {pos_color}; margin-left: 4px;" title="位置: X={ann.x:.1f}, Y={ann.y:.1f}"></span>'

                if ann.players:
                    item_html += '<div style="margin-top: 5px;">'
                    for p in ann.players:
                        item_html += f'<span class="player-chip">👤 {p}</span>'
                    item_html += '</div>'

                if ann.description:
                    item_html += f'<div class="ann-desc">{ann.description}</div>'

                if ann.notes:
                    item_html += f'<div class="ann-notes">📝 {ann.notes}</div>'

                item_html += '</div>'
                st.markdown(item_html, unsafe_allow_html=True)

                # 操作按钮
                btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
                with btn_col1:
                    if st.button("👁 跳转", key=f"goto_{ann.annotation_id}_v2", use_container_width=True):
                        annotator.switch_video(ann.video_index)
                        st.session_state.current_timestamp = ann.timestamp
                        if "video_seek_token" not in st.session_state:
                            st.session_state.video_seek_token = 0
                        st.session_state.video_seek_token += 1
                        st.rerun()
                with btn_col2:
                    if st.button("✏️ 编辑", key=f"edit_{ann.annotation_id}_v2", use_container_width=True):
                        st.session_state.editing_id = ann.annotation_id
                        st.session_state.current_timestamp = ann.timestamp
                        annotator.switch_video(ann.video_index)
                        st.session_state.form_key += 1
                        st.rerun()
                with btn_col3:
                    if st.button("🗑 删除", key=f"del_{ann.annotation_id}_v2", use_container_width=True):
                        st.session_state[f"confirm_del_{ann.annotation_id}"] = True

                if st.session_state.get(f"confirm_del_{ann.annotation_id}"):
                    st.warning("确定删除这条标注？")
                    del_col1, del_col2 = st.columns(2)
                    with del_col1:
                        if st.button("✅ 确认", key=f"confirm_{ann.annotation_id}_v2", use_container_width=True):
                            annotator.delete_annotation(ann.annotation_id)
                            if st.session_state.editing_id == ann.annotation_id:
                                st.session_state.editing_id = None
                            st.success("已删除")
                            st.rerun()
                    with del_col2:
                        if st.button("❌ 取消", key=f"cancel_{ann.annotation_id}_v2", use_container_width=True):
                            st.session_state[f"confirm_del_{ann.annotation_id}"] = False
                            st.rerun()

                if i < len(filtered) - 1:
                    st.markdown('<div style="height: 4px;"></div>', unsafe_allow_html=True)
        else:
            st.markdown(
                '<div class="empty-state">暂无标注数据<br>在"标注表单"中添加第一条标注吧！</div>',
                unsafe_allow_html=True,
            )

        st.markdown('</div>', unsafe_allow_html=True)

    # --------------------------------------------------------
    # Tab 4: 数据管理
    # --------------------------------------------------------
    with tab4:
        st.markdown('<div style="padding: 16px;">', unsafe_allow_html=True)
        st.markdown('<div class="section-title">💾 数据管理</div>', unsafe_allow_html=True)

        # 导出
        st.markdown("**📤 导出标注数据**")

        exp_col1, exp_col2 = st.columns(2)

        with exp_col1:
            if st.button("📄 JSON 导出", use_container_width=True, key="export_json_btn_v2"):
                if annotator.annotations:
                    st.session_state.show_json_download = True
                else:
                    st.warning("暂无标注数据")

            if st.button("📊 CSV 导出", use_container_width=True, key="export_csv_btn_v2"):
                if annotator.annotations:
                    st.session_state.show_csv_download = True
                else:
                    st.warning("暂无标注数据")

        with exp_col2:
            if st.button("📝 SRT 字幕", use_container_width=True, key="export_srt_btn_v2"):
                if annotator.annotations:
                    st.session_state.show_srt_download = True
                else:
                    st.warning("暂无标注数据")

            if st.button("📋 战术报告", use_container_width=True, key="export_report_btn_v2"):
                if annotator.annotations:
                    st.session_state.show_report = True
                else:
                    st.warning("暂无标注数据")

        # JSON 下载
        if st.session_state.get("show_json_download"):
            json_str = annotator.export_json_string()
            fn = f"tactical_annotations_{current_video.name.split('.')[0] if current_video else 'export'}.json"
            st.download_button(
                "💾 下载 JSON 文件",
                data=json_str,
                file_name=fn,
                mime="application/json",
                use_container_width=True,
                key="dl_json_v2",
            )

        # CSV 下载
        if st.session_state.get("show_csv_download"):
            csv_str = annotator.export_csv_string()
            fn = f"tactical_annotations_{current_video.name.split('.')[0] if current_video else 'export'}.csv"
            st.download_button(
                "💾 下载 CSV 文件",
                data=csv_str,
                file_name=fn,
                mime="text/csv",
                use_container_width=True,
                key="dl_csv_v2",
            )

        # SRT 下载
        if st.session_state.get("show_srt_download"):
            srt_str = annotator.export_srt_string()
            fn = f"tactical_annotations_{current_video.name.split('.')[0] if current_video else 'export'}.srt"
            st.download_button(
                "💾 下载 SRT 字幕",
                data=srt_str,
                file_name=fn,
                mime="text/plain",
                use_container_width=True,
                key="dl_srt_v2",
            )

        # 战术报告
        if st.session_state.get("show_report"):
            report_md = annotator.export_report_markdown()
            with st.expander("📋 查看战术报告", expanded=True):
                st.markdown(report_md)
            fn = f"tactical_report_{current_video.name.split('.')[0] if current_video else 'export'}.md"
            st.download_button(
                "💾 下载报告 (Markdown)",
                data=report_md,
                file_name=fn,
                mime="text/markdown",
                use_container_width=True,
                key="dl_report_v2",
            )

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 导入
        st.markdown("**📥 导入标注数据**")
        import_file = st.file_uploader(
            "选择 JSON 标注文件",
            type=["json"],
            label_visibility="collapsed",
            help="导入已有的标注数据",
            key="import_uploader_v2",
        )
        if import_file is not None:
            try:
                content = import_file.read().decode("utf-8")
                tfile = tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode="w", encoding="utf-8")
                tfile.write(content)
                tfile.close()
                if annotator.import_json(tfile.name):
                    st.success(f"✅ 成功导入 {len(annotator.annotations)} 条标注")
                    os.unlink(tfile.name)
                    st.rerun()
                else:
                    st.error("❌ 导入失败：文件格式不正确")
                    os.unlink(tfile.name)
            except Exception as e:
                st.error(f"❌ 导入失败：{str(e)}")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 页脚
# ============================================================

st.markdown(
    '''
    <div class="app-footer">
        ⚽ Tactical Video Annotator v2.1 · 专业足球战术分析工具 · 数据格式兼容 AI 战术验证脚本
    </div>
    ''',
    unsafe_allow_html=True,
)


# ============================================================
# JS 消息监听（时间轴点击等）
# ============================================================

# 注意：由于 Streamlit 限制，JS 到 Python 的双向通信有限制
# 主要交互通过 Streamlit 按钮和组件实现
# JS 键盘快捷键作为辅助增强（通过 postMessage 发送，需要额外组件支持
