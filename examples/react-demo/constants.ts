import { Tool } from './types';

// This mocks the "Suggester" database/index
export const AVAILABLE_TOOLS: Tool[] = [
  {
    id: 'export_csv',
    name: 'export_csv',
    description: 'Exports current dataset or query results to a CSV file format.',
    keywords: ['export', 'csv', 'save data', 'download', 'excel', 'spreadsheet'],
    category: 'data'
  },
  {
    id: 'generate_report',
    name: 'generate_report',
    description: 'Compiles a comprehensive PDF report based on active metrics and charts.',
    keywords: ['report', 'pdf', 'summary', 'overview', 'document', 'briefing'],
    category: 'data'
  },
  {
    id: 'send_email',
    name: 'send_email',
    description: 'Dispatches an email to specified recipients via the configured SMTP gateway.',
    keywords: ['email', 'send', 'mail', 'message', 'notify', 'alert'],
    category: 'communication'
  },
  {
    id: 'query_db',
    name: 'query_sql',
    description: 'Executes a raw SQL query against the connected production database.',
    keywords: ['query', 'sql', 'database', 'select', 'fetch', 'records'],
    category: 'system'
  },
  {
    id: 'visualize_chart',
    name: 'plot_chart',
    description: 'Generates a visualization (bar, line, scatter) from provided data points.',
    keywords: ['chart', 'plot', 'graph', 'visualize', 'trend', 'bar', 'line'],
    category: 'utility'
  },
  {
    id: 'schedule_task',
    name: 'schedule_cron',
    description: 'Schedules a background task to run at a specific time or interval.',
    keywords: ['schedule', 'time', 'cron', 'later', 'reminder', 'timer'],
    category: 'utility'
  }
];

export const SUGGESTION_DEBOUNCE_MS = 100;
