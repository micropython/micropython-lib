import sys
import ffilib
import uctypes


sq3 = ffilib.open("libsqlite3")

# int sqlite3_open(
#  const char *filename,   /* Database filename (UTF-8) */
#  sqlite3 **ppDb          /* OUT: SQLite db handle */
# );
sqlite3_open = sq3.func("i", "sqlite3_open", "sp")
# int sqlite3_config(int, ...);
sqlite3_config = sq3.func("i", "sqlite3_config", "ii")
# int sqlite3_get_autocommit(sqlite3*);
sqlite3_get_autocommit = sq3.func("i", "sqlite3_get_autocommit", "p")
# int sqlite3_close_v2(sqlite3*);
sqlite3_close = sq3.func("i", "sqlite3_close_v2", "p")
# int sqlite3_prepare(
#  sqlite3 *db,            /* Database handle */
#  const char *zSql,       /* SQL statement, UTF-8 encoded */
#  int nByte,              /* Maximum length of zSql in bytes. */
#  sqlite3_stmt **ppStmt,  /* OUT: Statement handle */
#  const char **pzTail     /* OUT: Pointer to unused portion of zSql */
# );
sqlite3_prepare = sq3.func("i", "sqlite3_prepare_v2", "psipp")
# int sqlite3_finalize(sqlite3_stmt *pStmt);
sqlite3_finalize = sq3.func("i", "sqlite3_finalize", "p")
# int sqlite3_step(sqlite3_stmt*);
sqlite3_step = sq3.func("i", "sqlite3_step", "p")
# int sqlite3_column_count(sqlite3_stmt *pStmt);
sqlite3_column_count = sq3.func("i", "sqlite3_column_count", "p")
# int sqlite3_column_type(sqlite3_stmt*, int iCol);
sqlite3_column_type = sq3.func("i", "sqlite3_column_type", "pi")
# int sqlite3_column_int(sqlite3_stmt*, int iCol);
sqlite3_column_int = sq3.func("i", "sqlite3_column_int", "pi")
# double sqlite3_column_double(sqlite3_stmt*, int iCol);
sqlite3_column_double = sq3.func("d", "sqlite3_column_double", "pi")
# const unsigned char *sqlite3_column_text(sqlite3_stmt*, int iCol);
sqlite3_column_text = sq3.func("s", "sqlite3_column_text", "pi")
# sqlite3_int64 sqlite3_last_insert_rowid(sqlite3*);
sqlite3_last_insert_rowid = sq3.func("l", "sqlite3_last_insert_rowid", "p")
# const char *sqlite3_errmsg(sqlite3*);
sqlite3_errmsg = sq3.func("s", "sqlite3_errmsg", "p")


SQLITE_OK = 0
SQLITE_ERROR = 1
SQLITE_BUSY = 5
SQLITE_MISUSE = 21
SQLITE_ROW = 100
SQLITE_DONE = 101

SQLITE_INTEGER = 1
SQLITE_FLOAT = 2
SQLITE_TEXT = 3
SQLITE_BLOB = 4
SQLITE_NULL = 5

SQLITE_CONFIG_URI = 17

# For compatibility with CPython sqlite3 driver
LEGACY_TRANSACTION_CONTROL = -1


class Error(Exception):
    pass


def check_error(db, s):
    if s != SQLITE_OK:
        raise Error(s, sqlite3_errmsg(db))


def get_ptr_size():
    return uctypes.sizeof({"ptr": (0 | uctypes.PTR, uctypes.PTR)})


def __prepare_stmt(db, sql):
    # Prepares a statement
    stmt_ptr = bytes(get_ptr_size())
    res = sqlite3_prepare(db, sql, -1, stmt_ptr, None)
    check_error(db, res)
    return int.from_bytes(stmt_ptr, sys.byteorder)

def __exec_stmt(db, sql):
    # Prepares, executes, and finalizes a statement
    stmt = __prepare_stmt(db, sql)
    sqlite3_step(stmt)
    res = sqlite3_finalize(stmt)
    check_error(db, res)

