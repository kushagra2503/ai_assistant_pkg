from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="QuackQuery",
    version="0.4.1",
    author="Kushagra",
    author_email="radhikayash2@gmail.com",
    description="A versatile AI assistant with multi-model support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kushagra2503/ai_assistant",
    project_urls={
        "Bug Tracker": "https://github.com/kushagra2503/ai_assistant/issues",
        "Documentation": "https://github.com/kushagra2503/ai_assistant#readme",
        "Source Code": "https://github.com/kushagra2503/ai_assistant",
    },
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "Topic :: Utilities",
    ],
    python_requires=">=3.7",
    install_requires=[
        "google-generativeai",
        "openai",
        "SpeechRecognition",
        "pillow",
        "opencv-python",
        "python-dotenv>=0.19.2",
        "gtts",
        "pytesseract",
        "requests",
        "send2trash",
        "pywin32; platform_system == 'Windows'",
        "pyaudio",
        "rich",
        "email-validator>=2.0.0"  # For email validation
    ],
    entry_points={
        "console_scripts": [
            "quackquery=ai_assistant.cli:main",
        ],
    },
)
