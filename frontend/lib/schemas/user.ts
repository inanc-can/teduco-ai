import { z } from "zod";

// User schema matching backend UserIn model
export const userSchema = z.object({
  fname: z.string().min(1, "First name is required"),
  lname: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email address"),
  password: z.string().min(8, "Password must be at least 8 characters"),
  birth_date: z.string().optional(),
});

export type UserIn = z.infer<typeof userSchema>;

export interface UserResponse {
  user_id: number;
}
