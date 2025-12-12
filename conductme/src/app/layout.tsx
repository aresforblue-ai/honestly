import type { Metadata } from "next";
// import { Inter } from "next/font/google"; // Temporarily disabled for build in offline environment
import "./globals.css";

// const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "ConductMe - AI Orchestration",
  description: "Orchestrate your AI ensemble with cryptographic proof of humanity",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <body className="font-sans antialiased">
        {children}
      </body>
    </html>
  );
}
