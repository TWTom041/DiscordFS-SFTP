from urllib.parse import urlparse
from typing import Union, Iterable
import time


class DSUrl:
    """
    Managing URLs for Discord attachments
    """

    def __init__(
        self,
        channel_id: int,
        message_id: int,
        attachment_id: int,
        filename: Union[str, bytes]=None,  # if is str, encode to bytes
        expire: int=None,
        issue: int=None,
        signature: bytes=None,
    ) -> None:
        self.channel_id = channel_id
        self.message_id = message_id
        self.attachment_id = attachment_id
        self.filename = filename if isinstance(filename, bytes) else filename.encode() 
        self.expire = expire
        self.issue = issue
        self.signature = signature

    @classmethod
    def from_url(self, url, message_id):
        """
        Create a DSUrl object from a URL

        Args:
            url (str): The URL to create the DSUrl object from
            message_id (int): The message ID

        Returns:
            DSUrl: The DSUrl object
        """
        parsed_url = urlparse(url)
        query = parsed_url.query
        query = filter(None, query.split("&"))
        query = {i.split("=")[0]: i.split("=")[1] for i in query}
        issue = int(query["is"], 16)
        expire = int(query["ex"], 16)
        signature = bytes.fromhex(query["hm"])

        ctx = parsed_url.path.split("/")[2:5]
        channel_id = int(ctx[0])
        attachment_id = int(ctx[1])
        filename = ctx[2] if isinstance(ctx[2], bytes) else ctx[2].encode()
        return DSUrl(channel_id, message_id, attachment_id, filename, expire, issue, signature)

    @property
    def save_format(self):
        """the format for saving to database"""
        return [self.channel_id, self.message_id, self.attachment_id, self.filename, self.expire, self.issue, self.signature]

    @property
    def url(self):
        """the url of the file, without expire, issue and signature"""
        if self.filename is None:
            raise ValueError("Filename is not set")
        return f"https://cdn.discordapp.com/attachments/{self.channel_id}/{self.attachment_id}/{self.filename.decode()}"
    
    @property
    def full_url(self):
        """the full url of the file"""
        if self.filename is None or self.expire is None or self.issue is None or self.signature is None:
            raise ValueError(f"Required attribute is not set: filename={self.filename}, expire={self.expire}, issue={self.issue}, signature={self.signature}")
        return f"https://cdn.discordapp.com/attachments/{self.channel_id}/{self.message_id}/{self.attachment_id}/{self.filename.decode()}?ex={self.expire:x}&is={self.issue:x}&hm={self.signature.hex()}"
    
    def __str__(self) -> str:
        return self.url
    
    def __repr__(self) -> str:
        return f"<DSUrl {self.url}>"



class BaseExpirePolicy:
    def __init__(self):
        pass

    def is_expired(self, dsurl):
        """check if the url is expired, will be True if the url will expire in 10 minutes"""
        timenow = int(time.time())
        return timenow > dsurl.expire - 600
    
    def setup(self, *args, **kwargs):
        """setup the expire policy"""
        pass

    def renew_url(self, dsurls: Iterable[DSUrl]):
        """renew the url"""
        raise NotImplementedError()