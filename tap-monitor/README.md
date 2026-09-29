# TAP Monitor (BEL → Europa)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # PROVIDER=demo já funciona sem chave
python app.py             # http://127.0.0.1:5000
```

Dados reais: crie conta em https://serpapi.com, coloque `PROVIDER=serpapi` e `SERPAPI_KEY=...` no `.env`.
Atenção à cota: chamadas/hora = destinos × datas (padrão 6×1 = 6/h ≈ 4.300/mês). Reduza `DESTINATIONS` para caber no plano.
Se trocar de demo para serpapi, apague `prices.db` para remover o histórico sintético.
