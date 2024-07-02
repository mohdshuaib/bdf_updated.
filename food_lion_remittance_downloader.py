from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator
 
class FLHFRemittanceAccelerator(Accelerator):
    display_name = "FLHF - Remittance Downloader"
    group_name = "Food Lion/Hannaford"
    start_url = "https://ws1.aholdusa.com/jfitvp/news"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
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
            # required because blank file download
            await self.sleep(10)
            try:
                download_file = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text()=' Export All Acct Activity ']")))
            except TimeoutException:
                await self.error('Invalid! Remittance data not found. Please try again with valid date range.')
                return
            download_file.click()

            await self.info('Processing output...')
            output_zip = os.path.join(self.output_path, "FLHF_Remittance.zip")
            files = await self.wait_for_output(lambda files: 'AP-AR DETAILS.csv' in files)
            from_date = from_date.strftime("%m%d%Y")
            to_date = to_date.strftime("%m%d%Y")
            if files:
                rename_files = []
                for file in files:
                    os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"FLHF_Remittance_Date_{from_date}-{to_date}_{file}"))
                    rename_files.append(f"FLHF_Remittance_Date_{from_date}-{to_date}_{file}")
                with zipfile.ZipFile(output_zip, 'w') as zipf:
                    for file_name in rename_files:
                        file_path = os.path.join(self.output_path, file_name)
                        zipf.write(file_path, arcname=file_name)
                if os.path.exists(output_zip):
                    await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                    return output_zip
            else:
                await self.error('There was a problem processing the outputs. Please try again.')
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
