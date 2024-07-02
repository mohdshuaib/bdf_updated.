from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from enum import Enum
from selenium.common.exceptions import StaleElementReferenceException
import os
from accelerators import Accelerator

class DocumentDateRange(str, Enum):
    LAST_10 = "Last 10 days"
    LAST_30 = "Last 30 days"
    LAST_60 = "Last 60 days"
    LAST_90 = "Last 90 days"

class WalgreensAccelerator(Accelerator):
    display_name = 'Walgreens'
    group_name = 'Walgreens'
    start_url = 'https://ppxvimspot.walgreens.com/sap/bc/ui5_ui5/ui2/ushell/shells/abap/FioriLaunchpad.html#OTBCWUI_PF07_BC_SEMOBJ-displayDesktopOnly?workplaceId=ACC_INBOX&system=OTBCWUI_BACKEND&appMode=FS'
    info_accelerator = ''
    
    async def run(self, document_date_range: DocumentDateRange) -> str:
        wait = WebDriverWait(self.driver, 70)
        
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()

                username_element = wait.until(EC.element_to_be_clickable((By.ID, "username")))
                username_element.clear()
                username_element.send_keys(username)

                password_element = wait.until(EC.element_to_be_clickable((By.ID, "txtpassword")))
                password_element.clear()
                password_element.send_keys(password)

                wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@title="Sign On"]'))).click()

                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info('Great! You’ve successfully logged into the targeted portal.')

        wait.until(EC.element_to_be_clickable((By.XPATH, '//td[text() = "No data"]')))
        date_range = document_date_range.value
        wait.until(EC.element_to_be_clickable((By.XPATH, '//bdi[text() = "Document Date"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[text() = "{date_range}"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//bdi[text() = "OK"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, f'//bdi[text() = "Document Date ({date_range})"]')))

        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        for _ in range(5):
            try:
                supplier = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[text()= "Supplier"]'))
                )
                supplier.click()
                break
            except StaleElementReferenceException:
                continue

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "BEIERSDORF INC(0001044697)"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//bdi[text() = "OK"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@class, "sapMLnk")])[1]'))).click()

        await self.info('Processing output...')
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Download"]'))).click()
        files = await self.wait_for_output(lambda files: any('.crdownload' not in file and '.tmp' not in file for file in files))
        for file in files:
            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"WALG_Remittance_Date_{date_range}_{file}"))
        return os.listdir(self.output_path)[0] if len(files) else None
    
    def is_logged_in(self) -> bool:
        return 'sso.walgreens.com' not in self.driver.current_url
