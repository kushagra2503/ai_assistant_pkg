@echo off
echo ===================================
echo TermCrawl AI Assistant Installer
echo ===================================
echo.

:: Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python 3.7 or higher from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

:: Check Python version
for /f "tokens=2" %%a in ('python --version 2^>^&1') do set PYTHON_VERSION=%%a
for /f "tokens=1 delims=." %%a in ("%PYTHON_VERSION%") do set PYTHON_MAJOR=%%a
for /f "tokens=2 delims=." %%a in ("%PYTHON_VERSION%") do set PYTHON_MINOR=%%a

if %PYTHON_MAJOR% lss 3 (
    echo Python 3.7 or higher is required.
    echo Current version: %PYTHON_VERSION%
    echo.
    pause
    exit /b 1
)

if %PYTHON_MAJOR% equ 3 (
    if %PYTHON_MINOR% lss 7 (
        echo Python 3.7 or higher is required.
        echo Current version: %PYTHON_VERSION%
        echo.
        pause
        exit /b 1
    )
)

echo Python %PYTHON_VERSION% detected.
echo.

:: Install or upgrade pip
echo Ensuring pip is up to date...
python -m pip install --upgrade pip
echo.

:: Install TermCrawl AI Assistant
echo Installing TermCrawl AI Assistant...
pip install git+https://github.com/kushagra2503/ai_assistant_pkg.git
if %errorlevel% neq 0 (
    echo.
    echo Installation failed. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ===================================
echo Installation successful!
echo.
echo To run TermCrawl AI Assistant, open a command prompt and type:
echo ai-assistant
echo.
echo Before running, make sure you have set up your API keys.
echo See the INSTALLATION.md file for details on setting up API keys.
echo ===================================
echo.

:: Ask if user wants to set up API keys now
set /p SETUP_KEYS=Do you want to set up API keys now? (y/n): 

if /i "%SETUP_KEYS%"=="y" (
    echo.
    echo Setting up API keys...
    echo.
    
    set /p GEMINI_KEY=Enter your Google Gemini API key (leave blank to skip): 
    set /p OPENAI_KEY=Enter your OpenAI API key (leave blank to skip): 
    
    echo.
    echo Creating .env file...
    
    > .env (
        if not "%GEMINI_KEY%"=="" echo GEMINI_API_KEY=%GEMINI_KEY%
        if not "%OPENAI_KEY%"=="" echo OPENAI_API_KEY=%OPENAI_KEY%
    )
    
    echo API keys saved to .env file.
    echo.
    
    echo Would you like to run TermCrawl AI Assistant now?
    set /p RUN_NOW=Run now? (y/n): 
    
    if /i "%RUN_NOW%"=="y" (
        echo.
        echo Starting TermCrawl AI Assistant...
        ai-assistant
    ) else (
        echo.
        echo You can run TermCrawl AI Assistant later by typing 'ai-assistant' in a command prompt.
    )
) else (
    echo.
    echo You can set up API keys later. See INSTALLATION.md for instructions.
)

echo.
pause
