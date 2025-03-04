# LLM Applications

## 📖 Table of Contents
- [About the Project](#about-the-project)
- [Features](#features)
- [LLMs](#llms)
- [Applications](#applications)
- [Installation](#installation)
- [Contributing](#contributing)
- [License](#license)
- [Contact](#contact)

---

## 📝 About the Project
LLM Applications based on SambaNova CloudAPI. SambaNova CloudAPI supports SOTA open source LLMs. This project
aims to 

- solve the well-known NLP tasks based on this CloudAPI, including the prompt engineer.

- usefull tools or API based on open source LLMs

---

## ✨ Features
- ✅ SambaNova FastInference API
- ✅ Well-known NLP task prompts
- ✅ Applications based on FastInference

---

## 📚 LLMs
- Llama3.1 8B, 70B, 405B instruction models
- Llama3.2 1B, 3B instruction models
- Llama3.3 70B instruction models
- Qwen 2.5 72B instruction models
- Qwen 2.5 coder 32B model
- QwQ model 32B

---

## ✨ Applications
- Text revision with explaination: start the server ```python3 -m applications.text_revision```, and then run HTML 'http://127.0.0.1:5000/'
- Question generation with given context and question type ```python3 -m applications.question_gen```, and then run HTML 'http://127.0.0.1:5000/'
- Single Round Chat or QA: start the server ```python3 -m chat.chatapi```, and then run HTML 'http://127.0.0.1:5000/'
- PDF paper to marked down text: start the server ```python3 -m applications.pdf2text```, and then run HTML 'http://127.0.0.1:5000/'

---

## 🚀 Getting Started
These instructions will help you set up and run the project on your local machine.

### 📦 Prerequisites
- [Tool/Software] – Apply SambaNova API key via https://cloud.sambanova.ai/?api_ref=117487
- Set SAMBANOVA_API_KEY
```bash
#  Setting Environment Variable (Linux/macOS)

export SAMBANOVA_API_KEY="your_sambanova_api_key_here"

#  Setting Environment Variable (Windows)

set SAMBANOVA_API_KEY=your_sambanova_api_key_here

```



### 📥 Installation
```bash
# Clone the repository
git clone 

pip install pdf4llm

pip install python-pptx
```

⭐️ Don’t forget to star the project if you found it useful!