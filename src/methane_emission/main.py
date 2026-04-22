import os
import gradio as gr
from datetime import date, datetime

from core.conversions import convert_emission, GWP_CH4, A_COEFF, B_COEFF
from core.models import Intervento, SurveyData, EmissionData
from data.excel_manager import save_intervento, get_all_interventi, EXCEL_FILE

# Crea directory temporanea locale per i file upload
TEMP_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".gradio_tmp"
)
os.makedirs(TEMP_DIR, exist_ok=True)
os.environ["GRADIO_TEMP_DIR"] = TEMP_DIR


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


def load_history():
    records = get_all_interventi()
    if not records:
        return []
    rows = []
    for r in records:
        rows.append(
            [
                r.get("Tipologia Sito (ME)", ""),
                r.get("Tipologia Sito (LCA)", ""),
                r.get("Tipologia di Materiale", ""),
                _fmt(r.get("Pressione Esercizio (bar)"), 2),
                r.get("Classificazione Dispersione", ""),
                r.get("Tipologia Riparazione", ""),
                r.get("Interruzione Fornitura", ""),
                r.get("Data Rilevamento Perdita", ""),
                r.get("Data Esecuzione Riparazione", ""),
                r.get("Image Path", ""),
                r.get("Unità di Misura Emissione", ""),
                _fmt(r.get("Valore Emissione"), 4),
                _fmt(r.get("PPM"), 2),
                _fmt(r.get("Kg/h CH4"), 8),
                _fmt(r.get("Fattore Emissione Kg/h CO2"), 6),
            ]
        )
    return rows


def on_tab_select(evt: gr.SelectData):
    """Fired when any tab is clicked. Loads data only for the Storico tab (index 1)."""
    if evt.index == 1:
        return load_history()
    return gr.skip()


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
    image_file,
    unit,
    value_str,
):
    if not tipologia_sito or not tubazione:
        return "Compilare almeno Tipologia Sito e Tubazione.", load_history()

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
        pressione_esercizio=pressione or "",
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
        row = save_intervento(
            Intervento(survey=survey, emission=emission), image_file=image_file
        )
        return f"Salvato alla riga {row -2} di `{EXCEL_FILE}`", load_history()
    except Exception as e:
        return f"Errore salvataggio: {e}", load_history()


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
    "Image Path",
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

with gr.Blocks(title="Emission Tracker", theme=THEME, css="style.css") as demo:

    gr.Markdown(
        """
    # 🏭 Emission Tracker — Singolo Intervento
    """
    )

    with gr.Tabs() as tabs:
        with gr.Tab("➕ Nuovo Intervento"):

            gr.Markdown("## 📍 SURVEY — Dati di Campo")
            with gr.Group():
                with gr.Row():
                    tipologia_sito = gr.Dropdown(
                        label="Tipologia Sito (ME) *",
                        choices=[
                            "City Gate (Cabina REMI)",
                            "Rete di distribuzione (Tubazione Stradale)",
                            "Linea di servizio (Allaccio)",
                            "Accessori della rete (IRI/GR)",
                        ],
                        value=None,
                        info="Seleziona tipologia sito",
                    )
                    tubazione = gr.Dropdown(
                        label="Tipologia Sito (LCA) *",
                        choices=["Interrato", "Aereo"],
                        value=None,
                        info="Seleziona tipologia tubazione",
                    )
                    tipologia_materiale = gr.Dropdown(
                        label="Tipologia di Materiale",
                        choices=[
                            "Acciaio",
                            "Acciaio Zincato",
                            "Acciaio Rivestito",
                            "Polietilene",
                            "Ghisa Duttile",
                            "Ghisa Grigia",
                            "PVC",
                        ],
                        value=None,
                        info="Seleziona tipologia materiale",
                    )

                with gr.Row():
                    # TODO
                    pressione = gr.Dropdown(
                        label="Pressione Esercizio (bar)",
                        choices=[
                            "7 specie (0.040 bar)",
                            "6 specie (0.50 bar)",
                            "5 specie",
                            "4 specie",
                            "3 specie",
                            "2 specie",
                            "1 specie (> 24 bar)",
                        ],
                        value=None,
                        info="Seleziona pressione esercizio",
                    )
                    classif_dispersione = gr.Dropdown(
                        label="Classificazione Dispersione",
                        choices=[
                            "A1",
                            "A2",
                            "B",
                            "C",
                        ],
                        value=None,
                        info="Seleziona classificazione dispersione",
                    )
                    # TODO
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
                        value=None,
                        info="Seleziona tipologia riparazione",
                    )

                with gr.Row():
                    interruzione = gr.Radio(
                        label="Interruzione Fornitura", choices=["SI", "NO"]
                    )
                    data_rilevamento = gr.Textbox(
                        label="Data Rilevamento Perdita (GG/MM/AAAA)",
                        info="es. 15/03/2024",
                    )
                    data_riparazione = gr.Textbox(
                        label="Data Esecuzione Riparazione (GG/MM/AAAA)",
                        info="es. 16/03/2024",
                    )

                with gr.Row():
                    image_upload = gr.File(
                        label="📸 Foto del Sito", file_types=["image"], type="filepath"
                    )

            gr.Markdown("## 📊 EMISSIONE — Valore Rilevato")
            with gr.Group():
                with gr.Row(equal_height=True):
                    unit = gr.Radio(
                        label="Unità di Misura",
                        choices=["PPM", "%Vol", "gr/h CH4"],
                    )
                    value_input = gr.Number(
                        label="Valore Emissione",
                        minimum=0,
                        info="Inserisci valore rilevato",
                    )
                    with gr.Column(min_width=120, elem_classes="btn-convert-col"):
                        btn_convert = gr.Button(
                            "⚡ Converti",
                            variant="secondary",
                        )
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

            gr.Markdown("---")
            with gr.Row():
                btn_save = gr.Button(
                    "💾 Salva nel Dataset Excel", variant="primary", scale=2
                )
                btn_reset = gr.Button("🔄 Resetta Form", scale=1)

            save_status = gr.Markdown("")

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
                    image_upload,
                    unit,
                    value_input,
                ],
                outputs=[save_status, history_table_main],
            )

            def reset_form():
                return (
                    None,
                    None,
                    None,
                    None,
                    None,
                    None,
                    "NO",
                    "",
                    "",
                    None,
                    "PPM",
                    None,
                    "",
                    "",
                    "",
                    "",
                    "",
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
                    image_upload,
                    unit,
                    value_input,
                    out_note,
                    out_ppm,
                    out_ch4,
                    out_co2,
                    save_status,
                ],
            )

        with gr.Tab("📋 Storico Interventi"):
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

    tabs.select(fn=on_tab_select, inputs=[], outputs=[history_table])


if __name__ == "__main__":
    demo.launch(inbrowser=False, debug=True, show_error=True)
