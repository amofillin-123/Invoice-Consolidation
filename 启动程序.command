#!/bin/bash
cd "$(dirname "$0")"
export PYTHONPATH=/opt/homebrew/lib/python3.11/site-packages:/opt/homebrew/lib/python3.11/site-packages/PySimpleGUI
export DISPLAY=:0
export TCL_LIBRARY=/opt/homebrew/opt/tcl-tk@8/lib/tcl8.6
export TK_LIBRARY=/opt/homebrew/opt/tcl-tk@8/lib/tk8.6
./venv/bin/python invoice_merger_v2.py
