"""
足球视频战术标注核心模块 v2.0
提供标注数据结构、标注管理、战术模板、球员名单、多视频管理、多格式导出等核心功能
"""

import json
import os
import csv
import io
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Tuple
from collections import defaultdict


# ============================================================
# 常量定义
# ============================================================

# 支持的事件类型（与 Opta/StatsBomb 常见分类对齐）
EVENT_TYPES = [
    "传球",
    "射门",
    "抢断",
    "定位球",
    "战术犯规",
    "换人",
    "阵型变化",
    "其他",
]

# 数字键到事件类型的映射
EVENT_TYPE_KEY_MAP = {
    "1": "传球",
    "2": "射门",
    "3": "抢断",
    "4": "定位球",
    "5": "战术犯规",
    "6": "换人",
    "7": "阵型变化",
    "8": "其他",
}

# 场区选项（按战术区域划分）
TACTIC_ZONES = [
    "本方半场",
    "中场",
    "对方半场",
    "禁区内",
    "禁区外",
]

# 事件类型对应的颜色（用于 UI 标签着色）
EVENT_COLORS = {
    "传球": "#36CFC9",       # 蓝绿
    "射门": "#FF7A45",       # 橙红
    "抢断": "#5CDBD3",       # 青
    "定位球": "#FFD666",     # 金黄
    "战术犯规": "#FF4D4F",   # 红
    "换人": "#9254DE",       # 紫
    "阵型变化": "#69C0FF",   # 蓝
    "其他": "#8C8C8C",       # 灰
}

# 默认主队颜色（蓝色系）
DEFAULT_HOME_COLOR = "#1890FF"
DEFAULT_HOME_COLOR_LIGHT = "#69C0FF"

# 默认客队颜色（红色系）
DEFAULT_AWAY_COLOR = "#F5222D"
DEFAULT_AWAY_COLOR_LIGHT = "#FF7875"

# 一帧的时间（25fps）
FRAME_DURATION = 0.04


# ============================================================
# 数据类
# ============================================================

