#!/bin/bash
# Wrapper script per semplificare l'esecuzione del scraper Esse3

echo "🚀 === ESSE3 UNIPARTHENOPE SCRAPER ==="
echo "Wrapper per l'estrazione delle date d'esame"
echo "======================================"

# Controlla se Python è installato
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 non trovato!"
    echo "💡 Installa Python 3 e riprova:"
    echo "   sudo apt update && sudo apt install python3 python3-pip  # Ubuntu/Debian"
    echo "   sudo yum install python3 python3-pip                     # CentOS/RHEL"
    echo "   brew install python3                                     # macOS"
    exit 1
fi

# Controlla se pip è installato
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 non trovato!"
    echo "💡 Installa pip3:"
    echo "   sudo apt install python3-pip  # Ubuntu/Debian"
    echo "   curl https://bootstrap.pypa.io/get-pip.py | python3  # Altri sistemi"
    exit 1
fi

echo "✅ Python 3 trovato: $(python3 --version)"
echo "✅ pip3 trovato: $(pip3 --version)"

# Directory dello script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/Esse3-Report-Esami-Parthenope.py"
VENV_DIR="$SCRIPT_DIR/venv"
REQUIREMENTS_FILE="$SCRIPT_DIR/requirements.txt"

# Controlla se il virtual environment esiste, altrimenti crealo
if [ ! -d "$VENV_DIR" ]; then
    echo ""
    echo "🔧 Creazione virtual environment..."
    python3 -m venv "$VENV_DIR"
    if [ $? -ne 0 ]; then
        echo "❌ Errore nella creazione del virtual environment!"
        echo "💡 Assicurati che python3-venv sia installato:"
        echo "   sudo apt install python3-venv  # Ubuntu/Debian"
        exit 1
    fi
    echo "✅ Virtual environment creato in: $VENV_DIR"
else
    echo "✅ Virtual environment già presente: $VENV_DIR"
fi

# Attiva il virtual environment
echo ""
echo "🔄 Attivazione virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "❌ Errore nell'attivazione del virtual environment!"
    exit 1
fi
echo "✅ Virtual environment attivato"

# Installa/aggiorna le dipendenze se esiste requirements.txt
if [ -f "$REQUIREMENTS_FILE" ]; then
    echo ""
    echo "📦 Installazione/aggiornamento dipendenze..."
    pip install --upgrade pip
    pip install -r "$REQUIREMENTS_FILE"
    if [ $? -ne 0 ]; then
        echo "❌ Errore nell'installazione delle dipendenze!"
        deactivate
        exit 1
    fi
    echo "✅ Dipendenze installate con successo"
else
    echo "⚠️  File requirements.txt non trovato, salto l'installazione delle dipendenze"
fi

# Controlla se lo script Python esiste
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Script Python non trovato: $PYTHON_SCRIPT"
    deactivate
    exit 1
fi

echo ""
echo "🐍 Esecuzione dello script Python..."
echo "📁 Script: $PYTHON_SCRIPT"
echo ""

# Esegui lo script Python con tutti gli argomenti passati (nel virtual environment)
python "$PYTHON_SCRIPT" "$@"

# Controlla il codice di uscita
exit_code=$?

# Disattiva il virtual environment
deactivate

if [ $exit_code -eq 0 ]; then
    echo ""
    echo "🎉 Script completato con successo!"
else
    echo ""
    echo "❌ Script terminato con errore (codice: $exit_code)"
    echo "💡 Controlla i messaggi di errore sopra per maggiori dettagli."
fi

exit $exit_code
