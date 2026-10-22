# OMCA PF350 ANFD Streamlit digital twin

## Run locally
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud
Use Python 3.12. Upload `app.py` and `requirements.txt` to the repository root. Do not use Python 3.14 for this package.

## Dimension status
- GA-controlled: 350 mm vessel ID, 5 mm nominal radial blade clearance, 3 mm blade/filter-plate gap, 65 mm mixer axial stroke.
- Photo-extrapolated: shaft, hub, arm and outer-blade dimensions.
- All uncertain agitator dimensions are editable in the sidebar.

## Modelling note
This package is an engineering visualization, not a fabrication model. Replace extrapolated values when certified vendor/component drawings become available.
