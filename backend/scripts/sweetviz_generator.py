#!/usr/bin/env python3
"""
SweetViz Professional Report Generator
Generates comprehensive data analysis reports using SweetViz library
"""

import sys
import json
import pandas as pd
import numpy as np
import os
import sweetviz as sv
import warnings
warnings.filterwarnings('ignore')

# Suppress stdout during SweetViz generation (except our final JSON)
import io
from contextlib import redirect_stdout, redirect_stderr

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return super(NumpyEncoder, self).default(obj)

class ProfessionalSweetVizGenerator:
    def __init__(self):
        pass
        
    def generate_report(self, csv_file_path, output_dir, target_column=None):
        """Generate professional SweetViz analysis report"""
        try:
            # Read the data
            df = pd.read_csv(csv_file_path)
            
            if df.empty:
                return {
                    'status': 'error',
                    'error': 'CSV file is empty or could not be read',
                    'report_generated': False,
                    'output_directory': output_dir,
                    'report_file': ''
                }
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Configure SweetViz report
            # Skip ID columns if present, but don't fail if they don't exist
            id_columns = [col for col in df.columns if 'id' in col.lower()]
            if id_columns:
                config = sv.FeatureConfig(skip=id_columns)
            else:
                config = sv.FeatureConfig()
            
            # Generate comprehensive report with suppressed output
            captured_output = io.StringIO()
            captured_error = io.StringIO()
            
            report_name = "sweetviz_comprehensive_analysis.html"
            report_path = os.path.join(output_dir, report_name)
            
            try:
                with redirect_stdout(captured_output), redirect_stderr(captured_error):
                    if target_column and target_column in df.columns:
                        # Targeted analysis with specific target variable
                        report = sv.analyze(df, target_feat=target_column, feat_cfg=config)
                        report_name = f"sweetviz_targeted_analysis_{target_column}.html"
                        report_path = os.path.join(output_dir, report_name)
                    else:
                        # General exploratory data analysis
                        report = sv.analyze(df, feat_cfg=config)
                    
                    # Generate the report
                    report.show_html(report_path, open_browser=False, layout='vertical')
            except Exception as sweetviz_error:
                # If SweetViz fails, return error but still provide some basic info
                return {
                    'status': 'error',
                    'error': f'SweetViz analysis failed: {str(sweetviz_error)}',
                    'report_generated': False,
                    'output_directory': output_dir,
                    'report_file': '',
                    'basic_info': {
                        'rows': int(len(df)),
                        'columns': int(len(df.columns)),
                        'columns_list': list(df.columns)
                    }
                }
            
            # Generate summary statistics
            summary = self._generate_summary_stats(df, output_dir)
            
            return {
                'status': 'success',
                'report_generated': True,
                'main_report': report_name,
                'report_file': report_path,
                'output_directory': output_dir,
                'summary_stats': summary,
                'data_insights': self._extract_insights(df)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to generate SweetViz report: {str(e)}',
                'error_type': type(e).__name__,
                'report_generated': False,
                'output_directory': output_dir,
                'report_file': ''
            }
    
    def _generate_summary_stats(self, df, output_dir):
        """Generate comprehensive summary statistics"""
        try:
            numeric_cols = df.select_dtypes(include=['number']).columns
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            
            summary = {
                'dataset_info': {
                    'total_rows': int(len(df)),
                    'total_columns': int(len(df.columns)),
                    'numeric_columns': int(len(numeric_cols)),
                    'categorical_columns': int(len(categorical_cols)),
                    'missing_values': int(df.isnull().sum().sum()),
                    'duplicate_rows': int(df.duplicated().sum())
                },
                'data_quality': {
                    'completeness_percentage': float((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100),
                    'duplicate_percentage': float((df.duplicated().sum() / len(df)) * 100)
                },
                'column_types': {
                    'numeric': list(numeric_cols),
                    'categorical': list(categorical_cols)
                }
            }
            
            # Add numeric statistics
            if len(numeric_cols) > 0:
                numeric_stats = {}
                for col in numeric_cols:
                    numeric_stats[col] = {
                        'mean': float(df[col].mean()),
                        'median': float(df[col].median()),
                        'std': float(df[col].std()),
                        'min': float(df[col].min()),
                        'max': float(df[col].max()),
                        'missing_count': int(df[col].isnull().sum())
                    }
                summary['numeric_statistics'] = numeric_stats
            
            # Add categorical statistics
            if len(categorical_cols) > 0:
                categorical_stats = {}
                for col in categorical_cols:
                    categorical_stats[col] = {
                        'unique_values': int(df[col].nunique()),
                        'most_frequent': str(df[col].mode().iloc[0] if not df[col].mode().empty else 'N/A'),
                        'missing_count': int(df[col].isnull().sum())
                    }
                summary['categorical_statistics'] = categorical_stats
            
            # Save summary as JSON
            summary_path = os.path.join(output_dir, 'sweetviz_summary_stats.json')
            with open(summary_path, 'w') as f:
                json.dump(summary, f, indent=2, cls=NumpyEncoder)
            
            return summary
            
        except Exception as e:
            return {
                'error': f'Failed to generate summary statistics: {str(e)}',
                'dataset_info': {
                    'total_rows': int(len(df)) if 'df' in locals() else 0,
                    'total_columns': int(len(df.columns)) if 'df' in locals() else 0
                }
            }
    
    def _extract_insights(self, df):
        """Extract key insights from the data"""
        try:
            insights = []
            
            # Data quality insights
            missing_percentage = (df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100
            if missing_percentage > 10:
                insights.append({
                    'type': 'data_quality',
                    'severity': 'warning',
                    'message': f'Dataset has {missing_percentage:.1f}% missing values - consider data cleaning'
                })
            elif missing_percentage < 1:
                insights.append({
                    'type': 'data_quality',
                    'severity': 'info',
                    'message': f'Excellent data quality with only {missing_percentage:.1f}% missing values'
                })
            
            # Dataset size insights
            if len(df) < 100:
                insights.append({
                    'type': 'sample_size',
                    'severity': 'warning',
                    'message': 'Small dataset - statistical analyses may be limited'
                })
            elif len(df) > 10000:
                insights.append({
                    'type': 'sample_size',
                    'severity': 'info',
                    'message': 'Large dataset - excellent for statistical analysis'
                })
            
            # Column type insights
            numeric_cols = len(df.select_dtypes(include=['number']).columns)
            categorical_cols = len(df.select_dtypes(include=['object', 'category']).columns)
            
            if numeric_cols > categorical_cols:
                insights.append({
                    'type': 'data_composition',
                    'severity': 'info',
                    'message': 'Numeric-heavy dataset - good for quantitative analysis'
                })
            elif categorical_cols > numeric_cols:
                insights.append({
                    'type': 'data_composition',
                    'severity': 'info',
                    'message': 'Categorical-heavy dataset - consider text analysis techniques'
                })
            
            return insights
            
        except Exception as e:
            return [{'type': 'error', 'severity': 'error', 'message': f'Failed to extract insights: {str(e)}'}]

def main():
    try:
        if len(sys.argv) < 3:
            result = {
                'status': 'error', 
                'error': 'Usage: python sweetviz_generator.py <csv_file> <output_dir> [target_column]'
            }
            print(json.dumps(result, cls=NumpyEncoder))
            return
        
        csv_file = sys.argv[1]
        output_dir = sys.argv[2]
        target_column = sys.argv[3] if len(sys.argv) > 3 else None
        
        if not os.path.exists(csv_file):
            result = {
                'status': 'error',
                'error': f'CSV file does not exist: {csv_file}'
            }
            print(json.dumps(result, cls=NumpyEncoder))
            return
        
        generator = ProfessionalSweetVizGenerator()
        result = generator.generate_report(csv_file, output_dir, target_column)
        
        print(json.dumps(result, indent=2, cls=NumpyEncoder))
        
    except Exception as e:
        # Ensure we ALWAYS output JSON, even on error
        error_result = {
            'status': 'error',
            'error': f'SweetViz generation failed: {str(e)}',
            'error_type': type(e).__name__,
            'report_generated': False,
            'output_directory': output_dir if 'output_dir' in locals() else '',
            'report_file': ''
        }
        print(json.dumps(error_result, cls=NumpyEncoder))

if __name__ == "__main__":
    main()