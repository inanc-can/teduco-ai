"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { supabase } from "@/lib/supabase";
import OnboardingForm from "@/components/onboarding-form";

export default function OnboardingPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function checkAuth() {
      try {
        const { data: { user } } = await supabase.auth.getUser();
        
        if (!user) {
          router.push('/login');
          return;
        }

        // Check if already completed onboarding
        const { data: profile } = await supabase
          .from('users')
          .select('onboarding_completed')
          .eq('user_id', user.id)
          .single();

        if (profile?.onboarding_completed) {
          router.push('/dashboard');
          return;
        }

        setIsLoading(false);
      } catch (error) {
        console.error('Error checking auth:', error);
        router.push('/login');
      }
    }

    checkAuth();
  }, [router]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

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
          <OnboardingForm onComplete={() => {
            router.push("/dashboard")
            router.refresh()
          }} />
        </div>
      </div>
    </div>
  );
}
