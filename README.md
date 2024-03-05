# dou-api

## 1. To Use

**Responde post no endpoint `/dou`.**

Cabecalho `data` no request recebe a chave como nome da coluna a filtrar
e uma lista de strings com o valor dos filtros a serem aplicados.

### 1.1. Schema cabeçalho data para o request

```
"exemplo_de_cabecalho_data_para_o_request": {
    "name": ["filter1", "filter2", "..."],
    "pub_name": ["filter1", "filter2", "..."],
    "pub_date": ["filter1", "filter2", "..."],
    "art_category": ["filter1", "filter2", "..."],
    "identifica": ["filter1", "filter2", "..."],
    "titulo": ["filter1", "filter2", "..."],
    "sub_titulo": ["filter1", "filter2", "..."],
    "texto": ["filter1", "filter2", "..."],
}
```

### 1.2. Exemplo CURL

```bash
curl -X POST "http://url:5057/dou" \
    -H "Content-Type: application/json" \
    -d '{"texto": ["licitação"], "pub_name": ["DO3"]}'
```

### 1.3. Exemplo python

```python
import requests
import json

url = 'http://url:5057/dou'
data = {
    "texto": ["licitação"],
    "pub_name": ["DO3"]
}
headers = {
    'Content-Type': 'application/json'
}
response = requests.post(url, headers=headers, data=json.dumps(data))
```

## 2. To Dev

1. Duplicar e renomear `.env.template`.

```bash
cp .env.template .env
```

2. Atualizar as variáveis de ambiente `INLABS_EMAIL`, `INLABS_PASSWORD`,
`SLACK_BOT_URL` em `.env`.

3. Rodar:

```bash
docker compose up
```

## 3. To Deploy

1. Duplicar e renomear `k8s/secrets.yml.template`.

```bash
cp k8s/secrets.yml.template k8s/secrets.yml
```

2. Atualizar as secrets kubernetes `INLABS_EMAIL`, `INLABS_PASSWORD`,
`SLACK_BOT_URL` em k8s/secrets.yml.

> [!WARNING]
> Colocar valor dos secrets em base64 com comando `echo -n "valor" | base64`

3. Rodar:

```bash
kubectl apply -f k8s/secrets.yml && \
kubectl apply -f k8s/manifest.yml
```

## 4. How CICD works

O Github Actions está definido em [build-push-deploy.yml](/.github/workflows/build-push-deploy.yml).

**Comportamento**:

* Quando criada uma `tag`:
    - Faz o build do dockerfile
    - Publica no packages do Github a imagem `:latest` e `:tag`
    - Deleta o pod no kubernetes para novo pull da imagem `:latest`