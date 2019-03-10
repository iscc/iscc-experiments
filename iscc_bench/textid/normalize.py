# -*- coding: utf-8 -*-
"""Text normalization"""
import unicodedata


def is_cc(char):
    """Checks whether `chars` is a control character."""
    # These are  control characters but we count them as whitespace.
    if char == "\t" or char == "\n" or char == "\r":
        return False
    cat = unicodedata.category(char)
    if cat.startswith("C"):
        return True
    return False


def is_ws(char):
    """Checks whether `char` is a whitespace character."""
    # \t, \n, and \r are control characters but we treat them as whitespace.
    if char == " " or char == "\t" or char == "\n" or char == "\r":
        return True
    cat = unicodedata.category(char)
    if cat == "Zs":
        return True
    return False


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    chars = []
    for char in text:
        cp = ord(char)
        cat = unicodedata.category(char)
        # skip control chars
        if cp == 0 or cp == 0xfffd or is_cc(char) or is_ws(char) or cat == "Mn":
            continue
        chars.append(char.lower())
    return "".join(chars)

