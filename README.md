## Требования
Python 3.12
## Установка и запуск
```
pip install pipenv
pipenv install
pipenv shell
Создать файл .secrets.toml из secrets.example.toml
Вставить API ключ от OpenAI и токен от Telegram бота
python main.py
```
## Сборка и запуск через Docker
```
Предварительно настроить файл .secrets.toml по примеру из secrets.example.toml
docker build -t stoicai .
docker run stoicai
```