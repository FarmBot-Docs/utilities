#!/usr/bin/env python3

'''Check image files in documentation.'''

import os
import json
from collections import Counter
import imagesize
from util.walk import is_content_dir, get_relative_filename
from util.versions import HUBS
from util.summary import color


class ImageFileChecker():
    'Check image files in documentation. (default directory: current)'

    def __init__(self, summary, folder=None):
        self.summary = summary
        self.verbose = False
        self.folder = folder or '.'
        self.current_hub = None
        self.current_hub_path = None
        self.summary_string = ''
        self.options = {'extras': False, 'top_count': 3}

    def add_line(self, text='', indent=2):
        'add line to summary string'
        self.summary_string += f'{" " * indent}{text}\n'

    def print_title(self, text):
        'print title'
        self.add_line()
        self.add_line(f'{text}')
        self.add_line(f'{"-" * 10}')

    def over(self, total_count, average_size, size):
        'print amount over specified size'
        total = total_count * size
        surplus = total_count * (average_size - size)
        total_string = f'{total:.2f} MB total ({surplus:.2f} MB less)'
        self.add_line(f'{size:10.2f} MB avg: {total_string}')

    def above(self, image_file_sizes, size):
        'print image count above size'
        count = len([img for img in image_file_sizes if img[0] > size])
        self.add_line(f'{count:10}    images > {size} MB')

    def check_all(self, hubs=None):
        'check image files in all hubs'
        if hubs is None:
            hubs = HUBS
        results_filepath = get_relative_filename('results/links_results.json')
        with open(results_filepath, 'r') as results_f:
            all_links = json.load(results_f)

        for hub in hubs:
            self.summary_string = ''
            self.add_line(' image file summary '.upper().center(50, '-'), 0)
            hub_dir = os.path.join(self.folder, f'farmbot-{hub}')

            used_image_paths = [link['to_absolute']
                                for link in all_links[hub]
                                if link['to_absolute'] is not None
                                and not link['to_absolute'].endswith('.md')]

            all_files = []
            version_count = 0
            for folder in os.listdir(hub_dir):
                if is_content_dir(folder):
                    version_count += 1
                    for root, _dirs, files in os.walk(os.path.join(hub_dir, folder)):
                        for filename in files:
                            filepath = os.path.join(root, filename)
                            all_files.append(filepath)

            image_file_paths = [os.sep.join(path.split('/')[2:])
                                for path in all_files if not path.endswith('.md')]

            image_file_sizes = []
            for path in image_file_paths:
                size = os.path.getsize(os.path.join(hub_dir, path)) / 1000000
                image_file_sizes.append([size, path])

            image_pixel_sizes = []
            for path in image_file_paths:
                width, height = imagesize.get(os.path.join(hub_dir, path))
                image_pixel_sizes.append(
                    [width * height / 1000000, width, height, path])

            self.print_title('Statistics')
            md_file_count = len([p for p in all_files if p.endswith('.md')])
            self.add_line(f'{version_count:10}    versions')
            self.add_line(f'{md_file_count:10}    markdown files')
            total_count = len(image_file_sizes)
            total_size = sum([img[0] for img in image_file_sizes])
            self.add_line(f'{total_count:10}    images')
            for megabytes in [4, 2, 1, 0.5]:
                self.above(image_file_sizes, megabytes)
            self.add_line(f'{total_size:10.2f} MB total size')
            average_size = total_size / (total_count or 1)
            self.add_line(f'{average_size:10.2f} MB average size')

            if self.options['extras']:
                self.print_title('Potential sizes')
                for megabytes in [0.25, 0.5]:
                    self.over(total_count, average_size, megabytes)
                self.add_line()

            top_count = self.options['top_count']

            if self.options['extras']:
                self.print_title('Most referenced images')
                for item in Counter(used_image_paths).most_common()[:top_count]:
                    self.add_line('{} {}'.format(*item[::-1]))

            self.print_title('Largest images by file size')
            for item in sorted(image_file_sizes)[::-1][:top_count]:
                self.add_line('{:6.2f} MB {}'.format(*item))

            self.print_title('Largest images by pixel count')
            for item in sorted(image_pixel_sizes)[::-1][:top_count]:
                self.add_line('{:6.2f} MP {:5} x {:5} {}'.format(*item))

            unused = set(image_file_paths) - set(used_image_paths)
            missing = set(used_image_paths) - set(image_file_paths)

            if len(unused) > 0 or len(missing) > 0:
                self.add_line()
                broken_image_title = ' problem images '.upper().center(50, '-')
                self.add_line(color(broken_image_title, 'bold'), 0)

                self.print_title('Unused images')
                for path in unused:
                    self.add_line(color(path))

                self.print_title('Missing images')
                for path in missing:
                    self.add_line(color(path))

            self.summary.extra_summaries[hub] = self.summary_string
            if len(unused) > 0 or len(missing) > 0:
                pass
                # self.summary.exit_code = 1
