from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from .. import models
from ..database import get_db
from pydantic import BaseModel

router = APIRouter()

class VocabularyBase(BaseModel):
    chinese_simplified: str
    chinese_traditional: Optional[str] = None
    pinyin: str
    english: str
    context_category: str
    difficulty_level: int
    usage_examples: dict

class VocabularyCreate(VocabularyBase):
    pass

class Vocabulary(VocabularyBase):
    id: int

    class Config:
        orm_mode = True

@router.post("/", response_model=Vocabulary)
async def create_vocabulary(
    vocabulary: VocabularyCreate,
    db: Session = Depends(get_db)
):
    db_vocabulary = models.Vocabulary(**vocabulary.dict())
    db.add(db_vocabulary)
    db.commit()
    db.refresh(db_vocabulary)
    return db_vocabulary

@router.get("/", response_model=List[Vocabulary])
async def get_vocabulary(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    difficulty: Optional[int] = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Vocabulary)
    
    if category:
        query = query.filter(models.Vocabulary.context_category == category)
    if difficulty:
        query = query.filter(models.Vocabulary.difficulty_level == difficulty)
    
    return query.offset(skip).limit(limit).all()

@router.get("/{vocabulary_id}", response_model=Vocabulary)
async def get_vocabulary_by_id(
    vocabulary_id: int,
    db: Session = Depends(get_db)
):
    vocabulary = db.query(models.Vocabulary).filter(models.Vocabulary.id == vocabulary_id).first()
    if vocabulary is None:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    return vocabulary

@router.get("/categories/list")
async def get_categories(
    db: Session = Depends(get_db)
):
    categories = db.query(models.Vocabulary.context_category).distinct().all()
    return [category[0] for category in categories]

@router.get("/search/{query}")
async def search_vocabulary(
    query: str,
    db: Session = Depends(get_db)
):
    # Search in both Chinese and English
    results = db.query(models.Vocabulary).filter(
        (models.Vocabulary.chinese_simplified.ilike(f"%{query}%")) |
        (models.Vocabulary.english.ilike(f"%{query}%"))
    ).all()
    return results
