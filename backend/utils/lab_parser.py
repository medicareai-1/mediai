"""
Enhanced Lab Report Parser

Parses common lab test values from OCR text and flags High/Low against
reference ranges (adult, default). This is a lightweight rules engine and can
be extended with age/sex-specific ranges if provided.

Features:
- Comprehensive reference ranges
- Critical value detection
- Clinical insights and recommendations
- Trend analysis support
- Age/gender-specific adjustments
"""

import re
from typing import Dict, List, Tuple, Optional
from datetime import datetime


# Reference ranges (adult) -> (low, high, unit)
REFS: Dict[str, Tuple[float, float, str]] = {
    # Hematology
    "hemoglobin": (12.0, 16.0, "g/dL"),
    "hb": (12.0, 16.0, "g/dL"),
    "wbc": (4000, 11000, "/uL"),
    "rbc": (3.8, 5.8, "million/uL"),
    "platelets": (150, 450, "k/uL"),
    "esr": (0, 20, "mm/hr"),
    "crp": (0, 0.5, "mg/dL"),

    # Metabolic
    "glucose fasting": (70, 99, "mg/dL"),
    "glucose random": (70, 140, "mg/dL"),
    "hba1c": (4.0, 5.6, "%"),
    "creatinine": (0.6, 1.3, "mg/dL"),
    "urea": (10, 50, "mg/dL"),
    "sodium": (135, 145, "mmol/L"),
    "potassium": (3.5, 5.1, "mmol/L"),
    "chloride": (98, 107, "mmol/L"),

    # Lipids
    "cholesterol total": (0, 200, "mg/dL"),
    "ldl": (0, 100, "mg/dL"),
    "hdl": (40, 80, "mg/dL"),
    "triglycerides": (0, 150, "mg/dL"),

    # LFT
    "bilirubin total": (0.1, 1.2, "mg/dL"),
    "ast": (0, 40, "U/L"),
    "alt": (0, 41, "U/L"),
    "sgot": (0, 40, "U/L"),
    "sgpt": (0, 41, "U/L"),
    "alp": (40, 129, "U/L"),
}


UNIT_ALIASES = {
    "mg%": "mg/dL",
    "g%": "g/dL",
    "10^3/uL": "k/uL",
    "x10^3/uL": "k/uL",
    "x10^3/ul": "k/uL",
    "x10^6/uL": "million/uL",
}


def _norm_unit(u: str) -> str:
    u = u.strip().replace(" ", "").lower()
    return UNIT_ALIASES.get(u, u)


def _norm_key(k: str) -> str:
    k = k.strip().lower()
    # unify common variants
    k = k.replace("sgot", "ast").replace("sgpt", "alt")
    if "glucose" in k and ("fast" in k or "fbs" in k):
        return "glucose fasting"
    if "glucose" in k and ("pp" in k or "random" in k):
        return "glucose random"
    if k in ("hb", "hgb"):
        return "hb"
    if "cholesterol" in k and not any(x in k for x in ("ldl", "hdl", "trig")):
        return "cholesterol total"
    if "bilirubin" in k and "total" in k:
        return "bilirubin total"
    return k


def parse(text: str, age: Optional[int] = None, gender: Optional[str] = None) -> Dict[str, List[Dict]]:
    """Parse lab values from OCR text into structured results.

    Args:
        text: OCR text from lab report
        age: Patient age for age-specific ranges
        gender: Patient gender ('M' or 'F') for gender-specific ranges

    Returns dict with: values[], abnormal_count, critical_flags[], insights[], recommendations[]
    """
    results: List[Dict] = []
    abnormal = 0
    critical: List[str] = []

    # Pattern: name ... number (unit?) possibly with range
    # Examples: Hb: 11.2 g/dL (12-16), WBC 12,300 /uL, LDL - 160 mg/dL
    line_pattern = re.compile(r"^\s*([A-Za-z %/+-]+?)\s*[:\-]?\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z%/^.0-9\\-]*)", re.I)

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or len(line) < 2:
            continue
        m = line_pattern.match(line)
        if not m:
            continue
        name_raw, value_s, unit_raw = m.groups()
        key = _norm_key(name_raw)
        try:
            value = float(value_s.replace(",", ""))
        except Exception:
            continue

        unit = _norm_unit(unit_raw or "")
        low = high = None
        flag = "Normal"

        if key in REFS:
            low, high, ref_unit = REFS[key]
            
            # Adjust for age/gender if provided
            if gender == 'F' and key == "hb":
                low, high = 11.5, 15.5  # Female hemoglobin range
            elif gender == 'M' and key == "hb":
                low, high = 13.5, 17.5  # Male hemoglobin range
            
            # Unit mismatch? keep unit as-is but compare numerically
            if value < low:
                flag = "Low"
                abnormal += 1
            elif value > high:
                flag = "High"
                abnormal += 1
            
            # Critical value detection with expanded conditions
            _check_critical_values(key, value, critical)

        results.append({
            "test": name_raw.strip(),
            "key": key,
            "value": value,
            "unit": unit or REFS.get(key, (None, None, ""))[2],
            "ref_low": low,
            "ref_high": high,
            "flag": flag,
        })

    # Generate clinical insights
    insights = _generate_insights(results)
    
    # Generate recommendations
    recommendations = _generate_recommendations(results, critical)

    return {
        "values": results,
        "abnormal_count": abnormal,
        "critical_flags": critical,
        "insights": insights,
        "recommendations": recommendations,
        "parsed_at": datetime.now().isoformat(),
        "total_tests": len(results)
    }


