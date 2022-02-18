@echo off
REM
REM !!! Generated file, don't edit !!!
REM

REM Create venv if not done yet
if exist venv\ (
    REM Just load it
    venv\Scripts\Activate.bat
) else (
    REM Create it
    python -m venv venv

    REM Load it
    venv\Scripts\Activate.bat
    
    REM Bootstrap it
    python -m pip install pip wheel --upgrade
)