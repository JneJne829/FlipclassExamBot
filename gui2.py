import sys
import json
from datetime import datetime
from typing import Dict, Optional
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QMessageBox, QFileDialog, QSpinBox, QDoubleSpinBox, QTabWidget,
    QTextEdit, QHeaderView
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject

from task_types import TaskConfig, TaskStatus
from task_executor import TaskExecutor
from functools import partial

class EditableTableItem(QTableWidgetItem):
    def __init__(self, text: str, editable: bool = True):
        super().__init__(text)
        if not editable:
            self.setFlags(self.flags() & ~Qt.ItemFlag.ItemIsEditable)

class LogSignals(QObject):
    new_log = pyqtSignal(str, str, str)  # account, message, level

class CustomLogger:
    def __init__(self, signals: LogSignals, account: str):
        self.signals = signals
        self.account = account

    def log(self, message: str, level: str = "INFO"):
        self.signals.new_log.emit(self.account, message, level)

class TaskLogTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

    def append_log(self, message: str, level: str):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        color = {
            "INFO": "black",
            "SUCCESS": "green",
            "WARNING": "orange",
            "ERROR": "red",
            "DEBUG": "gray"
        }.get(level, "black")
        
        self.log_text.append(
            f'<span style="color: {color}">[{timestamp}] [{level}] {message}</span>'
        )
        
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )

