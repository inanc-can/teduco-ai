import { z } from "zod";

// Step 1: Personal Information
export const personalSchema = z.object({
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email address"),
  phone: z.string().optional(),
});

// Step 2: Profile
export const profileSchema = z.object({
  applicantType: z.enum(["high-school", "university"], {
    message: "Please select your applicant type",
  }),
  desiredCountries: z.array(z.string()).min(1, "Select at least one country"),
  desiredField: z.array(z.string()).min(1, "Select at least one field"),
  targetProgram: z.array(z.string()).min(1, "Select at least one program"),
  preferredIntake: z.string().optional(),
});

// Step 3: Education (High School)
export const highSchoolEducationSchema = z.object({
  highSchoolName: z.string().min(1, "High school name is required"),
  highSchoolGPA: z.string().min(1, "GPA is required"),
  highSchoolGPAScale: z.string().optional(),
  highSchoolGradYear: z.string().min(1, "Graduation year is required"),
  yksPlaced: z.string().optional(),
  extracurriculars: z.string().optional(),
  scholarshipInterest: z.string().optional(),
});

// Step 3: Education (University)
export const universityEducationSchema = z.object({
  universityName: z.string().min(1, "University name is required"),
  universityProgram: z.string().min(1, "Program is required"),
  universityGPA: z.string().min(1, "GPA is required"),
  creditsCompleted: z.string().min(1, "Credits completed is required"),
  expectedGraduation: z.string().optional(),
  studyMode: z.string().optional(),
  researchFocus: z.string().optional(),
  portfolioLink: z.string().url("Invalid URL").optional().or(z.literal("")),
});

// Step 4: Documents
export const documentsSchema = z.object({
  documents: z.array(z.string()).min(1, "Select at least one document"),
  preferredSupport: z.string().optional(),
});

// Step 5: Review
export const reviewSchema = z.object({
  additionalNotes: z.string().optional(),
});

// Full schema (union of all fields)
export const onboardingSchema = z.object({
  // Personal
  firstName: z.string().min(1, "First name is required"),
  lastName: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email address"),
  phone: z.string().optional(),
  // Profile
  applicantType: z.enum(["high-school", "university"]).optional(),
  currentCity: z.string().optional(),
  desiredCountries: z.array(z.string()).default([]),
  desiredField: z.array(z.string()).default([]),
  targetProgram: z.array(z.string()).default([]),
  preferredIntake: z.string().optional(),
  // High school fields (optional when university path)
  highSchoolName: z.string().optional(),
  highSchoolGPA: z.string().optional(),
  highSchoolGPAScale: z.string().optional(),
  highSchoolGradYear: z.string().optional(),
  yksPlaced: z.string().optional(),
  extracurriculars: z.string().optional(),
  scholarshipInterest: z.string().optional(),
  // University fields (optional when high school path)
  universityName: z.string().optional(),
  universityProgram: z.string().optional(),
  universityGPA: z.string().optional(),
  creditsCompleted: z.string().optional(),
  expectedGraduation: z.string().optional(),
  studyMode: z.string().optional(),
  researchFocus: z.string().optional(),
  portfolioLink: z.string().optional(),
  // Documents & review
  documents: z.array(z.string()).default([]),
  preferredSupport: z.string().optional(),
  additionalNotes: z.string().optional(),
});

export type OnboardingFormValues = z.infer<typeof onboardingSchema>;

// Helper to get step-specific schema
export const getStepSchema = (step: number, applicantType?: "high-school" | "university") => {
  switch (step) {
    case 0:
      return personalSchema;
    case 1:
      return profileSchema;
    case 2:
      if (applicantType === "high-school") {
        return highSchoolEducationSchema;
      }
      if (applicantType === "university") {
        return universityEducationSchema;
      }
      return z.object({}); // fallback
    case 3:
      return documentsSchema;
    case 4:
      return reviewSchema;
    default:
      return z.object({});
  }
};
