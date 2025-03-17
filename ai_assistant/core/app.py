"""
Main application class for the QuackQuery AI Assistant.
"""

import os
import json
import logging
import asyncio
import re
import getpass
from dotenv import load_dotenv
from ..core.assistant import Assistant
from ..utils.screenshot import DesktopScreenshot
from ..utils.ocr import OCRProcessor
from ..integrations.github import GitHubIntegration
from ..utils.github_intent import GitHubIntentParser
from ..integrations.file_explorer import FileExplorer
from ..utils.file_intent import FileIntentParser
from ..utils.app_intent import AppIntentParser
from ..integrations.app_launcher import AppLauncher
from ..integrations.email_manager import EmailManager
from ..utils.email_intent import EmailIntentParser

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
        ocr_processor (OCRProcessor): OCR processor for text extraction
        github (GitHubIntegration): GitHub integration
        github_intent_parser (GitHubIntentParser): GitHub intent parser
        file_explorer (FileExplorer): File explorer integration
        file_intent_parser (FileIntentParser): File intent parser
        app_intent_parser (AppIntentParser): App intent parser
        app_launcher (AppLauncher): App launcher for application launching
    """

    def __init__(self):
        """Initialize the AI Assistant application."""
        self.config = load_config()
        self.desktop_screenshot = DesktopScreenshot()
        self.assistant = None
        self.ocr_processor = OCRProcessor()
        self.github = GitHubIntegration()
        self.github_intent_parser = GitHubIntentParser()
        
        # Initialize file explorer and intent parser
        self.file_explorer = FileExplorer()
        self.file_intent_parser = FileIntentParser()
        
        # Initialize app launcher and intent parser
        self.app_launcher = AppLauncher()
        self.app_intent_parser = AppIntentParser()
        
        # Initialize Email components
        try:
            self.email_manager = EmailManager()
            self.email_intent_parser = EmailIntentParser()
            self.email_setup_complete = os.path.exists(self.email_manager.config_path)
        except Exception as e:
            logger.error(f"Error initializing email components: {str(e)}")
            self.email_manager = None
            self.email_intent_parser = None
            self.email_setup_complete = False
        
        self.initialize_assistant()
        self.register_functions()

    def initialize_assistant(self):
        """Initialize the AI assistant with the configured model and role."""
        model_name = self.config.get("model", "Gemini")
        role = self.config.get("role", "General")
        
        # Try to get API key from environment first
        api_key = os.getenv(f"{model_name.upper()}_API_KEY")
        
        # If not in environment, try from config
        if not api_key:
            api_key = self.config.get("api_key")
            
        if not api_key:
            print(f"No API key found for {model_name}. Please enter it.")
            if model_name == "Gemini":
                print("\n❗ If you don't have a Gemini API key yet:")
                print("1. Visit https://aistudio.google.com/app/apikey")
                print("2. Sign in with your Google account")
                print("3. Click 'Create API key' and follow the prompts")
                print("4. Copy the generated API key and paste it below\n")
            api_key = input(f"Enter your {model_name} API Key: ").strip()
            # Save in config but not as environment variable for security
            self.config["api_key"] = api_key
            save_config(self.config)
            
        self.assistant = Assistant(model_name, api_key, role)

    def register_functions(self):
        """Register special command functions."""
        self.functions = {
            "/help": self.show_help,
            "/document": self.document_command,
            "/ocr": self.ocr_command,
            "/github": self.github_command
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
        print("/ocr - Optical Character Recognition")
        print("  /ocr extract <image_path> - Extract text from an image file")
        print("  /ocr analyze <image_path> - Extract and analyze text from an image file")
        print("  /ocr screen - Extract text from current screen")
        
        print("\nGitHub Integration:")
        print("- You can use natural language to perform GitHub operations")
        print("- Example: 'Create a new GitHub repository called my-project'")
        print("- Example: 'Delete the GitHub repository called my-project'")
        print("- Configure your GitHub token in the settings menu (option C)")
        
        print("\nEmail Integration:")
        print("- You can use natural language to perform email operations")
        print("- Example: 'Send email to john@example.com'")
        print("- Example: 'Check my emails'")
        print("- Example: 'Read email 3'")
        print("- Example: 'AI write an email to boss@company.com'")
        print("- Configure your email account in the settings menu (option C)")

    async def document_command(self, args):
        """
        Handle document analysis (placeholder).
        
        Args:
            args (str): Command arguments
        """
        print("\n📄 Document analysis functionality is not implemented in this version.")

    async def github_command(self, args):
        """
        Handle GitHub-related commands.
        
        Args:
            args (str): Command arguments
        """
        print("\n📄 GitHub functionality is not implemented in this version.")

    async def run(self):
        """Run the QuackQuery application."""
        print("\n🦆 QuackQuery AI Assistant initialized.")
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
        
        print("\n🎤 Listening... (speak now)")
        
        try:
            speech_text = listen_for_speech()
            
            if not speech_text:
                print("\n⚠️ No speech detected. Please try again.")
                return
            
            print(f"\n🔊 You said: {speech_text}")
            
            # Check if this is a command
            if speech_text.startswith("/"):
                command_processed = await self.process_command(speech_text)
                if command_processed:
                    return
            
            # Check for GitHub intent
            github_intent = self.github_intent_parser.parse_intent(speech_text)
            if github_intent:
                result = await self.handle_github_operation(github_intent)
                print(f"\n🤖 {result}")
                return
            
            # Check for File intent
            file_intent = self.file_intent_parser.parse_intent(speech_text)
            if file_intent:
                result = await self.handle_file_operation(file_intent)
                print(f"\n🤖 {result}")
                return
            
            # Check for App intent
            app_intent = self.app_intent_parser.parse_intent(speech_text)
            if app_intent:
                result = await self.handle_app_operation(app_intent)
                print(f"\n🤖 {result}")
                return
            
            # If not a command or intent, process as a regular question
            include_screenshot = input("Do you want to QuackQuery to capture your screen for reference? (y/n): ").lower() == 'y'
            
            # Show animated progress indicator
            print("\n🔄 Starting request processing...", flush=True)
            loading_task = asyncio.create_task(self._animated_loading())
            
            try:
                # Add a small delay to ensure spinner starts before heavy processing
                await asyncio.sleep(0.1)
                
                screenshot_encoded = self.desktop_screenshot.capture() if include_screenshot else None
                response = await self.assistant.answer_async(speech_text, screenshot_encoded)
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
            
        except Exception as e:
            logger.error(f"Speech input error: {e}")
            print(f"\n❌ Error processing speech: {e}")

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
        
        # Direct check for AI email composition
        ai_email_match = re.search(r'(?:ai|assistant|help me)\s+(?:write|compose|draft|create)\s+(?:an\s+)?(?:email|mail|message)', prompt.lower())
        if ai_email_match:
            logger.info("Detected AI email composition request directly")
            # Extract email address if present
            email_match = re.search(r'to\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', prompt.lower())
            to_address = email_match.group(1) if email_match else None
            
            # Create an intent dictionary
            ai_email_intent = {
                'operation': 'ai_compose_email',
                'to_address': to_address
            }
            
            # Handle the AI email composition
            result = await self.handle_email_operation(ai_email_intent, prompt)
            print(f"\n🤖 {result}")
            return
        
        # Check for App intent - Move this check to the top for priority
        logger.info(f"Checking for app intent: '{prompt}'")
        app_intent = self.app_intent_parser.parse_intent(prompt)
        if app_intent:
            logger.info(f"Found app intent: {app_intent}")
            result = await self.handle_app_operation(app_intent)
            print(f"\n🤖 {result}")
            return
        
        # Check for GitHub intent
        logger.info(f"Checking for GitHub intent: '{prompt}'")
        github_intent = self.github_intent_parser.parse_intent(prompt)
        if github_intent:
            logger.info(f"Found GitHub intent: {github_intent}")
            result = await self.handle_github_operation(github_intent)
            print(f"\n🤖 {result}")
            return
        
        # Check for Email intent
        logger.info(f"Checking for email intent: '{prompt}'")
        if hasattr(self, 'email_intent_parser') and self.email_intent_parser:
            try:
                email_intent = self.email_intent_parser.parse_intent(prompt)
                if email_intent:
                    logger.info(f"Found email intent: {email_intent}")
                    
                    # If the operation is setup_email, redirect to configuration
                    if email_intent.get('operation') == 'setup_email':
                        print("\n📧 Redirecting to email configuration...")
                        await self.configure_email()
                        return
                    
                    # For other operations, check if email is set up
                    if not hasattr(self, 'email_setup_complete') or not self.email_setup_complete:
                        print("\n⚠️ Your email account is not set up yet.")
                        setup = input("Would you like to set up your email account now? (y/n): ").strip().lower()
                        
                        if setup == 'y':
                            await self.configure_email()
                            if not self.email_setup_complete:
                                return
                        else:
                            print("\n❌ Email operation canceled. Please set up your email account first.")
                            return
                    
                    result = await self.handle_email_operation(email_intent, prompt)
                    print(f"\n🤖 {result}")
                    return
            except Exception as e:
                logger.error(f"Error processing email intent: {e}")
                print(f"\n❌ Error processing email command: {e}")
                return
        
        # Check for File intent
        logger.info(f"Checking for file intent: '{prompt}'")
        file_intent = self.file_intent_parser.parse_intent(prompt)
        if file_intent:
            logger.info(f"Found file intent: {file_intent}")
            result = await self.handle_file_operation(file_intent)
            print(f"\n🤖 {result}")
            return
        
        # If not a command or intent, process as a regular question
        include_screenshot = input("Do you want to QuackQuery to capture your screen for reference? (y/n): ").lower() == 'y'
        
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
        print("4. Configure GitHub Integration")
        print("5. Configure Email Account")
        print("6. Back to main menu")
        
        choice = input("Enter choice (1-6): ").strip()
        
        if choice == "1":
            self.change_model()
        elif choice == "2":
            self.change_role()
        elif choice == "3":
            self.update_api_key()
        elif choice == "4":
            self.configure_github()
        elif choice == "5":
            await self.configure_email()
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

    async def handle_image_analysis(self):
        """Handle image text analysis."""
        print("\n🖼️ Image Text Analysis")
        print("This feature extracts text from images and analyzes it using AI.")
        
        # Ask if user wants to use screen or file
        use_screen = input("\nUse current screen for text extraction? (y/n): ").lower().startswith('y')
        
        if use_screen:
            # Capture screen and extract text
            print("\n🔄 Capturing screen and extracting text...")
            screenshot_encoded = self.desktop_screenshot.capture(force_new=True)
            
            # Convert the raw screenshot to a format pytesseract can handle
            import numpy as np
            from PIL import Image
            
            # Use the raw screenshot array instead of the encoded version
            screenshot = self.desktop_screenshot.screenshot
            
            # Make sure screenshot is a valid numpy array
            if screenshot is not None and isinstance(screenshot, np.ndarray):
                extracted_text = self.ocr_processor.extract_text(screenshot)
            else:
                extracted_text = "Error: Failed to capture screenshot properly."
        else:
            # Ask for image path
            image_path = input("\nEnter the path to the image file: ").strip()
            
            if not image_path:
                print("\n⚠️ No image path provided. Please try again.")
                return
            
            # Check if file exists
            if not os.path.exists(image_path):
                print(f"\n❌ Image file not found: {image_path}")
                return
            
            # Extract text from image
            print("\n🔄 Extracting text from image...")
            extracted_text = self.ocr_processor.extract_text_from_file(image_path)
        
        # Continue with the rest of the method (showing extracted text and AI analysis)
        if not extracted_text or extracted_text.startswith("Error:") or extracted_text == "No text detected in image.":
            print(f"\n⚠️ {extracted_text}")
            return
            
        print("\n📝 Extracted Text:")
        print("=" * 50)
        print(extracted_text)
        print("=" * 50)
        
        # Ask if user wants AI analysis
        analyze = input("\nWould you like AI to analyze this text? (y/n): ").lower().startswith('y')
        
        if analyze:
            print("\n🔄 Analyzing text with AI...", flush=True)
            
            # Ask for specific question
            question = input("\nAny specific question about the text? (Press Enter to skip): ").strip()
            
            # Create prompt for AI
            prompt = f"The following text was extracted from an image using OCR:\n\n{extracted_text}\n\n"
            
            if question:
                prompt += f"Question: {question}\n\nPlease analyze this text and answer the question."
            else:
                prompt += "Please analyze this text and provide insights about its content, context, and key information."
            
            # Get AI analysis
            response = await self.assistant.answer_async(prompt)
            
            print("\n🤖 AI Analysis:")
            print("=" * 50)
            print(response)
            print("=" * 50)

    async def ocr_command(self, args):
        """
        Handle OCR-related commands.
        
        Args:
            args (str): Command arguments
        """
        if not args:
            print("\n📷 OCR Commands:")
            print("extract <image_path> - Extract text from an image file")
            print("analyze <image_path> - Extract and analyze text from an image file")
            print("screen - Extract text from current screen")
            return
            
        parts = args.split(maxsplit=1)
        subcommand = parts[0].lower()
        subargs = parts[1] if len(parts) > 1 else ""
        
        if subcommand == "extract" and subargs:
            print(f"\n🔄 Extracting text from image: {subargs}...")
            
            # Extract text from image file
            extracted_text = self.ocr_processor.extract_text_from_file(subargs)
            
            print("\n📝 Extracted Text:")
            print("=" * 50)
            print(extracted_text)
            print("=" * 50)
            
        elif subcommand == "analyze" and subargs:
            print(f"\n🔄 Analyzing text from image: {subargs}...")
            
            # Extract text from image file
            extracted_text = self.ocr_processor.extract_text_from_file(subargs)
            
            if not extracted_text or extracted_text.startswith("Error:") or extracted_text == "No text detected in image.":
                print(f"\n⚠️ {extracted_text}")
                return
                
            print("\n📝 Extracted Text:")
            print("=" * 50)
            print(extracted_text)
            print("=" * 50)
            
            # Create prompt for AI
            prompt = f"The following text was extracted from an image using OCR:\n\n{extracted_text}\n\n"
            prompt += "Please analyze this text and provide insights about its content, context, and key information."
            
            # Get AI analysis
            print("\n🧠 Analyzing extracted text...")
            response = await self.assistant.answer_async(prompt)
            
            print("\n🤖 AI Analysis:")
            print("=" * 50)
            print(response)
            print("=" * 50)
            
        elif subcommand == "screen":
            print("\n🔄 Capturing screen and extracting text...")
            
            # Capture screen
            self.desktop_screenshot.capture(force_new=True)
            
            # Convert base64 to image
            import base64
            from PIL import Image
            import io
            
            # Get the raw screenshot from desktop_screenshot
            screenshot = self.desktop_screenshot.screenshot
            
            # Extract text using OCR
            extracted_text = self.ocr_processor.extract_text(screenshot)
            
            print("\n📝 Extracted Text:")
            print("=" * 50)
            print(extracted_text)
            print("=" * 50)
            
        else:
            print(f"\n❌ Invalid OCR command or missing image path.")
            print("Usage: /ocr extract <image_path>")
            print("       /ocr analyze <image_path>")
            print("       /ocr screen")

    async def handle_github_operation(self, intent):
        """
        Handle GitHub operations based on detected intent.
        
        Args:
            intent (dict): GitHub intent information
            
        Returns:
            str: Result of the GitHub operation
        """
        operation = intent["operation"]
        params = intent["params"]
        
        # Check if authenticated first
        if not self.github.authenticated and operation != "authenticate":
            print("\n⚠️ You need to authenticate with GitHub first.")
            token = input("Enter your GitHub personal access token: ").strip()
            if not token:
                return "GitHub authentication canceled. Please provide a token to use GitHub features."
            
            if not self.github.authenticate(token):
                return "GitHub authentication failed. Please check your token and try again."
        
        # Handle different operations
        if operation == "authenticate":
            token = input("\nEnter your GitHub personal access token: ").strip()
            if not token:
                return "GitHub authentication canceled. Please provide a token to use GitHub features."
            
            if self.github.authenticate(token):
                return "Successfully authenticated with GitHub!"
            else:
                return "GitHub authentication failed. Please check your token and try again."
            
        elif operation == "list_repos":
            print("\n🔄 Fetching your GitHub repositories...")
            return self.github.list_repositories()
        
        elif operation == "create_repo":
            name = params.get("name")
            description = params.get("description")
            private = params.get("private", False)
            
            print(f"\n🔄 Creating GitHub repository: {name}...")
            return self.github.create_repository(name, description, private)
        
        elif operation == "list_issues":
            repo = params.get("repo")
            state = params.get("state", "open")
            
            print(f"\n🔄 Fetching {state} issues for {repo}...")
            return self.github.list_issues(repo, state)
        
        elif operation == "create_issue":
            repo = params.get("repo")
            title = params.get("title")
            body = params.get("body")
            labels = params.get("labels")
            
            print(f"\n🔄 Creating issue in {repo}: {title}...")
            return self.github.create_issue(repo, title, body, labels)
        
        elif operation == "create_file":
            repo = params.get("repo")
            path = params.get("path")
            content = params.get("content")
            message = params.get("message")
            
            print(f"\n🔄 Creating/updating file in {repo}: {path}...")
            return self.github.create_file(repo, path, content, message)
        
        elif operation == "delete_repo":
            repo = params.get("repo")
            
            # Clean up the repository name
            repo = repo.strip()
            
            # Display the repository name clearly
            print(f"\n🔍 Repository to delete: '{repo}'")
            
            # Add confirmation for safety
            confirm = input(f"\n⚠️ WARNING: You are about to delete the repository '{repo}'.\nThis action CANNOT be undone.\nType the repository name to confirm deletion: ").strip()
            
            if confirm == repo:
                print(f"\n🔄 Deleting GitHub repository: {repo}...")
                return self.github.delete_repository(repo)
            else:
                return f"Repository deletion canceled. You entered '{confirm}' but the repository name is '{repo}'."
        elif operation == "general_github":
            return "I detected a GitHub-related request, but I'm not sure what specific operation you want to perform. You can ask me to:\n\n" + \
                   "- List your GitHub repositories\n" + \
                   "- Create a new GitHub repository\n" + \
                   "- Delete a GitHub repository\n" + \
                   "- List issues in a repository\n" + \
                   "- Create a new issue\n" + \
                   "- Create or update a file in a repository"
        
        return "Unsupported GitHub operation."

    def configure_github(self):
        """Configure GitHub integration settings."""
        print("\nGitHub Integration Configuration:")
        print("1. Set GitHub Access Token")
        print("2. View Current GitHub Status")
        print("3. Remove GitHub Access Token")
        print("4. Back to configuration menu")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            token = input("\nEnter your GitHub Personal Access Token: ").strip()
            if token:
                if self.github.authenticate(token):
                    # Save token to environment variable
                    os.environ["GITHUB_TOKEN"] = token
                    
                    # Optionally save to .env file for persistence
                    try:
                        with open(".env", "a+") as env_file:
                            env_file.seek(0)
                            content = env_file.read()
                            if "GITHUB_TOKEN" not in content:
                                env_file.write(f"\nGITHUB_TOKEN={token}\n")
                            else:
                                # Replace existing token
                                lines = content.splitlines()
                                with open(".env", "w") as new_env_file:
                                    for line in lines:
                                        if line.startswith("GITHUB_TOKEN="):
                                            new_env_file.write(f"GITHUB_TOKEN={token}\n")
                                        else:
                                            new_env_file.write(f"{line}\n")
                    except Exception as e:
                        logger.error(f"Error saving GitHub token to .env file: {e}")
                    
                    print(f"\n✅ GitHub token set successfully! Authenticated as: {self.github.username}")
                else:
                    print("\n❌ GitHub authentication failed. Please check your token and try again.")
            else:
                print("\n⚠️ No token provided. GitHub integration will not be available.")
            
        elif choice == "2":
            if self.github.authenticated:
                print(f"\n✅ GitHub Status: Authenticated as {self.github.username}")
                print("GitHub integration is active and ready to use.")
            else:
                print("\n⚠️ GitHub Status: Not authenticated")
                print("You need to set a GitHub access token to use GitHub features.")
            
        elif choice == "3":
            if "GITHUB_TOKEN" in os.environ:
                del os.environ["GITHUB_TOKEN"]
            
            # Remove from .env file if it exists
            try:
                if os.path.exists(".env"):
                    with open(".env", "r") as env_file:
                        lines = env_file.readlines()
                
                    with open(".env", "w") as env_file:
                        for line in lines:
                            if not line.startswith("GITHUB_TOKEN="):
                                env_file.write(line)
            except Exception as e:
                logger.error(f"Error removing GitHub token from .env file: {e}")
            
            # Reset GitHub integration
            self.github = GitHubIntegration()
            print("\n✅ GitHub token removed successfully.")
        
        else:
            return

    async def handle_file_operation(self, intent):
        """
        Handle file operations based on detected intent.
        
        Args:
            intent (dict): File intent information
            
        Returns:
            str: Result of the file operation
        """
        operation = intent["operation"]
        params = intent["params"]
        
        # Handle different operations
        if operation == "list_directory":
            path = params.get("path")
            return self.file_explorer.list_directory(path)
        
        elif operation == "create_directory":
            path = params.get("path")
            return self.file_explorer.create_directory(path)
        
        elif operation == "delete_item":
            path = params.get("path")
            use_trash = params.get("use_trash", True)
            
            # Add confirmation for safety
            confirm = input(f"\n⚠️ WARNING: You are about to delete '{path}'.\nThis action cannot be undone.\nType 'yes' to confirm: ").strip().lower()
            
            if confirm == "yes":
                return self.file_explorer.delete_item(path, use_trash)
            else:
                return "Deletion canceled."
        
        elif operation == "move_item":
            source = params.get("source")
            destination = params.get("destination")
            return self.file_explorer.move_item(source, destination)
        
        elif operation == "copy_item":
            source = params.get("source")
            destination = params.get("destination")
            return self.file_explorer.copy_item(source, destination)
        
        elif operation == "rename_item":
            path = params.get("path")
            new_name = params.get("new_name")
            return self.file_explorer.rename_item(path, new_name)
        
        elif operation == "create_file":
            path = params.get("path")
            content = params.get("content", "")
            return self.file_explorer.create_file(path, content)
        
        elif operation == "read_file":
            path = params.get("path")
            return self.file_explorer.read_file(path)
        
        elif operation == "search_files":
            pattern = params.get("pattern", "*")
            path = params.get("path")
            content_search = params.get("content_search")
            return self.file_explorer.search_files(pattern, path, content_search)
        
        elif operation == "change_directory":
            path = params.get("path")
            return self.file_explorer.set_current_directory(path)
        
        elif operation == "zip_items":
            output_path = params.get("output_path")
            items = params.get("items", [])
            return self.file_explorer.zip_items(output_path, items)
        
        elif operation == "unzip_file":
            zip_path = params.get("zip_path")
            extract_path = params.get("extract_path")
            return self.file_explorer.unzip_file(zip_path, extract_path)
        
        elif operation == "general_file":
            return "I detected a file-related request, but I'm not sure what specific operation you want to perform. You can ask me to:\n\n" + \
                   "- List files in a directory\n" + \
                   "- Create a new directory or file\n" + \
                   "- Delete a file or directory\n" + \
                   "- Move or copy files\n" + \
                   "- Rename files or directories\n" + \
                   "- Read file contents\n" + \
                   "- Search for files\n" + \
                   "- Change the current directory\n" + \
                   "- Zip or unzip files"
        
        return "Unsupported file operation."

    async def handle_app_operation(self, intent):
        """
        Handle application operations based on detected intent.
        
        Args:
            intent (dict): App intent information
            
        Returns:
            str: Result of the app operation
        """
        operation = intent["operation"]
        params = intent["params"]
        
        # Handle different operations
        if operation == "launch_app":
            app_name = params.get("app_name")
            return self.launch_app(app_name)
        
        elif operation == "list_apps":
            return self.list_apps()
        
        elif operation == "general_app":
            return "I detected an app-related request, but I'm not sure what specific operation you want to perform. You can ask me to:\n\n" + \
                   "- List installed apps\n" + \
                   "- Launch an app"
        
        return "Unsupported app operation."

    def launch_app(self, app_name):
        """
        Launch an application based on the given app name.
        
        Args:
            app_name (str): Name of the application to launch
            
        Returns:
            str: Result of the app launch operation
        """
        try:
            # Use a simple method to launch the app
            result = self.app_launcher.launch_app(app_name)
            return result
        except Exception as e:
            logger.error(f"Error launching app: {e}")
            return f"Error launching application: {str(e)}"

    async def configure_email(self):
        """Configure email account settings."""
        print("\nEmail Account Configuration:")
        print("1. Set up email account")
        print("2. View current email status")
        print("3. Remove email account")
        print("4. Back to configuration menu")
        
        choice = input("Enter choice (1-4): ").strip()
        
        if choice == "1":
            # Initialize Email components if not already done
            if not hasattr(self, 'email_manager') or not self.email_manager:
                self.email_manager = EmailManager()
                self.email_intent_parser = EmailIntentParser()
            
            email_address = input("Enter your email address: ").strip()
            password = getpass.getpass("Enter your email password or app password: ")
            
            result = self.email_manager.setup_email_account(email_address, password)
            print(result)
            
            self.email_setup_complete = os.path.exists(self.email_manager.config_path)
            print(f"Email setup complete: {self.email_setup_complete}")
            
        elif choice == "2":
            if hasattr(self, 'email_manager') and self.email_manager:
                if os.path.exists(self.email_manager.config_path):
                    print("\n✅ Email Status: Configured")
                    print(f"Email configuration file: {self.email_manager.config_path}")
                    
                    # Try to load the email configuration to show the email address
                    try:
                        # Check if the method exists
                        if hasattr(self.email_manager, 'load_email_config'):
                            config = self.email_manager.load_email_config()
                            if config and 'email' in config:
                                print(f"Email address: {config['email']}")
                            else:
                                print("Email address: Not available")
                        else:
                            # Alternative approach if method doesn't exist
                            try:
                                with open(self.email_manager.config_path, 'r') as f:
                                    config = json.load(f)
                                    if 'email' in config:
                                        print(f"Email address: {config['email']}")
                                    else:
                                        print("Email address: Not available")
                            except Exception as e:
                                print(f"Could not read email configuration: {e}")
                    except Exception as e:
                        print(f"Error accessing email configuration: {e}")
                else:
                    print("\n⚠️ Email Status: Not configured")
                    print("You need to set up your email account to use email features.")
            else:
                print("\n⚠️ Email Status: Not initialized")
                print("Email functionality is not available.")
            
        elif choice == "3":
            if hasattr(self, 'email_manager') and self.email_manager:
                if os.path.exists(self.email_manager.config_path):
                    confirm = input("\n⚠️ Are you sure you want to remove your email account? (y/n): ").strip().lower()
                    
                    if confirm == 'y':
                        try:
                            os.remove(self.email_manager.config_path)
                            self.email_setup_complete = False
                            print("\n✅ Email account removed successfully.")
                        except Exception as e:
                            print(f"\n❌ Error removing email account: {e}")
                    else:
                        print("\nEmail account removal canceled.")
                else:
                    print("\n⚠️ No email account is configured.")
            else:
                print("\n⚠️ Email functionality is not available.")
        
        else:
            return

    async def handle_email_operation(self, intent, original_input):
        """
        Handle email-related operations.
        
        Args:
            intent: A dictionary containing the email operation and parameters
            original_input: The original user input
            
        Returns:
            A string response to the user
        """
        if not self.email_manager:
            return "Email functionality is not available. Please make sure you have the required dependencies installed."
        
        operation = intent.get('operation')
        logger.info(f"Handling email operation: {operation}")
        
        # Check if email is set up for operations that require it
        if operation != 'setup_email' and not self.email_setup_complete:
            return "Your email account is not set up yet. Please use 'set up email' to configure your email account."
        
        try:
            if operation == 'setup_email':
                print("\nSetting up your email account...")
                print(f"Email config path: {self.email_manager.config_path}")
                print(f"Config path exists before setup: {os.path.exists(self.email_manager.config_path)}")
                
                email_address = input("Enter your email address: ").strip()
                password = getpass.getpass("Enter your email password or app password: ")
                
                result = self.email_manager.setup_email_account(email_address, password)
                
                print(f"Config path exists after setup: {os.path.exists(self.email_manager.config_path)}")
                self.email_setup_complete = os.path.exists(self.email_manager.config_path)
                print(f"Email setup complete flag: {self.email_setup_complete}")
                
                return result
                
            elif operation == 'send_email':
                to_address = intent.get('to_address')
                subject = intent.get('subject', '')
                
                if not to_address:
                    to_address = input("Enter recipient's email address: ").strip()
                    
                if not subject:
                    subject = input("Enter email subject: ").strip()
                
                print(f"\nComposing email to {to_address} with subject '{subject}'")
                print("Enter your message (type '.' on a new line to finish):")
                
                body_lines = []
                while True:
                    line = input()
                    if line.strip() == '.':
                        break
                    body_lines.append(line)
                
                body = '\n'.join(body_lines)
                
                return self.email_manager.send_email(to_address, subject, body)
                
            elif operation == 'list_emails':
                from_address = intent.get('from_address')
                
                # Extract additional parameters from the original input
                folder = "inbox"
                limit = 10
                unread_only = "unread" in original_input.lower()
                
                if "sent" in original_input.lower():
                    folder = "sent"
                elif "draft" in original_input.lower():
                    folder = "drafts"
                
                # Try to extract a number if specified
                num_match = re.search(r'(\d+) (?:email|mail|message)', original_input.lower())
                if num_match:
                    limit = int(num_match.group(1))
                
                emails, summary = self.email_manager.list_emails(
                    folder=folder,
                    limit=limit,
                    unread_only=unread_only,
                    from_address=from_address
                )
                
                if not emails:
                    return summary
                
                # Format the email list
                result = f"{summary}\n\n"
                for i, email in enumerate(emails):
                    status = "📩 NEW" if not email['is_read'] else "📨"
                    result += f"{i+1}. {status} From: {email['from']}\n"
                    result += f"   Subject: {email['subject']}\n"
                    result += f"   Date: {email['date']}\n"
                    result += f"   Preview: {email['body']}\n\n"
                
                return result
                
            elif operation == 'read_email':
                email_id = intent.get('email_id')
                
                # If we don't have an email ID, we need to list emails first
                if not email_id:
                    emails, summary = self.email_manager.list_emails(limit=10)
                    
                    if not emails:
                        return "No emails found."
                    
                    # Format the email list
                    result = f"{summary}\n\n"
                    for i, email in enumerate(emails):
                        status = "📩 NEW" if not email['is_read'] else "📨"
                        result += f"{i+1}. {status} From: {email['from']}\n"
                        result += f"   Subject: {email['subject']}\n"
                    
                    email_id = input("\nEnter the number of the email to read: ").strip()
                
                # Convert from 1-based (user) to 0-based (internal) indexing
                try:
                    email_index = int(email_id) - 1
                    
                    # Get the list of emails
                    emails, _ = self.email_manager.list_emails(limit=20)
                    
                    if not emails or email_index < 0 or email_index >= len(emails):
                        return f"Email #{email_id} not found. Please check the email number."
                    
                    # Get the actual email ID from the list
                    actual_email_id = emails[email_index]['id']
                    
                    # Read the email
                    email_dict, summary = self.email_manager.read_email(actual_email_id)
                    
                    if not email_dict:
                        return summary
                    
                    # Format the email content
                    result = f"Email #{email_id}:\n\n"
                    result += f"From: {email_dict['from']}\n"
                    result += f"To: {email_dict['to']}\n"
                    result += f"Date: {email_dict['date']}\n"
                    result += f"Subject: {email_dict['subject']}\n\n"
                    result += email_dict['body']
                    
                    return result
                    
                except ValueError:
                    return f"Invalid email number: {email_id}"
                
            elif operation == 'reply_to_email':
                email_id = intent.get('email_id')
                
                # If we don't have an email ID, we need to list emails first
                if not email_id:
                    return "Please specify which email you want to reply to, e.g., 'reply to email 3'"
                
                # Convert from 1-based (user) to 0-based (internal) indexing
                try:
                    email_index = int(email_id) - 1
                    
                    # Get the list of emails
                    emails, _ = self.email_manager.list_emails(limit=20)
                    
                    if not emails or email_index < 0 or email_index >= len(emails):
                        return f"Email #{email_id} not found. Please check the email number."
                    
                    # Get the actual email ID from the list
                    actual_email_id = emails[email_index]['id']
                    
                    # Read the email to show what we're replying to
                    email_dict, _ = self.email_manager.read_email(actual_email_id)
                    
                    if not email_dict:
                        return f"Could not read email #{email_id}"
                    
                    print(f"\nReplying to email from {email_dict['from']} with subject '{email_dict['subject']}'")
                    print("Enter your reply (type '.' on a new line to finish):")
                    
                    reply_lines = []
                    while True:
                        line = input()
                        if line.strip() == '.':
                            break
                        reply_lines.append(line)
                    
                    reply_body = '\n'.join(reply_lines)
                    
                    # Ask about including the original email
                    include_original = input("Include original email in reply? (y/n): ").strip().lower() == 'y'
                    
                    return self.email_manager.reply_to_email(actual_email_id, reply_body, include_original)
                    
                except ValueError:
                    return f"Invalid email number: {email_id}"
                
            elif operation == 'forward_email':
                email_id = intent.get('email_id')
                to_address = intent.get('to_address')
                
                # If we don't have an email ID or to_address, we need more information
                if not email_id:
                    return "Please specify which email you want to forward, e.g., 'forward email 3 to john@example.com'"
                
                if not to_address:
                    to_address = input("Enter the email address to forward to: ").strip()
                
                # Convert from 1-based (user) to 0-based (internal) indexing
                try:
                    email_index = int(email_id) - 1
                    
                    # Get the list of emails
                    emails, _ = self.email_manager.list_emails(limit=20)
                    
                    if not emails or email_index < 0 or email_index >= len(emails):
                        return f"Email #{email_id} not found. Please check the email number."
                    
                    # Get the actual email ID from the list
                    actual_email_id = emails[email_index]['id']
                    
                    # Read the email to show what we're forwarding
                    email_dict, _ = self.email_manager.read_email(actual_email_id)
                    
                    if not email_dict:
                        return f"Could not read email #{email_id}"
                    
                    print(f"\nForwarding email from {email_dict['from']} with subject '{email_dict['subject']}' to {to_address}")
                    print("Enter an optional message to include (type '.' on a new line to finish):")
                    
                    forward_lines = []
                    while True:
                        line = input()
                        if line.strip() == '.':
                            break
                        forward_lines.append(line)
                    
                    forward_message = '\n'.join(forward_lines)
                    
                    return self.email_manager.forward_email(actual_email_id, to_address, forward_message)
                    
                except ValueError:
                    return f"Invalid email number: {email_id}"
                
            elif operation == 'delete_email':
                email_id = intent.get('email_id')
                
                # If we don't have an email ID, we need to list emails first
                if not email_id:
                    return "Please specify which email you want to delete, e.g., 'delete email 3'"
                
                # Convert from 1-based (user) to 0-based (internal) indexing
                try:
                    email_index = int(email_id) - 1
                    
                    # Get the list of emails
                    emails, _ = self.email_manager.list_emails(limit=20)
                    
                    if not emails or email_index < 0 or email_index >= len(emails):
                        return f"Email #{email_id} not found. Please check the email number."
                    
                    # Get the actual email ID from the list
                    actual_email_id = emails[email_index]['id']
                    
                    # Confirm deletion
                    email_dict, _ = self.email_manager.read_email(actual_email_id, mark_as_read=False)
                    
                    if not email_dict:
                        return f"Could not read email #{email_id}"
                    
                    print(f"\nAre you sure you want to delete this email?")
                    print(f"From: {email_dict['from']}")
                    print(f"Subject: {email_dict['subject']}")
                    
                    confirm = input("Type 'yes' to confirm: ").strip().lower()
                    
                    if confirm == 'yes':
                        result = self.email_manager.delete_email(actual_email_id)
                        return result
                    else:
                        return "Email deletion cancelled."
                    
                except ValueError:
                    return f"Invalid email number: {email_id}"
                
            elif operation == 'ai_compose_email':
                to_address = intent.get('to_address')
                
                if not to_address:
                    to_address = input("Enter recipient's email address: ").strip()
                
                subject = input("Enter email subject: ").strip()
                
                print("\nDescribe what you want the AI to write in this email:")
                instructions = input("Your instructions: ").strip()
                
                # Show animated progress indicator
                print("\n🔄 Generating email content...", flush=True)
                loading_task = asyncio.create_task(self._animated_loading())
                
                try:
                    # Create a prompt for the AI
                    prompt = f"""
                    Please write an email with the following requirements:
                    
                    To: {to_address}
                    Subject: {subject}
                    
                    Instructions: {instructions}
                    
                    Please format your response as an email body only, without including 'To:', 'Subject:', 
                    or any other email headers. The email should be professional and well-written.
                    """
                    
                    # Generate the email content using the AI assistant
                    email_body = await self.assistant.answer_async(prompt)
                    
                    # Display the generated email
                    print("\n📝 Generated Email:")
                    print("=" * 50)
                    print(f"To: {to_address}")
                    print(f"Subject: {subject}")
                    print("=" * 50)
                    print(email_body)
                    print("=" * 50)
                    
                    # Ask if the user wants to edit, send, or discard the email
                    choice = input("\nDo you want to (E)dit, (S)end, or (D)iscard this email? ").strip().lower()
                    
                    if choice == 's':
                        # Send the email
                        return self.email_manager.send_email(to_address, subject, email_body)
                    elif choice == 'e':
                        # Allow the user to edit the email
                        print("\nEdit the email content (type '.' on a new line to finish):")
                        print(email_body)
                        
                        edited_lines = []
                        while True:
                            line = input()
                            if line.strip() == '.':
                                break
                            edited_lines.append(line)
                        
                        if edited_lines:
                            edited_body = '\n'.join(edited_lines)
                            return self.email_manager.send_email(to_address, subject, edited_body)
                        else:
                            return "Email discarded."
                    else:
                        return "Email discarded."
                finally:
                    # Ensure spinner is properly canceled and cleaned up
                    loading_task.cancel()
                    try:
                        await loading_task
                    except asyncio.CancelledError:
                        pass
                    # Make sure the line is clear
                    print("\r" + " " * 50 + "\r", end="", flush=True)
                
            elif operation == 'generic_email':
                return """I can help you with email tasks. Try saying:
