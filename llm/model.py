from exceptions import SecretsError
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from llm.prompt_templates import SYS_MSG, SYS_MSG_QUERY_EXPANDER
from config import get_settings, get_secrets
from exceptions import LLMAPIError, LLMError, LLMTimeoutError
import logging


logger = logging.getLogger(__name__)



class LLM:
    def __init__(self, model_name: str = None, thinking_budget: int = None):
        
        settings = get_settings()
        
        self.model_name = model_name if model_name is not None else settings.llm_model
        self.thinking_budget = thinking_budget if thinking_budget is not None else settings.llm_thinking_budget
        
        self.temperature = settings.llm_temperature
        self.timeout = settings.llm_timeout
        

        try:
            secrets = get_secrets()
            api_keys = secrets.get_api_key()  # returns plain string

            logger.info("API Key loaded successfully")
        except Exception as e:
            raise SecretsError(
                "Failed to load API Key",
                details={
                    "error": str(e)
                }
            ) from e

        try:
            logger.info(
                f"Loading LLM model: {self.model_name} | "
                f"Temperature: {self.temperature} | "
                f"Thinking budget: {self.thinking_budget} | "
                f"Timeout: {self.timeout}"
            )
            self.model = ChatAnthropic(
                model_name=self.model_name,
                api_key=api_keys,
                temperature=self.temperature,
                thinking = {
                    "type": "enabled",
                    "budget_tokens": self.thinking_budget
                },
                timeout=self.timeout
            )
            logger.info("LLM model loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise LLMError(
                "Failed to load LLM model",
                details={
                    "model_name": self.model_name,
                    "error": str(e)
                }
            ) from e
            
            
        

    def generate(self, prompt: str) -> str:
        messages = [
            SystemMessage(content=SYS_MSG),
            HumanMessage(content=prompt)
        ]
        try:
            logger.debug(f"Generating response for prompt")

            thinking_started = False
            text_started = False
            for chunk in self.model.stream(messages):
                # Each chunk.content is a list of blocks
                for block in chunk.content if isinstance(chunk.content, list) else []:
                    if block.get("type") == "thinking":
                        if not thinking_started:
                            print("🧠 Thinking...", flush=True)
                            thinking_started = True
                    elif block.get("type") == "text":
                        if thinking_started and not text_started:
                            print("\n", flush=True)
                            text_started = True
                        print(block.get("text", ""), end="", flush=True)
                # Handle string content (some chunks come as plain strings)
                if isinstance(chunk.content, str) and chunk.content:
                    if thinking_started and not text_started:
                        print("\n", flush=True)
                        text_started = True
                    print(chunk.content, end="", flush=True)
            
            logger.debug("Response generated successfully")

        except TimeoutError as e:
            logger.error(f"LLM request timeed out after {self.timeout} seconds")
            raise LLMTimeoutError(
                f"LLM request timeed out after {self.timeout} seconds",
                details={
                    "timeout": self.timeout,
                    "model": self.model_name
                }
            ) from e

        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise LLMAPIError(
                "Failed to generate response",
                details={
                    "prompt": prompt,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            ) from e



class LLM_lite:
    def __init__(self, model_name: str = None):

        setting = get_settings()
        self.model_name = model_name if model_name is not None else setting.llm_lite_model
        self.temperature = setting.llm_temperature
        self.timeout = setting.llm_timeout

        try:
            secrets = get_secrets()
            api_keys = secrets.get_api_key()  # returns plain string

            logger.info("API Key loaded successfully")
        except Exception as e:
            raise SecretsError(
                "Failed to load API Key",
                details={
                    "error": str(e)
                }
            ) from e

        try:
            logger.info(
                f"Loading LLM Lite model: {self.model_name} | "
                f"Temperature: {self.temperature} | "
                f"Timeout: {self.timeout}"
            )
            self.model = ChatAnthropic(
                model_name=self.model_name,
                api_key=api_keys,
                temperature=self.temperature,
                timeout=self.timeout
            )
            logger.info("LLM Lite model loaded successfully")
        
        except Exception as e:
            logger.error(f"Failed to load LLM model: {e}")
            raise LLMAPIError(
                "Failed to load LLM model",
                details={
                    "model_name": self.model_name,
                    "error": str(e)
                }
            ) from e
        
        

    def generate(self, prompt: str) -> str:
        messages = [
            SystemMessage(content=SYS_MSG_QUERY_EXPANDER),
            HumanMessage(content=prompt)
        ]
        
        try:
            logger.debug(f"Generating response for prompt")
            response = self.model.invoke(messages)
            logger.debug("Response generated successfully")
            return response.content
        
        except TimeoutError as e:
            logger.error(f"LLM Lite request timeed out after {self.timeout} seconds")
            raise LLMTimeoutError(
                f"LLM Lite request timeed out after {self.timeout} seconds",
                details={
                    "timeout": self.timeout,
                    "model": self.model_name
                }
            ) from e
        
        except Exception as e:
            logger.error(f"Failed to generate response: {e}")
            raise LLMAPIError(
                "Failed to generate response",
                details={
                    "prompt": prompt,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            ) from e
                    


    

if __name__ == "__main__":
    llm = LLM()
    prompt = "What is the capital of Arrakis?"
    
    print("----------------------------------------------------------------")
    llm.generate(prompt)
    print("\n")
    print("----------------------------------------------------------------")
    
