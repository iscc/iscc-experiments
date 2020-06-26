# -*- coding: utf-8 -*-
"""
Show output for various standard base encodings

Notes:
    base64:
        - good: 12 chars per component, 48 chars for combined encoding
        - bad:  has some non-alphanumeric characters
        - bad:  is case sensitive (problem for some file systems and qr-codes)
    base32:
        - bad:  15 chars per component, 58 chars for combined encoding, (60 concat)
"""
import os
import base64


def main():
    for x in range(100):
        digest = os.urandom(9)
        code = base64.urlsafe_b64encode(digest).rstrip(b"=")
        print('b64c', len(code), code)
        code = base64.b32encode(digest).rstrip(b"=")
        print('b32c', len(code), code)
        fcd = b''.join(os.urandom(9) for _ in range(4))
        fcode = base64.urlsafe_b64encode(fcd).rstrip(b"=")
        print('b64f', len(fcode), fcode)
        fcode = base64.b32encode(fcd).rstrip(b"=")
        print('b32f', len(fcode), fcode)


if __name__ == '__main__':
    main()
