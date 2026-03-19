import firebase_admin
from firebase_admin import credentials, firestore
import json
import os

# Configuration: Project ID and Service Account Key
# On the VM, you can set the GOOGLE_APPLICATION_CREDENTIALS env var
PROJECT_ID = "construct-gents-04415613"
KEY_FILE = "service-account-key.json"

if not firebase_admin._apps:
    if os.path.exists(KEY_FILE):
        cred = credentials.Certificate(KEY_FILE)
        firebase_admin.initialize_app(cred, {'projectId': PROJECT_ID})
    else:
        # Fallback for VM environment if ADC is present
        firebase_admin.initialize_app(options={'projectId': PROJECT_ID})

db = firestore.client()

def get_latest_bids():
    """Fetches bids in the 'bids' collection."""
    try:
        # Fetching all for now since 'status' field might not exist yet
        docs = db.collection('bids').stream()
        bids = []
        for doc in docs:
            bid_data = doc.to_dict()
            bid_data['id'] = doc.id
            # Handle non-serializable objects like Datetime
            if 'timestamp' in bid_data:
                bid_data['timestamp'] = str(bid_data['timestamp'])
            bids.append(bid_data)
        
        # Return as JSON for OpenClaw to parse
        print(json.dumps(bids))
    except Exception as e:
        print(json.dumps({"error": str(e)}))

if __name__ == "__main__":
    get_latest_bids()
