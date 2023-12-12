import fs
from dsdrive_api import DSdriveApi, HookIter
import os

class DiscordFS(fs.base.FS):
    def __init__(self) -> None:
        self.dsdrive_api = None

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> Info
        """Get information about a resource on a filesystem.

        Arguments:
            path (str): A path to a resource on the filesystem.
            namespaces (list, optional): Info namespaces to query. The
                `"basic"` namespace is alway included in the returned
                info, whatever the value of `namespaces` may be.

        Returns:
            ~fs.info.Info: resource information object.

        Raises:
            fs.errors.ResourceNotFound: If ``path`` does not exist.

        For more information regarding resource information, see :ref:`info`.

        """

    def listdir(self, path):
        # type: (Text) -> List[Text]
        """Get a list of the resource names in a directory.

        This method will return a list of the resources in a directory.
        A *resource* is a file, directory, or one of the other types
        defined in `~fs.enums.ResourceType`.

        Arguments:
            path (str): A path to a directory on the filesystem

        Returns:
            list: list of names, relative to ``path``.

        Raises:
            fs.errors.DirectoryExpected: If ``path`` is not a directory.
            fs.errors.ResourceNotFound: If ``path`` does not exist.

        """
        stat, objs = list(self.dsdrive_api.list_dir("test"))
        if not stat:
            if objs == 1:
                raise fs.errors.ResourceNotFound(path)
            elif objs == 2:
                raise fs.errors.DirectoryExpected(path)
            return None
        return [i["name"] for i in objs]



    def makedir(
        self,
        path,  # type: Text
        permissions=None,  # type: Optional[Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> SubFS[FS]
        """Make a directory.

        Arguments:
            path (str): Path to directory from root.
            permissions (~fs.permissions.Permissions, optional): a
                `Permissions` instance, or `None` to use default.
            recreate (bool): Set to `True` to avoid raising an error if
                the directory already exists (defaults to `False`).

        Returns:
            ~fs.subfs.SubFS: a filesystem whose root is the new directory.

        Raises:
            fs.errors.DirectoryExists: If the path already exists.
            fs.errors.ResourceNotFound: If the path is not found.

        """
        paths = os.path.normpath(path).split(os.sep)
        paths = list(filter(None, paths))
        parent_id = self.dsdrive_api.makedirs(paths, allow_many=False)
        if parent_id == 1:
            raise fs.errors.ResourceNotFound(path)
        elif parent_id == 2:
            raise fs.errors.DirectoryExists(path)

        return fs.subfs.SubFS(self, path)

    def openbin(
        self,
        path,  # type: Text
        mode="r",  # type: Text
        buffering=-1,  # type: int
        **options  # type: Any
    ):
        # type: (...) -> BinaryIO
        """Open a binary file-like object.

        Arguments:
            path (str): A path on the filesystem.
            mode (str): Mode to open file (must be a valid non-text mode,
                defaults to *r*). Since this method only opens binary files,
                the ``b`` in the mode string is implied.
            buffering (int): Buffering policy (-1 to use default buffering,
                0 to disable buffering, or any positive integer to indicate
                a buffer size).
            **options: keyword arguments for any additional information
                required by the filesystem (if any).

        Returns:
            io.IOBase: a *file-like* object.

        Raises:
            fs.errors.FileExpected: If ``path`` exists and is not a file.
            fs.errors.FileExists: If the ``path`` exists, and
                *exclusive mode* is specified (``x`` in the mode).
            fs.errors.ResourceNotFound: If ``path`` does not exist and
                ``mode`` does not imply creating the file, or if any
                ancestor of ``path`` does not exist.

        """

    def remove(self, path):
        # type: (Text) -> None
        """Remove a file from the filesystem.

        Arguments:
            path (str): Path of the file to remove.

        Raises:
            fs.errors.FileExpected: If the path is a directory.
            fs.errors.ResourceNotFound: If the path does not exist.

        """
        stat = self.dsdrive_api.remove_file(path)
        if stat == 1:
            raise fs.errors.ResourceNotFound(path)
        elif stat == 2:
            raise fs.errors.FileExpected(path)

    def removedir(self, path):
        # type: (Text) -> None
        """Remove a directory from the filesystem.

        Arguments:
            path (str): Path of the directory to remove.

        Raises:
            fs.errors.DirectoryNotEmpty: If the directory is not empty (
                see `~fs.base.FS.removetree` for a way to remove the
                directory contents).
            fs.errors.DirectoryExpected: If the path does not refer to
                a directory.
            fs.errors.ResourceNotFound: If no resource exists at the
                given path.
            fs.errors.RemoveRootError: If an attempt is made to remove
                the root directory (i.e. ``'/'``)

        """
        stat = self.dsdrive_api.remove_dir(path)
        if stat == 1:
            raise fs.errors.ResourceNotFound(path)
        elif stat == 2:
            raise fs.errors.DirectoryExpected(path)
        elif stat == 3:
            raise fs.errors.DirectoryNotEmpty(path)
        elif stat == 4:
            raise fs.errors.RemoveRootError(path)

    def setinfo(self, path, info):
        # type: (Text, RawInfo) -> None
        """Set info on a resource.

        This method is the complement to `~fs.base.FS.getinfo`
        and is used to set info values on a resource.

        Arguments:
            path (str): Path to a resource on the filesystem.
            info (dict): Dictionary of resource info.

        Raises:
            fs.errors.ResourceNotFound: If ``path`` does not exist
                on the filesystem

        The ``info`` dict should be in the same format as the raw
        info returned by ``getinfo(file).raw``.

        Example:
            >>> details_info = {"details": {
            ...     "modified": time.time()
            ... }}
            >>> my_fs.setinfo('file.txt', details_info)

        """

with open("webhooks.txt", "r") as file:
    webhook_urls = [i for i in file.read().split("\n") if i]

hook = HookIter(webhook_urls)
dsdriveapi = DSdriveApi("mongodb://localhost:27017/", hook)

discord_fs = DiscordFS()
discord_fs.dsdrive_api = dsdriveapi
