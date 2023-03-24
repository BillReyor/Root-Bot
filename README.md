# Using the Code

This code is a Discord bot that can chat using OpenAI's GPT-3, search the Shodan database, and keep track of user command history. Follow the steps below to use this code:

## Prerequisites

Before you start, you will need the following:

- Python 3.7 or higher installed on your machine
- A Discord account and a server where you have the permission to add bots
- OpenAI API key - You can sign up for OpenAI [here](https://beta.openai.com/signup/)
- Shodan API key - You can sign up for Shodan [here](https://account.shodan.io/register)

# Setting up the Bot on Discord

Here are the steps to set up the bot on Discord:

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications).
2. Click the "New Application" button.
3. Give your application a name and click "Create".
4. In the left sidebar, click on "Bot" and then click "Add Bot".
5. Customize your bot by giving it a name and profile picture if desired.
6. Click the "Copy" button under "Token" to copy your bot token.
7. In the code, replace the empty string in `bot.run("")` with your bot token.
8. In the left sidebar, click on "OAuth2".
9. Under "Scopes", select "bot".
10. Under "Bot Permissions", select the appropriate permissions for your bot (e.g. "Send Messages", "Read Message History", "Embed Links").
11. Copy the generated URL and paste it into your browser.
12. Select the server where you want to add the bot and click "Authorize".
13. The bot should now be added to your server and ready to use.

## Setup

1. Clone the repository or download the code as a ZIP file and extract it to a directory.
2. Open the directory in a command prompt or terminal.
3. Install the required Python packages by running `pip install -r requirements.txt`.
4. Open the code in a text editor.
5. Add your OpenAI and Shodan API keys in the `openai.api_key` and `shodan_api_key` variables respectively.
6. Add your Discord bot token in the `bot.run("")` line.

## Running the Bot

1. Open a command prompt or terminal in the directory where the code is located.
2. Run the command `python bot.py` to start the bot.
3. The bot should now be online and ready to use.

## Using the Bot

### Chatting with GPT-3

To chat with the bot, type `!chat` followed by your message in the Discord chat. For example:  
`!chat What is the capital of France?`

The bot will then respond with an answer generated by GPT-3.

### Searching Shodan

To search the Shodan database, type `!shodan` followed by your query in the Discord chat. For example:  

`!shodan Apache`

The bot will then return the search results.

### Viewing Command History

To view your command history, type `!history` in the Discord chat.




