import type { Patient } from "@/types"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Lock, CheckCircle2, Clock, Star, ArrowRight, MoreHorizontal } from "lucide-react"
import { useState } from "react"
import { FeedbackDialog } from "./FeedbackDialog"
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
interface PatientListProps {
    patients: Patient[]
    onSelectPatient: (patient: Patient) => void
    selectedPatientId?: string | null
}
export default function PatientList({ patients, onSelectPatient, selectedPatientId }: PatientListProps) {
    const [feedbackPatient, setFeedbackPatient] = useState<Patient | null>(null);
    if (patients.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center h-full text-muted-foreground py-12">
                <div className="bg-muted/50 p-4 rounded-full mb-4">
                    <Clock className="h-8 w-8 opacity-50" />
                </div>
                <p className="font-medium">No patients processed yet</p>
                <p className="text-sm mt-1">Upload a document to get started</p>
            </div>
        )
    }
    return (
        <>
            <div className="divide-y divide-border">
                {patients.map((patient) => (
                    <div
                        key={patient.id}
                        className={`group flex items-center justify-between p-4 transition-all duration-200 cursor-pointer border-l-4 ${selectedPatientId === patient.id
                                ? 'bg-primary/5 border-primary'
                                : 'hover:bg-muted/50 border-transparent'
                            }`}
                        onClick={() => onSelectPatient(patient)}
                    >
                        <div className="flex items-center gap-4 flex-1">
                            <div className={`h-10 w-10 rounded-full flex items-center justify-center shrink-0 transition-colors ${patient.processed
                                ? 'bg-emerald-50 text-emerald-600 dark:bg-emerald-900/20'
                                : 'bg-amber-50 text-amber-600 dark:bg-amber-900/20'
                                }`}>
                                {patient.processed ? <CheckCircle2 className="h-5 w-5" /> : <Clock className="h-5 w-5 animate-pulse" />}
                            </div>
                            <div className="min-w-0 flex-1">
                                <div className="flex items-center gap-2 mb-1">
                                    <span className={`font-semibold text-sm truncate ${selectedPatientId === patient.id ? 'text-primary' : 'text-foreground'}`}>
                                        {patient.name_token}
                                    </span>
                                    <Badge variant="secondary" className="h-5 px-1.5 text-[10px] font-mono tracking-tight text-muted-foreground bg-muted/50">
                                        <Lock className="h-2.5 w-2.5 mr-1" />
                                        Encrypted
                                    </Badge>
                                    {patient.priority === 'URGENT' && (
                                        <Badge variant="destructive" className="h-5 px-1.5 text-[10px]">
                                            URGENT
                                        </Badge>
                                    )}
                                </div>
                                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                                    <span className="font-medium">{patient.department || 'General'}</span>
                                    <span className="w-1 h-1 rounded-full bg-muted-foreground/30" />
                                    <span className="truncate">{patient.condition}</span>
                                </div>
                            </div>
                        </div>
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                            {patient.processed && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 w-8 p-0 text-muted-foreground hover:text-amber-500"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        setFeedbackPatient(patient);
                                    }}
                                    title="Rate AI Analysis"
                                >
                                    <Star className="h-4 w-4" />
                                </Button>
                            )}
                            <DropdownMenu>
                                <DropdownMenuTrigger asChild>
                                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                                        <MoreHorizontal className="h-4 w-4" />
                                    </Button>
                                </DropdownMenuTrigger>
                                <DropdownMenuContent align="end">
                                    <DropdownMenuItem onClick={() => onSelectPatient(patient)}>
                                        View Details
                                    </DropdownMenuItem>
                                    <DropdownMenuItem>Export PDF</DropdownMenuItem>
                                    <DropdownMenuItem className="text-destructive">Delete Record</DropdownMenuItem>
                                </DropdownMenuContent>
                            </DropdownMenu>
                            <div className={`ml-2 ${selectedPatientId === patient.id ? 'text-primary' : 'text-muted-foreground/30'}`}>
                                <ArrowRight className="h-4 w-4" />
                            </div>
                        </div>
                    </div>
                ))}
            </div>
            {feedbackPatient && (
                <FeedbackDialog
                    open={!!feedbackPatient}
                    onOpenChange={(open) => !open && setFeedbackPatient(null)}
                    patientId={feedbackPatient.id}
                    patientName={feedbackPatient.name_token}
                />
            )}
        </>
    )
}