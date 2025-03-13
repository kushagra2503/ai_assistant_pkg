"""
Google Calendar integration for the AI Assistant.
"""

import os
import logging
import datetime
import pickle
from dateutil import parser
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

logger = logging.getLogger("ai_assistant")

class GoogleCalendarIntegration:
    """
    Google Calendar integration for the AI Assistant.
    
    Attributes:
        SCOPES (list): OAuth scopes required for calendar access
        creds (google.oauth2.credentials.Credentials): Google OAuth credentials
        service (googleapiclient.discovery.Resource): Google Calendar API service
        credentials_file (str): Path to the credentials pickle file
        client_secrets_file (str): Path to the OAuth client secrets file
    """
    
    def __init__(self):
        """Initialize the Google Calendar integration."""
        self.SCOPES = ['https://www.googleapis.com/auth/calendar']
        self.creds = None
        self.service = None
        self.credentials_file = 'token.pickle'
        self.client_secrets_file = 'credentials.json'
        
    def authenticate(self):
        """
        Authenticate with Google Calendar API.
        
        Returns:
            bool: True if authentication was successful, False otherwise
        """
        try:
            # Check if we have valid credentials saved
            if os.path.exists(self.credentials_file):
                with open(self.credentials_file, 'rb') as token:
                    self.creds = pickle.load(token)
            
            # If there are no valid credentials, let the user log in
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    if not os.path.exists(self.client_secrets_file):
                        logger.error(f"Missing {self.client_secrets_file}. Please download from Google Cloud Console.")
                        print(f"\n❌ Missing {self.client_secrets_file}. Please download from Google Cloud Console.")
                        return False
                        
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secrets_file, self.SCOPES)
                    self.creds = flow.run_local_server(port=0)
                
                # Save the credentials for the next run
                with open(self.credentials_file, 'wb') as token:
                    pickle.dump(self.creds, token)
            
            # Build the service
            self.service = build('calendar', 'v3', credentials=self.creds)
            return True
            
        except Exception as e:
            logger.error(f"Google Calendar authentication error: {e}")
            print(f"\n❌ Google Calendar authentication error: {e}")
            return False
    
    async def list_upcoming_events(self, max_results=10):
        """
        List upcoming calendar events.
        
        Args:
            max_results (int): Maximum number of events to retrieve
            
        Returns:
            str: Formatted list of upcoming events or error message
        """
        if not self.service and not self.authenticate():
            return "Failed to authenticate with Google Calendar."
            
        try:
            # Get the current time in ISO format
            now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
            
            # Call the Calendar API
            events_result = self.service.events().list(
                calendarId='primary',
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            if not events:
                return "No upcoming events found."
                
            # Format the events
            result = "📅 Upcoming events:\n\n"
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Parse the datetime
                if 'T' in start:  # This is a datetime
                    start_time = parser.parse(start)
                    start_str = start_time.strftime('%A, %B %d, %Y at %I:%M %p')
                else:  # This is a date
                    start_time = parser.parse(start)
                    start_str = start_time.strftime('%A, %B %d, %Y (all day)')
                    
                result += f"• {event['summary']}: {start_str}\n"
                
            return result
            
        except Exception as e:
            logger.error(f"Error listing calendar events: {e}")
            return f"Error listing calendar events: {str(e)}"
    
    async def add_event(self, summary, start_time, end_time=None, description=None, location=None):
        """
        Add a new event to the calendar.
        
        Args:
            summary (str): Event title
            start_time (str): Start time in a format parseable by dateutil.parser
            end_time (str, optional): End time in a format parseable by dateutil.parser
            description (str, optional): Event description
            location (str, optional): Event location
            
        Returns:
            str: Success message with event link or error message
        """
        if not self.service and not self.authenticate():
            return "Failed to authenticate with Google Calendar."
            
        try:
            # Parse the start time
            try:
                start_dt = parser.parse(start_time)
            except:
                return "Invalid start time format. Please use a format like 'tomorrow at 3pm' or '2023-06-15 14:00'."
                
            # If no end time is provided, make it 1 hour after start time
            if not end_time:
                end_dt = start_dt + datetime.timedelta(hours=1)
            else:
                try:
                    end_dt = parser.parse(end_time)
                except:
                    return "Invalid end time format. Please use a format like 'tomorrow at 4pm' or '2023-06-15 15:00'."
            
            # Create the event
            event = {
                'summary': summary,
                'start': {
                    'dateTime': start_dt.isoformat(),
                    'timeZone': 'America/Los_Angeles',  # You might want to make this configurable
                },
                'end': {
                    'dateTime': end_dt.isoformat(),
                    'timeZone': 'America/Los_Angeles',
                },
            }
            
            if description:
                event['description'] = description
                
            if location:
                event['location'] = location
                
            # Add the event to the calendar
            event = self.service.events().insert(calendarId='primary', body=event).execute()
            
            return f"✅ Event created successfully: {event.get('htmlLink')}"
            
        except Exception as e:
            logger.error(f"Error adding calendar event: {e}")
            return f"Error adding calendar event: {str(e)}"
