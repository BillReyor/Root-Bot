import os
import openai
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
    response = openai.Completion.create(
        engine="text-davinci-002",
        prompt=prompt,
        max_tokens=200,  # Increase the maximum number of tokens in the response
        n=1,
        stop=None,
        temperature=0.9,  # Increase the temperature to generate more verbose responses
    )
    return response.choices[0].text.strip()

# Define your bot commands
@bot.event
async def on_ready():
    print(f"{bot.user.name} is now online!")

@bot.command(name="chat")
async def chat(ctx, *, message):
    prompt = f"{ctx.author.name}: {message}\nChatGPT:"
    response = await chat_gpt(prompt)
    await ctx.send(response)

# Run the bot
bot.run("")
