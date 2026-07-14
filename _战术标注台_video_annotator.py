"""
足球视频战术标注核心模块
提供标注数据结构、标注管理、导入导出等核心功能
"""

import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional


# ============================================================
# 常量定义：事件类型与场区选项
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


# ============================================================
# 数据类：单条战术标注
# ============================================================

@dataclass
class TacticalAnnotation:
    """
    战术标注数据类

    Attributes:
        timestamp: 时间戳（秒，浮点数）
        event_type: 事件类型（传球/射门/抢断等）
        team: 队伍（主队/客队/其他，或自由输入）
        players: 涉及球员列表
        description: 事件描述
        tactic_zone: 场区
        notes: 备注信息
        annotation_id: 标注唯一标识（自动生成）
    """
    timestamp: float
    event_type: str
    team: str = ""
    players: List[str] = field(default_factory=list)
    description: str = ""
    tactic_zone: str = ""
    notes: str = ""
    annotation_id: str = ""

    def __post_init__(self):
        """初始化后自动生成 ID（若未提供）"""
        if not self.annotation_id:
            # 使用时间戳作为简易唯一 ID
            self.annotation_id = f"ann_{self.timestamp:.3f}_{id(self)}"

    @property
    def formatted_time(self) -> str:
        """将秒格式化为 MM:SS 字符串"""
        minutes = int(self.timestamp // 60)
        seconds = int(self.timestamp % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def to_dict(self) -> dict:
        """转换为字典（用于 JSON 序列化）"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "TacticalAnnotation":
        """从字典构建实例"""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


# ============================================================
# 核心类：视频标注管理器
# ============================================================

class VideoAnnotator:
    """
    视频战术标注管理器

    负责加载视频、管理标注列表、导入导出等核心逻辑。
    不涉及 UI 层，可独立被脚本或其他应用调用。
    """

    def __init__(self):
        """初始化标注器"""
        self.video_path: Optional[str] = None
        self.video_name: str = ""
        self.annotations: List[TacticalAnnotation] = []
        self.video_duration: float = 0.0

    # --------------------------------------------------------
    # 视频相关
    # --------------------------------------------------------

    def load_video(self, video_path: str, duration: float = 0.0) -> bool:
        """
        加载视频文件

        Args:
            video_path: 视频文件路径
            duration: 视频时长（秒），若传入 0 则需外部获取

        Returns:
            是否加载成功
        """
        if not os.path.exists(video_path):
            return False
        self.video_path = video_path
        self.video_name = os.path.basename(video_path)
        self.video_duration = duration
        return True

    def set_video_duration(self, duration: float):
        """设置视频时长"""
        self.video_duration = max(0.0, duration)

    # --------------------------------------------------------
    # 标注管理：增删改查
    # --------------------------------------------------------

    def add_annotation(
        self,
        timestamp: float,
        event_type: str,
        team: str = "",
        players: Optional[List[str]] = None,
        description: str = "",
        tactic_zone: str = "",
        notes: str = "",
    ) -> TacticalAnnotation:
        """
        添加一条标注

        Args:
            timestamp: 时间戳（秒）
            event_type: 事件类型
            team: 队伍
            players: 涉及球员列表
            description: 描述
            tactic_zone: 场区
            notes: 备注

        Returns:
            新创建的标注对象
        """
        annotation = TacticalAnnotation(
            timestamp=max(0.0, timestamp),
            event_type=event_type,
            team=team,
            players=players or [],
            description=description,
            tactic_zone=tactic_zone,
            notes=notes,
        )
        self.annotations.append(annotation)
        self._sort_annotations()
        return annotation

    def edit_annotation(
        self,
        annotation_id: str,
        **kwargs,
    ) -> bool:
        """
        编辑标注

        Args:
            annotation_id: 标注 ID
            **kwargs: 需要更新的字段

        Returns:
            是否找到并更新
        """
        for ann in self.annotations:
            if ann.annotation_id == annotation_id:
                for key, value in kwargs.items():
                    if hasattr(ann, key) and key != "annotation_id":
                        setattr(ann, key, value)
                self._sort_annotations()
                return True
        return False

    def delete_annotation(self, annotation_id: str) -> bool:
        """
        删除标注

        Args:
            annotation_id: 标注 ID

        Returns:
            是否找到并删除
        """
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

    def _sort_annotations(self):
        """按时间戳排序标注列表"""
        self.annotations.sort(key=lambda x: x.timestamp)

    # --------------------------------------------------------
    # 过滤与查询
    # --------------------------------------------------------

    def filter_by_event_type(self, event_type: str) -> List[TacticalAnnotation]:
        """按事件类型过滤"""
        return [a for a in self.annotations if a.event_type == event_type]

    def filter_by_team(self, team: str) -> List[TacticalAnnotation]:
        """按队伍过滤"""
        return [a for a in self.annotations if a.team == team]

    def filter_by_time_range(
        self, start: float, end: float
    ) -> List[TacticalAnnotation]:
        """按时间范围过滤"""
        return [a for a in self.annotations if start <= a.timestamp <= end]

    # --------------------------------------------------------
    # 导入导出（JSON）
    # --------------------------------------------------------

    def export_json(self, filepath: str) -> bool:
        """
        导出标注为 JSON 文件

        输出格式标准化，便于后续 AI 战术脚本读取：
        {
            "video_name": "xxx.mp4",
            "video_duration": 5400.0,
            "total_annotations": 128,
            "annotations": [
                {
                    "annotation_id": "...",
                    "timestamp": 125.5,
                    "formatted_time": "02:05",
                    "event_type": "传球",
                    "team": "主队",
                    "players": ["张三", "李四"],
                    "description": "...",
                    "tactic_zone": "对方半场",
                    "notes": "..."
                },
                ...
            ]
        }

        Args:
            filepath: 输出文件路径

        Returns:
            是否导出成功
        """
        try:
            data = {
                "video_name": self.video_name,
                "video_duration": self.video_duration,
                "total_annotations": len(self.annotations),
                "annotations": [
                    {
                        "annotation_id": ann.annotation_id,
                        "timestamp": round(ann.timestamp, 3),
                        "formatted_time": ann.formatted_time,
                        "event_type": ann.event_type,
                        "team": ann.team,
                        "players": ann.players,
                        "description": ann.description,
                        "tactic_zone": ann.tactic_zone,
                        "notes": ann.notes,
                    }
                    for ann in self.annotations
                ],
            }
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False

    def import_json(self, filepath: str) -> bool:
        """
        从 JSON 文件导入标注

        Args:
            filepath: JSON 文件路径

        Returns:
            是否导入成功
        """
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 兼容格式：直接是列表，或包含 annotations 字段
            ann_list = data.get("annotations", data) if isinstance(data, dict) else data

            if not isinstance(ann_list, list):
                return False

            imported = []
            for item in ann_list:
                if "timestamp" in item and "event_type" in item:
                    imported.append(TacticalAnnotation.from_dict(item))

            self.annotations = imported
            self._sort_annotations()

            # 如果 JSON 中有视频信息，也一并加载
            if isinstance(data, dict):
                if "video_name" in data:
                    self.video_name = data["video_name"]
                if "video_duration" in data:
                    self.video_duration = data["video_duration"]

            return True
        except Exception:
            return False

    def export_json_string(self) -> str:
        """导出为 JSON 字符串（用于内存中传递）"""
        data = {
            "video_name": self.video_name,
            "video_duration": self.video_duration,
            "total_annotations": len(self.annotations),
            "annotations": [
                {
                    "annotation_id": ann.annotation_id,
                    "timestamp": round(ann.timestamp, 3),
                    "formatted_time": ann.formatted_time,
                    "event_type": ann.event_type,
                    "team": ann.team,
                    "players": ann.players,
                    "description": ann.description,
                    "tactic_zone": ann.tactic_zone,
                    "notes": ann.notes,
                }
                for ann in self.annotations
            ],
        }
        return json.dumps(data, ensure_ascii=False, indent=2)

    # --------------------------------------------------------
    # 统计信息
    # --------------------------------------------------------

    @property
    def stats(self) -> dict:
        """获取标注统计信息"""
        event_counts = {}
        team_counts = {}
        zone_counts = {}
        for ann in self.annotations:
            event_counts[ann.event_type] = event_counts.get(ann.event_type, 0) + 1
            if ann.team:
                team_counts[ann.team] = team_counts.get(ann.team, 0) + 1
            if ann.tactic_zone:
                zone_counts[ann.tactic_zone] = zone_counts.get(ann.tactic_zone, 0) + 1

        return {
            "total": len(self.annotations),
            "by_event_type": event_counts,
            "by_team": team_counts,
            "by_zone": zone_counts,
        }
