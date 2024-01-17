from pydantic import BaseModel
from datetime import datetime


class NewsArticle(BaseModel):
    Article: str
    Heading: str
    Date: datetime
    NewsType: str