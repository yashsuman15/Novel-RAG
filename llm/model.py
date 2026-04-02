from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import SecretStr
from llm.prompt_templates import SYS_MSG, SYS_MSG_QUERY_EXPANDER
from dotenv import load_dotenv
import os
load_dotenv()



class LLM:
    def __init__(self, model_name: str = "claude-opus-4-5", thinking_budget: int = 10000):
        self.model_name = model_name
        
        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        self.model = ChatAnthropic(
            model_name=model_name,
            api_key=SecretStr(anthropic_api_key),
            temperature=1,       # must be 1 for extended thinking
            thinking={
                "type": "enabled",
                "budget_tokens": thinking_budget,
            },
            timeout=120,
        )

    def generate(self, prompt: str) -> str:
        messages = [
            SystemMessage(content=SYS_MSG),
            HumanMessage(content=prompt)
        ]
        
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


class LLM_lite:
    def __init__(self, model_name: str = "claude-sonnet-4-5"):
        self.model = model_name

        anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        self.model = ChatAnthropic(
            model_name=model_name,
            api_key=SecretStr(anthropic_api_key),
            temperature=0.7,
            timeout=120
        )

    def generate(self, prompt: str) -> str:
        messages = [
            SystemMessage(content=SYS_MSG_QUERY_EXPANDER),
            HumanMessage(content=prompt)
        ]
        
        response = self.model.invoke(messages)
        return response.content


    

if __name__ == "__main__":
    llm = LLM()
    prompt = "What is the capital of Arrakis?"
    
    print("----------------------------------------------------------------")
    llm.generate(prompt)
    print("\n")
    print("----------------------------------------------------------------")
    
