from flask import Flask, render_template, request
from utils.pdf_reader import PDF4LLMParser
import markdown

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Check if file is uploaded
        if 'file' not in request.files:
            return "No file uploaded!"
        
        file = request.files['file']

        if file.filename == '':
            return "No file selected!"
        
            # Save the file temporarily and extract the text
        file_path = "uploaded_file.pdf"
        file.save(file_path)
        
        # Extract text from the uploaded PDF
        if file and file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
            text = markdown.markdown(text=text)
            return render_template('pdf_index.html', text=text)
        else:
            return "Please upload a valid PDF file."

    return render_template('pdf_index.html', text=None)

def extract_text_from_pdf(pdf_file):
    reader = PDF4LLMParser(page_chunks=False)
    return reader.run(pdf_path=pdf_file)


if __name__ == "__main__":
    app.run(debug=True)