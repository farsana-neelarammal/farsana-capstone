import os
import sys
from dotenv import load_dotenv
from openai import OpenAI

# Load .env values if present.
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("OPENAI_API_KEY is not set. Add it to the .env file or environment.")

base_url = os.getenv("OPENAI_BASE_URL", "https://openai.vocareum.com/v1")

# Use the Vocareum OpenAI-compatible endpoint when provided.
client = OpenAI(api_key=api_key, base_url=base_url)


def ask(question: str) -> str:
    """Send one question to the LLM and return the answer text."""
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are concise."},
            {"role": "user", "content": question},
        ],
        temperature=0.3,
    )
    return resp.choices[0].message.content


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "Say hello in one sentence."
    answer = ask(question)
    print(answer if answer is not None else "No response received.")