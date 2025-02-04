import streamlit as st
import os
from helpers import extract_text_from_pdf, get_questions, answer_question
import time

uploaded_file = st.file_uploader(
    "Drag and drop stat 210 hw here",
    accept_multiple_files=False,
    
)

save_dir = "user_hw_files"
file_to_work = ""
file_paths = []

if uploaded_file:
    # Save uploaded files
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    file_to_work = file_path  # Treat uploaded files as selected

with st.expander("Or select previous homeworks", expanded=False):
    files = os.listdir(save_dir)
    for count, file in enumerate(files):
        file_path = os.path.join(save_dir, file)
        file_paths.append(file_path)
        
        if os.path.isfile(file_path):
            # Add a checkbox for each file
            is_selected = st.checkbox(f"📄 {file}", key=f"file_{count}")
            if is_selected:
                file_to_work = file_path
            
            
generate_answers = st.button("Gimme answers")

if generate_answers and file_to_work != "":
    extracted_text = extract_text_from_pdf(file_to_work)

    # Generate questions
    q_list = get_questions(extracted_text)

    # Display Sub-Questions
    st.subheader("Questions")
    answers = ""
    for q in q_list.questions:
        response = answer_question(q.question)
        answer = f"Q{q.question_number}: {response}\n"
        answers += answer
        st.write(answer)
        time.sleep(0.2)
    with open(f"answer_folder/{file_to_work.split('/')[-1]}", 'w') as f:
        f.write(answers)
    f.close()

