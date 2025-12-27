"use client"

import { useState, useEffect } from "react"
import { useForm, Controller } from "react-hook-form"
import { motion } from "framer-motion"
import { Loader2, Save, User, Briefcase, GraduationCap, FileText, Upload, X, Eye, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import { apiClient } from "@/lib/api-client"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Multiselect, { type Option } from "@/components/ui/multiselect"
import type { OnboardingFormValues } from "@/lib/schemas/onboarding"
import { useSettings, useUpdateSettings } from "@/hooks/api/use-settings"
import { useDocuments, useUploadDocument, useDeleteDocument } from "@/hooks/api/use-documents"

type ApplicantType = "high-school" | "university"

type DocumentRequirement = {
  id: string
  label: string
  detail: string
}

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
}

const countryOptions = ["Germany", "Netherlands", "Canada", "USA", "UK", "Australia", "France", "Sweden", "Austria", "Other"]
const fieldOptions = ["Computer Science", "Engineering", "Business", "Medicine", "Law", "Arts", "Social Sciences", "Other"]
const programOptions = ["Bachelor's", "Master's", "PhD", "Exchange", "Other"]
const intakeOptions = ["Fall 2025", "Spring 2026", "Fall 2026", "Spring 2027"]

const fadeInUp = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.3 } },
}

type DocumentType = {
  documentId: string
  userId: string
  docType: string
  storagePath: string
  mimeType: string
  uploadedAt: string
  createdAt?: string
}

