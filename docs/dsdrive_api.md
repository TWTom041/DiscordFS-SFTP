<a id="dsdrive_api"></a>

# dsdrive\_api

<a id="dsdrive_api.HookTool"></a>

## HookTool Objects

```python
class HookTool()
```

A tool to send data to multiple webhooks

**Attributes**:

- `hooks` _list_ - A list of webhook URLs
- `index` _int_ - The index of the current webhook URL
  

**Methods**:

- `get_hook` - Get the current webhook URL
- `send` - Send data to the current webhook URL
- `get` - Send a GET request to a URL, handling rate limits and nothing

<a id="dsdrive_api.HookTool.get_hook"></a>

#### get\_hook

```python
def get_hook()
```

Get the current webhook URL

<a id="dsdrive_api.HookTool.send"></a>

#### send

```python
def send(*args, **kwargs)
```

Send data to the current webhook URL, handling rate limits

**Arguments**:

- `*args` - Arguments to be passed to requests.post
- `**kwargs` - Keyword arguments to be passed to requests.post
  

**Returns**:

- `requests.Response` - The response of the request

<a id="dsdrive_api.HookTool.get"></a>

#### get

```python
def get(*args, **kwargs)
```

Send a GET request to a URL, handling rate limits and nothing

**Arguments**:

- `*args` - Arguments to be passed to requests.get
- `**kwargs` - Keyword arguments to be passed to requests.get
  

**Returns**:

- `requests.Response` - The response of the request

<a id="dsdrive_api.DSFile"></a>

## DSFile Objects

```python
class DSFile(BytesIO)
```

A file-like object that can be used to read and write files on DSdrive

**Attributes**:

- `path` _str_ - The path of the file
- `dsdrive` _DSdriveApi_ - The DSdriveApi object
- `mode` _str_ - The mode of the file
- `_read` _bool_ - Whether the file is readable
- `_write` _bool_ - Whether the file is writable
  

**Methods**:

- `readable` - Whether the file is readable
- `writable` - Whether the file is writable
- `read` - Read the file
- `write` - Write to the file
- `close` - Close the file

<a id="dsdrive_api.DSFile.__init__"></a>

#### \_\_init\_\_

```python
def __init__(path, dsdrive, mode="r", zero_size=False)
```

Create a DSFile object

**Arguments**:

- `path` _str_ - The path of the file
- `dsdrive` _DSdriveApi_ - The DSdriveApi object
- `mode` _str_ - The mode of the file
- `zero_size` _bool_ - Whether the file is empty

<a id="dsdrive_api.DSFile.read"></a>

#### read

```python
def read(size=-1) -> bytes
```

Read the file

**Arguments**:

- `size` _int_ - The number of bytes to read. If -1, read the whole file
  

**Returns**:

- `bytes` - The bytes read
  

**Raises**:

- `OSError` - If the file is not readable

<a id="dsdrive_api.DSFile.write"></a>

#### write

```python
def write(b: bytes) -> int
```

Read the file

**Arguments**:

- `b` _bytes_ - The bytes to write
  

**Returns**:

- `int` - The number of bytes written
  

**Raises**:

- `OSError` - If the file is not writable

<a id="dsdrive_api.DSFile.close"></a>

#### close

```python
def close()
```

Close the file, and send the file to DSdrive if the file is writable

<a id="dsdrive_api.DSdriveApi"></a>

## DSdriveApi Objects

```python
class DSdriveApi()
```

A wrapper class for DSdriveApiWebhook and DSdriveApiBot

<a id="dsdrive_api.DSdriveApi.__init__"></a>

#### \_\_init\_\_

```python
def __init__(*args, **kwargs)
```

Create a DSdriveApi object, where the backend api is either DSdriveApiWebhook or DSdriveApiBot, depending on the value of use_bot

<a id="dsdrive_api.DSdriveApiBase"></a>

## DSdriveApiBase Objects

```python
class DSdriveApiBase()
```

A base class for DSdrive API implementations

<a id="dsdrive_api.DSdriveApiBase.encrypt"></a>

#### encrypt

```python
def encrypt(data: bytes)
```

Encrypt data

**Arguments**:

- `data` _bytes_ - The data to encrypt
- `encryption_func` _function_ - The encryption function to use
  

**Returns**:

- `encrypted` _bytes_ - The encrypted data

<a id="dsdrive_api.DSdriveApiBase.decrypt"></a>

#### decrypt

```python
def decrypt(data: bytes)
```

Decrypt data

**Arguments**:

- `data` _bytes_ - The data to decrypt
- `encryption_func` _function_ - The decryption function to use
  

**Returns**:

- `decrypted` _bytes_ - The decrypted data

<a id="dsdrive_api.DSdriveApiBase.path_splitter"></a>

#### path\_splitter

```python
def path_splitter(path: str)
```

Split a path into a list

**Arguments**:

- `path` _str_ - The path to split
  

**Returns**:

- `filelist` _list_ - The list of directories

<a id="dsdrive_api.DSdriveApiBase.open_binary"></a>

#### open\_binary

```python
def open_binary(path: str, mode: str = "r")
```

Open a file

**Arguments**:

- `path` _str_ - The path of the file
- `mode` _str_ - The mode of the file
  

**Returns**:

- `IO` _DSFile_ - The file-like object

<a id="dsdrive_api.DSdriveApiWebhook"></a>

## DSdriveApiWebhook Objects

```python
class DSdriveApiWebhook(DSdriveApiBase)
```

A class to interact with Discord's file storage system

**Attributes**:

- `db` _pymongo.database.Database_ - The database object
- `hook` _HookTool_ - The HookTool object
- `root_id` _bson.objectid.ObjectId_ - The ID of the root directory
  

**Methods**:

