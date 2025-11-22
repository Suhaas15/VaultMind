import { useState } from "react"
import type { Patient } from "@/types"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Lock, Unlock } from "lucide-react"
import { decryptPatient } from "@/lib/api"

interface TokenViewerProps {
    patient: Patient | null
}

export default function TokenViewer({ patient }: TokenViewerProps) {
    const [isDecrypted, setIsDecrypted] = useState(false)
    const [decryptedData, setDecryptedData] = useState<{ name?: string; ssn?: string; dob?: string; address?: string } | null>(null)
    const [decrypting, setDecrypting] = useState(false)

    if (!patient) {
        return (
            <Card className="h-full flex items-center justify-center text-muted-foreground">
                <div className="text-center">
                    <Lock className="h-12 w-12 mx-auto mb-4 opacity-20" />
                    <p>Select a patient to view secure details</p>
                </div>
            </Card>
        )
    }

    return (
        <Card className="h-full flex flex-col">
            <CardHeader className="border-b bg-muted/50">
                <div className="flex items-center justify-between">
                    <div>
                        <CardTitle className="flex items-center gap-2">
                            {patient.name_token}
                            <Badge variant="outline" className="font-mono text-xs">
                                {patient.id}
                            </Badge>
                        </CardTitle>
                        <CardDescription className="mt-1">
                            {patient.department} • {patient.assigned_doctor}
                        </CardDescription>
                    </div>
                    <Button
                        variant="outline"
                        size="sm"
                        className="gap-2"
                        onClick={async () => {
                            if (!isDecrypted && patient) {
                                setDecrypting(true)
                                try {
                                    const data = await decryptPatient(patient.id)
                                    console.log("Decrypted data received:", data)
                                    setDecryptedData(data)
                                    setIsDecrypted(true)
                                    
                                    // Show warning if some fields are missing
                                    if (!data.name && !data.ssn) {
                                        alert("Warning: Could not decrypt any PII fields. The patient record may not have tokens stored, or Skyflow detokenization failed. Check the backend logs for details.")
                                    }
                                } catch (error: any) {
                                    console.error("Failed to decrypt:", error)
                                    const errorMsg = error?.message || "Failed to decrypt patient data"
                                    alert(`Failed to decrypt patient data: ${errorMsg}. Please check your Skyflow configuration and backend logs.`)
                                    setDecryptedData(null)
                                    setIsDecrypted(false)
                                } finally {
                                    setDecrypting(false)
                                }
                            } else {
                                setIsDecrypted(false)
                                setDecryptedData(null)
                            }
                        }}
                        disabled={decrypting}
                    >
                        {isDecrypted ? <Lock className="h-4 w-4" /> : <Unlock className="h-4 w-4" />}
                        {decrypting ? "Decrypting..." : isDecrypted ? "Encrypt PII" : "Decrypt PII"}
                    </Button>
                </div>
            </CardHeader>
            <CardContent className="flex-1 p-6 space-y-6">
                <div className="grid grid-cols-2 gap-4">
                    <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Name</label>
                        <div className={`p-2 rounded-md border font-mono text-sm ${isDecrypted ? 'bg-red-50 border-red-200 text-red-900' : 'bg-muted/50'}`}>
                            {isDecrypted ? (decryptedData?.name || "N/A") : patient.name_token}
                        </div>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">SSN</label>
                        <div className={`p-2 rounded-md border font-mono text-sm ${isDecrypted ? 'bg-red-50 border-red-200 text-red-900' : 'bg-muted/50'}`}>
                            {isDecrypted ? (decryptedData?.ssn || "N/A") : patient.ssn_token}
                        </div>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Condition</label>
                        <div className="p-2 rounded-md border bg-background text-sm">
                            {patient.condition}
                        </div>
                    </div>
                    <div className="space-y-1">
                        <label className="text-xs font-medium text-muted-foreground">Status</label>
                        <div className="p-2 rounded-md border bg-background text-sm">
                            {patient.processed ? "Processed" : "Pending"}
                        </div>
                    </div>
                </div>

                <div className="space-y-2">
                    <label className="text-sm font-medium">AI Clinical Summary</label>
                    <div className="rounded-md border bg-muted/30 p-4 text-sm leading-relaxed">
                        {patient.ai_summary || "Waiting for AI analysis..."}
                    </div>
                </div>
            </CardContent>
        </Card>
    )
}
