# -*- coding: utf-8 -*-
import random

from PIL import Image, ImageEnhance, ImageDraw
import os

from PIL import ImageFilter
from iscc_bench import DATA_DIR

IMAGE_SRC_DIR = os.path.join(DATA_DIR, 'images')


def prepare_images():
    for key, image in enumerate(os.listdir(IMAGE_SRC_DIR)):
        name_parts = image.split('.')
        type = name_parts[len(name_parts) - 1]
        src_path = os.path.join(IMAGE_SRC_DIR, image)
        dst_path = os.path.join(IMAGE_SRC_DIR, '%s.%s' % (key, type))
        while os.path.exists(dst_path) and not dst_path == src_path:
            key += 1
            dst_path = os.path.join(IMAGE_SRC_DIR, '%s.%s' % (key, type))
        os.rename(src_path, os.path.join(IMAGE_SRC_DIR, '%s.%s' % (key, type)))


def delete_test_images():
    for name in os.listdir(IMAGE_SRC_DIR):
        if '_' in name:
            os.remove(os.path.join(IMAGE_SRC_DIR, name))


def generate_test_images():
    for name in os.listdir(IMAGE_SRC_DIR):
        image = Image.open(os.path.join(IMAGE_SRC_DIR, name))
        name_parts = name.split('.')

        # brightness
        enhancer = ImageEnhance.Brightness(image)
        bright_image = enhancer.enhance(random.uniform(1.05, 1.2))
        dark_image = enhancer.enhance(random.uniform(0.8, 0.95))
        bright_image.save(os.path.join(IMAGE_SRC_DIR, '%s_bright.%s' % (name_parts[0], name_parts[1])), "PNG")
        dark_image.save(os.path.join(IMAGE_SRC_DIR, '%s_dark.%s' % (name_parts[0], name_parts[1])), "PNG")

        # contrast
        enhancer = ImageEnhance.Contrast(image)
        highContrast_image = enhancer.enhance(random.uniform(1.05, 1.2))
        lowContrast_image = enhancer.enhance(random.uniform(0.8, 0.95))
        highContrast_image.save(os.path.join(IMAGE_SRC_DIR, '%s_highContrast.%s' % (name_parts[0], name_parts[1])),
                                "PNG")
        lowContrast_image.save(os.path.join(IMAGE_SRC_DIR, '%s_lowContrast.%s' % (name_parts[0], name_parts[1])), "PNG")
        del enhancer

        # watermarks
        cross_image = image.copy()
        draw = ImageDraw.Draw(cross_image)
        draw.line((0, 0) + cross_image.size, fill=128)
        draw.line((0, cross_image.size[1], cross_image.size[0], 0), fill=128)
        cross_image.save(os.path.join(IMAGE_SRC_DIR, '%s_cross.%s' % (name_parts[0], name_parts[1])), "PNG")
        del draw

        # greyscale
        grey_image = image.convert('L')
        grey_image.save(os.path.join(IMAGE_SRC_DIR, '%s_grey.%s' % (name_parts[0], name_parts[1])), "PNG")

        # scaling
        scale = random.uniform(1.5, 3)
        size = int(image.size[0] / scale), int(image.size[1] / scale)
        scaled_image = image.copy()
        scaled_image.thumbnail(size)
        scaled_image.save(os.path.join(IMAGE_SRC_DIR, '%s_scaled.%s' % (name_parts[0], name_parts[1])), "PNG")

        # crop
        crop_image = image.crop((int(image.size[0] * random.uniform(0.01, 0.05)),
                                 int(image.size[1] * random.uniform(0.01, 0.05)),
                                 int(image.size[0] * random.uniform(0.95, 0.99)),
                                 int(image.size[1] * random.uniform(0.95, 0.99))))
        crop_image.save(os.path.join(IMAGE_SRC_DIR, '%s_cropped.%s' % (name_parts[0], name_parts[1])), "PNG")

        # gauss
        gauss_image = image.filter(ImageFilter.GaussianBlur(1))
        gauss_image.save(os.path.join(IMAGE_SRC_DIR, '%s_gauss.%s' % (name_parts[0], name_parts[1])), "PNG")

        if name_parts[1] == 'jpg':
            # jpeg compression
            image.save(os.path.join(IMAGE_SRC_DIR, '%s_compressed.%s' % (name_parts[0], name_parts[1])), "JPEG",
                       quality=random.randint(80, 95))


if __name__ == '__main__':
    delete_test_images()
    prepare_images()
    generate_test_images()
