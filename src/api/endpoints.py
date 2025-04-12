from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from src.models.models import Movie, Rating
from src.recommender import MovieRecommender
from typing import List
import pandas as pd
from datetime import datetime, timedelta

router = APIRouter()

# Инициализация рекомендательной системы
recommender = MovieRecommender(movies_path="src/archive/movies.csv", ratings_path="src/archive/ratings.csv")


@router.get(
        "/recommend/{title}",
        tags=["Рекомендации"],
        summary="Получить рекомендации фильмов по названию фильма",
        response_class=JSONResponse)
def recommend_movies(
    title: str,
    top_n: int = Query(10, ge=1, le=20, description="Количество рекомендаций (1-20)")
):
    """
    Возвращает JSON с рекомендованными фильмами по названию.
    """
    try:
        recommendations = recommender.recommend_by_title(title, top_n)
        return JSONResponse(content={"recommendations": recommendations})
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get(
    "/movies",
    tags=["Фильмы"],
    summary="Получить список всех фильмов",
    response_class=JSONResponse)
async def get_movies():
    movies = pd.read_csv('src/archive/movies.csv')
    return JSONResponse(content=movies[['movieId', 'title', 'genres']].to_dict(orient='records'))


# 3. Получить информацию о фильме по ID
@router.get(
    "/movies/{movie_id}",
    tags=["Фильмы"],
    summary="Получить информацию о фильме по ID",
    response_class=JSONResponse)
async def get_movie_by_id(movie_id: int):
    movies = pd.read_csv('src/archive/movies.csv')
    movie = movies[movies['movieId'] == movie_id]
    if movie.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
    return JSONResponse(content=movie.iloc[0].to_dict())


# 4. Топ фильмов по рейтингу
@router.get(
    "/top_movies",
    tags=["Фильмы"],
    summary="Получить топ фильмов по среднему рейтингу",
    response_class=JSONResponse)
async def get_top_movies(top_n: int = 10):
    ratings = pd.read_csv('src/archive/ratings.csv')
    movies = pd.read_csv('src/archive/movies.csv')
    avg_ratings = ratings.groupby('movieId')['rating'].mean().sort_values(ascending=False).head(top_n)
    top_movies = movies[movies['movieId'].isin(avg_ratings.index)]
    return JSONResponse(content=top_movies[['movieId', 'title', 'genres']].to_dict(orient='records'))


# 5. Получить фильмы по жанру
@router.get(
    "/movies/genre/{genre}",
    tags=["Фильмы"],
    summary="Получить фильмы по жанру",
    response_class=JSONResponse)
async def get_movies_by_genre(genre: str):
    movies = pd.read_csv('src/archive/movies.csv')
    filtered_movies = movies[movies['genres'].str.contains(genre, case=False, na=False)]
    return JSONResponse(content=filtered_movies[['movieId', 'title', 'genres']].to_dict(orient='records'))


# 6. Поиск фильмов по названию
@router.get(
    "/movies/search/{title}",
    tags=["Фильмы"],
    summary="Поиск фильма по названию",
    response_class=JSONResponse)
async def search_movies_by_title(title: str):
    movies = pd.read_csv('src/archive/movies.csv')
    matching_movies = movies[movies['title'].str.contains(title, case=False, na=False)]
    return JSONResponse(content=matching_movies[['movieId', 'title', 'genres']].to_dict(orient='records'))


# 7. Рейтинг фильма
@router.get(
    "/movies/{movie_id}/rating",
    tags=["Фильмы"],
    summary="Получить рейтинг фильма",
    response_class=JSONResponse)
async def get_movie_rating(movie_id: int):
    ratings = pd.read_csv('src/archive/ratings.csv')
    movie_ratings = ratings[ratings['movieId'] == movie_id]
    if movie_ratings.empty:
        raise HTTPException(status_code=404, detail="Movie not found")
    return JSONResponse(content=movie_ratings['rating'].mean())


# 8. Количество рейтингов для фильма
@router.get(
    "/movies/{movie_id}/rating_count",
    tags=["Фильмы"],
    summary="Получить количество рейтингов для фильма",
    response_class=JSONResponse)
async def get_movie_rating_count(movie_id: int):
    ratings = pd.read_csv('src/archive/ratings.csv')
    movie_ratings = ratings[ratings['movieId'] == movie_id]
    return JSONResponse(content=movie_ratings.shape[0])


# 9. Получить фильмы с рейтингами за последние 30 дней
@router.get(
    "/recent_ratings",
    tags=["Фильмы"],
    summary="Получить фильмы, оцененные за последние N месяцев",
    response_class=JSONResponse)
async def get_recent_ratings(months: int = Query(1, ge=1, description="Количество месяцев для фильтрации")):
    try:
        # Загрузим данные из файлов
        ratings = pd.read_csv('src/archive/ratings.csv')
        movies = pd.read_csv('src/archive/movies.csv')

        # Преобразуем timestamp в datetime
        ratings['timestamp'] = pd.to_datetime(ratings['timestamp'], unit='s')

        # Вычисляем дату N месяцев назад
        months_ago = datetime.now() - timedelta(days=months * 30)

        # Отфильтровываем рейтинги, которые были поставлены после этой даты
        recent_ratings = ratings[ratings['timestamp'] > months_ago]

        # Получаем уникальные movieId из последних N месяцев
        recent_movie_ids = recent_ratings['movieId'].unique()

        # Получаем названия фильмов, соответствующие этим ID
        recent_movies = movies[movies['movieId'].isin(recent_movie_ids)]

        # Составляем список фильмов с их ID и названиями
        result = recent_movies[['movieId', 'title']].to_dict(orient='records')

        return JSONResponse(content={"recent_movies": result})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 10. Получить рекомендации для фильма по ID
@router.get(
    "/movies/{movie_id}",
    tags=["Рекомендации"],
    summary="Получить рекомендации для фильма по ID",
    response_class=JSONResponse)
async def get_movie_recommendations(
    movie_id: int, 
    top_n: int = Query(10, ge=1, le=20, description="Количество рекомендаций (1-20)")):
    try:
        # Получаем название фильма по ID
        title = recommender.get_movie_title_by_id(movie_id)
        
        # Используем уже существующую функцию для рекомендаций по названию
        recommendations = recommender.recommend_by_title(title, top_n)
        
        return JSONResponse(content={"recommendations": recommendations})
    
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
