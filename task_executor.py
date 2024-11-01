import threading
from typing import Dict, Optional, Callable
import traceback
from task_types import TaskConfig, TaskStatus
from FlipclassExamBot import FlipclassExamBot

class TaskExecutor:
    """任務執行器類"""
    def __init__(self, status_callback):
        self.running_tasks = {}
        self.task_configs = {}
        self.status_callback = status_callback
        self._lock = threading.Lock()

    def add_task(self, row: int, config: TaskConfig) -> None:
        """添加新任務到執行器"""
        with self._lock:
            self.task_configs[row] = config

    def remove_task(self, row: int) -> bool:
        """移除任務並重新排序剩餘任務的索引"""
        with self._lock:
            if row not in self.task_configs:
                return False
                
            config = self.task_configs[row]
            if config.account in self.running_tasks and self.running_tasks[config.account].is_alive():
                return False

            # 刪除指定任務
            del self.task_configs[row]
            if config.account in self.running_tasks:
                del self.running_tasks[config.account]

            # 重新排序剩餘任務的索引
            new_configs = {}
            for old_row, cfg in self.task_configs.items():
                if old_row > row:
                    new_configs[old_row - 1] = cfg
                else:
                    new_configs[old_row] = cfg
            self.task_configs = new_configs

            return True

    def execute_task(self, row: int) -> bool:
        """執行指定行的任務"""
        with self._lock:
            if row not in self.task_configs:
                return False
            
            config = self.task_configs[row]
            account = config.account
            
            # 檢查任務是否已在執行
            if account in self.running_tasks and self.running_tasks[account].is_alive():
                return False

        # 更新狀態為執行中
        self.status_callback(row, TaskStatus.RUNNING)

        # 執行任務的線程函數
        def run_task():
            try:
                bot = FlipclassExamBot(
                    config.account,
                    config.password,
                    config.course_id,
                    config.answer_time,
                    config.target_score,
                    config.print_callback
                )
                success = bot.run()
                final_status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
            except Exception as e:
                final_status = TaskStatus.FAILED
                if config.print_callback:
                    config.print_callback(f"執行出錯: {str(e)}", "ERROR")
                    config.print_callback(traceback.format_exc(), "ERROR")
            finally:
                with self._lock:
                    if account in self.running_tasks:
                        del self.running_tasks[account]
                self.status_callback(row, final_status)

        # 創建並啟動新線程
        task_thread = threading.Thread(target=run_task, daemon=True)
        with self._lock:
            self.running_tasks[account] = task_thread
        task_thread.start()
        return True

    def is_task_running(self, account: str) -> bool:
        """檢查指定帳號的任務是否正在執行"""
        with self._lock:
            return account in self.running_tasks and self.running_tasks[account].is_alive()

    def get_task_config(self, row: int) -> Optional[TaskConfig]:
        """獲取指定行的任務配置"""
        with self._lock:
            return self.task_configs.get(row)

    def update_task_config(self, row: int, **kwargs) -> bool:
        """更新任務配置"""
        with self._lock:
            if row in self.task_configs:
                self.task_configs[row].update(**kwargs)
                return True
            return False

    def cleanup(self):
        """清理所有運行中的任務"""
        with self._lock:
            for thread in self.running_tasks.values():
                if thread.is_alive():
                    thread.join(timeout=1.0)
            self.running_tasks.clear()
            self.task_configs.clear()