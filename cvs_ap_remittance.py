from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
from datetime import date
from accelerators import Accelerator
import pandas as pd
import numpy as np
from selenium.common.exceptions import StaleElementReferenceException

class CVSRemittanceAccelerator(Accelerator):
    display_name = "CVS-AP Remittance Downloader"
    group_name = "CVS Health"
    start_url = "http://apvendorportal.cvshealth.com"
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        delta = to_date - from_date
        if delta.days <= 31:
            wait = WebDriverWait(self.driver, 30)
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            await self.info('Running...')
            async with self.authenticator() as auth:
                WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    login_tocken = False
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="buttonlogin"]'))).click()
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        wait.until(EC.element_to_be_clickable((By.ID, 'j_username')))
                        login_tocken = True
                    except TimeoutException:
                        login_tocken = False
                    
                    if login_tocken:
                        await self.info('Attempting to login…')
                        username, password = await auth.userpass()
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        username_input = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.ID, 'j_username')))
                        username_input.clear()
                        username_input.send_keys(username)
                        login_auth_tocken = False
                        try:
                            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Continue']"))).click()
                            login_auth_tocken = True
                        except TimeoutException:
                            login_auth_tocken = False
                        if login_auth_tocken:
                            pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="j_password"]')))
                            pass_input.clear()
                            pass_input.send_keys(password)
                            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Log On'][@class='fn-button__text']"))).click()
                        else:
                            pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="j_password"]')))
                            pass_input.clear()
                            pass_input.send_keys(password)
                            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Log On'][@class='fn-button__text']"))).click()
                        need_otp = False
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        try:
                            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="j_otpcode"]')))
                            need_otp = True
                        except TimeoutException:
                            need_otp = False
                        
                        if need_otp:
                            self.driver.switch_to.window(self.driver.window_handles[-1])
                            enter_otp = await auth.otp()
                            otp_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="j_otpcode"]')))
                            otp_input.clear()
                            otp_input.send_keys(enter_otp)
                            wait.until(EC.element_to_be_clickable((By.XPATH, "//*[text() = 'Continue']"))).click()
                            await self.info('Please wait...')

                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        for _ in range(5):
                            try:
                                payment_button = WebDriverWait(self.driver, 20).until(
                                    EC.presence_of_element_located((By.XPATH, '//*[text()= "Payments"]'))
                                )
                                payment_button.click()
                                break
                            except StaleElementReferenceException:
                                continue

                    if not login_tocken:
                        await self.info('No Need (Octa VERIFICATION) we are using session data.')
                        self.driver.switch_to.window(self.driver.window_handles[-1])
                        for _ in range(5):
                            try:
                                payment_button = WebDriverWait(self.driver, 20).until(
                                    EC.presence_of_element_located((By.XPATH, '//*[text()= "Payments"]'))
                                )
                                payment_button.click()
                                break
                            except StaleElementReferenceException:
                                continue
                    WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    if not self.is_logged_in():
                        await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                        return
                    await self.info('Great! You’ve successfully logged into the targeted portal.')
            
            WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            tocken_process = False
            try:
                WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//bdi[text() = 'Go']")))
                tocken_process = True
            except TimeoutException:
                tocken_process = False
            if tocken_process:
                from_formatted_date = from_date.strftime("%d %b %Y")
                to_formatted_date = to_date.strftime("%d %b %Y")
                # save our page from hunting
                await self.sleep(10)
                from_date_picker = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateFrom")])[@title="Open Picker"]')))
                from_date_picker.click()
                Tocken_date_match = False
                await self.info('Setting up date range...')
                for i in range(0, 230):
                    if Tocken_date_match:
                        break
                    else:
                        try:
                            previous_month = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateFrom")])[@title="Previous"]')))
                            # next_month = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateFrom")])[@title="Next"]')))
                            start_year = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "documentDateFrom-cal--Head-B2")]'))).text
                            start_month = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "documentDateFrom-cal--Head-B1")]'))).text
                            need_match = str(from_formatted_date)[3:]
                            expected = f'{start_month[:3]} {start_year}'
                            if need_match == expected:
                                Tocken_date_match = True
                                await self.sleep(5)
                                date_pick = self.driver.find_elements(By.XPATH, f"//*[@class='sapUiCalItemText'][text()='{from_date.day}']")[0]
                                date_pick.click()
                            else:
                                previous_month = WebDriverWait(self.driver, 3).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateFrom")])[@title="Previous"]')))
                                previous_month.click()
                                Tocken_date_match = False
                        except TimeoutException:
                            from_date_picker.click()
                
                to_date_picker = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateTo")])[@title="Open Picker"]')))
                to_date_picker.click()
                Tocken_date_match = False
                for i in range(0, 230):
                    if Tocken_date_match:
                        break
                    else:
                        try:
                            previous_month = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateTo")])[@title="Previous"]')))
                            # next_month = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateTo")])[@title="Next"]')))
                            start_year = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "documentDateTo-cal--Head-B2")]'))).text
                            start_month = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "documentDateTo-cal--Head-B1")]'))).text
                            need_match = str(to_formatted_date)[3:]
                            expected = f'{start_month[:3]} {start_year}'
                            if need_match == expected:
                                Tocken_date_match = True
                                await self.sleep(3)
                                sap_date_value = str(to_date).replace('-', '')
                                date_pick = wait.until(EC.element_to_be_clickable((By.XPATH, f'//*[@data-sap-day="{sap_date_value}"]')))
                                date_pick.click()
                                
                            else:
                                previous_month = wait.until(EC.element_to_be_clickable((By.XPATH, '(//*[contains(@id, "documentDateTo")])[@title="Previous"]')))
                                previous_month.click()
                                Tocken_date_match = False
                        except TimeoutException:
                            to_date_picker.click()
                # save our page from hunting
                await self.sleep(5)
                WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, "//bdi[text() = 'Go']"))).click()
                # save our page from hunting
                await self.sleep(40)
                WebDriverWait(self.driver, 180).until(EC.element_to_be_clickable((By.XPATH, '//*[contains(@id, "downloadExcel-inner")]'))).click()
                await self.wait_for_output(lambda files: 'ETS_PAYMENTS.xlsx' in files)
                from_date = from_date.strftime("%m%d%Y")
                to_date = to_date.strftime("%m%d%Y")
                os.rename(os.path.join(self.output_path, 'ETS_PAYMENTS.xlsx'), os.path.join(self.output_path, f"CVS-AP_Remittance_Date_{from_date}-{to_date}_ETS_PAYMENTS.xlsx"))
                files = await self.wait_for_output(lambda files: f"CVS-AP_Remittance_Date_{from_date}-{to_date}_ETS_PAYMENTS.xlsx" in files)
                await self.info('Great! Remittance file Download Success')
                file_data = pd.read_excel(os.path.join(self.output_path, f"CVS-AP_Remittance_Date_{from_date}-{to_date}_ETS_PAYMENTS.xlsx"))
                columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Reason Code ID', 'BDF Reason Description']
                for col in columns_addon:
                    file_data[f'{col}'] = ''

                conditions = [
                    file_data['Net Amount'] < 0,
                    (file_data['Net Amount'] > 0) & (file_data['Invoice Number'].str.match(r'^\d{10}$')),
                    (file_data['Net Amount'] > 0) & (~dataframe_food_lion['RefDocNo'].str.match(r'^\d{10}$'))

                    (file_data['Net Amount'] > 0)]


                choices = ['Deduction', 'Invoice Payment', 'Repayment']

                file_data['BDF Record Type'] = np.select(conditions, choices, default='-')

                tolerance_conditions = [
                    (file_data['BDF Record Type'] == 'Deduction') & (file_data['Net Amount'].abs() > 0) & (file_data['Net Amount'].abs() < 200),
                    (file_data['BDF Record Type'] == 'Deduction') & (file_data['Net Amount'].abs() > 200)]

                tolerance_choices = ['UT', 'OT']

                file_data['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')

                await self.info('Data Transformation...')
                reason_code_conditions = [
                    file_data['Invoice Number'].str.endswith('W', na=False),
                    file_data['Invoice Number'].str.startswith('MCR', na=False),
                    file_data['Invoice Number'].str.startswith('DSB', na=False),
                    file_data['Invoice Number'].str.startswith('DSBDC', na=False),
                    file_data['Invoice Number'].str.endswith('V', na=False),
                    file_data['Invoice Number'].str.startswith('R', na=False),
                    file_data['Invoice Number'].str.startswith('PR#', na=False),
                    file_data['Invoice Number'].str.startswith('SBHF', na=False),
                    file_data['Invoice Number'].str.startswith('SBWF', na=False),
                    file_data['Invoice Number'].str.startswith('SCP', na=False),
                    file_data['Invoice Number'].str.startswith('SLC', na=False),
                    file_data['Invoice Number'].str.endswith('RET', na=False),
                    file_data['Invoice Number'].str.endswith('R', na=False),
                    file_data['Invoice Number'].str.endswith('PRE', na=False),
                    file_data['Invoice Number'].str.endswith('RBRE', na=False),
                    file_data['Invoice Number'].str.startswith('AT', na=False),
                    file_data['Invoice Number'].str.contains('353162', case=False, na=False),
                    file_data['Invoice Number'].str.startswith('CC', na=False),
                    file_data['Invoice Number'].str.startswith('NAV', na=False),
                    file_data['Invoice Number'].str.startswith('AI', na=False),
                    file_data['Invoice Number'].str.startswith('PRB', na=False),
                    file_data['Invoice Number'].str.startswith('PRV', na=False),
                    file_data['Invoice Number'].str.endswith('FSI', na=False),
                ]

                reason_code_ID_choices = [
                    101, 102, 102, 102, 104, 105, 105, 108, 108, 108, 108, 302, 302, 302, 302, 306, 306, 306, 306, 306, 306, 306, 312
                ]
                reason_code_choices = [
                    'SHORTAGE', 'RETURN', 'UNSALEABLE', 'UNSALEABLE', 'FULL INVOICE DEDUCTION', 'UNSALEABLE', 'UNSALEABLE', 'Add in text field:UNSALE', 'Add in text field:UNSALE', 'Add in text field:OT', 'SHELF LIFE COMPLIANCE', 'VAN RETURN', 'VAN INVOICE REVERSAL', 'VAN/DSD RELATED', 'VAN/DSD RELATED', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COOP', 'COUPONS'
                ]
                file_data['BDF Reason Code ID'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                file_data['BDF Reason Description'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                await self.info("Processing...")
                file_data.to_excel(os.path.join(self.output_path, f"CVS-AP_Remittance_Date_{from_date}-{to_date}_ETS_PAYMENTS.xlsx"), index=False)
                return os.listdir(self.output_path)[0] if len(files) else None
            else:
                await self.error('Internal Error on CVS Tool Try Again in sometime...')
                return
        else:
            await self.error(f"Date range difference exceeds 31 days: {delta.days} days")
            return

    def is_logged_in(self) -> bool:
        wait = WebDriverWait(self.driver, 10)
        try:
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@class="buttonlogin"]')))
            return False
        except Exception:
            return True
