import openai
from flask import Flask, render_template_string, request
from utils.samba_api import call_api, SAMBA_MODEL
import markdown

# Initialize Flask app
app = Flask(__name__)

model_name_alias = 'llama70b_v3' # qwen72b

model_name = SAMBA_MODEL[model_name_alias]
prompt = """
Revise the following text for clarity, grammar, and coherence. Improve readability while preserving the original meaning. 
Provide the revised version of the text first, followed by a step-by-step explanation of the changes made. 
Explain each modification in a concise, educational manner, highlighting why the change was necessary and how it improves the text.
"""


# HTML Template for the Web Interface with a Run Button
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Text Revision with SambaNova FastAPI (Llama3.3 70B)</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        textarea { width: 100%; height: 150px; }
        button { padding: 10px 20px; margin-top: 10px; background: #4CAF50; color: white; border: none; cursor: pointer; }
        button:hover { background: #45a049; }
        h2 { color: #333; }
        .result { margin-top: 20px; padding: 10px; background: #e8f5e9; border: 1px solid #a5d6a7; border-radius: 8px; }
    </style>
</head>
<body>
    <h2>Text Revision using SambaNova FastAPI (Llama3.3 70B)</h2>
    <form action="/" method="POST">
        <textarea name="text" placeholder="Enter text here...">{{ text }}</textarea>
        <br>
        <button type="submit">Revise</button>
    </form>

    {% if revised_text %}
     <p><strong>Assistant:</strong> {{ revised_text | safe }}</p>
    {% endif %}
</body>
</html>
"""

# Flask Route for Text Revision using OpenAI API
@app.route("/", methods=["GET", "POST"])
def home():
    revised_text = ""
    input_text = ""
    if request.method == "POST":
        input_text = request.form.get("text")
        if input_text:
            revised_text = call_api(model_name, 
                                    [{"role": "system", "content": prompt}, {"role":"user","content":input_text}])
            revised_text = markdown.markdown(revised_text)
    return render_template_string(HTML_TEMPLATE, text=input_text, revised_text=revised_text)

if __name__ == "__main__":
    app.run(debug=True)