@dataclass
class TacticalAnnotation:
    """
    战术标注数据类

    Attributes:
        timestamp: 时间戳（秒，浮点数）
        event_type: 事件类型
        team: 队伍（主队/客队）
        team_side: 队伍侧别 home/away
        players: 涉及球员列表
        description: 事件描述
        tactic_zone: 场区
        notes: 备注信息
        x: 球场x坐标（0-100相对坐标）
        y: 球场y坐标（0-100相对坐标）
        video_index: 来自第几段视频
        annotation_id: 标注唯一标识
    """
    timestamp: float
    event_type: str
    team: str = ""
    team_side: str = ""  # "home" / "away" / ""
    players: List[str] = field(default_factory=list)
    description: str = ""
    tactic_zone: str = ""
    notes: str = ""
    x: float = -1.0  # -1 表示未设置
    y: float = -1.0
    video_index: int = 0
    annotation_id: str = ""

    def __post_init__(self):
        if not self.annotation_id:
            self.annotation_id = f"ann_{self.timestamp:.3f}_{id(self)}_{self.video_index}"

    @property
    def formatted_time(self) -> str:
        """格式化为 MM:SS 字符串"""
        minutes = int(self.timestamp // 60)
        seconds = int(self.timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def formatted_time_full(self) -> str:
        """格式化为 HH:MM:SS 字符串"""
        hours = int(self.timestamp // 3600)
        minutes = int((self.timestamp % 3600) // 60)
        seconds = int(self.timestamp % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return f"{minutes:02d}:{seconds:02d}"

    @property
    def has_coordinates(self) -> bool:
        """是否设置了坐标"""
        return self.x >= 0 and self.y >= 0

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TacticalAnnotation":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TacticalTemplate:
    """
    常用战术模板
    """
    template_id: str = ""
    name: str = ""
    event_type: str = "传球"
    team_side: str = ""  # home / away / ""
    description: str = ""
    tactic_zone: str = ""
    notes: str = ""
    is_custom: bool = False  # 是否用户自定义

    def __post_init__(self):
        if not self.template_id:
            self.template_id = f"tpl_{id(self)}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TacticalTemplate":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class Player:
    """球员数据"""
    number: str = ""
    name: str = ""

    @property
    def display(self) -> str:
        if self.number and self.name:
            return f"{self.number}号 {self.name}"
        elif self.name:
            return self.name
        else:
            return self.number

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class TeamRoster:
    """球队名单"""
    team_name: str = "主队"
    players: List[Player] = field(default_factory=list)

    def add_player(self, number: str, name: str) -> Player:
        p = Player(number=number, name=name)
        self.players.append(p)
        return p

    def remove_player(self, index: int):
        if 0 <= index < len(self.players):
            self.players.pop(index)

    def get_player_names(self) -> List[str]:
        return [p.display for p in self.players]

    def to_dict(self) -> dict:
        return {
            "team_name": self.team_name,
            "players": [p.to_dict() for p in self.players],
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TeamRoster":
        roster = cls(team_name=data.get("team_name", "球队"))
        for p_data in data.get("players", []):
            roster.players.append(Player.from_dict(p_data))
        return roster


@dataclass
class VideoSegment:
    """视频段（用于多段视频支持）"""
    index: int = 0
    name: str = ""
    video_path: str = ""
    video_bytes: Optional[bytes] = None
    duration: float = 0.0
    label: str = ""  # 如 "上半场"、"下半场"、"加时赛"

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "name": self.name,
            "duration": self.duration,
            "label": self.label,
        }


# ============================================================
# 默认战术模板
# ============================================================

DEFAULT_TEMPLATES = [
    {
        "name": "中路渗透配合",
        "event_type": "传球",
        "team_side": "home",
        "description": "中路连续短传配合，穿透对方防线制造威胁",
        "tactic_zone": "对方半场",
        "notes": "",
    },
    {
        "name": "边路传中",
        "event_type": "传球",
        "team_side": "home",
        "description": "边路球员带球突破后传中到禁区",
        "tactic_zone": "对方半场",
        "notes": "",
    },
    {
        "name": "高位逼抢断球",
        "event_type": "抢断",
        "team_side": "home",
        "description": "前场高位压迫，在对方半场完成抢断",
        "tactic_zone": "对方半场",
        "notes": "",
    },
    {
        "name": "防守反击",
        "event_type": "传球",
        "team_side": "home",
        "description": "断球后快速反击，利用对方防线身后空间",
        "tactic_zone": "本方半场",
        "notes": "",
    },
    {
        "name": "定位球-角球进攻",
        "event_type": "定位球",
        "team_side": "home",
        "description": "角球进攻战术配合",
        "tactic_zone": "禁区内",
        "notes": "",
    },
    {
        "name": "定位球-角球防守",
        "event_type": "定位球",
        "team_side": "away",
        "description": "角球防守站位与盯人",
        "tactic_zone": "禁区内",
        "notes": "",
    },
    {
        "name": "定位球-任意球进攻",
        "event_type": "定位球",
        "team_side": "home",
        "description": "前场任意球直接或间接进攻",
        "tactic_zone": "禁区外",
        "notes": "",
    },
    {
        "name": "定位球-任意球防守",
        "event_type": "定位球",
        "team_side": "away",
        "description": "人墙组织与任意球防守",
        "tactic_zone": "禁区外",
        "notes": "",
    },
    {
        "name": "远射破门",
        "event_type": "射门",
        "team_side": "home",
        "description": "禁区外远射尝试",
        "tactic_zone": "禁区外",
        "notes": "",
    },
    {
        "name": "内切射门",
        "event_type": "射门",
        "team_side": "home",
        "description": "边路球员内切后射门",
        "tactic_zone": "禁区内",
        "notes": "",
    },
    {
        "name": "中场拦截抢断",
        "event_type": "抢断",
        "team_side": "home",
        "description": "中场区域成功抢断，阻断对方进攻",
        "tactic_zone": "中场",
        "notes": "",
    },
    {
        "name": "战术犯规",
        "event_type": "战术犯规",
        "team_side": "away",
        "description": "为阻止对方反击而做出的战术犯规",
        "tactic_zone": "本方半场",
        "notes": "",
    },
    {
        "name": "换人调整",
        "event_type": "换人",
        "team_side": "home",
        "description": "战术换人调整，改变场上阵型或人员配置",
        "tactic_zone": "",
        "notes": "",
    },
    {
        "name": "阵型变化",
        "event_type": "阵型变化",
        "team_side": "home",
        "description": "比赛中调整战术阵型",
        "tactic_zone": "",
        "notes": "",
    },
    {
        "name": "二过一配合",
        "event_type": "传球",
        "team_side": "home",
        "description": "两名球员之间的二过一撞墙配合",
        "tactic_zone": "对方半场",
        "notes": "",
    },
]


# ============================================================
# 核心类：视频标注管理器
# ============================================================

class VideoAnnotator:
    """
    视频战术标注管理器 v2.0

    负责加载视频、管理标注列表、战术模板、球员名单、导入导出等核心逻辑。
    """

    def __init__(self):
        # 视频相关（多段视频）
        self.video_segments: List[VideoSegment] = []
        self.current_video_index: int = 0

        # 标注
        self.annotations: List[TacticalAnnotation] = []

        # 战术模板
        self.templates: List[TacticalTemplate] = []
        self._load_default_templates()

        # 球队名单
        self.home_roster = TeamRoster(team_name="主队")
        self.away_roster = TeamRoster(team_name="客队")

        # 球队颜色
        self.home_color: str = DEFAULT_HOME_COLOR
        self.home_color_light: str = DEFAULT_HOME_COLOR_LIGHT
        self.away_color: str = DEFAULT_AWAY_COLOR
        self.away_color_light: str = DEFAULT_AWAY_COLOR_LIGHT

        # 播放设置
        self.playback_rate: float = 1.0

    # --------------------------------------------------------
    # 默认模板
    # --------------------------------------------------------

    def _load_default_templates(self):
        """加载默认战术模板"""
        for tpl_data in DEFAULT_TEMPLATES:
            tpl = TacticalTemplate(**tpl_data, is_custom=False)
            self.templates.append(tpl)

    # --------------------------------------------------------
    # 视频相关（多段视频支持）
    # --------------------------------------------------------

    @property
    def current_video(self) -> Optional[VideoSegment]:
        """当前选中的视频段"""
        if 0 <= self.current_video_index < len(self.video_segments):
            return self.video_segments[self.current_video_index]
        return None

    @property
    def video_name(self) -> str:
        if self.current_video:
            return self.current_video.name
        return ""

    @property
    def video_duration(self) -> float:
        if self.current_video:
            return self.current_video.duration
        return 0.0

    def add_video_segment(self, name: str, video_bytes: bytes,
                          label: str = "") -> VideoSegment:
        """添加一段视频"""
        index = len(self.video_segments)
        if not label:
            label = f"第{index + 1}段"
        seg = VideoSegment(
            index=index,
            name=name,
            video_bytes=video_bytes,
            label=label,
        )
        self.video_segments.append(seg)
        self.current_video_index = index
        return seg

    def switch_video(self, index: int) -> bool:
        """切换到指定视频段"""
        if 0 <= index < len(self.video_segments):
            self.current_video_index = index
            return True
        return False

    def remove_video_segment(self, index: int) -> bool:
        """删除视频段（同时删除该段的所有标注）"""
        if index < 0 or index >= len(self.video_segments):
            return False
        # 删除该段视频的所有标注
        self.annotations = [
            a for a in self.annotations if a.video_index != index
        ]
        # 重新编号后续视频段的索引
        self.video_segments.pop(index)
        for i, seg in enumerate(self.video_segments):
            seg.index = i
        for ann in self.annotations:
            if ann.video_index > index:
                ann.video_index -= 1
        if self.current_video_index >= len(self.video_segments):
            self.current_video_index = max(0, len(self.video_segments) - 1)
        return True

    def set_video_duration(self, duration: float, video_index: Optional[int] = None):
        """设置视频时长"""
        idx = video_index if video_index is not None else self.current_video_index
        if 0 <= idx < len(self.video_segments):
            self.video_segments[idx].duration = max(0.0, duration)

    # --------------------------------------------------------
    # 标注管理：增删改查
    # --------------------------------------------------------

    def add_annotation(
        self,
        timestamp: float,
        event_type: str,
        team: str = "",
        team_side: str = "",
        players: Optional[List[str]] = None,
        description: str = "",
        tactic_zone: str = "",
        notes: str = "",
        x: float = -1.0,
        y: float = -1.0,
        video_index: Optional[int] = None,
    ) -> TacticalAnnotation:
        """添加一条标注"""
        v_idx = video_index if video_index is not None else self.current_video_index
        annotation = TacticalAnnotation(
            timestamp=max(0.0, timestamp),
            event_type=event_type,
            team=team,
            team_side=team_side,
            players=players or [],
            description=description,
            tactic_zone=tactic_zone,
            notes=notes,
            x=x,
            y=y,
            video_index=v_idx,
        )
        self.annotations.append(annotation)
        self._sort_annotations()
        return annotation

    def edit_annotation(self, annotation_id: str, **kwargs) -> bool:
        """编辑标注"""
        for ann in self.annotations:
            if ann.annotation_id == annotation_id:
                for key, value in kwargs.items():
                    if hasattr(ann, key) and key != "annotation_id":
                        setattr(ann, key, value)
                self._sort_annotations()
                return True
        return False

    def delete_annotation(self, annotation_id: str) -> bool:
        """删除标注"""
        for i, ann in enumerate(self.annotations):
            if ann.annotation_id == annotation_id:
                self.annotations.pop(i)
                return True
        return False

    def get_annotation(self, annotation_id: str) -> Optional[TacticalAnnotation]:
        """根据 ID 获取标注"""
        for ann in self.annotations:
            if ann.annotation_id == annotation_id:
                return ann
        return None

    def get_annotations_for_video(self, video_index: int) -> List[TacticalAnnotation]:
        """获取指定视频段的所有标注"""
        return [a for a in self.annotations if a.video_index == video_index]

    def _sort_annotations(self):
        """按视频索引+时间戳排序"""
        self.annotations.sort(key=lambda x: (x.video_index, x.timestamp))

    # --------------------------------------------------------
    # 战术模板管理
    # --------------------------------------------------------

    def add_template(self, name: str, event_type: str = "传球",
                     team_side: str = "", description: str = "",
                     tactic_zone: str = "", notes: str = "") -> TacticalTemplate:
        """添加自定义模板"""
        tpl = TacticalTemplate(
            name=name,
            event_type=event_type,
            team_side=team_side,
            description=description,
            tactic_zone=tactic_zone,
            notes=notes,
            is_custom=True,
        )
        self.templates.append(tpl)
        return tpl

    def delete_template(self, template_id: str) -> bool:
        """删除模板（只能删自定义的）"""
        for i, tpl in enumerate(self.templates):
            if tpl.template_id == template_id and tpl.is_custom:
                self.templates.pop(i)
                return True
        return False

    def get_template(self, template_id: str) -> Optional[TacticalTemplate]:
        for tpl in self.templates:
            if tpl.template_id == template_id:
                return tpl
        return None

    def apply_template(self, template_id: str) -> Optional[dict]:
        """应用模板，返回可填入表单的字段字典"""
        tpl = self.get_template(template_id)
        if not tpl:
            return None
        team_name = ""
        if tpl.team_side == "home":
            team_name = self.home_roster.team_name
        elif tpl.team_side == "away":
            team_name = self.away_roster.team_name
        return {
            "event_type": tpl.event_type,
            "team_side": tpl.team_side,
            "team": team_name,
            "description": tpl.description,
            "tactic_zone": tpl.tactic_zone,
            "notes": tpl.notes,
        }

    # --------------------------------------------------------
    # 球队名单管理
    # --------------------------------------------------------

    def set_team_name(self, side: str, name: str):
        """设置球队名称 side: home/away"""
        if side == "home":
            self.home_roster.team_name = name
        elif side == "away":
            self.away_roster.team_name = name

    def add_player(self, side: str, number: str, name: str):
        """添加球员"""
        roster = self.home_roster if side == "home" else self.away_roster
        roster.add_player(number, name)

    def remove_player(self, side: str, index: int):
        """删除球员"""
        roster = self.home_roster if side == "home" else self.away_roster
        roster.remove_player(index)

    def get_roster(self, side: str) -> TeamRoster:
        return self.home_roster if side == "home" else self.away_roster

    def set_team_colors(self, home_color: str, away_color: str):
        """设置队伍颜色"""
        self.home_color = home_color
        self.away_color = away_color

    def get_team_color(self, team_side: str) -> str:
        """获取队伍颜色"""
        if team_side == "home":
            return self.home_color
        elif team_side == "away":
            return self.away_color
        return "#8C8C8C"

    # --------------------------------------------------------
    # 过滤与查询
    # --------------------------------------------------------

    def filter_by_event_type(self, event_type: str) -> List[TacticalAnnotation]:
        return [a for a in self.annotations if a.event_type == event_type]

    def filter_by_team(self, team: str) -> List[TacticalAnnotation]:
        return [a for a in self.annotations if a.team == team]

    def filter_by_team_side(self, side: str) -> List[TacticalAnnotation]:
        return [a for a in self.annotations if a.team_side == side]

    def filter_by_time_range(self, start: float, end: float,
                             video_index: Optional[int] = None) -> List[TacticalAnnotation]:
        result = [a for a in self.annotations if start <= a.timestamp <= end]
        if video_index is not None:
            result = [a for a in result if a.video_index == video_index]
        return result

    # --------------------------------------------------------
    # 导入导出（多种格式）
    # --------------------------------------------------------

    def export_json(self, filepath: str) -> bool:
        """导出标注为 JSON 文件（完整格式）"""
        try:
            data = self._build_export_data()
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def export_json_string(self) -> str:
        """导出为 JSON 字符串"""
        data = self._build_export_data()
        return json.dumps(data, ensure_ascii=False, indent=2)

    def _build_export_data(self) -> dict:
        """构建导出数据结构"""
        return {
            "version": "2.0",
            "video_segments": [seg.to_dict() for seg in self.video_segments],
            "total_annotations": len(self.annotations),
            "home_roster": self.home_roster.to_dict(),
            "away_roster": self.away_roster.to_dict(),
            "home_color": self.home_color,
            "away_color": self.away_color,
            "custom_templates": [
                tpl.to_dict() for tpl in self.templates if tpl.is_custom
            ],
            "annotations": [
                {
                    "annotation_id": ann.annotation_id,
                    "timestamp": round(ann.timestamp, 3),
                    "formatted_time": ann.formatted_time,
                    "event_type": ann.event_type,
                    "team": ann.team,
                    "team_side": ann.team_side,
                    "players": ann.players,
                    "description": ann.description,
                    "tactic_zone": ann.tactic_zone,
                    "notes": ann.notes,
                    "x": ann.x,
                    "y": ann.y,
                    "video_index": ann.video_index,
                }
                for ann in self.annotations
            ],
        }

    def export_csv_string(self) -> str:
        """导出为 CSV 格式字符串"""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "序号", "视频段", "时间点", "事件类型", "队伍", "队伍侧别",
            "涉及球员", "场区", "X坐标", "Y坐标", "描述", "备注"
        ])
        for i, ann in enumerate(self.annotations, 1):
            video_label = (
                self.video_segments[ann.video_index].label
                if 0 <= ann.video_index < len(self.video_segments)
                else f"第{ann.video_index + 1}段"
            )
            writer.writerow([
                i,
                video_label,
                ann.formatted_time_full,
                ann.event_type,
                ann.team,
                {"home": "主队", "away": "客队", "": ""}.get(ann.team_side, ""),
                "、".join(ann.players),
                ann.tactic_zone,
                f"{ann.x:.1f}" if ann.has_coordinates else "",
                f"{ann.y:.1f}" if ann.has_coordinates else "",
                ann.description,
                ann.notes,
            ])
        return output.getvalue()

    def export_srt_string(self) -> str:
        """导出为 SRT 字幕格式"""
        lines = []
        sorted_anns = sorted(self.annotations, key=lambda x: (x.video_index, x.timestamp))
        for i, ann in enumerate(sorted_anns, 1):
            # SRT 时间格式：HH:MM:SS,mmm
            start = ann.timestamp
            end = start + 3.0  # 每条字幕显示3秒

            def format_srt_time(t):
                h = int(t // 3600)
                m = int((t % 3600) // 60)
                s = int(t % 60)
                ms = int((t - int(t)) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

            lines.append(str(i))
            lines.append(f"{format_srt_time(start)} --> {format_srt_time(end)}")

            # 字幕文本
            text_parts = []
            if ann.team:
                text_parts.append(f"【{ann.team}】")
            text_parts.append(ann.event_type)
            if ann.players:
                text_parts.append(f"({'/'.join(ann.players)})")
            if ann.description:
                text_parts.append(f"\n{ann.description}")

            lines.append("".join(text_parts))
            lines.append("")  # 空行分隔

        return "\n".join(lines)

    def export_report_markdown(self) -> str:
        """生成战术报告（Markdown 格式）"""
        stats = self.stats
        lines = []
        lines.append("# 足球战术标注报告")
        lines.append("")
        lines.append("## 基本信息")
        lines.append("")
        if self.video_segments:
            lines.append(f"- **视频数量**：{len(self.video_segments)} 段")
            for seg in self.video_segments:
                lines.append(f"  - {seg.label}：{seg.name}")
        lines.append(f"- **标注总数**：{stats['total']} 条")
        lines.append(f"- **主队**：{self.home_roster.team_name}（{len(self.home_roster.players)} 人）")
        lines.append(f"- **客队**：{self.away_roster.team_name}（{len(self.away_roster.players)} 人）")
        lines.append("")

        # 事件类型分布
        lines.append("## 事件类型分布")
        lines.append("")
        lines.append("| 事件类型 | 数量 | 占比 |")
        lines.append("|---------|------|------|")
        total = max(stats["total"], 1)
        for evt, count in sorted(stats["by_event_type"].items(), key=lambda x: -x[1]):
            pct = count / total * 100
            lines.append(f"| {evt} | {count} | {pct:.1f}% |")
        lines.append("")

        # 两队对比
        home_count = len(self.filter_by_team_side("home"))
        away_count = len(self.filter_by_team_side("away"))
        lines.append("## 两队对比")
        lines.append("")
        lines.append(f"| 队伍 | 标注数 | 占比 |")
        lines.append(f"|------|--------|------|")
        if total:
            lines.append(f"| {self.home_roster.team_name}（主队） | {home_count} | {home_count/total*100:.1f}% |")
            lines.append(f"| {self.away_roster.team_name}（客队） | {away_count} | {away_count/total*100:.1f}% |")
        lines.append("")

        # 各队事件分布
        lines.append("### 主队事件分布")
        lines.append("")
        home_events = defaultdict(int)
        for a in self.filter_by_team_side("home"):
            home_events[a.event_type] += 1
        if home_events:
            lines.append("| 事件类型 | 数量 |")
            lines.append("|---------|------|")
            for evt, count in sorted(home_events.items(), key=lambda x: -x[1]):
                lines.append(f"| {evt} | {count} |")
        else:
            lines.append("暂无数据")
        lines.append("")

        lines.append("### 客队事件分布")
        lines.append("")
        away_events = defaultdict(int)
        for a in self.filter_by_team_side("away"):
            away_events[a.event_type] += 1
        if away_events:
            lines.append("| 事件类型 | 数量 |")
            lines.append("|---------|------|")
            for evt, count in sorted(away_events.items(), key=lambda x: -x[1]):
                lines.append(f"| {evt} | {count} |")
        else:
            lines.append("暂无数据")
        lines.append("")

        # 关键时间点
        lines.append("## 关键事件时间线")
        lines.append("")
        if self.annotations:
            for ann in sorted(self.annotations, key=lambda x: (x.video_index, x.timestamp)):
                video_label = (
                    self.video_segments[ann.video_index].label
                    if 0 <= ann.video_index < len(self.video_segments)
                    else f"第{ann.video_index + 1}段"
                )
                team_str = f"**{ann.team}** " if ann.team else ""
                players_str = f"（{'/'.join(ann.players)}）" if ann.players else ""
                lines.append(
                    f"- **[{video_label} {ann.formatted_time}]** "
                    f"{team_str}{ann.event_type}{players_str}：{ann.description}"
                )
        else:
            lines.append("暂无标注数据")
        lines.append("")

        # 战术摘要
        lines.append("## 战术分析摘要")
        lines.append("")
        if stats["total"] > 0:
            # 自动生成一段摘要
            top_event = max(stats["by_event_type"].items(), key=lambda x: x[1])[0]
            summary_parts = [
                f"本场比赛共标注 **{stats['total']}** 条战术事件，",
                f"其中 **{top_event}** 最多（{stats['by_event_type'][top_event]}次）。",
            ]
            if home_count > 0 and away_count > 0:
                more_team = self.home_roster.team_name if home_count > away_count else self.away_roster.team_name
                summary_parts.append(
                    f"从队伍来看，{more_team}的被标注事件更多，"
                    f"两队标注数之比为 {home_count}:{away_count}。"
                )
            if stats["by_zone"]:
                top_zone = max(stats["by_zone"].items(), key=lambda x: x[1])[0]
                summary_parts.append(f"事件主要发生在**{top_zone}**区域。")

            lines.append("".join(summary_parts))
        else:
            lines.append("暂无标注数据，无法生成战术分析摘要。")
        lines.append("")

        return "\n".join(lines)

    def import_json(self, filepath: str) -> bool:
        """从 JSON 文件导入标注"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 兼容 v1 和 v2 格式
            if isinstance(data, list):
                ann_list = data
                video_segs_data = []
                home_data = None
                away_data = None
                custom_tpls = []
            elif isinstance(data, dict):
                ann_list = data.get("annotations", [])
                video_segs_data = data.get("video_segments", [])
                home_data = data.get("home_roster", None)
                away_data = data.get("away_roster", None)
                custom_tpls = data.get("custom_templates", [])

                # v1 格式兼容
                if not ann_list and "annotations" in data:
                    ann_list = data["annotations"]
                if "video_name" in data and not video_segs_data:
                    video_segs_data = [{
                        "index": 0,
                        "name": data.get("video_name", ""),
                        "duration": data.get("video_duration", 0),
                        "label": "全场",
                    }]
            else:
                return False

            if not isinstance(ann_list, list):
                return False

            # 导入标注
            imported = []
            for item in ann_list:
                if "timestamp" in item and "event_type" in item:
                    imported.append(TacticalAnnotation.from_dict(item))
            self.annotations = imported
            self._sort_annotations()

            # 导入球队名单
            if home_data:
                self.home_roster = TeamRoster.from_dict(home_data)
            if away_data:
                self.away_roster = TeamRoster.from_dict(away_data)

            # 导入颜色
            if "home_color" in data:
                self.home_color = data["home_color"]
            if "away_color" in data:
                self.away_color = data["away_color"]

            # 导入自定义模板
            for tpl_data in custom_tpls:
                if isinstance(tpl_data, dict):
                    self.templates.append(TacticalTemplate.from_dict(tpl_data))

            # 保存视频段元数据（不含视频文件本身）
            self.video_segments = []
            for seg_data in video_segs_data:
                seg = VideoSegment(
                    index=seg_data.get("index", len(self.video_segments)),
                    name=seg_data.get("name", ""),
                    duration=seg_data.get("duration", 0),
                    label=seg_data.get("label", ""),
                )
                self.video_segments.append(seg)

            return True
        except Exception:
            return False

    def export_roster_json_string(self) -> str:
        """导出球队名单为 JSON"""
        data = {
            "home_roster": self.home_roster.to_dict(),
            "away_roster": self.away_roster.to_dict(),
            "home_color": self.home_color,
            "away_color": self.away_color,
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    def import_roster_json(self, filepath: str) -> bool:
        """导入球队名单"""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            if "home_roster" in data:
                self.home_roster = TeamRoster.from_dict(data["home_roster"])
            if "away_roster" in data:
                self.away_roster = TeamRoster.from_dict(data["away_roster"])
            if "home_color" in data:
                self.home_color = data["home_color"]
            if "away_color" in data:
                self.away_color = data["away_color"]
            return True
        except Exception:
            return False

    # --------------------------------------------------------
    # 统计信息
    # --------------------------------------------------------

    @property
    def stats(self) -> dict:
        """获取标注统计信息"""
        event_counts = {}
        team_counts = {}
        zone_counts = {}
        player_counts = defaultdict(int)
        for ann in self.annotations:
            event_counts[ann.event_type] = event_counts.get(ann.event_type, 0) + 1
            if ann.team:
                team_counts[ann.team] = team_counts.get(ann.team, 0) + 1
            if ann.tactic_zone:
                zone_counts[ann.tactic_zone] = zone_counts.get(ann.tactic_zone, 0) + 1
            for p in ann.players:
                player_counts[p] += 1

        # 排序后的球员统计
        top_players = sorted(player_counts.items(), key=lambda x: -x[1])[:10]

        return {
            "total": len(self.annotations),
            "by_event_type": event_counts,
            "by_team": team_counts,
            "by_zone": zone_counts,
            "top_players": top_players,
        }
