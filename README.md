# Methane Emission

Applicazione Python per la raccolta dati di campo, conversione delle emissioni di metano e salvataggio nel dataset Excel.

---

## Struttura del Progetto

```
methane_emission/
├── main.py                  # Entry point
├── requirements.txt
├── core/
│   ├── conversions.py       # Formule di conversione (UNI 15446, IPCC)
│   └── models.py            # Dataclass: SurveyData, EmissionData, Intervento
├── data/
│   └── excel_manager.py     # Lettura/scrittura file Excel
└── ui/
    ├── app.py               # Finestra principale + Notebook
    ├── survey_frame.py      # Sezione Survey (9 campi)
    ├── emission_frame.py    # Sezione Emissione + pulsante Converti
    ├── result_frame.py      # Pannello risultati conversione
    └── history_frame.py     # Tab storico interventi salvati
```

---

## Installazione

```bash
cd methane_emission
uv pip install -r requirements.txt
python main.py
```

---

## Formule di Conversione

### Da PPM a Kg/h CH4 (UNI 15446, Tabella C.1)

```
ER = A × (SV)^B
A = 0.00000187
B = 0.873
SV = valore in PPM
```

### Da %Vol a PPM

```
PPM = %Vol × 10.000
(Esempio: 27 %Vol → 270.000 PPM)
```

### Da Kg/h CH4 a Kg/h CO2 equivalente (IPCC)

```
Kg/h CO2 = Kg/h CH4 × 29.8
(GWP metano = 29.8 volte CO2)
```

---

## Output Excel

Il file `interventi_emissioni.xlsx` viene creato automaticamente alla prima registrazione.

Colonne salvate:
| Survey (9 col) | Emissione (5 col) |
|---|---|
| Tipologia Sito, Tubazione, Materiale, Pressione, Dispersione, Riparazione, Interruzione, Date | Unità, Valore, PPM, Kg/h CH4, **Fattore Emissione Kg/h CO2** |
