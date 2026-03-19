import firebase_admin
from firebase_admin import firestore
import google.generativeai as genai
import os

# Init Firebase
cred = firebase_admin.credentials.Certificate('service-account-key.json')
firebase_admin.initialize_app(cred, options={'projectId': 'construct-gents-04415613'})
db = firestore.client()

# Init Gemini
api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    raise ValueError("Please set the GOOGLE_API_KEY environment variable.")
genai.configure(api_key=api_key)

# Define Agent Tool
def log_bid(client: str, total: float, details: str = ""):
    """Logs a new bid into the enterprise database."""
    args = {"client": client, "total": total, "details": details}
    db.collection("bids").add(args)
    return f"✅ Brain: Bid for {client} successfully logged."

# Launch Agent
model = genai.GenerativeModel("gemini-1.5-flash", tools=[log_bid])

def run_team_logic(prompt):
    chat = model.start_chat(enable_automatic_function_calling=True)
    response = chat.send_message(prompt)
    return response.text

if __name__ == "__main__":
    print(run_team_logic("Log a $15,000 hydro-vac bid for the Plantation City Project."))
