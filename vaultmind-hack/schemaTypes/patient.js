export default {
    name: 'patient',
    title: 'Patient',
    type: 'document',
    fields: [
        { name: 'name_token', type: 'string', title: 'Name Token' },
        { name: 'ssn_token', type: 'string', title: 'SSN Token' },
        { name: 'dob_token', type: 'string', title: 'DOB Token' },
        { name: 'address_token', type: 'string', title: 'Address Token' },
        { name: 'condition', type: 'string', title: 'Condition' },
        { name: 'department', type: 'string', title: 'Department' },
        {
            name: 'priority',
            type: 'string',
            title: 'Priority',
            options: { list: ['NORMAL', 'URGENT'] },
            initialValue: 'NORMAL'
        },
        { name: 'assigned_doctor', type: 'string', title: 'Assigned Doctor', initialValue: 'Unassigned' },
        { name: 'processed', type: 'boolean', title: 'Processed', initialValue: false },
        { name: 'ai_summary', type: 'text', title: 'AI Summary' },
        { name: 'cost_usd', type: 'number', title: 'Cost (USD)' },
        { name: 'claude_model', type: 'string', title: 'Claude Model' },
        { name: 'processedAt', type: 'datetime', title: 'Processed At' },
        { name: 'processing_duration_ms', type: 'number', title: 'Processing Duration (ms)' },
        { name: 'tokens_used', type: 'object', title: 'Tokens Used', fields: [
            { name: 'input', type: 'number', title: 'Input Tokens' },
            { name: 'output', type: 'number', title: 'Output Tokens' }
        ]},
        { name: 'prompt_version', type: 'string', title: 'Prompt Version' },
        // Lab Results - Array of objects
        { 
            name: 'lab_results', 
            type: 'array', 
            title: 'Lab Results', 
            of: [{
                type: 'object',
                fields: [
                    { name: 'test_name', type: 'string', title: 'Test Name' },
                    { name: 'value', type: 'string', title: 'Value' },
                    { name: 'date', type: 'string', title: 'Date' },
                    { name: 'normal_range', type: 'string', title: 'Normal Range' }
                ]
            }]
        },
        // Document Upload fields
        { name: 'original_filename', type: 'string', title: 'Original Filename' },
        { name: 'source', type: 'string', title: 'Source', options: {
            list: ['manual_entry', 'document_upload', 'batch_upload']
        }},
        // PII Detection Confidence Scores (from Skyflow Detect)
        { 
            name: 'name_confidence', 
            type: 'number', 
            title: 'Name Detection Confidence',
            description: 'Confidence score (0-1) for name PII detection',
            validation: Rule => Rule.min(0).max(1)
        },
        { 
            name: 'ssn_confidence', 
            type: 'number', 
            title: 'SSN Detection Confidence',
            description: 'Confidence score (0-1) for SSN PII detection',
            validation: Rule => Rule.min(0).max(1)
        },
        { 
            name: 'dob_confidence', 
            type: 'number', 
            title: 'DOB Detection Confidence',
            description: 'Confidence score (0-1) for date of birth PII detection',
            validation: Rule => Rule.min(0).max(1)
        }
    ]
}
