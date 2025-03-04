from playwright.sync_api import sync_playwright
import pyotp
import time
from sqlalchemy.orm import Session
# from app.models.transaction import Transaction

class RazerService:
    def __init__(self, db: Session):
        self.db = db
        self.browser = None
        self.page = None

    def start_browser(self):
        """ 啟動 Playwright 瀏覽器 """
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)  # 測試時可設為 False
        self.page = self.browser.new_page()


    def close_browser(self):
        """ 關閉瀏覽器 """
        self.browser.close()
        self.playwright.stop()

    def select_country(self):
        """ 選擇 Philippines"""
        self.page.goto("https://pay.neteasegames.com/identityv/topup?c=m")
        self.page.click(".region-selector-content")
        self.page.wait_for_selector(".bui-dropdown-placement-bottomRight", state="visible")
        self.page.click(".bui-select-selector")
        self.page.click("text=Philippines")

        """ 選擇 English"""
        english_option = self.page.locator("//div[contains(@class, 'lan-item') and text()='English']")
        english_option.click()


    def select_server(self):
        """選擇遊戲伺服器 (Asia)"""

        # 點擊伺服器選擇框
        self.page.click("//div[contains(@class, 'bui-select-selector') and .//span[contains(text(), 'Please choose server')]]")

        # 滾動到 Asia 選項並點擊
        asia_option = self.page.locator("//div[contains(@class, 'bui-select-item-option-content') and contains(text(), 'Asia')]")
        asia_option.scroll_into_view_if_needed()
        asia_option.click()

        print("✅ 選擇 Asia 伺服器")

    def input_game_id(self, game_id: str):
        """輸入遊戲帳號"""
        game_id_input = self.page.locator("//input[@type='text' and contains(@class, 'bui-input gc-input-pc')]")
        game_id_input.fill(game_id)
        print(f"✅ 輸入遊戲帳號: {game_id}")

    def agree_terms_and_login(self):
        """勾選同意條款並登入"""
        agree_terms_option = self.page.locator("//label[contains(@class, 'gc-checkbox-pc bui-checkbox')]")
        agree_terms_option.click()
        print("✅ 勾選同意條款")

        login_button = self.page.locator(".userid-login-btn")
        login_button.click()
        print("✅ 點擊登入按鈕")

    def select_product(self):
        """ 選擇商品並確認 """
        self.page.click("//div[@class='goods-item-pc' and @data-key='ios_h55na.mol.ph.680echoes']")
        self.page.click("//button[contains(@class, 'topup-btn')]")

    def login_account(self, user_id: str, password: str):
        """ 使用者登入儲值帳號 """
        # self.page.goto("ttps://pay.neteasegames.com/identityv/topup?c=m")

        self.page.fill("#loginEmail", user_id)
        self.page.fill("#loginPassword", password)
        self.page.click("#btn-log-in")
        time.sleep(3)  # 等待登入完成

        # 驗證使用者名稱
        user_name_displayed = self.page.inner_text(".col")  # 確保匹配 Selenium 的 XPath
        return user_name_displayed

    def login_razer(self, razer_email: str, razer_password: str):
        """ 登入 Razer 帳戶 """
        self.page.goto("https://razerid.razer.com/")

        self.page.fill("#loginEmail", razer_email)
        self.page.fill("#loginPassword", razer_password)
        self.page.click("#btn-log-in")
        time.sleep(3)

        # 檢查是否需要 OTP
        if self.page.locator(".input-otp").is_visible():
            otp_code = self.generate_otp()
            self.page.fill(".input-otp", otp_code)
            self.page.click("#otp-submit")
            time.sleep(3)

        return "dashboard" in self.page.url

    def generate_otp(self):
        """ 產生 OTP 驗證碼 """
        SECRET_KEY = "YOUR_OTP_SECRET_KEY"  # 需改為環境變數
        totp = pyotp.TOTP(SECRET_KEY)
        return totp.now()

    def complete_transaction(self):
        """ 點擊完成按鈕，確認交易成功 """
        self.page.click(".btnConfirm")
        time.sleep(3)
        return self.page.screenshot()

    def verify_final_user(self, expected_user_id: str, expected_user_name: str):
        """ 在交易成功畫面上再次驗證 ID & 名稱 """
        final_user_id = self.page.inner_text("#final-user-id")
        final_user_name = self.page.inner_text("#final-user-name")

        return final_user_id == expected_user_id and final_user_name == expected_user_name

    def perform_deposit(self, user_id: str, user_name: str, password: str, razer_email: str, razer_password: str, deposit_count: int):
        """ 執行完整儲值流程 """
        self.start_browser()
        self.select_country()

        # 登入並驗證名稱
        displayed_name = self.login_account(user_id, password)
        if displayed_name != user_name:
            self.close_browser()
            return {"error": "使用者名稱驗證失敗"}

        self.select_product()

        # Razer 登入
        if not self.login_razer(razer_email, razer_password):
            self.close_browser()
            return {"error": "Razer 登入失敗"}

        success_images = []
        first_image = None

        for i in range(deposit_count):
            screenshot = self.complete_transaction()

            # 第二次驗證 ID & 名稱
            if not self.verify_final_user(user_id, user_name):
                self.close_browser()
                return {"error": "最終驗證失敗"}

            if i == 0:
                first_image = screenshot
            else:
                success_images.append(screenshot)

            self.save_transaction(user_id, success=True)

        self.close_browser()
        return {"message": "儲值完成", "first_image": first_image, "images": success_images}

    def save_transaction(self, user_id: str, success: bool):
        """ 儲存交易紀錄到資料庫 """
        transaction = Transaction(user_id=user_id, status="Success" if success else "Failed")
        self.db.add(transaction)
        self.db.commit()

if __name__ == "__main__":
    print("RazerService 測試開始")

    # 創建 RazerService 但不使用 DB
    service = RazerService(db=None)

    # 測試啟動瀏覽器
    try:
        service.start_browser()
        print("✅ 瀏覽器啟動成功")

        # 測試選擇國家
        service.select_country()
        print("✅ 成功選擇國家")

        # 測試選擇伺服器
        service.select_server()
        print("✅ 伺服器選擇完成")

        # 測試寫入遊戲帳號
        service.input_game_id("52745230")
        print("✅ 成功輸入遊戲帳號")

        # 測試點擊選項後登入
        service.agree_terms_and_login()
        print("✅ 成功登入遊戲帳號")

        # 測試選擇商品
        service.select_product()
        print("✅商品選擇完成")

        # 測試登入（假數據）
        fake_user_id = "test_user"
        fake_password = "password123"
        displayed_name = service.login_account(fake_user_id, fake_password)
        print(f"✅ 使用者登入成功，顯示名稱: {displayed_name}")

    except Exception as e:
        print(f"❌ 測試失敗: {e}")

    finally:
        service.close_browser()
        print("✅ 瀏覽器已關閉")

