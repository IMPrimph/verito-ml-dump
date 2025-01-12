import pdfplumber
import re
from datetime import datetime
import json

class LinkedInPDFParser:
    def __init__(self):
        self.experience_markers = [
            "Experience",
            "Work Experience",
            "Professional Experience"
        ]
        
    def parse_pdf(self, pdf_path):
        """Parse LinkedIn PDF and extract work experience."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
                
                return self.extract_experience(text)
        except Exception as e:
            return {"error": f"Failed to parse PDF: {str(e)}"}
    
    def extract_experience(self, text):
        """Extract work experience sections from text."""
        experiences = []
        
        # Find the experience section
        exp_section = None
        for marker in self.experience_markers:
            if marker in text:
                exp_pattern = f"{marker}.*?(?=Education|Skills|Languages|$)"
                match = re.search(exp_pattern, text, re.DOTALL)
                if match:
                    exp_section = match.group(0)
                    break
        
        if not exp_section:
            return {"error": "No experience section found"}
        
        # Parse individual roles
        # Looking for patterns like:
        # Company Name
        # Title
        # Dates (Month Year - Month Year)
        # Location
        role_pattern = r"(.*?)\n(.*?)\n((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec).*?)\n"
        roles = re.finditer(role_pattern, exp_section)
        
        for role in roles:
            company = role.group(1).strip()
            title = role.group(2).strip()
            dates = role.group(3).strip()
            
            # Parse dates
            dates_pattern = r"(.*?) - (.*?$)"
            dates_match = re.search(dates_pattern, dates)
            if dates_match:
                start_date = dates_match.group(1).strip()
                end_date = dates_match.group(2).strip()
            else:
                start_date = dates
                end_date = "Present"
            
            experiences.append({
                "company": company,
                "title": title,
                "start_date": start_date,
                "end_date": end_date
            })
        
        return {
            "experiences": experiences
        }
    
    def verify_employment(self, parsed_data, company_name):
        """Verify if person worked at specific company."""
        if "error" in parsed_data:
            return {"verified": False, "error": parsed_data["error"]}
            
        company_name = company_name.lower()
        for exp in parsed_data.get("experiences", []):
            if company_name in exp["company"].lower():
                return {
                    "verified": True,
                    "details": {
                        "company": exp["company"],
                        "title": exp["title"],
                        "duration": f"{exp['start_date']} - {exp['end_date']}"
                    }
                }
        
        return {"verified": False, "message": f"No experience found at {company_name}"}

# Example usage
def verify_employment_from_pdf(pdf_path, company_name):
    parser = LinkedInPDFParser()
    parsed_data = parser.parse_pdf(pdf_path)
    return parser.verify_employment(parsed_data, company_name)