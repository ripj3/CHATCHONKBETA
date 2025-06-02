'use client'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Server,
  Database,
  Cpu,
  HardDrive,
  Wifi,
  CheckCircle,
  AlertCircle,
  XCircle,
  RefreshCw,
  Activity
} from 'lucide-react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  AreaChart,
  Area
} from 'recharts'

// Mock system health data - replace with real API calls
const systemStatus = [
  {
    name: 'API Server',
    status: 'healthy',
    uptime: '99.9%',
    responseTime: '120ms',
    icon: Server,
  },
  {
    name: 'Database',
    status: 'healthy',
    uptime: '99.8%',
    responseTime: '45ms',
    icon: Database,
  },
  {
    name: 'AI Processing',
    status: 'warning',
    uptime: '98.5%',
    responseTime: '2.3s',
    icon: Cpu,
  },
  {
    name: 'File Storage',
    status: 'healthy',
    uptime: '99.9%',
    responseTime: '80ms',
    icon: HardDrive,
  },
  {
    name: 'External APIs',
    status: 'degraded',
    uptime: '97.2%',
    responseTime: '1.8s',
    icon: Wifi,
  },
]

const performanceData = [
  { time: '00:00', cpu: 45, memory: 62, disk: 78 },
  { time: '04:00', cpu: 32, memory: 58, disk: 78 },
  { time: '08:00', cpu: 67, memory: 71, disk: 79 },
  { time: '12:00', cpu: 89, memory: 85, disk: 80 },
  { time: '16:00', cpu: 76, memory: 79, disk: 81 },
  { time: '20:00', cpu: 54, memory: 68, disk: 82 },
]

const responseTimeData = [
  { time: '00:00', api: 120, db: 45, ai: 2100 },
  { time: '04:00', api: 110, db: 42, ai: 1800 },
  { time: '08:00', api: 135, db: 48, ai: 2400 },
  { time: '12:00', api: 156, db: 52, ai: 2800 },
  { time: '16:00', api: 142, db: 49, ai: 2200 },
  { time: '20:00', api: 128, db: 46, ai: 1900 },
]

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'healthy':
      return <CheckCircle className="h-5 w-5 text-green-500" />
    case 'warning':
      return <AlertCircle className="h-5 w-5 text-yellow-500" />
    case 'degraded':
    case 'error':
      return <XCircle className="h-5 w-5 text-red-500" />
    default:
      return <Activity className="h-5 w-5 text-gray-500" />
  }
}

const getStatusBadge = (status: string) => {
  switch (status) {
    case 'healthy':
      return <Badge variant="default">Healthy</Badge>
    case 'warning':
      return <Badge variant="secondary">Warning</Badge>
    case 'degraded':
      return <Badge variant="destructive">Degraded</Badge>
    case 'error':
      return <Badge variant="destructive">Error</Badge>
    default:
      return <Badge variant="outline">Unknown</Badge>
  }
}

export default function SystemHealthPage() {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Health</h1>
          <p className="text-gray-600">Monitor system performance and health metrics</p>
        </div>
        <Button>
          <RefreshCw className="h-4 w-4 mr-2" />
          Refresh
        </Button>
      </div>

      {/* System Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-6">
        {systemStatus.map((service) => (
          <Card key={service.name}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {service.name}
              </CardTitle>
              <service.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="flex items-center space-x-2 mb-2">
                {getStatusIcon(service.status)}
                {getStatusBadge(service.status)}
              </div>
              <div className="text-xs text-muted-foreground space-y-1">
                <div>Uptime: {service.uptime}</div>
                <div>Response: {service.responseTime}</div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Performance Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Resource Usage */}
        <Card>
          <CardHeader>
            <CardTitle>Resource Usage</CardTitle>
            <CardDescription>
              CPU, Memory, and Disk usage over the last 24 hours
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <AreaChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value}%`, '']} />
                <Area
                  type="monotone"
                  dataKey="cpu"
                  stackId="1"
                  stroke="#8884d8"
                  fill="#8884d8"
                  name="CPU"
                />
                <Area
                  type="monotone"
                  dataKey="memory"
                  stackId="1"
                  stroke="#82ca9d"
                  fill="#82ca9d"
                  name="Memory"
                />
                <Area
                  type="monotone"
                  dataKey="disk"
                  stackId="1"
                  stroke="#ffc658"
                  fill="#ffc658"
                  name="Disk"
                />
              </AreaChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Response Times */}
        <Card>
          <CardHeader>
            <CardTitle>Response Times</CardTitle>
            <CardDescription>
              Service response times over the last 24 hours
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={responseTimeData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip formatter={(value) => [`${value}ms`, '']} />
                <Line
                  type="monotone"
                  dataKey="api"
                  stroke="#8884d8"
                  strokeWidth={2}
                  name="API"
                />
                <Line
                  type="monotone"
                  dataKey="db"
                  stroke="#82ca9d"
                  strokeWidth={2}
                  name="Database"
                />
                <Line
                  type="monotone"
                  dataKey="ai"
                  stroke="#ffc658"
                  strokeWidth={2}
                  name="AI Processing"
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      {/* System Information */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Server Information */}
        <Card>
          <CardHeader>
            <CardTitle>Server Information</CardTitle>
            <CardDescription>
              Current server configuration and status
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex justify-between">
                <span className="text-sm font-medium">Environment</span>
                <Badge>Production</Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Version</span>
                <span className="text-sm text-gray-600">v1.2.3</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Uptime</span>
                <span className="text-sm text-gray-600">15 days, 4 hours</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">CPU Cores</span>
                <span className="text-sm text-gray-600">4 cores</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Memory</span>
                <span className="text-sm text-gray-600">8 GB</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm font-medium">Storage</span>
                <span className="text-sm text-gray-600">100 GB SSD</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Alerts */}
        <Card>
          <CardHeader>
            <CardTitle>Recent Alerts</CardTitle>
            <CardDescription>
              Latest system alerts and notifications
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">High AI processing latency</p>
                  <p className="text-xs text-gray-500">2 minutes ago</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <XCircle className="h-5 w-5 text-red-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">External API timeout</p>
                  <p className="text-xs text-gray-500">15 minutes ago</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <CheckCircle className="h-5 w-5 text-green-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Database backup completed</p>
                  <p className="text-xs text-gray-500">1 hour ago</p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <AlertCircle className="h-5 w-5 text-yellow-500 mt-0.5" />
                <div className="flex-1">
                  <p className="text-sm font-medium">Memory usage above 80%</p>
                  <p className="text-xs text-gray-500">2 hours ago</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
