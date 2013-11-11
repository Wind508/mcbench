import unittest

import fakeredis

import manage
import mcbench.client

class McBenchTestCase(unittest.TestCase):
    def setUp(self):
        self.redis = fakeredis.FakeStrictRedis()
        self.client = mcbench.client.McBenchClient(self.redis, 'testdata')
        manage.load_manifest('testdata/manifest.json', self.client)

    def tearDown(self):
        self.redis.flushdb()

    def test_testdata_was_loaded_correctly(self):
        benchmarks = self.client.get_all_benchmarks()
        self.assertItemsEqual(
            ['1888-repmf', '8636-emgm', '33851-wind-barb-plotter'],
            [benchmark.name for benchmark in benchmarks])

        repmf = self.client.get_benchmark_by_name('1888-repmf')
        emgm = self.client.get_benchmark_by_name('8636-emgm')
        plotter = self.client.get_benchmark_by_name('33851-wind-barb-plotter')
        self.assertEqual('repmf', next(repmf.get_files()).name)
        self.assertEqual('EM_GM', next(emgm.get_files()).name)
        self.assertEqual('windbarbm', next(plotter.get_files()).name)

    def test_get_nonexistent_benchmark(self):
        with self.assertRaises(mcbench.client.BenchmarkDoesNotExist):
            self.client.get_benchmark_by_name('does-not-exist')

if __name__ == '__main__':
    unittest.main()
