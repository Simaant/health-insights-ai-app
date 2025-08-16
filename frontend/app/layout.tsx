import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Health Insights AI',
  description: 'AI-powered health insights from lab reports and wearable data',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className="bg-gray-900 min-h-screen font-sans antialiased">
        {children}
      </body>
    </html>
  )
}
