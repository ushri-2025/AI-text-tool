from flask import Flask, request, jsonify, render_template
import google.generativeai as genai
import requests

app = Flask(__name__)
import os

GEMINI_KEY = os.getenv("GEMINI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

genai.configure(api_key=GEMINI_KEY)


history_store = []


# =========================
# PROMPT BUILDER (STRICT)
# =========================
def build_prompt(text, mode, tone):

    lower = text.lower()

    if mode == "autocorrect":
        return f"""
Correct grammar only. Do not add anything.

{text}
"""

    if mode == "improve":
        return f"""
Rewrite in {tone} tone.

Rules:
- Single sentence only
- Do NOT expand

{text}
"""

    if mode == "humanize":
        return f"""
Make this sound natural.

Rules:
- Keep same format
- No expansion

{text}
"""

    if mode == "write":

        is_email = any(word in lower for word in [
            "email", "mail", "write to", "send to", "compose"
        ])

        if is_email:
            return f"""
Write a professional email.

Include:
- Subject
- Greeting
- Body
- Closing

{text}
"""

        if "story" in lower:
            return f"Write a meaningful short story:\n{text}"

        if "report" in lower or "paragraph" in lower:
            return f"Write a structured paragraph:\n{text}"

        return f"Write a good paragraph:\n{text}"

    return text


# =========================
# GEMINI
# =========================
def call_gemini(prompt):
    try:
        res = genai.GenerativeModel("gemini-1.5-flash").generate_content(prompt)
        return res.text.strip()
    except:
        return None


# =========================
# OPENROUTER
# =========================
def call_openrouter(prompt):
    try:
        r = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        return r.json()["choices"][0]["message"]["content"].strip()
    except:
        return None


# =========================
# MAIN ENGINE
# =========================
def generate_text(text, mode, tone="formal", variation=0):

    prompt = build_prompt(text, mode, tone)

    res = call_gemini(prompt)
    if res:
        return res

    res = call_openrouter(prompt)
    if res:
        return res

    return "Please retry. Service temporarily unavailable."


# =========================
# ROUTES
# =========================
@app.route("/")
def home():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    data = request.json

    result = generate_text(
        data.get("text"),
        data.get("mode"),
        data.get("tone")
    )

    return jsonify({"result": result})


if __name__ == "__main__":
    app.run(debug=True)