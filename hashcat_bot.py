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
bot.remove_command("help")  # Remove built-in help

# Global variables
is_processing_job = False
current_process = None  # To keep track of the running hashcat process
current_job_status = {
    "algorithm": None,
    "start_time": None,
    "progress": "0%"
}
current_mode = None

# Constants
RULE_FILE = "rules/OneRuleToRuleThemStill.rule"
SUPPORTED_ALGORITHMS = {
    "md5": 0,
    "sha1": 100,
    "ntlm": 1000,
    "netntlmv2": 5600,
    "mssql2000": 131,
    "mssql2005": 132
}
HASH_PATTERNS = {
    "md5": re.compile("^[a-fA-F0-9]{32}$"),
    "sha1": re.compile("^[a-fA-F0-9]{40}$"),
    "ntlm": re.compile("^[a-fA-F0-9]{32}$"),
    "netntlmv2": re.compile("^[a-zA-Z0-9\-_]+::[a-zA-Z0-9\-_]+:[a-fA-F0-9]{16}:[a-fA-F0-9]+:[a-fA-F0-9]+$"),
    "mssql2000": re.compile("^[a-fA-F0-9]{54}$"),
    "mssql2005": re.compile("^[a-fA-F0-9]{40}$")
}

def read_log_file(filename):
    with open(filename, 'r') as file:
        return file.read()

def find_password_for_hash(target_hash, filename="hashcat.potfile"):
    target_hash = target_hash.lower()
    with open(filename, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            parts = line.strip().rsplit(":", 1)
            if len(parts) != 2:
                continue
            hash_from_file, password = parts
            if hash_from_file.lower() == target_hash:
                return password
    return None

async def run_hashcat(command: list, timeout: int, job_type: str = "rockyou"):
    global is_processing_job, current_job_status, current_mode, current_process
    timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    log_filename = f"hashcat_output_{timestamp}.log"

    command.extend(["--status-timer=1"])  # <-- Added this line

    try:
        with open(log_filename, 'a') as log_file:
            current_process = await asyncio.create_subprocess_exec(*command, stdout=log_file, stderr=log_file)

            current_job_status["start_time"] = time.time()
            current_job_status["algorithm"] = command[2]

            await asyncio.wait_for(current_process.wait(), timeout=timeout)

            log_content = read_log_file(log_filename)

            if "Exhausted" in log_content:
                return log_content, "Exhausted"
            elif current_process.returncode == 0:
                current_job_status["progress"] = "100%"
                return log_content, "Success"
            else:
                return log_content, "Error"

    except asyncio.TimeoutError:
        return f"Hashcat operation timed out. Partial output in {log_filename}", "Timeout"
    except Exception as e:
        logging.error(f"Error running hashcat: {e}")
        return str(e), "Error"
    finally:
        current_process = None  # Clear the reference to the process
        if "Success" in log_content or job_type != "brute_force":
            is_processing_job = False
            current_mode = None

def get_hashcat_status(filename):
    with open(filename, 'r') as file:
        lines = file.readlines()
    for line in reversed(lines):
        if "Progress.........:" in line:
            match = re.search(r"Progress.........: .+? \((\d+\.\d+)%\)", line)
            if match:
                return match.group(1) + "%"
    return "0%"

@bot.command(name="hashcat_stop")
async def hashcat_stop(ctx):
    global is_processing_job, current_process
    if not is_processing_job:
        await ctx.send("No hashcat job is currently running.")
        return
    if current_process:
        current_process.terminate()
        is_processing_job = False
        await ctx.send("Hashcat job terminated.")
    else:
        await ctx.send("Error: Couldn't terminate hashcat job. Try again later.")

@bot.event
async def on_ready():
    logging.info(f"{bot.user.name} is now online!")

@bot.command(name="hashcat")
async def _hashcat(ctx, algorithm: str = None, hash_value: str = None):
    if not algorithm or not hash_value:
        help_text = ("Usage: !hashcat [algorithm] [hash_value]\n"
                     f"Supported algorithms: {', '.join(SUPPORTED_ALGORITHMS.keys())}\n"
                     "Example: !hashcat md5 5d41402abc4b2a76b9719d911017c592\n\n"
                     "To check the status of a running job, use: !hashcat_status\n"
                     "To stop a currently running job, use: !hashcat_stop")
        await ctx.send(help_text)
        return

    global is_processing_job, current_mode

    if is_processing_job:
        await ctx.send("Hashcat is currently processing a job. Please wait.")
        return

    if algorithm not in SUPPORTED_ALGORITHMS:
        await ctx.send("Unsupported hash algorithm.")
        return

    if not HASH_PATTERNS[algorithm].match(hash_value):
        await ctx.send("Invalid hash format.")
        return

    wordlist = "rockyou.txt"
    command = ["hashcat", "-m", str(SUPPORTED_ALGORITHMS[algorithm]), hash_value, wordlist, "-r", RULE_FILE]

    is_processing_job = True
    await ctx.send("Hashcat operation started using rockyou.txt wordlist with rule file, this may take up to an hour.")
    stdout, status = await run_hashcat(command, 3600, "rockyou")

    if status == "Exhausted" or status == "Timeout":
        password = find_password_for_hash(hash_value)
        if not password:
            await ctx.send("Did not find the password using rockyou.txt with rule file. Switching to brute force mode for an additional hour.")
            current_mode = "brute_force"
            is_processing_job = True
            command = ["hashcat", "-m", str(SUPPORTED_ALGORITHMS[algorithm]), hash_value, "-a", "3"]
            stdout, status = await run_hashcat(command, 3600, "brute_force")

    if status == "Success":
        password = find_password_for_hash(hash_value)
        if password:
            await ctx.send(f"Hash cracked!\n\nHash: {hash_value}\nPassword: {password}")
        else:
            await ctx.send(f"Hash cracked, but could not retrieve the password from the potfile.\n\n{stdout}")
    elif status == "Timeout":
        await ctx.send("Hashcat operation timed out without finding the password.")
    else:
        await ctx.send(f"Failed to crack the hash:\n\n{stdout}")

@bot.command(name="hashcat_status")
async def hashcat_status(ctx):
    global is_processing_job, current_job_status
    if is_processing_job:
        elapsed_time = time.time() - current_job_status["start_time"]
        timestamp = datetime.datetime.fromtimestamp(current_job_status["start_time"]).strftime('%Y%m%d%H%M%S')
        log_filename = f"hashcat_output_{timestamp}.log"
        progress = get_hashcat_status(log_filename)
        await ctx.send(f"Hashcat is currently processing a job using the {current_job_status['algorithm']} algorithm.\nElapsed time: {int(elapsed_time)} seconds\nProgress: {progress}")
    else:
        await ctx.send("Hashcat is not currently processing any jobs.")


if __name__ == "__main__":
    bot.run("")  # Replace with your actual bot token
