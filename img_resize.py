import os
import sys
import glob
import logging
import argparse

from PIL import Image


def argparser():
    parser = argparse.ArgumentParser(description='interactive graph cut for moth image')
    parser.add_argument('-i', '--image', help='process input image',
        nargs='+', default=[])
    parser.add_argument('-r', '--recursive', help='process all image in given directory',
        nargs='+', default=[])
    parser.add_argument('--height', help='the height of resized image',
        type=int, default=240)
    parser.add_argument('--width', help='the width of resized image',
        type=int, default=320)
    return parser

def main(args):
    imgs = []
    saved_path = '{}x{}'.format(args.width, args.height)
    flatten = lambda l: [item for sublist in l for item in sublist]

    if args.image or args.recursive:
        if args.image: imgs += [os.path.abspath(img) for img in args.image]
        if args.recursive:
            for repo in args.recursive:
                ext = ['jpg', 'jpeg', 'png']
                repo = [os.path.abspath(repo) + '/**/*.' + e for e in ext]
                repo = [glob.glob(r, recursive=True) for r in repo]
                repo = flatten(repo)
                imgs += repo

    for i, img in enumerate(imgs):
        saved_dir = os.path.join('/'.join(img.split('/')[:-1]), saved_path)
        saved_img_path = os.path.join(saved_dir, img.split('/')[-1])

        if not os.path.exists(saved_dir):
            os.makedirs(saved_dir)

        im = Image.open(img)
        im = im.resize((args.width, args.height), Image.BILINEAR)
        im.save(saved_img_path)
        logging.info('({}/{}) Saved {} with size ({})'.format(
            i+1, len(imgs), img.split('/')[-1], im.size))


if __name__ == '__main__':

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [ %(levelname)8s ] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        stream=sys.stdout
        )

    parser = argparser()
    main(parser.parse_args())
