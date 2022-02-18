# 
# !!! Generated file, don't edit !!!
#

# Create venv if not done yet
if test ! -d venv; then
    # Create it
    python3 -m venv venv

    # Load it
    source venv/bin/activate
    
    # Bootstrap it
    pip install pip wheel --upgrade

    # Patch it for nmk completion
    echo ' ' >> venv/bin/activate
    echo 'eval "$(register-python-argcomplete nmk)"' >> venv/bin/activate
fi

# Just load it
source venv/bin/activate