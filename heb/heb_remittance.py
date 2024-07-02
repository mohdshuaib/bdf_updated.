from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
import os
from accelerators.implementations.heb.base import HEBBase

class HEBRemittanceAccelerator(HEBBase):
    display_name = 'HEB Remittance Downloader'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        if not await self.login():
            return
        
        wait = WebDriverWait(self.driver, 30)

        search_tab = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="search-indicator"]')))
        search_tab.click()
        payment = wait.until(EC.element_to_be_clickable((By.XPATH, '//span[@id="payment"]')))
        payment.click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="customFilter"]/span'))).click()
        from_date_value = f"{from_date.month}/{from_date.day}/{from_date.year}"
        to_date_value = f"{to_date.month}/{to_date.day}/{to_date.year}"
        self.log.debug(f"Date Range from {from_date} : To {to_date} format MM/DD/YYYY")
        from_date_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="dateFrom"]')))
        from_date_field.clear()
        from_date_field.send_keys(from_date_value)
        to_date_field = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="dateTo"]')))
        to_date_field.clear()
        to_date_field.send_keys(to_date_value)
        button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="customDateSearchButton"]')))
        button.click()
        await self.info("Processing...")
        export_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_4"]')))
        export_button.click()
        details = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_6"]')))
        details.click()
        my_download = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="myDownloads-indicator"]')))
        my_download.click()
        file_download = WebDriverWait(self.driver, 250).until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div[3]/div[1]/div[1]/a')))
        file_download.click()
        files = await self.wait_for_output(lambda files: any('.tmp' not in file for file in files))
        from_date = from_date.strftime("%m%d%Y")
        to_date = to_date.strftime("%m%d%Y")
        for file in files:
            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"HEBG_Remittance_Date_{from_date}-{to_date}_{file}"))
        return os.listdir(self.output_path)[0] if len(files) else None
