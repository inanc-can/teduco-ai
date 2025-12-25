import { SignupForm } from "@/components/signup-form"

export default function SignupPage() {
  return (
    <div className="space-y-6">
      <div className="space-y-2 text-center">
        <h1 className="text-3xl font-bold">Create an Account</h1>
        <p className="text-muted-foreground">
          Start your journey with Teduco
        </p>
      </div>
      <SignupForm />
    </div>
  )
}
