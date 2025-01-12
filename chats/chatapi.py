from flask import Flask, render_template, request
import markdown
# Initialize the Flask application
app = Flask(__name__)

from utils.samba_api import call_api, SAMBA_MODEL, SAMBA_SYS_PROMPT

model_name_alias = 'llama70b_v3'
# model_name_alias = 'qwencoder'
model_name = SAMBA_MODEL[model_name_alias]


# Homepage with chat form
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        user_input = request.form.get("user_input")
        # Call OpenAI API for the response
        try:
            bot_reply = call_api(model_name, [{"role": "system", "content": SAMBA_SYS_PROMPT[2]},{"role":"user","content":user_input}])
            bot_reply = markdown.markdown(bot_reply)
        except Exception as e:
            bot_reply = f"Error: {str(e)}"
        return render_template("index_v1.html", user_input=user_input, bot_reply=bot_reply)
    return render_template("index_v1.html")

# Run the Flask appß
if __name__ == "__main__":
    app.run(debug=True)