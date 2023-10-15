"""
Setup Instructions:

1. Install the required packages using pip:
   pip install discord.py websocket-client

2. Replace the 'puttokenhere' string with your actual Discord bot token.
   You can obtain a bot token from the Discord Developer Portal.

3. Modify the API_URL with the address of your actual server.

4. Ensure you have permissions to read and write to "app.log" or adjust logging configuration accordingly.

5. Run this script to start the bot. Ensure you've invited the bot to your server and given it appropriate permissions.
"""

import logging
import discord
import random
import websocket
import json
from discord.ext import commands

# Setup logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Set up the Discord client with updated intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Remove built-in help because we use it already
bot.remove_command("help")

# Processing frequency setting (probability of processing a message through get_completion)
PROCESSING_FREQUENCY = 0.01

API_URL = "wss://chat.petals.dev/api/v2/generate"  # Modify with your actual server address
MODEL_NAME = "petals-team/StableBeluga2"

def open_inference_session():
    """Return the initial request payload to open an inference session."""
    return {
        "type": "open_inference_session",
        "model": MODEL_NAME,
        "max_length": 4096
    }

def generate_prompt(prompt):
    """Return the request payload to generate a prompt."""
    return {
        "type": "generate",
        "inputs": f"Can you elaborate on: {prompt}?",
        "do_sample": True,
        "temperature": 1.0,  
        "top_k": 80,         
        "top_p": 0.98,       
        "max_length": 500    
    }

async def get_completion(prompt):
    """
    Establish a connection to the server, send the prompt, 
    and get the model's completion.
    """
    ws = websocket.WebSocket()
    ws.connect(API_URL)

    ws.send(json.dumps(open_inference_session()))
    response = json.loads(ws.recv())
    if not response.get("ok"):
        logging.error(f"Failed to open the inference session: {response.get('traceback')}")
        return

    ws.send(json.dumps(generate_prompt(prompt)))
    response = json.loads(ws.recv())
    ws.close()

    if response.get("ok"):
        return response.get("outputs").strip()
    else:
        logging.error(f"Failed to get model's response: {response.get('traceback')}")
        return

async def send_large_message(channel, content, max_length=2000):
    """Send large messages split into chunks to a Discord channel."""
    for i in range(0, len(content), max_length):
        await channel.send(content[i:i + max_length])

@bot.event
async def on_message(message):
    """Event to handle incoming messages."""
    if message.author == bot.user or message.author.bot:
        return

    if message.content.startswith(bot.command_prefix):
        await bot.process_commands(message)
    elif random.random() < PROCESSING_FREQUENCY:
        try:
            response = await get_completion(message.content)
            await send_large_message(message.channel, f"{response}")
        except Exception as e:
            logging.exception("Exception in processing message")
            await message.channel.send(f"Error: {e}")

@bot.event
async def on_ready():
    """Event to log when the bot becomes ready."""
    logging.info(f"{bot.user.name} is now online!")

@bot.command(name="llm")
async def llm(ctx, *, message):
    """Command to get the model's response for a given prompt."""
    try:
        response = await get_completion(message)
        await send_large_message(ctx.channel, f"Response: {response}")
    except Exception as e:
        logging.exception("Exception in !llm command")
        await ctx.send(f"Error: {e}")

if __name__ == "__main__":
    BOT_TOKEN = "puttokenhere"
    bot.run(BOT_TOKEN)
