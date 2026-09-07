from datetime import datetime, timezone
from typing import Optional, List, Any
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    JSON,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone_number: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    role: Mapped[str] = mapped_column(String(32), default="user", nullable=False) # 'super_admin', 'admin', 'user'
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="user", cascade="all, delete-orphan")


class Test(Base):
    __tablename__ = "tests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, index=True, default="STANDART", nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question_count: Mapped[int] = mapped_column(Integer, default=45, nullable=False)
    time_limit_min: Mapped[int] = mapped_column(Integer, default=150, nullable=False)
    created_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    questions: Mapped[List["Question"]] = relationship("Question", back_populates="test", cascade="all, delete-orphan", order_by="Question.order_no")
    question_groups: Mapped[List["QuestionGroup"]] = relationship("QuestionGroup", back_populates="test", cascade="all, delete-orphan")
    attempts: Mapped[List["Attempt"]] = relationship("Attempt", back_populates="test", cascade="all, delete-orphan")


class QuestionGroup(Base):
    __tablename__ = "question_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    shared_context_text: Mapped[str] = mapped_column(Text, nullable=False)
    shared_image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    shared_options: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)  # {"A": "...", "B": "...", "C": "...", "D": "...", "E": "...", "F": "..."}

    test: Mapped["Test"] = relationship("Test", back_populates="question_groups")
    questions: Mapped[List["Question"]] = relationship("Question", back_populates="group")


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    group_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("question_groups.id", ondelete="SET NULL"), nullable=True)
    order_no: Mapped[int] = mapped_column(Integer, nullable=False)  # 1 dan 45 gacha
    type: Mapped[str] = mapped_column(String(32), nullable=False)   # 'Y-1', 'GROUPED', 'O'
    text: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    options: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)      # {"A": "...", "B": "...", "C": "...", "D": "..."}
    sub_parts: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)    # [{"label": "a", "correct_answer": "12", "difficulty_b": 0.4}, ...]
    correct_answer: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Y-1 va GROUPED uchun (masalan "B")
    difficulty_b: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)    # Rasch b-parametr
    section: Mapped[str] = mapped_column(String(128), default="Matematika", nullable=False)

    test: Mapped["Test"] = relationship("Test", back_populates="questions")
    group: Mapped[Optional["QuestionGroup"]] = relationship("QuestionGroup", back_populates="questions")
    answers: Mapped[List["AttemptAnswer"]] = relationship("AttemptAnswer", back_populates="question", cascade="all, delete-orphan")


class Attempt(Base):
    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    test_id: Mapped[int] = mapped_column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="in_progress", nullable=False) # 'in_progress', 'completed', 'timed_out'
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    finished_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    raw_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    theta: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    standard_error: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    final_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    is_certified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="attempts")
    test: Mapped["Test"] = relationship("Test", back_populates="attempts")
    answers: Mapped[List["AttemptAnswer"]] = relationship("AttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")


class AttemptAnswer(Base):
    __tablename__ = "attempt_answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    attempt_id: Mapped[int] = mapped_column(Integer, ForeignKey("attempts.id", ondelete="CASCADE"), nullable=False)
    question_id: Mapped[int] = mapped_column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False)
    sub_part_label: Mapped[Optional[str]] = mapped_column(String(16), nullable=True) # "a", "b" yoki null
    user_answer: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    answered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    attempt: Mapped["Attempt"] = relationship("Attempt", back_populates="answers")
    question: Mapped["Question"] = relationship("Question", back_populates="answers")
