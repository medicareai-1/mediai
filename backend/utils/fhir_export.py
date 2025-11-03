"""
FHIR (Fast Healthcare Interoperability Resources) Export
Converts MediScan data to FHIR R4 format for hospital integration
"""

from datetime import datetime
import json

class FHIRExporter:
    def __init__(self):
        """Initialize FHIR exporter"""
        self.fhir_version = "4.0.1"
    
    def export_patient(self, patient_data):
        """Export patient data in FHIR Patient resource format"""
        return {
            "resourceType": "Patient",
            "id": patient_data.get("id", "unknown"),
            "identifier": [{
                "system": "mediscan-ai",
                "value": patient_data.get("id", "")
            }],
            "name": [{
                "use": "official",
                "text": patient_data.get("name", "Unknown"),
                "family": patient_data.get("name", "Unknown").split()[-1] if patient_data.get("name") else "",
                "given": patient_data.get("name", "Unknown").split()[:-1] if patient_data.get("name") else []
            }],
            "gender": patient_data.get("gender", "unknown"),
            "birthDate": patient_data.get("dob", ""),
            "address": [{
                "use": "home",
                "text": patient_data.get("address", "")
            }],
            "telecom": [{
                "system": "phone",
                "value": patient_data.get("phone", ""),
                "use": "mobile"
            }]
        }
    
    def export_medication_request(self, prescription_data):
        """Export prescription in FHIR MedicationRequest format"""
        medicines = prescription_data.get("medicines", [])
        dosages = prescription_data.get("dosages", [])
        durations = prescription_data.get("durations", [])
        
        medication_requests = []
        
        for idx, medicine in enumerate(medicines):
            # Extract dosage and duration for this medicine
            dosage = dosages[idx] if idx < len(dosages) else ""
            duration = durations[idx] if idx < len(durations) else ""
            
            medication_request = {
                "resourceType": "MedicationRequest",
                "id": f"med-{idx}-{datetime.now().timestamp()}",
                "status": "active",
                "intent": "order",
                "medicationCodeableConcept": {
                    "coding": [{
                        "system": "mediscan-ai",
                        "code": medicine.replace(" ", "-").lower(),
                        "display": medicine
                    }],
                    "text": medicine
                },
                "subject": {
                    "reference": f"Patient/{prescription_data.get('patient_id', 'unknown')}",
                    "display": "Patient"
                },
                "authoredOn": prescription_data.get("timestamp", datetime.now().isoformat()),
                "dosageInstruction": [{
                    "text": f"{medicine} {dosage}".strip(),
                    "timing": {
                        "repeat": {
                            "duration": self._parse_duration(duration),
                            "durationUnit": "d"
                        }
                    },
                    "doseAndRate": [{
                        "doseQuantity": {
                            "value": self._parse_dosage_value(dosage),
                            "unit": self._parse_dosage_unit(dosage)
                        }
                    }]
                }],
                "note": [{
                    "text": f"OCR Confidence: {prescription_data.get('ocr_confidence', 0)*100:.0f}%"
                }]
            }
            
            medication_requests.append(medication_request)
        
        return medication_requests
    
    def export_diagnostic_report(self, analysis_data):
        """Export medical image analysis in FHIR DiagnosticReport format"""
        # Get classification and confidence based on document type
        classification, confidence = self._get_imaging_classification(analysis_data)
        
        return {
            "resourceType": "DiagnosticReport",
            "id": f"report-{datetime.now().timestamp()}",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/v2-0074",
                    "code": "RAD",
                    "display": "Radiology"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "mediscan-ai",
                    "code": analysis_data.get("document_type", "unknown"),
                    "display": analysis_data.get("document_type", "Medical Imaging").title()
                }]
            },
            "subject": {
                "reference": f"Patient/{analysis_data.get('patient_id', 'unknown')}"
            },
            "effectiveDateTime": analysis_data.get("timestamp", datetime.now().isoformat()),
            "issued": datetime.now().isoformat(),
            "result": [{
                "reference": f"Observation/imaging-{datetime.now().timestamp()}"
            }],
            "conclusion": analysis_data.get("diagnosis_summary", ""),
            "conclusionCode": [{
                "coding": [{
                    "system": "mediscan-ai",
                    "code": classification or "normal",
                    "display": classification or "Normal"
                }]
            }],
            "presentedForm": [{
                "contentType": "image/jpeg",
                "url": analysis_data.get("file_url", ""),
                "title": "Medical Image"
            }]
        }
    
    def export_observation(self, analysis_data):
        """Export AI analysis results as FHIR Observation"""
        # Get classification and confidence based on document type
        classification, confidence = self._get_imaging_classification(analysis_data)
        
        return {
            "resourceType": "Observation",
            "id": f"imaging-{datetime.now().timestamp()}",
            "status": "final",
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/observation-category",
                    "code": "imaging",
                    "display": "Imaging"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "mediscan-ai",
                    "code": "ai-classification",
                    "display": "AI Image Classification"
                }],
                "text": "AI Image Analysis"
            },
            "subject": {
                "reference": f"Patient/{analysis_data.get('patient_id', 'unknown')}"
            },
            "effectiveDateTime": analysis_data.get("timestamp", datetime.now().isoformat()),
            "valueCodeableConcept": {
                "coding": [{
                    "system": "mediscan-ai",
                    "code": classification or "normal",
                    "display": classification or "Normal"
                }],
                "text": f"{classification or 'Normal'} ({confidence*100:.1f}% confidence)"
            },
            "note": [{
                "text": f"AI Confidence: {confidence*100:.1f}%. Explainability: Grad-CAM heatmap available."
            }]
        }
    
    def export_condition(self, diagnosis_data):
        """Export suggested diagnosis as FHIR Condition"""
        if not diagnosis_data or not diagnosis_data.get("possible_conditions"):
            return None
        
        # Get top condition
        top_condition = diagnosis_data["possible_conditions"][0]
        
        return {
            "resourceType": "Condition",
            "id": f"condition-{datetime.now().timestamp()}",
            "clinicalStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-clinical",
                    "code": "active"
                }]
            },
            "verificationStatus": {
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-ver-status",
                    "code": "provisional",
                    "display": "Provisional - AI Suggested"
                }]
            },
            "category": [{
                "coding": [{
                    "system": "http://terminology.hl7.org/CodeSystem/condition-category",
                    "code": "encounter-diagnosis"
                }]
            }],
            "code": {
                "coding": [{
                    "system": "mediscan-ai",
                    "code": top_condition["condition"].replace(" ", "-").lower(),
                    "display": top_condition["condition"]
                }],
                "text": top_condition["condition"]
            },
            "subject": {
                "reference": "Patient/unknown"
            },
            "recordedDate": datetime.now().isoformat(),
            "evidence": [{
                "detail": [{
                    "display": f"Medicine: {med}"
                } for med in top_condition.get("supporting_medicines", [])]
            }],
            "note": [{
                "text": f"AI-suggested diagnosis with {top_condition['confidence']} confidence. Doctor verification required."
            }]
        }
    
    def export_bundle(self, complete_analysis):
        """Export complete analysis as FHIR Bundle"""
        bundle = {
            "resourceType": "Bundle",
            "id": f"bundle-{datetime.now().timestamp()}",
            "type": "collection",
            "timestamp": datetime.now().isoformat(),
            "entry": []
        }
        
        # Add patient if available
        if complete_analysis.get("patient_data"):
            bundle["entry"].append({
                "resource": self.export_patient(complete_analysis["patient_data"])
            })
        
        # Add medication requests
        if complete_analysis.get("medicines"):
            for med_request in self.export_medication_request(complete_analysis):
                bundle["entry"].append({"resource": med_request})
        
        # Add diagnostic report if imaging (X-ray, CT, or MRI)
        has_imaging = (
            complete_analysis.get("cnn_class") or 
            complete_analysis.get("ct_label") or 
            complete_analysis.get("mri_label")
        )
        if has_imaging:
            bundle["entry"].append({
                "resource": self.export_diagnostic_report(complete_analysis)
            })
            bundle["entry"].append({
                "resource": self.export_observation(complete_analysis)
            })
        
        # Add condition if diagnosis suggested
        if complete_analysis.get("diagnosis_suggestions"):
            condition = self.export_condition(complete_analysis["diagnosis_suggestions"])
            if condition:
                bundle["entry"].append({"resource": condition})
        
        return bundle
    
    def _get_imaging_classification(self, analysis_data):
        """
        Get classification and confidence for any imaging type
        Returns: (classification, confidence)
        """
        # Check for X-ray (CNN)
        if analysis_data.get("cnn_class"):
            return (
                analysis_data.get("cnn_class", "normal"),
                analysis_data.get("cnn_confidence", 0.0)
            )
        
        # Check for CT scan
        if analysis_data.get("ct_label"):
            return (
                analysis_data.get("ct_label", "normal"),
                analysis_data.get("ct_confidence", 0.0)
            )
        
        # Check for MRI scan
        if analysis_data.get("mri_label"):
            return (
                analysis_data.get("mri_label", "normal"),
                analysis_data.get("mri_confidence", 0.0)
            )
        
        # Default
        return ("normal", 0.0)
    
    def _parse_duration(self, duration_str):
        """Parse duration string to number of days"""
        if not duration_str:
            return 0
        
        # Extract number
        import re
        match = re.search(r'(\d+)', duration_str)
        if match:
            number = int(match.group(1))
            if 'week' in duration_str.lower():
                return number * 7
            elif 'month' in duration_str.lower():
                return number * 30
            else:
                return number
        return 0
    
    def _parse_dosage_value(self, dosage_str):
        """Extract dosage value"""
        import re
        match = re.search(r'(\d+(?:\.\d+)?)', dosage_str)
        return float(match.group(1)) if match else 0
    
    def _parse_dosage_unit(self, dosage_str):
        """Extract dosage unit"""
        if 'mg' in dosage_str.lower():
            return 'mg'
        elif 'ml' in dosage_str.lower():
            return 'ml'
        elif 'g' in dosage_str.lower():
            return 'g'
        elif 'tab' in dosage_str.lower():
            return 'tablet'
        return 'unit'


# Singleton instance
fhir_exporter = FHIRExporter()

