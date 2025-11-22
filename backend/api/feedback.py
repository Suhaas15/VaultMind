from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
from ..services.metrics_service import metrics_service
from ..services.prompt_service import prompt_service
router = APIRouter()
class FeedbackSubmission(BaseModel):
    patient_id: str
    doctor_id: Optional[str] = "anonymous"
    accuracy_rating: int  
    corrections: Optional[str] = ""
    summary_quality: Optional[str] = "good"  
@router.post("/")
async def submit_feedback(feedback: FeedbackSubmission):
    if feedback.accuracy_rating < 1 or feedback.accuracy_rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5")
    feedback_data = {
        "patient_id": feedback.patient_id,
        "doctor_id": feedback.doctor_id,
        "accuracy_rating": feedback.accuracy_rating,
        "corrections": feedback.corrections,
        "summary_quality": feedback.summary_quality,
        "timestamp": datetime.utcnow().isoformat()
    }
    result = await metrics_service.store_feedback(feedback_data)
    return {
        "status": "success",
        "message": "Feedback recorded. Thank you for helping improve the system!",
        "feedback_id": result.get("_id"),
        "learning_impact": "This feedback will be used to optimize future AI summaries"
    }
@router.get("/stats")
async def get_feedback_stats(days: int = 30):
    stats = metrics_service.get_feedback_stats(days=days)
    return {
        **stats,
        "interpretation": _interpret_stats(stats)
    }
@router.get("/prompts/performance")
async def get_prompt_performance():
    performance = metrics_service.get_prompt_performance()
    if isinstance(performance, list):
        performance_dict = {item.get('version', f'v{i}'): item for i, item in enumerate(performance)}
    else:
        performance_dict = performance
    return performance_dict
@router.get("/improvement-trend")
async def get_improvement_trend(days: int = 30):
    trend = metrics_service.get_improvement_trend(days=days)
    return {
        **trend,
        "summary": _summarize_trend(trend)
    }
@router.post("/prompts/evolve")
async def evolve_prompts():
    result = await prompt_service.evolve_prompts()
    return {
        "status": "analysis_complete",
        **result
    }
def _interpret_stats(stats: Dict[str, Any]) -> str:
    if stats.get("total_feedback", 0) == 0:
        return "No feedback data available yet. Start submitting feedback to see improvements!"
    avg_rating = stats.get("avg_rating", 0)
    trend = stats.get("trend", "unknown")
    if avg_rating >= 4.5:
        quality = "excellent"
    elif avg_rating >= 3.5:
        quality = "good"
    elif avg_rating >= 2.5:
        quality = "fair"
    else:
        quality = "needs improvement"
    interpretation = f"System performance is {quality} (avg rating: {avg_rating:.2f}/5). "
    if trend == "improving":
        interpretation += "📈 The system is actively improving based on your feedback!"
    elif trend == "stable":
        interpretation += "➡️ Performance is stable. Continue providing feedback for further improvements."
    elif trend == "declining":
        interpretation += "⚠️ Performance has declined. The system is analyzing patterns to recover."
    return interpretation
def _summarize_trend(trend: Dict[str, Any]) -> str:
    if trend.get("trend") == "insufficient_data":
        return "Not enough data to show trends yet. Process more patients to see improvements."
    accuracy_imp = trend.get("accuracy_improvement_pct", 0)
    cost_red = trend.get("cost_reduction_pct", 0)
    speed_imp = trend.get("speed_improvement_pct", 0)
    summary = f"Over the last {trend.get('period_days')} days: "
    improvements = []
    if accuracy_imp > 5:
        improvements.append(f"accuracy improved by {accuracy_imp:.1f}%")
    if cost_red > 5:
        improvements.append(f"costs reduced by {cost_red:.1f}%")
    if speed_imp > 5:
        improvements.append(f"processing speed improved by {speed_imp:.1f}%")
    if improvements:
        summary += ", ".join(improvements) + ". 🎉"
    else:
        summary += "performance is stable. Continue monitoring for optimization opportunities."
    return summary