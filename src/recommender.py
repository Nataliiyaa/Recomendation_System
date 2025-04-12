import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from difflib import get_close_matches


class MovieRecommender:
    def __init__(self, movies_path: str, ratings_path: str):
        self.movies = pd.read_csv(movies_path)
        self.ratings = pd.read_csv(ratings_path)

        # Очистка
        self.ratings = self.ratings.query("0 < rating < 6")
        self.ratings.drop(['timestamp'], axis=1, inplace=True)

        # Матрица пользователь-фильм
        user_item_matrix = self.ratings.pivot(index='movieId', columns='userId', values='rating')
        user_item_matrix.fillna(0, inplace=True)

        # Фильтрация активных пользователей и популярных фильмов
        users_votes = self.ratings.groupby('userId')['rating'].count()
        movies_votes = self.ratings.groupby('movieId')['rating'].count()
        user_mask = users_votes[users_votes > 50].index
        movie_mask = movies_votes[movies_votes > 10].index
        user_item_matrix = user_item_matrix.loc[movie_mask, user_mask]

        self.user_item_matrix = user_item_matrix.rename_axis(None, axis=1).reset_index()
        self.csr_data = csr_matrix(self.user_item_matrix.drop('movieId', axis=1).values)

        # Обучение модели
        self.knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
        self.knn.fit(self.csr_data)

    def recommend_by_title(self, movie_title: str, top_n: int = 10):
        # Поиск похожего названия
        all_titles = self.movies['title'].tolist()
        matches = get_close_matches(movie_title, all_titles, n=1, cutoff=0.6)
        if not matches:
            return {"error": f"No movie found matching title '{movie_title}'"}
        matched_title = matches[0]

        # Получаем movieId
        movie_id = self.movies[self.movies['title'] == matched_title].iloc[0]['movieId']

        # Проверка: есть ли этот movieId в user_item_matrix
        try:
            matrix_index = self.user_item_matrix[self.user_item_matrix['movieId'] == movie_id].index[0]
        except IndexError:
            return {"error": f"Movie '{matched_title}' not found in filtered rating data."}

        # Получение похожих фильмов
        distances, indices = self.knn.kneighbors(self.csr_data[matrix_index], n_neighbors=top_n + 1)
        indices_distances = list(zip(indices.squeeze().tolist(), distances.squeeze().tolist()))[1:]

        # Формируем список рекомендаций
        recommendations = []
        for idx, dist in indices_distances:
            recommended_movie_id = self.user_item_matrix.iloc[idx]['movieId']
            title = self.movies[self.movies['movieId'] == recommended_movie_id]['title'].values[0]
            recommendations.append({'title': title, 'distance': dist})

        return {
            "input_title": movie_title,
            "matched_title": matched_title,
            "recommendations": recommendations
        }
    
    # Функция для получения названия фильма по его ID
    def get_movie_title_by_id(self, movie_id: int) -> str:
        movie = self.movies[self.movies['movieId'] == movie_id]
        if not movie.empty:
            return movie['title'].values[0]
        else:
            raise ValueError("Movie not found")
