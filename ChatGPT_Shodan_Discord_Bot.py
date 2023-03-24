import os
import openai
import requests
import discord
import shodan
import csv
import random
from datetime import datetime, timedelta
from discord.ext import commands, tasks

# Set up the Discord client with updated intents
intents = discord.Intents.default()
intents.typing = False
intents.presences = False
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Set up your API keys
openai.api_key = ""
shodan_api_key = ""

shodan_api = shodan.Shodan(shodan_api_key)

last_interaction = datetime.now() - timedelta(hours=24)

def log_command_to_csv(command, message):
    with open("command_history.csv", mode="a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([command, message.content, message.author.name, message.created_at])

async def chat_gpt(prompt):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai.api_key}",
    }
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You are an informative, helpful, and neutral omnipotent being"},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 2000,
        "temperature": 0.9,
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
    response_json = response.json()

    if response.status_code != 200:
        raise Exception(f"OpenAI API returned an error: {response_json['error']}")

    return response_json['choices'][0]['message']['content'].strip()

async def get_random_fact():
    prompt = "Tell me an interesting random fact."
    fact = await chat_gpt(prompt)
    return fact

@tasks.loop(seconds=60)
async def check_and_send_fact():
    global last_interaction
    print("Checking for fact...")
    if datetime.now() - last_interaction > timedelta(hours=24):
        print("24 hours have passed. Getting fact...")
        fact = await get_random_fact()
        print("Got fact:", fact)
        target_channel_id = 1234567890  # Replace with your desired channel ID
        target_channel = bot.get_channel(target_channel_id)
        if target_channel is None:
            print("Error: Channel not found.")
        else:
            print("Sending fact...")
            await target_channel.send(f"Random fact: {fact}")
            last_interaction = datetime.now()

@bot.event
async def on_ready():
    print(f"{bot.user.name} is now online!")
    check_and_send_fact.start()

@bot.command(name="chat")
async def chat(ctx, *, message):
    global last_interaction
    last_interaction = datetime.now()
    log_command_to_csv("chat", ctx.message)
    response = await chat_gpt(message)
    await ctx.send(response)

@bot.command(name="shodan")
async def shodan_query(ctx, *, query):
    log_command_to_csv("shodan", ctx.message)
    try:
        results = shodan_api.search(query)
        response = f"Total results: {results['total']}\n"
        for idx, match in enumerate(results["matches"], start=1):
            response += f"{idx}. IP: {match['ip_str']} | Hostnames: {','.join(match['hostnames'])} | Org: {match['org']} | Location: {match['location']['country_name']} {match['location']['city']}\n"
        await ctx.send(response)
    except shodan.APIError as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="history")
async def history(ctx):
    with open("command_history.csv", mode="r", newline="", encoding="utf-8") as file:
        reader = csv.reader(file)
        response = "History of commands:\n"
        for row in reader:
            response += f"{row[0]} | {row[1]} | {row[2]} | {row[3]}\n"
        await ctx.send(response)

bot.run("")
