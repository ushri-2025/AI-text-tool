from google import genai

client = genai.Client(api_key="AIzaSyCAtFnwtKZ3A72UEaA2OhUumRh87JA-_qQ")

try:
    models = client.models.list()

    print("\nAvailable Models:\n")

    for model in models:
        print(model.name)

except Exception as e:
    print("Error:", e)