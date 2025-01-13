from flask import Flask, render_template, request
from utils.samba_api import call_api, SAMBA_MODEL
import markdown
"""
Can LLMs Design Good Questions Based on Context?
"""

app = Flask(__name__)

model_name_alias = 'llama70b_v3'

model_name = SAMBA_MODEL[model_name_alias]
system_prompt = """
You are to generate {NUM_QUESTIONS} self-contained short
answer questions based on the facts mentioned in the following content. Avoid questions that reference the content directly. Each question should include all relevant context and directly name any referenced items, avoiding pronouns like "it," "the game," or "the person."
Do not include phrases that reference the source or context, such as "mentioned in the article" or "according to the text." Provide the questions in an ordered list.
"""

def generate_question(context, question_type, num_questions):
    # Call the LLM API to generate a question based on the context and type
    try:
        response = call_api(model_name=model_name, messages=[{"role": "system", "content": system_prompt.format(NUM_QUESTIONS=num_questions)}, 
                                                             {"role":"user","content": context},
                                                             {"role":"user","content": 'Question type is {}'.format(question_type)},
                                                             ])
        response = markdown.markdown(response)
        return response
    except Exception as e:
        return f"Error generating question: {str(e)}"

@app.route('/', methods=['GET', 'POST'])
def index():
    # List of question types for the pull-down menu
    question_types = [
        "Multiple Choice", "True/False", "Open-Ended", 
        "Fill-in-the-Blank", "Short Answer", "Essay", 
        "Matching", "Ranking", "Likert Scale", "Yes/No"
    ]

    generated_question = None
    context = None
    question_type = None
    num_questions = None

    if request.method == 'POST':
        context = request.form.get('context')
        question_type = request.form.get('question_type')
        num_questions = request.form.get('num_questions')
        generated_question = generate_question(context, question_type, num_questions)

    return render_template('question_index.html', 
                           question_types=question_types, 
                           generated_question=generated_question, 
                           context=context, 
                           question_type=question_type, 
                           num_questions=num_questions)
if __name__ == '__main__':
    app.run(debug=True)

