import { z } from "zod";

// University schema matching backend UniversityIn model
export const universitySchema = z.object({
  name: z.string().min(1, "University name is required"),
  country: z.string().min(1, "Country is required"),
});

export type UniversityIn = z.infer<typeof universitySchema>;

export interface UniversityResponse {
  university_id: number;
}
