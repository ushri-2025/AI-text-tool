from flask import Flask, render_template, request, jsonify
from google import genai
import time
import random

app = Flask(__name__)

import os
client = genai.Client(api_key=os.getenv("API_KEY"))


def generate_with_retry(prompt):
    models_to_try = [
        "gemini-2.5-flash",
        "gemini-2.0-flash",
        "gemini-flash-latest"
    ]

    for model in models_to_try:
        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=prompt
                )

                if hasattr(response, "text") and response.text:
                    return response.text.strip()

            except Exception as e:
                print(f"Error with {model}, attempt {attempt+1}:", e)

                if "503" in str(e):
                    time.sleep(2)
                    continue
                else:
                    break

    return "Sorry, unable to process right now."


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/process', methods=['POST'])
def process_text():
    data = request.get_json()

    text = data.get('text', '').strip()
    mode = data.get('mode')
    style = data.get('style')
    retry_count = data.get('retry', 0)

    if not text:
        return jsonify({"result": "Please enter text."})

    variation = ""
    if retry_count > 0:
        variation = random.choice([
            "Use a different phrasing.",
            "Provide a fresh version.",
            "Reword creatively."
        ])

    if mode == "correct":
        prompt = f"""
Correct the text grammatically.

IMPORTANT:
- Return ONLY one version
- Preserve length and structure
- Do NOT summarize
- Do NOT expand unnecessarily

Text:
{text}
"""

    elif mode == "improve":
        prompt = f"""
Rewrite in a {style} tone.

IMPORTANT:
- Keep same length
- Do NOT expand unnecessarily
- No explanation
- {variation}

Text:
{text}
"""

    elif mode == "humanize":
        prompt = f"""
Rewrite to sound natural and human.

IMPORTANT:
- Maintain same length
- Do NOT expand unnecessarily
- No summarization
- {variation}

Text:
{text}
"""

    elif mode == "write":
        prompt = f"""
Write content based on the user's input.

IMPORTANT:
- Detect intent automatically (email, paragraph, story, etc.)
- Keep output concise and relevant
- If paragraph → 1–2 paragraphs
- If email → proper format
- Do NOT generate overly long output
- Keep it natural and readable

Input:
{text}

{variation}
"""

    else:
        prompt = text

    result = generate_with_retry(prompt)

    return jsonify({"result": result})


if __name__ == '__main__':
    app.run(debug=True)