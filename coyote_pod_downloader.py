from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import zipfile
from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException
from datetime import datetime
class CoyoteAccelerator(Accelerator):
    display_name = "Coyote POD Downloader"
    group_name = "Coyote Logistics"
    start_url = "https://go.coyote.com/"
    input_display_names = {'product_numbers': 'Enter PRO#s'}
    info_accelerator = ''
    
    async def run(self, product_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        await self.info('Running...')
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInName"]')))
                username_element.clear()
                username_element.send_keys(username)
 
                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="password"]')))
                password_element.clear()
                password_element.send_keys(password)
 
                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_login.click()
                try:
                    WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//button[text() = "Accept Cookies"]'))).click()
                except TimeoutException:
                    self.log.debug('cookies already accepted')
                try:
                    WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//a[text() = "My Shipments"]')))
                    await self.info('Great! You’ve successfully logged into the targeted portal.')
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
        WebDriverWait(self.driver, 30).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        WebDriverWait(self.driver, 60).until(EC.element_to_be_clickable((By.XPATH, '//a[text() = "My Shipments"]')))
        for invoice_number in list(set(product_numbers)):
            if len(str(invoice_number)) > 3:
                self.driver.get("https://go.coyote.com/")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.get(f"https://go.coyote.com/load-details#{invoice_number}/documents")
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    delivery_receipt = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text()="Proof of Delivery"][@class="text-link hook--document text-left"]')))
                except TimeoutException:
                    await self.info(f"POD no - {invoice_number} Not Processed.")
                    continue
                delivery_receipt.click()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.wait_for_output(lambda files: any('.tmp' not in file and '.crdownload' not in file for file in files))
                # Need time sleep due to files are push by browser in time
                await self.sleep(4)
                for file in os.listdir(self.output_path):
                    if 'Coyote Report' in file and str(file).endswith('.pdf'):
                        pass
                    else:
                        os.rename(os.path.join(self.output_path, file), os.path.join(self.output_path, f'COYO_POD Backup_PRO-{invoice_number}.pdf'))
                        await self.info(f"Great! POD no - {invoice_number} Processed.")

        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        zip_filename = os.path.join(self.output_path, f"COYO_Backups_{formatted_date}")
        pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
        if pdf_files:
            await self.info("Processing...")
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for pdf_file in pdf_files:
                    pdf_file_path = os.path.join(self.output_path, pdf_file)
                    zipf.write(pdf_file_path, arcname=pdf_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        await self.error('Not found or tracking information unavailable')
        return

    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="signInName"]')))
            return False
        except Exception:
            return True
