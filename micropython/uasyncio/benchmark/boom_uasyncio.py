#
# This is validation script for "boom" tool https://github.com/tarekziade/boom
# To use it:
#
# boom -n1000 --post-hook=boom_uasyncio.validate <rest of boom args>
#
# Note that if you'll use other -n value, you should update NUM_REQS below
# to match.
#

NUM_REQS = 1000
seen = []
cnt = 0

def validate(resp):
    global cnt
    t = resp.text
    l = t.split("\r\n", 1)[0]
    no = int(l.split()[1])
    seen.append(no)
    c = t.count(l + "\r\n")
    assert c == 400101, str(c)
    assert t.endswith("=== END ===")

    cnt += 1
    if cnt == NUM_REQS:
        seen.sort()
        print
        print seen
        print
        el = None
        for i in seen:
            if el is None:
                el = i
            else:
                el += 1
                assert i == el
    return resp
