"""
LangGraph-based AI Insights Generator
Uses a state graph for robust, traceable data analysis
"""

import pandas as pd
import json
import sys
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
from transformers import pipeline
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Define State using TypedDict for type safety
class AnalysisState(TypedDict):
    """State for the analysis workflow"""
    csv_path: str
    df: Any  # DataFrame
    analysis_type: str
    metadata: dict
    basic_stats: dict
    insights: dict
    recommendations: list
    error: str | None


def load_and_validate(state: AnalysisState) -> AnalysisState:
    """Load CSV and validate data"""
    logger.info(f"Loading CSV from {state['csv_path']}")
    try:
        df = pd.read_csv(state['csv_path'])
        state['df'] = df
        state['error'] = None
        logger.info(f"Successfully loaded CSV with {len(df)} rows and {len(df.columns)} columns")
    except Exception as e:
        logger.error(f"Failed to load CSV: {str(e)}")
        state['error'] = f"CSV loading failed: {str(e)}"
    
    return state


def extract_metadata(state: AnalysisState) -> AnalysisState:
    """Extract basic metadata from DataFrame"""
    if state['error']:
        return state
    
    logger.info("Extracting metadata...")
    try:
        df = state['df']
        metadata = {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": list(df.columns),
            "data_types": df.dtypes.to_dict(),
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": df.duplicated().sum(),
            "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }
        state['metadata'] = metadata
        logger.info(f"Metadata extracted: {metadata['row_count']} rows, {metadata['column_count']} columns")
    except Exception as e:
        logger.error(f"Metadata extraction failed: {str(e)}")
        state['error'] = f"Metadata extraction failed: {str(e)}"
    
    return state


def generate_statistics(state: AnalysisState) -> AnalysisState:
    """Generate statistical summary"""
    if state['error']:
        return state
    
    logger.info("Generating statistics...")
    try:
        df = state['df']
        
        # Numerical statistics
        numeric_cols = df.select_dtypes(include=['number']).columns
        numeric_stats = {}
        for col in numeric_cols:
            numeric_stats[col] = {
                "mean": float(df[col].mean()) if pd.notna(df[col].mean()) else None,
                "median": float(df[col].median()) if pd.notna(df[col].median()) else None,
                "std": float(df[col].std()) if pd.notna(df[col].std()) else None,
                "min": float(df[col].min()) if pd.notna(df[col].min()) else None,
                "max": float(df[col].max()) if pd.notna(df[col].max()) else None,
            }
        
        # Categorical statistics
        categorical_cols = df.select_dtypes(include=['object']).columns
        categorical_stats = {}
        for col in categorical_cols:
            categorical_stats[col] = {
                "unique_count": int(df[col].nunique()),
                "top_value": str(df[col].value_counts().index[0]) if len(df[col].value_counts()) > 0 else None,
                "top_value_count": int(df[col].value_counts().iloc[0]) if len(df[col].value_counts()) > 0 else None,
            }
        
        state['basic_stats'] = {
            "numeric": numeric_stats,
            "categorical": categorical_stats,
            "date_columns": list(df.select_dtypes(include=['datetime']).columns),
        }
        
        logger.info("Statistics generated successfully")
    except Exception as e:
        logger.error(f"Statistics generation failed: {str(e)}")
        state['error'] = f"Statistics generation failed: {str(e)}"
    
    return state


def generate_ai_insights(state: AnalysisState) -> AnalysisState:
    """Generate AI-powered insights using statistical analysis"""
    if state['error']:
        return state
    
    analysis_type = state.get('analysis_type', 'summary')
    logger.info(f"Generating AI insights for analysis type: {analysis_type}")
    
    try:
        df = state['df']
        metadata = state['metadata']
        stats = state['basic_stats']
        
        numeric_stats = stats.get('numeric', {})
        categorical_stats = stats.get('categorical', {})
        
        # Calculate data quality
        missing_vals = metadata.get('missing_values', {})
        total_missing = sum(v for v in missing_vals.values() if isinstance(v, (int, float)))
        total_cells = metadata.get('row_count', 1) * metadata.get('column_count', 1)
        data_quality = (1 - (total_missing / total_cells)) * 100 if total_cells > 0 else 100
        
        insights_text = ""
        
        # Generate different insights based on analysis type
        if analysis_type == 'summary':
            insights_text = generate_summary_insights(df, metadata, numeric_stats, categorical_stats, data_quality)
        elif analysis_type == 'trends':
            insights_text = generate_trends_insights(df, metadata, numeric_stats, categorical_stats)
        elif analysis_type == 'insights':
            insights_text = generate_key_insights(df, metadata, numeric_stats, categorical_stats)
        elif analysis_type == 'anomalies':
            insights_text = generate_anomaly_insights(df, metadata, numeric_stats, categorical_stats)
        elif analysis_type == 'correlations':
            insights_text = generate_correlation_insights(df, metadata, numeric_stats)
        else:
            insights_text = generate_summary_insights(df, metadata, numeric_stats, categorical_stats, data_quality)
        
        logger.info(f"{analysis_type.capitalize()} insights generated successfully")
        
        state['insights'] = {
            "analysis_type": analysis_type,
            "summary": insights_text,
            "data_quality_score": data_quality,
            "generated_at": pd.Timestamp.now().isoformat(),
            "method": "statistical_analysis"
        }
        
    except Exception as e:
        logger.error(f"AI insights generation failed: {str(e)}")
        state['error'] = f"AI insights generation failed: {str(e)}"
    
    return state


def generate_summary_insights(df, metadata, numeric_stats, categorical_stats, data_quality):
    """Generate summary overview insights"""
    insights = []
    insights.append("📊 DATASET SUMMARY")
    insights.append(f"Total Records: {metadata['row_count']:,} rows × {metadata['column_count']} columns")
    insights.append(f"Data Quality Score: {data_quality:.1f}%")
    
    if metadata.get('duplicate_rows', 0) > 0:
        insights.append(f"⚠️ Found {metadata['duplicate_rows']} duplicate rows")
    
    insights.append("\n📈 NUMERIC FEATURES:")
    if numeric_stats:
        for col, stats in list(numeric_stats.items())[:5]:  # Top 5
            insights.append(f"  • {col}: {stats['min']:.2f} to {stats['max']:.2f} (avg: {stats['mean']:.2f})")
    else:
        insights.append("  No numeric columns detected")
    
    insights.append("\n📝 CATEGORICAL FEATURES:")
    if categorical_stats:
        for col, stats in list(categorical_stats.items())[:5]:  # Top 5
            insights.append(f"  • {col}: {stats['unique_count']} unique values, top = '{stats['top_value']}'")
    else:
        insights.append("  No categorical columns detected")
    
    return "\n".join(insights)


def generate_trends_insights(df, metadata, numeric_stats, categorical_stats):
    """Generate trends and patterns insights"""
    insights = []
    insights.append("📈 TRENDS & PATTERNS ANALYSIS")
    
    if numeric_stats:
        insights.append("\n🔢 Numeric Trends:")
        for col, stats in numeric_stats.items():
            range_val = stats['max'] - stats['min']
            mean = stats['mean']
            std = stats['std']
            
            if std > 0:
                cv = (std / mean * 100) if mean != 0 else 0
                if cv > 50:
                    insights.append(f"  • {col}: HIGH variability (CV={cv:.1f}%), check for outliers")
                elif cv < 10:
                    insights.append(f"  • {col}: STABLE trend (CV={cv:.1f}%), consistent values")
                else:
                    insights.append(f"  • {col}: MODERATE variability (CV={cv:.1f}%)")
            
            # Skewness indicator
            if mean > stats['median']:
                insights.append(f"    → Right-skewed distribution (mean > median)")
            elif mean < stats['median']:
                insights.append(f"    → Left-skewed distribution (mean < median)")
    else:
        insights.append("\n🔢 No numeric columns available for trend analysis")
    
    if categorical_stats:
        insights.append("\n📊 Categorical Distribution Patterns:")
        for col, stats in categorical_stats.items():
            unique = stats['unique_count']
            total = metadata['row_count']
            top_count = stats.get('top_value_count', 0)
            concentration = (top_count / total * 100) if total > 0 else 0
            
            if concentration > 70:
                insights.append(f"  • {col}: HIGHLY concentrated - '{stats['top_value']}' dominates ({concentration:.1f}%)")
            elif unique / total > 0.9:
                insights.append(f"  • {col}: HIGHLY diverse - {unique} unique values (nearly all unique)")
            else:
                insights.append(f"  • {col}: BALANCED distribution - {unique} categories")
    
    return "\n".join(insights)


def generate_key_insights(df, metadata, numeric_stats, categorical_stats):
    """Generate key business insights and takeaways"""
    insights = []
    insights.append("💡 KEY INSIGHTS & BUSINESS TAKEAWAYS")
    
    # Data completeness insight
    missing = metadata.get('missing_values', {})
    cols_with_missing = sum(1 for v in missing.values() if v > 0)
    if cols_with_missing > 0:
        insights.append(f"\n⚠️ Data Completeness Issue:")
        insights.append(f"  • {cols_with_missing} columns have missing values")
        top_missing = sorted([(k, v) for k, v in missing.items() if v > 0], key=lambda x: x[1], reverse=True)[:3]
        for col, count in top_missing:
            pct = (count / metadata['row_count'] * 100) if metadata['row_count'] > 0 else 0
            insights.append(f"  • {col}: {count} missing ({pct:.1f}%)")
    else:
        insights.append("\n✅ Complete Dataset: No missing values detected")
    
    # Numeric insights
    if numeric_stats:
        insights.append("\n📊 Numeric Feature Insights:")
        for col, stats in list(numeric_stats.items())[:4]:
            mean = stats['mean']
            median = stats['median']
            if abs(mean - median) / (mean + 0.001) > 0.2:
                insights.append(f"  • {col}: Asymmetric distribution (investigate outliers)")
            else:
                insights.append(f"  • {col}: Well-balanced distribution")
    
    # Categorical insights
    if categorical_stats:
        insights.append("\n🏷️ Categorical Feature Insights:")
        for col, stats in list(categorical_stats.items())[:4]:
            cardinality = stats['unique_count']
            if cardinality == 1:
                insights.append(f"  • {col}: CONSTANT value - consider removing")
            elif cardinality == metadata['row_count']:
                insights.append(f"  • {col}: UNIQUE identifier - potential primary key")
            elif cardinality < 10:
                insights.append(f"  • {col}: LOW cardinality ({cardinality}) - good for grouping")
            else:
                insights.append(f"  • {col}: MEDIUM-HIGH cardinality ({cardinality})")
    
    return "\n".join(insights)


def generate_anomaly_insights(df, metadata, numeric_stats, categorical_stats):
    """Generate anomaly and outlier detection insights"""
    insights = []
    insights.append("🔍 ANOMALY & OUTLIER DETECTION")
    
    if numeric_stats:
        insights.append("\n📉 Numeric Anomalies:")
        for col, stats in numeric_stats.items():
            mean = stats['mean']
            std = stats['std']
            min_val = stats['min']
            max_val = stats['max']
            
            if std > 0:
                # Z-score based outlier detection
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
                
                outliers_likely = []
                if min_val < lower_bound:
                    outliers_likely.append(f"minimum ({min_val:.2f}) is {abs(min_val - lower_bound):.2f} below expected")
                if max_val > upper_bound:
                    outliers_likely.append(f"maximum ({max_val:.2f}) is {abs(max_val - upper_bound):.2f} above expected")
                
                if outliers_likely:
                    insights.append(f"  ⚠️ {col}: Potential outliers detected")
                    for outlier in outliers_likely:
                        insights.append(f"      → {outlier}")
                else:
                    insights.append(f"  ✓ {col}: No extreme outliers detected")
            else:
                insights.append(f"  • {col}: Constant value (no variation)")
    else:
        insights.append("\n📉 No numeric columns available for outlier detection")
    
    # Missing value patterns
    missing = metadata.get('missing_values', {})
    if any(v > 0 for v in missing.values()):
        insights.append("\n🕳️ Missing Value Patterns:")
        for col, count in missing.items():
            if count > 0:
                pct = (count / metadata['row_count'] * 100)
                if pct > 50:
                    insights.append(f"  ⚠️ CRITICAL: {col} has {pct:.1f}% missing - consider dropping")
                elif pct > 20:
                    insights.append(f"  ⚠️ HIGH: {col} has {pct:.1f}% missing - imputation needed")
                elif pct > 5:
                    insights.append(f"  ⚠️ MODERATE: {col} has {pct:.1f}% missing")
    
    # Check for duplicate rows
    dupes = metadata.get('duplicate_rows', 0)
    if dupes > 0:
        dup_pct = (dupes / metadata['row_count'] * 100)
        insights.append(f"\n🔄 Duplicate Rows: {dupes} ({dup_pct:.1f}%) - review and remove if necessary")
    else:
        insights.append("\n✅ No duplicate rows detected")
    
    return "\n".join(insights)


def generate_correlation_insights(df, metadata, numeric_stats):
    """Generate correlation and relationship insights"""
    insights = []
    insights.append("🔗 CORRELATION & RELATIONSHIPS ANALYSIS")
    
    if len(numeric_stats) < 2:
        insights.append("\nInsufficient numeric columns for correlation analysis (need at least 2)")
        return "\n".join(insights)
    
    try:
        # Calculate correlation matrix
        numeric_cols = list(numeric_stats.keys())
        corr_matrix = df[numeric_cols].corr()
        
        insights.append(f"\n📊 Correlation Matrix computed for {len(numeric_cols)} numeric features")
        
        # Find strong correlations
        strong_correlations = []
        for i in range(len(numeric_cols)):
            for j in range(i + 1, len(numeric_cols)):
                corr_val = corr_matrix.iloc[i, j]
                if abs(corr_val) > 0.7:
                    strength = "STRONG positive" if corr_val > 0 else "STRONG negative"
                    strong_correlations.append((numeric_cols[i], numeric_cols[j], corr_val, strength))
                elif abs(corr_val) > 0.5:
                    strength = "MODERATE positive" if corr_val > 0 else "MODERATE negative"
                    strong_correlations.append((numeric_cols[i], numeric_cols[j], corr_val, strength))
        
        if strong_correlations:
            insights.append("\n🔗 Notable Correlations Found:")
            for col1, col2, corr, strength in sorted(strong_correlations, key=lambda x: abs(x[2]), reverse=True)[:8]:
                insights.append(f"  • {col1} ↔ {col2}: {strength} (r={corr:.3f})")
        else:
            insights.append("\n✓ No strong correlations detected (all |r| < 0.5)")
            insights.append("  → Features appear to be independent")
        
        # Identify potential redundancy
        redundant = [x for x in strong_correlations if abs(x[2]) > 0.95]
        if redundant:
            insights.append("\n⚠️ Potential Redundant Features:")
            for col1, col2, corr, _ in redundant:
                insights.append(f"  • {col1} and {col2} (r={corr:.3f}) - consider removing one")
        
        # Find uncorrelated features
        avg_correlations = corr_matrix.abs().mean()
        weakly_correlated = [col for col in numeric_cols if avg_correlations[col] < 0.2]
        if weakly_correlated:
            insights.append("\n🔓 Weakly Correlated Features (potential independent predictors):")
            for col in weakly_correlated[:5]:
                insights.append(f"  • {col}")
    
    except Exception as e:
        insights.append(f"\n⚠️ Correlation computation failed: {str(e)}")
    
    return "\n".join(insights)


def generate_recommendations(state: AnalysisState) -> AnalysisState:
    """Generate recommendations based on analysis type"""
    if state['error']:
        return state
    
    analysis_type = state.get('analysis_type', 'summary')
    logger.info(f"Generating recommendations for {analysis_type} analysis...")
    
    try:
        metadata = state['metadata']
        stats = state['basic_stats']
        
        recommendations = []
        
        if analysis_type == 'summary':
            recommendations = [
                "✓ Perform detailed exploratory data analysis (EDA) on key features",
                "✓ Create visualizations for numeric and categorical distributions",
                "✓ Document data dictionary with column descriptions and units",
                "✓ Validate data types and convert if necessary",
                "✓ Consider creating derived features for deeper insights"
            ]
        
        elif analysis_type == 'trends':
            recommendations = [
                "✓ Create time-series plots if temporal data exists",
                "✓ Apply moving averages to smooth out short-term fluctuations",
                "✓ Use trend decomposition (trend, seasonal, residual)",
                "✓ Identify seasonality patterns in your data",
                "✓ Monitor features with high variability for stability"
            ]
        
        elif analysis_type == 'insights':
            recommendations = [
                "✓ Focus on features with business impact potential",
                "✓ Investigate asymmetric distributions for root causes",
                "✓ Perform cohort analysis on categorical segments",
                "✓ Create dashboards for stakeholder communication",
                "✓ Document key findings and share with decision-makers"
            ]
        
        elif analysis_type == 'anomalies':
            recommendations = [
                "✓ Apply robust outlier detection methods (IQR, Z-score, Isolation Forest)",
                "✓ Investigate root causes of detected anomalies",
                "✓ Decide whether to remove, cap, or keep outliers based on context",
                "✓ Implement data validation rules to prevent future anomalies",
                "✓ Use robust statistics (median, MAD) instead of mean/std for outlier-prone data"
            ]
        
        elif analysis_type == 'correlations':
            recommendations = [
                "✓ Remove highly correlated features to reduce multicollinearity",
                "✓ Use correlation insights for feature selection in modeling",
                "✓ Investigate causal relationships behind strong correlations",
                "✓ Consider dimensionality reduction (PCA) if many correlated features",
                "✓ Build predictive models using identified relationships"
            ]
        
        # Add missing value recommendations if applicable
        missing_vals = metadata.get('missing_values', {})
        if any(v > 0 for v in missing_vals.values()):
            recommendations.append("⚠️ Address missing values using imputation or removal strategies")
        
        # Add duplicate recommendations if applicable
        if metadata.get('duplicate_rows', 0) > 0:
            recommendations.append("⚠️ Review and remove duplicate rows if they are errors")
        
        state['recommendations'] = recommendations
        logger.info(f"Generated {len(recommendations)} recommendations for {analysis_type}")
        
    except Exception as e:
        logger.error(f"Recommendation generation failed: {str(e)}")
        state['error'] = f"Recommendation generation failed: {str(e)}"
    
    return state


def format_output(state: AnalysisState) -> AnalysisState:
    """Format the final output"""
    logger.info("Formatting output...")
    
    if state['error']:
        logger.error(f"Analysis failed with error: {state['error']}")
        return state
    
    # Final state is ready
    logger.info("Analysis complete!")
    return state


def create_analysis_graph():
    """Create the LangGraph state graph for analysis"""
    
    # Initialize graph with our state
    graph = StateGraph(AnalysisState)
    
    # Add nodes
    graph.add_node("load_validate", load_and_validate)
    graph.add_node("extract_metadata", extract_metadata)
    graph.add_node("generate_stats", generate_statistics)
    graph.add_node("ai_insights", generate_ai_insights)
    graph.add_node("recommendations", generate_recommendations)
    graph.add_node("format_output", format_output)
    
    # Add edges (workflow)
    graph.add_edge(START, "load_validate")
    graph.add_edge("load_validate", "extract_metadata")
    graph.add_edge("extract_metadata", "generate_stats")
    graph.add_edge("generate_stats", "ai_insights")
    graph.add_edge("ai_insights", "recommendations")
    graph.add_edge("recommendations", "format_output")
    graph.add_edge("format_output", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    return compiled_graph


def analyze_csv(csv_path: str, analysis_type: str = 'summary') -> dict:
    """Main function to run the analysis"""
    
    logger.info(f"Starting analysis for {csv_path} with type {analysis_type}")
    
    # Create and run the graph
    graph = create_analysis_graph()
    
    # Initial state
    initial_state: AnalysisState = {
        "csv_path": csv_path,
        "df": None,
        "analysis_type": analysis_type,
        "metadata": {},
        "basic_stats": {},
        "insights": {},
        "recommendations": [],
        "error": None,
    }
    
    # Run the graph
    try:
        final_state = graph.invoke(initial_state)
        
        # Prepare result
        result = {
            "success": final_state['error'] is None,
            "error": final_state['error'],
            "metadata": final_state['metadata'],
            "statistics": final_state['basic_stats'],
            "insights": final_state['insights'],
            "recommendations": final_state['recommendations'],
            "analysis_type": analysis_type,
        }
        
        logger.info("Analysis completed successfully")
        return result
    
    except Exception as e:
        logger.error(f"Graph execution failed: {str(e)}")
        return {
            "success": False,
            "error": f"Graph execution failed: {str(e)}",
            "metadata": {},
            "statistics": {},
            "insights": {},
            "recommendations": [],
        }


if __name__ == "__main__":
    # Handle command line arguments
    if len(sys.argv) < 2:
        print("Usage: python langgraph_analyzer.py <csv_path> [analysis_type]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    analysis_type = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    
    # Run analysis
    result = analyze_csv(csv_file, analysis_type)
    
    # Output result as JSON
    print("RESULT_JSON:" + json.dumps(result, default=str))
