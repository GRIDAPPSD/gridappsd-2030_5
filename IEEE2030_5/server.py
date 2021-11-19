import logging
import typing

from typing import Optional

from fastapi import FastAPI, Response

from IEEE2030_5 import IEEE2030_5_ENDPOINTS, XML_HEADERS
import uvicorn

from IEEE2030_5 import ConfigObj, TLSRepository
from IEEE2030_5.endpoints import dcap


class IEEE2030_5Response(Response):
    media_type = "application/xml"  # "application/sep+xml"

    def render(self, content: str) -> bytes:
        return content.encode("utf-8")


def run_server(config: ConfigObj, tlsrepo: TLSRepository):

    app = FastAPI()
    #
    # # Map name to function for loose coupling.
    # endpoint_mapping = dict(
    #     dcap=dcap
    # )
    #
    #
    # def mycallback():
    #     return {"woot": "there it is!"}
    #

    # # Testing how to get the headers and a callback to work properly with glue
    def fn_wrapper(callback):
        return Response(media_type="application/xml",
                        content=callback())
    #
    #
    # def load_endpoints(app):
    #     for d, endpoint in IEEE2030_5_ENDPOINTS.items():
    #
    #         callback = endpoint_mapping.get(endpoint.callback)
    #         if callback is None:
    #             callback = mycallback
    #         else:
    #             callback = fn_wrapper(callback)
    #         # TODO modify endpoint.callback to be an actual function
    #         # This is probably not done here but in the IEEE2030_5_ENDPOINTS module.
    #         app.add_api_route(endpoint.url, callback)
    #
    #
    # @app.get("/")
    # def read_root():
    #     return {"Hello": "World"}
    #
    #
    # @app.get("/items/{item_id}")
    # def read_item(item_id: int, q: Optional[str] = None):
    #     return {"item_id": item_id, "q": q}
    #
    #
    # # https://www.geeksforgeeks.org/python-xml-to-json/
    #
    cb = fn_wrapper(dcap)
    app.add_api_route("/dcap", dcap, response_class=IEEE2030_5Response)
    # @app.get("/dcap")

    #if __name__ == "__main__":
    #    load_endpoints(app)
    app.openapi()
    uvicorn.run(app, host="0.0.0.0", port=8000) # , reload=True)