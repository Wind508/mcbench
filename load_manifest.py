import argparse
import json
import os

import mcbench.client


def parse_args():
    parser = argparse.ArgumentParser(
        description='load benchmarks into McBench redis instance')
    parser.add_argument(
        '--redis_url',
        default='redis://localhost:6379',
        help='URL of redis instance.'
    )
    parser.add_argument(
        '--manifest', required=True,
        help='Path to manifest.json.')
    return parser.parse_args()


def main():
    args = parse_args()
    mcbench_client = mcbench.client.create(redis_url=args.redis_url)
    with open(os.path.expanduser(args.manifest)) as f:
        manifest = json.load(f)
        for project in manifest['projects']:
            benchmark = mcbench.client.Benchmark(**project)
            mcbench_client.insert_benchmark(benchmark)

if __name__ == '__main__':
    main()
