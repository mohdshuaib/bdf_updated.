from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from datetime import date
import os
import zipfile
from accelerators import Accelerator
 
class BJSAccelerator(Accelerator):
    display_name = "BJ's Wholesale"
    group_name = "BJ's Wholesale"
    start_url = "https://vendorportal.bjs.com/bd/public/frameset_top_html.jsp"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = 'BJs Wholesale Info'
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 30)
 
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Logging in...')
                username, password = await auth.userpass()
 
                for frame_change in ["billerdirect_application", "billerdirect_content"]:
                    self.driver.switch_to.frame(frame_change)
 
                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="User *"]')))
                username_element.clear()
                username_element.send_keys(username)
 
                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="j_password"]')))
                password_element.clear()
                password_element.send_keys(password)
 
                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_login.click()
                self.driver.switch_to.default_content()
 
                if not self.is_logged_in():
                    await self.error('Failed to log in; try again')
                    return
                await self.info('Login was successful')
 
        for frame_change in ["billerdirect_application", "billerdirect_navigation"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for Payment Detail {frame_change}")
 
        payment_detail = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Payment Detail']")))
        payment_detail.click()
        self.driver.switch_to.default_content()
 
        for frame_change in ["billerdirect_application", "billerdirect_content"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for {frame_change}")
 
        select_range_date = wait.until(EC.element_to_be_clickable((By.ID, "searchDateId")))
        self.driver.execute_script("arguments[0].click();", select_range_date)
        select_range_date.send_keys(Keys.END)
 
        # start date range
        from_date_field_month = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldFrom1")))
        from_date_field_day = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldFrom2")))
        from_date_field_year = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldFrom3")))
        # End date range
        to_date_field_month = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldTo1")))
        to_date_field_day = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldTo2")))
        to_date_field_year = wait.until(EC.element_to_be_clickable((By.ID, "dateFieldTo3")))
 
        from_date_field_month.clear()
        from_date_field_month.send_keys(from_date.month)
        from_date_field_day.clear()
        from_date_field_day.send_keys(from_date.day)
        from_date_field_year.clear()
        from_date_field_year.send_keys(from_date.year)
 
        to_date_field_month.clear()
        to_date_field_month.send_keys(to_date.month)
        to_date_field_day.clear()
        to_date_field_day.send_keys(to_date.day)
        to_date_field_year.clear()
        to_date_field_year.send_keys(to_date.year)
 
        submit_filter = wait.until(EC.element_to_be_clickable((By.NAME, "Search")))
        submit_filter.click()
 
        download_file = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Download"]')))
        download_file.click()
        self.driver.switch_to.default_content()
        await self.info('Processing output...')
        for frame_change in ["billerdirect_application", "billerdirect_navigation"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for Open Invoice {frame_change}")
 
        open_Invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Open Invoices/Credits"]')))
        open_Invoice.click()
 
        self.driver.switch_to.default_content()
        for frame_change in ["billerdirect_application", "billerdirect_content"]:
            self.driver.switch_to.frame(frame_change)
            self.log.debug(f"[+] Frame change Successfully Done for {frame_change}")
        download_file = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@value="Download"]')))
        download_file.click()
        self.driver.switch_to.default_content()
        output_zip = os.path.join(self.output_path, "BJS_All_Backup.zip")
        required_files = ["Payment_Details.csv", "Open_Invoices_Credits.csv"]
        files = await self.wait_for_output(lambda files: all(file in required_files for file in files))
        from_date = from_date.strftime("%m%d%Y")
        to_date = to_date.strftime("%m%d%Y")
        if len(files) == 2:
            rename_files = []
            for file in files:
                os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"BJSW_Remittance_Backup_Date_{from_date}-{to_date}_{file}"))
                rename_files.append(f"BJSW_Remittance_Backup_Date_{from_date}-{to_date}_{file}")
            with zipfile.ZipFile(output_zip, 'w') as zipf:
                for file_name in rename_files:
                    file_path = os.path.join(self.output_path, file_name)
                    zipf.write(file_path, arcname=file_name)
            if os.path.exists(output_zip):
                return output_zip
        else:
            await self.error('There was a problem processing the outputs. Please try again.')
            return
   
    def is_logged_in(self) -> bool:
        try:
            for frame_change in ["billerdirect_application", "billerdirect_content"]:
                self.driver.switch_to.frame(frame_change)
                self.log.debug(f"[+] Frame change Successfully Done for {frame_change}")
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="j_password"]')))
            self.driver.switch_to.default_content()
            return False
        except Exception:
            self.driver.switch_to.default_content()
            return True
