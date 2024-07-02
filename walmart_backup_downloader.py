from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from datetime import datetime
import os
import zipfile
from accelerators import Accelerator
 
class WALMBackupAccelerator(Accelerator):
    display_name = "WALM-HR - Backups Downloader"
    group_name = "Walmart"
    start_url = "https://walmart.highradius.com/RRDMSProject/dms/Home.do"
    input_display_names = {'invoice_numbers': 'Enter INVOICE#s'}
    info_accelerator = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Running...')
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()

                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="username"]')))
                username_element.clear()
                username_element.send_keys(username)

                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="password"]')))
                password_element.clear()
                password_element.send_keys(password)

                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@signin="Sign In"]')))
                submit_login.click()
                try:
                    WebDriverWait(self.driver, 80).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Closed Bills']")))
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info('Great! You’ve successfully logged into the targeted portal.')
        
        WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        closed_bills = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Closed Bills']")))
        closed_bills.click()
        WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Sales Invoice PDF']")))
        except TimeoutException:
            self.log.info('not available advanced filter')
        for invoice_number in set(invoice_numbers):
            if len(invoice_number) > 5:
                invoice_number = invoice_number.strip()
                await self.info(f'Processing invoice - {invoice_number}')
                advanced_tocken = False
                try:
                    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Sales Invoice PDF']")))
                except TimeoutException:
                    self.log.info('not available advanced filter')
                for xpath in self.driver.find_elements(By.XPATH, "//*[text() = 'Advanced Search']"):
                    if 'Advanced Search' in xpath.text:
                        xpath.click()
                        advanced_tocken = True
                        break
                if not advanced_tocken:
                    for xpath in self.driver.find_elements(By.XPATH, "//*[text() = 'Advanced Search']"):
                        if 'Advanced Search' in xpath.text:
                            xpath.click()
                            advanced_tocken = True
                            break

                WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                invoice_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@name="eippAcctDocHeader_documentNumber"]')))
                invoice_input.clear()
                invoice_input.send_keys(invoice_number)

                for xpath in self.driver.find_elements(By.XPATH, "//*[text() = 'Search']"):
                    if 'Search' in xpath.text:
                        xpath.click()
                        break
                try:
                    WebDriverWait(self.driver, 2).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Sales Invoice PDF']")))
                except TimeoutException:
                    self.log.info('not available advanced filter')
                WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                elems = self.driver.find_elements(By.TAG_NAME, 'img')
                download_tocken = False
                for elem in elems:
                    if 'eye_icon.png' in elem.get_attribute("src"):
                        download_view = self.driver.find_elements(By.XPATH, "//*[text()='View']")[0]
                        self.driver.execute_script("arguments[0].click();", download_view)
                        await self.wait_for_output(lambda files: any(f'SalesInvoice_Bills_{invoice_number}' in file and '.pdf' in file for file in files))
                        for file in os.listdir(self.output_path):
                            if f'SalesInvoice_Bills_{invoice_number}' in file and '.pdf' in file:
                                os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f'WALM-HR_Backup_Assign-{invoice_number}-{file}'))
                        await self.info(f'Record found for Invoice - {invoice_number}')
                        download_tocken = True
                if not download_tocken:
                    await self.info(f'No record found for POD - {invoice_number}')
                    continue

        pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
        if pdf_files:
            await self.info("Processing...")
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"WALM-HR - Backups {formatted_date}")
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for pdf_file in pdf_files:
                    pdf_file_path = os.path.join(self.output_path, pdf_file)
                    zipf.write(pdf_file_path, arcname=pdf_file)
            self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        await self.error('Not found or tracking information unavailable')
        return
       
    def is_logged_in(self) -> bool:
        return 'signin.do' not in self.driver.current_url
