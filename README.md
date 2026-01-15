# Телеграм бот для продажи товаров из Strapi CMS

Бот умеет:
- Выводить список товаров
- Отображать информацию о конкретном товаре
- Добавлять/удалять товары из корзины
- Сохранять контакты пользователя для заказа

## Установка Strapi
- Развернуть cms локально - [официальная документация](https://docs.strapi.io/cms/installation/cli) (версия 5.*)
- Запустить командой `npm run develop`
- Создать следующие content-type:
  - Product:
    - title - название
    - description - описание
    - picture - картинка
    - price - цена
  - Client:
    - telegram_id - идентификатор пользователя
    - email - email
  - Cart:
    - telegram_id - идентификатор пользователя
    - cart_items - связь с товарами
  - CartItem:
    - quantity - количество
    - cart - связь с корзиной
    - product - связь с товаром

## Установка Redis
- [официальная документация](https://redis.io/docs/latest/develop/get-started/)

## Установка зависимостей
- Создать виртуальное окружение
```shell
python -m venv .venv
```
- Установить зависимости
```shell
pip install -r requirements.txt
```

## Переменные окружения
- CMS_API_TOKEN - API токен Strapi
- CMS_HOST - адрес cms по умолчанию http://localhost:1337
- TG_BOT_TOKEN - API токен телеграм бота

## Запуск
- Убедиться что cms и redis запущены
- Запустить бота командой `python main.py`
