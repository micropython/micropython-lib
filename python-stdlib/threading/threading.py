import _thread
from time import ticks_ms, ticks_diff

try:
    from ucollections import deque as _deque

    _deque.clear
except (ImportError, AttributeError):
    from collections import deque as _deque


class Thread:
    def __init__(self, group=None, target=None, name=None, args=(), kwargs=None):
        self.target = target
        self.args = args
        self.daemon = None
        self.kwargs = {} if kwargs is None else kwargs

    def start(self):
        _thread.start_new_thread(self.run, ())

    def run(self):
        self.target(*self.args, **self.kwargs)

Lock = _thread.allocate_lock


class Condition:
    """Class that implements a condition variable."""

    # A condition variable allows one or more threads to wait until they are
    # notified by another thread.
    # If the lock argument is given and not None, it must be a Lock or RLock
    # object, and it is used as the underlying lock. Otherwise, a new RLock object
    # is created and used as the underlying lock.

    def __init__(self, lock=None):
        if lock is None:
            lock = Lock()
        self._lock = lock
        # Export the lock's acquire() and release() methods
        self.acquire = lock.acquire
        self.release = lock.release
        # If the lock defines _release_save() and/or _acquire_restore(),
        # these override the default implementations (which just call
        # release() and acquire() on the lock).  Ditto for _is_owned().
        try:
            self._release_save = lock._release_save
        except AttributeError:
            pass
        try:
            self._acquire_restore = lock._acquire_restore
        except AttributeError:
            pass
        try:
            self._is_owned = lock._is_owned
        except AttributeError:
            pass
        self._waiters = _deque()

    def _at_fork_reinit(self):
        self._lock._at_fork_reinit()
        self._waiters.clear()

    def __enter__(self):
        return self._lock.__enter__()

    def __exit__(self, *args):
        return self._lock.__exit__(*args)

    def __repr__(self):
        return "<Condition(%s, %d)>" % (self._lock, len(self._waiters))

    def _release_save(self):
        self._lock.release()  # No state to save

    def _acquire_restore(self, x):
        self._lock.acquire()  # Ignore saved state

    def _is_owned(self):
        """Return True if lock is owned by current_thread."""
        # This method is called only if _lock doesn't have _is_owned().
        if self._lock.acquire(False):
            self._lock.release()
            return False
        else:
            return True

    def wait(self, timeout=None):
        """Wait until notified or until a timeout occurs."""
        # If the calling thread has not acquired the lock when this method is
        # called, a RuntimeError is raised.
        # This method releases the underlying lock, and then blocks until it is
        # awakened by a notify() or notify_all() call for the same condition
        # variable in another thread, or until the optional timeout occurs. Once
        # awakened or timed out, it re-acquires the lock and returns.
        # When the timeout argument is present and not None, it should be a
        # floating point number specifying a timeout for the operation in seconds
        # (or fractions thereof).
        # When the underlying lock is an RLock, it is not released using its
        # release() method, since this may not actually unlock the lock when it
        # was acquired multiple times recursively. Instead, an internal interface
        # of the RLock class is used, which really unlocks it even when it has
        # been recursively acquired several times. Another internal interface is
        # then used to restore the recursion level when the lock is reacquired.
        if not self._is_owned():
            raise RuntimeError("cannot wait on un-acquired lock")
        waiter = _thread.allocate_lock()
        waiter.acquire()
        self._waiters.append(waiter)
        saved_state = self._release_save()
        gotit = False
        try:  # restore state no matter what (e.g., KeyboardInterrupt)
            if timeout is None:
                waiter.acquire()
                gotit = True
            else:
                if timeout > 0:
                    gotit = waiter.acquire(True, timeout)
                else:
                    gotit = waiter.acquire(False)
            return gotit
        finally:
            self._acquire_restore(saved_state)
            if not gotit:
                try:
                    self._waiters.remove(waiter)
                except ValueError:
                    pass

    def wait_for(self, predicate, timeout=None):
        """Wait until a condition evaluates to True."""
        # predicate should be a callable which result will be interpreted as a
        # boolean value.  A timeout may be provided giving the maximum time to
        # wait.
        endtime = None
        waittime = timeout
        result = predicate()
        while not result:
            if waittime is not None:
                if endtime is None:
                    endtime = ticks_ms() + int(waittime * 1000)
                else:
                    waittime = ticks_diff(endtime, ticks_ms())
                    if waittime <= 0:
                        break
            self.wait(waittime)
            result = predicate()
        return result

    def notify(self, n=1):
        """Wake up one or more threads waiting on this condition, if any."""
        # If the calling thread has not acquired the lock when this method is
        # called, a RuntimeError is raised.
        # This method wakes up at most n of the threads waiting for the condition
        # variable; it is a no-op if no threads are waiting.

        if not self._is_owned():
            raise RuntimeError("cannot notify on un-acquired lock")
        waiters = self._waiters
        while waiters and n > 0:
            waiter = waiters[0]
            try:
                waiter.release()
            except RuntimeError:
                # gh-92530: The previous call of notify() released the lock,
                # but was interrupted before removing it from the queue.
                # It can happen if a signal handler raises an exception,
                # like CTRL+C which raises KeyboardInterrupt.
                pass
            else:
                n -= 1
            try:
                waiters.remove(waiter)
            except ValueError:
                pass

    def notify_all(self):
        """Wake up all threads waiting on this condition."""
        # If the calling thread has not acquired the lock when this method
        # is called, a RuntimeError is raised.
        self.notify(len(self._waiters))


