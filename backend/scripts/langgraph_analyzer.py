"""
LangGraph-based AI Insights Generator
Uses a state graph for robust, traceable data analysis
"""

import pandas as pd
import json
import sys
import os
import time
from pathlib import Path
from typing import TypedDict, Any
from langgraph.graph import StateGraph, START, END
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# LLM Integration (optional - only needed for 'chat' mode)
ChatOpenAI = None
ChatGoogleGenerativeAI = None

try:
    from langchain_openai import ChatOpenAI as _ChatOpenAI
    ChatOpenAI = _ChatOpenAI
except ImportError:
    logger.info("langchain-openai not installed; OpenAI/Azure/GitHub providers disabled.")

try:
    from langchain_google_genai import ChatGoogleGenerativeAI as _ChatGoogleGenerativeAI  # type: ignore
    ChatGoogleGenerativeAI = _ChatGoogleGenerativeAI
except ImportError:
    logger.info("langchain-google-genai not installed; Gemini provider disabled.")

LLM_AVAILABLE = ChatOpenAI is not None or ChatGoogleGenerativeAI is not None

if not LLM_AVAILABLE:
    logger.warning("No LLM providers available. Install langchain-openai or langchain-google-genai to enable chat mode.")

# Security and resource configuration
MAX_FILE_SIZE_MB = 100  # Maximum file size in megabytes
MAX_ROWS_TO_READ = 100000  # Maximum rows to read from CSV
CHUNK_SIZE = 10000  # Rows per chunk for large file processing
# Allowed base directory (backend/uploads)
ALLOWED_BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'uploads'))


def _format_count(count: int) -> str:
    return f"{count:,}"


def maybe_answer_locally(question: str, metadata: dict, stats: dict) -> str | None:
    """Return a deterministic answer for common dataset questions without calling an LLM."""
    if not question:
        return None

    q = question.lower().strip()
    missing_values = metadata.get('missing_values') or {}
    duplicate_rows = metadata.get('duplicate_rows')
    row_count = metadata.get('row_count')
    column_count = metadata.get('column_count')
    column_names = metadata.get('columns') or []

    if 'missing' in q or 'null' in q:
        columns_with_missing = {col: cnt for col, cnt in missing_values.items() if cnt and cnt > 0}
        if columns_with_missing:
            lines = ["I checked the dataset for missing values:"]
            for col, cnt in sorted(columns_with_missing.items(), key=lambda item: item[1], reverse=True):
                lines.append(f"• {col}: {_format_count(cnt)} missing values")
            return "\n".join(lines)
        if missing_values:
            return "Good news—none of the columns contain missing values."
        return None

    if 'duplicate' in q:
        if duplicate_rows is None:
            return None
        if duplicate_rows == 0:
            return "No duplicate rows detected in the dataset."
        return f"There are {_format_count(int(duplicate_rows))} duplicate rows in the dataset."

    if ('how many' in q or 'number of' in q or 'count of' in q) and 'row' in q:
        if row_count is None:
            return None
        return f"The dataset contains {_format_count(int(row_count))} rows."

    if ('how many' in q or 'number of' in q or 'count of' in q) and 'column' in q:
        if column_count is None:
            return None
        return f"The dataset includes {int(column_count)} columns."

    if ('list' in q or 'show' in q or 'what are' in q) and 'column' in q:
        if not column_names:
            return None
        preview = ", ".join(column_names[:20])
        more = "" if len(column_names) <= 20 else f" (and {len(column_names) - 20} more)"
        return f"Column names: {preview}{more}."

    if 'average' in q and 'age' in q and 'age' in stats.get('numeric', {}):
        mean_age = stats['numeric']['Age'].get('mean')
        if mean_age is not None:
            return f"The average Age is {safe_format(mean_age)} years."

    return None


