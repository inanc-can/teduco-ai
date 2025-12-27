/**
 * Mock student profiles for testing
 */

export interface MockStudent {
  firstName: string
  lastName: string
  email: string
  education: {
    level: 'undergraduate' | 'graduate' | 'high-school'
    gpa: number
    major?: string
    schoolName: string
  }
  preferences: {
    countries: string[]
    budget: number
    fieldOfStudy: string
  }
}

export const mockStudents: Record<string, MockStudent> = {
  undergraduate: {
    firstName: 'Ahmet',
    lastName: 'Yılmaz',
    email: 'ahmet.yilmaz@test.com',
    education: {
      level: 'undergraduate',
      gpa: 3.5,
      major: 'Computer Science',
      schoolName: 'Boğaziçi University',
    },
    preferences: {
      countries: ['USA', 'UK', 'Germany'],
      budget: 30000,
      fieldOfStudy: 'Computer Science',
    },
  },
  graduate: {
    firstName: 'Zeynep',
    lastName: 'Kaya',
    email: 'zeynep.kaya@test.com',
    education: {
      level: 'graduate',
      gpa: 3.8,
      major: 'Data Science',
      schoolName: 'Middle East Technical University',
    },
    preferences: {
      countries: ['USA', 'Canada', 'Netherlands'],
      budget: 40000,
      fieldOfStudy: 'Artificial Intelligence',
    },
  },
  highSchool: {
    firstName: 'Mehmet',
    lastName: 'Demir',
    email: 'mehmet.demir@test.com',
    education: {
      level: 'high-school',
      gpa: 4.2,
      schoolName: 'Istanbul Lisesi',
    },
    preferences: {
      countries: ['UK', 'USA', 'Germany'],
      budget: 25000,
      fieldOfStudy: 'Engineering',
    },
  },
}

export const mockUniversities = [
  {
    id: 'uni-001',
    name: 'Massachusetts Institute of Technology',
    shortName: 'MIT',
    country: 'USA',
    city: 'Cambridge',
    tuitionUsd: 55000,
    programs: ['Computer Science', 'Engineering', 'Physics'],
    requirements: {
      gpaMin: 3.5,
      toeflMin: 100,
      ieltsMin: 7.5,
    },
    ranking: 1,
  },
  {
    id: 'uni-002',
    name: 'University of Oxford',
    shortName: 'Oxford',
    country: 'UK',
    city: 'Oxford',
    tuitionUsd: 45000,
    programs: ['Computer Science', 'Mathematics', 'Philosophy'],
    requirements: {
      gpaMin: 3.7,
      toeflMin: 110,
      ieltsMin: 7.5,
    },
    ranking: 2,
  },
  {
    id: 'uni-003',
    name: 'Technical University of Munich',
    shortName: 'TUM',
    country: 'Germany',
    city: 'Munich',
    tuitionUsd: 0,
    programs: ['Computer Science', 'Engineering', 'Data Science'],
    requirements: {
      gpaMin: 3.0,
      toeflMin: 88,
      ieltsMin: 6.5,
    },
    ranking: 15,
  },
]

export const mockChatMessages = [
  {
    id: 'msg-001',
    chatId: 'chat-001',
    role: 'user',
    content: 'What are the best universities for Computer Science in the USA?',
    timestamp: '2025-01-01T10:00:00Z',
  },
  {
    id: 'msg-002',
    chatId: 'chat-001',
    role: 'assistant',
    content:
      'Based on rankings and reputation, the top universities for Computer Science in the USA include:\n\n1. MIT - Known for cutting-edge research\n2. Stanford - Strong industry connections\n3. Carnegie Mellon - Excellent CS program',
    timestamp: '2025-01-01T10:00:05Z',
    sources: [
      { id: 'uni-001', title: 'MIT Computer Science', url: '#' },
    ],
  },
]

export const mockDocuments = [
  {
    documentId: 'doc-001',
    fileName: 'transcript.pdf',
    fileSize: 1024 * 100, // 100 KB
    docType: 'transcript',
    uploadedAt: '2025-01-01T09:00:00Z',
    status: 'processed',
  },
  {
    documentId: 'doc-002',
    fileName: 'diploma.pdf',
    fileSize: 1024 * 150, // 150 KB
    docType: 'diploma',
    uploadedAt: '2025-01-01T09:30:00Z',
    status: 'processed',
  },
]
