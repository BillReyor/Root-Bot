import os, time, zipfile, csv, random, traceback
import logging
from pathlib import Path
from datetime import datetime, timedelta
import openai, discord, shodan
from discord.ext import commands, tasks

#setup logging
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
pid = os.getpid()
logging.info(f"Process ID: {pid}")

# Set up the Discord client with updated intents
intents = discord.Intents.default()
intents.typing = intents.presences = False
intents.messages = intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Set up your API keys
openai.api_key = ""
shodan_api_key = ""

shodan_api = shodan.Shodan(shodan_api_key)

last_interaction = datetime.now() - timedelta(hours=24)

def zip_command_history():
    with zipfile.ZipFile(f"command_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip", "w", zipfile.ZIP_DEFLATED) as zipf:
        zipf.write("command_history.csv")
    os.remove("command_history.csv")

def should_zip_history():
    history_file = Path("command_history.csv")
    return history_file.exists() and history_file.stat().st_mtime < time.time() - 24 * 60 * 60

def log_command_to_csv(command, message, response=None):
    with open("command_history.csv", "a", newline="", encoding="utf-8") as file:
        csv.writer(file).writerow([command, message.content, message.author.name, message.created_at] + ([response] if response else []))

async def chat_gpt(prompt):
    max_tokens, max_prompt_tokens = 2000, 4086
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "Welcome to the Root Global, I am Root Bot, your AI assistant for exploring the world of hacking, security, and privacy. Feel free to ask me anything and I'll provide the knowledge you need. Let's respect the rules and each other, and share our knowledge and skills to push the limits of what's possible."},
            {"role": "user", "content": prompt[:max_prompt_tokens]},
        ],
        "max_tokens": max_tokens,
        "temperature": 1.2,
    }
    response = openai.ChatCompletion.create(**data)
    choice = response.choices[0].message['content'].strip()
    return choice, response.usage["total_tokens"]

async def get_random_fact():
    number = random.randint(1, 100)
    fact, _ = await chat_gpt(f"Think of 100 random facts, then select one single fact associated with the number {number} and tell me all about fact. Only list the fact nothing else")
    formatted_fact = f"Fact #{number}: {fact}"
    return formatted_fact

@tasks.loop(seconds=60)
async def check_and_send_fact():
    global last_interaction
    if datetime.now() - last_interaction > timedelta(hours=24):
        target_channel = bot.get_channel(1083001612269789254)  # Replace with your desired channel ID
        if target_channel:
            fact = await get_random_fact()
            await target_channel.send(f"Random fact: {fact}")
            last_interaction = datetime.now()

@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} is now online!")
    check_and_send_fact.start()

async def send_large_message(channel, content, max_length=2000):
    for i in range(0, len(content), max_length):
        await channel.send(content[i:i+max_length])

@bot.command(name="chat")
async def chat(ctx, *, message):
    global last_interaction
    last_interaction = datetime.now()
    try:
        response, tokens_used = await chat_gpt(message)
        log_command_to_csv("chat", ctx.message, response)
        cost = tokens_used * 0.002 / 1000
        await send_large_message(ctx.channel, f"Response: {response}\nCost: ${cost:.6f}")
    except openai.OpenAIError as e:
        logging.exception("Exception in !chat command")
        await ctx.send(f"Error: {e}")

@bot.command(name="shodan")
async def shodan_query(ctx, *, query):
    log_command_to_csv("shodan", ctx.message)
    try:
        results = shodan_api.search(query)
        response = f"Total results: {results['total']}\n"

        for idx, match in enumerate(results["matches"], 1):
            response += f"{idx}. IP: {match['ip_str']} | Hostnames: {','.join(match['hostnames'])} | Org: {match['org']} | Location: {match['location']['country_name']} {match['location']['city']}\n"

        await ctx.send(response)
    except shodan.APIError as e:
        await ctx.send(f"Error: {e}")

@bot.command(name="history")
async def history(ctx):
    try:
        with open("command_history.csv", "r", newline="", encoding="utf-8") as file:
            reader = csv.reader(file)
            response = "History of commands:\n"
            for row in reader:
                response += f"{row[0]} | {row[1]} | {row[2]} | {row[3]}\n"
            await send_large_message(ctx.channel, response)
    except IOError as e:
        logging.error(f"Error in !history command: {e}")
        await ctx.send(f"Error: {e}")

if __name__ == "__main__":
    if should_zip_history():
        zip_command_history()
    bot.run("")
