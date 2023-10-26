#Data 10/26/23
import re
import asyncio
import logging
import discord
import time
import datetime
from discord.ext import commands

# Logging Setup
logging.basicConfig(filename="app.log", level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Constants
INTENTS = discord.Intents.default()
INTENTS.typing = False
INTENTS.presences = False
INTENTS.messages = True
INTENTS.message_content = True

RULE_FILE = "rules/OneRuleToRuleThemStill.rule"
SUPPORTED_ALGORITHMS = {
    "md5": 0, "sha1": 100, "ntlm": 1000, "netntlmv2": 5600, "mssql2000": 131, "mssql2005": 132,  "asrep": 18200
}
HASH_PATTERNS = {
    "md5": re.compile("^[a-fA-F0-9]{32}$"),
    "sha1": re.compile("^[a-fA-F0-9]{40}$"),
    "ntlm": re.compile("^[a-fA-F0-9]{32}$"),
    "netntlmv2": re.compile("^[a-zA-Z0-9\-_$]+::[a-zA-Z0-9\-_$]*:[a-fA-F0-9]{16}:[a-fA-F0-9]+:[a-fA-F0-9]+$"),
    "mssql2000": re.compile("^[a-fA-F0-9]{54}$"),
    "mssql2005": re.compile("^[a-fA-F0-9]{40}$"),
    "asrep": re.compile(r"^\$krb5asrep\$[0-9]+\$[a-zA-Z0-9\-_.]+@[a-zA-Z0-9\-_.]+:.*\$[a-fA-F0-9]+$") #added
}

bot = commands.Bot(command_prefix="!", intents=INTENTS)
bot.remove_command("help")


class HashcatManager:

    def __init__(self):
        self.is_processing_job = False
        self.current_process = None
        self.current_job_status = {"algorithm": None, "start_time": None, "progress": "0%", "timeout": None}
        self.current_mode = None

    def read_log_file(self, filename):
        with open(filename, 'r') as file:
            return file.read()

    def find_password_for_hash(self, target_hash, filename="hashcat.potfile"):
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

    async def run_hashcat(self, command, timeout, job_type="rockyou"):
        log_content = ""
        timestamp = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
        log_filename = f"hashcat_output_{timestamp}.log"
        command.extend(["--status-timer=1"])
        try:
            with open(log_filename, 'a') as log_file:
                self.current_process = await asyncio.create_subprocess_exec(*command, stdout=log_file, stderr=log_file)
                self.current_job_status["start_time"] = time.time()
                self.current_job_status["algorithm"] = command[2]
                self.current_job_status["timeout"] = timeout
                await asyncio.wait_for(self.current_process.wait(), timeout=timeout)
                log_content = self.read_log_file(log_filename)
                if "Exhausted" in log_content:
                    return log_content, "Exhausted"
                elif self.current_process.returncode == 0:
                    self.current_job_status["progress"] = "100%"
                    return log_content, "Success"
                else:
                    return log_content, "Error"
        except asyncio.TimeoutError:
            if self.current_process:
                self.current_process.terminate()
            self.is_processing_job = False
            self.current_mode = None
            return f"Hashcat operation timed out. Partial output in {log_filename}", "Timeout"
        except Exception as e:
            logging.error(f"Error running hashcat: {e}")
            return str(e), "Error"
        finally:
            self.current_process = None
            if "Success" in log_content or job_type != "brute_force":
                self.is_processing_job = False
                self.current_mode = None

manager = HashcatManager()

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

    if manager.is_processing_job:
        await ctx.send("Hashcat is currently processing a job. Please wait.")
        return

    if algorithm not in SUPPORTED_ALGORITHMS:
        await ctx.send("Unsupported hash algorithm.")
        return

    if not HASH_PATTERNS[algorithm].match(hash_value):
        await ctx.send("Invalid hash format.")
        return

    wordlist = "rockyou.txt"
    command = ["hashcat", "-m", str(SUPPORTED_ALGORITHMS[algorithm]), hash_value, wordlist, "-r", RULE_FILE, "--loopback"]
    manager.is_processing_job = True
    await ctx.send("Hashcat operation started using a wordlist with rule file, this may take up to an hour.")
    stdout, status = await manager.run_hashcat(command, 3600, "rockyou")

    if status == "Exhausted" or status == "Timeout":
        manager.is_processing_job = False
        manager.current_mode = None
        password = manager.find_password_for_hash(hash_value)
        if not password:
            await ctx.send("Did not find the password using rockyou.txt with rule file. Switching to brute force mode for an additional hour.")
            manager.current_mode = "brute_force"
            manager.is_processing_job = True
            command = ["hashcat", "-m", str(SUPPORTED_ALGORITHMS[algorithm]), hash_value, "-a", "3"]
            stdout, status = await manager.run_hashcat(command, 3600, "brute_force")

    if status == "Success":
        password = manager.find_password_for_hash(hash_value)
        if password:
            await ctx.send(f"Found password: {password}")
        else:
            await ctx.send("Password not found in hashcat.potfile, but hashcat reported success. Please check manually.")
    elif status == "Timeout" or status == "Error":
        manager.is_processing_job = False
        manager.current_mode = None
        await ctx.send(f"Hashcat operation did not finish successfully. Status: {status}")

@bot.command(name="hashcat_stop")
async def hashcat_stop(ctx):
    if not manager.is_processing_job:
        await ctx.send("No Hashcat operation is currently running.")
        return
    if manager.current_process:
        manager.current_process.terminate()
    manager.is_processing_job = False
    manager.current_mode = None
    await ctx.send("Hashcat operation stopped.")

@bot.command(name="hashcat_status")
async def hashcat_status(ctx):
    if not manager.is_processing_job:
        await ctx.send("No Hashcat operation is currently running.")
        return
    elapsed_time = int(time.time() - manager.current_job_status["start_time"])
    total_time = manager.current_job_status["timeout"]
    progress_percentage = min(100, (elapsed_time / total_time) * 100)
    elapsed_time_string = str(datetime.timedelta(seconds=elapsed_time))
    status_message = (f"Hashcat is cracking with algorithm {manager.current_job_status['algorithm']}.\n"
                      f"Elapsed Time: {elapsed_time_string}\n"
                      f"Progress: {progress_percentage:.2f}%")
    await ctx.send(status_message)

@bot.event
async def on_ready():
    logging.info(f"We have logged in as {bot.user}")

if __name__ == "__main__":
    bot.run("")
