import requests
from .models import BinaryStruct
from requests_toolbelt.multipart import decoder
from app.ua import UA


class Request:

    _body = None
    _url = None
    _binary: BinaryStruct = None
    _status: int = None
    _json = None
    _requestargs = {}

    def __init__(self, url, *args, **kwargs):
        self._url = url
        self._requestargs = kwargs

    async def fetch(self):
        response = requests.get(self._url, headers=self.headers, **self._requestargs)
        self._status = response.status_code
        if response.status_code == 200:
            return response
        else:
            raise requests.RequestException()

    @property
    async def multipart(self) -> decoder.MultipartDecoder:
        response = await self.fetch()
        multipart_data = decoder.MultipartDecoder.from_response(response)
        return multipart_data

    @property
    async def status(self) -> int:
        if not self._status:
            try:
                await self.fetch()
            except Exception as e:
                self._status = 0
        return self._status

    @property
    async def body(self) -> str:
        if not self._body:
            response = await self.fetch()
            self._body = response.text
        return self._body

    @property
    async def json(self) -> dict:
        if not self._json:
            response = await self.fetch()
            self._json = response.json()
        return self._json

    @property
    async def binary(self) -> BinaryStruct:
        if not self._binary:
            resp = await self.fetch()
            self._binary = BinaryStruct(
                binary=resp.content, type=resp.headers.get("content-type")
            )
        return self._binary

    @property
    def headers(self) -> dict:
        return {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
            "Upgrade-Insecure-Requests": "1",
            "Cache-Control": "no-cache",
            "Cookie": "_gcl_au=1.1.110145187.1641683505; didomi_token=eyJ1c2VyX2lkIjoiMTdlM2JmNjUtMDBjMy02NzJmLWJlODUtMDZlNDNkODFkN2ZhIiwiY3JlYXRlZCI6IjIwMjItMDEtMDhUMjM6MTE6NDcuNjMzWiIsInVwZGF0ZWQiOiIyMDIyLTAxLTA4VDIzOjExOjQ3LjYzM1oiLCJ2ZW5kb3JzIjp7ImVuYWJsZWQiOlsidHdpdHRlciIsImM6aG90amFyIiwiYzpnb29nbGVhbmEtNFRYbkppZ1IiXX0sInZlbmRvcnNfbGkiOnsiZW5hYmxlZCI6WyJjOmF3c2tpbmVzaS1NZWRhaGFWYiJdfSwidmVyc2lvbiI6Mn0=; euconsent-v2=CPShQYEPShQYEAHABBENB8CgAP_AAA1AAAAAAAAAAAAA.f_gAAagAAAAA",
            "User-Agent": UA.random,
        }
