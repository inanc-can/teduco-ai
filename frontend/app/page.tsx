import Link from "next/link"
import {
  ArrowRight,
  Calendar,
  CheckCircle2,
  ChevronDown,
  FileText,
  Globe,
  GraduationCap,
  MessageSquare,
  Shield,
  Sparkles,
  Target,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"

const FEATURES = [
  {
    icon: MessageSquare,
    title: "AI-Powered Q&A",
    description: "Get instant answers about universities, programs, requirements, and scholarships from our intelligent chatbot.",
  },
  {
    icon: Shield,
    title: "Verified Information",
    description: "All answers are sourced from official university databases and verified for accuracy.",
  },
  {
    icon: Target,
    title: "Smart Matching",
    description: "Receive personalized university recommendations based on your profile, interests, and budget.",
  },
  {
    icon: FileText,
    title: "Document Review",
    description: "AI-powered feedback on your Statement of Purpose, CV, and application materials.",
  },
  {
    icon: Calendar,
    title: "Application Tracker",
    description: "Manage all your applications, deadlines, and requirements in one organized dashboard.",
  },
  {
    icon: Globe,
    title: "Multi-Language Support",
    description: "Get guidance in Turkish and English for a seamless experience.",
  },
]

const FAQ = [
  {
    q: "How does Teduco use AI to help with applications?",
    a: "Teduco uses AI to provide instant answers, personalized university matches, and feedback on application documents by synthesizing verified university data and best-practice guidance.",
  },
  {
    q: "Is Teduco free to use?",
    a: "You can get started for free. Some premium features such as in-depth document review or personalized coaching may require a paid plan.",
  },
  {
    q: "Which countries and languages are supported?",
    a: "We currently support guidance for a wide range of international universities and provide help in English and Turkish. More languages and regions will be added over time.",
  },
  {
    q: "How accurate is the information provided?",
    a: "Answers are sourced from official university databases and verified resources, but we still recommend double-checking official university pages for final confirmation.",
  },
  {
    q: "Can Teduco review my Statement of Purpose or CV?",
    a: "Yes — our AI provides feedback and suggestions to improve clarity, structure, and impact. Human expert review is available as a premium service.",
  },
]

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-50 dark:bg-zinc-950">
      <nav className="fixed inset-x-0 top-0 z-50 border-b border-zinc-200/70 bg-white/80 backdrop-blur dark:border-zinc-800/60 dark:bg-zinc-950/80">
        <div className="container max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-linear-to-br from-blue-500 to-purple-600 flex items-center justify-center">
              <GraduationCap className="w-5 h-5 text-white" />
            </div>
            <span className="font-bold text-xl">Teduco</span>
          </Link>
          
          <div className="hidden md:flex items-center gap-6">
            <a href="#features" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Features</a>
            <a href="#journey" className="text-sm text-muted-foreground hover:text-foreground transition-colors">How It Works</a>
            <a href="#stats" className="text-sm text-muted-foreground hover:text-foreground transition-colors">About</a>
          </div>
          
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link href="/login">Sign In</Link>
            </Button>
            <Button size="sm" asChild>
              <Link href="/signup">
                Get Started <ArrowRight className="w-4 h-4" />
              </Link>
            </Button>
          </div>
        </div>
      </nav>
      
      <section className="relative overflow-hidden px-4 pt-32 pb-20">
        <div className="absolute inset-0 bg-linear-to-b from-blue-50 to-transparent dark:from-blue-950/30" />
        <div className="absolute top-20 left-1/4 w-72 h-72 bg-blue-400/20 rounded-full blur-3xl" />
        <div className="absolute top-40 right-1/4 w-96 h-96 bg-purple-400/20 rounded-full blur-3xl" />
        <div className="container relative mx-auto max-w-6xl">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-sm font-medium mb-6">
              <Sparkles className="w-4 h-4" />
              AI-Powered Education Consulting
            </div>
            <h1 className="text-4xl md:text-6xl font-bold tracking-tight mb-6 bg-linear-to-r from-zinc-900 via-zinc-700 to-zinc-900 dark:from-white dark:via-zinc-200 bg-clip-text text-transparent">
              Your Dream University is Just a Conversation Away
            </h1>
            <p className="text-lg md:text-xl text-muted-foreground mb-8 leading-relaxed">
              Navigate the complexities of international education with Teduco — your AI companion for university discovery, application guidance, and personalized planning.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button size="lg" className="w-full sm:w-auto text-base px-8" asChild>
                <Link href="/signup">
                  Start Your Journey <ArrowRight className="w-5 h-5" />
                </Link>
              </Button>
              <Button size="lg" variant="outline" className="w-full sm:w-auto text-base px-8" asChild>
                <a href="#journey">
                  See How It Works <ChevronDown className="w-5 h-5" />
                </a>
              </Button>
            </div>
          </div>
        </div>
      </section>

      
      <section id="features" className="py-24 px-4">
        <div className="container mx-auto max-w-6xl">
          <div className="mx-auto mb-16 max-w-2xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">
              Everything You Need for Your Study Abroad Journey
            </h2>
            <p className="text-muted-foreground text-lg">
              From initial research to final acceptance — Teduco guides you every step of the way.
            </p>
          </div>

          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((feature) => (
              <Card key={feature.title} className="h-full border-zinc-200/80 shadow-sm transition hover:-translate-y-1 hover:shadow-lg dark:border-zinc-800">
                <CardContent className="p-6">
                  <div className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl bg-linear-to-r from-blue-500 to-purple-600 text-white">
                    <feature.icon className="h-6 w-6" />
                  </div>
                  <h3 className="text-lg font-semibold mb-2">{feature.title}</h3>
                  <p className="text-sm text-muted-foreground leading-relaxed">
                    {feature.description}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      <section className="relative overflow-hidden py-24 px-4">
        <div className="absolute inset-0 bg-linear-to-br from-blue-600 to-purple-700" />
        <div className="absolute inset-0 bg-[url('/grid.svg')] opacity-10" />

        <div className="container relative mx-auto max-w-4xl text-center text-white">
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 text-white text-sm font-medium mb-6">
              <CheckCircle2 className="w-4 h-4" />
              Free to get started
            </div>
            <h2 className="text-3xl md:text-5xl font-bold text-white mb-6">
              Ready to Start Your Journey?
            </h2>
            <p className="text-xl text-white/80 mb-8 max-w-2xl mx-auto">
              Join thousands of students who have found their dream university with Teduco. Your AI education consultant is ready to help.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <Button 
                size="lg" 
                className="w-full sm:w-auto text-base px-8 bg-white text-blue-600 hover:bg-zinc-100"
                asChild
              >
                <Link href="/signup">
                  Launch Teduco <ArrowRight className="w-5 h-5" />
                </Link>
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="w-full sm:w-auto text-base px-8 border-white/30 text-white hover:bg-white/10"
                asChild
              >
                <Link href="/login">
                  Sign In
                </Link>
              </Button>
            </div>
        </div>
      </section>

      <section id="faq" className="py-20 px-4 bg-zinc-50 dark:bg-zinc-950">
        <div className="container mx-auto max-w-6xl">
          <div className="mx-auto mb-12 max-w-2xl text-center">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Frequently Asked Questions</h2>
            <p className="text-muted-foreground">Answers to common questions about Teduco and our services.</p>
          </div>

          <div className="grid gap-4 md:grid-cols-2">
            {FAQ.map((item) => (
              <details
                key={item.q}
                className="group bg-white dark:bg-zinc-900 p-6 rounded-lg border border-zinc-200 dark:border-zinc-800"
              >
                <summary className="cursor-pointer select-none text-lg font-medium flex items-center justify-between">
                  {item.q}
                  <ChevronDown className="w-5 h-5 ml-4 text-muted-foreground group-open:rotate-180 transition-transform" />
                </summary>
                <div className="mt-4 text-sm text-muted-foreground">{item.a}</div>
              </details>
            ))}
          </div>
        </div>
      </section>

      <footer className="border-t border-zinc-200 bg-white py-12 px-4 dark:border-zinc-800 dark:bg-zinc-950">
        <div className="container mx-auto max-w-6xl">
          <div className="flex flex-col items-center justify-between gap-6 md:flex-row">
            <div className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-linear-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <GraduationCap className="w-5 h-5 text-white" />
              </div>
              <span className="font-bold text-xl">Teduco</span>
            </div>
            <p className="text-sm text-muted-foreground">
              © 2025 Teduco. Making international education accessible for everyone.
            </p>
            <div className="flex items-center gap-4">
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacy</a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Terms</a>
              <a href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Contact</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
