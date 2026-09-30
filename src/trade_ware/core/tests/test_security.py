from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from trade_ware.core.security import (
    create_access_token,
    create_refresh_token,
    get_current_user,
)


def test_access_token_identifies_user():
    credentials = Mock(credentials=create_access_token(42))
    user = Mock(id=42)
    db = Mock()
    db.query.return_value.filter.return_value.first.return_value = user

    result = get_current_user(credentials, db)

    assert result is user


def test_invalid_access_token_is_unauthorized():
    credentials = Mock(credentials="invalid-token")

    with pytest.raises(HTTPException) as error:
        get_current_user(credentials, Mock())

    assert error.value.status_code == 401


def test_refresh_token_is_not_accepted_as_access_token():
    credentials = Mock(credentials=create_refresh_token(42))

    with pytest.raises(HTTPException) as error:
        get_current_user(credentials, Mock())

    assert error.value.status_code == 401
