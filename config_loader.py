import yaml
import paramiko

class Config:
    def __init__(self, config_filename=None, host_key_filename=None, webhooks_filename=None, bot_token_filename=None):
        if config_filename is not None:
            self.load_config_file(config_filename)
        if host_key_filename is not None:
            self.load_host_key(host_key_filename)
        if webhooks_filename is not None:
            self.load_webhooks(webhooks_filename)
        if bot_token_filename is not None:
            self.load_bot_token(bot_token_filename)


    def load_config_file(self, config_filename):
        with open(config_filename, "r") as file:
            config = yaml.load(file.read(), Loader=yaml.FullLoader)
            mongodb_config = config.get("MongoDB", {})
            mongo_prefix = mongodb_config.get("Prefix", "mongodb://")
            mongo_host = mongodb_config.get("Host", "127.0.0.1")
            mongo_port = mongodb_config.get("Port", "27017")
            self.mgdb_url = f"{mongo_prefix}{mongo_host}:{mongo_port}"

            sftp_config = config.get("SFTP", {})
            self.sftp_host = sftp_config.get("Host", "0.0.0.0")
            self.sftp_port = sftp_config.get("Port", "8022")
            self.sftp_noauth = sftp_config.get("NoAuth", False)
            self.sftp_auths = sftp_config.get("Auths", [{"Username": "Anonymous", "Password": "susman"}])
    

    def load_host_key(self, host_key_filename):
        self.sftp_host_key = paramiko.RSAKey.from_private_key_file(host_key_filename)
    

    def load_webhooks(self, webhooks_filename):
        with open(webhooks_filename, "r") as file:
            self.webhooks = file.read().splitlines()

    def load_bot_token(self, token_filename):
        with open(token_filename, "r") as file:
            self.bot_token = file.read().strip()


def test_loader():
    config = Config(config_filename=".conf/config.yaml", host_key_filename=".conf/host_key", webhooks_filename=".conf/webhooks.txt", bot_token_filename=".conf/bot_token")
    print(config.mgdb_url)
    print(config.sftp_host)
    print(config.sftp_port)
    print(config.sftp_noauth)
    print(config.sftp_auths)
    print(config.sftp_host_key)
    print(config.webhooks)
    print(config.bot_token)


if __name__ == "__main__":
    test_loader()
