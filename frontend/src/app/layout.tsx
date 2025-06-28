import type { Metadata, Viewport } from 'next'
import { Inter, Poppins } from 'next/font/google'
import clsx from 'clsx'

import '@/styles/globals.css' // Assuming this will contain Tailwind directives and brand styles
// import { ThemeProvider } from '@/context/ThemeContext' // Placeholder for future ThemeProvider
import { Toaster } from '@/components/ui/sonner'; // Assuming sonner is set up in ui components
import Coach from '../components/Coach'; // Persistent AI coach component

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-inter',
  display: 'swap',
  weight: ['400', '500', '600', '700'],
  style: ['normal'],
})

const poppins = Poppins({
  subsets: ['latin'],
  variable: '--font-poppins',
  display: 'swap',
  weight: ['400', '500', '600', '700', '800'],
  style: ['normal', 'italic'],
})

const siteUrl = process.env.NEXT_PUBLIC_FRONTEND_URL || 'https://chatchonk.com'; // Fallback for local dev

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: {
    default: 'ChatChonk - Tame the Chatter. Find the Signal.',
    template: '%s | ChatChonk',
  },
  description: 'ChatChonk transforms messy AI chat logs from ChatGPT, Claude, Gemini and more into structured, searchable knowledge bundles. Designed for second-brain builders and neurodivergent thinkers.',
  keywords: [
    'ChatChonk',
    'AI Chat',
    'Knowledge Management',
    'Obsidian',
    'Notion',
    'Second Brain',
    'ADHD',
    'Neurodivergent',
    'Productivity',
    'Note Taking',
    'LLM',
    'ChatGPT',
    'Claude',
    'Gemini',
  ],
  authors: [{ name: 'Rip Jonesy', url: siteUrl }],
  creator: 'Rip Jonesy',
  publisher: 'ChatChonk',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-video-preview': -1,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  openGraph: {
    title: 'ChatChonk - Tame the Chatter. Find the Signal.',
    description: 'Transform AI chat logs into structured, searchable knowledge. Perfect for Obsidian, Notion, and neurodivergent thinkers.',
    url: siteUrl,
    siteName: 'ChatChonk',
    images: [
      {
        url: '/images/og-image.png', // Replace with your actual OG image path
        width: 1200,
        height: 630,
        alt: 'ChatChonk - AI Chat to Structured Notes',
      },
    ],
    locale: 'en_US',
    type: 'website',
  },
  twitter: {
    card: 'summary_large_image',
    title: 'ChatChonk - Tame the Chatter. Find the Signal.',
    description: 'Transform AI chat logs into structured, searchable knowledge. Perfect for Obsidian, Notion, and neurodivergent thinkers.',
    // site: '@yourtwitterhandle', // Replace with your Twitter handle
    // creator: '@yourtwitterhandle', // Replace with your Twitter handle
    images: ['/images/twitter-image.png'], // Replace with your actual Twitter image path
  },
  icons: {
    icon: '/icons/favicon.ico',
    shortcut: '/icons/favicon-16x16.png',
    apple: '/icons/apple-touch-icon.png',
    other: [
      { rel: 'apple-touch-icon-precomposed', url: '/icons/apple-touch-icon-precomposed.png' },
      { rel: 'icon', type: 'image/png', sizes: '32x32', url: '/icons/favicon-32x32.png' },
      { rel: 'icon', type: 'image/png', sizes: '16x16', url: '/icons/favicon-16x16.png' },
      { rel: 'mask-icon', url: '/icons/safari-pinned-tab.svg', color: '#FF4B8C' }, // Brand pink
    ],
  },
  manifest: '/site.webmanifest',
};

export const viewport: Viewport = {
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FFFFFF' }, // chatchonk-white
    { media: '(prefers-color-scheme: dark)', color: '#1A1A1A' }, // chatchonk-black (for future dark mode)
  ],
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  colorScheme: 'light', // Set to 'light dark' if dark mode is implemented
};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={clsx(inter.variable, poppins.variable, 'scroll-smooth')} suppressHydrationWarning>
      <body className="font-primary bg-chatchonk-neutral-50 text-chatchonk-neutral-800 antialiased selection:bg-chatchonk-pink-500 selection:text-white">
        <HighlightProvider projectId={process.env.NEXT_PUBLIC_HIGHLIGHT_PROJECT_ID!}>
        {/* <ThemeProvider attribute="class" defaultTheme="light" enableSystem> */}
          {/* Header can go here if it's part of every page */}
          <main className="flex min-h-screen flex-col">
            {children}
          </main>
          {/* Footer can go here if it's part of every page */}
          <Toaster richColors position="top-right" />
          {/* Persistent AI Coach */}
          <Coach userId="demo-user" />
        {/* </ThemeProvider> */}
        </HighlightProvider>
      </body>
    </html>
  );
}
