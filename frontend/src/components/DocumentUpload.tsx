import { useState, useRef } from 'react';
import { Button } from './ui/button';
import { Card } from './ui/card';
import { Upload, FileText, CheckCircle, AlertCircle, X } from 'lucide-react';

interface DetectedEntity {
    type: string;
    value: string;
    confidence: number;
}

export function DocumentUpload({ onClose, onPatientCreated }: { onClose?: () => void; onPatientCreated?: () => void }) {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [result, setResult] = useState<any>(null);
    const [dragActive, setDragActive] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleDrag = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(true);
        } else if (e.type === "dragleave") {
            setDragActive(false);
        }
    };

    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(false);

        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            setFile(e.dataTransfer.files[0]);
            setResult(null);
        }
    };

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setResult(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:8000/api/patients/upload-document', {
                method: 'POST',
                body: formData,
            });

            const data = await response.json();
            setResult(data);

            // Notify parent that a new patient was created
            if (data.status === 'success' && onPatientCreated) {
                onPatientCreated();
            }
        } catch (error) {
            console.error('Upload error:', error);
            setResult({ status: 'error', message: 'Failed to upload document' });
        } finally {
            setUploading(false);
        }
    };

    const reset = () => {
        setFile(null);
        setResult(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = '';
        }
    };

    return (
        <Card className="p-6 h-full flex flex-col border-0 shadow-none bg-transparent">
            {!result ? (
                <>
                    {/* Drag and Drop Zone */}
                    <div
                        className={`border-2 border-dashed rounded-lg p-8 text-center transition-colors ${dragActive
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-300 hover:border-gray-400'
                            }`}
                        onDragEnter={handleDrag}
                        onDragLeave={handleDrag}
                        onDragOver={handleDrag}
                        onDrop={handleDrop}
                    >
                        <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
                        <p className="text-sm font-medium mb-2">
                            {file ? file.name : 'Drag and drop a file here, or click to browse'}
                        </p>
                        <p className="text-xs text-gray-500 mb-4">
                            Supports: TXT, PDF, DOCX (max 10MB)
                        </p>
                        <input
                            ref={fileInputRef}
                            type="file"
                            className="hidden"
                            accept=".txt,.pdf,.docx"
                            onChange={handleFileChange}
                        />
                        <Button
                            variant="outline"
                            onClick={() => fileInputRef.current?.click()}
                            disabled={uploading}
                        >
                            <FileText className="w-4 h-4 mr-2" />
                            Select File
                        </Button>
                    </div>

                    {file && (
                        <div className="mt-4 flex gap-2">
                            <Button onClick={handleUpload} disabled={uploading} className="flex-1">
                                {uploading ? 'Processing...' : 'Upload & Detect PII'}
                            </Button>
                            <Button variant="outline" onClick={reset}>
                                <X className="w-4 h-4" />
                            </Button>
                        </div>
                    )}
                </>
            ) : (
                <>
                    {/* Results */}
                    <div className="flex flex-col h-full max-h-[600px]">
                        {/* Scrollable content area */}
                        <div className="flex-1 overflow-y-auto space-y-4 pr-2">
                            {result.status === 'success' && (
                                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                                    <div className="flex items-start gap-3">
                                        <CheckCircle className="w-5 h-5 text-green-600 mt-0.5" />
                                        <div className="flex-1">
                                            <h4 className="font-semibold text-green-900">Patient Record Created!</h4>
                                            <p className="text-sm text-green-700 mt-1">{result.message}</p>
                                            <p className="text-xs text-green-600 mt-2">
                                                Patient ID: {result.patient_id}
                                            </p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {result.status === 'review_required' && (
                                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className="w-5 h-5 text-yellow-600 mt-0.5" />
                                        <div className="flex-1">
                                            <h4 className="font-semibold text-yellow-900">Manual Review Required</h4>
                                            <p className="text-sm text-yellow-700 mt-1">{result.message}</p>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {result.status === 'insufficient_data' && (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                                    <div className="flex items-start gap-3">
                                        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5" />
                                        <div className="flex-1">
                                            <h4 className="font-semibold text-red-900">Insufficient Data</h4>
                                            <p className="text-sm text-red-700 mt-1">{result.message}</p>
                                            {result.required && (
                                                <p className="text-xs text-red-600 mt-2">
                                                    Required fields missing: {result.required.join(', ')}
                                                </p>
                                            )}
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Detected Entities - Scrollable */}
                            {result.detected_entities && result.detected_entities.length > 0 && (
                                <div>
                                    <h4 className="font-semibold mb-2">Detected PII Entities ({result.detected_entities.length}):</h4>
                                    <div className="space-y-2 max-h-[300px] overflow-y-auto pr-2">
                                        {result.detected_entities.map((entity: DetectedEntity, idx: number) => (
                                            <div
                                                key={idx}
                                                className="flex items-center justify-between bg-gray-50 rounded p-3 border border-gray-200"
                                            >
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-center gap-2">
                                                        <span className="text-xs font-medium text-gray-500 uppercase whitespace-nowrap">
                                                            {entity.type}
                                                        </span>
                                                        <span className="text-sm font-mono truncate">{entity.value}</span>
                                                    </div>
                                                </div>
                                                <div className="text-right ml-2 shrink-0">
                                                    <div className="text-xs text-gray-500">Confidence</div>
                                                    <div className={`text-sm font-semibold ${entity.confidence >= 0.9 ? 'text-green-600' :
                                                        entity.confidence >= 0.7 ? 'text-yellow-600' :
                                                            'text-orange-600'
                                                        }`}>
                                                        {(entity.confidence * 100).toFixed(0)}%
                                                    </div>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Auto-Extracted Info */}
                            {result.auto_extracted && (
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                                    <h4 className="font-semibold text-blue-900 mb-2">Auto-Extracted Information:</h4>
                                    <div className="text-sm text-blue-800 space-y-1">
                                        <p><strong>Condition:</strong> {result.auto_extracted.condition}</p>
                                        <p><strong>Total PII Found:</strong> {result.auto_extracted.pii_count || result.auto_extracted.total_pii_found || result.detected_entities?.length || 0}</p>
                                    </div>
                                </div>
                            )}
                        </div>

                        {/* Sticky buttons at bottom */}
                        <div className="flex gap-3 pt-4 border-t border-gray-200 mt-4 shrink-0">
                            <Button onClick={reset} variant="outline" className="flex-1">
                                Upload Another
                            </Button>
                            <Button onClick={onClose} className="flex-1">
                                View Patient
                            </Button>
                        </div>
                    </div>
                </>
            )}
        </Card>
    );
}
