export default {
    name: 'feedback',
    title: 'Doctor Feedback',
    type: 'document',
    fields: [
        {
            name: 'patient_id',
            type: 'string',
            title: 'Patient ID',
            description: 'Reference to the patient record'
        },
        {
            name: 'doctor_id',
            type: 'string',
            title: 'Doctor ID',
            description: 'ID of the doctor providing feedback'
        },
        {
            name: 'accuracy_rating',
            type: 'number',
            title: 'Accuracy Rating',
            description: 'Rating from 1-5 on AI summary accuracy',
            validation: Rule => Rule.required().min(1).max(5)
        },
        {
            name: 'corrections',
            type: 'text',
            title: 'Corrections/Suggestions',
            description: 'Doctor\'s corrections or suggestions for improvement'
        },
        {
            name: 'summary_quality',
            type: 'string',
            title: 'Summary Quality',
            options: {
                list: [
                    { title: 'Excellent', value: 'excellent' },
                    { title: 'Good', value: 'good' },
                    { title: 'Fair', value: 'fair' },
                    { title: 'Poor', value: 'poor' }
                ]
            }
        },
        {
            name: 'timestamp',
            type: 'datetime',
            title: 'Timestamp',
            description: 'When the feedback was submitted'
        },
        {
            name: 'prompt_version',
            type: 'string',
            title: 'Prompt Version',
            description: 'Which prompt template was used for this analysis'
        }
    ]
}