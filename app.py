"""
足球视频战术标注工具 v2.0 - Streamlit 主界面
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
    EVENT_TYPE_KEY_MAP,
    TACTIC_ZONES,
    EVENT_COLORS,
    FRAME_DURATION,
    DEFAULT_HOME_COLOR,
    DEFAULT_AWAY_COLOR,
)


# ============================================================
# 页面配置
# ============================================================

st.set_page_config(
    page_title="足球战术标注工具 v2.0",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# 自定义 CSS
# ============================================================

CUSTOM_CSS = """
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
    padding: 16px 20px;
    margin-bottom: 14px;
    backdrop-filter: blur(10px);
}

.tac-card h3 {
    color: #36CFC9;
    font-size: 15px;
    font-weight: 600;
    margin-bottom: 14px;
    letter-spacing: 1px;
    border-bottom: 1px solid rgba(54, 207, 201, 0.2);
    padding-bottom: 6px;
    margin-top: 0;
}

/* 视频容器 - 放大占满宽度 */
.video-wrapper {
    border-radius: 8px;
    overflow: hidden;
    border: 1px solid rgba(54, 207, 201, 0.2);
    margin-bottom: 12px;
    min-height: 480px;
    background: #000;
    display: flex;
    align-items: center;
    justify-content: center;
}
.video-wrapper video {
    width: 100%;
    max-height: 600px;
}

/* 播放控制栏 */
.playback-controls {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
    margin-bottom: 10px;
}
.pb-btn {
    background: rgba(54, 207, 201, 0.1);
    border: 1px solid rgba(54, 207, 201, 0.3);
    color: #5cdbd3;
    padding: 4px 10px;
    border-radius: 5px;
    font-size: 12px;
    cursor: pointer;
    transition: all 0.2s;
}
.pb-btn:hover {
    background: rgba(54, 207, 201, 0.2);
    border-color: rgba(54, 207, 201, 0.5);
}
.pb-btn.active {
    background: #08979c;
    color: white;
    border-color: #36CFC9;
}
.pb-speed-label {
    color: #9ca3af;
    font-size: 11px;
    margin-right: 4px;
}

/* 标注时间轴 */
.annotation-timeline {
    position: relative;
    height: 24px;
    background: rgba(255,255,255,0.03);
    border-radius: 4px;
    margin: 8px 0;
    border: 1px solid rgba(255,255,255,0.06);
    cursor: pointer;
}
.timeline-dot {
    position: absolute;
    top: 50%;
    transform: translate(-50%, -50%);
    width: 10px;
    height: 10px;
    border-radius: 50%;
    cursor: pointer;
    transition: transform 0.15s;
    border: 2px solid rgba(0,0,0,0.3);
    z-index: 2;
}
.timeline-dot:hover {
    transform: translate(-50%, -50%) scale(1.4);
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
}
.timeline-label {
    font-size: 11px;
    color: #6b7280;
    margin-bottom: 2px;
    display: flex;
    justify-content: space-between;
}

