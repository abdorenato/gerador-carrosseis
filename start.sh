#!/bin/bash
cd /Users/renatoabdo/Documents/gerador-carrosseis
exec /Users/renatoabdo/Library/Python/3.9/bin/streamlit run app.py --server.port ${PORT:-8501} --server.headless true
