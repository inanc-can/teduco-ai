"use client";

import { useState } from "react";
import { useForm, Controller } from "react-hook-form";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Check, Loader2, Upload, X } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import Multiselect, { type Option } from "@/components/ui/multiselect";
import { toast } from "sonner";
import { cn } from "@/lib/utils";
import { getStepSchema, type OnboardingFormValues } from "@/lib/schemas/onboarding";
import { useCompleteOnboarding } from "@/hooks/api/use-user";
import { apiClient } from "@/lib/api-client";

const steps = [
  { id: "personal", title: "Personal" },
  { id: "profile", title: "Profile" },
  { id: "education", title: "Education" },
  { id: "documents", title: "Documents" },
  { id: "review", title: "Review" },
];

type ApplicantType = "high-school" | "university";

type DocumentRequirement = {
  id: string;
  label: string;
  detail: string;
};

const DOCUMENT_REQUIREMENTS: Record<ApplicantType, DocumentRequirement[]> = {
  "high-school": [
    { id: "transcript", label: "High school transcript", detail: "Latest transcript (Turkish + translated copy)." },
    { id: "diploma", label: "Diploma / graduation certificate", detail: "Diploma or equivalency." },
    { id: "osym", label: "ÖSYM Placement Result", detail: "YKS Yerleştirme Sonuç Belgesi (Required for Germany)." },
    { id: "language", label: "Language certificate", detail: "IELTS, TOEFL, PTE, TestDaF, or planned exam." },
  ],
  university: [
    { id: "transcript", label: "University transcript", detail: "Detailed transcript (Turkish + English)." },
    { id: "course", label: "Course descriptions", detail: "Syllabus snippets for transfer review." },
    { id: "language", label: "Language certificate", detail: "IELTS/TOEFL/TestDaF/C1 or planned exam." },
    { id: "statement", label: "Statement of purpose", detail: "Outline, draft, or bullet points you already have." },
    { id: "rec", label: "Recommendation", detail: "Lecturer/employer letter (Turkish or English)." },
    { id: "portfolio", label: "Portfolio", detail: "Design, research summary, or coding showcase." },
  ],
};

const countryOptions = ["Germany", "Netherlands", "Canada", "USA", "UK", "Australia", "France", "Sweden", "Austria", "Other"];
const fieldOptions = ["Computer Science", "Engineering", "Business", "Medicine", "Law", "Arts", "Social Sciences", "Other"];
const programOptions = ["Bachelor's", "Master's", "PhD", "Exchange", "Other"];
const intakeOptions = ["Fall 2025", "Spring 2026", "Fall 2026", "Spring 2027"];

interface OnboardingFormProps {
  onComplete?: (data: OnboardingFormValues) => void;
}

const initialFormData: Partial<OnboardingFormValues> = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  applicantType: undefined,
  currentCity: "",
  desiredCountries: [],
  desiredField: [],
  targetProgram: [],
  preferredIntake: "",
  highSchoolName: "",
  highSchoolGPA: undefined,
  highSchoolGPAScale: "",
  highSchoolGradYear: undefined,
  yksPlaced: "",
  universityName: "",
  universityProgram: "",
  universityGPA: undefined,
  creditsCompleted: undefined,
  expectedGraduation: "",
  studyMode: "",
  researchFocus: "",
  portfolioLink: "",
  preferredSupport: "",
  documents: [],
  additionalNotes: "",
};

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
};

const contentVariants = {
  hidden: { opacity: 0, x: 50 },
  visible: { opacity: 1, x: 0, transition: { duration: 0.3 } },
  exit: { opacity: 0, x: -50, transition: { duration: 0.2 } },
};

