# ADTC: Ancestral Differences of Transcriptome and Clinical Utility in Cancers

ADTC is an interactive web resource for exploring ancestry-associated transcriptomic
features with relevance to therapeutics and prognosis across 21 TCGA cancer types.
It summarizes differences among European (EUR), East Asian (EAS) and African (AFR)
patients in:

- long non-coding RNAs (lncRNA)
- alternative splicing (AS)
- alternative polyadenylation (APA)
- A-to-I RNA editing

It also shows Kaplan–Meier survival curves for each feature in each ancestry group.

This repository contains the source code of the web application.

## Architecture

| Layer    | Technology |
|----------|------------|
| Backend  | Python / Flask + Flask-RESTful (`ADTC/ajax.py`) |
| Database | MongoDB (via Flask-PyMongo) |
| Plots    | R (`ADTC/script/survival.R`, uses `survival`, `survminer`, `dplyr`, `ggplot2`) |
| Frontend | AngularJS 1.8, Bootstrap 4, Plotly, ECharts (`ADTC/static/ADTC`) |

```
.
├── run.py                     # development server entry point
├── requirements.txt
├── .env.example               # configuration template
└── ADTC/
    ├── __init__.py            # Flask app
    ├── settings.py            # configuration (read from environment variables)
    ├── core.py                # MongoDB connection
    ├── controllers.py         # page routes
    ├── ajax.py                # REST API (/api/...)
    ├── wsgi.py                # WSGI entry point for production
    ├── script/survival.R      # survival curve generation
    ├── templates/             # index.html
    └── static/ADTC/
        ├── js/ pages/ partials/ css/ image/   # AngularJS front end
        ├── lib/               # third-party JS/CSS libraries
        ├── data/              # per-cancer RData files (not in repo, see below)
        └── download/          # downloadable tables (large ones not in repo)
```

## Data

The processed data is too large for a code repository (about 4.8 GB), so it is
distributed separately: <!-- TODO: add Zenodo/Figshare DOI -->

1. **RData files** for survival analysis: `<CANCER>.<TYPE>.RData`, with `TYPE` one of
   `lncRNA`, `AS`, `APA` or `Editing`. Each contains a `merge_data` table with the
   columns `barcode`, `OS`, `Status`, `ancestry` and one column per feature.
   Put them in `ADTC/static/ADTC/data/` or point `ADTC_DATA_DIR` at them.
2. **Download tables**: `TABLE1_hg38_v2.txt`, `PanCanAtlas_SplAdder_AS.info`,
   `impute_drug_VAEN.txt`, `impute_drug_cancerRxTissue.txt` and `DT_Curated.txt`.
   Put them in `ADTC/static/ADTC/download/`.
The MongoDB database behind the web interface is not distributed at this time.
For reference, the application reads these collections: `lncrna_psm`, `as_psm`, `apa_psm`, `editing_psm`,
`survive_res_lnc`, `survive_res_as`, `survive_res_apa`, `survive_res_editing`,
`lnc_target`, `ADTC_clinic_info`, `ADTC_lncRNAdata`, `ADTC_ASdata`, `ADTC_APAdata`
and `ADTC_Editingdata`.

## Installation

```bash
# Python dependencies
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# R dependencies
Rscript -e 'install.packages(c("survival", "survminer", "dplyr", "ggplot2"))'

# Configuration
cp .env.example .env        # then edit .env
set -a; source .env; set +a
```

| Variable          | Description                                  | Default |
|-------------------|----------------------------------------------|---------|
| `ADTC_MONGO_URI`  | MongoDB connection string                    | `mongodb://127.0.0.1:27017/ADTC` |
| `ADTC_SECRET_KEY` | Flask secret key                             | random at each start |
| `ADTC_RSCRIPT`    | Path to `Rscript`                            | `Rscript` |
| `ADTC_DATA_DIR`   | Directory with the RData files               | `ADTC/static/ADTC/data` |
| `ADTC_DEBUG`      | Flask debug mode                             | `false` |

## Running

Development server:

```bash
python run.py              # http://127.0.0.1:1237 (change with PORT / HOST)
```

Production (example with gunicorn):

```bash
pip install gunicorn
gunicorn -w 4 -b 127.0.0.1:1237 ADTC.wsgi:application
```

The survival endpoint writes plots to `ADTC/static/ADTC/analysis_result_tmp_file/`.
Clean this directory periodically, for example with a cron job.

## Citation

If you use ADTC, please cite:

> Ancestral disparities in lncRNAs and post-transcriptional modifications associated
> with cancer patient survival and treatment response. *Nature Communications*.
<!-- TODO: add authors, year, volume and DOI -->

```bibtex
@article{ADTC,
  title   = {Ancestral disparities in lncRNAs and post-transcriptional modifications associated with cancer patient survival and treatment response},
  journal = {Nature Communications},
  author  = {TODO},
  year    = {TODO},
  doi     = {TODO}
}
```

## Contact

Leng Han Lab, Indiana University School of Medicine: https://hanlaboratory.com/
