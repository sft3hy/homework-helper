
from typing import List
from pydantic import BaseModel


class SubQuestion(BaseModel):
    question_number: int
    question_context: str
    individual_question_list: List[str]

class QuestionList(BaseModel):
    questions: List[SubQuestion]
