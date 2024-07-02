from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator

class KrogerAllBackupsAccelerator(Accelerator):
    display_name = 'KROG - All Backups Downloader'
    group_name = 'Kroger'
    input_display_names = {'invoice_numbers': 'InvoiceNUM'}
    start_url = "https://partnerpass.krogerapps.com/vendorsso/dashboard"
    info_accelerator = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 45)
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                self.driver.maximize_window()
                username, password = await auth.userpass()
                username_element = "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[3]/div/div[2]/span/input"
                try:
                    username_input = wait.until(EC.element_to_be_clickable((By.XPATH, username_element)))
                    username_input.clear()
                    username_input.send_keys(username)
                except TimeoutException:
                    self.log.debug('username element not found.')
                    return
                try:
                    next_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='form19']/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", next_button)
                except TimeoutException:
                    self.log.debug('next button not found.')
                try:
                    password_input = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[4]/div/div[2]/span/input")))
                    password_input.clear()
                    password_input.send_keys(password)
                except TimeoutException:
                    self.log.debug('password input element not found.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    verify_password = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input")))
                    self.driver.execute_script("arguments[0].click();", verify_password)
                except TimeoutException:
                    self.log.debug('verify password element not found')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    select_octa_push = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/div/div[1]/div[2]/div[2]/a")))
                    self.driver.execute_script("arguments[0].click();", select_octa_push)
                except TimeoutException:
                    self.log.debug('select octa push element not found.')
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                await self.info('waiting for the otp.')
                code = await auth.otp()
                octa_code = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[1]/div[4]/div/div[2]/span/input")))
                octa_code.send_keys(code)
                verify_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/main/div[2]/div/div/div[2]/form/div[2]/input")))
                self.driver.execute_script("arguments[0].click();", verify_button)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                self.log.debug('Please wait, verifying the OTP code.')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
        except TimeoutException:
            self.log.debug('popup not found...')
        if '/vendorsso/dashboard' in self.driver.current_url:
            await self.info('Great! You’ve successfully logged into the targeted portal.')
            self.driver.get("https://partnerpass.lavante.com/sim/supplierDashboard.lvp")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            self.driver.get('https://partnerpass.lavante.com/sim/supplierInvoiceSearchResult.lvp#search')
            await self.info('click on invoice search button please wait.')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            for invoice_number in set(list(invoice_numbers)):
                if len(str(invoice_number)) > 7:
                    try:
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="invoiceNumber"]')))
                    except TimeoutException:
                        self.log.debug('popup not found...')
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    fill_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[7]/div/div[3]/div/div[1]/div/div[4]/div[1]/form/div/div[3]/div[2]/input')))
                    fill_invoice.clear()
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    fill_invoice.send_keys(invoice_number)
                    search_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="invoiceSearch"]')))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", search_button)
                    self.driver.execute_script("arguments[0].click();", search_button)
                    await self.info('filled all the required feild click on search button')
                    try:
                        iframe_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_results"]')))
                        self.driver.switch_to.frame(iframe_element)
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    except TimeoutException:
                        await self.info(f'{invoice_number} not found in Record.')
                        continue
                    try:
                        WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/div/div[4]/div/div/table/tbody/tr[1]/td[4]/a")))
                    except TimeoutException:
                        self.log.debug('export button not found...')
                    try:
                        click_on_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/div/div[4]/div/div/table/tbody/tr[1]/td[4]/a")))
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_invoice)
                        self.driver.execute_script("arguments[0].click();", click_on_invoice)
                    except TimeoutException:
                        await self.info(f'{invoice_number} not found in Record.')
                        continue
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    more_option = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="button-action-bar"]/div[3]/button')))
                    self.driver.execute_script("arguments[0].click();", more_option)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    export_button = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='button-action-bar']/div[3]/ul/li/a")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", export_button)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='button-action-bar']/div[3]/ul/li/a")))
                    except TimeoutException:
                        self.log.debug('export button not found...')
                    self.driver.execute_script("arguments[0].click();", export_button)
                    refresh_token = False
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='button-action-bar']/div[3]/ul/li/a")))
                        refresh_token = True
                    except TimeoutException:
                        await self.info("Data not found for document number: {}".format(invoice_number))
                        refresh_token = False
                    if not refresh_token:
                        await self.error("Data not found for document number: {}. Moving to next...".format(invoice_number))
                        continue
                    click_on_back = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='content']/div[1]/div[1]/div[1]/a")))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_back)
                    wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='content']/div[1]/div[1]/div[1]/a")))
                    try:
                        self.driver.execute_script("arguments[0].click();", click_on_back)
                    except TimeoutException:
                        self.log.debug('back button not found.')
                    click_on_clear = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_supplier_form"]/div/div[16]/input[1]')))
                    self.driver.execute_script("arguments[0].scrollIntoView(true);", click_on_clear)
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_supplier_form"]/div/div[16]/input[1]')))
                    try:
                        self.driver.execute_script("arguments[0].click();", click_on_clear)
                    except TimeoutException:
                        self.log.debug('back button not found.')
                    self.driver.switch_to.default_content()
                    self.log.debug("[+] Stage Download output")
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    for filename in os.listdir(self.output_path):
                        if filename.startswith('AssociatedDeductions_Invoice'):
                            os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'KROG-Backups_Downloader_InvoiceNUM{invoice_number}_file_{filename}'))
                    await self.info(f"this Kroger_Backups InvoiceNUM {invoice_number} data is being Processed")
            count_invoices = len(invoice_numbers)
            current_date = datetime.today().strftime('%Y%m%d')
            zip_filename = os.path.join(self.output_path, f"KROG-Backups_Downloader_{count_invoices}_{current_date}")
            pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
            if len(pdf_files) > 0:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for pdf_file in pdf_files:
                        pdf_file_path = os.path.join(self.output_path, pdf_file)
                        zipf.write(pdf_file_path, arcname=pdf_file)
                await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Invalid! Not found. Please try again with valid invoices.')
                return
        else:
            await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
            return

    def is_logged_in(self) -> bool:
        return "https://okta.supplier-prod.kroger.com/oauth2/" in self.driver.current_url
