from enum import Enum
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from accelerators import Accelerator
from datetime import timedelta, date, datetime
import zipfile
import os


class SelectSearchCriteria(str, Enum):
    LAST_01 = "Last 1 Day"
    LAST_03 = "Last 3 Days"
    LAST_07 = "Last 7 Days"
    Enter_date = "Last 15 days"

class CAndSAccelerator(Accelerator):
    display_name = 'CSWG - Remittance Downloader'
    group_name = 'C&S WHOLESALE Grocer'
    start_url = "https://websso.cswg.com/oam/server/obrareq.cgi?encquery%3DS3YmdXVDxozZJNsQ1kaD8B392xA2nxCvfyc%2FtcT%2FQDNtSHNThYBzZyOsekisHxh1TtAoTq5T%2Fqkkj1punHwCLvO1Vc9t1dLOxf18uM6KK2Xx4caNl0119iwgVNDT%2BrSt1mXxDH03RGaRnq1jLcgELO8W4gx%2BvQIIId5b1LUiRdc2PHPPtXfjXnRwoL6a5ucEfTSfJEUiC1qhZOAo2R3%2BzHR4D%2BCUcyvRgAD1rOa1dUauMR1fuJQc3aLXrp3hRR9nfgHrG3knZG0CkaXm1cLF9vdO%2BfZKuq408LrxsRc10lA%3D%20agentid%3Dvendorportal.cswg.com%20ver%3D1%20crmethod%3D2"
    info_accelerator = ''
    
    async def run(self, Select_Search_Criteria: SelectSearchCriteria, user_date: date) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            await self.info('Running…')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="username"]')))
                username_input.clear()
                username_input.send_keys(username)
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@name="password"]')))
                password_input.clear()
                password_input.send_keys(password)
                submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_button.click()
                try:
                    acknowledge_popup_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="pgl12"]')))
                    acknowledge_popup_button.click()
                except Exception:
                    self.log.debug("acknowledge_popup_button not found")
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info('Great! You’ve successfully logged into the targeted portal.')
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Reports']")))
        except TimeoutException:
            self.log.info('not available advanced filter')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        self.driver.get('https://vendorportal.cswg.com/vip/faces/pages_reports/CheckCoverSheetsDashboard')
        try:
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "/html/body//button[@id='pt1:pt_sfm1j_id_3:pt_s12j_id_7:pt_cb2']")))
        except TimeoutException:
            self.log.info('not available advanced filter')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/div/form/div/div/div/div[5]/div/div[2]/div/div/div/div/iframe")))
        date_box = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td')))
        self.driver.execute_script("arguments[0].click();", date_box)
        if Select_Search_Criteria == SelectSearchCriteria.LAST_01:
            start_date = user_date - timedelta(days=1)
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_03:
            start_date = user_date - timedelta(days=3)
        elif Select_Search_Criteria == SelectSearchCriteria.LAST_07:
            start_date = user_date - timedelta(days=7)
        elif Select_Search_Criteria == SelectSearchCriteria.Enter_date:
            start_date = user_date - timedelta(days=15)  # Assuming "last 15 days" means the past 15 days including today
        else:
            await self.error('Invalid search criteria. Please select a valid option.')
            return
        current_date = start_date
        while current_date < user_date:
            current_date_str = current_date.strftime("%m/%d/%Y")
            insert_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr/td/span/input')))
            insert_date_input.clear()
            insert_date_input.send_keys(current_date_str)
            insert_date_input.send_keys(Keys.ENTER)
            insert_date_input.send_keys(Keys.ENTER)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            for _ in range(5):
                try:
                    apply_button = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[2]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td/div/form/div/table/tbody/tr[3]/td/input')))
                    apply_button.click()
                    break
                except StaleElementReferenceException:
                    continue
            export_button_xpath = '/html/body/div[7]/div/table/tbody/tr/td/div[1]/div[2]/table/tbody/tr/td[1]/div/table/tbody/tr[3]/td/div/table/tbody/tr[2]/td/div/table/tbody/tr/td/div/div/div/table/tbody/tr/td[9]/a'
            export_button_visible = EC.visibility_of_element_located((By.XPATH, export_button_xpath))
            try:
                wait.until(export_button_visible)
            except TimeoutException:
                await self.info(f"Check creation date - {current_date_str} Not Found. Moving to Next...")
                current_date += timedelta(days=1)
                continue
            try:
                export_button = wait.until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.execute_script("arguments[0].click();", export_button)
            except StaleElementReferenceException:
                self.log.debug('export button element is stale. Trying to find it again...')
                export_button = wait.until(EC.element_to_be_clickable((By.XPATH, export_button_xpath)))
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.execute_script("arguments[0].click();", export_button)
            try:
                click_excel = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//td[contains(text(), 'Excel 2007+')]")))
                click_excel.click()
            except TimeoutException:
                self.log.debug('click excel not found, please try again')
                continue
            await self.wait_for_output(lambda files: any(file.startswith("Check Cover Sheets Report") for file in files))
            try:
                click_ok = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'a.masterToolbarTextButton.button[name="OK"]')))
                click_ok.click()
            except TimeoutException:
                self.log.debug("click_ok button not found ...")
                continue
            for filename in os.listdir(self.output_path):
                if filename.startswith('Check Cover Sheets Report'):
                    try:
                        os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'CSWG_Remittance_{Select_Search_Criteria.value}_file_{current_date_str.replace("/", "-")}.xlsx'))
                    except TimeoutException:
                        self.log.debug("TimeoutException while renaming file or maybe file is not found")
            await self.info(f"Check_creation_date - {current_date_str} Processed")
            current_date += timedelta(days=1)
        currentdate = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"CSWG_Remittance_{Select_Search_Criteria.value}_{currentdate}")
        xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.xlsx')]
        if len(xl_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in xl_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid check creation date.')
            return
        
    def is_logged_in(self) -> bool:
        return 'https://websso.cswg.com/oam' not in self.driver.current_url
