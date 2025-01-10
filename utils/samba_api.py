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

# response = client.chat.completions.create(
#     model='Meta-Llama-3.1-8B-Instruct',
#     messages=[{"role":"system","content":"You are a helpful assistant"},{"role":"user","content":"Hello"}],
#     temperature =  0.1,
#     top_p = 0.1
# )

# print(response.choices[0].message.content)

print(call_api("Meta-Llama-3.3-70B-Instruct", [{"role":"system","content":"You are a helpful assistant"},{"role":"user","content":"Which number is greater, 9.9 or 9.11?"}]))