"""
core.py  – minimal DB layer 

Users
 create_user(...)
 delete_user(user_id)

Universities
 create_university(...)
 delete_university(university_id)

User ↔ University links
 add_university_to_user(user_id, university_id)
 remove_university_from_user(user_id, university_id)

Documents
 add_document(...)
 delete_document(document_id)

Helper
 get_session()
"""

import os
import datetime as dt
from contextlib import contextmanager
from typing import Optional

from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, Date, Text, Enum, TIMESTAMP, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import registry, relationship, Session, Mapped, mapped_column
from sqlalchemy.sql import func
from passlib.context import CryptContext

# DB CONNECTION
# ───────────────────────────────

DATABASE_URL: str = os.getenv(
    "DATABASE_URL",
    "postgresql://teduco-user:changeme@localhost:5432/teduco_db"
)

engine = create_engine(DATABASE_URL, echo=False, future=True)

# Declarative mappings
# ───────────────────────────────

mapper_registry = registry()
Base = mapper_registry.generate_base(metadata=MetaData(schema=None))

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_fname: Mapped[str] = mapped_column(String(50))
    user_lname: Mapped[str] = mapped_column(String(50))
    password_hash: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    birth_date: Mapped[Optional[dt.date]] = mapped_column(Date)

    # relationships ----- optional
    universities: Mapped[list["University"]] = relationship(
        secondary="user_universities",
        back_populates="users",
        cascade="all"
    )
    documents: Mapped[list["Document"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


class University(Base):
    __tablename__ = "universities"

    university_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    country: Mapped[str] = mapped_column(String(100), nullable=False)
    last_updated: Mapped[Optional[dt.datetime]] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True
    )

    users: Mapped[list[User]] = relationship(
        secondary="user_universities",
        back_populates="universities"
    )


class UserUniversity(Base):
    __tablename__ = "user_universities"
    __table_args__ = (
        UniqueConstraint("user_id", "university_id"),
    )

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        primary_key=True
    )
    university_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("universities.university_id", ondelete="CASCADE"),
        primary_key=True
    )


class Document(Base):
    __tablename__ = "documents"

    document_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.user_id", ondelete="CASCADE"),
        nullable=False
    )
    document_path: Mapped[str] = mapped_column(Text, nullable=False)
    document_type: Mapped[str] = mapped_column(
        Enum("transcript", "vpd", "cover_letter", name="document_type_enum"),
        nullable=False
    )
    uploaded_at: Mapped[dt.datetime] = mapped_column(
        TIMESTAMP(timezone=True),
        server_default=func.now()
    )

    user: Mapped[User] = relationship(back_populates="documents")


# Session helper

@contextmanager
def get_session() -> Session:
    """Context-manager that yields a SQLAlchemy Session and commits/rolls back."""
    session = Session(engine, expire_on_commit=False)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# CRUD FUNCTIONS
# ───────────────────────────────


# Users

def create_user(
    fname: str,
    lname: str,
    password: str,
    email: str,
    birth_date: Optional[str | dt.date] = None
) -> User:
    """Add a new user. Returns the persisted User object."""
    hashed = pwd_ctx.hash(password)
    if isinstance(birth_date, str):
        birth_date = dt.date.fromisoformat(birth_date)

    new_user = User(
        user_fname=fname,
        user_lname=lname,
        password_hash=hashed,
        email=email,
        birth_date=birth_date
    )
    with get_session() as s:
        s.add(new_user)
        s.flush()     # assign PK
        return new_user


def delete_user(user_id: int) -> None:
    with get_session() as s:
        user = s.get(User, user_id)
        if user:
            s.delete(user)


# Universities

def create_university(name: str, country: str) -> University:
    uni = University(name=name, country=country, last_updated=None)
    with get_session() as s:
        s.add(uni)
        s.flush()
        return uni


def delete_university(university_id: int) -> None:
    with get_session() as s:
        uni = s.get(University, university_id)
        if uni:
            s.delete(uni)



# User - University links

def add_university_to_user(user_id: int, university_id: int) -> None:
    with get_session() as s:
        # Ensures both exist
        s.add(UserUniversity(user_id=user_id, university_id=university_id))


def remove_university_from_user(user_id: int, university_id: int) -> None:
    with get_session() as s:
        link = (
            s.query(UserUniversity)
            .filter_by(user_id=user_id, university_id=university_id)
            .first()
        )
        if link:
            s.delete(link)


# Documents

def add_document(
    user_id: int,
    document_path: str,
    document_type: str  # 'transcript' | 'vpd' | 'cover_letter'
) -> Document:
    doc = Document(
        user_id=user_id,
        document_path=document_path,
        document_type=document_type
    )
    with get_session() as s:
        s.add(doc)
        s.flush()
        return doc


def delete_document(document_id: int) -> None:
    with get_session() as s:
        doc = s.get(Document, document_id)
        if doc:
            s.delete(doc)