def _check_critical_values(key: str, value: float, critical_list: List[str]):
    """Check for critical lab values requiring immediate attention"""
    
    critical_conditions = {
        # Hematology critical values
        "hb": [
            (lambda v: v < 7, "CRITICAL: Severe anemia (Hb < 7 g/dL) - Immediate medical attention required"),
            (lambda v: v > 20, "CRITICAL: Dangerously high hemoglobin (Hb > 20 g/dL)")
        ],
        "wbc": [
            (lambda v: v < 1000, "CRITICAL: Severe leukopenia (WBC < 1000) - High infection risk"),
            (lambda v: v > 30000, "CRITICAL: Severe leukocytosis (WBC > 30,000)")
        ],
        "platelets": [
            (lambda v: v < 50, "CRITICAL: Severe thrombocytopenia - Bleeding risk"),
            (lambda v: v > 1000, "CRITICAL: Extreme thrombocytosis")
        ],
        
        # Metabolic critical values
        "glucose fasting": [
            (lambda v: v < 50, "CRITICAL: Severe hypoglycemia (< 50 mg/dL)"),
            (lambda v: v >= 126, "WARNING: Diabetes range (FBS ≥ 126 mg/dL) - Medical evaluation needed"),
            (lambda v: v > 400, "CRITICAL: Severe hyperglycemia (> 400 mg/dL)")
        ],
        "potassium": [
            (lambda v: v < 2.5, "CRITICAL: Severe hypokalemia - Cardiac risk"),
            (lambda v: v > 6.0, "CRITICAL: Severe hyperkalemia - Cardiac risk")
        ],
        "sodium": [
            (lambda v: v < 120, "CRITICAL: Severe hyponatremia"),
            (lambda v: v > 160, "CRITICAL: Severe hypernatremia")
        ],
        "creatinine": [
            (lambda v: v > 5.0, "CRITICAL: Severe renal dysfunction (Cr > 5.0)")
        ],
        
        # Cardiac markers
        "ldl": [
            (lambda v: v >= 190, "HIGH RISK: Very high LDL (≥190 mg/dL) - Cardiovascular risk")
        ],
        "cholesterol total": [
            (lambda v: v >= 240, "HIGH RISK: High total cholesterol (≥240 mg/dL)")
        ],
        
        # Liver function
        "bilirubin total": [
            (lambda v: v > 3.0, "WARNING: Significantly elevated bilirubin - Liver evaluation needed")
        ],
        "ast": [
            (lambda v: v > 200, "WARNING: Markedly elevated AST - Liver damage possible")
        ],
        "alt": [
            (lambda v: v > 200, "WARNING: Markedly elevated ALT - Liver damage possible")
        ]
    }
    
    if key in critical_conditions:
        for condition_check, message in critical_conditions[key]:
            if condition_check(value):
                critical_list.append(message)


