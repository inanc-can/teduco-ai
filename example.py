from fpdf import FPDF

class PDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'MOCK DOCUMENT - FOR TESTING PURPOSES ONLY', 0, 1, 'C')
        self.ln(10)

def create_transcript():
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("Arial", size=11)
    
    # Title
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "OFFICIAL HIGH SCHOOL TRANSCRIPT", 0, 1, 'C')
    pdf.set_font("Arial", size=11)
    pdf.ln(5)
    
    # Student Info
    pdf.cell(0, 8, "Student: John Doe", 0, 1)
    pdf.cell(0, 8, "ID: 123456789", 0, 1)
    pdf.cell(0, 8, "DOB: 01/01/2005", 0, 1)
    pdf.ln(10)
    
    # Grades Table
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(60, 10, "Subject", 1)
    pdf.cell(30, 10, "Grade 10", 1)
    pdf.cell(30, 10, "Grade 11", 1)
    pdf.cell(30, 10, "Grade 12", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=11)
    data = [
        ["Mathematics", "90", "92", "88"],
        ["Physics", "85", "85", "90"],
        ["Chemistry", "88", "82", "85"],
        ["Biology", "90", "92", "94"],
        ["Literature", "85", "90", "92"],
        ["English", "95", "98", "98"],
    ]
    
    for row in data:
        pdf.cell(60, 10, row[0], 1)
        pdf.cell(30, 10, row[1], 1)
        pdf.cell(30, 10, row[2], 1)
        pdf.cell(30, 10, row[3], 1)
        pdf.ln()
        
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Cumulative GPA: 89.5 / 100", 0, 1)
    
    pdf.output("mock_transcript.pdf")
    print("Generated: mock_transcript.pdf")

def create_diploma():
    pdf = PDF()
    pdf.add_page()
    
    pdf.ln(20)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, "HIGH SCHOOL DIPLOMA", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "This certifies that\n\nJOHN DOE\n\nhas successfully completed the Course of Study prescribed by the Ministry of National Education and is entitled to this Diploma.", align='C')
    
    pdf.ln(20)
    pdf.cell(0, 10, "Graduation Date: 15 June 2024", 0, 1, 'C')
    pdf.cell(0, 10, "Diploma Grade: 4.5 / 5.0", 0, 1, 'C')
    
    pdf.ln(30)
    pdf.cell(0, 10, "_________________________", 0, 1, 'C')
    pdf.cell(0, 10, "School Principal", 0, 1, 'C')
    
    pdf.output("mock_diploma.pdf")
    print("Generated: mock_diploma.pdf")

def create_osym():
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "OSYM PLACEMENT RESULT (YKS)", 0, 1, 'C')
    pdf.ln(5)
    
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, "Candidate: John Doe", 0, 1)
    pdf.cell(0, 8, "TC Number: 12345678901", 0, 1)
    pdf.ln(5)
    
    # Scores
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 10, "Exam Scores:", 0, 1)
    pdf.set_font("Arial", size=11)
    pdf.cell(0, 8, "- TYT Score: 450.123", 0, 1)
    pdf.cell(0, 8, "- AYT (Numerical): 480.678", 0, 1)
    pdf.cell(0, 8, "- Ranking: 12,500", 0, 1)
    
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "PLACEMENT RESULT:", 0, 1)
    pdf.ln(5)
    pdf.set_border(1) # Visual box
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, "MIDDLE EAST TECHNICAL UNIVERSITY (ANKARA)\nFaculty of Engineering\nComputer Engineering (English)")
    
    pdf.output("mock_osym_result.pdf")
    print("Generated: mock_osym_result.pdf")

def create_ielts():
    pdf = PDF()
    pdf.add_page()
    
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Test Report Form - IELTS", 0, 1, 'C')
    pdf.ln(10)
    
    pdf.set_font("Arial", size=12)
    pdf.cell(0, 10, "Candidate Name: DOE, JOHN", 0, 1)
    pdf.cell(0, 10, "Candidate Number: 001234", 0, 1)
    pdf.ln(10)
    
    # Score Grid
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Listening", 1)
    pdf.cell(40, 10, "Reading", 1)
    pdf.cell(40, 10, "Writing", 1)
    pdf.cell(40, 10, "Speaking", 1)
    pdf.ln()
    
    pdf.set_font("Arial", size=12)
    pdf.cell(40, 10, "7.5", 1)
    pdf.cell(40, 10, "8.0", 1)
    pdf.cell(40, 10, "6.5", 1)
    pdf.cell(40, 10, "7.0", 1)
    pdf.ln(20)
    
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, "OVERALL BAND SCORE: 7.5", 0, 1, 'C')
    pdf.cell(0, 10, "CEFR Level: C1", 0, 1, 'C')
    
    pdf.output("mock_ielts.pdf")
    print("Generated: mock_ielts.pdf")

if __name__ == "__main__":
    create_transcript()
    create_diploma()
    create_osym()
    create_ielts()