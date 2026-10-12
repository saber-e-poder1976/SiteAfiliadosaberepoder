# Motor de produtos Shopee — V4

## Campo de afiliado confirmado

Nos dois CSVs enviados, o campo:

`product_short link`

contém o redirecionamento de afiliado da Shopee (`https://shope.ee/an_redir?...`).

O importador preserva esse valor no campo `link` de cada produto.

## Teste local

```bash
python scripts/atualizar-shopee.py --input "seu-feed.csv"
```

## Produção

Não coloque o link do datafeed no código.

No GitHub, o endereço do feed será armazenado em:

`Settings > Secrets and variables > Actions`

com o nome:

`SHOPEE_DATAFEED_URL`

Depois o GitHub Actions executará o script automaticamente.

## Arquivos gerados

- `data/produtos.json`
- `data/categorias.json`
