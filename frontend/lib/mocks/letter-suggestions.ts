import { Program, AISuggestion, LetterDraft } from '@/lib/types/letters';

export const MOCK_PROGRAMS: Program[] = [
  {
    id: '1',
    name: 'Informatics',
    slug: 'informatics-bachelor-of-science-bsc',
    university: 'Technical University of Munich',
    level: 'bachelor',
  },
  {
    id: '2',
    name: 'Mathematics',
    slug: 'mathematics-master-of-science-msc',
    university: 'Technical University of Munich',
    level: 'master',
  },
  {
    id: '3',
    name: 'Data Science',
    slug: 'mathematics-in-data-science-master-of-science-msc',
    university: 'Technical University of Munich',
    level: 'master',
  },
  {
    id: '4',
    name: 'Games Engineering',
    slug: 'informatics-games-engineering-master-of-science-msc',
    university: 'Technical University of Munich',
    level: 'master',
  },
];

export const MOCK_LETTER_DRAFTS: LetterDraft[] = [
  {
    id: '1',
    title: 'Informatics BSc Application',
    programName: 'Informatics',
    lastEdited: new Date(Date.now() - 1000 * 60 * 30).toISOString(), // 30 minutes ago
    wordCount: 342,
  },
  {
    id: '2',
    title: 'Mathematics MSc Application',
    programName: 'Mathematics',
    lastEdited: new Date(Date.now() - 1000 * 60 * 60 * 24).toISOString(), // 1 day ago
    wordCount: 289,
  },
  {
    id: '3',
    title: 'Data Science MSc Application',
    programName: 'Data Science',
    lastEdited: new Date(Date.now() - 1000 * 60 * 60 * 24 * 3).toISOString(), // 3 days ago
    wordCount: 401,
  },
];

