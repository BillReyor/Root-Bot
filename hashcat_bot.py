import subprocess
import re
import asyncio
import logging
import discord
import time
import datetime
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

# Remove built-in help
bot.remove_command("help")

# Global variable to keep track of whether the bot is currently running a hashcat job
is_processing_job = False
HASHCAT_PROGRESS_RE = re.compile(r"Progress\.+?(\d+\.\d+)%")
current_job_status = {
    "algorithm": None,
    "start_time": None,
    "progress": "0%"
}

async def run_hashcat(command: list, timeout: int):
    global is_processing_job, current_job_status
    process = None

    # 1. Create a unique filename
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    log_filename = f"hashcat_output_{timestamp}.log"

    try:
        # Open the log file in append mode
        with open(log_filename, 'a') as log_file:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=log_file,
                stderr=log_file
            )

            current_job_status["start_time"] = time.time()
            current_job_status["algorithm"] = command[2]

            await asyncio.wait_for(process.wait(), timeout=timeout)

            if process.returncode == 0:
                current_job_status["progress"] = "100%"
                return f"Output logged in {log_filename}", "Success"
            else:
                return f"Hashcat encountered an error. Check {log_filename} for details.", "Error"

    except asyncio.TimeoutError:
        return f"Hashcat operation timed out. Partial output in {log_filename}", "Timeout"
    except Exception as e:
        logging.error(f"Error running hashcat: {e}")
        return str(e), "Error"
    finally:
        is_processing_job = False

def find_password_for_hash(target_hash, filename="hashcat.potfile"):
    target_hash = target_hash.lower()
    with open(filename, 'r') as f:
        for line in f:
            parts = line.strip().rsplit(":", 1)
            if len(parts) != 2:
                continue
            hash_from_file, password = parts
            if hash_from_file.lower() == target_hash:
                return password
    return None

@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} is now online!")

@bot.command(name="hashcat")
async def _hashcat(ctx, algorithm: str, hash_value: str):
    global is_processing_job

    if is_processing_job:
        await ctx.send("Hashcat is currently processing a job. Please wait.")
        return

    supported_algorithms = {
        "md5": 0,
        "sha1": 100,
        "ntlm": 1000,
        "netntlmv2": 5600,
        "mssql2000": 131,
        "mssql2005": 132
    }

    hash_patterns = {
        "md5": re.compile("^[a-fA-F0-9]{32}$"),
        "sha1": re.compile("^[a-fA-F0-9]{40}$"),
        "ntlm": re.compile("^[a-fA-F0-9]{32}$"),
        "netntlmv2": re.compile("^[a-zA-Z0-9\-_]+::[a-zA-Z0-9\-_]+:[a-fA-F0-9]{16}:[a-fA-F0-9]+:[a-fA-F0-9]+$"),
        "mssql2000": re.compile("^[a-fA-F0-9]{54}$"),
        "mssql2005": re.compile("^[a-fA-F0-9]{40}$")
    }

    if algorithm not in supported_algorithms:
        await ctx.send("Unsupported hash algorithm.")
        return

    if not hash_patterns[algorithm].match(hash_value):
        await ctx.send("Invalid hash format.")
        return

    wordlist = "rockyou.txt"
    command = ["hashcat", "-m", str(supported_algorithms[algorithm]), hash_value, wordlist]

    is_processing_job = True

    await ctx.send("Hashcat operation started, this may take up to an hour.")
    stdout, status = await run_hashcat(command, 3600)

    if status == "Success":
        password = find_password_for_hash(hash_value)
        if password:
            await ctx.send(f"Hash cracked!\n\nHash: {hash_value}\nPassword: {password}")
        else:
            await ctx.send(f"Hash cracked, but could not retrieve the password from the potfile.\n\n{stdout}")
    elif status == "Timeout":
        await ctx.send("Hashcat operation timed out.")
    else:
        await ctx.send(f"Failed to crack the hash:\n\n{stdout}")

@bot.command(name="hashcat_status")
async def hashcat_status(ctx):
    if not is_processing_job:
        await ctx.send("Hashcat is not currently running a job.")
        return

    elapsed_time = time.time() - current_job_status["start_time"]
    message = (f"Hashcat is currently processing a {current_job_status['algorithm']} job.\n"
               f"Elapsed Time: {elapsed_time:.2f} seconds\n"
               f"Progress: {current_job_status['progress']}")
    
    await ctx.send(message)

if __name__ == "__main__":
    bot.run("")  # Replace with your actual bot token
