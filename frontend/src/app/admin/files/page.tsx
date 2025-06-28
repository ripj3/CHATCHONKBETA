'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
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
  Search,
  Filter,
  Download,
  MoreHorizontal,
  FileText,
  Clock,
  CheckCircle,
  AlertCircle,
  Upload
} from 'lucide-react'

// Mock file data - replace with real API calls
// Utility class for visually-hidden content
const srOnly =
  'absolute w-px h-px p-0 -m-1 overflow-hidden clip-rect-0 whitespace-nowrap border-0'

const files = [
  {
    id: 1,
    filename: 'chat_export_2024_01_15.zip',
    user: 'john.doe@example.com',
    size: '2.4 MB',
    status: 'completed',
    uploadedAt: '2024-01-15T10:30:00Z',
    processedAt: '2024-01-15T10:35:00Z',
    template: 'ADHD Idea Harvest',
    type: 'ChatGPT Export',
  },
  {
    id: 2,
    filename: 'claude_conversation_batch.zip',
    user: 'jane.smith@example.com',
    size: '1.8 MB',
    status: 'processing',
    uploadedAt: '2024-01-15T11:15:00Z',
    processedAt: null,
    template: 'Meeting Notes Synthesizer',
    type: 'Claude Export',
  },
  {
    id: 3,
    filename: 'gemini_chats_december.zip',
    user: 'bob.wilson@example.com',
    size: '3.2 MB',
    status: 'failed',
    uploadedAt: '2024-01-15T09:45:00Z',
    processedAt: null,
    template: 'Plot Development Companion',
    type: 'Gemini Export',
  },
  {
    id: 4,
    filename: 'mixed_ai_conversations.zip',
    user: 'alice.brown@example.com',
    size: '5.1 MB',
    status: 'completed',
    uploadedAt: '2024-01-14T16:20:00Z',
    processedAt: '2024-01-14T16:28:00Z',
    template: 'Worldbuilding Companion',
    type: 'Mixed Export',
  },
]

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return <CheckCircle className="h-4 w-4 text-green-500" aria-hidden="true" />
    case 'processing':
      return <Clock className="h-4 w-4 text-yellow-500" aria-hidden="true" />
    case 'failed':
      return <AlertCircle className="h-4 w-4 text-red-500" aria-hidden="true" />
    default:
      return <FileText className="h-4 w-4 text-gray-500" aria-hidden="true" />
  }
}

export default function FilesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [statusFilter, setStatusFilter] = useState('all')
  const [announcement, setAnnouncement] = useState('')

  const filteredFiles = files.filter(file => {
    const matchesSearch = file.filename.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         file.user.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesStatus = statusFilter === 'all' || file.status === statusFilter
    return matchesSearch && matchesStatus
  })

  const totalFiles = files.length
  const completedFiles = files.filter(f => f.status === 'completed').length
  const processingFiles = files.filter(f => f.status === 'processing').length
  const failedFiles = files.filter(f => f.status === 'failed').length

  // announce table result count changes
  useEffect(() => {
    setAnnouncement(`Showing ${filteredFiles.length} files.`)
  }, [filteredFiles])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">File Management</h1>
          <p className="text-gray-600">Monitor file uploads and processing status</p>
        </div>
        <Button>
          <Upload className="h-4 w-4 mr-2" aria-hidden="true" />
          Upload File
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Files</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalFiles}</div>
            <p className="text-xs text-muted-foreground">
              All uploaded files
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="h-4 w-4 text-green-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{completedFiles}</div>
            <p className="text-xs text-muted-foreground">
              Successfully processed
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Processing</CardTitle>
            <Clock className="h-4 w-4 text-yellow-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{processingFiles}</div>
            <p className="text-xs text-muted-foreground">
              Currently processing
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <AlertCircle className="h-4 w-4 text-red-500" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{failedFiles}</div>
            <p className="text-xs text-muted-foreground">
              Processing failed
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Files Table */}
      <Card>
        <CardHeader>
          <CardTitle>Files</CardTitle>
          <CardDescription>
            All uploaded files and their processing status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" aria-hidden="true" />
              {/* Hidden label for search */}
              <label htmlFor="search-files" className={srOnly}>
                Search files
              </label>
              <input
                id="search-files"
                type="text"
                placeholder="Search files..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            {/* Hidden label for status selector */}
            <label htmlFor="status-filter" className={srOnly}>
              Filter files by status
            </label>
            <select
              id="status-filter"
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>File</TableHead>
                <TableHead>User</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Template</TableHead>
                <TableHead>Size</TableHead>
                <TableHead>Uploaded</TableHead>
                <TableHead>Processed</TableHead>
                <TableHead className="w-[50px]"></TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredFiles.map((file) => (
                <TableRow key={file.id}>
                  <TableCell>
                    <div className="flex items-center space-x-3">
                      {getStatusIcon(file.status)}
                      <div>
                        <div className="font-medium text-gray-900">{file.filename}</div>
                        <div className="text-sm text-gray-500">{file.type}</div>
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm text-gray-900">{file.user}</div>
                  </TableCell>
                  <TableCell>
                    <Badge 
                      variant={
                        file.status === 'completed' ? 'default' :
                        file.status === 'processing' ? 'secondary' :
                        'destructive'
                      }
                    >
                      {file.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="text-sm text-gray-900">{file.template}</div>
                  </TableCell>
                  <TableCell>{file.size}</TableCell>
                  <TableCell>{formatDate(file.uploadedAt)}</TableCell>
                  <TableCell>
                    {file.processedAt ? formatDate(file.processedAt) : '-'}
                  </TableCell>
                  <TableCell>
                    <Button variant="ghost" size="icon" aria-label="More actions">
                      <MoreHorizontal className="h-4 w-4" aria-hidden="true" />
                    </Button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      {/* Live region for table updates */}
      <div className={srOnly} aria-live="assertive">
        {announcement}
      </div>
    </div>
  )
}
