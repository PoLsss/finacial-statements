/**
 * Header Component - Enhanced with cool blue theme + active tab highlighting
 */
'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { FileText, MessageSquare, Upload, Sparkles, LayoutDashboard, BarChart3 } from 'lucide-react';

const NAV_LINKS = [
  { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { href: '/statistics', label: 'Statistics', icon: BarChart3 },
  { href: '/chat', label: 'Chat', icon: MessageSquare },
];

export function Header() {
  const pathname = usePathname();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-primary/10 bg-gradient-to-r from-background via-background to-primary/5 backdrop-blur-xl supports-[backdrop-filter]:bg-background/80">
      <div className="container flex h-16 items-center">
        {/* Logo */}
        <div className="mr-4 flex">
          <Link href="/" className="mr-6 flex items-center space-x-3 group">
            <div className="relative">
              <div className="absolute inset-0 bg-primary/20 blur-lg rounded-full group-hover:bg-primary/30 transition-all"></div>
              <div className="relative bg-gradient-to-br from-primary to-accent p-2 rounded-xl shadow-lg">
                <FileText className="h-5 w-5 text-primary-foreground" />
              </div>
            </div>
            <div className="flex flex-col">
              <span className="font-bold text-lg bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
                Financial Expert
              </span>
              <span className="text-[10px] text-muted-foreground -mt-1">AI-Powered Analysis</span>
            </div>
          </Link>
        </div>

        {/* Navigation */}
        <nav className="flex items-center space-x-1 text-sm font-medium">
          {NAV_LINKS.map(({ href, label, icon: Icon }) => {
            const isActive = pathname === href || (href !== '/' && pathname.startsWith(href));
            return (
              <Link
                key={href}
                href={href}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-primary/15 text-primary font-semibold shadow-sm border-b-2 border-primary'
                    : 'text-foreground/70 hover:bg-primary/10 hover:text-primary'
                }`}
              >
                <Icon className={`h-4 w-4 ${isActive ? 'text-primary' : ''}`} />
                {label}
              </Link>
            );
          })}
        </nav>

        {/* Right Side */}
        <div className="flex flex-1 items-center justify-end space-x-3">
          <div className="hidden md:flex items-center gap-2 text-xs text-muted-foreground bg-muted/50 px-3 py-1.5 rounded-full">
            <Sparkles className="h-3 w-3 text-accent" />
            <span>Hybrid RAG System</span>
          </div>
          <Link
            href="/upload"
            className={`flex items-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200 border ${
              pathname === '/upload'
                ? 'text-white bg-gradient-to-r from-green-600 to-emerald-600 shadow-lg border-green-500/50 ring-2 ring-green-400/30'
                : 'text-white bg-gradient-to-r from-green-500 to-emerald-500 hover:from-green-600 hover:to-emerald-600 shadow-md hover:shadow-lg border-green-400/30'
            }`}
          >
            <Upload className="h-4 w-4" />
            Upload
          </Link>
        </div>
      </div>
    </header>
  );
}
