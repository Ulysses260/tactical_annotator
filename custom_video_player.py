"""
足球视频战术标注工具 v2.1 - 自定义视频播放器模块
所有播放控制通过 JS 实现，使用 Streamlit.setComponentValue 双向通信
"""

import json


def render_custom_video_player_html(
    video_data_url: str,
    annotations_data: list,
    initial_time: float = 0.0,
    initial_rate: float = 1.0,
    seek_token: int = 0,
    duration: float = 0.0,
    mime_type: str = "video/mp4",
) -> str:
    """
    自定义 HTML5 视频播放器 - 所有播放控制都在组件内部通过 JS 实现
    使用 Streamlit.setComponentValue 将当前播放时间传回 Python 端
    """
    ann_data_json = json.dumps(annotations_data, ensure_ascii=False)

    html_parts = []
    html_parts.append('<!DOCTYPE html>')
    html_parts.append('<html lang="zh-CN">')
    html_parts.append('<head>')
    html_parts.append('<meta charset="UTF-8">')
    html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    html_parts.append('<style>')
    html_parts.append('* {box-sizing: border-box; margin: 0; padding: 0;}')
    html_parts.append('body { background: transparent; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; color: #e6edf3; padding: 0; margin: 0; }')
    
    # Video container
    html_parts.append('.video-container { width: 100%; background: #000; border-radius: 10px; overflow: hidden; border: 1px solid rgba(54, 207, 201, 0.2); margin-bottom: 10px; position: relative; }')
    html_parts.append('.video-container video { width: 100%; display: block; min-height: 480px; max-height: 560px; object-fit: contain; background: #000; }')
    
    # Timeline section
    html_parts.append('.timeline-section { background: rgba(22, 27, 34, 0.8); border: 1px solid rgba(54, 207, 201, 0.12); border-radius: 8px; padding: 10px 14px; margin-bottom: 10px; }')
    html_parts.append('.timeline-label { font-size: 12px; color: #9ca3af; margin-bottom: 6px; display: flex; justify-content: space-between; align-items: center; }')
    html_parts.append('.timeline-label .title { color: #e6edf3; font-weight: 500; }')
    html_parts.append('.annotation-timeline { position: relative; height: 32px; background: rgba(255,255,255,0.03); border-radius: 6px; border: 1px solid rgba(255,255,255,0.06); cursor: pointer; user-select: none; }')
    html_parts.append('.timeline-progress { position: absolute; top: 0; left: 0; bottom: 0; background: rgba(54, 207, 201, 0.15); border-radius: 6px 0 0 6px; pointer-events: none; }')
    html_parts.append('.timeline-cursor { position: absolute; top: -3px; bottom: -3px; width: 2px; background: #36CFC9; z-index: 5; pointer-events: none; box-shadow: 0 0 6px rgba(54, 207, 201, 0.5); }')
    html_parts.append('.timeline-dot { position: absolute; top: 50%; transform: translate(-50%, -50%); width: 12px; height: 12px; border-radius: 50%; cursor: pointer; transition: transform 0.15s; border: 2px solid rgba(0,0,0,0.4); z-index: 2; box-shadow: 0 1px 3px rgba(0,0,0,0.3); }')
    html_parts.append('.timeline-dot:hover { transform: translate(-50%, -50%) scale(1.6); z-index: 3; }')
    
    # Playback controls
    html_parts.append('.playback-controls { background: rgba(22, 27, 34, 0.8); border: 1px solid rgba(54, 207, 201, 0.12); border-radius: 8px; padding: 12px 14px; }')
    html_parts.append('.pb-section-title { font-size: 12px; color: #9ca3af; margin-bottom: 8px; font-weight: 500; }')
    html_parts.append('.control-row { display: flex; gap: 6px; align-items: center; margin-bottom: 8px; flex-wrap: wrap; }')
    html_parts.append('.ctrl-btn { background: rgba(54, 207, 201, 0.08); border: 1px solid rgba(54, 207, 201, 0.2); color: #5cdbd3; padding: 7px 12px; border-radius: 6px; font-size: 13px; cursor: pointer; transition: all 0.2s; white-space: nowrap; font-family: inherit; }')
    html_parts.append('.ctrl-btn:hover { background: rgba(54, 207, 201, 0.18); border-color: rgba(54, 207, 201, 0.4); }')
    html_parts.append('.ctrl-btn:active { transform: translateY(1px); }')
    html_parts.append('.ctrl-btn.primary { background: linear-gradient(135deg, #08979c 0%, #006d75 100%); color: white; border-color: transparent; font-weight: 500; }')
    html_parts.append('.ctrl-btn.primary:hover { background: linear-gradient(135deg, #36CFC9 0%, #08979c 100%); box-shadow: 0 2px 8px rgba(54, 207, 201, 0.3); }')
    html_parts.append('.ctrl-btn.speed-btn { padding: 5px 10px; font-size: 12px; }')
    html_parts.append('.ctrl-btn.speed-btn.active { background: rgba(54, 207, 201, 0.25); border-color: rgba(54, 207, 201, 0.5); color: #36CFC9; font-weight: 600; }')
    html_parts.append('.time-display { font-family: "Courier New", monospace; font-size: 22px; font-weight: 700; color: #36CFC9; text-align: center; padding: 0 12px; letter-spacing: 2px; min-width: 110px; flex-shrink: 0; }')
    html_parts.append('.spacer { flex: 1; }')
    html_parts.append('.control-label { font-size: 11px; color: #8b949e; min-width: 50px; }')
    html_parts.append('.jump-input { display: flex; gap: 4px; align-items: center; }')
    html_parts.append('.jump-input input { width: 45px; background: rgba(0,0,0,0.3); border: 1px solid rgba(255,255,255,0.1); color: #e6edf3; padding: 5px 6px; border-radius: 4px; font-size: 12px; text-align: center; font-family: monospace; }')
    html_parts.append('.jump-input input:focus { outline: none; border-color: rgba(54, 207, 201, 0.4); }')
    html_parts.append('.jump-input span { color: #6b7280; font-size: 12px; }')
    html_parts.append('.divider { height: 1px; background: linear-gradient(90deg, transparent, rgba(54, 207, 201, 0.15), transparent); margin: 10px 0; }')
    
    html_parts.append('</style>')
    html_parts.append('</head>')
    html_parts.append('<body>')
    
    # Video player
    html_parts.append('<div class="video-container">')
    html_parts.append('<video id="videoPlayer" preload="metadata" playsinline>')
    html_parts.append(f'<source src="{video_data_url}" type="{mime_type}">')
    html_parts.append('您的浏览器不支持视频播放')
    html_parts.append('</video>')
    html_parts.append('</div>')
    
    # Timeline
    html_parts.append('<div class="timeline-section">')
    html_parts.append('<div class="timeline-label">')
    html_parts.append('<span class="title">📌 标注时间轴</span>')
    html_parts.append('<span id="timeRangeText">00:00 / 00:00</span>')
    html_parts.append('</div>')
    html_parts.append('<div class="annotation-timeline" id="annTimeline">')
    html_parts.append('<div class="timeline-progress" id="timelineProgress"></div>')
    html_parts.append('<div class="timeline-cursor" id="timelineCursor"></div>')
    html_parts.append('</div>')
    html_parts.append('</div>')
    
    # Playback controls
    html_parts.append('<div class="playback-controls">')
    html_parts.append('<div class="pb-section-title">⏯ 播放控制</div>')
    
    # Main control row
    html_parts.append('<div class="control-row">')
    html_parts.append('<button class="ctrl-btn primary" id="playPauseBtn" onclick="togglePlay()">▶ 播放</button>')
    html_parts.append('<div class="time-display" id="timeDisplay">00:00</div>')
    html_parts.append('<div class="spacer"></div>')
    html_parts.append('<span class="control-label">速度：</span>')
    html_parts.append('<button class="ctrl-btn speed-btn" onclick="setSpeed(0.25)">0.25x</button>')
    html_parts.append('<button class="ctrl-btn speed-btn" onclick="setSpeed(0.5)">0.5x</button>')
    html_parts.append('<button class="ctrl-btn speed-btn" onclick="setSpeed(0.75)">0.75x</button>')
    html_parts.append('<button class="ctrl-btn speed-btn active" onclick="setSpeed(1.0)">1x</button>')
    html_parts.append('<button class="ctrl-btn speed-btn" onclick="setSpeed(1.5)">1.5x</button>')
    html_parts.append('<button class="ctrl-btn speed-btn" onclick="setSpeed(2.0)">2x</button>')
    html_parts.append('</div>')
    
    html_parts.append('<div class="divider"></div>')
    
    # Seek controls
    html_parts.append('<div class="control-row">')
    html_parts.append('<button class="ctrl-btn" onclick="seekBy(-5)">⏮ -5s</button>')
    html_parts.append('<button class="ctrl-btn" onclick="seekBy(-1)">◀ -1s</button>')
    html_parts.append('<button class="ctrl-btn" onclick="seekBy(1)">▶ +1s</button>')
    html_parts.append('<button class="ctrl-btn" onclick="seekBy(5)">⏭ +5s</button>')
    html_parts.append('</div>')
    
    # Frame step
    html_parts.append('<div class="control-row">')
    html_parts.append('<span class="control-label">逐帧：</span>')
    html_parts.append('<button class="ctrl-btn" onclick="frameStep(-1)">⏮ 上一帧</button>')
    html_parts.append('<button class="ctrl-btn" onclick="frameStep(1)">⏭ 下一帧</button>')
    html_parts.append('<div class="spacer"></div>')
    html_parts.append('<button class="ctrl-btn" onclick="sendTimeToStreamlit()">📍 标注点</button>')
    html_parts.append('</div>')
    
    html_parts.append('<div class="divider"></div>')
    
    # Jump to time
    html_parts.append('<div class="control-row">')
    html_parts.append('<span class="control-label">跳转至：</span>')
    html_parts.append('<div class="jump-input">')
    html_parts.append('<input type="number" id="jumpMin" min="0" value="0" placeholder="分">')
    html_parts.append('<span>:</span>')
    html_parts.append('<input type="number" id="jumpSec" min="0" max="59" value="0" placeholder="秒">')
    html_parts.append('</div>')
    html_parts.append('<button class="ctrl-btn" onclick="jumpToTime()">跳转</button>')
    html_parts.append('</div>')
    
    html_parts.append('</div>')  # End playback-controls
    
    # JavaScript
    html_parts.append('<script>')
    html_parts.append('const video = document.getElementById("videoPlayer");')
    html_parts.append('const playPauseBtn = document.getElementById("playPauseBtn");')
    html_parts.append('const timeDisplay = document.getElementById("timeDisplay");')
    html_parts.append('const timeRangeText = document.getElementById("timeRangeText");')
    html_parts.append('const timeline = document.getElementById("annTimeline");')
    html_parts.append('const timelineCursor = document.getElementById("timelineCursor");')
    html_parts.append('const timelineProgress = document.getElementById("timelineProgress");')
    html_parts.append('const speedBtns = document.querySelectorAll(".speed-btn");')
    html_parts.append(f'const annotationData = {ann_data_json};')
    html_parts.append(f'let duration = {duration};')
    html_parts.append('let lastSentTime = -1;')
    html_parts.append('let sendThrottleTimer = null;')
    
    # Format time
    html_parts.append('function formatTime(seconds) {')
    html_parts.append('  const m = Math.floor(seconds / 60);')
    html_parts.append('  const s = Math.floor(seconds % 60);')
    html_parts.append('  return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");')
    html_parts.append('}')
    
    # Update time display
    html_parts.append('function updateTimeDisplay() {')
    html_parts.append('  timeDisplay.textContent = formatTime(video.currentTime);')
    html_parts.append('  if (duration > 0) {')
    html_parts.append('    timeRangeText.textContent = formatTime(video.currentTime) + " / " + formatTime(duration);')
    html_parts.append('    const pct = (video.currentTime / duration) * 100;')
    html_parts.append('    timelineCursor.style.left = pct + "%";')
    html_parts.append('    timelineProgress.style.width = pct + "%";')
    html_parts.append('  }')
    html_parts.append('}')
    
    # Toggle play
    html_parts.append('function togglePlay() {')
    html_parts.append('  if (video.paused) { video.play(); } else { video.pause(); }')
    html_parts.append('}')
    
    # Event listeners
    html_parts.append('video.addEventListener("play", function() {')
    html_parts.append('  playPauseBtn.textContent = "⏸ 暂停";')
    html_parts.append('  sendStateToStreamlit("play");')
    html_parts.append('});')
    
    html_parts.append('video.addEventListener("pause", function() {')
    html_parts.append('  playPauseBtn.textContent = "▶ 播放";')
    html_parts.append('  sendStateToStreamlit("pause");')
    html_parts.append('});')
    
    html_parts.append('video.addEventListener("timeupdate", function() {')
    html_parts.append('  updateTimeDisplay();')
    html_parts.append('  if (Math.abs(video.currentTime - lastSentTime) >= 0.25) {')
    html_parts.append('    throttledSendTime();')
    html_parts.append('  }')
    html_parts.append('});')
    
    html_parts.append('video.addEventListener("loadedmetadata", function() {')
    html_parts.append('  duration = video.duration;')
    html_parts.append('  updateTimeDisplay();')
    html_parts.append('  renderAnnotationDots();')
    html_parts.append(f'  if ({initial_time} > 0) {{ video.currentTime = {initial_time}; }}')
    html_parts.append(f'  video.playbackRate = {initial_rate};')
    html_parts.append('  updateSpeedButtons();')
    html_parts.append('  sendStateToStreamlit("loaded");')
    html_parts.append('});')
    
    html_parts.append('video.addEventListener("ratechange", function() {')
    html_parts.append('  updateSpeedButtons();')
    html_parts.append('  sendStateToStreamlit("ratechange");')
    html_parts.append('});')
    
    html_parts.append('video.addEventListener("seeked", function() {')
    html_parts.append('  updateTimeDisplay();')
    html_parts.append('  sendStateToStreamlit("seek");')
    html_parts.append('});')
    
    # Speed control
    html_parts.append('function setSpeed(rate) { video.playbackRate = rate; }')
    
    html_parts.append('function updateSpeedButtons() {')
    html_parts.append('  speedBtns.forEach(function(btn) {')
    html_parts.append('    const text = btn.textContent;')
    html_parts.append('    const rate = parseFloat(text);')
    html_parts.append('    if (Math.abs(rate - video.playbackRate) < 0.01) { btn.classList.add("active"); } else { btn.classList.remove("active"); }')
    html_parts.append('  });')
    html_parts.append('}')
    
    # Seek
    html_parts.append('function seekBy(delta) {')
    html_parts.append('  video.currentTime = Math.max(0, Math.min(duration || 99999, video.currentTime + delta));')
    html_parts.append('}')
    
    # Frame step
    html_parts.append('function frameStep(direction) {')
    html_parts.append('  const frameTime = 0.04;')
    html_parts.append('  video.pause();')
    html_parts.append('  video.currentTime = Math.max(0, Math.min(duration || 99999, video.currentTime + direction * frameTime));')
    html_parts.append('}')
    
    # Jump to time
    html_parts.append('function jumpToTime() {')
    html_parts.append('  const min = parseInt(document.getElementById("jumpMin").value) || 0;')
    html_parts.append('  const sec = parseInt(document.getElementById("jumpSec").value) || 0;')
    html_parts.append('  const target = min * 60 + sec;')
    html_parts.append('  video.currentTime = Math.max(0, Math.min(duration || 99999, target));')
    html_parts.append('}')
    
    # Render annotation dots
    html_parts.append('function renderAnnotationDots() {')
    html_parts.append('  if (duration <= 0) return;')
    html_parts.append('  const oldDots = timeline.querySelectorAll(".timeline-dot");')
    html_parts.append('  oldDots.forEach(function(d) { d.remove(); });')
    html_parts.append('  annotationData.forEach(function(ann) {')
    html_parts.append('    const pct = (ann.timestamp / duration) * 100;')
    html_parts.append('    const dot = document.createElement("div");')
    html_parts.append('    dot.className = "timeline-dot";')
    html_parts.append('    dot.style.left = pct + "%";')
    html_parts.append('    dot.style.background = ann.color || "#8C8C8C";')
    html_parts.append('    dot.title = ann.timeText + " - " + ann.eventType + (ann.team ? " " + ann.team : "");')
    html_parts.append('    dot.addEventListener("click", function(e) {')
    html_parts.append('      e.stopPropagation();')
    html_parts.append('      video.currentTime = ann.timestamp;')
    html_parts.append('    });')
    html_parts.append('    timeline.appendChild(dot);')
    html_parts.append('  });')
    html_parts.append('}')
    
    # Timeline click
    html_parts.append('timeline.addEventListener("click", function(e) {')
    html_parts.append('  if (duration <= 0) return;')
    html_parts.append('  const rect = timeline.getBoundingClientRect();')
    html_parts.append('  const pct = (e.clientX - rect.left) / rect.width;')
    html_parts.append('  video.currentTime = Math.max(0, Math.min(duration, pct * duration));')
    html_parts.append('});')
    
    # Timeline drag
    html_parts.append('let isDragging = false;')
    html_parts.append('timeline.addEventListener("mousedown", function(e) { isDragging = true; handleTimelineDrag(e); });')
    html_parts.append('document.addEventListener("mousemove", function(e) { if (isDragging && duration > 0) { handleTimelineDrag(e); } });')
    html_parts.append('document.addEventListener("mouseup", function() { isDragging = false; });')
    html_parts.append('function handleTimelineDrag(e) {')
    html_parts.append('  const rect = timeline.getBoundingClientRect();')
    html_parts.append('  const pct = (e.clientX - rect.left) / rect.width;')
    html_parts.append('  video.currentTime = Math.max(0, Math.min(duration, pct * duration));')
    html_parts.append('}')
    
    # Keyboard shortcuts
    html_parts.append('document.addEventListener("keydown", function(e) {')
    html_parts.append('  if (e.target.tagName === "INPUT") return;')
    html_parts.append('  switch(e.key) {')
    html_parts.append('    case " ": e.preventDefault(); togglePlay(); break;')
    html_parts.append('    case "ArrowLeft": e.preventDefault(); seekBy(e.shiftKey ? -5 : -1); break;')
    html_parts.append('    case "ArrowRight": e.preventDefault(); seekBy(e.shiftKey ? 5 : 1); break;')
    html_parts.append('    case "ArrowUp": e.preventDefault(); frameStep(1); break;')
    html_parts.append('    case "ArrowDown": e.preventDefault(); frameStep(-1); break;')
    html_parts.append('  }')
    html_parts.append('});')
    
    # Streamlit bidirectional communication
    html_parts.append('function sendStateToStreamlit(action) {')
    html_parts.append('  if (typeof Streamlit === "undefined") return;')
    html_parts.append('  const data = {')
    html_parts.append('    currentTime: video.currentTime,')
    html_parts.append('    duration: duration,')
    html_parts.append('    isPlaying: !video.paused,')
    html_parts.append('    playbackRate: video.playbackRate,')
    html_parts.append(f'    action: action,')
    html_parts.append(f'    seekToken: {seek_token}')
    html_parts.append('  };')
    html_parts.append('  lastSentTime = video.currentTime;')
    html_parts.append('  try { Streamlit.setComponentValue(data); } catch(e) {}')
    html_parts.append('}')
    
    html_parts.append('function throttledSendTime() {')
    html_parts.append('  if (sendThrottleTimer) return;')
    html_parts.append('  sendThrottleTimer = setTimeout(function() {')
    html_parts.append('    sendStateToStreamlit("timeupdate");')
    html_parts.append('    sendThrottleTimer = null;')
    html_parts.append('  }, 200);')
    html_parts.append('}')
    
    html_parts.append('function sendTimeToStreamlit() { sendStateToStreamlit("manual"); }')
    
    # Set frame height
    html_parts.append('try { Streamlit.setFrameHeight(); } catch(e) {}')
    
    # Init
    html_parts.append('updateTimeDisplay();')
    html_parts.append('updateSpeedButtons();')
    
    html_parts.append('</script>')
    html_parts.append('</body>')
    html_parts.append('</html>')
    
    return '\n'.join(html_parts)
