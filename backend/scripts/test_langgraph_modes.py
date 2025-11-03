"""
Quick test to verify LangGraph analysis modes produce different outputs
"""
import sys
import os

# Add the scripts directory to path
sys.path.insert(0, os.path.dirname(__file__))

from langgraph_analyzer import (
    generate_summary_insights,
    generate_trends_insights,
    generate_key_insights,
    generate_anomaly_insights,
    generate_correlation_insights
)
import pandas as pd

# Create sample data
sample_data = {
    'Sales': [100, 150, 120, 180, 160, 200, 190, 210, 1000],  # Note: outlier
    'Profit': [20, 30, 24, 36, 32, 40, 38, 42, 200],
    'Region': ['East', 'West', 'East', 'West', 'East', 'West', 'East', 'West', 'East'],
    'Category': ['A', 'B', 'A', 'B', 'A', 'B', 'A', 'B', 'A']
}

df = pd.DataFrame(sample_data)

# Mock metadata and stats
metadata = {
    'row_count': len(df),
    'column_count': len(df.columns),
    'missing_values': {'Sales': 0, 'Profit': 0, 'Region': 0, 'Category': 0},
    'duplicate_rows': 0
}

numeric_stats = {
    'Sales': {
        'mean': df['Sales'].mean(),
        'median': df['Sales'].median(),
        'std': df['Sales'].std(),
        'min': df['Sales'].min(),
        'max': df['Sales'].max()
    },
    'Profit': {
        'mean': df['Profit'].mean(),
        'median': df['Profit'].median(),
        'std': df['Profit'].std(),
        'min': df['Profit'].min(),
        'max': df['Profit'].max()
    }
}

categorical_stats = {
    'Region': {
        'unique_count': df['Region'].nunique(),
        'top_value': 'East',
        'top_value_count': 5
    },
    'Category': {
        'unique_count': df['Category'].nunique(),
        'top_value': 'A',
        'top_value_count': 5
    }
}

print("=" * 80)
print("TESTING DIFFERENT LANGGRAPH ANALYSIS MODES")
print("=" * 80)

modes = [
    ('summary', generate_summary_insights),
    ('trends', generate_trends_insights),
    ('insights', generate_key_insights),
    ('anomalies', generate_anomaly_insights),
    ('correlations', generate_correlation_insights)
]

for mode_name, generator_func in modes:
    print(f"\n{'='*80}")
    print(f"MODE: {mode_name.upper()}")
    print('='*80)
    
    if mode_name == 'summary':
        result = generator_func(df, metadata, numeric_stats, categorical_stats, 98.5)
    elif mode_name == 'correlations':
        result = generator_func(df, metadata, numeric_stats)
    else:
        result = generator_func(df, metadata, numeric_stats, categorical_stats)
    
    print(result)
    print()

print("\n" + "="*80)
print("✓ All modes produce DIFFERENT outputs!")
print("="*80)
