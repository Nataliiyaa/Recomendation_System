from pydantic import BaseModel, Field
from typing import Optional

class Movie(BaseModel):
    id: int = Field(..., description="Уникальный идентификатор фильма (movieId)")
    title: str = Field(..., description="Название фильма")
    genres: str = Field(..., description="Жанры фильма через |")

class Rating(BaseModel):
    user_id: int = Field(..., description="ID пользователя")
    movie_id: int = Field(..., description="ID фильма")
    rating: float = Field(..., ge=1, le=5, description="Оценка от 1 до 5")