export default function SettingsPage() {
  const [activeTab, setActiveTab] = useState("personal")
  const [documentFiles, setDocumentFiles] = useState<Record<string, File[]>>({})

  // React Query hooks
  const { data: settings, isLoading, error: settingsError } = useSettings()
  const { data: existingDocuments = [], isLoading: docsLoading } = useDocuments()
  const updateSettings = useUpdateSettings()
  const uploadDocument = useUploadDocument()
  const deleteDocument = useDeleteDocument()

  const {
    control,
    register,
    handleSubmit,
    watch,
    reset,
    formState: { errors, isDirty },
  } = useForm<Partial<OnboardingFormValues>>({
    defaultValues: {},
  })

  // Load settings data when available
  useEffect(() => {
    if (settings) {
      reset(settings)
    }
  }, [settings, reset])

  const formData = watch()
  const applicantType = formData.applicantType as ApplicantType | undefined
  const documentsList = applicantType ? DOCUMENT_REQUIREMENTS[applicantType] : DOCUMENT_REQUIREMENTS["high-school"]
  const selectedDocuments = formData.documents || []

  const handleFileUpload = (documentId: string, files: FileList | null) => {
    if (!files) return
    
    const fileArray = Array.from(files)
    setDocumentFiles(prev => ({
      ...prev,
      [documentId]: [...(prev[documentId] || []), ...fileArray]
    }))
  }

  const removeFile = (documentId: string, fileIndex: number) => {
    setDocumentFiles(prev => ({
      ...prev,
      [documentId]: prev[documentId].filter((_, index) => index !== fileIndex)
    }))
  }

  const handleReviewFile = async (documentId: string) => {
    try {
      const { signedUrl } = await apiClient.getDocumentSignedUrl(documentId, 3600) // 1 hour expiry
      
      if (signedUrl) {
        window.open(signedUrl, '_blank')
      }
    } catch (error) {
      console.error("Failed to review file:", error)
      toast.error("Failed to open file")
    }
  }

  const handleRemoveExistingFile = async (documentId: string) => {
    try {
      await deleteDocument.mutateAsync(documentId)
    } catch (error) {
      // Error already handled by the hook
      console.error("Failed to remove document:", error)
    }
  }

  const onSubmit = async (data: Partial<OnboardingFormValues>) => {
    try {
      // Upload all document files first
      for (const [docType, files] of Object.entries(documentFiles)) {
        for (const file of files) {
          await uploadDocument.mutateAsync({ file, docType })
        }
      }

      // Clear the document files after successful upload
      setDocumentFiles({})
      
      // Save the settings
      await updateSettings.mutateAsync(data)
      
      // Reset form state to mark as not dirty
      reset(data)
    } catch (error) {
      // Errors already handled by the hooks
      console.error("Save error:", error)
    }
  }

  // Loading states
  if (isLoading || docsLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="space-y-4 max-w-5xl w-full mx-auto px-4">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-64 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      </div>
    )
  }

  // Error state
  if (settingsError) {
    return (
      <div className="flex h-screen items-center justify-center p-4">
        <Alert variant="destructive" className="max-w-lg">
          <AlertDescription>
            Failed to load settings. Please try refreshing the page.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  return (
    <div className="flex flex-col w-full h-full overflow-y-auto">
      <div className="max-w-5xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
          <p className="text-muted-foreground mt-2">
            Manage your profile and application preferences
          </p>
        </motion.div>

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
      >
        <form onSubmit={handleSubmit(onSubmit)}>
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="grid w-full grid-cols-4 mb-8">
              <TabsTrigger value="personal" className="flex items-center gap-2">
                <User className="h-4 w-4" />
                <span className="hidden sm:inline">Personal</span>
              </TabsTrigger>
              <TabsTrigger value="profile" className="flex items-center gap-2">
                <Briefcase className="h-4 w-4" />
                <span className="hidden sm:inline">Profile</span>
              </TabsTrigger>
              <TabsTrigger value="education" className="flex items-center gap-2">
                <GraduationCap className="h-4 w-4" />
                <span className="hidden sm:inline">Education</span>
              </TabsTrigger>
              <TabsTrigger value="documents" className="flex items-center gap-2">
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">Documents</span>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="personal">
              <Card>
                <CardHeader>
                  <CardTitle>Personal Information</CardTitle>
                  <CardDescription>
                    Your basic contact information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="firstName">First name *</Label>
                      <Input
                        id="firstName"
                        placeholder="Ayşe"
                        {...register("firstName")}
                      />
                      {errors.firstName && (
                        <p className="text-sm text-destructive">{errors.firstName.message}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="lastName">Last name *</Label>
                      <Input
                        id="lastName"
                        placeholder="Yılmaz"
                        {...register("lastName")}
                      />
                      {errors.lastName && (
                        <p className="text-sm text-destructive">{errors.lastName.message}</p>
                      )}
                    </div>
                  </motion.div>
                  <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="email">Email *</Label>
                      <Input
                        id="email"
                        type="email"
                        placeholder="ayse@example.com"
                        {...register("email")}
                      />
                      {errors.email && (
                        <p className="text-sm text-destructive">{errors.email.message}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="phone">Phone</Label>
                      <Input
                        id="phone"
                        placeholder="0505 123 45 67"
                        {...register("phone")}
                      />
                    </div>
                  </motion.div>
                  <motion.div variants={fadeInUp} className="space-y-2">
                    <Label htmlFor="currentCity">Current city</Label>
                    <Input
                      id="currentCity"
                      placeholder="Istanbul"
                      {...register("currentCity")}
                    />
                  </motion.div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="profile">
              <Card>
                <CardHeader>
                  <CardTitle>Applicant Profile</CardTitle>
                  <CardDescription>
                    Your application goals and target programs
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <motion.div variants={fadeInUp} className="space-y-2">
                    <Label>Applying from *</Label>
                    <Controller
                      name="applicantType"
                      control={control}
                      render={({ field }) => (
                        <RadioGroup
                          className="grid gap-3"
                          value={field.value}
                          onValueChange={field.onChange}
                        >
                          <Label
                            htmlFor="high-school"
                            className={cn(
                              "flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-accent",
                              field.value === "high-school" && "border-primary bg-accent"
                            )}
                          >
                            <RadioGroupItem value="high-school" id="high-school" />
                            <div className="flex-1">
                              <div className="font-medium">High School</div>
                              <div className="text-sm text-muted-foreground">
                                Currently in or graduated from lise
                              </div>
                            </div>
                          </Label>
                          <Label
                            htmlFor="university"
                            className={cn(
                              "flex cursor-pointer items-center gap-3 rounded-lg border p-4 transition-colors hover:bg-accent",
                              field.value === "university" && "border-primary bg-accent"
                            )}
                          >
                            <RadioGroupItem value="university" id="university" />
                            <div className="flex-1">
                              <div className="font-medium">University</div>
                              <div className="text-sm text-muted-foreground">
                                Current undergraduate or graduate student
                              </div>
                            </div>
                          </Label>
                        </RadioGroup>
                      )}
                    />
                  </motion.div>
                  <motion.div variants={fadeInUp} className="grid grid-cols-1 gap-4">
                    <div className="space-y-2">
                      <Label>Target countries *</Label>
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
                    </div>
                    <div className="space-y-2">
                      <Label>Fields of interest *</Label>
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
                    </div>
                    <div className="space-y-2">
                      <Label>Target programs *</Label>
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
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="preferredIntake">Preferred intake</Label>
                      <Controller
                        name="preferredIntake"
                        control={control}
                        render={({ field }) => (
                          <select
                            id="preferredIntake"
                            className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            {...field}
                          >
                            <option value="">Select intake</option>
                            {intakeOptions.map((intake) => (
                              <option key={intake} value={intake}>
                                {intake}
                              </option>
                            ))}
                          </select>
                        )}
                      />
                    </div>
                  </motion.div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="education">
              <Card>
                <CardHeader>
                  <CardTitle>Education Background</CardTitle>
                  <CardDescription>
                    Your academic history and achievements
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {applicantType === "high-school" && (
                    <motion.div variants={fadeInUp} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="highSchoolName">High school name *</Label>
                        <Input
                          id="highSchoolName"
                          placeholder="Istanbul Fen Lisesi"
                          {...register("highSchoolName")}
                        />
                      </div>
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                        <div className="space-y-2">
                          <Label htmlFor="highSchoolGPA">GPA *</Label>
                          <Input
                            id="highSchoolGPA"
                            placeholder="85"
                            {...register("highSchoolGPA")}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="highSchoolGPAScale">GPA Scale</Label>
                          <Input
                            id="highSchoolGPAScale"
                            placeholder="100"
                            {...register("highSchoolGPAScale")}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="highSchoolGradYear">Graduation year *</Label>
                          <Input
                            id="highSchoolGradYear"
                            placeholder="2024"
                            {...register("highSchoolGradYear")}
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="yksPlaced">YKS placement (if applicable)</Label>
                        <Input
                          id="yksPlaced"
                          placeholder="Boğaziçi University - Computer Engineering"
                          {...register("yksPlaced")}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="extracurriculars">Extracurriculars</Label>
                        <Textarea
                          id="extracurriculars"
                          placeholder="Clubs, sports, volunteer work..."
                          {...register("extracurriculars")}
                        />
                      </div>
                    </motion.div>
                  )}
                  {applicantType === "university" && (
                    <motion.div variants={fadeInUp} className="space-y-4">
                      <div className="space-y-2">
                        <Label htmlFor="universityName">University name *</Label>
                        <Input
                          id="universityName"
                          placeholder="Boğaziçi University"
                          {...register("universityName")}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="universityProgram">Program *</Label>
                        <Input
                          id="universityProgram"
                          placeholder="Computer Engineering"
                          {...register("universityProgram")}
                        />
                      </div>
                      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                        <div className="space-y-2">
                          <Label htmlFor="universityGPA">GPA *</Label>
                          <Input
                            id="universityGPA"
                            placeholder="3.5"
                            {...register("universityGPA")}
                          />
                        </div>
                        <div className="space-y-2">
                          <Label htmlFor="creditsCompleted">Credits completed *</Label>
                          <Input
                            id="creditsCompleted"
                            placeholder="120"
                            {...register("creditsCompleted")}
                          />
                        </div>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="expectedGraduation">Expected graduation</Label>
                        <Input
                          id="expectedGraduation"
                          placeholder="June 2025"
                          {...register("expectedGraduation")}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="researchFocus">Research focus</Label>
                        <Textarea
                          id="researchFocus"
                          placeholder="Machine learning, AI applications..."
                          {...register("researchFocus")}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="portfolioLink">Portfolio link</Label>
                        <Input
                          id="portfolioLink"
                          type="url"
                          placeholder="https://github.com/username"
                          {...register("portfolioLink")}
                        />
                      </div>
                    </motion.div>
                  )}
                  {!applicantType && (
                    <div className="text-center text-muted-foreground py-8">
                      Please select your applicant type in the Profile tab first
                    </div>
                  )}
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="documents">
              <Card>
                <CardHeader>
                  <CardTitle>Documents & Support</CardTitle>
                  <CardDescription>
                    Documents you have and support you need
                  </CardDescription>
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
                            <Label
                              key={document.id}
                              htmlFor={`doc-${document.id}`}
                              className={cn(
                                "flex cursor-pointer items-start gap-3 rounded-lg border p-4 transition-colors hover:bg-accent",
                                (field.value || []).includes(document.id) && "border-primary bg-accent"
                              )}
                            >
                              <Checkbox
                                id={`doc-${document.id}`}
                                checked={(field.value || []).includes(document.id)}
                                onCheckedChange={(checked) => {
                                  const current = field.value || []
                                  const updated = checked
                                    ? [...current, document.id]
                                    : current.filter((id) => id !== document.id)
                                  field.onChange(updated)
                                }}
                              />
                              <div className="flex-1">
                                <div className="font-medium">{document.label}</div>
                                <div className="text-sm text-muted-foreground">
                                  {document.detail}
                                </div>
                              </div>
                            </Label>
                          ))}
                        </div>
                      )}
                    />
                  </motion.div>

                  {existingDocuments.length > 0 && (
                    <motion.div variants={fadeInUp} className="space-y-4">
                      <Label>Already uploaded documents</Label>
                      <div className="space-y-2">
                        {existingDocuments.map((doc) => (
                          <div
                            key={doc.documentId}
                            className="flex items-center justify-between bg-muted/50 rounded-lg px-4 py-3"
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">
                                  {doc.docType?.charAt(0).toUpperCase() + doc.docType?.slice(1)} Document
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Uploaded {new Date(doc.createdAt || doc.uploadedAt).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => handleReviewFile(doc.documentId)}
                              >
                                <Eye className="h-4 w-4 mr-1" />
                                Review
                              </Button>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => handleRemoveExistingFile(doc.documentId)}
                              >
                                <Trash2 className="h-4 w-4 mr-1" />
                                Remove
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </motion.div>
                  )}

                  {selectedDocuments.length > 0 && (
                    <motion.div variants={fadeInUp} className="space-y-4">
                      <Label>Upload required documents</Label>
                      <div className="space-y-3">
                        {selectedDocuments.map((docId) => {
                          const document = documentsList.find(d => d.id === docId)
                          if (!document) return null
                          const files = documentFiles[docId] || []

                          return (
                            <div key={docId} className="rounded-lg border p-4 space-y-3">
                              <div className="flex items-center justify-between">
                                <div className="flex-1">
                                  <p className="font-medium text-sm">{document.label}</p>
                                  <p className="text-xs text-muted-foreground">{document.detail}</p>
                                </div>
                                <label htmlFor={`file-${docId}`} className="cursor-pointer">
                                  <div className="flex items-center gap-2 px-3 py-2 text-sm border rounded-md hover:bg-accent transition-colors">
                                    <Upload className="h-4 w-4" />
                                    <span>Upload</span>
                                  </div>
                                  <input
                                    id={`file-${docId}`}
                                    type="file"
                                    multiple
                                    className="hidden"
                                    onChange={(e) => handleFileUpload(docId, e.target.files)}
                                    accept=".pdf,.doc,.docx,.jpg,.jpeg,.png"
                                  />
                                </label>
                              </div>
                              
                              {files.length > 0 && (
                                <div className="space-y-2 mt-2">
                                  {files.map((file, index) => (
                                    <div
                                      key={`${file.name}-${index}`}
                                      className="flex items-center justify-between bg-muted/50 rounded px-3 py-2 text-sm"
                                    >
                                      <div className="flex items-center gap-2 flex-1 min-w-0">
                                        <FileText className="h-4 w-4 shrink-0" />
                                        <span className="truncate">{file.name}</span>
                                        <span className="text-xs text-muted-foreground shrink-0">
                                          ({(file.size / 1024).toFixed(1)} KB)
                                        </span>
                                      </div>
                                      <button
                                        type="button"
                                        onClick={() => removeFile(docId, index)}
                                        className="ml-2 p-1 hover:bg-destructive/10 rounded"
                                      >
                                        <X className="h-4 w-4 text-destructive" />
                                      </button>
                                    </div>
                                  ))}
                                </div>
                              )}
                              
                              {files.length === 0 && (
                                <p className="text-xs text-destructive">
                                  * Please upload at least one file for this document
                                </p>
                              )}
                            </div>
                          )
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

                  <motion.div variants={fadeInUp} className="space-y-2">
                    <Label htmlFor="additionalNotes">Additional notes</Label>
                    <Textarea
                      id="additionalNotes"
                      placeholder="Any other information you'd like to share..."
                      {...register("additionalNotes")}
                    />
                  </motion.div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>

          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
            className="mt-6 flex justify-end"
          >
            <Button 
              type="submit" 
              disabled={!isDirty || updateSettings.isPending || uploadDocument.isPending} 
              size="lg"
            >
              {(updateSettings.isPending || uploadDocument.isPending) ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </>
              )}
            </Button>
          </motion.div>
        </form>
      </motion.div>
      </div>
    </div>
  )
}
