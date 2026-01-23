"""
Generate test user PDF documents (transcripts and CVs)
"""
from fpdf import FPDF
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

class TranscriptPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 14)
        self.cell(0, 10, self.title, align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', align='C')

class CVPDF(FPDF):
    def header(self):
        self.set_font('Helvetica', 'B', 16)
        self.cell(0, 10, 'Curriculum Vitae', align='C', new_x='LMARGIN', new_y='NEXT')
        self.ln(5)

def generate_elif_transcript():
    """Generate high school transcript for Elif Yilmaz"""
    pdf = TranscriptPDF()
    pdf.title = "Istanbul Erkek Lisesi - Official Transcript"
    pdf.add_page()

    # Header info
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'STUDENT INFORMATION', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'Name: Elif Yilmaz', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Student ID: 2021-1234', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Date of Birth: March 15, 2007', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Enrollment Year: 2021', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Expected Graduation: June 2025', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Grades table
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'ACADEMIC RECORD', new_x='LMARGIN', new_y='NEXT')

    # Table header
    pdf.set_font('Helvetica', 'B', 9)
    pdf.cell(80, 7, 'Subject', border=1)
    pdf.cell(30, 7, 'Grade 11', border=1, align='C')
    pdf.cell(30, 7, 'Grade 12', border=1, align='C')
    pdf.cell(30, 7, 'Average', border=1, align='C', new_x='LMARGIN', new_y='NEXT')

    # Subjects
    subjects = [
        ('Mathematics', 95, 96, 95.5),
        ('Physics', 92, 94, 93.0),
        ('Chemistry', 88, 90, 89.0),
        ('Biology', 85, 87, 86.0),
        ('Turkish Language', 90, 91, 90.5),
        ('English', 94, 95, 94.5),
        ('German', 88, 92, 90.0),
        ('History', 87, 88, 87.5),
        ('Geography', 86, 88, 87.0),
        ('Computer Science', 98, 99, 98.5),
        ('Physical Education', 95, 95, 95.0),
        ('Art', 90, 92, 91.0),
    ]

    pdf.set_font('Helvetica', '', 9)
    for subj, g11, g12, avg in subjects:
        pdf.cell(80, 6, subj, border=1)
        pdf.cell(30, 6, str(g11), border=1, align='C')
        pdf.cell(30, 6, str(g12), border=1, align='C')
        pdf.cell(30, 6, f'{avg:.1f}', border=1, align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, f'CUMULATIVE GPA: 92.0 / 100', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, 'CLASS RANK: 5 / 180', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 6, 'This is an official transcript issued by Istanbul Erkek Lisesi.', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Date of Issue: January 15, 2025', new_x='LMARGIN', new_y='NEXT')

    output_path = os.path.join(BASE_DIR, 'elif_yilmaz', 'student_documents', 'high_school_transcript.pdf')
    pdf.output(output_path)
    print(f"Generated: {output_path}")

def generate_elif_cv():
    """Generate CV for Elif Yilmaz"""
    pdf = CVPDF()
    pdf.add_page()

    # Name
    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 10, 'ELIF YILMAZ', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'Istanbul, Turkey | elif.yilmaz.test@gmail.com | +90 532 123 4567', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)

    # Objective
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'OBJECTIVE', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, 'Passionate high school student seeking to pursue a Bachelor\'s degree in Informatics at TUM, with long-term goal of specializing in Game Development and Computer Graphics.')
    pdf.ln(5)

    # Education
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'EDUCATION', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Istanbul Erkek Lisesi', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, 'High School Diploma (Expected June 2025)', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'GPA: 92/100 | Class Rank: 5/180', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Technical Skills
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'TECHNICAL SKILLS', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Programming: C++, Python, C#, JavaScript', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Game Engines: Unity (3 years), Unreal Engine (1 year)', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- 3D Modeling: Blender, Maya basics', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Version Control: Git, GitHub', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Languages: Turkish (native), English (C1), German (B1)', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Extracurricular
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'EXTRACURRICULAR ACTIVITIES', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Game Development Club - President (2023-2025)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Founded and led club with 25+ members', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Organized game jams and workshops', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Global Game Jam 2024 - Participant', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Developed puzzle game in 48 hours using Unity', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Team of 4, responsible for gameplay programming', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Achievements
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'ACHIEVEMENTS', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- 2nd Place, National High School Programming Competition 2024', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- YKS Score: Top 1% in Mathematics', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Published 3 games on itch.io with 1000+ downloads', new_x='LMARGIN', new_y='NEXT')

    output_path = os.path.join(BASE_DIR, 'elif_yilmaz', 'student_documents', 'cv.pdf')
    pdf.output(output_path)
    print(f"Generated: {output_path}")

