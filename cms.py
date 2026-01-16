from typing import Any

import requests
import logging

logger = logging.getLogger()


def get_products(cms_api_token: str, cms_host: str) -> list[dict[str, Any]]:
    response = requests.get(
        f"{cms_host}/api/products", headers={"Authorization": f"bearer {cms_api_token}"}
    )
    response.raise_for_status()
    return response.json()["data"]


def get_product(cms_api_token: str, cms_host: str, product_id: str) -> dict[str, Any]:
    response = requests.get(
        f"{cms_host}/api/products/{product_id}",
        params={"populate": "picture"},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()
    return response.json()["data"]


def get_product_picture(cms_api_token: str, cms_host: str, picture_url: str) -> bytes:
    response = requests.get(
        f"{cms_host}{picture_url}", headers={"Authorization": f"bearer {cms_api_token}"}
    )
    response.raise_for_status()
    return response.content


def create_cart(cms_api_token: str, cms_host: str, telegram_id: int) -> str:
    response = requests.post(
        f"{cms_host}/api/carts",
        json={"data": {"telegram_id": telegram_id}},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()
    return response.json()["data"]["documentId"]


def get_cart_id_by_telegram_id(cms_api_token: str, cms_host: str, telegram_id: int) -> str | None:
    response = requests.get(
        f"{cms_host}/api/carts/",
        params={"filters[telegram_id][$eq]": telegram_id},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()
    return response.json()["data"]


def get_cart_by_id(cms_api_token: str, cms_host: str, cart_id: str) -> dict[str, Any] | None:
    response = requests.get(
        f"{cms_host}/api/carts/{cart_id}",
        params={"populate[cart_items][populate][0]": "product"},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()
    return response.json()["data"]


def add_items_to_cart(
    cms_api_token: str, cms_host: str, cart_id: str, cart_items: list[str]
) -> None:
    response = requests.put(
        f"{cms_host}/api/carts/{cart_id}",
        json={"data": {"cart_items": {"connect": cart_items}}},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()


def create_cart_item(cms_api_token: str, cms_host: str, cart_id: str, product_id: str) -> str:
    response = requests.post(
        f"{cms_host}/api/cart-items",
        json={"data": {"cart": cart_id, "product": product_id, "quantity": 1}},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()
    return response.json()["data"]["documentId"]


def remove_cart_item(cms_api_token: str, cms_host: str, cart_item_id: str) -> None:
    response = requests.delete(
        f"{cms_host}/api/cart-items/{cart_item_id}",
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()


def create_client(cms_api_token: str, cms_host: str, telegram_id: int, email: str) -> str:
    response = requests.post(
        f"{cms_host}/api/clients",
        json={"data": {"telegram_id": telegram_id, "email": email}},
        headers={"Authorization": f"bearer {cms_api_token}"},
    )
    response.raise_for_status()
    return response.json()["data"]["documentId"]