- `clear` - Clear the database, very dangerous
- `path_splitter` - Split a path into a list of directories
- `makedirs` - Create directories
- `find` - Find a path
- `send_file` - Send a file to DSdrive
- `open_binary` - Open a file
- `get_file_urls` - Get the URLs of a file
- `download_file` - Download a file
- `list_dir` - List a directory
- `remove_file` - Remove a file
- `remove_dir` - Remove a directory
- `remove_tree` - Remove a tree
- `get_info` - Get the info of a file or directory
- `set_info` - Set the info of a file or directory

<a id="dsdrive_api.DSdriveApiWebhook.__init__"></a>

#### \_\_init\_\_

```python
def __init__(url: str,
             hook: HookTool,
             url_expire_policy: BaseExpirePolicy = ApiExpirePolicy,
             token: Optional[str] = None,
             key: Union[str, bytes] = "despacito") -> None
```

Create a DSdriveApi object, creates the root directory if it doesn't exist

**Arguments**:

- `url` _str_ - The URL of the MongoDB database
- `hook` _HookTool_ - The HookTool object

<a id="dsdrive_api.DSdriveApiWebhook.clear"></a>

#### clear

```python
def clear()
```

Clear the database safely

<a id="dsdrive_api.DSdriveApiWebhook.makedirs"></a>

#### makedirs

```python
def makedirs(paths: list, allow_many: bool = False, exist_ok: bool = False)
```

Create directories

**Arguments**:

- `paths` _list_ - The list of directories to create
- `allow_many` _bool_ - Whether to allow creating multiple directories
- `exist_ok` _bool_ - Whether to allow creating directories that already exist
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful
- `parent_id` _Union[ObjectID, None]_ - The ID of the last directory created

<a id="dsdrive_api.DSdriveApiWebhook.find"></a>

#### find

```python
def find(paths: str, return_obj: bool = False)
```

Find a path

**Arguments**:

- `paths` _list_ - The list of directories to find
- `return_obj` _bool_ - Whether to return the object found or the ID of the object found
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful
- `found_id` _Union[ObjectID, None]_ - The ID of the last position found

<a id="dsdrive_api.DSdriveApiWebhook.send_file"></a>

#### send\_file

```python
def send_file(path: str, file_obj: Union[str, BytesIO, DSFile, None] = None)
```

Send a file to Didcord

**Arguments**:

- `path` _str_ - The path to send the file to
- `file_obj` _Union[str, BytesIO, DSFile]_ - The file to send

<a id="dsdrive_api.DSdriveApiWebhook.get_file_urls"></a>

#### get\_file\_urls

```python
def get_file_urls(path: str)
```

Get the URLs of a file

**Arguments**:

- `path` _str_ - The path of the file
  

**Returns**:

- `filelist` _list_ - The list of URLs of the file

<a id="dsdrive_api.DSdriveApiWebhook.download_file"></a>

#### download\_file

```python
def download_file(path_src: str, path_dst: Optional[str] = None)
```

Download a file from Discord to the local filesystem

**Arguments**:

- `path_src` _str_ - The path of the file on Discord
- `path_dst` _str_ - The path of the file on the local filesystem

<a id="dsdrive_api.DSdriveApiWebhook.list_dir"></a>

#### list\_dir

```python
def list_dir(path: str)
```

List a directory

**Arguments**:

- `path` _str_ - The path of the directory
  

**Returns**:

- `code` _int_ - an error code, or 0 if successful
- `filelist` _Union[Iterable, None]_ - A list of files and directories, or None if an error occured

<a id="dsdrive_api.DSdriveApiWebhook.remove_file"></a>

#### remove\_file

```python
def remove_file(path: str)
```

Remove a file

**Arguments**:

- `path` _str_ - The path of the file
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful

<a id="dsdrive_api.DSdriveApiWebhook.remove_dir"></a>

#### remove\_dir

```python
def remove_dir(path: str)
```

Remove a directory

**Arguments**:

- `path` _str_ - The path of the directory
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful

<a id="dsdrive_api.DSdriveApiWebhook.remove_tree"></a>

#### remove\_tree

```python
def remove_tree(path: str)
```

Remove a tree, not implemented yet

**Arguments**:

- `path` _str_ - The path of the tree
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful

<a id="dsdrive_api.DSdriveApiWebhook.rename"></a>

#### rename

```python
def rename(path_src: str,
           path_dst: str,
           overwrite: bool = False,
           create_dirs: bool = False,
           preserve_timestamps: bool = False)
```

Rename a file or directory

**Arguments**:

- `path_src` _str_ - The path of the file or directory
- `path_dst` _str_ - The new path of the file or directory
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful

<a id="dsdrive_api.DSdriveApiWebhook.copy"></a>

#### copy

```python
def copy(path_src: str,
         path_dst: str,
         overwrite: bool = False,
         create_dirs: bool = False,
         preserve_timestamps: bool = False)
```

Copy a file or directory

**Arguments**:

- `path_src` _str_ - The path of the file or directory
- `path_dst` _str_ - The new path of the file or directory
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful

<a id="dsdrive_api.DSdriveApiWebhook.get_info"></a>

#### get\_info

```python
def get_info(path: str)
```

Get the info of a file or directory

**Arguments**:

- `path` _str_ - The path of the file or directory
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful
- `info` _dict_ - The info of the file or directory

<a id="dsdrive_api.DSdriveApiWebhook.set_info"></a>

#### set\_info

```python
def set_info(path: str, info: dict)
```

Set the info of a file or directory

**Arguments**:

- `path` _str_ - The path of the file or directory
- `info` _dict_ - The info you want to set
  

**Returns**:

- `code` _int_ - An error code, or 0 if successful

