from urllib.parse import urlparse
from typing import Union, Iterable

class DSUrl:
    """
    Managing URLs for Discord attachments
    """

    def __init__(
        self,
        channel_id: int,
        message_id: int,
        filename: Union[str, bytes]=None,  # if is str, encode to bytes
        expire: int=None,
        signature: bytes=None,
    ) -> None:
        self.channel_id = channel_id
        self.message_id = message_id
        self.filename = filename if isinstance(filename, bytes) else filename.encode() 
        self.expire = expire
        self.signature = signature

    @classmethod
    def from_url(self, url):
        """
        Create a DSUrl object from a URL

        Args:
            url (str): The URL to create the DSUrl object from

        Returns:
            DSUrl: The DSUrl object
        """
        parsed_url = urlparse(url)
        query = parsed_url.query
        query = filter(None, query.split("&"))
        query = {i.split("=")[0]: i.split("=")[1] for i in query}
        expire = int(query["ex"], 16)
        signature = bytes.fromhex(query["hm"])

        ctx = parsed_url.path.split("/")[2:5]
        channel_id = int(ctx[0])
        message_id = int(ctx[1])
        filename = ctx[2] if isinstance(ctx[2], bytes) else ctx[2].encode()
        return DSUrl(channel_id, message_id, filename, expire, signature)

    @property
    def save_format(self):
        return [self.channel_id, self.message_id, self.filename, self.expire, self.signature]

    @property
    def url(self):
        if self.filename is None:
            raise ValueError("Filename is not set")
        return f"https://cdn.discordapp.com/attachments/{self.channel_id}/{self.message_id}/{self.filename.decode()}"
    
    def __str__(self) -> str:
        return self.url



class BaseExpirePolicy:
    def __init__(self, expire_time):
        self.expire_time = expire_time

    def is_expired(self, url):
        raise NotImplementedError()
    
    def setup(self):
        pass

    def renew_url(self, dsurls: Iterable[DSUrl]):
        raise NotImplementedError()