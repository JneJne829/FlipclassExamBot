import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException  # 添加這個導入
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
import os
import json
import traceback

class FlipclassExamBot:
    def __init__(self, account, password, course_id, answer_time, target_score, print_callback=None):
        self.account = account
        self.password = password
        self.course_id = course_id
        self.answer_time = float(answer_time)
        self.target_score = target_score
        self.driver = None
        self.wait = None
        self.answer_page_url = None
        self.exam_page_url = None
        self.print_callback = print_callback

    def print_message(self, message, level='INFO'):
        """統一的消息輸出函數"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        formatted_message = f"[{level.upper()}] {message}"
        if self.print_callback:
            self.print_callback(message, level)  # 直接傳遞原始消息和級別
        else:
            print(formatted_message)

    def setup_browser(self):
        try:
            self.print_message("開始設置瀏覽器...", "DEBUG")
            options = Options()
            options.add_argument("--headless")
            options.add_argument("--disable-blink-features=AutomationControlled")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            
            service = Service(log_path=os.devnull)
            self.driver = webdriver.Chrome(service=service, options=options)
            self.wait = WebDriverWait(self.driver, 20)
            self.print_message("瀏覽器設置完成", "SUCCESS")
        except Exception as e:
            self.print_message(f"設置瀏覽器時發生錯誤: {str(e)}", "ERROR")
            raise

    def login(self):
        self.print_message("開始登入程序", "INFO")
        self.driver.get("https://flipclass.stust.edu.tw/")
        try:
            self.print_message("等待登入頁面加載...", "DEBUG")
            account_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "account")))
            account_input.clear()
            account_input.send_keys(self.account)
            self.print_message(f"已輸入帳號: {self.account}", "DEBUG")

            password_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "password")))
            password_input.clear()
            password_input.send_keys(self.password)
            self.print_message("已輸入密碼", "DEBUG")

            login_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@type='submit' and @data-role='form-submit']")
            ))
            login_button.click()
            self.print_message("已點擊登入按鈕", "DEBUG")

            # 創建一個3秒的短等待時間
            short_wait = WebDriverWait(self.driver, 3)

            try:
                # 優先檢查保持登入按鈕
                keep_login_button = short_wait.until(
                    EC.element_to_be_clickable((By.CLASS_NAME, "keepLoginBtn"))
                )
                self.handle_keep_login()
                self.wait.until(EC.visibility_of_element_located(
                    (By.XPATH, "//div[@class='caption underline' and text()='最近事件']")
                ))
                self.print_message("登入成功！", "SUCCESS")
                return True
            except TimeoutException:
                # 如果沒有找到保持登入按鈕，檢查是否有錯誤訊息
                try:
                    error_message = short_wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "fs-form-message"))
                    )
                    if error_message.is_displayed():
                        self.print_message("登入失敗：檢測到錯誤訊息", "ERROR")
                        return False
                except TimeoutException:
                    self.print_message("登入失敗：未能檢測到登入狀態", "ERROR")
                    return False

        except Exception as e:
            self.print_message(f"登入過程中發生錯誤: {str(e)}", "ERROR")
            return False

    def handle_keep_login(self):
        try:
            keep_login_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "keepLoginBtn")))
            keep_login_button.click()
            self.print_message("已選擇保持登入", "SUCCESS")
        except:
            self.print_message("未檢測到保持登入提示", "DEBUG")

    def navigate_to_course(self):
        course_url = f"https://flipclass.stust.edu.tw/course/exam/{self.course_id}"
        self.print_message(f"正在導航到課程頁面: {course_url}", "INFO")
        self.driver.get(course_url)
        self.print_message("已進入課程頁面", "SUCCESS")

        keep_focus_script = "window.onblur = function() { window.focus(); };"
        self.driver.execute_script(keep_focus_script)
        self.print_message("已注入防切窗腳本", "DEBUG")

    def modify_url(self, url):
        url_parts = urlparse(url)
        query_params = parse_qs(url_parts.query)
        query_params = {key: query_params[key] for key in query_params if key in ['key', 'title']}
        query_params['mode'] = 'view'
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((url_parts.scheme, url_parts.netloc, url_parts.path, url_parts.params, new_query, url_parts.fragment))

    def extract_exam_and_answer_urls(self):
        try:
            self.print_message("開始提取考試和答案頁面URL", "INFO")
            element = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//a[span[text()='開始測驗' or text()='繼續測驗']]")
            ))
            href = element.get_attribute('href')
            self.exam_page_url = urljoin(self.driver.current_url, href)
            self.print_message(f"已獲取考試頁面URL", "DEBUG")

            self.answer_page_url = self.modify_url(self.exam_page_url)
            self.print_message(f"已生成答案頁面", "DEBUG")
            return True
        except Exception as e:
            self.print_message(f"提取URL時發生錯誤: {str(e)}", "ERROR")
            return False

    def load_exam_page(self):
        if self.exam_page_url:
            self.print_message("正在加載考試頁面...", "INFO")
            self.driver.get(self.exam_page_url)
            
            # 等待考試頁面關鍵元素加載完成
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kques-item")))
                
                # 注入防切窗腳本
                keep_focus_script = """
                window.onblur = function() { 
                    window.focus(); 
                    return true;
                };
                window.onfocus = function() {
                    return true;
                };
                // 攔截 visibilitychange 事件
                document.addEventListener('visibilitychange', function(e) {
                    e.preventDefault();
                    document.hidden = false;
                    return true;
                });
                // 確保窗口始終保持焦點
                setInterval(function() {
                    window.focus();
                }, 100);
                """
                self.driver.execute_script(keep_focus_script)
                self.print_message("已注入防切窗腳本", "DEBUG")
                
                # 驗證腳本是否成功注入
                validation_result = self.driver.execute_script("""
                    return {
                        hasOnBlur: typeof window.onblur === 'function',
                        hasOnFocus: typeof window.onfocus === 'function'
                    };
                """)
                
                if validation_result['hasOnBlur'] and validation_result['hasOnFocus']:
                    self.print_message("防切窗腳本驗證成功", "SUCCESS")
                else:
                    self.print_message("防切窗腳本可能未正確注入", "WARNING")
                
                self.print_message("已成功加載考試頁面", "SUCCESS")
                
            except Exception as e:
                self.print_message(f"加載考試頁面時發生錯誤: {str(e)}", "ERROR")
                raise
                
        else:
            self.print_message("無法加載考試頁面：URL未定義", "ERROR")

    def extract_answers(self):
        try:
            self.print_message("開始提取答案...", "INFO")
            js_file_path = "extract_answers.js"
            with open(js_file_path, "r", encoding="utf-8") as js_file:
                js_script = js_file.read()
                result = self.driver.execute_script(js_script)
                if result:
                    self.print_message("答案提取成功", "SUCCESS")
                else:
                    self.print_message("未能提取到答案", "WARNING")
                return result
        except Exception as e:
            self.print_message(f"提取答案時發生錯誤: {str(e)}", "ERROR")
            return None

    def wait_before_submit(self):
        total_seconds = round(self.answer_time * 60)
        self.print_message(f"開始等待作答時間: {self.answer_time:.1f}分鐘", "INFO")
        
        for remaining in range(total_seconds, 0, -5):
            minutes = remaining // 60
            seconds = remaining % 60
            
            if remaining < 60:
                time_str = f"剩餘時間: {seconds}秒"
            else:
                time_str = f"剩餘時間: {minutes:02d}分{seconds:02d}秒"
            
            if remaining <= 30:
                time_str += " (即將結束!)"
                level = "WARNING"
            else:
                level = "INFO"
            
            self.print_message(time_str, level)
            time.sleep(min(5, remaining))
        
        self.print_message("作答時間結束，準備提交...", "INFO")

    def fill_answers_and_submit(self, answers):
        try:
            self.print_message("開始填充答案...", "INFO")
            js_file_path = "fill_answers.js"
            with open(js_file_path, "r", encoding="utf-8") as js_file:
                fill_script = js_file.read()

            self.driver.execute_script(fill_script, answers, self.target_score)
            self.print_message(f"答案填充完成，目標分數：{self.target_score}", "SUCCESS")

            self.wait_before_submit()

            self.print_message("正在點擊提交按鈕...", "INFO")
            submit_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='tool-submit']//button[@role='submit-exam']")
            ))
            submit_button.click()
            self.print_message("已點擊提交按鈕", "SUCCESS")

            confirm_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-bb-handler='confirm' and text()='交卷']")
            ))
            confirm_button.click()
            self.print_message("已確認提交", "SUCCESS")

        except Exception as e:
            self.print_message(f"填充答案或提交時發生錯誤: {str(e)}", "ERROR")
            raise

    def get_score(self):
        try:
            self.print_message("正在獲取分數...", "INFO")
            
            # 等待分數元素出現
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='infobar']//div[@class='score']//span[contains(@class, 'recordScore')]")
            ))
            
            # 查找分數和滿分元素
            score_element = self.driver.find_element(
                By.XPATH, "//div[@class='infobar']//div[@class='score']//span[contains(@class, 'recordScore')]"
            )
            fullmark_element = self.driver.find_element(
                By.XPATH, "//div[@class='infobar']//div[@class='score']//span[@class='fullmark']"
            )

            # 獲取文本內容
            score = score_element.text.strip()
            fullmark = fullmark_element.text.strip()
            
            self.print_message(f"最終得分：{score} {fullmark}", "SUCCESS")
            return score, fullmark
        except Exception as e:
            self.print_message(f"獲取分數時發生錯誤: {str(e)}", "ERROR")
            traceback.print_exc()
            return None, None

    def run(self):
        try:
            self.print_message("開始執行自動化流程", "INFO")
            self.setup_browser()
            
            if not self.login():
                self.print_message("登入失敗，停止執行", "ERROR")
                return False

            self.navigate_to_course()
            
            if not self.extract_exam_and_answer_urls():
                self.print_message("無法提取測驗URL，停止執行", "ERROR")
                return False

            # 進入答案頁面
            self.driver.get(self.answer_page_url)
            self.print_message("已進入答案頁面", "SUCCESS")

            # 等待答案頁面加載
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kques-item")))
            except Exception as e:
                self.print_message("答案頁面加載超時", "ERROR")
                return False

            # 提取答案
            answers = self.extract_answers()
            if not answers:
                self.print_message("未能提取答案，停止執行", "ERROR")
                return False

            # 回到考試頁面
            self.load_exam_page()

            # 等待考試頁面加載
            try:
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kques-item")))
            except Exception as e:
                self.print_message("考試頁面加載超時", "ERROR")
                return False

            # 填充答案並提交
            self.fill_answers_and_submit(answers)

            # 獲取分數
            score, fullmark = self.get_score()
            
            self.print_message("自動化流程執行完成", "SUCCESS")
            return True

        except Exception as e:
            self.print_message(f"執行過程中發生錯誤: {str(e)}", "ERROR")
            traceback.print_exc()
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.print_message("已關閉瀏覽器", "INFO")

def validate_account(account):
    """驗證帳號是否為8個字元"""
    return len(account) == 8

if __name__ == "__main__":
    while True:
        # 帳號驗證部分保持不變
        account = input("請輸入您的帳號 (8個字元): ").strip()
        if not validate_account(account):
            print("錯誤：帳號必須是8個字元！")
            continue
        
        # 密碼輸入部分保持不變
        password = input("請輸入您的密碼: ").strip()
        if not password:
            print("錯誤：密碼不能為空！")
            continue
            
        # 課程ID輸入部分保持不變
        course_id = input("請輸入考試課程ID: ").strip()
        if not course_id:
            print("錯誤：課程ID不能為空！")
            continue

        # 新增期望分數輸入
        while True:
            try:
                target_score = input("請輸入期望分數 (0-100): ").strip()
                target_score = float(target_score)
                if target_score < 0 or target_score > 100:
                    print("錯誤：分數必須在0到100之間！")
                    continue
                target_score = round(target_score)  # 四捨五入到整數
                break
            except ValueError:
                print("錯誤：請輸入有效的數字！")
                continue

        # 作答時間輸入部分保持不變
        while True:
            try:
                answer_time = input("請輸入作答時間(分鐘，支援小數點，例如0.5): ").strip()
                answer_time = float(answer_time)
                if answer_time <= 0:
                    print("錯誤：作答時間必須大於0分鐘！")
                    continue
                break
            except ValueError:
                print("錯誤：請輸入有效的數字！")
                continue

        # 確認資訊顯示
        print("\n=== 請確認您的輸入資訊 ===")
        print(f"帳號: {account}")
        print(f"密碼: {'*' * len(password)}")
        print(f"課程ID: {course_id}")
        print(f"期望分數: {target_score}分")
        print(f"作答時間: {answer_time:.1f}分鐘")
        
        confirm = input("\n確認是否正確？(y/n): ").strip().lower()
        if confirm == 'y':
            break
        print("\n請重新輸入資訊。\n")

    try:
        # 創建並運行自動化實例
        print("\n正在啟動自動化程序...")
        automation = FlipclassExamBot(account, password, course_id, answer_time, target_score)
        automation.run()
    except Exception as e:
        print(f"程序執行時發生錯誤: {e}")
        input("按Enter鍵結束程序...")