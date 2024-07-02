from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException
import os
import zipfile
from accelerators import Accelerator
from datetime import datetime
class CHROPodAccelerator(Accelerator):
    display_name = "CHRO - POD Downloader"
    group_name = "C.H. Robinson"
    start_url = "https://account.chrobinson.com/"
    input_display_names = {'invoice_numbers': 'Enter PRO#s'}
    info_accelerator = ''
    
    async def run(self, invoice_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
        WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        await self.info('Running...')
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()

                user_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-username"]')))
                user_input.clear()
                user_input.send_keys(username)
                auth_tocken = False
                try:
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-password"]')))
                    auth_tocken = True
                except TimeoutException:
                    auth_tocken = False
                    self.log.debug('method change for login...')
                if not auth_tocken:
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"][@value="Sign in"]')))
                    submit_login.click()
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-password"]')))
                    pass_input.clear()
                    pass_input.send_keys(password)
                else:
                    pass_input = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-password"]')))
                    pass_input.clear()
                    pass_input.send_keys(password)
                    submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                    submit_login.click()
                try:
                    await self.info('Please wait...')
                    WebDriverWait(self.driver, 60).until(EC.invisibility_of_element((By.XPATH, '//*[@type="submit"]')))
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                await self.info('Great! You’ve successfully logged into the targeted portal.')
        
        WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
        
        for invoice_number in set(invoice_numbers):
            if len(invoice_number) > 7:
                invoice_number = invoice_number.strip()
                await self.info(f'Processing invoice - {invoice_number}')
                self.driver.get(f'https://online.chrobinson.com/search/#/?view=purchaseOrder&page=1&search={invoice_number}&customsStatus=&status=&riskLevels=&account=&supplier=&transportMode=&shippingMethod=&timeFrame=&timeFrames=&sortByDirection=desc&sortByField=earliestPickupDate&bookingFromDate=&bookingToDate=&pickupFromDate=&pickupToDate=&deliveryFromDate=&deliveryToDate=&activeTimeframePanel=Pre-Defined&currentTimeframe=&pickupLocation=&deliveryLocation=&deliveryLocationName=&portLoading=&countryOfOrigin=&countryOfExport=&entryPort=&bookingDateType=Requested&pickupDateType=Requested&deliveryDateType=Requested&redirecting=&shipDateType=Requested&shipFromDate=&shipToDate=&entrySubmittedDateType=Submitted&entrySubmittedFromDate=&entrySubmittedToDate=&entryPortArrivalDateType=Expected&entryPortArrivalFromDate=&entryPortArrivalToDate=&entryType=&carrier=&disruption=&box=&isClusterView=&flightNumber=&vesselImoNumber=&facilityStop=')
                WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                self.driver.get(f'https://online.chrobinson.com/search/#/?view=purchaseOrder&page=1&search={invoice_number}&customsStatus=&status=&riskLevels=&account=&supplier=&transportMode=&shippingMethod=&timeFrame=&timeFrames=&sortByDirection=desc&sortByField=earliestPickupDate&bookingFromDate=&bookingToDate=&pickupFromDate=&pickupToDate=&deliveryFromDate=&deliveryToDate=&activeTimeframePanel=Pre-Defined&currentTimeframe=&pickupLocation=&deliveryLocation=&deliveryLocationName=&portLoading=&countryOfOrigin=&countryOfExport=&entryPort=&bookingDateType=Requested&pickupDateType=Requested&deliveryDateType=Requested&redirecting=&shipDateType=Requested&shipFromDate=&shipToDate=&entrySubmittedDateType=Submitted&entrySubmittedFromDate=&entrySubmittedToDate=&entryPortArrivalDateType=Expected&entryPortArrivalFromDate=&entryPortArrivalToDate=&entryType=&carrier=&disruption=&box=&isClusterView=&flightNumber=&vesselImoNumber=&facilityStop=')
                WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                pan_order = WebDriverWait(self.driver, 160).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-controls="search-view-tabs-component-pane-order"]')))
                stable_tocken = False
                try:
                    self.driver.execute_script("arguments[0].click();", pan_order)
                    stable_tocken = True
                except TimeoutException:
                    self.log.debug('Page Load failed Re-try again with attemp 1')
                    stable_tocken = False

                if not stable_tocken:
                    try:
                        WebDriverWait(self.driver, 80).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-controls="search-view-tabs-component-pane-order"]'))).click()
                        stable_tocken = True
                    except TimeoutException:
                        self.log.debug('Page Load failed Re-try again with attemp 2')
                        stable_tocken = False
                if not stable_tocken:
                    self.log.debug('Page Load failed Re-try again with attemp 3')
                    await self.info(f'No record found for POD - {invoice_number}')
                    continue
                WebDriverWait(self.driver, 80).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    results = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search-view-tabs-component-pane-purchaseOrder"]/div/div[2]/div/div/div[1]/h3'))).text
                    if "We couldn't find any results that match your search." in results:
                        await self.info(f'No record found for POD - {invoice_number}')
                        continue
                except TimeoutException:
                    self.log.debug(f'Record found for POD - {invoice_number}')
                    
                try:
                    WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Skip"]'))).click()
                except TimeoutException:
                    self.log.debug('not find close button')
                wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-controls="search-view-tabs-component-pane-order"]'))).click()
                tocken_id = False
                try:
                    doc_id = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="search-view-tabs-component-pane-order"]/div/div[3]/div/div/div[2]/div[2]/div[1]/div/div/div[2]/a/span'))).text
                    tocken_id = True
                except TimeoutException:
                    tocken_id = False

                if not tocken_id:
                    await self.info(f'No record found for POD - {invoice_number}')
                    continue
                else:
                    doc_id_link = f"https://online.chrobinson.com/ordersdetail/#/{doc_id}"
                    print('find docID')
                    self.driver.get(doc_id_link)
                    WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Skip"]'))).click()
                except TimeoutException:
                    self.log.debug('not find close button')
                tocken_toor = False
                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ordersDetail-tab-documents"]'))).click()
                    tocken_toor = True
                except TimeoutException:
                    tocken_toor = False
                if not tocken_toor:
                    try:
                        WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Skip"]'))).click()
                    except TimeoutException:
                        self.log.debug('not find close button')
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="ordersDetail-tab-documents"]'))).click()
                    WebDriverWait(self.driver, 50).until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                table = WebDriverWait(self.driver, 50).until(EC.element_to_be_clickable((By.XPATH, '//*[@aria-label="Documents Table"]')))
                rows = table.find_elements(By.TAG_NAME, 'tr')
                for download_index in range(1, int(len(rows))):
                    download_div = wait.until(EC.element_to_be_clickable((By.XPATH, f'/html/body/div/div/section/div/div[3]/div[3]/div[7]/div/div[2]/table/tbody/tr[{download_index}]/td[2]/button')))
                    if download_div.text.startswith('DOC'):
                        download_div.click()
                        await self.wait_for_output(lambda files: f'{download_div.text}-{doc_id}.pdf' in files)
                        os.rename(os.path.join(self.output_path, f'{download_div.text}-{doc_id}.pdf'), os.path.join(self.output_path, f"CHRO_POD Backup_{download_div.text}-PRO-{invoice_number}-{doc_id}.pdf"))
                        await self.info(f'Pod DOC - {invoice_number} - {download_div.text}-{doc_id}.pdf, Processed')
                    elif download_div.text.startswith('Pallet'):
                        download_div.click()
                        await self.wait_for_output(lambda files: f'Pallet Label-{doc_id}.pdf' in files)
                        os.rename(os.path.join(self.output_path, f'Pallet Label-{doc_id}.pdf'), os.path.join(self.output_path, f"CHRO_POD Backup_Label{download_div.text}-PRO-{invoice_number}-{doc_id}.pdf"))
                        await self.info(f'Pallet Label- - {invoice_number} - {download_div.text}-{doc_id}.pdf, Processed')

        pdf_files = [file for file in os.listdir(self.output_path) if file.endswith('.pdf')]
        if pdf_files:
            await self.info("Processing...")
            current_date = datetime.now()
            formatted_date = current_date.strftime("%m%d%Y")
            zip_filename = os.path.join(self.output_path, f"CHRO_POD Backup_{formatted_date}")
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
            wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="okta-signin-username"]')))
            return False
        except Exception:
            return True
