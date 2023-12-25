DiscordFS-SFTP
============

Utilizing Discord's free storage to create a filesystem with SFTP server capabilities.

## Overview

This project leverages Discord's free storage through webhooks and integrates with PyMongo and PyFilesystem2 to create a filesystem. Additionally, it provides the capability to create a secure SFTP server for file operations.

## Features

- **Discord Integration:** Utilizes Discord webhooks for free storage and communication.
- **Database Storage:** MongoDB integration through PyMongo for metadata and file management.
- **Filesystem Operations:** Powered by pyfilesystem2 for handling OS operations in a seamless manner.
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

- SFTP connection details can be configured in `config.yaml`.
- You should create a file called webhooks.txt with your webhooks, one webhook per line.
- You can use the bot we created [link](https://discord.com/api/oauth2/authorize?client_id=1186899111643987990&permissions=536872960&scope=bot) or **host the bot**.

#### Host the Bot

- create `.env` file and insert your bot token:
```.env
TOKEN=your_bot_token
```
- install dependencies:
```bash
pip install -r requirements-bot.txt
```
- run `bot.py`

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
    
    Bind your `webhooks.txt` to `/app/webhooks.yaml` or it won't work.
    You may also bind your `config.yaml` to `/app/config.yaml`, if no config is provided, you'll use the default config, which isn't quite safe. If you want to use your host key, bind it to `/app/host_key`.
    ```yaml
    services:
        dsfs:
            build: .
            ports:
                - "8022:8022"  # change it if you need to.
            volumes:
                - "/path/to/config.yaml:/app/config.yaml"
                - "/path/to/webhooks.txt:/app/webhooks.txt"
                - "/path/to/host_key:/app/host_key"
        ...
    ```
2. Run Docker compose

    ```bash
    docker compose up
    ```


## Example

If you're using the default config.yaml, and you want to log into shrek's account, you should do this:
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

`expose_sftp.py` is adapted from [PyFilesystem](https://github.com/PyFilesystem/pyfilesystem/blob/master/fs/expose/sftp.py) and makes it support PyFilesystem2. You should edit `config.yaml` to have detailed settings of the SFTP server.

## Contribution
Feel free to contribute by opening issues or submitting pull requests.

## License

This project is licensed under the [MIT License](LICENSE).
