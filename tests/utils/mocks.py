# -*- coding: utf-8 -*-
from unittest.mock import AsyncMock, MagicMock
from typing import Optional, Dict, Any


def create_mock_response(status=200, json_data=None, text=""):
    mock_response = MagicMock()
    mock_response.status = status
    mock_response.text = text
    mock_response.json = AsyncMock(return_value=json_data or {})
    return mock_response


def create_mock_redis_client():
    mock = MagicMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=False)
    mock.expire = AsyncMock(return_value=True)
    mock.ttl = AsyncMock(return_value=-1)
    return mock


def create_mock_aiohttp_session():
    mock_session = MagicMock()
    mock_context = MagicMock()
    mock_session.post = MagicMock(return_value=mock_context)
    mock_session.get = MagicMock(return_value=mock_context)
    mock_session.put = MagicMock(return_value=mock_context)
    mock_session.delete = MagicMock(return_value=mock_context)
    mock_context.__aenter__ = AsyncMock()
    mock_context.__aexit__ = AsyncMock()
    return mock_session