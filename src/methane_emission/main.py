"""
app_gradio.py
Emission Tracker — interfaccia Gradio
Sostituisce ui/ con un'unica app web servita in locale.
"""

import gradio as gr
from datetime import date, datetime

from core.conversions import convert_emission, GWP_CH4, A_COEFF, B_COEFF
from core.models import Intervento, SurveyData, EmissionData
from data.excel_manager import save_intervento, get_all_interventi, EXCEL_FILE


def _fmt(v, dec=6):
    if v is None or v == "":
        return "—"
    try:
        return f"{float(v):.{dec}f}"
    except Exception:
        return str(v)


def _parse_date(s: str):
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except Exception:
            pass
    return None


def do_convert(unit, value_str):
    try:
        value = float(str(value_str).replace(",", "."))
    except Exception:
        return "Valore non valido", "", "", ""

    res = convert_emission(unit, value)
    if res.get("error"):
        return f"{res['error']}", "", "", ""

    ppm_str = _fmt(res["ppm"], 2) if res["ppm"] is not None else "N/A"
    ch4_str = _fmt(res["kgh_ch4"], 8)
    co2_str = _fmt(res["kgh_co2"], 6)

    note = (
        f"Formula UNI 15446 Tab C.1 — ER = {A_COEFF} × SV^{B_COEFF}   |   GWP CH₄ = {GWP_CH4} (IPCC)"
        if unit in ("PPM", "%Vol")
        else f"Conversione diretta gr/h → Kg/h × {GWP_CH4} (GWP IPCC)"
    )
    return note, ppm_str, ch4_str, co2_str


def do_save(
    tipologia_sito,
    tubazione,
    tipologia_materiale,
    pressione,
    classif_dispersione,
    tipologia_riparazione,
    interruzione,
    data_rilevamento,
    data_riparazione,
    unit,
    value_str,
):
    # Validate
    if not tipologia_sito or not tubazione:
        return "Compilare almeno Tipologia Sito e Tubazione.", load_history()

    try:
        pressione_f = float(str(pressione).replace(",", ".")) if pressione else 0.0
    except Exception:
        return "Pressione non valida.", load_history()

    try:
        value = float(str(value_str).replace(",", "."))
    except Exception:
        return "Valore emissione non valido.", load_history()

    res = convert_emission(unit, value)
    if res.get("error"):
        return f"{res['error']}", load_history()

    survey = SurveyData(
        tipologia_sito=tipologia_sito,
        tubazione=tubazione,
        tipologia_materiale=tipologia_materiale or "",
        pressione_esercizio=pressione_f,
        classificazione_dispersione=classif_dispersione or "",
        tipologia_riparazione=tipologia_riparazione or "",
        interruzione_fornitura=interruzione or "",
        data_rilevamento_perdita=(
            _parse_date(data_rilevamento) if data_rilevamento else None
        ),
        data_esecuzione_riparazione=(
            _parse_date(data_riparazione) if data_riparazione else None
        ),
    )
    emission = EmissionData(
        input_unit=res["input_unit"],
        input_value=res["input_value"],
        ppm=res["ppm"],
        kgh_ch4=res["kgh_ch4"],
        kgh_co2=res["kgh_co2"],
    )

    try:
        row = save_intervento(Intervento(survey=survey, emission=emission))
        return f"Salvato alla riga {row} di `{EXCEL_FILE}`", load_history()
    except Exception as e:
        return f"Errore salvataggio: {e}", load_history()


def load_history():
    records = get_all_interventi()
    if not records:
        return []
    rows = []
    for r in records:
        rows.append(
            [
                r.get("Tipologia Sito (Categoria)", ""),
                r.get("Tubazione", ""),
                r.get("Tipologia Materiale", ""),
                _fmt(r.get("Pressione Esercizio (bar)"), 2),
                r.get("Classificazione Dispersione", ""),
                r.get("Tipologia Riparazione", ""),
                r.get("Interruzione Fornitura", ""),
                r.get("Data Rilevamento Perdita", ""),
                r.get("Data Esecuzione Riparazione", ""),
                r.get("Unità Emissione", ""),
                _fmt(r.get("Valore Inserito"), 4),
                _fmt(r.get("PPM"), 2),
                _fmt(r.get("Kg/h CH4"), 8),
                _fmt(r.get("Fattore Emissione Kg/h CO2"), 6),
            ]
        )
    return rows


