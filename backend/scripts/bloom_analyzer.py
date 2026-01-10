import pandas as pd
import numpy as np
import json
import sys
import os
from datetime import datetime
import requests
from transformers import pipeline, AutoTokenizer, AutoModelForCausalLM
import torch
import warnings
warnings.filterwarnings('ignore')

class BloomAIAnalyzer:
    def __init__(self):
        """Initialize the Bloom AI Analyzer with model configuration"""
        self.model_name = "bigscience/bloom-560m"  # Using smaller model for faster inference
        self.tokenizer = None
        self.model = None
        self.generator = None
        self.max_length = 512
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        # Initialize model on first use to save memory
        self._model_loaded = False
    
    def load_model(self):
        """Load the Bloom model and tokenizer"""
        if self._model_loaded:
            return
            
        try:
            print(f"Loading Bloom model: {self.model_name} on {self.device}...")
            
            # Load tokenizer and model
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                self.model_name,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None
            )
            
            # Create text generation pipeline
            self.generator = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=0 if self.device == "cuda" else -1,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
            )
            
            self._model_loaded = True
            print("✅ Bloom model loaded successfully!")
            
        except Exception as e:
            print(f"❌ Error loading Bloom model: {e}")
            # Fallback to a simpler approach or mock responses
            self._model_loaded = False
            raise e
    
    def analyze_dataframe_basic(self, df):
        """Generate basic statistical analysis of the dataframe"""
        analysis = {
            'shape': df.shape,
            'columns': list(df.columns),
            'dtypes': df.dtypes.to_dict(),
            'null_counts': df.isnull().sum().to_dict(),
            'numeric_summary': {},
            'categorical_summary': {}
        }
        
        # Numeric columns analysis
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            analysis['numeric_summary'][col] = {
                'mean': float(df[col].mean()) if not df[col].isnull().all() else None,
                'median': float(df[col].median()) if not df[col].isnull().all() else None,
                'std': float(df[col].std()) if not df[col].isnull().all() else None,
                'min': float(df[col].min()) if not df[col].isnull().all() else None,
                'max': float(df[col].max()) if not df[col].isnull().all() else None
            }
        
        # Categorical columns analysis
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in categorical_cols:
            if len(df[col].dropna()) > 0:
                analysis['categorical_summary'][col] = {
                    'unique_count': int(df[col].nunique()),
                    'top_values': df[col].value_counts().head(5).to_dict()
                }
        
        return analysis
    
    def create_analysis_prompt(self, df, analysis_type, basic_stats):
        """Create a prompt for the Bloom model based on data analysis"""
        
        # Create a concise data summary
        rows, cols = df.shape
        numeric_cols = len(basic_stats['numeric_summary'])
        categorical_cols = len(basic_stats['categorical_summary'])
        
        data_summary = f"Dataset with {rows} rows and {cols} columns ({numeric_cols} numeric, {categorical_cols} categorical)."
        
        # Add column names
        columns_str = ", ".join(df.columns[:10])  # Limit to first 10 columns
        if len(df.columns) > 10:
            columns_str += f" and {len(df.columns) - 10} more"
        
        # Add sample statistics
        stats_summary = ""
        if basic_stats['numeric_summary']:
            first_numeric = list(basic_stats['numeric_summary'].keys())[0]
            stats = basic_stats['numeric_summary'][first_numeric]
            if stats['mean'] is not None:
                stats_summary = f" {first_numeric} ranges from {stats['min']:.2f} to {stats['max']:.2f} (mean: {stats['mean']:.2f})."
        
        # Create analysis-specific prompts
        prompts = {
            'summary': f"Analyze this dataset: {data_summary} Columns: {columns_str}.{stats_summary} Provide a concise summary of what this data represents and its key characteristics.",
            
            'trends': f"Analyze trends in this dataset: {data_summary} Columns: {columns_str}.{stats_summary} Identify patterns, trends, and relationships in the data.",
            
            'insights': f"Generate insights from this dataset: {data_summary} Columns: {columns_str}.{stats_summary} What are the most important findings and actionable insights?",
            
            'anomalies': f"Detect anomalies in this dataset: {data_summary} Columns: {columns_str}.{stats_summary} What unusual patterns or outliers should be investigated?",
            
            'correlations': f"Find correlations in this dataset: {data_summary} Columns: {columns_str}.{stats_summary} What relationships exist between different variables?"
        }
        
        return prompts.get(analysis_type, prompts['summary'])
    
    def generate_insights_with_bloom(self, prompt):
        """Generate insights using the Bloom model"""
        if not self._model_loaded:
            self.load_model()
        
        try:
            # Generate text with Bloom
            response = self.generator(
                prompt,
                max_length=self.max_length,
                num_return_sequences=1,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                truncation=True
            )
            
            # Extract generated text (remove the original prompt)
            generated_text = response[0]['generated_text']
            insights = generated_text[len(prompt):].strip()
            
            return insights
            
        except Exception as e:
            print(f"❌ Error generating insights with Bloom: {e}")
            # Fallback to rule-based insights
            return self.generate_fallback_insights(prompt)
    
    def generate_fallback_insights(self, prompt):
        """Generate fallback insights when Bloom model fails"""
        fallback_insights = {
            'summary': "This dataset contains structured data with multiple variables. The data appears to be well-organized with both numerical and categorical features that can provide valuable insights for analysis.",
            
            'trends': "Based on the data structure, there appear to be opportunities to identify patterns across different time periods or categories. Key variables show variation that suggests underlying trends worth investigating.",
            
            'insights': "The dataset shows potential for meaningful analysis. Consider examining relationships between key variables, identifying patterns in categorical data, and investigating distribution patterns in numerical features.",
            
            'anomalies': "Data quality appears generally good based on the structure. However, it would be valuable to investigate any extreme values, missing patterns, or unexpected distributions in key variables.",
            
            'correlations': "The dataset contains multiple variables that may have interesting relationships. Consider exploring correlations between numerical features and examining how categorical variables influence numerical outcomes."
        }
        
        # Simple keyword matching for fallback
        for key, text in fallback_insights.items():
            if key in prompt.lower():
                return text
        
        return fallback_insights['summary']
    
    def analyze_csv_data(self, csv_file_path, analysis_type='summary'):
        """Main method to analyze CSV data and generate AI insights"""
        try:
            # Read CSV file
            print(f"📊 Reading CSV file: {csv_file_path}")
            df = pd.read_csv(csv_file_path)
            
            # Basic analysis
            basic_stats = self.analyze_dataframe_basic(df)
            
            # Create prompt for AI analysis
            prompt = self.create_analysis_prompt(df, analysis_type, basic_stats)
            print(f"🤖 Generating insights for analysis type: {analysis_type}")
            
            # Generate AI insights
            ai_insights = self.generate_insights_with_bloom(prompt)
            
            # Structure the response
            result = {
                'success': True,
                'analysis_type': analysis_type,
                'dataset_info': {
                    'rows': int(df.shape[0]),
                    'columns': int(df.shape[1]),
                    'column_names': list(df.columns),
                    'numeric_columns': len(basic_stats['numeric_summary']),
                    'categorical_columns': len(basic_stats['categorical_summary'])
                },
                'summary': f"Analysis of {df.shape[0]} rows and {df.shape[1]} columns covering: {', '.join(df.columns[:5])}{'...' if len(df.columns) > 5 else ''}",
                'insights': ai_insights,
                'recommendations': self.generate_recommendations(df, basic_stats, analysis_type),
                'metadata': {
                    'timestamp': datetime.now().isoformat(),
                    'model': self.model_name,
                    'analysis_type': analysis_type,
                    'device': self.device
                }
            }
            
            return result
            
        except Exception as e:
            print(f"❌ Error in analyze_csv_data: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def generate_recommendations(self, df, basic_stats, analysis_type):
        """Generate recommendations based on data analysis"""
        recommendations = []
        
        # Data quality recommendations
        null_cols = [col for col, count in basic_stats['null_counts'].items() if count > 0]
        if null_cols:
            recommendations.append(f"Consider handling missing values in columns: {', '.join(null_cols[:3])}")
        
        # Data exploration recommendations
        if basic_stats['numeric_summary']:
            recommendations.append("Examine distributions of numerical variables for outliers and patterns")
        
        if basic_stats['categorical_summary']:
            recommendations.append("Analyze categorical variables for imbalanced classes or unusual patterns")
        
        # Analysis-specific recommendations
        if analysis_type == 'correlations':
            recommendations.append("Create correlation matrices and scatter plots to visualize relationships")
        elif analysis_type == 'trends':
            recommendations.append("Consider time-series analysis if temporal data is available")
        elif analysis_type == 'anomalies':
            recommendations.append("Apply statistical tests or machine learning methods for anomaly detection")
        
        return "\\n\\n".join([f"• {rec}" for rec in recommendations])

def main():
    """Main function to handle command line arguments"""
    if len(sys.argv) != 3:
        print("Usage: python bloom_analyzer.py <csv_file_path> <analysis_type>")
        sys.exit(1)
    
    csv_file_path = sys.argv[1]
    analysis_type = sys.argv[2]
    
    # Initialize analyzer
    analyzer = BloomAIAnalyzer()
    
    # Analyze data
    result = analyzer.analyze_csv_data(csv_file_path, analysis_type)
    
    # Output JSON result
    print("RESULT_JSON:", json.dumps(result))

if __name__ == "__main__":
    main()