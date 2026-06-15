import { useEffect } from 'react'
import Hero from './components/Hero'
import TheGap from './components/TheGap'
import Features from './components/Features'
import ComparisonTable from './components/ComparisonTable'
import Feasibility from './components/Feasibility'
import Footer from './components/Footer'

export default function App() {
  useEffect(() => {
    const els = document.querySelectorAll('.fade-in')
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            observer.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.12 }
    )
    els.forEach((el) => observer.observe(el))
    return () => observer.disconnect()
  }, [])

  return (
    <main>
      <Hero />
      <TheGap />
      <Features />
      <ComparisonTable />
      <Feasibility />
      <Footer />
    </main>
  )
}
