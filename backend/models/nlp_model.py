"""
NLP Model - Lightweight, regex-based extractor (works without spaCy)
Provides practical medicine, dosage, and duration extraction without heavy deps
"""

import re

class NLPModel:
    def __init__(self):
        """Initialize lightweight NLP model"""
        print("NLP Model initialized (Regex mode - no spaCy required)")
        
        self.medicine_keywords = [
            'mg', 'ml', 'tablet', 'capsule', 'syrup', 'injection',
            'suspension', 'drops', 'cream', 'ointment', 'inhaler'
        ]
    
    def extract_entities(self, text):
        """
        Extract medical entities from text (regex-based, lightweight)

        Args:
            text: String containing medical text
            
        Returns:
            dict with entities, medicines, dosages, durations
        """
        try:
            # Simple regex-based extraction
            medicines = self.extract_medicines_simple(text)
            dosages = self.extract_dosages_simple(text)
            durations = self.extract_durations_simple(text)
            
            return {
                "entities": [],
                "custom_entities": [],
                "medicines": medicines,
                "dosages": dosages,
                "durations": durations,
                "summary": self._generate_summary(medicines, dosages, durations)
            }
            
        except Exception as e:
            print(f"NLP error: {str(e)}")
            return {
                "entities": [],
                "medicines": [],
                "dosages": [],
                "durations": [],
                "error": str(e)
            }
    
    def extract_medicines_simple(self, text):
        """Enhanced medicine extraction using regex"""
        medicines = []
        seen_medicines = set()
        
        # Expanded medicine patterns - optimized for handwritten prescriptions
        medicine_patterns = [
            # Pattern 1: Common medicine suffixes (catches -olol, -prazole, -tidine, etc.)
            r'\b([A-Z][a-z]+(?:cillin|mycin|fenac|profen|azole|prazole|dipine|olol|statin|sartan|floxacin|tidine|mab|zolam|amide|prelol|taloc))\b',
            
            # Pattern 2: Specific common medicines (including cardiovascular drugs like in the prescription)
            r'\b(Amoxicillin|Ibuprofen|Paracetamol|Acetaminophen|Aspirin|Multivitamin|Vitamin|Azithromycin|Ciprofloxacin|Metformin|Omeprazole|Losartan|Amlodipine|Atorvastatin|Simvastatin|Lisinopril|Metoprolol|Levothyroxine|Gabapentin|Sertraline|Citalopram|Escitalopram|Fluoxetine|Alprazolam|Lorazepam|Clonazepam|Prednisone|Dexamethasone|Cetirizine|Loratadine|Montelukast|Albuterol|Fluticasone|Warfarin|Clopidogrel|Insulin|Glipizide|Hydrochlorothiazide|Furosemide|Spironolactone|Pantoprazole|Ranitidine|Tramadol|Codeine|Morphine|Oxycodone|Diclofenac|Naproxen|Celecoxib|Tamsulosin|Finasteride|Sildenafil|Tadalafil|Betaloc|Metoprolol|Dorzolamide|Cimetidine|Oxprelol|Carvedilol|Bisoprolol|Atenolol|Propranolol|Timolol|Labetalol)\b',
            
            # Pattern 3: Generic pattern - Capitalized word followed by dosage (catches handwritten variations)
            r'\b([A-Z][a-z]{3,})\s*\d+\s*(?:mg|ml|g|mcg)\b',
            
            # Pattern 4: Medicine name with "tab" or "tabs" (common in prescriptions)
            r'\b([A-Z][a-z]{4,})\s*\d+\s*(?:mg|ml)?\s*[-–—]\s*\d+\s*tabs?\b',
            
            # Pattern 5: Less strict - any capitalized word 5+ letters near dosage indicators
            r'\b([A-Z][a-z]{4,})\b(?=.*?(?:\d+\s*(?:mg|ml|tab)))'
        ]
        
        for pattern in medicine_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                med_name = match.group(0).strip()
                # Avoid duplicates
                if med_name.lower() not in seen_medicines:
                    seen_medicines.add(med_name.lower())
                    medicines.append({
                        "text": med_name,
                        "label": "MEDICINE",
                        "start": match.start(),
                        "end": match.end()
                    })
        
        return medicines
    
    def extract_dosages_simple(self, text):
        """Simple dosage extraction"""
        dosages = []
        
        # Pattern for dosages like "500mg", "2 tablets"
        dosage_pattern = r'\b(\d+\s?(?:mg|ml|g|mcg|tablet|tablets|capsule|capsules))\b'
        
        matches = re.finditer(dosage_pattern, text, re.IGNORECASE)
        for match in matches:
            dosages.append({
                "text": match.group(0),
                "label": "DOSAGE",
                "start": match.start(),
                "end": match.end()
            })
        
        return dosages
    
    def extract_durations_simple(self, text):
        """Simple duration extraction"""
        durations = []
        
        # Pattern for durations like "7 days", "2 weeks"
        duration_pattern = r'\b(\d+\s?(?:day|days|week|weeks|month|months))\b'
        
        matches = re.finditer(duration_pattern, text, re.IGNORECASE)
        for match in matches:
            durations.append({
                "text": match.group(0),
                "label": "DURATION",
                "start": match.start(),
                "end": match.end()
            })
        
        return durations
    
    def _generate_summary(self, medicines, dosages, durations):
        """Generate a text summary"""
        summary_parts = []
        
        if medicines:
            med_names = [m["text"] for m in medicines[:3]]
            summary_parts.append(f"Medicines: {', '.join(med_names)}")
        
        if dosages:
            summary_parts.append(f"{len(dosages)} dosage instruction(s)")
        
        if durations:
            dur_texts = [d["text"] for d in durations[:2]]
            summary_parts.append(f"Duration: {', '.join(dur_texts)}")
        
        return "; ".join(summary_parts) if summary_parts else "No medical information extracted"
