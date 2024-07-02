from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
import os
import urllib
import shutil
from accelerators import Accelerator
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from selenium.common.exceptions import TimeoutException
from datetime import datetime
class EstesExpressAccelerator(Accelerator):
    display_name = "Estes POD Downloader"
    group_name = "Estes Express"
    start_url = "https://www.estes-express.com/myestes/home/"
    input_display_names = {'product_numbers': 'Enter PRO#s'}
    info_accelerator = ''
    
    async def run(self, product_numbers: list[str]) -> str:
        wait = WebDriverWait(self.driver, 30)
 
        async with self.authenticator() as auth:
            await self.info('Running...')
            if not self.is_logged_in():
                await self.info('Attempting to login…')
                username, password = await auth.userpass()
                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                username_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inputUsername"]')))
                username_element.clear()
                username_element.send_keys(username)
 
                password_element = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="inputPassword"]')))
                password_element.clear()
                password_element.send_keys(password)
 
                submit_login = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_login.click()

                try:
                    wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Track Now "]')))
                    await self.info('Great! You’ve successfully logged into the targeted portal.')
                except TimeoutException:
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return
                
        wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Track Now "]')))
        pod_folder_path = os.path.join(self.output_path, "Estes POD")
        os.mkdir(pod_folder_path)
        track_detail = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[text() = " Track Now "]')))
        track_detail.click()
        for invoice_number in list(set(product_numbers)):
            if len(str(invoice_number)) > 3:
                self.log.info(f"Processing Invoice - {invoice_number}")
                product_folder_path = os.path.join(pod_folder_path, f"{invoice_number}")
                os.makedirs(product_folder_path, exist_ok=True)
                self.driver.get("https://www.estes-express.com/myestes/tracking/shipments")

                criteria_text = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="criteria"]')))
                criteria_text.clear()
                criteria_text.send_keys(invoice_number)

                submit_invoice = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@type="submit"]')))
                submit_invoice.click()

                wait.until(lambda driver: self.driver.execute_script('return document.readyState') == 'complete')
                try:
                    delivery_detail = WebDriverWait(self.driver, 5).until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/div/main/div/div/app-root/div/app-tracking-results/mat-card/mat-card-content/table[2]/tbody/tr[1]/td[7]/div/span[1]")))
                except TimeoutException:
                    await self.info(f"POD no - {invoice_number} Not Found Move to Next...")
                    continue
                delivery_detail.click()

                self.driver.execute_script("window.scrollTo(0, 1000);")
                try:
                    delivery_receipt = wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/app-root/div/main/div/div/app-root/div/app-tracking-results/mat-card/mat-card-content/table[2]/tbody/tr[2]/td/div/div/div/div[6]/table/tbody/tr[8]/td/a")))
                except TimeoutException:
                    await self.info(f"POD no - {invoice_number} Not Found Move to Next...")
                    continue
                main_window = self.driver.current_window_handle
                delivery_receipt.click()
                self.driver.switch_to.window(self.driver.window_handles[-1])
                image_elements = self.driver.find_elements(By.CSS_SELECTOR, "img")

                for idx, img in enumerate(image_elements):
                    img_url = img.get_attribute("src").strip()
                    image_file_path = os.path.join(product_folder_path, f'product_of_delivery-{invoice_number}_{idx+1}.gif')
                    urllib.request.urlretrieve(img_url, image_file_path)
                self.driver.close()
                await self.info(f"Processing Invoice - {invoice_number}")
                self.driver.switch_to.window(main_window)

        os.mkdir(os.path.join(self.output_path, "POD Output"))
        output_folder = os.path.join(self.output_path, "POD Output")
        self.log.info("Processing...")
        for folder_name in os.listdir(pod_folder_path):
            folder_path = os.path.join(pod_folder_path, folder_name)
            if os.path.isdir(folder_path) and len(os.listdir(folder_path)) > 0:
                pdf_path = os.path.join(output_folder, f"ESTE_POD Backup_PRO_{folder_name}.pdf")
                c = canvas.Canvas(pdf_path, pagesize=letter)
                image_files = [f for f in os.listdir(folder_path) if f.endswith(('.gif'))]
                for i, image_file in enumerate(image_files):
                    img = Image.open(os.path.join(folder_path, image_file))
                    c.setPageSize((img.width, img.height))
                    c.drawImage(os.path.join(folder_path, image_file), 0, 0, img.width, img.height)
                    if i != len(image_files) - 1:
                        c.showPage()
                c.save()

        current_date = datetime.now()
        formatted_date = current_date.strftime("%m%d%Y")
        zip_filename = os.path.join(self.output_path, f"ESTE_POD Backups_{formatted_date}")
        files = os.listdir(output_folder)
        if len(files) >= 1:
            shutil.make_archive(zip_filename, 'zip', output_folder)
            await self.info("Success! The targeted data has been successfully extracted from the portal. Click the button below to download locally.")
            return f'{zip_filename}.zip'
        else:
            await self.error('Not found! Tracking information unavailable')
            return
   
    def is_logged_in(self) -> bool:
        return '/myestes/home/login' not in self.driver.current_url
