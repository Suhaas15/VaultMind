export default {
    name: 'prompt_template',
    title: 'Prompt Template',
    type: 'document',
    fields: [
        {
            name: 'version',
            type: 'string',
            title: 'Version',
            description: 'Template version (e.g., v1.0, v2.0)',
            validation: Rule => Rule.required()
        },
        {
            name: 'template',
            type: 'text',
            title: 'Template Content',
            description: 'The actual prompt template with placeholders'
        },
        {
            name: 'description',
            type: 'string',
            title: 'Description',
            description: 'What makes this template unique'
        },
        {
            name: 'parameters',
            type: 'object',
            title: 'Claude Parameters',
            fields: [
                { name: 'temperature', type: 'number', title: 'Temperature' },
                { name: 'max_tokens', type: 'number', title: 'Max Tokens' }
            ]
        },
        {
            name: 'avg_rating',
            type: 'number',
            title: 'Average Rating',
            description: 'Average accuracy rating from feedback',
            initialValue: 0
        },
        {
            name: 'usage_count',
            type: 'number',
            title: 'Usage Count',
            description: 'How many times this template has been used',
            initialValue: 0
        },
        {
            name: 'avg_cost',
            type: 'number',
            title: 'Average Cost',
            description: 'Average cost per analysis using this template',
            initialValue: 0
        },
        {
            name: 'active',
            type: 'boolean',
            title: 'Active',
            description: 'Whether this template is currently in use',
            initialValue: false
        },
        {
            name: 'created_at',
            type: 'datetime',
            title: 'Created At'
        },
        {
            name: 'last_used',
            type: 'datetime',
            title: 'Last Used'
        }
    ]
}