/* 标注条目卡片 */
.ann-item {
    background: rgba(22, 27, 34, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-left: 4px solid #36CFC9;
    border-radius: 8px;
    padding: 10px 12px;
    margin-bottom: 8px;
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
    font-size: 13px;
    font-weight: 700;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 6px;
}

/* 事件类型标签 */
.event-tag {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 10px;
    color: #0d1117;
    margin-right: 4px;
}

/* 队伍标签 */
.team-tag {
    display: inline-block;
    font-size: 10px;
    padding: 1px 7px;
    border-radius: 4px;
    margin-right: 4px;
    font-weight: 500;
}

/* 场区标签 */
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

/* 描述文字 */
.ann-desc {
    color: #d1d5db;
    font-size: 12px;
    margin-top: 5px;
    line-height: 1.5;
}

/* 球员标签 */
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

/* 位置图标 */
.pos-icon {
    display: inline-block;
    width: 14px;
    height: 14px;
    border-radius: 50%;
    margin-right: 4px;
    vertical-align: middle;
    border: 2px solid rgba(255,255,255,0.3);
}

/* 备注文字 */
.ann-notes {
    color: #9ca3af;
    font-size: 11px;
    margin-top: 3px;
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
    gap: 6px;
    margin-bottom: 10px;
}
.stat-box {
    background: rgba(22, 27, 34, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 8px;
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

/* 标题栏 */
.app-title {
    text-align: center;
    padding: 14px 0 18px;
}
.app-title h1 {
    color: #f0f5ff;
    font-size: 24px;
    font-weight: 700;
    margin: 0;
    letter-spacing: 2px;
}
.app-title .subtitle {
    color: #36CFC9;
    font-size: 11px;
    margin-top: 3px;
    letter-spacing: 3px;
    opacity: 0.8;
}

/* 分隔线 */
.divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(54, 207, 201, 0.3), transparent);
    margin: 12px 0;
}

/* 空状态 */
.empty-state {
    text-align: center;
    padding: 24px 16px;
    color: #6b7280;
    font-size: 12px;
}

/* 迷你球场容器 */
.pitch-container {
    background: rgba(22, 27, 34, 0.8);
    border-radius: 6px;
    padding: 8px;
    margin: 8px 0;
    border: 1px solid rgba(54, 207, 201, 0.15);
}
.pitch-svg {
    width: 100%;
    cursor: crosshair;
}
.pitch-info {
    text-align: center;
    font-size: 11px;
    color: #9ca3af;
    margin-top: 4px;
    font-family: monospace;
}

/* 战术模板卡片 */
.template-card {
    background: rgba(22, 27, 34, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 6px;
    padding: 8px 10px;
    margin-bottom: 6px;
    cursor: pointer;
    transition: all 0.2s;
}
.template-card:hover {
    border-color: rgba(54, 207, 201, 0.4);
    background: rgba(30, 41, 59, 0.8);
}
.template-name {
    font-size: 12px;
    font-weight: 600;
    color: #e6edf3;
    margin-bottom: 2px;
}
.template-meta {
    font-size: 10px;
    color: #8b949e;
}

/* 快捷键面板 */
.shortcut-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 3px 0;
    font-size: 11px;
    border-bottom: 1px dashed rgba(255,255,255,0.05);
}
.shortcut-key {
    background: rgba(54, 207, 201, 0.15);
    color: #5cdbd3;
    padding: 1px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 10px;
    font-weight: 600;
}
.shortcut-desc {
    color: #9ca3af;
}

/* 视频段切换标签 */
.video-tab {
    display: inline-block;
    padding: 4px 12px;
    margin-right: 4px;
    border-radius: 6px 6px 0 0;
    cursor: pointer;
    font-size: 12px;
    border: 1px solid rgba(255,255,255,0.1);
    border-bottom: none;
    color: #8b949e;
    transition: all 0.2s;
}
.video-tab.active {
    background: rgba(54, 207, 201, 0.1);
    color: #36CFC9;
    border-color: rgba(54, 207, 201, 0.3);
}
.video-tab:hover {
    color: #e6edf3;
}

/* 球队颜色预览 */
.color-preview {
    display: inline-block;
    width: 16px;
    height: 16px;
    border-radius: 4px;
    vertical-align: middle;
    margin-right: 6px;
    border: 1px solid rgba(255,255,255,0.2);
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

/* 小型次要按钮 */
.mini-btn {
    font-size: 11px !important;
    padding: 2px 8px !important;
}

/* 球员列表项 */
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

/* 折叠面板标题 */
.collapsible-title {
    cursor: pointer;
    user-select: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.collapsible-title:hover {
    color: #5cdbd3;
}

/* 导出按钮组 */
.export-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 6px;
    margin-bottom: 8px;
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
    if "show_shortcuts" not in st.session_state:
        st.session_state.show_shortcuts = True
    if "show_team_settings" not in st.session_state:
        st.session_state.show_team_settings = False
    if "show_templates" not in st.session_state:
        st.session_state.show_templates = True
    if "pitch_x" not in st.session_state:
        st.session_state.pitch_x = -1.0
    if "pitch_y" not in st.session_state:
        st.session_state.pitch_y = -1.0
    if "pending_template_id" not in st.session_state:
        st.session_state.pending_template_id = None
    if "goto_timestamp" not in st.session_state:
        st.session_state.goto_timestamp = None


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


def render_timeline_svg(video_index: int) -> str:
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
            f'onclick="window.parent.postMessage({{type: \'goto_timestamp\', ts: {ann.timestamp}}}, \'*\');">'
            f'</div>'
        )

    cursor_pct = (current_time / duration) * 100

    return f"""
    <div class="timeline-label">
        <span>📌 标注时间轴</span>
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


def render_pitch_svg(clickable: bool = True, mark_x: float = -1, mark_y: float = -1) -> str:
    """渲染迷你足球场 SVG"""
    # 球场坐标系统：宽 100%，高按比例
    # x: 0-100 表示左右方向，y: 0-100 表示上下方向
    svg_content = '''
    <svg class="pitch-svg" viewBox="0 0 200 130" xmlns="http://www.w3.org/2000/svg"
         onclick="handlePitchClick(event)">
        <!-- 场地背景 -->
        <rect x="1" y="1" width="198" height="128" fill="#1a3d1f" stroke="#2d5a33" stroke-width="1" rx="2"/>
        
        <!-- 中线 -->
        <line x1="100" y1="1" x2="100" y2="129" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        
        <!-- 中圈 -->
        <circle cx="100" cy="65" r="18" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        <circle cx="100" cy="65" r="2" fill="rgba(255,255,255,0.6)"/>
        
        <!-- 左半场禁区 -->
        <rect x="1" y="35" width="32" height="60" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        <!-- 左半场小禁区 -->
        <rect x="1" y="50" width="14" height="30" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
        <!-- 左球门 -->
        <rect x="-2" y="57" width="4" height="16" fill="rgba(255,255,255,0.5)"/>
        
        <!-- 右半场禁区 -->
        <rect x="167" y="35" width="32" height="60" fill="none" stroke="rgba(255,255,255,0.4)" stroke-width="1"/>
        <!-- 右半场小禁区 -->
        <rect x="185" y="50" width="14" height="30" fill="none" stroke="rgba(255,255,255,0.3)" stroke-width="1"/>
        <!-- 右球门 -->
        <rect x="198" y="57" width="4" height="16" fill="rgba(255,255,255,0.5)"/>
        
        <!-- 左右半场标识 -->
        <text x="35" y="12" fill="rgba(255,255,255,0.3)" font-size="9" text-anchor="middle">主队半场</text>
        <text x="165" y="12" fill="rgba(255,255,255,0.3)" font-size="9" text-anchor="middle">客队半场</text>
    '''

    # 如果有标记点，绘制标记
    if mark_x >= 0 and mark_y >= 0:
        # 转换为 SVG 坐标
        svg_x = mark_x * 2  # 0-100 -> 0-200
        svg_y = mark_y * 1.3  # 0-100 -> 0-130
        svg_content += f'''
        <circle cx="{svg_x}" cy="{svg_y}" r="6" fill="rgba(255, 77, 79, 0.8)" stroke="white" stroke-width="2">
            <animate attributeName="r" values="6;8;6" dur="1.5s" repeatCount="indefinite"/>
        </circle>
        <circle cx="{svg_x}" cy="{svg_y}" r="2" fill="white"/>
        '''

    svg_content += '</svg>'

    # 添加点击事件处理脚本
    if clickable:
        script = '''
        <script>
        function handlePitchClick(event) {
            const svg = event.currentTarget;
            const pt = svg.createSVGPoint();
            pt.x = event.clientX;
            pt.y = event.clientY;
            const svgP = pt.matrixTransform(svg.getScreenCTM().inverse());
            const x = Math.max(0, Math.min(100, (svgP.x / 200) * 100));
            const y = Math.max(0, Math.min(100, (svgP.y / 130) * 100));
            window.parent.postMessage({
                type: 'pitch_click',
                x: Math.round(x * 10) / 10,
                y: Math.round(y * 10) / 10
            }, '*');
        }
        </script>
        '''
        svg_content += script

    return svg_content


def render_shortcuts_panel() -> str:
    """渲染快捷键说明面板"""
    shortcuts = [
        ("空格", "播放/暂停"),
        ("← / →", "快退/快进 5秒"),
        ("↑ / ↓", "上一帧/下一帧"),
        ("1-8", "选择事件类型"),
        ("N", "新建标注"),
        ("S", "保存标注"),
    ]

    items_html = ""
    for key, desc in shortcuts:
        items_html += f'''
        <div class="shortcut-item">
            <span class="shortcut-key">{key}</span>
            <span class="shortcut-desc">{desc}</span>
        </div>
        '''

    return f'<div style="margin-top: 6px;">{items_html}</div>'


# ============================================================
# 键盘快捷键 JavaScript
# ============================================================

KEYBOARD_JS = """
<script>
// 键盘快捷键监听
document.addEventListener('keydown', function(e) {
    // 如果用户正在输入框中，不触发快捷键
    const activeTag = document.activeElement.tagName.toLowerCase();
    if (['input', 'textarea', 'select'].includes(activeTag)) {
        return;
    }

    const key = e.key;
    let action = null;
    let payload = {};

    switch(key) {
        case ' ':
            e.preventDefault();
            action = 'toggle_play';
            break;
        case 'ArrowLeft':
            e.preventDefault();
            action = 'seek_backward';
            payload = { seconds: 5 };
            break;
        case 'ArrowRight':
            e.preventDefault();
            action = 'seek_forward';
            payload = { seconds: 5 };
            break;
        case 'ArrowUp':
            e.preventDefault();
            action = 'prev_frame';
            break;
        case 'ArrowDown':
            e.preventDefault();
            action = 'next_frame';
            break;
        case 'n':
        case 'N':
            e.preventDefault();
            action = 'new_annotation';
            break;
        case 's':
        case 'S':
            // 不阻止默认，留给表单提交
            action = 'save_annotation';
            break;
        case '1':
        case '2':
        case '3':
        case '4':
        case '5':
        case '6':
        case '7':
        case '8':
            e.preventDefault();
            action = 'select_event_type';
            payload = { key: key };
            break;
    }

    if (action) {
        window.parent.postMessage({
            type: 'keyboard_shortcut',
            action: action,
            payload: payload
        }, '*');
    }
});

// 监听来自 iframe 的消息
window.addEventListener('message', function(e) {
    const data = e.data;
    if (!data || !data.type) return;

    // 处理球场点击
    if (data.type === 'pitch_click') {
        // 通过 Streamlit 组件回传
        const pitchInputX = document.querySelector('input[data-testid="stPitchX"]');
        const pitchInputY = document.querySelector('input[data-testid="stPitchY"]');
        if (pitchInputX) pitchInputX.value = data.x;
        if (pitchInputY) pitchInputY.value = data.y;
        // 触发变化事件 - 由于 Streamlit 限制，用其他方式传递
        window.streamlitPitchX = data.x;
        window.streamlitPitchY = data.y;
    }

    // 处理时间轴跳转
    if (data.type === 'goto_timestamp') {
        window.streamlitGotoTs = data.ts;
    }
});
</script>
"""

st.markdown(KEYBOARD_JS, unsafe_allow_html=True)


# ============================================================
# 侧边栏：球队设置 + 战术模板
# ============================================================

with st.sidebar:
    st.markdown("### ⚙️ 设置面板")

    # --- 球队设置 ---
    team_col_title, team_col_toggle = st.columns([3, 1])
    with team_col_title:
        st.markdown("**👥 球队设置**")
    with team_col_toggle:
        if st.button("展开" if not st.session_state.show_team_settings else "收起",
                     key="toggle_team", use_container_width=True):
            st.session_state.show_team_settings = not st.session_state.show_team_settings
            st.rerun()

    if st.session_state.show_team_settings:
        # 主队设置
        st.markdown("#### 🔵 主队")
        home_name = st.text_input("主队名称", value=annotator.home_roster.team_name, key="home_name_input")
        if home_name != annotator.home_roster.team_name:
            annotator.set_team_name("home", home_name)

        home_color = st.color_picker("主队颜色", value=annotator.home_color, key="home_color_picker")
        if home_color != annotator.home_color:
            annotator.home_color = home_color

        # 主队球员列表
        st.markdown("**球员名单**")
        with st.expander(f"查看/编辑（{len(annotator.home_roster.players)}人）", expanded=False):
            # 添加球员
            h_num_col, h_name_col, h_add_col = st.columns([1, 2, 1])
            with h_num_col:
                h_number = st.text_input("号码", key="home_add_num", label_visibility="collapsed", placeholder="号")
            with h_name_col:
                h_name_p = st.text_input("姓名", key="home_add_name", label_visibility="collapsed", placeholder="姓名")
            with h_add_col:
                if st.button("➕", key="home_add_btn", use_container_width=True):
                    if h_number or h_name_p:
                        annotator.add_player("home", h_number, h_name_p)
                        st.rerun()

            # 现有球员
            for idx, player in enumerate(annotator.home_roster.players):
                pcol1, pcol2, pcol3 = st.columns([1, 3, 1])
                with pcol1:
                    st.markdown(f'<div class="number">{player.number or "-"}</div>', unsafe_allow_html=True)
                with pcol2:
                    st.markdown(f'<div class="name">{player.name or "未命名"}</div>', unsafe_allow_html=True)
                with pcol3:
                    if st.button("🗑", key=f"home_del_{idx}", use_container_width=True):
                        annotator.remove_player("home", idx)
                        st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 客队设置
        st.markdown("#### 🔴 客队")
        away_name = st.text_input("客队名称", value=annotator.away_roster.team_name, key="away_name_input")
        if away_name != annotator.away_roster.team_name:
            annotator.set_team_name("away", away_name)

        away_color = st.color_picker("客队颜色", value=annotator.away_color, key="away_color_picker")
        if away_color != annotator.away_color:
            annotator.away_color = away_color

        # 客队球员列表
        st.markdown("**球员名单**")
        with st.expander(f"查看/编辑（{len(annotator.away_roster.players)}人）", expanded=False):
            a_num_col, a_name_col, a_add_col = st.columns([1, 2, 1])
            with a_num_col:
                a_number = st.text_input("号码", key="away_add_num", label_visibility="collapsed", placeholder="号")
            with a_name_col:
                a_name_p = st.text_input("姓名", key="away_add_name", label_visibility="collapsed", placeholder="姓名")
            with a_add_col:
                if st.button("➕", key="away_add_btn", use_container_width=True):
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
                    if st.button("🗑", key=f"away_del_{idx}", use_container_width=True):
                        annotator.remove_player("away", idx)
                        st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 名单导入导出
        roster_col1, roster_col2 = st.columns(2)
        with roster_col1:
            roster_json = annotator.export_roster_json_string()
            st.download_button(
                "📤 导出名单",
                data=roster_json,
                file_name="team_rosters.json",
                mime="application/json",
                use_container_width=True,
                key="export_roster_btn",
            )
        with roster_col2:
            roster_file = st.file_uploader(
                "📥 导入名单",
                type=["json"],
                label_visibility="collapsed",
                key="import_roster_uploader",
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

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

    # --- 战术模板 ---
    tpl_col_title, tpl_col_toggle = st.columns([3, 1])
    with tpl_col_title:
        st.markdown("**📋 战术模板**")
    with tpl_col_toggle:
        if st.button("展开" if not st.session_state.show_templates else "收起",
                     key="toggle_tpl", use_container_width=True):
            st.session_state.show_templates = not st.session_state.show_templates
            st.rerun()

    if st.session_state.show_templates:
        for tpl in annotator.templates:
            team_color = get_team_color(tpl.team_side) if tpl.team_side else "#8C8C8C"
            team_label = {"home": annotator.home_roster.team_name, "away": annotator.away_roster.team_name, "": "通用"}.get(tpl.team_side, "")
            tpl_html = f'''
            <div class="template-card" onclick="window.parent.postMessage({{type: \'apply_template\', id: \'{tpl.template_id}\'}}, \'*\');">
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
            st.markdown(tpl_html, unsafe_allow_html=True)

        # 自定义模板
        st.markdown("##### ✨ 自定义模板")
        with st.expander("新建模板", expanded=False):
            new_tpl_name = st.text_input("模板名称", key="new_tpl_name")
            new_tpl_event = st.selectbox("事件类型", EVENT_TYPES, key="new_tpl_event")
            new_tpl_side = st.selectbox(
                "队伍",
                ["通用", "主队", "客队"],
                key="new_tpl_side",
            )
            new_tpl_zone = st.selectbox("场区", [""] + TACTIC_ZONES, key="new_tpl_zone")
            new_tpl_desc = st.text_area("描述", height=60, key="new_tpl_desc")
            if st.button("创建模板", use_container_width=True, key="create_tpl_btn"):
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

        # 删除自定义模板
        custom_tpls = [t for t in annotator.templates if t.is_custom]
        if custom_tpls:
            with st.expander("管理自定义模板", expanded=False):
                for tpl in custom_tpls:
                    tpl_del_col1, tpl_del_col2 = st.columns([3, 1])
                    with tpl_del_col1:
                        st.markdown(f"• {tpl.name}")
                    with tpl_del_col2:
                        if st.button("删除", key=f"del_tpl_{tpl.template_id}", use_container_width=True):
                            annotator.delete_template(tpl.template_id)
                            st.rerun()


# ============================================================
# 标题
# ============================================================

st.markdown(
    """
    <div class="app-title">
        <h1>⚽ 足球战术视频标注工具</h1>
        <div class="subtitle">TACTICAL VIDEO ANNOTATOR · v2.0 PRO EDITION</div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 三栏布局
# ============================================================

col_left, col_mid, col_right = st.columns([4.5, 3.5, 4])


# ============================================================
# 左栏：视频播放器 + 控制 + 时间轴
# ============================================================

with col_left:
    st.markdown('<div class="tac-card"><h3>🎥 视频面板</h3>', unsafe_allow_html=True)

    # 多段视频标签切换
    if annotator.video_segments:
        tabs_html = '<div style="margin-bottom: 10px;">'
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

    # 视频上传
    uploaded_files = st.file_uploader(
        "上传比赛视频（支持多段）",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        accept_multiple_files=True,
        help="支持 MP4/MOV/AVI/MKV/WEBM 格式，可上传多个视频（上下半场等）",
    )

    if uploaded_files:
        # 处理上传的视频
        current_count = len(annotator.video_segments)
        for i, uf in enumerate(uploaded_files):
            vid_bytes = uf.getvalue()
            # 检查是否已存在
            exists = False
            for seg in annotator.video_segments:
                if seg.name == uf.name:
                    exists = True
                    break
            if not exists:
                label_options = ["上半场", "下半场", "加时赛上", "加时赛下", "点球大战"]
                label = label_options[i + current_count] if (i + current_count) < len(label_options) else f"第{i + current_count + 1}段"
                annotator.add_video_segment(uf.name, vid_bytes, label)

    # 视频播放器
    current_video = annotator.current_video
    if current_video and current_video.video_bytes:
        # 视频播放框 - 占满宽度，至少 480px 高
        st.markdown('<div class="video-wrapper">', unsafe_allow_html=True)

        # 使用 HTML5 video 以支持倍速和 frame 控制
        video_html = f'''
        <video id="mainVideo" controls style="width:100%; min-height: 480px; max-height: 600px; background: #000;"
               playbackRate="{st.session_state.playback_rate}"
               ontimeupdate="updateVideoTime(this.currentTime)"
               onloadedmetadata="videoLoaded(this.duration)">
            <source src="data:video/mp4;base64,{__import__('base64').b64encode(current_video.video_bytes).decode()}" type="video/mp4">
        </video>
        <script>
        function updateVideoTime(t) {{
            window.streamlitVideoTime = t;
        }}
        function videoLoaded(dur) {{
            window.streamlitVideoDuration = dur;
        }}
        // 设置初始倍速
        setTimeout(function() {{
            const v = document.getElementById('mainVideo');
            if (v) v.playbackRate = {st.session_state.playback_rate};
        }}, 500);
        </script>
        '''
        # 简化：使用 st.video 配合 JS 控制
        st.video(current_video.video_bytes)

        st.markdown('</div>', unsafe_allow_html=True)

        # 标注时间轴
        timeline_html = render_timeline_svg(annotator.current_video_index)
        st.markdown(timeline_html, unsafe_allow_html=True)

        # 播放控制栏 - 倍速
        st.markdown("**⏯ 播放控制**")

        # 倍速按钮
        speed_rates = [0.25, 0.5, 0.75, 1.0, 1.5, 2.0]
        speed_cols = st.columns(len(speed_rates))
        for i, rate in enumerate(speed_rates):
            with speed_cols[i]:
                is_active = st.session_state.playback_rate == rate
                btn_label = f"{rate}x"
                if st.button(btn_label, key=f"speed_{rate}", use_container_width=True,
                             type="primary" if is_active else "secondary"):
                    st.session_state.playback_rate = rate
                    st.rerun()

        # 逐帧控制 + 跳转
        st.markdown("")
        frame_cols = st.columns([1, 1, 1.5, 1, 1])
        with frame_cols[0]:
            if st.button("⏮ -5s", use_container_width=True, key="back5"):
                st.session_state.current_timestamp = max(0, st.session_state.current_timestamp - 5)
                st.rerun()
        with frame_cols[1]:
            if st.button("◀ -1s", use_container_width=True, key="back1"):
                st.session_state.current_timestamp = max(0, st.session_state.current_timestamp - 1)
                st.rerun()
        with frame_cols[2]:
            current_min = int(st.session_state.current_timestamp // 60)
            current_sec = int(st.session_state.current_timestamp % 60)
            st.markdown(
                f'<div style="text-align:center; font-family:monospace; font-size:18px; '
                f'font-weight:bold; color:#36CFC9; padding:4px 0;">'
                f'{current_min:02d}:{current_sec:02d}'
                f'</div>',
                unsafe_allow_html=True,
            )
        with frame_cols[3]:
            if st.button("▶ +1s", use_container_width=True, key="fwd1"):
                st.session_state.current_timestamp += 1
                st.rerun()
        with frame_cols[4]:
            if st.button("⏭ +5s", use_container_width=True, key="fwd5"):
                st.session_state.current_timestamp += 5
                st.rerun()

        # 逐帧控制
        frame2_cols = st.columns([1, 1, 1, 1])
        with frame2_cols[0]:
            if st.button("⏮ 上一帧", use_container_width=True, key="prev_frame"):
                st.session_state.current_timestamp = max(0, st.session_state.current_timestamp - FRAME_DURATION)
                st.rerun()
        with frame2_cols[1]:
            if st.button("⏭ 下一帧", use_container_width=True, key="next_frame"):
                st.session_state.current_timestamp += FRAME_DURATION
                st.rerun()
        with frame2_cols[2]:
            if st.button("📌 设为标注点", use_container_width=True, key="set_time_point"):
                st.success(f"已设定时间点：{format_time(st.session_state.current_timestamp)}")
        with frame2_cols[3]:
            if st.button("🆕 新建标注", use_container_width=True, key="quick_new_ann"):
                st.session_state.editing_id = None
                st.session_state.form_key += 1
                st.session_state.pitch_x = -1.0
                st.session_state.pitch_y = -1.0
                st.rerun()

        # 手动设置时间
        with st.expander("手动设置时间", expanded=False):
            time_col1, time_col2, time_col3 = st.columns(3)
            with time_col1:
                set_min = st.number_input("分钟", min_value=0, value=int(st.session_state.current_timestamp // 60), step=1, key="set_min")
            with time_col2:
                set_sec = st.number_input("秒", min_value=0, max_value=59, value=int(st.session_state.current_timestamp % 60), step=1, key="set_sec")
            with time_col3:
                set_ms = st.number_input("毫秒(10ms)", min_value=0, max_value=99,
                                        value=int((st.session_state.current_timestamp % 1) * 100), step=1, key="set_ms")
            if st.button("应用时间", use_container_width=True, key="apply_time"):
                st.session_state.current_timestamp = set_min * 60 + set_sec + set_ms / 100
                st.rerun()

        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 快捷键说明
        sc_col1, sc_col2 = st.columns([3, 1])
        with sc_col1:
            st.markdown("**⌨️ 快捷键**")
        with sc_col2:
            if st.button("展开" if not st.session_state.show_shortcuts else "收起",
                         key="toggle_sc", use_container_width=True):
                st.session_state.show_shortcuts = not st.session_state.show_shortcuts
                st.rerun()

        if st.session_state.show_shortcuts:
            shortcuts_html = render_shortcuts_panel()
            st.markdown(shortcuts_html, unsafe_allow_html=True)

        # 多段视频管理
        if len(annotator.video_segments) > 1:
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            with st.expander("📹 视频段管理", expanded=False):
                for i, seg in enumerate(annotator.video_segments):
                    vcol1, vcol2, vcol3 = st.columns([2, 3, 1])
                    with vcol1:
                        new_label = st.text_input("标签", value=seg.label, key=f"seg_label_{i}", label_visibility="collapsed")
                        if new_label != seg.label:
                            seg.label = new_label
                    with vcol2:
                        st.markdown(f"<small>{seg.name}</small>", unsafe_allow_html=True)
                    with vcol3:
                        if st.button("删除", key=f"del_seg_{i}", use_container_width=True):
                            annotator.remove_video_segment(i)
                            st.rerun()

    else:
        st.markdown(
            '<div class="empty-state">请上传视频文件开始标注<br><br>支持 MP4 / MOV / AVI / MKV<br>可上传多段视频（上下半场等）</div>',
            unsafe_allow_html=True,
        )

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 中栏：标注表单
# ============================================================

with col_mid:
    st.markdown('<div class="tac-card"><h3>📝 标注表单</h3>', unsafe_allow_html=True)

    # 编辑模式
    editing_ann = None
    if st.session_state.editing_id:
        editing_ann = annotator.get_annotation(st.session_state.editing_id)
        if editing_ann:
            st.session_state.pitch_x = editing_ann.x
            st.session_state.pitch_y = editing_ann.y

    form_key = f"ann_form_{st.session_state.form_key}"

    # 迷你球场 - 坐标标注（放在form外面以支持滑块实时更新SVG）
    st.markdown("**🏟 战术位置（拖动滑块标注）**")
    pitch_x = st.session_state.get("pitch_x", -1.0)
    pitch_y = st.session_state.get("pitch_y", -1.0)

    # 显示球场 SVG
    pitch_html = f'''
    <div class="pitch-container">
        {render_pitch_svg(clickable=False, mark_x=pitch_x, mark_y=pitch_y)}
        <div class="pitch-info">
            {"X: " + f"{pitch_x:.1f}" + "   Y: " + f"{pitch_y:.1f}" if pitch_x >= 0 else "未设置位置"}
        </div>
    </div>
    '''
    st.markdown(pitch_html, unsafe_allow_html=True)

    # 坐标滑块
    if pitch_x < 0:
        if st.button("📍 设置坐标位置", key="enable_position", use_container_width=True):
            st.session_state.pitch_x = 50.0
            st.session_state.pitch_y = 50.0
            st.rerun()
    else:
        new_x = st.slider("横向位置 X（左→右）", 0.0, 100.0, pitch_x, 0.5,
                         key="pitch_x_slider")
        new_y = st.slider("纵向位置 Y（上→下）", 0.0, 100.0, pitch_y, 0.5,
                         key="pitch_y_slider")
        if new_x != pitch_x or new_y != pitch_y:
            st.session_state.pitch_x = new_x
            st.session_state.pitch_y = new_y

        # 快捷位置按钮
        st.caption("⚡ 快捷位置：")
        qcol1, qcol2, qcol3, qcol4 = st.columns(4)
        with qcol1:
            if st.button("本方禁区", key="qp1", use_container_width=True):
                st.session_state.pitch_x = 10.0
                st.session_state.pitch_y = 50.0
                st.rerun()
        with qcol2:
            if st.button("中场", key="qp2", use_container_width=True):
                st.session_state.pitch_x = 50.0
                st.session_state.pitch_y = 50.0
                st.rerun()
        with qcol3:
            if st.button("对方禁区", key="qp3", use_container_width=True):
                st.session_state.pitch_x = 90.0
                st.session_state.pitch_y = 50.0
                st.rerun()
        with qcol4:
            if st.button("清除", key="qp4", use_container_width=True):
                st.session_state.pitch_x = -1.0
                st.session_state.pitch_y = -1.0
                st.rerun()

    st.markdown('<div style="height: 8px;"></div>', unsafe_allow_html=True)

    with st.form(key=form_key, clear_on_submit=False):
        # 时间戳 + 视频段
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
            help="1-8数字键可快速选择",
            key="form_event_type",
        )

        # 队伍侧别 + 队伍名
        team_col1, team_col2 = st.columns([1, 2])
        with team_col1:
            team_side_options = ["", "主队", "客队"]
            current_side_label = {"home": "主队", "away": "客队", "": ""}.get(
                editing_ann.team_side if editing_ann else "", ""
            )
            team_side_label = st.selectbox(
                "队伍侧别",
                team_side_options,
                index=team_side_options.index(current_side_label) if current_side_label in team_side_options else 0,
                key="form_team_side",
            )
            team_side = {"主队": "home", "客队": "away", "": ""}.get(team_side_label, "")

        with team_col2:
            default_team = editing_ann.team if editing_ann else ""
            if team_side and not default_team:
                default_team = annotator.home_roster.team_name if team_side == "home" else annotator.away_roster.team_name
            team = st.text_input(
                "队伍名称",
                value=default_team,
                key="form_team",
            )

        # 球员 - 下拉多选（基于名单）
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
            # 编辑模式下选中已有球员
            default_players = []
            if editing_ann and editing_ann.players:
                for p in editing_ann.players:
                    if p in all_players:
                        default_players.append(p)
                    else:
                        # 尝试匹配
                        for ap in all_players:
                            if p in ap:
                                default_players.append(ap)
                                break

            selected_players = st.multiselect(
                "从名单选择",
                all_players,
                default=default_players,
                key="form_players_select",
                label_visibility="collapsed",
            )
            players_input_text = st.text_input(
                "手动补充（逗号分隔）",
                value="",
                placeholder="其他球员，用逗号分隔",
                key="form_players_manual",
            )
            players_list = selected_players + [p.strip() for p in players_input_text.split(",") if p.strip()]
        else:
            players_input_text = st.text_input(
                "涉及球员（逗号分隔）",
                value=",".join(editing_ann.players) if editing_ann else "",
                placeholder="在左侧设置中添加球员名单，即可下拉选择",
                key="form_players",
            )
            players_list = [p.strip() for p in players_input_text.split(",") if p.strip()]

        # 场区
        tactic_zone = st.selectbox(
            "场区",
            [""] + TACTIC_ZONES,
            index=(TACTIC_ZONES.index(editing_ann.tactic_zone) + 1) if editing_ann and editing_ann.tactic_zone in TACTIC_ZONES else 0,
            key="form_zone",
        )

        # 描述
        description = st.text_area(
            "事件描述",
            value=editing_ann.description if editing_ann else "",
            placeholder="简要描述本次战术事件...",
            height=70,
            key="form_desc",
        )

        # 备注
        notes = st.text_area(
            "备注",
            value=editing_ann.notes if editing_ann else "",
            placeholder="其他补充说明...",
            height=50,
            key="form_notes",
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
                # 清空坐标
                st.session_state.pitch_x = -1.0
                st.session_state.pitch_y = -1.0
                st.rerun()

    # 取消编辑
    if st.session_state.editing_id:
        if st.button("↩️ 取消编辑", use_container_width=True, key="cancel_edit"):
            st.session_state.editing_id = None
            st.session_state.form_key += 1
            st.session_state.pitch_x = -1.0
            st.session_state.pitch_y = -1.0
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

    # 事件类型图例
    st.markdown('<div class="tac-card"><h3>🎨 事件类型图例</h3>', unsafe_allow_html=True)
    legend_html = '<div style="display: flex; flex-wrap: wrap; gap: 5px;">'
    for evt, color in EVENT_COLORS.items():
        legend_html += f'<span class="event-tag" style="background: {color};">{evt}</span>'
    legend_html += '</div>'
    st.markdown(legend_html, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 右栏：统计 + 导入导出 + 标注列表
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
                f'<div style="display: flex; align-items: center; margin-bottom: 3px;">'
                f'<span class="event-tag" style="background: {color}; min-width: 55px; text-align: center; font-size: 10px;">{evt}</span>'
                f'<div style="flex: 1; margin-left: 6px; background: rgba(255,255,255,0.05); border-radius: 4px; height: 7px;">'
                f'<div style="background: {color}; width: {pct}%; height: 100%; border-radius: 4px;"></div>'
                f'</div>'
                f'<span style="margin-left: 6px; color: #d1d5db; font-size: 11px; min-width: 25px; text-align: right;">{count}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )

    st.markdown('</div>', unsafe_allow_html=True)

    # 导入导出操作
    st.markdown('<div class="tac-card"><h3>💾 数据管理</h3>', unsafe_allow_html=True)

    # 导出格式选择
    st.markdown("**导出格式**")

    exp_col1, exp_col2 = st.columns(2)

    with exp_col1:
        # JSON 导出
        if st.button("📄 JSON", use_container_width=True, key="export_json_btn"):
            if annotator.annotations:
                st.session_state.show_json_download = True
            else:
                st.warning("暂无标注数据")

        # CSV 导出
        if st.button("📊 CSV", use_container_width=True, key="export_csv_btn"):
            if annotator.annotations:
                st.session_state.show_csv_download = True
            else:
                st.warning("暂无标注数据")

    with exp_col2:
        # SRT 导出
        if st.button("📝 SRT字幕", use_container_width=True, key="export_srt_btn"):
            if annotator.annotations:
                st.session_state.show_srt_download = True
            else:
                st.warning("暂无标注数据")

        # 报告导出
        if st.button("📋 战术报告", use_container_width=True, key="export_report_btn"):
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
            key="dl_json",
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
            key="dl_csv",
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
            key="dl_srt",
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
            key="dl_report",
        )

    st.markdown('<div style="height: 6px;"></div>', unsafe_allow_html=True)

    # 导入
    st.markdown("**导入数据**")
    import_file = st.file_uploader(
        "📥 导入 JSON 标注文件",
        type=["json"],
        label_visibility="collapsed",
        help="导入已有的标注数据",
        key="import_uploader",
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
                "事件筛选",
                ["全部事件"] + EVENT_TYPES,
                key="filter_event",
            )
        with filter_col2:
            filter_team_side = st.selectbox(
                "队伍筛选",
                ["全部队伍", "主队", "客队"],
                key="filter_team_side",
            )

        # 视频段筛选
        if len(annotator.video_segments) > 1:
            filter_video_opts = ["全部视频"] + [seg.label or f"第{i+1}段" for i, seg in enumerate(annotator.video_segments)]
            filter_video = st.selectbox(
                "视频段筛选",
                filter_video_opts,
                key="filter_video",
            )
        else:
            filter_video = "全部视频"

        # 过滤标注
        filtered = annotator.annotations
        if filter_event != "全部事件":
            filtered = [a for a in filtered if a.event_type == filter_event]
        if filter_team_side != "全部队伍":
            side = "home" if filter_team_side == "主队" else "away"
            filtered = [a for a in filtered if a.team_side == side]
        if filter_video != "全部视频":
            video_idx = filter_video_opts.index(filter_video) - 1 if filter_video_opts else 0
            filtered = [a for a in filtered if a.video_index == video_idx]

        st.markdown(f"共 **{len(filtered)}** 条标注")
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)

        # 逐条渲染标注
        for i, ann in enumerate(filtered):
            # 队伍颜色
            team_color = get_team_color(ann.team_side)
            team_color_light = get_team_color_light(ann.team_side)

            # 构建卡片
            item_html = f'<div class="ann-item" style="border-left-color: {team_color if ann.team_side else EVENT_COLORS.get(ann.event_type, "#8C8C8C")};">'

            # 视频段标识（多段时显示）
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

            # 位置图标
            if ann.has_coordinates:
                pos_color = team_color if ann.team_side else EVENT_COLORS.get(ann.event_type, "#8C8C8C")
                item_html += f'<span class="pos-icon" style="background: {pos_color}; margin-left: 4px;" title="位置: X={ann.x:.1f}, Y={ann.y:.1f}"></span>'

            # 球员
            if ann.players:
                item_html += '<div style="margin-top: 5px;">'
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
            btn_col1, btn_col2, btn_col3 = st.columns([1, 1, 1])
            with btn_col1:
                if st.button("👁 跳转", key=f"goto_{ann.annotation_id}", use_container_width=True):
                    annotator.switch_video(ann.video_index)
                    st.session_state.current_timestamp = ann.timestamp
                    st.rerun()
            with btn_col2:
                if st.button("✏️ 编辑", key=f"edit_{ann.annotation_id}", use_container_width=True):
                    st.session_state.editing_id = ann.annotation_id
                    st.session_state.current_timestamp = ann.timestamp
                    annotator.switch_video(ann.video_index)
                    st.session_state.form_key += 1
                    st.rerun()
            with btn_col3:
                if st.button("🗑 删除", key=f"del_{ann.annotation_id}", use_container_width=True):
                    st.session_state[f"confirm_del_{ann.annotation_id}"] = True

            # 删除确认
            if st.session_state.get(f"confirm_del_{ann.annotation_id}"):
                st.warning("确定删除这条标注？")
                del_col1, del_col2 = st.columns(2)
                with del_col1:
                    if st.button("✅ 确认", key=f"confirm_{ann.annotation_id}", use_container_width=True):
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
                st.markdown('<div style="height: 3px;"></div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# 页脚
# ============================================================

st.markdown(
    """
    <div style="text-align: center; padding: 16px 0; color: #4b5563; font-size: 11px;">
        ⚽ Tactical Video Annotator v2.0 · 专业足球战术分析工具 · 数据格式兼容 AI 战术验证脚本
    </div>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# 键盘快捷键处理（通过 query params 模拟）
# ============================================================

# 使用 st.query_params 来处理来自 JS 的消息
# 注意：Streamlit 限制使得 JS->Python 双向通信有限制
# 这里提供一个通过按钮触发的显式操作方式作为主要交互
# JS 键盘快捷键作为辅助增强
