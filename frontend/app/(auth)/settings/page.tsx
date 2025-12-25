"use client"

import { useState, useEffect } from "react"
import { useForm, Controller } from "react-hook-form"
import { motion } from "framer-motion"
import { Loader2, Save, User, Briefcase, GraduationCap, FileText, Upload, X, Eye, Trash2 } from "lucide-react"
import { toast } from "sonner"

import { cn } from "@/lib/utils"
import { supabase, getCachedSession } from "@/lib/supabase"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { RadioGroup, RadioGroupItem } from "@/components/ui/radio-group"
import { Checkbox } from "@/components/ui/checkbox"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import Multiselect, { type Option } from "@/components/ui/multiselect"
import type { OnboardingFormValues } from "@/lib/schemas/onboarding"

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
  document_id: string
  user_id: string
  doc_type: string
  storage_path: string
  mime_type: string
  uploaded_at: string
}

export default function SettingsPage() {
  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [activeTab, setActiveTab] = useState("personal")
  const [documentFiles, setDocumentFiles] = useState<Record<string, File[]>>({})
  const [existingDocuments, setExistingDocuments] = useState<DocumentType[]>([])

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

  const handleReviewFile = async (storagePath: string) => {
    try {
      const { data, error } = await supabase.storage
        .from('user-documents')
        .createSignedUrl(storagePath, 60 * 60) // 1 hour expiry
      
      if (error) throw error
      
      if (data?.signedUrl) {
        window.open(data.signedUrl, '_blank')
      }
    } catch (error) {
      console.error("Failed to review file:", error)
      toast.error("Failed to open file")
    }
  }

  const handleRemoveExistingFile = async (documentId: string) => {
    try {
      const session = await getCachedSession()
      
      if (!session) {
        toast.error("You must be logged in")
        return
      }

      const res = await fetch(`http://localhost:8000/documents/${documentId}`, {
        method: "DELETE",
        headers: {
          "Authorization": `Bearer ${session.access_token}`,
        },
      })
      
      if (res.ok) {
        setExistingDocuments(prev => prev.filter(doc => doc.document_id !== documentId))
        toast.success("Document removed successfully")
      } else {
        const error = await res.json().catch(() => ({ error: "Unknown error" }))
        toast.error(error.error || "Failed to remove document")
      }
    } catch (error) {
      console.error("Failed to remove document:", error)
      toast.error("Failed to remove document")
    }
  }

  // Load user data and documents on mount
  useEffect(() => {
    const loadSettings = async () => {
      try {
        const session = await getCachedSession()
        
        if (!session) {
          toast.error("You must be logged in")
          return
        }

        // Parallel fetching for better performance
        const [settingsRes, docsRes] = await Promise.all([
          fetch("/api/settings", {
            headers: {
              "Authorization": `Bearer ${session.access_token}`,
            },
          }),
          fetch("http://localhost:8000/documents", {
            headers: {
              "Authorization": `Bearer ${session.access_token}`,
            },
          })
        ])
        
        if (settingsRes.ok) {
          const data = await settingsRes.json()
          reset(data)
        } else {
          const error = await settingsRes.json().catch(() => ({ error: "Unknown error" }))
          console.error("Failed to load settings:", error)
          toast.error(error.error || "Failed to load your settings")
        }
        
        if (docsRes.ok) {
          const docs = await docsRes.json()
          setExistingDocuments(docs)
        } else {
          console.error("Failed to load documents")
        }
      } catch (error) {
        console.error("Failed to load settings:", error)
        toast.error("Failed to load your settings")
      } finally {
        setIsLoading(false)
      }
    }

    loadSettings()
  }, [reset])

  const onSubmit = async (data: Partial<OnboardingFormValues>) => {
    // Validate that all selected documents have files
    const selectedDocs = data.documents || []
    const missingFiles = selectedDocs.filter(docId => !documentFiles[docId] || documentFiles[docId].length === 0)
    
    if (missingFiles.length > 0) {
      const missingNames = missingFiles
        .map(docId => documentsList.find(d => d.id === docId)?.label)
        .filter(Boolean)
        .join(", ")
      toast.error(`Please upload files for: ${missingNames}`)
      return
    }

    setIsSaving(true)
    try {
      const session = await getCachedSession()
      
      if (!session) {
        toast.error("You must be logged in")
        return
      }

      // Upload all document files to the backend
      for (const [docType, files] of Object.entries(documentFiles)) {
        for (const file of files) {
          const formData = new FormData()
          formData.append('file', file)
          formData.append('doc_type', docType)
          
          const uploadRes = await fetch("http://localhost:8000/documents", {
            method: "POST",
            headers: {
              "Authorization": `Bearer ${session.access_token}`,
            },
            body: formData,
          })
          
          if (!uploadRes.ok) {
            const errorText = await uploadRes.text()
            console.error("Upload error response:", uploadRes.status, errorText)
            let errorMessage = "Upload failed"
            try {
              const errorJson = JSON.parse(errorText)
              errorMessage = errorJson.detail || errorJson.error || errorJson.message || errorText
            } catch {
              errorMessage = errorText || `HTTP ${uploadRes.status}`
            }
            throw new Error(`Failed to upload ${file.name}: ${errorMessage}`)
          }
          
          console.log(`Successfully uploaded: ${file.name}`)
        }
      }

      // Clear the document files after successful upload
      setDocumentFiles({})
      
      // Reload documents to show the newly uploaded ones
      const docsRes = await fetch("http://localhost:8000/documents", {
        headers: {
          "Authorization": `Bearer ${session.access_token}`,
        },
      })
      
      if (docsRes.ok) {
        const docs = await docsRes.json()
        setExistingDocuments(docs)
      }

      // Save the settings (without file data, just document type selections)
      const res = await fetch("/api/settings", {
        method: "PUT",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${session.access_token}`,
        },
        body: JSON.stringify(data),
      })

      if (!res.ok) {
        console.error("Response status:", res.status, res.statusText)
        const responseText = await res.text()
        console.error("Response body:", responseText)
        
        let errorData
        try {
          errorData = JSON.parse(responseText)
        } catch {
          errorData = { error: responseText || "Unknown error" }
        }
        
        console.error("Settings save error:", errorData)
        if (errorData.details) {
          console.error("Validation details:", errorData.details)
        }
        throw new Error(errorData.error || "Failed to save settings")
      }

      toast.success("Settings saved successfully!")
      reset(data) // Reset form state to mark as not dirty
    } catch (error) {
      console.error("Save error:", error)
      toast.error(error instanceof Error ? error.message : "Failed to save settings")
    } finally {
      setIsSaving(false)
    }
  }

  if (isLoading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
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
                            key={doc.document_id}
                            className="flex items-center justify-between bg-muted/50 rounded-lg px-4 py-3"
                          >
                            <div className="flex items-center gap-3 flex-1 min-w-0">
                              <FileText className="h-5 w-5 shrink-0 text-muted-foreground" />
                              <div className="flex-1 min-w-0">
                                <p className="font-medium text-sm truncate">
                                  {doc.doc_type.charAt(0).toUpperCase() + doc.doc_type.slice(1)} Document
                                </p>
                                <p className="text-xs text-muted-foreground">
                                  Uploaded {new Date(doc.uploaded_at).toLocaleDateString()}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center gap-2">
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => handleReviewFile(doc.storage_path)}
                              >
                                <Eye className="h-4 w-4 mr-1" />
                                Review
                              </Button>
                              <Button
                                type="button"
                                variant="outline"
                                size="sm"
                                onClick={() => handleRemoveExistingFile(doc.document_id)}
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
            <Button type="submit" disabled={!isDirty || isSaving} size="lg">
              {isSaving ? (
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