def generate_ahmet_transcript():
    """Generate university transcript for Ahmet Ozturk"""
    pdf = TranscriptPDF()
    pdf.title = "Middle East Technical University - Official Transcript"
    pdf.add_page()

    # Header
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'STUDENT INFORMATION', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'Name: Ahmet Ozturk', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Student ID: 2021-2345678', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Department: Computer Engineering', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Faculty: Engineering', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Enrollment: Fall 2021', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Expected Graduation: June 2025', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'COURSE RECORD (Selected Courses)', new_x='LMARGIN', new_y='NEXT')

    # Table header
    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(70, 6, 'Course', border=1)
    pdf.cell(20, 6, 'Credits', border=1, align='C')
    pdf.cell(20, 6, 'Grade', border=1, align='C')
    pdf.cell(30, 6, 'Semester', border=1, align='C', new_x='LMARGIN', new_y='NEXT')

    courses = [
        ('CENG 140 - C Programming', 4, 'AA', 'Fall 2021'),
        ('CENG 213 - Data Structures', 4, 'BA', 'Spr 2022'),
        ('CENG 315 - Algorithms', 4, 'AA', 'Fall 2022'),
        ('CENG 336 - Operating Systems', 4, 'BA', 'Spr 2023'),
        ('CENG 462 - AI', 4, 'AA', 'Fall 2023'),
        ('CENG 477 - Computer Graphics', 4, 'AA', 'Fall 2023'),
        ('CENG 478 - Game Development', 3, 'AA', 'Spr 2024'),
        ('CENG 491 - Senior Project I', 4, 'AA', 'Fall 2024'),
        ('CENG 492 - Senior Project II', 4, 'IP', 'Spr 2025'),
        ('MATH 119 - Calculus I', 4, 'BA', 'Fall 2021'),
        ('MATH 120 - Calculus II', 4, 'BB', 'Spr 2022'),
        ('MATH 260 - Linear Algebra', 4, 'BA', 'Fall 2022'),
        ('STAT 201 - Statistics', 4, 'AA', 'Spr 2022'),
    ]

    pdf.set_font('Helvetica', '', 8)
    for course, cred, grade, sem in courses:
        pdf.cell(70, 5, course, border=1)
        pdf.cell(20, 5, str(cred), border=1, align='C')
        pdf.cell(20, 5, grade, border=1, align='C')
        pdf.cell(30, 5, sem, border=1, align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'CUMULATIVE GPA: 3.45 / 4.00', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, 'CREDITS COMPLETED: 210 / 240', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, 'CREDITS IN PROGRESS: 30', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Thesis: Procedural Dungeon Generation Using Machine Learning', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 5, 'Advisor: Prof. Dr. Mehmet Yildirim', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(8)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(0, 5, 'Official transcript issued by METU Registrar Office', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'Date: January 20, 2025', new_x='LMARGIN', new_y='NEXT')

    output_path = os.path.join(BASE_DIR, 'ahmet_ozturk', 'student_documents', 'university_transcript.pdf')
    pdf.output(output_path)
    print(f"Generated: {output_path}")

def generate_ahmet_cv():
    """Generate CV for Ahmet Ozturk"""
    pdf = CVPDF()
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 10, 'AHMET OZTURK', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'Ankara, Turkey | ahmet.ozturk.test@gmail.com | github.com/ahmetozturk-gamedev', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)

    # Objective
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'OBJECTIVE', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, 'Computer Engineering graduate specializing in Game AI and Procedural Content Generation, seeking Master\'s in Games Engineering at TUM to advance research in intelligent game systems.')
    pdf.ln(5)

    # Education
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'EDUCATION', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Middle East Technical University (METU)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, 'BSc Computer Engineering (Expected June 2025)', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'GPA: 3.45/4.00 | Credits: 210/240', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'Thesis: Procedural Dungeon Generation Using Machine Learning', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Research
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'RESEARCH EXPERIENCE', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Teaching Assistant - Computer Graphics (2023-2024)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Assisted Prof. Yildirim with CENG 477 labs and grading', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Developed supplementary materials for shader programming', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Publication', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, '"Reinforcement Learning for NPC Behavior in Open-World Games" - Turkish Game Development Conference 2024')
    pdf.ln(5)

    # Work Experience
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'WORK EXPERIENCE', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Peak Games - Game Developer Intern (Summer 2024)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Implemented AI systems for mobile puzzle games', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Optimized game performance for low-end devices', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Skills
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'TECHNICAL SKILLS', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Languages: C++, C#, Python, GLSL/HLSL', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Game Engines: Unity, Unreal Engine 5, Godot', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Graphics: OpenGL, DirectX, Ray Tracing basics', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- ML/AI: PyTorch, TensorFlow, Reinforcement Learning', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Languages: Turkish (native), English (C1)', new_x='LMARGIN', new_y='NEXT')

    output_path = os.path.join(BASE_DIR, 'ahmet_ozturk', 'student_documents', 'cv.pdf')
    pdf.output(output_path)
    print(f"Generated: {output_path}")

