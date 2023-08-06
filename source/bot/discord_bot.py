import api.akatsuki as akatsuki
import bot.commands as commands
import traceback
import discord


intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
thread = None
bot_prefix = None


@client.event
async def on_ready():
    akatsuki.update_scorelb()
    print(f"We have logged in as {client.user}")


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    thread.sleeping = False
    args = message.content.split(" ")
    if not message.content.startswith(bot_prefix):
        thread.sleeping = True
        return
    try:
        command = args[0].lower()[len(bot_prefix) :]
        if command == "link":
            await commands.link(message, args)
        elif command == "setgamemode":
            await commands.set_default_gamemode(message, args)
        elif command == "showclan":
            await commands.show_clan(message, args)
        elif command == "show":
            await commands.show(message, args)
        elif command == "reset":
            await commands.reset(message, args)
        elif command == "info":
            await commands.info(message, args)
        elif command == "show1s":
            await commands.show_1s(message, args)
    except Exception as e:
        await message.reply("An error has occurred.")
        print(repr(e))
        print(traceback.format_exc())
    thread.sleeping = True


def akataltbot(secrets):
    global bot_prefix
    bot_prefix = secrets["discord_command_prefix"]
    client.run(secrets["discord_token"])
