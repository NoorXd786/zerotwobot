import random
import html
from datetime import datetime
import humanize

from zerotwobot import LOGGER, application
from zerotwobot.modules.disable import (
    DisableAbleCommandHandler,
    DisableAbleMessageHandler,
)
from zerotwobot.modules.sql import afk_sql as sql
from zerotwobot.modules.users import get_user_id
from telegram import MessageEntity, Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes, filters, MessageHandler

AFK_GROUP = 7
AFK_REPLY_GROUP = 8



async def afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_message.text:
        args = update.effective_message.text.split(None, 1)
    else:
        return
    user = update.effective_user

    if not user:  # ignore channels
        return


    notice = ""
    if len(args) >= 2:
        reason = args[1]
        if len(reason) > 100:
            reason = reason[:100]
            notice = "\nYour afk reason was shortened to 100 characters."
    else:
        reason = ""

    sql.set_afk(update.effective_user.id, reason)
    fname = update.effective_user.first_name
    try:
        if reason:
            await update.effective_message.reply_text(
                f"{fname} is now away! \nReason: <code>{reason}</code> \n {notice}",
                parse_mode="html"
            )
        else:
            await update.effective_message.reply_text(f"{fname} is now away!{notice}")
    except BadRequest:
        pass



async def no_longer_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message = update.effective_message

    if not user:  # ignore channels
        return

    if sql.is_afk(user.id):
        afk_user = sql.check_afk_status(user.id)

        time = humanize.naturaldelta(datetime.now() - afk_user.time)

    if res := sql.rm_afk(user.id):
        if message.new_chat_members:  # dont say msg
            return
        firstname = update.effective_user.first_name
        try:
            options = [
                "{} is here!",
                "{} is back!",
                "{} is now in the chat!",
                "{} is awake!",
                "{} is back online!",
                "{} is finally here!",
                "Welcome back! {}",
                "We missed you {}",
            ]
            chosen_option = random.choice(options)
            await update.effective_message.reply_text(
                f"{chosen_option.format(firstname)}\nYou were AFK for: <code>{time}</code>",
                parse_mode="html",
            )
        except:
            return



async def reply_afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    bot = context.bot
    message = update.effective_message
    userc = update.effective_user
    userc_id = userc.id
    if message.entities and message.parse_entities(
        [MessageEntity.TEXT_MENTION, MessageEntity.MENTION],
    ):
        entities = message.parse_entities(
            [MessageEntity.TEXT_MENTION, MessageEntity.MENTION],
        )

        chk_users = []
        for ent in entities:
            if ent.type == MessageEntity.TEXT_MENTION:
                user_id = ent.user.id
                fst_name = ent.user.first_name

                if user_id in chk_users:
                    return
                chk_users.append(user_id)

            if ent.type != MessageEntity.MENTION:
                return

            user_id = await get_user_id(
                message.text[ent.offset: ent.offset + ent.length],
            )
            if not user_id:
                # Should never happen, since for a user to become AFK they must have spoken. Maybe changed username?
                return

            if user_id in chk_users:
                return
            chk_users.append(user_id)

            try:
                chat = await bot.get_chat(user_id)
            except BadRequest:
                LOGGER.error(f"Error: Could not fetch userid {user_id} for AFK module")
                return
            fst_name = chat.first_name

            await check_afk(update, context, user_id, fst_name, userc_id)

    elif message.reply_to_message:
        user_id = message.reply_to_message.from_user.id
        fst_name = message.reply_to_message.from_user.first_name
        await check_afk(update, context, user_id, fst_name, userc_id)


async def check_afk(update: Update, context: ContextTypes.DEFAULT_TYPE, user_id: int, fst_name: str, userc_id: int):
    if not sql.is_afk(user_id):
        return
    user = sql.check_afk_status(user_id)

    if userc_id == user_id:
        return

    time = humanize.naturaldelta(datetime.now() - user.time)

    if not user.reason:
        res = f"{fst_name} is afk.\n\nLast seen {time} ago."
        await update.effective_message.reply_text(res)
    else:
        res = f"{html.escape(fst_name)} is afk.\nReason: <code>{html.escape(user.reason)}</code>\n\nLast seen {time} ago."
        await update.effective_message.reply_text(res, parse_mode="html")


__help__ = """
 • `/afk <reason>`*:* mark yourself as AFK (away from keyboard).
 • `brb <reason>`*:* same as the afk command - but not a command.
When marked as AFK, any mentions will be replied to with a message to say you're not available!
"""

AFK_HANDLER = DisableAbleCommandHandler("afk", afk, block=False)
AFK_REGEX_HANDLER = DisableAbleMessageHandler(
    filters.Regex(r"^(?i)brb(.*)$"), afk, friendly="afk", block=False
)
NO_AFK_HANDLER = MessageHandler(filters.ALL & filters.ChatType.GROUPS, no_longer_afk, block=False)
AFK_REPLY_HANDLER = MessageHandler(filters.ALL & filters.ChatType.GROUPS, reply_afk, block=False)

application.add_handler(AFK_HANDLER, AFK_GROUP)
application.add_handler(AFK_REGEX_HANDLER, AFK_GROUP)
application.add_handler(NO_AFK_HANDLER, AFK_GROUP)
application.add_handler(AFK_REPLY_HANDLER, AFK_REPLY_GROUP)

__mod_name__ = "AFK"
__command_list__ = ["afk"]
__handlers__ = [
    (AFK_HANDLER, AFK_GROUP),
    (AFK_REGEX_HANDLER, AFK_GROUP),
    (NO_AFK_HANDLER, AFK_GROUP),
    (AFK_REPLY_HANDLER, AFK_REPLY_GROUP),
]
