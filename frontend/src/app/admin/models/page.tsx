'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { 
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { 
  Brain,
  Zap,
  Clock,
  TrendingUp,
  Activity,
  CheckCircle,
  AlertCircle
} from 'lucide-react'
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'

// Mock data - replace with real API calls
const modelStats = [
  {
    title: 'Total Requests',
    value: '12,345',
    change: '+23%',
    icon: Brain,
  },
  {
    title: 'Avg Response Time',
    value: '2.3s',
    change: '-12%',
    icon: Clock,
  },
  {
    title: 'Success Rate',
    value: '98.5%',
    change: '+0.5%',
    icon: CheckCircle,
  },
  {
    title: 'Active Models',
    value: '6',
    change: '+1',
    icon: Activity,
  },
]

const performanceData = [
  { time: '00:00', requests: 45, responseTime: 2.1 },
  { time: '04:00', requests: 23, responseTime: 1.8 },
  { time: '08:00', requests: 89, responseTime: 2.4 },
  { time: '12:00', requests: 156, responseTime: 2.8 },
  { time: '16:00', requests: 134, responseTime: 2.2 },
  { time: '20:00', requests: 78, responseTime: 1.9 },
]

const modelUsageData = [
  { name: 'HuggingFace', requests: 4500, successRate: 98.2, avgTime: 2.1 },
  { name: 'OpenAI GPT-4', requests: 3200, successRate: 99.1, avgTime: 1.8 },
  { name: 'Anthropic Claude', requests: 2800, successRate: 97.8, avgTime: 2.4 },
  { name: 'Mistral', requests: 1200, successRate: 96.5, avgTime: 2.0 },
  { name: 'DeepSeek', requests: 800, successRate: 95.2, avgTime: 2.6 },
  { name: 'Qwen', requests: 500, successRate: 94.8, avgTime: 2.3 },
]

const taskDistribution = [
  { name: 'Summarization', value: 35, color: '#8884d8' },
  { name: 'Topic Extraction', value: 25, color: '#82ca9d' },
  { name: 'Classification', value: 20, color: '#ffc658' },
  { name: 'Sensemaking', value: 15, color: '#ff7300' },
  { name: 'Other', value: 5, color: '#00ff00' },
]

const recentErrors = [
  {
    id: 1,
    model: 'HuggingFace',
    error: 'Rate limit exceeded',
    time: '2 minutes ago',
    severity: 'warning',
  },
  {
    id: 2,
    model: 'OpenAI GPT-4',
    error: 'API timeout',
    time: '15 minutes ago',
    severity: 'error',
  },
  {
    id: 3,
    model: 'Anthropic Claude',
    error: 'Invalid request format',
    time: '1 hour ago',
    severity: 'warning',
  },
]

export default function ModelsPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI Models Performance</h1>
        <p className="text-gray-600">Monitor AI model usage, performance, and health</p>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        {modelStats.map((stat) => (
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
                <span className="inline-flex items-center text-green-600">
                  <TrendingUp className="h-3 w-3 mr-1" />
                  {stat.change}
                </span>
                {' '}from last hour
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Performance Over Time */}
        <Card>
          <CardHeader>
            <CardTitle>Performance Over Time</CardTitle>
            <CardDescription>
              Request volume and response times over the last 24 hours
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis yAxisId="left" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Bar yAxisId="left" dataKey="requests" fill="#8884d8" name="Requests" />
                <Line 
                  yAxisId="right"
                  type="monotone" 
                  dataKey="responseTime" 
                  stroke="#82ca9d" 
                  strokeWidth={2}
                  name="Response Time (s)"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Task Distribution */}
        <Card>
          <CardHeader>
            <CardTitle>Task Distribution</CardTitle>
            <CardDescription>
              Distribution of AI tasks processed today
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={taskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {taskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* Model Performance Table */}
      <Card>
        <CardHeader>
          <CardTitle>Model Performance</CardTitle>
          <CardDescription>
            Detailed performance metrics for each AI model
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Model</TableHead>
                <TableHead>Requests</TableHead>
                <TableHead>Success Rate</TableHead>
                <TableHead>Avg Response Time</TableHead>
                <TableHead>Status</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {modelUsageData.map((model) => (
                <TableRow key={model.name}>
                  <TableCell>
                    <div className="flex items-center space-x-3">
                      <Brain className="h-5 w-5 text-chatchonk-pink-500" />
                      <div className="font-medium text-gray-900">{model.name}</div>
                    </div>
                  </TableCell>
                  <TableCell>{model.requests.toLocaleString()}</TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <span>{model.successRate}%</span>
                      {model.successRate > 97 ? (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      ) : (
                        <AlertCircle className="h-4 w-4 text-yellow-500" />
                      )}
                    </div>
                  </TableCell>
                  <TableCell>{model.avgTime}s</TableCell>
                  <TableCell>
                    <Badge 
                      variant={model.successRate > 97 ? 'default' : 'secondary'}
                    >
                      {model.successRate > 97 ? 'Healthy' : 'Warning'}
                    </Badge>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Recent Errors */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Errors</CardTitle>
          <CardDescription>
            Latest errors and warnings from AI models
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {recentErrors.map((error) => (
              <div key={error.id} className="flex items-center space-x-4 p-4 border rounded-lg">
                <div className="flex-shrink-0">
                  {error.severity === 'error' ? (
                    <AlertCircle className="h-5 w-5 text-red-500" />
                  ) : (
                    <AlertCircle className="h-5 w-5 text-yellow-500" />
                  )}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium text-gray-900">
                    {error.model}: {error.error}
                  </p>
                  <p className="text-sm text-gray-500">
                    {error.time}
                  </p>
                </div>
                <div className="flex-shrink-0">
                  <Badge 
                    variant={error.severity === 'error' ? 'destructive' : 'secondary'}
                  >
                    {error.severity}
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
