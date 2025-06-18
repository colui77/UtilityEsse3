#!/usr/bin/env python3
"""
Enhanced HTTP scraper for Esse3 Uniparthenope exam dates
Groups exam dates by professor within each course and creates detailed reports

Installazione dipendenze:
pip install requests beautifulsoup4 pandas openpyxl
"""

import sys
import subprocess
import importlib.util

def check_and_install_dependencies():
    """Controlla e installa automaticamente le dipendenze necessarie"""
    
    # Controlla versione Python
    if sys.version_info < (3, 6):
        print("❌ VERSIONE PYTHON NON SUPPORTATA!")
        print(f"Versione corrente: Python {sys.version}")
        print("Versione richiesta: Python 3.6 o superiore")
        print("\n💡 Aggiorna Python e riprova.")
        sys.exit(1)
    
    required_packages = {
        'requests': 'requests',
        'bs4': 'beautifulsoup4', 
        'pandas': 'pandas',
        'openpyxl': 'openpyxl'
    }
    
    missing_packages = []
    
    # Controlla quali pacchetti mancano
    for import_name, pip_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError:
            missing_packages.append((import_name, pip_name))
    
    if missing_packages:
        print("❌ DIPENDENZE MANCANTI RILEVATE!")
        print("=" * 50)
        print("I seguenti pacchetti Python sono necessari ma non installati:")
        for import_name, pip_name in missing_packages:
            print(f"  • {import_name} (pip install {pip_name})")
        
        print("\n🔧 SOLUZIONI:")
        print("1. Installa manualmente:")
        pip_packages = " ".join([pip_name for _, pip_name in missing_packages])
        print(f"   pip install {pip_packages}")
        
        print("\n2. Installa dal file requirements.txt:")
        print("   pip install -r requirements.txt")
        
        print("\n3. Usa un ambiente virtuale:")
        print("   python -m venv esse3_env")
        print("   source esse3_env/bin/activate  # Linux/Mac")
        print("   esse3_env\\Scripts\\activate     # Windows")
        print("   pip install -r requirements.txt")
        
        # Prova installazione automatica
        try:
            response = input("\n🤖 Vuoi che provi a installarle automaticamente? (s/n): ").lower().strip()
            if response in ['s', 'si', 'y', 'yes']:
                print("\n⏳ Installazione in corso...")
                for _, pip_name in missing_packages:
                    print(f"  Installando {pip_name}...")
                    result = subprocess.run([sys.executable, '-m', 'pip', 'install', pip_name], 
                                          capture_output=True, text=True)
                    if result.returncode == 0:
                        print(f"  ✅ {pip_name} installato con successo")
                    else:
                        print(f"  ❌ Errore nell'installazione di {pip_name}")
                        print(f"     {result.stderr}")
                        print("\n💡 Prova a installare manualmente:")
                        print(f"     pip install {pip_name}")
                        sys.exit(1)
                
                print("\n🎉 Tutte le dipendenze sono state installate!")
                print("Lo script continuerà ora...\n")
            else:
                print("\n💡 Installa le dipendenze manualmente e riprova.")
                sys.exit(1)
        except KeyboardInterrupt:
            print("\n\n⏹️  Installazione annullata dall'utente.")
            sys.exit(1)
        except Exception as e:
            print(f"\n❌ Errore durante l'installazione automatica: {e}")
            print("💡 Prova a installare manualmente le dipendenze.")
            sys.exit(1)

# Controlla le dipendenze prima di importare
check_and_install_dependencies()

# Ora importa tutte le dipendenze
import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime, timedelta
import time
import re
import argparse
import logging
from collections import defaultdict
from typing import List, Dict, Optional, Tuple

