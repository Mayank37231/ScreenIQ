import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "ScreenIQ",
  description: "AI-assisted applicant screening for HR teams"
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <header className="topbar">
          <Link className="brand" href="/screen">ScreenIQ</Link>
          <nav>
            <Link href="/screen">Screen</Link>
            <Link href="/dashboard">Dashboard</Link>
          </nav>
        </header>
        {children}
      </body>
    </html>
  );
}
