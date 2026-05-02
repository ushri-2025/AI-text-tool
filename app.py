from flask import Flask, render_template, request, jsonify
import google.generativeai as genai
import os
import random

app = Flask(__name__)

# ===== API KEYS =====
GEMINI_KEY = os.getenv("GEMINI_KEY")
OPENROUTER_KEY = os.getenv("OPENROUTER_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")


# ===== SAFE GEMINI RESPONSE FUNCTION =====
def get_gemini_response(prompt):
    try:
        response = model.generate_content(prompt)

        # FIX: Proper extraction
        if hasattr(response, "text") and response.text:
            return response.text.strip()

        elif hasattr(response, "candidates") and response.candidates:
            return response.candidates[0].content.parts[0].text.strip()

        else:
            return None

    except Exception as e:
        print("Gemini Error:", e)
        return None


# ===== FALLBACK (only if API fails) =====
def fallback_response(text, mode, tone=None):
    text = text.strip()

    if mode == "autocorrect":
        return text.capitalize()

    if mode == "improve":
        if tone == "formal":
            return f"I would like to state that {text}."
        elif tone == "casual":
            return f"Hey, just saying — {text}."
        else:
            return f"{text}."

    if mode == "humanize":
        return f"{text}. It sounds more natural when expressed this way."

    if mode == "write":
        if "email" in text.lower():
            return (
                "Subject: Request\n\n"
                "Dear Sir/Madam,\n\n"
                "I hope you are doing well. I am writing regarding your request.\n\n"
                "Thank you.\n\n"
                "Sincerely,\nYour Name"
            )
        else:
            return f"{text}. This is a basic response."

    return text


# ===== MAIN ROUTE =====
@app.route("/")
def home():
    return render_template("index.html")


# ===== PROCESS ROUTE =====
@app.route("/process", methods=["POST"])
def process():
    data = request.json
    text = data.get("text", "")
    mode = data.get("mode", "")
    tone = data.get("tone", "")
    retry = data.get("retry", False)

    prompt = ""

    # ===== AUTOCORRECT =====
    if mode == "autocorrect":
        prompt = f"Correct grammar and rewrite properly:\n{text}"

    # ===== IMPROVE =====
    elif mode == "improve":
        if tone == "formal":
            prompt = f"Rewrite this in a formal professional tone:\n{text}"
        elif tone == "casual":
            prompt = f"Rewrite this in a casual friendly tone:\n{text}"
        elif tone == "technical":
            prompt = f"Rewrite this in a technical and precise tone:\n{text}"
        else:
            prompt = f"Improve the quality of this text:\n{text}"

    # ===== HUMANIZE =====
    elif mode == "humanize":
        prompt = f"Make this sound natural, human-like, and fluent:\n{text}"

    # ===== WRITE =====
    elif mode == "write":
        lower = text.lower()

        if "email" in lower:
            prompt = f"""
Write a professional email based on this request.
Keep it well-structured with subject, greeting, body, and closing.

{text}
"""
        elif "report" in lower:
            if retry:
                prompt = f"Write a detailed, structured report (300-500 words):\n{text}"
            else:
                prompt = f"Write a concise but meaningful report (120-180 words):\n{text}"

        elif "story" in lower:
            if retry:
                prompt = f"Write a detailed engaging story (300-500 words):\n{text}"
            else:
                prompt = f"Write a short but complete story (120-180 words):\n{text}"

        else:
            prompt = f"Write a clear and complete response:\n{text}"

    # ===== GET RESPONSE =====
    result = get_gemini_response(prompt)

    # ===== FALLBACK IF FAILED =====
    if not result:
        result = fallback_response(text, mode, tone)

    return jsonify({"result": result})


# ===== RUN =====
if __name__ == "__main__":
    app.run(debug=True)