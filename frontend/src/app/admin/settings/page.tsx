'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { 
  Settings,
  Database,
  Key,
  Mail,
  Shield,
  Server,
  Save,
  RefreshCw,
  AlertTriangle
} from 'lucide-react'

export default function SettingsPage() {
  const [settings, setSettings] = useState({
    maxFileSize: '2GB',
    processingTimeout: '300',
    enableNotifications: true,
    enableAnalytics: true,
    maintenanceMode: false,
    autoBackup: true,
    backupFrequency: 'daily',
    apiRateLimit: '1000',
    maxConcurrentProcessing: '10'
  })

  const handleSave = () => {
    // Save settings logic here
    console.log('Saving settings:', settings)
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">System Settings</h1>
          <p className="text-gray-600">Configure ChatChonk system parameters and preferences</p>
        </div>
        <div className="flex items-center space-x-3">
          <Button variant="outline">
            <RefreshCw className="h-4 w-4 mr-2" />
            Reset to Defaults
          </Button>
          <Button onClick={handleSave}>
            <Save className="h-4 w-4 mr-2" />
            Save Changes
          </Button>
        </div>
      </div>

      {/* Settings Sections */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* File Processing Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Server className="h-5 w-5 mr-2" />
              File Processing
            </CardTitle>
            <CardDescription>
              Configure file upload and processing parameters
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Maximum File Size
              </label>
              <select 
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={settings.maxFileSize}
                onChange={(e) => setSettings({...settings, maxFileSize: e.target.value})}
              >
                <option value="1GB">1 GB</option>
                <option value="2GB">2 GB</option>
                <option value="5GB">5 GB</option>
              </select>
            </div>
            
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Processing Timeout (seconds)
              </label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={settings.processingTimeout}
                onChange={(e) => setSettings({...settings, processingTimeout: e.target.value})}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Max Concurrent Processing
              </label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={settings.maxConcurrentProcessing}
                onChange={(e) => setSettings({...settings, maxConcurrentProcessing: e.target.value})}
              />
            </div>
          </CardContent>
        </Card>

        {/* API Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Key className="h-5 w-5 mr-2" />
              API Configuration
            </CardTitle>
            <CardDescription>
              Manage API keys and rate limiting
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Rate Limit (requests/hour)
              </label>
              <input
                type="number"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={settings.apiRateLimit}
                onChange={(e) => setSettings({...settings, apiRateLimit: e.target.value})}
              />
            </div>

            <div className="space-y-3">
              <h4 className="text-sm font-medium text-gray-700">AI Provider Keys</h4>
              <div className="space-y-2">
                <div className="flex items-center justify-between p-3 border rounded-md">
                  <span className="text-sm">OpenAI API Key</span>
                  <Badge variant="default">Configured</Badge>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-md">
                  <span className="text-sm">Anthropic API Key</span>
                  <Badge variant="default">Configured</Badge>
                </div>
                <div className="flex items-center justify-between p-3 border rounded-md">
                  <span className="text-sm">HuggingFace API Key</span>
                  <Badge variant="secondary">Not Set</Badge>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Database Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Database & Backup
            </CardTitle>
            <CardDescription>
              Database configuration and backup settings
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Auto Backup</p>
                <p className="text-xs text-gray-500">Automatically backup database</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.autoBackup}
                  onChange={(e) => setSettings({...settings, autoBackup: e.target.checked})}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-chatchonk-pink-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-chatchonk-pink-600"></div>
              </label>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Backup Frequency
              </label>
              <select 
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-chatchonk-pink-500 focus:border-transparent"
                value={settings.backupFrequency}
                onChange={(e) => setSettings({...settings, backupFrequency: e.target.value})}
              >
                <option value="hourly">Hourly</option>
                <option value="daily">Daily</option>
                <option value="weekly">Weekly</option>
              </select>
            </div>

            <div className="p-3 bg-green-50 border border-green-200 rounded-md">
              <div className="flex items-center">
                <Database className="h-4 w-4 text-green-600 mr-2" />
                <span className="text-sm text-green-800">Database Status: Healthy</span>
              </div>
              <p className="text-xs text-green-600 mt-1">Last backup: 2 hours ago</p>
            </div>
          </CardContent>
        </Card>

        {/* Security & Notifications */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Security & Notifications
            </CardTitle>
            <CardDescription>
              Security settings and notification preferences
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Email Notifications</p>
                <p className="text-xs text-gray-500">Receive system alerts via email</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.enableNotifications}
                  onChange={(e) => setSettings({...settings, enableNotifications: e.target.checked})}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-chatchonk-pink-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-chatchonk-pink-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Analytics Tracking</p>
                <p className="text-xs text-gray-500">Enable usage analytics</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.enableAnalytics}
                  onChange={(e) => setSettings({...settings, enableAnalytics: e.target.checked})}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-chatchonk-pink-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-chatchonk-pink-600"></div>
              </label>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-700">Maintenance Mode</p>
                <p className="text-xs text-gray-500">Temporarily disable user access</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  className="sr-only peer"
                  checked={settings.maintenanceMode}
                  onChange={(e) => setSettings({...settings, maintenanceMode: e.target.checked})}
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-red-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-red-600"></div>
              </label>
            </div>

            {settings.maintenanceMode && (
              <div className="p-3 bg-red-50 border border-red-200 rounded-md">
                <div className="flex items-center">
                  <AlertTriangle className="h-4 w-4 text-red-600 mr-2" />
                  <span className="text-sm text-red-800">Maintenance mode is enabled</span>
                </div>
                <p className="text-xs text-red-600 mt-1">Users cannot access the system</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* System Information */}
      <Card>
        <CardHeader>
          <CardTitle>System Information</CardTitle>
          <CardDescription>
            Current system status and version information
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-sm font-medium text-gray-700">Version</p>
              <p className="text-lg font-semibold">v1.2.3</p>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Environment</p>
              <Badge>Production</Badge>
            </div>
            <div>
              <p className="text-sm font-medium text-gray-700">Last Updated</p>
              <p className="text-sm text-gray-600">January 15, 2024</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
