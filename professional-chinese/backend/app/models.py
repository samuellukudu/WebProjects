from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON, Boolean, ARRAY
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
    
    # Remove the user relationship for now
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User", back_populates="progress")
    
    vocabulary = relationship("Vocabulary", back_populates="progress")

class LearningGoal(Base):
    __tablename__ = "learning_goals"

    id = Column(Integer, primary_key=True, index=True)
    prompt = Column(String)
    target_level = Column(Integer)
    focus_categories = Column(JSON)  # Store categories as a JSON array
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_updated = Column(DateTime(timezone=True), server_default=func.now())
    
    # Add any user relationship if you implement authentication later
    # user_id = Column(Integer, ForeignKey("users.id"))
    # user = relationship("User", back_populates="learning_goals")

class PersonalizedLesson(Base):
    __tablename__ = "personalized_lessons"

    id = Column(Integer, primary_key=True, index=True)
    goal_id = Column(Integer, ForeignKey("learning_goals.id"))
    vocabulary_ids = Column(JSON)  # Store as JSON array
    difficulty_level = Column(Integer)
    focus_category = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed = Column(Boolean, default=False)
    
    goal = relationship("LearningGoal", backref="lessons")

class WeeklyLesson(Base):
    __tablename__ = "weekly_lessons"

    id = Column(Integer, primary_key=True, index=True)
    focus = Column(String)
    vocabulary_focus = Column(JSON)  # Store as JSON array
    grammar_points = Column(JSON)    # Store as JSON array
    status = Column(String)          # 'not_started', 'in_progress', 'completed'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
