from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from datetime import date
from selenium.common.exceptions import TimeoutException
import os
import pathlib
import pandas as pd
import numpy as np
import shutil
from accelerators.implementations.amazon.base import AmazonBase

class AmazonRemitAccelerator(AmazonBase):
    display_name = 'Amazon Remittance Downloader'
    input_display_names = {'from_date': 'Start Date', 'to_date': 'End Date'}
    info_accelerator = ''
    
    async def run(self, from_date: date, to_date: date) -> str:
        wait = WebDriverWait(self.driver, 10)
        await self.info("Please wait...")
        delta = to_date - from_date
        if delta.days <= 90:
            account_select = 'US - Beiersdorf Inc. (current)'
            if not await self.login():
                return
            reports_path = self.output_path
            browser_default_path = self.output_path
            self.log.debug("[+] Remittance Steps ")
            wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
            self.driver.get('https://vendorcentral.amazon.com/hz/vendor/members/remittance/home')
            from_date_value = f"{from_date.month}/{from_date.day}/{from_date.year}"
            to_date_value = f"{to_date.month}/{to_date.day}/{to_date.year}"
            self.log.debug(f"[+] Dates provided by User ::: {from_date} {to_date}")
            try:
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Maybe later "]'))).click()
                self.log.debug("Window Close Success...!")
            except TimeoutException:
                self.log.debug("[+] No window Popups")
                
            main_window_handle = self.driver.current_window_handle
            all_window_handles = self.driver.window_handles
            for window_handle in all_window_handles:
                if window_handle != main_window_handle:
                    self.driver.switch_to.window(window_handle)
                    self.driver.close()

            self.driver.switch_to.window(main_window_handle)
            reports_path = os.path.join(reports_path, account_select)
            for directory in ["Remittance Raw Data", "Payments Data", "Remittance Final Data"]:
                os.makedirs(os.path.join(reports_path, directory), exist_ok=True)
            try:
                feedback_page = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='hmd2f-trigger-tab']/a/img")))
                feedback_page.click()
            except TimeoutException:
                self.log.debug("feedback_page not found")
            try:
                element = wait.until(EC.element_to_be_clickable((By.CLASS_NAME, "a-container")))
                self.driver.execute_script("arguments[0].scrollIntoView();", element)
            except TimeoutException:
                self.log.debug("[+] Scroll Not Possible")
            self.driver.find_elements(By.CLASS_NAME, "a-input-text-addon")[0].click()  # Click the calendar option for From date
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div[5]/form/div[1]/div[2]/div[5]/span/div[1]/div/div[1]/div[2]/div/div/div/input"))).clear()  # Clear From date field
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div[5]/form/div[1]/div[2]/div[5]/span/div[1]/div/div[1]/div[2]/div/div/div/input"))).send_keys(str(from_date_value))  # Enter From Date into from date input field
            self.driver.find_elements(By.CLASS_NAME, "a-input-text-addon")[1].click()  # Click the calendar option for To date
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div[5]/form/div[1]/div[2]/div[5]/span/div[2]/div/div[1]/div[2]/div/div/div/input"))).clear()  # Clear To date field
            wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div[5]/form/div[1]/div[2]/div[5]/span/div[2]/div/div[1]/div[2]/div/div/div/input"))).send_keys(str(to_date_value))  # Enter To Date into to date input field
            self.driver.find_elements(By.CLASS_NAME, "a-input-text-addon")[1].click()  # Click the calendar option for To date
            try:
                feedback_page = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='hmd2f-trigger-tab']/a/img")))
                feedback_page.click()
            except TimeoutException:
                self.log.debug("feedback_page not found")
                
            feedback = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='hmd2f-exit']/img")))
            feedback.click()
            wait.until(EC.element_to_be_clickable((By.ID, "remittanceSearchForm-submit"))).click()  # Click on Search button
            try:
                feedback_page = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='hmd2f-trigger-tab']/a/img")))
                feedback_page.click()
            except TimeoutException:
                self.log.debug("feedback_page not found")
            try:
                feedback = wait.until(EC.element_to_be_clickable((By.XPATH, "//*[@id='hmd2f-exit']/img")))
                feedback.click()
            except TimeoutException:
                self.log.debug("feedback not found")
            try:
                WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "remittance-home-select-all"))).click()
            except TimeoutException:
                await self.error('Invalid! Remittance data not found. Please try again with valid date range.')
                return
            WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.ID, "remittance-home-export-link"))).click()
            await self.wait_for_output(lambda files: 'Payments.xlsx' in files)
            self.log.debug("[+] Stage Download output")
            for file in os.listdir(browser_default_path):
                self.log.debug(f"checking for downloaded file...{file}")
                if file.startswith("Payments") and file.endswith(".xlsx"):
                    raw_file_name = pathlib.Path(browser_default_path, file).stem

                    read_excel = pd.read_excel(pathlib.Path(browser_default_path, raw_file_name + ".xlsx"))
                    await self.info('File download success...')
                    read_excel.to_csv(pathlib.Path(reports_path, "Remittance Raw Data", raw_file_name + ".csv"), index=None, header=None)

                    shutil.move(pathlib.Path(browser_default_path, raw_file_name + ".xlsx"), pathlib.Path(reports_path, "Remittance Raw Data", raw_file_name + ".xlsx"))

            await self.info('Processing...')
            for file in os.listdir(pathlib.Path(reports_path, "Remittance Raw Data")):
                self.log.debug("[+] Stage Remittance Raw")
                if file.startswith("Payments") and file.endswith(".csv"):
                    whole_data = pd.read_csv(pathlib.Path(reports_path, "Remittance Raw Data", file), skiprows=2, encoding='cp1252')
                    payments_data = whole_data.loc[whole_data['Payment Type'] == "EFT"]
                    count_for_next_dataframe = whole_data['Payment Type'].value_counts()["EFT"]
                    skip_rows = count_for_next_dataframe + 6
                    whole_data_secondary_data = pd.read_csv(pathlib.Path(reports_path, "Remittance Raw Data", file), skiprows=skip_rows, encoding='cp1252')
                    if whole_data_secondary_data.columns[0] != "Payment Number":
                        skip_rows += 1
                        whole_data_secondary_data = pd.read_csv(pathlib.Path(reports_path, "Remittance Raw Data", file), skiprows=skip_rows, encoding='cp1252')
                    else:
                        print("No Payment Issue")
                    whole_data_secondary_data["Payment Number"] = whole_data_secondary_data["Payment Number"].astype(str)
                    consolidate_payment_data_frame = pd.merge(whole_data_secondary_data, payments_data, on='Payment Number', how='left')
                    columns_addon = ['BDF Record Type', 'BDF Tolerance', 'BDF Expiry', 'BDF Reason Code ID', 'BDF Reason Code', 'BDF Reason Description']
                    for col in columns_addon:
                        consolidate_payment_data_frame[f'{col}'] = ''
                    conditions = [
                        consolidate_payment_data_frame['Amount Paid'] < 0,
                        (consolidate_payment_data_frame['Amount Paid'] > 0) & (consolidate_payment_data_frame['Invoice Number'].str.match(r'^\d{10}$')),
                        (consolidate_payment_data_frame['Amount Paid'] > 0) & (~consolidate_payment_data_frame['Invoice Number'].str.match(r'^\d{10}$'))
                    ]
                    choices = ['Deduction', 'Invoice Payment', 'Repayment']
                    consolidate_payment_data_frame['BDF Record Type'] = np.select(conditions, choices, default='-')
                    
                    tolerance_conditions = [
                        (consolidate_payment_data_frame['BDF Record Type'] == 'Deduction') & (consolidate_payment_data_frame['Amount Paid'].abs() > 0) & (consolidate_payment_data_frame['Amount Paid'].abs() < 200),
                        (consolidate_payment_data_frame['BDF Record Type'] == 'Deduction') & (consolidate_payment_data_frame['Amount Paid'].abs() > 200)
                    ]
                    tolerance_choices = ['UT', 'OT']
                    consolidate_payment_data_frame['BDF Tolerance'] = np.select(tolerance_conditions, tolerance_choices, default='-')
                    
                    consolidate_payment_data_frame['Payment Date'] = pd.to_datetime(consolidate_payment_data_frame['Payment Date'])
                    consolidate_payment_data_frame['BDF Expiry'] = consolidate_payment_data_frame['Payment Date'] + pd.Timedelta(days=45)

                    reason_code_conditions = [
                        consolidate_payment_data_frame['Invoice Number'].str.endswith('SC'),
                        consolidate_payment_data_frame['Invoice Number'].str.endswith('SC-'),
                        consolidate_payment_data_frame['Invoice Number'].str.endswith('VC'),
                        consolidate_payment_data_frame['Invoice Number'].str.endswith('PC'),
                        consolidate_payment_data_frame['Invoice Number'].str.startswith('6403'),
                        consolidate_payment_data_frame['Invoice Number'].str.startswith('APAUDITUS'),
                        consolidate_payment_data_frame['Invoice Number'].str.startswith('IPAPAUDUS'),
                        consolidate_payment_data_frame['Invoice Number'].str.startswith('6430'),
                        consolidate_payment_data_frame['Invoice Number'].str.startswith('6440'),
                        consolidate_payment_data_frame['Invoice Number'].str.contains('PROVISION', case=False),
                        consolidate_payment_data_frame['Invoice Number'].str.endswith('AMS'),
                        consolidate_payment_data_frame['Invoice Number'].str.endswith('ADV')
                    ]
                    reason_code_ID_choices = [101, 101, 108, 201, 306, 306, 306, 306, 306, 311, 313, 313]
                    reason_code_choices = ['SHORTAGE', 'SHORTAGE', 'VENDOR FINE', 'PRICING', 'COOP', 'COOP', 'POST AUDIT', 'COOP', 'COOP', 'PROVISION', 'OMD', 'OMD']
                    consolidate_payment_data_frame['BDF Reason Code ID'] = np.select(reason_code_conditions, reason_code_ID_choices, default='-')
                    consolidate_payment_data_frame['BDF Reason Code'] = np.select(reason_code_conditions, reason_code_choices, default='-')
                    consolidate_payment_data_frame['BDF Reason Description'] = consolidate_payment_data_frame['BDF Reason Code']
                    await self.info('Data transformation...')
            
            from_dt = from_date.strftime("%m%d%Y")
            to_dt = to_date.strftime("%m%d%Y")

            if len(consolidate_payment_data_frame) > 0:
                consolidate_payment_data_frame.to_csv(os.path.join(self.output_path, f"AMZN_Remittance_Date_{from_dt}-{to_dt}_Check-Detail-Payments.csv"), index=False)
                await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
                return os.path.join(self.output_path, f"AMZN_Remittance_Date_{from_dt}-{to_dt}_Check-Detail-Payments.csv")
            else:
                await self.error('Invalid! Remittance data not found. Please try again with valid date range.')
        else:
            await self.error(f"Date range difference exceeds 90 days: {delta.days} days")
            return
