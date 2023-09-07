import logging
import os
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

from ieee_2030_5_gui.init import init

logging.basicConfig(level=logging.DEBUG)

api = FastAPI()

@api.get("/")
def read_root():
    return  RedirectResponse(url='/certs')

init(api)

if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser()
    
    parser.add_argument("config", help="Path to config server configuration file.")
    
    opts = parser.parse_args()
    
    # Because we are going to run uvicorn in a subprocess, we need to pass the config file to it.
    # We do that here through creating a .env file that uvicorn will read.
    with open('.env', 'w') as f:
        f.write(f"CONFIG_FILE={opts.config}")
    
    uvicorn.run("main:api", host="0.0.0.0", port=8000, reload=True, env_file='.env')