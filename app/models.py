# Database schemas (SQLAlchemy)
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# Mixins
class TimestampMixin:
    """Mixin to add created and updated timestamps."""
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc)
    )
    
class SoftDeleteMixin:
    """Mixin to add soft delete functionality."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    @property
    def is_deleted(self) -> bool:
        return self.deleted_at is not None
    
    def delete(self) -> None:
        self.deleted_at = datetime.now(timezone.utc)
    
    def restore(self) -> None:
        self.deleted_at = None

# Models
class User(UserMixin, TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    
    # Relationships: One user has many notes
    # back_populates ensures both sides of the relationship are aware of each other
    notes: Mapped[List['Note']] = relationship(back_populates='author', cascade="all, delete-orphan")

    def set_password(self, password: str) -> None:
        """Hash the password and store it in the database"""
        self.password_hash = generate_password_hash(password) 

    def check_password(self, password: str) -> bool:
        """Check if the provided password matches the stored hash"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Note(TimestampMixin, SoftDeleteMixin, db.Model):
    __tablename__ = 'notes'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    content: Mapped[str] = mapped_column(db.Text, nullable=False)
    user_id: Mapped[int] = mapped_column(db.ForeignKey("users.id"), index=True)
    
    # Relationships: One note belongs to one user
    # back_populates ensures both sides of the relationship are aware of each other
    author: Mapped['User'] = relationship(back_populates='notes')
    
    def __repr__(self):
        return f'<Note {self.title}>'
    