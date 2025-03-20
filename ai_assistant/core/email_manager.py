"""
Email manager module for QuackQuery AI Assistant.
Handles email configuration, sending, and reading using SMTP/IMAP.
"""

import os
import json
import smtplib
import imaplib
import email
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from pathlib import Path
import email.utils

logger = logging.getLogger("ai_assistant")

class EmailManager:
    """
    Handles email operations including configuration, sending and reading emails.
    Uses SMTP for sending and IMAP for reading emails.
    """
    
    def __init__(self):
        """Initialize the email manager with configuration."""
        # Set up config path in user's home directory
        self.home_dir = os.path.expanduser("~")
        self.config_dir = os.path.join(self.home_dir, ".quackquery")
        
        # Create directory if it doesn't exist
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
            
        self.config_path = os.path.join(self.config_dir, "email_config.json")
        self.config = self._load_config()
        
    def _load_config(self):
        """Load email configuration from file."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    logger.info(f"Loading email config from {self.config_path}")
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading email config: {e}")
                return {}
        return {}
        
    def _save_config(self):
        """Save email configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                logger.info(f"Saving email config to {self.config_path}")
                json.dump(self.config, f)
            return True
        except Exception as e:
            logger.error(f"Error saving email config: {e}")
            return False
            
    def setup_email(self, email_address, email_password, smtp_server, smtp_port, imap_server, imap_port):
        """
        Configure email settings.
        
        Args:
            email_address: User's email address
            email_password: Password or app password
            smtp_server: SMTP server address
            smtp_port: SMTP server port
            imap_server: IMAP server address
            imap_port: IMAP server port
            
        Returns:
            bool: True if configuration was successful
        """
        self.config = {
            "email_address": email_address,
            "email_password": email_password,
            "smtp_server": smtp_server,
            "smtp_port": int(smtp_port),
            "imap_server": imap_server,
            "imap_port": int(imap_port),
            "setup_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Test connection to verify settings
        try:
            logger.info(f"Testing SMTP connection to {smtp_server}:{smtp_port}")
            # Test SMTP connection
            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.ehlo()
                server.starttls()
                logger.info(f"Logging in as {email_address}")
                server.login(email_address, email_password)
                logger.info("SMTP login successful")
                
            logger.info(f"Testing IMAP connection to {imap_server}:{imap_port}")
            # Test IMAP connection
            with imaplib.IMAP4_SSL(imap_server, int(imap_port)) as server:
                logger.info(f"Logging in to IMAP as {email_address}")
                server.login(email_address, email_password)
                server.select('INBOX')
                logger.info("IMAP login successful")
                
            # Save config if tests pass
            logger.info("Email configuration successful, saving settings")
            return self._save_config()
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication Error: {e}")
            return False
        except imaplib.IMAP4.error as e:
            logger.error(f"IMAP Error: {e}")
            return False
        except Exception as e:
            logger.error(f"Error testing email connection: {e}")
            logger.exception("Detailed traceback for email testing error:")
            self.config = {}
            return False
            
    def send_email(self, to_address, subject, body):
        """
        Send an email using the configured SMTP settings.
        
        Args:
            to_address (str): Recipient email address
            subject (str): Email subject
            body (str): Email body content
            
        Returns:
            str: Success or error message
        """
        try:
            # Ensure we have configuration
            if not self.is_configured():
                raise ValueError("Email credentials not set up")
                
            # Get configuration values with safe defaults
            email_address = self.config.get('email_address')
            email_password = self.config.get('email_password')
            smtp_server = self.config.get('smtp_server')
            smtp_port = self.config.get('smtp_port')
            
            if not all([email_address, email_password, smtp_server, smtp_port]):
                raise ValueError("Missing required email configuration")
                
            # Create the email message
            msg = MIMEMultipart()
            msg['From'] = email_address
            msg['To'] = to_address
            msg['Subject'] = subject
            msg['Date'] = email.utils.formatdate(localtime=True)
            
            # Attach the body
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server and send the email
            logger.info(f"Connecting to SMTP server: {smtp_server}:{smtp_port}")
            
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.ehlo()
                server.starttls()
                logger.info(f"Logging in as {email_address}")
                server.login(email_address, email_password)
                
                logger.info(f"Sending email to: {to_address}")
                server.send_message(msg)
                
            logger.info("Email sent successfully")
            return "Email sent successfully!"
            
        except smtplib.SMTPAuthenticationError:
            error_msg = "Failed to authenticate with the SMTP server. Please check your email and password."
            logger.error(error_msg)
            return error_msg
            
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.exception("Unexpected error during email sending:")
            return error_msg
            
    def check_emails(self, limit=10):
        """
        Check for new emails in the inbox.
        
        Args:
            limit (int): Maximum number of emails to retrieve
            
        Returns:
            list: List of email dictionaries or error message
        """
        try:
            # Ensure we have configuration
            if not self.is_configured():
                return "Email credentials not set up. Please run '/email setup' first."
                
            # Get configuration values with safe defaults
            email_address = self.config.get('email_address')
            email_password = self.config.get('email_password')
            imap_server = self.config.get('imap_server')
            imap_port = self.config.get('imap_port', 993)
            
            if not all([email_address, email_password, imap_server, imap_port]):
                return "Missing required email configuration for reading emails."
                
            # Connect to IMAP server
            logger.info(f"Connecting to IMAP server: {imap_server}:{imap_port}")
            with imaplib.IMAP4_SSL(imap_server, imap_port) as server:
                logger.info(f"Logging in as {email_address}")
                server.login(email_address, email_password)
                
                # Select inbox
                logger.info("Selecting INBOX")
                status, data = server.select('INBOX')
                
                if status != 'OK':
                    error_msg = f"Could not select inbox: {status}"
                    logger.error(error_msg)
                    return error_msg
                    
                # Search for emails (ALL or UNSEEN for unread only)
                logger.info("Searching for emails")
                status, messages = server.search(None, 'ALL')
                
                if status != 'OK':
                    error_msg = f"Error searching emails: {status}"
                    logger.error(error_msg)
                    return error_msg
                    
                # Get message numbers
                message_numbers = messages[0].split()
                logger.info(f"Found {len(message_numbers)} emails")
                
                # No emails found
                if not message_numbers:
                    return "No emails found in inbox."
                    
                # Get the latest emails (up to the limit)
                emails = []
                for num in sorted(message_numbers, reverse=True)[:limit]:
                    status, data = server.fetch(num, '(RFC822)')
                    
                    if status != 'OK':
                        logger.error(f"Error fetching email {num}: {status}")
                        continue
                        
                    # Parse email message
                    raw_email = data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    # Extract email details
                    email_data = {
                        'id': num.decode('utf-8'),
                        'from': self._decode_header(msg.get('From', 'Unknown')),
                        'to': self._decode_header(msg.get('To', 'Unknown')),
                        'subject': self._decode_header(msg.get('Subject', '(No Subject)')),
                        'date': msg.get('Date', 'Unknown Date'),
                        'body': self._get_email_body(msg)
                    }
                    
                    emails.append(email_data)
                    
                return emails
                
        except imaplib.IMAP4.error as e:
            error_msg = f"IMAP server error: {str(e)}"
            logger.error(error_msg)
            return error_msg
            
        except ValueError as e:
            error_msg = str(e)
            logger.error(error_msg)
            return error_msg
            
        except Exception as e:
            error_msg = f"Error checking emails: {str(e)}"
            logger.exception("Unexpected error while checking emails:")
            return error_msg
            
    def read_email(self, email_number):
        """
        Read a specific email by its number.
        
        Args:
            email_number: The number (index) of the email to read
            
        Returns:
            dict: Email content including headers and body
        """
        if not self.config:
            logger.error("Email not configured")
            return "Email not configured. Run /email setup first."
            
        try:
            with imaplib.IMAP4_SSL(self.config['imap_server'], self.config['imap_port']) as server:
                server.login(self.config['email_address'], self.config['email_password'])
                server.select('INBOX')
                
                # Search for all emails
                status, data = server.search(None, 'ALL')
                if status != 'OK':
                    return "No emails found"
                    
                # Get email IDs
                email_ids = data[0].split()
                
                # Check if the requested email number is valid
                if not email_ids or email_number > len(email_ids):
                    return "Invalid email number"
                    
                # Get the email ID for the requested number (newest first)
                email_ids.reverse()
                email_id = email_ids[email_number - 1]
                
                # Fetch the email
                status, data = server.fetch(email_id, '(RFC822)')
                
                if status != 'OK':
                    return "Could not fetch email"
                    
                # Parse the email
                raw_email = data[0][1]
                parsed_email = email.message_from_bytes(raw_email)
                
                # Extract info
                from_address = parsed_email['From']
                subject = parsed_email['Subject']
                date = parsed_email['Date']
                
                # Extract body
                body = ""
                if parsed_email.is_multipart():
                    for part in parsed_email.walk():
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        
                        # Skip attachments
                        if "attachment" in content_disposition:
                            continue
                            
                        # Get plain text body
                        if content_type == "text/plain":
                            body = part.get_payload(decode=True).decode()
                            break
                else:
                    body = parsed_email.get_payload(decode=True).decode()
                    
                return {
                    "from": from_address,
                    "subject": subject or "(No Subject)",
                    "date": date,
                    "body": body
                }
        except Exception as e:
            logger.error(f"Error reading email: {e}")
            return f"Error reading email: {str(e)}"

    def is_configured(self):
        """
        Check if email is configured.
        
        Returns:
            bool: True if email is configured, False otherwise
        """
        try:
            # Check if we have the required configuration
            if not self.config:
                logger.error("Email configuration is empty")
                return False
                
            required_fields = ['email_address', 'email_password', 'smtp_server', 'smtp_port', 'imap_server', 'imap_port']
            for field in required_fields:
                if field not in self.config or not self.config.get(field):
                    logger.error(f"Missing required email configuration field: {field}")
                    return False
                    
            logger.info(f"Email configuration found for {self.config.get('email_address')}")
            return True
            
        except Exception as e:
            logger.error(f"Error checking email configuration: {e}")
            return False

    def _decode_header(self, header):
        decoded_header = ""
        for part in email.header.decode_header(header):
            if part[1] is not None:
                decoded_header += part[0].decode(part[1])
            else:
                decoded_header += part[0]
        return decoded_header

    def _get_email_body(self, msg):
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                    
                # Get plain text body
                if content_type == "text/plain":
                    body = part.get_payload(decode=True).decode()
                    break
        else:
            body = msg.get_payload(decode=True).decode()
            
        return body
