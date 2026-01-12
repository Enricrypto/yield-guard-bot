import sys

try:
    with open('simulation_summary.txt', 'r') as f:
        content = f.read()
        if 'Return:' in content:
            for line in content.splitlines():
                if 'Return:' in line and '%' in line:
                    return_str = line.split('Return:')[1].split('%')[0].strip()
                    return_pct = float(return_str)
                    if return_pct < -2.0:
                        print(f'⚠️ ALERT: Significant loss detected: {return_pct}%')
                        sys.exit(1)
                    elif return_pct < 0:
                        print(f'⚠️ Warning: Negative return: {return_pct}%')
                    else:
                        print(f'✓ Positive return: {return_pct}%')
except Exception as e:
    print(f'Could not parse return value: {e}')
    sys.exit(0)