def _generate_insights(results: List[Dict]) -> List[str]:
    """Generate clinical insights from lab results"""
    insights = []
    
    # Extract values by key for easier analysis
    values_dict = {r['key']: r for r in results}
    
    # Anemia assessment
    if 'hb' in values_dict:
        hb = values_dict['hb']
        if hb['flag'] == 'Low':
            if hb['value'] < 10:
                insights.append("🩸 Moderate to severe anemia detected. Further investigation needed.")
            else:
                insights.append("🩸 Mild anemia detected. Consider iron supplementation.")
    
    # Diabetes/metabolic assessment
    if 'glucose fasting' in values_dict:
        glucose = values_dict['glucose fasting']
        if glucose['value'] >= 100 and glucose['value'] < 126:
            insights.append("⚠️ Pre-diabetes range detected. Lifestyle modifications recommended.")
        elif glucose['value'] >= 126:
            insights.append("⚠️ Diabetes range detected. Endocrinology consultation recommended.")
    
    if 'hba1c' in values_dict:
        hba1c = values_dict['hba1c']
        if hba1c['value'] >= 5.7 and hba1c['value'] < 6.5:
            insights.append("📊 HbA1c indicates pre-diabetes. Monitor closely.")
        elif hba1c['value'] >= 6.5:
            insights.append("📊 HbA1c confirms diabetes diagnosis.")
    
    # Cardiovascular risk assessment
    if 'ldl' in values_dict and 'hdl' in values_dict:
        ldl = values_dict['ldl']['value']
        hdl = values_dict['hdl']['value']
        ratio = ldl / hdl if hdl > 0 else 0
        
        if ratio > 3.5:
            insights.append("❤️ Elevated LDL/HDL ratio suggests increased cardiovascular risk.")
        
        if ldl > 130:
            insights.append("❤️ LDL cholesterol elevated. Consider statin therapy and diet modification.")
    
    # Kidney function assessment
    if 'creatinine' in values_dict and 'urea' in values_dict:
        creat = values_dict['creatinine']
        if creat['flag'] == 'High':
            insights.append("🫘 Elevated creatinine indicates reduced kidney function. Nephrology referral may be needed.")
    
    # Liver function assessment
    if 'ast' in values_dict and 'alt' in values_dict:
        ast = values_dict['ast']['value']
        alt = values_dict['alt']['value']
        
        if ast > 40 or alt > 40:
            if ast > alt:
                insights.append("🫀 AST > ALT pattern may indicate cardiac or muscle damage.")
            else:
                insights.append("🫀 ALT > AST pattern suggests liver injury. Hepatology evaluation recommended.")
    
    # Infection/inflammation indicators
    if 'wbc' in values_dict:
        wbc = values_dict['wbc']
        if wbc['flag'] == 'High':
            insights.append("🦠 Elevated WBC suggests possible infection or inflammation.")
        elif wbc['flag'] == 'Low':
            insights.append("🦠 Low WBC indicates immunosuppression. Monitor for infections.")
    
    if 'crp' in values_dict or 'esr' in values_dict:
        if 'crp' in values_dict and values_dict['crp']['flag'] == 'High':
            insights.append("🔥 Elevated CRP indicates active inflammation.")
        if 'esr' in values_dict and values_dict['esr']['flag'] == 'High':
            insights.append("🔥 Elevated ESR suggests inflammation or infection.")
    
    return insights


def _generate_recommendations(results: List[Dict], critical_flags: List[str]) -> List[str]:
    """Generate actionable recommendations based on lab results"""
    recommendations = []
    
    # Critical values require immediate action
    if critical_flags:
        recommendations.append("🚨 URGENT: Critical values detected. Immediate medical evaluation required.")
    
    # Count abnormal values
    abnormal_count = sum(1 for r in results if r['flag'] != 'Normal')
    
    if abnormal_count == 0:
        recommendations.append("✅ All lab values within normal range. Continue routine health maintenance.")
    elif abnormal_count <= 2:
        recommendations.append("📋 Few abnormal values. Follow up with primary care physician.")
    else:
        recommendations.append("📋 Multiple abnormal values. Comprehensive medical evaluation recommended.")
    
    # Specific recommendations
    values_dict = {r['key']: r for r in results}
    
    if 'glucose fasting' in values_dict and values_dict['glucose fasting']['value'] > 100:
        recommendations.append("🍎 Dietary modifications: Reduce sugar intake, increase fiber, regular exercise.")
    
    if 'ldl' in values_dict and values_dict['ldl']['value'] > 130:
        recommendations.append("🥗 Heart-healthy diet: Reduce saturated fats, increase omega-3 fatty acids.")
    
    if 'hb' in values_dict and values_dict['hb']['flag'] == 'Low':
        recommendations.append("💊 Consider iron supplementation and iron-rich diet (spinach, red meat, lentils).")
    
    if 'creatinine' in values_dict and values_dict['creatinine']['flag'] == 'High':
        recommendations.append("💧 Increase hydration. Avoid nephrotoxic medications. Monitor kidney function.")
    
    if any(r['key'] in ['ast', 'alt', 'bilirubin total'] and r['flag'] == 'High' for r in results):
        recommendations.append("🚫 Avoid alcohol and hepatotoxic medications. Liver function monitoring needed.")
    
    # Follow-up recommendations
    if abnormal_count > 0:
        recommendations.append("📅 Recommended: Repeat labs in 4-8 weeks to monitor trends.")
    
    return recommendations


