import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from trade_ware.database.base import Base
from trade_ware.models.user import User
from trade_ware.schemas.profile import ProfileUpdate
from trade_ware.services.profile_service import ProfileService


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_profile_is_incomplete_without_required_fields(db_session):
    user = User(
        email="person@example.com",
        password_hash="hashed",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    result = ProfileService.get_profile(db_session, user)

    assert result.is_verified is True
    assert result.profile_completed is False
    assert result.first_name is None
    assert result.last_name is None


def test_profile_update_completes_profile(db_session):
    user = User(
        email="person@example.com",
        password_hash="hashed",
        is_verified=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    partial = ProfileService.update_profile(
        db_session, user, ProfileUpdate(first_name="Ada")
    )
    complete = ProfileService.update_profile(
        db_session, user, ProfileUpdate(last_name="Lovelace")
    )

    assert partial.profile_completed is False
    assert complete.profile_completed is True
    assert complete.first_name == "Ada"
    assert complete.last_name == "Lovelace"
