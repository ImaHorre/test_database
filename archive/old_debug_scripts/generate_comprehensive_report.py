"""
Generate Comprehensive Analysis Report

This script analyzes the most recent fake scan report and generates
detailed statistics with recommendations.
"""

import re
from pathlib import Path
from collections import Counter, defaultdict
from datetime import datetime


def parse_report(report_path):
    """Parse the fake scan report and extract statistics."""
    with open(report_path, 'r', encoding='utf-8') as f:
        content = f.read()

    stats = {}

    # Extract summary statistics
    if match := re.search(r'Files processed:\s+(\d+)', content):
        stats['total_processed'] = int(match.group(1))

    if match := re.search(r'Complete quality:\s+(\d+)', content):
        stats['complete'] = int(match.group(1))

    if match := re.search(r'Partial quality:\s+(\d+)', content):
        stats['partial'] = int(match.group(1))

    if match := re.search(r'Minimal quality:\s+(\d+)', content):
        stats['minimal'] = int(match.group(1))

    if match := re.search(r'Failed extractions:\s+(\d+)', content):
        stats['failed'] = int(match.group(1))

    # Extract typo corrections
    stats['typo_corrections'] = {}
    typo_section = re.search(r'TYPO CORRECTIONS APPLIED\n-+(.*?)\n\n', content, re.DOTALL)
    if typo_section:
        for line in typo_section.group(1).split('\n'):
            if match := re.match(r'\s+(\w+):\s+(\d+)', line):
                stats['typo_corrections'][match.group(1)] = int(match.group(2))

    # Extract inferences
    stats['inferences'] = {}
    infer_section = re.search(r'INFERRED FIELDS\n-+(.*?)\n\n', content, re.DOTALL)
    if infer_section:
        for line in infer_section.group(1).split('\n'):
            if match := re.match(r'\s+(\w+):\s+(\d+)', line):
                stats['inferences'][match.group(1)] = int(match.group(2))

    # Extract missing field counts
    stats['missing_fields'] = {}
    missing_section = re.search(r'MISSING PRIORITY FIELDS\n-+(.*?)(?=\nEXAMPLE|$)', content, re.DOTALL)
    if missing_section:
        for match in re.finditer(r'(\w+):\s+(\d+)\s+files missing', missing_section.group(1)):
            stats['missing_fields'][match.group(1)] = int(match.group(2))

    # Extract example successful extractions
    stats['success_examples'] = []
    success_section = re.search(r'EXAMPLE SUCCESSFUL EXTRACTIONS.*?\n-+(.*?)(?=\nEXAMPLE FAILURES|$)', content, re.DOTALL)
    if success_section:
        for file_block in re.finditer(r'File: (.*?)\n((?:  .*?\n)+)', success_section.group(1)):
            example = {'path': file_block.group(1), 'fields': {}}
            for field_line in file_block.group(2).split('\n'):
                if match := re.match(r'\s+(\w+(?:\s+\w+)?):\s+(.+)', field_line):
                    example['fields'][match.group(1).strip().lower().replace(' ', '_')] = match.group(2)
            stats['success_examples'].append(example)

    # Extract example failures
    stats['failure_examples'] = []
    failure_section = re.search(r'EXAMPLE FAILURES.*?\n-+(.*?)(?=\n=|$)', content, re.DOTALL)
    if failure_section:
        for file_block in re.finditer(r'File: (.*?)\n((?:  .*?\n)+)', failure_section.group(1)):
            example = {'path': file_block.group(1), 'fields': {}}
            for field_line in file_block.group(2).split('\n'):
                if match := re.match(r'\s+(\w+(?:\s+\w+)?):\s+(.+)', field_line):
                    example['fields'][match.group(1).strip().lower().replace(' ', '_')] = match.group(2)
            stats['failure_examples'].append(example)

    return stats


