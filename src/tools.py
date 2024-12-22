from pydantic import BaseModel, Field
from langchain.tools import tool
from typing import Literal
import requests
from bs4 import BeautifulSoup
from langchain_community.tools import TavilySearchResults
from dotenv import load_dotenv

load_dotenv()

class AddShoppingListInput(BaseModel):
    item: str = Field(description="elemento da aggiungere alla lista, l'elemento deve essere singolo")
    overwrite: bool = Field(description="True per sovrascrivere la lista, False per aggiungere l'elemento in concatenazione con quelli già scritti nella lista")

class HoroscopeInput(BaseModel):
    segno: Literal[
        'ariete',
        'toro',
        'gemelli',
        'cancro',
        'leone',
        'vergine',
        'bilancia',
        'scorpione',
        'sagittario',
        'capricorno',
        'acquario',
        'pesci'
    ] = Field(description='segno zodiacale da scegliere')
    periodo: Literal[
        'oggi',
        'mese',
        'anno'
    ] = Field(description="periodo di riferimento dell'oroscopo")

class SendMessageInput(BaseModel):
    destinatario: Literal[
        'Giulia',
        'Federico'
    ] = Field(description='Destinatario a cui mandare il messaggio')
    messaggio: str = Field(description="Messaggio da mandare al destinatario. Se serve sfrutta l'indentazione per renderlo più leggibile")

@tool("add_shopping_list", args_schema=AddShoppingListInput)
def add_shopping_list(
    item: str,
    overwrite: bool
) -> str:
    """
    Questa funzione serve ad aggiungere elementi alla lista della spesa.
    Se più elementi devono essere aggiunti alla lista della spesa, utilizza questa funzione per ognuno singolarmente.
    C'è la possibilità di sovrascrivere la vecchia lista per crearne una nuova.
    Se non viene specificato, non sovrascrivere mai la lista.
    Dopo aver aggiungo uno o più elementi chiedi sempre all'utente se ci sono altri elementi da aggiungere.
    Quando l'utente ti dice che non ci sono altri elementi da aggiungere, chiedi sempre successivamente se ci sono altri richieste da risolvere.
    """

    with open('artifacts/shopping_list.txt', "w" if overwrite else "a") as file:
        file.write(f"{item}\n")

    return f"{item} aggiunto"

@tool("leggi_oroscopo", args_schema=HoroscopeInput)
def leggi_oroscopo(
    segno: str,
    periodo: str
) -> str:
    """
    Questa funzione serve a cercare su internet informazioni sull'oroscopo odierno del segno desiderato.
    Quando ti viene chiesto l'oroscopo utilizza obbligatoriamente questo tool.
    Non rielaborare il risultato, riportalo esattamente così come è.
    """
    request = requests.get(f'https://www.corriere.it/oroscopo/{periodo}/{segno}/')
    soup = BeautifulSoup(request.content, 'html.parser', from_encoding='utf-8')
    contents = soup.find_all('div', class_='content')
    paragraphs = []
    for content in contents:
        p = content.find('p')
        if p:
            paragraphs.append(p.get_text())

    horoscope = '\n'.join(paragraphs)

    return horoscope

@tool
def read_shopping_list():
    "Questa funzione serve a leggere la lista della spesa."
    with open('artifacts/shopping_list.txt', "r") as file:
        lista = file.read()
    return lista

search_tool = TavilySearchResults(max_results=5)


