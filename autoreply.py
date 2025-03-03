import os.path
import base64
import email
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://mail.google.com/"]


# Function to authenticate and create Gmail service
def get_gmail_service():
    creds = None
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        with open("token.json", "w") as token:
            token.write(creds.to_json())
    print("[DEBUG] Gmail service authenticated successfully.")
    return build("gmail", "v1", credentials=creds)


# Function to fetch emails that have not been processed
def get_unprocessed_emails(service):
    results = (
        service.users()
        .messages()
        .list(userId="me", labelIds=["INBOX"], q="-label:PROCESSED")
        .execute()
    )
    messages = results.get("messages", [])
    print(f"[DEBUG] Found {len(messages)} unprocessed emails.")
    return messages


# Function to process an email
def process_email(service, msg_id):
    print(f"[DEBUG] Processing email ID: {msg_id}")
    msg = (
        service.users().messages().get(userId="me", id=msg_id, format="full").execute()
    )
    headers = msg["payload"].get("headers", [])

    return_path = next(
        (h["value"] for h in headers if h["name"].lower() == "return-path"), ""
    )
    to_address = next((h["value"] for h in headers if h["name"].lower() == "to"), "")

    print(f"[DEBUG] Email return path (sender): {return_path}")
    print(f"[DEBUG] Original recipient (To): {to_address}")

    # Check if the email was originally sent to m384973@datamond.ca
    # if "m384973@datamond.ca" not in to_address:
    if not to_address.startswith("mi"):
        print("[DEBUG] Email was not sent to mi*@datamond.ca, skipping.")
        return

    has_attachment = any(
        part.get("filename") for part in msg["payload"].get("parts", [])
    )
    print(f"[DEBUG] Email has attachment: {has_attachment}")

    response_body = "Hello Michael! "
    response_body += (
        "Your attachment is saved!" if has_attachment else "There is no attachment."
    )

    send_reply(service, return_path, msg, response_body)
    mark_email_as_processed(service, msg_id)


# Function to send reply
def send_reply(service, sender, msg, body):
    headers = msg["payload"].get("headers", [])
    subject = next((h["value"] for h in headers if h["name"].lower() == "subject"), "")
    reply_subject = f"Re: {subject}"

    print(f"[DEBUG] Sending reply to: {sender}")
    print(f"[DEBUG] Reply subject: {reply_subject}")
    print(f"[DEBUG] Reply body: {body}")

    message = email.message.EmailMessage()
    message["To"] = sender
    message["Subject"] = reply_subject
    message.set_content(body)

    raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw_message}).execute()
    print("[DEBUG] Reply sent successfully.")


# # Function to mark email as processed
# def mark_email_as_processed(service, msg_id):
#     service.users().messages().modify(
#         userId="me", id=msg_id, body={"addLabelIds": ["PROCESSED"]}
#     ).execute()
#     print(f"[DEBUG] Marked email {msg_id} as processed.")


# Function to mark email as processed
def mark_email_as_processed(service, msg_id):
    label_name = "PROCESSED"

    # Get existing labels
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    label_ids = {label["name"]: label["id"] for label in labels}

    # Create the label if it doesn't exist
    if label_name not in label_ids:
        print(f"[DEBUG] Creating label: {label_name}")
        label = (
            service.users()
            .labels()
            .create(
                userId="me",
                body={
                    "name": label_name,
                    "labelListVisibility": "labelShow",
                    "messageListVisibility": "show",
                },
            )
            .execute()
        )
        label_ids[label_name] = label["id"]

    # Apply label to email
    service.users().messages().modify(
        userId="me", id=msg_id, body={"addLabelIds": [label_ids[label_name]]}
    ).execute()

    print(f"[DEBUG] Marked email {msg_id} as processed.")


# Main function
def main():
    service = get_gmail_service()
    unprocessed_emails = get_unprocessed_emails(service)
    for email_data in unprocessed_emails:
        process_email(service, email_data["id"])
    print("[DEBUG] Processing complete.")


if __name__ == "__main__":
    main()
