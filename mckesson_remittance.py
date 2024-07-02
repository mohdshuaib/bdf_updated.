from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException
from datetime import date, datetime
import zipfile
import os

class McKessonRemittanceAccelerator(Accelerator):
    display_name = 'McKesson Remittance'
    group_name = 'McKesson'
    start_url = "https://connect.mckesson.com/portal/site/smo/template.LOGIN/"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                to_month, to_day, to_year = to_date.strftime("%m %d %Y").split()
                from_month, from_day, from_year = from_date.strftime("%m %d %Y").split()
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div/div/div[2]/div/div/button[2]")))
                except TimeoutException:
                    self.log.debug("cookies_button element not found")
                try:
                    cookies_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[6]/div[2]/div/div/div[2]/div/div/button[2]")))
                    cookies_button.click()
                except TimeoutException:
                    self.log.debug("TimeoutException while clicking cookies button")
                username_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[1]/div[2]/span/input")))
                username_input.send_keys(username)
                next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                next_button.click()
                password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[2]/div[2]/span/input")))
                password_input.send_keys(password)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                login_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                login_button.click()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                except TimeoutException:
                    self.log.debug("send_code_button element not found")
                try:
                    send_code_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                    send_code_button.click()
                except TimeoutException:
                    self.log.debug('otp send button not found..')
                await self.info('waiting for the otp code…')
                code = await auth.otp()
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[3]/div[2]/span/input")))
                except TimeoutException:
                    self.log.debug("otp_input element not found")
                otp_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[1]/div[2]/div[3]/div[2]/span/input")))
                otp_input.send_keys(code)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                verify_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/form/div/div/div[1]/div/div[2]/div/div/form/div[2]/input")))
                verify_button.click()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info("Great! You've successfully logged into the targeted portal.")
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
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        wait.until(EC.frame_to_be_available_and_switch_to_it((By.XPATH, "/html/body/div[1]/table/tbody/tr/td/iframe")))
        checkbox = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/form/table/tbody/tr[7]/td/div/table/tbody/tr/td/table[2]/tbody/tr/td/input")))
        checkbox.click()
        WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
        try:
            save_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@value='submit'][@alt='Save']")))
            self.driver.execute_script("arguments[0].scrollIntoView(true);", save_button)
            self.driver.execute_script("arguments[0].click();", save_button)
        except TimeoutException:
            self.log.debug('save button not found...')
        self.driver.execute_script("popup('payments')")
        dropdown = wait.until(EC.visibility_of_element_located((By.XPATH, "/html/body/form/table/tbody/tr[1]/td/div[2]/a[2]/div")))
        dropdown.click()
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        select_begin_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/input[1]")))
        select_begin_month.send_keys(from_month)
        select_begin_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/input[2]")))
        select_begin_day.send_keys(from_day)
        select_begin_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[3]/input[3]")))
        select_begin_year.send_keys(from_year)
        select_last_month = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input[1]")))
        select_last_month.send_keys(to_month)
        select_last_day = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input[2]")))
        select_last_day.send_keys(to_day)
        select_last_year = WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[5]/td/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/input[3]")))
        select_last_year.send_keys(to_year)
        retrieve_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[6]/td/table/tbody/tr/td[1]/input")))
        retrieve_button.click()
        await self.info('filled all the required field click on the retrieve_button')
        WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.ID, "pnum")))
        WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.TAG_NAME, "option")))
        page_count_dropdown = self.driver.find_element(By.ID, "pnum")
        total_pages = len(page_count_dropdown.find_elements(By.TAG_NAME, "option"))
        for page_number in range(1, total_pages + 1):
            page_count_dropdown = self.driver.find_element(By.ID, "pnum")
            page_count_dropdown.find_element(By.CSS_SELECTOR, f"option[value='{page_number}']").click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[8]/td/div/table/tbody/tr/td/table/tbody/tr")))
            all_rows = self.driver.find_elements(By.XPATH, "/html/body/form/table/tbody/tr[8]/td/div/table/tbody/tr/td/table/tbody/tr")
            for row_index, row in enumerate(all_rows, start=1):
                row_xpath = f"/html/body/form/table/tbody/tr[8]/td/div/table/tbody/tr/td/table/tbody/tr[{row_index}]/td[1]/a"
                row_element = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, row_xpath)))
                try:
                    self.driver.execute_script("arguments[0].click();", row_element)
                except TimeoutException:
                    self.log.debug('row eleemnt not found please try again')
                await self.info('click on row element..')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                WebDriverWait(self.driver, 90).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[9]/td/table/tbody/tr/td[1]/input[2]")))
                refresh_token = False
                try:
                    click_on_download = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[9]/td/table/tbody/tr/td[1]/input[2]")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_download)
                    self.driver.execute_script("arguments[0].click();", click_on_download)
                    await self.info('click on download button..')
                    refresh_token = True
                except TimeoutException:
                    self.log.debug("Download button not found")
                    refresh_token = False
                if not refresh_token:
                    await self.log.error("Download button not clickable")
                    return
                await self.wait_for_output(lambda files: any(file.startswith('000') and file.endswith('.xls') for file in files))
                await self.info('click on download element.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    click_on_back = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[9]/td/table/tbody/tr/td[1]/input[1]")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_back)
                    self.driver.execute_script("arguments[0].click();", click_on_back)
                except TimeoutException:
                    self.log.debug('back button is not found try again.')
            await self.info('file is downloaded click on back button.')
            for filename in os.listdir(self.output_path):
                if filename.startswith('000'):
                    os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'MCKE_Remittance_{from_date}_{to_date}_file_{filename}'))
                await self.info(f"This remittance data is being processed: {filename}")
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f"MCKE_Remittance_{current_date}")
        xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.xls')]
        if len(xl_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in xl_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! Not found. Please try again with valid date.')
            return
        
    def is_logged_in(self) -> bool:
        return 'https://connect.mckesson.com/portal' not in self.driver.current_url
