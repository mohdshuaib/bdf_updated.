from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from enum import Enum
import os
from accelerators.implementations.supervalu.base import SupervaluBase

class DocumentDateRange(str, Enum):
    LAST_30 = "Last 30 Days"
    LAST_60 = "Last 6 Months"
    LAST_90 = "Last 12 Months"

class SupervalueRemittanceAccelerator(SupervaluBase):
    display_name = 'Remittance Downloader'
    info_accelerator = ''
    
    async def run(self, document_date_range: DocumentDateRange) -> str:
        await self.info('Running...')
        if not await self.login():
            return

        wait = WebDriverWait(self.driver, 30)

        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[text() ="Go"]')))

        if document_date_range is DocumentDateRange.LAST_30:
            xpath_range = '//*[@name="dateCriteria"][@value="1"]'

        elif document_date_range is DocumentDateRange.LAST_60:
            xpath_range = '//*[@name="dateCriteria"][@value="2"]'

        elif document_date_range is DocumentDateRange.LAST_90:
            xpath_range = '//*[@name="dateCriteria"][@value="4"]'
        await self.info('Running...')
        input_doc_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="docNum1"]')))
        input_doc_field.clear()
        wait.until(EC.element_to_be_clickable((By.XPATH, f'{xpath_range}'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Go"]'))).click()
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Export All"]'))).click()

        await self.info('Processing...')
        files = await self.wait_for_output(lambda files: 'epassSearchResults.csv' in files)
        date_range = document_date_range.value
        for file in files:
            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"SUPR_Remittance_Date_{date_range}_{file}"))
        return os.listdir(self.output_path)[0] if len(files) else None
