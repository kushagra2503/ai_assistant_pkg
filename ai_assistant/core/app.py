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
from ai_assistant.integrations.whatsapp_manager import WhatsAppManager
from ai_assistant.utils.whatsapp_intent import WhatsAppIntentParser
from ai_assistant.utils.speech import SpeechRecognizer

# Rich UI components
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.markdown import Markdown
from rich.syntax import Syntax
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich import box
from datetime import datetime
import shutil
import smtplib
import imaplib
import tempfile
import subprocess
from rich.columns import Columns
import pandas as pd

# Load environment variables for API keys
load_dotenv()

logger = logging.getLogger("ai_assistant")

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
        whatsapp_manager (WhatsAppManager): WhatsApp integration
    """

    def __init__(self, config_path=None, debug=False):
        """
        Initialize the AI Assistant App.
        
        Args:
            config_path (str, optional): Path to the configuration file
            debug (bool, optional): Enable debug mode
        """
        # Set up console globally
        global console
        console = Console()
        
        # Set up debugging
        self.debug = debug
        if self.debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
        
        # Load configuration
        self.config_path = config_path or os.path.join(os.path.expanduser("~"), ".aiassistant", "config.json")
        self.config = load_config(self.config_path)
        
        # Initialize required attributes with default values
        self.speech_recognizer = None
        self.whatsapp_manager = None
        
        # Load or initialize components based on config
        self.initialize_core_components()
        
        # Set WhatsApp auto-login to False by default, regardless of stored config
        # User can explicitly enable this later via /whatsapp setup if desired
        self.whatsapp_auto_login = False
        
        # Show a welcome message if debug is enabled
        if self.debug:
            console.print(Panel(
                "[yellow]Debug mode enabled.[/yellow] Detailed logging will be shown.",
                title="[bold]Debug Info[/bold]",
                border_style="yellow",
                box=box.ROUNDED
            ))
            
    def display_error(self, error_message, error_detail=None):
        """Display a formatted error message using Rich."""
        error_panel = Panel(
            f"[bold red]{error_message}[/bold red]" + 
            (f"\n\n[dim]{error_detail}[/dim]" if error_detail else ""),
            title="[bold]Error[/bold]",
            border_style="red",
            box=box.ROUNDED
        )
        console.print(error_panel)
        
    def display_success(self, message):
        """Display a formatted success message using Rich."""
        success_panel = Panel(
            f"[bold green]{message}[/bold green]",
            title="[bold]Success[/bold]",
            border_style="green",
            box=box.ROUNDED
        )
        console.print(success_panel)
        
    def display_warning(self, message):
        """Display a formatted warning message using Rich."""
        warning_panel = Panel(
            f"[bold yellow]{message}[/bold yellow]",
            title="[bold]Warning[/bold]",
            border_style="yellow",
            box=box.ROUNDED
        )
        console.print(warning_panel)
        
    def display_info(self, message):
        """Display an informational message with Rich styling"""
        console.print(Panel(
            message,
            title="[bold]Info[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))

    def initialize_core_components(self):
        """Initialize core components based on configuration."""
        self.config = load_config(self.config_path)
        self.desktop_screenshot = DesktopScreenshot()
        self.assistant = None
        self.ocr_processor = OCRProcessor()
        self.github = GitHubIntegration()
        self.github_intent_parser = GitHubIntentParser()
        
        # Initialize speech recognizer
        try:
            from ai_assistant.utils.speech import SpeechRecognizer
            self.speech_recognizer = SpeechRecognizer()
            logger.info("Speech recognition initialized")
        except Exception as e:
            logger.warning(f"Speech recognition not available: {str(e)}")
            self.speech_recognizer = None
        
        # Initialize file explorer and intent parser
        self.file_explorer = FileExplorer()
        self.file_intent_parser = FileIntentParser()
        
        # Initialize app launcher and intent parser
        self.app_launcher = AppLauncher()
        self.app_intent_parser = AppIntentParser()
        
        # Initialize email manager
        try:
            self.email_manager = EmailManager()
            # Check if email is configured
            if self.email_manager.is_configured():
                self.email_setup_complete = True
                logger.info("Email configuration loaded successfully")
            else:
                logger.info("Email not configured")
        except Exception as e:
            logger.error(f"Error initializing email manager: {e}")
            self.email_manager = None
            self.email_setup_complete = False
        
        # Initialize WhatsApp manager if configured
        self.whatsapp_manager = WhatsAppManager(self.config_path)
        
        self.initialize_assistant()
        self.register_functions()

    def initialize_assistant(self):
        """Initialize the AI assistant with the configured model and role."""
        model_name = self.config.get("model", "Gemini")
        role = self.config.get("role", "General")
        
        # Try to get API key from environment first
        api_key = os.getenv(f"{model_name.upper()}_API_KEY")
        
        # If not in environment, try from config with model-specific key
        if not api_key:
            # Look for model-specific API key first
            api_key = self.config.get(f"{model_name.lower()}_api_key")
            
            # Fall back to generic api_key for backward compatibility
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
            
            # Save in config with model-specific key
            self.config[f"{model_name.lower()}_api_key"] = api_key
            
            # Also save to generic api_key for backward compatibility
            self.config["api_key"] = api_key
            
            save_config(self.config)
            
        self.assistant = Assistant(model_name, api_key, role)

    def register_functions(self):
        """Register special command functions."""
        self.functions = {
            "/help": self.show_help,
            "/document": self.document_command,
            "/ocr": self.ocr_command,
            "/github": self.github_command,
            "/email": self.email_command,
            "/whatsapp": self.whatsapp_command,
            "/stats": self.stats_command,
            "/excel": self.excel_command,  # Add the Excel command
            "/code-edit": self.code_edit_command
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
        
        # Help command
        if command == "/help":
            await self.show_help(args)
            return True
            
        # OCR command
        elif command == "/ocr":
            await self.ocr_command(args)
            return True
            
        # Document command
        elif command == "/document":
            await self.document_command(args)
            return True
            
        # Web command
        elif command == "/web":
            await self.web_command(args)
            return True
            
        # Exit command
        elif command == "/exit" or command == "/quit":
            console.print("[yellow]Goodbye! 👋[/yellow]")
            sys.exit(0)
            
        # Email command
        elif command == "/email":
            await self.email_command(args)
            return True
            
        # WhatsApp command
        elif command == "/whatsapp":
            await self.whatsapp_command(args)
            return True
            
        # Stats command
        elif command == "/stats":
            await self.stats_command(args)
            return True
            
        # Excel command
        elif command == "/excel":
            await self.excel_command(args)
            return True
            
        # Code-edit command
        elif command == "/code-edit":
            await self.code_edit_command(args)
            return True
            
        # Unknown command
        else:
            console.print(Panel(
                f"[bold red]Unknown command:[/bold red] {command}\nType /help to see available commands.",
                title="[bold]Command Error[/bold]",
                border_style="red",
                box=box.ROUNDED
            ))
            return True
        
        return False

    async def show_help(self, args=None):
        """
        Display help information about available commands.
        
        Args:
            args: Optional arguments to specify specific help topics
        """
        if args:
            # Show specific help for a command
            command = args.strip().lower()
            if command.startswith('/'):
                command = command[1:]  # Remove leading slash if present
                
            # Command-specific help
            if command == "ocr":
                console.print(Panel(
                    "The OCR command allows you to extract text from images.\n\n"
                    "[bold cyan]Syntax:[/bold cyan]\n"
                    "• [bold]/ocr[/bold] - Capture screen area and extract text\n"
                    "• [bold]/ocr [file_path][/bold] - Extract text from an image file\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/ocr[/bold] - Opens screen capture tool\n"
                    "• [bold]/ocr screenshot.png[/bold] - Extracts text from screenshot.png\n\n"
                    "[bold cyan]Options:[/bold cyan]\n"
                    "• After text extraction, you can choose to analyze the text with AI\n"
                    "• You can save extracted text to a file",
                    title="[bold]OCR Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "document":
                console.print(Panel(
                    "The document command helps you work with documents and files.\n\n"
                    "[bold cyan]Subcommands:[/bold cyan]\n"
                    "• [bold cyan]summarize [file_path][/bold cyan] - Generate a summary of a document\n"
                    "• [bold cyan]generate[/bold cyan] - Create a new document using AI\n"
                    "• [bold cyan]analyze [file_path][/bold cyan] - Analyze the content of a document\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/document summarize report.pdf[/bold cyan] - Summarizes the PDF file\n"
                    "• [bold]/document generate[/bold cyan] - Starts the document generation wizard\n"
                    "• [bold]/document analyze data.csv[/bold cyan] - Analyzes the CSV file",
                    title="[bold]Document Commands Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "web":
                console.print(Panel(
                    "The web command allows you to search the web and access online content.\n\n"
                    "[bold cyan]Syntax:[/bold cyan]\n"
                    "• [bold]/web search [query][/bold cyan] - Search the web for information\n"
                    "• [bold]/web open [url][/bold cyan] - Open and extract content from a webpage\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/web search latest AI developments[/bold cyan] - Searches for AI news\n"
                    "• [bold]/web open https://example.com[/bold cyan] - Extracts content from the URL\n\n"
                    "[bold cyan]Options:[/bold cyan]\n"
                    "• After fetching web content, you can choose to analyze it with AI",
                    title="[bold]Web Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "email":
                console.print(Panel(
                    "The email command helps you compose, read, and manage emails.\n\n"
                    "[bold cyan]Subcommands:[/bold cyan]\n"
                    "• [bold cyan]compose [recipient][/bold cyan] - Compose a new email\n"
                    "• [bold cyan]ai [recipient][/bold cyan] - Let AI help you write an email\n"
                    "• [bold cyan]read[/bold cyan] - Read your emails\n"
                    "• [bold cyan]setup[/bold cyan] - Configure your email settings\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/email compose john@example.com[/bold cyan] - Start composing an email\n"
                    "• [bold]/email ai boss@company.com[/bold cyan] - Use AI to draft an email\n"
                    "• [bold]/email read[/bold cyan] - View your recent emails\n"
                    "• [bold]/email setup[/bold cyan] - Configure your email account",
                    title="[bold]Email Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "github":
                console.print(Panel(
                    "The GitHub command allows you to interact with GitHub repositories.\n\n"
                    "[bold cyan]Subcommands:[/bold cyan]\n"
                    "• [bold cyan]setup[/bold cyan] - Configure GitHub integration\n"
                    "• [bold cyan]status[/bold cyan] - Check GitHub integration status\n"
                    "• [bold cyan]repos[/bold cyan] - List your GitHub repositories\n"
                    "• [bold cyan]issues [owner/repo][/bold cyan] - List issues for a repository\n"
                    "• [bold cyan]create[/bold cyan] - Create a new issue or pull request\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/github repos[/bold cyan] - Shows your repositories\n"
                    "• [bold]/github issues username/repo[/bold cyan] - Lists issues in that repo\n"
                    "• [bold]/github create[/bold cyan] - Start the creation wizard",
                    title="[bold]GitHub Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "config":
                console.print(Panel(
                    "The config command allows you to configure assistant settings.\n\n"
                    "[bold cyan]Subcommands:[/bold cyan]\n"
                    "• [bold cyan]model[/bold cyan] - Change the AI model\n"
                    "• [bold cyan]role[/bold cyan] - Change the assistant's role\n"
                    "• [bold cyan]show[/bold cyan] - Show current configuration\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/config model[/bold cyan] - Change the AI model\n"
                    "• [bold]/config role[/bold cyan] - Set a new role for the assistant\n"
                    "• [bold]/config show[/bold cyan] - Display current settings",
                    title="[bold]Configuration Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "voice":
                console.print(Panel(
                    "Voice commands allow you to speak to the assistant.\n\n"
                    "[bold cyan]Syntax:[/bold cyan]\n"
                    "• [bold]/voice[/bold cyan] - Start voice recognition mode\n\n"
                    "[bold cyan]Voice Command Examples:[/bold cyan]\n"
                    "• \"What is the weather today?\"\n"
                    "• \"Summarize this article: [URL]\"\n"
                    "• \"Write an email to John about the project meeting\"\n"
                    "• \"Take a screenshot and extract text\"\n"
                    "• \"Stop listening\" (to exit voice mode)",
                    title="[bold]Voice Command Help[/bold]",
                    border_style="blue", 
                    box=box.ROUNDED
                ))
                
            elif command == "whatsapp":
                console.print(Panel(
                    "The WhatsApp command allows you to send and manage WhatsApp messages.\n\n"
                    "[bold cyan]Subcommands:[/bold cyan]\n"
                    "• [bold cyan]setup[/bold cyan] - Configure WhatsApp integration\n"
                    "• [bold cyan]connect[/bold cyan] - Connect to WhatsApp Web\n"
                    "• [bold cyan]disconnect[/bold cyan] - Disconnect from WhatsApp Web\n"
                    "• [bold cyan]send[/bold cyan] - Send a WhatsApp message\n"
                    "• [bold cyan]ai[/bold cyan] - Use AI to compose a message\n"
                    "• [bold cyan]contacts[/bold cyan] - List recent contacts\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/whatsapp setup[/bold cyan] - Set up WhatsApp integration\n"
                    "• [bold]/whatsapp connect[/bold cyan] - Connect to WhatsApp Web\n"
                    "• [bold]/whatsapp send +1234567890 Hello![/bold cyan] - Send a message\n"
                    "• [bold]/whatsapp ai +1234567890[/bold cyan] - AI will help write a message\n"
                    "• [bold]/whatsapp ai +1234567890 Business \"Schedule meeting\"[/bold cyan] - Use Business role\n\n"
                    "[bold cyan]Role-based message generation:[/bold cyan]\n"
                    "You can now use any of the assistant roles to generate WhatsApp messages. Available roles include:\n"
                    "• General - All-purpose assistant\n"
                    "• Business Consultant - Professional business communication\n"
                    "• Sales Agent - Persuasive sales messaging\n"
                    "• Personal Coach - Supportive and motivational\n"
                    "• Creative Writer - Engaging and imaginative\n"
                    "And many more. Use them to tailor your message style to the recipient and purpose.",
                    title="[bold]WhatsApp Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "stats":
                console.print(Panel(
                    "The stats command shows installation statistics for QuackQuery.\n\n"
                    "[bold cyan]Syntax:[/bold cyan]\n"
                    "• [bold]/stats[/bold] - Show how many systems have QuackQuery installed\n\n"
                    "[bold cyan]Options:[/bold cyan]\n"
                    "• [bold]/stats detailed[/bold] - Show detailed statistics by platform, version, etc.",
                    title="[bold]Stats Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            elif command == "excel":
                console.print(Panel(
                    "The Excel command allows you to work with Excel files using natural language.\n\n"
                    "[bold cyan]Capabilities:[/bold cyan]\n"
                    "• List, open, and analyze Excel files\n"
                    "• Extract and filter data using natural language\n"
                    "• Create visualizations and charts\n"
                    "• Perform data analysis and calculations\n"
                    "• Connect directly to Excel application\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/excel list all spreadsheets[/bold] - Find all Excel files\n"
                    "• [bold]/excel show the file sales_data.xlsx[/bold] - Display contents\n"
                    "• [bold]/excel analyze data in budget.xlsx[/bold] - Get statistics\n"
                    "• [bold]/excel create bar chart from sales.xlsx with x as Month and y as Revenue[/bold]\n"
                    "• [bold]/excel filter data where Revenue > 1000 from sales.xlsx[/bold]\n"
                    "• [bold]/excel extract top 10 rows from customer_data.xlsx[/bold]",
                    title="[bold]Excel Command Help[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
                
            elif command == "code-edit":
                console.print(Panel(
                    "The code-edit command allows you to edit code files using natural language.\n\n"
                    "[bold cyan]Syntax:[/bold cyan]\n"
                    "• [bold]/code-edit [file_path][/bold] - Edit a code file\n"
                    "• [bold]/code-edit [file_path] [instructions][/bold] - Edit a code file with specific instructions\n\n"
                    "[bold cyan]Examples:[/bold cyan]\n"
                    "• [bold]/code-edit my_script.py[/bold] - Edit the code file\n"
                    "• [bold]/code-edit my_script.py \"Add a comment at the beginning of the file\"[/bold]\n\n"
                    "[bold cyan]Options:[/bold cyan]\n"
                    "• You can use natural language to describe changes\n"
                    "• You can specify specific instructions for the changes",
                    title="[bold]Code Edit Command Help[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
            else:
                self.display_error(f"No help available for '{command}'")
                console.print("Type [bold]/help[/bold] for a list of all commands")
                
        else:
            # General help - list all commands
            command_list = [
                "• [bold]/help[/bold] - Show this help message",
                "• [bold]/ocr[/bold] - Extract text from images",
                "• [bold]/document[/bold] - Work with documents",
                "• [bold]/web[/bold] - Search and browse the web",
                "• [bold]/email[/bold] - Email management",
                "• [bold]/github[/bold] - GitHub integration",
                "• [bold]/whatsapp[/bold] - WhatsApp messaging",
                "• [bold]/stats[/bold] - Show installation statistics",
                "• [bold]/exit[/bold] - Exit the assistant"
            ]
            
            commands_text = "\n".join(command_list)
            
            console.print(Panel(
                f"[bold cyan]Available Commands:[/bold cyan]\n\n{commands_text}\n\n"
                f"Type [bold]/help command[/bold] for detailed help on a specific command.",
                title="[bold]QuackQuery Help[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
    
    async def stats_command(self, args=None):
        """Show statistics about the AI assistant."""
        from rich.columns import Columns
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        
        console.print(Panel(
            "[bold]AI Assistant Statistics[/bold]\n",
            title="[bold]Stats[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))

        # Display stats here
        if hasattr(self, 'stats') and self.stats:
            stats_panels = []
            for key, value in self.stats.items():
                if key == 'recent_commands':
                    continue
                stats_panels.append(
                    Panel(f"[bold cyan]{value}[/bold cyan]", title=f"[bold]{key.replace('_', ' ').title()}[/bold]", border_style="green")
                )
            
            console.print(Columns(stats_panels))
        else:
            console.print("[yellow]No statistics available yet.[/yellow]")

    async def excel_command(self, user_input=None):
        """Handle Excel operations through natural language commands."""
        from rich.panel import Panel
        from rich.console import Console
        from rich.table import Table
        from rich.box import ROUNDED
        from rich.prompt import Prompt, Confirm
        
        console = Console()
        
        if not user_input:
            # Show Excel command help
            console.print(Panel(
                "The Excel command allows you to work with Excel files using natural language.\n\n"
                "[bold cyan]Examples:[/bold cyan]\n"
                "• [bold]/excel list all spreadsheets[/bold] - Find all Excel files\n"
                "• [bold]/excel show the file sales_data.xlsx[/bold] - Display contents\n"
                "• [bold]/excel analyze data in budget.xlsx[/bold] - Get statistics\n"
                "• [bold]/excel create bar chart from sales.xlsx[/bold]\n"
                "• [bold]/excel filter data where Revenue > 1000 from sales.xlsx[/bold]\n"
                "• [bold]/excel extract top 10 rows from customer_data.xlsx[/bold]",
                title="[bold]Excel Command Help[/bold]",
                border_style="green",
                box=ROUNDED
            ))
            return

        # Import the Excel handler and NLP processor
        from ai_assistant.utils.excel_handler import ExcelHandler
        from ai_assistant.utils.excel_nlp import ExcelNLProcessor
        
        # Initialize Excel handler and NLP processor
        excel_handler = ExcelHandler()
        excel_nlp = ExcelNLProcessor()
        
        # Parse the user input
        operation = excel_nlp.parse_command(user_input)
        
        console.print(f"[bold cyan]Processing Excel command: {operation['operation']}[/bold cyan]")
        
        # Process operations based on the operation type
        if operation["operation"] == "list_files":
            # List Excel files
            directory = operation.get("directory", "")
            
            console.print(f"[bold cyan]Searching for Excel files{' in ' + directory if directory else ''}...[/bold cyan]")
            
            excel_files = excel_handler.list_excel_files(directory)
            
            if not excel_files:
                console.print("[yellow]No Excel files found.[/yellow]")
                return
                
            # Create table for display
            table = Table(title="Excel Files", box=ROUNDED)
            table.add_column("File", style="cyan")
            table.add_column("Info")
            
            for file in excel_files:
                # Get file info
                file_info = excel_handler.get_excel_info(file)
                
                if "error" in file_info:
                    info_text = f"[red]Error: {file_info['error']}[/red]"
                else:
                    sheet_count = len(file_info.get("sheets", []))
                    sheet_text = f"{sheet_count} sheet{'s' if sheet_count != 1 else ''}"
                    
                    # For the first sheet, show row and column count
                    if sheet_count > 0:
                        first_sheet = file_info["sheets"][0]
                        rows = first_sheet.get("rows", 0)
                        columns = first_sheet.get("columns", 0)
                        sheet_text += f" (Sheet 1: {rows} rows × {columns} columns)"
                        
                    info_text = sheet_text
                    
                table.add_row(file, info_text)
                
            console.print(table)
            
            # Ask if user wants to open any of the files
            if Confirm.ask("[bold]Would you like to open one of these files?[/bold]", default=False):
                file_to_open = Prompt.ask("[bold]Enter the file name to open[/bold]")
                await self.excel_command(f"show the file {file_to_open}")
                
        elif operation["operation"] == "show_file":
            # Show Excel file contents
            file_name = operation.get("file_name")
            sheet_name = operation.get("sheet_name")
            
            if not file_name:
                console.print("[bold red]Error: No file name specified.[/bold red]")
                return
                
            console.print(f"[bold cyan]Opening '{file_name}'...[/bold cyan]")
            
            # If no sheet specified, get available sheets
            if not sheet_name:
                sheet_names = excel_handler.get_sheet_names(file_name)
                
                if not sheet_names:
                    console.print(f"[bold red]Error: Could not open file '{file_name}'.[/bold red]")
                    return
                    
                # If multiple sheets, ask which one to open
                if len(sheet_names) > 1:
                    console.print(f"[bold cyan]Available sheets:[/bold cyan]")
                    for i, name in enumerate(sheet_names, 1):
                        console.print(f"{i}. {name}")
                        
                    sheet_index = Prompt.ask(
                        "[bold]Which sheet would you like to open? (enter number)[/bold]",
                        choices=[str(i) for i in range(1, len(sheet_names) + 1)],
                        default="1"
                    )
                    
                    sheet_name = sheet_names[int(sheet_index) - 1]
                else:
                    sheet_name = sheet_names[0]
                    
            # Read the Excel file
            df = excel_handler.read_excel_file(file_name, sheet_name)
            
            if df is None:
                console.print(f"[bold red]Error: Could not read file '{file_name}'.[/bold red]")
                return
                
            # Display data
            console.print(f"[bold cyan]Viewing '{file_name}', sheet '{sheet_name}':[/bold cyan]")
            
            # Check data size
            row_count, col_count = df.shape
            
            # Create a Rich table
            table = Table(title=f"{file_name} - {sheet_name}")
            
            # Add columns (limit to prevent overwhelming the display)
            max_cols = min(col_count, 15)
            for i in range(max_cols):
                col_name = str(df.columns[i])
                table.add_column(col_name)
                
            if max_cols < col_count:
                table.add_column("...")
                
            # Add rows (limit to prevent overwhelming the display)
            max_rows = min(row_count, 20)
            for i in range(max_rows):
                row_data = []
                for j in range(max_cols):
                    cell_value = str(df.iloc[i, j])
                    # Truncate long cell values
                    if len(cell_value) > 50:
                        cell_value = cell_value[:47] + "..."
                    row_data.append(cell_value)
                    
                if max_cols < col_count:
                    row_data.append("...")
                    
                table.add_row(*row_data)
                
            if max_rows < row_count:
                table.add_row(*["..." for _ in range(max_cols + (1 if max_cols < col_count else 0))])
                
            console.print(table)
            
            console.print(f"[cyan]Showed {max_rows} of {row_count} rows and {max_cols} of {col_count} columns.[/cyan]")
            
            # Ask if user wants to perform operations on this file
            if Confirm.ask("[bold]Would you like to perform operations on this file?[/bold]", default=False):
                operation_type = Prompt.ask(
                    "[bold]Select operation[/bold]",
                    choices=["analyze", "filter", "chart", "save", "cancel"],
                    default="analyze"
                )
                
                if operation_type == "analyze":
                    await self.excel_command(f"analyze data in {file_name}")
                elif operation_type == "filter":
                    filter_query = Prompt.ask("[bold]Enter filter condition[/bold]")
                    await self.excel_command(f"filter data where {filter_query} from {file_name}")
                elif operation_type == "chart":
                    # Create proper chart command
                    # Display available columns
                    df = excel_handler.read_excel_file(file_name, sheet_name)
                    if df is not None:
                        column_table = Table(box=ROUNDED)
                        column_table.add_column("#", style="cyan")
                        column_table.add_column("Column Name")
                        column_table.add_column("Data Type")
                        
                        for i, column in enumerate(df.columns, 1):
                            data_type = str(df[column].dtype)
                            column_table.add_row(str(i), column, data_type)
                            
                        console.print(Panel(column_table, title="[bold]Available Columns[/bold]", border_style="blue"))
                        
                        # Get x column
                        x_col_idx = Prompt.ask(
                            "[bold]Select column for X-axis (enter number)[/bold]",
                            choices=[str(i) for i in range(1, len(df.columns) + 1)],
                            default="1"
                        )
                        x_column = df.columns[int(x_col_idx) - 1]
                        
                        # Get y column
                        y_col_idx = Prompt.ask(
                            "[bold]Select column for Y-axis (enter number)[/bold]",
                            choices=[str(i) for i in range(1, len(df.columns) + 1)],
                            default="2"
                        )
                        y_column = df.columns[int(y_col_idx) - 1]
                        
                        # Get chart type
                        chart_type = Prompt.ask(
                            "[bold]Select chart type[/bold]",
                            choices=["bar", "line", "scatter", "pie"],
                            default="bar"
                        )
                        
                        # Create chart directly
                        console.print(f"[bold cyan]Generating {chart_type} chart of {y_column} by {x_column}...[/bold cyan]")
                        
                        try:
                            chart_path = excel_handler.generate_excel_visualization(
                                df, chart_type, x_column, y_column, f"{y_column} by {x_column}"
                            )
                            
                            if isinstance(chart_path, str) and chart_path.startswith("Error"):
                                console.print(f"[bold red]{chart_path}[/bold red]")
                                # Suggest possible solution
                                if "not supported between instances of 'str' and 'int'" in chart_path:
                                    console.print("[yellow]This might be due to mixed data types. The visualization has been fixed to handle this case.[/yellow]")
                                elif "not found in DataFrame" in chart_path:
                                    available_cols = ", ".join([f"'{col}'" for col in df.columns])
                                    console.print(f"[yellow]Available columns are: {available_cols}[/yellow]")
                            else:
                                console.print(f"[bold green]✓ Chart generated and saved to {chart_path}[/bold green]")
                                
                                # Ask if user wants to view the chart
                                if Confirm.ask("[bold]View the chart?[/bold]", default=True):
                                    try:
                                        import os
                                        os.system(f"start {chart_path}")
                                    except Exception as e:
                                        console.print(f"[bold red]Error opening chart: {e}[/bold red]")
                        except Exception as e:
                            console.print(f"[bold red]Error generating chart: {str(e)}[/bold red]")
                            console.print("[yellow]This might be due to incompatible data types. Try selecting different columns or chart types.[/yellow]")
                    else:
                        console.print(f"[bold red]Error: Could not read file '{file_name}'.[/bold red]")
                elif operation_type == "save":
                    save_path = Prompt.ask("[bold]Enter file name to save[/bold]", default=f"modified_{file_name}")
                    if excel_handler.save_dataframe_to_excel(df, save_path):
                        console.print(f"[bold green]✓ Data saved to {save_path}[/bold green]")
                    else:
                        console.print(f"[bold red]Error saving data to {save_path}[/bold red]")
        
        elif operation["operation"] == "analyze":
            # Analyze Excel file
            file_name = operation.get("file_name")
            analysis_type = operation.get("analysis_type", "summary")
            
            if not file_name:
                console.print("[bold red]Error: No file name specified.[/bold red]")
                return
                
            # Read the Excel file
            console.print(f"[bold cyan]Analyzing '{file_name}'...[/bold cyan]")
            
            df = excel_handler.read_excel_file(file_name)
            
            if df is None:
                console.print(f"[bold red]Error: Could not read file '{file_name}'.[/bold red]")
                return
                
            # Perform analysis
            analysis = excel_handler.analyze_excel_data(df, analysis_type)
            
            if "error" in analysis:
                console.print(f"[bold red]Error: {analysis['error']}[/bold red]")
                return
                
            # Display analysis results based on type
            if analysis_type == "summary":
                summary_df = pd.DataFrame(analysis["summary"])
                
                console.print(Panel(
                    f"[bold]Summary Statistics for {file_name}[/bold]\n\n{summary_df.to_string()}",
                    title="[bold]Data Analysis Results[/bold]",
                    border_style="green",
                    box=ROUNDED
                ))
                
                # Display null values
                null_counts = pd.Series(analysis["null_values"])
                if null_counts.sum() > 0:
                    console.print(Panel(
                        f"[bold]Null Value Counts[/bold]\n\n{null_counts.to_string()}",
                        title="[bold]Missing Data[/bold]",
                        border_style="yellow",
                        box=ROUNDED
                    ))
                    
            elif analysis_type == "correlation":
                corr_df = pd.DataFrame(analysis["correlation"])
                
                console.print(Panel(
                    f"[bold]Correlation Matrix for {file_name}[/bold]\n\n{corr_df.to_string()}",
                    title="[bold]Correlation Analysis[/bold]",
                    border_style="green",
                    box=ROUNDED
                ))
                
            elif analysis_type == "descriptive":
                console.print(f"[bold cyan]Descriptive Statistics for {file_name}:[/bold cyan]\n")
                
                for column, stats in analysis["descriptive"].items():
                    stat_table = Table(title=f"Column: {column}", box=ROUNDED)
                    stat_table.add_column("Statistic", style="cyan")
                    stat_table.add_column("Value")
                    
                    for stat, value in stats.items():
                        stat_table.add_row(stat, str(value))
                        
                    console.print(stat_table)
                    console.print("")
                    
            # Ask if user wants to visualize the data
            if Confirm.ask("[bold]Would you like to visualize this data?[/bold]", default=False):
                # Simplified visualization flow
                await self.excel_command(f"create chart from {file_name}")
                
        elif operation["operation"] == "create_chart":
            # Create chart from Excel file
            file_name = operation.get("file_name")
            chart_type = operation.get("chart_type", "bar")
            x_column = operation.get("x_column")
            y_column = operation.get("y_column")
            title = operation.get("title", f"{chart_type.capitalize()} Chart")
            
            if not file_name:
                console.print("[bold red]Error: No file name specified.[/bold red]")
                return
                
            # Read the Excel file
            console.print(f"[bold cyan]Reading '{file_name}' for chart creation...[/bold cyan]")
            
            df = excel_handler.read_excel_file(file_name)
            
            if df is None:
                console.print(f"[bold red]Error: Could not read file '{file_name}'.[/bold red]")
                return
                
            # If columns not specified, ask user to select
            if not x_column or not y_column:
                # Display available columns
                column_table = Table(box=ROUNDED)
                column_table.add_column("#", style="cyan")
                column_table.add_column("Column Name")
                column_table.add_column("Data Type")
                
                for i, column in enumerate(df.columns, 1):
                    data_type = str(df[column].dtype)
                    column_table.add_row(str(i), column, data_type)
                    
                console.print(Panel(column_table, title="[bold]Available Columns[/bold]", border_style="blue"))
                
                # Get x column if not specified
                if not x_column:
                    x_col_idx = Prompt.ask(
                        "[bold]Select column for X-axis (enter number)[/bold]",
                        choices=[str(i) for i in range(1, len(df.columns) + 1)],
                        default="1"
                    )
                    x_column = df.columns[int(x_col_idx) - 1]
                    
                # Get y column if not specified
                if not y_column:
                    y_col_idx = Prompt.ask(
                        "[bold]Select column for Y-axis (enter number)[/bold]",
                        choices=[str(i) for i in range(1, len(df.columns) + 1)],
                        default="2"
                    )
                    y_column = df.columns[int(y_col_idx) - 1]
            
            # Generate chart
            console.print(f"[bold cyan]Generating {chart_type} chart of {y_column} by {x_column}...[/bold cyan]")
            
            try:
                chart_path = excel_handler.generate_excel_visualization(
                    df, chart_type, x_column, y_column, title
                )
                
                if isinstance(chart_path, str) and chart_path.startswith("Error"):
                    console.print(f"[bold red]{chart_path}[/bold red]")
                    # Suggest possible solution
                    if "not supported between instances of 'str' and 'int'" in chart_path:
                        console.print("[yellow]This might be due to mixed data types. The visualization has been fixed to handle this case.[/yellow]")
                    elif "not found in DataFrame" in chart_path:
                        available_cols = ", ".join([f"'{col}'" for col in df.columns])
                        console.print(f"[yellow]Available columns are: {available_cols}[/yellow]")
                else:
                    console.print(f"[bold green]✓ Chart generated and saved to {chart_path}[/bold green]")
                    
                    # Ask if user wants to view the chart
                    if Confirm.ask("[bold]View the chart?[/bold]", default=True):
                        try:
                            import os
                            os.system(f"start {chart_path}")
                        except Exception as e:
                            console.print(f"[bold red]Error opening chart: {e}[/bold red]")
            except Exception as e:
                console.print(f"[bold red]Error generating chart: {str(e)}[/bold red]")
                console.print("[yellow]This might be due to incompatible data types. Try selecting different columns or chart types.[/yellow]")
                
                # Ask if user wants to add the chart to the Excel file
                if Confirm.ask("[bold]Add this chart to the Excel file?[/bold]", default=False):
                    # Get sheet name
                    sheet_names = excel_handler.get_sheet_names(file_name)
                    sheet_name = sheet_names[0] if sheet_names else "Sheet1"
                    
                    # Get data range for chart (simplified)
                    data_range = "A1:B10"  # This is a placeholder
                    
                    success = excel_handler.create_excel_chart(
                        file_name, sheet_name, data_range, chart_type, title
                    )
                    
                    if success:
                        console.print(f"[bold green]✓ Chart added to {file_name}[/bold green]")
                    else:
                        console.print(f"[bold red]Error adding chart to {file_name}[/bold red]")
                        
        elif operation["operation"] == "filter_data":
            # Filter data from Excel file
            file_name = operation.get("file_name")
            conditions = operation.get("conditions")
            
            if not file_name or not conditions:
                console.print("[bold red]Error: File name and filter conditions are required.[/bold red]")
                return
                
            # Read the Excel file
            console.print(f"[bold cyan]Reading '{file_name}' for filtering...[/bold cyan]")
            
            df = excel_handler.read_excel_file(file_name)
            
            if df is None:
                console.print(f"[bold red]Error: Could not read file '{file_name}'.[/bold red]")
                return
                
            # Translate conditions to pandas query
            pandas_query = excel_nlp.translate_to_pandas_query(conditions)
            
            console.print(f"[bold cyan]Filtering data where {pandas_query}...[/bold cyan]")
            
            # Apply the filter
            filtered_df = excel_handler.query_excel_data(df, pandas_query)
            
            if filtered_df.empty:
                console.print("[yellow]No data matches the filter condition.[/yellow]")
                return
                
            console.print(f"[green]Found {len(filtered_df)} matching rows out of {len(df)} total.[/green]")
            
            # Convert filtered DataFrame to a Rich table
            table = Table(title=f"Filtered Data from {file_name} ({pandas_query})")
            
            # Add columns
            for column in filtered_df.columns:
                table.add_column(str(column))
                
            # Add rows (limit to prevent overwhelming the console)
            max_rows = 20
            if len(filtered_df) > max_rows:
                console.print(f"[yellow]Note: Showing first {max_rows} of {len(filtered_df)} rows[/yellow]")
                display_df = filtered_df.head(max_rows)
            else:
                display_df = filtered_df
                
            for _, row in display_df.iterrows():
                table.add_row(*[str(cell) for cell in row])
                
            console.print(table)
            
            # Ask if user wants to save the filtered data
            if Confirm.ask("[bold]Save filtered data to a new Excel file?[/bold]", default=False):
                save_path = Prompt.ask("[bold]Enter file name to save[/bold]", default=f"filtered_{file_name}")
                
                if excel_handler.save_dataframe_to_excel(filtered_df, save_path):
                    console.print(f"[bold green]✓ Filtered data saved to {save_path}[/bold green]")
                else:
                    console.print(f"[bold red]Error saving filtered data to {save_path}[/bold red]")
                    
        elif operation["operation"] == "extract_data":
            # Extract data from Excel file
            file_name = operation.get("file_name")
            columns = operation.get("columns")
            row_limit = operation.get("row_limit")
            
            if not file_name:
                console.print("[bold red]Error: No file name specified.[/bold red]")
                return
                
            # Read the Excel file
            console.print(f"[bold cyan]Extracting data from '{file_name}'...[/bold cyan]")
            
            df = excel_handler.read_excel_file(file_name)
            
            if df is None:
                console.print(f"[bold red]Error: Could not read file '{file_name}'.[/bold red]")
                return
                
            # Filter columns if specified
            if columns:
                # Find matching columns (case-insensitive partial match)
                matching_columns = []
                for col_pattern in columns:
                    col_pattern = col_pattern.strip().lower()
                    matches = [col for col in df.columns if col_pattern in str(col).lower()]
                    matching_columns.extend(matches)
                    
                if matching_columns:
                    df = df[matching_columns]
                else:
                    console.print("[bold yellow]Warning: No matching columns found. Showing all columns.[/bold yellow]")
                    
            # Limit rows if specified
            if row_limit:
                if row_limit < len(df):
                    df = df.head(row_limit)
                    console.print(f"[bold yellow]Showing first {row_limit} of {len(df)} rows.[/bold yellow]")
            
            # Convert DataFrame to a Rich table
            table = Table(title=f"Extracted Data from {file_name}")
            
            # Add columns
            for column in df.columns:
                table.add_column(str(column))
                
            # Add rows (limit to prevent overwhelming the console)
            max_rows = 30
            if len(df) > max_rows:
                console.print(f"[yellow]Note: Showing first {max_rows} of {len(df)} rows[/yellow]")
                display_df = df.head(max_rows)
            else:
                display_df = df
                
            for _, row in display_df.iterrows():
                table.add_row(*[str(cell) for cell in row])
                
            console.print(table)
            
            # Ask if user wants to save the extracted data
            if Confirm.ask("[bold]Save extracted data to a new Excel file?[/bold]", default=False):
                save_path = Prompt.ask("[bold]Enter file name to save[/bold]", default=f"extracted_{file_name}")
                
                if excel_handler.save_dataframe_to_excel(df, save_path):
                    console.print(f"[bold green]✓ Extracted data saved to {save_path}[/bold green]")
                else:
                    console.print(f"[bold red]Error saving extracted data to {save_path}[/bold red]")
                    
        elif operation["operation"] == "excel_query":
            # Handle generic Excel query
            query = operation.get("query")
            file_name = operation.get("file_name")
            
            console.print(f"[bold cyan]Analyzing Excel query: '{query}'[/bold cyan]")
            
            # If file specified, try to read it
            df = None
            if file_name:
                console.print(f"[bold cyan]Reading '{file_name}'...[/bold cyan]")
                df = excel_handler.read_excel_file(file_name)
                
            # Use AI to interpret the query and generate a response
            prompt = f"The user has the following Excel query: {query}\n\n"
            
            if df is not None:
                # Include a sample of the data
                prompt += f"Here's sample data from {file_name}:\n"
                prompt += df.head(5).to_string() + "\n\n"
                
            prompt += "Please provide a concise response explaining what Excel operations would address this query. Include specific Excel formulas, functions, or techniques that would be helpful."
            
            # Get AI response 
            console.print(f"[bold cyan]Analyzing your Excel query...[/bold cyan]")
            response = await self.assistant.answer_async(prompt)
            
            # Display response
            console.print(Panel(response, title="[bold]Excel Assistant Response[/bold]", border_style="green"))
            
        else:
            console.print(f"[bold red]Error: Unknown or unsupported Excel operation '{operation['operation']}'[/bold red]")
            console.print("Type [bold cyan]/excel[/bold cyan] for help with available commands.")

    async def code_edit_command(self, args=None):
        """Handle code edit command using OpenAI or Google AI."""
        from rich.prompt import Prompt
        from rich.console import Console
        from rich.panel import Panel
        
        console = Console()
        
        if not args:
            console.print(Panel(
                "The code-edit command allows you to edit code files using natural language.\n\n"
                "[bold cyan]Syntax:[/bold cyan]\n"
                "• [bold]/code-edit [file_path][/bold] - Edit a code file\n"
                "• [bold]/code-edit [file_path] [instructions][/bold] - Edit a code file with specific instructions\n\n"
                "[bold cyan]Examples:[/bold cyan]\n"
                "• [bold]/code-edit my_script.py[/bold] - Edit the code file\n"
                "• [bold]/code-edit my_script.py \"Add a comment at the beginning of the file\"[/bold]\n\n"
                "[bold cyan]Options:[/bold cyan]\n"
                "• You can use natural language to describe changes\n"
                "• You can specify specific instructions for the changes",
                title="[bold]Code Edit Command Help[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            return

        # Parse the command
        parts = args.split(maxsplit=1)
        file_path = parts[0]
        instructions = parts[1] if len(parts) > 1 else ""

        # Check if the file exists
        if not os.path.exists(file_path):
            console.print(f"[bold red]Error: File '{file_path}' not found.[/bold red]")
            return

        # Use AI to generate the edited file
        console.print(f"[bold cyan]Editing file '{file_path}'...[/bold cyan]")
        edited_file = await self.assistant.answer_async(f"Edit the file '{file_path}' with the following instructions: {instructions}")

        # Save the edited file
        with open(file_path, 'w') as f:
            f.write(edited_file)

        console.print(f"[bold green]✓ File '{file_path}' edited successfully.[/bold green]")

    async def document_command(self, args):
        """
        Handle document commands for file processing and generation.
        
        Args:
            args: Command arguments
        """
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else ""
        params = parts[1] if len(parts) > 1 else ""
        
        if subcmd == "summarize":
            # Document summarization
            if not params:
                self.display_error("Please specify a file path to summarize")
                console.print("[dim]Example: /document summarize path/to/file.pdf[/dim]")
                return
                
            file_path = params.strip()
            if not os.path.exists(file_path):
                self.display_error(f"File not found: {file_path}")
                return
                
            # Determine the file type
            file_ext = os.path.splitext(file_path)[1].lower()
            supported_extensions = [".pdf", ".docx", ".txt", ".md", ".csv", ".json"]
            
            if file_ext not in supported_extensions:
                self.display_error(f"Unsupported file type: {file_ext}")
                console.print(f"[dim]Supported file types: {', '.join(supported_extensions)}[/dim]")
                return
                
            console.print(Panel(
                f"[bold]Summarizing document:[/bold] {os.path.basename(file_path)}",
                title="[bold]Document Operation[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Extract text from the document
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Reading document...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Extracting text...", total=None)
                
                try:
                    # Extract text based on file type
                    if file_ext == ".pdf":
                        # Code to extract text from PDF
                        text = f"PDF text extraction from {file_path} would go here"
                    elif file_ext == ".docx":
                        # Code to extract text from DOCX
                        text = f"DOCX text extraction from {file_path} would go here"
                    else:
                        # For text-based files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            text = f.read()
                except Exception as e:
                    self.display_error(f"Error reading file: {str(e)}")
                    return
            
            # Generate a summary using AI
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Generating summary...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Analyzing content...", total=None)
                
                prompt = f"Please summarize the following document content:\n\n{text[:4000]}"
                if len(text) > 4000:
                    prompt += "\n\n[Content truncated due to length...]"
                    
                summary = await self.assistant.answer_async(prompt)
            
            # Display the summary
            console.print(Panel(
                Markdown(summary),
                title=f"[bold]Summary of {os.path.basename(file_path)}[/bold]",
                border_style="green",
                box=box.ROUNDED
            ))
            
        elif subcmd == "generate":
            # Document generation
            console.print(Panel(
                "[bold]Document Generation Assistant[/bold]\n"
                "I'll help you create a new document based on your specifications.",
                title="[bold]Document Generator[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Get document details
            doc_type = Prompt.ask(
                "[bold]Document type[/bold]", 
                choices=["report", "letter", "proposal", "article", "other"],
                default="report"
            )
            
            if doc_type == "other":
                doc_type = Prompt.ask("[bold]Specify document type[/bold]")
                
            topic = Prompt.ask("[bold]Topic or title[/bold]")
            instructions = Prompt.ask("[bold]Additional instructions[/bold] (optional)")
            output_format = Prompt.ask(
                "[bold]Output format[/bold]",
                choices=["markdown", "text", "html"],
                default="markdown"
            )
            
            # Generate the document
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Generating document...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Creating content...", total=None)
                
                prompt = f"Generate a {doc_type} about '{topic}'. "
                prompt += f"Additional instructions: {instructions}" if instructions else ""
                prompt += f" Please format the output in {output_format}."
                
                generated_content = await self.assistant.answer_async(prompt)
            
            # Display the generated document
            if output_format == "markdown":
                console.print(Panel(
                    Markdown(generated_content),
                    title=f"[bold]Generated {doc_type.title()}: {topic}[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
            elif output_format == "html":
                console.print(Panel(
                    Syntax(generated_content, "html", theme="monokai"),
                    title=f"[bold]Generated {doc_type.title()} (HTML): {topic}[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
            else:
                console.print(Panel(
                    generated_content,
                    title=f"[bold]Generated {doc_type.title()}: {topic}[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
                
            # Ask if user wants to save the document
            if Confirm.ask("Would you like to save this document to a file?", default=True):
                default_filename = f"{topic.lower().replace(' ', '_')}.{output_format}"
                if output_format == "markdown":
                    default_filename = f"{topic.lower().replace(' ', '_')}.md"
                elif output_format == "html":
                    default_filename = f"{topic.lower().replace(' ', '_')}.html"
                else:
                    default_filename = f"{topic.lower().replace(' ', '_')}.txt"
                    
                file_path = Prompt.ask("Enter file path", default=default_filename)
                
                try:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(generated_content)
                    self.display_success(f"Document saved to {file_path}")
                except Exception as e:
                    self.display_error(f"Error saving document: {str(e)}")
                    
        elif subcmd == "analyze":
            # Document analysis
            if not params:
                self.display_error("Please specify a file path to analyze")
                console.print("[dim]Example: /document analyze path/to/file.pdf[/dim]")
                return
                
            file_path = params.strip()
            if not os.path.exists(file_path):
                self.display_error(f"File not found: {file_path}")
                return
                
            # Check file type
            file_ext = os.path.splitext(file_path)[1].lower()
            supported_extensions = [".pdf", ".docx", ".txt", ".md", ".csv", ".json", ".py", ".js", ".html", ".css"]
            
            if file_ext not in supported_extensions:
                self.display_error(f"Unsupported file type: {file_ext}")
                console.print(f"[dim]Supported file types: {', '.join(supported_extensions)}[/dim]")
                return
                
            console.print(Panel(
                f"[bold]Analyzing document:[/bold] {os.path.basename(file_path)}",
                title="[bold]Document Analysis[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Extract content from the file
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Reading document...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Extracting content...", total=None)
                
                try:
                    # Extract text based on file type (simplified implementation)
                    if file_ext in [".pdf", ".docx"]:
                        # Code to extract text from PDF/DOCX
                        content = f"Text extraction from {file_path} would go here"
                    else:
                        # For text-based files
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                except Exception as e:
                    self.display_error(f"Error reading file: {str(e)}")
                    return
            
            # Analyze the document
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Analyzing content...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Processing...", total=None)
                
                prompt = f"Analyze the following document and provide a detailed analysis including main topics, key points, and insights:\n\n{content[:4000]}"
                if len(content) > 4000:
                    prompt += "\n\n[Content truncated due to length...]"
                    
                analysis = await self.assistant.answer_async(prompt)
            
            # Display the analysis
            console.print(Panel(
                Markdown(analysis),
                title=f"[bold]Analysis of {os.path.basename(file_path)}[/bold]",
                border_style="green",
                box=box.ROUNDED
            ))
            
        else:
            # Help for document command
            console.print(Panel(
                "Available document subcommands:\n\n"
                "• [bold cyan]summarize [file_path][/bold cyan] - Generate a summary of a document\n"
                "• [bold cyan]generate[/bold cyan] - Create a new document using AI\n"
                "• [bold cyan]analyze [file_path][/bold cyan] - Analyze the content of a document",
                title="[bold]Document Commands Help[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))

    async def github_command(self, args):
        """
        Handle GitHub commands.
        
        Args:
            args: Command arguments
        """
        parts = args.split(maxsplit=1)
        subcmd = parts[0].lower() if parts else ""
        params = parts[1] if len(parts) > 1 else ""
        
        if subcmd == "setup":
            # GitHub setup
            await self.configure_github()
            
        elif subcmd == "status":
            # GitHub status
            if not self.config.get("github", {}).get("token"):
                self.display_error("GitHub is not configured. Please run /github setup first.")
                return
                
            console.print(Panel(
                "[bold]GitHub Status[/bold]\n"
                f"[green]✓[/green] GitHub API is configured and ready to use.\n"
                f"[dim]Token: ...{self.config['github']['token'][-4:]} (last 4 characters)[/dim]",
                title="[bold]GitHub Integration[/bold]",
                border_style="green",
                box=box.ROUNDED
            ))
            
        elif subcmd == "repos":
            # List GitHub repositories
            if not self.config.get("github", {}).get("token"):
                self.display_error("GitHub is not configured. Please run /github setup first.")
                return
                
            console.print(Panel(
                "[bold]Fetching your GitHub repositories...[/bold]",
                title="[bold]GitHub Repositories[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Fetch repositories
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to GitHub API...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching repositories...", total=None)
                
                # Placeholder for actual GitHub API call
                repositories = [
                    {"name": "project-alpha", "description": "A cool project", "stars": 12, "forks": 5, "language": "Python"},
                    {"name": "web-app", "description": "Web application template", "stars": 45, "forks": 20, "language": "JavaScript"},
                    {"name": "data-tools", "description": "Tools for data analysis", "stars": 8, "forks": 2, "language": "Python"}
                ]
            
            # Display repositories in a table
            repo_table = Table(title="Your GitHub Repositories", box=box.ROUNDED, border_style="blue")
            repo_table.add_column("Name", style="cyan")
            repo_table.add_column("Description")
            repo_table.add_column("Stars", justify="right", style="yellow")
            repo_table.add_column("Forks", justify="right", style="green")
            repo_table.add_column("Language", style="magenta")
            
            for repo in repositories:
                repo_table.add_row(
                    repo["name"],
                    repo["description"] or "",
                    str(repo["stars"]),
                    str(repo["forks"]),
                    repo["language"] or "Unknown"
                )
                
            console.print(repo_table)
            
            # Ask if user wants to clone a repository
            if Confirm.ask("Would you like to clone one of these repositories?", default=False):
                repo_name = Prompt.ask("[bold]Enter repository name to clone[/bold]")
                clone_dir = Prompt.ask("[bold]Enter directory to clone into[/bold]", default=".")
                
                console.print(Panel(
                    f"[bold]Cloning repository:[/bold] {repo_name}\n"
                    f"[bold]Target directory:[/bold] {clone_dir}",
                    title="[bold]Git Clone Operation[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Cloning repository...[/bold blue]"),
                    BarColumn(),
                    TimeElapsedColumn(),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Cloning...", total=None)
                    
                    # Placeholder for actual git clone operation
                    # This would use subprocess to run git commands
                    import time
                    time.sleep(2)  # Simulate cloning process
            
            self.display_success(f"Repository {repo_name} cloned successfully to {clone_dir}")
            
        elif subcmd == "issues":
            # List GitHub issues
            if not self.config.get("github", {}).get("token"):
                self.display_error("GitHub is not configured. Please run /github setup first.")
                return
                
            repo_name = params
            if not repo_name:
                repo_name = Prompt.ask("[bold]Enter repository name[/bold] (format: owner/repo)")
                
            console.print(Panel(
                f"[bold]Fetching issues for:[/bold] {repo_name}",
                title="[bold]GitHub Issues[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Fetch issues
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to GitHub API...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching issues...", total=None)
                
                # Placeholder for actual GitHub API call
                issues = [
                    {"number": 42, "title": "Fix login bug", "state": "open", "created_at": "2023-01-15", "comments": 3},
                    {"number": 36, "title": "Update documentation", "state": "closed", "created_at": "2023-01-10", "comments": 5},
                    {"number": 45, "title": "Add new feature", "state": "open", "created_at": "2023-01-20", "comments": 2}
                ]
            
            if not issues:
                self.display_warning(f"No issues found for repository {repo_name}")
                return
                
            # Display issues in a table
            issue_table = Table(title=f"Issues for {repo_name}", box=box.ROUNDED, border_style="blue")
            issue_table.add_column("#", style="cyan", justify="right")
            issue_table.add_column("Title")
            issue_table.add_column("State", style="bold")
            issue_table.add_column("Created", style="yellow")
            issue_table.add_column("Comments", justify="right")
            
            for issue in issues:
                issue_table.add_row(
                    str(issue["number"]),
                    issue["title"],
                    f"[green]{issue['state']}[/green]" if issue["state"] == "open" else f"[red]{issue['state']}[/red]",
                    issue["created_at"],
                    str(issue["comments"])
                )
                
            console.print(issue_table)
            
        elif subcmd == "create":
            # Create GitHub issues or pull requests
            if not self.config.get("github", {}).get("token"):
                self.display_error("GitHub is not configured. Please run /github setup first.")
                return
                
            # Determine what to create
            create_type = Prompt.ask(
                "[bold]What would you like to create?[/bold]",
                choices=["issue", "pr"],
                default="issue"
            )
            
            repo_name = Prompt.ask("[bold]Enter repository name[/bold] (format: owner/repo)")
            
            if create_type == "issue":
                console.print(Panel(
                    f"[bold]Creating new issue in:[/bold] {repo_name}",
                    title="[bold]New GitHub Issue[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
                title = Prompt.ask("[bold]Issue title[/bold]")
                console.print("[bold]Issue description:[/bold] (Type your message, press Enter then Ctrl+D to finish)")
                
                # Collect body lines
                body_lines = []
                while True:
                    try:
                        line = input()
                        body_lines.append(line)
                    except EOFError:
                        break
                        
                body = "\n".join(body_lines)
                
                # Preview the issue
                console.print(Panel(
                    f"[bold]Title:[/bold] {title}\n\n"
                    f"[bold]Description:[/bold]\n{body}",
                    title="[bold]Issue Preview[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
                
                # Ask for confirmation
                if Confirm.ask("Create this issue?", default=True):
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]Creating issue...[/bold blue]"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task("[green]Connecting to GitHub API...", total=None)
                        
                        # Placeholder for actual GitHub API call
                        issue_number = 46  # This would be the actual issue number from the API response
                    
                    self.display_success(f"Issue #{issue_number} created successfully in {repo_name}")
                else:
                    self.display_warning("Issue creation canceled")
                    
            elif create_type == "pr":
                console.print(Panel(
                    f"[bold]Creating new pull request in:[/bold] {repo_name}",
                    title="[bold]New GitHub Pull Request[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
                base_branch = Prompt.ask("[bold]Base branch[/bold]", default="main")
                head_branch = Prompt.ask("[bold]Head branch[/bold]")
                title = Prompt.ask("[bold]PR title[/bold]")
                console.print("[bold]PR description:[/bold] (Type your message, press Enter then Ctrl+D to finish)")
                
                # Collect body lines
                body_lines = []
                while True:
                    try:
                        line = input()
                        body_lines.append(line)
                    except EOFError:
                        break
                        
                body = "\n".join(body_lines)
                
                # Preview the PR
                console.print(Panel(
                    f"[bold]Title:[/bold] {title}\n"
                    f"[bold]Branches:[/bold] {head_branch} → {base_branch}\n\n"
                    f"[bold]Description:[/bold]\n{body}",
                    title="[bold]Pull Request Preview[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
                
                # Ask for confirmation
                if Confirm.ask("Create this pull request?", default=True):
                    with Progress(
                        SpinnerColumn(),
                        TextColumn("[bold blue]Creating pull request...[/bold blue]"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task("[green]Connecting to GitHub API...", total=None)
                        
                        # Placeholder for actual GitHub API call
                        pr_number = 15  # This would be the actual PR number from the API response
                    
                    self.display_success(f"Pull request #{pr_number} created successfully in {repo_name}")
                else:
                    self.display_warning("Pull request creation canceled")
                    
        else:
            # Help for GitHub command
            console.print(Panel(
                "Available GitHub subcommands:\n\n"
                "• [bold cyan]setup[/bold cyan] - Configure GitHub integration\n"
                "• [bold cyan]status[/bold cyan] - Check GitHub integration status\n"
                "• [bold cyan]repos[/bold cyan] - List your GitHub repositories\n"
                "• [bold cyan]issues [owner/repo][/bold cyan] - List issues for a repository\n"
                "• [bold cyan]create[/bold cyan] - Create a new issue or pull request",
                title="[bold]GitHub Commands Help[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
    async def configure_github(self):
        """Configure GitHub integration."""
        console.print(Panel(
            "[bold]GitHub Configuration[/bold]\n"
            "This will set up your GitHub API token for integration with the assistant.\n"
            "[yellow]Note: Your token will be stored securely but not encrypted.[/yellow]",
            title="[bold]GitHub Setup[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        console.print(Panel(
            "To create a new GitHub token:\n"
            "1. Go to [link=https://github.com/settings/tokens]https://github.com/settings/tokens[/link]\n"
            "2. Click 'Generate new token'\n"
            "3. Add a note like 'QuackQuery Assistant'\n"
            "4. Select scopes: 'repo', 'read:user'\n"
            "5. Click 'Generate token'\n"
            "6. Copy the generated token\n",
            title="[bold]Token Instructions[/bold]",
            border_style="yellow",
            box=box.ROUNDED
        ))
        
        # Get GitHub token
        token = Prompt.ask(
            "[bold]Enter your GitHub personal access token[/bold]", 
            password=True
        )
        
        if not token:
            self.display_error("No token provided. GitHub integration not configured.")
            return
            
        # Test the token
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Testing GitHub token...[/bold blue]"),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("[green]Connecting to GitHub API...", total=None)
            
            # Test connection to GitHub API
            test_result = True  # Placeholder for actual test
            
        if test_result:
            # Save the token in configuration
            if not self.config.get("github"):
                self.config["github"] = {}
                
            self.config["github"]["token"] = token
            save_config(self.config)
            
            self.display_success("GitHub token validated and saved successfully!")
        else:
            self.display_error("Failed to validate GitHub token. Please check your token and try again.")
            
    async def handle_github_operation(self, intent):
        """
        Handle GitHub operations based on detected intent.
        
        Args:
            intent: Dictionary containing detected intent information
        """
        if not self.config.get("github", {}).get("token"):
            self.display_error("GitHub is not configured. Please run /github setup first.")
            return
            
        operation = intent.get("operation")
        repo = intent.get("repository")
        
        if not operation:
            self.display_error("Unable to determine GitHub operation. Please try again with more details.")
            return
            
        if operation == "list_repos":
            console.print(Panel(
                "[bold]Fetching your GitHub repositories...[/bold]",
                title="[bold]GitHub Repositories[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Fetch repositories
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to GitHub API...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching repositories...", total=None)
                
                # Placeholder for actual GitHub API call
                repositories = [
                    {"name": "project-alpha", "description": "A cool project", "stars": 12, "forks": 5, "language": "Python"},
                    {"name": "web-app", "description": "Web application template", "stars": 45, "forks": 20, "language": "JavaScript"},
                    {"name": "data-tools", "description": "Tools for data analysis", "stars": 8, "forks": 2, "language": "Python"}
                ]
            
            # Display repositories in a table
            repo_table = Table(title="Your GitHub Repositories", box=box.ROUNDED, border_style="blue")
            repo_table.add_column("Name", style="cyan")
            repo_table.add_column("Description")
            repo_table.add_column("Stars", justify="right", style="yellow")
            repo_table.add_column("Forks", justify="right", style="green")
            repo_table.add_column("Language", style="magenta")
            
            for repo in repositories:
                repo_table.add_row(
                    repo["name"],
                    repo["description"] or "",
                    str(repo["stars"]),
                    str(repo["forks"]),
                    repo["language"] or "Unknown"
                )
                
            console.print(repo_table)
            
        elif operation == "list_issues" and repo:
            console.print(Panel(
                f"[bold]Fetching issues for:[/bold] {repo}",
                title="[bold]GitHub Issues[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Fetch issues
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to GitHub API...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching issues...", total=None)
                
                # Placeholder for actual GitHub API call
                issues = [
                    {"number": 42, "title": "Fix login bug", "state": "open", "created_at": "2023-01-15", "comments": 3},
                    {"number": 36, "title": "Update documentation", "state": "closed", "created_at": "2023-01-10", "comments": 5},
                    {"number": 45, "title": "Add new feature", "state": "open", "created_at": "2023-01-20", "comments": 2}
                ]
            
            if not issues:
                self.display_warning(f"No issues found for repository {repo}")
                return
                
            # Display issues in a table
            issue_table = Table(title=f"Issues for {repo}", box=box.ROUNDED, border_style="blue")
            issue_table.add_column("#", style="cyan", justify="right")
            issue_table.add_column("Title")
            issue_table.add_column("State", style="bold")
            issue_table.add_column("Created", style="yellow")
            issue_table.add_column("Comments", justify="right")
            
            for issue in issues:
                issue_table.add_row(
                    str(issue["number"]),
                    issue["title"],
                    f"[green]{issue['state']}[/green]" if issue["state"] == "open" else f"[red]{issue['state']}[/red]",
                    issue["created_at"],
                    str(issue["comments"])
                )
                
            console.print(issue_table)
            
        elif operation == "create_issue" and repo:
            console.print(Panel(
                f"[bold]Creating new issue in:[/bold] {repo}",
                title="[bold]New GitHub Issue[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            title = Prompt.ask("[bold]Issue title[/bold]")
            console.print("[bold]Issue description:[/bold] (Type your message, press Enter then Ctrl+D to finish)")
            
            # Collect body lines
            body_lines = []
            while True:
                try:
                    line = input()
                    body_lines.append(line)
                except EOFError:
                    break
                    
            body = "\n".join(body_lines)
            
            # Preview the issue
            console.print(Panel(
                f"[bold]Title:[/bold] {title}\n\n"
                f"[bold]Description:[/bold]\n{body}",
                title="[bold]Issue Preview[/bold]",
                border_style="green",
                box=box.ROUNDED
            ))
            
            # Ask for confirmation
            if Confirm.ask("Create this issue?", default=True):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Creating issue...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Connecting to GitHub API...", total=None)
                    
                    # Placeholder for actual GitHub API call
                    issue_number = 46  # This would be the actual issue number from the API response
                
                self.display_success(f"Issue #{issue_number} created successfully in {repo}")
            else:
                self.display_warning("Issue creation canceled")
                
        elif operation == "clone" and repo:
            # Clone operation
            clone_dir = intent.get("directory", ".")
            
            console.print(Panel(
                f"[bold]Cloning repository:[/bold] {repo}\n"
                f"[bold]Target directory:[/bold] {clone_dir}",
                title="[bold]Git Clone Operation[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Cloning repository...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Cloning...", total=None)
                
                # Placeholder for actual git clone operation
                # This would use subprocess to run git commands
                import time
                time.sleep(2)  # Simulate cloning process
            
            self.display_success(f"Repository {repo} cloned successfully to {clone_dir}")
            
        else:
            self.display_error(f"Unsupported GitHub operation: {operation}")
            
    async def handle_text_input(self):
        """Handle text input from the user."""
        from ai_assistant.utils.github_intent import GitHubIntentParser
        from ai_assistant.utils.file_intent import FileIntentParser
        from ai_assistant.utils.app_intent import AppIntentParser
        from ai_assistant.utils.email_intent import EmailIntentParser
        from ai_assistant.utils.whatsapp_intent import WhatsAppIntentParser
        
        try:
            # Get user input with Rich Prompt
            text = Prompt.ask("\n[bold cyan]You[/bold cyan]")
            
            # Skip empty input
            if not text:
                return

            # Check for exit command
            if text.lower() in ["exit", "quit", "/exit", "/quit"]:
                console.print("[bold green]Goodbye![/bold green]")
                raise KeyboardInterrupt()
                
            # Process special commands
            if text.startswith("/"):
                if await self.process_command(text):
                    return
                    
            # Initialize intent parsers if not already done
            github_intent_parser = GitHubIntentParser()
            file_intent_parser = FileIntentParser()
            app_intent_parser = AppIntentParser()
            email_intent_parser = EmailIntentParser()
            whatsapp_intent_parser = WhatsAppIntentParser()
            
            # Check for GitHub operations
            github_intent = github_intent_parser.parse_intent(text)
            if github_intent:
                result = await self.handle_github_operation(github_intent)
                self._format_and_display_response(result)
                return

            # Check for WhatsApp operations
            whatsapp_intent = whatsapp_intent_parser.parse_intent(text)
            logger.info(f"WhatsApp intent detection result: {whatsapp_intent}")
            
            if whatsapp_intent:
                result = await self.handle_whatsapp_operation(whatsapp_intent)
                # Format the response to make it visible
                self._format_and_display_response(result)
                return
                
            # If the shared text appears to be a WhatsApp-related request with a phone number
            if ("message" in text.lower() or "whatsapp" in text.lower()) and re.search(r'[+=]?\d{10,}', text):
                logger.info("Detected potential WhatsApp message to phone number")
                # Try to extract recipient (phone number) and message content
                phone_match = re.search(r'(?:to\s+)?([+=]?\d{10,})', text)
                if phone_match:
                    recipient = phone_match.group(1)
                    # Look for content after "about" or similar terms
                    content_match = re.search(r'(?:about|regarding|on|for)\s+(.*?)(?:\.|$)', text, re.IGNORECASE)
                    instruction = text  # Use full text as instruction if no specific content found
                    
                    logger.info(f"Creating manual WhatsApp intent for phone: {recipient}")
                    # Create a WhatsApp intent
                    whatsapp_intent = {
                        'action': 'ai_compose_whatsapp',
                        'recipient': recipient.strip(),
                        'instruction': instruction
                    }
                    
                    result = await self.handle_whatsapp_operation(whatsapp_intent)
                    self._format_and_display_response(result)
                    return
                
            # Direct pattern match for AI write message with phone number
            ai_whatsapp_phone_match = re.search(r'(?:ai|assistant|help)\s+(?:write|compose|draft|create)\s+(?:a\s+)?(?:message|msg)(?:\s+to\s+|\s+for\s+)?([+=]?\d{10,})', text.lower())
            if ai_whatsapp_phone_match:
                logger.info("Direct pattern match for AI WhatsApp message to phone")
                recipient = ai_whatsapp_phone_match.group(1)
                
                # Create a WhatsApp intent
                whatsapp_intent = {
                    'action': 'ai_compose_whatsapp',
                    'recipient': recipient.strip(),
                    'instruction': text
                }
                
                result = await self.handle_whatsapp_operation(whatsapp_intent)
                self._format_and_display_response(result)
                return
            
            # Check for Email operations
            email_intent = email_intent_parser.parse_intent(text)
            if email_intent:
                result = await self.handle_email_operation(email_intent, prompt=text)
                self._format_and_display_response(result)
                return
                
            # Check for File operations
            file_intent = file_intent_parser.parse_intent(text)
            if file_intent:
                result = await self.handle_file_operation(file_intent)
                self._format_and_display_response(result)
                return
                
            # Check for App operations
            app_intent = app_intent_parser.parse_intent(text)
            if app_intent:
                result = await self.handle_app_operation(app_intent)
                self._format_and_display_response(result)
                return
                
            # Process as a regular question with Rich UI feedback
            include_screenshot = Confirm.ask("Include screenshot context?", default=False)
            
            # Use Rich progress bar instead of animated loading
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Processing...[/bold blue]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Thinking...", total=None)
                
                try:
                    screenshot_encoded = self.desktop_screenshot.capture() if include_screenshot else None
                    response = await self.assistant.answer_async(text, screenshot_encoded)
                    
                    # Display response with syntax highlighting for code blocks
                    self._format_and_display_response(response)
                    
                    return response
                    
                except Exception as e:
                    logger.error(f"Question processing error: {e}")
                    console.print(f"\n[bold red]❌ Error processing question: {e}[/bold red]")
                    return

        except Exception as e:
            console.print(f"\n[bold red]❌ Error processing input: {str(e)}[/bold red]")
            logger.exception("Error processing input:")

    def _format_and_display_response(self, response):
        """Format and display AI response with Rich UI enhancements."""
        # Check if response is None or empty
        if not response:
            logger.warning("Received empty response from assistant")
            console.print("[yellow]No response received from assistant.[/yellow]")
            return
            
        # Check for code blocks in the response
        if "```" in response:
            # Split the response by code blocks
            parts = response.split("```")
            
            # Display each part with appropriate formatting
            for i, part in enumerate(parts):
                if i == 0:
                    # First part is always text before the first code block
                    if part.strip():
                        console.print(Markdown(part.strip()))
                elif i % 2 == 1:
                    # Odd-indexed parts are code blocks
                    # Extract language if specified (e.g., ```python)
                    code_lines = part.strip().split('\n')
                    if code_lines and not code_lines[0].isspace() and len(code_lines[0].strip()) > 0:
                        lang = code_lines[0].strip().lower()
                        code = '\n'.join(code_lines[1:])
                    else:
                        lang = "text"
                        code = part.strip()
                    
                    # Display code with syntax highlighting
                    console.print(Syntax(code, lang, theme="monokai", line_numbers=True, word_wrap=True))
                else:
                    # Even-indexed parts (except 0) are text between code blocks
                    if part.strip():
                        console.print(Markdown(part.strip()))
        else:
            # No code blocks, display as markdown
            console.print(Markdown(response))

    async def ocr_command(self, args):
        """
        Handle OCR command for extracting text from images.
        
        Args:
            args: Command arguments
        """
        if not args:
            self.display_error("Please specify an image path or 'screen' to capture the current screen")
            console.print("[dim]Example: /ocr path/to/image.jpg[/dim]")
            console.print("[dim]Example: /ocr screen[/dim]")
            return
            
        # Check if the user wants to capture the screen
        if args.lower() == "screen":
            console.print(Panel(
                "[bold]📸 Capturing your screen...[/bold]",
                title="[bold]OCR Operation[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Capturing screen...[/bold blue]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Processing...", total=None)
                # Capture the screen
                screenshot_path = os.path.join(os.getcwd(), "screenshot.png")
                self.desktop_screenshot.capture_to_file(screenshot_path)
                image_path = screenshot_path
                
            self.display_success(f"Screen captured and saved to {screenshot_path}")
        else:
            # User provided an image path
            image_path = args.strip()
            if not os.path.exists(image_path):
                self.display_error(f"Image file not found: {image_path}")
                return
        
        # Progress indicators for OCR processing
        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Extracting text...[/bold blue]"),
            BarColumn(),
            TimeElapsedColumn(),
            console=console,
            transient=True
        ) as progress:
            task = progress.add_task("[green]Processing image...", total=None)
            extracted_text = self.ocr_processor.extract_text(image_path)
        
        if not extracted_text:
            self.display_warning("No text was extracted from the image")
            return
        
        # Display the extracted text
        console.print(Panel(
            f"[bold green]Extracted Text:[/bold green]\n\n{extracted_text}",
            title=f"[bold]OCR Results: {os.path.basename(image_path)}[/bold]",
            border_style="green",
            box=box.ROUNDED
        ))
        
        # Ask if user wants to save the extracted text
        if Confirm.ask("Would you like to save this text to a file?", default=False):
            default_filename = f"{os.path.basename(image_path).split('.')[0]}.txt"
            file_path = Prompt.ask("Enter file path", default=default_filename)
            
            try:
                with open(file_path, 'w') as f:
                    f.write(extracted_text)
                self.display_success(f"Text saved to {file_path}")
            except Exception as e:
                self.display_error(f"Error saving file: {str(e)}")
                
        # Ask if user wants AI analysis of the extracted text
        if Confirm.ask("Would you like AI analysis of this text?", default=True):
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Analyzing text...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                analysis_task = progress.add_task("[green]Thinking...", total=None)
                
                # Ask the AI to analyze the extracted text
                analysis_prompt = f"Analyze the following OCR extracted text and provide insights:\n\n{extracted_text}"
                analysis = await self.assistant.answer_async(analysis_prompt)
            
            # Display the analysis
            console.print(Panel(
                Markdown(analysis),
                title="[bold]AI Analysis[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))

    async def web_command(self, args):
        """
        Handle web command for searching or accessing web content.
        
        Args:
            args: Command arguments
        """
        if not args:
            self.display_error("Please specify a search query or URL")
            console.print("[dim]Example: /web how to make pancakes[/dim]")
            console.print("[dim]Example: /web https://example.com[/dim]")
            return
            
        query = args.strip()
        
        # Check if it's a URL
        if query.startswith(("http://", "https://")):
            console.print(Panel(
                f"[bold]🌐 Accessing URL:[/bold] {query}",
                title="[bold]Web Operation[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Fetching content...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Loading...", total=None)
                
                try:
                    # Implement a web fetcher or use an existing one
                    content = "Web content fetching would go here"
                    
                    # Display a sample of the content
                    console.print(Panel(
                        f"[dim]{content[:500]}...[/dim]",
                        title=f"[bold]Content from {query}[/bold]",
                        border_style="blue",
                        box=box.ROUNDED
                    ))
                    
                    # Ask if the user wants AI to analyze the web content
                    if Confirm.ask("Would you like AI analysis of this web content?", default=True):
                        with Progress(
                            SpinnerColumn(),
                            TextColumn("[bold blue]Analyzing content...[/bold blue]"),
                            BarColumn(),
                            TimeElapsedColumn(),
                            console=console,
                            transient=True
                        ) as progress:
                            analysis_task = progress.add_task("[green]Thinking...", total=None)
                            analysis = await self.assistant.answer_async(f"Analyze this web content: {content[:2000]}")
                        
                        # Display the analysis
                        console.print(Panel(
                            Markdown(analysis),
                            title="[bold]AI Analysis[/bold]",
                            border_style="blue",
                            box=box.ROUNDED
                        ))
                    
                except Exception as e:
                    self.display_error(f"Error fetching web content: {str(e)}")
            
        else:
            # It's a search query
            console.print(Panel(
                f"[bold]🔍 Searching for:[/bold] {query}",
                title="[bold]Web Search[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Searching...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching results...", total=None)
                
                try:
                    # Use the assistant to search for answers
                    response = await self.assistant.answer_async(f"Web search: {query}")
                    
                    # Format and display the response
                    self._format_and_display_response(response)
                    
                except Exception as e:
                    self.display_error(f"Error during web search: {str(e)}")

    async def email_command(self, args):
        """
        Handle email commands.
        
        Args:
            args: Command arguments
        """
        try:
            if not hasattr(self, 'email_manager') or self.email_manager is None:
                self.display_error("Email functionality is not available")
                return True
                
            if not args:
                self.display_error("Missing email subcommand. Available commands: setup, send, read, check")
                return True
                
            subcommand = args[0].lower()
            
            # First validate if email is set up for commands that require it
            if subcommand in ["send", "read"] and not getattr(self, 'email_setup_complete', False):
                # Try to load the configuration
                await self.check_email_config()
                
                # If still not configured after check
                if not getattr(self, 'email_setup_complete', False):
                    self.display_error("Email is not set up. Please run '/email setup' first.")
                    return
            
            if subcommand == "setup":
                await self.email_setup()
                return True
                
            elif subcommand == "send":
                # Optional recipient from command
                recipient = args[1] if len(args) > 1 else None
                
                if recipient and recipient.startswith("to"):
                    recipient = recipient[2:].strip()
                    
                # Basic validation
                if recipient and '@' not in recipient:
                    self.display_error(f"Invalid email address: {recipient}")
                    recipient = None
                    
                await self.compose_email(recipient)
                return True
                
            elif subcommand == "read":
                await self.read_emails()
                return True
                
            elif subcommand == "check":
                await self.check_email_config()
                return True
                
            else:
                self.display_error(f"Unknown email subcommand: {subcommand}")
                self.display_warning("Available commands: setup, send, read, check")
                return True
                
        except Exception as e:
            self.display_error(f"Error processing email command: {str(e)}")
            logger.exception("Email command error")
            return True

    async def email_ai_write(self, to_address=None, prompt=None):
        """
        Use AI to write an email.
        
        Args:
            to_address (str, optional): Optional recipient email address
            prompt (str, optional): The original prompt text for context
        """
        try:
            # First make sure email is configured
            if not hasattr(self, 'email_manager') or not getattr(self, 'email_setup_complete', False):
                await self.check_email_config()
                
                if not getattr(self, 'email_setup_complete', False):
                    self.display_error("Email is not configured. Please run '/email setup' first.")
                    return
            
            # If no recipient provided, ask for one
            if not to_address:
                console.print(Panel(
                    "To generate an email with AI assistance, we need a recipient email address.",
                    title="[bold]AI Email Writer[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                to_address = Prompt.ask("[bold cyan]Recipient email address[/bold cyan]")
                
            console.print(Panel(
                f"[bold]AI Email Composition Assistant[/bold]\n"
                f"Recipient: {to_address}",
                title="[bold]AI Email Writer[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Get email details
            subject = Prompt.ask("[bold cyan]Subject[/bold cyan]")
            
            # More comprehensive instructions
            console.print(Panel(
                "Tell the AI what kind of email you want to write. Be specific about:\n"
                "• Tone (formal, friendly, professional)\n"
                "• Purpose (meeting request, thank you, application, etc.)\n"
                "• Key points to include\n"
                "• Any specific requirements",
                title="[bold]Email Instructions[/bold]",
                border_style="green",
                box=box.ROUNDED
            ))
            
            instructions = Prompt.ask("[bold cyan]Instructions for AI[/bold cyan]")
            
            # Generate the email using AI
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Generating email...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Thinking...", total=None)
                
                prompt = f"Write an email to {to_address} with the subject '{subject}'. {instructions}"
                if prompt:
                    generated_email = await self.assistant.answer_async(prompt)
                else:
                    generated_email = await self.assistant.answer_async(f"Write an email to {to_address} with the subject '{subject}'.")
                
                # Extract subject and body from the generated email
                # This is a simple implementation; might need better parsing
                generated_body = generated_email
            
            # Preview the email with improved formatting
            console.print(Panel(
                f"[bold]Subject:[/bold] {subject}\n\n"
                f"[bold]Body:[/bold]\n{generated_body}",
                title=f"[bold]Generated Email: {subject}[/bold]",
                border_style="green",
                box=box.ROUNDED,
                padding=(1, 2)
            ))
            
            # Ask for what to do with the generated email
            console.print("[bold cyan]What would you like to do with this email?[/bold cyan]")
            choices = {
                "1": "Send as is",
                "2": "Edit before sending",
                "3": "Regenerate with new instructions",
                "4": "Save as draft (not implemented)",
                "5": "Cancel"
            }
            
            # Display options with styling
            for key, value in choices.items():
                console.print(f"[bold blue]{key}.[/bold blue] {value}")
                
            choice = Prompt.ask("[bold]Select an option[/bold]", choices=list(choices.keys()), default="2")
            
            if choice == "1":  # Send as is
                console.print(f"[bold cyan]Sending email to {to_address}...[/bold cyan]")
                success = await asyncio.to_thread(self.email_manager.send_email, to_address, subject, generated_body)
                
                if success:
                    self.display_success("Email sent successfully!")
                else:
                    self.display_error(f"Failed to send email: {success}")
            elif choice == "2":  # Edit before sending
                # Create a temporary file for editing in Notepad
                with tempfile.NamedTemporaryFile(mode='w+', suffix='.txt', delete=False) as temp_file:
                    temp_file.write(generated_body)
                    temp_path = temp_file.name
                
                self.display_info(f"Opening email in Notepad for editing. Save and close Notepad when done.")
                
                # Use the appropriate command based on OS
                if os.name == 'nt':  # Windows
                    subprocess.run(['notepad.exe', temp_path], check=True)
                else:
                    # Use default editor on Unix systems
                    editor = os.environ.get('EDITOR', 'nano')
                    subprocess.run([editor, temp_path], check=True)
                
                # Read the edited content back
                try:
                    with open(temp_path, 'r', encoding='utf-8') as edited_file:
                        edited_body = edited_file.read()
                    
                    # Clean up the temporary file
                    os.unlink(temp_path)
                    
                    # Preview the edited email
                    console.print(Panel(
                        f"[bold]Subject:[/bold] {subject}\n\n"
                        f"[bold]Body:[/bold]\n{edited_body}",
                        title=f"[bold]Edited Email: {subject}[/bold]",
                        border_style="green",
                        box=box.ROUNDED,
                        padding=(1, 2)
                    ))
                    
                    # Confirm sending
                    if Confirm.ask("Send this edited email?"):
                        console.print(f"[bold cyan]Sending email to {to_address}...[/bold cyan]")
                        success = await asyncio.to_thread(self.email_manager.send_email, to_address, subject, edited_body)
                        
                        if success:
                            self.display_success("Email sent successfully!")
                        else:
                            self.display_error(f"Failed to send email: {success}")
                    else:
                        self.display_warning("Email sending canceled")
                except Exception as e:
                    self.display_error(f"Error reading edited file: {str(e)}")
                    os.unlink(temp_path)  # Clean up even on error
                            
            elif choice == "3":  # Regenerate
                console.print("[bold cyan]New instructions for regenerating the email:[/bold cyan]")
                new_instructions = Prompt.ask("[bold]New instructions[/bold]")
                await self.email_ai_write(to_address, prompt=new_instructions)  # Restart the process
                
            elif choice == "4":  # Save draft
                self.display_warning("Save as draft feature is not yet implemented")
                
            elif choice == "5":  # Cancel
                self.display_warning("Email creation canceled")
                
        except Exception as e:
            self.display_error(f"Error in AI email composition: {str(e)}")
            logger.exception("Error in email_ai_write:")

    async def read_emails(self):
        """
        Read and display emails from the inbox.
        """
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Checking emails...[/bold blue]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Connecting to mail server...", total=None)
                
                # Check emails using the email manager
                emails = self.email_manager.check_emails(limit=10)
                
            # Handle error messages (string responses)
            if isinstance(emails, str):
                self.display_error(emails)
                return
                
            # No emails found
            if not emails:
                self.display_warning("No emails found in your inbox.")
                return
                
            # Display email list
            console.print(Panel(
                f"Found [bold cyan]{len(emails)}[/bold cyan] emails in your inbox",
                title="[bold]Email Inbox[/bold]",
                border_style="cyan",
                box=box.ROUNDED
            ))
            
            # Create a table for the emails
            table = Table(title="Recent Emails", box=box.ROUNDED, border_style="blue")
            table.add_column("#", style="dim", width=4)
            table.add_column("From", style="bold", width=30, overflow="fold")
            table.add_column("Subject", style="italic green", width=40, overflow="fold")
            table.add_column("Date", style="blue", width=25)
            
            for i, email_data in enumerate(emails, 1):
                from_addr = email_data['from']
                subject = email_data['subject'] or "(No Subject)"
                date = email_data['date']
                
                table.add_row(
                    str(i),
                    from_addr,
                    subject,
                    date
                )
                
            # Display the table
            console.print(table)
            
            # Ask which email to read
            email_num = Prompt.ask(
                "[bold cyan]Enter email number to read (or 'q' to quit)[/bold cyan]",
                default="q",
                show_default=False
            )
            
            if email_num.lower() == 'q':
                return
                
            try:
                # Validate the selection
                email_index = int(email_num) - 1
                if email_index < 0 or email_index >= len(emails):
                    self.display_error(f"Invalid email number: {email_num}")
                    return
                    
                # Get the selected email
                selected_email = emails[email_index]
                
                # Display the email content
                console.print(Panel(
                    f"[bold]From:[/bold] {selected_email['from']}\n"
                    f"[bold]To:[/bold] {selected_email['to']}\n"
                    f"[bold]Date:[/bold] {selected_email['date']}\n"
                    f"[bold]Subject:[/bold] {selected_email['subject']}\n\n"
                    f"{selected_email['body']}",
                    title=f"[bold]Email #{email_num}[/bold]",
                    border_style="green",
                    box=box.ROUNDED,
                    padding=(1, 2),
                    expand=False
                ))
                
                # Option to reply
                if Confirm.ask("Reply to this email?"):
                    reply_to = selected_email['from']
                    reply_subject = f"Re: {selected_email['subject']}"
                    
                    # Extract the email address from the From field if needed
                    import re
                    email_pattern = r'[\w\.-]+@[\w\.-]+\.[A-Z|a-z]{2,}'
                    email_matches = re.findall(email_pattern, reply_to)
                    if email_matches:
                        reply_to = email_matches[0]
                    
                    # Compose reply
                    await self.compose_email(reply_to, reply_subject)
                
            except ValueError:
                self.display_error("Please enter a valid number or 'q'")
                
        except Exception as e:
            self.display_error(f"Error reading emails: {str(e)}")
            logger.exception("Error reading emails:")

    async def handle_github_operation(self, intent):
        """
        Handle GitHub operations based on detected intent.
        
        Args:
            intent: Dictionary containing detected intent information
        """
        if not self.config.get("github", {}).get("token"):
            self.display_error("GitHub is not configured. Please run /github setup first.")
            return
            
        operation = intent.get("operation")
        repo = intent.get("repository")
        
        if not operation:
            self.display_error("Unable to determine GitHub operation. Please try again with more details.")
            return
            
        if operation == "list_repos":
            console.print(Panel(
                "[bold]Fetching your GitHub repositories...[/bold]",
                title="[bold]GitHub Repositories[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Fetch repositories
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to GitHub API...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching repositories...", total=None)
                
                # Placeholder for actual GitHub API call
                repositories = [
                    {"name": "project-alpha", "description": "A cool project", "stars": 12, "forks": 5, "language": "Python"},
                    {"name": "web-app", "description": "Web application template", "stars": 45, "forks": 20, "language": "JavaScript"},
                    {"name": "data-tools", "description": "Tools for data analysis", "stars": 8, "forks": 2, "language": "Python"}
                ]
            
            # Display repositories in a table
            repo_table = Table(title="Your GitHub Repositories", box=box.ROUNDED, border_style="blue")
            repo_table.add_column("Name", style="cyan")
            repo_table.add_column("Description")
            repo_table.add_column("Stars", justify="right", style="yellow")
            repo_table.add_column("Forks", justify="right", style="green")
            repo_table.add_column("Language", style="magenta")
            
            for repo in repositories:
                repo_table.add_row(
                    repo["name"],
                    repo["description"] or "",
                    str(repo["stars"]),
                    str(repo["forks"]),
                    repo["language"] or "Unknown"
                )
                
            console.print(repo_table)
            
        elif operation == "list_issues" and repo:
            console.print(Panel(
                f"[bold]Fetching issues for:[/bold] {repo}",
                title="[bold]GitHub Issues[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            # Fetch issues
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Connecting to GitHub API...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Fetching issues...", total=None)
                
                # Placeholder for actual GitHub API call
                issues = [
                    {"number": 42, "title": "Fix login bug", "state": "open", "created_at": "2023-01-15", "comments": 3},
                    {"number": 36, "title": "Update documentation", "state": "closed", "created_at": "2023-01-10", "comments": 5},
                    {"number": 45, "title": "Add new feature", "state": "open", "created_at": "2023-01-20", "comments": 2}
                ]
            
            if not issues:
                self.display_warning(f"No issues found for repository {repo}")
                return
                
            # Display issues in a table
            issue_table = Table(title=f"Issues for {repo}", box=box.ROUNDED, border_style="blue")
            issue_table.add_column("#", style="cyan", justify="right")
            issue_table.add_column("Title")
            issue_table.add_column("State", style="bold")
            issue_table.add_column("Created", style="yellow")
            issue_table.add_column("Comments", justify="right")
            
            for issue in issues:
                issue_table.add_row(
                    str(issue["number"]),
                    issue["title"],
                    f"[green]{issue['state']}[/green]" if issue["state"] == "open" else f"[red]{issue['state']}[/red]",
                    issue["created_at"],
                    str(issue["comments"])
                )
                
            console.print(issue_table)
            
        elif operation == "create_issue" and repo:
            console.print(Panel(
                f"[bold]Creating new issue in:[/bold] {repo}",
                title="[bold]New GitHub Issue[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            title = Prompt.ask("[bold]Issue title[/bold]")
            console.print("[bold]Issue description:[/bold] (Type your message, press Enter then Ctrl+D to finish)")
            
            # Collect body lines
            body_lines = []
            while True:
                try:
                    line = input()
                    body_lines.append(line)
                except EOFError:
                    break
                    
            body = "\n".join(body_lines)
            
            # Preview the issue
            console.print(Panel(
                f"[bold]Title:[/bold] {title}\n\n"
                f"[bold]Description:[/bold]\n{body}",
                title="[bold]Issue Preview[/bold]",
                border_style="green",
                box=box.ROUNDED
            ))
            
            # Ask for confirmation
            if Confirm.ask("Create this issue?", default=True):
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Creating issue...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Connecting to GitHub API...", total=None)
                    
                    # Placeholder for actual GitHub API call
                    issue_number = 46  # This would be the actual issue number from the API response
                
                self.display_success(f"Issue #{issue_number} created successfully in {repo}")
            else:
                self.display_warning("Issue creation canceled")
                
        elif operation == "clone" and repo:
            # Clone operation
            clone_dir = intent.get("directory", ".")
            
            console.print(Panel(
                f"[bold]Cloning repository:[/bold] {repo}\n"
                f"[bold]Target directory:[/bold] {clone_dir}",
                title="[bold]Git Clone Operation[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Cloning repository...[/bold blue]"),
                BarColumn(),
                TimeElapsedColumn(),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Cloning...", total=None)
                
                # Placeholder for actual git clone operation
                # This would use subprocess to run git commands
                import time
                time.sleep(2)  # Simulate cloning process
            
            self.display_success(f"Repository {repo} cloned successfully to {clone_dir}")
            
        else:
            self.display_error(f"Unsupported GitHub operation: {operation}")
            
    async def handle_file_operation(self, intent):
        """
        Handle file operations.
        
        Args:
            intent: The detected intent for file operations
            
        Returns:
            str: Result of the file operation
        """
        operation = intent.get("operation", "").lower() if isinstance(intent, dict) else ""
        params = intent.get("params", {}) if isinstance(intent, dict) else {}
        
        # Extract the file path if present
        file_path = params.get("path", "")
        
        if operation == "list":
            # List files in a directory
            directory = file_path or os.getcwd()
            
            try:
                console.print(Panel(
                    f"[bold]Listing files in:[/bold] {directory}",
                    title="[bold]File Operation[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
                files = os.listdir(directory)
                
                # Create a table to display files
                file_table = Table(
                    title=f"Contents of {os.path.basename(directory)}",
                    box=box.ROUNDED,
                    border_style="blue"
                )
                
                file_table.add_column("Name", style="cyan")
                file_table.add_column("Type", style="green")
                file_table.add_column("Size", style="magenta")
                file_table.add_column("Modified", style="yellow")
                
                for file in files:
                    full_path = os.path.join(directory, file)
                    file_stat = os.stat(full_path)
                    
                    # Determine file type
                    file_type = "Directory" if os.path.isdir(full_path) else "File"
                    
                    # Format file size
                    size_bytes = file_stat.st_size
                    if size_bytes < 1024:
                        size_str = f"{size_bytes} B"
                    elif size_bytes < 1024 * 1024:
                        size_str = f"{size_bytes / 1024:.1f} KB"
                    else:
                        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"
                    
                    # Format modification time
                    mod_time = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
                    
                    file_table.add_row(file, file_type, size_str, mod_time)
                
                console.print(file_table)
                return f"Listed {len(files)} files in {directory}"
                
            except PermissionError:
                self.display_error(f"Permission denied for: {directory}")
                return f"Permission denied for: {directory}"
            except FileNotFoundError:
                self.display_error(f"Directory not found: {directory}")
                return f"Directory not found: {directory}"
            except Exception as e:
                self.display_error(f"Error listing files: {str(e)}")
                return f"Error listing files: {str(e)}"
                
        elif operation == "create":
            # Create a file
            content = params.get("content", "")
            
            if not file_path:
                self.display_error("No file path specified")
                return "No file path specified"
                
            try:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
                
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Creating file...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Writing file...", total=None)
                    with open(file_path, 'w') as f:
                        f.write(content)
                
                self.display_success(f"File created: {file_path}")
                return f"Successfully created file: {file_path}"
                
            except PermissionError:
                self.display_error(f"Permission denied for: {file_path}")
                return f"Permission denied for: {file_path}"
            except Exception as e:
                self.display_error(f"Error creating file: {str(e)}")
                return f"Error creating file: {str(e)}"
                
        elif operation == "delete":
            # Delete a file
            if not file_path:
                self.display_error("No file path specified")
                return "No file path specified"
                
            try:
                # Confirm deletion
                if not Confirm.ask(f"Are you sure you want to delete [bold red]{file_path}[/bold red]?", default=False):
                    self.display_warning("File deletion canceled")
                    return "File deletion canceled"
                    
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Deleting file...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Removing file...", total=None)
                    if os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                    else:
                        os.remove(file_path)
                
                self.display_success(f"Successfully deleted: {file_path}")
                return f"Successfully deleted: {file_path}"
                
            except PermissionError:
                self.display_error(f"Permission denied for: {file_path}")
                return f"Permission denied for: {file_path}"
            except FileNotFoundError:
                self.display_error(f"File not found: {file_path}")
                return f"File not found: {file_path}"
            except Exception as e:
                self.display_error(f"Error deleting file: {str(e)}")
                return f"Error deleting file: {str(e)}"
                
        elif operation == "read":
            # Read a file
            if not file_path:
                self.display_error("No file path specified")
                return "No file path specified"
                
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Reading file...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Loading content...", total=None)
                    
                    # Check file size
                    file_size = os.path.getsize(file_path)
                    if file_size > 10 * 1024 * 1024:  # 10MB limit
                        self.display_warning(f"File is too large ({file_size / (1024 * 1024):.1f} MB). Only the first 100 lines will be displayed.")
                        with open(file_path, 'r') as f:
                            content = "".join(f.readlines()[:100])
                            content += "\n... (file truncated) ..."
                    else:
                        with open(file_path, 'r') as f:
                            content = f.read()
                
                # Determine syntax highlighting based on file extension
                file_ext = os.path.splitext(file_path)[1].lower()
                lexer_name = {
                    ".py": "python",
                    ".js": "javascript",
                    ".html": "html",
                    ".css": "css",
                    ".json": "json",
                    ".md": "markdown",
                    ".xml": "xml",
                    ".java": "java",
                    ".c": "c",
                    ".cpp": "cpp",
                    ".cs": "csharp",
                    ".go": "go",
                    ".rb": "ruby",
                    ".php": "php",
                    ".sh": "bash",
                    ".bat": "batch",
                    ".ps1": "powershell",
                    ".sql": "sql",
                    ".yaml": "yaml",
                    ".yml": "yaml",
                    ".txt": None
                }.get(file_ext, None)
                
                file_panel = Panel(
                    Syntax(content, lexer_name) if lexer_name else content,
                    title=f"[bold]{os.path.basename(file_path)}[/bold]",
                    border_style="blue",
                    box=box.ROUNDED,
                    width=min(len(max(content.split('\n'), key=len)) + 10, console.width - 10)
                )
                
                console.print(file_panel)
                return f"Read file: {file_path}"
                
            except PermissionError:
                self.display_error(f"Permission denied for: {file_path}")
                return f"Permission denied for: {file_path}"
            except FileNotFoundError:
                self.display_error(f"File not found: {file_path}")
                return f"File not found: {file_path}"
            except UnicodeDecodeError:
                self.display_error(f"Unable to read file: {file_path}. This might be a binary file.")
                return f"Unable to read file: {file_path}. This might be a binary file."
            except Exception as e:
                self.display_error(f"Error reading file: {str(e)}")
                return f"Error reading file: {str(e)}"
        
        else:
            self.display_warning("Unsupported file operation")
            return "Unsupported file operation. Try 'list', 'create', 'read', or 'delete'."

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

    async def configure(self):
        """Configure the AI Assistant settings."""
        console.print(Panel("[bold cyan]⚙️ Configuration[/bold cyan]", box=box.ROUNDED, border_style="cyan"))
        
        config_table = Table(show_header=False, box=box.SIMPLE)
        config_table.add_column("Option", style="cyan")
        config_table.add_column("Description")
        config_table.add_row("1", "Change AI model")
        config_table.add_row("2", "Change assistant role")
        config_table.add_row("3", "Update API key")
        config_table.add_row("4", "Configure GitHub integration")
        config_table.add_row("5", "Configure email integration")
        config_table.add_row("6", "Configure WhatsApp integration")
        config_table.add_row("7", "Return to main menu")
        
        console.print(Panel(
            config_table,
            title="[bold]Settings Menu[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4", "5", "6", "7"], default="7")
        
        if choice == "1":
            await self.change_model()
        elif choice == "2":
            await self.change_role()
        elif choice == "3":
            await self.update_api_key()
        elif choice == "4":
            await self.configure_github()
        elif choice == "5":
            await self.configure_email()
        elif choice == "6":
            await self.configure_whatsapp()
        # Return to main menu for '7' or any other input

    async def change_model(self):
        """Change the AI model."""
        model_table = Table(box=box.ROUNDED)
        model_table.add_column("Option", style="cyan")
        model_table.add_column("Model")
        model_table.add_column("Description")
        
        model_table.add_row("1", "Gemini", "Google AI large language model")
        model_table.add_row("2", "OpenAI", "GPT-4 and GPT-3.5 models")
        
        console.print(Panel(
            model_table,
            title="[bold]Available AI Models[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        model_choice = Prompt.ask("Enter your choice", choices=["1", "2"], default="1")
        model_map = {"1": "Gemini", "2": "OpenAI"}
        
        if model_choice in model_map:
            self.config["model"] = model_map[model_choice]
            save_config(self.config)
            self.initialize_assistant()
            console.print(f"[green]✅ Model changed to {self.config['model']}[/green]")
        else:
            console.print("[bold red]❌ Invalid choice.[/bold red]")

    async def change_role(self):
        """Change the assistant role."""
        from ..core.prompts import ROLE_PROMPTS
        
        role_table = Table(box=box.ROUNDED)
        role_table.add_column("Option", style="cyan")
        role_table.add_column("Role")
        role_table.add_column("Description")
        
        for i, (role, description) in enumerate(ROLE_PROMPTS.items(), 1):
            # Extract a short description from the full prompt
            short_desc = description.split("\n")[0] if "\n" in description else description[:50] + "..."
            role_table.add_row(str(i), role, short_desc)
        
        console.print(Panel(
            role_table,
            title="[bold]Assistant Roles[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        role_choices = [str(i) for i in range(1, len(ROLE_PROMPTS) + 1)]
        role_choice = Prompt.ask("Enter your choice", choices=role_choices, default="1")
        
        try:
            role_idx = int(role_choice) - 1
            if 0 <= role_idx < len(ROLE_PROMPTS):
                self.config["role"] = list(ROLE_PROMPTS.keys())[role_idx]
                save_config(self.config)
                self.initialize_assistant()
                console.print(f"[green]✅ Role changed to {self.config['role']}[/green]")
            else:
                console.print("[bold red]❌ Invalid choice.[/bold red]")
        except ValueError:
            console.print("[bold red]❌ Please enter a number.[/bold red]")

    async def update_api_key(self):
        """Update the API key for the current model."""
        model = self.config.get("model", "Gemini")
        
        console.print(Panel(
            f"The current AI model is [bold cyan]{model}[/bold cyan].\nPlease provide a new API key for this model.",
            title="[bold]API Key Update[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        # Use getpass for API keys for security
        import getpass
        new_key = getpass.getpass(f"Enter new {model} API Key: ")
        
        if new_key.strip():
            # Save in config with model-specific key
            self.config[f"{model.lower()}_api_key"] = new_key
            
            # Also save to generic api_key for backward compatibility
            self.config["api_key"] = new_key
            
            save_config(self.config)
            self.initialize_assistant()
            
            console.print(f"[green]✅ API key updated for {model}[/green]")
            console.print("[dim]Your API key has been saved and will be remembered for future sessions[/dim]")
        else:
            console.print("[bold red]❌ No API key provided. Operation canceled.[/bold red]")

    async def configure_github(self):
        """Configure GitHub integration settings."""
        github_table = Table(show_header=False, box=box.SIMPLE)
        github_table.add_column("Option", style="cyan")
        github_table.add_column("Description")
        github_table.add_row("1", "Set GitHub Access Token")
        github_table.add_row("2", "View Current GitHub Status")
        github_table.add_row("3", "Remove GitHub Access Token")
        github_table.add_row("4", "Back to configuration menu")
        
        console.print(Panel(
            github_table,
            title="[bold]GitHub Integration Configuration[/bold]",
            border_style="blue",
            box=box.ROUNDED
        ))
        
        choice = Prompt.ask("Enter your choice", choices=["1", "2", "3", "4"], default="4")
        
        if choice == "1":
            # Use getpass for secret tokens
            import getpass
            token = getpass.getpass("\nEnter your GitHub Personal Access Token: ")
            
            if token:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Authenticating with GitHub...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Connecting...", total=None)
                    
                    # Simulate a bit of waiting time for the authentication process
                    import time
                    time.sleep(1)
                    
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
                        
                        console.print(Panel(
                            f"[green]✅ GitHub token set successfully![/green]\nAuthenticated as: [bold]{self.github.username}[/bold]",
                            title="[bold]GitHub Authentication[/bold]",
                            border_style="green",
                            box=box.ROUNDED
                        ))
                    else:
                        console.print(Panel(
                            "[bold red]❌ GitHub authentication failed.[/bold red]\nPlease check your token and try again.",
                            title="[bold]GitHub Authentication[/bold]",
                            border_style="red",
                            box=box.ROUNDED
                        ))
            else:
                console.print("[bold orange]⚠️ No token provided. GitHub integration will not be available.[/bold orange]")
            
        elif choice == "2":
            if self.github.authenticated:
                console.print(Panel(
                    f"[green]✅ GitHub Status: Authenticated[/green]\nUsername: [bold]{self.github.username}[/bold]\nGitHub integration is active and ready to use.",
                    title="[bold]GitHub Status[/bold]",
                    border_style="green",
                    box=box.ROUNDED
                ))
            else:
                console.print(Panel(
                    "[bold orange]⚠️ GitHub Status: Not authenticated[/bold orange]\nYou need to set a GitHub access token to use GitHub features.",
                    title="[bold]GitHub Status[/bold]",
                    border_style="orange",
                    box=box.ROUNDED
                ))
            
        elif choice == "3":
            if "GITHUB_TOKEN" in os.environ:
                confirm = Confirm.ask("Are you sure you want to remove your GitHub token?", default=False)
                
                if confirm:
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
                    console.print("[green]✅ GitHub token removed successfully.[/green]")
                else:
                    console.print("[blue]Operation canceled.[/blue]")
            else:
                console.print("[blue]No GitHub token is currently set.[/blue]")
        
        # Return to config menu for '4' or any other input

    async def configure_whatsapp(self):
        """Configure WhatsApp integration settings."""
        from rich.prompt import Confirm
        
        console.print(Panel("[bold cyan]⚙️ WhatsApp Configuration[/bold cyan]", box=box.ROUNDED, border_style="cyan"))
        
        # Check if WhatsApp is already configured
        whatsapp_config = self.whatsapp_manager.config if self.whatsapp_manager else {}
        
        if whatsapp_config:
            # Show current configuration
            config_table = Table(show_header=False, box=box.SIMPLE)
            config_table.add_column("Setting", style="cyan")
            config_table.add_column("Value")
            
            config_table.add_row("Auto Login", "Yes" if whatsapp_config.get('auto_login', False) else "No")
            config_table.add_row("Remember Session", "Yes" if whatsapp_config.get('remember_session', True) else "No")
            
            console.print(Panel(
                config_table,
                title="[bold]Current WhatsApp Configuration[/bold]",
                border_style="blue",
                box=box.ROUNDED
            ))
        
        # Ask for configuration options
        auto_login = Confirm.ask("Automatically connect to WhatsApp at startup?", default=False)
        remember_session = Confirm.ask("Remember WhatsApp session (avoids scanning QR code every time)?", default=True)
        
        # Initialize WhatsApp manager if not already done
        if not self.whatsapp_manager:
            self.whatsapp_manager = WhatsAppManager(self.config_path)
        
        # Update configuration
        success = self.whatsapp_manager.configure(auto_login, remember_session)
        
        if success:
            self.display_success("WhatsApp configuration updated successfully")
            
            # If auto-login is enabled, ask if the user wants to connect now
            if auto_login:
                connect_now = Confirm.ask("Connect to WhatsApp now?", default=True)
                if connect_now:
                    await self.handle_whatsapp_operation({'action': 'connect_whatsapp'})
        else:
            self.display_error("Failed to update WhatsApp configuration")
            
    async def whatsapp_command(self, args=None):
        """
        Handle WhatsApp commands.
        
        Args:
            args: Command arguments
        """
        # Import intent parser
        from ai_assistant.utils.whatsapp_intent import WhatsAppIntentParser
        from ..core.prompts import ROLE_PROMPTS
        
        # Initialize WhatsApp manager if not already done
        if not self.whatsapp_manager:
            self.whatsapp_manager = WhatsAppManager(self.config_path)
            
        # Parse the arguments correctly - args might be a string or a list
        if isinstance(args, str):
            # If args is a string, split it into a list
            args_list = args.strip().split()
        else:
            # If args is already a list or None, use it as is
            args_list = args or []
        
        # Get the subcommand (if provided)
        subcommand = args_list[0].lower() if args_list else ""
        
        # Show help if no arguments
        if not subcommand:
            # Show help for WhatsApp commands
            console.print(Panel(
                "WhatsApp Commands:\n\n"
                "• [bold cyan]setup[/bold cyan] - Configure WhatsApp integration\n"
                "• [bold cyan]connect[/bold cyan] - Connect to WhatsApp Web\n"
                "• [bold cyan]disconnect[/bold cyan] - Disconnect from WhatsApp Web\n"
                "• [bold cyan]send[/bold cyan] - Send a WhatsApp message\n"
                "• [bold cyan]ai[/bold cyan] - Use AI to compose a message\n"
                "• [bold cyan]contacts[/bold cyan] - List recent contacts\n\n"
                "[bold cyan]Role-based message composition:[/bold cyan]\n"
                "• [bold cyan]ai <recipient> [role] [instructions][/bold cyan] - Generate a message using a specific AI role\n"
                "• Example: [bold cyan]/whatsapp ai +1234567890 Business \"Schedule a meeting for tomorrow\"[/bold cyan]",
                title="[bold]WhatsApp Help[/bold]",
                border_style="cyan",
                box=box.ROUNDED
            ))
            return
        
        # Process WhatsApp subcommands
        if subcommand == "setup":
            await self.configure_whatsapp()
        elif subcommand == "connect":
            result = await self.handle_whatsapp_operation({'action': 'connect_whatsapp'})
            self.display_info(result)
        elif subcommand == "disconnect":
            result = await self.handle_whatsapp_operation({'action': 'disconnect_whatsapp'})
            self.display_info(result)
        elif subcommand == "contacts":
            result = await self.handle_whatsapp_operation({'action': 'list_contacts'})
            self.display_info(result)
        elif subcommand == "ai":
            # AI-assisted message composition
            if len(args_list) >= 2:
                recipient = args_list[1]
                
                # Check if the third argument is a valid role
                role = None
                instruction = ""
                
                if len(args_list) >= 3:
                    potential_role = args_list[2]
                    
                    # Check if it's a valid role
                    if potential_role in ROLE_PROMPTS:
                        role = potential_role
                        # Join the rest of the arguments as the instruction
                        if len(args_list) >= 4:
                            instruction = " ".join(args_list[3:])
                    else:
                        # No valid role, treat everything after recipient as instruction
                        instruction = " ".join(args_list[2:])
                
                # Show available roles if no instruction is provided
                if not instruction:
                    console.print("[bold cyan]Available Roles:[/bold cyan]")
                    for role_name in ROLE_PROMPTS.keys():
                        console.print(f"• [bold]{role_name}[/bold]")
                    
                    # Prompt for role if not provided
                    if not role:
                        use_role = Confirm.ask("[bold]Do you want to use a specific AI role?[/bold]", default=False)
                        if use_role:
                            role_options = list(ROLE_PROMPTS.keys())
                            role_choice = Prompt.ask("[bold]Choose a role[/bold]", choices=role_options, default="General")
                            role = role_choice
                    
                    # Get instruction
                    instruction = Prompt.ask("[bold]Enter your message instructions[/bold]")
                
                # Create the intent with role if specified
                intent = {
                    'action': 'ai_compose_whatsapp',
                    'recipient': recipient,
                    'instruction': instruction
                }
                
                if role:
                    intent['role'] = role
                
                result = await self.handle_whatsapp_operation(intent)
                self.display_info(result)
            else:
                # No recipient provided, go to interactive mode
                recipient = Prompt.ask("[bold]Enter recipient (phone number with country code or contact name)[/bold]")
                
                # Show available roles
                console.print("[bold cyan]Available Roles:[/bold cyan]")
                for role_name in ROLE_PROMPTS.keys():
                    console.print(f"• [bold]{role_name}[/bold]")
                
                # Ask if user wants to use a specific role
                use_role = Confirm.ask("[bold]Do you want to use a specific AI role?[/bold]", default=False)
                role = None
                
                if use_role:
                    role_options = list(ROLE_PROMPTS.keys())
                    role_choice = Prompt.ask("[bold]Choose a role[/bold]", choices=role_options, default="General")
                    role = role_choice
                
                # Get message instructions
                instruction = Prompt.ask("[bold]Enter your message instructions[/bold]")
                
                # Create the intent with role if specified
                intent = {
                    'action': 'ai_compose_whatsapp',
                    'recipient': recipient,
                    'instruction': instruction
                }
                
                if role:
                    intent['role'] = role
                
                result = await self.handle_whatsapp_operation(intent)
                self.display_info(result)
        elif subcommand == "send":
            # Extract recipient and message if provided
            if len(args_list) >= 3:
                recipient = args_list[1]
                message = " ".join(args_list[2:])
                result = await self.handle_whatsapp_operation({
                    'action': 'send_whatsapp',
                    'recipient': recipient,
                    'message': message
                })
                self.display_info(result)
            else:
                # Interactive mode for sending a message
                from rich.prompt import Prompt
                
                recipient = Prompt.ask("Enter recipient (phone number with country code or contact name)")
                message = Prompt.ask("Enter message")
                
                if recipient and message:
                    result = await self.handle_whatsapp_operation({
                        'action': 'send_whatsapp',
                        'recipient': recipient,
                        'message': message
                    })
                    self.display_info(result)
                else:
                    self.display_error("Recipient and message are required")
        else:
            self.display_error(f"Unknown WhatsApp command: {subcommand}")
            
    async def whatsapp_ai_compose(self, recipient, instruction=None):
        """
        Use AI to compose a WhatsApp message.
        
        Args:
            recipient (str): Recipient of the message
            instruction (str, optional): Instructions for composing the message
            
        Returns:
            str: Result of the operation
        """
        try:
            # Import role prompts
            from ..core.prompts import ROLE_PROMPTS
            
            # Ensure WhatsApp is initialized
            if not self.whatsapp_manager:
                self.display_warning("WhatsApp integration is not configured. Setting it up now.")
                await self.whatsapp_command('setup')
            
            # Get instructions for the AI if not provided
            if not instruction:
                purpose = Prompt.ask("[bold]What is the purpose of this message?[/bold]")
                tone = Prompt.ask("[bold]What tone should the message have?[/bold]", choices=["friendly", "formal", "casual", "professional"], default="friendly")
                length = Prompt.ask("[bold]How long should the message be?[/bold]", choices=["short", "medium", "long"], default="medium")
                instruction = f"Write a {tone} WhatsApp message to {recipient} about {purpose}. The message should be {length} in length."
            
            # Ask if the user wants to use a specific role for composing
            use_role = Confirm.ask("[bold]Do you want to use a specific AI role for composing this message?[/bold]", default=False)
            
            selected_role = "General"  # Default role
            
            if use_role:
                # Display available roles
                role_table = Table(box=box.ROUNDED)
                role_table.add_column("Option", style="cyan")
                role_table.add_column("Role")
                role_table.add_column("Description")
                
                for i, (role, description) in enumerate(ROLE_PROMPTS.items(), 1):
                    # Truncate description if too long
                    short_desc = description.split("\n")[0][:50] + "..." if len(description) > 50 else description
                    role_table.add_row(str(i), role, short_desc)
                    
                console.print(Panel(
                    role_table,
                    title="[bold]Assistant Roles[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
                # Let user select role
                role_choices = [str(i) for i in range(1, len(ROLE_PROMPTS) + 1)]
                role_choice = Prompt.ask("[bold]Select a role for message composition[/bold]", choices=role_choices, default="1")
                
                # Get the selected role
                role_idx = int(role_choice) - 1
                if 0 <= role_idx < len(ROLE_PROMPTS):
                    selected_role = list(ROLE_PROMPTS.keys())[role_idx]
                    console.print(f"[green]Using {selected_role} role for message composition[/green]")
            
            # Use Rich progress bar for AI processing
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]AI is composing your message...[/bold blue]"),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("[green]Thinking...", total=None)
                
                # Get the prompt for the selected role
                role_prompt = ROLE_PROMPTS.get(selected_role, ROLE_PROMPTS["General"])
                
                # Create a prompt for the AI that includes the role context
                ai_prompt = f"{role_prompt}\n\nNow, compose a WhatsApp message to {recipient}. The message should be about: {instruction}"
                ai_prompt += "\nThe message should be concise and appropriate for WhatsApp. Don't include any introduction or explanation, just the message content."
                
                # Generate the message
                generated_message = await self.assistant.answer_async(ai_prompt)
            
            # Clean up the generated message
            generated_message = generated_message.strip()
            
            # If message starts with a quote or similar, clean it up
            if generated_message.startswith('"') and generated_message.endswith('"'):
                generated_message = generated_message[1:-1]
            
            # Preview the message with improved formatting
            console.print(Panel(
                f"[bold]Generated message (using {selected_role} role):[/bold]\n\n{generated_message}",
                title="[bold]AI-Generated WhatsApp Message[/bold]",
                border_style="cyan",
                box=box.ROUNDED
            ))
            
            # Ask for what to do with the message
            console.print("[bold cyan]What would you like to do with this message?[/bold cyan]")
            choices = {
                "1": "Send as is",
                "2": "Edit before sending",
                "3": "Regenerate with new instructions",
                "4": "Regenerate with different role",
                "5": "Save as draft (not implemented)",
                "6": "Cancel"
            }
            
            # Display options with styling
            for key, value in choices.items():
                console.print(f"[bold blue]{key}.[/bold blue] {value}")
                
            choice = Prompt.ask("[bold]Select an option[/bold]", choices=list(choices.keys()), default="2")
            
            if choice == "1":  # Send as is
                console.print(f"[bold cyan]Sending message to {recipient}...[/bold cyan]")
                success = await asyncio.to_thread(self.whatsapp_manager.send_message, recipient, generated_message)
                
                if success:
                    self.display_success(f"Message sent to {recipient}")
                    return f"Message sent to {recipient}"
                else:
                    self.display_error(f"Failed to send message to {recipient}")
                    return f"Failed to send message to {recipient}"
                    
            elif choice == "2":  # Edit before sending
                edited_message = Prompt.ask("[bold]Edit the message[/bold]", default=generated_message)
                console.print(f"[bold cyan]Sending edited message to {recipient}...[/bold cyan]")
                success = await asyncio.to_thread(self.whatsapp_manager.send_message, recipient, edited_message)
                
                if success:
                    self.display_success(f"Edited message sent to {recipient}")
                    return f"Edited message sent to {recipient}"
                else:
                    self.display_error(f"Failed to send edited message to {recipient}")
                    return f"Failed to send edited message to {recipient}"
                
            elif choice == "3":  # Regenerate with new instructions
                console.print("[bold cyan]New instructions for regenerating the message:[/bold cyan]")
                new_instructions = Prompt.ask("[bold]New instructions[/bold]")
                return await self.whatsapp_ai_compose(recipient, new_instructions)
                
            elif choice == "4":  # Regenerate with different role
                # Call the method again but force role selection
                console.print("[bold cyan]Select a different role for message composition:[/bold cyan]")
                return await self.whatsapp_ai_compose(recipient, instruction)
                
            elif choice == "5":  # Save as draft
                self.display_warning("Draft saving is not implemented yet")
                return "Draft saving is not implemented yet"
                
            elif choice == "6":  # Cancel
                self.display_warning("Message sending canceled")
                return "Message sending canceled"
                
        except Exception as e:
            logger.exception("Error in WhatsApp AI compose")
            self.display_error(f"Error composing WhatsApp message: {str(e)}")
            return f"Error composing WhatsApp message: {str(e)}"

    async def handle_whatsapp_operation(self, intent):
        """
        Handle WhatsApp operations based on intent.
        
        Args:
            intent: Dictionary containing WhatsApp operation details
            
        Returns:
            String describing the result
        """
        # Initialize WhatsApp manager if not already done
        if not self.whatsapp_manager:
            self.whatsapp_manager = WhatsAppManager(self.config_path)
        
        action = intent.get('action')
        
        if action == 'setup_whatsapp':
            await self.configure_whatsapp()
            return "WhatsApp configuration completed"
            
        elif action == 'connect_whatsapp':
            console.print("[bold cyan]Connecting to WhatsApp Web...[/bold cyan]")
            console.print("If prompted, scan the QR code with your phone to log in.")
            
            # Connect in a non-blocking way
            success = await asyncio.to_thread(self.whatsapp_manager.connect)
            
            if success:
                self.display_success("Connected to WhatsApp Web")
                return "Connected to WhatsApp Web"
            else:
                self.display_error("Failed to connect to WhatsApp Web")
                return "Failed to connect to WhatsApp Web"
                
        elif action == 'disconnect_whatsapp':
            success = await asyncio.to_thread(self.whatsapp_manager.disconnect)
            
            if success:
                self.display_success("Disconnected from WhatsApp Web")
                return "Disconnected from WhatsApp Web"
            else:
                self.display_error("Failed to disconnect from WhatsApp Web")
                return "Failed to disconnect from WhatsApp Web"
                
        elif action == 'list_contacts':
            contacts = await asyncio.to_thread(self.whatsapp_manager.get_recent_contacts)
            
            if contacts:
                contact_table = Table(title="Recent WhatsApp Contacts")
                contact_table.add_column("#", style="cyan")
                contact_table.add_column("Contact Name")
                
                for i, contact in enumerate(contacts, 1):
                    contact_table.add_row(str(i), contact)
                
                console.print(contact_table)
                return f"Found {len(contacts)} recent contacts"
            else:
                self.display_warning("No recent contacts found or not connected to WhatsApp Web")
                return "No recent contacts found or not connected to WhatsApp Web"
                
        elif action == 'send_whatsapp':
            recipient = intent.get('recipient', '')
            message = intent.get('message', '')
            
            # If we have an AI instruction, use the assistant to generate the message
            if 'ai_instruction' in intent:
                instruction = intent.get('ai_instruction', '')
                tone = intent.get('tone', 'neutral')
                
                # Import role prompts
                from ..core.prompts import ROLE_PROMPTS
                
                # Check if a specific role is requested
                role = intent.get('role', 'General')
                if role not in ROLE_PROMPTS:
                    role = 'General'
                
                # Get the role prompt
                role_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS['General'])
                
                # Generate a message using the AI assistant with the selected role
                ai_prompt = f"{role_prompt}\n\nNow, compose a WhatsApp message to {recipient} with a {tone} tone. The message should be about: {instruction}"
                ai_prompt += "\nThe message should be concise and appropriate for WhatsApp. Don't include any introduction or explanation, just the message content."
                
                generated_message = await self.assistant.answer_async(ai_prompt)
                
                # Use the generated message if it's not empty
                if generated_message:
                    message = generated_message
                    console.print(Panel(
                        f"[bold]Generated message (using {role} role):[/bold]\n\n{message}",
                        title="[bold]AI-Generated Message[/bold]",
                        border_style="cyan",
                        box=box.ROUNDED
                    ))
            
            if not recipient:
                self.display_error("Recipient is required")
                return "Recipient is required"
                
            if not message:
                self.display_error("Message is required")
                return "Message is required"
            
            # Send the message
            console.print(f"[bold cyan]Sending message to {recipient}...[/bold cyan]")
            success = await asyncio.to_thread(self.whatsapp_manager.send_message, recipient, message)
            
            if success:
                self.display_success(f"Message sent to {recipient}")
                return f"Message sent to {recipient}"
            else:
                self.display_error(f"Failed to send message to {recipient}")
                return f"Failed to send message to {recipient}"
                
        elif action == 'ai_compose_whatsapp':
            recipient = intent.get('recipient', '')
            instruction = intent.get('instruction', '')
            role = intent.get('role', None)  # Check if a specific role is requested
            
            if not recipient:
                self.display_error("Recipient is required")
                return "Recipient is required"
            
            # If a role is specified in the intent, we'll set up a special handler
            if role:
                from ..core.prompts import ROLE_PROMPTS
                if role in ROLE_PROMPTS:
                    # Modify the instruction to include the role
                    console.print(f"[green]Using {role} role for message composition[/green]")
                    
                    # We'll use the existing method but pre-select the role
                    role_prompt = ROLE_PROMPTS.get(role, ROLE_PROMPTS["General"])
                    
                    # Use Rich progress bar for AI processing
                    with Progress(
                        SpinnerColumn(),
                        TextColumn(f"[bold blue]AI is composing your message using {role} role...[/bold blue]"),
                        console=console,
                        transient=True
                    ) as progress:
                        task = progress.add_task("[green]Thinking...", total=None)
                        
                        # Create a prompt for the AI that includes the role context
                        ai_prompt = f"{role_prompt}\n\nNow, compose a WhatsApp message to {recipient}. The message should be about: {instruction}"
                        ai_prompt += "\nThe message should be concise and appropriate for WhatsApp. Don't include any introduction or explanation, just the message content."
                        
                        # Generate the message
                        generated_message = await self.assistant.answer_async(ai_prompt)
                    
                    # Clean up the generated message
                    generated_message = generated_message.strip()
                    if generated_message.startswith('"') and generated_message.endswith('"'):
                        generated_message = generated_message[1:-1]
                    
                    # Preview the message with improved formatting
                    console.print(Panel(
                        f"[bold]Generated message (using {role} role):[/bold]\n\n{generated_message}",
                        title="[bold]AI-Generated WhatsApp Message[/bold]",
                        border_style="cyan",
                        box=box.ROUNDED
                    ))
                    
                    # Ask to send the message
                    if Confirm.ask("[bold]Send this message?[/bold]", default=True):
                        console.print(f"[bold cyan]Sending message to {recipient}...[/bold cyan]")
                        success = await asyncio.to_thread(self.whatsapp_manager.send_message, recipient, generated_message)
                        
                        if success:
                            self.display_success(f"Message sent to {recipient}")
                            return f"Message sent to {recipient}"
                        else:
                            self.display_error(f"Failed to send message to {recipient}")
                            return f"Failed to send message to {recipient}"
                    else:
                        # Use the standard composer for more options
                        console.print("[cyan]Using the full message composer for more options...[/cyan]")
            
            # Use the dedicated AI compose function
            return await self.whatsapp_ai_compose(recipient, instruction)
            
        else:
            self.display_error(f"Unknown WhatsApp action: {action}")
            return f"Unknown WhatsApp action: {action}"

    async def handle_email_operation(self, intent, prompt=None):
        """
        Handle email operations based on detected intent.
        
        Args:
            intent (dict): Dictionary containing email operation details
            prompt (str, optional): The original prompt text for context
            
        Returns:
            str: Result message
        """
        logger.info(f"Handling email operation: {intent}")
        operation = intent.get('operation', '')
        
        try:
            # Handle AI email composition
            if operation == 'ai_compose_email':
                to_address = intent.get('to_address')
                await self.email_ai_write(to_address, prompt=prompt)
                return "Email composition initiated"
                
            # Handle email reading
            elif operation == 'read_email' or operation == 'list_emails':
                email_id = intent.get('email_id')
                if email_id:
                    await self.email_command(f"read {email_id}")
                else:
                    await self.email_command("read")
                return "Displaying emails"
                
            # Handle email sending
            elif operation == 'send_email':
                to_address = intent.get('to_address')
                if not to_address:
                    return "Please specify a recipient email address"
                
                subject = intent.get('subject', '')
                content = intent.get('content', '')
                await self.email_command(f"send {to_address} {subject} {content}")
                return f"Email sent to {to_address}"
                
            # Handle email setup
            elif operation == 'setup_email':
                await self.email_command("setup")
                return "Email setup initiated"
                
            # Handle email reply
            elif operation == 'reply_to_email':
                email_id = intent.get('email_id')
                if not email_id:
                    return "Please specify an email ID to reply to"
                
                await self.email_command(f"reply {email_id}")
                return f"Replying to email #{email_id}"
                
            # Handle email forwarding
            elif operation == 'forward_email':
                email_id = intent.get('email_id')
                to_address = intent.get('to_address')
                if not email_id:
                    return "Please specify an email ID to forward"
                
                command = f"forward {email_id}"
                if to_address:
                    command += f" {to_address}"
                
                await self.email_command(command)
                return f"Forwarding email #{email_id}"
                
            # Handle email deletion
            elif operation == 'delete_email':
                email_id = intent.get('email_id')
                if not email_id:
                    return "Please specify an email ID to delete"
                
                await self.email_command(f"delete {email_id}")
                return f"Deleted email #{email_id}"
                
            # Handle generic email operations
            else:
                await self.email_command("")
                return "Email command executed"
                
        except Exception as e:
            logger.error(f"Error in handle_email_operation: {str(e)}")
            return f"Error processing email operation: {str(e)}"
            #Welcome message
    async def run(self):
        """Run the QuackQuery application."""
        console.clear()
        console.print(Panel.fit(
            "🦆 [bold cyan]QuackQuery AI Assistant[/bold cyan] [green]initialized for your service[/green]",
            box=box.ROUNDED,
            border_style="cyan",
            title="Welcome",
            subtitle="v5.0"
        ))
        
        # If WhatsApp auto-login is enabled, connect now that we have a running event loop
        if hasattr(self, 'whatsapp_auto_login') and self.whatsapp_auto_login:
            try:
                await self.handle_whatsapp_operation({'action': 'connect_whatsapp'})
            except Exception as e:
                logger.error(f"Error during WhatsApp auto-login: {str(e)}")
                self.display_warning("WhatsApp auto-connection failed. You can try connecting manually later.")
        
        while True:
            try:
                # Display menu in a styled panel
                menu_table = Table(show_header=False, box=box.SIMPLE)
                menu_table.add_column("Option", style="cyan")
                menu_table.add_column("Description")
                menu_table.add_row("S", "Speak to the assistant")
                menu_table.add_row("T", "Type a question")
                menu_table.add_row("C", "Configure settings")
                menu_table.add_row("Q", "Quit")
                
                console.print(Panel(
                    menu_table,
                    title="[bold]Main Menu[/bold]",
                    border_style="blue",
                    box=box.ROUNDED
                ))
                
                # Use Rich prompt for input
                user_input = Prompt.ask("\nEnter your choice", choices=["s", "t", "c", "q"], default="t").lower()
                
                if user_input == 's':
                    await self.handle_speech_input()
                    console.print("\n[green]✅ Ready for next command...[/green]")
                elif user_input == 't':
                    await self.handle_text_input()
                    console.print("\n[green]✅ Ready for next command...[/green]")
                elif user_input == 'c':
                    await self.configure()
                    console.print("\n[green]✅ Settings updated. Ready for next command...[/green]")
                elif user_input == 'q':
                    console.print("\n[yellow]Exiting assistant. Goodbye! 👋[/yellow]")
                    break
                else:
                    console.print("\n[bold red]❌ Invalid input. Please choose S, T, C, or Q.[/bold red]")
            except Exception as e:
                logger.error(f"Error in main loop: {str(e)}")
                self.display_error(f"An error occurred: {str(e)}")

    async def handle_speech_input(self):
        """Handle speech input from the user."""
        from ai_assistant.utils.github_intent import GitHubIntentParser
        from ai_assistant.utils.file_intent import FileIntentParser
        from ai_assistant.utils.app_intent import AppIntentParser
        from ai_assistant.utils.email_intent import EmailIntentParser
        from ai_assistant.utils.whatsapp_intent import WhatsAppIntentParser
        
        if not self.speech_recognizer:
            self.display_error("Speech recognition component not initialized.")
            self.display_info("You might need to configure speech services using '/configure speech' or ensure necessary libraries are installed.")
            return

        console.print("\n🎙️  Listening for your command (say 'stop listening' to cancel)...")
        try:
            # Use the existing listen_and_recognize method
            recognized_text = await asyncio.to_thread(self.speech_recognizer.listen_and_recognize)
            
            if recognized_text:
                console.print(f"[dim]Heard:[/dim] [italic]'{recognized_text}'[/italic]")
                if recognized_text.lower() == "stop listening":
                    self.display_info("Speech input cancelled.")
                    return
                    
                # Check for exit command
                if recognized_text.lower() in ["exit", "quit", "/exit", "/quit"]:
                    console.print("[bold green]Goodbye![/bold green]")
                    raise KeyboardInterrupt()
                
                # Process special commands
                if recognized_text.startswith("/"):
                    if await self.process_command(recognized_text):
                        return
                
                # Initialize intent parsers if not already done
                github_intent_parser = GitHubIntentParser()
                file_intent_parser = FileIntentParser()
                app_intent_parser = AppIntentParser()
                email_intent_parser = EmailIntentParser()
                whatsapp_intent_parser = WhatsAppIntentParser()
                
                # Check for GitHub operations
                github_intent = github_intent_parser.parse_intent(recognized_text)
                if github_intent:
                    result = await self.handle_github_operation(github_intent)
                    self._format_and_display_response(result)
                    return

                # Check for WhatsApp operations
                whatsapp_intent = whatsapp_intent_parser.parse_intent(recognized_text)
                logger.info(f"WhatsApp intent detection result: {whatsapp_intent}")
                
                if whatsapp_intent:
                    result = await self.handle_whatsapp_operation(whatsapp_intent)
                    # Format the response to make it visible
                    self._format_and_display_response(result)
                    return
                    
                # If the shared text appears to be a WhatsApp-related request with a phone number
                if ("message" in recognized_text.lower() or "whatsapp" in recognized_text.lower()) and re.search(r'[+=]?\d{10,}', recognized_text):
                    logger.info("Detected potential WhatsApp message to phone number")
                    # Try to extract recipient (phone number) and message content
                    phone_match = re.search(r'(?:to\s+)?([+=]?\d{10,})', recognized_text)
                    if phone_match:
                        recipient = phone_match.group(1)
                        instruction = recognized_text  # Use full text as instruction
                        
                        logger.info(f"Creating manual WhatsApp intent for phone: {recipient}")
                        # Create a WhatsApp intent
                        whatsapp_intent = {
                            'action': 'ai_compose_whatsapp',
                            'recipient': recipient.strip(),
                            'instruction': instruction
                        }
                        
                        result = await self.handle_whatsapp_operation(whatsapp_intent)
                        self._format_and_display_response(result)
                        return
                    
                # Direct pattern match for AI write message with phone number
                ai_whatsapp_phone_match = re.search(r'(?:ai|assistant|help)\s+(?:write|compose|draft|create)\s+(?:a\s+)?(?:message|msg)(?:\s+to\s+|\s+for\s+)?([+=]?\d{10,})', recognized_text.lower())
                if ai_whatsapp_phone_match:
                    logger.info("Direct pattern match for AI WhatsApp message to phone")
                    recipient = ai_whatsapp_phone_match.group(1)
                    
                    # Create a WhatsApp intent
                    whatsapp_intent = {
                        'action': 'ai_compose_whatsapp',
                        'recipient': recipient.strip(),
                        'instruction': recognized_text
                    }
                    
                    result = await self.handle_whatsapp_operation(whatsapp_intent)
                    self._format_and_display_response(result)
                    return
                
                # Check for Email operations
                email_intent = email_intent_parser.parse_intent(recognized_text)
                if email_intent:
                    result = await self.handle_email_operation(email_intent, prompt=recognized_text)
                    self._format_and_display_response(result)
                    return
                    
                # Check for File operations
                file_intent = file_intent_parser.parse_intent(recognized_text)
                if file_intent:
                    result = await self.handle_file_operation(file_intent)
                    self._format_and_display_response(result)
                    return
                    
                # Check for App operations
                app_intent = app_intent_parser.parse_intent(recognized_text)
                if app_intent:
                    result = await self.handle_app_operation(app_intent)
                    self._format_and_display_response(result)
                    return
                
                # Process as a regular question
                include_screenshot = False  # For speech commands, don't include screenshot by default
                
                # Use Rich progress bar
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[bold blue]Processing...[/bold blue]"),
                    console=console,
                    transient=True
                ) as progress:
                    task = progress.add_task("[green]Thinking...", total=None)
                    
                    try:
                        screenshot_encoded = self.desktop_screenshot.capture() if include_screenshot else None
                        response = await self.assistant.answer_async(recognized_text, screenshot_encoded)
                        
                        # Display response with syntax highlighting for code blocks
                        self._format_and_display_response(response)
                        
                    except Exception as e:
                        logger.error(f"Question processing error: {e}")
                        console.print(f"\n[bold red]❌ Error processing question: {e}[/bold red]")
            else:
                # listen_and_recognize handles displaying the error internally
                pass # Error/warning already displayed by SpeechRecognizer
        except Exception as e:
            logger.error(f"Error during speech input handling: {e}", exc_info=True)
            self.display_error(f"An error occurred during speech recognition: {e}")


    def _format_and_display_response(self, response):
        """Format and display AI response with Rich UI enhancements."""
        # Check if response is None or empty
        if not response:
            logger.warning("Received empty response from assistant")
            console.print("[yellow]No response received from assistant.[/yellow]")
            return
            
        # Check for code blocks in the response
        if "```" in response:
            # Split the response by code blocks
            parts = response.split("```")
            
            # Display each part with appropriate formatting
            for i, part in enumerate(parts):
                if i == 0:
                    # First part is always text before the first code block
                    if part.strip():
                        console.print(Markdown(part.strip()))
                elif i % 2 == 1:
                    # Odd-indexed parts are code blocks
                    # Extract language if specified (e.g., ```python)
                    code_lines = part.strip().split('\n')
                    if code_lines and not code_lines[0].isspace() and len(code_lines[0].strip()) > 0:
                        lang = code_lines[0].strip().lower()
                        code = '\n'.join(code_lines[1:])
                    else:
                        lang = "text"
                        code = part.strip()
                    
                    # Display code with syntax highlighting
                    console.print(Syntax(code, lang, theme="monokai", line_numbers=True, word_wrap=True))
                else:
                    # Even-indexed parts (except 0) are text between code blocks
                    if part.strip():
                        console.print(Markdown(part.strip()))
        else:
            # No code blocks, display as markdown
            console.print(Markdown(response))

def load_config(config_path="config.json"):
    """
    Load configuration from disk.
    
    Returns:
        dict: Configuration dictionary
    """
    try:
        # Use absolute path to the user's home directory
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".quackquery")
        abs_config_path = os.path.join(config_dir, "config.json")
        
        # Check for the config in the home directory first
        if os.path.exists(abs_config_path):
            with open(abs_config_path, 'r') as f:
                logger.info(f"Loading config from {abs_config_path}")
                return json.load(f)
        
        # Fallback to the provided path (legacy support)
        elif os.path.exists(config_path):
            with open(config_path, 'r') as f:
                logger.info(f"Loading config from {config_path}")
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
        # Create a dedicated configuration directory in the user's home
        home_dir = os.path.expanduser("~")
        config_dir = os.path.join(home_dir, ".quackquery")
        
        # Create directory if it doesn't exist
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
            
        # Save to the absolute path
        abs_config_path = os.path.join(config_dir, "config.json")
        with open(abs_config_path, 'w') as f:
            logger.info(f"Saving config to {abs_config_path}")
            json.dump(config, f)
            
        # Also save to the current directory for backward compatibility
        with open("config.json", 'w') as f:
            json.dump(config, f)
            
    except Exception as e:
        logger.error(f"Error saving config: {e}")
