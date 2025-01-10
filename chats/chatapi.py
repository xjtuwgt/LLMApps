from flask import Flask, render_template, request
# Initialize the Flask application
app = Flask(__name__)

import os
import openai

client = openai.OpenAI(
    api_key=os.environ.get("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1",
)

def call_api(model_name, messages, **kwargs):
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=kwargs.get("temperature", 0.1),
        top_p=kwargs.get("top_p", 0.1),
    )
    return response.choices[0].message.content


# Homepage with chat form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        # Call OpenAI API for the response
        try:
            bot_reply = call_api("Meta-Llama-3.3-70B-Instruct", [{"role":"system","content":"You are a helpful assistant"},{"role":"user","content":user_input}])
        except Exception as e:
            bot_reply = f"Error: {str(e)}"
        return render_template("index.html", user_input=user_input, bot_reply=bot_reply)
    return render_template("index_v2.html")

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)