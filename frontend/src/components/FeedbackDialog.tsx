import { useState } from 'react';
import { Button } from './ui/button';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from './ui/dialog';
import { Textarea } from './ui/textarea';
import { Star } from 'lucide-react';

interface FeedbackDialogProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    patientId: string;
    patientName: string;
}

export function FeedbackDialog({ open, onOpenChange, patientId, patientName }: FeedbackDialogProps) {
    const [rating, setRating] = useState(0);
    const [hoveredRating, setHoveredRating] = useState(0);
    const [corrections, setCorrections] = useState('');
    const [submitting, setSubmitting] = useState(false);
    const [submitted, setSubmitted] = useState(false);

    const handleSubmit = async () => {
        if (rating === 0) {
            alert('Please provide a rating');
            return;
        }

        setSubmitting(true);

        try {
            const response = await fetch('http://localhost:8000/api/feedback', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    patient_id: patientId,
                    accuracy_rating: rating,
                    corrections: corrections,
                    summary_quality: rating >= 4 ? 'excellent' : rating >= 3 ? 'good' : 'fair',
                }),
            });

            if (response.ok) {
                setSubmitted(true);
                setTimeout(() => {
                    onOpenChange(false);
                    setSubmitted(false);
                    setRating(0);
                    setCorrections('');
                }, 2000);
            } else {
                alert('Failed to submit feedback');
            }
        } catch (error) {
            console.error('Error submitting feedback:', error);
            alert('Error submitting feedback');
        } finally {
            setSubmitting(false);
        }
    };

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="sm:max-w-[500px]">
                <DialogHeader>
                    <DialogTitle>Rate AI Summary</DialogTitle>
                    <DialogDescription>
                        Help improve the system by rating the AI summary for {patientName}
                    </DialogDescription>
                </DialogHeader>

                {submitted ? (
                    <div className="py-8 text-center">
                        <div className="text-green-600 text-lg font-semibold mb-2">✓ Thank you!</div>
                        <p className="text-sm text-gray-600">
                            Your feedback helps the system learn and improve
                        </p>
                    </div>
                ) : (
                    <>
                        <div className="space-y-4 py-4">
                            {/* Star Rating */}
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Accuracy Rating</label>
                                <div className="flex gap-2">
                                    {[1, 2, 3, 4, 5].map((star) => (
                                        <button
                                            key={star}
                                            type="button"
                                            onClick={() => setRating(star)}
                                            onMouseEnter={() => setHoveredRating(star)}
                                            onMouseLeave={() => setHoveredRating(0)}
                                            className="transition-transform hover:scale-110"
                                        >
                                            <Star
                                                className={`w-8 h-8 ${star <= (hoveredRating || rating)
                                                    ? 'fill-yellow-400 text-yellow-400'
                                                    : 'text-gray-300'
                                                    }`}
                                            />
                                        </button>
                                    ))}
                                </div>
                                <p className="text-xs text-gray-500">
                                    {rating === 0 && 'Click to rate'}
                                    {rating === 1 && 'Poor - Needs significant improvement'}
                                    {rating === 2 && 'Fair - Several issues'}
                                    {rating === 3 && 'Good - Minor improvements needed'}
                                    {rating === 4 && 'Very Good - Mostly accurate'}
                                    {rating === 5 && 'Excellent - Highly accurate'}
                                </p>
                            </div>

                            {/* Corrections */}
                            <div className="space-y-2">
                                <label className="text-sm font-medium">
                                    Corrections or Suggestions (Optional)
                                </label>
                                <Textarea
                                    placeholder="What could be improved? Any specific corrections?"
                                    value={corrections}
                                    onChange={(e: React.ChangeEvent<HTMLTextAreaElement>) => setCorrections(e.target.value)}
                                    rows={4}
                                    className="resize-none"
                                />
                            </div>

                            {/* Learning Impact Notice */}
                            <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                                <p className="text-xs text-blue-800">
                                    <strong>🧠 Self-Learning:</strong> Your feedback directly improves the AI.
                                    The system will use this to optimize prompts and parameters for future analyses.
                                </p>
                            </div>
                        </div>

                        <DialogFooter>
                            <Button
                                variant="outline"
                                onClick={() => onOpenChange(false)}
                                disabled={submitting}
                            >
                                Cancel
                            </Button>
                            <Button onClick={handleSubmit} disabled={submitting || rating === 0}>
                                {submitting ? 'Submitting...' : 'Submit Feedback'}
                            </Button>
                        </DialogFooter>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
