from typing import Text, Optional, Collection, Any, BinaryIO
import os
import string
import sys

import fs
import fs.base
import fs.errors
import fs.info
import fs.subfs
import fs.permissions
import yaml

from dsdrive_api import DSdriveApi, HookTool
from config_loader import Config

sys.setrecursionlimit(1200)

class DiscordFS(fs.base.FS):
    def __init__(self, dsdrive_api=None) -> None:
        self.dsdrive_api: DSdriveApi = dsdrive_api
        self._lock = fs.base.threading.RLock()
        self._meta = {"read_only": False, "unicode_paths": True, "case_insensitive": False}

    def get_new_fs(self):
        return DiscordFS(self.dsdrive_api)

    def getinfo(self, path, namespaces=None):
        # type: (Text, Optional[Collection[Text]]) -> fs.info.Info
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
        self.check()
        stat, info = self.dsdrive_api.get_info(path)
        if stat == 1:
            raise fs.errors.ResourceNotFound(path)
        return fs.info.Info(info)

    def listdir(self, path, *a, **k):
        # # type: (Text) -> List[Text]
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
        self.check()
        stat, objs = list(self.dsdrive_api.list_dir(path))
        if stat == 1:
            raise fs.errors.ResourceNotFound(path)
        elif stat == 2:
            raise fs.errors.DirectoryExpected(path)
        return [i["name"] for i in objs]



    def makedir(
        self,
        path,  # type: Text
        permissions=None,  # type: Optional[fs.permissions.Permissions]
        recreate=False,  # type: bool
    ):
        # type: (...) -> fs.subfs.SubFS[fs.FS]
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
        self.check()
        paths = self.dsdrive_api.path_splitter(path)
        stat, parent_id = self.dsdrive_api.makedirs(paths, allow_many=False, exist_ok=recreate)
        if stat == 1:
            raise fs.errors.ResourceNotFound(path)
        elif stat == 2:
            raise fs.errors.DirectoryExists(path)
        elif stat == 3:
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
        self.check()
        if all(i not in mode for i in ("r", "w", "a", "x")):
            raise ValueError("Must be a valid non-text mode")
        if not path.isprintable():
            raise fs.errors.InvalidCharsInPath(path)
        paths = self.dsdrive_api.path_splitter(path)
        stat, fn = self.dsdrive_api.find(paths, return_obj=True)
        if stat == 0:
            if fn["type"] == "folder":
                raise fs.errors.FileExpected(path)
        
            if "x" in mode:
                raise fs.errors.FileExists(path)
        else:
            if stat == 1:
                if not ("w" in mode or "a" in mode or "x" in mode):
                    raise fs.errors.ResourceNotFound((path, mode))           
            elif stat == 2:
                raise fs.errors.ResourceNotFound((path, mode))

        
        return self.dsdrive_api.open_binary(path, mode)
    
    def copy(
        self,
        src_path,  # type: Text
        dst_path,  # type: Text
        overwrite=False,  # type: bool
        preserve_time=False,  # type: bool
    ):
        # type: (...) -> None
        """Copy file contents from ``src_path`` to ``dst_path``.

        Arguments:
            src_path (str): Path of source file.
            dst_path (str): Path to destination file.
            overwrite (bool): If `True`, overwrite the destination file
                if it exists (defaults to `False`).
            preserve_time (bool): If `True`, try to preserve mtime of the
                resource (defaults to `False`).

        Raises:
            fs.errors.DestinationExists: If ``dst_path`` exists,
                and ``overwrite`` is `False`.
            fs.errors.ResourceNotFound: If a parent directory of
                ``dst_path`` does not exist.
            fs.errors.FileExpected: If ``src_path`` is not a file.

        """
        self.check()
        stat = self.dsdrive_api.copy(src_path, dst_path, overwrite=overwrite, preserve_timestamps=preserve_time)
        if stat == 1:
            raise fs.errors.ResourceNotFound(src_path)
        elif stat == 2:
            raise fs.errors.FileExpected(src_path)
        elif stat == 3:
            raise fs.errors.DestinationExists(dst_path)
    
    def move(self, src_path, dst_path, overwrite=False, preserve_time=False):
        # type: (Text, Text, bool, bool) -> None
        """Move a file from ``src_path`` to ``dst_path``.

        Arguments:
            src_path (str): A path on the filesystem to move.
            dst_path (str): A path on the filesystem where the source
                file will be written to.
            overwrite (bool): If `True`, destination path will be
                overwritten if it exists.
            preserve_time (bool): If `True`, try to preserve mtime of the
                resources (defaults to `False`).

        Raises:
            fs.errors.FileExpected: If ``src_path`` maps to a
                directory instead of a file.
            fs.errors.DestinationExists: If ``dst_path`` exists,
                and ``overwrite`` is `False`.
            fs.errors.ResourceNotFound: If a parent directory of
                ``dst_path`` does not exist.

        """
        self.check()
        stat = self.dsdrive_api.rename(src_path, dst_path, overwrite=overwrite, preserve_timestamps=preserve_time)
        if stat == 1:
            raise fs.errors.ResourceNotFound(src_path)
        elif stat == 2:
            raise fs.errors.FileExpected(src_path)
        elif stat == 3:
            raise fs.errors.DestinationExists(dst_path)

    def remove(self, path):
        # type: (Text) -> None
        """Remove a file from the filesystem.

        Arguments:
            path (str): Path of the file to remove.

        Raises:
            fs.errors.FileExpected: If the path is a directory.
            fs.errors.ResourceNotFound: If the path does not exist.

        """
        self.check()
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
        self.check()
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
        # type: (Text, fs.info.RawInfo) -> None
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
        self.check()

        stat = self.dsdrive_api.set_info(path, info)
        if stat == 1:
            raise fs.errors.ResourceNotFound(path)
    
    def validatepath(self, path: Text) -> Text:
        if not path.isprintable():
            raise fs.errors.InvalidCharsInPath(path)
        return super().validatepath(path)
        

if __name__ == "__main__":
    fulltest = True
    configs = Config(config_filename=".conf/config.yaml", host_key_filename=".conf/host_key", webhooks_filename=".conf/webhooks.txt", bot_token_filename=".conf/bot_token")
    hooks = HookTool(configs.webhooks)

    dsdriveapi = DSdriveApi(configs.mgdb_url, hooks, token=configs.bot_token)

    # discord_fs = DiscordFS()
    # discord_fs.dsdrive_api = dsdriveapi
    # print(discord_fs.listdir("test"))
    import unittest
    from fs.test import FSTestCases
    
    class TestMyFS(FSTestCases, unittest.TestCase):

        def make_fs(self):
            dsdriveapi.clear()
            # Return an instance of your FS object here
            discord_fs = DiscordFS(dsdriveapi)
            return discord_fs
    if fulltest:
        unittest.main()
    else:
        dsfs = DiscordFS(dsdriveapi)
        print(dsfs.getmeta())



