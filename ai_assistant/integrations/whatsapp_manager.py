import os
import logging
import json
import re
import time
from typing import Dict, Any, Optional, List
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
import urllib.parse
from selenium.webdriver import ActionChains
from urllib.parse import quote
from selenium.webdriver.common.keys import Keys

logger = logging.getLogger("ai_assistant")

class WhatsAppManager:
    """
    Class for managing WhatsApp operations through the AI Assistant.
    Supports sending messages via WhatsApp Web using Selenium.
    """
    
    def __init__(self, config_path=None):
        """
        Initialize the WhatsApp manager.
        
        Args:
            config_path (str, optional): Path to the configuration file
        """
        self.config_path = config_path or os.path.join(os.path.expanduser("~"), ".aiassistant", "config.json")
        self.load_config()
        self.driver = None
        self.is_connected = False
    
    def load_config(self):
        """Load WhatsApp configuration from the config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    self.config = config.get('whatsapp', {})
            else:
                self.config = {}
                
            logger.info("WhatsApp configuration loaded")
        except Exception as e:
            logger.error(f"Error loading WhatsApp configuration: {str(e)}")
            self.config = {}
    
    def save_config(self):
        """Save WhatsApp configuration to the config file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
            else:
                config = {}
            
            # Update WhatsApp config
            config['whatsapp'] = self.config
            
            # Ensure the directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
                
            logger.info("WhatsApp configuration saved")
        except Exception as e:
            logger.error(f"Error saving WhatsApp configuration: {str(e)}")
    
    def configure(self, auto_login: bool = False, remember_session: bool = True) -> bool:
        """
        Configure WhatsApp settings.
        
        Args:
            auto_login (bool): Whether to automatically try to log in at startup
            remember_session (bool): Whether to remember the session cookies
            
        Returns:
            bool: True if configuration was successful, False otherwise
        """
        try:
            # Update configuration
            self.config['auto_login'] = auto_login
            self.config['remember_session'] = remember_session
            
            # Save the updated configuration
            self.save_config()
            logger.info("WhatsApp configuration updated successfully")
            return True
        except Exception as e:
            logger.error(f"Error configuring WhatsApp: {str(e)}")
            return False
    
    def connect(self) -> bool:
        """
        Connect to WhatsApp Web.
        
        Returns:
            bool: True if connection is successful, False otherwise
        """
        if self.is_connected and self.driver:
            logger.info("Already connected to WhatsApp Web")
            return True
            
        logger.info("Starting WhatsApp Web connection attempt")
        
        try:
            # Set up Chrome options
            chrome_options = Options()
            
            # Directory for user data - used to remember login sessions
            user_data_dir = os.path.join(os.path.expanduser('~'), '.aiassistant', 'whatsapp_data')
            logger.info(f"Using Chrome user data directory: {user_data_dir}")
            os.makedirs(user_data_dir, exist_ok=True)
            
            # Add Chrome options for better compatibility
            if self.config.get('remember_session', True):
                chrome_options.add_argument(f"user-data-dir={user_data_dir}")
            
            # Add debugging options to improve stability
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--window-size=1200,800")
            chrome_options.add_argument("--remote-debugging-port=9222")
            
            # Try to use a more stable approach for headless mode if specified
            if self.config.get('headless', False):
                chrome_options.add_argument("--headless=new")
                logger.info("Using headless mode for Chrome")
            
            logger.info("Initializing Chrome driver...")
            
            # Try using a direct path for chromedriver if available
            chromedriver_path = self.config.get('chromedriver_path')
            if chromedriver_path and os.path.exists(chromedriver_path):
                logger.info(f"Using custom ChromeDriver path: {chromedriver_path}")
                service = Service(executable_path=chromedriver_path)
            else:
                # Otherwise let webdriver_manager download it
                logger.info("Using webdriver_manager to get ChromeDriver")
                service = Service(ChromeDriverManager().install())
            
            # Initialize the Chrome driver
            self.driver = webdriver.Chrome(service=service, options=chrome_options)
            logger.info("Chrome driver initialized successfully")
            
            # Open WhatsApp Web
            logger.info("Opening WhatsApp Web...")
            self.driver.get("https://web.whatsapp.com/")
            
            # Check if the page loaded correctly
            if "whatsapp" not in self.driver.current_url.lower():
                logger.error(f"Failed to load WhatsApp Web. Current URL: {self.driver.current_url}")
                self.driver.quit()
                self.driver = None
                return False
            
            # Wait for QR code scan or for WhatsApp to load
            try:
                logger.info("Waiting for WhatsApp Web to load (looking for chat-list)...")
                WebDriverWait(self.driver, 30).until(
                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='chat-list']"))
                )
                logger.info("Chat list found - connection successful")
                self.is_connected = True
                logger.info("Connected to WhatsApp Web successfully")
                return True
                
            except TimeoutException:
                # Handle timeout - check for QR code or other elements
                logger.warning("Timeout looking for chat list, checking for QR code or other elements")
                
                # Default error message in case we can't determine the exact issue
                error_msg = "Could not establish connection to WhatsApp Web"
                
                # Try different selectors to find the QR code or landing page elements
                qr_selectors = [
                    # Newest selectors for QR code in WhatsApp Web
                    "//div[contains(@data-ref, 'qr')]",
                    "//div[contains(@class, 'two') and contains(@class, 'phone')]//canvas",
                    "//div[contains(@class, '_3ArsE')]//canvas",
                    "//div[contains(@class, '_2tRJL')]/canvas",  # Recent class observed
                    "//div[@class='_2I5ox']/canvas",  # Another recent class
                    
                    # Standard selectors for QR code
                    "//canvas[contains(@aria-label, 'Scan me!')]",
                    "//div[contains(@data-testid, 'qrcode')]//canvas",
                    "//div[contains(@data-testid, 'qr-code-canvas')]",
                    "//div[contains(@class, 'landing-wrapper')]//canvas",
                    
                    # More general fallbacks
                    "//canvas",
                    
                    # Text-based detection for landing page
                    "//*[contains(text(), 'To use WhatsApp on your computer')]",
                    "//*[contains(text(), 'Use WhatsApp on your computer')]",
                    "//div[contains(text(), 'WhatsApp Web')]"
                ]
                
                qr_found = False
                for selector in qr_selectors:
                    try:
                        qr_element = self.driver.find_element(By.XPATH, selector)
                        if qr_element:
                            logger.info(f"Found QR code or landing element with selector: {selector}")
                            logger.info("QR code found. Please scan the QR code to log in to WhatsApp Web")
                            qr_found = True
                            
                            # Wait longer for user to scan QR code
                            try:
                                logger.info("Waiting for scan (looking for chat-list)...")
                                WebDriverWait(self.driver, 60).until(
                                    EC.presence_of_element_located((By.XPATH, "//div[@data-testid='chat-list']"))
                                )
                                self.is_connected = True
                                logger.info("QR code scanned, connected to WhatsApp Web")
                                return True
                            except TimeoutException:
                                logger.error("Timeout waiting for QR code scan")
                                error_msg = "Timeout waiting for QR code scan. Please try again."
                            break
                    except NoSuchElementException:
                        continue
                
                if not qr_found:
                    # If no QR code element found with any selector
                    logger.error("Could not find QR code or landing page element with any known selector")
                    error_msg = "Could not find QR code or landing page. WhatsApp Web interface may have changed."
                    
                # Check for other elements to diagnose the state of WhatsApp Web
                page_source = self.driver.page_source
                
                # More comprehensive diagnostic checks
                if any(text in page_source.lower() for text in ["use whatsapp on your computer", "to use whatsapp on your computer"]):
                    logger.info("WhatsApp Web landing page detected")
                    error_msg = "WhatsApp landing page found, but couldn't interact with it automatically. Try manually at https://web.whatsapp.com/"
                elif any(text in page_source.lower() for text in ["reload the page", "try reloading", "connection problem"]):
                    logger.error("WhatsApp Web is asking to reload the page")
                    error_msg = "WhatsApp Web needs to be reloaded. Please try again."
                elif any(text in page_source.lower() for text in ["multidevice", "multi-device", "multiple device"]):
                    logger.info("Multi-device beta screen detected")
                    error_msg = "WhatsApp multi-device screen detected. Try enabling multi-device in your WhatsApp settings."
                elif "blocked" in page_source.lower() or "suspicious" in page_source.lower():
                    logger.error("WhatsApp Web may be detecting automation")
                    error_msg = "WhatsApp Web might be detecting automation tools. Try connecting manually first."
                
                # Check if we're already logged in but didn't detect it properly
                chat_list_selectors = [
                    "//div[@data-testid='chat-list']",
                    "//div[contains(@class, 'chat-list')]",
                    "//div[@id='pane-side']",
                    "//div[contains(@class, '_3YS_f')]"
                ]
                
                for chat_selector in chat_list_selectors:
                    try:
                        if self.driver.find_element(By.XPATH, chat_selector):
                            logger.info(f"Found chat list with selector: {chat_selector}")
                            self.is_connected = True
                            return True
                    except:
                        pass
                        
                # Take screenshot of the current state for debugging
                try:
                    screenshot_path = os.path.join(os.path.expanduser('~'), '.aiassistant', 'whatsapp_error.png')
                    self.driver.save_screenshot(screenshot_path)
                    logger.info(f"Saved error screenshot to {screenshot_path}")
                    error_msg += f"\nScreenshot saved to: {screenshot_path}"
                except Exception as ss_error:
                    logger.error(f"Failed to save error screenshot: {str(ss_error)}")
                
                # Get some console logs if available
                try:
                    console_logs = self.driver.get_log('browser')
                    if console_logs:
                        logger.info("Browser console logs:")
                        for log in console_logs[-10:]:  # Last 10 logs
                            logger.info(f"  {log}")
                except Exception as log_error:
                    logger.error(f"Error getting console logs: {str(log_error)}")
                
                # Failed to connect properly
                logger.error(f"Failed to connect to WhatsApp Web: {error_msg}")
                if self.driver:
                    self.driver.quit()
                    self.driver = None
                return False
                
        except Exception as e:
            logger.error(f"Error connecting to WhatsApp Web: {str(e)}")
            if self.driver:
                try:
                    self.driver.quit()
                except Exception:
                    logger.error("Error closing Chrome driver")
                self.driver = None
            return False
    
    def disconnect(self) -> bool:
        """
        Disconnect from WhatsApp Web.
        
        Returns:
            bool: True if disconnected successfully, False otherwise
        """
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
                self.is_connected = False
                logger.info("Disconnected from WhatsApp Web")
                return True
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from WhatsApp Web: {str(e)}")
            return False
    
    def is_configured(self) -> bool:
        """
        Check if WhatsApp is configured.
        
        Returns:
            bool: True if configured, False otherwise
        """
        return self.config != {}
    
    def send_message(self, recipient: str, message: str) -> bool:
        """
        Send a WhatsApp message to a recipient.
        
        Args:
            recipient (str): The recipient's phone number with country code or contact name
            message (str): The message to send
            
        Returns:
            bool: True if the message was sent successfully, False otherwise
        """
        try:
            if not self.is_connected and not self.connect():
                logger.error("Not connected to WhatsApp Web")
                return False
            
            # Format recipient if it's a phone number
            if re.match(r'^\+?[0-9]+$', recipient):
                # Format as international number without + (WhatsApp Web API format)
                recipient = recipient.lstrip('+')
                
                # First try using the direct link approach
                try:
                    logger.info(f"Sending message to phone number: {recipient}")
                    # Open chat using WhatsApp Web API
                    message_encoded = urllib.parse.quote(message)
                    self.driver.get(f"https://web.whatsapp.com/send?phone={recipient}&text={message_encoded}")
                    
                    # Wait for chat to load
                    try:
                        # Try different selectors for the message input element
                        input_selectors = [
                            "//div[@data-testid='conversation-compose-box-input']",
                            "//div[contains(@class, '_3Uu1_')]",
                            "//div[contains(@class, 'selectable-text')]",
                            "//footer//div[@contenteditable='true']"
                        ]
                        
                        # Wait for any of the selectors to be present
                        for selector in input_selectors:
                            try:
                                WebDriverWait(self.driver, 30).until(
                                    EC.presence_of_element_located((By.XPATH, selector))
                                )
                                logger.info(f"Found message input using selector: {selector}")
                                break
                            except TimeoutException:
                                continue
                        
                        # Try to find and click the send button
                        send_button_selectors = [
                            "//button[@data-testid='compose-btn-send']",
                            "//span[@data-icon='send']",
                            "//button[contains(@class, '_3HQNh')]",
                            "//span[contains(@data-testid, 'send')]",
                            "//button[contains(@aria-label, 'Send')]",
                            "//div[contains(@class, '_4sWnG')]"
                        ]
                        
                        # Try multiple approaches to click the send button
                        send_clicked = False
                        
                        # First try standard WebDriverWait approach
                        for selector in send_button_selectors:
                            try:
                                send_button = WebDriverWait(self.driver, 5).until(
                                    EC.element_to_be_clickable((By.XPATH, selector))
                                )
                                send_button.click()
                                logger.info(f"Clicked send button using standard approach: {selector}")
                                send_clicked = True
                                break
                            except Exception as e:
                                logger.error(f"Error clicking send button with selector {selector}: {str(e)}")
                                continue
                        
                        # Try to find button using direct search if WebDriverWait failed
                        if not send_clicked:
                            for selector in send_button_selectors:
                                try:
                                    buttons = self.driver.find_elements(By.XPATH, selector)
                                    if buttons:
                                        # Try JavaScript click first (most reliable)
                                        self.driver.execute_script("arguments[0].click();", buttons[0])
                                        logger.info(f"Clicked send button using JavaScript: {selector}")
                                        send_clicked = True
                                        break
                                except Exception as e:
                                    logger.error(f"Error with JavaScript click on send button with selector {selector}: {str(e)}")
                                    continue
                        
                        # Try keyboard shortcut as last resort
                        if not send_clicked:
                            try:
                                # Use Enter key to send message (works in most WhatsApp Web versions)
                                actions = ActionChains(self.driver)
                                actions.send_keys(Keys.ENTER).perform()
                                logger.info("Used Enter key to send message")
                                send_clicked = True
                            except Exception as key_error:
                                logger.error(f"Error using keyboard shortcut to send: {str(key_error)}")
                        
                        if send_clicked:
                            logger.info(f"Message sent to {recipient}")
                            return True
                        else:
                            logger.error("Send button not found or not clickable using all methods")
                            return False
                    except TimeoutException:
                        logger.error(f"Could not find the chat for {recipient}")
                        return False
                except Exception as e:
                    logger.error(f"Error using direct link approach: {str(e)}")
                    # Fall back to search method
            
            # Search approach (used for contacts or as fallback)
            try:
                logger.info(f"Trying to send message to {recipient} using search approach")
                # Click on the new chat button
                new_chat_selectors = [
                    "//div[@data-testid='chat-list-search']",
                    "//button[@title='New chat']",
                    "//span[@data-icon='chat']"
                ]
                
                for selector in new_chat_selectors:
                    try:
                        new_chat_button = WebDriverWait(self.driver, 10).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        new_chat_button.click()
                        logger.info("Clicked new chat button")
                        break
                    except (TimeoutException, NoSuchElementException):
                        continue
                
                # Try to find the search input and enter the recipient's name
                logger.info("Looking for search input field after clicking new chat")
                time.sleep(2)  # Wait for new chat interface to appear
                
                search_input = None
                search_selectors = [
                    "//div[@title='Search input textbox']",
                    "//div[@data-testid='chat-list-search']//div[@contenteditable='true']",
                    "//div[@data-testid='search-input']//div[@contenteditable='true']",
                    "//div[contains(@class, 'lexical-rich-text-input')]//div[@contenteditable='true']",
                    "//div[contains(@class, 'copyable-text selectable-text')][@contenteditable='true']",
                    "//div[@role='textbox'][@contenteditable='true' and @spellcheck='true']",
                    "//input[@title='Search contacts']"
                ]
                
                for selector in search_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            for element in elements:
                                try:
                                    # Check if element is visible and enabled
                                    if element.is_displayed() and element.is_enabled():
                                        search_input = element
                                        logger.info(f"Found search input with selector: {selector}")
                                        break
                                except:
                                    continue
                            if search_input:
                                break
                    except Exception as e:
                        logger.error(f"Error finding search input with selector {selector}: {str(e)}")
                        continue
                
                if not search_input:
                    logger.error("Could not find search input field after clicking new chat")
                    return False
                
                # Clear and type the recipient name using multiple methods
                try:
                    # First try standard approach
                    search_input.click()
                    search_input.clear()  # Clear any existing text
                    time.sleep(0.5)
                    
                    # Send keys character by character with small delays to ensure it's properly recognized
                    for char in recipient:
                        search_input.send_keys(char)
                        time.sleep(0.1)
                        
                    logger.info(f"Entered search text for recipient: {recipient}")
                    
                    # Wait for search results to populate
                    time.sleep(2)
                except Exception as e:
                    logger.error(f"Error entering search text: {str(e)}")
                    try:
                        # Try JavaScript approach if the standard approach fails
                        self.driver.execute_script(
                            "arguments[0].textContent = arguments[1]; " +
                            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                            search_input, recipient
                        )
                        logger.info(f"Entered search text using JavaScript: {recipient}")
                        time.sleep(2)
                    except Exception as js_error:
                        logger.error(f"Error entering search text with JavaScript: {str(js_error)}")
                        return False
                
                # Verify search results before proceeding
                logger.info("Waiting for search results to appear...")
                time.sleep(2)  # Wait for search results to populate
                
                # Try to find the contact in search results with exact matching
                exact_match_selectors = [
                    f"//span[@title='{recipient}']",
                    f"//div[contains(@title, '{recipient}')]",
                    f"//span[text()='{recipient}']",
                    f"//div[text()='{recipient}']"
                ]
                
                # First try to find an exact match with the recipient name
                logger.info(f"Looking for exact match contact: {recipient}")
                exact_match_found = False
                
                for selector in exact_match_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            for element in elements:
                                if element.is_displayed():
                                    # Verify this is actually the contact we want
                                    element_text = element.text.strip()
                                    logger.info(f"Found potential exact match: '{element_text}'")
                                    
                                    # Check if it's an exact match or close match
                                    if element_text.lower() == recipient.lower() or recipient.lower() in element_text.lower():
                                        logger.info(f"Confirmed exact match for contact: {recipient}")
                                        
                                        # Try to click using JavaScript (more reliable)
                                        self.driver.execute_script("arguments[0].click();", element)
                                        time.sleep(1)
                                        
                                        exact_match_found = True
                                        contact_clicked = True
                                        break
                            if exact_match_found:
                                break
                    except Exception as e:
                        logger.error(f"Error finding exact match with selector {selector}: {str(e)}")
                        continue
                
                # If no exact match found, try the first result that partially matches
                if not exact_match_found:
                    logger.info("No exact match found, looking for partial matches...")
                    
                    # Get all search results and check each one
                    list_item_selectors = [
                        "//div[@data-testid='chat-list']//div[@role='listitem']", 
                        "//div[@data-testid='chat-list']//div[contains(@class, 'lhggkp7q')]",
                        "//div[contains(@data-testid, 'cell-frame')]"
                    ]
                    
                    for list_selector in list_item_selectors:
                        try:
                            list_items = self.driver.find_elements(By.XPATH, list_selector)
                            
                            if list_items:
                                logger.info(f"Found {len(list_items)} potential contacts in search results")
                                
                                # Only use the first result if we have a very close match
                                # or if there's only one result
                                if len(list_items) == 1:
                                    logger.info("Only one search result found, selecting it")
                                    
                                    # Take screenshot before clicking
                                    try:
                                        screenshot_path = os.path.join(os.path.expanduser('~'), '.aiassistant', 'whatsapp_contact_selection.png')
                                        self.driver.save_screenshot(screenshot_path)
                                        logger.info(f"Saved contact selection screenshot to {screenshot_path}")
                                    except Exception:
                                        pass
                                        
                                    # Try JavaScript click
                                    self.driver.execute_script("arguments[0].click();", list_items[0])
                                    time.sleep(1)
                                    
                                    contact_clicked = True
                                    break
                                else:
                                    # If multiple results, look for one that matches our recipient
                                    for item in list_items:
                                        try:
                                            # Try to get text from the list item
                                            item_text = item.text.strip()
                                            logger.info(f"Checking list item: '{item_text}'")
                                            
                                            # If item text contains our recipient name, select it
                                            if recipient.lower() in item_text.lower():
                                                logger.info(f"Found matching contact in results: '{item_text}'")
                                                
                                                # Take screenshot before clicking
                                                try:
                                                    screenshot_path = os.path.join(os.path.expanduser('~'), '.aiassistant', 'whatsapp_contact_match.png')
                                                    self.driver.save_screenshot(screenshot_path)
                                                    logger.info(f"Saved contact match screenshot to {screenshot_path}")
                                                except Exception:
                                                    pass
                                                    
                                                # Try JavaScript click
                                                self.driver.execute_script("arguments[0].click();", item)
                                                time.sleep(1)
                                                
                                                contact_clicked = True
                                                break
                                        except:
                                            continue
                                    
                                    if contact_clicked:
                                        break
                        except Exception as e:
                            logger.error(f"Error processing list items with selector {list_selector}: {str(e)}")
                            continue
                            
                # If we still haven't found a contact, and there's only one visible result, use it
                if not contact_clicked:
                    logger.warning("No matching contact found in results, will check if only one result exists")
                    
                    try:
                        visible_list_items = []
                        list_items = self.driver.find_elements(By.XPATH, "//div[@role='listitem']")
                        
                        for item in list_items:
                            if item.is_displayed():
                                visible_list_items.append(item)
                        
                        if len(visible_list_items) == 1:
                            logger.info("Only one visible result, will use it as fallback")
                            
                            # Take screenshot before clicking
                            try:
                                screenshot_path = os.path.join(os.path.expanduser('~'), '.aiassistant', 'whatsapp_contact_fallback.png')
                                self.driver.save_screenshot(screenshot_path)
                                logger.info(f"Saved fallback screenshot to {screenshot_path}")
                            except Exception:
                                pass
                                
                            # Try JavaScript click
                            self.driver.execute_script("arguments[0].click();", visible_list_items[0])
                            time.sleep(1)
                            
                            contact_clicked = True
                    except Exception as e:
                        logger.error(f"Error in fallback contact selection: {str(e)}")
                
                # If all other methods failed, try direct phone number approach if recipient looks like a phone number
                if not contact_clicked:
                    # Try to go directly to chat with phone number if it looks like one
                    phone_pattern = re.compile(r'^\+?[0-9\s\-\(\)]+$')
                    if phone_pattern.match(recipient):
                        logger.info(f"Recipient looks like a phone number, trying direct approach: {recipient}")
                        try:
                            # Clean up phone number - remove spaces, dashes, parentheses
                            clean_phone = re.sub(r'[\s\-\(\)]', '', recipient)
                            # Go directly to chat
                            self.driver.get(f"https://web.whatsapp.com/send?phone={clean_phone}&text={quote(message, safe='')}")
                            logger.info(f"Navigating directly to chat with phone: {clean_phone}")
                            
                            # Wait for the page to load
                            time.sleep(5)
                            
                            # Check if we're in a chat
                            chat_indicators = [
                                "//footer[@data-testid='conversation-footer']",
                                "//div[@data-testid='conversation-panel-body']",
                                "//div[contains(@class, 'conversation-panel')]"
                            ]
                            
                            for indicator in chat_indicators:
                                try:
                                    if self.driver.find_elements(By.XPATH, indicator):
                                        logger.info("Successfully loaded direct chat via phone number")
                                        contact_clicked = True
                                        
                                        # Check if message is already filled in the text field
                                        # If so, we can directly find and click the send button
                                        logger.info("Checking for send button after direct navigation")
                                        
                                        send_button_selectors = [
                                            "//button[@data-testid='compose-btn-send']",
                                            "//span[@data-icon='send']",
                                            "//button[contains(@class, '_3HQNh')]",
                                            "//span[contains(@data-testid, 'send')]",
                                            "//button[contains(@aria-label, 'Send')]",
                                            "//div[contains(@class, '_4sWnG')]"
                                        ]
                                        
                                        # Try to click the send button
                                        for selector in send_button_selectors:
                                            try:
                                                send_buttons = self.driver.find_elements(By.XPATH, selector)
                                                if send_buttons:
                                                    # Try JavaScript click
                                                    self.driver.execute_script("arguments[0].click();", send_buttons[0])
                                                    logger.info("Clicked send button after direct navigation")
                                                    return True
                                            except Exception as btn_error:
                                                logger.error(f"Error clicking send button after direct navigation: {str(btn_error)}")
                                                continue
                                                
                                        break
                                except:
                                    continue
                        except Exception as e:
                            logger.error(f"Error trying direct phone navigation: {str(e)}")
                
                if not contact_clicked:
                    logger.error(f"Could not find or click contact: {recipient}")
                    return False
                
                # Make sure we're actually in a chat and not in search view
                logger.info("Checking if we are in the correct chat view...")
                
                # First check if we can see any chat-specific elements that confirm we're in a chat
                chat_indicators = [
                    "//div[contains(@data-testid, 'conversation-panel-wrapper')]",
                    "//div[@data-testid='conversation-panel-body']",
                    "//footer[@data-testid='conversation-footer']",
                    "//header[contains(@data-testid, 'conversation-header')]",
                    "//div[contains(@class, 'conversation-panel')]"
                ]
                
                in_chat = False
                for indicator in chat_indicators:
                    try:
                        if self.driver.find_elements(By.XPATH, indicator):
                            in_chat = True
                            logger.info(f"Detected we are in a chat view with indicator: {indicator}")
                            break
                    except:
                        continue
                
                if not in_chat:
                    logger.warning("We might not be in a chat view! Will try to press Enter to select the contact first")
                    try:
                        # Try to press Enter to select the first contact from search
                        actions = ActionChains(self.driver)
                        actions.send_keys(Keys.ENTER).perform()
                        logger.info("Pressed Enter to select contact from search results")
                        time.sleep(2)  # Give time for the chat to load
                    except Exception as e:
                        logger.error(f"Error pressing Enter to select contact: {str(e)}")
                
                # Now try to find the message input field in the chat view
                message_input_selectors = [
                    "//footer//div[@data-testid='conversation-compose-box-input']",
                    "//footer//div[@contenteditable='true']",
                    "//footer//div[contains(@class, 'copyable-text selectable-text')]",
                    "//div[contains(@title, 'Type a message')]",
                    "//div[@role='textbox' and contains(@spellcheck, 'true')]",
                    "//footer//div[@role='textbox']"
                ]
                
                # Try to find the message input field specifically in the footer (chat area)
                message_input = None
                for selector in message_input_selectors:
                    try:
                        elements = self.driver.find_elements(By.XPATH, selector)
                        if elements:
                            for element in elements:
                                try:
                                    # Check if element is visible and enabled
                                    if element.is_displayed() and element.is_enabled():
                                        # Check if this element is NOT in the search area
                                        parent_html = self.driver.execute_script(
                                            "return arguments[0].parentElement.parentElement.parentElement.innerHTML;", 
                                            element
                                        )
                                        # Skip if this appears to be in search
                                        if "search" in parent_html.lower() or "searching" in parent_html.lower():
                                            logger.info("Skipping element that appears to be in search area")
                                            continue
                                            
                                        message_input = element
                                        logger.info(f"Found message input in chat view with selector: {selector}")
                                        break
                                except:
                                    continue
                            if message_input:
                                break
                    except Exception as e:
                        logger.error(f"Error finding message input with selector {selector}: {str(e)}")
                        continue
                
                if not message_input:
                    logger.error("Could not find message input field")
                    
                    # Take screenshot for debugging
                    try:
                        screenshot_path = os.path.join(os.path.expanduser('~'), '.aiassistant', 'whatsapp_input_error.png')
                        self.driver.save_screenshot(screenshot_path)
                        logger.info(f"Saved error screenshot to {screenshot_path}")
                    except Exception:
                        pass
                        
                    return False
                
                # Try different approaches to input the message
                input_success = False
                
                # Method 1: Standard click and send_keys
                try:
                    message_input.click()
                    time.sleep(0.5)
                    message_input.clear()  # Try to clear any existing text
                    message_input.send_keys(message)
                    logger.info("Entered message using standard approach")
                    input_success = True
                except Exception as e:
                    logger.error(f"Error using standard input method: {str(e)}")
                
                # Method 2: JavaScript approach
                if not input_success:
                    try:
                        self.driver.execute_script(
                            "arguments[0].textContent = arguments[1]; " +
                            "arguments[0].dispatchEvent(new Event('input', {bubbles: true}));",
                            message_input, message
                        )
                        logger.info("Entered message using JavaScript")
                        input_success = True
                    except Exception as js_error:
                        logger.error(f"Error using JavaScript input method: {str(js_error)}")
                
                # Method 3: ActionChains
                if not input_success:
                    try:
                        actions = ActionChains(self.driver)
                        actions.move_to_element(message_input).click().send_keys(message).perform()
                        logger.info("Entered message using ActionChains")
                        input_success = True
                    except Exception as action_error:
                        logger.error(f"Error using ActionChains input method: {str(action_error)}")
                
                if not input_success:
                    logger.error("Failed to input message using all available methods")
                    return False
                
                # Send message
                send_button_selectors = [
                    "//button[@data-testid='compose-btn-send']",
                    "//span[@data-icon='send']",
                    "//button[contains(@class, '_3HQNh')]",
                    "//span[contains(@data-testid, 'send')]",
                    "//button[contains(@aria-label, 'Send')]",
                    "//div[contains(@class, '_4sWnG')]"
                ]
                
                # Try multiple approaches to click the send button
                send_clicked = False
                
                # First try standard WebDriverWait approach
                for selector in send_button_selectors:
                    try:
                        send_button = WebDriverWait(self.driver, 5).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        send_button.click()
                        logger.info(f"Clicked send button using standard approach: {selector}")
                        send_clicked = True
                        break
                    except Exception as e:
                        logger.error(f"Error clicking send button with selector {selector}: {str(e)}")
                        continue
                
                # Try to find button using direct search if WebDriverWait failed
                if not send_clicked:
                    for selector in send_button_selectors:
                        try:
                            buttons = self.driver.find_elements(By.XPATH, selector)
                            if buttons:
                                # Try JavaScript click first (most reliable)
                                self.driver.execute_script("arguments[0].click();", buttons[0])
                                logger.info(f"Clicked send button using JavaScript: {selector}")
                                send_clicked = True
                                break
                        except Exception as e:
                            logger.error(f"Error with JavaScript click on send button with selector {selector}: {str(e)}")
                            continue
                
                # Try keyboard shortcut as last resort
                if not send_clicked:
                    try:
                        # Use Enter key to send message (works in most WhatsApp Web versions)
                        actions = ActionChains(self.driver)
                        actions.send_keys(Keys.ENTER).perform()
                        logger.info("Used Enter key to send message")
                        send_clicked = True
                    except Exception as key_error:
                        logger.error(f"Error using keyboard shortcut to send: {str(key_error)}")
                
                if send_clicked:
                    logger.info(f"Message sent to {recipient}")
                    return True
                else:
                    logger.error("Send button not found or not clickable using all methods")
                    return False
            except Exception as e:
                logger.error(f"Error with search approach: {str(e)}")
                return False
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False
    
    def get_recent_contacts(self, limit: int = 5) -> List[str]:
        """
        Get a list of recent WhatsApp contacts.
        
        Args:
            limit (int): Maximum number of contacts to return
            
        Returns:
            List[str]: List of contact names/numbers
        """
        try:
            if not self.is_connected and not self.connect():
                logger.error("Not connected to WhatsApp Web")
                return []
            
            # Find all chat elements
            chat_elements = WebDriverWait(self.driver, 30).until(
                EC.presence_of_all_elements_located((By.XPATH, "//div[@data-testid='chat-list']//span[@data-testid='cell-frame-title']"))
            )
            
            # Extract contact names
            contacts = []
            for i, element in enumerate(chat_elements):
                if i >= limit:
                    break
                contacts.append(element.text)
            
            return contacts
        except Exception as e:
            logger.error(f"Error getting recent contacts: {str(e)}")
            return []
