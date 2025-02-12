import os
import pymupdf
import json
from groq import Groq
from config import QuestionList
import re
from rpy2.robjects import r, default_converter
from rpy2.robjects.conversion import localconverter

original_dir = os.getcwd()
r(f'setwd("{original_dir}")')

json_parser_sys_prompt = """
You are a question parser for homework documents. Each homework is a large text, separated into sub questions (numbered) 
and those sub questions are composed of lettered individual questions. Infer the homework number from the top of the text.
Given an input text, you will output a JSON object with the following structure:
{
    "Homework_Number": "1"
    "Question_List": [
        {
            "question_number": "1",
            "question_context": "the text immediately following the question number",
            "individual_question_list": [
                { "question_letter": "a", "question": "a sample question for part a" }
                { "question_letter": "b", "question": "a sample question for part b" }
            ]
        },
        {
        "question_number": "2",
            "question_context": "the text immediately following the question number",
            "individual_question_list": [
                { "question_letter": "a", "question": "a sample question for part a" }
                { "question_letter": "b", "question": "a sample question for part b" }
            ]
        },
        ...
    ]
}
"""

answerer_prompt = """
You are an expert statistician and data scientist that specializes in answering homework questions.
Assume all necessary text files are downloaded at /Users/samueltownsend/Desktop/UCI/Winter_2025/R_class/Homework/HW<homework_number>/<filename>.txt
and when writing R code, make sure to read in the data and assume there is a header (header=True).
Not all files will need to write R code, so only write code when it's explicitly stated that there is a file in the question context.
You will be provided with a list of available data files to you - do not write any code that includes files not listed in the available files.
You can infer the homework number from the given input.
In your output, rewrite each question with the answer right below it.
"""


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


def get_questions(homework: str, file_path: str) -> QuestionList:
    # determine if there is a file at 'extracted_questions/<homework_name>
    clean_file_path = f"extracted_questions/{file_path.split('/')[-1]}.txt"
    if os.path.exists(clean_file_path):
        # read the file and parse it into a QuestionList object
        print("questions have already been extracted from homework document in the extracted_questions folder")
        with open(clean_file_path, 'r') as f:
            text = f.read()
            return text

    else:
        # extract the text from the PDF file and save it to a file in the 'text_extractions' folder
        chat_completion = groq.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": json_parser_sys_prompt,
                },
                {
                    "role": "user",
                    "content": f"Generate a question list for the following text:\n\n{homework}",
                },
            ],
            model="llama3-8b-8192",
            temperature=0,
            response_format={"type": "json_object"},
        )
        
        output = chat_completion.choices[0].message.content
        with open(clean_file_path, 'w') as f:
            f.write("\n\n"+str(output))
        return output
    
def get_file_snippet(file_path):
    with open(file_path, 'r') as f:
        data = f.read()
        return data[:500]

def answer_questions(questions: str, q_context: str, homework_number: int, available_text_files: list[str]):
    snips = []
    for file in available_text_files:
        full_path = f"/Users/samueltownsend/Desktop/UCI/Winter_2025/R_class/Homework/HW{homework_number}/{file}"
        snips.append(get_file_snippet(full_path))
    chat_completion = groq.chat.completions.create(
        messages=[
            {
                "role": "system",
                "content": answerer_prompt
            },
            {
                "role": "user",
                "content": f"""You have this question context: {q_context}
                And this list of available files to you: {available_text_files}
                And here's a preview of the files: {snips}
                And this homework number: {homework_number}
                Answer these questions:\n{questions}
            """,
            },
        ],
        model="llama3-70b-8192",
        temperature=0.2,
    )
    output = chat_completion.choices[0].message.content
    with open("logs/generated_answers.log", 'a') as f:
        f.write("\n\n"+str(output))
    return output



def extract_all_r_code(llm_output):
    # Regular expression to capture all R code blocks
    matches = re.findall(r"```R(.*?)```", llm_output, re.DOTALL)
    if matches:
        # Combine all extracted R code blocks into one
        combined_code = "\n".join(code.strip() for code in matches)
        return str(combined_code)
    else:
        return None  # Return None if no R code is found


def run_r(extracted_r_code: str):
    # Run the R code
    original_dir = os.getcwd()
    with localconverter(default_converter):
        try:
            r(f'setwd("{os.path.abspath("R_images")}")')
            r('options(device="png")')
            # Execute R code
            result = r(extracted_r_code)
            r(f'setwd("{original_dir}")')
            return result

        except Exception as e:
            r(f'setwd("{original_dir}")')
            return str(e)

example = """
pulse_data <- read.table("/Users/samueltownsend/Desktop/UCI/Winter_2025/R_class/Homework/HW3/pulse.txt", header=TRUE)
summary(pulse_data$Wgt)
"""
# print(run_r(example))