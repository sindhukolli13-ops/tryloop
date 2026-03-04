import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Tryloop — Try before you buy",
  description:
    "Rent electronics on short-term trials. Try before you buy, reduce e-waste.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="nl">
      <body>{children}</body>
    </html>
  );
}
