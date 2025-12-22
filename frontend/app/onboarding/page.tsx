"use client";

import { useRouter } from "next/navigation";

import OnboardingForm from "@/components/onboarding-form";

export default function OnboardingPage() {
  const router = useRouter();

  return (
    <div className="min-h-screen bg-muted/40 py-10 px-4">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-8 lg:flex-row">
        <div className="w-full lg:w-2/5">
          <div className="rounded-3xl border bg-background/70 p-8 shadow-sm backdrop-blur">
            <p className="text-sm font-medium text-primary">Teduco Onboarding</p>
            <h1 className="mt-4 text-3xl font-bold tracking-tight">Let&apos;s personalize your guidance</h1>
            <p className="mt-3 text-sm text-muted-foreground">
              Share a few details about your academic path so we can tailor AI prompts,
              timelines, and counselor support for Turkish students heading abroad.
            </p>
            <div className="mt-6 space-y-3 text-sm">
              <p className="font-semibold text-foreground">Here&apos;s what happens next:</p>
              <ul className="list-disc space-y-1 pl-5 text-muted-foreground">
                <li>Complete this quick form with your goals and documents.</li>
                <li>Get matched with the right universities, scholarships, and advisors.</li>
                <li>Access your dashboard to chat with Teduco AI and track progress.</li>
              </ul>
            </div>
          </div>
        </div>
        <div className="w-full lg:w-3/5">
          <OnboardingForm onComplete={() => router.push("/auth/dashboard")} />
        </div>
      </div>
    </div>
  );
}
