# GitSearch

Охота на конфиденциальные данные в GitHub: dork‑запросы, API и Python‑скрипт

2. Введение – зачем искать по GitHub

GitHub содержит более 400 миллионов репозиториев. Разработчики нередко случайно коммитят файлы с паролями, API‑ключами и другими секретами. Поиск таких «утечек» — важная задача для:

Brand Protection – выявление использования фирменных токенов до того, как злоумышленники их найдут.

Blue‑Team Leak Hunting – мониторинг собственных публичных и внутренних репозиториев.

Статья покажет, как автоматизировать процесс с помощью GitHub Code Search API и Python‑скрипта.

3. Предварительные требования

Требование

Подробности

GitHub PAT

Минимум scope public_repo. Создайте в Settings → Developer settings → Personal access tokens (Classic).

Python ≥ 3.10

Используем match/case и typing.

Доп. библиотеки

requests, argparse, tqdm, csv, time, pathlib, signal, re. Устанавливаются командой:pip install requests tqdm


# GitSearch
Hunting Sensitive Data on GitHub: Dork Queries, API &amp; Python Script
