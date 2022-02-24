"""API interface base class."""
from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import AbstractAsyncContextManager
import random
from typing import Any, cast

from aiohttp import ClientResponse, ClientSession, ClientTimeout

from .consts import API_URL, LOGIN_KEY, TIMEOUT
from .exceptions import (
    SleepIQAPIException,
    SleepIQLoginException,
    SleepIQTimeoutException,
)


def random_user_agent() -> str:
    """Create a randomly generated sorta valid User Agent string."""
    uas = {
        "Edge": (
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/98.0.4758.80 Safari/537.36 Edg/98.0.1108.43"
        ),
        "Chrome": (
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/97.0.4692.99 Safari/537.36"
        ),
        "Firefox": "Gecko/20100101 Firefox/96.0",
        "iphone": (
            "AppleWebKit/605.1.15 (KHTML, like Gecko) "
            "Version/15.2 Mobile/15E148 Safari/604.1"
        ),
        "Safari": (
            "AppleWebKit/605.1.15 (KHTML, like Gecko) " "Version/11.1.2 Safari/605.1.15"
        ),
    }
    os = {
        "windows": "Windows NT 10.0; Win64; x64",
        "iphone": "iPhone; CPU iPhone OS 15_2_1 like Mac OS X",
        "mac": "Macintosh; Intel Mac OS X 10_11_6",
    }
    template = "Mozilla/5.0 ({os}) {ua}"

    return template.format(
        os=random.choice(list(os.values())), ua=random.choice(list(uas.values()))
    )


class SleepIQAPI:
    """API interface base class."""

    def __init__(
        self,
        email: str | None = None,
        password: str | None = None,
        login_method: int = LOGIN_KEY,
        client_session: ClientSession | None = None,
    ) -> None:
        """Initialize AsyncSleepIQ API Interface."""
        self.email = email
        self.password = password
        self.key = ""
        self._session = client_session or ClientSession()
        self._headers = {"User-Agent": random_user_agent()}
        self._login_method = login_method

    async def close_session(self) -> None:
        """Close the API session."""
        if self._session:
            await self._session.close()

    async def login(
        self, email: str | None = None, password: str | None = None
    ) -> None:
        """Login using the with the email/password provided or stored."""
        if not email:
            email = self.email
        if not password:
            password = self.password
        if not email or not password:
            raise SleepIQLoginException("username/password not set")

        try:
            if self._login_method == LOGIN_KEY:
                await self.login_key(email, password)
            else:
                await self.login_cookie(email, password)

        except asyncio.TimeoutError as ex:
            # timed out
            raise SleepIQTimeoutException("API call timed out") from ex
        except SleepIQTimeoutException as ex:
            raise ex
        except Exception as ex:
            raise SleepIQLoginException(f"Connection failure: {ex}") from ex

        # store in case we need to login again
        self.email = email
        self.password = password

    async def login_key(self, email: str, password: str) -> None:
        """Login using the key authentication method with the email/password provided."""
        self.key = ""
        auth_data = {"login": email, "password": password}

        async with self._session.put(
            API_URL + "/login", headers=self._headers, timeout=TIMEOUT, json=auth_data
        ) as resp:

            if resp.status == 401:
                raise SleepIQLoginException("Incorrect username or password")
            if resp.status == 403:
                raise SleepIQLoginException(
                    "User Agent is blocked. May need to update GenUserAgent data?"
                )
            if resp.status not in (200, 201):
                raise SleepIQLoginException(
                    "Unexpected response code: {code}\n{body}".format(
                        code=resp.status,
                        body=resp.text,
                    )
                )

            json = await resp.json()
            self.key = json["key"]

    async def login_cookie(self, email: str, password: str) -> None:
        """Login using the cookie authentication method with the email/password provided."""
        auth_data = {
            "Email": email,
            "Password": password,
            "ClientID": "2oa5825venq9kek1dnrhfp7rdh",
        }
        async with self._session.post(
            "https://l06it26kuh.execute-api.us-east-1.amazonaws.com/Prod/v1/token",
            headers=self._headers,
            timeout=TIMEOUT,
            json=auth_data,
        ) as resp:

            if resp.status == 401:
                raise SleepIQLoginException("Incorrect username or password")
            if resp.status == 403:
                raise SleepIQLoginException(
                    "User Agent is blocked. May need to update GenUserAgent data?"
                )
            if resp.status not in (200, 201):
                raise SleepIQLoginException(
                    "Unexpected response code: {code}\n{body}".format(
                        code=resp.status,
                        body=resp.text,
                    )
                )
            json = await resp.json()
            token = json["data"]["AccessToken"]
            self._headers["Authorization"] = token

        async with self._session.get(
            API_URL + "/user/jwt", headers=self._headers, timeout=TIMEOUT
        ) as resp:
            if resp.status not in (200, 201):
                raise SleepIQLoginException(
                    "Unexpected response code: {code}\n{body}".format(
                        code=resp.status,
                        body=resp.text,
                    )
                )

    async def put(
        self, url: str, json: dict[str, Any] = {}, params: dict[str, Any] = {}
    ) -> None:
        """Make a PUT request to the API."""
        await self.__make_request(self._session.put, url, json, params)

    async def get(
        self, url: str, json: dict[str, Any] = {}, params: dict[str, Any] = {}
    ) -> dict[str, Any] | Any:
        """Make a GET request to the API."""
        return await self.__make_request(self._session.get, url, json, params)

    async def check(
        self, url: str, json: dict[str, Any] = {}, params: dict[str, Any] = {}
    ) -> bool:
        """Check if a GET request to the API would be successful."""
        return cast(
            bool,
            await self.__make_request(self._session.get, url, json, params, check=True),
        )

    async def __make_request(
        self,
        make_request: Callable[..., AbstractAsyncContextManager[ClientResponse]],
        url: str,
        json: dict[str, Any] = {},
        params: dict[str, Any] = {},
        retry: bool = True,
        check: bool = False,
    ) -> bool | dict[str, Any] | Any:
        """Make a request to the API."""
        timeout = ClientTimeout(total=TIMEOUT)
        params["_k"] = self.key
        try:
            async with make_request(
                API_URL + "/" + url,
                headers=self._headers,
                timeout=timeout,
                json=json,
                params=params,
            ) as resp:
                if check:
                    return resp.status == 200

                if resp.status != 200:
                    if retry and resp.status in (401, 404):
                        # login and try again
                        await self.login()
                        return await self.__make_request(
                            make_request, url, json, params, False
                        )
                    raise SleepIQAPIException(
                        f"API call error response {resp.status}\n{resp.text}"
                    )
                return await resp.json()
        except asyncio.TimeoutError as ex:
            # timed out
            raise SleepIQTimeoutException("API call timed out") from ex
