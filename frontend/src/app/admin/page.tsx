'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Users, 
  Files, 
  Brain, 
  FileText, 
  TrendingUp,
  Clock,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts'

// Mock data - replace with real API calls
const stats = [
  {
    title: 'Total Users',
    value: '1,234',
    change: '+12%',
    changeType: 'positive' as const,
    icon: Users,
  },
  {
    title: 'Files Processed',
    value: '5,678',
    change: '+8%',
    changeType: 'positive' as const,
    icon: Files,
  },
  {
    title: 'AI Requests',
    value: '12,345',
    change: '+23%',
    changeType: 'positive' as const,
    icon: Brain,
  },
  {
    title: 'Templates Used',
    value: '89',
    change: '+5%',
    changeType: 'positive' as const,
    icon: FileText,
  },
]

const processingData = [
  { name: 'Mon', files: 24, requests: 45 },
  { name: 'Tue', files: 13, requests: 32 },
  { name: 'Wed', files: 98, requests: 123 },
  { name: 'Thu', files: 39, requests: 67 },
  { name: 'Fri', files: 48, requests: 89 },
  { name: 'Sat', files: 38, requests: 56 },
  { name: 'Sun', files: 43, requests: 78 },
]

const modelUsageData = [
  { name: 'HuggingFace', value: 45, color: '#8884d8' },
  { name: 'OpenAI', value: 30, color: '#82ca9d' },
  { name: 'Anthropic', value: 20, color: '#ffc658' },
  { name: 'Other', value: 5, color: '#ff7300' },
]

const recentActivity = [
  {
    id: 1,
    type: 'file_upload',
    message: 'New file uploaded: chat_export_2024.zip',
    time: '2 minutes ago',
    status: 'processing',
  },
  {
    id: 2,
    type: 'ai_request',
    message: 'AI processing completed for user_123',
    time: '5 minutes ago',
    status: 'completed',
  },
  {
    id: 3,
    type: 'template_used',
    message: 'ADHD Idea Harvest template applied',
    time: '10 minutes ago',
    status: 'completed',
  },
  {
    id: 4,
    type: 'user_signup',
    message: 'New user registered: john@example.com',
    time: '15 minutes ago',
    status: 'completed',
  },
]

export default function AdminDashboard() {
  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground">
                <span className={`inline-flex items-center ${
                  stat.changeType === 'positive' ? 'text-green-600' : 'text-red-600'
                }`}>
                  <TrendingUp className="h-3 w-3 mr-1" />
                  {stat.change}
                </span>
                {' '}from last month
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Processing Activity Chart */}
        <Card>
          <CardHeader>
            <CardTitle>Processing Activity</CardTitle>
            <CardDescription>
              Files processed and AI requests over the last 7 days
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={processingData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="files" 
                  stroke="#8884d8" 
                  strokeWidth={2}
                  name="Files"
                />
                <Line 
                  type="monotone" 
                  dataKey="requests" 
                  stroke="#82ca9d" 
                  strokeWidth={2}
                  name="AI Requests"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Model Usage Chart */}
        <Card>
          <CardHeader>
            <CardTitle>AI Model Usage</CardTitle>
            <CardDescription>
              Distribution of AI model usage this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={modelUsageData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {modelUsageData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Recent Activity */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>
            Latest system activities and events
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentActivity.map((activity) => (
              <div key={activity.id} className="flex items-center space-x-4">
                <div className="flex-shrink-0">
                  {activity.status === 'completed' ? (
                    <CheckCircle className="h-5 w-5 text-green-500" />
                  ) : activity.status === 'processing' ? (
                    <Clock className="h-5 w-5 text-yellow-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {activity.message}
                  </p>
                  <p className="text-sm text-gray-500">
                    {activity.time}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <Badge 
                    variant={
                      activity.status === 'completed' ? 'default' : 
                      activity.status === 'processing' ? 'secondary' : 
                      'destructive'
                    }
                  >
                    {activity.status}
                  </Badge>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
