class DatabaseError(Exception):
    pass

class DatabaseConnectionError(DatabaseError):
    pass

class UniqueConstraintError(DatabaseError):
    pass

class InvalidDataError(DatabaseError):
    pass

class TransactionError(DatabaseError):
    pass
