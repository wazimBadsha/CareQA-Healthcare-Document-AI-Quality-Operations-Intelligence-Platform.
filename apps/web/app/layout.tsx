import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CareQA · Quality Operations Intelligence",
  description: "Synthetic document-AI quality evaluation dashboard"
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}


