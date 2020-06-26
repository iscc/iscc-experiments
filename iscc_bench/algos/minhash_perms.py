# -*- coding: utf-8 -*-
"""Find a good set of random permutations for minhash

Top Seeds Ref:
(96, 0.15205639204635668),
(73, 0.15229689259262588),
(9, 0.15315327588351788),
(61, 0.15377402833479373),
(81, 0.15381738009803106),
(58, 0.15389816815111984),

Top Seeds XOR:
(28, 0.15043602516368526),
(18, 0.15095065712594843),
(62, 0.15147909780114388),
(47, 0.15180138707722712),
(98, 0.15180438596694779),
(3, 0.15199068753973843),

Top Seeds Ref 64/256:
(69, (0.01306824854824915, 0.010476447089936948)),
(98, (0.013122977555621198, 0.009925452387907341)),
(31, (0.01339718530271762, 0.009716144886184821)),
(19, (0.013460961594560061, 0.009398987421376195)),
(84, (0.013546444240384486, 0.01045235463226382)),
(3, (0.01356503403919503, 0.009955851968776817)),
"""
import operator
from itertools import chain
from pprint import pprint
from statistics import mean
import numpy as np
from numba import njit
from xxhash.cpython import xxh32_intdigest
from iscc_bench.algos.metrics import jaccard
from iscc_bench.algos.minhash import minhash_xor_numba
from iscc_bench.algos.slide import sliding_window
from iscc_bench.readers.gutenberg import gutenberg
from iscc_bench.readers.mltext import mltext
from iscc_bench.textid.normalize import text_normalize
from iscc_bench.utils import load_text_file

# Random Permutations (Seed 96)
PERMS_A = [
    3960274120300065754,
    16777357385564948844,
    15075331859002466913,
    16673651701421934658,
    13039621000660356413,
    2178121520072581510,
    1704494190441614153,
    10366590618702216578,
    10540690208148703356,
    718629239043485146,
    6023737476818450877,
    5364648567369485443,
    9418228297839158893,
    5604984416321436519,
    5603087484815973274,
    2641060255717410420,
    670170731985121560,
    7364592190673572541,
    13776803823856308556,
    15771371186332180221,
    12076722878157988073,
    17824905107673409791,
    11873345038598581774,
    13729305973750866106,
    15347738751135559959,
    109906670781626837,
    9838712542825460629,
    16986270503861230036,
    3380990636684525687,
    18205980549406025194,
    8662445176514852549,
    10261138128756980964,
    4632530969219240399,
    8045773355498290610,
    15221166430826819640,
    11750345127091753390,
    15181792116876784903,
    5227182645665674789,
    8314488401447395128,
    3225454105350242276,
    830029702368232549,
    12287789882098825497,
    6020782672580988122,
    4779985924203962237,
    13794485673875659359,
    12835855926005187757,
    17817115533364032536,
    6177885715123756057,
    16405314285497713063,
    7890879897229023938,
    17204772319528407852,
    14175216710732288317,
    3986241735470471991,
    15874657355013622660,
    15810865688125417570,
    18439338102023024029,
    5564719411781274251,
    5108268120626580115,
    6256103298827578569,
    4133604877823693623,
    5628363535249287656,
    13160369141729060922,
    11557169437079305020,
    4505949230224805708,
]

PERMS_B = [
    3565013898071686233,
    18265572134685450248,
    6789754060089385484,
    3339725282278369024,
    4646463204812244361,
    15564031373223359638,
    7926486177255669672,
    13633602406734010860,
    2634234526947988721,
    13981994416502860207,
    15023277397027985967,
    5707700682291358480,
    818020962799819849,
    458586138823984145,
    6549567868065955675,
    16823045317546172365,
    2052218297079612313,
    13883548810637282504,
    12352387620591042296,
    10141623849284770787,
    4486610756227327694,
    4810760588532849129,
    17499802171023290369,
    1314783561755986590,
    4888852460780292146,
    1909064185724040260,
    6116214891091104228,
    6699830646832556054,
    4889102023244481489,
    16074700581471948368,
    15313523036917039188,
    18068991201828449705,
    10077794139845035996,
    10150072837260913061,
    2083632199764551339,
    12982250953149043419,
    15893469775497294277,
    456474986983203272,
    17220716034001852476,
    15368018699821458993,
    7107899200757404734,
    4465592077607041777,
    7326983261081703939,
    2416869210798304472,
    17792956681618431896,
    3608397142932379760,
    3871382493706847444,
    12725817574229443009,
    8223639129128721258,
    7430992545390912236,
    10888974431582514296,
    1064455547552874264,
    5059397173812251537,
    4811203520858039876,
    7452367341718315367,
    14102052425075113620,
    7448455396102028164,
    6610188449822798882,
    7097027043779001525,
    2072099569549763767,
    13514831191020536233,
    18112851787996508509,
    12181872597917687579,
    5875845716493427251,
]

