from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from .sanity_service import sanity_service
class MetricsService:
    def __init__(self):
        self.sanity = sanity_service
    async def store_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        feedback_doc = {
            "_type": "feedback",
            "patient_id": feedback_data["patient_id"],
            "doctor_id": feedback_data.get("doctor_id", "unknown"),
            "accuracy_rating": feedback_data["accuracy_rating"],
            "corrections": feedback_data.get("corrections", ""),
            "summary_quality": feedback_data.get("summary_quality", "good"),
            "timestamp": feedback_data.get("timestamp", datetime.utcnow().isoformat()),
            "prompt_version": feedback_data.get("prompt_version", "v1.0")
        }
        result = self.sanity.create_document("feedback", feedback_doc)
        await self._update_prompt_metrics(feedback_doc["prompt_version"], feedback_doc["accuracy_rating"])
        return result
    async def _update_prompt_metrics(self, prompt_version: str, rating: int):
        metrics = self.sanity.query(
            f'*[_type=="prompt_template" && version=="{prompt_version}"][0]'
        )
        if metrics:
            current_count = metrics.get("usage_count", 0)
            current_avg = metrics.get("avg_rating", 0)
            new_avg = ((current_avg * current_count) + rating) / (current_count + 1)
            self.sanity.update_document(metrics["_id"], {
                "usage_count": current_count + 1,
                "avg_rating": new_avg,
                "last_used": datetime.utcnow().isoformat()
            })
    def get_feedback_stats(self, days: int = 30) -> Dict[str, Any]:
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = f'*[_type=="feedback" && timestamp > "{cutoff_date}"] | order(timestamp desc)'
        feedbacks = self.sanity.query(query)
        if not feedbacks:
            return {
                "total_feedback": 0,
                "avg_rating": 0,
                "trend": "insufficient_data"
            }
        total = len(feedbacks)
        avg_rating = sum(f.get("accuracy_rating", 0) for f in feedbacks) / total
        mid_point = total // 2
        if mid_point > 0:
            first_half_avg = sum(f.get("accuracy_rating", 0) for f in feedbacks[:mid_point]) / mid_point
            second_half_avg = sum(f.get("accuracy_rating", 0) for f in feedbacks[mid_point:]) / (total - mid_point)
            trend = "improving" if second_half_avg > first_half_avg else "stable" if second_half_avg == first_half_avg else "declining"
        else:
            trend = "insufficient_data"
        quality_dist = {
            "excellent": sum(1 for f in feedbacks if f.get("accuracy_rating", 0) == 5),
            "good": sum(1 for f in feedbacks if f.get("accuracy_rating", 0) == 4),
            "fair": sum(1 for f in feedbacks if f.get("accuracy_rating", 0) == 3),
            "poor": sum(1 for f in feedbacks if f.get("accuracy_rating", 0) <= 2)
        }
        return {
            "total_feedback": total,
            "avg_rating": round(avg_rating, 2),
            "trend": trend,
            "quality_distribution": quality_dist,
            "period_days": days
        }
    def get_prompt_performance(self) -> List[Dict[str, Any]]:
        query = '*[_type=="prompt_template"] | order(avg_rating desc)'
        templates = self.sanity.query(query)
        return [
            {
                "version": t.get("version"),
                "avg_rating": t.get("avg_rating", 0),
                "usage_count": t.get("usage_count", 0),
                "avg_cost": t.get("avg_cost", 0),
                "active": t.get("active", False),
                "last_used": t.get("last_used")
            }
            for t in templates
        ]
    async def record_performance_metrics(self, metrics_data: Dict[str, Any]):
        metrics_doc = {
            "_type": "performance_metrics",
            "date": datetime.utcnow().isoformat(),
            "total_processed": metrics_data.get("total_processed", 0),
            "avg_accuracy": metrics_data.get("avg_accuracy", 0),
            "avg_cost": metrics_data.get("avg_cost", 0),
            "avg_duration_ms": metrics_data.get("avg_duration_ms", 0),
            "prompt_version": metrics_data.get("prompt_version", "v1.0")
        }
        return self.sanity.create_document("performance_metrics", metrics_doc)
    def get_improvement_trend(self, days: int = 30) -> Dict[str, Any]:
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).isoformat()
        query = f'*[_type=="performance_metrics" && date > "{cutoff_date}"] | order(date asc)'
        metrics = self.sanity.query(query)
        if not metrics:
            return {"trend": "insufficient_data", "data_points": []}
        first_metric = metrics[0]
        last_metric = metrics[-1]
        accuracy_improvement = (
            ((last_metric.get("avg_accuracy", 0) - first_metric.get("avg_accuracy", 0)) 
             / first_metric.get("avg_accuracy", 1)) * 100
        ) if first_metric.get("avg_accuracy", 0) > 0 else 0
        cost_reduction = (
            ((first_metric.get("avg_cost", 0) - last_metric.get("avg_cost", 0)) 
             / first_metric.get("avg_cost", 1)) * 100
        ) if first_metric.get("avg_cost", 0) > 0 else 0
        speed_improvement = (
            ((first_metric.get("avg_duration_ms", 0) - last_metric.get("avg_duration_ms", 0)) 
             / first_metric.get("avg_duration_ms", 1)) * 100
        ) if first_metric.get("avg_duration_ms", 0) > 0 else 0
        return {
            "period_days": days,
            "accuracy_improvement_pct": round(accuracy_improvement, 2),
            "cost_reduction_pct": round(cost_reduction, 2),
            "speed_improvement_pct": round(speed_improvement, 2),
            "data_points": [
                {
                    "date": m.get("date"),
                    "accuracy": m.get("avg_accuracy"),
                    "cost": m.get("avg_cost"),
                    "duration_ms": m.get("avg_duration_ms")
                }
                for m in metrics
            ]
        }
metrics_service = MetricsService()