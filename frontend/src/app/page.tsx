/**
 * Home Page - Landing page with enhanced cool blue theme
 */

import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { MessageSquare, Upload, FileText, Brain, Search, Table, Bot, Sparkles, LayoutDashboard, BarChart3 } from 'lucide-react';

export default function Home() {
  return (
    <div className="container py-6 flex flex-col items-center justify-center min-h-[70vh] space-y-12 py-8">
      {/* Hero Section */}
      <div className="text-center space-y-6 relative">
        {/* Background decoration */}
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-0 left-1/2 -translate-x-1/2 w-96 h-96 bg-primary/10 rounded-full blur-3xl"></div>
          <div className="absolute top-10 left-1/4 w-64 h-64 bg-accent/10 rounded-full blur-2xl"></div>
        </div>
        
        {/* Icon */}
        <div className="flex justify-center">
          <div className="relative">
            <div className="absolute inset-0 bg-gradient-to-r from-primary to-accent blur-2xl opacity-30 rounded-full scale-150"></div>
            <div className="relative bg-gradient-to-br from-primary to-accent p-5 rounded-2xl shadow-2xl shadow-primary/30">
              <FileText className="h-12 w-12 text-white" />
            </div>
          </div>
        </div>
        
        <h1 className="text-5xl font-bold bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
          Financial Expert Assistant
        </h1>
        <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
          AI-powered RAG chatbox for analyzing Vietnamese financial reports. 
          <br />
          <span className="text-primary font-medium">Upload PDFs, ask questions, get insights.</span>
        </p>
      </div>

      {/* Quick Actions */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 w-full max-w-5xl px-4">
        {/* Dashboard Card */}
        <Card className="group hover:shadow-2xl hover:shadow-blue-500/10 transition-all duration-300 border-blue-500/10 hover:border-blue-500/30 bg-gradient-to-br from-card to-blue-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-lg">
              <div className="bg-gradient-to-br from-blue-500 to-blue-600 p-2.5 rounded-xl shadow-lg shadow-blue-500/25 group-hover:scale-110 transition-transform">
                <LayoutDashboard className="h-5 w-5 text-white" />
              </div>
              Dashboard
            </CardTitle>
            <CardDescription>
              System performance and monitoring overview
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 shadow-lg shadow-blue-500/25">
              <Link href="/dashboard" className="flex items-center gap-2">
                <LayoutDashboard className="h-4 w-4" />
                View Dashboard
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Statistics Card */}
        <Card className="group hover:shadow-2xl hover:shadow-teal-500/10 transition-all duration-300 border-teal-500/10 hover:border-teal-500/30 bg-gradient-to-br from-card to-teal-500/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-lg">
              <div className="bg-gradient-to-br from-teal-500 to-teal-600 p-2.5 rounded-xl shadow-lg shadow-teal-500/25 group-hover:scale-110 transition-transform">
                <BarChart3 className="h-5 w-5 text-white" />
              </div>
              Statistics
            </CardTitle>
            <CardDescription>
              Financial ratios and risk classification
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full bg-gradient-to-r from-teal-500 to-teal-600 hover:from-teal-600 hover:to-teal-700 shadow-lg shadow-teal-500/25">
              <Link href="/statistics" className="flex items-center gap-2">
                <BarChart3 className="h-4 w-4" />
                View Statistics
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Chat Card */}
        <Card className="group hover:shadow-2xl hover:shadow-primary/10 transition-all duration-300 border-primary/10 hover:border-primary/30 bg-gradient-to-br from-card to-primary/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-lg">
              <div className="bg-gradient-to-br from-primary to-primary/80 p-2.5 rounded-xl shadow-lg shadow-primary/25 group-hover:scale-110 transition-transform">
                <MessageSquare className="h-5 w-5 text-white" />
              </div>
              Chat
            </CardTitle>
            <CardDescription>
              Ask questions using hybrid RAG system
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild className="w-full bg-gradient-to-r from-primary to-primary/80 hover:from-primary/90 hover:to-primary shadow-lg shadow-primary/25">
              <Link href="/chat" className="flex items-center gap-2">
                <Sparkles className="h-4 w-4" />
                Start Chatting
              </Link>
            </Button>
          </CardContent>
        </Card>

        {/* Upload Card */}
        <Card className="group hover:shadow-2xl hover:shadow-accent/10 transition-all duration-300 border-accent/10 hover:border-accent/30 bg-gradient-to-br from-card to-accent/5">
          <CardHeader>
            <CardTitle className="flex items-center gap-3 text-lg">
              <div className="bg-gradient-to-br from-amber-500 to-amber-600 p-2.5 rounded-xl shadow-lg shadow-amber-500/25 group-hover:scale-110 transition-transform">
                <Upload className="h-5 w-5 text-white" />
              </div>
              Upload
            </CardTitle>
            <CardDescription>
              Upload financial reports with Landing AI
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button asChild variant="outline" className="w-full border-amber-500/50 hover:bg-amber-50 hover:border-amber-500">
              <Link href="/upload" className="flex items-center gap-2">
                <Upload className="h-4 w-4" />
                Upload Report
              </Link>
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Features */}
      <div className="text-center space-y-6 pt-8 border-t border-primary/10 w-full max-w-4xl px-4">
        <h2 className="text-lg font-semibold text-muted-foreground">Powered by Advanced AI</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <FeatureBadge icon={<FileText className="h-4 w-4" />} text="Landing AI Parsing" />
          <FeatureBadge icon={<Brain className="h-4 w-4" />} text="OpenAI Embeddings" />
          <FeatureBadge icon={<Search className="h-4 w-4" />} text="Hybrid RAG" />
          <FeatureBadge icon={<Table className="h-4 w-4" />} text="Table Preservation" />
          <FeatureBadge icon={<Bot className="h-4 w-4" />} text="Agent Mode" />
        </div>
      </div>
    </div>
  );
}

function FeatureBadge({ icon, text }: { icon: React.ReactNode; text: string }) {
  return (
    <div className="flex items-center gap-2 px-4 py-2.5 bg-muted/50 hover:bg-primary/10 rounded-xl text-sm text-muted-foreground hover:text-primary transition-colors cursor-default">
      <span className="text-primary/60">{icon}</span>
      <span>{text}</span>
    </div>
  );
}
