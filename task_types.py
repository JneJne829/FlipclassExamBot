from dataclasses import dataclass
from typing import Callable, Optional

@dataclass
class TaskStatus:
    """任務狀態常量"""
    WAITING = "等待中"
    RUNNING = "執行中"
    COMPLETED = "已完成"
    FAILED = "執行失敗"

@dataclass
class TaskConfig:
    """任務配置數據類"""
    account: str
    password: str
    course_id: str
    target_score: float
    answer_time: float
    print_callback: Optional[Callable] = None

    def update(self, **kwargs):
        """更新任務配置"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)