def build_fallback_answer(question: str, metadata: dict, stats: dict, provider_errors: list[dict]) -> str:
    """Construct a graceful fallback response when all LLM calls fail."""
    lines = [
        "I couldn’t reach the language model right now, so here’s what I can tell you directly from the data:",
        f"• Rows: {_format_count(metadata.get('row_count', 0))}",
        f"• Columns: {_format_count(metadata.get('column_count', 0))}",
        f"• Duplicate rows: {_format_count(metadata.get('duplicate_rows', 0))}",
    ]

    missing_values = metadata.get('missing_values') or {}
    columns_with_missing = {col: cnt for col, cnt in missing_values.items() if cnt and cnt > 0}
    if columns_with_missing:
        lines.append("• Columns with missing values:")
        for col, cnt in sorted(columns_with_missing.items(), key=lambda item: item[1], reverse=True):
            lines.append(f"  - {col}: {_format_count(cnt)}")
    else:
        lines.append("• No missing values detected in the current dataset sample.")

    if provider_errors:
        unique_codes = sorted({err.get('code') for err in provider_errors if err.get('code')})
        if unique_codes:
            lines.append("• LLM error codes encountered: " + ", ".join(unique_codes))

    if question:
        lines.append("\nIf you still need a conversational explanation, try again in a bit or switch providers using LLM_PROVIDER.")

    return "\n".join(lines)


# Helper function for safe numeric formatting
def safe_format(value, format_spec=".2f", placeholder="N/A"):
    """Safely format numeric values, returning placeholder if None"""
    if value is None:
        return placeholder
    try:
        return f"{value:{format_spec}}"
    except (ValueError, TypeError):
        return placeholder


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
    # For chat mode
    user_question: str
    llm_response: str


