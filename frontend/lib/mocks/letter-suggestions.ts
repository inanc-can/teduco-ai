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

  // Grammar suggestions
  if (content.toLowerCase().includes('i am very passionate')) {
    const index = content.toLowerCase().indexOf('i am very passionate');
    suggestions.push({
      id: 'gram-1',
      category: 'grammar',
      severity: 'info',
      title: 'Avoid weak intensifiers',
      description: '"Very" is often an unnecessary intensifier that weakens your statement.',
      suggestion: 'Consider replacing "very passionate" with a stronger word like "deeply passionate" or "enthusiastic".',
      highlightRange: { start: index, end: index + 20 },
    });
  }

  if (content.match(/\b(alot|a lot)\b/gi)) {
    const match = content.match(/\b(alot|a lot)\b/gi);
    if (match) {
      const index = content.indexOf(match[0]);
      suggestions.push({
        id: 'gram-2',
        category: 'grammar',
        severity: 'warning',
        title: 'Spelling error',
        description: 'Common spelling mistake detected.',
        suggestion: 'Use "a lot" (two words) or consider "many" or "numerous" for formal writing.',
        highlightRange: { start: index, end: index + match[0].length },
      });
    }
  }

  // Tone suggestions
  if (content.toLowerCase().includes('i think') || content.toLowerCase().includes('i believe')) {
    const phrase = content.toLowerCase().includes('i think') ? 'I think' : 'I believe';
    const index = content.toLowerCase().indexOf(phrase.toLowerCase());
    suggestions.push({
      id: 'tone-1',
      category: 'tone',
      severity: 'info',
      title: 'Use more assertive language',
      description: 'Phrases like "I think" or "I believe" can sound uncertain in application letters.',
      suggestion: 'State your points directly. Instead of "I think I would be a good fit", write "I am well-suited for this program because..."',
      highlightRange: { start: index, end: index + phrase.length },
    });
  }

  if (!content.toLowerCase().includes('dear') && !content.toLowerCase().includes('to whom it may concern')) {
    suggestions.push({
      id: 'tone-2',
      category: 'tone',
      severity: 'warning',
      title: 'Missing formal greeting',
      description: 'Your letter should start with a formal greeting.',
      suggestion: 'Begin with "Dear Admissions Committee," or "Dear Sir/Madam," to establish a professional tone.',
    });
  }

  // Structure suggestions
  if (wordCount < 200) {
    suggestions.push({
      id: 'struct-1',
      category: 'structure',
      severity: 'warning',
      title: 'Letter may be too short',
      description: 'Your application letter is quite brief. Most strong applications are 300-500 words.',
      suggestion: 'Consider expanding on your academic background, relevant experience, and specific interest in this program.',
    });
  } else if (wordCount > 600) {
    suggestions.push({
      id: 'struct-2',
      category: 'structure',
      severity: 'info',
      title: 'Letter may be too long',
      description: 'Your letter exceeds 600 words. Admissions officers prefer concise, focused letters.',
      suggestion: 'Review your content and remove any redundant information. Aim for 300-500 words.',
    });
  }

  if (!content.toLowerCase().includes('sincerely') && !content.toLowerCase().includes('regards')) {
    suggestions.push({
      id: 'struct-3',
      category: 'structure',
      severity: 'warning',
      title: 'Missing closing statement',
      description: 'Your letter should end with a formal closing.',
      suggestion: 'End with "Sincerely," or "Best regards," followed by your name.',
    });
  }

  // Program-specific suggestions
  if (programSlug === 'informatics-bachelor-of-science-bsc') {
    if (!content.toLowerCase().includes('programming') && !content.toLowerCase().includes('software')) {
      suggestions.push({
        id: 'prog-1',
        category: 'program-alignment',
        severity: 'info',
        title: 'Highlight technical skills',
        description: 'For an Informatics program, emphasize your programming and technical experience.',
        suggestion: 'Mention specific programming languages, projects, or technologies you\'ve worked with to demonstrate your readiness.',
      });
    }

    if (!content.toLowerCase().includes('problem') && !content.toLowerCase().includes('analytical')) {
      suggestions.push({
        id: 'prog-2',
        category: 'program-alignment',
        severity: 'info',
        title: 'Emphasize analytical thinking',
        description: 'TUM\'s Informatics program values problem-solving and abstract thinking.',
        suggestion: 'Describe situations where you\'ve applied analytical or problem-solving skills, such as in mathematics, logic puzzles, or coding challenges.',
      });
    }
  }

  if (programSlug === 'mathematics-master-of-science-msc') {
    if (!content.toLowerCase().includes('research') && !content.toLowerCase().includes('thesis')) {
      suggestions.push({
        id: 'prog-3',
        category: 'program-alignment',
        severity: 'warning',
        title: 'Mention research experience',
        description: 'Master\'s programs value research background and academic rigor.',
        suggestion: 'Discuss any research projects, bachelor thesis, or independent studies you\'ve completed. Mention specific mathematical areas that interest you.',
      });
    }

    if (!content.toLowerCase().includes('proof') && !content.toLowerCase().includes('theorem')) {
      suggestions.push({
        id: 'prog-4',
        category: 'program-alignment',
        severity: 'info',
        title: 'Demonstrate mathematical maturity',
        description: 'Show your readiness for advanced mathematical study.',
        suggestion: 'Reference your experience with proof-based courses, advanced topics, or mathematical research to demonstrate your preparation.',
      });
    }
  }

  // General program alignment
  if (!content.toLowerCase().includes('tum') && !content.toLowerCase().includes('technical university of munich')) {
    suggestions.push({
      id: 'prog-5',
      category: 'program-alignment',
      severity: 'info',
      title: 'Mention the university specifically',
      description: 'Demonstrate your genuine interest by referencing TUM specifically.',
      suggestion: 'Explain why TUM\'s program is particularly appealing to you. Mention specific faculty, research groups, or program features that attract you.',
    });
  }

  return suggestions;
}
