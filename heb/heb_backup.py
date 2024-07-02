from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import os
import zipfile

from accelerators.implementations.heb.base import HEBBase

class HEBBackupAccelerator(HEBBase):
    display_name = 'HEB Backup Downloader'
    input_display_names = {'invoice_input_file': 'Invoice Numbers'}
    info_accelerator = ''
    
    async def run(self, invoice_input_file: list[str]) -> str:
        if not await self.login():
            return

        wait = WebDriverWait(self.driver, 30)
        
        for invoice_number in invoice_input_file:
            self.log.info(f"Processing for Invoice Number {invoice_number}")
            try:
                search_tab = wait.until(EC.presence_of_element_located((By.XPATH, '//a[@class="search-indicator"]')))
                search_tab.click()
                backup = wait.until(EC.presence_of_element_located((By.XPATH, '//span[@id="deduction"]')))
                backup.click()
                invoice = wait.until(EC.presence_of_element_located((By.XPATH, '//label[@id="invoice"]')))
                invoice.click()
                invoice_search = wait.until(EC.element_to_be_clickable((By.XPATH, '//input[@id="searchByMyInvoice"]')))
                invoice_search.clear()
                invoice_search.send_keys(invoice_number, Keys.ENTER)
                export_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_5"]')))
                export_button.click()
                details = wait.until(EC.element_to_be_clickable((By.XPATH, '//button[@id="ToolTables_summary-table_8"]')))
                details.click()
                my_download = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@class="myDownloads-indicator"]')))
                my_download.click()
                file_download = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[2]/div[3]/div/div[3]/div[1]/div[1]/a')))
                file_download.click()
                await self.info(f'Invoice Processed - {invoice_number}')
            except Exception:
                await self.info(f"Invoice Information Not Available for Invoice Number: {invoice_number}")
        await self.wait_for_output(lambda files: any('.crdownload' not in file and '.tmp' not in file for file in files))
        await self.info("Processing ...")
        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        zip_filename = os.path.join(self.output_path, f"HEBG_Backups_{formatted_date}")
        csv_files = [file for file in os.listdir(self.output_path) if file.endswith(".csv")]
        if len(csv_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for csv_file in csv_files:
                    zipf.write(os.path.join(self.output_path, csv_file), arcname=csv_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! No backup data found. Please try again with valid reference numbers.')
            return
