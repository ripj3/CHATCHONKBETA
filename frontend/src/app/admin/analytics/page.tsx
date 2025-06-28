'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  TrendingUp,
  TrendingDown,
  Users,
  FileText,
  Brain,
  Clock,
  Download,
  Calendar,
  Server, // New icon for backend metrics
  CheckCircle, // New icon for successful requests
  XCircle // New icon for error requests
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
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell
} from 'recharts'

// Utility class for screen-reader-only content
const srOnly = "absolute w-px h-px p-0 -m-1 overflow-hidden clip-rect-0 whitespace-nowrap border-0"

// Define a type for the metrics data
interface BackendMetrics {
  total_requests: number;
  successful_requests: number;
  error_requests: number;
  average_processing_time_seconds: string; // Keep as string for now, parse if needed for calculations
  request_counts_by_path: { [key: string]: number };
  error_counts_by_path: { [key: string]: number };
  status_code_counts: { [key: string]: number };
}

// Mock analytics data - replace with real API calls
const kpiData = [
  {
    title: 'Total Users',
    value: '2,847',
    change: '+12.5%',
    changeType: 'positive' as const,
    icon: Users,
    period: 'vs last month'
  },
  {
    title: 'Files Processed',
    value: '18,392',
    change: '+23.1%',
    changeType: 'positive' as const,
    icon: FileText,
    period: 'vs last month'
  },
  {
    title: 'AI Requests',
    value: '45,678',
    change: '+18.7%',
    changeType: 'positive' as const,
    icon: Brain,
    period: 'vs last month'
  },
  {
    title: 'Avg Processing Time',
    value: '2.3s',
    change: '-8.2%',
    changeType: 'positive' as const, // Note: a decrease in processing time is positive
    icon: Clock,
    period: 'vs last month'
  }
]

const userGrowthData = [
  { month: 'Jan', users: 1200, newUsers: 150, activeUsers: 980 },
  { month: 'Feb', users: 1350, newUsers: 180, activeUsers: 1100 },
  { month: 'Mar', users: 1580, newUsers: 230, activeUsers: 1280 },
  { month: 'Apr', users: 1820, newUsers: 240, activeUsers: 1450 },
  { month: 'May', users: 2100, newUsers: 280, activeUsers: 1680 },
  { month: 'Jun', users: 2450, newUsers: 350, activeUsers: 1950 },
  { month: 'Jul', users: 2847, newUsers: 397, activeUsers: 2280 },
]

const processingVolumeData = [
  { date: '2024-01-01', files: 45, requests: 234 },
  { date: '2024-01-02', files: 52, requests: 267 },
  { date: '2024-01-03', files: 38, requests: 198 },
  { date: '2024-01-04', files: 67, requests: 345 },
  { date: '2024-01-05', files: 89, requests: 456 },
  { date: '2024-01-06', files: 76, requests: 389 },
  { date: '2024-01-07', files: 94, requests: 478 },
]

const templateUsageData = [
  { name: 'ADHD Idea Harvest', usage: 35, color: '#8884d8' },
  { name: 'Meeting Notes', usage: 25, color: '#82ca9d' },
  { name: 'Plot Development', usage: 20, color: '#ffc658' },
  { name: 'Research Outline', usage: 12, color: '#ff7300' },
  { name: 'Worldbuilding', usage: 8, color: '#00ff00' },
]

const revenueData = [
  { month: 'Jan', revenue: 4500, subscriptions: 45 },
  { month: 'Feb', revenue: 5200, subscriptions: 52 },
  { month: 'Mar', revenue: 6800, subscriptions: 68 },
  { month: 'Apr', revenue: 7900, subscriptions: 79 },
  { month: 'May', revenue: 9200, subscriptions: 92 },
  { month: 'Jun', revenue: 11500, subscriptions: 115 },
  { month: 'Jul', revenue: 14200, subscriptions: 142 },
]

