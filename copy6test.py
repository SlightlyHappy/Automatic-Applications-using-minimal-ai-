import os
import time
import logging
import json
import re

from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

import google.generativeai as genai

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.FileHandler('gemini_automation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NaukriAutomation:
    def __init__(self):
        load_dotenv()
        self.username = os.getenv("NAUKRI_USERNAME")
        self.password = os.getenv("NAUKRI_PASSWORD")
        if not self.username or not self.password:
            raise ValueError("Please set NAUKRI_USERNAME and NAUKRI_PASSWORD in your .env file")

        self.driver = None
        self.wait = None

        logger.debug("Initializing Google Gemini client...")
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        generation_config = {
            "temperature": 1,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
            "response_mime_type": "text/plain",
        }
        system_instruction = """
Modify this as needed - don't just install and run the script. That's dangerous you can get hacked.  
Respond in the following JSON format:

"action": "select" or "input",
"element": "exact text of the option to select",
"text": "text to input if action is input",
"explanation": "brief reasoning for the choice"
        """
        self.model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            generation_config=generation_config,
            system_instruction=system_instruction,
        )
        self.chat_session = self.model.start_chat(history=[])
        logger.debug("Google Gemini client initialized")

    def setup_driver(self):
        try:
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--start-maximized")
            chrome_options.add_argument("--disable-notifications")
            logger.debug("Setting up Chrome WebDriver...")
            self.driver = webdriver.Chrome(
                service=ChromeService(ChromeDriverManager().install()),
                options=chrome_options
            )
            self.wait = WebDriverWait(self.driver, 15)
            logger.info("WebDriver initialized successfully")
        except WebDriverException as e:
            logger.error(f"Failed to initialize WebDriver: {str(e)}", exc_info=True)
            raise

    def analyze_and_answer_question(self, chat_html):
        try:
            logger.debug(f"Sending chat HTML to Google Gemini for analysis: {chat_html[:200]}...")
            response = self.chat_session.send_message(chat_html)
            answer = response.text.strip()

            # Remove code block markers if present (e.g., ``````)
            if answer.startswith("```"):
                answer = answer[3:]
            if answer.endswith("```"):
                answer = answer[:-3]
            answer = answer.strip()

            # Remove a leading "json" prefix if present
            if answer.lower().startswith("json"):
                answer = answer[4:].strip()

            logger.info(f"Generated answer: {answer[:200]}...")
            try:
                return json.loads(answer)
            except json.JSONDecodeError as e:
                logger.error(f"JSON decode error: {str(e)}")
                logger.error(f"Raw response: {answer}")
                return None
        except Exception as e:
            logger.error(f"Google Gemini error details: {str(e)}", exc_info=True)
            return None

    def handle_application_questions(self):
        try:
            logger.debug("Waiting for chat container...")
            chat_container = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "chatbot_MessageContainer"))
            )
            while True:
                chat_html = chat_container.get_attribute('outerHTML')
                gemini_response = self.analyze_and_answer_question(chat_html)
                if gemini_response:
                    action = gemini_response.get('action')
                    if action == 'select':
                        option_text = gemini_response.get('element')
                        logger.debug(f"Selecting option: {option_text}")
                        option_element = self.driver.find_element(By.XPATH, f"//label[contains(text(), '{option_text}')]")
                        option_element.click()
                    elif action == 'input':
                        input_text = gemini_response.get('text')
                        logger.debug(f"Inputting text: {input_text}")
                        input_box = self.wait.until(
                            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
                        )
                        # Clear the contenteditable element using JavaScript
                        self.driver.execute_script("arguments[0].innerHTML = '';", input_box)
                        # Input the text and dispatch an input event to simulate typing
                        self.driver.execute_script("arguments[0].innerHTML = arguments[1];", input_box, input_text)
                        self.driver.execute_script(
                            "var event = new Event('input', { bubbles: true }); arguments[0].dispatchEvent(event);",
                            input_box
                        )
                    # Click the Save button after input or selection
                    logger.debug("Clicking Save button")
                    save_button = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, "//div[@class='sendMsg' and text()='Save']"))
                    )
                    save_button.click()
                    # Allow time for the response to be processed before checking for chat updates.
                    time.sleep(2)
                    if "thank you for your responses" in chat_html.lower():
                        logger.info("Application process completed")
                        break
                time.sleep(2)  # Wait for the next question to load
        except Exception as e:
            logger.error(f"Error handling application questions: {str(e)}", exc_info=True)

    def login(self):
        try:
            logger.info("Navigating to login page")
            self.driver.get("https://www.naukri.com/nlogin/login")
            username_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "usernameField"))
            )
            username_field.clear()
            username_field.send_keys(self.username)
            password_field = self.wait.until(
                EC.presence_of_element_located((By.ID, "passwordField"))
            )
            password_field.clear()
            password_field.send_keys(self.password)
            login_button = self.wait.until(
                EC.element_to_be_clickable((By.XPATH, "//button[@type='submit']"))
            )
            login_button.click()
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error during login: {str(e)}", exc_info=True)

    def search_jobs(self, job_title="Business Development Executive"):
        try:
            self.driver.get("https://www.naukri.com/")
            logger.info("Navigated to main page")
            search_bar = self.wait.until(
                EC.presence_of_element_located((By.XPATH, "//span[contains(text(),'Search jobs here')]"))
            )
            search_bar.click()
            search_input = self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "suggestor-input"))
            )
            search_input.clear()
            search_input.send_keys(job_title)
            search_input.send_keys(Keys.ENTER)
            logger.info(f"Searching for job: {job_title}")
            time.sleep(5)
            filters = {
                "Remote": "//span[@title='Remote']",
                "Hybrid": "//span[@title='Hybrid']",
                "New Delhi": "//span[@title='New Delhi']",
                "Gurugram": "//span[@title='Gurugram']"
            }
            for filter_name, xpath in filters.items():
                try:
                    filter_element = self.wait.until(
                        EC.element_to_be_clickable((By.XPATH, xpath))
                    )
                    filter_element.click()
                    time.sleep(2)
                    logger.info(f"Applied filter: {filter_name}")
                except Exception as e:
                    logger.warning(f"Could not apply filter {filter_name}: {str(e)}")
        except Exception as e:
            logger.error(f"Error during job search: {str(e)}", exc_info=True)
            raise

    def apply_to_jobs(self):
        try:
            job_cards = self.driver.find_elements(By.CLASS_NAME, "cust-job-tuple")
            logger.info(f"Found {len(job_cards)} job cards")
            for index, card in enumerate(job_cards):
                try:
                    logger.info(f"Processing job {index + 1} of {len(job_cards)}")
                    main_window = self.driver.current_window_handle
                    title = card.find_element(By.CLASS_NAME, "title")
                    job_title = title.text
                    logger.debug(f"Clicking job title: {job_title}")
                    title.click()
                    time.sleep(3)
                    new_window = [handle for handle in self.driver.window_handles if handle != main_window][0]
                    self.driver.switch_to.window(new_window)
                    logger.debug("Looking for apply button...")
                    
                    # Check for external application button
                    external_apply_button = self.driver.find_elements(By.XPATH, "//button[contains(text(), 'Apply on company website')]")
                    if external_apply_button:
                        logger.info("Application requires external website. Skipping.")
                        self.driver.close()
                        self.driver.switch_to.window(main_window)
                        continue
                    
                    apply_button = self.wait.until(
                        EC.element_to_be_clickable((By.ID, "apply-button"))
                    )
                    logger.debug("Clicking apply button")
                    apply_button.click()
                    self.handle_application_questions()
                    logger.debug("Closing job window")
                    self.driver.close()
                    self.driver.switch_to.window(main_window)
                except Exception as e:
                    logger.error(f"Error processing job card {index + 1}: {str(e)}", exc_info=True)
                    continue
        except Exception as e:
            logger.error(f"Error in apply_to_jobs: {str(e)}", exc_info=True)

    def close(self):
        if self.driver:
            self.driver.quit()


def main():
    naukri_bot = NaukriAutomation()
    try:
        naukri_bot.setup_driver()
        naukri_bot.login()
        naukri_bot.search_jobs()
        naukri_bot.apply_to_jobs()
    except Exception as e:
        logger.error(f"Main execution failed: {str(e)}", exc_info=True)
    finally:
        naukri_bot.close()


if __name__ == "__main__":
    main()
