"""
Main application class for the AI Assistant.
"""

import os
import json
import logging
import asyncio
import re
from dotenv import load_dotenv
from ..core.assistant import Assistant
from ..utils.screenshot import DesktopScreenshot
from ..integrations.calendar import GoogleCalendarIntegration
from ..utils.task_manager import TaskManager

# Load environment variables for API keys
load_dotenv()

logger = logging.getLogger("ai_assistant")

# Configuration management
CONFIG_FILE = "config.json"

def load_config():
    """
    Load configuration from disk.
    
    Returns:
        dict: Configuration dictionary
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {"model": "Gemini", "role": "General"}
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        return {"model": "Gemini", "role": "General"}

def save_config(config):
    """
    Save configuration to disk.
    
    Args:
        config (dict): Configuration dictionary
    """
    try:
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f)
    except Exception as e:
        logger.error(f"Error saving config: {e}")

class AIAssistantApp:
    """
    Main application class for the AI Assistant.
    
    Attributes:
        config (dict): Application configuration
        desktop_screenshot (DesktopScreenshot): Desktop screenshot utility
        assistant (Assistant): AI assistant instance
        calendar (GoogleCalendarIntegration): Google Calendar integration
        task_manager (TaskManager): Task manager for managing tasks
    """
    
    def __init__(self):
        """Initialize the AI Assistant application."""
        self.config = load_config()
        self.desktop_screenshot = DesktopScreenshot()
        self.assistant = None
        self.calendar = GoogleCalendarIntegration()
        self.task_manager = TaskManager()
        self.initialize_assistant()
        self.register_functions()
        
        # After initializing the assistant, connect it to the task manager
        if self.assistant:
            self.task_manager.assistant = self.assistant

    def initialize_assistant(self):
        """Initialize the AI assistant with better error handling."""
        try:
            model_name = self.config.get("model", "Gemini")
            role = self.config.get("role", "General")
            
            # Try to get API key from environment first
            api_key = os.getenv(f"{model_name.upper()}_API_KEY")
            
            # If not in environment, try from config
            if not api_key:
                api_key = self.config.get("api_key")
                
            if not api_key:
                print(f"\n⚠️ No API key found for {model_name}.")
                print("Please enter your API key or press Enter to switch to a different model.")
                api_key = input(f"Enter your {model_name} API Key (or press Enter to switch models): ").strip()
                
                if not api_key:
                    # Switch to alternative model
                    model_name = "OpenAI" if model_name == "Gemini" else "Gemini"
                    print(f"\nSwitching to {model_name}...")
                    api_key = os.getenv(f"{model_name.upper()}_API_KEY")
                    if not api_key:
                        api_key = input(f"Enter your {model_name} API Key: ").strip()
                
                # Save in config but not as environment variable for security
                self.config["model"] = model_name
                self.config["api_key"] = api_key
                save_config(self.config)
                
            try:
                self.assistant = Assistant(model_name, api_key, role)
                print(f"\n✅ Successfully initialized {model_name} assistant with role: {role}")
            except Exception as e:
                print(f"\n❌ Error initializing {model_name}: {str(e)}")
                print("Would you like to try a different model?")
                if input("Switch models? (y/n): ").lower().startswith('y'):
                    # Switch to alternative model
                    model_name = "OpenAI" if model_name == "Gemini" else "Gemini"
                    print(f"\nTrying {model_name}...")
                    self.config["model"] = model_name
                    save_config(self.config)
                    self.initialize_assistant()  # Recursive call with new model
                else:
                    raise
                
        except Exception as e:
            print(f"\n❌ Could not initialize AI assistant: {str(e)}")
            print("Please check your API keys and internet connection.")
            if input("Would you like to reconfigure? (y/n): ").lower().startswith('y'):
                self.configure()

    def register_functions(self):
        """Register special command functions."""
        self.functions = {
            "/calendar": self.calendar_command,
            "/help": self.show_help,
            "/document": self.document_command,
        }

    async def process_command(self, text):
        """
        Process special commands starting with /.
        
        Args:
            text (str): Command text
            
        Returns:
            bool: True if a command was processed, False otherwise
        """
        if not text.startswith("/"):
            return False
            
        parts = text.split(maxsplit=1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if command in self.functions:
            await self.functions[command](args)
            return True
        else:
            print(f"\n❌ Unknown command: {command}")
            await self.show_help("")
            return True

    async def show_help(self, args):
        """Show help for available commands."""
        print("\n📚 Available Commands:")
        print("/help - Show this help message")
        print("/calendar - Manage your Google Calendar")
        print("  /calendar list - List upcoming events")
        print("  /calendar add \"Meeting with Team\" \"tomorrow at 3pm\" - Add a new event")
        print("  /calendar add \"Doctor Appointment\" \"2023-06-15 14:00\" \"2023-06-15 15:00\" \"Annual checkup\" \"123 Medical Center\" - Add detailed event")

    async def calendar_command(self, args):
        """
        Handle calendar-related commands.
        
        Args:
            args (str): Command arguments
        """
        if not args:
            print("\n📅 Calendar Commands:")
            print("list - List upcoming events")
            print("add \"Event Title\" \"Start Time\" [\"End Time\"] [\"Description\"] [\"Location\"] - Add a new event")
            return
            
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "list":
            print("\n🔄 Fetching your calendar events...")
            result = await self.calendar.list_upcoming_events()
            print(result)
            
        elif subcommand == "add":
            # Parse the event details from the arguments
            try:
                # Extract quoted parameters
                params = re.findall(r'"([^"]*)"', subargs)
                
                if len(params) < 2:
                    print("\n❌ Not enough parameters. Format: /calendar add \"Event Title\" \"Start Time\" [\"End Time\"] [\"Description\"] [\"Location\"]")
                    return
                    
                summary = params[0]
                start_time = params[1]
                end_time = params[2] if len(params) > 2 else None
                description = params[3] if len(params) > 3 else None
                location = params[4] if len(params) > 4 else None
                
                print(f"\n🔄 Adding event: {summary}...")
                result = await self.calendar.add_event(summary, start_time, end_time, description, location)
                print(result)
                
            except Exception as e:
                print(f"\n❌ Error parsing event details: {e}")
                print("Format: /calendar add \"Event Title\" \"Start Time\" [\"End Time\"] [\"Description\"] [\"Location\"]")
        
        else:
            print(f"\n❌ Unknown calendar subcommand: {subcommand}")
            print("Available subcommands: list, add")

    async def document_command(self, args):
        """
        Handle document analysis (placeholder).
        
        Args:
            args (str): Command arguments
        """
        print("\n📄 Document analysis functionality is not implemented in this version.")

    async def run(self):
        """Run the AI Assistant application."""
        print("\n🤖 AI Assistant initialized.")
        print("------------------------------")
        
        while True:
            print("\nWhat would you like to do?")
            print("S - Speak to the assistant")
            print("T - Type a question")
            print("C - Configure settings")
            print("Q - Quit")
            
            user_input = input("\nEnter your choice > ").strip().lower()
            
            if user_input == 's':
                await self.handle_speech_input()
                print("\n✅ Ready for next command...")
            elif user_input == 't':
                await self.handle_text_input()
                print("\n✅ Ready for next command...")
            elif user_input == 'c':
                await self.configure()
                print("\n✅ Settings updated. Ready for next command...")
            elif user_input == 'q':
                print("\nExiting assistant. Goodbye! 👋")
                break
            else:
                print("\n❌ Invalid input. Please choose S, T, C, or Q.")

    async def handle_speech_input(self):
        """Handle speech input from the user."""
        from ..utils.speech import listen_for_speech
        
        prompt = listen_for_speech()
        if prompt:
            print("\n🔄 Processing your request...")
            screenshot_encoded = self.desktop_screenshot.capture()
            response = await self.assistant.answer_async(prompt, screenshot_encoded)
            print(f"\n🤖 {response}")
        else:
            print("\n⚠️ No valid speech detected. Please try again.")

    async def handle_text_input(self):
        """Handle text input from the user."""
        prompt = input("Enter your question or command: ").strip()
        if not prompt:
            print("\n⚠️ No input provided. Please try again.")
            return
        
        # Check if this is a command
        if prompt.startswith("/"):
            command_processed = await self.process_command(prompt)
            if command_processed:
                return
        
        # If not a command, process as a regular question
        include_screenshot = input("Do you want to TermCrawl to capture your screen for reference? (y/n): ").lower() == 'y'
        
        # Show animated progress indicator
        print("\n🔄 Starting request processing...", flush=True)
        loading_task = asyncio.create_task(self._animated_loading())
        
        try:
            # Add a small delay to ensure spinner starts before heavy processing
            await asyncio.sleep(0.1)
            
            screenshot_encoded = self.desktop_screenshot.capture() if include_screenshot else None
            response = await self.assistant.answer_async(prompt, screenshot_encoded)
            print(f"\n🤖 {response}")
            return response
        finally:
            # Ensure spinner is properly canceled and cleaned up
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass
            # Make sure the line is clear
            print("\r" + " " * 50 + "\r", end="", flush=True)

    async def _animated_loading(self):
        """
        Display an animated loading indicator.
        
        Raises:
            asyncio.CancelledError: When the animation is canceled
        """
        spinner = ['⣾', '⣽', '⣻', '⢿', '⡿', '⣟', '⣯', '⣷']
        i = 0
        try:
            while True:
                # Force flush to ensure immediate display
                print(f"\r{spinner[i % len(spinner)]} Processing request...", end="", flush=True)
                await asyncio.sleep(0.2)  # Slightly slower animation for better visibility
                i += 1
        except asyncio.CancelledError:
            # Clear the spinner line before exiting
            print("\r" + " " * 50 + "\r", end="", flush=True)
            raise

    async def configure(self):
        """Configure the AI Assistant settings."""
        print("\nConfiguration:")
        print("1. Change AI Model")
        print("2. Change Assistant Role")
        print("3. Update API Key")
        print("4. Back to main menu")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            self.change_model()
        elif choice == "2":
            self.change_role()
        elif choice == "3":
            self.update_api_key()
        else:
            return

    def change_model(self):
        """Change the AI model."""
        print("\nChoose your AI Model:")
        print("1. Gemini (Google AI)")
        print("2. OpenAI (GPT-4, GPT-3.5)")
        
        model_choice = input("Enter choice (1-2): ").strip()
        model_map = {"1": "Gemini", "2": "OpenAI"}
        
        if model_choice in model_map:
            self.config["model"] = model_map[model_choice]
            save_config(self.config)
            self.initialize_assistant()
            print(f"Model changed to {self.config['model']}")
        else:
            print("Invalid choice.")

    def change_role(self):
        """Change the assistant role."""
        from ..core.prompts import ROLE_PROMPTS
        
        print("\nSelect Assistant Role:")
        for i, role in enumerate(ROLE_PROMPTS.keys(), 1):
            print(f"{i}. {role}")
            
        role_choice = input(f"Enter choice (1-{len(ROLE_PROMPTS)}): ").strip()
        
        try:
            role_idx = int(role_choice) - 1
            if 0 <= role_idx < len(ROLE_PROMPTS):
                self.config["role"] = list(ROLE_PROMPTS.keys())[role_idx]
                save_config(self.config)
                self.initialize_assistant()
                print(f"Role changed to {self.config['role']}")
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a number.")

    def update_api_key(self):
        """Update the API key for the current model."""
        model = self.config.get("model", "Gemini")
        new_key = input(f"Enter new {model} API Key: ").strip()
        self.config["api_key"] = new_key
        save_config(self.config)
        self.initialize_assistant()
        print(f"API key updated for {model}")

    async def handle_browser_crawl_input(self):
        """Handle browser crawl input from the user."""
        print("\n🌐 Browser Crawl")
        print("This feature will capture content from your open browser tabs.")
        
        try:
            # Show animated progress indicator
            print("\n🔄 Starting browser crawl...", flush=True)
            # Capture screenshot and detect URLs
            self.desktop_screenshot.capture(force_new=True)
            detected_urls = self.desktop_screenshot.detect_urls()
            
            if not detected_urls:
                print("\n⚠️ No URLs detected in your screen.")
                print("Would you like to enter a URL manually?")
                if input("Enter URL manually? (y/n): ").lower().startswith('y'):
                    url = input("\nEnter the URL to analyze (e.g., https://example.com): ").strip()
                    if not url:
                        print("\n⚠️ No URL provided.")
                        return
                else:
                    return
            else:
                # Show detected URLs and let user choose
                print("\nDetected URLs:")
                for i, url in enumerate(detected_urls, 1):
                    print(f"{i}. {url}")
                
                choice = input("\nSelect URL number to analyze (or enter a different URL): ").strip()
                
                if choice.isdigit() and 1 <= int(choice) <= len(detected_urls):
                    url = detected_urls[int(choice) - 1]
                else:
                    url = choice
            
            # Add https:// if missing
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            # Show animated progress indicator
            print(f"\n🔄 Analyzing {url}...", flush=True)
            loading_task = asyncio.create_task(self._animated_loading())
            
            try:
                await asyncio.sleep(0.1)
                browser_content = self.browser_crawler.capture(force_new=True, url=url)
                
                if "error" in browser_content:
                    print(f"\n⚠️ {browser_content['error']}")
                    return
                
                if not browser_content:
                    print("\n⚠️ No content was captured from the website.")
                    return
                
                # If we got here, we have content
                content = list(browser_content.values())[0]
                print(f"\n✅ Successfully analyzed: {content['title']}")
                
                # Ask what the user wants to know about the content
                print("\nWhat would you like to know about this website?")
                prompt = input("Enter your question: ").strip()
                
                if not prompt:
                    print("\n⚠️ No question provided.")
                    return
                
                # Prepare context for the AI
                context = f"Website Analysis for {url}:\n\n"
                context += f"Title: {content['title']}\n"
                context += f"Description: {content['meta_description']}\n\n"
                context += "Main Headings:\n"
                for heading in content['headings'][:5]:
                    context += f"- {heading}\n"
                context += "\nContent Summary:\n"
                context += content['main_content'][:1500] + "...\n\n"
                
                # Process with AI
                full_prompt = f"{context}\n\nUser Question: {prompt}\n\nPlease answer based on the website content."
                
                response = await self.assistant.answer_async(full_prompt)
                print(f"\n🤖 {response}")
                
            finally:
                loading_task.cancel()
                try:
                    await loading_task
                except asyncio.CancelledError:
                    pass
                print("\r" + " " * 50 + "\r", end="", flush=True)
                
        except Exception as e:
            print(f"\n❌ Error analyzing website: {str(e)}")
