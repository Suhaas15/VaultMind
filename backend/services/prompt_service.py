from typing import Dict, List, Optional, Any
from datetime import datetime
import random
from .sanity_service import sanity_service

class PromptService:
    """
    Manages adaptive prompt engineering with A/B testing and automatic optimization.
    Evolves prompts based on performance feedback.
    """
    
    # Base prompt templates
    PROMPT_TEMPLATES = {
        "v1.0": {
            "template": """Analyze the following patient data and provide a concise clinical summary:

Patient Information:
- Name: {name}
- Condition: {condition}
- Department: {department}
- Lab Results: {lab_results}

Provide a professional medical summary focusing on:
1. Current condition assessment
2. Key findings from lab results
3. Recommended next steps

Keep the summary concise and clinical.""",
            "description": "Original baseline prompt",
            "parameters": {
                "temperature": 0.7,
                "max_tokens": 500
            }
        },
        "v2.0": {
            "template": """You are an experienced medical AI assistant. Analyze this patient data with clinical precision:

PATIENT DATA:
Name: {name}
Primary Condition: {condition}
Department: {department}
Laboratory Results: {lab_results}

ANALYSIS REQUIREMENTS:
1. Assess severity and urgency
2. Identify critical lab value deviations
3. Suggest evidence-based interventions
4. Note any red flags requiring immediate attention

Format: Professional medical summary (3-4 sentences).""",
            "description": "Enhanced with structured analysis requirements",
            "parameters": {
                "temperature": 0.6,
                "max_tokens": 600
            }
        },
        "v3.0": {
            "template": """Clinical Summary Request:

Patient: {name}
Chief Complaint: {condition}
Treating Department: {department}
Lab Data: {lab_results}

Generate a SOAP-style summary:
- Subjective: Patient presentation
- Objective: Lab findings and vitals
- Assessment: Clinical interpretation
- Plan: Recommended actions

Be specific, actionable, and evidence-based.""",
            "description": "SOAP format for structured output",
            "parameters": {
                "temperature": 0.5,
                "max_tokens": 700
            }
        },
        "v4.0": {
            "template": """You are an expert medical AI assistant. Your task is to analyze patient data and generate a professional clinical summary.

<patient_data>
    <name>{name}</name>
    <condition>{condition}</condition>
    <department>{department}</department>
    <lab_results>
{lab_results}
    </lab_results>
</patient_data>

<requirements>
    1. Analyze the patient's current status based on the condition and lab results.
    2. Identify any critical values or concerning trends.
    3. Recommend specific, evidence-based next steps or interventions.
    4. Maintain a professional, objective clinical tone.
</requirements>

<example>
    <input>
        <name>Jane Doe</name>
        <condition>Type 2 Diabetes</condition>
        <department>Endocrinology</department>
        <lab_results>
          - HbA1c: 8.5% (Normal: <5.7%)
          - Fasting Glucose: 145 mg/dL (Normal: <100 mg/dL)
        </lab_results>
    </input>
    <output>
        **Clinical Assessment**: Patient presents with uncontrolled Type 2 Diabetes, evidenced by elevated HbA1c (8.5%) and fasting glucose (145 mg/dL), indicating suboptimal glycemic control.
        
        **Key Findings**:
        - Hyperglycemia and elevated long-term glucose markers.
        
        **Plan**:
        1. Review and potentially intensify oral hypoglycemic agents or consider insulin initiation.
        2. Reinforce lifestyle modifications (diet/exercise).
        3. Schedule follow-up in 3 months to monitor HbA1c.
    </output>
</example>

Based on the patient data provided above, generate the clinical summary within <clinical_summary> tags.
""",
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
        """Initialize prompt templates in Sanity if they don't exist."""
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
                    "active": version == "v1.0",  # Start with v1.0 active
                    "created_at": datetime.utcnow().isoformat()
                })
    
    def select_prompt(self, strategy: str = "best_performing") -> Dict[str, Any]:
        """
        Select the optimal prompt template based on strategy.
        
        Args:
            strategy: 
                - "best_performing": Use highest rated template
                - "ab_test": Randomly select for A/B testing
                - "latest": Use newest version
        
        Returns:
            Selected prompt template with version and content
        """
        if strategy == "ab_test":
            return self._ab_test_selection()
        elif strategy == "latest":
            return self._select_latest()
        else:  # best_performing (default)
            return self._select_best_performing()
    
    def _select_best_performing(self) -> Dict[str, Any]:
        """Select prompt with highest average rating."""
        query = '*[_type=="prompt_template" && usage_count > 5] | order(avg_rating desc)[0]'
        best_prompt = self.sanity.query(query)
        
        if not best_prompt:
            # Fallback to v4.0 (XML Optimized) if no data yet
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
        """Randomly select a template for A/B testing."""
        # Get all active templates
        query = '*[_type=="prompt_template" && active==true]'
        active_templates = self.sanity.query(query)
        
        if not active_templates:
            version = "v1.0"
        else:
            # Random selection weighted by inverse usage (explore less-used templates)
            total_usage = sum(t.get("usage_count", 0) for t in active_templates)
            if total_usage == 0:
                selected = random.choice(active_templates)
            else:
                # Weight by inverse usage to balance exploration
                weights = [1 / (t.get("usage_count", 0) + 1) for t in active_templates]
                selected = random.choices(active_templates, weights=weights)[0]
            
            version = selected.get("version", "v1.0")
        
        return {
            "version": version,
            **self.PROMPT_TEMPLATES.get(version, self.PROMPT_TEMPLATES["v1.0"])
        }
    
    def _select_latest(self) -> Dict[str, Any]:
        """Select the most recently created template."""
        query = '*[_type=="prompt_template"] | order(created_at desc)[0]'
        latest = self.sanity.query(query)
        
        version = latest.get("version", "v1.0") if latest else "v1.0"
        return {
            "version": version,
            **self.PROMPT_TEMPLATES.get(version, self.PROMPT_TEMPLATES["v1.0"])
        }
    
    def format_prompt(self, template_version: str, patient_data: Dict[str, Any]) -> str:
        """
        Format a prompt template with patient data.
        
        Args:
            template_version: Version of template to use
            patient_data: Patient information to insert
        
        Returns:
            Formatted prompt string
        """
        template_config = self.PROMPT_TEMPLATES.get(template_version, self.PROMPT_TEMPLATES["v1.0"])
        template = template_config["template"]
        
        # Format lab results
        lab_results = patient_data.get("lab_results", [])
        if lab_results:
            lab_text = "\n".join([
                f"  - {lr.get('test_name')}: {lr.get('value')} (Normal: {lr.get('normal_range')})"
                for lr in lab_results
            ])
        else:
            lab_text = "No lab results available"
        
        # Fill template
        formatted = template.format(
            name=patient_data.get("name", "Unknown"),
            condition=patient_data.get("condition", "Unknown"),
            department=patient_data.get("department", "General"),
            lab_results=lab_text
        )
        
        return formatted
    
    def get_parameters(self, template_version: str) -> Dict[str, Any]:
        """Get Claude API parameters for a template version."""
        template_config = self.PROMPT_TEMPLATES.get(template_version, self.PROMPT_TEMPLATES["v1.0"])
        return template_config.get("parameters", {
            "temperature": 0.7,
            "max_tokens": 500
        })
    
    async def evolve_prompts(self) -> Dict[str, Any]:
        """
        Analyze performance and recommend prompt evolution.
        
        Returns:
            Recommendations for prompt improvements
        """
        # Get all templates with their performance
        query = '*[_type=="prompt_template"] | order(avg_rating desc)'
        templates = self.sanity.query(query)
        
        if not templates or len(templates) < 2:
            return {
                "action": "continue_testing",
                "reason": "Insufficient data for evolution"
            }
        
        best = templates[0]
        worst = templates[-1]
        
        # If best template has high rating and sufficient usage, make it primary
        if best.get("avg_rating", 0) >= 4.0 and best.get("usage_count", 0) >= 10:
            # Deactivate others, activate best
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
        
        # If all templates have similar performance, continue A/B testing
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
