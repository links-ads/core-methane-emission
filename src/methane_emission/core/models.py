"""
core/models.py
Modelli dati per il tracciamento delle emissioni
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional


@dataclass
class SurveyData:
    """Dati raccolti dalla sezione Survey"""

    tipologia_sito: str = ""
    tubazione: str = ""  # Aerea o Interrata
    tipologia_materiale: str = ""
    pressione_esercizio: float = 0.0
    classificazione_dispersione: str = ""
    tipologia_riparazione: str = ""
    interruzione_fornitura: str = ""  # SI / NO
    data_rilevamento_perdita: Optional[date] = None
    data_esecuzione_riparazione: Optional[date] = None


@dataclass
class EmissionData:
    """Dati delle emissioni rilevate e convertite"""

    input_unit: str = ""  # PPM, %Vol, gr/h CH4
    input_value: float = 0.0
    ppm: Optional[float] = None
    kgh_ch4: Optional[float] = None
    kgh_co2: Optional[float] = None


@dataclass
class Intervento:
    """Record completo di un singolo intervento"""

    survey: SurveyData = field(default_factory=SurveyData)
    emission: EmissionData = field(default_factory=EmissionData)

    def to_excel_row(self) -> dict:
        """Serializza l'intervento come riga per Excel"""
        s = self.survey
        e = self.emission
        return {
            "Tipologia Sito (ME)": s.tipologia_sito,
            "Tipologia Sito (LCA)": s.tubazione,
            "Tipologia di Materiale": s.tipologia_materiale,
            "Pressione Esercizio (bar)": s.pressione_esercizio,
            "Classificazione Dispersione": s.classificazione_dispersione,
            "Tipologia Riparazione": s.tipologia_riparazione,
            "Interruzione Fornitura": s.interruzione_fornitura,
            "Data Rilevamento Perdita": (
                s.data_rilevamento_perdita.isoformat()
                if s.data_rilevamento_perdita
                else ""
            ),
            "Data Esecuzione Riparazione": (
                s.data_esecuzione_riparazione.isoformat()
                if s.data_esecuzione_riparazione
                else ""
            ),
            "Unità di Misura Emissione": e.input_unit,
            "Valore Emissione": e.input_value,
            "PPM": e.ppm if e.ppm is not None else "",
            "Kg/h CH4": e.kgh_ch4 if e.kgh_ch4 is not None else "",
            "Fattore Emissione Kg/h CO2": e.kgh_co2 if e.kgh_co2 is not None else "",
        }
