import pytest
from unittest.mock import AsyncMock, MagicMock
from aiogram.types import Message, User, Chat

from bot.handlers.common import show_help, cmd_get_id


@pytest.mark.asyncio
async def test_show_help_displays_user_chat_id():
    # Mock message
    message = MagicMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 123456789
    
    user = MagicMock(spec=User)
    user.id = 123456789
    user.full_name = "Ali Valiyev"
    user.username = "alivaliyev"
    message.from_user = user
    
    message.answer = AsyncMock()

    await show_help(message)

    message.answer.assert_called_once()
    sent_text = message.answer.call_args[0][0]
    
    # Check that chat id is clearly included
    assert "123456789" in sent_text
    assert "Sizning Telegram Chat ID:" in sent_text
    assert "Ali Valiyev" in sent_text


@pytest.mark.asyncio
async def test_cmd_get_id_displays_chat_id():
    message = MagicMock(spec=Message)
    message.chat = MagicMock(spec=Chat)
    message.chat.id = 987654321
    
    user = MagicMock(spec=User)
    user.id = 987654321
    user.full_name = "Sardor Azimov"
    user.username = "sardor"
    message.from_user = user
    
    message.answer = AsyncMock()

    await cmd_get_id(message)

    message.answer.assert_called_once()
    sent_text = message.answer.call_args[0][0]
    
    assert "987654321" in sent_text
    assert "Sardor Azimov" in sent_text
    assert "@sardor" in sent_text
