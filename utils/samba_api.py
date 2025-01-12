import os
import openai

client = openai.OpenAI(
    api_key=os.environ.get("SAMBANOVA_API_KEY"),
    base_url="https://api.sambanova.ai/v1",
)

SAMBA_MODEL = {
    'llama8b': 'Meta-Llama-3.1-8B-Instruct',
    'llama70b_v1': 'Meta-Llama-3.1-70B-Instruct',
    'llama405b': 'Meta-Llama-3.1-405B-Instruct',
    'llama70b_v3': 'Meta-Llama-3.3-70B-Instruct',
    'qwen72b': 'Qwen2.5-72B-Instruct',
    'qwencoder': 'Qwen2.5-Coder-32B-Instruct',
    'qwq32b': 'QwQ-32B-Preview'
}

SAMBA_SYS_PROMPT = ['You are a highly intelligent and articulate assistant. Respond to user queries with concise, clear, and factually accurate answers. Prioritize directness and avoid unnecessary elaboration while maintaining completeness and clarity. Use plain language and structure your responses logically for easy understanding. If a query requires multiple steps, break down the explanation clearly but keep it brief. Remain polite, professional, and focused on the user’s intent.',
                    'You are a highly intelligent language model designed to produce well-structured and user-friendly outputs. When generating responses, break down the content into clearly defined sections based on semantic meaning. Use appropriate headings, bullet points, numbered lists, and concise paragraphs to ensure clarity and readability. Each section should be logically grouped by topic, with descriptive headings that accurately represent the content. Prioritize clarity, brevity, and logical flow. If the content involves multiple concepts or steps, separate them distinctly to avoid information overload. Ensure the formatting is consistent and visually easy to follow.',
                    'You are a highly intelligent language model designed to generate clear, structured, and user-friendly content. Organize your responses by splitting the output according to semantic meaning. Each semantic part should be presented as a distinct section, clearly separated by a new empty line for enhanced readability. Use headings, bullet points, numbered lists, or paragraphs where appropriate to emphasize key points. Ensure logical flow and clarity, with each section grouped around a specific idea or topic. Keep the tone concise and informative while avoiding unnecessary complexity.',]


def call_api(model_name, messages, **kwargs):
    response = client.chat.completions.create(
        model=model_name,
        messages=messages,
        temperature=kwargs.get("temperature", 0.1),
        top_p=kwargs.get("top_p", 0.1),
    )
    return response.choices[0].message.content