- set up email
- send email to someone@example.com
- check my emails
- read email 3
- reply to email 2
- forward email 1 to someone@example.com
- delete email 4
- ai write an email to someone@example.com"""
            
            else:
                return f"Unknown email operation: {operation}"
            
        except Exception as e:
            logger.error(f"Error executing email operation {operation}: {str(e)}")
            return f"Error executing email operation: {str(e)}"

    async def compose_email_with_ai(self):
        """Use AI to compose an email based on user instructions."""
        print("\n✍️ AI Email Composition")
        print("------------------------------ \n")
        
        # Get recipient
        to_address = input("To: ").strip()
        if not to_address:
            print("Recipient email address is required.")
            return
        
        # Get subject
        subject = input("Subject: ").strip()
        if not subject:
            print("Email subject is required.")
            return
        
        # Get instructions for the AI
        print("\nDescribe what you want the AI to write in this email:")
        print("(For example: 'Write a professional email requesting a meeting next week' or")
        print("'Compose a friendly follow-up to our conversation yesterday about the project')")
        instructions = input("\nYour instructions: ").strip()
        
        if not instructions:
            print("Instructions are required to generate the email.")
            return
        
        # Show animated progress indicator
        print("\n🔄 Generating email content...", flush=True)
        loading_task = asyncio.create_task(self._animated_loading())
        
        try:
            # Create a prompt for the AI
            prompt = f"""
            Please write an email with the following requirements:
            
            To: {to_address}
            Subject: {subject}
            
            Instructions: {instructions}
            
            Please format your response as an email body only, without including 'To:', 'Subject:', 
            or any other email headers. The email should be professional and well-written.
            """
            
            # Generate the email content using the AI assistant
            email_body = await self.assistant.answer_async(prompt)
            
            # Display the generated email
            print("\n📝 Generated Email:")
            print("=" * 50)
            print(f"To: {to_address}")
            print(f"Subject: {subject}")
            print("=" * 50)
            print(email_body)
            print("=" * 50)
            
            # Ask if the user wants to edit, send, or discard the email
            choice = input("\nDo you want to (E)dit, (S)end, or (D)iscard this email? ").strip().lower()
            
            if choice == 's':
                # Send the email
                result = self.email_manager.send_email(to_address, subject, email_body)
                print(result)
            elif choice == 'e':
                # Allow the user to edit the email
                print("\nEdit the email content (type '.' on a new line to finish):")
                print(email_body)
                
                edited_lines = []
                while True:
                    line = input()
                    if line.strip() == '.':
                        break
                    edited_lines.append(line)
                
                if edited_lines:
                    edited_body = '\n'.join(edited_lines)
                    result = self.email_manager.send_email(to_address, subject, edited_body)
                    print(result)
                else:
                    print("Email discarded.")
            else:
                print("Email discarded.")
            
        except Exception as e:
            logger.error(f"Error generating email with AI: {str(e)}")
            print(f"\n❌ Error generating email: {str(e)}")
        finally:
            # Ensure spinner is properly canceled and cleaned up
            loading_task.cancel()
            try:
                await loading_task
            except asyncio.CancelledError:
                pass
            # Make sure the line is clear
            print("\r" + " " * 50 + "\r", end="", flush=True)
