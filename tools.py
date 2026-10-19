import os
import time
import asyncio
import httpx
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


# ---------- Third-party REST API: OpenWeatherMap ----------

OW_URL = "https://api.openweathermap.org/data/2.5/weather"


def get_weather(city: str) -> str:
    """Get the current weather for a city by name.

    Args:
        city: The city name, for example "Lahore".
    """
    api_key = os.getenv("OPENWEATHER_API_KEY")

    # Authentication check: make sure the key exists before calling the API
    if not api_key:
        return "Error: OPENWEATHER_API_KEY is not set in the .env file."

    params = {"q": city, "appid": api_key, "units": "metric"}

    with httpx.Client(timeout=10) as client:
        # Rate limit handling: retry on HTTP 429 with exponential backoff (1s, 2s, 4s)
        for attempt in range(3):
            try:
                response = client.get(OW_URL, params=params)
            except httpx.HTTPError as e:
                return f"Error: network problem while calling the weather API: {e}"

            if response.status_code == 429:
                time.sleep(2 ** attempt)
                continue
            if response.status_code == 401:
                return "Error: invalid API key (401). Check OPENWEATHER_API_KEY in .env."
            if response.status_code == 404:
                return f"Error: city '{city}' was not found."
            if response.status_code != 200:
                return f"Error: weather API returned status {response.status_code}."

            data = response.json()
            return (
                f"{data['name']}: {data['weather'][0]['description']}, "
                f"{data['main']['temp']}°C, humidity {data['main']['humidity']}%"
            )

    return "Error: rate limit still exceeded after 3 attempts. Try again later."


# ---------- MCP server: official fetch server ----------

async def _fetch_via_mcp(url: str) -> str:
    server = StdioServerParameters(command="uvx", args=["mcp-server-fetch"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            result = await session.call_tool("fetch", {"url": url})
            texts = [c.text for c in result.content if hasattr(c, "text")]
            return "\n".join(texts)[:4000]  # limit the length sent to the model


def fetch_page(url: str) -> str:
    """Fetch a web page through the MCP fetch server and return its text.

    Args:
        url: A full URL that starts with https://
    """
    try:
        return asyncio.run(_fetch_via_mcp(url))
    except Exception as e:
        return f"Error: MCP fetch failed: {e}"