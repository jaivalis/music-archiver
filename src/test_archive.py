import unittest.mock as mock
from unittest import TestCase
from pyfakefs import fake_filesystem_unittest
from .archive import *
import os


class Test(fake_filesystem_unittest.TestCase):
    
    def setUp(self):
        self.setUpPyfakefs()
    
    def test_get_existing_library_album_paths(self):
        os.makedirs('/home/alpha')
        os.makedirs('/home/alpha/alpha - beta')
        os.makedirs('/home/alpha/alpha - bet')
        os.makedirs('/home/alpha/alpha - berta')
        os.makedirs('/home/x')

        ret = get_existing_library_album_paths('/home', 'alpha', 'alpha - beta (2000)')

        self.assertEqual(len(ret), 1)
        self.assertTrue('/home/alpha/alpha - beta' in ret)

    def test_get_existing_library_album_paths_with_dash(self):
        # self.fail()
        os.makedirs('/home/al-pha')
        os.makedirs('/home/al-pha/al-Pha - bet-a (2999)')
        os.makedirs('/home/al-pha/al-pha - title containing bet-a (2999)')
        os.makedirs('/home/al-pha/al-pha-bet-a (2999)')
        os.makedirs('/home/al-pha/bet-a')
        suggested = format_album('al-pha', 'bet-a', '2999')

        ret = get_existing_library_album_paths('/home', 'al-pha', suggested)

        self.assertEqual(len(ret), 3)
        self.assertTrue('/home/al-pha/al-Pha - bet-a (2999)' in ret)
        self.assertTrue('/home/al-pha/al-pha-bet-a (2999)' in ret)
        self.assertTrue('/home/al-pha/bet-a' in ret)
        self.assertTrue('/home/al-pha/al-pha - title containing bet-a (2999)' not in ret)
