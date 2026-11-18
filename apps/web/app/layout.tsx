import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata = { title: "CareQA — AI Quality Intelligence", description: "Synthetic healthcare document AI quality and operations intelligence." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
