import streamlit as st
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from icalendar import Calendar, Event
import socket
import hashlib
import json
import os
from dotenv import load_dotenv
import requests
import math

# Carrega as variáveis de ambiente
load_dotenv()

# Configurações do Google Sheets
SPREADSHEET_ID = os.getenv('SPREADSHEET_ID')
SHEET_NAME = 'Página1'
CALENDAR_FILE = 'calendario_pos.ics'

# Coordenadas da UFMA (São Luís)
UFMA_LAT = -2.5897
UFMA_LON = -44.2103
MAX_DISTANCE_KM = 1.0  # Distância máxima permitida em quilômetros

def calcular_distancia(lat1, lon1, lat2, lon2):
    """
    Calcula a distância entre dois pontos usando a fórmula de Haversine.
    Retorna a distância em quilômetros.
    """
    R = 6371  # Raio da Terra em quilômetros

    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c

def obter_localizacao_ip(ip):
    """
    Obtém a localização geográfica de um IP usando a API ip-api.com
    Retorna um dicionário com latitude e longitude, ou None em caso de erro.
    """
    try:
        response = requests.get(f'http://ip-api.com/json/{ip}')
        data = response.json()
        
        if data['status'] == 'success':
            return {
                'latitude': data['lat'],
                'longitude': data['lon']
            }
        return None
    except Exception as e:
        st.error(f"Erro ao obter localização: {e}")
        return None

def verificar_localizacao():
    """
    Verifica se o IP do usuário está dentro da área permitida.
    Retorna True se estiver dentro do limite, False caso contrário.
    """
    try:
        # Obtém o IP do usuário
        sock = socket.create_connection(("8.8.8.8", 53))
        ip_address = sock.getsockname()[0]
        sock.close()
    except OSError:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            st.error("Erro: Não foi possível obter o endereço IP.")
            return False

    # Obtém a localização do IP
    localizacao = obter_localizacao_ip(ip_address)
    if not localizacao:
        st.error("Não foi possível determinar sua localização.")
        return False

    # Calcula a distância até a UFMA
    distancia = calcular_distancia(
        localizacao['latitude'],
        localizacao['longitude'],
        UFMA_LAT,
        UFMA_LON
    )

    if distancia > MAX_DISTANCE_KM:
        st.error(f"Você está muito longe da UFMA. Distância atual: {distancia:.2f} km")
        return False

    return True

def get_google_credentials():
    """
    Obtém as credenciais do Google Sheets a partir da variável de ambiente.
    """
    try:
        credentials_json = json.loads(os.getenv('GOOGLE_SHEETS_CREDENTIALS'))
        return service_account.Credentials.from_service_account_info(
            credentials_json,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
    except Exception as e:
        st.error(f"Erro ao carregar credenciais: {e}")
        return None

def ler_datas_do_calendario(arquivo_calendario):
    """
    Lê as datas e nomes dos eventos do arquivo de calendário.
    """
    eventos = []
    try:
        with open(arquivo_calendario, 'r', encoding='utf-8') as f:
            calendario_str = f.read()
        calendario = Calendar.from_ical(calendario_str)
        for componente in calendario.walk():
            if isinstance(componente, Event):
                data_inicio = componente.get('dtstart').dt
                if isinstance(data_inicio, datetime.datetime):
                    data_inicio = data_inicio.date()
                nome_evento = str(componente.get('summary', 'Sem nome'))
                eventos.append((data_inicio, nome_evento))
    except FileNotFoundError:
        st.error(f"Erro: Arquivo de calendário não encontrado em {arquivo_calendario}")
        return []
    except Exception as e:
        st.error(f"Erro ao ler o arquivo de calendário: {e}")
        return []
    return eventos

def verificar_data_atual(eventos):
    """
    Verifica se a data atual está presente na lista de eventos e retorna o nome do evento.
    """
    data_atual = datetime.date.today()
    for data, nome in eventos:
        if data == data_atual:
            return True, nome
    return False, None

def obter_ip_hash():
    """
    Obtém o endereço IP do usuário e retorna um hash dele.
    """
    try:
        sock = socket.create_connection(("8.8.8.8", 53))
        ip_address = sock.getsockname()[0]
        sock.close()
    except OSError:
        try:
            ip_address = socket.gethostbyname(socket.gethostname())
        except socket.gaierror:
            st.error("Erro: Não foi possível obter o endereço IP.")
            return None
    ip_hash = hashlib.sha256(ip_address.encode()).hexdigest()
    return ip_hash

def verificar_registro_unico(ip_hash, sheet):
    """
    Verifica se o usuário já se registrou hoje usando o hash do IP.
    """
    try:
        result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=f"{SHEET_NAME}!A:B").execute()
        registros = result.get('values', [])
        if not registros:
            return False
        data_atual = datetime.date.today().strftime('%Y-%m-%d')
        for linha in registros:
            if len(linha) >= 2 and linha[0] == ip_hash and linha[1] == data_atual:
                return True
        return False
    except Exception as e:
        st.error(f"Erro ao verificar registro: {e}")
        return False

def registrar_presenca(nome, ip_hash, sheet, nome_evento):
    """
    Registra a presença do usuário na planilha do Google Sheets.
    """
    try:
        data_atual = datetime.date.today().strftime('%Y-%m-%d')
        sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=SHEET_NAME,
            valueInputOption='RAW',
            body={'values': [[ip_hash, data_atual, nome, nome_evento]]}
        ).execute()
        st.success(f"Presença de {nome} registrada com sucesso para o evento: {nome_evento}!")
    except Exception as e:
        st.error(f"Erro ao registrar presença: {e}")

def main():
    """
    Função principal para executar o sistema de registro de presença.
    """
    st.title("Sistema de Registro de Presença")
    st.subheader("Especialização em Gestão Portuária")

    # Verifica a localização do usuário
    if not verificar_localizacao():
        st.error("Acesso negado: Você precisa estar próximo à UFMA para registrar sua presença.")
        return

    eventos = ler_datas_do_calendario(CALENDAR_FILE)
    if not eventos:
        st.error("Não foi possível obter as datas dos eventos. O programa será encerrado.")
        return

    tem_evento, nome_evento = verificar_data_atual(eventos)
    if not tem_evento:
        st.warning("Não há evento agendado para hoje.")
        return

    st.subheader(f"Disciplina do dia: {nome_evento}")

    try:
        creds = get_google_credentials()
        if creds is None:
            st.error("Não foi possível carregar as credenciais do Google Sheets.")
            return
            
        service = build('sheets', 'v4', credentials=creds)
        sheet = service.spreadsheets()
        
        # Tenta obter os valores, mas não retorna se estiver vazio
        values_result = sheet.values().get(spreadsheetId=SPREADSHEET_ID, range=SHEET_NAME).execute()
        
        ip_hash = obter_ip_hash()
        if ip_hash is None:
            st.error("Não foi possível obter o seu endereço IP. O registro de presença não pode continuar.")
            return

        # Verifica registro único apenas se houver valores na planilha
        if 'values' in values_result:
            ja_registrado = verificar_registro_unico(ip_hash, sheet)
            if ja_registrado:
                st.warning("Você já registrou sua presença hoje.")
                return

        nome = st.text_input("Por favor, insira seu nome:")
        if st.button("Registrar Presença"):
            if nome:
                registrar_presenca(nome, ip_hash, sheet, nome_evento)
            else:
                st.warning("Por favor, insira seu nome antes de registrar a presença.")

    except Exception as e:
        st.error(f"Erro ao conectar com o Google Sheets: {e}")
        return

if __name__ == "__main__":
    main()
