from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from accelerators import Accelerator

class SupervaluBase(Accelerator):
    group_name = 'SUPERVALU INC'
    start_url = "https://epass.svharbor.com/epass/newDocumentSearch?isformreset=true"
    info_accelerator = ''
    
    async def login(self):
        wait = WebDriverWait(self.driver, 30)
        
        async with self.authenticator() as auth:
            if not self.is_logged_in():
                await self.info("Attempting to login…")
                username, password = await auth.userpass()

                username_element = wait.until(EC.element_to_be_clickable((By.ID, "USER")))
                username_element.clear()
                username_element.send_keys(username)

                password_element = wait.until(EC.element_to_be_clickable((By.ID, "PASSWORD")))
                password_element.clear()
                password_element.send_keys(password)

                wait.until(EC.element_to_be_clickable((By.ID, 'btnSignIn'))).click()
                if not self.is_logged_in():
                    await self.error('There was an error with the credentials. Please enter the correct username and password, or refresh the page and try again.')
                    return False
                await self.info('Great! You’ve successfully logged into the targeted portal.')
        return True

    def is_logged_in(self) -> bool:
        return 'https://epass.svharbor.com/siteminderagent/forms/svhlogin.fcc?' not in self.driver.current_url
