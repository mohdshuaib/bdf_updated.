from datetime import date, datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.action_chains import ActionChains
import os
import zipfile
from accelerators import Accelerator

class KrogerRemittanceAccelerator(Accelerator):
    display_name = 'KROG - Remittance Downloader'
    group_name = 'Kroger'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    start_url = "https://partnerpass.krogerapps.com/vendorsso/dashboard"
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
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
            self.driver.get('https://partnerpass.lavante.com/sim/supplierClaimsPaymentResult.lvp#search')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                popup = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='closeSliderButton']")))
                popup.click()
            except TimeoutException:
                self.log.debug('popup not found...')
            await self.info('Trying to fill all the required feilds.')
            new_value = from_date
            read_only = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paidDateFrom"]')))
            self.driver.execute_script("arguments[0].value = arguments[1];", read_only, new_value)
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paidDateTo"]'))).clear()
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="paidDateTo"]'))).send_keys(to_date)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="claimsPaymentBasicSearch"]'))).click()
            await self.info('filled all the required feild click on search button')
            iframe_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_results"]')))
            self.driver.switch_to.frame(iframe_element)
            button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dLabel"]')))
            self.driver.execute_script("arguments[0].click();", button)
            hover_span = self.driver.find_element(By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/a')
            ActionChains(self.driver).move_to_element(hover_span).perform()
            tocken_data = False
            try:
                click_download_csv = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/ul/li[2]/a')))
                tocken_data = True
            except TimeoutException:
                self.log.debug('No Data Found for given date Range...')
                tocken_data = False
            if not tocken_data:
                self.driver.switch_to.default_content()
                iframe_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search_results"]')))
                self.driver.switch_to.frame(iframe_element)
                button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="dLabel"]')))
                self.driver.execute_script("arguments[0].click();", button)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                click_download_csv = wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/ul/li[2]/a')))
            except TimeoutException:
                await self.error('No Data Found for given date Range...')
                return
            hover_span = self.driver.find_element(By.XPATH, '/html/body/div/form/div[2]/div[1]/div[2]/div[2]/div/div/ul/li/a')
            await self.info('hover span')
            ActionChains(self.driver).move_to_element(hover_span).perform()
            self.driver.execute_script("arguments[0].click();", click_download_csv)
            await self.info('click on download button')
            await self.wait_for_output(lambda files: 'BasicSupplierPaymentList.csv' in files)
            self.log.debug("[+] Stage Download output")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            for filename in os.listdir(self.output_path):
                if filename.startswith('BasicSupplierPaymentList'):
                    os.rename(os.path.join(self.output_path, filename), os.path.join(self.output_path, f'KROG_Remittance_Date_{from_date.replace("/","-")}_{to_date.replace("/","-")}-file_{filename}'))
            await self.info("this Kroger_Remittance data is being Processed")
            current_date = datetime.today().strftime('%Y%m%d')
            zip_filename = os.path.join(self.output_path, f"KROG_Remittance_Date_{current_date}")
            xl_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv')]
            if len(xl_files) == 1:
                with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                    for xl_file in xl_files:
                        xl_file_path = os.path.join(self.output_path, xl_file)
                        zipf.write(xl_file_path, arcname=xl_file)
                await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                return f'{zip_filename}.zip'
            else:
                await self.error('Invalid! Not found. Please try again with Date range.')
                return
        else:
            await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
            return

    def is_logged_in(self) -> bool:
        return "https://okta.supplier-prod.kroger.com/oauth2/" in self.driver.current_url
