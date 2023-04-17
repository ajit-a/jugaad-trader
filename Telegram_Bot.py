#https://docs.python.org/3/library/asyncio-subprocess.html
#pip install python-telegram-bot
#pip install telegram
#Ideally static data should come from db


# Enter your bot token here
bot_token = '1931632990:AAG7Yb6es04h-pVVWJezQ-WSyFQgvARNyAU'

#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

"""
Simple Bot to reply to Telegram messages.

First, a few handler functions are defined. Then, those functions are passed to
the Application and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.

Usage:
Basic Echobot example, repeats messages.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""

import logging
import subprocess
from urllib import parse

from telegram import __version__ as TG_VER

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )
from telegram import ForceReply, Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

passwd = {}
apikeys = {}
userids = {}
supported_commands = set()

#Clean the screat file for today
with open('secretdata.csv', 'w'): pass
with open('alltokens.csv', 'w'): pass

# Define a few command handlers. These usually take the two arguments update and
# context.
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /start is issued."""
    user = update.effective_user
    await update.message.reply_html(
        rf"Hi {user.mention_html()}!",
        reply_markup=ForceReply(selective=True),
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(str(supported_commands))

async def capture_access_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Enter your App Code !",
        reply_markup=ForceReply(selective=True),
    )

async def capture_telegram_details(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send a message when the command /help is issued."""
    await update.message.reply_text(
        "Enter your userid:pass !",
        reply_markup=ForceReply(selective=True),
    )

async def extract_data(update: Update) -> None:
    if update.message.reply_to_message == None:
        return
    original_msg=update.message.reply_to_message.text
    if original_msg != "Enter your userid:pass !":
        return
    userid=update.message.from_user.id
    if userid in apikeys:
        await update.message.reply_text("User already exists. Please contact admin, if you want to overwrite your details")
        return
    msg="Incorrect format for:"+str(userid)
    try:
        userText = update.message.text
        loginid = userText.split(':')[0].strip()
        passw = userText.split(':')[1].strip()
        msg="Captured details for:"+str(loginid)+" id:"+str(userid)
        f=open("static_secretdata.csv","a+")
        f.write(str(userid)+","+passw+","+"XXXX"+","+loginid+'\n')
        f.close()
        passwd[userid] = passw
        apikeys[userid] = "XXXX"
        userids[userid] = loginid
    except Exception as e:
        print(repr(e))
    print(msg)
    await update.message.reply_text(msg)


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Echo the user message."""
    if update.message.reply_to_message == None:
        return
    original_msg=update.message.reply_to_message.text
    if original_msg == "Enter your userid:pass !":
        await extract_data(update)
        return
    if original_msg != "Enter your App Code !":
        return
    userText = update.message.text
    if len(userText) == 6:
        user=update.message.from_user.username
        fname=update.message.from_user.first_name
        userid=update.message.from_user.id
        pin=userText
        try:
            #print(userids)
            #print(type(userid))
            if userid not in userids:
                msg=str(userid)+" does not exist in the system"
                print(msg)
                await update.message.reply_text(msg)
            else:
                msg="Captured pin for:"+str(user)+" id:"+str(userid)+" in reply:"+original_msg
                print(msg)
                await update.message.reply_text(msg)
                #subprocess.Popen(['python', 'OMS_passive.py', pin, passwd[userid], userids[userid]])
                subprocess.call(['python', 'generateSession.py', pin, passwd[userid], userids[userid]])
                #await update.message.reply_text("Captured token for:"+user+" id:"+str(userid)+" in reply:"+original_msg)
        except Exception as e:
            erromsg = "Error while login: for:"+str(user)+" id:"+str(userid)+" in reply:"+original_msg
            print(errormsg)
            await update.message.reply_text(errormsg)
            print(repr(e))
    else:
        print("Incorrect Pin from:"+str(update.message.from_user.id)+" "+update.message.from_user.username)
        await update.message.reply_text("Pin seems incorrect, please try again to login")


def populate_static_data():
    try:
        with open('static_secretdata.csv') as f:
            lines = f.readlines()
        for line in lines:
            tokens = line.strip('\n').split(',')
            telegramid = int(tokens[0])
            passwd[telegramid] = tokens[1]
            apikeys[telegramid] = tokens[2]
            userids[telegramid] = tokens[3]
    except Exception as e:
        print(repr(e))

populate_static_data()

def main() -> None:
    """Start the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(bot_token).build()

    # on different commands - answer in Telegram
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("login", capture_access_token))
    application.add_handler(CommandHandler("register", capture_telegram_details))

    supported_commands.add("/start")
    supported_commands.add("/help")
    supported_commands.add("/login")
    supported_commands.add("/register")

    # on non command i.e message - echo the message on Telegram
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    # Run the bot until the user presses Ctrl-C
    application.run_polling()


if __name__ == "__main__":
    main()