HISTORY_HEADERS = [
    "Sito",
    "Tubazione",
    "Materiale",
    "Pressione (bar)",
    "Dispersione",
    "Riparazione",
    "Interruzione",
    "Data Rilevamento",
    "Data Riparazione",
    "Unità",
    "Valore Input",
    "PPM",
    "Kg/h CH4",
    "Kg/h CO2 eq.",
]

THEME = gr.themes.Soft(
    primary_hue="teal",
    secondary_hue="violet",
    neutral_hue="slate",
    font=gr.themes.GoogleFont("Inter"),
)

with gr.Blocks(title="Emission Tracker") as demo:

    gr.Markdown(
        """
    # 🏭 Emission Tracker — Singolo Intervento
    Raccolta dati Survey · Conversione emissioni CH₄ · Dataset Excel
    """
    )

    with gr.Tabs():
        with gr.Tab("➕ Nuovo Intervento"):

            # Survey section
            gr.Markdown("## 📍 SURVEY — Dati di Campo")
            with gr.Group():
                with gr.Row():
                    tipologia_sito = gr.Dropdown(
                        label="Tipologia Sito (Categoria) *",
                        choices=[
                            "Distribuzione",
                            "Trasporto",
                            "Industriale",
                            "Civile",
                            "Altro",
                        ],
                    )
                    tubazione = gr.Dropdown(
                        label="Tubazione *",
                        choices=["Aerea", "Interrata"],
                    )
                    tipologia_materiale = gr.Dropdown(
                        label="Tipologia Materiale",
                        choices=["Acciaio", "PEAD", "Ghisa", "Rame", "PVC", "Altro"],
                    )

                with gr.Row():
                    pressione = gr.Number(
                        label="Pressione Esercizio (bar)",
                        minimum=0,
                        step=0.1,
                    )
                    classif_dispersione = gr.Dropdown(
                        label="Classificazione Dispersione",
                        choices=[
                            "Classe 1 - Critica",
                            "Classe 2 - Maggiore",
                            "Classe 3 - Minore",
                            "Classe 4 - Trascurabile",
                        ],
                    )
                    tipologia_riparazione = gr.Dropdown(
                        label="Tipologia Riparazione",
                        choices=[
                            "Sostituzione tratto",
                            "Riparazione rapida",
                            "Morsetto",
                            "Saldatura",
                            "Fasciatura",
                            "Altro",
                        ],
                    )

                with gr.Row():
                    interruzione = gr.Radio(
                        label="Interruzione Fornitura",
                        choices=["SI", "NO"],
                        value="NO",
                    )
                    data_rilevamento = gr.Textbox(
                        label="Data Rilevamento Perdita (GG/MM/AAAA)",
                        placeholder="es. 15/03/2024",
                    )
                    data_riparazione = gr.Textbox(
                        label="Data Esecuzione Riparazione (GG/MM/AAAA)",
                        placeholder="es. 16/03/2024",
                    )

            # Emission section
            gr.Markdown("## 📊 EMISSIONE — Valore Rilevato")
            with gr.Group():
                with gr.Row():
                    unit = gr.Radio(
                        label="Unità di Misura",
                        choices=["PPM", "%Vol", "gr/h CH4"],
                        value="PPM",
                    )
                    value_input = gr.Number(
                        label="Valore Emissione",
                        minimum=0,
                    )
                    btn_convert = gr.Button("⚡ Converti", variant="secondary", scale=0)

                with gr.Row():
                    out_note = gr.Textbox(label="Formula applicata", interactive=False)
                    out_ppm = gr.Textbox(label="PPM", interactive=False)
                    out_ch4 = gr.Textbox(label="Kg/h CH₄", interactive=False)
                    out_co2 = gr.Textbox(
                        label="🟢 Fattore Emissione Kg/h CO₂", interactive=False
                    )

            btn_convert.click(
                do_convert,
                inputs=[unit, value_input],
                outputs=[out_note, out_ppm, out_ch4, out_co2],
            )

            # Save
            gr.Markdown("---")
            with gr.Row():
                btn_save = gr.Button(
                    "💾 Salva nel Dataset Excel", variant="primary", scale=2
                )
                btn_reset = gr.Button("🔄 Resetta Form", scale=1)

            save_status = gr.Markdown("")

            # History table (updated on save)
            history_table_main = gr.Dataframe(
                headers=HISTORY_HEADERS,
                datatype=["str"] * len(HISTORY_HEADERS),
                label="Ultimi interventi salvati",
                visible=False,
            )

            btn_save.click(
                do_save,
                inputs=[
                    tipologia_sito,
                    tubazione,
                    tipologia_materiale,
                    pressione,
                    classif_dispersione,
                    tipologia_riparazione,
                    interruzione,
                    data_rilevamento,
                    data_riparazione,
                    unit,
                    value_input,
                ],
                outputs=[save_status, history_table_main],
            )

            def reset_form():
                return (
                    None,
                    None,
                    None,  # dropdowns
                    None,  # pressione
                    None,
                    None,  # classif, riparazione
                    "NO",  # interruzione
                    "",
                    "",  # date
                    "PPM",
                    None,  # unit, value
                    "",
                    "",
                    "",
                    "",  # conversion outputs
                    "",  # save status
                )

            btn_reset.click(
                reset_form,
                outputs=[
                    tipologia_sito,
                    tubazione,
                    tipologia_materiale,
                    pressione,
                    classif_dispersione,
                    tipologia_riparazione,
                    interruzione,
                    data_rilevamento,
                    data_riparazione,
                    unit,
                    value_input,
                    out_note,
                    out_ppm,
                    out_ch4,
                    out_co2,
                    save_status,
                ],
            )
        with gr.Tab("📋 Storico Interventi") as tab_storico:
            gr.Markdown(f"### Dataset: `{EXCEL_FILE}`")
            btn_reload = gr.Button("🔄 Aggiorna", variant="secondary", scale=0)
            history_table = gr.Dataframe(
                headers=HISTORY_HEADERS,
                datatype=["str"] * len(HISTORY_HEADERS),
                value=[],
                interactive=False,
                wrap=False,
            )
            btn_reload.click(fn=load_history, inputs=[], outputs=[history_table])
            tab_storico.select(fn=load_history, inputs=[], outputs=[history_table])

        with gr.Tab("ℹ️ Formule & Riferimenti"):
            gr.Markdown(
                f"""
## Formule di Conversione

### Da %Vol → PPM
```
PPM = %Vol × 10.000
Esempio: 27 %Vol → 270.000 PPM
```

### Da PPM → Kg/h CH₄ &nbsp;*(UNI 15446, Tabella C.1)*
```
ER = A × (SV)^B
A  = {A_COEFF}
B  = {B_COEFF}
SV = valore in PPM
```

### Da gr/h CH₄ → Kg/h CH₄
```
Kg/h = gr/h ÷ 1.000
```

### Da Kg/h CH₄ → Kg/h CO₂ equivalente &nbsp;*(IPCC)*
```
Kg/h CO₂ = Kg/h CH₄ × {GWP_CH4}
(GWP metano = {GWP_CH4} volte CO₂)
```

---

## Struttura Excel Output

| Sezione | Colonne |
|---------|---------|
| Survey (9) | Tipologia Sito, Tubazione, Materiale, Pressione, Dispersione, Riparazione, Interruzione, Data Rilevamento, Data Riparazione |
| Emissione (5) | Unità, Valore Input, PPM, Kg/h CH₄, **Fattore Emissione Kg/h CO₂** |
"""
            )


if __name__ == "__main__":
    demo.launch(inbrowser=False, theme=THEME, debug=True, show_error=True)
