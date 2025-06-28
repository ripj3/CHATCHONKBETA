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
  Plus,
  Edit,
  Trash2,
  FileText,
  Download,
  Eye,
  TrendingUp
} from 'lucide-react'

// Visually-hidden helper class
const srOnly =
  'absolute w-px h-px p-0 -m-1 overflow-hidden clip-rect-0 whitespace-nowrap border-0'

// Mock template data - replace with real API calls
const templates = [
  {
    id: 1,
    name: 'ADHD Idea Harvest',
    description: 'Organizes scattered thoughts and ideas from ADHD-style conversations',
    category: 'Personal Development',
    usageCount: 1234,
    lastUsed: '2024-01-15T10:30:00Z',
    createdAt: '2023-12-01T09:00:00Z',
    status: 'active',
    compatibility: ['obsidian-md', 'notion', 'html'],
    tags: ['adhd', 'productivity', 'ideas'],
  },
  {
    id: 2,
    name: 'Meeting Notes Synthesizer',
    description: 'Transforms meeting conversations into structured action items and summaries',
    category: 'Business',
    usageCount: 856,
    lastUsed: '2024-01-15T11:15:00Z',
    createdAt: '2023-11-15T14:20:00Z',
    status: 'active',
    compatibility: ['obsidian-md', 'notion', 'pdf'],
    tags: ['meetings', 'business', 'action-items'],
  },
  {
    id: 3,
    name: 'Plot Development Companion',
    description: 'Organizes creative writing and storytelling conversations',
    category: 'Creative',
    usageCount: 567,
    lastUsed: '2024-01-14T16:45:00Z',
    createdAt: '2023-10-20T11:30:00Z',
    status: 'active',
    compatibility: ['obsidian-md', 'html', 'docx'],
    tags: ['creative', 'writing', 'storytelling'],
  },
  {
    id: 4,
    name: 'Research Paper Outline',
    description: 'Structures academic research conversations into paper outlines',
    category: 'Academic',
    usageCount: 234,
    lastUsed: '2024-01-12T09:20:00Z',
    createdAt: '2023-09-10T13:45:00Z',
    status: 'draft',
    compatibility: ['obsidian-md', 'pdf', 'docx'],
    tags: ['academic', 'research', 'outline'],
  },
  {
    id: 5,
    name: 'Worldbuilding Companion',
    description: 'Organizes fantasy and sci-fi worldbuilding conversations',
    category: 'Creative',
    usageCount: 445,
    lastUsed: '2024-01-13T15:30:00Z',
    createdAt: '2023-08-05T10:15:00Z',
    status: 'active',
    compatibility: ['obsidian-md', 'notion', 'html'],
    tags: ['worldbuilding', 'fantasy', 'scifi'],
  },
]

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const getCategoryColor = (category: string) => {
  const colors = {
    'Personal Development': 'bg-blue-100 text-blue-800',
    'Business': 'bg-green-100 text-green-800',
    'Creative': 'bg-purple-100 text-purple-800',
    'Academic': 'bg-orange-100 text-orange-800',
  }
  return colors[category as keyof typeof colors] || 'bg-gray-100 text-gray-800'
}

export default function TemplatesPage() {
  const [searchTerm, setSearchTerm] = useState('')
  const [categoryFilter, setCategoryFilter] = useState('all')
  const [announcement, setAnnouncement] = useState('')

  const filteredTemplates = templates.filter(template => {
    const matchesSearch = template.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         template.description.toLowerCase().includes(searchTerm.toLowerCase())
    const matchesCategory = categoryFilter === 'all' || template.category === categoryFilter
    return matchesSearch && matchesCategory
  })

  const totalTemplates = templates.length
  const activeTemplates = templates.filter(t => t.status === 'active').length
  const totalUsage = templates.reduce((sum, t) => sum + t.usageCount, 0)
  const categories = Array.from(new Set(templates.map(t => t.category)))

  // Announce result count when filter changes
  useEffect(() => {
    setAnnouncement(`Showing ${filteredTemplates.length} templates.`)
  }, [filteredTemplates])

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Template Management</h1>
          <p className="text-gray-600">Manage ChatChonk processing templates</p>
        </div>
        <Button>
          <Plus className="h-4 w-4 mr-2" aria-hidden="true" />
          Create Template
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Templates</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalTemplates}</div>
            <p className="text-xs text-muted-foreground">
              {activeTemplates} active templates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Usage</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalUsage.toLocaleString()}</div>
            <p className="text-xs text-muted-foreground">
              Across all templates
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Categories</CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{categories.length}</div>
            <p className="text-xs text-muted-foreground">
              Template categories
            </p>
          </CardContent>
        </Card>
      </div>

      {/* Templates Table */}
      <Card>
        <CardHeader>
          <CardTitle>Templates</CardTitle>
          <CardDescription>
            All available processing templates
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center space-x-4 mb-6">
            <div className="relative flex-1 max-w-sm">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" aria-hidden="true" />
              {/* Hidden label for search */}
              <label htmlFor="search-templates" className={srOnly}>
                Search templates
              </label>
              <input
                id="search-templates"
                type="text"
                placeholder="Search templates..."
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            {/* Hidden label for category filter */}
            <label htmlFor="category-filter" className={srOnly}>
              Filter templates by category
            </label>
            <select
              id="category-filter"
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
            >
              <option value="all">All Categories</option>
              {categories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>

          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Template</TableHead>
                <TableHead>Category</TableHead>
                <TableHead>Usage Count</TableHead>
                <TableHead>Last Used</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Compatibility</TableHead>
                <TableHead className="w-[120px]">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filteredTemplates.map((template) => (
                <TableRow key={template.id}>
                  <TableCell>
                    <div>
                      <div className="font-medium text-gray-900">{template.name}</div>
                      <div className="text-sm text-gray-500 max-w-xs truncate">
                        {template.description}
                      </div>
                      <div className="flex flex-wrap gap-1 mt-1">
                        {template.tags.slice(0, 3).map(tag => (
                          <Badge key={tag} variant="outline" className="text-xs">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </TableCell>
                  <TableCell>
                    <Badge className={getCategoryColor(template.category)}>
                      {template.category}
                    </Badge>
                  </TableCell>
                  <TableCell>{template.usageCount.toLocaleString()}</TableCell>
                  <TableCell>{formatDate(template.lastUsed)}</TableCell>
                  <TableCell>
                    <Badge 
                      variant={template.status === 'active' ? 'default' : 'secondary'}
                    >
                      {template.status}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <div className="flex flex-wrap gap-1">
                      {template.compatibility.map(format => (
                        <Badge key={format} variant="outline" className="text-xs">
                          {format}
                        </Badge>
                      ))}
                    </div>
                  </TableCell>
                  <TableCell>
                    <div className="flex items-center space-x-2">
                      <Button variant="ghost" size="icon" aria-label="Preview template">
                        <Eye className="h-4 w-4" aria-hidden="true" />
                      </Button>
                      <Button variant="ghost" size="icon" aria-label="Edit template">
                        <Edit className="h-4 w-4" aria-hidden="true" />
                      </Button>
                      <Button variant="ghost" size="icon" aria-label="Download template">
                        <Download className="h-4 w-4" aria-hidden="true" />
                      </Button>
                      <Button variant="ghost" size="icon" aria-label="Delete template">
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </Button>
                    </div>
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
