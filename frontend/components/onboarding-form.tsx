"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Check, Loader2 } from "lucide-react";
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

interface FormData {
  firstName: string;
  lastName: string;
  email: string;
  phone: string;
  applicantType: ApplicantType | "";
  currentCity: string;
  desiredCountries: string[];
  desiredField: string[];
  targetProgram: string[];
  preferredIntake: string;
  highSchoolName: string;
  highSchoolGPA: string;
  highSchoolGPAScale: string;
  highSchoolGradYear: string;
  yksPlaced: string;
  extracurriculars: string;
  scholarshipInterest: string;
  universityName: string;
  universityProgram: string;
  universityGPA: string;
  creditsCompleted: string;
  expectedGraduation: string;
  studyMode: string;
  researchFocus: string;
  portfolioLink: string;
  preferredSupport: string;
  documents: string[];
  additionalNotes: string;
}

interface OnboardingFormProps {
  onComplete?: (data: FormData) => void;
}

const initialFormData: FormData = {
  firstName: "",
  lastName: "",
  email: "",
  phone: "",
  applicantType: "",
  currentCity: "",
  desiredCountries: [],
  desiredField: [],
  targetProgram: [],
  preferredIntake: "",
  highSchoolName: "",
  highSchoolGPA: "",
  highSchoolGPAScale: "",
  highSchoolGradYear: "",
  yksPlaced: "",
  extracurriculars: "",
  scholarshipInterest: "",
  universityName: "",
  universityProgram: "",
  universityGPA: "",
  creditsCompleted: "",
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
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formData, setFormData] = useState<FormData>(initialFormData);

  const applicantType = formData.applicantType as ApplicantType;
  const documentsList = applicantType ? DOCUMENT_REQUIREMENTS[applicantType] : DOCUMENT_REQUIREMENTS["high-school"];
  const highSchoolPath = applicantType === "high-school";
  const universityPath = applicantType === "university";

  const updateFormData = (field: keyof FormData, value: string | string[]) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const toggleDocument = (id: string) => {
    setFormData((prev) => {
      const collection = prev.documents.includes(id)
        ? prev.documents.filter((doc) => doc !== id)
        : [...prev.documents, id];
      return { ...prev, documents: collection };
    });
  };

  const toggleMultiSelect = (field: keyof FormData, value: string) => {
    setFormData((prev) => {
      const current = prev[field] as string[];
      const updated = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current, value];
      return { ...prev, [field]: updated };
    });
  };

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep((prev) => prev + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep((prev) => prev - 1);
    }
  };

  const handleSubmit = () => {
    setIsSubmitting(true);
    setTimeout(() => {
      toast.success("We saved your intake—our counselors will follow up in Turkish shortly.");
      setIsSubmitting(false);
      onComplete?.(formData);
    }, 1500);
  };

  const isStepValid = () => {
    switch (currentStep) {
      case 0:
        return formData.firstName.trim() !== "" && formData.lastName.trim() !== "" && formData.email.trim() !== "";
      case 1:
        return (
          formData.applicantType !== "" &&
          formData.currentCity.trim() !== "" &&
          formData.desiredCountries.length > 0 &&
          formData.desiredField.length > 0 &&
          formData.targetProgram.length > 0
        );
      case 2:
        if (highSchoolPath) {
          return (
            formData.highSchoolName.trim() !== "" &&
            formData.highSchoolGPA.trim() !== "" &&
            formData.highSchoolGradYear.trim() !== ""
          );
        }
        if (universityPath) {
          return (
            formData.universityName.trim() !== "" &&
            formData.universityProgram.trim() !== "" &&
            formData.universityGPA.trim() !== "" &&
            formData.creditsCompleted.trim() !== ""
          );
        }
        return false;
      case 3:
        return formData.documents.length > 0;
      default:
        return true;
    }
  };

  const summaryRows = [
    { label: "Applicant", value: `${formData.firstName} ${formData.lastName}`.trim() },
    { label: "Email", value: formData.email },
    { label: "City", value: formData.currentCity },
    { label: "Target Countries", value: formData.desiredCountries.join(", ") },
    { label: "Fields", value: formData.desiredField.join(", ") },
    { label: "Programs", value: formData.targetProgram.join(", ") },
    { label: "Intake", value: formData.preferredIntake },
  ];

  return (
    <div className="w-full max-w-3xl mx-auto py-10 px-4">
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
                            value={formData.firstName}
                            className="mt-2"
                            onChange={(e) => updateFormData("firstName", e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="lastName">Last name</Label>
                          <Input
                            id="lastName"
                            placeholder="Yılmaz"
                            value={formData.lastName}
                            className="mt-2"
                            onChange={(e) => updateFormData("lastName", e.target.value)}
                          />
                        </div>
                      </motion.div>
                      <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="email">Email</Label>
                          <Input
                            id="email"
                            type="email"
                            placeholder="ayse@example.com"
                            value={formData.email}
                            className="mt-2"
                            onChange={(e) => updateFormData("email", e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="phone">Phone / WhatsApp</Label>
                          <Input
                            id="phone"
                            placeholder="0505 123 45 67"
                            value={formData.phone}
                            className="mt-2"
                            onChange={(e) => updateFormData("phone", e.target.value)}
                          />
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
                        <RadioGroup
                          className="grid gap-3"
                          value={formData.applicantType}
                          onValueChange={(value) => updateFormData("applicantType", value)}
                        >
                          <label className="flex items-start gap-3 rounded-xl border px-4 py-3">
                            <RadioGroupItem value="high-school" id="type-hs" />
                            <div>
                              <p className="font-semibold">High school student</p>
                              <p className="text-xs text-muted-foreground">Applying for undergraduate programs directly out of high school.</p>
                            </div>
                          </label>
                          <label className="flex items-start gap-3 rounded-xl border px-4 py-3">
                            <RadioGroupItem value="university" id="type-uni" />
                            <div>
                              <p className="font-semibold">University student</p>
                              <p className="text-xs text-muted-foreground">Transferring, continuing, or doing a dual degree abroad.</p>
                            </div>
                          </label>
                        </RadioGroup>
                      </motion.div>
                      <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4">
                        <div className="space-y-2">
                          <Label htmlFor="currentCity">Current city</Label>
                          <Input
                            id="currentCity"
                            placeholder="İstanbul"
                            value={formData.currentCity}
                            onChange={(e) => updateFormData("currentCity", e.target.value)}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="desiredCountries">Preferred countries</Label>
                          <Multiselect
                            options={countryOptions.map(country => ({ label: country, value: country }))}
                            value={formData.desiredCountries.map(country => ({ label: country, value: country }))}
                            onChange={(options: Option[]) => updateFormData("desiredCountries", options.map(o => o.value))}
                            placeholder="Select countries"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="desiredField">Field / major</Label>
                          <Multiselect
                            options={fieldOptions.map(field => ({ label: field, value: field }))}
                            value={formData.desiredField.map(field => ({ label: field, value: field }))}
                            onChange={(options: Option[]) => updateFormData("desiredField", options.map(o => o.value))}
                            placeholder="Select fields"
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="targetProgram">Target program</Label>
                          <Multiselect
                            options={programOptions.map(program => ({ label: program, value: program }))}
                            value={formData.targetProgram.map(program => ({ label: program, value: program }))}
                            onChange={(options: Option[]) => updateFormData("targetProgram", options.map(o => o.value))}
                            placeholder="Select programs"
                          />
                        </div>
                        <div className="grid gap-4 md:grid-cols-2">
                          <div className="space-y-2">
                            <Label>Preferred intake</Label>
                            <Select value={formData.preferredIntake} onValueChange={(value) => updateFormData("preferredIntake", value)}>
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
                            value={formData.highSchoolName}
                            onChange={(e) => updateFormData("highSchoolName", e.target.value)}
                          />
                        </div>
                          <div className="grid grid-cols-2 gap-2">
                            <div className="space-y-2">
                              <Label htmlFor="highSchoolGPA">GPA</Label>
                              <Input
                                id="highSchoolGPA"
                                placeholder="85"
                                value={formData.highSchoolGPA}
                                onChange={(e) => updateFormData("highSchoolGPA", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="highSchoolGPAScale">Scale</Label>
                              <Select value={formData.highSchoolGPAScale} onValueChange={(value) => updateFormData("highSchoolGPAScale", value)}>
                                <SelectTrigger>
                                  <SelectValue placeholder="/ 100" />
                                </SelectTrigger>
                                <SelectContent>
                                  <SelectItem value="100">Out of 100</SelectItem>
                                  <SelectItem value="4.0">Out of 4.0</SelectItem>
                                  <SelectItem value="5.0">Out of 5.0</SelectItem>
                                  <SelectItem value="IB">IB Score</SelectItem>
                                </SelectContent>
                              </Select>
                            </div>
                          </div>

                          <div className="space-y-2">
                            <Label htmlFor="highSchoolGradYear">Graduation year</Label>
                            <Input
                              id="highSchoolGradYear"
                              placeholder="2024"
                              value={formData.highSchoolGradYear}
                              onChange={(e) => updateFormData("highSchoolGradYear", e.target.value)}
                            />
                          </div>

                          <div className="space-y-2">
                            <Label>YKS (University Exam) Placement?</Label>
                            <Select value={formData.yksPlaced} onValueChange={(value) => updateFormData("yksPlaced", value)}>
                              <SelectTrigger>
                                <SelectValue placeholder="Select status" />
                              </SelectTrigger>
                              <SelectContent>
                                <SelectItem value="yes">Yes, I have been placed</SelectItem>
                                <SelectItem value="no">No, not yet / not planning</SelectItem>
                                <SelectItem value="student">I am already a uni student</SelectItem>
                              </SelectContent>
                            </Select>
                            <p className="text-[10px] text-muted-foreground">Crucial for Germany/Austria applications.</p>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="extracurriculars">Extracurriculars or awards</Label>
                            <Textarea
                              id="extracurriculars"
                              placeholder="Model United Nations, robotics club, Turkish Olympiad"
                              value={formData.extracurriculars}
                              onChange={(e) => updateFormData("extracurriculars", e.target.value)}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="scholarshipInterest">Scholarship interest?</Label>
                            <Input
                              id="scholarshipInterest"
                              placeholder="Need tuition-free options, partial scholarships"
                              value={formData.scholarshipInterest}
                              onChange={(e) => updateFormData("scholarshipInterest", e.target.value)}
                            />
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
                                value={formData.universityName}
                                onChange={(e) => updateFormData("universityName", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="universityProgram">Program/location</Label>
                              <Input
                                id="universityProgram"
                                placeholder="Civil Engineering, Ankara"
                                value={formData.universityProgram}
                                onChange={(e) => updateFormData("universityProgram", e.target.value)}
                              />
                            </div>
                          </div>
                          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                              <Label htmlFor="universityGPA">GPA average</Label>
                              <Input
                                id="universityGPA"
                                placeholder="3.40 / 3.5"
                                value={formData.universityGPA}
                                onChange={(e) => updateFormData("universityGPA", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="creditsCompleted">Credits completed</Label>
                              <Input
                                id="creditsCompleted"
                                placeholder="90 ECTS / 60 US"
                                value={formData.creditsCompleted}
                                onChange={(e) => updateFormData("creditsCompleted", e.target.value)}
                              />
                            </div>
                          </div>
                          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                            <div className="space-y-2">
                              <Label htmlFor="expectedGraduation">Expected graduation</Label>
                              <Input
                                id="expectedGraduation"
                                placeholder="June 2025"
                                value={formData.expectedGraduation}
                                onChange={(e) => updateFormData("expectedGraduation", e.target.value)}
                              />
                            </div>
                            <div className="space-y-2">
                              <Label htmlFor="studyMode">Study mode</Label>
                              <Select value={formData.studyMode} onValueChange={(value) => updateFormData("studyMode", value)}>
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
                            </div>
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="researchFocus">Research / project focus</Label>
                            <Textarea
                              id="researchFocus"
                              placeholder="Artificial intelligence, urban policy, renewable energy"
                              value={formData.researchFocus}
                              onChange={(e) => updateFormData("researchFocus", e.target.value)}
                            />
                          </div>
                          <div className="space-y-2">
                            <Label htmlFor="portfolioLink">Portfolio / project link</Label>
                            <Input
                              id="portfolioLink"
                              placeholder="https://github.com/ayse"
                              value={formData.portfolioLink}
                              onChange={(e) => updateFormData("portfolioLink", e.target.value)}
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
                        <div className="grid gap-3 md:grid-cols-2">
                          {documentsList.map((document) => (
                            <label
                              key={document.id}
                              className={cn(
                                "flex flex-col gap-2 rounded-2xl border p-4",
                                formData.documents.includes(document.id)
                                  ? "border-primary bg-primary/5"
                                  : "border-border"
                              )}
                            >
                              <div className="flex items-center gap-2">
                                <Checkbox
                                  id={`doc-${document.id}`}
                                  checked={formData.documents.includes(document.id)}
                                  onCheckedChange={() => toggleDocument(document.id)}
                                />
                                <div>
                                  <p className="font-semibold">{document.label}</p>
                                  <p className="text-xs text-muted-foreground">{document.detail}</p>
                                </div>
                              </div>
                            </label>
                          ))}
                        </div>
                      </motion.div>
                      <motion.div variants={fadeInUp} className="space-y-2">
                        <Label htmlFor="preferredSupport">How can we support?</Label>
                        <Textarea
                          id="preferredSupport"
                          placeholder="Study plan, visa consulting, scholarship search, etc."
                          value={formData.preferredSupport}
                          onChange={(e) => updateFormData("preferredSupport", e.target.value)}
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
                          value={formData.additionalNotes}
                          onChange={(e) => updateFormData("additionalNotes", e.target.value)}
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
                  onClick={currentStep === steps.length - 1 ? handleSubmit : nextStep}
                  disabled={!isStepValid() || isSubmitting}
                  className="flex items-center gap-1"
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 className="h-4 w-4 animate-spin" /> Submitting...
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

