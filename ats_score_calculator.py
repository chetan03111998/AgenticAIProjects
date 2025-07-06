import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display, update_display
from msal_auth import GPT_model
import pdfplumber
from docx import Document
class ATS:
    proxies = {
        "http":"",
        "https":"",
        
    }
    headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
                }
    ATS_system_prompt = "You are an expert resume and job description analyzer. Your task is to evaluate how well a resume matches a given job description using common ATS (Applicant Tracking System) best practices. Please follow these steps:\
                         Parse both the resume and the job description.\
                         Extract and compare relevant keywords, skills, qualifications, experience, titles, certifications, and education requirements.\
                         Match the terminology and phrasing in the resume with those in the job description.\
                         Assign an ATS compatibility score (from 0 to 100) indicating the percentage match between the resume and the job description.\
                         Identify the top missing or weakly matched keywords or requirements, and suggest improvements for better alignment.\
                         Provide a brief summary justifying the scoring and recommendations.\
                         Input:\
                         Resume: [Insert Resume Text]\
                         Job Description: [Insert Job Description Text]\
                         Output:\
                         { 'ATS Score': [Score out of 100]\
                           'Missing/Weak Keywords/Qualifications': [List]\
                           'Suggestions for Improvement': [List]\
                           'Scoring Summary': [Explanation]\
                         }"

    def __init__(self,model):
        """ATS class initalizer
        
        Args:
            model = AI model used for task.

        """
        self.model = model
        self.text =  ''

    def get_web_content(self,job_url):
        """retrieve web content

        Args:
            job_url: url of job posted on any company portal.
        """
        response = requests.get(job_url, headers=self.headers,verify=False,proxies=self.proxies,timeout=30)
        body = response.content
        soup = BeautifulSoup(body, 'html.parser')
        title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        
    def get_job_description(self,job_url):
        """Retrieve job description from webpage

        Args:
            job_url: url of job posted on any company portal.
        
        Returns:
            text: job description.
        """
        self.get_web_content(job_url)
        user_prompt = f"please analyse following text and give me job description from below text \
                        {self.text}"
        message =  [
            {"role": "user", "content": user_prompt}
        ]
        response = self.model.chat(chat_msg=message)
        return response.text

    def extract_text_from_file(self,resume_path):
        """Extract pdf or doc file.

        Args:
            resume_path: system path for user resume.
        
        Returns:
            text: extracted text from resume.
        
        Raises:
            ValueError: if unsupported file provided.
        """
        ext = os.path.splitext(resume_path)[1].lower()
        if ext == '.pdf':
            text = ''
            with pdfplumber.open(resume_path) as pdf:
                text = ''.join([page.extract_text() for page in pdf.pages])
            return text
        elif ext == '.docx':
            doc = Document(resume_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        else:
            raise ValueError("Unsupported file format: Only PDF and DOCX are supported")

    def get_user_prompt(self,resume_path,job_url):
        """generate user prompt.

        Args:
            resume_path: system path os user resume.
            job_url: url of job posted on any company portal.
        """
        try:
            resume = self.extract_text_from_file(resume_path)
            user_prompt = "Please analyze my resume against the following job description and provide an ATS (Applicant Tracking System) compatibility score out of 100.\
                       Also, list any missing or weak keywords, suggest improvements, and briefly summarize how well my resume matches the job requirements.\
                       Resume:"
            user_prompt += f"{resume} "
            user_prompt += f"Job Description: {self.get_job_description(job_url)}"
            return user_prompt
        except Exception as ex:
            raise

    def get_ats_score(self,resume_path,job_url):
        """generate ATS Score.

        Args:
            resume_path: system path os user resume.
            job_url: url of job posted on any company portal.

        Returns:
            text: Ats score with explaination where is the gap.
        """
        response = self.model.chat(
            
            chat_msg=[
                {"role": "system", "content": self.ATS_system_prompt},
                {"role": "user", "content": self.get_user_prompt(resume_path,job_url)}
            ],
        )
        return response.text
    
if __name__=="__main__":
    model = GPT_Model()
    job_url = "https://www.amazon.jobs/en/jobs/3004585/sde"
    resume_path = "C:\\resume.pdf"
    ats = ATS(model)
    # print(ats.extract_text_from_file(resume_path))
    print(ats.get_ats_score(resume_path,job_url))

