// Step 20: Root layout
// frontend/app/layout.tsx
import type { Metadata } from 'next'
import { Orbitron, Share_Tech_Mono, Rajdhani } from 'next/font/google'
import './globals.css'

const rajdhani = Rajdhani({
  subsets: ['latin'],
  weight: ['300', '500', '700'],
  variable: '--font-rajdhani'
})

const orbitron = Orbitron({
  subsets: ['latin'],
  variable: '--font-orbitron'
})

const shareTechMono = Share_Tech_Mono({
  subsets: ['latin'],
  weight: '400',
  variable: '--font-mono'
})

export const metadata: Metadata = {
  title: 'OPENCLAW — Agent Empire',
  description: 'Autonomous AI agents that want things'
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={`${rajdhani.variable} ${orbitron.variable} ${shareTechMono.variable}`}>
        {children}
      </body>
    </html>
  )
}