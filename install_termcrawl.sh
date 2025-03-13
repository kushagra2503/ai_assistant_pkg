#!/bin/bash

echo "==================================="
echo "TermCrawl AI Assistant Installer"
echo "==================================="
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed or not in PATH."
    echo "Please install Python 3.7 or higher."
    echo "On Ubuntu/Debian: sudo apt install python3 python3-pip"
    echo "On macOS: brew install python3"
    echo
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 7 ]); then
    echo "Python 3.7 or higher is required."
    echo "Current version: $PYTHON_VERSION"
    echo
    exit 1
fi

echo "Python $PYTHON_VERSION detected."
echo

# Install or upgrade pip
echo "Ensuring pip is up to date..."
python3 -m pip install --upgrade pip
echo

# Install TermCrawl AI Assistant
echo "Installing TermCrawl AI Assistant..."
python3 -m pip install git+https://github.com/kushagra2503/ai_assistant_pkg.git

if [ $? -ne 0 ]; then
    echo
    echo "Installation failed. Please check the error messages above."
    exit 1
fi

echo
echo "==================================="
echo "Installation successful!"
echo
echo "To run TermCrawl AI Assistant, open a terminal and type:"
echo "ai-assistant"
echo
echo "Before running, make sure you have set up your API keys."
echo "See the INSTALLATION.md file for details on setting up API keys."
echo "==================================="
echo

# Ask if user wants to set up API keys now
read -p "Do you want to set up API keys now? (y/n): " SETUP_KEYS

if [[ $SETUP_KEYS == "y" || $SETUP_KEYS == "Y" ]]; then
    echo
    echo "Setting up API keys..."
    echo
    
    read -p "Enter your Google Gemini API key (leave blank to skip): " GEMINI_KEY
    read -p "Enter your OpenAI API key (leave blank to skip): " OPENAI_KEY
    
    echo
    echo "Creating .env file..."
    
    # Create or overwrite .env file
    > .env
    
    # Add keys if provided
    if [ ! -z "$GEMINI_KEY" ]; then
        echo "GEMINI_API_KEY=$GEMINI_KEY" >> .env
    fi
    
    if [ ! -z "$OPENAI_KEY" ]; then
        echo "OPENAI_API_KEY=$OPENAI_KEY" >> .env
    fi
    
    echo "API keys saved to .env file."
    echo
    
    read -p "Would you like to run TermCrawl AI Assistant now? (y/n): " RUN_NOW
    
    if [[ $RUN_NOW == "y" || $RUN_NOW == "Y" ]]; then
        echo
        echo "Starting TermCrawl AI Assistant..."
        ai-assistant
    else
        echo
        echo "You can run TermCrawl AI Assistant later by typing 'ai-assistant' in a terminal."
    fi
else
    echo
    echo "You can set up API keys later. See INSTALLATION.md for instructions."
fi

echo