def __is_dml(sql):
    # Checks if a sql query is a DML, as these get a BEGIN in LEGACY_TRANSACTION_CONTROL
    for dml in ["INSERT", "DELETE", "UPDATE", "MERGE"]:
        if dml in sql.upper():
            return True
    return False


class Connections:
    def __init__(self, db, isolation_level, autocommit):
        self.db = db
        self.isolation_level = isolation_level
        self.autocommit = autocommit

    def commit(self):
        if self.autocommit == LEGACY_TRANSACTION_CONTROL and not sqlite3_get_autocommit(self.db):
            __exec_stmt(self.db, "COMMIT")
        elif self.autocommit == False:
            __exec_stmt(self.db, "COMMIT")
            __exec_stmt(self.db, "BEGIN")

    def rollback(self):
        if self.autocommit == LEGACY_TRANSACTION_CONTROL and not sqlite3_get_autocommit(self.db):
            __exec_stmt(self.db, "ROLLBACK")
        elif self.autocommit == False:
            __exec_stmt(self.db, "ROLLBACK")
            __exec_stmt(self.db, "BEGIN")

    def cursor(self):
        return Cursor(self.db, self.isolation_level, self.autocommit)

    def close(self):
        if self.db:
            if self.autocommit == False and not sqlite3_get_autocommit(self.db):
                __exec_stmt(self.db, "ROLLBACK")

            res = sqlite3_close(self.db)
            check_error(self.db, res)
            self.db = None


class Cursor:
    def __init__(self, db, isolation_level, autocommit):
        self.db = db
        self.isolation_level = isolation_level
        self.autocommit = autocommit
        self.stmt = None

    def __quote(val):
        if isinstance(val, str):
            return "'%s'" % val
        return str(val)

    def execute(self, sql, params=None):
        if self.stmt:
            # If there is an existing statement, finalize that to free it
            res = sqlite3_finalize(self.stmt)
            check_error(self.db, res)

        if params:
            params = [self.__quote(v) for v in params]
            sql = sql % tuple(params)

        if __is_dml(sql) and self.autocommit == LEGACY_TRANSACTION_CONTROL and sqlite3_get_autocommit(self.db):
            # For compatibility with CPython, add functionality for their default transaction
            # behavior. Changing autocommit from LEGACY_TRANSACTION_CONTROL will remove this
            __exec_stmt(self.db, "BEGIN " + self.isolation_level)

        self.stmt = __prepare_stmt(self.db, sql)
        self.num_cols = sqlite3_column_count(self.stmt)

        if not self.num_cols:
            v = self.fetchone()
            # If it's not select, actually execute it here
            # num_cols == 0 for statements which don't return data (=> modify it)
            assert v is None
            self.lastrowid = sqlite3_last_insert_rowid(self.db)

    def close(self):
        if self.stmt:
            res = sqlite3_finalize(self.stmt)
            check_error(self.db, res)
            self.stmt = None

    def __make_row(self):
        res = []
        for i in range(self.num_cols):
            t = sqlite3_column_type(self.stmt, i)
            if t == SQLITE_INTEGER:
                res.append(sqlite3_column_int(self.stmt, i))
            elif t == SQLITE_FLOAT:
                res.append(sqlite3_column_double(self.stmt, i))
            elif t == SQLITE_TEXT:
                res.append(sqlite3_column_text(self.stmt, i))
            else:
                raise NotImplementedError
        return tuple(res)

    def fetchone(self):
        res = sqlite3_step(self.stmt)
        if res == SQLITE_DONE:
            return None
        if res == SQLITE_ROW:
            return self.__make_row()
        check_error(self.db, res)


def connect(fname, uri=False, isolation_level="", autocommit=LEGACY_TRANSACTION_CONTROL):
    if isolation_level not in [None, "", "DEFERRED", "IMMEDIATE", "EXCLUSIVE"]:
        raise Error("Invalid option for isolation level")

    sqlite3_config(SQLITE_CONFIG_URI, int(uri))

    sqlite_ptr = bytes(get_ptr_size())
    sqlite3_open(fname, sqlite_ptr)
    db = int.from_bytes(sqlite_ptr, sys.byteorder)

    if autocommit == False:
        __exec_stmt(db, "BEGIN")

    return Connections(db, isolation_level, autocommit)
