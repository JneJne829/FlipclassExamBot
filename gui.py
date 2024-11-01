import sys
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, 
                            QPushButton, QTextEdit, QProgressBar, QMessageBox, 
                            QGroupBox, QFormLayout)
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QFont, QIcon
from FlipclassExamBot import FlipclassExamBot

class ExamWorker(QThread):
    """後台工作執行緒"""
    progress = pyqtSignal(str, str)  # 訊息, 級別
    finished = pyqtSignal(bool)      # 成功/失敗

    def __init__(self, account, password, course_id, answer_time, target_score):
        super().__init__()
        self.account = account
        self.password = password
        self.course_id = course_id
        self.answer_time = answer_time
        self.target_score = target_score

    def run(self):
        bot = FlipclassExamBot(
            self.account, 
            self.password, 
            self.course_id,
            self.answer_time,
            self.target_score,
            print_callback=lambda msg, level: self.progress.emit(msg, level)
        )
        success = bot.run()
        self.finished.emit(success)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.worker = None

    def initUI(self):
        self.setWindowTitle('FlipClass 考試小幫手')
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)

        # 主要容器
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 輸入區域
        input_group = QGroupBox("考試設定")
        input_layout = QFormLayout()

        # 帳號輸入
        self.account_input = QLineEdit()
        self.account_input.setMaxLength(8)
        input_layout.addRow("帳號:", self.account_input)

        # 密碼輸入
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        input_layout.addRow("密碼:", self.password_input)

        # 課程ID輸入
        self.course_id_input = QLineEdit()
        input_layout.addRow("課程ID:", self.course_id_input)

        # 目標分數輸入
        self.target_score_input = QSpinBox()
        self.target_score_input.setRange(0, 100)
        self.target_score_input.setValue(60)
        input_layout.addRow("目標分數:", self.target_score_input)

        # 作答時間輸入
        self.answer_time_input = QDoubleSpinBox()
        self.answer_time_input.setRange(0.1, 60.0)
        self.answer_time_input.setValue(1.0)
        self.answer_time_input.setSingleStep(0.5)
        input_layout.addRow("作答時間(分鐘):", self.answer_time_input)

        input_group.setLayout(input_layout)
        layout.addWidget(input_group)

        # 按鈕區域
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton('開始執行')
        self.start_button.clicked.connect(self.start_exam)
        self.start_button.setMinimumHeight(40)
        
        self.stop_button = QPushButton('停止')
        self.stop_button.clicked.connect(self.stop_exam)
        self.stop_button.setEnabled(False)
        self.stop_button.setMinimumHeight(40)
        
        button_layout.addWidget(self.start_button)
        button_layout.addWidget(self.stop_button)
        layout.addLayout(button_layout)

        # 進度條
        self.progress_bar = QProgressBar()
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # 日誌顯示區域
        log_group = QGroupBox("執行日誌")
        log_layout = QVBoxLayout()
        
        self.log_display = QTextEdit()
        self.log_display.setReadOnly(True)
        log_layout.addWidget(self.log_display)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)

        # 設置樣式
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 3px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
            QLineEdit, QSpinBox, QDoubleSpinBox {
                padding: 5px;
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
            QTextEdit {
                border: 1px solid #cccccc;
                border-radius: 3px;
            }
        """)

    def append_log(self, message, level):
        """添加日誌到顯示區域"""
        color_map = {
            'ERROR': '#FF0000',
            'WARNING': '#FFA500',
            'SUCCESS': '#008000',
            'INFO': '#000000',
            'DEBUG': '#808080'
        }
        color = color_map.get(level, '#000000')
        self.log_display.append(f'<span style="color: {color}">{message}</span>')

    def validate_inputs(self):
        """驗證輸入內容"""
        if len(self.account_input.text()) != 8:
            QMessageBox.warning(self, '輸入錯誤', '帳號必須為8個字元！')
            return False
            
        if not self.password_input.text():
            QMessageBox.warning(self, '輸入錯誤', '請輸入密碼！')
            return False
            
        if not self.course_id_input.text():
            QMessageBox.warning(self, '輸入錯誤', '請輸入課程ID！')
            return False
            
        return True

    def start_exam(self):
        """開始執行考試"""
        if not self.validate_inputs():
            return

        self.log_display.clear()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setMaximum(0)  # 顯示忙碌狀態

        self.worker = ExamWorker(
            self.account_input.text(),
            self.password_input.text(),
            self.course_id_input.text(),
            self.answer_time_input.value(),
            self.target_score_input.value()
        )
        self.worker.progress.connect(self.append_log)
        self.worker.finished.connect(self.exam_finished)
        self.worker.start()

    def stop_exam(self):
        """停止執行"""
        if self.worker and self.worker.isRunning():
            reply = QMessageBox.question(
                self, '確認停止', 
                '確定要停止當前執行的考試嗎？',
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                self.worker.terminate()
                self.worker.wait()
                self.exam_finished(False)
                self.append_log("使用者手動停止執行", "WARNING")

    def exam_finished(self, success):
        """考試完成處理"""
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(100 if success else 0)
        
        if success:
            QMessageBox.information(self, '完成', '考試已完成！')
        else:
            QMessageBox.warning(self, '錯誤', '考試執行過程中出現錯誤，請查看日誌了解詳情。')

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main()