from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import selectinload
from typing import List, Optional
from app.config import Config
from app.database import async_session, create_tables
from app.models import Cafe, Category, CafeCategory
from app.schemas import CafeCreate, CafeResponse, UserRead, UserCreate
from app.auth import User, backend, fastapi_users
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app = FastAPI(title=Config.APP_TITLE, version=Config.APP_VERSION,
              description=Config.APP_DESCRIPTION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

app.include_router(fastapi_users.get_auth_router(backend), prefix="/auth/jwt", tags=["auth"])
app.include_router(fastapi_users.get_register_router(UserRead, UserCreate), prefix="/auth", tags=["auth"])


@asynccontextmanager
async def lifespan():
    await create_tables()
    yield


app.lifespan = lifespan


async def get_db():
    async with async_session() as db:
        yield db


@app.get("/cafes", response_model=List[CafeResponse])
async def get_cafes(
        city: Optional[str] = None,
        best_for: Optional[str] = None,
        also_good_for: Optional[List[str]] = None,
        db: AsyncSession = Depends(get_db)):

    category_names = set()
    if best_for:
        category_names.add(best_for)
    if also_good_for:
        category_names.update(also_good_for)

    if category_names:
        result = await db.execute(select(Category.name).filter(Category.name.in_(category_names)))
        found_categories = {row[0] for row in result.all()}

        missing = category_names - found_categories
        if missing:
            raise HTTPException(status_code=400, detail=f"Categories do not exist: {', '.join(missing)}")

    query = select(Cafe).options(selectinload(Cafe.category_associations).selectinload(CafeCategory.category))

    if city:
        query = query.filter(Cafe.city.ilike(f"%{city}%"))

    if best_for or also_good_for:
        query = query.join(CafeCategory).join(Category)

    if best_for:
        query = query.filter(Category.name == best_for, CafeCategory.is_best is True)

    if also_good_for:
        query = query.filter(Category.name.in_(also_good_for), CafeCategory.is_best is False)

    result = await db.execute(query.distinct())
    cafes = result.scalars().all()

    return [CafeResponse.from_orm(c) for c in cafes]


@app.post("/cafes", response_model=CafeResponse)
async def create_cafe(
        cafe: CafeCreate,
        db: AsyncSession = Depends(get_db),
        _current_user: User = Depends(fastapi_users.current_user(active=True))):

    category_names = {cafe.best_for}
    if cafe.also_good_for:
        category_names.update(cafe.also_good_for)
    result = await db.execute(select(Category).filter(Category.name.in_(category_names)))
    valid_categories = {cat.name: cat for cat in result.scalars().all()}

    if cafe.best_for not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Category {cafe.best_for} does not exist")
    for cat_name in cafe.also_good_for:
        if cat_name not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Category {cat_name} does not exist")

    db_cafe = Cafe(
        title=cafe.title,
        city=cafe.city,
        description=cafe.description,
        image_url=cafe.image_url
    )
    try:
        db.add(db_cafe)
        await db.flush()

        db.add(CafeCategory(cafe_id=db_cafe.id, category_id=valid_categories[cafe.best_for].id, is_best=True))
        for cat_name in cafe.also_good_for:
            db.add(CafeCategory(cafe_id=db_cafe.id, category_id=valid_categories[cat_name].id, is_best=False))

        await db.commit()
        await db.refresh(db_cafe)
        return CafeResponse.from_orm(db_cafe)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Cafe with this title and city already exists")


@app.put("/cafes/{cafe_id}", response_model=CafeResponse)
async def update_cafe(
        cafe_id: int,
        cafe: CafeCreate,
        db: AsyncSession = Depends(get_db),
        _current_user: User = Depends(fastapi_users.current_user(active=True))):
    result = await db.execute(select(Cafe).filter_by(id=cafe_id))
    db_cafe = result.scalars().first()
    if not db_cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    category_names = {cafe.best_for}
    if cafe.also_good_for:
        category_names.update(cafe.also_good_for)
    result = await db.execute(select(Category).filter(Category.name.in_(category_names)))
    valid_categories = {cat.name: cat for cat in result.scalars().all()}

    if cafe.best_for not in valid_categories:
        raise HTTPException(status_code=400, detail=f"Category {cafe.best_for} does not exist")
    for cat_name in cafe.also_good_for:
        if cat_name not in valid_categories:
            raise HTTPException(status_code=400, detail=f"Category {cat_name} does not exist")

    db_cafe.title = cafe.title
    db_cafe.city = cafe.city
    db_cafe.description = cafe.description
    db_cafe.image_url = cafe.image_url

    try:
        await db.execute(delete(CafeCategory).filter_by(cafe_id=db_cafe.id))
        db.add(CafeCategory(cafe_id=db_cafe.id, category_id=valid_categories[cafe.best_for].id, is_best=True))
        for cat_name in cafe.also_good_for:
            db.add(CafeCategory(cafe_id=db_cafe.id, category_id=valid_categories[cat_name].id, is_best=False))

        await db.commit()
        await db.refresh(db_cafe)
        return CafeResponse.from_orm(db_cafe)

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Cafe with this title and city already exists")


@app.delete("/cafes/{cafe_id}")
async def delete_cafe(
        cafe_id: int,
        db: AsyncSession = Depends(get_db),
        _current_user: User = Depends(fastapi_users.current_user(active=True))):
    result = await db.execute(select(Cafe).filter_by(id=cafe_id))
    db_cafe = result.scalars().first()
    if not db_cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")

    await db.execute(delete(CafeCategory).filter_by(cafe_id=db_cafe.id))
    await db.delete(db_cafe)
    await db.commit()
    return {"message": "Cafe deleted"}


async def recommend_similar_cafes(cafe_id: int, db: AsyncSession):
    result = await db.execute(select(Cafe).filter_by(id=cafe_id))
    target_cafe = result.scalars().first()

    if not target_cafe:
        raise HTTPException(status_code=404, detail="Cafe not found")
    result = await db.execute(select(Cafe))
    cafes = result.scalars().all()
    if len(cafes) <= 1:
        return []
    texts = [f"{cafe.description} {cafe.best_for} {' '.join(cafe.also_good_for)}" for cafe in cafes]
    vectorizer = TfidfVectorizer()
    x = vectorizer.fit_transform(texts)
    similarities = cosine_similarity(x)
    cafe_idx = [c.id for c in cafes].index(cafe_id)
    similar_indices = np.argsort(similarities[cafe_idx])[::-1][1:4]
    return [CafeResponse.from_orm(cafes[i]) for i in similar_indices]


@app.get("/cafes/{cafe_id}/recommend", response_model=List[CafeResponse])
async def get_recommendations(cafe_id: int, db: AsyncSession = Depends(get_db)):
    return await recommend_similar_cafes(cafe_id, db)


@app.get("/categories", response_model=List[dict])
async def get_categories(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Category))
    categories = result.scalars().all()
    return [{"id": cat.id, "name": cat.name} for cat in categories]
