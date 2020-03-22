# -*- coding: utf-8 -*-
import math
import textwrap
import iscc
from iscc import const


# Short-Code Private Use
HEAD_SID_PU = 0b01000000 .to_bytes(1, "big")
# Short-Code Content Blockchain
HEAD_SID_CB = 0b01000001 .to_bytes(1, "big")


ISCC_COMPONENT_TYPES = {
    const.HEAD_MID: {"name": "Meta-ID", "code": "CC"},
    const.HEAD_CID_T: {"name": "Content-ID Text", "code": "CT"},
    const.HEAD_CID_T_PCF: {"name": "Content-ID Text", "code": "Ct"},
    const.HEAD_CID_I: {"name": "Content-ID Image", "code": "CY"},
    const.HEAD_CID_I_PCF: {"name": "Content-ID Image", "code": "Ci"},
    const.HEAD_CID_A: {"name": "Content-ID Audio", "code": "CA"},
    const.HEAD_CID_A_PCF: {"name": "Content-ID Audio", "code": "Ca"},
    const.HEAD_CID_V: {"name": "Content-ID Video", "code": "CV"},
    const.HEAD_CID_V_PCF: {"name": "Content-ID Video", "code": "Cv"},
    const.HEAD_CID_M: {"name": "Content-ID Mixed", "code": "CM"},
    const.HEAD_CID_M_PCF: {"name": "Content-ID Mixed", "code": "Cm"},
    const.HEAD_DID: {"name": "Data-ID", "code": "CD"},
    const.HEAD_IID: {"name": "Instance-ID", "code": "CR"},
    HEAD_SID_PU: {"name": "Short-Code Private Use", "code": "27"},
    HEAD_SID_CB: {"name": "Short-Code Content Blockchain", "code": "28"},
}


ISCC_COMPONENT_CODES = {
    value["code"]: {"name": value["name"], "marker": key}
    for key, value in ISCC_COMPONENT_TYPES.items()
}


def iscc_clean(i):
    """Remove leading scheme and dashes"""
    return i.split(":")[-1].strip().replace("-", "")


def iscc_verify(i):
    i = iscc_clean(i)
    for c in i:
        if c not in iscc.SYMBOLS:
            raise ValueError('Illegal character "{}" in ISCC Code'.format(c))
    for component_code in iscc_split(i):
        iscc_verify_component(component_code)


def iscc_verify_component(component_code):

    if not len(component_code) == 13:
        raise ValueError(
            "Illegal component length {} for {}".format(
                len(component_code), component_code
            )
        )

    header_code = component_code[:2]
    if header_code not in ISCC_COMPONENT_CODES.keys():
        raise ValueError("Illegal component header {}".format(header_code))


def iscc_split(i):
    return textwrap.wrap(iscc_clean(i), 13)


def iscc_decode(code):
    return b"".join(iscc.decode(c) for c in iscc_split(code))


def b58i_encode(digest):
    digest = reversed(digest)
    value = 0
    numvalues = 1
    for octet in digest:
        octet *= numvalues
        value += octet
        numvalues *= 256
    chars = []
    while numvalues > 0:
        chars.append(value % 58)
        value //= 58
        numvalues //= 58
    return str.translate("".join([chr(c) for c in reversed(chars)]), iscc.V2CTABLE)


def b58i_decode(code):
    bit_length = math.floor(math.log(58 ** len(code), 256)) * 8
    code = reversed(str.translate(code, iscc.C2VTABLE))
    value = 0
    numvalues = 1
    for c in code:
        c = ord(c)
        c *= numvalues
        value += c
        numvalues *= 58
    numvalues = 2 ** bit_length
    data = []
    while numvalues > 1:
        data.append(value % 256)
        value //= 256
        numvalues //= 256
    return bytes(reversed(data))
