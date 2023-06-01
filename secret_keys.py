import os

openai_api_key = os.getenv("OPENAI_API_KEY")
from_email = os.getenv('SDGPT_FROM_EMAIL')
from_email_password = os.getenv("SDGPT_APP_PW")
to_email = os.getenv("SDGPT_TO_EMAIL")
gcp_project_id = os.getenv("GCP_PROJECT_ID")
gcp_secret_id = os.getenv("GCP_SECRET_ID")

if __name__ == "__main__":
    # for testing purposes
    print(openai_api_key)
    print(from_email)
    print(from_email_password)
    print(to_email)
    print(gcp_project_id)
    print(gcp_secret_id)