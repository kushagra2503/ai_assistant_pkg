import asyncio
import os
from dotenv import load_dotenv

# Import from the QuackQuery package - using only the modules that definitely exist
from ai_assistant import Assistant, DesktopScreenshot
from ai_assistant.utils.speech import listen_for_speech

# Try to import automation components with error handling
try:
    # Try to import file management components
    from ai_assistant.utils.file_intent import FileIntentParser
    from ai_assistant.integrations.file_manager import FileManager
    file_automation_available = True
except ImportError:
    file_automation_available = False

try:
    # Try to import GitHub components
    from ai_assistant.utils.github_intent import GitHubIntentParser
    from ai_assistant.integrations.github_integration import GitHubIntegration
    github_automation_available = True
except ImportError:
    github_automation_available = False

try:
    # Try to import app launcher components
    from ai_assistant.utils.app_intent import AppIntentParser
    from ai_assistant.integrations.app_launcher import AppLauncher
    app_automation_available = True
except ImportError:
    app_automation_available = False

# Load environment variables (for API keys)
load_dotenv()

async def main():
    print("Initializing QuackQuery Assistant...")
    
    # Initialize the assistant with Gemini model
    assistant = Assistant(
        model_choice="Gemini",
        role="General"
    )
    
    # Initialize automation components that are available
    automation_options = []
    
    # Initialize file automation if available
    file_manager = None
    file_intent_parser = None
    if file_automation_available:
        try:
            file_manager = FileManager()
            file_intent_parser = FileIntentParser()
            automation_options.append("File operations")
            print("File automation enabled")
        except Exception as e:
            print(f"File automation initialization failed: {str(e)}")
    
    # Initialize GitHub integration if available and token exists
    github_integration = None
    github_intent_parser = None
    if github_automation_available:
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token:
            try:
                github_integration = GitHubIntegration(github_token)
                github_intent_parser = GitHubIntentParser()
                automation_options.append("GitHub operations")
                print("GitHub integration enabled")
            except Exception as e:
                print(f"GitHub automation initialization failed: {str(e)}")
        else:
            print("GitHub integration disabled (no token found)")
    
    # Initialize app launcher if available
    app_launcher = None
    app_intent_parser = None
    if app_automation_available:
        try:
            app_launcher = AppLauncher()
            app_intent_parser = AppIntentParser()
            automation_options.append("Application launching")
            print("App launcher enabled")
        except Exception as e:
            print(f"App launcher initialization failed: {str(e)}")
    
    # Initialize the desktop screenshot utility
    screenshot = DesktopScreenshot()
    
    # Ask user for interaction mode
    print("\nHow would you like to interact with QuackQuery?")
    print("1. Voice input")
    print("2. Text input with screenshot")
    if automation_options:
        print("3. Automation commands")
    choice = input(f"Enter your choice (1, 2{', 3' if automation_options else ''}): ").strip()
    
    if choice == "1":
        # Use voice input
        print("\nUsing voice input...")
        question = listen_for_speech()
        
        if not question:
            print("No valid speech detected. Exiting.")
            return
            
        print(f"\nQuestion: {question}")
        print("-" * 50)
        
        # Ask if user wants to include a screenshot
        include_screenshot = input("Include screenshot with your question? (y/n): ").lower() == 'y'
        screenshot_encoded = screenshot.capture(force_new=True) if include_screenshot else None
        
        # Get the response from the assistant
        print("Sending question to AI...")
        response = await assistant.answer_async(question, screenshot_encoded)
        
        print("\nResponse:")
        print("=" * 50)
        print(response)
        print("=" * 50)
    
    elif choice == "2":
        # Capture a screenshot
        print("\nCapturing desktop screenshot...")
        screenshot_encoded = screenshot.capture(force_new=True)
        
        if screenshot_encoded:
            print("Screenshot captured successfully!")
            
            # Ask a question about the screen
            question = input("\nEnter your question: ")
            print(f"\nQuestion: {question}")
            print("-" * 50)
            
            # Get the response from the assistant with the screenshot
            print("Sending question with screenshot to AI...")
            response = await assistant.answer_async(question, screenshot_encoded)
            
            print("\nResponse:")
            print("=" * 50)
            print(response)
            print("=" * 50)
        else:
            print("Failed to capture screenshot.")
    
    elif choice == "3" and automation_options:
        # Automation commands
        print("\n=== QuackQuery Automation ===")
        print("Available automation types:")
        for option in automation_options:
            print(f"- {option}")
        print("Type 'exit' to quit")
        
        while True:
            command = input("\nEnter command: ").strip()
            
            if command.lower() == 'exit':
                break
            
            # Check for file operations
            if file_manager and file_intent_parser:
                try:
                    file_intent = file_intent_parser.parse_intent(command)
                    if file_intent:
                        print(f"Detected file operation: {file_intent['operation']}")
                        result = file_manager.execute_operation(file_intent)
                        print(f"Result: {result}")
                        continue
                except Exception as e:
                    print(f"Error with file operation: {str(e)}")
            
            # Check for GitHub operations
            if github_integration and github_intent_parser:
                try:
                    github_intent = github_intent_parser.parse_intent(command)
                    if github_intent:
                        print(f"Detected GitHub operation: {github_intent['operation']}")
                        result = github_integration.execute_operation(github_intent)
                        print(f"Result: {result}")
                        continue
                except Exception as e:
                    print(f"Error with GitHub operation: {str(e)}")
            
            # Check for app operations
            if app_launcher and app_intent_parser:
                try:
                    app_intent = app_intent_parser.parse_intent(command)
                    if app_intent:
                        print(f"Detected app operation: {app_intent['operation']}")
                        if app_intent['operation'] == 'launch_app':
                            try:
                                app_name = app_intent.get('app_name', '')
                                print(f"Attempting to launch: {app_name}...")
                                result = app_launcher.launch_app(app_name)
                                print(f"✅ Successfully launched: {app_name}")
                            except Exception as launch_error:
                                print(f"❌ Failed to launch application: {str(launch_error)}")
                        elif app_intent['operation'] == 'list_apps':
                            try:
                                print("Retrieving list of installed applications...")
                                apps = app_launcher.list_installed_apps()
                                print("\nInstalled applications:")
                                for app in apps[:20]:  # Show first 20 to avoid flooding console
                                    print(f"- {app}")
                                if len(apps) > 20:
                                    print(f"...and {len(apps) - 20} more")
                            except Exception as list_error:
                                print(f"❌ Failed to list applications: {str(list_error)}")
                        continue
                except Exception as e:
                    print(f"Error with app operation: {str(e)}")
            
            # If no automation intent detected, send to AI assistant
            print("No automation intent detected, sending to AI...")
            response = await assistant.answer_async(command)
            print("\nResponse:")
            print("=" * 50)
            print(response)
            print("=" * 50)
    
    else:
        print("Invalid choice. Exiting.")

if __name__ == "__main__":
    # Run the async main function
    asyncio.run(main())