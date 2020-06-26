# -*- coding: utf-8 -*-
import os
import platform
import iscc
import cpuinfo
from codetiming import Timer
from tqdm import tqdm
from humanize import naturalsize as nsize


def system_info():
    """Printable system info"""
    cinfo = cpuinfo.get_cpu_info()
    sinfo = (
        "ISCC Performance Benchmark\n"
        "==========================================================================\n"
        "CPU:    {}\n"
        "Cores:  {}\n"
        "OS:     {}\n"
        "Python: {} - {} - {}\n"
        "ISCC:   {}\n"
        "==========================================================================\n"
    ).format(
        cinfo.get("brand_raw"),
        cinfo.get("count"),
        platform.platform(),
        platform.python_implementation(),
        platform.python_version(),
        platform.python_compiler(),
        iscc.__version__,
    )
    return sinfo


def benchmark(func, files, timer_name=None):
    total_bytes = 0
    timer_name = timer_name or func.__name__
    print("Benchmarking {} with {} files:\n".format(timer_name, len(files)))
    t = Timer(timer_name, logger=None)
    t.start()
    for fp in tqdm(files, ncols=74):
        fs = os.path.getsize(fp)
        total_bytes += fs
        func(fp)
    t.stop()
    print("\nProcessed: {}".format(nsize(total_bytes)))
    data_per_s = total_bytes / Timer.timers.mean(timer_name)
    print("{}: {}/s".format(timer_name, nsize(data_per_s)))
    print("=" * 74)


def list_files(path):
    """List absolute path to files in directory"""
    path = os.path.abspath(path)
    return [entry.path for entry in os.scandir(path) if entry.is_file()]


if __name__ == "__main__":
    print(system_info())
