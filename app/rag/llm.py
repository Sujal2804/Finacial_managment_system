from groq import Groq
from dotenv import load_dotenv
import os

load_dotenv()  
GROQ_API_KEY = os.getenv("GROQ_API_KEY")


client = Groq(api_key=GROQ_API_KEY)

def generate_answer(query, context):
    prompt = f"""
    Answer the question based on the context below.
    Context:
    {context}
    Question:
    {query}
    Answer:
    """
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content
