# GitSearch

Охота на конфиденциальные данные в GitHub: dork‑запросы, API и Python‑скрипт

## Введение – зачем искать по GitHub

GitHub содержит более 400 миллионов репозиториев. Разработчики нередко случайно коммитят файлы с паролями, API‑ключами и другими секретами. Поиск таких «утечек» — важная задача для:

**Brand Protection** – выявление использования фирменных токенов до того, как злоумышленники их найдут.

**Blue‑Team Leak Hunting** – мониторинг собственных публичных и внутренних репозиториев.

Статья покажет, как автоматизировать процесс с помощью GitHub Code Search API и Python‑скрипта.

## Предварительные требования

[+] GitHub PAT - берем здесь: @git_keys_shop_bot

[+] Python ≥ 3.10

[+] Используем match/case и typing.

[+] Дополнительные библиотеки - requests, argparse, tqdm, csv, time, pathlib, signal, re. Устанавливаются командой:pip install requests tqdm

# 5. Пошаговое руководство

## Установка

```bash
python -m venv venv && source venv/bin/activate
pip install requests tqdm

```

## Пример запуска

```bash
python GitSearch.py \
  --token $GITHUB_PAT \
  --dork "filename:.env DB_PASSWORD" \
  --resume

```

## Что появится

```
output/
└─ github.com/user/repo/.env
findings.csv  # контекст + ссылки

```

`findings.csv` можно открыть в Excel для фильтрации строк.

# 6. Сценарии применения

- **Защита бренда**: обнаружение опубликованных клиентских SDK‑ключей до индексации поисковиками.
- **Внутренние проверки**: автоматизированный скан open‑source зеркал компании.

# 7. Заключение и дальнейшие шаги

Используя GitHub API и простой Python‑скрипт, можно построить ежедневный мониторинг. Рекомендуется интегрировать результат с SIEM или Slack‑ботом и настроить cron‑запуск.

# 8. Дисклеймер

*Скрипт предназначен исключительно для законного аудита. Вы несёте полную ответственность за соблюдение GitHub TOS, законов о защите данных и уведомление владельцев репозиториев при обнаружении утечек.*

---

# 1. Title

**Hunting Sensitive Data on GitHub: Dork Queries, API & Python Script**

# 2. Introduction – Why GitHub Search Matters

With 400 M+ repositories, GitHub has become the world’s largest code archive—and an endless source of accidental secrets. Engineers commit `.env` files; DevOps push CI logs; interns forget to purge test credentials. A proactive search keeps your brand and customers safe:

- **Brand Protection** – catch exposed API tokens before attackers do.
- **Blue‑Team Leak Hunting** – continuously scan your own public & internal org repos.

This article shows how to automate the hunt using GitHub Code Search API and Python.

# 3. Prerequisites

| Requirement | Details |
| --- | --- |
| **GitHub PAT** | At least `public_repo` scope. Create via *Settings → Developer settings → Personal access tokens (Classic)*. |
| **Python ≥ 3.10** | We use modern syntax and type hints. |
| Extra libs | `requests`, `argparse`, `tqdm`, `csv`, `time`, `pathlib`, `signal`, `re`. Install with:`pip install requests tqdm` |

# 4. Script Listing

*(Identical to the Russian block above for easy copy‑paste.)*

```python
# see previous code block – same content

```

# 5. Step‑by‑Step Guide

## Installation

```bash
python -m venv venv && source venv/bin/activate
pip install requests tqdm

```

## Example Command

```bash
python gh_dork_download.py \
  --token YOUR_GITHUB_PAT \
  --dork "filename:.env DB_PASSWORD" \
  --resume

```

## Output Explained

```
output/
└─ github.com/user/repo/.env
findings.csv  # match context & links

```

Open `findings.csv` in Excel, or pipe into a SIEM pipeline.

# 6. Use‑Case Scenarios

- **Brand Protection / Digital Risk** – discover leaked SaaS credentials, licensed SDK keys, or copyrighted assets.
- **Internal Security Audits** – validate engineers follow secrets‑management policy; feed results into JIRA tickets.

# 7. Conclusion & Next Steps

The presented Python tool covers 10 000 results per run—enough for daily monitoring of high‑risk terms. Next, schedule it in `cron`, feed alerts into Slack, and add richer regexes to classify findings.

# 8. Disclaimer – Legal & Ethical Usage

This script is provided for legitimate security audits **only**. Always comply with GitHub Terms of Service, data‑protection laws, and responsible disclosure guidelines. Never use the data for malicious purposes.

# GitSearch
Hunting Sensitive Data on GitHub: Dork Queries, API &amp; Python Script
