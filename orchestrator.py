import os
import firebase_admin
from firebase_admin import firestore
from google import genai
from google.genai import types
import json

# Configuration
PROJECT_ID = "construct-gents-04415613"
KEY_FILE = "service-account-key.json"

# Initialize Firebase
if not firebase_admin._apps:
    cred = firebase_admin.credentials.Certificate(KEY_FILE)
    firebase_admin.initialize_app(cred, options={'projectId': PROJECT_ID})
db = firestore.client()

# Initialize Gemini Client
API_KEY = os.environ.get("GOOGLE_API_KEY")
if not API_KEY:
    raise ValueError("Missing GOOGLE_API_KEY environment variable.")
client = genai.Client(api_key=API_KEY)

# --- Agent Capabilities (Tools) ---

def request_new_tool(tool_name: str, reason: str):
    """
    If the agent needs a capability or API key it doesn't have, it logs a request here.
    """
    db.collection("tool_requests").add({
        "tool_name": tool_name,
        "reason": reason,
        "status": "pending_admin_approval",
        "timestamp": firestore.SERVER_TIMESTAMP
    })
    return f"Tool request for '{tool_name}' submitted to the dashboard."

def verify_compliance_with_document(document_path: str, bid_details: str):
    """
    Uploads a massive PDF (like state building codes) and verifies the bid details against it.
    """
    if not os.path.exists(document_path):
        return f"Error: Document {document_path} not found locally. Perhaps request a web search tool?"
    
    print(f"📄 Uploading {document_path} to Gemini for Compliance Review...")
    try:
        # Upload using the File API (handles huge files up to 2GB)
        uploaded_file = client.files.upload(file=document_path)
        
        print("🔍 Reviewing compliance against document...")
        response = client.models.generate_content(
            model="gemini-2.5-flash", # Large context window
            contents=[
                uploaded_file,
                f"Review the following bid details against the provided regulatory document. Highlight any violations. Bid: {bid_details}"
            ]
        )
        return f"Compliance Report:\n{response.text}"
    except Exception as e:
        return f"Error analyzing document: {e}"

def log_enterprise_bid(client_name: str, estimated_value: float, project_type: str, compliance_status: str):
    """Logs the final bid to the database to be picked up by the Action Arm (OpenClaw)."""
    try:
        bid_data = {
            "client_name": client_name,
            "project_type": project_type,
            "estimated_value": estimated_value,
            "date_logged": firestore.SERVER_TIMESTAMP,
            "compliance": {
                "status": compliance_status,
                "reviewed_by_agent": "Enterprise-Orchestrator"
            },
            "action_arm": {
                "status": "pending_human_review",
                "capability_statement_drafted": False,
                "outreach_email_sent": False
            }
        }
        db.collection("bids").add(bid_data)
        return f"✅ SUCCESS: Logged {project_type} bid for {client_name}. Status: PENDING HUMAN REVIEW."
    except Exception as e:
        return f"❌ ERROR: {str(e)}"

# Setup Orchestrator
tools = [request_new_tool, verify_compliance_with_document, log_enterprise_bid]

def run_orchestrator(task_description: str):
    """
    The main routing agent that decides how to handle complex construction tasks.
    """
    print(f"🧠 Orchestrator Processing Task: '{task_description}'\n")
    
    system_instruction = """
    You are the RIDIS LLC Enterprise Orchestrator Agent. Your job is to handle complex construction tasks.
    
    1. If the task requires checking regulations, use 'verify_compliance_with_document' first (if a local PDF exists).
    2. If you need to search the web, check competitor pricing, or need an API you don't have, use 'request_new_tool'.
    3. Once you have formulated a valid, compliant bid, use 'log_enterprise_bid' to send it to the Command Center.
    """
    
    response = client.models.generate_content(
        model="gemini-2.5-pro", # Using Pro for advanced reasoning and routing
        contents=task_description,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            tools=tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
        )
    )
    return response.text

if __name__ == "__main__":
    # Example Task that requires tools the agent might not have
    task = "Draft a $55,000 Utility Locating bid for Miami-Dade County. Ensure it complies with the local building codes. If you don't have the codes, request a web search tool to find them."
    print(run_orchestrator(task))
