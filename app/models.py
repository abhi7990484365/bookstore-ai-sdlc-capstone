from pydantic import BaseModel, Field

class Book(BaseModel):
    id: int
    title: str
    author: str
    category: str
    format: str
    language: str
    publication_date: str
    customer_rating: float = Field(ge=0, le=5)
    price: float = Field(ge=0)
