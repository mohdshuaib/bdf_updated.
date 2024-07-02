from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator
from datetime import datetime
class FLHFBackupAccelerator(Accelerator):
    display_name = " FLHF - Backups Downloader"
    group_name = "Food Lion/Hannaford"
    start_url = "https://ws1.aholdusa.com/jfitvp/news"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date', 'invoice_numbers': 'Enter INVOICE#s'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Running...')
        delta = to_date - from_date
        if delta.days <= 31:
            async with self.authenticator() as auth:
                if not self.is_logged_in():
                    await self.info('Attempting to login…')
                    username, password = await auth.userpass()
    
                    username_element = wait.until(EC.element_to_be_clickable((By.ID, 'uid')))
                    username_element.clear()
                    username_element.send_keys(username)
    
                    password_element = wait.until(EC.element_to_be_clickable((By.ID, 'password')))
                    password_element.clear()
                    password_element.send_keys(password)
    
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"][@value="Sign in"]')))
                    submit_login.click()
    
                    if not self.is_logged_in():
                        await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                        return
                    await self.info('Great! You’ve successfully logged into the targeted portal.')
            
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            self.driver.get("https://ws1.aholdusa.com/jfitvp/accounts/payable")
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            
            select_vendor = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, '/html/body/app-root/div/div/div/app-accounts-payable/div/div/div[2]/table/thead/tr/th[1]')))
            select_vendor.click()
            try:
                WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Continue "]'))).click()
            except TimeoutException:
                select_vendor.click()
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Continue "]'))).click()

            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            select_range_date_start = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@formcontrolname="dateRangeStart"]')))
            select_range_date_end = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@formcontrolname="dateRangeEnd"]')))
            select_range_date_start.clear()
            select_range_date_end.clear()
            for i in range(1, 10):
                select_range_date_start.send_keys(Keys.BACKSPACE)
            for j in range(1, 10):
                select_range_date_end.send_keys(Keys.BACKSPACE)
            select_range_date_start.send_keys(f"{from_date.month}/{from_date.day}/{from_date.year}")
            select_range_date_end.send_keys(f"{to_date.month}/{to_date.day}/{to_date.year}")

            # start date range
            submit_filter = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()=' Go ']")))
            submit_filter.click()
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            
            for invoice_number in set(invoice_numbers):
                if len(invoice_number) > 7:
                    await self.info(f'Processing invoice - {invoice_number}')
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="form-group"]'))).click()
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()='Invoice #']"))).click()
                    invoice_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//input[@placeholder='Value']")))
                    invoice_input.clear()
                    invoice_input.send_keys(invoice_number)
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() =" Add Filter "]'))).click()
                    WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    await self.sleep(2)
                    try:
                        results = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/div/div/div/app-consolidated-ap-ar/div/div/div[3]/div[3]/div"))).text
                        if 'No records found.' in results:
                            await self.info(f'No record found for invoice - {invoice_number}')
                            continue
                    except TimeoutException:
                        await self.info(f'Record found for invoice - {invoice_number}')
                        
                    status_clickable = '/html/body/app-root/div/div/div/app-consolidated-ap-ar/div/div/div[3]/table/tbody/tr/td[6]/span'
                    span_xpath = status_clickable
                    span_element = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.XPATH, span_xpath)))
                    anchor_element = span_element.find_elements(By.TAG_NAME, 'a')
                    if anchor_element:
                        anchor_element[0].click()
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@src, "pdf")])'))))
                        if not os.path.isfile(os.path.join(self.output_path, 'download.pdf')):
                            self.log.debug("Checking PDF Download ...")
                            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="open-button"]'))).click()
                        self.driver.switch_to.default_content()
                        self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        await self.info(f'invoice - {invoice_number} Processed')
                        await self.wait_for_output(lambda files: any('.tmp' not in file for file in files))
                        os.rename(os.path.join(self.output_path, 'download.pdf'), os.path.join(self.output_path, f'FLHF_Backup_Assign-{invoice_number}.pdf'))
                    else:
                        await self.info(f'No any option to download invoice - {invoice_number}')

            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            if pdf_files:
                await self.info("Processing...")
                zip_filename = os.path.join(self.output_path, f"FLHF_Backups_{formatted_date}")
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                return f'{zip_filename}.zip'
            await self.error('Not found or tracking information unavailable')
            return
        else:
            await self.error(f"Date range difference exceeds 31 days: {delta.days} days")
            return
        
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.visibility_of_element_located((By.ID, 'uid')))
            return False
        except Exception:
            return True