class Event:
    """Class implementing event objects."""

    # Events manage a flag that can be set to true with the set() method and reset
    # to false with the clear() method. The wait() method blocks until the flag is
    # true.  The flag is initially false.

    def __init__(self):
        self._cond = Condition(Lock())
        self._flag = False

    def _at_fork_reinit(self):
        # Private method called by Thread._reset_internal_locks()
        self._cond._at_fork_reinit()

    def is_set(self):
        """Return true if and only if the internal flag is true."""
        return self._flag

    def set(self):
        """Set the internal flag to true."""

        # All threads waiting for it to become true are awakened. Threads
        # that call wait() once the flag is true will not block at all.

        with self._cond:
            self._flag = True
            self._cond.notify_all()

    def clear(self):
        """Reset the internal flag to false."""

        # Subsequently, threads calling wait() will block until set() is called to
        # set the internal flag to true again.

        with self._cond:
            self._flag = False

    def wait(self, timeout=None):
        """Block until the internal flag is true."""

        # If the internal flag is true on entry, return immediately. Otherwise,
        # block until another thread calls set() to set the flag to true, or until
        # the optional timeout occurs.

        # When the timeout argument is present and not None, it should be a
        # floating point number specifying a timeout for the operation in seconds
        # (or fractions thereof).

        # This method returns the internal flag on exit, so it will always return
        # True except if a timeout is given and the operation times out.

        with self._cond:
            signaled = self._flag
            if not signaled:
                signaled = self._cond.wait(timeout)
            return signaled


class Semaphore:
    """This class implements semaphore objects."""

    # Semaphores manage a counter representing the number of release() calls minus
    # the number of acquire() calls, plus an initial value. The acquire() method
    # blocks if necessary until it can return without making the counter
    # negative. If not given, value defaults to 1.

    def __init__(self, value=1):
        if value < 0:
            raise ValueError("semaphore initial value must be >= 0")
        self._cond = Condition(Lock())
        self._value = value

    def acquire(self, blocking=True, timeout=None):
        """Acquire a semaphore, decrementing the internal counter by one."""

        # When invoked without arguments: if the internal counter is larger than
        # zero on entry, decrement it by one and return immediately. If it is zero
        # on entry, block, waiting until some other thread has called release() to
        # make it larger than zero. This is done with proper interlocking so that
        # if multiple acquire() calls are blocked, release() will wake exactly one
        # of them up. The implementation may pick one at random, so the order in
        # which blocked threads are awakened should not be relied on. There is no
        # return value in this case.

        # When invoked with blocking set to true, do the same thing as when called
        # without arguments, and return true.

        # When invoked with blocking set to false, do not block. If a call without
        # an argument would block, return false immediately; otherwise, do the
        # same thing as when called without arguments, and return true.

        # When invoked with a timeout other than None, it will block for at
        # most timeout seconds.  If acquire does not complete successfully in
        # that interval, return false.  Return true otherwise.

        if not blocking and timeout is not None:
            raise ValueError("can't specify timeout for non-blocking acquire")
        rc = False
        endtime = None
        with self._cond:
            while self._value == 0:
                if not blocking:
                    break
                if timeout is not None:
                    if endtime is None:
                        endtime = ticks_ms() + int(timeout * 1000)
                    else:
                        timeout = ticks_diff(endtime, ticks_ms())
                        if timeout <= 0:
                            break
                self._cond.wait(timeout)
            else:
                self._value -= 1
                rc = True
        return rc

    __enter__ = acquire

    def release(self, n=1):
        """Release a semaphore, incrementing the internal counter by one or more."""

        # When the counter is zero on entry and another thread is waiting for it
        # to become larger than zero again, wake up that thread.

        if n < 1:
            raise ValueError("n must be one or more")
        with self._cond:
            self._value += n
            for i in range(n):
                self._cond.notify()

    def __exit__(self, t, v, tb):
        self.release()
