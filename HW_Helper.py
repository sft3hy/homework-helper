import streamlit as st
import os
from helpers import extract_text, get_questions, answer_questions, extract_all_r_code, run_r
import time
import json
from custom_st_components import gen_copy_button
import streamlit.components.v1 as components



uploaded_file = st.file_uploader(
    "Drag and drop stat 210 hw here",
    accept_multiple_files=False,
)


save_dir = "user_hw_files"
file_to_work = ""
file_paths = []

files = os.listdir(save_dir)
# print(files)
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
            
col1, col2, col3 = st.columns(3)

with col2:
    generate_answers = st.button("Let's see the answers", use_container_width=True, type='primary')

if generate_answers and file_to_work != "":
    print(file_to_work)
    extracted_text = extract_text(file_to_work)

    # Generate questions
    with st.spinner("Parsing questions..."):
        q_list = json.loads(get_questions(extracted_text, file_to_work))
    # create the path to where the text files are stored:
    data_folder_path = f"/Users/samueltownsend/Desktop/UCI/Winter_2025/R_class/Homework/HW{q_list['Homework_Number']}"
    # get a list of all the .txt files in that directory:
    txt_files = [f for f in os.listdir(data_folder_path) if f.endswith('.txt')]
    # Display Sub-Questions
    answers = ""
    with st.chat_message('ai'):
        for q in q_list['Question_List']:
            q_num = q['question_number']
            with st.spinner(f"Answering question {q_num}..."):
                response = answer_questions(questions=q['individual_question_list'], q_context=q['question_context'], homework_number=q_list['Homework_Number'], available_text_files=txt_files)
                answers += response
                st.subheader(f"Question {q_num}:")
                st.write(response)
                time.sleep(0.1)
                r_code = extract_all_r_code(response)
                if r_code is not None:
                    print("\n\n\nR CODE:", r_code)
                    r_output = run_r(r_code)
                    st.subheader(f"R Output for {q_num}:")
                    st.write(r_output)
        components.html(gen_copy_button(answers), height=60)

    with open(f"answer_folder/{file_to_work.split('/')[-1]}", 'w') as f:
        f.write(answers)
    f.close()

elif generate_answers and file_to_work == "":
    st.error("Please select a homework to work on.")
