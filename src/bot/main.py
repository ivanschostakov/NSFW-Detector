from io import BytesIO
import logging

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ChatMemberStatus
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import MessageReactionUpdated, ChatMemberUpdated, Message

from src.classifier.main import is_nsfw
from config import TELEGRAM_BOT_TOKEN


logger = logging.getLogger(__name__)
bot = Bot(TELEGRAM_BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())


async def check_user_nsfw(chat_id: int, user_id: int) -> None:
    logger.info("Checking user profile photo: chat_id=%s, user_id=%s", chat_id, user_id)

    member = await bot.get_chat_member(chat_id, user_id)
    logger.info("User member status: chat_id=%s, user_id=%s, status=%s", chat_id, user_id, member.status)

    if member.status in {
        ChatMemberStatus.CREATOR,
        ChatMemberStatus.ADMINISTRATOR,
    }:
        logger.info("Skipping admin/creator: chat_id=%s, user_id=%s", chat_id, user_id)
        return

    photos = await bot.get_user_profile_photos(user_id=user_id, limit=1)
    if photos.total_count == 0:
        logger.info("No profile photos found: user_id=%s", user_id)
        return

    logger.info("Profile photo found: user_id=%s, total_count=%s", user_id, photos.total_count)

    photo_size = photos.photos[0][-1]
    file = await bot.get_file(photo_size.file_id)

    logger.info("Downloading profile photo: user_id=%s, file_id=%s", user_id, photo_size.file_id)

    buffer = await bot.download_file(file.file_path)
    if isinstance(buffer, BytesIO): file_bytes = buffer.getvalue()
    else: file_bytes = buffer.read()

    logger.info("Profile photo downloaded: user_id=%s, bytes=%s", user_id, len(file_bytes))
    result = is_nsfw(file_bytes)
    logger.info("NSFW check result: chat_id=%s, user_id=%s, nsfw=%s, score=%.2f%%", chat_id, user_id, result.nsfw, result.max_score * 100)

    if not result.nsfw: return

    logger.warning("NSFW profile photo detected: chat_id=%s, user_id=%s, score=%.2f%%", chat_id, user_id, result.max_score * 100)
    await bot.ban_chat_member(chat_id=chat_id, user_id=user_id)

    logger.warning("User banned: chat_id=%s, user_id=%s", chat_id, user_id)


@dp.message_reaction(F.chat.type != "private")
async def handle_message_reaction(event: MessageReactionUpdated) -> None:
    logger.info("Message reaction update: chat_id=%s, message_id=%s", event.chat.id, event.message_id)

    from_user = event.user
    if not from_user:
        logger.info("Reaction update has no visible user: chat_id=%s, message_id=%s", event.chat.id, event.message_id)
        return

    logger.info("Reaction from user: chat_id=%s, message_id=%s, user_id=%s", event.chat.id, event.message_id, from_user.id)
    await check_user_nsfw(
        chat_id=event.chat.id,
        user_id=from_user.id,
    )


@dp.chat_member(ChatMemberUpdatedFilter(IS_NOT_MEMBER >> IS_MEMBER))
async def handle_user_joined(event: ChatMemberUpdated) -> None:
    logger.info(
        "Chat member joined: chat_id=%s, user_id=%s, old_status=%s, new_status=%s",
        event.chat.id,
        event.new_chat_member.user.id,
        event.old_chat_member.status,
        event.new_chat_member.status,
    )

    if event.new_chat_member.user.is_bot:
        logger.info("Skipping bot user: chat_id=%s, user_id=%s", event.chat.id, event.new_chat_member.user.id)
        return

    await check_user_nsfw(
        chat_id=event.chat.id,
        user_id=event.new_chat_member.user.id,
    )



@dp.message(F.chat.type == "private", F.photo)
async def handle_test_photo(message: Message) -> None:
    logger.info("Test photo received: user_id=%s", message.from_user.id)
    photo_size = message.photo[-1]
    file = await bot.get_file(photo_size.file_id)

    logger.info("Downloading test photo: user_id=%s, file_id=%s", message.from_user.id, photo_size.file_id)
    buffer = await bot.download_file(file.file_path)
    if isinstance(buffer, BytesIO): file_bytes = buffer.getvalue()
    else: file_bytes = buffer.read()

    logger.info("Test photo downloaded: user_id=%s, bytes=%s", message.from_user.id, len(file_bytes))
    result = is_nsfw(file_bytes)
    logger.info("Test NSFW result: user_id=%s, nsfw=%s, score=%.2f%%", message.from_user.id, result.nsfw, result.max_score * 100)

    if result.nsfw: await message.answer(f"NSFW detected. Score: {result.max_score:.2%}")
    else: await message.answer(f"Passed. Score: {result.max_score:.2%}")

async def run_bot():
    logging.basicConfig(level=logging.INFO)
    logger.info("Deleting webhook and starting polling")
    await bot.delete_webhook(False)
    await dp.start_polling(bot)
