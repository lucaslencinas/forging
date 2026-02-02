import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Forging - AI-Powered Game Coaching",
  description:
    "Upload your gameplay video and get personalized, timestamped coaching tips. Improve faster with AI analysis for Age of Empires II, Counter-Strike 2, and more.",
  openGraph: {
    title: "Forging - AI-Powered Game Coaching",
    description:
      "Upload your gameplay video and get personalized, timestamped coaching tips in minutes.",
    type: "website",
    siteName: "Forging",
  },
  twitter: {
    card: "summary_large_image",
    title: "Forging - AI-Powered Game Coaching",
    description:
      "Upload your gameplay video and get personalized, timestamped coaching tips in minutes.",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="bg-zinc-950">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-zinc-950`}
      >
        {children}
      </body>
    </html>
  );
}
