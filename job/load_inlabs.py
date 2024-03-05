#!/usr/local/bin/python

import os
import subprocess
import logging
from datetime import date
import glob
import zipfile
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import xml.etree.ElementTree as ET
import sqlite3
from slack_sdk import WebhookClient

# Configura logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

BASE_URL = "https://inlabs.in.gov.br"

CREDENTIALS = {
    "email": os.environ.get("INLABS_EMAIL"),
    "password": os.environ.get("INLABS_PASSWORD"),
}
DEST_PATH = "/tmp/download_dou"
DB_PATH = "/dou-api/data"
SLACK_BOT_URL = os.environ.get("SLACK_BOT_URL")

# 1. Criar diretórios se não existirem


def create_directories():
    subprocess.run(f"mkdir -p {DEST_PATH}", shell=True, check=True)
    subprocess.run(f"mkdir -p {DB_PATH}", shell=True, check=True)

    logging.info(f"Directories `{DEST_PATH}`, `{DB_PATH}` created.")


# 2. Autenticar no inlabs


def get_session():
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    session = requests.Session()
    session.request(
        "POST", urljoin(BASE_URL, "logar.php"), data=CREDENTIALS, headers=headers
    )

    # test if logged
    if session.cookies.get("inlabs_session_cookie", False):
        return session
    else:
        raise ValueError("Auth failed")


# 3. Baixar arquivos


def download_files(session):
    cookie = session.cookies.get("inlabs_session_cookie")
    # 3.1 Descobrir arquivos disponíveis
    headers = {"Cookie": f"inlabs_session_cookie={cookie}", "origem": "736372697074"}
    response = session.request(
        "GET",
        urljoin(BASE_URL, f"index.php?p={date.today().strftime('%Y-%m-%d')}"),
        headers=headers,
    )

    soup = BeautifulSoup(response.text, "html.parser")
    a_tags = soup.find_all("a", title="Baixar Arquivo")
    files = [tag.get("href") for tag in a_tags if tag.get("href").endswith(".zip")]

    # 3.2. Baixar arquivos
    headers = {"Cookie": f"inlabs_session_cookie={cookie}", "origem": "736372697074"}

    for file in files:
        r = session.request(
            "GET", urljoin(BASE_URL, f"index.php{file}"), headers=headers
        )
        with open(os.path.join(DEST_PATH, file.split("dl=")[1]), "wb") as f:
            f.write(r.content)

    logging.info(f"Downloaded files: {files}.")

    return files


# 4. Descompactar


def unzip_files():
    all_files = os.listdir(DEST_PATH)
    # filter zip files
    zip_files = [file for file in all_files if file.endswith(".zip")]
    for zip_file in zip_files:
        zip_file_path = os.path.join(DEST_PATH, zip_file)
        with zipfile.ZipFile(zip_file_path, "r") as zip_ref:
            zip_ref.extractall(os.path.join(DEST_PATH, "extract"))

    logging.info(f"Unzipped files: {zip_files}.")


# 5. Escrever no banco


def init_db(conn):
    cursor = conn.cursor()
    cursor.execute(
        """
            CREATE TABLE IF NOT EXISTS article (
                article_id INTEGER,
                name TEXT,
                pub_name TEXT,
                art_type TEXT,
                pub_date TEXT,
                art_category TEXT,
                pdf_page TEXT,
                identifica TEXT,
                data TEXT,
                ementa TEXT,
                titulo TEXT,
                sub_titulo TEXT,
                texto TEXT)
        """
    )
    cursor.execute(
        f"DELETE FROM article WHERE pub_date = '{date.today().strftime('%d/%m/%Y')}'"
    )
    conn.commit()


def write_xml_to_db(root, conn):
    cursor = conn.cursor()
    for article in root.findall("article"):
        article_id = article.attrib["id"]
        name = article.attrib["name"]
        pub_name = article.attrib["pubName"]
        art_type = article.attrib["artType"]
        pub_date = article.attrib["pubDate"]
        art_category = article.attrib["artCategory"]
        pdf_page = article.attrib["pdfPage"]
        identifica = article.find("body").find("Identifica").text
        data = article.find("body").find("Data").text
        ementa = article.find("body").find("Ementa").text
        titulo = article.find("body").find("Titulo").text
        sub_titulo = article.find("body").find("SubTitulo").text
        texto = article.find("body").find("Texto").text

        cursor.execute(
            """
                INSERT INTO article (article_id,name,pub_name,art_type,pub_date,art_category,pdf_page,identifica,data,ementa,titulo,sub_titulo,texto) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                article_id,
                name,
                pub_name,
                art_type,
                pub_date,
                art_category,
                pdf_page,
                identifica,
                data,
                ementa,
                titulo,
                sub_titulo,
                texto,
            ),
        )

        conn.commit()


def load_xml_files():
    conn = sqlite3.connect(os.path.join(DB_PATH, "dou.db"))
    init_db(conn)

    for xml_file in glob.glob(
        os.path.join(DEST_PATH, "extract/**/*.xml"), recursive=True
    ):
        tree = ET.parse(xml_file)
        root = tree.getroot()

        write_xml_to_db(root, conn)

    cursor = conn.cursor()
    cursor.execute(
        f"SELECT count(*) from article WHERE pub_date = '{date.today().strftime('%d/%m/%Y')}'"
    )
    row_count = cursor.fetchone()

    conn.close()

    logging.info(
        f"Database `{os.path.join(DB_PATH, 'dou.db')}` updated with {row_count} lines."
    )


# 6. Remover arquivos


def remove_files():
    subprocess.run(f"rm -rf {DEST_PATH}", shell=True, check=True)

    logging.info(f"Directory {DEST_PATH} removed.")


# 7. Notificar slack conclusão


def notify(files):
    webhook = WebhookClient(SLACK_BOT_URL)
    cleaned_files = ", ".join([item.split("dl=")[-1] for item in files])

    response = webhook.send(
        text="Hello from dou-job!",
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"""
                    * :tada: [ref. {date.today().strftime('%Y-%m-%d')}] Dados do DOU atualizados.* \n\n Arquivos: {cleaned_files}
                """,
                },
            }
        ],
    )
    assert response.status_code == 200
    assert response.body == "ok"


if __name__ == "__main__":
    create_directories()
    session = get_session()
    files = download_files(session)
    unzip_files()
    load_xml_files()
    remove_files()
    notify(files)
