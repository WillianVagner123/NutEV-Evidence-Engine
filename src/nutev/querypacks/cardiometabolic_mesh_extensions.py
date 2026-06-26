from __future__ import annotations

from nutev.querypacks import provider_queries

CARDIOMETABOLIC_MESH_EXTENSIONS = {
    "adiposity": "Adiposity",
    "central adiposity": "Obesity, Abdominal",
    "abdominal adiposity": "Obesity, Abdominal",
    "abdominal obesity": "Obesity, Abdominal",
    "central obesity": "Obesity, Abdominal",
    "visceral adiposity": "Intra-Abdominal Fat",
    "visceral fat": "Intra-Abdominal Fat",
    "body mass index": "Body Mass Index",
    "bmi": "Body Mass Index",
    "waist circumference": "Waist Circumference",
    "waist-to-height ratio": "Waist Circumference",
    "waist to height ratio": "Waist Circumference",
    "waist-to-hip ratio": "Waist-Hip Ratio",
    "waist to hip ratio": "Waist-Hip Ratio",
    "cardiometabolic health": "Cardiovascular Diseases",
    "metabolic health": "Metabolic Syndrome",
    "blood pressure": "Blood Pressure",
    "ldl cholesterol": "Cholesterol, LDL",
    "non-hdl cholesterol": "Cholesterol",
    "non hdl cholesterol": "Cholesterol",
    "lipid lowering": "Hypolipidemic Agents",
    "triglyceride lowering": "Triglycerides",
    "glucose intolerance": "Glucose Intolerance",
    "impaired fasting glucose": "Prediabetic State",
    "impaired glucose tolerance": "Glucose Intolerance",
    "dysglycemia": "Blood Glucose",
    "dysglycaemia": "Blood Glucose",
    "hepatic steatosis": "Fatty Liver",
}


def apply_cardiometabolic_mesh_extensions() -> None:
    for term, mesh in CARDIOMETABOLIC_MESH_EXTENSIONS.items():
        provider_queries.PUBMED_MESH_MAP.setdefault(term, mesh)
