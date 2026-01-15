from typing import Any

import requests
from environs import env
from requests import Response, RequestException
import logging

logger = logging.getLogger()


def _send_cms_request(
    endpoint: str, method: str = "get", params: dict = None, data: dict = None
) -> Response:
    cms_api_token = env("CMS_API_TOKEN")
    cms_host = env("CMS_HOST")
    headers = {"Authorization": f"bearer {cms_api_token}"}
    response = requests.request(
        method, f"{cms_host}{endpoint}", headers=headers, params=params, json=data
    )

    try:
        response.raise_for_status()
    except RequestException as e:
        logger.warning(f"REQUEST ERROR {e}\n{response.text = }")
        raise

    return response


def get_products() -> list[dict[str, Any]]:
    response = _send_cms_request("/api/products")
    return response.json()["data"]


def get_product(product_id: str) -> dict[str, Any]:
    response = _send_cms_request(f"/api/products/{product_id}", params={"populate": "picture"})
    return response.json()["data"]


def get_product_picture(picture_url: str) -> bytes:
    response = _send_cms_request(picture_url)
    return response.content


def create_cart(telegram_id: int) -> str:
    data = {"data": {"telegram_id": telegram_id}}
    response = _send_cms_request("/api/carts", method="post", data=data)
    return response.json()["data"]["documentId"]


def get_cart_id_by_telegram_id(telegram_id: int) -> str | None:
    params = {"filters[telegram_id][$eq]": telegram_id}
    response = _send_cms_request("/api/carts/", params=params)
    return response.json()["data"]


def get_cart_by_id(cart_id: str) -> dict[str, Any] | None:
    response = _send_cms_request(
        f"/api/carts/{cart_id}", params={"populate[cart_items][populate][0]": "product"}
    )
    return response.json()["data"]


def add_items_to_cart(cart_id: str, cart_items: list[str]) -> None:
    data = {"data": {"cart_items": {"connect": cart_items}}}
    _send_cms_request(f"/api/carts/{cart_id}", method="put", data=data)


def create_cart_item(cart_id: str, product_id: str) -> str:
    data = {"data": {"cart": cart_id, "product": product_id, "quantity": 1}}
    response = _send_cms_request("/api/cart-items", method="post", data=data)
    return response.json()["data"]["documentId"]


def remove_cart_item(cart_item_id: str) -> None:
    _send_cms_request(f"/api/cart-items/{cart_item_id}", method="delete")


def create_client(telegram_id: int, email: str) -> str:
    data = {"data": {"telegram_id": telegram_id, "email": email}}
    response = _send_cms_request("/api/clients", method="post", data=data)
    return response.json()["data"]["documentId"]
