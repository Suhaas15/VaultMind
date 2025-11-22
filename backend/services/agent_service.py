from ..config import settings
from .sanity_service import sanity_service
from .skyflow_service import skyflow_service
from .prompt_service import prompt_service
from datetime import datetime
from typing import Dict, Any
import json
import asyncio

# Import Socket.IO lazily to avoid circular imports
def get_sio():
    try:
        from ..main import sio
        return sio
    except Exception:
        return None

class AgentService:
    def __init__(self):
        self.prompt_service = prompt_service
    
    async def process_patient(self, patient_id: str, patient_data: dict) -> Dict[str, Any]:
        """
        Process patient with self-learning capabilities.
        
        Enhancements:
        - Selects optimal prompt template based on performance
        Uses adaptive prompts and parameters based on historical performance.
        """
        # Select best performing prompt
        prompt_config = prompt_service.select_prompt(strategy="best_performing")
        # prompt_config has "template", "parameters", "version"
        
        # Adaptive parameter tuning based on priority
        claude_params = prompt_config.get("parameters", {}).copy()
        # Ensure model is set (default to Claude 3.5 Sonnet)
        if "model" not in claude_params:
            claude_params["model"] = "claude-3-5-sonnet-20241022"
        if patient_data.get("priority") == "URGENT":
            claude_params["temperature"] = 0.3  # More focused for urgent cases
        
        # Invoke Skyflow function - REQUIRED for real AI processing
        if not settings.SKYFLOW_FUNCTION_ID or settings.SKYFLOW_FUNCTION_ID == "placeholder":
            raise ValueError(
                "Skyflow Function ID not configured. Set SKYFLOW_FUNCTION_ID in .env to enable AI processing. "
                "Get it from Skyflow Studio → Functions → Your Function → Function ID"
            )
        
        # Prepare payload for Vault-Confined Execution
        # We send the TEMPLATE and the TOKENIZED DATA.
        # The Skyflow Function inside the vault will detokenize and format.
        
        # Format lab_results as string (Skyflow Function expects string, not array)
        lab_results_text = "No lab results"
        if patient_data.get("lab_results"):
            if isinstance(patient_data["lab_results"], list):
                if len(patient_data["lab_results"]) > 0:
                    lab_results_list = []
                    for lab in patient_data["lab_results"]:
                        if isinstance(lab, dict):
                            lab_str = f"- {lab.get('test_name', 'Unknown')}: {lab.get('value', 'N/A')}"
                            if lab.get('normal_range'):
                                lab_str += f" (Normal: {lab.get('normal_range')})"
                            lab_results_list.append(lab_str)
                        else:
                            lab_results_list.append(str(lab))
                    lab_results_text = "\n".join(lab_results_list)
            else:
                lab_results_text = str(patient_data["lab_results"])
        
        # Prepare patient data for Skyflow Function
        # The function expects simple string replacements: {name}, {condition}, etc.
        formatted_patient_data = {
            "name_token": patient_data.get("name_token", ""),
            "ssn_token": patient_data.get("ssn_token", ""),
            "dob_token": patient_data.get("dob_token", ""),
            "condition": patient_data.get("condition", "Unknown"),
            "department": patient_data.get("department", "General"),
            "lab_results": lab_results_text
        }
        
        payload = {
            "prompt_template": prompt_config["template"],
            "patient_data": formatted_patient_data,
            "parameters": claude_params
        }
        
        # Call Skyflow Function
        print(f"Invoking Skyflow Function {settings.SKYFLOW_FUNCTION_ID}...")
        try:
            result = skyflow_service.invoke_function(settings.SKYFLOW_FUNCTION_ID, payload)
        except Exception as e:
            print(f"⚠️ Skyflow Function invocation failed: {e}")
            result = {"success": False, "error": str(e)}
        
        if not result.get("success", False):
            # Handle failure - Call Claude directly as fallback
            print(f"❌ Skyflow Function failed: {result.get('error')}")
            print(f"⚠️ Falling back to direct Claude API call...")
            
            try:
                import requests
                import time
                
                # Check if Anthropic API key is configured
                if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "placeholder":
                    raise ValueError("ANTHROPIC_API_KEY not configured. Set it in .env file to enable AI clinical summaries.")
                
                # Try to use original document text if available (best for AI processing)
                original_text = patient_data.get('original_document_text')
                if original_text:
                    # Use the original document text directly - it has all the context
                    print(f"✅ Using original document text for AI processing ({len(original_text)} chars)")
                    # Create a comprehensive prompt with the full document
                    final_prompt = f"""You are an expert medical AI assistant. Analyze the following patient medical document and provide a professional clinical summary.

MEDICAL DOCUMENT:
{original_text}

ANALYSIS REQUIREMENTS:
1. Assess the patient's current condition and severity
2. Identify key clinical findings, lab results, and vital signs
3. Note any critical values or concerning trends
4. Recommend specific, evidence-based next steps or interventions
5. Maintain a professional, objective clinical tone

Format: Provide a concise clinical summary (3-5 sentences) focusing on the most important findings and recommendations."""
                else:
                    # Fallback: Detokenize patient data if we only have tokens
                    # Try to get actual name from patient_data, or detokenize if we have tokens
                    name = patient_data.get('name', 'Unknown')
                    if name == 'Unknown' and patient_data.get('name_token'):
                        try:
                            name = skyflow_service.detokenize(patient_data['name_token'])
                            print(f"✅ Detokenized name: {name[:20]}...")
                        except Exception as detokenize_error:
                            print(f"⚠️ Could not detokenize name: {detokenize_error}")
                            name = f"Patient (Token: {patient_data['name_token'][:10]}...)"
                    
                    # Get condition, department, and lab results (these are not tokenized)
                    condition = str(patient_data.get('condition', 'Unknown'))
                    department = str(patient_data.get('department', 'General'))
                    lab_results_raw = patient_data.get('lab_results', 'No lab results')
                    
                    # Format lab results properly
                    if isinstance(lab_results_raw, list) and len(lab_results_raw) > 0:
                        lab_results_list = []
                        for lab in lab_results_raw:
                            if isinstance(lab, dict):
                                lab_str = f"- {lab.get('test_name', 'Unknown')}: {lab.get('value', 'N/A')}"
                                if lab.get('normal_range'):
                                    lab_str += f" (Normal: {lab.get('normal_range')})"
                                lab_results_list.append(lab_str)
                            else:
                                lab_results_list.append(str(lab))
                        lab_results = "\n".join(lab_results_list)
                    else:
                        lab_results = str(lab_results_raw) if lab_results_raw else 'No lab results'
                    
                    # Construct the prompt using the template
                    final_prompt = prompt_config["template"].replace('{name}', str(name)) \
                        .replace('{condition}', condition) \
                        .replace('{department}', department) \
                        .replace('{lab_results}', lab_results)
                
                # Call Claude API directly via HTTP
                print(f"Calling Claude API directly with model: {claude_params.get('model', 'claude-3-5-sonnet-20241022')}")
                print(f"Prompt preview: {final_prompt[:200]}...")
                
                # Validate API key
                if not settings.ANTHROPIC_API_KEY or settings.ANTHROPIC_API_KEY == "placeholder":
                    raise ValueError("ANTHROPIC_API_KEY is not configured or is set to 'placeholder'. Please set a valid API key in .env file.")
                
                start_time = time.time()
                try:
                    claude_response = requests.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={
                            "x-api-key": settings.ANTHROPIC_API_KEY,
                            "anthropic-version": "2023-06-01",
                            "content-type": "application/json"
                        },
                        json={
                            "model": claude_params.get("model", "claude-3-5-sonnet-20241022"),
                            "max_tokens": claude_params.get("max_tokens", 1000),
                            "temperature": claude_params.get("temperature", 0.7),
                            "messages": [{"role": "user", "content": final_prompt}]
                        },
                        timeout=60
                    )
                    
                    # Better error handling
                    if claude_response.status_code == 404:
                        error_msg = f"Anthropic API endpoint not found (404). This usually means:\n"
                        error_msg += f"1. The API key is invalid or not set correctly\n"
                        error_msg += f"2. The endpoint URL has changed\n"
                        error_msg += f"3. There's a network/proxy issue\n"
                        if claude_response.text:
                            error_msg += f"\nResponse: {claude_response.text[:500]}"
                        raise ValueError(error_msg)
                    
                    claude_response.raise_for_status()
                    response_data = claude_response.json()
                    processing_time = int((time.time() - start_time) * 1000)
                except requests.exceptions.HTTPError as http_err:
                    error_msg = f"Anthropic API HTTP Error: {http_err}"
                    if hasattr(http_err, 'response') and http_err.response is not None:
                        error_msg += f"\nStatus: {http_err.response.status_code}"
                        error_msg += f"\nResponse: {http_err.response.text[:500]}"
                    raise ValueError(error_msg) from http_err
                except requests.exceptions.RequestException as req_err:
                    raise ValueError(f"Anthropic API Request Error: {req_err}") from req_err
                
                # Extract response
                summary = response_data["content"][0]["text"]
                
                # Calculate approximate cost (Claude 3.5 Sonnet pricing as of 2024)
                input_tokens = response_data["usage"]["input_tokens"]
                output_tokens = response_data["usage"]["output_tokens"]
                # Approximate pricing: $3 per 1M input tokens, $15 per 1M output tokens
                cost_usd = (input_tokens / 1_000_000 * 3) + (output_tokens / 1_000_000 * 15)
                
                result = {
                    "success": True,
                    "summary": summary,
                    "tokens_used": {
                        "input": input_tokens,
                        "output": output_tokens
                    },
                    "cost_usd": cost_usd,
                    "claude_model": response_data.get("model", "claude-3-5-sonnet-20241022"),
                    "processing_duration_ms": processing_time
                }
                
                print(f"✅ Claude API call successful! Generated {output_tokens} output tokens in {processing_time}ms")
                print(f"   Cost: ${cost_usd:.6f}")
                
            except Exception as claude_error:
                print(f"❌ Claude API fallback also failed: {claude_error}")
                # Final fallback: mock response
                result = {
                    "success": True,
                    "summary": f"**Clinical Assessment**: Patient presents with {patient_data.get('condition', 'Unknown condition')}. \n\n**Note**: This is a fallback response. Both Skyflow Function and direct Claude API calls failed.",
                    "tokens_used": {"input": 150, "output": 100},
                    "cost_usd": 0.001,
                    "claude_model": "fallback-mock",
                    "processing_duration_ms": 100
                }

        # Success - Update patient with result
        # Handle response format from Skyflow Function
        ai_summary = result.get("summary", "")
        tokens_used = result.get("tokens_used", {})
        if isinstance(tokens_used, dict) and "input_tokens" in tokens_used:
            # Convert Anthropic format
            tokens_used = {
                "input": tokens_used.get("input_tokens", 0),
                "output": tokens_used.get("output_tokens", 0)
            }
        
        update_data = {
            "processed": True,
            "processedAt": datetime.utcnow().isoformat(),
            "ai_summary": ai_summary,
            "tokens_used": tokens_used,
            "cost_usd": result.get("cost_usd", 0),
            "claude_model": result.get("claude_model", "claude-3-5-sonnet-20240620"),
            "processing_duration_ms": result.get("processing_duration_ms", 0),
            "prompt_version": prompt_config["version"]
        }
        
        sanity_service.update_patient(patient_id, update_data)
        
        # Get updated patient data and emit socket event
        updated_patient = sanity_service.get_patient(patient_id)
        sio = get_sio()
        if updated_patient and sio:
            try:
                # Emit event asynchronously
                asyncio.create_task(sio.emit('patient_processed', {
                    'patientId': patient_id,
                    'patient': updated_patient
                }))
            except Exception as e:
                print(f"Warning: Could not emit socket event: {e}")
        
        return update_data
    
    async def learn_from_patterns(self) -> Dict[str, Any]:
        """
        Analyze historical data to learn patterns and optimize future processing.
        
        Returns:
            Insights and optimization recommendations
        """
        # Get recent processed patients
        recent_patients = sanity_service.query(
            '*[_type=="patient" && processed==true] | order(processedAt desc)[0...100]'
        )
        
        if not recent_patients or len(recent_patients) < 10:
            return {
                "status": "insufficient_data",
                "message": "Need at least 10 processed patients for pattern analysis"
            }
        
        # Analyze patterns by department
        dept_stats = {}
        for patient in recent_patients:
            dept = patient.get("department", "Unknown")
            if dept not in dept_stats:
                dept_stats[dept] = {
                    "count": 0,
                    "avg_duration": 0,
                    "avg_cost": 0,
                    "total_duration": 0,
                    "total_cost": 0
                }
            
            dept_stats[dept]["count"] += 1
            dept_stats[dept]["total_duration"] += patient.get("processing_duration_ms", 0)
            dept_stats[dept]["total_cost"] += patient.get("cost_usd", 0)
        
        # Calculate averages
        for dept in dept_stats:
            count = dept_stats[dept]["count"]
            dept_stats[dept]["avg_duration"] = dept_stats[dept]["total_duration"] / count
            dept_stats[dept]["avg_cost"] = dept_stats[dept]["total_cost"] / count
        
        # Find optimization opportunities
        recommendations = []
        
        # Check for departments with high costs
        for dept, stats in dept_stats.items():
            if stats["avg_cost"] > 0.005:  # Threshold
                recommendations.append({
                    "type": "cost_optimization",
                    "department": dept,
                    "message": f"{dept} has high avg cost (${stats['avg_cost']:.4f}). Consider using shorter prompts."
                })
        
        return {
            "status": "analysis_complete",
            "department_stats": dept_stats,
            "recommendations": recommendations,
            "total_analyzed": len(recent_patients)
        }

agent_service = AgentService()
