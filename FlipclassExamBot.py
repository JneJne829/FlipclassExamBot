import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse, urljoin
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import json


class FlipclassExamBot:
    def __init__(self, account, password, course_id, answer_time, target_score):
        self.account = account
        self.password = password
        self.course_id = course_id
        self.answer_time = float(answer_time)
        self.target_score = target_score
        self.driver = None
        self.wait = None
        self.answer_page_url = None  # 保存答案頁面的 URL
        self.exam_page_url = None    # 保存考試頁面的 URL

    def setup_browser(self):
        # 設定 Chrome 瀏覽器選項（無頭模式和隱藏特徵）
        options = Options()
        #options.add_argument("profile-directory=Default")
        options.add_argument("--headless")  # 啟用無頭模式
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # 如果需要偽裝用戶代理，可以取消下面的註解並設置適當的用戶代理
        # options.add_argument("user-agent=您的用戶代理字串")
        service = Service(log_path=os.devnull)
        self.driver = webdriver.Chrome(service=service, options=options)
        self.wait = WebDriverWait(self.driver, 20)

    def login(self):
        # 打開登入頁面並進行登入操作
        self.driver.get("https://flipclass.stust.edu.tw/")
        try:
            # 定位帳號和密碼輸入框，並輸入用戶信息
            account_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "account")))
            account_input.clear()
            account_input.send_keys(self.account)

            password_input = self.wait.until(EC.visibility_of_element_located((By.NAME, "password")))
            password_input.clear()
            password_input.send_keys(self.password)

            # 點擊登入按鈕
            login_button = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and @data-role='form-submit']")))
            login_button.click()

            # 檢查是否出現“保持登入”提示
            self.handle_keep_login()

            # 等待登入成功
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='caption underline' and text()='最近事件']")
            ))
            print("登入成功！")
            return True
        except Exception as e:
            print("登入時發生錯誤:", e)
            return False

    def handle_keep_login(self):
        # 檢查是否出現帳號已在其他位置登入的提示
        try:
            keep_login_button = self.wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "keepLoginBtn")))
            keep_login_button.click()
            print("選擇保持登入。")
        except:
            print("未檢測到保持登入提示。")

    def navigate_to_course(self):
        # 導航到指定課程頁面
        course_url = f"https://flipclass.stust.edu.tw/course/exam/{self.course_id}"
        self.driver.get(course_url)
        print(f"已進入課程頁面：{course_url}")

        # 注入防切窗的保持焦點 JavaScript
        keep_focus_script = "window.onblur = function() { window.focus(); };"
        self.driver.execute_script(keep_focus_script)

    def extract_exam_and_answer_urls(self):
        try:
            # 提取“開始測驗”或“繼續測驗”按鈕的 URL
            element = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//a[span[text()='開始測驗' or text()='繼續測驗']]")))
            href = element.get_attribute('href')
            self.exam_page_url = urljoin(self.driver.current_url, href)  # 將考試頁面設為 exam_page_url
            print("考試按鈕鏈接（原始）：", self.exam_page_url)

            # 獲取答案頁面 URL
            self.answer_page_url = self.modify_url(self.exam_page_url)
            print("答案頁面鏈接：", self.answer_page_url)
            return True
        except Exception as e:
            print("提取考試和答案 URL 時發生錯誤:", e)
            return False

    def modify_url(self, url):
        # 解析並修改鏈接
        url_parts = urlparse(url)
        query_params = parse_qs(url_parts.query)

        # 保留 'key' 和 'title' 參數，刪除其他參數，並添加 'mode=view'
        query_params = {key: query_params[key] for key in query_params if key in ['key', 'title']}
        query_params['mode'] = 'view'

        # 重組 URL
        new_query = urlencode(query_params, doseq=True)
        return urlunparse((url_parts.scheme, url_parts.netloc, url_parts.path, url_parts.params, new_query, url_parts.fragment))

    def load_exam_page(self):
        # 回到考試頁面，使用 self.exam_page_url
        if self.exam_page_url:
            self.driver.get(self.exam_page_url)
            print("已返回考試頁面：", self.exam_page_url)
        else:
            print("無法導航到考試頁面，exam_page_url 未定義。")

    def extract_answers(self):
        try:
            # 讀取並執行 extract_answers.js 文件來提取答案
            js_file_path = "E:/JavaScript/Flipclass tool/extract_answers.js"
            with open(js_file_path, "r", encoding="utf-8") as js_file:
                js_script = js_file.read()
                result = self.driver.execute_script(js_script)
                print("提取的答案數據:\n", result)
                return result
        except Exception as e:
            print("提取答案時發生錯誤:", e)
            return None

    def wait_before_submit(self):
        """等待指定的作答時間，每5秒更新一次倒計時"""
        # 將分鐘轉換為秒，使用 round 確保精確度
        total_seconds = round(self.answer_time * 60)
        print(f"\n開始等待作答時間: {self.answer_time:.1f}分鐘")
        
        # 每5秒更新一次倒計時
        for remaining in range(total_seconds, 0, -5):
            minutes = remaining // 60
            seconds = remaining % 60
            
            # 如果剩餘時間小於1分鐘，顯示更詳細的格式
            if remaining < 60:
                time_str = f"\r剩餘時間: {seconds}秒"
            else:
                # 對於超過1分鐘的時間，顯示分和秒
                time_str = f"\r剩餘時間: {minutes:02d}分{seconds:02d}秒"
            
            # 在最後30秒時添加提醒
            if remaining <= 30:
                time_str += " (即將結束!)"
            
            print(time_str, end='', flush=True)
            time.sleep(min(5, remaining))  # 確保最後一次等待不會超過剩餘時間
            
        print("\n作答時間結束，準備提交...")

    def fill_answers_and_submit(self, answers):
        try:
            # 使用實例變量 self.target_score
            js_file_path = "E:/JavaScript/Flipclass tool/fill_answers.js"
            with open(js_file_path, "r", encoding="utf-8") as js_file:
                fill_script = js_file.read()

            # 使用實例的目標分數
            self.driver.execute_script(fill_script, answers, self.target_score)
            print(f"所有答案已成功填充！目標分數：{self.target_score}")

            # 等待指定的作答時間
            self.wait_before_submit()

            # 點擊"交卷"按鈕
            submit_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//div[@class='tool-submit']//button[@role='submit-exam']")
            ))
            submit_button.click()
            print("已點擊交卷按鈕。")

            # 處理彈出的確認交卷對話框
            confirm_button = self.wait.until(EC.element_to_be_clickable(
                (By.XPATH, "//button[@data-bb-handler='confirm' and text()='交卷']")
            ))
            confirm_button.click()
            print("已確認交卷。")

        except Exception as e:
            print("填充答案或交卷時發生錯誤:", e)



    def get_score(self):
        try:
            # 等待分数元素出现
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='infobar']//div[@class='score']//span[contains(@class, 'recordScore')]")
            ))
            # 查找分数和满分元素
            score_element = self.driver.find_element(
                By.XPATH, "//div[@class='infobar']//div[@class='score']//span[contains(@class, 'recordScore')]"
            )
            fullmark_element = self.driver.find_element(
                By.XPATH, "//div[@class='infobar']//div[@class='score']//span[@class='fullmark']"
            )

            # 获取文本内容
            score = score_element.text.strip()
            fullmark = fullmark_element.text.strip()
            print(f"您的得分是: {score} {fullmark}")
        except Exception as e:
            print("提取分数时发生错误:", e)
            import traceback
            traceback.print_exc()

    def run(self):
        self.setup_browser()
        if not self.login():
            print("登入失败，停止执行。")
            self.driver.quit()
            return

        self.navigate_to_course()
        if not self.extract_exam_and_answer_urls():
            print("无法提取测验或答案页面 URL。")
            self.driver.quit()
            return

        # 进入答案页面
        self.driver.get(self.answer_page_url)
        print("已进入答案页面：", self.answer_page_url)

        # 等待答案页面加载完成
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kques-item")))
        except Exception as e:
            print("答案页面加载超时:", e)
            self.driver.quit()
            return

        # 提取答案
        answers = self.extract_answers()

        # 回到考试页面
        self.load_exam_page()

        # 等待考试页面加载完成
        try:
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "kques-item")))
        except Exception as e:
            print("考试页面加载超时:", e)
            self.driver.quit()
            return

        # 填充答案并提交
        if answers:
            self.fill_answers_and_submit(answers)
        else:
            print("未能提取答案，请检查错误。")
            self.driver.quit()
            return

        # 等待提交后页面加载完成
        try:
            # 等待包含分数的元素出现
            self.wait.until(EC.visibility_of_element_located(
                (By.XPATH, "//div[@class='infobar']")
            ))
            # 提取并显示分数
            self.get_score()
        except Exception as e:
            print("分数页面加载超时或提取分数时发生错误:", e)
            import traceback
            traceback.print_exc()

        # 自动结束浏览器
        self.driver.quit()

    def keep_browser_open(self):
        # 保持瀏覽器打開（如果需要）
        try:
            while True:
                time.sleep(10)
        except KeyboardInterrupt:
            print("結束程式。")
            self.driver.quit()

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

'''
# 主程式執行
if __name__ == "__main__":
    account = "4b1g0162"
    password = "MYworldcow03"
    course_id = "26885"
    # 創建並運行自動化實例
    automation = FlipclassExamBot(account, password, course_id)
    automation.run()
    # 如果需要保持瀏覽器打開，取消下面的註解
    # automation.keep_browser_open()'''

