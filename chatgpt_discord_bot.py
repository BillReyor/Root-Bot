import os
import openai
import requests
import discord
from discord.ext import commands

# Set up the Discord client with updated intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Set up your OpenAI API key
openai.api_key = ""

# Set up your ChatGPT function
async def chat_gpt(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
                "role": "system",
                "content": "You are a helpful assistant."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.9,
    }

    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response_json = response.json()

    if response.status_code != 200:
        raise Exception(f"OpenAI API returned an error: {response_json['error']}")

    assistant_message = response_json['choices'][0]['message']['content'].strip()
    return assistant_message

# Define your bot commands
@bot.event
async def on_ready():
    print(f"{bot.user.name} is now online!")

@bot.command(name="chat")
async def chat(ctx, *, message):
    prompt = message
    response = await chat_gpt(prompt)
    await ctx.send(response)

# Run the bot
bot.run("")
