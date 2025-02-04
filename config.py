
from typing import List, Optional
from pydantic import BaseModel

from typing import List
from pydantic import BaseModel

class SubQuestion(BaseModel):
    question_number: int
    question: str

class QuestionList(BaseModel):
    question_context: str
    questions: List[SubQuestion]
