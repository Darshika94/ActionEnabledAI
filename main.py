from dotenv import load_dotenv
import os
from openai import OpenAI
from gmail import GmailService
from google_sheets import SheetService

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
gmail_credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH")
sheet_id = os.getenv("GOOGLE_SHEET_ID")
sheet_name = os.getenv("GOOGLE_SHEET_NAME")

client = OpenAI(api_key=openai_api_key)
gmail_service = GmailService(credentials_path=gmail_credentials_path)
sheet_service = SheetService(sheet_id=sheet_id, sheet_name=sheet_name)

def extract_email_context(email):
    return f"From: {email['From']}\n\nSubject: {email['Subject']}\n\nEmail Body: {email['snippet']}"

def classify_email(context):
    prompt = f"""
    Your task is to determine whether an email is related to a sponsorship deal or not.

    Respond ONLY with a valid JSON object in this exact format:
    {{
      "isSponsorship": true or false,
      "reasoning": "A short explanation here"
    }}

    Do not include any other text, headers, or formatting. Only provide the JSON object.

    {context}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return eval(response.choices[0].message.content)

def generate_reply(context):
    prompt = f"""
    **Role:**
    You work for a YouTube channel called *AI with Darshika*.
    Your task is to respond to sponsorship inquiries by drafting a reply email.

    **Task:**
    Review the email context below and write a friendly and professional email (HTML format only).

    ### Sponsorship Terms
    - Standalone Video: $850 – $1,400
    - Integrated Mention: $650

    Only accept sponsors that align with the channel’s values.

    Email Context: {context}
    """
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def process_emails():
    new_emails = gmail_service.fetch_new_emails()
    for email in new_emails:
        context = extract_email_context(email)
        classification = classify_email(context)

        if classification["isSponsorship"]:
            reply = generate_reply(context)
            gmail_service.reply(email_id=email["id"], message=reply)
            sheet_service.append_row({
                "From": email["From"],
                "Subject": email["Subject"],
                "Body": email["snippet"]
            })
        else:
            print("Email skipped (not sponsorship)")

if __name__ == "__main__":
    process_emails()