const OnboardingForm = ({ onComplete }: OnboardingFormProps) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [documentFiles, setDocumentFiles] = useState<Record<string, File[]>>({});
  const [isUploading, setIsUploading] = useState(false);

  // React Query mutation
  const completeOnboarding = useCompleteOnboarding();
  
  const {
    control,
    register,
    handleSubmit: rhfHandleSubmit,
    watch,
    formState: { errors },
    getValues,
    setError,
  } = useForm({
    defaultValues: initialFormData,
    mode: "onChange",
  });

  const formData = watch();

  const applicantType = formData.applicantType as ApplicantType | undefined;
  const documentsList = applicantType ? DOCUMENT_REQUIREMENTS[applicantType] : DOCUMENT_REQUIREMENTS["high-school"];
  const highSchoolPath = applicantType === "high-school";
  const universityPath = applicantType === "university";
  const selectedDocuments = formData.documents || [];

  const handleFileUpload = (documentId: string, files: FileList | null) => {
    if (!files) return;
    
    const fileArray = Array.from(files);
    setDocumentFiles(prev => ({
      ...prev,
      [documentId]: [...(prev[documentId] || []), ...fileArray]
    }));
  };

  const removeFile = (documentId: string, fileIndex: number) => {
    setDocumentFiles(prev => ({
      ...prev,
      [documentId]: prev[documentId].filter((_, index) => index !== fileIndex)
    }));
  };

  const nextStep = async () => {
    const stepSchema = getStepSchema(currentStep, applicantType);
    const values = getValues();
    console.log("Validating step", currentStep, "with values:", values);
    const result = stepSchema.safeParse(values);
    
    if (!result.success) {
      console.log("Validation errors:", result.error.flatten().fieldErrors);
      // Set errors in react-hook-form so they display under fields
      const fieldErrors = result.error.flatten().fieldErrors;
      Object.entries(fieldErrors).forEach(([field, messages]) => {
        if (messages && messages.length > 0) {
          setError(field as Parameters<typeof setError>[0], {
            type: "manual",
            message: messages[0],
          });
        }
      });
      
      // Also show toast
      toast.error("Please complete all required fields");
      return;
    }
    
    console.log("Validation passed, moving to next step");
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleFormSubmit = async (data: Record<string, unknown>) => {
    try {
      // Transform numeric fields to ensure they're proper numbers (not strings or NaN)
      const transformedData = {
        ...data,
        highSchoolGPA: data.highSchoolGPA !== undefined && data.highSchoolGPA !== "" && !Number.isNaN(data.highSchoolGPA)
          ? Number(data.highSchoolGPA)
          : undefined,
        highSchoolGradYear: data.highSchoolGradYear !== undefined && data.highSchoolGradYear !== "" && !Number.isNaN(data.highSchoolGradYear)
          ? Number(data.highSchoolGradYear)
          : undefined,
        universityGPA: data.universityGPA !== undefined && data.universityGPA !== "" && !Number.isNaN(data.universityGPA)
          ? Number(data.universityGPA)
          : undefined,
        creditsCompleted: data.creditsCompleted !== undefined && data.creditsCompleted !== "" && !Number.isNaN(data.creditsCompleted)
          ? Number(data.creditsCompleted)
          : undefined,
      };

      await completeOnboarding.mutateAsync(transformedData as OnboardingFormValues)

      // Upload document files if any were selected
      const allFiles = Object.entries(documentFiles).flatMap(
        ([docType, files]) => files.map((file) => ({ file, docType }))
      );

      if (allFiles.length > 0) {
        setIsUploading(true);
        try {
          const results = await Promise.allSettled(
            allFiles.map(({ file, docType }) =>
              apiClient.uploadDocument(file, docType)
            )
          );

          const failed = results.filter((r) => r.status === "rejected").length;
          if (failed > 0 && failed < allFiles.length) {
            toast.warning(
              `${allFiles.length - failed} of ${allFiles.length} documents uploaded. You can upload the rest from your dashboard.`
            );
          } else if (failed === allFiles.length) {
            toast.warning(
              "Documents could not be uploaded. You can upload them from your dashboard."
            );
          }
        } finally {
          setIsUploading(false);
        }
      }

      onComplete?.(transformedData as OnboardingFormValues)
    } catch (error) {
      // Error already handled by the hook
      console.error("Submission error:", error)
    }
  };



  const summaryRows = [
    { label: "Applicant", value: `${formData.firstName || ''} ${formData.lastName || ''}`.trim() },
    { label: "Email", value: formData.email || '' },
    { label: "City", value: formData.currentCity || '' },
    { label: "Target Countries", value: (formData.desiredCountries || []).join(", ") },
    { label: "Fields", value: (formData.desiredField || []).join(", ") },
    { label: "Programs", value: (formData.targetProgram || []).join(", ") },
    { label: "Intake", value: formData.preferredIntake || '' },
  ];

  return (
    <div className="w-full">
      <motion.div className="mb-8" initial={{ opacity: 0, y: -24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }}>
        <div className="flex justify-between mb-2">
          {steps.map((step, index) => (
            <motion.div key={step.id} className="flex flex-col items-center" whileHover={{ scale: 1.05 }}>
              <motion.div
                className={cn(
                  "w-4 h-4 rounded-full transition-colors duration-200",
                  index < currentStep
                    ? "bg-primary"
                    : index === currentStep
                      ? "bg-primary ring-4 ring-primary/20"
                      : "bg-muted"
                )}
              />
              <span className={cn("text-xs mt-1.5 hidden sm:block", index === currentStep ? "text-primary font-medium" : "text-muted-foreground")}>
                {step.title}
              </span>
            </motion.div>
          ))}
        </div>
        <div className="w-full bg-muted h-1.5 rounded-full overflow-hidden">
          <motion.div
            className="h-full bg-primary"
            initial={{ width: 0 }}
            animate={{ width: `${(currentStep / (steps.length - 1)) * 100}%` }}
            transition={{ duration: 0.3 }}
          />
        </div>
      </motion.div>

      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5, delay: 0.2 }}>
        <Card className="border shadow-md rounded-3xl overflow-hidden">
          <div>
            <AnimatePresence mode="wait">
              <motion.div key={currentStep} initial="hidden" animate="visible" exit="exit" variants={contentVariants}>
                {currentStep === 0 && (
                  <>
                    <CardHeader>
                      <CardTitle>Personal Information</CardTitle>
                      <CardDescription>Start with your name, email, and phone so we can reach you in Turkish.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="firstName">First name</Label>
                          <Input
                            id="firstName"
                            placeholder="Ayşe"
                            className="mt-2"
                            {...register("firstName")}
                          />
                          {errors.firstName && <p className="text-xs text-red-500">{errors.firstName.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="lastName">Last name</Label>
                          <Input
                            id="lastName"
                            placeholder="Yılmaz"
                            className="mt-2"
                            {...register("lastName")}
                          />
                          {errors.lastName && <p className="text-xs text-red-500">{errors.lastName.message}</p>}
                        </div>
                      </motion.div>
                      <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            placeholder="ayse@example.com"
                            className="mt-2"
                            {...register("email")}
                          />
                          {errors.email && <p className="text-xs text-red-500">{errors.email.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="phone">Phone / WhatsApp</Label>
                          <Input
                            id="phone"
                            placeholder="0505 123 45 67"
                            className="mt-2"
                            {...register("phone")}
                          />
                          {errors.phone && <p className="text-xs text-red-500">{errors.phone.message}</p>}
                        </div>
                      </motion.div>
                    </CardContent>
                  </>
                )}

                {currentStep === 1 && (
                  <>
                    <CardHeader>
                      <CardTitle>Applicant Profile</CardTitle>
                      <CardDescription>Help us tailor the journey for Turkish high school or university students.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <motion.div variants={fadeInUp} className="space-y-2">
                        <Label>Applying from</Label>
                        <Controller
                          name="applicantType"
                          control={control}
                          render={({ field }) => (
                            <RadioGroup
                              className="grid gap-3"
                              value={field.value}
                              onValueChange={field.onChange}
                            >
                              <label className="flex items-center gap-3 rounded-xl border px-4 py-3">
                              <RadioGroupItem value="high-school" id="type-hs" />
                              <div>
                                <p className="font-semibold">High school student</p>
                                <p className="text-xs text-muted-foreground">Applying for undergraduate programs directly out of high school.</p>
                              </div>
                              </label>
                              <label className="flex items-center gap-3 rounded-xl border px-4 py-3">
                              <RadioGroupItem value="university" id="type-uni" />
                              <div>
                                <p className="font-semibold">University student</p>
                                <p className="text-xs text-muted-foreground">Transferring, continuing, or doing a dual degree abroad.</p>
                              </div>
                              </label>
                            </RadioGroup>
                          )}
                        />
                        {errors.applicantType && <p className="text-xs text-red-500">{errors.applicantType.message}</p>}
                      </motion.div>
                      <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="desiredCountries">Preferred countries</Label>
                          <Controller
                            name="desiredCountries"
                            control={control}
                            render={({ field }) => (
                              <Multiselect
                                options={countryOptions.map(country => ({ label: country, value: country }))}
                                value={(field.value || []).map(country => ({ label: country, value: country }))}
                                onChange={(options: Option[]) => field.onChange(options.map(o => o.value))}
                                placeholder="Select countries"
                              />
                            )}
                          />
                          {errors.desiredCountries && <p className="text-xs text-red-500">{errors.desiredCountries.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="desiredField">Field / major</Label>
                          <Controller
                            name="desiredField"
                            control={control}
                            render={({ field }) => (
                              <Multiselect
                                options={fieldOptions.map(f => ({ label: f, value: f }))}
                                value={(field.value || []).map(f => ({ label: f, value: f }))}
                                onChange={(options: Option[]) => field.onChange(options.map(o => o.value))}
                                placeholder="Select fields"
                              />
                            )}
                          />
                          {errors.desiredField && <p className="text-xs text-red-500">{errors.desiredField.message}</p>}
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="targetProgram">Target program</Label>
                          <Controller
                            name="targetProgram"
                            control={control}
                            render={({ field }) => (
                              <Multiselect
                                options={programOptions.map(program => ({ label: program, value: program }))}
                                value={(field.value || []).map(program => ({ label: program, value: program }))}
                                onChange={(options: Option[]) => field.onChange(options.map(o => o.value))}
                                placeholder="Select programs"
                              />
                            )}
                          />
                          {errors.targetProgram && <p className="text-xs text-red-500">{errors.targetProgram.message}</p>}
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Preferred intake</Label>
                            <Controller
                              name="preferredIntake"
                              control={control}
                              render={({ field }) => (
                                <Select value={field.value} onValueChange={field.onChange}>
                                  <SelectTrigger>
                                    <SelectValue placeholder="Choose intake" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {intakeOptions.map((option) => (
                                      <SelectItem key={option} value={option}>
                                        {option}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              )}
                            />
                          </div>
                        </div>
                      </motion.div>
                    </CardContent>
                  </>
                )}

                {currentStep === 2 && (
                  <>
                    <CardHeader>
                      <CardTitle>Education Background</CardTitle>
                      <CardDescription>
                        Provide your GPA, graduation year, and any preparatory documents we should know about.
                      </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {highSchoolPath && (
                        <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="highSchoolName">High school name</Label>
                          <Input
                            id="highSchoolName"
                            placeholder="Koç Lisesi"
                            {...register("highSchoolName")}
                          />
                          {errors.highSchoolName && <p className="text-xs text-red-500">{errors.highSchoolName.message}</p>}
                        </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-2">
                              <Label htmlFor="highSchoolGPA">GPA</Label>
                              <Input
                                id="highSchoolGPA"
                                type="number"
                                step="0.01"
                                placeholder="85"
                                {...register("highSchoolGPA", { valueAsNumber: true })}
                              />
                              {errors.highSchoolGPA && <p className="text-xs text-red-500">{errors.highSchoolGPA.message}</p>}
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="highSchoolGPAScale">Scale</Label>
                              <Controller
                                name="highSchoolGPAScale"
                                control={control}
                                render={({ field }) => (
                                  <Select value={field.value} onValueChange={field.onChange}>
                                    <SelectTrigger>
                                      <SelectValue placeholder="/ 100" />
                                    </SelectTrigger>
                                    <SelectContent>
                                      <SelectItem value="100">Out of 100</SelectItem>
                                      <SelectItem value="IB">IB Score</SelectItem>
                                    </SelectContent>
                                  </Select>
                                )}
                              />
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="highSchoolGradYear">Graduation year</Label>
                            <Controller
                              name="highSchoolGradYear"
                              control={control}
                              render={({ field }) => (
                                <Select 
                                  value={field.value?.toString() ?? ""} 
                                  onValueChange={(val) => field.onChange(val ? parseInt(val, 10) : undefined)}
                                >
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select year" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    {Array.from({ length: 10 }, (_, i) => (2024 + i).toString()).map((year) => (
                                      <SelectItem key={year} value={year}>
                                        {year}
                                      </SelectItem>
                                    ))}
                                  </SelectContent>
                                </Select>
                              )}
                            />
                            {errors.highSchoolGradYear && <p className="text-xs text-red-500">{errors.highSchoolGradYear.message}</p>}
                          </div>

                          <div className="space-y-2">
                            <Label>YKS (University Exam) Placement?</Label>
                            <Controller
                              name="yksPlaced"
                              control={control}
                              render={({ field }) => (
                                <Select value={field.value} onValueChange={field.onChange}>
                                  <SelectTrigger>
                                    <SelectValue placeholder="Select status" />
                                  </SelectTrigger>
                                  <SelectContent>
                                    <SelectItem value="yes">Yes, I have been placed</SelectItem>
                                    <SelectItem value="no">No, not yet / not planning</SelectItem>
                                    <SelectItem value="student">I am already a uni student</SelectItem>
                                  </SelectContent>
                                </Select>
                              )}
                            />
                            <p className="text-[10px] text-muted-foreground">Crucial for Germany/Austria applications.</p>
                          </div>
                        </motion.div>
                      )}
                      {universityPath && (
                        <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4">
                          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                              <Label htmlFor="universityName">Current / previous university</Label>
                              <Input
                                id="universityName"
                                placeholder="Middle East Technical University"
                                {...register("universityName")}
                              />
                              {errors.universityName && <p className="text-xs text-red-500">{errors.universityName.message}</p>}
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="universityProgram">Program/location</Label>
                              <Input
                                id="universityProgram"
                                placeholder="Civil Engineering, Ankara"
                                {...register("universityProgram")}
                              />
                              {errors.universityProgram && <p className="text-xs text-red-500">{errors.universityProgram.message}</p>}
                            </div>
                          </div>
                          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                              <Label htmlFor="universityGPA">GPA average</Label>
                              <Input
                                id="universityGPA"
                                type="number"
                                step="0.01"
                                placeholder="3.40"
                                {...register("universityGPA", { valueAsNumber: true })}
                              />
                              {errors.universityGPA && <p className="text-xs text-red-500">{errors.universityGPA.message}</p>}
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="creditsCompleted">Credits completed</Label>
                              <Input
                                id="creditsCompleted"
                                type="number"
                                placeholder="90"
                                {...register("creditsCompleted", { valueAsNumber: true })}
                              />
                              {errors.creditsCompleted && <p className="text-xs text-red-500">{errors.creditsCompleted.message}</p>}
                            </div>
                          </div>
                          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                              <Label htmlFor="expectedGraduation">Expected graduation</Label>
                              <Input
                                id="expectedGraduation"
                                placeholder="June 2025"
                                {...register("expectedGraduation")}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="studyMode">Study mode</Label>
                              <Controller
                                name="studyMode"
                                control={control}
                                render={({ field }) => (
                                  <Select value={field.value} onValueChange={field.onChange}>
                                    <SelectTrigger>
                                      <SelectValue placeholder="Select mode" />
                                    </SelectTrigger>
                                    <SelectContent>
                                      {["Full-time", "Part-time", "Dual degree", "Exchange", "Other"].map((option) => (
                                        <SelectItem key={option} value={option}>
                                          {option}
                                        </SelectItem>
                                      ))}
                                    </SelectContent>
                                  </Select>
                                )}
                              />
                            </div>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="researchFocus">Research / project focus</Label>
                            <Textarea
                              id="researchFocus"
                              placeholder="Artificial intelligence, urban policy, renewable energy"
                              {...register("researchFocus")}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="portfolioLink">Portfolio / project link</Label>
                            <Input
                              id="portfolioLink"
                              placeholder="https://github.com/ayse"
                              {...register("portfolioLink")}
                            />
                          </div>
                        </motion.div>
                      )}
                    </CardContent>
                  </>
                )}

                {currentStep === 3 && (
                  <>
                    <CardHeader>
                      <CardTitle>Documents & Support</CardTitle>
                      <CardDescription>Choose the documents you already have and tell us how we can support you.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <motion.div variants={fadeInUp} className="space-y-2">
                        <Label>Documents on hand</Label>
                        <Controller
                          name="documents"
                          control={control}
                          render={({ field }) => (
                            <div className="grid gap-3 md:grid-cols-2">
                              {documentsList.map((document) => (
                                <label
                                  key={document.id}
                                  className={cn(
                                    "flex flex-col gap-2 rounded-2xl border p-4 cursor-pointer",
                                    (field.value || []).includes(document.id)
                                      ? "border-primary bg-primary/5"
                                      : "border-border"
                                  )}
                                >
                                  <div className="flex items-center gap-2">
                                    <Checkbox
                                      id={`doc-${document.id}`}
                                      checked={(field.value || []).includes(document.id)}
                                      onCheckedChange={(checked) => {
                                        const current = field.value || [];
                                        if (checked) {
                                          field.onChange([...current, document.id]);
                                        } else {
                                          field.onChange(current.filter((id) => id !== document.id));
                                        }
                                      }}
                                    />
                                    <div>
                                      <p className="font-semibold">{document.label}</p>
                                      <p className="text-xs text-muted-foreground">{document.detail}</p>
                                    </div>
                                  </div>
                                </label>
                              ))}
                            </div>
                          )}
                        />
                        {errors.documents && <p className="text-xs text-red-500">{errors.documents.message}</p>}
                      </motion.div>

                      {selectedDocuments.length > 0 && (
                        <motion.div variants={fadeInUp} className="space-y-4">
                          <Label>Upload your documents</Label>
                          <div className="space-y-3">
                            {selectedDocuments.map((docId) => {
                              const document = documentsList.find(d => d.id === docId);
                              if (!document) return null;
                              
                              return (
                                <div key={docId} className="rounded-2xl border p-4 space-y-3">
                                  <div className="flex items-center justify-between">
                                    <div>
                                      <p className="font-semibold text-sm">{document.label}</p>
                                      <p className="text-xs text-muted-foreground">{document.detail}</p>
                                    </div>
                                  </div>
                                  
                                  <div className="space-y-2">
                                    <label 
                                      htmlFor={`file-${docId}`}
                                      className="flex items-center justify-center gap-2 w-full rounded-lg border-2 border-dashed border-muted-foreground/25 p-4 cursor-pointer hover:border-primary/50 hover:bg-primary/5 transition-colors"
                                    >
                                      <Upload className="h-4 w-4 text-muted-foreground" />
                                      <span className="text-sm text-muted-foreground">
                                        Click to upload or drag and drop
                                      </span>
                                      <input
                                        id={`file-${docId}`}
                                        type="file"
                                        multiple
                                        accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                                        className="hidden"
                                        onChange={(e) => handleFileUpload(docId, e.target.files)}
                                      />
                                    </label>
                                    
                                    {documentFiles[docId]?.length > 0 && (
                                      <div className="space-y-2">
                                        {documentFiles[docId].map((file, index) => (
                                          <div 
                                            key={index}
                                            className="flex items-center justify-between bg-muted/50 rounded-lg px-3 py-2"
                                          >
                                            <div className="flex items-center gap-2 flex-1 min-w-0">
                                              <div className="shrink-0 w-8 h-8 rounded bg-primary/10 flex items-center justify-center">
                                                <span className="text-xs font-medium text-primary">
                                                  {file.name.split('.').pop()?.toUpperCase()}
                                                </span>
                                              </div>
                                              <div className="flex-1 min-w-0">
                                                <p className="text-sm font-medium truncate">{file.name}</p>
                                                <p className="text-xs text-muted-foreground">
                                                  {(file.size / 1024).toFixed(1)} KB
                                                </p>
                                              </div>
                                            </div>
                                            <Button
                                              type="button"
                                              variant="ghost"
                                              size="sm"
                                              onClick={() => removeFile(docId, index)}
                                              className="shrink-0 h-8 w-8 p-0"
                                            >
                                              <X className="h-4 w-4" />
                                            </Button>
                                          </div>
                                        ))}
                                      </div>
                                    )}
                                  </div>
                                </div>
                              );
                            })}
                          </div>
                        </motion.div>
                      )}

                      <motion.div variants={fadeInUp} className="space-y-2">
                        <Label htmlFor="preferredSupport">How can we support?</Label>
                        <Textarea
                          id="preferredSupport"
                          placeholder="Study plan, visa consulting, scholarship search, etc."
                          {...register("preferredSupport")}
                        />
                      </motion.div>
                    </CardContent>
                  </>
                )}

                {currentStep === 4 && (
                  <>
                    <CardHeader>
                      <CardTitle>Review & Submit</CardTitle>
                      <CardDescription>Check that everything looks correct before our team contacts you in Turkish.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <motion.div variants={fadeInUp} className="space-y-3">
                        {summaryRows.map((row) => (
                          <div key={row.label} className="grid grid-cols-[120px,1fr] gap-2 text-sm">
                            <span className="font-semibold text-muted-foreground">{row.label}</span>
                            <span className="text-foreground">{row.value || "Not provided"}</span>
                          </div>
                        ))}
                      </motion.div>
                      <motion.div variants={fadeInUp} className="space-y-2">
                        <Label htmlFor="additionalNotes">Additional notes</Label>
                        <Textarea
                          id="additionalNotes"
                          placeholder="Anything else we should communicate to the counselor?"
                          {...register("additionalNotes")}
                        />
                      </motion.div>
                    </CardContent>
                  </>
                )}
              </motion.div>
            </AnimatePresence>
            <CardFooter className="flex justify-between pt-6 pb-4">
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button type="button" variant="outline" onClick={prevStep} disabled={currentStep === 0} className="flex items-center gap-1">
                  <ChevronLeft className="h-4 w-4" /> Back
                </Button>
              </motion.div>
              <motion.div whileHover={{ scale: 1.05 }} whileTap={{ scale: 0.95 }}>
                <Button
                  type="button"
                  onClick={currentStep === steps.length - 1 ? rhfHandleSubmit(handleFormSubmit) : nextStep}
                  disabled={completeOnboarding.isPending || isUploading}
                  className="flex items-center gap-1"
                >
                  {completeOnboarding.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Submitting...
                    </>
                  ) : isUploading ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Uploading documents...
                    </>
                  ) : (
                    <>
                      {currentStep === steps.length - 1 ? "Submit" : "Next"}
                      {currentStep === steps.length - 1 ? <Check className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
                    </>
                  )}
                </Button>
              </motion.div>
            </CardFooter>
          </div>
        </Card>
      </motion.div>
      <motion.div className="mt-4 text-center text-sm text-muted-foreground" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.5, delay: 0.4 }}>
        Step {currentStep + 1} of {steps.length}: {steps[currentStep].title}
      </motion.div>
    </div>
  );
};

export default OnboardingForm;

