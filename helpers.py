import os
import pymupdf
import json
from groq import Groq
from config import QuestionList

groq = Groq()

def extract_text(file_path):
    """
    Extracts text from a PDF, PPTX, or TXT file.

    Args:
        file_path (str): Path to the file.

    Returns:
        str: Extracted text from the file.
    """
    # Check if the file exists
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    # Get the file extension
    file_extension = os.path.splitext(file_path)[1].lower()

    potential_already_extracted = f"text_extractions/{file_path.split('/')[-1]}.txt"
    if os.path.exists(potential_already_extracted):
        return open(potential_already_extracted, 'r').read()
    else:
    # Extract text based on file type
        if file_extension == '.pdf':
            return extract_text_from_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    text = ""
    doc = pymupdf.open(file_path)
    for page in doc:
        text += page.get_text()
    with open(f"text_extractions/{file_path}.txt", 'w') as f:
        f.write(text)
    return text


def write_text_to_extractions_folder(text, file_path):
    file_name = file_path.split('/')[-1]
    new_path = f"text_extractions/{file_name}"
    with open(new_path, 'w') as f:
        f.write(text)
    return new_path


import json

def get_questions(homework: str) -> QuestionList:
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are a question parser that extracts the context of the entire question set and lists the sub-questions in JSON format. "
                f"Use this schema to structure your response: {json.dumps(QuestionList.model_json_schema(), indent=2)}",
            },
            {
                "role": "user",
                "content": f"Generate a question list for the following text:\n\n{homework}",
            },
        ],
        model="llama3-70b-8192",
        temperature=0,
        response_format={"type": "json_object"},
    )
    
    # Parse the JSON response to match the defined Pydantic model
    return QuestionList.model_validate_json(chat_completion.choices[0].message.content)

def answer_question(question: str):
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": "You are an expert statistician and data scientest that specializes in answer homework questions"
            },
            {
                "role": "user",
                "content": f"Answer this question:\n{question}",
            },
        ],
        model="llama3-70b-8192",
        temperature=0.2,
    )
    
    # Parse the JSON response to match the defined Pydantic model
    return chat_completion.choices[0].message.content