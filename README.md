# ChatGPT Discord Bot

A simple Discord bot that utilizes OpenAI's ChatGPT to respond to user messages. Users can interact with the bot by sending messages prefixed with a command.

## Prerequisites

- Python 3.6 or higher
- `discord.py` library
- `openai` library
- A Discord account and a registered bot
- An OpenAI API key

## Create a ChatGPT Discord bot in the discord portal
1. Register a bot on Discord Developer Portal:

a. Go to the Discord Developer Portal (https://discord.com/developers/applications) and sign in with your Discord account.
b. Click on the "New Application" button, give your bot a name, and click "Create."
c. Navigate to the "Bot" tab on the left side and click on "Add Bot."
d. Make sure to save the bot token, as you'll need it later.

2. Invite the bot to your server:
a. Go back to the Discord Developer Portal and navigate to the "OAuth2" tab.
b. In the "SCOPES" section, check the "bot" option, and in the "BOT PERMISSIONS" section, check "Send Messages" and "Read Message History."
c. Copy the generated URL and paste it into your browser to invite the bot to your server.

3. Enable the "Message Content" intent in your bot application:
a. Go to the Discord Developer Portal (https://discord.com/developers/applications) and sign in with your Discord account.
b. Click on your bot application and navigate to the "Bot" tab.
c. Scroll down to the "Privileged Gateway Intents" section and enable the "Message Content" intent.
d. Click "Save Changes" at the bottom of the page.

## Installation

1. Clone the repository
- git clone https://github.com/BillReyor/ChatGPT_Discord_Bot.git
- cd ChatGPT_Discord_Bot

2. Install the required Python libraries:
- pip install discord.py
- pip install openai

3. Add your OpenAI API key and Discord bot token to the chatgpt_discord_bot.py script:
- openai.api_key = "YOUR_OPENAI_API_KEY"
- bot.run("YOUR_DISCORD_BOT_TOKEN")

- Replace YOUR_OPENAI_API_KEY and YOUR_DISCORD_BOT_TOKEN with your actual OpenAI API key and Discord bot token, respectively.

4. python chatgpt_discord_bot.py

5. Invite the bot to your server by following the instructions in the Create a ChatGPT Discord bot section.

## Usage
Once the bot is online, users can interact with it using the following command:

!chat <your message>

The bot will respond with a generated message based on the input.

## Customization
You can customize the bot's behavior by modifying the chat_gpt function in the chatgpt_discord_bot.py script. Adjust the temperature parameter for more creative or focused responses, and change the max_tokens parameter to control the length of the generated responses.


