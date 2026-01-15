import redis
from environs import env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update, InputMediaPhoto
from telegram.ext import Filters, Updater, CallbackContext
from telegram.ext import CallbackQueryHandler, CommandHandler, MessageHandler

from cms import (
    get_products,
    get_product,
    get_product_picture,
    create_cart,
    create_cart_item,
    add_items_to_cart,
    get_cart_by_id,
    remove_cart_item,
    create_client,
)

_database = None


def start(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния START.

    Бот отвечает пользователю фразой "Привет!" и переводит его в состояние HANDLE_MENU.
    Теперь в ответ на его команды будет запускаеться хэндлер handle_menu.
    """

    if update.callback_query and update.callback_query.data == "RETURN_TO_MENU":
        update.callback_query.delete_message()

    keyboard = []

    for product in get_products():
        keyboard.append(
            [InlineKeyboardButton(text=product["title"], callback_data=product["documentId"])]
        )

    keyboard.append([InlineKeyboardButton("Моя корзина", callback_data="SHOW_CART")])

    message = update.message or update.callback_query.message
    message.reply_text("Please choose:", reply_markup=InlineKeyboardMarkup(keyboard))

    return "HANDLE_MENU"


def handle_menu(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния HANDLE_MENU.

    Бот отправляет данные товара по его id.
    Переводит пользователя в состояние START.
    """
    query = update.callback_query
    query.answer()

    if query.data == "SHOW_CART":
        return show_cart(update, context)

    product = get_product(update.callback_query.data)

    if picture := product.get("picture"):
        picture_url = picture["formats"]["thumbnail"]["url"]
        picture = get_product_picture(picture_url)
    else:
        picture = None

    keyboard = [
        [InlineKeyboardButton(text="Добавить в корзину", callback_data=product["documentId"])],
        [InlineKeyboardButton("Моя корзина", callback_data="SHOW_CART")],
        [InlineKeyboardButton(text="Назад", callback_data="RETURN_TO_MENU")],
    ]
    query.edit_message_media(
        media=InputMediaPhoto(picture, caption=product["description"]),
        reply_markup=InlineKeyboardMarkup(keyboard),
    )
    return "HANDLE_DESCRIPTION"


def handle_description(update: Update, context: CallbackContext):
    """
    Хэндлер для состояния HANDLE_DESCRIPTION.

    Если была нажата кнопка Назад - переводит в меню.
    Если была нажата кнопка Корзина - показывает товары в корзине.

    Бот создаёт новую корзину.
    Переводит пользователя в состояние START.
    """
    query = update.callback_query

    if query.data == "RETURN_TO_MENU":
        return start(update, context)
    if query.data == "SHOW_CART":
        return show_cart(update, context)

    cart_id = get_or_create_cart_id(telegram_id=query.message.chat_id)
    cart_item_id = create_cart_item(cart_id=cart_id, product_id=query.data)
    add_items_to_cart(cart_id=cart_id, cart_items=[cart_item_id])
    query.answer("Товар добавлен в корзину", show_alert=True)
    query.delete_message()
    return start(update, context)


def show_cart(update: Update, context: CallbackContext):
    """
    Хэндлер состояния SHOW_CART
    Бот показывает корзину пользователя.
    Переводит в состояние HANDLE_CART
    """
    query = update.callback_query
    query.answer()

    cart_id = get_or_create_cart_id(query.message.chat_id)
    cart_items = get_cart_by_id(cart_id).get("cart_items", [])

    text = []
    keyboard = []

    for item in cart_items:
        text.append(f"{item['product']['title']} - {item['quantity']}кг.")
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"Убрать {item['product']['title']}", callback_data=item["documentId"]
                )
            ]
        )

    keyboard.append([InlineKeyboardButton(text="Оплатить", callback_data="REQUEST_EMAIL")])
    keyboard.append([InlineKeyboardButton(text="В меню", callback_data="RETURN_TO_MENU")])

    text = "\n".join(text) or "В корзине пусто..."
    query.delete_message()
    query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))

    return "HANDLE_CART"


def handle_cart(update: Update, context: CallbackContext):
    """
    Хэндлер состояния HANDLE_CART
    Бот удаляет выбранные товары из корзины.
    Переводит в состояние SHOW_CART
    """

    query = update.callback_query

    if query.data == "RETURN_TO_MENU":
        return start(update, context)
    elif query.data == "REQUEST_EMAIL":
        return request_email(update, context)

    remove_cart_item(query.data)
    query.answer("Товар удалён из корзины", show_alert=True)
    return show_cart(update, context)


def request_email(update: Update, context: CallbackContext):
    """
    Бот запрашивает почту пользователя.
    Переводит в состояние HANDLE_WAITING_EMAIL
    """

    update.callback_query.edit_message_text("Введите адрес электронный почты")
    return "HANDLE_WAITING_EMAIL"


def handle_waiting_email(update: Update, context: CallbackContext):
    """
    Хэндлер состояния HANDLE_WAITING_EMAIL
    Бот получает почту пользователя и сохраняет её в cms.
    Переводит в состояние START
    """

    create_client(telegram_id=update.message.chat_id, email=update.message.text)
    keyboard = [[InlineKeyboardButton(text="В меню", callback_data="RETURN_TO_MENU")]]

    update.message.reply_text("Заказ оформлен!", reply_markup=InlineKeyboardMarkup(keyboard))
    return "START"


def handle_users_reply(update: Update, context: CallbackContext):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    Если пользователь только начал пользоваться ботом, Telegram форсит его написать "/start",
    поэтому по этой фразе выставляется стартовое состояние.
    Если пользователь захочет начать общение с ботом заново, он также может воспользоваться этой командой.
    """
    db = get_database_connection()
    if update.message:
        user_reply = update.message.text
        chat_id = update.message.chat_id
    elif update.callback_query:
        user_reply = update.callback_query.data
        chat_id = update.callback_query.message.chat_id
    else:
        return
    if user_reply == "/start":
        user_state = "START"
    else:
        user_state = db.get(chat_id).decode("utf-8")

    states_functions = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description,
        "HANDLE_CART": handle_cart,
        "HANDLE_WAITING_EMAIL": handle_waiting_email,
    }
    state_handler = states_functions[user_state]

    next_state = state_handler(update, context)
    db.set(chat_id, next_state)


def get_database_connection():
    """
    Возвращает конекшн с базой данных Redis, либо создаёт новый, если он ещё не создан.
    """
    global _database
    if _database is None:
        _database = redis.Redis()
    return _database


def get_or_create_cart_id(telegram_id: int) -> str:
    db = get_database_connection()
    key = f"cart:{telegram_id}"

    if cart_id := db.get(key):
        return cart_id.decode("utf-8")

    cart_id = create_cart(telegram_id)
    db.set(key, cart_id)

    return cart_id


if __name__ == "__main__":
    env.read_env()
    tg_bot_token = env("TG_BOT_TOKEN")

    updater = Updater(tg_bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    updater.start_polling()
    updater.idle()
