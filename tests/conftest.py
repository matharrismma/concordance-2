"""Test-wide guards.

The tortoise (find.py) reaches the open web only in production. Tests must NEVER touch the network,
so web-find is disabled here by default. test_find re-enables it per-test with STUBBED providers
(never real HTTP) and restores this default afterward.
"""
import os

os.environ["WEB_FIND_DISABLED"] = "1"
