from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from selenium.common.exceptions import TimeoutException
import os
from accelerators.implementations.supervalu.base import SupervaluBase


class SupervalueRemittanceManualAccelerator(SupervaluBase):
    display_name = 'Remittance Manual Downloader'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        await self.info('Running...')
        if not await self.login():
            return
        from_date_field = f"{from_date.month}/{from_date.day}/{from_date.year}"
        to_date_field = f"{to_date.month}/{to_date.day}/{to_date.year}"
        wait = WebDriverWait(self.driver, 30)

        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[text() ="Go"]')))

        xpath_range = '//*[@name="dateCriteria"][@value="manual"]'

        input_doc_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="docNum1"]')))
        input_doc_field.clear()

        wait.until(EC.element_to_be_clickable((By.XPATH, f'{xpath_range}'))).click()
        from_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="f_date_a"]')))
        from_date_input.clear()
        from_date_input.send_keys(from_date_field)

        to_date_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="f_date_b"]')))
        to_date_input.clear()
        to_date_input.send_keys(to_date_field)

        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Go"]'))).click()
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@title="Export All"]'))).click()
        except TimeoutException:
            await self.error('Invalid! Remittance data not found. Please try again with valid date range.')
            return
        
        await self.info('Processing...')
        files = await self.wait_for_output(lambda files: 'epassSearchResults.csv' in files)
        from_date = from_date.strftime("%m%d%Y")
        to_date = to_date.strftime("%m%d%Y")
        for file in files:
            os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f"SUPR_Remittance_Date_{from_date}-{to_date}_{file}"))
        return os.listdir(self.output_path)[0] if len(files) else None
