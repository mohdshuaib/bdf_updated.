from datetime import date, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator
from enum import Enum

class SelectReason(str, Enum):
    OSD = "OSD-Backup"
    PROMO = "Promo-Backup"
    PRICE = "Price-Backup"
    OTHER = "Other-Backup"

class McKessonBackupAccelerator(Accelerator):
    display_name = 'McKesson Bakckup'
    group_name = 'McKesson'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    start_url = "https://connect.McKesson.com/portal/site/smo/template.LOGIN/"
    info_accelerator = ''
    
    async def run(self, select_reason: SelectReason, document_numbers: list[str], from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 50)
        async with self.authenticator() as auth:
            await self.info('Attempting to login…')
            self.driver.maximize_window()
            username, password = await auth.userpass()
            to_month, to_day, to_year = to_date.strftime("%m %d %Y").split()
            from_month, from_day, from_year = from_date.strftime("%m %d %Y").split()
            try:
                WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div/div/div[2]/div/div/button[2]")))
            except TimeoutException:
                self.log.debug('cookies button not found')
            try:
                cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div/div/div[2]/div/div/button[2]")))
                cookies_button.click()
            except TimeoutException:
                self.log.debug("TimeoutException while clicking cookies button")
            username_element = "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[1]/div[2]/span/input"
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            username_input = wait.until(EC.element_to_be_clickable((By.XPATH, username_element)))
            username_input.send_keys(username)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
            next_button.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[2]/div[2]/span/input")))
            password_input.send_keys(password)
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
            login_button.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
            except TimeoutException:
                self.log.debug('send code not found')
            try:
                send_code_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                send_code_button.click()
            except TimeoutException:
                self.log.debug('otp not requested..')
            await self.info('waiting for the otp...')
            code = await auth.otp()
            try:
                WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[3]/div[2]/span/input")))
            except TimeoutException:
                self.log.debug('otp input feild not found.')
            otp_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[3]/div[2]/span/input")))
            otp_input.send_keys(code)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            verify_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
            verify_button.click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            if not self.is_logged_in():
                await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                return
            await self.info('Great! You’ve successfully logged into the targeted portal.')
            if select_reason is SelectReason.OSD:
                xpath_select_reason = '/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/select/option[3]'
            elif select_reason is SelectReason.PROMO:
                xpath_select_reason = '/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/select/option[5]'
            elif select_reason is SelectReason.PRICE:
                xpath_select_reason = '/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/select/option[4]'
            elif select_reason is SelectReason.OTHER:
                xpath_select_reason = '/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/select/option[7]'
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        await self.info('finding account management...')
        try:
            WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/table/tbody/tr/td[3]/a")))
        except TimeoutException:
            self.log.debug('accound management button not founded..')
        account_management = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[1]/table/tbody/tr/td[3]/a")))
        account_management.click()
        supplier_management = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div[2]/div[2]/table/tbody/tr/td/div/table/tbody/tr/td[1]/ul/li/a")))
        supplier_management.click()
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/div[1]/table/tbody/tr/td/iframe")))
        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/form/table/tbody/tr[7]/td/div/table/tbody/tr/td/table[2]/tbody/tr/td/input")))
        checkbox.click()
        try:
            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
        except TimeoutException:
            self.log.debug('save button not found..')
        try:
            save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            self.driver.execute_script("arguments[0].click();", save_button)
        except TimeoutException:
            self.log.debug('save button not found...')
        self.driver.execute_script("popup('payments')")
        await self.info('click on save button..')
        output_path = os.path.join(self.output_path)
        if not os.path.exists(output_path):
            os.makedirs(output_path)
        for document_number in list(set(document_numbers)):
            if len(str(document_number)) > 7:
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.execute_script("popup('deductions')")
                dropdown = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[1]/td/div[3]/a/div")))
                dropdown.click()
                debit_memos = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/input")))
                debit_memos.clear()
                debit_memos.send_keys(document_number)
                await self.info('entered document number..')
                select_category = wait.until(EC.element_to_be_clickable((By.XPATH, f'{xpath_select_reason}')))
                select_category.click()
                select_deduction_date = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td[1]/select/option[3]")))
                select_deduction_date.click()
                select_from_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td[3]/input[1]")))
                select_from_month.send_keys(from_month)
                select_from_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td[3]/input[2]")))
                select_from_day.send_keys(from_day)
                select_from_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[1]/td[3]/input[3]")))
                select_from_year.send_keys(from_year)
                select_to_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td[2]/input[1]")))
                select_to_month.send_keys(to_month)
                select_to_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td[2]/input[2]")))
                select_to_day.send_keys(to_day)
                select_to_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td[2]/input[3]")))
                select_to_year.send_keys(to_year)
                click_retrieve_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[6]/td/table/tbody/tr/td[1]/input")))
                click_retrieve_button.click()
                await self.info('filled all required feild click retrieve button, waiting download button..')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                download_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Download']")))
                self.driver.execute_script("arguments[0].scrollIntoView(true);", download_button)
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Download']")))
                except TimeoutException:
                    self.log.debug('download button not found...')
                self.driver.execute_script("arguments[0].click();", download_button)
                refresh_token = False
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@alt='Download']")))
                    refresh_token = True
                except TimeoutException:
                    await self.info("Data not found for document number: {}".format(document_number))
                    refresh_token = False
                if not refresh_token:
                    await self.error("Data not found for document number: {}. Moving to next...".format(document_number))
                    continue
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.wait_for_output(lambda files: 'debitmemos.xls' in files)
                await self.info('waiting for the download file..')
                self.log.debug("[+] Stage Download output")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                for filename in os.listdir(output_path):
                    if filename.startswith('debitmemos'):
                        await self.info('trying to rename the file..')
                        os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'MCKE_{select_reason.value}_{document_number}-file_{filename}'))
                    await self.info(f"this McKesson Backup data is being Processed: {document_number} ")
        count_invoices = len(document_numbers)
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"MCKE_{select_reason.value}_{count_invoices}_{current_date}")
        xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.xls')]
        if len(xl_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in xl_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid invoices.')
            return
    
    def is_logged_in(self) -> bool:
        return 'https://connect.McKesson.com/portal' not in self.driver.current_url
