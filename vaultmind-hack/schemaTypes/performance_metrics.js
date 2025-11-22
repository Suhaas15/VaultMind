export default {
    name: 'performance_metrics',
    title: 'Performance Metrics',
    type: 'document',
    fields: [
        {
            name: 'date',
            type: 'datetime',
            title: 'Date',
            description: 'Date of this metrics snapshot'
        },
        {
            name: 'total_processed',
            type: 'number',
            title: 'Total Processed',
            description: 'Number of patients processed on this date'
        },
        {
            name: 'avg_accuracy',
            type: 'number',
            title: 'Average Accuracy',
            description: 'Average accuracy rating from feedback'
        },
        {
            name: 'avg_cost',
            type: 'number',
            title: 'Average Cost',
            description: 'Average cost per analysis in USD'
        },
        {
            name: 'avg_duration_ms',
            type: 'number',
            title: 'Average Duration (ms)',
            description: 'Average processing time in milliseconds'
        },
        {
            name: 'prompt_version',
            type: 'string',
            title: 'Prompt Version',
            description: 'Primary prompt version used on this date'
        }
    ]
}