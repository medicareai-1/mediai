"""
Imaging Recommendations Engine
Provides clinical recommendations for CT, MRI, and X-ray findings
"""

class ImagingRecommendations:
    def __init__(self):
        """Initialize imaging recommendation database"""
        
        # Imaging findings → recommendations mapping
        self.finding_recommendations = {
            'lesion': {
                'severity': 'HIGH',
                'specialist': {
                    'name': 'Radiologist + Referring Physician',
                    'urgency': 'URGENT - Within 24-48 hours',
                    'reason': 'Lesion requires immediate evaluation and biopsy consideration'
                },
                'next_steps': [
                    '🩺 Immediate follow-up with referring physician',
                    '🔬 May need biopsy or additional imaging (MRI with contrast)',
                    '📋 Get complete medical history and previous scans',
                    '⏰ Do not delay - early detection improves outcomes'
                ],
                'warning_signs': [
                    '⚠️ NEW symptoms: severe headache, vision changes, seizures → ER',
                    '⚠️ Rapid symptom progression',
                    '⚠️ Neurological deficits (weakness, numbness, speech changes)'
                ],
                'what_it_means': 'A lesion is an abnormal area detected in the scan that requires further investigation to determine if it is benign or requires treatment.',
                'lifestyle': [
                    '📝 Document all symptoms daily',
                    '💊 Continue current medications unless doctor advises otherwise',
                    '🚭 Avoid smoking and alcohol',
                    '😴 Adequate rest and stress management'
                ]
            },
            'fracture': {
                'severity': 'MODERATE-HIGH',
                'specialist': {
                    'name': 'Orthopedic Surgeon',
                    'urgency': 'Within 1-3 days for stable fractures, immediate for displaced',
                    'reason': 'Fracture management and treatment planning'
                },
                'next_steps': [
                    '🦴 Orthopedic consultation for treatment plan',
                    '🩹 Immobilization (cast/splint) if not already done',
                    '📊 Follow-up X-rays in 1-2 weeks to monitor healing',
                    '💊 Pain management and anti-inflammatories as prescribed'
                ],
                'warning_signs': [
                    '⚠️ Increased pain, swelling, or numbness → Contact doctor',
                    '⚠️ Cold/blue fingers or toes (circulation problem) → ER',
                    '⚠️ Signs of infection: fever, wound drainage'
                ],
                'what_it_means': 'A bone fracture (break) has been detected. Treatment depends on location, severity, and alignment.',
                'lifestyle': [
                    '❄️ Apply ice 20 min every 2-3 hours first 48 hours',
                    '⬆️ Elevate injured area above heart level',
                    '⚖️ Avoid weight-bearing until cleared',
                    '🥗 High-calcium diet for bone healing'
                ]
            },
            'pneumonia': {
                'severity': 'MODERATE-HIGH',
                'specialist': {
                    'name': 'Pulmonologist or Internal Medicine',
                    'urgency': 'Within 24-48 hours if outpatient, immediate if severe',
                    'reason': 'Respiratory infection requiring antibiotic therapy and monitoring'
                },
                'next_steps': [
                    '💊 Antibiotic course (if not already started)',
                    '🩺 Follow-up chest X-ray in 4-6 weeks to ensure resolution',
                    '💧 Aggressive hydration',
                    '🌡️ Monitor temperature and oxygen saturation'
                ],
                'warning_signs': [
                    '⚠️ Difficulty breathing, chest pain → ER immediately',
                    '⚠️ Fever >103°F or persistent high fever',
                    '⚠️ Confusion, low oxygen (lips/nails blue)',
                    '⚠️ Coughing up blood'
                ],
                'what_it_means': 'Lung infection causing inflammation. Can be bacterial, viral, or fungal.',
                'lifestyle': [
                    '😴 Plenty of rest - your body needs energy to fight infection',
                    '💧 Drink 8-10 glasses of water daily',
                    '🚭 No smoking - critical for recovery',
                    '🧘 Deep breathing exercises to prevent fluid buildup'
                ]
            },
            'tumor': {
                'severity': 'HIGH',
                'specialist': {
                    'name': 'Oncologist + Surgeon',
                    'urgency': 'URGENT - Within 48-72 hours',
                    'reason': 'Tumor requires oncology evaluation for biopsy and treatment planning'
                },
                'next_steps': [
                    '🏥 Multidisciplinary consultation (oncology, surgery, radiology)',
                    '🔬 Tissue biopsy for definitive diagnosis',
                    '📊 Staging workup (additional imaging, blood tests)',
                    '📋 Tumor board review for treatment recommendations'
                ],
                'warning_signs': [
                    '⚠️ Rapid symptom changes → Contact oncologist immediately',
                    '⚠️ New neurological symptoms, severe pain',
                    '⚠️ Unexplained weight loss, night sweats'
                ],
                'what_it_means': 'An abnormal growth detected that needs biopsy to determine if benign or malignant.',
                'lifestyle': [
                    '💪 Maintain nutrition - consult oncology dietitian',
                    '🧘 Stress management and emotional support',
                    '👨‍👩‍👧 Family support and counseling resources',
                    '📝 Keep detailed symptom log'
                ]
            },
            'normal': {
                'severity': 'LOW',
                'specialist': {
                    'name': 'Routine Follow-up with Primary Care',
                    'urgency': 'Routine - schedule per doctor recommendation',
                    'reason': 'No urgent findings, routine monitoring'
                },
                'next_steps': [
                    '✅ Discuss results with your doctor',
                    '📅 Follow routine screening schedule',
                    '🩺 Address any symptoms you\'re experiencing',
                    '📋 Keep scan results for your records'
                ],
                'warning_signs': [
                    '⚠️ New symptoms develop → Contact your doctor',
                    '⚠️ Symptoms worsen despite normal scan'
                ],
                'what_it_means': 'No significant abnormalities detected on this imaging study.',
                'lifestyle': [
                    '✅ Continue healthy lifestyle habits',
                    '🏃 Regular exercise as appropriate',
                    '🥗 Balanced diet',
                    '😴 Adequate sleep and stress management'
                ]
            },
            'inflammation': {
                'severity': 'MODERATE',
                'specialist': {
                    'name': 'Internal Medicine or Specialist per region',
                    'urgency': 'Within 1-2 weeks',
                    'reason': 'Inflammatory process needs evaluation and treatment'
                },
                'next_steps': [
                    '🔬 Blood tests to identify cause (infection, autoimmune)',
                    '💊 Anti-inflammatory medication if appropriate',
                    '📊 Follow-up imaging in 4-6 weeks',
                    '🩺 Monitor for improvement or worsening'
                ],
                'warning_signs': [
                    '⚠️ Fever, chills, or worsening symptoms',
                    '⚠️ Severe pain not controlled by medication',
                    '⚠️ New symptoms develop'
                ],
                'what_it_means': 'Inflammation detected, which could be from infection, injury, or other causes.',
                'lifestyle': [
                    '😴 Rest and avoid strenuous activity',
                    '💧 Stay well hydrated',
                    '🥗 Anti-inflammatory diet (fruits, vegetables, omega-3)',
                    '❄️ Ice/heat therapy as appropriate'
                ]
            },
            'fluid': {
                'severity': 'MODERATE',
                'specialist': {
                    'name': 'Specialist based on location (Pulmonologist, Cardiologist)',
                    'urgency': 'Within 3-7 days',
                    'reason': 'Fluid accumulation needs evaluation for underlying cause'
                },
                'next_steps': [
                    '🩺 Clinical correlation with symptoms',
                    '🔬 Additional tests (echocardiogram, blood tests)',
                    '💊 Diuretics may be prescribed if appropriate',
                    '📊 Monitor for resolution or progression'
                ],
                'warning_signs': [
                    '⚠️ Increasing shortness of breath → ER',
                    '⚠️ Chest pain, rapid heart rate',
                    '⚠️ Swelling in legs or abdomen increases'
                ],
                'what_it_means': 'Abnormal fluid collection that can indicate various conditions.',
                'lifestyle': [
                    '🧂 Reduce salt intake',
                    '💧 Monitor fluid intake per doctor guidance',
                    '⚖️ Daily weight monitoring',
                    '🛏️ Elevate legs when resting if peripheral edema'
                ]
            },
            'calcification': {
                'severity': 'LOW-MODERATE',
                'specialist': {
                    'name': 'Cardiologist or Primary Care',
                    'urgency': 'Within 2-4 weeks',
                    'reason': 'Calcifications need evaluation for cardiovascular risk'
                },
                'next_steps': [
                    '❤️ Cardiovascular risk assessment',
                    '📊 Lipid panel and metabolic screening',
                    '🩺 Consider calcium score if coronary calcification',
                    '💊 Statin therapy may be recommended'
                ],
                'warning_signs': [
                    '⚠️ Chest pain, shortness of breath → ER',
                    '⚠️ Heart palpitations or irregular rhythm',
                    '⚠️ Unexplained fatigue or dizziness'
                ],
                'what_it_means': 'Calcium deposits often indicate atherosclerosis (arterial plaque buildup).',
                'lifestyle': [
                    '🏃 Regular aerobic exercise (30 min daily)',
                    '🥗 Heart-healthy diet (Mediterranean)',
                    '🚭 Smoking cessation critical',
                    '⚖️ Weight management and stress reduction'
                ]
            }
        }
        
        # Body region-specific general guidance
        self.region_guidance = {
            'head': {
                'general': 'Brain imaging findings require neurological evaluation',
                'follow_up': 'Neurology or Neurosurgery consultation',
                'monitoring': 'May need repeat imaging in 3-6 months'
            },
            'chest': {
                'general': 'Chest findings require pulmonary/cardiac evaluation',
                'follow_up': 'Pulmonology or Cardiology consultation',
                'monitoring': 'Follow-up chest imaging typically in 3-12 months'
            },
            'abdomen': {
                'general': 'Abdominal findings need gastroenterology evaluation',
                'follow_up': 'Gastroenterologist or General Surgeon',
                'monitoring': 'Abdominal ultrasound or CT follow-up as needed'
            },
            'spine': {
                'general': 'Spinal findings may need orthopedic/neurosurgery review',
                'follow_up': 'Orthopedic Surgeon or Neurosurgeon',
                'monitoring': 'Physical therapy often beneficial'
            },
            'musculoskeletal': {
                'general': 'Bone/joint findings need orthopedic evaluation',
                'follow_up': 'Orthopedic Surgeon',
                'monitoring': 'Repeat X-rays in 4-6 weeks for fractures'
            }
        }
    
    def generate_recommendations(self, imaging_result, document_type='ct_scan'):
        """
        Generate comprehensive recommendations for imaging findings
        
        Args:
            imaging_result: Dict with imaging analysis results
            document_type: 'ct_scan', 'mri', or 'xray'
            
        Returns:
            Dict with recommendations, specialists, next steps
        """
        try:
            recommendations = {
                'recommendations': [],
                'specialist': {},
                'next_steps': [],
                'warning_signs': [],
                'what_it_means': '',
                'urgency_level': 'ROUTINE',
                'disclaimer': '⚠️ Imaging interpretation for educational purposes. Radiologist report is definitive.'
            }
            
            # Extract findings from result
            label = None
            findings = []
            region = 'unknown'
            confidence = 0.0
            
            if document_type == 'ct_scan':
                label = imaging_result.get('ct_label', '').lower()
                findings = imaging_result.get('ct_findings', [])
                region = imaging_result.get('ct_body_region', 'unknown').lower()
                confidence = imaging_result.get('ct_confidence', 0.0)
            elif document_type == 'mri':
                label = imaging_result.get('mri_label', '').lower()
                findings = imaging_result.get('mri_findings', [])
                region = imaging_result.get('mri_body_region', 'unknown').lower()
                confidence = imaging_result.get('mri_confidence', 0.0)
            elif document_type == 'xray':
                label = imaging_result.get('cnn_class', '').lower()
                findings = imaging_result.get('cnn_findings', [])
                confidence = imaging_result.get('cnn_confidence', 0.0)
            
            # Match findings to recommendations
            matched_finding = None
            for keyword, rec_data in self.finding_recommendations.items():
                if keyword in label or any(keyword in str(f).lower() for f in findings):
                    matched_finding = keyword
                    break
            
            # Use matched recommendations or defaults
            if matched_finding:
                rec_data = self.finding_recommendations[matched_finding]
                recommendations['specialist'] = rec_data['specialist']
                recommendations['next_steps'] = rec_data['next_steps']
                recommendations['warning_signs'] = rec_data['warning_signs']
                recommendations['what_it_means'] = rec_data['what_it_means']
                recommendations['urgency_level'] = rec_data['severity']
                recommendations['recommendations'].extend(rec_data.get('lifestyle', []))
            else:
                # Default recommendations if no match
                recommendations['specialist'] = {
                    'name': 'Primary Care Physician',
                    'urgency': 'Routine follow-up within 1-2 weeks',
                    'reason': 'Review imaging results and clinical correlation'
                }
                recommendations['next_steps'] = [
                    '🩺 Schedule follow-up with your doctor',
                    '📋 Bring imaging report to appointment',
                    '📝 Document any symptoms you\'re experiencing'
                ]
                recommendations['warning_signs'] = [
                    '⚠️ New or worsening symptoms → Contact doctor',
                    '⚠️ Severe pain, fever, or neurological changes → ER'
                ]
            
            # Add region-specific guidance
            if region in self.region_guidance:
                region_info = self.region_guidance[region]
                recommendations['region_guidance'] = {
                    'general': region_info['general'],
                    'specialist': region_info['follow_up'],
                    'monitoring': region_info['monitoring']
                }
            
            # Confidence-based messaging
            if confidence > 0.85:
                recommendations['confidence_note'] = '✅ High confidence in finding detection'
            elif confidence > 0.70:
                recommendations['confidence_note'] = '⚠️ Moderate confidence - clinical correlation recommended'
            else:
                recommendations['confidence_note'] = '⚠️ Low confidence - radiologist review essential'
            
            # Add key findings summary
            if findings:
                recommendations['key_findings_summary'] = findings[:5]  # Top 5 findings
            
            return recommendations
            
        except Exception as e:
            print(f"Imaging recommendations error: {e}")
            return {
                'error': 'Could not generate imaging recommendations',
                'specialist': {
                    'name': 'Radiologist + Primary Care',
                    'urgency': 'Within 1 week',
                    'reason': 'Review imaging findings'
                },
                'disclaimer': '⚠️ Imaging interpretation for educational purposes. Radiologist report is definitive.'
            }


# Singleton instance
imaging_recommendations = ImagingRecommendations()

