import os
import tarfile
import shutil
import urllib.request

from django.core.management.base import BaseCommand
from django.conf import settings


class Command(BaseCommand):

    help = 'update geo db files'

    def handle(self, *args, **options):
        path = settings.GEOIP_PATH
        os.chdir(path)

        urllib.request.urlretrieve('http://geolite.maxmind.com/download/geoip/database/GeoLite2-City.tar.gz',
            'GeoLite2-City.tar.gz')
        urllib.request.urlretrieve('http://geolite.maxmind.com/download/geoip/database/GeoLite2-Country.tar.gz',
            'GeoLite2-Country.tar.gz')

        os.remove('GeoLite2-City.mmdb')
        os.remove('GeoLite2-Country.mmdb')

        tar_names = ('GeoLite2-City.tar.gz', 'GeoLite2-Country.tar.gz')
        for name in tar_names:
            tar = tarfile.open(name, "r:gz")
            for member in tar.getmembers():
                arch_path = ''
                if name.split('.')[0] in member.name and 'mmdb' in member.name:
                    arch_path = member.name
                    print(arch_path)
                    tar.extractall()
                    shutil.copy(arch_path, path)
                    shutil.rmtree(member.name.split('/')[0])

        tar.close()
        os.remove('GeoLite2-City.tar.gz')
        os.remove('GeoLite2-Country.tar.gz')
