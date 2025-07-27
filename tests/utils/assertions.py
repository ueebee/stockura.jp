# -*- coding: utf-8 -*-
from app.domain.exceptions.jquants_exceptions import (
    AuthenticationError,
    ValidationError,
    DataNotFoundError,
    NetworkError,
    TokenRefreshError
)


def assert_authentication_error(exc_info, expected_message):
    assert isinstance(exc_info.value, AuthenticationError)
    assert expected_message in str(exc_info.value)


def assert_validation_error(exc_info, expected_message):
    assert isinstance(exc_info.value, ValidationError)
    assert expected_message in str(exc_info.value)


def assert_data_not_found_error(exc_info, expected_message):
    assert isinstance(exc_info.value, DataNotFoundError)
    assert expected_message in str(exc_info.value)


def assert_network_error(exc_info, expected_message):
    assert isinstance(exc_info.value, NetworkError)
    assert expected_message in str(exc_info.value)


def assert_token_refresh_error(exc_info, expected_message):
    assert isinstance(exc_info.value, TokenRefreshError)
    assert expected_message in str(exc_info.value)