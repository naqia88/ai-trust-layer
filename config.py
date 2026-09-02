# Import environment-variable support and load values from the .env file.
import os

from dotenv import load_dotenv


# Load project configuration values stored outside source control.
load_dotenv()

# Store the API key outside the codebase.
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.5-flash"

# Define the project paths used by the audit log and policy retriever.
DB_PATH = "database/audit.db"
POLICY_PDF_PATH = "policies/company_policy.pdf"
CHROMA_PATH = "database/chroma"

# Define the risk-score boundaries for action decisions.
AUTO_APPROVE = 40
FLAG_FOR_REVIEW = 70
AUTO_BLOCK = 90

# Set the checker importance for each supported action type.
WEIGHTS = {
    "transfer_money": {
        "financial": 0.4,
        "privacy": 0.3,
        "policy": 0.3,
    },
    "send_email": {
        "financial": 0.2,
        "privacy": 0.5,
        "policy": 0.3,
    },
    "execute_code": {
        "financial": 0.3,
        "privacy": 0.2,
        "policy": 0.5,
    },
}
