import sqlite3


def test_autocommit():
    conn = sqlite3.connect(":memory:", autocommit=True)

    # First cursor creates table and inserts value (DML)
    cur = conn.cursor()
    cur.execute("CREATE TABLE foo(a int)")
    cur.execute("INSERT INTO foo VALUES (42)")
    cur.close()

    # Second cursor fetches 42 due to the autocommit
    cur = conn.cursor()
    cur.execute("SELECT * FROM foo")
    assert cur.fetchone() == (42,)
    assert cur.fetchone() is None

    cur.close()
    conn.close()

def test_manual():
    conn = sqlite3.connect(":memory:", autocommit=False)

    # First cursor creates table, insert rolls back
    cur = conn.cursor()
    cur.execute("CREATE TABLE foo(a int)")
    conn.commit()
    cur.execute("INSERT INTO foo VALUES (42)")
    cur.close()
    conn.rollback()

    # Second connection fetches nothing due to the rollback
    cur = conn.cursor()
    cur.execute("SELECT * FROM foo")
    assert cur.fetchone() is None

    cur.close()
    conn.close()

test_autocommit()
test_manual()
