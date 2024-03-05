from flask import Flask, request, abort, jsonify
import sqlite3

app = Flask(__name__)


def query_db(data):
    conn = sqlite3.connect("/dou-api/data/dou.db")
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    sql_query = "SELECT * FROM article"
    allowed_keys = [
        "name",
        "pub_name",
        "pub_date",
        "art_category",
        "identifica",
        "titulo",
        "sub_titulo",
        "texto",
    ]

    filtered_data = {key: data[key] for key in data if key in allowed_keys}

    sql_params = " AND ".join(
        [
            f"({key} LIKE '%{value[0]}%'"
            + "".join([f" OR {key} LIKE '%{v}%'" for v in value[1:]])
            + ")"
            for key, value in filtered_data.items()
        ]
    )

    if sql_params:
        sql_query = f"{sql_query} WHERE {sql_params}"

    cur.execute(sql_query)
    rows = cur.fetchall()
    results = [dict(row) for row in rows]
    conn.close()

    return results


def assert_data(var):
    if not isinstance(var, dict):
        return False, "Variable is not a dictionary"

    if not all(isinstance(key, str) for key in var.keys()):
        return False, "Not all keys are strings"

    for value in var.values():
        if not isinstance(value, list):
            return False, "One of the values is not a list"
        if not all(isinstance(item, str) for item in value):
            return False, "One of the lists contains non-string elements"

    return True, ""


@app.route("/dou", methods=["POST"])
def get_entries():
    data = request.json

    is_valid, error_message = assert_data(data)
    if not is_valid:
        abort(400, description=error_message)

    results = query_db(data)

    return jsonify(results)


@app.route("/", methods=["GET"])
def get_help():
    help = """
        <h1>Api do DOU diária</h1>

        <p><strong>Responde post no endpoint `/dou`.</strong></p>
        <p>Cabecalho `data` no request recebe a chave como nome da coluna<br>
        a filtrar e uma lista de strings com o valor dos filtros a serem aplicados.</p>

        <h2>Exemplo cabeçalho data para o request</h2>
        <p>"exemplo_de_cabecalho_data_para_o_request": { <br>
            "name": ["filter1", "filter2", "..."], <br>
            "pub_name": ["filter1", "filter2", "..."], <br>
            "pub_date": ["filter1", "filter2", "..."], <br>
            "art_category": ["filter1", "filter2", "..."], <br>
            "identifica": ["filter1", "filter2", "..."], <br>
            "titulo": ["filter1", "filter2", "..."], <br>
            "sub_titulo": ["filter1", "filter2", "..."], <br>
            "texto": ["filter1", "filter2", "..."], <br>
        }</p>

        <h2>Exemplo CURL</h2>
        <p>``` <br>
        curl -X POST "http://a3cc3c4ab83724ac591bf3338ea2cf99-1795401753.sa-east-1.elb.amazonaws.com:5057/dou" \ <br>
            -H "Content-Type: application/json" \ <br>
            -d '{"texto": ["licitação"], "pub_name": ["DO3"]}' <br>
        ```</p>

        <h2>Exemplo python</h2>
        <p>``` <br>
        import requests <br>
        import json <br>
        <br>
        url = 'http://a3cc3c4ab83724ac591bf3338ea2cf99-1795401753.sa-east-1.elb.amazonaws.com:5057/dou' <br>
        data = { <br>
            "texto": ["licitação"], <br>
            "pub_name": ["DO3"] <br>
        } <br>
        headers = { <br>
            'Content-Type': 'application/json' <br>
        } <br>
        response = requests.post(url, headers=headers, data=json.dumps(data)) <br>
        ```</p>
    """

    return help


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5057, debug=True)
