-- Fix GPA field precision to support 100-point grading scales
-- numeric(4,2) only supports up to 99.99; change to numeric(6,2) for up to 9999.99

ALTER TABLE public.high_school_education
  ALTER COLUMN gpa TYPE numeric(6,2),
  ALTER COLUMN gpa_scale TYPE numeric(6,2);
