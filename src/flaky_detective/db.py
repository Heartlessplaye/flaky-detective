from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .models import Base


def make_session_factory(url: str = "sqlite:///flaky.db"):
    engine = create_engine(url)
    Base.metadata.create_all(engine)
    return sessionmaker(engine, expire_on_commit=False)
