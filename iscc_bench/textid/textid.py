# -*- coding: utf-8 -*-
from xxhash import xxh64_intdigest

from iscc_bench.algos.slide import sliding_window
from iscc_bench.textid.normalize import text_normalize
import numpy as np

R = np.random.RandomState(seed=74)
MASKS = R.randint(0, 2 ** 64 - 1, 64, dtype=np.uint64)

HEAD_CID_T = b"\x10"
HEAD_CID_T_PCF = b"\x11"

SYMBOLS = "C23456789rB1ZEFGTtYiAaVvMmHUPWXKDNbcdefghLjkSnopRqsJuQwxyz"
VALUES = "".join([chr(i) for i in range(58)])
C2VTABLE = str.maketrans(SYMBOLS, VALUES)
V2CTABLE = str.maketrans(VALUES, SYMBOLS)
WINDOW_SIZE_CID_T = 9

MINHASH_PERMUTATIONS = [
    [
        1465573649454982733,
        50671401556847464,
        464454191238539071,
        79121974684475339,
        1204172773865074508,
        1599360705907791122,
        1277912255369958294,
        160110214425958988,
        467753012659127075,
        1846500734868477684,
        337877366765600783,
        1910046430333214712,
        432991213508534293,
        458494058485982523,
        488627824275561651,
        838108366281102774,
        56421635900613245,
        41152469170208093,
        81795297597986189,
        1655634145464649340,
        625354851427597534,
        2204825841199416657,
        2234919984064510783,
        1013888525398624866,
        1955287890196929674,
        446634993784978105,
        754698625499853375,
        222042093077244875,
        871379034919191540,
        284785552184080815,
        543192509429361466,
        1161746297560325877,
        1960287370909864238,
        1846445530880870657,
        1469786218271285891,
        1448922133907529478,
        399602985777301894,
        2022057865440131188,
        1017153326444367824,
        606183561047677968,
        1598320042930326758,
        1116499924437966538,
        1125748350977128481,
        27225217426126585,
        384261112471101066,
        1033966260045922389,
        960201057416530170,
        251241047872847492,
        1271075573485035961,
        2163496639851351130,
        236290923696725726,
        1814667029972018154,
        470006580483358731,
        754988189928330202,
        1724648305364661516,
        436487060460267949,
        695653806960763463,
        2150760309693273629,
        924044207510448651,
        149809514353780767,
        1314612118644492866,
        1755300371282918056,
        518697226054308549,
        1569254193062057079,
    ],
    [
        1237857379018613025,
        1001921070941957488,
        656622217376943453,
        1238551308896951561,
        1331489939266224632,
        356372363153075238,
        502039359164234437,
        2244189427579536420,
        2261264705847976303,
        520021327101242735,
        2248861447464088572,
        1575238347461123506,
        1977164277640575068,
        443328659258048693,
        2164775033633161402,
        422864362428985564,
        1013886767037446358,
        2031519161666131866,
        960810283122122980,
        915146140710507812,
        1650364839972853328,
        417710596676127062,
        971941928151168238,
        112835823272522671,
        875463099753474542,
        2103760042641721929,
        1174817080219344992,
        956718707065671240,
        504714530717344612,
        698866224796044997,
        772686875752263236,
        508124985106117155,
        32050429651149070,
        2050193692902100504,
        113320117099579589,
        1157406858255878787,
        958938521872285562,
        1690655700081062480,
        654710156142217420,
        1374581228985750872,
        2293273111845819604,
        584158434721485467,
        1697469239658036408,
        1631417643814704636,
        759939753303206598,
        730557314242689590,
        514488987075693066,
        758386722945284999,
        205448532149163355,
        1955950223882840638,
        2178239790474234865,
        2150432790731678261,
        525986446085794211,
        243818715676446213,
        1448695519298583067,
        787612676545388580,
        1808140070502055045,
        1935597324863623502,
        990087375750577947,
        238222040856000242,
        902438855124964046,
        1573311567944127103,
        1685584091916149959,
        469424979690030816,
    ],
]


def content_id_text(text, partial=False):

    text = text_normalize(text)

    shingles = ("".join(s) for s in sliding_window(text, WINDOW_SIZE_CID_T, 1))

    # 5. Create 32-bit features with xxHash32
    features = [xxh64_intdigest(s.encode("utf8")) for s in shingles]

    # 6. Apply minimum_hash

    minhash = minimum_hash(features)

    # # 7. Collect least significant bits
    lsb = "".join([str(x & 1) for x in minhash])

    # 8. Create two 64-bit digests
    digest = int(lsb, 2).to_bytes(8, "big", signed=False)

    if partial:
        content_id_text_digest = HEAD_CID_T_PCF + digest
    else:
        content_id_text_digest = HEAD_CID_T + digest

    # 11. Encode and return
    return encode(content_id_text_digest)


def minimum_hash(features):

    hashes = np.empty(64, dtype=np.uint64)
    hashes.fill(2 ** 64 - 1)

    for f in features:
        hashes = np.minimum(hashes, np.bitwise_xor(MASKS, f))
    return hashes.tolist()


def minimum_hash_text(text, w=13):
    chunks = ("".join(c) for c in sliding_window(text, w))
    features = (xxh64_intdigest(s.encode("utf8")) for s in chunks)
    hashes = np.empty(64, dtype=np.uint64)
    hashes.fill(2 ** 64 - 1)

    for f in features:
        hashes = np.minimum(hashes, np.bitwise_xor(MASKS, f))
    return hashes.tolist()


def similarity_hash(hash_digests):

    n_bytes = 8
    n_bits = 64
    vector = [0] * n_bits

    for h in hash_digests:

        for i in range(n_bits):
            vector[i] += h & 1
            h >>= 1

    minfeatures = len(hash_digests) * 1.0 / 2
    shash = 0

    for i in range(n_bits):
        shash |= int(vector[i] >= minfeatures) << i

    return shash.to_bytes(n_bytes, "big", signed=False)


def encode(digest):

    if len(digest) == 9:
        return encode(digest[:1]) + encode(digest[1:])
    assert len(digest) in (1, 8), "Digest must be 1, 8 or 9 bytes long"
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
    return str.translate("".join([chr(c) for c in reversed(chars)]), V2CTABLE)


if __name__ == "__main__":
    print(content_id_text("Hello World"))
