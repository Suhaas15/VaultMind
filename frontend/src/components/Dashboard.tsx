import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Activity, Shield, Users, FileText, Upload, TrendingUp, Zap, Search, Bell, Trash2 } from "lucide-react"
import PatientList from "@/components/PatientList"
import TokenViewer from "@/components/TokenViewer"
import { DocumentUpload } from "@/components/DocumentUpload"
import type { Patient } from "@/types"
import { socket, connectSocket, disconnectSocket } from "@/lib/socket"
import { getPatients, getStats, getImprovementTrend, resetSystem } from "@/lib/api"
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog"
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"

export default function Dashboard() {
    const [patients, setPatients] = useState<Patient[]>([])
    const [selectedPatient, setSelectedPatient] = useState<Patient | null>(null)
    const [uploadDialogOpen, setUploadDialogOpen] = useState(false)
    const [stats, setStats] = useState<any>(null)
    const [trend, setTrend] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        async function fetchData() {
            try {
                const [patientsData, statsData, trendData] = await Promise.all([
                    getPatients(),
                    getStats(),
                    getImprovementTrend()
                ])
                setPatients(patientsData)
                setStats(statsData)
                setTrend(trendData)
            } catch (error) {
                console.error("Failed to fetch dashboard data:", error)
            } finally {
                setLoading(false)
            }
        }

        fetchData()
        connectSocket()

        function onPatientProcessed(data: { patientId: string, patient: Patient }) {
            setPatients(prev => prev.map(p => p.id === data.patientId ? data.patient : p))
            if (selectedPatient?.id === data.patientId) {
                setSelectedPatient(data.patient)
            }
        }

        function onPatientCreated(data: { patient: Patient }) {
            setPatients(prev => [data.patient, ...prev])
        }

        socket.on("patient_processed", onPatientProcessed)
        socket.on("patient_created", onPatientCreated)

        return () => {
            socket.off("patient_processed", onPatientProcessed)
            socket.off("patient_created", onPatientCreated)
            disconnectSocket()
        }
    }, [selectedPatient])

    const refreshPatients = async () => {
        try {
            const patientsData = await getPatients()
            setPatients(patientsData)
        } catch (error) {
            console.error("Failed to refresh patients:", error)
        }
    }

    return (
        <div className="min-h-screen bg-background flex flex-col">
            {/* Top Navigation Bar */}
            <header className="h-16 border-b bg-background/80 backdrop-blur-md sticky top-0 z-50">
                <div className="container h-full mx-auto px-4 flex items-center justify-between">
                    <div className="flex items-center gap-8">
                        <div className="flex items-center gap-2.5">
                            <div className="bg-primary/10 p-2 rounded-xl">
                                <Shield className="h-6 w-6 text-primary" />
                            </div>
                            <div>
                                <h1 className="text-lg font-bold tracking-tight text-foreground">
                                    VaultMind
                                    <span className="text-primary ml-1">Pro</span>
                                </h1>
                                <p className="text-[10px] font-medium text-muted-foreground uppercase tracking-wider">
                                    Medical Intelligence
                                </p>
                            </div>
                        </div>

                        <nav className="hidden md:flex items-center gap-1">
                            <Button variant="ghost" className="text-sm font-medium text-foreground/80 hover:text-primary hover:bg-primary/5">
                                Dashboard
                            </Button>
                            <Button variant="ghost" className="text-sm font-medium text-muted-foreground hover:text-primary hover:bg-primary/5">
                                Patients
                            </Button>
                            <Button variant="ghost" className="text-sm font-medium text-muted-foreground hover:text-primary hover:bg-primary/5">
                                Analytics
                            </Button>
                            <Button variant="ghost" className="text-sm font-medium text-muted-foreground hover:text-primary hover:bg-primary/5">
                                Settings
                            </Button>
                        </nav>
                    </div>

                    <div className="flex items-center gap-4">
                        <div className="relative hidden md:block w-64">
                            <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
                            <Input
                                placeholder="Search patients, tokens..."
                                className="pl-9 bg-muted/50 border-transparent focus:bg-background focus:border-primary/20 transition-all"
                            />
                        </div>

                        <Button variant="ghost" size="icon" className="relative text-muted-foreground hover:text-foreground">
                            <Bell className="h-5 w-5" />
                            <span className="absolute top-2 right-2 h-2 w-2 bg-red-500 rounded-full border-2 border-background" />
                        </Button>

                        <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
                            <DialogTrigger asChild>
                                <Button className="bg-primary hover:bg-primary/90 shadow-lg shadow-primary/20 transition-all hover:scale-[1.02]">
                                    <Upload className="h-4 w-4 mr-2" />
                                    Upload Record
                                </Button>
                            </DialogTrigger>
                            <DialogContent className="max-w-2xl max-h-[90vh] flex flex-col">
                                <DialogHeader className="shrink-0">
                                    <DialogTitle>Upload Medical Document</DialogTitle>
                                </DialogHeader>
                                <div className="flex-1 overflow-hidden min-h-0">
                                    <DocumentUpload
                                        onClose={() => setUploadDialogOpen(false)}
                                        onPatientCreated={refreshPatients}
                                    />
                                </div>
                            </DialogContent>
                        </Dialog>

                        <AlertDialog>
                            <AlertDialogTrigger asChild>
                                <Button variant="destructive" size="icon" className="ml-2" title="Reset System">
                                    <Trash2 className="h-4 w-4" />
                                </Button>
                            </AlertDialogTrigger>
                            <AlertDialogContent>
                                <AlertDialogHeader>
                                    <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
                                    <AlertDialogDescription>
                                        This action cannot be undone. This will permanently delete all patient records from the database.
                                    </AlertDialogDescription>
                                </AlertDialogHeader>
                                <AlertDialogFooter>
                                    <AlertDialogCancel>Cancel</AlertDialogCancel>
                                    <AlertDialogAction onClick={async () => {
                                        try {
                                            await resetSystem()
                                            setPatients([])
                                            setSelectedPatient(null)
                                            setStats(null)
                                            setTrend(null)
                                        } catch (error) {
                                            console.error("Failed to reset system:", error)
                                        }
                                    }}>
                                        Yes, Delete All Data
                                    </AlertDialogAction>
                                </AlertDialogFooter>
                            </AlertDialogContent>
                        </AlertDialog>
                    </div>
                </div>
            </header>

            <main className="flex-1 container mx-auto px-4 py-8 space-y-8">
                {/* Stats Row */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <StatsCard
                        title="Active Patients"
                        value={patients.length.toString()}
                        label="Total records processed"
                        icon={Users}
                        trend="+12% this week"
                        trendUp={true}
                        color="blue"
                    />
                    <StatsCard
                        title="AI Accuracy"
                        value={stats?.avg_rating ? `${stats.avg_rating.toFixed(1)}/5.0` : 'N/A'}
                        label="Based on doctor feedback"
                        icon={Activity}
                        trend={stats?.trend === 'improving' ? "Improving" : "Stable"}
                        trendUp={stats?.trend === 'improving'}
                        color="green"
                    />
                    <StatsCard
                        title="Processing Speed"
                        value={trend?.speed_improvement_pct ? `+${trend.speed_improvement_pct.toFixed(1)}%` : '0%'}
                        label="Latency reduction"
                        icon={Zap}
                        trend="Optimizing"
                        trendUp={true}
                        color="amber"
                    />
                    <StatsCard
                        title="Cost Efficiency"
                        value={trend?.cost_reduction_pct ? `-${trend.cost_reduction_pct.toFixed(1)}%` : '0%'}
                        label="Token usage optimization"
                        icon={FileText}
                        trend="Saving costs"
                        trendUp={true}
                        color="purple"
                    />
                </div>

                {/* Main Content Grid */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 h-[calc(100vh-12rem)] min-h-[600px]">
                    {/* Patient List Column */}
                    <Card className="lg:col-span-7 xl:col-span-8 flex flex-col border-none shadow-xl bg-card/50 backdrop-blur-sm ring-1 ring-border">
                        <CardHeader className="border-b px-6 py-4 flex flex-row items-center justify-between">
                            <div>
                                <CardTitle className="text-base font-semibold">Patient Records</CardTitle>
                                <p className="text-xs text-muted-foreground mt-1">Real-time incoming data stream</p>
                            </div>
                            <div className="flex items-center gap-2">
                                <Badge variant="outline" className="bg-background/50">
                                    {patients.length} Records
                                </Badge>
                            </div>
                        </CardHeader>
                        <div className="flex-1 overflow-auto">
                            {loading ? (
                                <div className="flex flex-col items-center justify-center h-full space-y-4">
                                    <div className="relative">
                                        <div className="h-12 w-12 rounded-full border-4 border-primary/20 border-t-primary animate-spin" />
                                        <div className="absolute inset-0 flex items-center justify-center">
                                            <Shield className="h-4 w-4 text-primary/50" />
                                        </div>
                                    </div>
                                    <p className="text-sm text-muted-foreground animate-pulse">
                                        Syncing secure vault...
                                    </p>
                                </div>
                            ) : (
                                <PatientList
                                    patients={patients}
                                    onSelectPatient={setSelectedPatient}
                                    selectedPatientId={selectedPatient?.id}
                                />
                            )}
                        </div>
                    </Card>

                    {/* Detail View Column */}
                    <div className="lg:col-span-5 xl:col-span-4 h-full">
                        <TokenViewer patient={selectedPatient} />
                    </div>
                </div>
            </main>
        </div>
    )
}

function StatsCard({ title, value, label, icon: Icon, trend, trendUp, color }: any) {
    const colorStyles = {
        blue: "text-blue-600 bg-blue-50 dark:bg-blue-900/20",
        green: "text-emerald-600 bg-emerald-50 dark:bg-emerald-900/20",
        amber: "text-amber-600 bg-amber-50 dark:bg-amber-900/20",
        purple: "text-purple-600 bg-purple-50 dark:bg-purple-900/20",
    }

    return (
        <Card className="border-none shadow-sm hover:shadow-md transition-all bg-card/50 backdrop-blur-sm ring-1 ring-border">
            <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className={`p-2.5 rounded-xl ${colorStyles[color as keyof typeof colorStyles]}`}>
                        <Icon className="h-5 w-5" />
                    </div>
                    {trend && (
                        <Badge variant="secondary" className={`font-medium ${trendUp ? 'text-emerald-600 bg-emerald-50' : 'text-zinc-600 bg-zinc-100'}`}>
                            {trendUp && <TrendingUp className="h-3 w-3 mr-1" />}
                            {trend}
                        </Badge>
                    )}
                </div>
                <div>
                    <h3 className="text-2xl font-bold tracking-tight text-foreground">{value}</h3>
                    <p className="text-sm font-medium text-muted-foreground mt-1">{title}</p>
                    <p className="text-xs text-muted-foreground/60 mt-2">{label}</p>
                </div>
            </CardContent>
        </Card>
    )
}
