#!/usr/bin/env python3
# Based on https://github.com/OpenIPC/website/blob/master/app/models/firmware.rb
import argparse
import tarfile
import tempfile
import requests

def main():
    parser = argparse.ArgumentParser('firmware_builder')
    parser.add_argument('TAR', help='Firmware tar file')
    parser.add_argument('SIZE', type=int, help='Size of the flash image in MB')

    args = parser.parse_args()

    # Source tar file
    source = tarfile.open(args.TAR)

    # Identify the files needed
    for fl in source.getmembers():
        if 'md5sum' in fl.name:
            continue
        if fl.name.startswith('uImage'):
            kernel = fl
            soc = kernel.name.split('.')[1]
            print('SOC: {0}'.format(soc))
            print('Kernel: {0}'.format(kernel.name))
        elif fl.name.startswith('rootfs.squashfs'):
            rootfs = fl
            print('Rootfs: {0}'.format(rootfs.name))

    # Get u-boot from OpenIPC
    url = "https://github.com/OpenIPC/firmware/releases/download/latest/u-boot-{0}-nor.bin".format(soc)
    print('U-boot: {0}'.format(url))
    resp = requests.get(url)
    if not resp.ok:
        print('Error grabbing {0}'.format(url))
        return
    uboot = tempfile.TemporaryFile()
    uboot.write(resp.content)
    uboot.seek(0)

    # Prep file
    output_filename = '{0}-{1}mb.bin'.format(soc, args.SIZE)
    dest = open(output_filename, 'wb')
    dest.write(b"\xff" * (args.SIZE * (1024 ** 2)))
    dest.seek(0)

    # Write u-boot
    dest.write(uboot.read())

    # Write kernel
    dest.seek(0x50000)
    dest.write(source.extractfile(kernel).read())

    # Write rootfs
    if args.SIZE == 8 or soc.startswith('ssc'):
        rootfs_offset = 0x250000
    elif args.SIZE == 16:
        rootfs_offset = 0x350000
    elif args.SIZE == 32:
        rootfs_offset = 0x350000
    print('Rootfs Offset: {0}'.format(rootfs_offset))

    dest.seek(rootfs_offset)
    dest.write(source.extractfile(rootfs).read())

    dest.close()

    print('Bin Wrote: {0}'.format(output_filename))

if __name__ == '__main__':
    main()