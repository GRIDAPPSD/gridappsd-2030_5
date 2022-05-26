"""
Provides a key/value store interface for setting retrieving points from a datastore.

This implementation just uses pickledb for loading a json datastore.  After
each set the data will be written to disk.
"""
import atexit

import pickledb

db = pickledb.load("db.data.db", True)


def set_point(key, value):
    """
    Set a point into the key/value store.  Both key and value must be hashable types.

    Example:
        set_point("_e55a4c7a-c006-4596-b658-e23bc771b5cb.angle", -156.38295096513662)
        set_point("known_mrids": ["_4da919f1-762f-4755-b674-5faccf3faec6"])
    """
    db.set(key, value)


def get_point(key):
    """
    Retrieve a point from the key/value store.  If the key doesn't exist returns None.
    """
    return db.get(key)


def get_points():
    return db.getall()


atexit.register(db.dump)


if __name__ == '__main__':

    set_point("foo", "bar")
    set_point("bim", "baf")
    # print(get_point("foo"))
    get_points()
