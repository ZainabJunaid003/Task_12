from dotenv import load_dotenv
from google import genai
from google.genai import types
from tools import get_weather, fetch_page

load_dotenv()  # loads GEMINI_API_KEY and OPENWEATHER_API_KEY from .env
client = genai.Client()  # reads GEMINI_API_KEY automatically

MODEL = "gemini-3.8-flash"

SYSTEM_INSTRUCTION = (
    "You are a helpful assistant. Use get_weather for weather questions. "
    "Use fetch_page when the user asks you to read a web page. "
    "If a tool returns an error, explain the problem clearly to the user."
)


def run(prompt: str):
    print(f"\nQUESTION: {prompt}")

    # A new chat for each question, with the tools attached.
    # send_message runs the tool calls automatically and returns the final answer.
    chat = client.chats.create(
        model=MODEL,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_INSTRUCTION,
            tools=[get_weather, fetch_page],
        ),
    )
    response = chat.send_message(prompt)

    print("ANSWER:", response.text)
    print("-" * 60)


if __name__ == "__main__":
    # Test 1: third-party REST API tool (two calls)
    run("What's the weather in Lahore right now, and what's the weather in Karachi?")

    # Test 2: MCP tool
    run("Fetch https://modelcontextprotocol.io and tell me what it is in one sentence.")

    # Test 3: error handling
    run("What's the weather in Nowhere-City-XYZ?")