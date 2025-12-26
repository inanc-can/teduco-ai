"use client"

import { useState } from "react"
import { CheckCircle2, Circle, Clock, GraduationCap, MapPin, Calendar, ChevronDown, ChevronUp } from "lucide-react"

import { cn } from "@/lib/utils"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

type ApplicationStatus = "not_started" | "in_progress" | "submitted" | "under_review" | "accepted" | "rejected"

type ApplicationStep = {
  id: string
  name: string
  status: "completed" | "current" | "pending"
  dueDate?: string
}

type Application = {
  id: string
  university: string
  country: string
  degree: string
  program: string
  status: ApplicationStatus
  progress: number
  deadline: string
  steps: ApplicationStep[]
}

// Mock data for applications
const MOCK_APPLICATIONS: Application[] = [
  {
    id: "1",
    university: "Technical University of Munich (TUM)",
    country: "Germany",
    degree: "Master's",
    program: "Computer Science",
    status: "in_progress",
    progress: 60,
    deadline: "2025-01-15",
    steps: [
      { id: "1-1", name: "Create account on TUMonline", status: "completed" },
      { id: "1-2", name: "Upload transcripts", status: "completed" },
      { id: "1-3", name: "Submit statement of purpose", status: "completed" },
      { id: "1-4", name: "Request recommendation letters", status: "current", dueDate: "2024-12-15" },
      { id: "1-5", name: "Submit English proficiency test", status: "pending", dueDate: "2024-12-20" },
      { id: "1-6", name: "Pay application fee", status: "pending", dueDate: "2025-01-10" },
      { id: "1-7", name: "Final submission", status: "pending", dueDate: "2025-01-15" },
    ],
  },
  {
    id: "2",
    university: "ETH Zurich",
    country: "Switzerland",
    degree: "Master's",
    program: "Data Science",
    status: "submitted",
    progress: 100,
    deadline: "2024-12-15",
    steps: [
      { id: "2-1", name: "Online application form", status: "completed" },
      { id: "2-2", name: "Upload academic documents", status: "completed" },
      { id: "2-3", name: "Submit motivation letter", status: "completed" },
      { id: "2-4", name: "Submit GRE scores", status: "completed" },
      { id: "2-5", name: "Pay application fee", status: "completed" },
      { id: "2-6", name: "Final submission", status: "completed" },
    ],
  },
  {
    id: "3",
    university: "University of Amsterdam",
    country: "Netherlands",
    degree: "Master's",
    program: "Artificial Intelligence",
    status: "under_review",
    progress: 100,
    deadline: "2024-11-30",
    steps: [
      { id: "3-1", name: "Submit application", status: "completed" },
      { id: "3-2", name: "Document verification", status: "completed" },
      { id: "3-3", name: "Academic review", status: "current" },
      { id: "3-4", name: "Final decision", status: "pending" },
    ],
  },
  {
    id: "4",
    university: "KTH Royal Institute of Technology",
    country: "Sweden",
    degree: "Master's",
    program: "Machine Learning",
    status: "not_started",
    progress: 0,
    deadline: "2025-01-15",
    steps: [
      { id: "4-1", name: "Create University Admissions account", status: "pending", dueDate: "2024-12-01" },
      { id: "4-2", name: "Upload transcripts", status: "pending", dueDate: "2024-12-15" },
      { id: "4-3", name: "Submit CV", status: "pending", dueDate: "2024-12-20" },
      { id: "4-4", name: "Submit motivation letter", status: "pending", dueDate: "2025-01-01" },
      { id: "4-5", name: "Submit recommendation letters", status: "pending", dueDate: "2025-01-10" },
      { id: "4-6", name: "Pay application fee", status: "pending", dueDate: "2025-01-15" },
    ],
  },
  {
    id: "5",
    university: "Delft University of Technology",
    country: "Netherlands",
    degree: "Master's",
    program: "Computer Engineering",
    status: "accepted",
    progress: 100,
    deadline: "2024-10-15",
    steps: [
      { id: "5-1", name: "Application submitted", status: "completed" },
      { id: "5-2", name: "Documents verified", status: "completed" },
      { id: "5-3", name: "Interview completed", status: "completed" },
      { id: "5-4", name: "Offer received", status: "completed" },
    ],
  },
]

const STATUS_CONFIG: Record<ApplicationStatus, { label: string; variant: "default" | "secondary" | "destructive" | "outline"; className?: string }> = {
  not_started: { label: "Not Started", variant: "outline" },
  in_progress: { label: "In Progress", variant: "default", className: "bg-blue-500 hover:bg-blue-600" },
  submitted: { label: "Submitted", variant: "default", className: "bg-purple-500 hover:bg-purple-600" },
  under_review: { label: "Under Review", variant: "default", className: "bg-amber-500 hover:bg-amber-600" },
  accepted: { label: "Accepted", variant: "default", className: "bg-green-500 hover:bg-green-600" },
  rejected: { label: "Rejected", variant: "destructive" },
}

function StepIcon({ status }: { status: ApplicationStep["status"] }) {
  switch (status) {
    case "completed":
      return <CheckCircle2 className="h-5 w-5 text-green-500" />
    case "current":
      return <Clock className="h-5 w-5 text-blue-500 animate-pulse" />
    case "pending":
      return <Circle className="h-5 w-5 text-muted-foreground" />
  }
}