def load_and_validate(state: AnalysisState) -> AnalysisState:
    """Load CSV and validate data with comprehensive security checks"""
    csv_path = state['csv_path']
    logger.info(f"Starting validation for CSV path: {csv_path}")
    
    try:
        # Step 1: Resolve to absolute path
        try:
            absolute_path = os.path.abspath(csv_path)
            logger.info(f"Resolved absolute path: {absolute_path}")
        except Exception as e:
            error_msg = f"Path resolution failed: {str(e)}"
            logger.error(error_msg)
            state['error'] = error_msg
            return state
        
        # Step 2: Ensure path is inside allowed base directory (prevent path traversal)
        try:
            # Resolve both paths to handle symlinks and relative paths
            resolved_file = Path(absolute_path).resolve()
            resolved_base = Path(ALLOWED_BASE_DIR).resolve()
            
            # Check if file path starts with base directory
            if not str(resolved_file).startswith(str(resolved_base)):
                error_msg = f"Security violation: File path '{resolved_file}' is outside allowed directory '{resolved_base}'"
                logger.error(error_msg)
                state['error'] = error_msg
                return state
            
            logger.info(f"Path validation passed: file is within allowed directory")
        except Exception as e:
            error_msg = f"Path security check failed: {str(e)}"
            logger.error(error_msg)
            state['error'] = error_msg
            return state
        
        # Step 3: Check file exists
        if not os.path.exists(absolute_path):
            error_msg = f"File not found: {absolute_path}"
            logger.error(error_msg)
            state['error'] = error_msg
            return state
        
        # Step 4: Check it's a regular file (not directory, symlink, etc.)
        if not os.path.isfile(absolute_path):
            error_msg = f"Path is not a regular file: {absolute_path}"
            logger.error(error_msg)
            state['error'] = error_msg
            return state
        
        logger.info("File existence and type validation passed")
        
        # Step 5: Check file size
        file_size_bytes = os.path.getsize(absolute_path)
        file_size_mb = file_size_bytes / (1024 * 1024)
        logger.info(f"File size: {file_size_mb:.2f} MB")
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            error_msg = f"File too large: {file_size_mb:.2f} MB exceeds maximum of {MAX_FILE_SIZE_MB} MB"
            logger.error(error_msg)
            state['error'] = error_msg
            return state
        
        # Step 6: Read CSV with appropriate strategy based on size
        # For files > 10MB, use chunked reading or row limits
        if file_size_mb > 10:
            logger.info(f"Large file detected ({file_size_mb:.2f} MB), reading with row limit")
            try:
                # Read in chunks and concatenate up to MAX_ROWS_TO_READ
                chunks = []
                total_rows = 0
                
                for chunk in pd.read_csv(absolute_path, chunksize=CHUNK_SIZE):
                    chunks.append(chunk)
                    total_rows += len(chunk)
                    
                    if total_rows >= MAX_ROWS_TO_READ:
                        logger.warning(f"Row limit reached: reading first {MAX_ROWS_TO_READ} rows only")
                        break
                
                df = pd.concat(chunks, ignore_index=True)
                
                # Trim to exact limit if we overshot
                if len(df) > MAX_ROWS_TO_READ:
                    df = df.head(MAX_ROWS_TO_READ)
                
                logger.info(f"Successfully loaded {len(df)} rows from large file")
                
            except Exception as e:
                error_msg = f"Failed to read large CSV file: {str(e)}"
                logger.error(error_msg)
                state['error'] = error_msg
                return state
        else:
            # For smaller files, read normally but still enforce row limit
            logger.info(f"Reading file normally (size: {file_size_mb:.2f} MB)")
            try:
                df = pd.read_csv(absolute_path, nrows=MAX_ROWS_TO_READ)
                logger.info(f"Successfully loaded {len(df)} rows")
            except Exception as e:
                error_msg = f"Failed to read CSV file: {str(e)}"
                logger.error(error_msg)
                state['error'] = error_msg
                return state
        
        # All validation passed, update state
        state['df'] = df
        state['error'] = None
        logger.info(f"CSV validation complete: {len(df)} rows, {len(df.columns)} columns")
        
    except Exception as e:
        # Catch-all for any unexpected errors
        error_msg = f"Unexpected error during CSV loading: {str(e)}"
        logger.error(error_msg)
        state['error'] = error_msg
    
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
            "data_types": {col: str(dtype) for col, dtype in df.dtypes.to_dict().items()},
            "missing_values": df.isnull().sum().to_dict(),
            "duplicate_rows": int(df.duplicated().sum()),
            "memory_usage_mb": float(df.memory_usage(deep=True).sum() / 1024 / 1024),
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
        elif analysis_type == 'chat':
            # For chat mode, call the LLM function instead
            logger.info("Chat mode detected - will use LLM for interactive Q&A")
            state['insights'] = {
                "analysis_type": "chat",
                "method": "llm_powered"
            }
            return state  # LLM processing happens in answer_question_with_llm node
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
        dup_count = metadata['duplicate_rows']
        dup_pct = (dup_count / metadata['row_count'] * 100) if metadata['row_count'] > 0 else 0
        insights.append(f"⚠️ Found {dup_count} duplicate rows ({dup_pct:.1f}%)")
    
    if numeric_stats:
        insights.append(f"\n📊 Numeric Features: {len(numeric_stats)} columns")
    if categorical_stats:
        insights.append(f"🏷️ Categorical Features: {len(categorical_stats)} columns")
    
    return "\n".join(insights)


def generate_trends_insights(df, metadata, numeric_stats, categorical_stats):
    """Generate trend and variability insights"""
    insights = []
    insights.append("📈 TRENDS & VARIABILITY ANALYSIS")
    
    if numeric_stats:
        insights.append("\n📊 Coefficient of Variation (CV) Analysis:")
        for col, stats in list(numeric_stats.items())[:6]:
            mean = stats.get('mean')
            std = stats.get('std')
            
            # Skip if mean or std is None
            if mean is None or std is None:
                insights.append(f"  • {col}: Insufficient data for variability analysis")
                continue
            
            if abs(mean) < 0.0001:  # Avoid division by zero
                insights.append(f"  • {col}: Mean near zero, CV not meaningful")
                continue
                
            cv = (std / abs(mean)) * 100
            if cv < 10:
                insights.append(f"  • {col}: LOW variability (CV={safe_format(cv, '.1f')}%) - stable feature")
            elif cv < 30:
                insights.append(f"  • {col}: MODERATE variability (CV={safe_format(cv, '.1f')}%)")
            else:
                insights.append(f"  • {col}: HIGH variability (CV={safe_format(cv, '.1f')}%) - volatile feature")
    else:
        insights.append("\n📊 No numeric columns available for trend analysis")
    
    return "\n".join(insights)


