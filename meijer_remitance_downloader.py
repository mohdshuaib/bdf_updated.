from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
from accelerators import Accelerator
import os
import zipfile
from datetime import datetime
 
class MeijerRemittanceAccelerator(Accelerator):
    display_name = "Meijer Remittance Downloader"
    group_name = "Meijer"
    start_url = "https://vendornet.meijer.com/Welcome"
    info_accelerator = ''
    
    async def run(self) -> str:
        wait = WebDriverWait(self.driver, 30)
        async with self.authenticator() as auth:
            await self.info('Running...')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                user_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@autocomplete='username']")))
                user_input.clear()
                user_input.send_keys(username)
                auth_tocken = False
                try:
                    pass_input = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[@type='password']")))
                    auth_tocken = True
                except TimeoutException:
                    auth_tocken = False
                    self.log.debug('method change for login...')
                if not auth_tocken:
                    submit_login = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//input[@type="submit"]')))
                    submit_login.click()
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@type='password']")))
                    pass_input.clear()
                    pass_input.send_keys(password)
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                    submit_login.click()
                else:
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@type='password']")))
                    pass_input.clear()
                    pass_input.send_keys(password)
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                    submit_login.click()
                try:
                    await self.info('Please wait...')
                    WebDriverWait(self.driver, 10).until(EC.invisibility_of_element((By.XPATH, '//*[@type="submit"]')))
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info("Great! You've successfully logged into the targeted portal.")
        
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            WebDriverWait(self.driver, 30).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/ul/li[3]/div/div[1]/span[1]")))
        except TimeoutException:
            self.log.info('order_payment element not found')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        order_payment = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div/div/ul/li[3]/div/div[1]/span[1]")))
        self.driver.execute_script("arguments[0].click();", order_payment)
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/div[2]")))
        except TimeoutException:
            self.log.info('payment_claims_drop element not found')
        payment_claims_drop = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/div[2]")))
        self.driver.execute_script("arguments[0].click();", payment_claims_drop)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/ul/li[1]/div/div/span")))
        except TimeoutException:
            self.log.info('account_pay_query element not found')
        account_pay_query = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[2]/div[2]/div[2]/div/div/div[1]/ul/li[9]/ul/li[1]/div/div/span")))
        self.driver.execute_script("arguments[0].click();", account_pay_query)
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div/div/p[5]/a")))
        except TimeoutException:
            self.log.info('for switching  element not found')
        wait.until(EC.element_to_be_clickable((By.XPATH, '/html/body/div[3]/div/div/p[5]/a'))).click()
        try:
            WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Sales Invoice PDF']")))
        except TimeoutException:
            self.log.info('not available advanced filter')
        await self.info(f'first window before new window:{self.driver.current_url}')
        self.driver.switch_to.window(self.driver.window_handles[-1])
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        await self.info(f'secondary window before:{self.driver.current_url}')
        try:
            select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
            select_vendor.click()
        except TimeoutException:
            username_element = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[1]")))
            username, password = await auth.userpass()
            username_element.send_keys(username)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            password_element = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[2]")))
            password_element.send_keys(password)
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            click_signon = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/a")))
            self.driver.execute_script("arguments[0].click();", click_signon)
            await self.info('session refreshed')
        await self.info(f'secondary window after :{self.driver.current_url}')
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
        except TimeoutException:
            self.log.info('for select_vendor  element not found')
        vendor_tocken = False
        try:
            select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
            vendor_tocken = True
        except TimeoutException:
            vendor_tocken = False
        if not vendor_tocken:
            self.driver.refresh()
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            try:
                username_element = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[1]")))
                username, password = await auth.userpass()
                username_element.send_keys(username)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                password_element = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/input[2]")))
                password_element.send_keys(password)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                click_signon = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, "/html/body/div/form/div/a")))
                self.driver.execute_script("arguments[0].click();", click_signon)
                await self.info('session refreshed')
            except TimeoutException:
                self.log.debug('username password not required..')
        try:
            select_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select")))
            select_vendor.click()
        except TimeoutException:
            self.log.debug('select_vendor not found. ')
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select/option[2]")))
        except TimeoutException:
            self.log.info('for choose_vendor  element not found')
        try:
            choose_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr/td/select/option[2]")))
            choose_vendor.click()
        except TimeoutException:
            self.log.debug('choose vendor button not found.')
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[3]/td[1]/table/tbody/tr[8]/td/input[1]")))
        except TimeoutException:
            self.log.info('click_submit_button  element not found')
        click_submit_button = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/form/table/tbody/tr[3]/td[1]/table/tbody/tr[8]/td/input[1]")))
        click_submit_button.click()
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//table[@id='grdResult']//a[contains(@id, 'txtDate')]")))
        except TimeoutException:
            self.log.info('click line:96  element not found')
        element = self.driver.find_element(By.XPATH, "//table[@id='grdResult']//a[contains(@id, 'txtDate')]")
        element.click()
        try:
            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='lnkExcelExport1']")))
        except TimeoutException:
            self.log.info('export_excel element not found')
        export_excel = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='lnkExcelExport1']")))
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        export_excel.click()
        await self.wait_for_output(lambda files: 'Remittance Detail.csv' in files)
        self.log.debug("[+] Stage Download output")
        csv_files = [filename for filename in os.listdir(self.output_path) if filename.startswith('Remittance')]
        if len(csv_files) == 1:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            os.rename(os.path.join(self.output_path, "Remittance Detail.csv"), os.path.join(self.output_path, 'MEIJ_Remittance_file_Remittance Detail.csv'))
            await self.info('Meijer_Remittance Processed')
        else:
            await self.error('Invalid! Not found or multiple files found. Please try again.')
        current_date = datetime.today().strftime('%Y%m%d')
        zip_filename = os.path.join(self.output_path, f'MEIJ_Remittance_{current_date}')
        csv_files = [file for file in os.listdir(self.output_path) if file.endswith('.csv')]
        if csv_files:
            with zipfile.ZipFile(f"{zip_filename}.zip", 'w') as zipf:
                for xl_file in csv_files:
                    xl_file_path = os.path.join(self.output_path, xl_file)
                    zipf.write(xl_file_path, arcname=xl_file)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error("try 'Invalid! Data not found. Please adjust the criteria and try again.'")
            return
        
    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 30)
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            click_log = wait.until(EC.element_to_be_clickable((By.XPATH, "//div[contains(text(), 'Log In')]")))
            click_log.click()
        except TimeoutException:
            self.log.debug('click_log button not found')
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        try:
            click_vendor = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[3]/div[1]/div[1]/div/div/span")))
            click_vendor.click()
        except TimeoutException:
            self.log.debug('vendor option not found..')
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        return 'https://vendornet.meijer.com/Welcome' in self.driver.current_url
