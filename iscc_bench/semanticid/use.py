# -*- coding: utf-8 -*-
"""Test universal sentence encoding for Semantic-ID text."""
from pprint import pprint

from loguru import logger as log
from syntok import segmenter
import tensorflow as tf
import tensorflow_hub as hub
import numpy as np
import tf_sentencepiece

from iscc_bench.readers.gutenberg import gutenberg
from langdetect import detect

embed = hub.load(
    "https://tfhub.dev/google/universal-sentence-encoder-multilingual-large/3"
)


def sentencize(text):
    """Sentence segementation"""
    sentences = []
    for para in segmenter.analyze(text):
        for sent in para:
            s = []
            for tok in sent:
                s.extend([tok.spacing, tok.value])
            sentences.append("".join(s))
    return sentences


def demo():
    # Graph set up.
    g = tf.Graph()
    with g.as_default():
        text_input = tf.placeholder(dtype=tf.string, shape=[None])
        embed = hub.Module(
            "https://tfhub.dev/google/universal-sentence-encoder-multilingual/1"
        )
        embedded_text = embed(text_input)
        init_op = tf.group([tf.global_variables_initializer(), tf.tables_initializer()])
    g.finalize()

    # Initialize session.
    session = tf.Session(graph=g)
    session.run(init_op)

    for fp in gutenberg():
        log.info(fp)
        doc = open(fp, "rt", encoding="UTF-8").read()
        lng = detect(doc)
        log.info(f"{lng}: {doc.strip()[:100]}")
        sentences = sentencize(doc)
        vec = session.run(embedded_text, feed_dict={text_input: sentences})
        print(vec)


if __name__ == "__main__":
    demo()
