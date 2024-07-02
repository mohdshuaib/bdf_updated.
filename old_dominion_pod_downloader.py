from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import zipfile
from accelerators import Accelerator
from selenium.common.exceptions import TimeoutException
from datetime import datetime
class OldDominationAccelerator(Accelerator):
    display_name = "ODFL - POD Downloader"
    group_name = "Old Dominion Freight Lines"
    start_url = "https://www.odfl.com/"
    input_display_names = {'product_numbers': 'Enter PRO#s'}
    info_accelerator = ''
    
    async def run(self, product_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
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
                    wait.until(EC.element_to_be_clickable((By.XPATH, f'//label[text() = "{username}"]')))
                    await self.info('Great! You’ve successfully logged into the targeted portal.')
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return

        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            await self.info('Running...')
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
        except TimeoutException:
            self.log.debug("No Need to Click on cokies Button")
        try:
            WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//button[@aria-label="Close"][@class="_pendo-close-guide"]'))).click()
        except TimeoutException:
            self.log.debug("No Need to Close popup")
        for invoice_number in product_numbers:
            
            self.driver.get(f"https://www.odfl.com/us/en/tools/shipping-documents.html?proNumber={invoice_number}&docType=Delivery%20Receipt")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                delivery_receipt = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="messageDisplay__section--description"]')))
                if 'No Result found' in delivery_receipt.text:
                    self.log.debug(f"POD no - {invoice_number} Not Found Move to Next...")
                    continue
            except TimeoutException:
                await self.info(f"POD no - {invoice_number} Not Processed.")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            while not os.path.isfile(os.path.join(self.output_path, 'download.pdf')):
                self.log.debug("Checking PDF Download ...")
                self.driver.switch_to.frame(wait.until(EC.element_to_be_clickable((By.ID, 'pdfID'))))
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="open-button"]'))).click()
                self.driver.switch_to.default_content()
            os.rename(os.path.join(self.output_path, 'download.pdf'), os.path.join(self.output_path, f'ODFL_POD Backup_PRO-{invoice_number}.pdf'))
            await self.info(f"Great! POD no - {invoice_number} Processed.")
        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        zip_filename = os.path.join(self.output_path, f"ODFL_POD Backups_{formatted_date}")
        pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
        await self.info("Processing...")
        if pdf_files:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for pdf_file in pdf_files:
                    pdf_file_path = os.path.join(self.output_path, pdf_file)
                    zipf.write(pdf_file_path, arcname=pdf_file)
            self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        await self.error('Not found or tracking information unavailable')
        return

    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="onetrust-accept-btn-handler"]'))).click()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            login_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="logIn"][@tabindex="0"]')))
            login_button.click()
        except TimeoutException:
            self.log.debug("Running...")
        return 'odflb2c.b2clogin.com' not in self.driver.current_url
