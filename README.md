DiscordFS-SFTP
============

Utilizing Discord's free storage to create a filesystem with SFTP server capabilities.

## Overview

This project leverages Discord's free storage through webhooks and integrates with PyMongo and PyFilesystem2 to create a filesystem. Additionally, it provides the capability to create a secure SFTP server for file operations.

## Features

- **Discord Integration:** Utilizes Discord webhooks for free storage and communication.
- **Database Storage:** MongoDB integration through PyMongo for metadata and file management.
- **Filesystem Operations:** Powered by pyfilesystem2 for seamlessly handling OS operations.
- **CDN link renewal:** Automatically renew the link when the CDN link expires.
- **SFTP Server:** Ability to create a secure SFTP server for file transfer and management.

## Prerequisites

Ensure you have the following installed:

- Python 3.x
- Required Python packages: [`pymongo`](https://github.com/mongodb/mongo-python-driver), [`fs`](https://github.com/PyFilesystem/pyfilesystem2), [`paramiko`](https://github.com/paramiko/paramiko), [`requests`](https://github.com/psf/requests)
- MongoDB installation on the OS you're running

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/TWTom041/DiscordFS-SFTP.git
    ```

2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Configuration

- SFTP connection details can be configured in `.conf/config.yaml`.
- You should create a file called `.conf/webhooks.txt` with your webhooks, one webhook per line.
- You should create a file called `.conf/bot_token`, which only contains the bot token. Make sure the bot has `MANAGE_WEBHOOKS`, `SEND_MESSAGES` and `READ_MESSAGE_HISTORY` permission.
- *Optional* - You can use the webhook generation bot we created [link](https://discord.com/api/oauth2/authorize?client_id=1186899111643987990&permissions=536872960&scope=bot). Or you can **host the bot yourself**.
- *Optional* - You can also just run `webhook_man_api.py` to interact with discord API and create multiple webhooks swiftly.

> [!Note] 
> Providing bot_token is not just for creating a lot of webhooks at a time, it's also used when renewing the attachment's CDN URL.

#### Host the Bot

- install dependencies:
```bash
pip install -r requirements-bot.txt
```
- run `webhook_man_bot.py`

#### Bot Commands

- `_gen [amount]` generates **amount** webhooks and sends the link to the channel. amount defaults to 1 and can be at most 10.
- `_rem` removes all webhooks in the channel. 

## Usage

1. Run the main script:

    ```bash
    python expose_sftp.py
    ```

2. Access the filesystem and SFTP server through the specified endpoints.
    ```bash
    sftp -P <PORT> user@<HOST>
    ```

## Docker Setup

1. Docker Compose setup:
    
    Bind your `webhooks.txt` to `/app/.conf/webhooks.txt` or it won't work.
    You may also bind your `config.yaml` to `/app/.conf/config.yaml`, if no config is provided, you'll use the default config, which isn't quite safe. If you want to use your host key, bind it to `/app/.conf/host_key`.
    ```yaml
    services:
        dsfs:
            build: .
            ports:
                - "8022:8022"  # change it if you need to.
            volumes:
                - "/path/to/config.yaml:/app/.conf/config.yaml"
                - "/path/to/webhooks.txt:/app/.conf/webhooks.txt"
                - "/path/to/host_key:/app/.conf/host_key"
                - "/path/to/bot_token:/app/.conf/bot_token"
        ...
    ```
2. Run Docker compose

    ```bash
    docker compose up
    ```


## Example

If you're using the default `config.yaml`, and you want to log into shrek's account, you should do this:
```bash
sftp -P 8022 shrek@127.0.0.1
```
when asked for a password, you should input `somebodyoncetoldme`.

And if you want to log into nopwduser, the command is the same, but you don't need to provide a password to log in.

For logging into pubkeyuser, you can either provide a keyfile:
```bash
sftp -P 8022 -i testkey shrek@127.0.0.1
```
or you can provide a password.

But if you want to log into purepubkeyuser, password is not allowed.
Logging into uselessuser is impossible because neither Password nor PubKey is not provided.

## Implementation
First, I created `dsdrive_api.py`, this file is meant to create an interface to communicate with Discord. Specifically, there are 3 classes, named **HookTool**, **DSFile**, **DSdriveApi**.

Then `discord_fs.py` is created. It creates a **FS** subclass that can communicate with **DSdriveApi**, named **DiscordFS**.

`expose_sftp.py` is adapted from [PyFilesystem](https://github.com/PyFilesystem/pyfilesystem/blob/master/fs/expose/sftp.py) and makes it support PyFilesystem2. You should edit `.conf/config.yaml` to have detailed settings of the SFTP server.

## Contribution
Feel free to contribute by opening issues or submitting pull requests.

## License

This project is licensed under the [MIT License](LICENSE).
