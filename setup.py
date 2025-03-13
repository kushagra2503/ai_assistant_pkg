from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai_assistant",
    version="0.1.0",
    author="AI Assistant Developer",
    author_email="example@example.com",
    description="A versatile AI assistant with multi-model support",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai_assistant",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=[
        "google-generativeai",
        "openai",
        "SpeechRecognition",
        "pillow",
        "opencv-python",
        "python-dotenv",
        "google-api-python-client",
        "google-auth-httplib2",
        "google-auth-oauthlib",
        "python-dateutil",
        "gtts",
        "beautifulsoup4",
    ],
    entry_points={
        "console_scripts": [
            "ai-assistant=ai_assistant.cli:main",
        ],
    },
)
