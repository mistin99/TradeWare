import pytest
from fastapi import HTTPException
from unittest.mock import Mock

from trade_ware.core.security import create_access_token, get_current_user


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
