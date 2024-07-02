from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import datetime
import os
import zipfile

from accelerators.implementations.supervalu.base import SupervaluBase

class SupervaluBackupAccelerator(SupervaluBase):
    display_name = 'Backup Downloader'
    input_display_names = {'documents': 'Document Numbers'}
    info_accelerator = ''
    
    async def run(self, documents: list[str]) -> str:
        await self.info('Running...')
        if not await self.login():
            return

        wait = WebDriverWait(self.driver, 30)
        await self.info('Running...')
        wait.until(EC.visibility_of_element_located((By.XPATH, '//*[text() ="Go"]')))
        for document_no in documents:
            if len(str(document_no)) > 4:
                self.driver.get("https://epass.svharbor.com/epass/newDocumentSearch")
                self.log.debug(f"Processing Invoice for document -{document_no}")
                input_doc_field = wait.until(EC.visibility_of_element_located((By.XPATH, '//input[@name="docNum1"]')))
                input_doc_field.clear()
                input_doc_field.send_keys(document_no)
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="dateCriteria"][@value="4"]'))).click()
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() ="Go"]'))).click()
                status = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/div[2]/div/form/div/table/tbody/tr[1]/td[3]"))).text
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name = "documentOutputType"][@value = "pdf"]'))).click()
                if status == "View":
                    document_status = wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[text() ="{document_no}"]')))
                    document_status.click()
                    self.driver.switch_to.window(self.driver.window_handles[1])
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    await self.sleep(5)
                    window_handles = self.driver.window_handles
                    if len(window_handles) > 0:
                        self.driver.close()
                        first_window_handle = window_handles[0]
                        await self.info(f"Backup Found for document -{document_no}")
                        for filename in os.listdir(self.output_path):
                            if filename.startswith('BATCH'):
                                os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'SUPR_Backup_Assign - {document_no}.pdf'))
                        self.driver.switch_to.window(first_window_handle)
                else:
                    await self.info(f"Backup Not Found! for document no - {document_no} Move to Next...")

        await self.info('Processing...')
        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        zip_filename = os.path.join(self.output_path, f"SUPR_Backups_{formatted_date}")
        files = os.listdir(self.output_path)
        self.log.debug(f"There are Downloaded File Supervalu :{files}")
        pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
        if len(pdf_files) > 0:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for pdf_file in pdf_files:
                    pdf_file_path = os.path.join(self.output_path, pdf_file)
                    zipf.write(pdf_file_path, arcname=pdf_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! No backup data found. Please try again with valid reference numbers.')
            return
