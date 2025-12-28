**AI-Powered Email Audio to CRM Automation**


This  project focuses on automating the process of extracting valuable customer information from audio files received via email and updating this information directly into a CRM system (HubSpot). The goal is to reduce manual data entry, improve data accuracy, and save time for sales and consulting teams.

**Problem Statement**
In many organizations, important customer details are shared through voice messages or call recordings sent via email. Manually listening to these recordings and entering data into a CRM is time-consuming and error-prone. There is a need for an automated system that can handle this workflow efficiently.

**Project Objective**
The objective of this project is to design and implement an automated pipeline that:
- Reads emails with audio attachments
- Transcribes the audio into text
- Extracts structured customer data using AI
- Updates the extracted data into HubSpot CRM
- Uploads the original audio file as a CRM attachment
  
**System Overview**
The system works as an end-to-end automation pipeline. Emails containing audio files are fetched from Gmail. The audio is transcribed using an AI speech-to-text model. The transcript is then analyzed by a language model to extract structured fields such as job title, nationality, expat status, lead status, and interested products. Finally, the extracted data and audio file are uploaded to HubSpot CRM.

**Technologies Used**
- Gmail API for email access
- Whisper (Speech-to-Text) for audio transcription
- OpenAI GPT model for information extraction
- HubSpot CRM API for data storage
- Python as the main programming language

**Data Extraction Approach**
Instead of using keyword-based rules, the project uses an AI language model to understand the meaning of the conversation. This allows the system to extract information even if the wording changes, making the solution more flexible and scalable.

**CRM Integration**
The extracted data is mapped to HubSpot contact properties such as Job Title, Nationality, Expat Status, Interested Products, and Lead Status. The original audio file is also uploaded and attached to the contact record, ensuring full traceability


**System Architecture**

Email with Audio
       ↓
Gmail API
       ↓
Audio Download
       ↓
Whisper (Speech-to-Text)
       ↓
GPT (Data Extraction)
       ↓
Data Normalization & Mapping
       ↓
HubSpot CRM Update
       ↓
Audio Uploaded to Contact Attachments

**Step-by-Step Workflow**
Step 1: Email Detection
The system connects to Gmail using OAuth
Searches for emails containing audio attachments (.mp3, .wav, .m4a, .mp4)
User can specify a target email address to process
target_email = input("Enter the email address you want to process: ").strip().lower()

Step 2: Audio Download
Audio files are downloaded locally
Sender or subject email is extracted for CRM matching

Step 3: Speech-to-Text (Whisper)
Audio files are transcribed using OpenAI Whisper
Works fully offline after model download
Supports multiple languages (English & German)

Step 4: AI-Based Information Extraction
Using GPT, the transcript is analyzed to extract:
Job title
Nationality
Expat status
Interested products
Lead status
Potential units 
Address 
The AI returns clean JSON, ensuring structured output.

Step 5: Data Normalization & Validation
To match HubSpot requirements:
Nationalities are mapped to valid dropdown options
Boolean fields like expat are normalized (true / false)
Lead status values are mapped to valid CRM pipeline values

Step 6: HubSpot CRM Update
Contact is found using email
CRM properties are updated via HubSpot API
Only valid properties are sent (prevents API errors)

Step 7: Audio Upload to HubSpot Attachments
Audio file is uploaded to HubSpot File Manager
File is attached to the contact via a CRM note
Ensures traceability and auditability
