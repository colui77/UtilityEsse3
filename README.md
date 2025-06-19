# Esse3 Parthenope University Exam Scraper

Uno tool, implementato come script Python, utile per estrarre dall'Esse3 dell'Università Parthenope dei report con tutte le date per gli esami dei corsi di studio afferenti alle Scuole dell'Ateneo. I dati sono organizzati per docente e mese.

## Caratteristiche

- **Estrazione dinamica**: Recupera automaticamente dipartimenti e corsi dal sito web
- **Estrazione automatica**: Scraping HTTP del sito Esse3 Uniparthenope
- **Focus sulle scuole**: Filtra automaticamente solo le scuole reali (non i dipartimenti generici)
- **Ricerca intelligente**: Trova corsi con corrispondenza parziale (es. "cyber" → "Cybersecurity")
- **Organizzazione per mesi**: Le date sono raggruppate per mese (Giugno, Luglio, Agosto, ecc.)
- **Raggruppamento per docente**: Ogni insegnamento è diviso per docente
- **Filtro temporale**: Configurabile da 1 a N mesi in avanti
- **Export Excel**: Genera report dettagliati in formato Excel
- **Date corrette**: Estrae solo le date effettive degli esami, non quelle di prenotazione
- **CLI avanzata**: Comandi per listare dipartimenti, corsi, ricerca interattiva

## Installazione

1. Clona il repository:
```bash
git clone https://github.com/colui77/UtilityEsse3.git
cd UtilityEsse3
```

2. Crea un virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate && pip install --upgrade pip
```

3. Installa le dipendenze:
```bash
pip install -r requirements.txt
```

## Utilizzo

### Uso Base
```bash
python Esse3-Report-Esami-Parthenope.py --course "cybersecurity" --months 6
```

### Comandi Avanzati
```bash
# Lista tutte le scuole disponibili
python Esse3-Report-Esami-Parthenope.py --list-departments

# Lista tutti i corsi disponibili  
python Esse3-Report-Esami-Parthenope.py --list-courses

# Ricerca per nome corso completo
python Esse3-Report-Esami-Parthenope.py --course "INGEGNERIA E SCIENZE INFORMATICHE PER LA CYBERSECURITY" --months 7

# Modalità interattiva
python Esse3-Report-Esami-Parthenope.py --interactive

# Output personalizzato
python Esse3-Report-Esami-Parthenope.py --course "cyber" --output "report_dicembre" --months 8

# Debug dettagliato
python Esse3-Report-Esami-Parthenope.py --course "cyber" --verbose
```

## Output

Lo script genererà due file Excel:
- `esami_[course]_raw_[timestamp].xlsx` - Dati grezzi estratti
- `esami_[course]_report_[timestamp].xlsx` - Report organizzato per mesi

## Formato del Report

Il report finale contiene:
- **Nome_Insegnamento**: Nome del corso
- **Professore**: Nome del docente
- **Totale_Date**: Numero totale di date d'esame
- **Giugno, Luglio, Agosto, ecc.**: Giorni degli esami per ogni mese (separati da "/")

## Esempio Output

| Nome_Insegnamento | Professore | Totale_Date | Giugno | Luglio | Agosto |
|-------------------|------------|-------------|--------|--------|--------|
| Matematica I | ROSSI MARIO | 3 | 15/28 | 12 | 5 |
| Fisica Generale | BIANCHI LUCA | 2 | | 20 | 3/17 |

## Requisiti

- Python 3.6+
- requests
- beautifulsoup4
- pandas
- openpyxl

## Note

- Lo script estrae dinamicamente dipartimenti e corsi dal sito web (non liste fisse)
- Filtra automaticamente solo le scuole vere (non i "Dipartimento ..." generici)
- Supporta ricerca di corsi con corrispondenza parziale (es. "cyber" trova "Cybersecurity")
- Periodo configurabile da 1 a N mesi in avanti
- Estrae la data effettiva dell'esame, non le date di prenotazione
- Include gestione automatica delle dipendenze Python
- Richiede connessione internet per accedere al sito Esse3

## Licenza

MIT License

**UtilityEsse3** è uno strumento di automazione web sviluppato specificamente per l'Università Parthenope che consente di estrarre automaticamente dal portale Esse3 i calendari degli esami di tutti i corsi di studio dell'Ateneo. Il sistema organizza intelligentemente i dati raccolti per docente e periodo temporale, generando report strutturati e facilmente consultabili per l'analisi delle sessioni d'esame.
