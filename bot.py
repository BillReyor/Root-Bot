import os, time, zipfile, csv, random, traceback
import logging, requests
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
#remove built-in help because we use it already
bot.remove_command("help")


# Set up your API keys
openai.api_key = ""
shodan_api_key = ""
HIBP_API_KEY = "your_api_key_here"

shodan_api = shodan.Shodan(shodan_api_key)

last_interaction = datetime.now() - timedelta(hours=24)

instructions = """
Welcome to Root Bot, your AI assistant for exploring the world of hacking, security, and privacy.

Here are the available commands:
- !chat [message]: Chat with Root Bot and get answers to your questions.
- !shodan [query]: Search for devices using the Shodan API.
- !pwned [email]: Check if an email address has been involved in a data breach using the HIBP API.
- !history: View the history of commands used with Root Bot.
- !help: Display this message.
"""

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
            {"role": "system", "content": "I am Root Bot, your AI assistant for exploring the world of hacking, security, and privacy. As Root Bot, I answer normal questions as an assistant but I also create image prompts from user-provided concepts. For example:\n\nConcept: Steampunk insect macro shot\nPrompt: a close up of a bug with big eyes, cyber steampunk, highly detailed 8k, space insect android --v 4 --q 2 --stylize 1000\nConcept: Orange pie on a wooden table\nPrompt: a pie on a table, orange details, vivid attention to detail, warm sunshine, crisp smooth lines --v 4 --q 2 --stylize 1000\nConcept: Close up of a plant with blue and golden leaves\nPrompt: close-up of golden leaves, abstract design, blue flax, solid colors, background artwork --v 4 --q 2 --stylize 1000\nConcept: close up of two prisoners with there hands through the bars\nPrompt: two sad bank robbers in a prison in classic prisoner suit with stripes, onether one thin and another one fat, standing and keeping their hands on bars, Robert Crump style --ar 16:9\nConcept: city scape based on Vancouverism\nPrompt: city scape based on Vancouverism :: skyscrapers made of highly reflective 🪞 material in assorted colors :: chrome reflections city :: modern buidlings, green recreation areas, ponds, river, japanese gardens, eco friendly, sustainable, vibrant :: Godzilla reflections in the buildings' windows --ar 1:2 --v 5\nConcept: a black kid picking fruit to eat\nPrompt: a cool and elegant African teenager boy full figure is picking a tree fruit on the left of a lush garden environment full of african fruit trees and flowers, spring, cinematic, photoshoot, shot on 25mm lens, depth of field, tilt blur, shutter speed 1/ 1000, f/ 22, white balance, 32k, super resolution, professional photo rgb, bright background, dramatic lighting, incandescent, soft lighting, volumetric, Conte - Jour, global illumination, screen space global illumination, scattering, shadows, harsh, flickering, lumen reflections, screen space reflections, diffraction gradation, aberration Chromatic, IT Offset, Scanlines, Ambient Occlusion, Anti - aliasing, FKAA, TXAA, RTX, SSAO, OpenGL - Shader's, Post Processing, Post Production, Cell Shading, Tone Mapping, CGI, VFX, SFX, Insanely Detailed and intricate, hyper maximalist, elegant, photography, volumetric, ultra - detailed, intricate detail, super - detailed, --ar 3:2 --q 2 --uplight --v 5\n\nFeel free to ask me anything and I'll provide the knowledge you need. Let's respect the rules and each other, and share our knowledge and skills to push the limits of what's possible."},
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
    channel = bot.get_channel(1083001612269789254) # Replace YOUR_CHANNEL_ID with the ID of the channel where the bot will be used
    await channel.send(instructions)

async def send_large_message(channel, content, max_length=2000):
    for i in range(0, len(content), max_length):
        await channel.send(content[i:i+max_length])

@bot.command(name="help")
async def help_command(ctx):
    await ctx.send(instructions)

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

@bot.command(name="pwned")
async def pwned(ctx, *, email):
    if HIBP_API_KEY == "your_api_key_here":
        await ctx.send("Error: HIBP API key is not configured. Please set your HIBP API key and try again.")
        return
    try:
        response = requests.get(f"https://haveibeenpwned.com/api/v3/breachedaccount/{email}",
                                headers={"User-Agent": "Mozilla/5.0", "hibp-api-key": HIBP_API_KEY})
        if response.status_code == 200:
            breaches = response.json()
            sites = ", ".join([breach["Name"] for breach in breaches])
            message = f"{email} has been pwned in the following breaches: {sites}"
        elif response.status_code == 404:
            message = f"{email} has not been pwned."
        else:
            message = f"Error checking if {email} has been pwned."
            logging.error(f"Error checking if {email} has been pwned. API response: {response.text}")
        await ctx.send(message)
    except requests.exceptions.RequestException as e:
        message = f"Error checking if {email} has been pwned: {e}"
        await ctx.send(message)
        logging.exception(f"Exception in pwned command for email '{email}'")

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
