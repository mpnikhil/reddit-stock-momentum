import React, { useState } from 'react';
import { Settings as SettingsIcon, RefreshCw, Download, Activity, AlertTriangle } from 'lucide-react';
import { useApi } from '../hooks/useApi';
import { apiClient } from '../utils/api';
import LoadingSpinner from '../components/LoadingSpinner';
import ErrorMessage from '../components/ErrorMessage';
import StatCard from '../components/StatCard';

export default function Settings() {
  const [triggeringJob, setTriggeringJob] = useState<string | null>(null);
  const [exportFormat, setExportFormat] = useState<'json' | 'csv'>('json');
  const [exportDays, setExportDays] = useState(7);

  const { data: schedulerStatus, loading: schedulerLoading, refetch: refetchScheduler } = useApi(
    () => apiClient.getSchedulerStatus()
  );

  const { data: subredditsData, loading: subredditsLoading } = useApi(
    () => apiClient.getSubreddits()
  );

  const { data: systemStats, loading: statsLoading } = useApi(
    () => apiClient.getSystemStats()
  );

  const handleTriggerJob = async (jobId: string) => {
    try {
      setTriggeringJob(jobId);
      await apiClient.triggerSchedulerJob(jobId);
      // Refresh scheduler status after triggering
      setTimeout(() => {
        refetchScheduler();
        setTriggeringJob(null);
      }, 1000);
    } catch (error) {
      console.error('Failed to trigger job:', error);
      setTriggeringJob(null);
    }
  };

  const handleExportData = async () => {
    try {
      const data = await apiClient.exportTrendingData(exportDays, exportFormat);
      
      if (exportFormat === 'csv') {
        // Handle CSV download
        const url = window.URL.createObjectURL(data);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trending_stocks_${exportDays}d.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      } else {
        // Handle JSON download
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `trending_stocks_${exportDays}d.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        window.URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to export data:', error);
    }
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
        <p className="mt-2 text-gray-600">
          System configuration and maintenance tools
        </p>
      </div>

      {/* System Status */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">System Status</h2>
        
        {statsLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard
              title="Reddit API Status"
              value={systemStats?.reddit_api_status?.error ? 'Error' : 'Active'}
              subtitle={systemStats?.reddit_api_status?.remaining ? 
                `${systemStats.reddit_api_status.remaining} requests remaining` : 
                undefined
              }
              icon={Activity}
              color={systemStats?.reddit_api_status?.error ? 'danger' : 'success'}
            />
            
            <StatCard
              title="Scheduler Status"
              value={schedulerStatus?.scheduler_running ? 'Running' : 'Stopped'}
              subtitle={schedulerStatus ? `${schedulerStatus.total_jobs} jobs` : undefined}
              icon={RefreshCw}
              color={schedulerStatus?.scheduler_running ? 'success' : 'warning'}
            />
            
            <StatCard
              title="Active Subreddits"
              value={subredditsData?.active_subreddits || 0}
              subtitle={`of ${subredditsData?.total_subreddits || 0} total`}
              icon={SettingsIcon}
              color="primary"
            />
            
            <StatCard
              title="Data Freshness"
              value="30min"
              subtitle="Update interval"
              icon={RefreshCw}
              color="primary"
            />
          </div>
        )}
      </div>

      {/* Scheduler Management */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Background Jobs</h2>
        
        {schedulerLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : schedulerStatus ? (
          <div className="space-y-4">
            {schedulerStatus.jobs.map((job) => (
              <div key={job.id} className="card">
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{job.name}</h3>
                    <div className="flex items-center space-x-4 text-sm text-gray-500 mt-1">
                      <span>ID: {job.id}</span>
                      <span>Trigger: {job.trigger}</span>
                      {job.next_run_time && (
                        <span>Next run: {new Date(job.next_run_time).toLocaleString()}</span>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center space-x-3">
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                      job.running ? 'bg-success-100 text-success-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {job.running ? 'Active' : 'Idle'}
                    </span>
                    
                    <button
                      onClick={() => handleTriggerJob(job.id)}
                      disabled={triggeringJob === job.id}
                      className="btn-secondary flex items-center space-x-1 text-xs"
                    >
                      {triggeringJob === job.id ? (
                        <LoadingSpinner size="sm" />
                      ) : (
                        <RefreshCw className="h-3 w-3" />
                      )}
                      <span>Trigger</span>
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <ErrorMessage error="Failed to load scheduler status" />
        )}
      </div>

      {/* Monitored Subreddits */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Monitored Subreddits</h2>
        
        {subredditsLoading ? (
          <div className="flex justify-center py-8">
            <LoadingSpinner />
          </div>
        ) : subredditsData ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {subredditsData.subreddits.map((subreddit) => (
              <div key={subreddit.name} className="card">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-medium text-gray-900">{subreddit.display_name}</h3>
                  <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
                    subreddit.is_active ? 'bg-success-100 text-success-800' : 'bg-gray-100 text-gray-800'
                  }`}>
                    {subreddit.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                
                <div className="space-y-1 text-sm text-gray-600">
                  {subreddit.subscribers && (
                    <p>Subscribers: {subreddit.subscribers.toLocaleString()}</p>
                  )}
                  <p>Posts collected: {subreddit.total_posts_collected}</p>
                  <p>Recent (7d): {subreddit.recent_posts_7d}</p>
                  {subreddit.last_scraped && (
                    <p>Last scraped: {new Date(subreddit.last_scraped).toLocaleDateString()}</p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <ErrorMessage error="Failed to load subreddits data" />
        )}
      </div>

      {/* Data Export */}
      <div>
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Data Export</h2>
        
        <div className="card">
          <div className="flex flex-col sm:flex-row sm:items-end sm:space-x-4 space-y-4 sm:space-y-0">
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Period
              </label>
              <select
                value={exportDays}
                onChange={(e) => setExportDays(Number(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value={1}>Last 1 day</option>
                <option value={3}>Last 3 days</option>
                <option value={7}>Last 7 days</option>
                <option value={14}>Last 14 days</option>
                <option value={30}>Last 30 days</option>
              </select>
            </div>
            
            <div className="flex-1">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Format
              </label>
              <select
                value={exportFormat}
                onChange={(e) => setExportFormat(e.target.value as 'json' | 'csv')}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                <option value="json">JSON</option>
                <option value="csv">CSV</option>
              </select>
            </div>
            
            <button
              onClick={handleExportData}
              className="btn-primary flex items-center space-x-2"
            >
              <Download className="h-4 w-4" />
              <span>Export Data</span>
            </button>
          </div>
          
          <p className="mt-3 text-sm text-gray-600">
            Export trending stocks data for analysis in external tools.
          </p>
        </div>
      </div>

      {/* Configuration Notice */}
      <div className="card bg-warning-50 border-warning-200">
        <div className="flex items-start">
          <AlertTriangle className="h-5 w-5 text-warning-600 mt-0.5" />
          <div className="ml-3">
            <h3 className="text-sm font-medium text-warning-800">Configuration Required</h3>
            <p className="mt-1 text-sm text-warning-700">
              To collect data from Reddit, you need to configure your Reddit API credentials. 
              Create a Reddit app at <a href="https://www.reddit.com/prefs/apps" target="_blank" rel="noopener noreferrer" className="underline">reddit.com/prefs/apps</a> 
              and add your credentials to <code>backend/config/config.yaml</code>.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}