from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()


books = [
    {
        "id": 1,
        "title": "Асинхронность в Python",
        "author": "Мэттью",
    },
    {
        "id": 2,
        "title": "Backend разработка в Python",
        "author": "Артём",
    },
]


class BookSchema(BaseModel):
    title: str
    author: str


@app.get("/books",
         tags=["Книги 📚"],
         summary="Получить список книг",
         description="<h1>Отдает список всех книг</h1>",
)
def get_books():
    return books


@app.post("/books", 
          tags=["Книги 📚"], 
          summary="Добавить книгу")
def add_book(book: BookSchema):
    new_book_id = len(books) + 1
    books.append({
        "id": new_book_id,
        "title": book.title,
        "author": book.author
    })
    return {"success": True, "message": "Книга добавлена"}


@app.put("/books/{book_id}", 
         tags=["Книги 📚"],
         summary="Изменить книгу")
def change_book(book_id: int, data: BookSchema):
    match = [book for book in books if book["id"] == book_id]
    if not match:
        raise HTTPException(status_code=404, detail="Книга с таким id не найдена")
    match[0] |= data.model_dump()
    return {"success": True, "message": "Книга обновлена"}

# ============

@app.delete("/books/{book_id}", 
            tags=["Книги 📚"],
            summary="Удалить книгу")
def delete_book(book_id: int):
    match = [book for book in books if book["id"] == book_id]
    if not match:
        raise HTTPException(status_code=404, detail="Книга с таким id не найдена")
    books.remove(match[0])
    return {"success": True, "message": "Книга удалена"}