def generate_anomaly_insights(df, metadata, numeric_stats, categorical_stats):
    """Generate anomaly and outlier detection insights"""
    insights = []
    insights.append("🔍 ANOMALY & OUTLIER DETECTION")
    
    if numeric_stats:
        insights.append("\n📉 Numeric Anomalies:")
        for col, stats in numeric_stats.items():
            mean = stats.get('mean')
            std = stats.get('std')
            min_val = stats.get('min')
            max_val = stats.get('max')
            
            # Skip if essential stats are missing
            if mean is None or std is None or min_val is None or max_val is None:
                insights.append(f"  • {col}: Insufficient data for anomaly detection")
                continue
            
            if std > 0:
                # Z-score based outlier detection
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
                
                outliers_likely = []
                if min_val < lower_bound:
                    outliers_likely.append(f"minimum ({safe_format(min_val)}) is {safe_format(abs(min_val - lower_bound))} below expected")
                if max_val > upper_bound:
                    outliers_likely.append(f"maximum ({safe_format(max_val)}) is {safe_format(abs(max_val - upper_bound))} above expected")
                
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
            mean = stats.get('mean')
            median = stats.get('median')
            
            # Skip if mean or median is None
            if mean is None or median is None:
                insights.append(f"  • {col}: Insufficient data for distribution analysis")
                continue
                
            if abs(mean - median) / (abs(mean) + 0.001) > 0.2:
                insights.append(f"  • {col}: Asymmetric distribution (investigate outliers)")
            else:
                insights.append(f"  • {col}: Well-balanced distribution")
    
    # Categorical insights
    if categorical_stats:
        insights.append("\n🏷️ Categorical Feature Insights:")
        for col, stats in list(categorical_stats.items())[:4]:
            cardinality = stats.get('unique_count')
            if cardinality is None:
                insights.append(f"  • {col}: Insufficient data for cardinality analysis")
                continue
                
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
            mean = stats.get('mean')
            std = stats.get('std')
            min_val = stats.get('min')
            max_val = stats.get('max')
            
            # Skip if essential stats are missing
            if mean is None or std is None or min_val is None or max_val is None:
                insights.append(f"  • {col}: Insufficient data for anomaly detection")
                continue
            
            if std > 0:
                # Z-score based outlier detection
                lower_bound = mean - 3 * std
                upper_bound = mean + 3 * std
                
                outliers_likely = []
                if min_val < lower_bound:
                    outliers_likely.append(f"minimum ({safe_format(min_val)}) is {safe_format(abs(min_val - lower_bound))} below expected")
                if max_val > upper_bound:
                    outliers_likely.append(f"maximum ({safe_format(max_val)}) is {safe_format(abs(max_val - upper_bound))} above expected")
                
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


