"use client";
import "./globals.css";
import { Inter } from "next/font/google";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: { queries: { staleTime: 30_000 } },
      })
  );

  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen bg-gray-50 font-sans antialiased">
        <QueryClientProvider client={queryClient}>
          <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
            <div className="max-w-5xl mx-auto px-4 h-14 flex items-center justify-between">
              <a href="/" className="font-bold text-lg text-lego-red">
                Lego Set Matcher
              </a>
              <nav className="flex items-center gap-4 text-sm text-gray-500">
                <a
                  href="https://github.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:text-gray-700 transition-colors"
                >
                  GitHub
                </a>
              </nav>
            </div>
          </header>
          <main className="max-w-5xl mx-auto px-4 py-8">{children}</main>
        </QueryClientProvider>
      </body>
    </html>
  );
}
