import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Kisan Mitra AI",
  description: "Enterprise-grade multi-agent agricultural advisory platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.JSX.Element | React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className="h-full antialiased dark"
    >
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
