import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import ThemeProviderWrapper from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: {
    template: '%s | Teduco',
    default: 'Teduco - AI Study Abroad Assistant',
  },
  description: 'Navigate the complexities of international education with AI-powered guidance tailored for Turkish students',
  keywords: ['study abroad', 'university application', 'AI assistant', 'international education', 'Turkey', 'university counseling'],
  authors: [{ name: 'Teduco' }],
  openGraph: {
    type: 'website',
    locale: 'en_US',
    url: 'https://teduco.com',
    title: 'Teduco - AI Study Abroad Assistant',
    description: 'Navigate the complexities of international education with AI-powered guidance',
    siteName: 'Teduco',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <ThemeProviderWrapper>
          {children}
          <Toaster />
        </ThemeProviderWrapper>
      </body>
    </html>
  );
}