MAX_UINT64 = (1 << 64) - 1


def get_perms(seed=1):
    mprime = (1 << 61) - 1
    rand = np.random.RandomState(seed=seed)
    perms = np.array(
        [
            (
                rand.randint(1, mprime, dtype=np.uint64),
                rand.randint(0, mprime, dtype=np.uint64),
            )
            for _ in range(256)
        ],
        dtype=np.uint64,
    ).T
    perms[0] = np.bitwise_or(perms[0], 1)
    return perms


def get_perms_xor(seed=1):
    rand = np.random.RandomState(seed=seed)
    perms = rand.randint(0, MAX_UINT64, 64, dtype=np.uint64)
    return perms


@njit
def minhash_ref_numba(features_32, perms):
    _mersenne_prime = np.uint64((1 << 61) - 1)
    _max_hash = np.uint32((1 << 32) - 1)

    hashvalues = np.full(256, _max_hash, dtype=np.uint64)

    a = perms[0]
    b = perms[1]
    for hv in features_32:
        phv = np.bitwise_and((a * hv + b) % _mersenne_prime, np.uint64(_max_hash))
        hashvalues = np.minimum(phv, hashvalues)
    return hashvalues


def get_minhash(features, a, b):
    mhashes = minhash_ref_numba(features, a, b)
    h = [(i, x & 1) for i, x in enumerate(mhashes.tolist())]
    return h


def get_minhash_xor(features, perms):
    mhashes = minhash_xor_numba(features, perms)
    h = [(i, x & 1) for i, x in enumerate(mhashes.tolist())]
    return h


def ngrams(text):
    return ("".join(c) for c in sliding_window(text, 13))


def features(ngrams):
    return np.array([xxh32_intdigest(f) for f in ngrams], np.uint32)


def find_perms():
    print("Searching for best permutations")
    fps = list(chain(mltext(), gutenberg()))
    results = {}
    for seed in range(100):
        errs64 = []
        errs256 = []
        perms = get_perms(seed)
        for ab in sliding_window(fps, 2, 2, fillvalue=None):
            ab = list(ab)
            if ab[-1] is None:
                continue
            texts = (load_text_file(t) for t in ab)
            norm_texts = (text_normalize(t) for t in texts)
            ngrams_texts = (ngrams(t) for t in norm_texts)
            feature_texts = [features(f) for f in ngrams_texts]
            sim = jaccard(feature_texts[0], feature_texts[1])
            mhash_sigs = [minhash_ref_numba(f, perms) for f in feature_texts]
            sim_sig_64 = jaccard(mhash_sigs[0][:64], mhash_sigs[1][:64])
            sim_sig_256 = jaccard(mhash_sigs[0], mhash_sigs[1])
            sim_sig_64_err = abs(sim - sim_sig_64)
            sim_sig_256_err = abs(sim - sim_sig_256)
            mhash_hashes = [
                [(i, x & 1) for i, x in enumerate(ms.tolist())] for ms in mhash_sigs
            ]
            sim_mh_64 = jaccard(mhash_hashes[0][:64], mhash_hashes[1][:64])
            sim_mh_256 = jaccard(mhash_hashes[0], mhash_hashes[1])
            sim_mh_64_err = abs(sim - sim_mh_64)
            sim_mh_256_err = abs(sim - sim_mh_256)
            print(
                f"Errors: Mh64 {sim_mh_64_err}, Mh256 {sim_mh_256_err}, Sig64 {sim_sig_64_err}, Sig256 {sim_sig_256_err}"
            )
            errs64.append(sim_mh_64_err)
            errs256.append(sim_mh_256_err)
        results[seed] = (mean(errs64), mean(errs256))
        pprint(sorted(results.items(), key=operator.itemgetter(1)))
    sresults = sorted(results.items(), key=operator.itemgetter(1))
    pprint(sresults)


def reference_perms():
    MAX_UINT64 = (1 << 64) - 1
    rand = np.random.RandomState(seed=96)
    perms = rand.randint(0, MAX_UINT64, 128, dtype=np.uint64)
    a, b = perms[:64], perms[64:]
    a = a + rand.randint(0, MAX_UINT64, 128, dtype=np.uint64)
    return perms[:64], perms[64:]


if __name__ == "__main__":
    # find_perms()
    perms = get_perms(69)
    print(perms)
    print([*zip(*perms)])
