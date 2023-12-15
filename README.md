DiscordSFTP
============

## Overview

This project leverages Discord's free storage through webhooks and integrates with pymongo and pyfilesystem2 to create a filesystem. Additionally, it provides the capability to create a secure SFTP server for file operations.

## Features

- **Discord Integration:** Utilizes Discord webhooks for free storage and communication.
- **Database Storage:** MongoDB integration through pymongo for metadata and file management.
- **Filesystem Operations:** Powered by pyfilesystem2 for handling OS operations in a seamless manner.
- **SFTP Server:** Ability to create a secure SFTP server for file transfer and management.

## Prerequisites

Ensure you have the following installed:

- Python 3.x
- Required Python packages: `discord`, `pymongo`, `fs`, `paramiko`
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


## Usage

1. Run the main script:

    ```bash
    python expose_sftp.py
    ```

2. Access the filesystem and SFTP server through the specified endpoints.
    ```bash
    sftp -P <PORT> user@<HOST>
    ```


## Example

If you're using the default config.yaml, and you want to log into shrek's account, you should do this:
```bash
sftp -P 8022 shrek@127.0.0.1
```
when asked for password, you should input `somebodyoncetoldme`.

And if you want to log into nopwduser, the command is the same, but you don't need to provide a password to log in.

For logging into pubkeyuser, you can either provide a keyfile:
```bash
sftp -P 8022 -i testkey shrek@127.0.0.1
```
or you can provide a password.

But if you want to log into purepubkeyuser, password is not allowed.
Logging into uselessuser is impossible, because neither Password nor PubKey is not provided.

## Contribution
Feel free to contribute by opening issues or submitting pull requests.

## License

This project is licensed under the [MIT License](LICENSE).