function ApplicationCard({ application }: { application: Application }) {
  const [isExpanded, setIsExpanded] = useState(false)
  const statusConfig = STATUS_CONFIG[application.status]
  
  const stepsLeft = application.steps.filter(step => step.status !== "completed").length
  const currentStep = application.steps.find(step => step.status === "current")

  return (
    <Card className="overflow-hidden">
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-1">
            <CardTitle className="text-lg flex items-center gap-2">
              <GraduationCap className="h-5 w-5 text-primary" />
              {application.university}
            </CardTitle>
            <CardDescription className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {application.country}
              </span>
              <span>{application.degree} in {application.program}</span>
            </CardDescription>
          </div>
          <Badge variant={statusConfig.variant} className={statusConfig.className}>
            {statusConfig.label}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress bar */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Application Progress</span>
            <span className="font-medium">{application.progress}%</span>
          </div>
          <Progress value={application.progress} className="h-2" />
        </div>

        {/* Quick info */}
        <div className="flex flex-wrap gap-4 text-sm">
          <div className="flex items-center gap-1.5 text-muted-foreground">
            <Calendar className="h-4 w-4" />
            <span>Deadline: <span className="text-foreground font-medium">{new Date(application.deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</span></span>
          </div>
          {stepsLeft > 0 && (
            <div className="text-muted-foreground">
              <span className="text-foreground font-medium">{stepsLeft}</span> step{stepsLeft !== 1 ? 's' : ''} remaining
            </div>
          )}
        </div>

        {/* Current step highlight */}
        {currentStep && (
          <div className="rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900 p-3">
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="font-medium text-blue-700 dark:text-blue-400">Current Step:</span>
              <span className="text-blue-600 dark:text-blue-300">{currentStep.name}</span>
              {currentStep.dueDate && (
                <span className="ml-auto text-blue-500 text-xs">Due: {new Date(currentStep.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>
              )}
            </div>
          </div>
        )}

        {/* Expandable steps list */}
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          {isExpanded ? "Hide all steps" : "Show all steps"}
        </button>

        {isExpanded && (
          <div className="space-y-2 pt-2 border-t">
            {application.steps.map((step) => (
              <div
                key={step.id}
                className={cn(
                  "flex items-center gap-3 py-2 px-3 rounded-lg text-sm",
                  step.status === "current" && "bg-blue-50 dark:bg-blue-950/30",
                  step.status === "completed" && "text-muted-foreground"
                )}
              >
                <StepIcon status={step.status} />
                <span className={cn(
                  "flex-1",
                  step.status === "completed" && "line-through"
                )}>
                  {step.name}
                </span>
                {step.dueDate && step.status !== "completed" && (
                  <span className="text-xs text-muted-foreground">
                    {new Date(step.dueDate).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  )
}

export default function ProgressTrackingPage() {
  const [filter, setFilter] = useState<ApplicationStatus | "all">("all")

  const filteredApplications = filter === "all" 
    ? MOCK_APPLICATIONS 
    : MOCK_APPLICATIONS.filter(app => app.status === filter)

  const stats = {
    total: MOCK_APPLICATIONS.length,
    inProgress: MOCK_APPLICATIONS.filter(a => a.status === "in_progress").length,
    submitted: MOCK_APPLICATIONS.filter(a => a.status === "submitted" || a.status === "under_review").length,
    accepted: MOCK_APPLICATIONS.filter(a => a.status === "accepted").length,
  }

  return (
    <div className="flex-1 overflow-auto">
      <div className="container max-w-4xl mx-auto py-8 px-4 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Application Tracker</h1>
          <p className="text-muted-foreground mt-1">
            Track your university applications and stay on top of deadlines
          </p>
        </div>

        {/* Stats Overview */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="py-4">
            <CardContent className="p-0 px-4 text-center">
              <div className="text-2xl font-bold">{stats.total}</div>
              <div className="text-xs text-muted-foreground">Total Applications</div>
            </CardContent>
          </Card>
          <Card className="py-4">
            <CardContent className="p-0 px-4 text-center">
              <div className="text-2xl font-bold text-blue-500">{stats.inProgress}</div>
              <div className="text-xs text-muted-foreground">In Progress</div>
            </CardContent>
          </Card>
          <Card className="py-4">
            <CardContent className="p-0 px-4 text-center">
              <div className="text-2xl font-bold text-purple-500">{stats.submitted}</div>
              <div className="text-xs text-muted-foreground">Submitted</div>
            </CardContent>
          </Card>
          <Card className="py-4">
            <CardContent className="p-0 px-4 text-center">
              <div className="text-2xl font-bold text-green-500">{stats.accepted}</div>
              <div className="text-xs text-muted-foreground">Accepted</div>
            </CardContent>
          </Card>
        </div>

        {/* Filter */}
        <div className="flex flex-wrap gap-2">
          {(["all", "not_started", "in_progress", "submitted", "under_review", "accepted"] as const).map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={cn(
                "px-3 py-1.5 rounded-full text-sm font-medium transition-colors",
                filter === status
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:text-foreground"
              )}
            >
              {status === "all" ? "All" : STATUS_CONFIG[status].label}
            </button>
          ))}
        </div>

        {/* Applications List */}
        <div className="space-y-4">
          {filteredApplications.length === 0 ? (
            <Card className="py-12">
              <CardContent className="text-center text-muted-foreground">
                No applications found with this filter.
              </CardContent>
            </Card>
          ) : (
            filteredApplications.map((application) => (
              <ApplicationCard key={application.id} application={application} />
            ))
          )}
        </div>
      </div>
    </div>
  )
}