# Configurazione logging più leggera
logging.basicConfig(
    level=logging.WARNING,  # Solo errori e warning di default
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

class ScraperConfig:
    """Configurazione per il scraper"""
    
    DEFAULT_MONTHS = 6
    DEFAULT_COURSE = 'cybersecurity'
    MAX_RETRIES = 2  # Ridotto per velocità
    DELAY_BETWEEN_REQUESTS = 0.2  # Ridotto delay
    TIMEOUT = 10  # Timeout più breve

class EnhancedEsse3Scraper:
    def __init__(self, course: str = ScraperConfig.DEFAULT_COURSE, 
                 months: int = ScraperConfig.DEFAULT_MONTHS,
                 start_date: Optional[datetime] = None):
        """
        Inizializza il scraper HTTP migliorato
        
        Args:
            course: Nome del corso da cercare
            months: Numero di mesi da oggi per cui cercare gli esami
            start_date: Data di inizio ricerca (default: oggi)
        """
        self.logger = logging.getLogger(__name__)
        self.course = course.lower()
        self.months = months
        self.start_date = start_date or datetime.now()
        self.end_date = self.start_date + timedelta(days=months * 30)
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Linux; x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36'
        })
        # Timeout più breve per tutte le richieste
        self.session.timeout = ScraperConfig.TIMEOUT
        self.base_url = "https://uniparthenope.esse3.cineca.it"
        
        self.logger.info(f"Scraper inizializzato per corso: {course}")
        self.logger.info(f"Periodo di ricerca: {self.start_date.strftime('%d/%m/%Y')} - {self.end_date.strftime('%d/%m/%Y')}")
    
    def get_dipartimenti(self) -> List[Dict[str, str]]:
        """
        Ottiene la lista dinamica dei dipartimenti disponibili
        
        Returns:
            Lista di dizionari con {id, nome} dei dipartimenti
        """
        self.logger.info("Recupero dipartimenti disponibili...")
        
        try:
            response = self.session.get(f"{self.base_url}/ListaAppelliOfferta.do", timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Lista di possibili nomi per il select dei dipartimenti
            dept_select_names = ['fac_id', 'prov_cds', 'dipartimento', 'dip_id', 'department', 'facolta', 'facolta_id']
            dept_select = None
            
            # Cerca il select dei dipartimenti con vari nomi possibili
            for name in dept_select_names:
                dept_select = soup.find('select', {'name': name})
                if dept_select:
                    self.logger.info(f"Select dipartimenti trovato con nome: {name}")
                    break
            
            # Se non trova con i nomi standard, cerca select che contenga "dipartimento" o "facolta" negli ID o classi
            if not dept_select:
                all_selects = soup.find_all('select')
                for select in all_selects:
                    select_id = select.get('id', '').lower()
                    select_class = ' '.join(select.get('class', [])).lower()
                    select_name = select.get('name', '').lower()
                    
                    if any(keyword in select_id + select_class + select_name 
                           for keyword in ['dipartimento', 'facolta', 'department', 'faculty', 'dip', 'fac']):
                        dept_select = select
                        self.logger.info(f"Select dipartimenti trovato tramite ricerca pattern: name={select.get('name')}")
                        break
            
            if not dept_select:
                self.logger.warning("Select dipartimenti non trovato, debug della pagina...")
                # Debug completo della struttura
                debug_info = self.debug_page_structure()
                
                # Prova a trovare il select con più opzioni (potrebbe essere quello dei dipartimenti)
                all_selects = soup.find_all('select')
                max_options = 0
                best_select = None
                
                for select in all_selects:
                    options_count = len([opt for opt in select.find_all('option') 
                                       if opt.get('value') and opt.get('value').strip()])
                    if options_count > max_options:
                        max_options = options_count
                        best_select = select
                
                if best_select and max_options > 2:
                    self.logger.info(f"Uso il select con più opzioni ({max_options}) come fallback")
                    dept_select = best_select
                else:
                    self.logger.error("Impossibile trovare il select dei dipartimenti")
                    return []
            
            dipartimenti = []
            for option in dept_select.find_all('option'):
                value = option.get('value', '').strip()
                text = option.get_text(strip=True)
                
                # Filtra solo le scuole (che iniziano con "Scuola" o "[S")
                if (value and value != '' and value != '0' and 
                    text and (text.startswith('Scuola') or text.startswith('[S'))):
                    dipartimenti.append({
                        'id': value,
                        'nome': text
                    })
            
            self.logger.info(f"Trovate {len(dipartimenti)} scuole")
            if dipartimenti:
                self.logger.debug("Scuole disponibili:")
                for i, dept in enumerate(dipartimenti):
                    self.logger.debug(f"  {i+1}. [{dept['id']}] {dept['nome']}")
            
            return dipartimenti
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore nella richiesta per ottenere i dipartimenti: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Errore imprevisto nel recupero dipartimenti: {e}")
            return []
    
    def get_all_corsi(self, dipartimento_id: Optional[str] = None) -> List[Dict[str, str]]:
        """
        Ottiene la lista dinamica di tutti i corsi disponibili
        
        Args:
            dipartimento_id: ID del dipartimento (opzionale)
            
        Returns:
            Lista di dizionari con {id, nome, dipartimento} dei corsi
        """
        self.logger.info("Recupero corsi disponibili...")
        
        try:
            # Ottieni i dati del form iniziale
            form_data = self.get_form_data()
            if not form_data:
                return []
            
            # Se è specificato un dipartimento, impostalo e fai una prima richiesta
            if dipartimento_id:
                form_data['fac_id'] = dipartimento_id
                # Prima richiesta per aggiornare la pagina con il dipartimento selezionato
                response1 = self.session.post(f"{self.base_url}/ListaAppelliOfferta.do", 
                                            data=form_data, timeout=30)
                response1.raise_for_status()
                
                # Aggiorna i dati del form con quelli della nuova pagina
                soup1 = BeautifulSoup(response1.text, 'html.parser')
                form = soup1.find('form', {'id': 'formRicercaCds'})
                if form:
                    new_form_data = {}
                    for input_elem in form.find_all('input', type='hidden'):
                        name = input_elem.get('name')
                        value = input_elem.get('value', '')
                        if name:
                            new_form_data[name] = value
                    
                    # Mantieni il dipartimento selezionato
                    new_form_data['fac_id'] = dipartimento_id
                    new_form_data.update({
                        'ad_name': '',
                        'aa_off_desc': '2024/2025',
                        'stu_status': '1',
                        'ad_mod': '',
                        'tipoRicAd': '',
                        'btnSelect1': 'Avanti'
                    })
                    form_data = new_form_data
            
            # Seconda richiesta per ottenere i corsi
            response = self.session.post(f"{self.base_url}/ListaAppelliOfferta.do", 
                                       data=form_data, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trova il select dei corsi
            corso_select = soup.find('select', {'name': 'cds_id'})
            if not corso_select:
                self.logger.warning("Select corsi non trovato nella pagina!")
                return []
            
            corsi = []
            for option in corso_select.find_all('option'):
                value = option.get('value', '').strip()
                text = option.get_text(strip=True)
                
                if value and value != '' and text and len(text) > 3:  # Filtra opzioni vuote
                    corsi.append({
                        'id': value,
                        'nome': text,
                        'dipartimento': dipartimento_id or 'N/A'
                    })
            
            self.logger.info(f"Trovati {len(corsi)} corsi")
            return corsi
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore nella richiesta per ottenere i corsi: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Errore imprevisto nel recupero corsi: {e}")
            return []
    
    def find_corso_by_name(self, nome_corso: str) -> Optional[Dict[str, str]]:
        """
        Cerca un corso per nome in tutti i dipartimenti
        
        Args:
            nome_corso: Nome del corso da cercare
            
        Returns:
            Dizionario con info del corso se trovato, None altrimenti
        """
        self.logger.info(f"Ricerca corso: {nome_corso}")
        
        # Prima prova senza specificare dipartimento
        corsi = self.get_all_corsi()
        
        # Cerca corrispondenze esatte o parziali
        nome_lower = nome_corso.lower()
        best_match = None
        
        for corso in corsi:
            corso_nome_lower = corso['nome'].lower()
            
            # Corrispondenza esatta
            if nome_lower == corso_nome_lower:
                self.logger.info(f"Corrispondenza esatta trovata: {corso['nome']}")
                return corso
            
            # Corrispondenza parziale
            if nome_lower in corso_nome_lower or corso_nome_lower in nome_lower:
                if not best_match or len(corso['nome']) < len(best_match['nome']):
                    best_match = corso
        
        if best_match:
            self.logger.info(f"Corrispondenza parziale trovata: {best_match['nome']}")
            return best_match
        
        # Se non trovato senza dipartimento, prova con tutti i dipartimenti
        self.logger.info("Corso non trovato, cerco in tutti i dipartimenti...")
        dipartimenti = self.get_dipartimenti()
        
        for dept in dipartimenti[:3]:  # Limita a primi 3 dipartimenti per performance
            self.logger.debug(f"Cerco nel dipartimento: {dept['nome']}")
            corsi_dept = self.get_all_corsi(dept['id'])
            
            for corso in corsi_dept:
                corso_nome_lower = corso['nome'].lower()
                if nome_lower in corso_nome_lower or corso_nome_lower in nome_lower:
                    self.logger.info(f"Corso trovato nel dipartimento {dept['nome']}: {corso['nome']}")
                    return corso
        
        self.logger.warning(f"Corso '{nome_corso}' non trovato in nessun dipartimento")
        return None

    def get_form_data(self):
        """Ottiene i dati del form iniziale e i parametri necessari"""
        print("Caricamento form iniziale...")
        try:
            response = self.session.get(f"{self.base_url}/ListaAppelliOfferta.do")
            print(f"Status code: {response.status_code}")
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"Errore nel caricamento della pagina: {e}")
            raise
        
        # Estrai i parametri del form
        form_data = {}
        
        # Trova tutti gli input hidden nel form
        form = soup.find('form', {'id': 'formRicercaCds'})
        if form:
            for input_elem in form.find_all('input', type='hidden'):
                name = input_elem.get('name')
                value = input_elem.get('value', '')
                if name:
                    form_data[name] = value
        
        # Aggiungi i parametri base
        oggi = datetime.today()
        tra_6_mesi = oggi + timedelta(days=180)
        
        form_data.update({
            'data_da': oggi.strftime('%d/%m/%Y'),
            'data_a': tra_6_mesi.strftime('%d/%m/%Y'),
            'fac_id': '10021',  # [S2] Scuola delle Scienze, dell'Ingegneria e della Salute
            'TIPO_FORM': '1'
        })
        
        print(f"Parametri form estratti: {len(form_data)} parametri")
        return form_data
    
    def get_corsi(self, form_data: Dict) -> Optional[str]:
        """
        Ottiene l'ID del corso specificato usando la ricerca dinamica
        
        Args:
            form_data: Dati del form per la richiesta
            
        Returns:
            ID del corso se trovato, None altrimenti
        """
        self.logger.info(f"Ricerca corso: {self.course}")
        
        # Usa la funzione di ricerca dinamica
        corso_info = self.find_corso_by_name(self.course)
        
        if corso_info:
            self.logger.info(f"Corso trovato: {corso_info['nome']} (ID: {corso_info['id']})")
            return corso_info['id']
        
        # Fallback: cerca manualmente nella pagina corrente
        try:
            response = self.session.post(f"{self.base_url}/ListaAppelliOfferta.do", 
                                       data=form_data, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Trova il select dei corsi
            corso_select = soup.find('select', {'name': 'cds_id'})
            if not corso_select:
                self.logger.error("Select corsi non trovato nella pagina!")
                return None
            
            # Lista di tutti i corsi per debug
            available_courses = []
            for option in corso_select.find_all('option'):
                if option.get('value') and option.get('value') != '':
                    available_courses.append(option.text.strip())
            
            self.logger.info(f"Corsi disponibili nella pagina: {len(available_courses)}")
            
            # Cerca il corso specificato
            search_terms = [
                self.course.upper(),
                self.course.title(),
                self.course.lower()
            ]
            
            for option in corso_select.find_all('option'):
                option_text = option.text.upper()
                for term in search_terms:
                    if term.upper() in option_text:
                        course_id = option.get('value')
                        if course_id and course_id != '':
                            self.logger.info(f"Corso trovato nella pagina: {option.text.strip()} (ID: {course_id})")
                            return course_id
            
            self.logger.warning(f"Corso '{self.course}' non trovato nella pagina!")
            self.logger.info("Primi 10 corsi disponibili nella pagina:")
            for course in available_courses[:10]:
                self.logger.info(f"  - {course}")
            if len(available_courses) > 10:
                self.logger.info(f"  ... e altri {len(available_courses) - 10} corsi")
                
            return None
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Errore nella richiesta per ottenere i corsi: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Errore imprevisto nel recupero corsi: {e}")
            return None
    
    def get_attivita(self, form_data, corso_id):
        """Ottiene la lista delle attività didattiche per il corso"""
        print("Caricamento attività didattiche...")
        
        form_data['cds_id'] = corso_id
        response = self.session.post(f"{self.base_url}/ListaAppelliOfferta.do", 
                                   data=form_data)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Trova il select delle attività
        attivita_select = soup.find('select', {'name': 'ad_id'})
        if not attivita_select:
            print("Select attività non trovato!")
            return []
            
        attivita = []
        for option in attivita_select.find_all('option'):
            value = option.get('value')
            text = option.text.strip()
            if value and value != '':  # Escludi l'opzione "-- Seleziona --"
                attivita.append({'value': value, 'text': text})
        
        print(f"Trovate {len(attivita)} attività didattiche")
        return attivita
    
    def search_exam_dates(self, form_data, attivita_id):
        """Effettua la ricerca per una specifica attività didattica"""
        search_data = form_data.copy()
        search_data['ad_id'] = attivita_id
        search_data['btnSubmit'] = 'Avvia Ricerca'
        
        response = self.session.post(f"{self.base_url}/ListaAppelliOfferta.do", 
                                   data=search_data)
        
        return self.extract_exam_dates_enhanced(response.text)
    
    def parse_date_string(self, date_str):
        """Estrae la data effettiva dell'esame dalla stringa della cella 2"""
        if not date_str:
            return []
        
        # La cella 2 contiene formato come "03/07/2025 - 09:30"
        # Estraiamo solo la data (prima parte)
        date_pattern = r'\b(\d{1,2}/\d{1,2}/\d{4})\b'
        found_dates = re.findall(date_pattern, date_str)
        
        # Valida le date trovate
        valid_dates = []
        for date in found_dates:
            try:
                datetime.strptime(date, '%d/%m/%Y')
                valid_dates.append(date)
            except ValueError:
                continue
        
        # Prendi solo la prima data trovata (quella dell'esame)
        return valid_dates[:1] if valid_dates else []
    
    def extract_exam_dates_enhanced(self, html_content):
        """Estrae le date d'esame con informazioni dettagliate sui docenti"""
        soup = BeautifulSoup(html_content, 'html.parser')
        exam_dates = []
        
        try:
            # Prima strategia: cerca tabelle con classe specifica
            table_rows = soup.find_all('tr', class_='rigaElenco')
            
            if table_rows:
                print(f"Trovate {len(table_rows)} righe nella tabella dei risultati")
                for i, row in enumerate(table_rows):
                    cells = row.find_all('td')
                    if len(cells) >= 3:
                        # Debug: stampa il contenuto di tutte le celle per capire la struttura
                        print(f"\nRiga {i+1}: {len(cells)} celle")
                        for j, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            print(f"  Cella {j}: '{cell_text}'")
                        
                        # Cerca il nome del docente in modo intelligente
                        docente_trovato = ''
                        for j, cell in enumerate(cells):
                            cell_text = cell.get_text(strip=True)
                            # Salta celle con contenuto che non può essere un nome docente
                            if cell_text and cell_text.lower() not in ['scritto', 'orale', 'prova', 'esame', 'appello']:
                                # Controlla se sembra un nome (contiene almeno 2 parole con maiuscole)
                                parole = cell_text.split()
                                if len(parole) >= 2 and any(p[0].isupper() for p in parole if p):
                                    # Evita date e orari
                                    if not re.match(r'\d{1,2}/\d{1,2}/\d{4}', cell_text) and not re.match(r'\d{1,2}:\d{2}', cell_text):
                                        docente_trovato = cell_text
                                        print(f"    -> Docente identificato nella cella {j}: '{cell_text}'")
                                        break
                        
                        exam_info = {
                            'data_esame': cells[0].get_text(strip=True),
                            'ora_esame': cells[1].get_text(strip=True) if len(cells) > 1 else '',
                            'dettagli': cells[2].get_text(strip=True) if len(cells) > 2 else '',
                            'docente': docente_trovato if docente_trovato else 'Docente non specificato',
                            'note': cells[4].get_text(strip=True) if len(cells) > 4 else ''
                        }
                        exam_dates.append(exam_info)
            
            # Seconda strategia: cerca tutte le tabelle
            if not exam_dates:
                all_tables = soup.find_all('table')
                print(f"Cercando in {len(all_tables)} tabelle...")
                
                for table_idx, table in enumerate(all_tables):
                    rows = table.find_all('tr')
                    
                    for row_idx, row in enumerate(rows):
                        cells = row.find_all(['td', 'th'])
                        if len(cells) >= 5:  # Assicurati che ci siano almeno 5 celle
                            cell_texts = [cell.get_text(strip=True) for cell in cells]
                            
                            # Verifica se la riga contiene una data (saltando l'header)
                            if row_idx > 0 and len(cell_texts) >= 5:
                                # La struttura corretta è:
                                # Cella 0: Nome corso
                                # Cella 1: Periodo prenotazioni (NON CI SERVE)
                                # Cella 2: Data e ora esame (QUESTA CI SERVE)
                                # Cella 3: Tipo esame
                                # Cella 4: Nome docente (QUESTO CI SERVE)
                                
                                data_esame = cell_texts[2]
                                docente = cell_texts[4] if cell_texts[4] else 'Docente non specificato'
                                
                                # Verifica che la cella 2 contenga effettivamente una data
                                date_pattern = r'\d{2}/\d{2}/\d{4}'
                                if re.search(date_pattern, data_esame):
                                    exam_info = {
                                        'data_esame': data_esame,
                                        'ora_esame': '',  # L'ora è già inclusa nella data_esame
                                        'dettagli': cell_texts[3],  # Tipo esame
                                        'docente': docente,
                                        'note': cell_texts[5] if len(cell_texts) > 5 else ''
                                    }
                                    exam_dates.append(exam_info)
            
            # Terza strategia: cerca pattern di testo specifici
            if not exam_dates:
                # Cerca blocchi di testo che contengono informazioni sui docenti
                text_content = soup.get_text()
                lines = text_content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # Cerca righe che contengono multiple date (tipico formato degli appelli)
                    date_pattern = r'\d{2}/\d{2}/\d{4}'
                    dates_in_line = re.findall(date_pattern, line)
                    
                    if len(dates_in_line) >= 1:  # Se c'è almeno una data
                        exam_info = {
                            'data_esame': line,  # Tutta la riga per l'elaborazione
                            'ora_esame': '',
                            'dettagli': line,
                            'docente': '',
                            'note': ''
                        }
                        
                        # Cerca orari nella stessa riga
                        time_match = re.search(r'(\d{1,2}:\d{2})', line)
                        if time_match:
                            exam_info['ora_esame'] = time_match.group(1)
                        
                        # Cerca docenti nella stessa riga
                        if re.search(r'(Prof\.|Dott\.|PROF\.|DOTT\.)', line, re.IGNORECASE):
                            # Estrai il nome del docente
                            docente_match = re.search(r'(Prof\.|Dott\.|PROF\.|DOTT\.)\s*([A-Z][a-z]+\s+[A-Z][a-z]+)', line, re.IGNORECASE)
                            if docente_match:
                                exam_info['docente'] = docente_match.group(0)
                        
                        exam_dates.append(exam_info)
            
            # Fallback finale: estrazione date semplice con regex
            if not exam_dates:
                print("Usando metodo fallback di estrazione date...")
                text_content = soup.get_text()
                lines = text_content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    date_pattern = r'\d{2}/\d{2}/\d{4}'
                    if re.search(date_pattern, line):
                        exam_dates.append({
                            'data_esame': line,
                            'ora_esame': '',
                            'dettagli': line,
                            'docente': 'Da determinare',
                            'note': ''
                        })
        
        except Exception as e:
            print(f"Errore nell'estrazione date: {e}")
        
        return exam_dates
    
    def scrape_all_exam_dates(self):
        """Scraping completo di tutte le date d'esame con informazioni sui docenti"""
        try:
            # 1. Ottieni i dati del form
            form_data = self.get_form_data()
            
            # 2. Ottieni l'ID del corso
            corso_id = self.get_corsi(form_data)
            if not corso_id:
                return []
            
            print(f"Corso ID trovato: {corso_id}")
            
            # 3. Ottieni tutte le attività
            attivita = self.get_attivita(form_data, corso_id)
            if not attivita:
                return []
            
            # 4. Per ogni attività, cerca le date d'esame
            all_exam_data = []
            
            for idx, att in enumerate(attivita):
                print(f"[{idx+1}/{len(attivita)}] Elaborazione: {att['text']}")
                
                exam_dates = self.search_exam_dates(form_data, att['value'])
                print(f"Trovate {len(exam_dates)} date per questa attività")
                
                for exam_date in exam_dates:
                    exam_date['attivita_didattica'] = att['text']
                    all_exam_data.append(exam_date)
                
                # Piccola pausa per non sovraccaricare il server
                time.sleep(0.5)
            
            return all_exam_data
            
        except Exception as e:
            print(f"Errore durante lo scraping: {e}")
            return []
    
    def create_professor_report(self, exam_data: List[Dict]) -> List[Dict]:
        """
        Crea un report raggruppato per professore con date organizzate per mesi
        
        Args:
            exam_data: Lista di dati degli esami
            
        Returns:
            Lista di dizionari con il report organizzato
        """
        self.logger.info("Creazione report raggruppato per professore con organizzazione per mesi...")
        
        # Usa le date configurate nella classe
        start_date = self.start_date
        end_date = self.end_date
        
        self.logger.info(f"Filtraggio date: {start_date.strftime('%d/%m/%Y')} - {end_date.strftime('%d/%m/%Y')}")
        
        # Raggruppa i dati per attività didattica e docente
        grouped_data = defaultdict(lambda: defaultdict(list))
        
        for exam in exam_data:
            attivita = exam['attivita_didattica']
            docente = exam['docente'] if exam['docente'] and exam['docente'].strip() else 'Docente non specificato'
            grouped_data[attivita][docente].append(exam)
        
        # Definisci i nomi dei mesi in italiano
        month_names = {
            1: 'Gennaio', 2: 'Febbraio', 3: 'Marzo', 4: 'Aprile',
            5: 'Maggio', 6: 'Giugno', 7: 'Luglio', 8: 'Agosto',
            9: 'Settembre', 10: 'Ottobre', 11: 'Novembre', 12: 'Dicembre'
        }
        
        # Raccogli tutti i mesi che hanno esami per creare le colonne
        all_months = set()
        
        # Crea il report strutturato con colonne per mesi
        report_data = []
        
        for attivita, docenti_dict in grouped_data.items():
            for docente, esami in docenti_dict.items():
                # Estrai tutte le date per questo docente
                all_dates = []
                for esame in esami:
                    date_str = esame['data_esame']
                    parsed_dates = self.parse_date_string(date_str)
                    
                    if parsed_dates:
                        all_dates.extend(parsed_dates)
                    elif date_str.strip():
                        all_dates.append(date_str.strip())
                
                # Filtra solo le date future e organizza per mesi
                dates_by_month = defaultdict(list)  # {month_num: [day1, day2, ...]}
                
                for date_str in all_dates:
                    try:
                        exam_date = datetime.strptime(date_str, '%d/%m/%Y')
                        if start_date <= exam_date <= end_date:
                            month_num = exam_date.month
                            day = exam_date.day
                            dates_by_month[month_num].append(day)
                            all_months.add(month_num)
                    except ValueError:
                        self.logger.warning(f"Data non valida ignorata: {date_str}")
                        continue
                
                # Rimuovi duplicati e ordina i giorni per ogni mese
                for month_num in dates_by_month:
                    dates_by_month[month_num] = sorted(list(set(dates_by_month[month_num])))
                
                # Salta se non ci sono date future
                if not dates_by_month:
                    continue
                
                # Crea l'entry del report
                report_entry = {
                    'Nome_Insegnamento': attivita,
                    'Professore': docente,
                    'Totale_Date': sum(len(days) for days in dates_by_month.values())
                }
                
                # Aggiungi una colonna per ogni mese con date
                for month_num, days in dates_by_month.items():
                    month_name = month_names[month_num]
                    # Converti i giorni in stringa separata da "/"
                    days_str = "/".join(str(day) for day in days)
                    report_entry[month_name] = days_str
                
                report_data.append(report_entry)
        
        # Ordina i mesi per creare le colonne in ordine cronologico
        sorted_months = sorted(all_months)
        month_columns = [month_names[month] for month in sorted_months]
        
        # Assicurati che tutte le entries abbiano tutte le colonne dei mesi (vuote se necessario)
        for entry in report_data:
            for month_name in month_columns:
                if month_name not in entry:
                    entry[month_name] = ''
        
        print(f"Report creato con {len(report_data)} righe")
        print(f"Mesi con esami: {', '.join(month_columns)}")
        return report_data
    
    def save_detailed_report(self, exam_data, report_data, base_filename="esami_cybersecurity"):
        """Salva i dati in multipli file Excel con formato date separate"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # File 1: Dati grezzi completi
        raw_filename = f"{base_filename}_raw_{timestamp}.xlsx"
        if exam_data:
            df_raw = pd.DataFrame(exam_data)
            df_raw.to_excel(raw_filename, index=False)
            print(f"Dati grezzi salvati in {raw_filename}")
        
        # File 2: Report raggruppato per professore con colonne separate
        report_filename = f"{base_filename}_report_{timestamp}.xlsx"
        if report_data:
            df_report = pd.DataFrame(report_data)
            df_report = df_report.sort_values(['Nome_Insegnamento', 'Professore'])
            
            with pd.ExcelWriter(report_filename, engine='openpyxl') as writer:
                # Foglio principale con il report
                df_report.to_excel(writer, sheet_name='Report Date Separate', index=False)
                
                # Foglio con statistiche
                stats_data = []
                for _, row in df_report.iterrows():
                    stats_data.append({
                        'Nome_Insegnamento': row['Nome_Insegnamento'],
                        'Professore': row['Professore'],
                        'Totale_Date': row['Totale_Date']
                    })
                
                df_stats = pd.DataFrame(stats_data)
                df_stats.to_excel(writer, sheet_name='Statistiche', index=False)
                
                # Riepilogo generale
                summary = {
                    'Totale Insegnamenti': df_report['Nome_Insegnamento'].nunique(),
                    'Totale Docenti': df_report['Professore'].nunique(),
                    'Totale Date Esame': df_report['Totale_Date'].sum(),
                    'Media Date per Docente': df_report['Totale_Date'].mean()
                }
                
                df_summary = pd.DataFrame([summary])
                df_summary.to_excel(writer, sheet_name='Riepilogo', index=False)
            
            print(f"Report con date separate salvato in {report_filename}")
        
        return raw_filename, report_filename
    
    def print_summary_report(self, report_data):
        """Stampa un riassunto del report con formato colonne separate"""
        if not report_data:
            print("Nessun dato nel report")
            return
        
        print("\n" + "="*80)
        print("REPORT ESAMI CYBERSECURITY - DATE ORGANIZZATE PER MESI")
        print("="*80)
        
        current_course = None
        for entry in sorted(report_data, key=lambda x: (x['Nome_Insegnamento'], x['Professore'])):
            if entry['Nome_Insegnamento'] != current_course:
                current_course = entry['Nome_Insegnamento']
                print(f"\n📚 CORSO: {current_course}")
                print("-" * 60)
            
            print(f"  👨‍🏫 Docente: {entry['Professore']}")
            print(f"  📅 Totale date: {entry['Totale_Date']}")
            
            # Mostra le date per mese
            month_cols = [col for col in entry.keys() 
                         if col in ['Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno', 
                                   'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre'] 
                         and entry[col]]
            if month_cols:
                months_info = []
                for month in month_cols:
                    months_info.append(f"{month}: {entry[month]}")
                print(f"  🗓️  Date per mese: {', '.join(months_info)}")
            print()

    def list_all_available_options(self) -> Dict[str, List[Dict]]:
        """
        Lista tutti i dipartimenti e corsi disponibili sul sito
        
        Returns:
            Dizionario con dipartimenti e corsi disponibili
        """
        self.logger.info("Lista completa di tutte le opzioni disponibili sul sito...")
        
        result = {
            'dipartimenti': [],
            'corsi': [],
            'tutti_corsi_per_dipartimento': {}
        }
        
        # Ottieni tutti i dipartimenti
        dipartimenti = self.get_dipartimenti()
        result['dipartimenti'] = dipartimenti
        
        self.logger.info(f"Trovati {len(dipartimenti)} dipartimenti:")
        for dept in dipartimenti:
            self.logger.info(f"  - {dept['nome']} (ID: {dept['id']})")
        
        # Per ogni dipartimento, ottieni i corsi disponibili
        for dept in dipartimenti:
            self.logger.info(f"Recupero corsi per dipartimento: {dept['nome']}")
            corsi = self.get_all_corsi(dept['id'])
            
            if corsi:
                result['tutti_corsi_per_dipartimento'][dept['nome']] = corsi
                result['corsi'].extend(corsi)
                self.logger.info(f"  - Trovati {len(corsi)} corsi")
            else:
                self.logger.warning(f"  - Nessun corso trovato per {dept['nome']}")
            
            # Pausa per non sovraccaricare il server
            time.sleep(0.5)
        
        return result

    def debug_page_structure(self, url: str = None) -> Dict[str, List[str]]:
        """
        Debug della struttura HTML della pagina per identificare select disponibili
        
        Args:
            url: URL da analizzare (default: pagina principale)
            
        Returns:
            Dizionario con informazioni sui select trovati
        """
        if not url:
            url = f"{self.base_url}/ListaAppelliOfferta.do"
        
        self.logger.info(f"Debug struttura pagina: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            debug_info = {
                'select_elements': [],
                'form_elements': [],
                'input_hidden': [],
                'page_title': soup.find('title').get_text(strip=True) if soup.find('title') else 'N/A'
            }
            
            # Analizza tutti i select
            all_selects = soup.find_all('select')
            for select in all_selects:
                select_info = {
                    'name': select.get('name', 'unnamed'),
                    'id': select.get('id', 'no-id'),
                    'options_count': len(select.find_all('option')),
                    'first_options': []
                }
                
                # Prime 5 opzioni per debug
                for option in select.find_all('option')[:5]:
                    value = option.get('value', '')
                    text = option.get_text(strip=True)
                    select_info['first_options'].append({
                        'value': value,
                        'text': text[:50] + '...' if len(text) > 50 else text
                    })
                
                debug_info['select_elements'].append(select_info)
            
            # Analizza tutti i form
            all_forms = soup.find_all('form')
            for form in all_forms:
                form_info = {
                    'id': form.get('id', 'no-id'),
                    'name': form.get('name', 'no-name'),
                    'action': form.get('action', 'no-action'),
                    'method': form.get('method', 'GET')
                }
                debug_info['form_elements'].append(form_info)
            
            # Analizza input hidden
            hidden_inputs = soup.find_all('input', type='hidden')
            for inp in hidden_inputs:
                debug_info['input_hidden'].append({
                    'name': inp.get('name', 'no-name'),
                    'value': inp.get('value', '')[:50] + '...' if len(inp.get('value', '')) > 50 else inp.get('value', '')
                })
            
            self.logger.info(f"Debug completato: {len(debug_info['select_elements'])} select, {len(debug_info['form_elements'])} form")
            return debug_info
            
        except Exception as e:
            self.logger.error(f"Errore nel debug della pagina: {e}")
            return {}

    def smart_search_department_and_course(self, search_term: str) -> List[Dict[str, str]]:
        """
        Ricerca intelligente di dipartimenti e corsi basata su un termine di ricerca
        
        Args:
            search_term: Termine da cercare
            
        Returns:
            Lista di risultati trovati
        """
        self.logger.info(f"Ricerca intelligente per: {search_term}")
        
        results = []
        search_lower = search_term.lower()
        
        # Cerca nei dipartimenti
        dipartimenti = self.get_dipartimenti()
        for dept in dipartimenti:
            if search_lower in dept['nome'].lower():
                results.append({
                    'tipo': 'dipartimento',
                    'nome': dept['nome'],
                    'id': dept['id'],
                    'match_score': self._calculate_match_score(search_lower, dept['nome'].lower())
                })
        
        # Cerca nei corsi
        all_courses = self.get_all_corsi()
        for corso in all_courses:
            if search_lower in corso['nome'].lower():
                results.append({
                    'tipo': 'corso',
                    'nome': corso['nome'],
                    'id': corso['id'],
                    'dipartimento': corso['dipartimento'],
                    'match_score': self._calculate_match_score(search_lower, corso['nome'].lower())
                })
        
        # Ordina per punteggio di corrispondenza
        results.sort(key=lambda x: x['match_score'], reverse=True)
        
        self.logger.info(f"Trovati {len(results)} risultati")
        return results[:10]  # Limita ai primi 10 risultati
    
    def _calculate_match_score(self, search_term: str, target: str) -> float:
        """
        Calcola un punteggio di corrispondenza tra termine di ricerca e target
        
        Args:
            search_term: Termine cercato
            target: Stringa di destinazione
            
        Returns:
            Punteggio di corrispondenza (0-1)
        """
        if search_term == target:
            return 1.0
        if search_term in target:
            return 0.8
        
        # Verifica parole in comune
        search_words = set(search_term.split())
        target_words = set(target.split())
        
        if search_words.intersection(target_words):
            return 0.6
        
        # Verifica caratteri in comune
        common_chars = sum(1 for c in search_term if c in target)
        return common_chars / max(len(search_term), len(target)) * 0.4

    # ...existing code...
def interactive_course_selection() -> Tuple[str, int, Optional[datetime]]:
    """
    Interfaccia interattiva per selezionare corso e parametri
    
    Returns:
        Tupla (corso, mesi, data_inizio)
    """
    print("\n🎓 === SCRAPER ESSE3 UNIPARTHENOPE ===")
    
    # Crea un'istanza temporanea per ottenere i dati
    temp_scraper = EnhancedEsse3Scraper()
    
    print("\n� Recupero dipartimenti disponibili...")
    dipartimenti = temp_scraper.get_dipartimenti()
    
    if not dipartimenti:
        print("❌ Impossibile recuperare i dipartimenti. Usa modalità manuale.")
        course = input("Inserisci il nome del corso: ").strip()
    else:
        print("\n🏛️ Dipartimenti disponibili:")
        for i, dept in enumerate(dipartimenti, 1):
            print(f"  {i}. {dept['nome']}")
        
        # Selezione dipartimento
        dept_choice = input(f"\nSeleziona dipartimento (1-{len(dipartimenti)}) o INVIO per tutti: ").strip()
        selected_dept = None
        
        if dept_choice.isdigit():
            idx = int(dept_choice) - 1
            if 0 <= idx < len(dipartimenti):
                selected_dept = dipartimenti[idx]['id']
        
        print("\n🔍 Recupero corsi disponibili...")
        corsi = temp_scraper.get_all_corsi(selected_dept)
        
        if not corsi:
            print("❌ Impossibile recuperare i corsi. Usa modalità manuale.")
            course = input("Inserisci il nome del corso: ").strip()
        else:
            # Mostra fino a 20 corsi per non saturare lo schermo
            print("\n📚 Corsi disponibili:")
            display_corsi = corsi[:20]
            for i, corso in enumerate(display_corsi, 1):
                print(f"  {i}. {corso['nome']}")
            
            if len(corsi) > 20:
                print(f"  ... e altri {len(corsi) - 20} corsi")
            
            # Selezione corso
            while True:
                choice = input(f"\nSeleziona corso (1-{len(display_corsi)}) o digita il nome: ").strip()
                
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(display_corsi):
                        course = display_corsi[idx]['nome']
                        break
                else:
                    # Cerca per nome
                    found_corso = temp_scraper.find_corso_by_name(choice)
                    if found_corso:
                        course = found_corso['nome']
                        break
                    else:
                        print("❌ Corso non trovato. Riprova.")
    
    # Selezione mesi
    while True:
        try:
            months_input = input(f"\nNumero di mesi da cercare (default {ScraperConfig.DEFAULT_MONTHS}): ").strip()
            if not months_input:
                months = ScraperConfig.DEFAULT_MONTHS
                break
            months = int(months_input)
            if 1 <= months <= 12:
                break
            print("❌ Inserisci un numero tra 1 e 12.")
        except (ValueError, KeyboardInterrupt):
            print("\n👋 Operazione annullata.")
            sys.exit(0)
    
    # Data di inizio (opzionale)
    while True:
        try:
            start_input = input("\nData di inizio (dd/mm/yyyy) o INVIO per oggi: ").strip()
            if not start_input:
                start_date = None
                break
            start_date = datetime.strptime(start_input, '%d/%m/%Y')
            break
        except ValueError:
            print("❌ Formato data non valido. Usa dd/mm/yyyy.")
        except KeyboardInterrupt:
            print("\n👋 Operazione annullata.")
            sys.exit(0)
    
    return course, months, start_date

def parse_arguments() -> argparse.Namespace:
    """
    Parsing degli argomenti della riga di comando
    
    Returns:
        Namespace con gli argomenti
    """
    parser = argparse.ArgumentParser(
        description="Scraper per esami Esse3 Uniparthenope",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Esempi di utilizzo:
  python Esse3-Report-Esami-Parthenope.py --interactive
  python Esse3-Report-Esami-Parthenope.py --course cybersecurity --months 6
  python Esse3-Report-Esami-Parthenope.py --course informatica --months 3 --start-date 01/07/2025
  python Esse3-Report-Esami-Parthenope.py --list-courses
        """
    )
    
    parser.add_argument('--course', '-c', 
                       default=ScraperConfig.DEFAULT_COURSE,
                       help=f'Nome del corso (default: {ScraperConfig.DEFAULT_COURSE})')
    
    parser.add_argument('--months', '-m', 
                       type=int, 
                       default=ScraperConfig.DEFAULT_MONTHS,
                       help=f'Numero di mesi da cercare (default: {ScraperConfig.DEFAULT_MONTHS})')
    
    parser.add_argument('--start-date', '-s',
                       help='Data di inizio ricerca (formato: dd/mm/yyyy, default: oggi)')
    
    parser.add_argument('--interactive', '-i',
                       action='store_true',
                       help='Modalità interattiva per selezionare parametri')
    
    parser.add_argument('--list-courses', '-l',
                       action='store_true',
                       help='Mostra la lista dei corsi supportati')
    
    parser.add_argument('--list-departments', '-ld',
                       action='store_true',
                       help='Mostra la lista delle scuole disponibili')
    
    parser.add_argument('--list-all', '-la',
                       action='store_true',
                       help='Mostra tutti i dipartimenti e corsi disponibili sul sito')
    
    parser.add_argument('--search', '-sr',
                       help='Ricerca intelligente di corsi e dipartimenti per nome')
    
    parser.add_argument('--debug-page', '-dp',
                       action='store_true',
                       help='Debug della struttura HTML della pagina')
    
    parser.add_argument('--verbose', '-v',
                       action='store_true',
                       help='Output dettagliato')
    
    parser.add_argument('--output', '-o',
                       help='Prefisso per i file di output (default: esami_cybersecurity)')
    
    return parser.parse_args()

def main():
    """Funzione principale migliorata"""
    args = parse_arguments()
    
    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Lista scuole disponibili
    if args.list_departments:
        print("\n🔍 Recupero scuole disponibili...")
        temp_scraper = EnhancedEsse3Scraper()
        
        scuole = temp_scraper.get_dipartimenti()
        if scuole:
            print(f"\n🏛️ SCUOLE DISPONIBILI ({len(scuole)}):")
            for i, scuola in enumerate(scuole, 1):
                print(f"  {i}. [{scuola['id']}] {scuola['nome']}")
        else:
            print("❌ Impossibile recuperare le scuole")
        return
    
    # Lista corsi dinamica
    if args.list_courses:
        print("\n🔍 Recupero dipartimenti e corsi disponibili...")
        temp_scraper = EnhancedEsse3Scraper()
        
        dipartimenti = temp_scraper.get_dipartimenti()
        if dipartimenti:
            print("\n🏛️ Dipartimenti disponibili:")
            for dept in dipartimenti:
                print(f"  • {dept['nome']} (ID: {dept['id']})")
            
            print("\n📚 Recupero corsi da tutti i dipartimenti...")
            all_corsi = []
            for dept in dipartimenti[:3]:  # Limita a primi 3 per performance
                corsi = temp_scraper.get_all_corsi(dept['id'])
                all_corsi.extend(corsi)
            
            if all_corsi:
                print(f"\n📚 Corsi disponibili ({len(all_corsi)} trovati):")
                for i, corso in enumerate(all_corsi[:30], 1):  # Mostra primi 30
                    print(f"  {i:2d}. {corso['nome']}")
                if len(all_corsi) > 30:
                    print(f"      ... e altri {len(all_corsi) - 30} corsi")
            else:
                print("❌ Nessun corso trovato")
        else:
            print("❌ Impossibile recuperare i dipartimenti")
        return
    
    # Lista completa di tutti i dipartimenti e corsi
    if args.list_all:
        print("\n🔍 Recupero TUTTI i dipartimenti e corsi disponibili...")
        temp_scraper = EnhancedEsse3Scraper()
        
        options = temp_scraper.list_all_available_options()
        
        print(f"\n🏛️ DIPARTIMENTI DISPONIBILI ({len(options['dipartimenti'])}):")
        for i, dept in enumerate(options['dipartimenti'], 1):
            print(f"  {i:2d}. {dept['nome']} (ID: {dept['id']})")
        
        print(f"\n📚 TUTTI I CORSI DISPONIBILI ({len(options['corsi'])}):")
        for i, corso in enumerate(options['corsi'], 1):
            dept_name = next((dept['nome'] for dept in options['dipartimenti'] 
                            if dept['id'] == corso['dipartimento']), 'N/A')
            print(f"  {i:3d}. {corso['nome']}")
            print(f"       Dipartimento: {dept_name}")
        
        if options['tutti_corsi_per_dipartimento']:
            print(f"\n📋 CORSI PER DIPARTIMENTO:")
            for dept_name, corsi in options['tutti_corsi_per_dipartimento'].items():
                print(f"\n  📚 {dept_name} ({len(corsi)} corsi):")
                for corso in corsi:
                    print(f"    • {corso['nome']}")
        return
    
    # Ricerca intelligente
    if args.search:
        print(f"\n🔍 Ricerca per: '{args.search}'")
        temp_scraper = EnhancedEsse3Scraper()
        
        results = temp_scraper.smart_search_department_and_course(args.search)
        
        if results:
            print(f"\n✅ Trovati {len(results)} risultati:")
            for i, result in enumerate(results, 1):
                if result['tipo'] == 'dipartimento':
                    print(f"  {i:2d}. 🏛️ DIPARTIMENTO: {result['nome']}")
                    print(f"       ID: {result['id']}")
                else:
                    print(f"  {i:2d}. 📚 CORSO: {result['nome']}")
                    print(f"       ID: {result['id']}, Dipartimento: {result['dipartimento']}")
                print(f"       Match: {result['match_score']:.2f}")
        else:
            print("❌ Nessun risultato trovato")
        return
    
    # Debug struttura pagina
    if args.debug_page:
        print("\n🔍 Debug struttura pagina HTML...")
        temp_scraper = EnhancedEsse3Scraper()
        
        debug_info = temp_scraper.debug_page_structure()
        
        if debug_info:
            print(f"\n📄 Titolo pagina: {debug_info['page_title']}")
            
            print(f"\n📋 SELECT ELEMENTS ({len(debug_info['select_elements'])}):")
            for i, select in enumerate(debug_info['select_elements'], 1):
                print(f"  {i:2d}. Name: '{select['name']}', ID: '{select['id']}', Opzioni: {select['options_count']}")
                for j, option in enumerate(select['first_options'], 1):
                    print(f"       {j}. value='{option['value']}' text='{option['text']}'")
            
            print(f"\n📝 FORM ELEMENTS ({len(debug_info['form_elements'])}):")
            for i, form in enumerate(debug_info['form_elements'], 1):
                print(f"  {i:2d}. ID: '{form['id']}', Name: '{form['name']}', Action: '{form['action']}', Method: {form['method']}")
            
            print(f"\n🔒 INPUT HIDDEN ({len(debug_info['input_hidden'])}):")
            for i, inp in enumerate(debug_info['input_hidden'], 1):
                print(f"  {i:2d}. Name: '{inp['name']}', Value: '{inp['value']}'")
        return
    
    # Modalità interattiva
    if args.interactive:
        course, months, start_date = interactive_course_selection()
    else:
        course = args.course
        months = args.months
        start_date = None
        if args.start_date:
            try:
                start_date = datetime.strptime(args.start_date, '%d/%m/%Y')
            except ValueError:
                print("❌ Formato data non valido. Usa dd/mm/yyyy.")
                sys.exit(1)
    
    # Validazione parametri
    if months < 1 or months > 12:
        print("❌ Il numero di mesi deve essere tra 1 e 12.")
        sys.exit(1)
    
    print(f"\n🚀 === SCRAPER ESSE3 UNIPARTHENOPE ===")
    print(f"📚 Corso: {course.title()}")
    print(f"📅 Periodo: {months} mesi da {(start_date or datetime.now()).strftime('%d/%m/%Y')}")
    print("="*50)
    
    # Inizializza scraper
    scraper = EnhancedEsse3Scraper(
        course=course,
        months=months,
        start_date=start_date
    )
    
    # Test connessione
    print("🔗 Test connessione al sito...")
    try:
        test_response = scraper.session.get(scraper.base_url, timeout=10)
        test_response.raise_for_status()
        print(f"✅ Connessione OK - Status: {test_response.status_code}")
    except Exception as e:
        print(f"❌ Errore di connessione: {e}")
        return
    
    try:
        print("🔍 Inizio scraping delle date d'esame...")
        exam_data = scraper.scrape_all_exam_dates()
        
        if exam_data:
            print(f"✅ Trovate {len(exam_data)} date d'esame totali")
            
            # Crea il report raggruppato per professore
            report_data = scraper.create_professor_report(exam_data)
            
            if report_data:
                # Stampa il riassunto
                scraper.print_summary_report(report_data)
                
                # Salva i file
                base_filename = args.output or f"esami_{course}"
                raw_file, report_file = scraper.save_detailed_report(exam_data, report_data, base_filename)
                
                print(f"\n🎉 Elaborazione completata!")
                print(f"📄 File dati grezzi: {raw_file}")
                print(f"📊 File report dettagliato: {report_file}")
            else:
                print("⚠️  Nessun dato nel periodo specificato")
        else:
            print("❌ Nessuna data d'esame trovata")
    
    except KeyboardInterrupt:
        print("\n👋 Operazione interrotta dall'utente")
    except Exception as e:
        logging.exception("Errore durante l'esecuzione")
        print(f"❌ Errore: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