export function generateMockSuggestions(content: string, programSlug?: string): AISuggestion[] {
  const suggestions: AISuggestion[] = [];
  const wordCount = content.trim().split(/\s+/).length;

  // == 1. Objective Corrections (Grammarly Stage) ==

  // Grammar suggestions
  if (content.toLowerCase().includes('i am very passionate')) {
    const index = content.toLowerCase().indexOf('i am very passionate');
    suggestions.push({
      id: 'gram-1',
      category: 'grammar',
      severity: 'info',
      type: 'objective',
      title: 'Stronger alternative',
      description: '"Very" is a weak intensifier.',
      suggestion: 'Use "deeply" or "extremely" instead of "very".',
      replacement: 'I am deeply passionate',
      highlightRange: { start: index, end: index + 20 },
    });
  }

  // Conciseness
  if (content.toLowerCase().includes('due to the fact that')) {
    const index = content.toLowerCase().indexOf('due to the fact that');
    suggestions.push({
      id: 'conc-1',
      category: 'conciseness',
      severity: 'info',
      type: 'objective',
      title: 'Wordy phrasing',
      description: '"Due to the fact that" can be shortened.',
      suggestion: 'Use "Because" for better conciseness.',
      replacement: 'Because',
      highlightRange: { start: index, end: index + 20 },
    });
  }

  // Passive Voice
  if (content.toLowerCase().includes('is being conducted')) {
    const index = content.toLowerCase().indexOf('is being conducted');
    suggestions.push({
      id: 'pass-1',
      category: 'passive-voice',
      severity: 'info',
      type: 'objective',
      title: 'Passive voice detected',
      description: 'Active voice is usually more engaging.',
      suggestion: 'Rephrase using an active verb.',
      highlightRange: { start: index, end: index + 18 },
    });
  }

  // == 2. Strategic Advice (Consultant Stage) ==

  // Tone suggestions
  if (content.toLowerCase().includes('i think') || content.toLowerCase().includes('i believe')) {
    const phrase = content.toLowerCase().includes('i think') ? 'I think' : 'I believe';
    const index = content.toLowerCase().indexOf(phrase.toLowerCase());
    suggestions.push({
      id: 'tone-1',
      category: 'tone',
      severity: 'info',
      type: 'strategic',
      title: 'Use more assertive language',
      description: 'Phrases like "I think" or "I believe" can sound uncertain in application letters.',
      suggestion: 'State your points directly. Instead of "I think I would be a good fit", write "I am well-suited for this program because..."',
      reasoning: 'At TUM, admissions committees look for confidence and clear self-assessment. Avoiding hedges makes your application stronger.',
      highlightRange: { start: index, end: index + phrase.length },
    });
  }

  if (!content.toLowerCase().includes('dear') && !content.toLowerCase().includes('to whom it may concern')) {
    suggestions.push({
      id: 'tone-2',
      category: 'tone',
      severity: 'warning',
      type: 'strategic',
      title: 'Missing formal greeting',
      description: 'Your letter should start with a formal greeting.',
      suggestion: 'Begin with "Dear Admissions Committee," or "Dear Sir/Madam," to establish a professional tone.',
      reasoning: 'German academic culture values formal etiquette. Missing a greeting can be seen as a lack of professionalism.',
    });
  }

  // Structure suggestions
  if (wordCount < 200) {
    suggestions.push({
      id: 'struct-1',
      category: 'structure',
      severity: 'warning',
      type: 'strategic',
      title: 'Letter may be too short',
      description: 'Your application letter is quite brief. Most strong applications are 300-500 words.',
      suggestion: 'Consider expanding on your academic background, relevant experience, and specific interest in this program.',
      reasoning: 'A short letter implies a lack of depth or motivation for the specific TUM program.',
    });
  } else if (wordCount > 600) {
    suggestions.push({
      id: 'struct-2',
      category: 'structure',
      severity: 'info',
      type: 'strategic',
      title: 'Letter may be too long',
      description: 'Your letter exceeds 600 words. Admissions officers prefer concise, focused letters.',
      suggestion: 'Review your content and remove any redundant information. Aim for 300-500 words.',
      reasoning: 'TUM reviewers often have thousands of applications; being concise shows respect for their time and clarity of thought.',
    });
  }

  if (!content.toLowerCase().includes('sincerely') && !content.toLowerCase().includes('regards')) {
    suggestions.push({
      id: 'struct-3',
      category: 'structure',
      severity: 'warning',
      type: 'strategic',
      title: 'Missing closing statement',
      description: 'Your letter should end with a formal closing.',
      suggestion: 'End with "Sincerely," or "Best regards," followed by your name.',
      reasoning: 'A formal closing is standard in German academic applications.',
    });
  }

  // == 3. Program-Specific Strategy (Expert Stage) ==
  if (programSlug === 'informatics-bachelor-of-science-bsc') {
    if (!content.toLowerCase().includes('programming') && !content.toLowerCase().includes('software')) {
      suggestions.push({
        id: 'prog-1',
        category: 'program-alignment',
        severity: 'info',
        type: 'strategic',
        title: 'Highlight technical skills',
        description: 'For an Informatics program, emphasize your programming and technical experience.',
        suggestion: 'Mention specific programming languages, projects, or technologies you\'ve worked with to demonstrate your readiness.',
        reasoning: 'TUM Informatics is highly technical. Highlighting these skills immediately signals your readiness for the coursework.',
      });
    }

    if (!content.toLowerCase().includes('problem') && !content.toLowerCase().includes('analytical')) {
      suggestions.push({
        id: 'prog-2',
        category: 'program-alignment',
        severity: 'info',
        type: 'strategic',
        title: 'Emphasize analytical thinking',
        description: 'TUM\'s Informatics program values problem-solving and abstract thinking.',
        suggestion: 'Describe situations where you\'ve applied analytical or problem-solving skills, such as in mathematics, logic puzzles, or coding challenges.',
        reasoning: 'Demonstrating an "analytical mindset" is key for the aptitude assessment score at TUM.',
      });
    }
  }

  if (programSlug === 'mathematics-master-of-science-msc') {
    if (!content.toLowerCase().includes('research') && !content.toLowerCase().includes('thesis')) {
      suggestions.push({
        id: 'prog-3',
        category: 'program-alignment',
        severity: 'warning',
        type: 'strategic',
        title: 'Mention research experience',
        description: 'Master\'s programs value research background and academic rigor.',
        suggestion: 'Discuss any research projects, bachelor thesis, or independent studies you\'ve completed. Mention specific mathematical areas that interest you.',
        reasoning: 'TUM Master\'s programs are research-oriented. Evidence of prior research strongly correlates with success in the Master\'s thesis phase.',
      });
    }
  }

  // General program alignment
  if (!content.toLowerCase().includes('double degree') && programSlug?.includes('master')) {
    suggestions.push({
      id: 'prog-4',
      category: 'content',
      severity: 'info',
      type: 'strategic',
      title: 'Mention international perspective',
      description: 'TUM values international experience and global perspective.',
      suggestion: 'Consider mentioning any international projects or your interest in TUM\'s global network.',
      reasoning: 'TUM is one of Europe\'s most international universities. Showing a global mindset fits the university\'s "The Entrepreneurial University" vision.',
    });
  }

  return suggestions;
}