export default function AnalyticsPage() {
  const [backendMetrics, setBackendMetrics] = useState<BackendMetrics | null>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(true);
  const [metricsError, setMetricsError] = useState<string | null>(null);
  const [announcement, setAnnouncement] = useState('');

  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        setLoadingMetrics(true);
        const response = await fetch('/api/metrics'); // Assuming /api/metrics is accessible
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: BackendMetrics = await response.json();
        setBackendMetrics(data);
        setAnnouncement('Backend metrics loaded.');
      } catch (error) {
        console.error("Failed to fetch backend metrics:", error);
        setMetricsError("Failed to load backend metrics.");
        setAnnouncement('Failed to load backend metrics.');
      } finally {
        setLoadingMetrics(false);
      }
    };

    fetchMetrics();
    // Optionally, refetch metrics periodically
    const intervalId = setInterval(fetchMetrics, 15000); // Refetch every 15 seconds
    return () => clearInterval(intervalId); // Cleanup on unmount
  }, []);

  // Combine mock KPI data with real backend metrics
  const combinedKpiData = [
    ...kpiData,
    {
      title: 'Total API Requests',
      value: backendMetrics?.total_requests.toLocaleString() || 'N/A',
      change: '', // No change calculation for now
      changeType: 'positive' as const,
      icon: Server,
      period: 'since last restart'
    },
    {
      title: 'Successful Requests',
      value: backendMetrics?.successful_requests.toLocaleString() || 'N/A',
      change: '',
      changeType: 'positive' as const,
      icon: CheckCircle,
      period: 'since last restart'
    },
    {
      title: 'Error Requests',
      value: backendMetrics?.error_requests.toLocaleString() || 'N/A',
      change: '',
      changeType: 'negative' as const, // Assuming errors are negative
      icon: XCircle,
      period: 'since last restart'
    },
    {
      title: 'Avg API Latency',
      value: backendMetrics?.average_processing_time_seconds ? `${parseFloat(backendMetrics.average_processing_time_seconds).toFixed(2)}s` : 'N/A',
      change: '',
      changeType: 'positive' as const, // Can be positive or negative depending on trend
      icon: Clock,
      period: 'since last restart'
    }
  ]

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics Dashboard</h1>
          <p className="text-gray-600">Comprehensive insights into ChatChonk performance and usage</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <Calendar className="h-4 w-4 mr-2" aria-hidden="true" />
            Last 30 Days
          </Button>
          <Button>
            <Download className="h-4 w-4 mr-2" aria-hidden="true" />
            Export Report
          </Button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {loadingMetrics && (
          <Card className="col-span-full">
            <CardContent className="p-6 text-center text-gray-500">
              Loading backend metrics...
            </CardContent>
          </Card>
        )}
        {metricsError && (
          <Card className="col-span-full border-red-500">
            <CardContent className="p-6 text-center text-red-600">
              {metricsError}
            </CardContent>
          </Card>
        )}
        {combinedKpiData.map((kpi) => (
          <Card key={kpi.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {kpi.title}
              </CardTitle>
              <kpi.icon className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{kpi.value}</div>
              <p className="text-xs text-muted-foreground flex items-center">
                {kpi.change && (
                  kpi.changeType === 'positive' ? (
                    <TrendingUp className="h-3 w-3 mr-1 text-green-600" aria-hidden="true" />
                  ) : (
                    <TrendingDown className="h-3 w-3 mr-1 text-red-600" aria-hidden="true" />
                  )
                )}
                {kpi.change && (
                  <span className={kpi.changeType === 'positive' ? 'text-green-600' : 'text-red-600'}>
                    {kpi.change}
                  </span>
                )}
                <span className="ml-1">{kpi.period}</span>
              </p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* User Growth */}
        <Card>
          <CardHeader>
            <CardTitle>User Growth</CardTitle>
            <CardDescription>
              Total users, new signups, and active users over time
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div tabIndex={0}>
              <ResponsiveContainer
                width="100%"
                height={300}
                role="img"
                aria-label="Area chart showing total users, new users, and active users over the last seven months."
              >
                <AreaChart data={userGrowthData} isAnimationActive={false}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis />
                  <Tooltip />
                  <Area
                    type="monotone"
                    dataKey="users"
                    stackId="1"
                    stroke="#8884d8"
                    fill="#8884d8"
                    name="Total Users"
                  />
                  <Area
                    type="monotone"
                    dataKey="activeUsers"
                    stackId="2"
                    stroke="#82ca9d"
                    fill="#82ca9d"
                    name="Active Users"
                  />
                </AreaChart>
              </ResponsiveContainer>
              {/* Screen-reader fallback table */}
              <table className={srOnly}>
                <caption>User Growth Data</caption>
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Total Users</th>
                    <th>New Users</th>
                    <th>Active Users</th>
                  </tr>
                </thead>
                <tbody>
                  {userGrowthData.map((d) => (
                    <tr key={d.month}>
                      <td>{d.month}</td>
                      <td>{d.users}</td>
                      <td>{d.newUsers}</td>
                      <td>{d.activeUsers}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Processing Volume */}
        <Card>
          <CardHeader>
            <CardTitle>Processing Volume</CardTitle>
            <CardDescription>
              Daily file uploads and AI processing requests
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div tabIndex={0}>
              <ResponsiveContainer
                width="100%"
                height={300}
                role="img"
                aria-label="Line chart showing daily file uploads and AI processing requests over the last week."
              >
                <LineChart data={processingVolumeData} isAnimationActive={false}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" tickFormatter={(value: string) => new Date(value).toLocaleDateString()} />
                  <YAxis />
                  <Tooltip labelFormatter={(value) => new Date(value).toLocaleDateString()} />
                  <Line
                    type="monotone"
                    dataKey="files"
                    stroke="#8884d8"
                    strokeWidth={2}
                    name="Files Uploaded"
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
              {/* Screen-reader fallback table */}
              <table className={srOnly}>
                <caption>Processing Volume Data</caption>
                <thead>
                  <tr>
                    <th>Date</th>
                    <th>Files Uploaded</th>
                    <th>AI Requests</th>
                  </tr>
                </thead>
                <tbody>
                  {processingVolumeData.map((d) => (
                    <tr key={d.date}>
                      <td>{new Date(d.date).toLocaleDateString()}</td>
                      <td>{d.files}</td>
                      <td>{d.requests}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Template Usage */}
        <Card>
          <CardHeader>
            <CardTitle>Template Usage</CardTitle>
            <CardDescription>
              Most popular processing templates this month
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div tabIndex={0}>
              <ResponsiveContainer
                width="100%"
                height={300}
                role="img"
                aria-label="Pie chart showing distribution of template usage this month."
              >
                <PieChart isAnimationActive={false}>
                  <Pie
                    data={templateUsageData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="usage"
                  >
                    {templateUsageData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
              {/* Screen-reader fallback list */}
              <ul className={srOnly}>
                {templateUsageData.map((d) => (
                  <li key={d.name}>
                    {d.name}: {d.usage}% usage
                  </li>
                ))}
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Revenue Growth */}
        <Card>
          <CardHeader>
            <CardTitle>Revenue & Subscriptions</CardTitle>
            <CardDescription>
              Monthly recurring revenue and subscription growth
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div tabIndex={0}>
              <ResponsiveContainer
                width="100%"
                height={300}
                role="img"
                aria-label="Bar chart showing monthly revenue and subscription growth."
              >
                <BarChart data={revenueData} isAnimationActive={false}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="month" />
                  <YAxis yAxisId="left" />
                  <YAxis yAxisId="right" orientation="right" />
                  <Tooltip />
                  <Bar yAxisId="left" dataKey="revenue" fill="#8884d8" name="Revenue ($)" />
                  <Line yAxisId="right" type="monotone" dataKey="subscriptions" stroke="#82ca9d" strokeWidth={2} name="Subscriptions" />
                </BarChart>
              </ResponsiveContainer>
              {/* Screen-reader fallback table */}
              <table className={srOnly}>
                <caption>Revenue and Subscription Data</caption>
                <thead>
                  <tr>
                    <th>Month</th>
                    <th>Revenue ($)</th>
                    <th>Subscriptions</th>
                  </tr>
                </thead>
                <tbody>
                  {revenueData.map((d) => (
                    <tr key={d.month}>
                      <td>{d.month}</td>
                      <td>{d.revenue}</td>
                      <td>{d.subscriptions}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Summary Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader>
            <CardTitle>Top Performing Template</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">ADHD Idea Harvest</p>
                <p className="text-sm text-gray-600">35% of all processing</p>
              </div>
              <Badge className="bg-green-100 text-green-800">
                +15% this month
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Peak Usage Time</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">2:00 PM - 4:00 PM</p>
                <p className="text-sm text-gray-600">EST weekdays</p>
              </div>
              <Badge className="bg-blue-100 text-blue-800">
                Consistent
              </Badge>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>User Satisfaction</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-2xl font-bold">4.8/5.0</p>
                <p className="text-sm text-gray-600">Average rating</p>
              </div>
              <Badge className="bg-green-100 text-green-800">
                Excellent
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Live region for screen reader announcements */}
      <div className={srOnly} aria-live="assertive">
        {announcement}
      </div>
    </div>
  );
}
