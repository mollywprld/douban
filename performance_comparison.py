#!/usr/bin/env python3
"""
豆瓣Top250爬虫性能对比脚本
比较requests+Selenium版本 vs Scrapy版本的性能差异
"""

import json
import sqlite3
import time
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Tuple
import psutil
import os


class PerformanceComparator:
    """性能对比器"""

    def __init__(self):
        self.results = {}
        self.project_root = Path(__file__).parent

    def archive_existing_file(self, file_path: Path) -> None:
        """如果文件存在，则重命名备份以保留旧文件。"""
        if file_path.exists():
            timestamp = time.strftime('%Y%m%d_%H%M%S')
            archive_path = file_path.with_name(f"{file_path.stem}_{timestamp}{file_path.suffix}")
            file_path.replace(archive_path)

    def measure_memory_usage(self, pid: int) -> Dict[str, float]:
        """测量进程内存使用情况"""
        try:
            process = psutil.Process(pid)
            memory_info = process.memory_info()
            return {
                'rss': memory_info.rss / 1024 / 1024,  # MB
                'vms': memory_info.vms / 1024 / 1024,  # MB
                'percent': process.memory_percent()
            }
        except psutil.NoSuchProcess:
            return {'rss': 0, 'vms': 0, 'percent': 0}

    def run_requests_version(self, limit: int = 10) -> Dict[str, Any]:
        """运行requests版本的爬虫"""
        print("🚀 运行requests+Selenium版本...")

        # 备份旧的 requests 输出 JSON，保留历史文件
        self.archive_existing_file(self.project_root / 'douban_requests.json')

        start_time = time.time()
        initial_memory = psutil.virtual_memory().used / 1024 / 1024  # MB

        # 运行爬虫
        cmd = [
            sys.executable, 'douban_top250_spider.py',
            '--output', 'douban_requests.json',
            '--posters', 'posters_requests',
            '--limit', str(limit)
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )

            end_time = time.time()
            final_memory = psutil.virtual_memory().used / 1024 / 1024

            # 分析结果
            success = result.returncode == 0
            execution_time = end_time - start_time
            memory_used = max(0, final_memory - initial_memory)

            # 检查输出文件
            json_file = self.project_root / 'douban_requests.json'
            data_count = 0
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data_count = len(data)
                except:
                    pass

            return {
                'version': 'requests',
                'success': success,
                'execution_time': execution_time,
                'memory_used': memory_used,
                'data_count': data_count,
                'stdout': result.stdout[-1000:] if result.stdout else '',
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'return_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'version': 'requests',
                'success': False,
                'execution_time': 600,
                'memory_used': 0,
                'data_count': 0,
                'error': 'Timeout after 10 minutes'
            }

    def run_scrapy_version(self, limit: int = 10) -> Dict[str, Any]:
        """运行Scrapy版本的爬虫"""
        print("🚀 运行Scrapy版本...")

        scrapy_dir = self.project_root / 'scrapy_douban'

        # 备份旧的 Scrapy 输出 JSON/CSV，保留历史文件
        for file in ['douban_scrapy.json', 'movies_scrapy.csv', 'comments_scrapy.csv']:
            self.archive_existing_file(scrapy_dir / file)

        start_time = time.time()
        initial_memory = psutil.virtual_memory().used / 1024 / 1024

        # 运行Scrapy爬虫
        cmd = [
            sys.executable, '-m', 'scrapy', 'crawl', 'douban_top250',
            '-a', f'limit={limit}',
            '-L', 'INFO'
        ]

        try:
            result = subprocess.run(
                cmd,
                cwd=scrapy_dir,
                capture_output=True,
                text=True,
                timeout=600
            )

            end_time = time.time()
            final_memory = psutil.virtual_memory().used / 1024 / 1024

            success = result.returncode == 0
            execution_time = end_time - start_time
            memory_used = max(0, final_memory - initial_memory)

            # 检查输出文件
            json_file = scrapy_dir / 'douban_scrapy.json'
            data_count = 0
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        data_count = len(data)
                except:
                    pass

            return {
                'version': 'scrapy',
                'success': success,
                'execution_time': execution_time,
                'memory_used': memory_used,
                'data_count': data_count,
                'stdout': result.stdout[-1000:] if result.stdout else '',
                'stderr': result.stderr[-1000:] if result.stderr else '',
                'return_code': result.returncode
            }

        except subprocess.TimeoutExpired:
            return {
                'version': 'scrapy',
                'success': False,
                'execution_time': 600,
                'memory_used': 0,
                'data_count': 0,
                'error': 'Timeout after 10 minutes'
            }

    def analyze_database_size(self, db_path: Path) -> Dict[str, Any]:
        """分析数据库大小"""
        if not db_path.exists():
            return {'size_mb': 0, 'movies_count': 0, 'comments_count': 0}

        size_mb = db_path.stat().st_size / 1024 / 1024

        try:
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            cursor.execute('SELECT COUNT(*) FROM movies')
            movies_count = cursor.fetchone()[0]

            cursor.execute('SELECT COUNT(*) FROM comments')
            comments_count = cursor.fetchone()[0]

            conn.close()

            return {
                'size_mb': round(size_mb, 2),
                'movies_count': movies_count,
                'comments_count': comments_count
            }
        except:
            return {'size_mb': round(size_mb, 2), 'movies_count': 0, 'comments_count': 0}

    def compare_versions(self, limit: int = 10) -> Dict[str, Any]:
        """比较两个版本的性能"""
        print(f"🎯 开始性能对比测试 (限制{limit}部电影)...")

        # 运行requests版本
        requests_result = self.run_requests_version(limit)

        # 等待系统恢复
        time.sleep(5)

        # 运行Scrapy版本
        scrapy_result = self.run_scrapy_version(limit)

        # 分析数据库大小
        requests_db = self.project_root / 'douban_requests.db'
        if not requests_db.exists():
            requests_db = self.project_root / 'douban_top250.db'
        scrapy_db = self.project_root / 'scrapy_douban' / 'douban_scrapy.db'

        requests_db_info = self.analyze_database_size(requests_db)
        scrapy_db_info = self.analyze_database_size(scrapy_db)

        # 计算对比指标
        time_ratio = None
        if requests_result['execution_time'] > 0 and scrapy_result['execution_time'] > 0:
            time_ratio = requests_result['execution_time'] / scrapy_result['execution_time']

        memory_ratio = None
        if requests_result['memory_used'] > 0 and scrapy_result['memory_used'] > 0:
            memory_ratio = requests_result['memory_used'] / scrapy_result['memory_used']

        size_ratio = None
        if scrapy_db_info['size_mb'] > 0 and requests_db_info['size_mb'] > 0:
            size_ratio = requests_db_info['size_mb'] / scrapy_db_info['size_mb']

        comparison = {
            'test_config': {
                'movie_limit': limit,
                'timestamp': time.time()
            },
            'requests_version': requests_result,
            'scrapy_version': scrapy_result,
            'performance_comparison': {
                'time_ratio': time_ratio,
                'memory_ratio': memory_ratio,
                'success_rate_requests': 1 if requests_result['success'] else 0,
                'success_rate_scrapy': 1 if scrapy_result['success'] else 0,
                'data_completeness_requests': requests_result['data_count'] / limit,
                'data_completeness_scrapy': scrapy_result['data_count'] / limit
            },
            'database_comparison': {
                'requests_db': requests_db_info,
                'scrapy_db': scrapy_db_info,
                'size_ratio': size_ratio
            }
        }

        return comparison

    def print_comparison_report(self, comparison: Dict[str, Any]):
        """打印对比报告"""
        print("\n" + "="*80)
        print("📊 豆瓣Top250爬虫性能对比报告")
        print("="*80)

        config = comparison['test_config']
        req = comparison['requests_version']
        scrapy = comparison['scrapy_version']
        perf = comparison['performance_comparison']
        db = comparison['database_comparison']

        print(f"测试配置: 限制爬取 {config['movie_limit']} 部电影")
        print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(config['timestamp']))}")
        print()

        print("🚀 Requests+Selenium版本:")
        print(f"   执行时间: {req['execution_time']:.2f} 秒")
        print(f"   内存使用: {req['memory_used']:.2f} MB")
        print(f"   数据条数: {req['data_count']}")
        print(f"   成功状态: {'✅' if req['success'] else '❌'}")
        print()

        print("🕷️  Scrapy版本:")
        print(f"   执行时间: {scrapy['execution_time']:.2f} 秒")
        print(f"   内存使用: {scrapy['memory_used']:.2f} MB")
        print(f"   数据条数: {scrapy['data_count']}")
        print(f"   成功状态: {'✅' if scrapy['success'] else '❌'}")
        print()

        print("⚡ 性能对比:")
        if perf['time_ratio'] is None:
            print("   时间效率: 无法计算，执行时间数据不足")
        elif perf['time_ratio'] > 1:
            print(f"   时间效率: Scrapy快 {perf['time_ratio']:.2f} 倍")
        else:
            print(f"   时间效率: Requests快 {1/perf['time_ratio']:.2f} 倍")

        if perf['memory_ratio'] is None:
            print("   内存效率: 无法计算，内存数据不足")
        elif perf['memory_ratio'] > 1:
            print(f"   内存效率: Scrapy节省 {perf['memory_ratio']:.2f} 倍内存")
        else:
            print(f"   内存效率: Requests节省 {1/perf['memory_ratio']:.2f} 倍内存")

        print(f"   数据完整性 - Requests: {perf['data_completeness_requests']:.1%}")
        print(f"   数据完整性 - Scrapy: {perf['data_completeness_scrapy']:.1%}")
        print()

        print("💾 数据库对比:")
        print(f"   Requests DB: {db['requests_db']['size_mb']:.2f} MB ({db['requests_db']['movies_count']}电影, {db['requests_db']['comments_count']}评论)")
        print(f"   Scrapy DB: {db['scrapy_db']['size_mb']:.2f} MB ({db['scrapy_db']['movies_count']}电影, {db['scrapy_db']['comments_count']}评论)")
        if db['size_ratio'] is None:
            print("   数据库大小: 无法计算，数据库大小数据不足")
        elif db['size_ratio'] > 1:
            print(f"   数据库大小: Scrapy小 {db['size_ratio']:.2f} 倍")
        else:
            print(f"   数据库大小: Requests小 {1/db['size_ratio']:.2f} 倍")
        print()

        print("🏆 总结:")
        if req['success'] and scrapy['success']:
            if perf['time_ratio'] is not None:
                if perf['time_ratio'] > 1.2:
                    print("   🏃 Scrapy版本速度更快，适合大规模爬取")
                elif perf['time_ratio'] < 0.8:
                    print("   🐌 Requests版本速度更快，但代码复杂度更高")
                else:
                    print("   ⚖️ 两个版本性能相近，建议根据项目需求选择")
            else:
                print("   速度对比: 无法计算")

            if perf['memory_ratio'] is not None:
                if perf['memory_ratio'] > 1.5:
                    print("   🧠 Scrapy版本内存效率更高")
                elif perf['memory_ratio'] < 0.7:
                    print("   💾 Requests版本内存使用更少")
            else:
                print("   内存效率对比: 无法计算")
        else:
            print("   ⚠️  存在执行失败的情况，请检查日志")


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='豆瓣Top250爬虫性能对比')
    parser.add_argument('--limit', type=int, default=10, help='爬取电影数量限制')
    parser.add_argument('--output', type=str, default='performance_comparison.json', help='对比结果输出文件')

    args = parser.parse_args()

    comparator = PerformanceComparator()
    comparison = comparator.compare_versions(args.limit)
    comparator.print_comparison_report(comparison)

    # 保存对比结果
    output_file = Path(args.output)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(comparison, f, ensure_ascii=False, indent=2)

    print(f"\n📄 详细对比结果已保存到: {output_file}")


if __name__ == '__main__':
    main()