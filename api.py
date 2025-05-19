from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from pdf2image import convert_from_path
import pytesseract
import os
import uuid
import openai
import json
from openai import OpenAI
import os
from datetime import datetime


client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "null"))
app = FastAPI()

UPLOAD_DIR = "data"
os.makedirs(UPLOAD_DIR, exist_ok=True)

def extract_text_from_pdf(pdf_path):
    images = convert_from_path(pdf_path)
    full_text = ""

    for i, image in enumerate(images):
        text = pytesseract.image_to_string(image)
        full_text += f"\n--- Page {i + 1} ---\n{text}"

    return full_text

def parse_with_openai(resume_text: str):
    prompt = (
        "Summarize the text below into a JSON with exactly the following structure and make sure the mobile number is in +country code format: "
        "{data: {name, email, mobileNumber, location, summary, "
        "education: [{university, graduation_year, majors, GPA}], "
        "workExperience: [{job_title, company, location, duration, job_summary}], "
        "project_experience: [{project_name, project_description}], "
        "skills: [{name}], certifications: [{name}]}}"
    )

    messages = [
        {
            "role": "system",
            "content": "You are an expert resume parser that converts unstructured resume text into structured JSON."
        },
        {
            "role": "user",
            "content": prompt + "\n\n" + resume_text
        }
    ]

    print("🧠 Sending to GPT...")

    response = client.chat.completions.create(
        model="gpt-4",
        messages=messages,
        max_tokens=2000,
        temperature=0.2
    )

    return response.choices[0].message.content

@app.post("/upload-cv/")
async def upload_cv(file: UploadFile = File(...)):
    try:
        # Save file
        file_ext = os.path.splitext(file.filename)[1]
        unique_id = uuid.uuid4().hex
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        saved_filename = f"cv_{timestamp}_{unique_id}{file_ext}"
        saved_path = os.path.join(UPLOAD_DIR, saved_filename)

        with open(saved_path, "wb") as buffer:
            buffer.write(await file.read())

        # OCR to extract text
        parsed_text = extract_text_from_pdf(saved_path)

        # Save raw text
        txt_path = saved_path.replace(file_ext, ".txt")
        with open(txt_path, "w") as f:
            f.write(parsed_text)

        # Send to OpenAI
        gpt_response_text = parse_with_openai(parsed_text)

        # Try parsing GPT response into JSON
        try:
            gpt_response_json = json.loads(gpt_response_text)
        except json.JSONDecodeError:
            gpt_response_json = {
                "error": "❌ Failed to parse OpenAI response as JSON.",
                "raw_response": gpt_response_text
            }

        return JSONResponse({
            "message": "✅ CV parsed successfully.",
            "original_file": saved_filename,
            "parsed_file": os.path.basename(txt_path),
            "data": gpt_response_json.get("data", gpt_response_json)
        })

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})