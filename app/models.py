from sqlalchemy import ForeignKey, String, Text, Boolean, UniqueConstraint, Index
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import List


class Base(DeclarativeBase):
    pass


class Cafe(Base):
    __tablename__ = "cafes"
    __table_args__ = (
        UniqueConstraint("title", "city", name="uq_cafe_title_city"),
        Index('idx_cafe_city', 'city'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[str] = mapped_column(String(500), nullable=True)

    category_associations: Mapped[List["CafeCategory"]] = relationship(
        back_populates="cafe", cascade="all, delete-orphan"
    )

    @property
    def best_for(self) -> "Category":
        for assoc in self.category_associations:
            if assoc.is_best:
                return assoc.category
        return None

    @property
    def also_good_for(self) -> List["Category"]:
        return [assoc.category for assoc in self.category_associations if not assoc.is_best]

    def __repr__(self):
        return f"<Cafe(id={self.id}, title='{self.title}', city='{self.city}')>"


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (Index('idx_category_name', 'name'),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    cafe_associations: Mapped[List["CafeCategory"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class CafeCategory(Base):
    __tablename__ = "cafe_categories"
    __table_args__ = (
        UniqueConstraint("cafe_id", "category_id", name="uq_cafe_category"),
        Index('idx_cafe_category_cafe_id', 'cafe_id'),
        Index('idx_cafe_category_category_id', 'category_id'),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cafe_id: Mapped[int] = mapped_column(ForeignKey("cafes.id"), nullable=False)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    is_best: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    cafe: Mapped["Cafe"] = relationship(back_populates="category_associations")
    category: Mapped["Category"] = relationship(back_populates="cafe_associations")

    def __repr__(self):
        return f"<CafeCategory(id={self.id}, cafe_id={self.cafe_id}, category_id={self.category_id}, " \
               f"is_best={self.is_best})>"