def generate_zeynep_transcript():
    """Generate university transcript for Zeynep Kaya"""
    pdf = TranscriptPDF()
    pdf.title = "Izmir Institute of Technology - Official Transcript"
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'STUDENT INFORMATION', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'Name: Zeynep Kaya', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Student ID: 2020-3456789', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Department: Mathematics', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Faculty: Science', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Enrollment: Fall 2020', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 6, 'Graduation: January 2025', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'COURSE RECORD (Selected Courses)', new_x='LMARGIN', new_y='NEXT')

    pdf.set_font('Helvetica', 'B', 8)
    pdf.cell(70, 6, 'Course', border=1)
    pdf.cell(20, 6, 'Credits', border=1, align='C')
    pdf.cell(20, 6, 'Grade', border=1, align='C')
    pdf.cell(30, 6, 'Semester', border=1, align='C', new_x='LMARGIN', new_y='NEXT')

    courses = [
        ('MATH 111 - Calculus I', 4, 'AA', 'Fall 2020'),
        ('MATH 112 - Calculus II', 4, 'AA', 'Spr 2021'),
        ('MATH 211 - Linear Algebra', 4, 'AA', 'Fall 2021'),
        ('MATH 301 - Real Analysis', 4, 'BA', 'Fall 2022'),
        ('MATH 341 - Probability Theory', 4, 'AA', 'Fall 2022'),
        ('MATH 342 - Mathematical Statistics', 4, 'AA', 'Spr 2023'),
        ('MATH 421 - Numerical Analysis', 4, 'BA', 'Fall 2023'),
        ('MATH 451 - Statistical Learning', 4, 'AA', 'Spr 2024'),
        ('CENG 111 - Intro to Programming', 3, 'AA', 'Fall 2020'),
        ('CENG 211 - Data Structures', 3, 'BA', 'Fall 2021'),
        ('CENG 311 - Machine Learning', 3, 'AA', 'Fall 2023'),
        ('CENG 411 - Deep Learning', 3, 'AA', 'Spr 2024'),
        ('MATH 490 - Thesis', 8, 'AA', 'Fall 2024'),
    ]

    pdf.set_font('Helvetica', '', 8)
    for course, cred, grade, sem in courses:
        pdf.cell(70, 5, course, border=1)
        pdf.cell(20, 5, str(cred), border=1, align='C')
        pdf.cell(20, 5, grade, border=1, align='C')
        pdf.cell(30, 5, sem, border=1, align='C', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 11)
    pdf.cell(0, 8, 'CUMULATIVE GPA: 3.72 / 4.00', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, 'TOTAL CREDITS: 180', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 8, 'MINOR: Computer Science', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Thesis: Bayesian Methods for High-Dimensional Regression', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 9)
    pdf.cell(0, 5, 'Advisor: Assoc. Prof. Dr. Ayse Demir', new_x='LMARGIN', new_y='NEXT')

    pdf.ln(8)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(0, 5, 'Official transcript issued by IYTE Registrar', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'Date: January 25, 2025', new_x='LMARGIN', new_y='NEXT')

    output_path = os.path.join(BASE_DIR, 'zeynep_kaya', 'student_documents', 'university_transcript.pdf')
    pdf.output(output_path)
    print(f"Generated: {output_path}")

def generate_zeynep_cv():
    """Generate CV for Zeynep Kaya"""
    pdf = CVPDF()
    pdf.add_page()

    pdf.set_font('Helvetica', 'B', 18)
    pdf.cell(0, 10, 'ZEYNEP KAYA', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 6, 'Izmir, Turkey | zeynep.kaya.test@gmail.com | kaggle.com/zeynepkaya', align='C', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(8)

    # Objective
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'OBJECTIVE', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, 'Mathematics graduate with strong foundation in statistical learning and machine learning, seeking Master\'s in Mathematics in Data Science at TUM to pursue career in data science research.')
    pdf.ln(5)

    # Education
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'EDUCATION', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Izmir Institute of Technology (IYTE)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, 'BSc Mathematics (Graduated January 2025)', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'GPA: 3.72/4.00 | Minor: Computer Science', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, 'Thesis: Bayesian Methods for High-Dimensional Regression', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Research
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'RESEARCH & PUBLICATIONS', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Research Assistant - Applied Statistics Lab (2023-2024)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Developed statistical models for healthcare data analysis', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Implemented Bayesian inference algorithms in Python', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Publication', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.multi_cell(0, 5, '"Variable Selection in High-Dimensional Bayesian Regression" - Turkish Statistical Association Journal, 2024')
    pdf.ln(5)

    # Work Experience
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'WORK EXPERIENCE', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', 'B', 10)
    pdf.cell(0, 6, 'Vestel Electronics - Data Analyst Intern (Summer 2024)', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Analyzed customer behavior data using Python and SQL', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Built predictive models for product recommendations', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Created interactive dashboards with Tableau', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Skills
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'TECHNICAL SKILLS', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Programming: Python, R, SQL, MATLAB', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- ML/DL: TensorFlow, PyTorch, scikit-learn, XGBoost', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Statistics: Bayesian inference, regression, time series', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Visualization: Matplotlib, Seaborn, Tableau', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Languages: Turkish (native), English (C1)', new_x='LMARGIN', new_y='NEXT')
    pdf.ln(5)

    # Certifications
    pdf.set_font('Helvetica', 'B', 12)
    pdf.cell(0, 8, 'CERTIFICATIONS', new_x='LMARGIN', new_y='NEXT')
    pdf.set_font('Helvetica', '', 10)
    pdf.cell(0, 5, '- Google Data Analytics Professional Certificate (2024)', new_x='LMARGIN', new_y='NEXT')
    pdf.cell(0, 5, '- Kaggle: 2 Silver Medals in Competitions', new_x='LMARGIN', new_y='NEXT')

    output_path = os.path.join(BASE_DIR, 'zeynep_kaya', 'student_documents', 'cv.pdf')
    pdf.output(output_path)
    print(f"Generated: {output_path}")

if __name__ == '__main__':
    print("Generating PDF documents for test users...")
    generate_elif_transcript()
    generate_elif_cv()
    generate_ahmet_transcript()
    generate_ahmet_cv()
    generate_zeynep_transcript()
    generate_zeynep_cv()
    print("\nAll documents generated successfully!")