def generate_comprehensive_report(stats):
    """Generate a comprehensive analysis report."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_path = f'comprehensive_analysis_{timestamp}.txt'

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write('=' * 80 + '\n')
        f.write('COMPREHENSIVE SCAN TEST ANALYSIS REPORT\n')
        f.write(f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
        f.write('=' * 80 + '\n\n')

        # Executive Summary
        f.write('EXECUTIVE SUMMARY\n')
        f.write('-' * 80 + '\n')
        total = stats['total_processed']
        complete = stats['complete']
        partial = stats['partial']
        minimal = stats['minimal']
        failed = stats['failed']
        successful = complete + partial + minimal

        f.write(f'Total Files Processed:        {total}\n')
        f.write(f'Overall Success Rate:         {successful/total*100:.1f}% ({successful}/{total})\n')
        f.write(f'  - Complete Quality:         {complete} ({complete/total*100:.1f}%)\n')
        f.write(f'  - Partial Quality:          {partial} ({partial/total*100:.1f}%)\n')
        f.write(f'  - Minimal Quality:          {minimal} ({minimal/total*100:.1f}%)\n')
        f.write(f'Failed Extractions:           {failed} ({failed/total*100:.1f}%)\n')
        f.write('\n')

        # Success Metrics
        f.write('SUCCESS METRICS\n')
        f.write('-' * 80 + '\n')
        f.write(f'Complete extractions represent files where all critical metadata was\n')
        f.write(f'successfully extracted, including device ID, dates, fluids, and flow parameters.\n')
        f.write(f'\n')
        f.write(f'Achievement Breakdown:\n')
        f.write(f'  - EXCELLENT (Complete):     {complete} files - All critical fields extracted\n')
        f.write(f'  - GOOD (Partial):           {partial} files - Most fields extracted, minor gaps\n')
        f.write(f'  - ACCEPTABLE (Minimal):     {minimal} files - Basic identification possible\n')
        f.write(f'  - NEEDS ATTENTION (Failed): {failed} files - Missing critical identifiers\n')
        f.write('\n')

        # Data Quality Improvements
        f.write('DATA QUALITY IMPROVEMENTS\n')
        f.write('-' * 80 + '\n')
        f.write('The extractor successfully applied corrections and inferences:\n')
        f.write('\n')

        if stats.get('typo_corrections'):
            f.write('Typo Corrections Applied:\n')
            for field, count in stats['typo_corrections'].items():
                f.write(f'  - {field}: {count} corrections\n')
            f.write('\n')

        if stats.get('inferences'):
            f.write('Intelligent Inferences Made:\n')
            for field, count in stats['inferences'].items():
                f.write(f'  - {field}: {count} inferences (default values applied)\n')
            f.write('\n')

        # Field Extraction Coverage
        f.write('FIELD EXTRACTION COVERAGE\n')
        f.write('-' * 80 + '\n')

        if stats.get('missing_fields'):
            f.write('Coverage by Field:\n')
            for field, missing_count in sorted(stats['missing_fields'].items()):
                present_count = total - missing_count
                coverage_pct = present_count / total * 100
                f.write(f'  {field:20s}: {present_count:4d}/{total} ({coverage_pct:5.1f}%) extracted\n')
            f.write('\n')

        # Successful Extraction Examples
        f.write('SUCCESSFUL EXTRACTION EXAMPLES\n')
        f.write('-' * 80 + '\n')
        f.write('These files demonstrate the extractor working correctly:\n')
        f.write('\n')

        for i, example in enumerate(stats.get('success_examples', [])[:5], 1):
            f.write(f'{i}. {example["path"]}\n')
            for field, value in example['fields'].items():
                f.write(f'   {field}: {value}\n')
            f.write('\n')

        # Failure Pattern Analysis
        f.write('FAILURE PATTERN ANALYSIS\n')
        f.write('-' * 80 + '\n')
        f.write('Analyzing common failure patterns:\n')
        f.write('\n')

        # Analyze failure examples
        failure_patterns = defaultdict(list)
        for example in stats.get('failure_examples', []):
            path = example['path']

            # Pattern 1: Flow parameter folder without device hierarchy
            if '5mlhr' in path and not any('W13' in p or 'W14' in p for p in path.split('/')):
                failure_patterns['Missing device hierarchy (flow param folder at root)'].append(path)

            # Pattern 2: Device in filename but not extracted
            if 'W13' in path.upper() or 'W14' in path.upper():
                if 'device' in example['fields'] and example['fields']['device'] == 'MISSING':
                    failure_patterns['Device in path but not extracted'].append(path)

            # Pattern 3: Date in filename but not extracted
            if re.search(r'\d{4}_\d{4}', path):
                if 'bonding_date' in example['fields'] and example['fields']['bonding_date'] == 'MISSING':
                    failure_patterns['Date in filename but not extracted'].append(path)

        if failure_patterns:
            for pattern, paths in failure_patterns.items():
                f.write(f'Pattern: {pattern}\n')
                f.write(f'  Occurrences: {len(paths)}\n')
                for path in paths[:3]:
                    f.write(f'  - {path}\n')
                if len(paths) > 3:
                    f.write(f'  ... and {len(paths)-3} more\n')
                f.write('\n')

        # Recommendations
        f.write('RECOMMENDATIONS\n')
        f.write('-' * 80 + '\n')
        f.write('\n')

        # Calculate improvement priority
        device_missing = stats['missing_fields'].get('device_id', 0)
        date_missing = stats['missing_fields'].get('bonding_date', 0)

        if device_missing > 100:
            f.write('1. HIGH PRIORITY: Device ID Extraction\n')
            f.write(f'   - {device_missing} files missing device ID ({device_missing/total*100:.1f}%)\n')
            f.write(f'   - Most failures appear to be files in non-standard directory structures\n')
            f.write(f'   - Recommend: Enhance device ID extraction from filename when folder hierarchy is incomplete\n')
            f.write('\n')

        if date_missing > 100:
            f.write('2. HIGH PRIORITY: Date Extraction\n')
            f.write(f'   - {date_missing} files missing bonding date ({date_missing/total*100:.1f}%)\n')
            f.write(f'   - These files are often in the same non-standard directories\n')
            f.write(f'   - Recommend: Improve date extraction from filename when folder hierarchy is incomplete\n')
            f.write('\n')

        if complete / total < 0.5:
            f.write('3. MEDIUM PRIORITY: Overall Quality Improvement\n')
            f.write(f'   - Only {complete/total*100:.1f}% of files have complete metadata\n')
            f.write(f'   - Recommendation: Focus on completing extractions for partial/minimal quality files\n')
            f.write(f'   - This will improve query accuracy and data reliability\n')
            f.write('\n')

        # Positive notes
        f.write('POSITIVE ACHIEVEMENTS\n')
        f.write('-' * 80 + '\n')

        if complete > 300:
            f.write(f'- Successfully extracted complete metadata for {complete} files ({complete/total*100:.1f}%)\n')

        if stats.get('typo_corrections'):
            total_corrections = sum(stats['typo_corrections'].values())
            f.write(f'- Auto-corrected {total_corrections} typos in metadata fields\n')

        if stats.get('inferences'):
            total_inferences = sum(stats['inferences'].values())
            f.write(f'- Applied {total_inferences} intelligent inferences for missing data\n')

        if successful / total > 0.5:
            f.write(f'- Overall success rate of {successful/total*100:.1f}% indicates robust extraction logic\n')

        f.write('\n')

        # Next Steps
        f.write('SUGGESTED NEXT STEPS\n')
        f.write('-' * 80 + '\n')
        f.write('\n')
        f.write('1. Address High Priority Issues:\n')
        f.write('   - Review the failure examples and identify common patterns\n')
        f.write('   - Enhance extraction logic for non-standard directory structures\n')
        f.write('   - Add fallback mechanisms for filename-based extraction\n')
        f.write('\n')
        f.write('2. Test Specific Failure Cases:\n')
        f.write('   - Create targeted tests for the identified failure patterns\n')
        f.write('   - Verify that fixes work without breaking existing successful extractions\n')
        f.write('\n')
        f.write('3. Production Validation:\n')
        f.write('   - Run extraction on full dataset\n')
        f.write('   - Generate sample reports to verify query accuracy\n')
        f.write('   - Document any edge cases for future reference\n')
        f.write('\n')

        f.write('=' * 80 + '\n')
        f.write('END OF COMPREHENSIVE ANALYSIS\n')
        f.write('=' * 80 + '\n')

    return report_path


def main():
    # Find the most recent fake scan report
    reports = sorted(Path('.').glob('fake_scan_report_*.txt'))

    if not reports:
        print("ERROR: No fake scan reports found")
        return

    latest_report = reports[-1]
    print(f"Analyzing: {latest_report}")
    print()

    # Parse the report
    stats = parse_report(latest_report)

    # Generate comprehensive analysis
    report_path = generate_comprehensive_report(stats)

    print(f"Comprehensive analysis saved to: {report_path}")
    print()
    print("Key Metrics:")
    print(f"  Total Processed: {stats['total_processed']}")
    print(f"  Success Rate: {(stats['complete'] + stats['partial'] + stats['minimal']) / stats['total_processed'] * 100:.1f}%")
    print(f"  Complete: {stats['complete']}")
    print(f"  Failed: {stats['failed']}")


if __name__ == '__main__':
    main()
