<a id="dsurl"></a>

# dsurl

<a id="dsurl.DSUrl"></a>

## DSUrl Objects

```python
class DSUrl()
```

Managing URLs for Discord attachments

<a id="dsurl.DSUrl.from_url"></a>

#### from\_url

```python
@classmethod
def from_url(url, message_id)
```

Create a DSUrl object from a URL

**Arguments**:

- `url` _str_ - The URL to create the DSUrl object from
- `message_id` _int_ - The message ID
  

**Returns**:

- `DSUrl` - The DSUrl object

<a id="dsurl.DSUrl.save_format"></a>

#### save\_format

```python
@property
def save_format()
```

the format for saving to database

<a id="dsurl.DSUrl.url"></a>

#### url

```python
@property
def url()
```

the url of the file, without expire, issue and signature

<a id="dsurl.DSUrl.full_url"></a>

#### full\_url

```python
@property
def full_url()
```

the full url of the file

<a id="dsurl.BaseExpirePolicy"></a>

## BaseExpirePolicy Objects

```python
class BaseExpirePolicy()
```

<a id="dsurl.BaseExpirePolicy.is_expired"></a>

#### is\_expired

```python
def is_expired(dsurl)
```

check if the url is expired, will be True if the url will expire in 10 minutes

<a id="dsurl.BaseExpirePolicy.setup"></a>

#### setup

```python
def setup(*args, **kwargs)
```

setup the expire policy

<a id="dsurl.BaseExpirePolicy.renew_url"></a>

#### renew\_url

```python
def renew_url(dsurls: Iterable[DSUrl])
```

renew the url

