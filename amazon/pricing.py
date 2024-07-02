from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from glob import glob
import os
import pandas as pd
import shutil
from selenium.common.exceptions import TimeoutException
from accelerators.implementations.amazon.base import AmazonBase
from datetime import datetime

class AmazonPricingAccelerator(AmazonBase):
    display_name = 'Amazon Pricing Backup Downloader'
    input_display_names = {'invoice_numbers': 'Invoice Numbers'}
    info_accelerator = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 10)
        await self.info("Running...")
        if not await self.login():
            return
        selected_account = 'US - Beiersdorf Inc. (current)'
        report_output_path = os.path.join(self.output_path, "Pricing", "Pricing_SKU", selected_account)
        self.log.debug("[+] Pricing Steps ")
        final_df_new = pd.DataFrame()
        browser_default_path = self.output_path
        os.makedirs(report_output_path, exist_ok=True)
        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        for invoice_number in set(invoice_numbers):
            if len(invoice_number) > 3:
                invoice_number_url = invoice_number.replace('PC', '')
                invoice_url = f"https://vendorcentral.amazon.com/hz/vendor/members/inv-mgmt/invoice-po-search?searchByNumberToken={invoice_number_url}"
                self.driver.get(invoice_url)
                WebDriverWait(self.driver, 40).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                counter = 0
                for i in range(1, 4):
                    if counter == 2:
                        break
                    try:
                        alert_warning = WebDriverWait(self.driver, 4).until(EC.element_to_be_clickable((By.XPATH, '//div[@id="custom-error-sub-text"]')))
                        if alert_warning.text == "We have got a very high number of requests from you and have throttled any further requests. Please reload the page after couple of minutes.":
                            print('Refreshing....')
                            self.driver.get(invoice_url)
                            counter += 1
                    except TimeoutException:
                        self.driver.get(invoice_url)
                        self.log.info('Refreshed...')
                        counter += 1
                WebDriverWait(self.driver, 100).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Maybe later "]'))).click()
                    self.log.debug("Popup Window Close Success...!")
                except TimeoutException:
                    self.log.debug("[+] No window Popups")
                main_window_handle = self.driver.current_window_handle
                all_window_handles = self.driver.window_handles
                for window_handle in all_window_handles:
                    if window_handle != main_window_handle:
                        self.driver.switch_to.window(window_handle)
                        self.driver.close()

                self.driver.switch_to.window(main_window_handle)
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')

                if wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="advancedsearchresponsemelodictable"]'))).text == "No results were found.":
                    await self.info(f"Invoice information is not available for {invoice_number}")
                else:
                    await self.info(f"Invoice information is available for {invoice_number}")
                    payment_code = self.driver.find_element(By.XPATH, '//*[@id="r0-PAYEE_CODE"]').text
                    download_url = f"https://vendorcentral.amazon.com/hz/vendor/members/inv-mgmt/invoice-details?invoiceNumber={invoice_number_url}&payeeCode={payment_code}&activeTab=lineItems"
                    self.driver.get(download_url)
                    try:
                        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = "Maybe later "]'))).click()
                        self.log.debug("Popup Window Close Success...!")
                    except TimeoutException:
                        self.log.debug("[+] No window Popups")
                    main_window_handle = self.driver.current_window_handle
                    all_window_handles = self.driver.window_handles
                    for window_handle in all_window_handles:
                        if window_handle != main_window_handle:
                            self.driver.switch_to.window(window_handle)
                            self.driver.close()
                    self.driver.switch_to.window(main_window_handle)
                    wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                    financial_button_query = EC.presence_of_element_located((By.XPATH, '//*[@id="viewFinancialDefectsButton"]/span/a'))
                    try:
                        financial_button = wait.until(financial_button_query)
                    except TimeoutException:
                        self.driver.refresh()
                        wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                        financial_button = wait.until(financial_button_query)
                    financial_button.click()
                    for a_tag in self.driver.find_elements(By.TAG_NAME, 'a'):
                        if "PPVDFCT" in str(a_tag.get_attribute('href')):
                            self.driver.get(a_tag.get_attribute('href'))
                            break
                    if 'financialscorecard/defectdetails?defectName=PPVDFCT' in self.driver.current_url:
                        WebDriverWait(self.driver, 40).until(lambda driver: driver.execute_script('return document.readyState') == 'complete')
                        wait.until(EC.presence_of_element_located((By.XPATH, '/html/body/div[1]/div[2]/div/div[5]/div[3]/a'))).click()
                        await self.wait_for_output(lambda files: 'PPV_DEFECTS_BEIH7.xlsx' in files)
                        os.rename(os.path.join(self.output_path, "PPV_DEFECTS_BEIH7.xlsx"), os.path.join(report_output_path, str(invoice_number) + ".xlsx"))
                        await self.info(f"Invoice Number - {invoice_number} Processed")
                    else:
                        await self.info(f"Invoice Number - {invoice_number} Not Processed")

        report_output_path = os.path.join(browser_default_path, "Pricing", "Pricing_SKU")
        await self.info('Processing...')
        filenames = glob(os.path.join(report_output_path, selected_account, "*.xlsx"))
        for file in filenames:
            consolidate_dataframe = pd.read_excel(file, dtype='object')
            final_df_new = pd.concat([final_df_new, consolidate_dataframe], ignore_index=True)
        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        if len(final_df_new) > 0:
            final_df_new.to_excel(os.path.join(report_output_path + "AMZN_Pricing_Backup_downloader_Consolidated.xlsx"), index=False, header=True)
            report_output_path = os.path.join(browser_default_path, "Pricing")
            zip_filename = os.path.join(self.output_path, f"AMZN_Pricing_Backup_{formatted_date}")
            shutil.make_archive(zip_filename, 'zip', report_output_path)
            await self.info("Success! The targeted data has been successfully extracted from the portal.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Invalid! No backup data found. Please try again with valid reference numbers.')
