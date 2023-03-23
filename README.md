# ChatGPT Discord Bot

A simple Discord bot that utilizes OpenAI's ChatGPT to respond to user messages. Users can interact with the bot by sending messages prefixed with a command.

## Prerequisites

- Python 3.6 or higher
- `discord.py` library
- `openai` library
- A Discord account and a registered bot
- An OpenAI API key

## Installation

1. Clone the repository:

```sh
git clone https://github.com/BillReyor/ChatGPT_Discord_Bot.git
cd ChatGPT_Discord_Bot

2. Install the required Python libraries:
- pip install discord.py
- pip install openai

3. Add your OpenAI API key and Discord bot token to the chatgpt_discord_bot.py script:
openai.api_key = "YOUR_OPENAI_API_KEY"
bot.run("YOUR_DISCORD_BOT_TOKEN")

Replace YOUR_OPENAI_API_KEY and YOUR_DISCORD_BOT_TOKEN with your actual OpenAI API key and Discord bot token, respectively.

4. python chatgpt_discord_bot.py

5. Invite the bot to your server by following the instructions in the Create a ChatGPT Discord bot section.

## Usage
Once the bot is online, users can interact with it using the following command:

!chat <your message>

The bot will respond with a generated message based on the input.

## Customization
You can customize the bot's behavior by modifying the chat_gpt function in the chatgpt_discord_bot.py script. Adjust the temperature parameter for more creative or focused responses, and change the max_tokens parameter to control the length of the generated responses.


