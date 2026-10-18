# -*- coding: utf-8 -*-
"""Continuous Glucose & Meal Impact Analyzer Skill for GenPark Personal Health Agents."""
import json
import math
from typing import Dict, Any, List

def calculate_trapezoidal_auc(readings: List[float], baseline: float, interval_minutes: float = 15.0) -> float:
    """Calculate Incremental Area Under the Curve (iAUC) above baseline using trapezoidal rule."""
    if not readings:
        return 0.0
    total_auc = 0.0
    prev = max(0.0, readings[0] - baseline)
    for r in readings[1:]:
        curr = max(0.0, r - baseline)
        trapezoid = ((prev + curr) / 2.0) * (interval_minutes / 60.0) # mg*hr/dL
        total_auc += trapezoid
        prev = curr
    return round(total_auc, 2)

def analyze_cgm_meal_impact(baseline_glucose_mg_dl: float, meal_macronutrients: Dict[str, float], cgm_readings_mg_dl: List[float]) -> Dict[str, Any]:
    if not cgm_readings_mg_dl:
        return {"error": "cgm_readings_mg_dl cannot be empty"}
    
    peak_glucose = max(cgm_readings_mg_dl)
    peak_index = cgm_readings_mg_dl.index(peak_glucose)
    time_to_peak_min = (peak_index + 1) * 15
    spike_delta = peak_glucose - baseline_glucose_mg_dl
    auc_score = calculate_trapezoidal_auc(cgm_readings_mg_dl, baseline_glucose_mg_dl)
    
    # Assess Glycemic Risk Category
    if peak_glucose > 180.0 or spike_delta > 55.0:
        spike_severity = "HIGH_SPIKE"
        metabolic_impact = "Elevated postprandial hyper-glycemic excursion; rapid insulin surge induced."
    elif peak_glucose > 140.0 or spike_delta > 35.0:
        spike_severity = "MODERATE_SPIKE"
        metabolic_impact = "Moderate postprandial glucose rise within acceptable non-diabetic transient bounds."
    else:
        spike_severity = "OPTIMAL_STEADY"
        metabolic_impact = "Excellent glycemic stability with negligible glycemic volatility."

    net_carbs = meal_macronutrients.get("net_carbs_g", 0.0)
    fiber = meal_macronutrients.get("fiber_g", 0.0)
    carbs_to_fiber_ratio = round(net_carbs / max(1.0, fiber), 2)

    return {
        "baseline_glucose_mg_dl": baseline_glucose_mg_dl,
        "peak_glucose_mg_dl": peak_glucose,
        "spike_delta_mg_dl": round(spike_delta, 1),
        "time_to_peak_minutes": time_to_peak_min,
        "iauc_above_baseline_mg_hr_dl": auc_score,
        "spike_severity": spike_severity,
        "carbs_to_fiber_ratio": carbs_to_fiber_ratio,
        "metabolic_impact_summary": metabolic_impact,
        "verified_by": "GenPark Personal Health Telemetry Engine"
    }

def recommend_glycemic_mitigations(peak_glucose_mg_dl: float, spike_delta_mg_dl: float, auc_score: float = 0.0) -> Dict[str, Any]:
    mitigations = []
    if spike_delta_mg_dl > 40.0 or peak_glucose_mg_dl > 160.0:
        mitigations.append({
            "action": "Immediate 15-minute zone-1 brisk walk",
            "mechanism": "Translocates GLUT4 transporters to skeletal muscle independent of insulin to clear circulating glucose."
        })
        mitigations.append({
            "action": "Food Sequencing Adjustment for future meals",
            "mechanism": "Consume fiber and protein 10 minutes prior to carbohydrates to retard gastric emptying."
        })
    elif spike_delta_mg_dl > 25.0:
        mitigations.append({
            "action": "Light post-meal movement or standing desk activation",
            "mechanism": "Increases non-exercise activity thermogenesis (NEAT) and accelerates glucose uptake."
        })
    else:
        mitigations.append({
            "action": "Maintain current nutritional cadence",
            "mechanism": "Current meal composition maintains tight glycemic homeostasis."
        })

    return {
        "peak_glucose_mg_dl": peak_glucose_mg_dl,
        "spike_delta_mg_dl": spike_delta_mg_dl,
        "interventions_count": len(mitigations),
        "recommended_interventions": mitigations,
        "guidance": "Consult qualified clinical healthcare professionals for diabetic diagnostic management."
    }
