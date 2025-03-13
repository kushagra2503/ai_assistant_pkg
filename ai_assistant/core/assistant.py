"""
Core AI Assistant implementation with multi-model support.
"""

import os
import logging
import google.generativeai as genai
import openai
from ..core.prompts import ROLE_PROMPTS
from ..core.conversation import ConversationHistory

logger = logging.getLogger("ai_assistant")

class Assistant:
    """
    AI Assistant with multi-model support.
    
    Attributes:
        model_choice (str): The AI model to use (Gemini or OpenAI)
        api_key (str): API key for the selected model
        role (str): Assistant role that determines the system prompt
        prompt_prefix (str): System prompt based on the selected role
        history (ConversationHistory): Conversation history manager
    """
    
    def __init__(self, model_choice, api_key=None, role="General"):
        """
        Initialize the AI Assistant.
        
        Args:
            model_choice (str): The AI model to use (Gemini or OpenAI)
            api_key (str, optional): API key for the selected model. If None, will try to get from environment.
            role (str, optional): Assistant role that determines the system prompt. Defaults to "General".
        
        Raises:
            Exception: If the model initialization fails
        """
        self.model_choice = model_choice
        self.api_key = api_key or os.getenv(f"{model_choice.upper()}_API_KEY")
        self.role = role
        self.prompt_prefix = ROLE_PROMPTS.get(role, ROLE_PROMPTS["General"])
        self.history = ConversationHistory()
        
        try:
            if model_choice == "Gemini":
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-pro")
            elif model_choice == "OpenAI":
                openai.api_key = self.api_key
            logger.info(f"Initialized {model_choice} assistant with role: {role}")
        except Exception as e:
            logger.error(f"Failed to initialize {model_choice}: {e}")
            raise

    async def answer_async(self, prompt, image=None):
        """
        Get an answer from the AI model asynchronously.
        
        Args:
            prompt (str): User's query
            image (str, optional): Base64-encoded image data
            
        Returns:
            str: AI model's response
        """
        if not prompt:
            return "No input provided."

        # Include conversation history for context
        context = self.history.get_context()
        final_prompt = f"{self.prompt_prefix}\n\nConversation History:\n{context}\n\nUser Request: {prompt}\n"
        logger.info(f"User Query ({self.model_choice}): {prompt}")

        try:
            if self.model_choice == "Gemini":
                image_data = {
                    "mime_type": "image/jpeg",
                    "data": image
                } if image else None

                response = self.model.generate_content([final_prompt, image_data] if image else [final_prompt])
                response_text = response.text.strip() if response and response.text else "I couldn't understand."

            elif self.model_choice == "OpenAI":
                messages = [{"role": "user", "content": final_prompt}]
                
                # Add image if provided
                if image:
                    messages = [
                        {"role": "user", 
                         "content": [
                             {"type": "text", "text": final_prompt},
                             {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{image}"}}
                         ]}
                    ]
                
                response = openai.ChatCompletion.create(
                    model="gpt-4-turbo",
                    messages=messages
                )
                response_text = response["choices"][0]["message"]["content"].strip()

            else:
                response_text = "Invalid AI model selected. Please use Gemini or OpenAI."

            self.history.add(prompt, response_text)
            
            # Log the response
            logger.info(f"AI Response ({self.model_choice}): {response_text[:100]}...")
            
            return response_text
            
        except Exception as e:
            error_msg = f"Error with {self.model_choice}: {str(e)}"
            logger.error(error_msg)
            return f"I encountered an error: {error_msg}"
