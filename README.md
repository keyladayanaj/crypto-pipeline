# 📈 Crypto Market Tracker

Pipeline de dados end-to-end que coleta preços de criptomoedas da API CoinGecko a cada hora, armazena em PostgreSQL e exibe em um dashboard interativo com Streamlit.

---

## 🏗️ Arquitetura

```
CoinGecko API
      │
      ▼
 collector.py  ──►  detect_alerts()
      │                   │
      ▼                   ▼
PostgreSQL ◄─── save_snapshot() + save_alerts()
      │
      ▼
 Streamlit Dashboard (localhost:8501)
```

**Stack:** Python 3.11 · PostgreSQL 15 · SQLAlchemy 2 · APScheduler · Streamlit · Plotly · Docker

---

## 🚀 Setup em 2 comandos

```bash
make setup   # copia .env e faz build das imagens
make run     # sobe tudo em background
```

Acesse:
- **Dashboard:** http://localhost:8501
- **Banco (Adminer):** http://localhost:8080 *(server: db, user: admin, senha: secret)*

---

## 📁 Estrutura do Projeto

```
crypto-pipeline/
├── src/
│   ├── config.py       # Configurações via variáveis de ambiente
│   ├── collector.py    # Coleta da API + detecção de alertas
│   ├── database.py     # Models SQLAlchemy + funções de persistência
│   └── scheduler.py    # Orquestração e agendamento (entry point)
├── dashboard/
│   └── app.py          # Dashboard Streamlit completo
├── tests/
│   ├── test_collector.py
│   └── test_database.py
├── docker-compose.yml  # Postgres + Adminer + App + Dashboard
├── Dockerfile
├── Makefile            # make run / make test / make logs
├── requirements.txt
└── .env.example
```

---

## ⚙️ Variáveis de Ambiente

| Variável | Padrão | Descrição |
|---|---|---|
| `DATABASE_URL` | `postgresql://...` | String de conexão do Postgres |
| `TOP_N_COINS` | `20` | Quantas moedas coletar |
| `COLLECT_INTERVAL_HOURS` | `1` | Frequência de coleta em horas |
| `ALERT_THRESHOLD_PCT` | `5.0` | % de variação para disparar alerta |

---

## 🧪 Testes

```bash
make test
```

Cobertura: coleta da API (com mock), detecção de alertas, persistência, validação de CSV.

---

## 📊 Funcionalidades do Dashboard

- KPIs globais: Market Cap total, Volume 24h, variação média
- Tabela completa com formatação condicional (verde/vermelho)
- Ranking top gainers e losers do dia
- Gráfico histórico de preço + volume por moeda (período ajustável)
- Log de alertas de variação extrema

---

## 🛠️ Comandos úteis

```bash
make logs    # ver logs do pipeline em tempo real
make stop    # parar todos os containers
make clean   # parar + remover volumes + limpar cache
```

---

*Dados fornecidos pela [CoinGecko API](https://www.coingecko.com/en/api) (plano gratuito, sem chave necessária)*