class FlipclassGUI(QMainWindow):
    status_changed = pyqtSignal(int, str)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flipclass Exam Bot Manager")
        self.setMinimumSize(800, 600)
        
        self.log_signals = LogSignals()
        self.log_signals.new_log.connect(self.handle_new_log)
        self.status_changed.connect(self.update_task_status_and_button)
        
        self.task_logs: Dict[str, TaskLogTab] = {}
        self.task_executor = TaskExecutor(self.status_changed.emit)
        
        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        
        # 左側控制面板
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        
        # 任務輸入區域
        input_group = self.create_input_group()
        control_layout.addWidget(input_group)
        
        # 控制按鈕
        button_layout = QHBoxLayout()
        self.add_task_btn = QPushButton("添加任務")
        self.import_btn = QPushButton("導入JSON")
        
        self.add_task_btn.clicked.connect(self.add_task)
        self.import_btn.clicked.connect(self.import_json)
        
        button_layout.addWidget(self.add_task_btn)
        button_layout.addWidget(self.import_btn)
        control_layout.addLayout(button_layout)
        
        control_panel.setMaximumWidth(300)
        main_layout.addWidget(control_panel)
        
        # 右側標籤頁
        self.tab_widget = QTabWidget()
        
        # 任務列表標籤頁
        self.task_table = self.create_task_table()
        self.tab_widget.addTab(self.task_table, "任務列表")
        
        main_layout.addWidget(self.tab_widget)

    def create_input_group(self) -> QWidget:
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        self.account_input = QLineEdit()
        self.account_input.setPlaceholderText("帳號 (8個字元)")
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("密碼")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        
        self.course_id_input = QLineEdit()
        self.course_id_input.setPlaceholderText("課程ID")
        
        self.target_score_input = QSpinBox()
        self.target_score_input.setRange(0, 100)
        self.target_score_input.setValue(60)
        self.target_score_input.setPrefix("目標分數: ")
        self.target_score_input.setSuffix(" 分")
        
        self.answer_time_input = QDoubleSpinBox()
        self.answer_time_input.setRange(0.1, 120)
        self.answer_time_input.setValue(1.0)
        self.answer_time_input.setPrefix("作答時間: ")
        self.answer_time_input.setSuffix(" 分鐘")
        
        layout.addWidget(self.account_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.course_id_input)
        layout.addWidget(self.target_score_input)
        layout.addWidget(self.answer_time_input)
        
        return widget

    def create_task_table(self) -> QTableWidget:
        table = QTableWidget()
        table.setColumnCount(8)
        table.setHorizontalHeaderLabels(["帳號", "課程ID", "目標分數", "作答時間", "狀態", "日誌", "操作", "刪除"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        table.itemChanged.connect(self.handle_cell_changed)
        return table

    def handle_cell_changed(self, item: QTableWidgetItem):
        row = item.row()
        col = item.column()
        new_value = item.text().strip()
        
        config = self.task_executor.get_task_config(row)
        if not config:
            return
            
        try:
            if col == 0:  # 帳號
                if len(new_value) != 8:
                    QMessageBox.warning(self, "錯誤", "帳號必須為8個字元")
                    item.setText(config.account)
                    return
                if self.task_executor.update_task_config(row, account=new_value):
                    self.update_log_tab_title(config.account, new_value)
                    
            elif col == 1:  # 課程ID
                self.task_executor.update_task_config(row, course_id=new_value)
                
            elif col == 2:  # 目標分數
                try:
                    score = float(new_value.replace('分', ''))
                    if 0 <= score <= 100:
                        self.task_executor.update_task_config(row, target_score=score)
                        item.setText(f"{score}分")
                    else:
                        raise ValueError
                except ValueError:
                    QMessageBox.warning(self, "錯誤", "目標分數必須在0-100之間")
                    item.setText(f"{config.target_score}分")
                    
            elif col == 3:  # 作答時間
                try:
                    time = float(new_value.replace('分鐘', ''))
                    if time > 0:
                        self.task_executor.update_task_config(row, answer_time=time)
                        item.setText(f"{time}分鐘")
                    else:
                        raise ValueError
                except ValueError:
                    QMessageBox.warning(self, "錯誤", "作答時間必須大於0")
                    item.setText(f"{config.answer_time}分鐘")
                    
        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"更新失敗: {str(e)}")
            self.refresh_table_row(row)

    def update_log_tab_title(self, old_account: str, new_account: str):
        """更新日誌標籤頁的標題"""
        if old_account in self.task_logs:
            log_tab = self.task_logs.pop(old_account)
            self.task_logs[new_account] = log_tab
            
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == f"日誌-{old_account}":
                    self.tab_widget.setTabText(i, f"日誌-{new_account}")
                    break

    def refresh_table_row(self, row: int):
        """刷新表格行的顯示"""
        config = self.task_executor.get_task_config(row)
        if config:
            self.task_table.item(row, 0).setText(config.account)
            self.task_table.item(row, 1).setText(config.course_id)
            self.task_table.item(row, 2).setText(f"{config.target_score}分")
            self.task_table.item(row, 3).setText(f"{config.answer_time}分鐘")

    def add_task_log_tab(self, account: str) -> CustomLogger:
        """添加任務日誌標籤頁並返回日誌器"""
        log_tab = TaskLogTab()
        self.task_logs[account] = log_tab
        self.tab_widget.addTab(log_tab, f"日誌-{account}")
        
        logger = CustomLogger(self.log_signals, account)
        return logger

    def handle_new_log(self, account: str, message: str, level: str):
        """處理新的日誌消息"""
        if account in self.task_logs:
            self.task_logs[account].append_log(message, level)

    def update_task_status_and_button(self, row: int, status: str):
        """更新任務狀態和按鈕狀態"""
        if self.task_table.rowCount() <= row:
            return
            
        status_item = self.task_table.item(row, 4)
        execute_btn = self.task_table.cellWidget(row, 6)
        
        if not status_item or not execute_btn:
            return
            
        status_item.setText(status)
        
        # 根據狀態設置顏色和按鈕
        if status == TaskStatus.WAITING:
            status_item.setForeground(Qt.GlobalColor.black)
            execute_btn.setEnabled(True)
            execute_btn.setText("執行")
            execute_btn.setToolTip("點擊執行任務")
            
        elif status == TaskStatus.RUNNING:
            status_item.setForeground(Qt.GlobalColor.blue)
            execute_btn.setEnabled(False)
            execute_btn.setText("執行中")
            execute_btn.setToolTip("任務正在執行中")
            
        elif status == TaskStatus.COMPLETED:
            status_item.setForeground(Qt.GlobalColor.green)
            execute_btn.setEnabled(True)
            execute_btn.setText("重新執行")
            execute_btn.setToolTip("點擊重新執行任務")
            
        elif status == TaskStatus.FAILED:
            status_item.setForeground(Qt.GlobalColor.red)
            execute_btn.setEnabled(True)
            execute_btn.setText("重試")
            execute_btn.setToolTip("點擊重試")

    def execute_task(self, row: int, config: TaskConfig):
        """執行單個任務"""
        try:
            # 檢查行是否存在
            if row >= self.task_table.rowCount():
                return
                
            # 安全地獲取狀態
            status_item = self.task_table.item(row, 4)
            if status_item is None:
                return
                
            current_status = status_item.text()
            if current_status == TaskStatus.RUNNING:
                return
            
            self.task_executor.add_task(row, config)
            self.task_executor.execute_task(row)
        except Exception as e:
            QMessageBox.warning(
                self,
                "錯誤",
                f"執行任務時發生錯誤: {str(e)}"
            )

    def add_task_with_buttons(self, row: int, config: TaskConfig):
        """添加任務及其按鈕"""
        try:
            # 添加日誌按鈕
            log_btn = QPushButton("查看日誌")
            log_btn.clicked.connect(partial(self.show_task_log, config.account))
            self.task_table.setCellWidget(row, 5, log_btn)

            # 添加執行按鈕
            execute_btn = QPushButton("執行")
            execute_btn.clicked.connect(partial(self.execute_task, row, config))
            self.task_table.setCellWidget(row, 6, execute_btn)

            # 添加刪除按鈕
            delete_btn = QPushButton("刪除")
            delete_btn.clicked.connect(partial(self.delete_task, row))
            self.task_table.setCellWidget(row, 7, delete_btn)

        except Exception as e:
            print(f"添加任務按鈕時發生錯誤: {str(e)}")


    def add_task(self):
        """添加新任務"""
        account = self.account_input.text().strip()
        password = self.password_input.text().strip()
        course_id = self.course_id_input.text().strip()
        target_score = self.target_score_input.value()
        answer_time = self.answer_time_input.value()
        
        if not all([account, password, course_id]):
            QMessageBox.warning(self, "錯誤", "請填寫所有必要欄位")
            return
            
        if len(account) != 8:
            QMessageBox.warning(self, "錯誤", "帳號必須為8個字元")
            return
        
        # 創建任務專屬的日誌器
        logger = self.add_task_log_tab(account)
        
        config = TaskConfig(
            account=account,
            password=password,
            course_id=course_id,
            target_score=target_score,
            answer_time=answer_time,
            print_callback=logger.log
        )
        
        # 更新表格
        row = self.task_table.rowCount()
        self.task_table.insertRow(row)
        
        self.task_table.setItem(row, 0, EditableTableItem(account))
        self.task_table.setItem(row, 1, EditableTableItem(course_id))
        self.task_table.setItem(row, 2, EditableTableItem(f"{target_score}分"))
        self.task_table.setItem(row, 3, EditableTableItem(f"{answer_time}分鐘"))
        self.task_table.setItem(row, 4, EditableTableItem(TaskStatus.WAITING, editable=False))
        
        # 添加按鈕
        self.add_task_with_buttons(row, config)
        
        # 保存任務配置
        self.task_executor.add_task(row, config)
        
        # 清空輸入欄位
        self.account_input.clear()
        self.password_input.clear()
        self.course_id_input.clear()
        
        logger.log("任務已添加", "INFO")

    def delete_task(self, row: int):
        """刪除指定行的任務"""
        try:
            current_row = row
            if current_row < 0 or current_row >= self.task_table.rowCount():
                return

            config = self.task_executor.get_task_config(current_row)
            if not config:
                QMessageBox.warning(self, "錯誤", f"找不到行 {current_row} 的任務配置")
                return

            if self.task_executor.is_task_running(config.account):
                QMessageBox.warning(self, "錯誤", "無法刪除正在執行的任務")
                return

            # 顯示確認對話框
            reply = QMessageBox.question(
                self, 
                "確認刪除", 
                f"確定要刪除帳號 {config.account} 的任務嗎？",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )

            if reply == QMessageBox.StandardButton.Yes:
                account = config.account

                # 從任務執行器中移除任務
                if not self.task_executor.remove_task(current_row):
                    QMessageBox.warning(self, "錯誤", "無法從任務執行器中移除任務")
                    return

                # 刪除日誌標籤頁
                for i in range(self.tab_widget.count() - 1, -1, -1):  # 從後往前遍歷
                    if self.tab_widget.tabText(i) == f"日誌-{account}":
                        self.tab_widget.removeTab(i)
                        break

                # 清理日誌
                if account in self.task_logs:
                    del self.task_logs[account]

                # 從表格中移除行
                self.task_table.removeRow(current_row)

                # 更新剩餘行的按鈕
                self.update_task_buttons()

        except Exception as e:
            QMessageBox.warning(
                self,
                "錯誤",
                f"刪除任務時發生錯誤: {str(e)}"
            )

    def update_task_buttons(self):
        """更新所有任務的按鈕"""
        try:
            for row in range(self.task_table.rowCount()):
                config = self.task_executor.get_task_config(row)
                if config:
                    # 清除現有的按鈕
                    for col in [5, 6, 7]:
                        widget = self.task_table.cellWidget(row, col)
                        if widget:
                            widget.deleteLater()

                    # 重新添加按鈕
                    self.add_task_with_buttons(row, config)

        except Exception as e:
            print(f"更新任務按鈕時發生錯誤: {str(e)}")


    def rebind_row_buttons(self):
        """重新綁定所有行的按鈕事件"""
        for row in range(self.task_table.rowCount()):
            config = self.task_executor.get_task_config(row)
            if config:
                # 重新綁定日誌按鈕
                log_btn = self.task_table.cellWidget(row, 5)
                if log_btn:
                    log_btn.clicked.disconnect()
                    log_btn.clicked.connect(partial(self.show_task_log, config.account))
                
                # 重新綁定執行按鈕
                execute_btn = self.task_table.cellWidget(row, 6)
                if execute_btn:
                    execute_btn.clicked.disconnect()
                    execute_btn.clicked.connect(partial(self.execute_task, row, config))
                
                # 重新綁定刪除按鈕
                delete_btn = self.task_table.cellWidget(row, 7)
                if delete_btn:
                    delete_btn.clicked.disconnect()
                    delete_btn.clicked.connect(partial(self.delete_task, row))

    def update_task_indices(self, deleted_row: int):
        """更新刪除任務後的索引"""
        try:
            # 獲取當前的行數
            row_count = self.task_table.rowCount()
            
            # 遍歷剩餘的行
            for row in range(deleted_row, row_count):
                # 更新執行按鈕
                execute_btn = self.task_table.cellWidget(row, 6)
                if execute_btn:
                    config = self.task_executor.get_task_config(row)
                    if config:
                        try:
                            execute_btn.clicked.disconnect()
                        except TypeError:
                            pass  # 忽略如果沒有連接的情況
                        execute_btn.clicked.connect(
                            lambda checked, r=row, c=config: self.execute_task(r, c)
                        )

                # 更新刪除按鈕
                delete_btn = self.task_table.cellWidget(row, 7)
                if delete_btn:
                    try:
                        delete_btn.clicked.disconnect()
                    except TypeError:
                        pass  # 忽略如果沒有連接的情況
                    delete_btn.clicked.connect(
                        lambda checked, r=row: self.delete_task(r)
                    )
        except Exception as e:
            print(f"更新任務索引時發生錯誤: {str(e)}")

    def show_task_log(self, account: str):
        """查看指定帳號的任務日誌"""
        if not isinstance(account, str):
            QMessageBox.warning(self, "錯誤", f"無效的帳號格式")
            return
            
        tab_name = f"日誌-{account}"
        
        if account not in self.task_logs:
            QMessageBox.warning(self, "錯誤", f"找不到帳號 {account} 的日誌頁面")
            return
        
        # 查找並切換到對應的標籤頁
        for i in range(self.tab_widget.count()):
            if self.tab_widget.tabText(i) == tab_name:
                self.tab_widget.setCurrentIndex(i)
                log_tab = self.task_logs[account]
                log_tab.log_text.verticalScrollBar().setValue(
                    log_tab.log_text.verticalScrollBar().maximum()
                )
                return
                
        QMessageBox.warning(self, "錯誤", f"找不到帳號 {account} 的日誌標籤頁")

    def import_json(self):
        """從JSON文件導入任務配置"""
        file_name, _ = QFileDialog.getOpenFileName(
            self, "選擇JSON文件", "", "JSON Files (*.json)"
        )
        
        if not file_name:
            return
            
        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                configs = json.load(f)
                
            for config_dict in configs:
                account = config_dict['account']
                logger = self.add_task_log_tab(account)
                
                config_dict['print_callback'] = logger.log
                config = TaskConfig(**config_dict)
                
                row = self.task_table.rowCount()
                self.task_table.insertRow(row)
                
                self.task_table.setItem(row, 0, EditableTableItem(config.account))
                self.task_table.setItem(row, 1, EditableTableItem(config.course_id))
                self.task_table.setItem(row, 2, EditableTableItem(f"{config.target_score}分"))
                self.task_table.setItem(row, 3, EditableTableItem(f"{config.answer_time}分鐘"))
                self.task_table.setItem(row, 4, EditableTableItem(TaskStatus.WAITING, editable=False))
                
                # 使用新的方法添加按鈕
                self.add_task_with_buttons(row, config)
                
                # 保存任務配置
                self.task_executor.add_task(row, config)
                
                logger.log("任務已通過JSON導入", "INFO")
                
            QMessageBox.information(self, "成功", f"已導入 {len(configs)} 個任務")
        except Exception as e:
            QMessageBox.warning(self, "錯誤", f"導入失敗: {str(e)}")


    def closeEvent(self, event):
        """關閉程序時確保所有線程都已終止"""
        self.task_executor.cleanup()
        event.accept()

def main():
    app = QApplication(sys.argv)
    
    # 設置應用程序樣式
    app.setStyle('Fusion')
    
    # 創建並顯示主窗口
    window = FlipclassGUI()
    window.show()
    
    # 執行應用程序
    sys.exit(app.exec())

if __name__ == "__main__":
    main()