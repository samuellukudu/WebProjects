from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

class Vocabulary(Base):
    __tablename__ = "vocabulary"

    id = Column(Integer, primary_key=True, index=True)
    chinese_simplified = Column(String)
    chinese_traditional = Column(String)
    pinyin = Column(String)
    english = Column(String)
    context_category = Column(String)
    difficulty_level = Column(Integer)
    usage_examples = Column(JSON)
    
    # Relationships
    progress = relationship("UserProgress", back_populates="vocabulary")

class UserProgress(Base):
    __tablename__ = "user_progress"

    id = Column(Integer, primary_key=True, index=True)
    vocabulary_id = Column(Integer, ForeignKey("vocabulary.id"))
    proficiency_level = Column(Integer, default=0)
    last_reviewed = Column(DateTime(timezone=True), server_default=func.now())
    next_review = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    vocabulary = relationship("Vocabulary", back_populates="progress")
