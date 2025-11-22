export interface LabResult {
    test_name: string
    value: string
    date: string
    normal_range: string
}

export interface Patient {
    id: string
    name_token: string
    ssn_token: string
    dob_token: string
    address_token?: string
    condition: string
    department?: string
    priority?: string
    assigned_doctor?: string
    lab_results?: LabResult[]
    processed: boolean
    processedAt?: string
    processing_duration_ms?: number
    ai_summary?: string
    tokens_used?: {
        input: number
        output: number
    }
    cost_usd?: number
    claude_model?: string
}

export interface AuditLog {
    id: string
    timestamp: string
    user: string
    action: string
    patientId: string
    details: string
}