def answer_question_with_llm(state: AnalysisState) -> AnalysisState:
    """
    Use LLM to answer user questions about the dataset.
    This function integrates OpenAI/Azure OpenAI/GitHub Models for interactive Q&A.
    """
    if state['error']:
        return state
    
    if not LLM_AVAILABLE:
        state['error'] = (
            "LLM integration not available. Install langchain-openai and/or langchain-google-genai "
            "to enable chat mode."
        )
        logger.error(state['error'])
        return state
    
    user_question = state.get('user_question', '')
    if not user_question:
        state['error'] = "No question provided for chat mode"
        logger.error(state['error'])
        return state

    if not isinstance(state.get('insights'), dict):
        state['insights'] = {}
    
    logger.info(f"Processing user question: {user_question}")
    
    try:
        # Prepare context about the dataset
        metadata = state['metadata']
        stats = state['basic_stats']
        df = state['df']

        # Try deterministic answer before calling any LLM
        local_answer = maybe_answer_locally(user_question, metadata, stats)
        if local_answer:
            logger.info("Answered question locally without LLM call.")
            state['llm_response'] = local_answer
            state['insights']['chat_response'] = local_answer
            state['insights']['user_question'] = user_question
            state['insights']['method'] = 'rule_based'
            state['insights']['llm_provider'] = 'local'
            state['error'] = None
            return state

        # Get LLM configuration from environment
        # Supports Gemini, OpenAI, Azure OpenAI, and GitHub Models
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_api_key = os.getenv('AZURE_OPENAI_KEY')
        openai_key = os.getenv('OPENAI_API_KEY')
        github_token = os.getenv('GITHUB_TOKEN')
        gemini_api_key = os.getenv('GEMINI_API_KEY')
        provider_override = (os.getenv('LLM_PROVIDER') or '').strip().lower()
        llm_model_override = os.getenv('LLM_MODEL')
        gemini_model_override = os.getenv('GEMINI_MODEL')

        valid_providers = {'gemini', 'azure', 'openai', 'github'}
        providers: list[str] = []

        if provider_override:
            if provider_override not in valid_providers:
                state['error'] = "LLM_PROVIDER must be one of: gemini, azure, openai, github."
                logger.error(state['error'])
                return state
            providers = [provider_override]
        else:
            if gemini_api_key and ChatGoogleGenerativeAI is not None:
                providers.append('gemini')
            elif gemini_api_key and ChatGoogleGenerativeAI is None:
                logger.warning("GEMINI_API_KEY detected but langchain-google-genai is not installed.")

            if azure_endpoint and azure_api_key and ChatOpenAI is not None:
                providers.append('azure')
            elif (azure_endpoint or azure_api_key) and ChatOpenAI is None:
                logger.warning("Azure OpenAI credentials detected but langchain-openai is not installed.")

            if openai_key and ChatOpenAI is not None:
                providers.append('openai')
            elif openai_key and ChatOpenAI is None:
                logger.warning("OPENAI_API_KEY detected but langchain-openai is not installed.")

            if github_token and ChatOpenAI is not None:
                providers.append('github')
            elif github_token and ChatOpenAI is None:
                logger.warning("GITHUB_TOKEN detected but langchain-openai is not installed.")

        if not providers:
            state['error'] = (
                "No LLM credentials detected. Set GEMINI_API_KEY for Gemini, OPENAI_API_KEY for OpenAI, "
                "GITHUB_TOKEN (with models scope) for GitHub Models, or AZURE_OPENAI_* variables for Azure OpenAI."
            )
            logger.error(state['error'])
            return state

        default_models = {
            'gemini': 'gemini-1.5-flash',
            'azure': 'gpt-4o',
            'openai': 'gpt-4o',
            'github': 'gpt-4o',
        }

        # Build dataset summary for LLM context
        missing_values = metadata.get('missing_values', {})
        total_missing = sum(missing_values.values())
        row_count = metadata.get('row_count', 0)
        column_count = metadata.get('column_count', 0)
        total_cells = row_count * column_count if row_count and column_count else 0
        data_quality = metadata.get('data_quality')
        if data_quality is None and total_cells:
            data_quality = (1 - (total_missing / total_cells)) * 100 if total_cells else 100
        data_types = metadata.get('data_types') or metadata.get('column_types', {})

        dataset_context = f"""
Dataset Information:
- Filename: {metadata.get('filename', 'Unknown')}
- Total Rows: {metadata.get('row_count', 0):,}
- Total Columns: {metadata.get('column_count', 0)}
- Data Quality Score: {(data_quality or 0):.1f}%
- Missing Values: {total_missing} total
- Duplicate Rows: {metadata.get('duplicate_rows', 0)}

Columns:
{chr(10).join(f"  - {col} ({dtype})" for col, dtype in data_types.items())}

Numeric Statistics Summary:
"""
        # Add key statistics for numeric columns
        numeric_stats = stats.get('numeric', {})
        for col, col_stats in list(numeric_stats.items())[:10]:  # Limit to first 10
            dataset_context += f"\n  {col}:"
            if col_stats.get('mean') is not None:
                dataset_context += f" mean={safe_format(col_stats['mean'])}"
            if col_stats.get('std') is not None:
                dataset_context += f" std={safe_format(col_stats['std'])}"
            if col_stats.get('min') is not None:
                dataset_context += f" min={safe_format(col_stats['min'])}"
            if col_stats.get('max') is not None:
                dataset_context += f" max={safe_format(col_stats['max'])}"
        
        # Add sample rows for better context (first 5 rows)
        dataset_context += f"\n\nSample Data (first 5 rows):\n{df.head(5).to_string()}"
        
        # Create the prompt
        prompt = f"""{dataset_context}

User Question: {user_question}

Please provide a clear, accurate, and helpful answer based on the dataset information provided above. 
If the question requires calculations or analysis not shown in the statistics, explain what analysis would be needed.
Be specific and reference actual values from the data when possible.
If you cannot answer based on the available information, explain what additional data or analysis would be required."""
        
        provider_errors: list[dict] = []
        llm_answer = None
        used_provider = None

        for provider in providers:
            try:
                if provider == 'gemini':
                    if ChatGoogleGenerativeAI is None:
                        raise RuntimeError("Gemini selected but langchain-google-genai is not installed.")
                    if not gemini_api_key:
                        raise RuntimeError("Gemini selected but GEMINI_API_KEY is missing.")
                    selected_model = gemini_model_override or llm_model_override or default_models['gemini']
                    llm = ChatGoogleGenerativeAI(
                        model=selected_model,
                        temperature=0.3,
                        google_api_key=gemini_api_key,
                    )
                elif provider == 'azure':
                    if not (azure_endpoint and azure_api_key):
                        raise RuntimeError("Azure OpenAI selected but AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_KEY is missing.")
                    llm = ChatOpenAI(
                        azure_endpoint=azure_endpoint,
                        api_key=azure_api_key,
                        api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
                        model=llm_model_override or default_models['azure'],
                        temperature=0.3,
                    )
                elif provider == 'openai':
                    if not openai_key:
                        raise RuntimeError("OpenAI selected but OPENAI_API_KEY is missing.")
                    llm = ChatOpenAI(
                        api_key=openai_key,
                        model=llm_model_override or default_models['openai'],
                        temperature=0.3,
                    )
                else:
                    if not github_token:
                        raise RuntimeError("GitHub Models selected but GITHUB_TOKEN is missing.")
                    llm = ChatOpenAI(
                        base_url="https://models.inference.ai.azure.com",
                        api_key=github_token,
                        model=llm_model_override or default_models['github'],
                        temperature=0.3,
                    )

                logger.info(f"Sending request to LLM provider '{provider}'...")
                response = llm.invoke(prompt)
                llm_answer = response.content
                used_provider = provider
                logger.info(f"LLM response received from {provider} ({len(llm_answer)} characters)")
                break
            except Exception as provider_exc:  # noqa: BLE001
                error_message = str(provider_exc)
                error_code = None
                if 'Error code:' in error_message:
                    try:
                        error_code = error_message.split('Error code:')[1].split()[0]
                    except Exception:  # noqa: BLE001
                        error_code = None
                provider_errors.append({
                    'provider': provider,
                    'message': error_message,
                    'code': error_code,
                })
                logger.warning(f"LLM provider '{provider}' failed: {error_message}")
                if provider != providers[-1]:
                    time.sleep(0.5)

        if llm_answer is None:
            if provider_override:
                final_error = provider_errors[-1] if provider_errors else {'message': 'Unknown LLM error'}
                error_msg = final_error.get('message', 'LLM request failed')
                friendly_message = (
                    f"{provider_override.title()} provider failure: {error_msg}. "
                    "Please verify the credentials or switch providers."
                )
                logger.error(f"Forced provider '{provider_override}' failed without fallback: {error_msg}")

                state['insights']['chat_response'] = friendly_message
                state['insights']['user_question'] = user_question
                state['insights']['method'] = 'provider_error'
                state['insights']['llm_provider'] = provider_override
                state['insights']['llm_errors'] = provider_errors
                state['llm_response'] = friendly_message
                state['error'] = error_msg
                return state

            fallback_answer = build_fallback_answer(user_question, metadata, stats, provider_errors)
            state['llm_response'] = fallback_answer
            state['insights']['chat_response'] = fallback_answer
            state['insights']['user_question'] = user_question
            state['insights']['method'] = 'llm_fallback'
            state['insights']['llm_provider'] = 'fallback'
            state['insights']['llm_errors'] = provider_errors
            state['error'] = None
            logger.error("All LLM providers failed; returned fallback answer.")
            return state

        # Store the successful response
        state['llm_response'] = llm_answer
        state['insights']['chat_response'] = llm_answer
        state['insights']['user_question'] = user_question
        state['insights']['method'] = 'llm_powered'
        state['insights']['llm_provider'] = used_provider
        state['error'] = None
        
        return state
        
    except Exception as e:
        error_msg = f"LLM question answering failed: {str(e)}"
        if 'models' in str(e).lower() and 'permission' in str(e).lower():
            error_msg += " | Hint: GitHub tokens must include the `models` scope to access GitHub Models."
        logger.error(error_msg)
        state['error'] = error_msg
        return state


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
    graph.add_node("llm_chat", answer_question_with_llm)
    graph.add_node("recommendations", generate_recommendations)
    graph.add_node("format_output", format_output)
    
    # Helper function to decide next step after insights
    def route_after_insights(state: AnalysisState):
        """Route to LLM chat if analysis_type is 'chat', otherwise to recommendations"""
        if state.get('analysis_type') == 'chat':
            return "llm_chat"
        return "recommendations"
    
    # Add edges (workflow)
    graph.add_edge(START, "load_validate")
    graph.add_edge("load_validate", "extract_metadata")
    graph.add_edge("extract_metadata", "generate_stats")
    graph.add_edge("generate_stats", "ai_insights")
    
    # Conditional routing: go to LLM chat if chat mode, otherwise recommendations
    graph.add_conditional_edges(
        "ai_insights",
        route_after_insights,
        {
            "llm_chat": "llm_chat",
            "recommendations": "recommendations"
        }
    )
    
    graph.add_edge("llm_chat", "format_output")
    graph.add_edge("recommendations", "format_output")
    graph.add_edge("format_output", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    return compiled_graph


def analyze_csv(csv_path: str, analysis_type: str = 'summary', user_question: str = None) -> dict:
    """
    Main function to run the analysis
    
    Args:
        csv_path: Path to the CSV file
        analysis_type: Type of analysis ('summary', 'trends', 'insights', 'anomalies', 'correlations', 'chat')
        user_question: User's question (required for 'chat' mode)
    """
    
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
        "user_question": user_question or "",
        "llm_response": "",
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
        print("Usage: python langgraph_analyzer.py <csv_path> [analysis_type] [user_question]")
        print("  analysis_type: summary|trends|insights|anomalies|correlations|chat")
        print("  user_question: Required for 'chat' mode")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    analysis_type = sys.argv[2] if len(sys.argv) > 2 else 'summary'
    user_question = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Run analysis
    result = analyze_csv(csv_file, analysis_type, user_question)
    
    # Output result as JSON
    print("RESULT_JSON:" + json.dumps(result, default=str))
