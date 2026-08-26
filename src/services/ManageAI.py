from openai import OpenAI
import openai

client = OpenAI(
    api_key="sk-f14f33d93b0740e89408cb3063417569",
    base_url="https://api.deepseek.com"
)

try:
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": "Hello!"}
        ]
    )
    print(response.choices[0].message.content)
    
except openai.APIStatusError as e:
    if e.status_code == 402:
        print("❌ Insufficient balance. Please add credits at https://platform.deepseek.com")
    elif e.status_code == 401:
        print("❌ Invalid API key")
    else:
        print(f"❌ API Error: {e}")