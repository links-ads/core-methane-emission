"""
core/conversions.py
Logica di conversione delle emissioni secondo UNI 15446 e IPCC
"""

import math

# Costanti
PPM_PER_PERCENT = 10000        # 1% Vol = 10000 PPM
GWP_CH4 = 29.8                 # Global Warming Potential metano (IPCC)
A_COEFF = 0.00000187           # Coefficiente A (UNI 15446, Tabella C.1)
B_COEFF = 0.873                # Coefficiente B (UNI 15446, Tabella C.1)


def percent_to_ppm(percent_vol: float) -> float:
    """Converte %Vol in PPM"""
    return percent_vol * PPM_PER_PERCENT


def grh_ch4_to_kgh_ch4(grh: float) -> float:
    """Converte gr/h CH4 in Kg/h CH4"""
    return grh / 1000.0


def ppm_to_kgh_ch4(ppm: float) -> float:
    """
    Converte PPM in Kg/h CH4
    Formula UNI 15446 Tabella C.1: ER = A * (SV)^B
    A = 0.00000187, B = 0.873, SV = valore in PPM
    """
    if ppm <= 0:
        return 0.0
    return A_COEFF * math.pow(ppm, B_COEFF)


def kgh_ch4_to_kgh_co2(kgh_ch4: float) -> float:
    """
    Converte Kg/h CH4 in Kg/h CO2 equivalente
    Coefficiente GWP = 29.8 (IPCC)
    """
    return kgh_ch4 * GWP_CH4


def convert_emission(unit: str, value: float) -> dict:
    """
    Conversione completa dell'emissione partendo dall'unità di misura inserita.
    
    Ritorna un dizionario con tutti i valori intermedi e finali.
    """
    result = {
        "input_unit": unit,
        "input_value": value,
        "ppm": None,
        "kgh_ch4": None,
        "kgh_co2": None,
        "error": None,
    }

    try:
        if unit == "PPM":
            result["ppm"] = value
            result["kgh_ch4"] = ppm_to_kgh_ch4(value)

        elif unit == "%Vol":
            result["ppm"] = percent_to_ppm(value)
            result["kgh_ch4"] = ppm_to_kgh_ch4(result["ppm"])

        elif unit == "gr/h CH4":
            result["kgh_ch4"] = grh_ch4_to_kgh_ch4(value)
            # Per gr/h CH4 non passiamo per PPM
            result["ppm"] = None

        else:
            result["error"] = f"Unità non riconosciuta: {unit}"
            return result

        result["kgh_co2"] = kgh_ch4_to_kgh_co2(result["kgh_ch4"])

    except Exception as e:
        result["error"] = str(e)

    return result
