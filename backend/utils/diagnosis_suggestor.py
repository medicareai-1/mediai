"""
Diagnosis Suggestion Engine
Rule-based medical diagnosis suggestions from medicines and symptoms
"""

class DiagnosisSuggestor:
    def __init__(self):
        """Initialize diagnosis database"""
        # Medicine -> Possible conditions mapping
        self.medicine_conditions = {
            # Cardiovascular
            'betaloc': ['Hypertension', 'Angina', 'Heart Failure', 'Arrhythmia'],
            'metoprolol': ['Hypertension', 'Angina', 'Heart Failure'],
            'atenolol': ['Hypertension', 'Angina'],
            'propranolol': ['Hypertension', 'Migraine', 'Anxiety'],
            'amlodipine': ['Hypertension', 'Angina'],
            'losartan': ['Hypertension', 'Diabetic Nephropathy'],
            'enalapril': ['Hypertension', 'Heart Failure'],
            'lisinopril': ['Hypertension', 'Heart Failure'],
            'warfarin': ['Atrial Fibrillation', 'DVT', 'Pulmonary Embolism'],
            'aspirin': ['Cardiovascular Disease Prevention', 'Pain', 'Fever'],
            
            # Gastrointestinal
            'omeprazole': ['GERD', 'Peptic Ulcer', 'Gastritis'],
            'pantoprazole': ['GERD', 'Peptic Ulcer'],
            'ranitidine': ['GERD', 'Peptic Ulcer'],
            'cimetidine': ['GERD', 'Peptic Ulcer', 'Gastritis'],
            
            # Ophthalmology
            'dorzolamide': ['Glaucoma', 'Ocular Hypertension'],
            'timolol': ['Glaucoma', 'Ocular Hypertension'],
            'latanoprost': ['Glaucoma', 'Ocular Hypertension'],
            
            # Antibiotics
            'amoxicillin': ['Bacterial Infection', 'Respiratory Infection', 'UTI'],
            'azithromycin': ['Bacterial Infection', 'Respiratory Infection'],
            'ciprofloxacin': ['Bacterial Infection', 'UTI'],
            
            # Diabetes
            'metformin': ['Type 2 Diabetes', 'PCOS'],
            'insulin': ['Type 1 Diabetes', 'Type 2 Diabetes'],
            'glipizide': ['Type 2 Diabetes'],
            
            # Respiratory
            'albuterol': ['Asthma', 'COPD', 'Bronchospasm'],
            'fluticasone': ['Asthma', 'Allergic Rhinitis'],
            'montelukast': ['Asthma', 'Allergic Rhinitis'],
            
            # Pain/Inflammation
            'ibuprofen': ['Pain', 'Inflammation', 'Fever'],
            'paracetamol': ['Pain', 'Fever'],
            'diclofenac': ['Pain', 'Inflammation', 'Arthritis'],
            'naproxen': ['Pain', 'Inflammation', 'Arthritis'],
            
            # Mental Health
            'sertraline': ['Depression', 'Anxiety', 'OCD', 'PTSD'],
            'escitalopram': ['Depression', 'Anxiety'],
            'alprazolam': ['Anxiety', 'Panic Disorder'],
            
            # Beta-blockers (generic)
            'olol': ['Hypertension', 'Cardiac Condition'],  # Suffix match
            'prazole': ['Acid Reflux', 'Gastritis'],  # Suffix match
        }
        
        # Condition severity keywords
        self.severity_keywords = {
            'chronic': 'Chronic condition requiring long-term management',
            'acute': 'Acute condition requiring immediate attention',
            'emergency': 'Emergency - seek immediate medical care'
        }
    
    def suggest_diagnosis(self, medicines_list, ocr_text="", cnn_results=None):
        """
        Suggest possible diagnoses based on prescribed medicines
        
        Args:
            medicines_list: List of medicine names
            ocr_text: Full OCR text (for context)
            cnn_results: CNN analysis results if available
            
        Returns:
            dict with suggested diagnoses, confidence, and recommendations
        """
        try:
            suggestions = {
                "possible_conditions": [],
                "confidence": "Medium",
                "recommendations": [],
                "disclaimer": "⚠️ AI-suggested diagnosis for reference only. Doctor verification required."
            }
            
            if not medicines_list:
                suggestions["message"] = "No medicines detected. Upload clearer prescription."
                return suggestions
            
            # Track conditions and their frequencies
            condition_counts = {}
            condition_sources = {}
            
            # Analyze each medicine
            for medicine in medicines_list:
                medicine_lower = medicine.lower()
                
                # Direct match
                matched = False
                for med_key, conditions in self.medicine_conditions.items():
                    if med_key in medicine_lower:
                        matched = True
                        for condition in conditions:
                            condition_counts[condition] = condition_counts.get(condition, 0) + 1
                            if condition not in condition_sources:
                                condition_sources[condition] = []
                            condition_sources[condition].append(medicine)
                
                # If no match, check suffix patterns (e.g., -olol, -prazole)
                if not matched:
                    for suffix in ['olol', 'prazole', 'cillin', 'mycin']:
                        if medicine_lower.endswith(suffix) and suffix in self.medicine_conditions:
                            for condition in self.medicine_conditions[suffix]:
                                condition_counts[condition] = condition_counts.get(condition, 0) + 1
                                if condition not in condition_sources:
                                    condition_sources[condition] = []
                                condition_sources[condition].append(f"{medicine} (beta-blocker)")
            
            # Sort conditions by frequency
            sorted_conditions = sorted(condition_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Build suggestions
            for condition, count in sorted_conditions[:5]:  # Top 5
                suggestion = {
                    "condition": condition,
                    "confidence": self._calculate_confidence(count, len(medicines_list)),
                    "supporting_medicines": condition_sources[condition],
                    "medicine_count": count
                }
                suggestions["possible_conditions"].append(suggestion)
            
            # Overall confidence
            if sorted_conditions:
                max_count = sorted_conditions[0][1]
                if max_count >= 2:
                    suggestions["confidence"] = "High"
                elif max_count == 1 and len(medicines_list) <= 2:
                    suggestions["confidence"] = "Medium"
                else:
                    suggestions["confidence"] = "Low"
            
            # Add recommendations
            suggestions["recommendations"] = self._generate_recommendations(
                sorted_conditions, medicines_list, ocr_text
            )

            # Suggested specialists based on top conditions
            suggestions["specialists"] = self._suggest_specialists(sorted_conditions)
            
            # Add CNN insights if available
            if cnn_results:
                suggestions["imaging_analysis"] = {
                    "classification": cnn_results.get("class_name", ""),
                    "confidence": cnn_results.get("confidence", 0)
                }
            
            return suggestions
            
        except Exception as e:
            print(f"Diagnosis suggestion error: {e}")
            return {
                "error": "Could not generate diagnosis suggestions",
                "disclaimer": "⚠️ AI-suggested diagnosis for reference only. Doctor verification required."
            }
    
    def _calculate_confidence(self, count, total_medicines):
        """Calculate confidence level"""
        ratio = count / max(1, total_medicines)
        if ratio >= 0.5 and count >= 2:
            return "High"
        elif ratio >= 0.3 or count >= 2:
            return "Medium"
        else:
            return "Low"
    
    def _generate_recommendations(self, conditions, medicines, ocr_text):
        """Generate comprehensive clinical recommendations with risk reduction and preventive measures"""
        recommendations = {
            "lifestyle_changes": [],
            "risk_reduction": [],
            "preventive_measures": [],
            "warning_signs": [],
            "dietary_advice": [],
            "follow_up": []
        }
        
        if not conditions:
            recommendations["follow_up"].append("Review prescription with doctor")
            recommendations["preventive_measures"].append("Ensure proper dosage and timing")
            return self._flatten_recommendations(recommendations)
        
        # Get top condition for detailed recommendations
        top_condition = conditions[0][0].lower()
        
        # HYPERTENSION / HEART CONDITIONS
        if any(keyword in top_condition for keyword in ['hypertension', 'angina', 'heart', 'cardiac']):
            recommendations["lifestyle_changes"] = [
                "🏃 Exercise 30 minutes daily (brisk walking, swimming)",
                "🧘 Practice stress management (meditation, yoga)",
                "🚭 Quit smoking if applicable",
                "🍷 Limit alcohol to 1-2 drinks per day"
            ]
            recommendations["risk_reduction"] = [
                "📊 Monitor blood pressure daily (target: <120/80 mmHg)",
                "⚖️ Maintain healthy weight (BMI 18.5-24.9)",
                "💊 Take medications at same time daily",
                "🩺 Regular cardiology checkups every 3-6 months"
            ]
            recommendations["dietary_advice"] = [
                "🧂 Reduce sodium intake (<2g/day)",
                "🥗 DASH diet: fruits, vegetables, whole grains",
                "🐟 Omega-3 fatty acids (fish, nuts)",
                "❌ Avoid processed and fried foods"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Chest pain or pressure → Emergency room immediately",
                "⚠️ Severe headache, dizziness, vision changes",
                "⚠️ Shortness of breath or irregular heartbeat"
            ]
        
        # DIABETES
        elif 'diabetes' in top_condition:
            recommendations["lifestyle_changes"] = [
                "🏃 Regular physical activity (150 min/week)",
                "⚖️ Weight management if overweight",
                "😴 Adequate sleep (7-8 hours)",
                "🧘 Stress reduction techniques"
            ]
            recommendations["risk_reduction"] = [
                "📊 Monitor blood glucose before meals and bedtime",
                "🦶 Daily foot inspection for cuts/wounds",
                "👁️ Annual eye examination for retinopathy",
                "💉 HbA1c testing every 3 months (target <7%)"
            ]
            recommendations["dietary_advice"] = [
                "🥗 Low glycemic index foods",
                "🍽️ Portion control and meal timing",
                "🚫 Avoid sugary drinks and refined carbs",
                "🥜 Include fiber-rich foods and lean proteins"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Frequent urination, extreme thirst → Check glucose",
                "⚠️ Blurred vision, tingling in extremities",
                "⚠️ Slow healing wounds, frequent infections"
            ]
        
        # RESPIRATORY (ASTHMA/COPD)
        elif any(keyword in top_condition for keyword in ['asthma', 'copd', 'respiratory', 'bronchospasm']):
            recommendations["lifestyle_changes"] = [
                "🚭 Avoid smoking and secondhand smoke",
                "🏃 Regular breathing exercises",
                "💨 Use air purifiers at home",
                "😷 Mask in polluted areas"
            ]
            recommendations["risk_reduction"] = [
                "📊 Peak flow meter monitoring daily",
                "💊 Always carry rescue inhaler",
                "🩺 Pulmonology follow-up every 3-6 months",
                "💉 Annual flu and pneumonia vaccines"
            ]
            recommendations["preventive_measures"] = [
                "🌳 Avoid allergens (pollen, dust, pet dander)",
                "🌡️ Prevent respiratory infections",
                "🏠 Keep home environment clean and ventilated",
                "❄️ Protect airways in cold weather"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Severe breathlessness → Use rescue inhaler",
                "⚠️ Blue lips/fingernails → Emergency room",
                "⚠️ Chest tightness not relieved by medication"
            ]
        
        # GASTROINTESTINAL (GERD/ULCER)
        elif any(keyword in top_condition for keyword in ['gerd', 'ulcer', 'gastritis']):
            recommendations["lifestyle_changes"] = [
                "🍽️ Eat smaller, frequent meals",
                "😴 Elevate head while sleeping (6-8 inches)",
                "⏰ Don't eat 2-3 hours before bedtime",
                "👔 Wear loose-fitting clothing"
            ]
            recommendations["dietary_advice"] = [
                "❌ Avoid: spicy, acidic, fried, fatty foods",
                "❌ Reduce: caffeine, alcohol, chocolate",
                "✅ Include: lean proteins, vegetables, whole grains",
                "💧 Stay hydrated with water (not carbonated)"
            ]
            recommendations["risk_reduction"] = [
                "💊 Take acid reducers as prescribed",
                "🩺 Gastroenterologist if symptoms persist",
                "⚖️ Maintain healthy weight",
                "🚭 Quit smoking (worsens symptoms)"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Black/bloody stools → Emergency care",
                "⚠️ Severe abdominal pain, vomiting blood",
                "⚠️ Unexplained weight loss"
            ]
        
        # INFECTIONS
        elif 'infection' in top_condition:
            recommendations["preventive_measures"] = [
                "💊 Complete full antibiotic course (don't stop early)",
                "🧼 Frequent handwashing",
                "💧 Stay well hydrated",
                "😴 Get adequate rest for recovery"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Fever >103°F or persistent fever",
                "⚠️ Rash, difficulty breathing (allergic reaction)",
                "⚠️ Severe diarrhea or dehydration signs"
            ]
            recommendations["follow_up"] = [
                "📞 Contact doctor if no improvement in 48-72 hours",
                "🩺 Complete follow-up visit as scheduled",
                "🧪 Repeat tests if recommended"
            ]
        
        # MENTAL HEALTH (ANXIETY/DEPRESSION)
        elif any(keyword in top_condition for keyword in ['anxiety', 'depression', 'ocd', 'ptsd']):
            recommendations["lifestyle_changes"] = [
                "🧘 Mindfulness and meditation practice",
                "🏃 Regular exercise (releases endorphins)",
                "😴 Maintain consistent sleep schedule",
                "👥 Social connections and support groups"
            ]
            recommendations["risk_reduction"] = [
                "💊 Take medications consistently",
                "🗣️ Consider therapy (CBT, counseling)",
                "📝 Journal thoughts and feelings",
                "🚫 Limit alcohol and avoid recreational drugs"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Suicidal thoughts → Crisis hotline/ER immediately",
                "⚠️ Severe panic attacks, inability to function",
                "⚠️ Worsening symptoms despite medication"
            ]
            recommendations["follow_up"] = [
                "🩺 Psychiatrist/therapist every 2-4 weeks initially",
                "📊 Monitor mood and side effects",
                "📞 Emergency contacts readily available"
            ]
        
        # PAIN/INFLAMMATION
        elif any(keyword in top_condition for keyword in ['pain', 'inflammation', 'arthritis']):
            recommendations["lifestyle_changes"] = [
                "🏃 Low-impact exercise (swimming, cycling)",
                "❄️ Ice/heat therapy as needed",
                "⚖️ Weight management to reduce joint stress",
                "🧘 Stretching and flexibility exercises"
            ]
            recommendations["risk_reduction"] = [
                "💊 Take pain medication with food to prevent stomach upset",
                "⏰ Don't exceed recommended dosage",
                "🩺 Regular monitoring if long-term use",
                "🚫 Avoid prolonged NSAID use without doctor guidance"
            ]
            recommendations["warning_signs"] = [
                "⚠️ Stomach pain, dark stools (GI bleeding)",
                "⚠️ Swelling, rash (allergic reaction)",
                "⚠️ Pain worsens or doesn't improve"
            ]
        
        # GENERAL RECOMMENDATIONS (for all conditions)
        if not recommendations["follow_up"]:
            recommendations["follow_up"] = [
                "🩺 Regular follow-ups with your doctor",
                "📋 Keep medication list updated",
                "📊 Track symptoms and side effects"
            ]
        
        # Polypharmacy warning
        if len(medicines) >= 5:
            recommendations["warning_signs"].insert(0, "⚠️ Multiple medications: Watch for drug interactions")
            recommendations["follow_up"].insert(0, "💊 Medication review with pharmacist recommended")
        
        return self._flatten_recommendations(recommendations)
    
    def _flatten_recommendations(self, recommendations_dict):
        """Flatten categorized recommendations into a prioritized list"""
        flattened = []
        
        # Priority order
        priority_order = [
            "warning_signs",
            "risk_reduction", 
            "lifestyle_changes",
            "dietary_advice",
            "preventive_measures",
            "follow_up"
        ]
        
        for category in priority_order:
            if recommendations_dict.get(category):
                # Add category header if there are items
                if category == "warning_signs" and recommendations_dict[category]:
                    flattened.append(f"\n⚠️ WARNING SIGNS:")
                flattened.extend(recommendations_dict[category][:3])  # Top 3 per category
        
        return flattened[:12]  # Max 12 recommendations total

    def _suggest_specialists(self, conditions):
        """Return detailed specialist recommendations with reasoning"""
        seen = set()
        result = []
        
        # Enhanced specialist mapping with reasons
        specialist_details = {
            'Cardiologist': {
                'keywords': ['hypertension', 'angina', 'arrhythmia', 'heart', 'cardiac'],
                'reason': 'For heart and blood pressure management',
                'when': 'Schedule within 2-4 weeks for non-emergency'
            },
            'Endocrinologist': {
                'keywords': ['diabetes', 'glucose'],
                'reason': 'For diabetes and hormonal disorder management',
                'when': 'Schedule within 3-4 weeks, sooner if glucose uncontrolled'
            },
            'Pulmonologist': {
                'keywords': ['asthma', 'copd', 'respiratory', 'bronchospasm'],
                'reason': 'For lung and breathing condition management',
                'when': 'Schedule within 2-3 weeks, urgent if severe symptoms'
            },
            'Gastroenterologist': {
                'keywords': ['gerd', 'ulcer', 'gastritis', 'gastro'],
                'reason': 'For digestive system and stomach issues',
                'when': 'Schedule within 4-6 weeks'
            },
            'Ophthalmologist': {
                'keywords': ['glaucoma', 'ocular', 'ophthal'],
                'reason': 'For eye pressure and vision problems',
                'when': 'Schedule within 1-2 weeks (glaucoma requires prompt care)'
            },
            'Psychiatrist': {
                'keywords': ['anxiety', 'depression', 'ocd', 'ptsd'],
                'reason': 'For mental health medication management',
                'when': 'Schedule within 2-3 weeks, urgent if crisis'
            },
            'Nephrologist': {
                'keywords': ['uti', 'nephropathy', 'kidney'],
                'reason': 'For kidney function monitoring',
                'when': 'Schedule within 3-4 weeks'
            },
            'General Physician': {
                'keywords': ['infection', 'fever', 'pain'],
                'reason': 'For overall health assessment and medication review',
                'when': 'Schedule routine checkup within 1-2 weeks'
            }
        }
        
        for condition, _ in conditions[:5]:
            name = condition.lower()
            for specialist, details in specialist_details.items():
                if any(k in name for k in details['keywords']):
                    if specialist not in seen:
                        seen.add(specialist)
                        result.append({
                            'specialist': specialist,
                            'reason': details['reason'],
                            'when_to_schedule': details['when'],
                            'condition': condition
                        })
        
        # Fallback
        if not result:
            result.append({
                'specialist': 'General Physician',
                'reason': 'For comprehensive health evaluation',
                'when_to_schedule': 'Schedule within 1-2 weeks',
                'condition': 'General Health'
            })
        
        return result[:3]  # Top 3 most relevant specialists


# Singleton instance
diagnosis_suggestor = DiagnosisSuggestor()

