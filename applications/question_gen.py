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
answer questions based on the facts mentioned in the fol。     lowing content. Avoid questions that reference the content directly. Each question should include all relevant context and directly name any referenced items, avoiding pronouns like "it," "the game," or "the person."
Do not include phrases that reference the source or context, such as "mentioned in the article" or "according to the text." Provide the questions in an ordered list.
"""

QUESTION_TYPES = """\
1. **Verification/Affirmation Questions**: These questions ask for confirmation about the equivalence or relationship between two or more entities. They often use formats like "Are...?" or "Which...?"
2. **Specific Fact and Figure Questions**: These questions request a specific quantitative or qualitative fact. They are straightforward and seek concrete data or a precise answer, often involving numbers or specific details.
3. **Identity and Attribution Questions**: These inquiries focus on identifying a person or entity responsible for an action or associated with a work. They tend to ask "Who...?" or refer to persons or origins related to a context.
4. **Which/What-Based General Knowledge Questions**: This group contains questions that start with "Which" or "What" and inquire about general knowledge, often requiring a selection from a set or identification of a type/category.
5. **Event/Outcome Questions**: These questions inquire about the outcome of specific events or actions, focusing on consequences or results. They often address changes, damages, or effects.
6. **Sequential/Ordering/Causation Questions**: These questions require identifying a sequence, comparison, or causation among entities, often using terms like "first," "before," "between," etc.
7. **Location-Based Questions**: These questions focus on identifying a geographic location or specific place where something is based or occurs.
8. **Descriptive/Characterization Questions**: These questions seek an explanation or characterization of entities, often requiring a description of how or why something is the way it is, involving traits or actions.
9. **Comparison and Selection Questions**: Questions in this group involve comparing two entities to determine which one holds a particular status or characteristic, often using formats like "Between X and Y, who/which is...?"
10. **Classification and Categorization Questions**: These inquiries request the classification or categorical identity of entities or things, often seeking to place an item within a broader group or category.
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
        "Multiple Choice", 
        "True/False", 
        "Open-Ended", 
        "Fill-in-the-Blank", 
        "Short Answer", 
        "Essay", 
        "Matching", 
        "Ranking", 
        "Likert Scale", 
        "Yes/No",
        "Classification and Categorization",
        "Comparison and Selection",
        "Descriptive/Characterization",
        "Specific Fact",
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

