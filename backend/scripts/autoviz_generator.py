#!/usr/bin/env python3
"""
AutoViz Professional Visualization Generator
Generates high-quality automated visualizations using AutoViz library
"""

import sys
import json
import pandas as pd
import numpy as np
import os
from autoviz.AutoViz_Class import AutoViz_Class
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import warnings
warnings.filterwarnings('ignore')

# Suppress stdout during AutoViz generation (except our final JSON)
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

class ProfessionalAutoVizGenerator:
    def __init__(self):
        self.av = AutoViz_Class()
        
    def generate_visualizations(self, csv_file_path, output_dir):
        """Generate professional AutoViz visualizations"""
        try:
            # Read the data
            df = pd.read_csv(csv_file_path)
            
            if df.empty:
                return {
                    'status': 'error',
                    'error': 'CSV file is empty or could not be read',
                    'charts_generated': 0,
                    'output_directory': output_dir,
                    'chart_files': []
                }
            
            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate AutoViz plots with suppressed output
            captured_output = io.StringIO()
            captured_error = io.StringIO()
            
            charts = []
            try:
                with redirect_stdout(captured_output), redirect_stderr(captured_error):
                    charts = self.av.AutoViz(
                        filename=csv_file_path,
                        sep=',',
                        depVar='',
                        dfte=df,
                        header=0,
                        verbose=0,  # Reduced verbosity
                        lowess=False,
                        chart_format='html',
                        max_rows_analyzed=5000,
                        max_cols_analyzed=30,
                        save_plot_dir=output_dir
                    )
            except Exception as autoviz_error:
                # If AutoViz fails, continue with custom charts
                charts = []
            
            # Generate additional professional visualizations
            additional_charts = self._generate_custom_charts(df, output_dir)
            
            # Create summary report
            summary = self._create_summary_report(df, output_dir)
            
            return {
                'status': 'success',
                'charts_generated': len(charts) + len(additional_charts),
                'output_directory': output_dir,
                'summary': summary,
                'chart_files': self._list_generated_files(output_dir)
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': f'Failed to generate visualizations: {str(e)}',
                'error_type': type(e).__name__,
                'charts_generated': 0,
                'output_directory': output_dir,
                'chart_files': []
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _generate_custom_charts(self, df, output_dir):
        """Generate additional professional charts"""
        charts = []
        
        # Get numeric and categorical columns
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # 1. Professional Correlation Heatmap
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            fig = px.imshow(
                corr_matrix,
                title="Professional Correlation Analysis",
                color_continuous_scale='RdBu_r',
                aspect='auto'
            )
            fig.update_layout(
                title_font_size=16,
                title_x=0.5,
                font=dict(family="Arial", size=12),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            fig.write_html(os.path.join(output_dir, 'correlation_heatmap.html'))
            charts.append('correlation_heatmap.html')
        
        # 2. Distribution Analysis
        if numeric_cols:
            fig = make_subplots(
                rows=min(2, len(numeric_cols)),
                cols=min(2, (len(numeric_cols) + 1) // 2),
                subplot_titles=numeric_cols[:4],
                vertical_spacing=0.1
            )
            
            for i, col in enumerate(numeric_cols[:4]):
                row = (i // 2) + 1
                col_pos = (i % 2) + 1
                fig.add_trace(
                    go.Histogram(x=df[col], name=col, showlegend=False),
                    row=row, col=col_pos
                )
            
            fig.update_layout(
                title="Distribution Analysis Dashboard",
                title_font_size=16,
                title_x=0.5,
                font=dict(family="Arial", size=12),
                plot_bgcolor='white',
                paper_bgcolor='white',
                height=600
            )
            fig.write_html(os.path.join(output_dir, 'distribution_analysis.html'))
            charts.append('distribution_analysis.html')
        
        # 3. Professional Box Plots
        if numeric_cols and categorical_cols:
            cat_col = categorical_cols[0]
            num_col = numeric_cols[0]
            
            fig = px.box(
                df, 
                x=cat_col, 
                y=num_col,
                title=f"Professional Box Plot: {num_col} by {cat_col}",
                color=cat_col
            )
            fig.update_layout(
                title_font_size=16,
                title_x=0.5,
                font=dict(family="Arial", size=12),
                plot_bgcolor='white',
                paper_bgcolor='white'
            )
            fig.write_html(os.path.join(output_dir, 'professional_boxplot.html'))
            charts.append('professional_boxplot.html')
        
        return charts
    
    def _create_summary_report(self, df, output_dir):
        """Create a professional summary report"""
        summary = {
            'dataset_info': {
                'rows': int(len(df)),
                'columns': int(len(df.columns)),
                'numeric_columns': int(len(df.select_dtypes(include=['number']).columns)),
                'categorical_columns': int(len(df.select_dtypes(include=['object', 'category']).columns)),
                'missing_values': int(df.isnull().sum().sum())
            },
            'data_quality': {
                'completeness': float((1 - df.isnull().sum().sum() / (len(df) * len(df.columns))) * 100),
                'duplicates': int(len(df) - len(df.drop_duplicates()))
            }
        }
        
        # Save summary as JSON
        with open(os.path.join(output_dir, 'analysis_summary.json'), 'w') as f:
            json.dump(summary, f, indent=2, cls=NumpyEncoder)
            
        return summary
    
    def _list_generated_files(self, output_dir):
        """List all generated visualization files"""
        try:
            files = [f for f in os.listdir(output_dir) if f.endswith(('.html', '.png', '.jpg', '.svg'))]
            return files
        except:
            return []

def main():
    try:
        if len(sys.argv) != 3:
            result = {
                'status': 'error', 
                'error': 'Usage: python autoviz_generator.py <csv_file> <output_dir>'
            }
            print(json.dumps(result, cls=NumpyEncoder))
            return
        
        csv_file = sys.argv[1]
        output_dir = sys.argv[2]
        
        if not os.path.exists(csv_file):
            result = {
                'status': 'error',
                'error': f'CSV file does not exist: {csv_file}'
            }
            print(json.dumps(result, cls=NumpyEncoder))
            return
        
        generator = ProfessionalAutoVizGenerator()
        result = generator.generate_visualizations(csv_file, output_dir)
        
        print(json.dumps(result, indent=2, cls=NumpyEncoder))
        
    except Exception as e:
        # Ensure we ALWAYS output JSON, even on error
        error_result = {
            'status': 'error',
            'error': f'AutoViz generation failed: {str(e)}',
            'error_type': type(e).__name__,
            'charts_generated': 0,
            'output_directory': output_dir if 'output_dir' in locals() else '',
            'chart_files': []
        }
        print(json.dumps(error_result, cls=NumpyEncoder))

if __name__ == "__main__":
    main()