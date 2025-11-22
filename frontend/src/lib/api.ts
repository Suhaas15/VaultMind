import type { Patient } from "@/types"
const API_URL = "http://localhost:8000/api"
export async function getPatients(): Promise<Patient[]> {
    const response = await fetch(`${API_URL}/patients`)
    if (!response.ok) {
        throw new Error("Failed to fetch patients")
    }
    const data = await response.json()
    return data.patients || []
}
export async function getStats() {
    const response = await fetch(`${API_URL}/feedback/stats`)
    if (!response.ok) {
        throw new Error("Failed to fetch stats")
    }
    return response.json()
}
export async function getImprovementTrend() {
    const response = await fetch(`${API_URL}/feedback/improvement-trend`)
    if (!response.ok) {
        throw new Error("Failed to fetch improvement trend")
    }
    return response.json()
}
export async function resetSystem() {
    const response = await fetch(`${API_URL}/patients/reset`, {
        method: 'DELETE'
    })
    if (!response.ok) {
        throw new Error("Failed to reset system")
    }
    return response.json()
}
export async function decryptPatient(patientId: string) {
    const response = await fetch(`${API_URL}/patients/${patientId}/decrypt`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({})
    })
    if (!response.ok) {
        throw new Error("Failed to decrypt patient data")
    }
    return response.json()
}