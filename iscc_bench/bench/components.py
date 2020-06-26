# -*- coding: utf-8 -*-
"""Performance Benchmarking of core components of reference implementation"""
import iscc
from iscc_bench.bench.utils import benchmark, system_info
from iscc_bench.readers import caltech_256, web_video
from iscc_cli.video_id import get_frame_vectors, content_id_video


def vid(file):
    try:
        features = get_frame_vectors(file)
        cidv = content_id_video(features)
    except Exception:
        return None
    return cidv


def benchmark_components():
    print(system_info())
    image_files = list(caltech_256())
    video_files = list(web_video.seed_videos())
    benchmark(iscc.instance_id, image_files)
    benchmark(iscc.data_id, image_files)
    benchmark(iscc.content_id_image, image_files)
    benchmark(vid, video_files, "content_id_video")


if __name__ == "__main__":
    benchmark_components()
