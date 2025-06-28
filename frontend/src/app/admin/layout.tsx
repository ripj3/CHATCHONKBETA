import { Metadata } from 'next'
import Link from 'next/link'
import { 
  Users, 
  Files, 
  Brain, 
  FileText, 
  Activity,
  Settings,
  Home,
  BarChart3
} from 'lucide-react'

export const metadata: Metadata = {
  title: 'Admin Dashboard | ChatChonk',
  description: 'ChatChonk Admin Dashboard - Manage users, files, AI models, and system health',
}

const navigation = [
  { name: 'Dashboard', href: '/admin', icon: Home },
  { name: 'Users', href: '/admin/users', icon: Users },
  { name: 'Files', href: '/admin/files', icon: Files },
  { name: 'AI Models', href: '/admin/models', icon: Brain },
  { name: 'Templates', href: '/admin/templates', icon: FileText },
  { name: 'Analytics', href: '/admin/analytics', icon: BarChart3 },
  { name: 'System Health', href: '/admin/system', icon: Activity },
  { name: 'Settings', href: '/admin/settings', icon: Settings },
]

export default function AdminLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg">
        <div className="flex h-16 items-center justify-center border-b border-gray-200">
          <h1 className="text-xl font-bold text-chatchonk-pink-600">
            ChatChonk Admin
          </h1>
        </div>
        
        <nav className="mt-8 px-4" aria-label="Main Navigation">
          <ul className="space-y-2">
            {navigation.map((item) => (
              <li key={item.name}>
                <Link
                  href={item.href}
                  className="flex items-center rounded-lg px-4 py-2 text-sm font-medium text-gray-700 hover:bg-chatchonk-pink-50 hover:text-chatchonk-pink-700 transition-colors"
                >
                  <item.icon className="mr-3 h-5 w-5" aria-hidden="true" />
                  {item.name}
                </Link>
              </li>
            ))}
          </ul>
        </nav>
      </aside>

      {/* Main content */}
      <main className="pl-64">
        {/* Top header */}
        <header className="bg-white shadow-sm border-b border-gray-200">
          <div className="px-6 py-4">
            <div className="flex items-center justify-between">
              <h2 className="text-2xl font-bold text-gray-900">
                Admin Dashboard
              </h2>
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-500">
                  Welcome back, Admin
                </span>
                <div className="h-8 w-8 rounded-full bg-chatchonk-pink-500 flex items-center justify-center">
                  <span className="text-white text-sm font-medium">A</span>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-6">
          {children}
        </main>
      </main>
    </div>
  )
}
