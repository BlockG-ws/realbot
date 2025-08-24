#!/usr/bin/env python3
import asyncio
import getpass
import json
import os
import sys
import aiofiles
from nio import AsyncClient, LoginResponse

CONFIG_FILE = "credentials.json"
# Check out main() below to see how it's done.
def write_details_to_disk(resp: LoginResponse, homeserver) -> None:
    """Writes the required login details to disk so we can log in later without
    using a password.

    Arguments:
        resp {LoginResponse} -- the successful client login response.
        homeserver -- URL of homeserver, e.g. "https://matrix.example.org"
    """
    # open the config file in write-mode
    with open(CONFIG_FILE, "w") as f:
        # write the login details to disk
        json.dump(
            {
                "homeserver": homeserver,  # e.g. "https://matrix.example.org"
                "user_id": resp.user_id,  # e.g. "@user:example.org"
                "device_id": resp.device_id,  # device ID, 10 uppercase letters
                "access_token": resp.access_token,  # cryptogr. access token
            },
            f,
        )

async def main() -> None:
    # If there are no previously-saved credentials, we'll use the password
    if not os.path.exists(CONFIG_FILE):
        print(
            "First time use. Did not find credential file. Asking for "
            "homeserver, user, and password to create credential file."
        )
        homeserver = "https://matrix.example.org"
        homeserver = input(f"Enter your homeserver URL: [{homeserver}] ")
        if not (homeserver.startswith("https://") or homeserver.startswith("http://")):
            homeserver = "https://" + homeserver
        user_id = "@user:example.org"
        user_id = input(f"Enter your full user ID: [{user_id}] ")
        device_name = "matrix-nio"
        device_name = input(f"Choose a name for this device: [{device_name}] ")
        client = AsyncClient(homeserver, user_id)
        pw = getpass.getpass()
        resp = await client.login(pw, device_name=device_name)
        # check that we logged in successfully
        if isinstance(resp, LoginResponse):
            write_details_to_disk(resp, homeserver)
        else:
            print(f'homeserver = "{homeserver}"; user = "{user_id}"')
            print(f"Failed to log in: {resp}")
            sys.exit(1)
        print(
            "登录成功，凭据已经保存到 " + CONFIG_FILE + " 文件中"
        )
    # Otherwise the config file exists, so we'll use the stored credentials
    else:
        print("你已经登录过了")

asyncio.run(main())
