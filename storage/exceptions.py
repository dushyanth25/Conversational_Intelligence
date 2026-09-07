class StorageError(Exception):
    pass

class StorageConnectionError(StorageError):
    pass

class StorageAuthenticationError(StorageError):
    pass

class BucketMissingError(StorageError):
    pass

class ObjectNotFoundError(StorageError):
    pass

class UploadError(StorageError):
    pass

class DownloadError(StorageError):
    pass

class CorruptedObjectError(StorageError):
    pass
