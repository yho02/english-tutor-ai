from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

sentence = "She don't know what to do."

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "system", "content": "You are an English language tutor. Identify grammar issues and explain the linguistic reason clearly."},
        {"role": "user", "content": f"Analyze this sentence: {sentence}"}
    ]
)

print(response.choices[0].content)