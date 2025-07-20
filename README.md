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

# Пошаговое руководство

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

```

## Запуск тестов
```bash
pip install -r requirements-dev.txt
pytest
```

## Что появится

```
output/
└─ github.com/user/repo/.env
findings.csv  # контекст + ссылки

```

`findings.csv` можно открыть в Excel для фильтрации строк.

# Сценарии применения

- **Защита бренда**: обнаружение опубликованных клиентских SDK‑ключей до индексации поисковиками.
- **Внутренние проверки**: автоматизированный скан open‑source зеркал компании.

1. Скрипт выкачивает все подряд файлы с гитхаба с ключевыми словами:

<img width="1170" alt="Скрипт выкачивает все подряд файлы с гитхаба с ключевыми словами" src="https://github.com/user-attachments/assets/cf7ae597-1ed0-4355-9589-bb16d7aff9cc" />

(Я вижу на скрине ключ, забирайте)

2. Ищем по файлам:
```bash
grep -R --line-number --color=auto "AWS_ACCESS_KEY_ID"    
```

3. Получаем желаемое:
<img width="670" alt="Имеем на выходе кучу дедиков" src="https://github.com/user-attachments/assets/9ee54d74-4b1a-4a46-aad6-8678b6d72b92" />



# Заключение и дальнейшие шаги

Используя GitHub API и простой Python‑скрипт, можно построить ежедневный мониторинг. Рекомендуется интегрировать результат с SIEM или Slack‑ботом и настроить cron‑запуск.

# Дисклеймер

*Скрипт предназначен исключительно для законного аудита. Вы несёте полную ответственность за соблюдение GitHub TOS, законов о защите данных и уведомление владельцев репозиториев при обнаружении утечек.*

---

# GitSearch
Hunting Confidential Data on GitHub: Dork Queries, API, and a Python Script

## Introduction — Why Search GitHub
GitHub hosts more than 400 million repositories. Developers sometimes accidentally commit files containing passwords, API keys, and other secrets. Detecting such “leaks” is crucial for:

**Brand Protection** — discovering company-specific tokens before attackers do.

**Blue-Team Leak Hunting** — monitoring your public and internal repositories.

This guide shows how to automate the process using the GitHub Code Search API and a Python script.

## Prerequisites
GitHub PAT — via @git_keys_shop_bot

Python ≥ 3.10 — the script uses modern features like match/case and type hints.

Libraries — requests, argparse, tqdm, csv, time, pathlib, signal, re.
Install with:

pip install requests tqdm

## Step-by-Step Guide

**Installation**

```bash
python -m venv venv && source venv/bin/activate
pip install requests tqdm

```

## Example Run

```bash
python GitSearch.py \
  --token $GITHUB_PAT \
  --dork "filename:.env DB_PASSWORD" \

```

## Running Tests
```bash
pip install -r requirements-dev.txt
pytest
```

## What You Get

```
output/
└─ github.com/user/repo/.env
`findings.csv`  # context + links
```

Open findings.csv in Excel or any spreadsheet tool to filter rows.

## Use-Case Scenarios

**Brand Protection** — detect leaked client SDK keys before search engines index them.

**Internal Audits** — automate scanning of the company’s open-source mirrors.

##Conclusion & Next Steps

With the GitHub API and a lightweight Python script, you can build a daily monitoring routine. Integrate the results into your SIEM or a Slack bot, and schedule it via cron for continuous coverage.

## Disclaimer

This script is intended solely for lawful security auditing. You are fully responsible for complying with GitHub’s Terms of Service, data-protection laws, and for notifying repository owners when leaks are discovered.
