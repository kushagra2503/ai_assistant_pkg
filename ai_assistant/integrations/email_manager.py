import os
import logging
import smtplib
import imaplib
import email
import email.header
import email.utils
import getpass
import re
import time
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("ai_assistant")

class EmailManager:
    """
    Class for managing email operations through QuackQuery.
    Supports Gmail, Outlook, Yahoo, and other IMAP/SMTP providers.
    """
    
    # Common email providers
    EMAIL_PROVIDERS = {
        'gmail': {
            'imap_server': 'imap.gmail.com',
            'imap_port': 993,
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587
        },
        'outlook': {
            'imap_server': 'outlook.office365.com',
            'imap_port': 993,
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587
        },
        'yahoo': {
            'imap_server': 'imap.mail.yahoo.com',
            'imap_port': 993,
            'smtp_server': 'smtp.mail.yahoo.com',
            'smtp_port': 587
        }
    }
    
    def __init__(self, config_path=None):
        """
        Initialize the email manager.
        
        Args:
            config_path: Path to the email configuration file
        """
        self.config_path = config_path or os.path.join(os.path.expanduser("~"), ".quackquery", "email_config.json")
        self.email_address = None
        self.email_password = None
        self.provider = None
        self.imap_server = None
        self.smtp_server = None
        self.imap_connection = None
        self.smtp_connection = None
        self.is_authenticated = False
        
        # Create config directory if it doesn't exist
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        # Try to load existing configuration
        self._load_config()
        
        logger.info("Email Manager initialized")
    
    def _load_config(self):
        """Load email configuration from file."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                
                self.email_address = config.get('email_address')
                # Password is stored encrypted in the actual implementation
                self.email_password = config.get('email_password')
                self.provider = config.get('provider')
                self.imap_server = config.get('imap_server')
                self.imap_port = config.get('imap_port')
                self.smtp_server = config.get('smtp_server')
                self.smtp_port = config.get('smtp_port')
                
                logger.info(f"Loaded email configuration for {self.email_address}")
        except Exception as e:
            logger.error(f"Error loading email configuration: {str(e)}")
    
    def _save_config(self):
        """Save email configuration to file."""
        try:
            config = {
                'email_address': self.email_address,
                # Password should be encrypted in the actual implementation
                'email_password': self.email_password,
                'provider': self.provider,
                'imap_server': self.imap_server,
                'imap_port': self.imap_port,
                'smtp_server': self.smtp_server,
                'smtp_port': self.smtp_port
            }
            
            with open(self.config_path, 'w') as f:
                json.dump(config, f)
                
            logger.info(f"Saved email configuration for {self.email_address}")
        except Exception as e:
            logger.error(f"Error saving email configuration: {str(e)}")
    
    def setup_email_account(self, email_address=None, password=None, provider=None):
        """
        Set up email account credentials.
        
        Args:
            email_address: User's email address
            password: Email account password or app password
            provider: Email provider (gmail, outlook, yahoo, or other)
            
        Returns:
            A string describing the result
        """
        try:
            # Get email address if not provided
            if not email_address:
                email_address = input("Enter your email address: ").strip()
            
            # Determine provider if not specified
            if not provider:
                if "@gmail" in email_address:
                    provider = "gmail"
                elif "@outlook" in email_address or "@hotmail" in email_address or "@live" in email_address:
                    provider = "outlook"
                elif "@yahoo" in email_address:
                    provider = "yahoo"
                else:
                    provider = input("Enter your email provider (gmail, outlook, yahoo, or other): ").strip().lower()
            
            # Get password if not provided
            if not password:
                password = getpass.getpass("Enter your email password or app password: ")
            
            # Set up server information
            if provider in self.EMAIL_PROVIDERS:
                self.imap_server = self.EMAIL_PROVIDERS[provider]['imap_server']
                self.imap_port = self.EMAIL_PROVIDERS[provider]['imap_port']
                self.smtp_server = self.EMAIL_PROVIDERS[provider]['smtp_server']
                self.smtp_port = self.EMAIL_PROVIDERS[provider]['smtp_port']
            else:
                # For custom providers
                self.imap_server = input("Enter IMAP server address: ").strip()
                self.imap_port = int(input("Enter IMAP port (usually 993): ").strip())
                self.smtp_server = input("Enter SMTP server address: ").strip()
                self.smtp_port = int(input("Enter SMTP port (usually 587): ").strip())
            
            # Store the credentials
            self.email_address = email_address
            self.email_password = password
            self.provider = provider
            
            # Test the connection
            if self._test_connection():
                # Save the configuration
                self._save_config()
                return f"Email account {email_address} set up successfully."
            else:
                return "Failed to connect to email servers. Please check your credentials and try again."
                
        except Exception as e:
            logger.error(f"Error setting up email account: {str(e)}")
            return f"Error setting up email account: {str(e)}"
    
    def _test_connection(self):
        """
        Test the email connection.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            # Test IMAP connection
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            imap.login(self.email_address, self.email_password)
            imap.logout()
            
            # Test SMTP connection
            smtp = smtplib.SMTP(self.smtp_server, self.smtp_port)
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.email_address, self.email_password)
            smtp.quit()
            
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
    
    def connect(self):
        """
        Connect to email servers.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if not self.email_address or not self.email_password:
            logger.error("Email credentials not set up")
            return False
            
        try:
            # Connect to IMAP server
            self.imap_connection = imaplib.IMAP4_SSL(self.imap_server, self.imap_port)
            self.imap_connection.login(self.email_address, self.email_password)
            
            # Connect to SMTP server
            self.smtp_connection = smtplib.SMTP(self.smtp_server, self.smtp_port)
            self.smtp_connection.ehlo()
            self.smtp_connection.starttls()
            self.smtp_connection.login(self.email_address, self.email_password)
            
            self.is_authenticated = True
            logger.info(f"Connected to email servers for {self.email_address}")
            return True
            
        except Exception as e:
            logger.error(f"Error connecting to email servers: {str(e)}")
            self.is_authenticated = False
            return False
    
    def disconnect(self):
        """Disconnect from email servers."""
        try:
            if self.imap_connection:
                self.imap_connection.logout()
                self.imap_connection = None
                
            if self.smtp_connection:
                self.smtp_connection.quit()
                self.smtp_connection = None
                
            self.is_authenticated = False
            logger.info("Disconnected from email servers")
            
        except Exception as e:
            logger.error(f"Error disconnecting from email servers: {str(e)}")
    
    def send_email(self, to_address, subject, body, cc=None, bcc=None, html=False):
        """
        Send an email.
        
        Args:
            to_address: Recipient email address or addresses (comma-separated)
            subject: Email subject
            body: Email body content
            cc: Carbon copy recipients (comma-separated)
            bcc: Blind carbon copy recipients (comma-separated)
            html: Whether the body contains HTML content
            
        Returns:
            A string describing the result
        """
        if not self.is_authenticated:
            if not self.connect():
                return "Not connected to email servers. Please set up your email account first."
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_address
            msg['To'] = to_address
            msg['Subject'] = subject
            
            if cc:
                msg['Cc'] = cc
                
            # Add body
            if html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Prepare recipients
            recipients = to_address.split(',')
            
            if cc:
                recipients.extend(cc.split(','))
                
            if bcc:
                recipients.extend(bcc.split(','))
            
            # Send the email
            self.smtp_connection.sendmail(self.email_address, recipients, msg.as_string())
            
            logger.info(f"Email sent to {to_address}")
            return f"Email sent successfully to {to_address}"
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return f"Error sending email: {str(e)}"
    
    def list_emails(self, folder="inbox", limit=10, unread_only=False, from_address=None, search_term=None, days=7):
        """
        List emails from a folder.
        
        Args:
            folder: Email folder to list (inbox, sent, drafts, etc.)
            limit: Maximum number of emails to list
            unread_only: Whether to list only unread emails
            from_address: Filter emails from a specific address
            search_term: Search term to filter emails
            days: Number of days to look back
            
        Returns:
            A list of email dictionaries and a string summary
        """
        if not self.is_authenticated:
            if not self.connect():
                return [], "Not connected to email servers. Please set up your email account first."
        
        try:
            # Select the folder
            folder = folder.lower()
            if folder == "inbox":
                self.imap_connection.select("INBOX")
            else:
                self.imap_connection.select(folder)
            
            # Build search criteria
            search_criteria = []
            
            # Date filter
            if days > 0:
                date_since = (datetime.now() - timedelta(days=days)).strftime("%d-%b-%Y")
                search_criteria.append(f'(SINCE "{date_since}")')
            
            # Unread filter
            if unread_only:
                search_criteria.append('(UNSEEN)')
            
            # Sender filter
            if from_address:
                search_criteria.append(f'(FROM "{from_address}")')
            
            # Text search
            if search_term:
                search_criteria.append(f'(SUBJECT "{search_term}" OR BODY "{search_term}")')
            
            # Combine search criteria
            if search_criteria:
                search_string = ' '.join(search_criteria)
                result, data = self.imap_connection.search(None, search_string)
            else:
                result, data = self.imap_connection.search(None, 'ALL')
            
            if result != 'OK':
                return [], f"Error searching for emails in {folder}"
            
            # Get email IDs
            email_ids = data[0].split()
            
            # Limit the number of emails
            if limit > 0 and len(email_ids) > limit:
                email_ids = email_ids[-limit:]
            
            emails = []
            
            # Fetch emails
            for email_id in reversed(email_ids):
                result, data = self.imap_connection.fetch(email_id, '(RFC822)')
                
                if result != 'OK':
                    continue
                
                raw_email = data[0][1]
                email_message = email.message_from_bytes(raw_email)
                
                # Extract email details
                subject = self._decode_header(email_message['Subject'])
                from_address = self._decode_header(email_message['From'])
                date = email.utils.parsedate_to_datetime(email_message['Date'])
                
                # Get email body
                body = self._get_email_body(email_message)
                
                # Check if email is read
                result, flags_data = self.imap_connection.fetch(email_id, '(FLAGS)')
                flags = flags_data[0].decode('utf-8')
                is_read = '\\Seen' in flags
                
                # Add email to list
                emails.append({
                    'id': email_id.decode('utf-8'),
                    'subject': subject,
                    'from': from_address,
                    'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                    'body': body[:200] + ('...' if len(body) > 200 else ''),
                    'is_read': is_read
                })
            
            # Create summary
            summary = f"Found {len(emails)} emails in {folder}"
            if unread_only:
                summary += " (unread only)"
            if from_address:
                summary += f" from {from_address}"
            if search_term:
                summary += f" containing '{search_term}'"
            if days > 0:
                summary += f" from the last {days} days"
            
            return emails, summary
            
        except Exception as e:
            logger.error(f"Error listing emails: {str(e)}")
            return [], f"Error listing emails: {str(e)}"
    
    def read_email(self, email_id, folder="inbox", mark_as_read=True):
        """
        Read a specific email.
        
        Args:
            email_id: ID of the email to read
            folder: Folder containing the email
            mark_as_read: Whether to mark the email as read
            
        Returns:
            A dictionary containing the email details and a string summary
        """
        if not self.is_authenticated:
            if not self.connect():
                return None, "Not connected to email servers. Please set up your email account first."
        
        try:
            # Select the folder
            folder = folder.lower()
            if folder == "inbox":
                self.imap_connection.select("INBOX")
            else:
                self.imap_connection.select(folder)
            
            # Fetch the email
            result, data = self.imap_connection.fetch(email_id.encode('utf-8'), '(RFC822)')
            
            if result != 'OK':
                return None, f"Error fetching email with ID {email_id}"
            
            raw_email = data[0][1]
            email_message = email.message_from_bytes(raw_email)
            
            # Extract email details
            subject = self._decode_header(email_message['Subject'])
            from_address = self._decode_header(email_message['From'])
            to_address = self._decode_header(email_message['To'])
            date = email.utils.parsedate_to_datetime(email_message['Date'])
            
            # Get email body
            body = self._get_email_body(email_message)
            
            # Mark as read if requested
            if mark_as_read:
                self.imap_connection.store(email_id.encode('utf-8'), '+FLAGS', '\\Seen')
            
            # Create email dictionary
            email_dict = {
                'id': email_id,
                'subject': subject,
                'from': from_address,
                'to': to_address,
                'date': date.strftime('%Y-%m-%d %H:%M:%S'),
                'body': body
            }
            
            summary = f"Email from {from_address} with subject '{subject}'"
            
            return email_dict, summary
            
        except Exception as e:
            logger.error(f"Error reading email: {str(e)}")
            return None, f"Error reading email: {str(e)}"
    
    def reply_to_email(self, email_id, reply_body, include_original=True, reply_all=False, folder="inbox"):
        """
        Reply to an email.
        
        Args:
            email_id: ID of the email to reply to
            reply_body: Body of the reply
            include_original: Whether to include the original email in the reply
            reply_all: Whether to reply to all recipients
            folder: Folder containing the email
            
        Returns:
            A string describing the result
        """
        if not self.is_authenticated:
            if not self.connect():
                return "Not connected to email servers. Please set up your email account first."
        
        try:
            # Get the original email
            email_dict, _ = self.read_email(email_id, folder, mark_as_read=False)
            
            if not email_dict:
                return f"Could not find email with ID {email_id}"
            
            # Extract original email details
            original_subject = email_dict['subject']
            original_from = email_dict['from']
            original_body = email_dict['body']
            
            # Create reply subject
            if not original_subject.startswith('Re:'):
                reply_subject = f"Re: {original_subject}"
            else:
                reply_subject = original_subject
            
            # Extract email address from the "From" field
            match = re.search(r'<([^>]+)>', original_from)
            if match:
                reply_to = match.group(1)
            else:
                reply_to = original_from.strip()
            
            # Prepare reply body
            if include_original:
                formatted_reply = f"{reply_body}\n\nOn {email_dict['date']}, {original_from} wrote:\n\n"
                
                # Format original body with '>' prefix
                formatted_original = '\n'.join([f'> {line}' for line in original_body.split('\n')])
                formatted_reply += formatted_original
            else:
                formatted_reply = reply_body
            
            # Send the reply
            result = self.send_email(reply_to, reply_subject, formatted_reply)
            
            return f"Replied to email from {original_from}: {result}"
            
        except Exception as e:
            logger.error(f"Error replying to email: {str(e)}")
            return f"Error replying to email: {str(e)}"
    
    def forward_email(self, email_id, to_address, forward_message="", folder="inbox"):
        """
        Forward an email.
        
        Args:
            email_id: ID of the email to forward
            to_address: Recipient email address
            forward_message: Additional message to include
            folder: Folder containing the email
            
        Returns:
            A string describing the result
        """
        if not self.is_authenticated:
            if not self.connect():
                return "Not connected to email servers. Please set up your email account first."
        
        try:
            # Get the original email
            email_dict, _ = self.read_email(email_id, folder, mark_as_read=False)
            
            if not email_dict:
                return f"Could not find email with ID {email_id}"
            
            # Extract original email details
            original_subject = email_dict['subject']
            original_from = email_dict['from']
            original_body = email_dict['body']
            
            # Create forward subject
            if not original_subject.startswith('Fwd:'):
                forward_subject = f"Fwd: {original_subject}"
            else:
                forward_subject = original_subject
            
            # Prepare forward body
            forward_body = f"{forward_message}\n\n---------- Forwarded message ----------\n"
            forward_body += f"From: {original_from}\n"
            forward_body += f"Date: {email_dict['date']}\n"
            forward_body += f"Subject: {original_subject}\n"
            forward_body += f"To: {email_dict['to']}\n\n"
            forward_body += original_body
            
            # Send the forward
            result = self.send_email(to_address, forward_subject, forward_body)
            
            return f"Forwarded email to {to_address}: {result}"
            
        except Exception as e:
            logger.error(f"Error forwarding email: {str(e)}")
            return f"Error forwarding email: {str(e)}"
    
    def delete_email(self, email_id, folder="inbox", move_to_trash=True):
        """
        Delete an email.
        
        Args:
            email_id: ID of the email to delete
            folder: Folder containing the email
            move_to_trash: Whether to move to trash or permanently delete
            
        Returns:
            A string describing the result
        """
        if not self.is_authenticated:
            if not self.connect():
                return "Not connected to email servers. Please set up your email account first."
        
        try:
            # Select the folder
            folder = folder.lower()
            if folder == "inbox":
                self.imap_connection.select("INBOX")
            else:
                self.imap_connection.select(folder)
            
            if move_to_trash:
                # Move to trash
                result = self.imap_connection.copy(email_id.encode('utf-8'), "[Gmail]/Trash")
                if result[0] == 'OK':
                    # Mark for deletion
                    self.imap_connection.store(email_id.encode('utf-8'), '+FLAGS', '\\Deleted')
                    # Expunge to actually delete
                    self.imap_connection.expunge()
                    return "Email moved to trash"
                else:
                    return "Failed to move email to trash"
            else:
                # Mark for deletion
                self.imap_connection.store(email_id.encode('utf-8'), '+FLAGS', '\\Deleted')
                # Expunge to actually delete
                self.imap_connection.expunge()
                return "Email permanently deleted"
            
        except Exception as e:
            logger.error(f"Error deleting email: {str(e)}")
            return f"Error deleting email: {str(e)}"
    
    def _decode_header(self, header):
        """Decode email header."""
        if not header:
            return ""
            
        try:
            decoded_header = email.header.decode_header(header)
            header_parts = []
            
            for part, encoding in decoded_header:
                if isinstance(part, bytes):
                    if encoding:
                        header_parts.append(part.decode(encoding))
                    else:
                        header_parts.append(part.decode('utf-8', errors='replace'))
                else:
                    header_parts.append(part)
                    
            return ' '.join(header_parts)
            
        except Exception as e:
            logger.error(f"Error decoding header: {str(e)}")
            return header
    
    def _get_email_body(self, email_message):
        """Extract the body from an email message."""
        body = ""
        
        if email_message.is_multipart():
            for part in email_message.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                # Skip attachments
                if "attachment" in content_disposition:
                    continue
                
                # Get text content
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        break
                    except:
                        pass
                elif content_type == "text/html" and not body:
                    try:
                        # If no plain text is found, use HTML
                        body = part.get_payload(decode=True).decode('utf-8', errors='replace')
                        # Simple HTML to text conversion
                        body = re.sub(r'<[^>]+>', '', body)
                    except:
                        pass
        else:
            # Not multipart - get the content directly
            try:
                body = email_message.get_payload(decode=True).decode('utf-8', errors='replace')
            except:
                body = str(email_message.get_payload())
        
        return body
    
    def load_email_config(self):
        """
        Load email configuration from disk.
        
        Returns:
            dict: Email configuration dictionary or None if not found
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            return None
        except Exception as e:
            logger.error(f"Error loading email configuration: {e}")
            return None 