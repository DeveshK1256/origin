Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-Location "$PSScriptRoot\backend"
python -m streamlit run streamlit_app.py
