import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Fish Speech · 聊天式语音体验",
  description: "像聊天一样体验 Fish Speech 免费语音合成，自填密钥，默认可莉音色。",
  icons: {
    icon: "/favicon.svg",
    shortcut: "/favicon.svg",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="antialiased">{children}</body>
    </html>
  );
}
