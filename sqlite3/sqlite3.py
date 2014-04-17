import ffi


sq3 = ffi.open("libsqlite3.so.0")

sqlite3_open = sq3.func("i", "sqlite3_open", "sp")
#int sqlite3_prepare(
#  sqlite3 *db,            /* Database handle */
#  const char *zSql,       /* SQL statement, UTF-8 encoded */
#  int nByte,              /* Maximum length of zSql in bytes. */
#  sqlite3_stmt **ppStmt,  /* OUT: Statement handle */
#  const char **pzTail     /* OUT: Pointer to unused portion of zSql */
#);
sqlite3_prepare = sq3.func("i", "sqlite3_prepare", "psipp")
#int sqlite3_step(sqlite3_stmt*);
sqlite3_step = sq3.func("i", "sqlite3_step", "p")
#int sqlite3_column_count(sqlite3_stmt *pStmt);
sqlite3_column_count = sq3.func("i", "sqlite3_column_count", "p")
#int sqlite3_column_type(sqlite3_stmt*, int iCol);
sqlite3_column_type = sq3.func("i", "sqlite3_column_type", "pi")
sqlite3_column_int = sq3.func("i", "sqlite3_column_int", "pi")
# using "d" return type gives wrong results
sqlite3_column_double = sq3.func("f", "sqlite3_column_double", "pi")
sqlite3_column_text = sq3.func("s", "sqlite3_column_text", "pi")


SQLITE_ERROR      = 1
SQLITE_BUSY       = 5
SQLITE_MISUSE     = 21
SQLITE_ROW        = 100
SQLITE_DONE       = 101

SQLITE_INTEGER  = 1
SQLITE_FLOAT    = 2
SQLITE_TEXT     = 3
SQLITE_BLOB     = 4
SQLITE_NULL     = 5


class Connections:

    def __init__(self, h):
        self.h = h

    def cursor(self):
        return Cursor(self.h)


class Cursor:

    def __init__(self, h):
        self.h = h
        self.s = None

    def execute(self, sql):
        b = bytearray(4)
        sqlite3_prepare(self.h, sql, -1, b, None)
        self.s = int.from_bytes(b)
        self.num_cols = sqlite3_column_count(self.s)
        #print("num_cols", self.num_cols)

    def make_row(self):
        res = []
        for i in range(self.num_cols):
            t = sqlite3_column_type(self.s, i)
            #print("type", t)
            if t == SQLITE_INTEGER:
                res.append(sqlite3_column_int(self.s, i))
            elif t == SQLITE_FLOAT:
                res.append(sqlite3_column_double(self.s, i))
            elif t == SQLITE_TEXT:
                res.append(sqlite3_column_text(self.s, i))
            else:
                raise NotImplementedError
        return tuple(res)

    def fetchone(self):
        res = sqlite3_step(self.s)
        #print("step:", res)
        if res == SQLITE_DONE:
            return None
        if res == SQLITE_ROW:
            return self.make_row()
        assert False, res


def connect(fname):
    b = bytearray(4)
    sqlite3_open(fname, b)
    h = int.from_bytes(b)
    return Connections(h)
