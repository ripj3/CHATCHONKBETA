'use client'

// This is a test comment for Kimi-Dev review

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Upload, 
  Download, 
  Brain, 
  FileText, 
  Zap, 
  Shield, 
  CheckCircle,
  ArrowRight,
  Settings,
  Sparkles
} from 'lucide-react'

export default function HomePage() {
  const [dragActive, setDragActive] = useState(false)

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true)
    } else if (e.type === "dragleave") {
      setDragActive(false)
    }
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      // Handle file upload
      console.log('File dropped:', e.dataTransfer.files[0])
    }
  }

  const features = [
    {
      icon: Upload,
      title: "Upload Chat Exports",
      description: "Drop your ChatGPT, Claude, Gemini exports (up to 2GB) and let ChatChonk work its magic."
    },
    {
      icon: Brain,
      title: "AI-Powered Processing",
      description: "Our AutoModel system intelligently processes your conversations using multiple AI providers."
    },
    {
      icon: FileText,
      title: "Smart Templates",
      description: "Choose from ADHD-optimized templates or create custom ones for your specific needs."
    },
    {
      icon: Download,
      title: "Export Ready Files",
      description: "Get Obsidian-ready Markdown, Notion imports, or clean PDFs with backlinks and metadata."
    }
  ]

  const templates = [
    { name: "ADHD Idea Harvest", description: "Perfect for scattered thoughts and hyperfocus sessions", popular: true },
    { name: "Meeting Notes Synthesizer", description: "Transform conversations into actionable summaries" },
    { name: "Plot Development Companion", description: "Organize creative writing and storytelling ideas" },
    { name: "Worldbuilding Companion", description: "Structure fantasy and sci-fi world creation" }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-chatchonk-neutral-50 to-chatchonk-pink-50">
      {/* Header */}
      <header className="border-b border-chatchonk-neutral-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-chatchonk-pink-500 to-chatchonk-pink-600 flex items-center justify-center">
                <Sparkles className="h-5 w-5 text-white" />
              </div>
              <h1 className="text-2xl font-bold text-chatchonk-neutral-900">ChatChonk</h1>
            </div>
            <div className="flex items-center space-x-4">
              <Link 
                href="/admin" 
                className="text-sm text-chatchonk-neutral-600 hover:text-chatchonk-pink-600 transition-colors"
              >
                <Settings className="h-4 w-4 inline mr-1" />
                Admin
              </Link>
              <Button variant="outline">Sign In</Button>
              <Button>Get Started</Button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="container mx-auto px-6 py-16">
        <div className="text-center max-w-4xl mx-auto">
          <Badge className="mb-4 bg-chatchonk-pink-100 text-chatchonk-pink-800 hover:bg-chatchonk-pink-200">
            ✨ Tame the Chatter. Find the Signal.
          </Badge>
          <h1 className="text-5xl font-bold text-chatchonk-neutral-900 mb-6 leading-tight">
            Transform AI Chat Chaos into 
            <span className="text-chatchonk-pink-600"> Organized Knowledge</span>
          </h1>
          <p className="text-xl text-chatchonk-neutral-600 mb-8 leading-relaxed">
            ChatChonk turns messy AI conversations from ChatGPT, Claude, and Gemini into 
            structured, searchable knowledge bundles. Perfect for ADHD minds and second-brain builders.
          </p>
          
          {/* Upload Area */}
          <Card className="max-w-2xl mx-auto mb-8">
            <CardContent className="p-8">
              <div
                className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                  dragActive 
                    ? 'border-chatchonk-pink-500 bg-chatchonk-pink-50' 
                    : 'border-chatchonk-neutral-300 hover:border-chatchonk-pink-400'
                }`}
                onDragEnter={handleDrag}
                onDragLeave={handleDrag}
                onDragOver={handleDrag}
                onDrop={handleDrop}
              >
                <Upload className="h-12 w-12 text-chatchonk-pink-500 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-chatchonk-neutral-900 mb-2">
                  Drop your chat exports here
                </h3>
                <p className="text-chatchonk-neutral-600 mb-4">
                  Support for ZIP files up to 2GB from ChatGPT, Claude, Gemini & more
                </p>
                <Button size="lg" className="bg-chatchonk-pink-600 hover:bg-chatchonk-pink-700">
                  <Upload className="h-4 w-4 mr-2" />
                  Choose Files
                </Button>
              </div>
            </CardContent>
          </Card>

          <div className="flex items-center justify-center space-x-6 text-sm text-chatchonk-neutral-500">
            <div className="flex items-center">
              <Shield className="h-4 w-4 mr-1" />
              Privacy-first
            </div>
            <div className="flex items-center">
              <Zap className="h-4 w-4 mr-1" />
              Fast processing
            </div>
            <div className="flex items-center">
              <CheckCircle className="h-4 w-4 mr-1" />
              No signup required
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white py-16">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-chatchonk-neutral-900 mb-4">
              How ChatChonk Works
            </h2>
            <p className="text-lg text-chatchonk-neutral-600 max-w-2xl mx-auto">
              Four simple steps to transform your AI conversations into organized knowledge
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <Card key={feature.title} className="text-center hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="h-12 w-12 rounded-lg bg-chatchonk-pink-100 flex items-center justify-center mx-auto mb-4">
                    <feature.icon className="h-6 w-6 text-chatchonk-pink-600" />
                  </div>
                  <CardTitle className="text-lg">{feature.title}</CardTitle>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-chatchonk-neutral-600">
                    {feature.description}
                  </CardDescription>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Templates Section */}
      <section className="py-16 bg-chatchonk-neutral-50">
        <div className="container mx-auto px-6">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-chatchonk-neutral-900 mb-4">
              ADHD-Optimized Templates
            </h2>
            <p className="text-lg text-chatchonk-neutral-600 max-w-2xl mx-auto">
              Choose from templates designed for neurodivergent minds and hyperfocus sessions
            </p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto">
            {templates.map((template) => (
              <Card key={template.name} className="hover:shadow-lg transition-shadow">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-lg">{template.name}</CardTitle>
                    {template.popular && (
                      <Badge className="bg-chatchonk-pink-100 text-chatchonk-pink-800">
                        Popular
                      </Badge>
                    )}
                  </div>
                </CardHeader>
                <CardContent>
                  <CardDescription className="text-chatchonk-neutral-600 mb-4">
                    {template.description}
                  </CardDescription>
                  <Button variant="outline" size="sm">
                    Preview Template
                    <ArrowRight className="h-3 w-3 ml-1" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-chatchonk-neutral-900 text-white py-12">
        <div className="container mx-auto px-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <div className="h-6 w-6 rounded bg-chatchonk-pink-600 flex items-center justify-center">
                <Sparkles className="h-4 w-4 text-white" />
              </div>
              <span className="font-semibold">ChatChonk</span>
            </div>
            <div className="flex items-center space-x-6">
              <Link href="/admin" className="text-sm hover:text-chatchonk-pink-400 transition-colors">
                Admin Dashboard
              </Link>
              <span className="text-sm text-chatchonk-neutral-400">
                Built with ❤️ by Rip Jonesy
              </span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
