import type { Metadata } from "next";
import "./globals.css";
import { Header } from "@/components/layout/Header";

export const metadata: Metadata = {
  title: "Financial Expert Assistant",
  description: "RAG Chatbox for Financial Reports",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body
        className="font-sans antialiased min-h-screen flex flex-col"
      >
        <Header />
        <main className="flex-1 overflow-hidden">{children}</main>

      </body>
    </html>
  );
}
