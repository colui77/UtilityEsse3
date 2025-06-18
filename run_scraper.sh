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

# Controlla se lo script Python esiste
if [ ! -f "$PYTHON_SCRIPT" ]; then
    echo "❌ Script Python non trovato: $PYTHON_SCRIPT"
    exit 1
fi

echo ""
echo "🐍 Esecuzione dello script Python..."
echo "📁 Script: $PYTHON_SCRIPT"
echo ""

# Esegui lo script Python con tutti gli argomenti passati
python3 "$PYTHON_SCRIPT" "$@"

# Controlla il codice di uscita
exit_code=$?
if [ $exit_code -eq 0 ]; then
    echo ""
    echo "🎉 Script completato con successo!"
else
    echo ""
    echo "❌ Script terminato con errore (codice: $exit_code)"
    echo "💡 Controlla i messaggi di errore sopra per maggiori dettagli."
fi

exit $exit_code
