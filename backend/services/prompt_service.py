from typing import Dict, List, Optional, Any
from datetime import datetime
import random
from .sanity_service import sanity_service
class PromptService:
    PROMPT_TEMPLATES = {
        "v1.0": {
            "template": "Patient Name: {name}\nCondition: {condition}\nDepartment: {department}\nLab Results:\n{lab_results}\n\nPlease provide a clinical summary.",
            "description": "Original baseline prompt",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        "v2.0": {
            "template": "Analyze the following patient data:\nName: {name}\nCondition: {condition}\nDepartment: {department}\nLabs: {lab_results}\n\nProvide a structured analysis including: 1. Key Findings 2. Diagnosis 3. Plan.",
            "description": "Enhanced with structured analysis requirements",
            "parameters": {
                "temperature": 0.6,
                "max_tokens": 600
            }
        },
        "v3.0": {
            "template": "Patient: {name}\nPresenting Condition: {condition}\nDept: {department}\n\nLabs:\n{lab_results}\n\nGenerate a SOAP note (Subjective, Objective, Assessment, Plan) for this patient.",
            "description": "SOAP format for structured output",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 700
            }
        },
        "v4.0": {
            "template": "<patient>\n<name>{name}</name>\n<condition>{condition}</condition>\n<department>{department}</department>\n<labs>\n{lab_results}\n</labs>\n</patient>\n\nPlease analyze this patient data and provide a comprehensive clinical assessment in XML format.",
            "description": "XML-structured prompt with few-shot example (Anthropic Best Practices)",
            "parameters": {
                "temperature": 0.4,
                "max_tokens": 800
            }
        }
    }
    def __init__(self):
        self.sanity = sanity_service
        self._initialize_templates()
    def _initialize_templates(self):
        for version, config in self.PROMPT_TEMPLATES.items():
            existing = self.sanity.query(
                f'*[_type=="prompt_template" && version=="{version}"][0]'
            )
            if not existing:
                self.sanity.create_document("prompt_template", {
                    "_type": "prompt_template",
                    "version": version,
                    "template": config["template"],
                    "description": config["description"],
                    "parameters": config["parameters"],
                    "avg_rating": 0,
                    "usage_count": 0,
                    "avg_cost": 0,
                    "active": version == "v1.0",  
                    "created_at": datetime.utcnow().isoformat()
                })
    def select_prompt(self, strategy: str = "best_performing") -> Dict[str, Any]:
        if strategy == "ab_test":
            return self._ab_test_selection()
        elif strategy == "latest":
            return self._select_latest()
        else:  
            return self._select_best_performing()
    def _select_best_performing(self) -> Dict[str, Any]:
        query = '*[_type=="prompt_template" && usage_count > 5] | order(avg_rating desc)[0]'
        best_prompt = self.sanity.query(query)
        if not best_prompt:
            return {
                "version": "v4.0",
                **self.PROMPT_TEMPLATES["v4.0"]
            }
        version = best_prompt.get("version", "v1.0")
        return {
            "version": version,
            **self.PROMPT_TEMPLATES.get(version, self.PROMPT_TEMPLATES["v1.0"])
        }
    def _ab_test_selection(self) -> Dict[str, Any]:
        query = '*[_type=="prompt_template" && active==true]'
        active_templates = self.sanity.query(query)
        if not active_templates:
            version = "v1.0"
        else:
            total_usage = sum(t.get("usage_count", 0) for t in active_templates)
            if total_usage == 0:
                selected = random.choice(active_templates)
            else:
                weights = [1 / (t.get("usage_count", 0) + 1) for t in active_templates]
                selected = random.choices(active_templates, weights=weights)[0]
            version = selected.get("version", "v1.0")
        return {
            "version": version,
            **self.PROMPT_TEMPLATES.get(version, self.PROMPT_TEMPLATES["v1.0"])
        }
    def _select_latest(self) -> Dict[str, Any]:
        query = '*[_type=="prompt_template"] | order(created_at desc)[0]'
        latest = self.sanity.query(query)
        version = latest.get("version", "v1.0") if latest else "v1.0"
        return {
            "version": version,
            **self.PROMPT_TEMPLATES.get(version, self.PROMPT_TEMPLATES["v1.0"])
        }
    def format_prompt(self, template_version: str, patient_data: Dict[str, Any]) -> str:
        template_config = self.PROMPT_TEMPLATES.get(template_version, self.PROMPT_TEMPLATES["v1.0"])
        template = template_config["template"]
        lab_results = patient_data.get("lab_results", [])
        if lab_results:
            lab_text = "\n".join([
                f"  - {lr.get('test_name')}: {lr.get('value')} (Normal: {lr.get('normal_range')})"
                for lr in lab_results
            ])
        else:
            lab_text = "No lab results available"
        formatted = template.format(
            name=patient_data.get("name", "Unknown"),
            condition=patient_data.get("condition", "Unknown"),
            department=patient_data.get("department", "General"),
            lab_results=lab_text
        )
        return formatted
    def get_parameters(self, template_version: str) -> Dict[str, Any]:
        template_config = self.PROMPT_TEMPLATES.get(template_version, self.PROMPT_TEMPLATES["v1.0"])
        return template_config.get("parameters", {
            "temperature": 0.7,
            "max_tokens": 500
        })
    async def evolve_prompts(self) -> Dict[str, Any]:
        query = '*[_type=="prompt_template"] | order(avg_rating desc)'
        templates = self.sanity.query(query)
        if not templates or len(templates) < 2:
            return {
                "action": "continue_testing",
                "reason": "Insufficient data for evolution"
            }
        best = templates[0]
        worst = templates[-1]
        if best.get("avg_rating", 0) >= 4.0 and best.get("usage_count", 0) >= 10:
            for t in templates:
                self.sanity.update_document(t["_id"], {
                    "active": t["version"] == best["version"]
                })
            return {
                "action": "promoted",
                "version": best["version"],
                "reason": f"High performance (rating: {best.get('avg_rating')})",
                "recommendation": "Consider creating v4.0 based on v3.0 patterns"
            }
        rating_variance = max(t.get("avg_rating", 0) for t in templates) - min(t.get("avg_rating", 0) for t in templates)
        if rating_variance < 0.5:
            return {
                "action": "continue_ab_testing",
                "reason": "Templates performing similarly, need more data"
            }
        return {
            "action": "analyze",
            "best_version": best.get("version"),
            "best_rating": best.get("avg_rating"),
            "recommendation": "Continue monitoring performance"
        }
prompt_service = PromptService()