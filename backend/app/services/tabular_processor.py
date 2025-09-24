import pandas as pd
import numpy as np
import json
import io
import os
from typing import Dict, Any, List, Optional, Union
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TabularProcessor:
    """Service for processing tabular data (Excel, CSV, etc.) using pandas"""
    
    def __init__(self):
        self.supported_formats = [
            'application/vnd.ms-excel',  # .xls
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',  # .xlsx
            'text/csv',  # .csv
            'text/tab-separated-values',  # .tsv
            'application/json'  # .json
        ]
    
    def is_tabular_file(self, content_type: str, filename: str = "") -> bool:
        """Check if file is a supported tabular format"""
        if content_type in self.supported_formats:
            return True
        
        # Check by file extension as backup
        if filename:
            ext = Path(filename).suffix.lower()
            return ext in ['.xls', '.xlsx', '.csv', '.tsv', '.json']
        
        return False
    
    async def process_tabular_file(self, file_content: bytes, filename: str, content_type: str) -> Dict[str, Any]:
        """Process tabular file and extract meaningful information"""
        try:
            logger.info(f"Processing tabular file: {filename} ({content_type})")
            
            # Read the file based on type
            df = await self._read_file(file_content, filename, content_type)
            
            if df is None or df.empty:
                return {
                    "summary": "Empty or unreadable file",
                    "data_preview": "",
                    "insights": [],
                    "error": "No data found"
                }
            
            # Generate comprehensive analysis
            analysis = await self._analyze_dataframe(df, filename)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error processing tabular file {filename}: {str(e)}")
            return {
                "summary": f"Error processing {filename}",
                "data_preview": "",
                "insights": [],
                "error": str(e)
            }
    
    async def _read_file(self, file_content: bytes, filename: str, content_type: str) -> Optional[pd.DataFrame]:
        """Read file content into pandas DataFrame"""
        try:
            file_buffer = io.BytesIO(file_content)
            
            # Determine file type and read accordingly
            if content_type == 'text/csv' or filename.endswith('.csv'):
                # Try different encodings and separators for CSV
                for encoding in ['utf-8', 'latin-1', 'cp1252']:
                    for sep in [',', ';', '\t']:
                        try:
                            file_buffer.seek(0)
                            df = pd.read_csv(file_buffer, encoding=encoding, sep=sep)
                            if not df.empty and len(df.columns) > 1:
                                return df
                        except:
                            continue
                
            elif content_type in ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] or filename.endswith(('.xls', '.xlsx')):
                # Read Excel file
                file_buffer.seek(0)
                df = pd.read_excel(file_buffer, engine='openpyxl' if filename.endswith('.xlsx') else 'xlrd')
                return df
                
            elif content_type == 'text/tab-separated-values' or filename.endswith('.tsv'):
                # Read TSV file
                file_buffer.seek(0)
                df = pd.read_csv(file_buffer, sep='\t', encoding='utf-8')
                return df
                
            elif content_type == 'application/json' or filename.endswith('.json'):
                # Read JSON file
                file_buffer.seek(0)
                data = json.load(file_buffer)
                df = pd.json_normalize(data) if isinstance(data, list) else pd.DataFrame([data])
                return df
                
            return None
            
        except Exception as e:
            logger.error(f"Error reading file {filename}: {str(e)}")
            return None
    
    async def _analyze_dataframe(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        """Perform comprehensive analysis of the DataFrame"""
        try:
            # Basic info
            shape = df.shape
            columns = df.columns.tolist()
            data_types = df.dtypes.to_dict()
            
            # Data preview (first few rows)
            preview = df.head(5).to_dict('records')
            
            # Statistical summary for numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            stats_summary = {}
            if len(numeric_cols) > 0:
                stats_summary = df[numeric_cols].describe().to_dict()
            
            # Missing data analysis
            missing_data = df.isnull().sum().to_dict()
            missing_percentage = (df.isnull().sum() / len(df) * 100).to_dict()
            
            # Unique values for categorical columns
            categorical_info = {}
            for col in df.columns:
                if df[col].dtype == 'object' or df[col].nunique() < 20:
                    unique_count = df[col].nunique()
                    if unique_count <= 10:
                        categorical_info[col] = {
                            "unique_values": df[col].value_counts().head(10).to_dict(),
                            "unique_count": unique_count
                        }
                    else:
                        categorical_info[col] = {
                            "unique_count": unique_count,
                            "sample_values": df[col].value_counts().head(5).to_dict()
                        }
            
            # Generate insights
            insights = []
            
            # Dataset size insight
            insights.append(f"Dataset contains {shape[0]} rows and {shape[1]} columns")
            
            # Missing data insights
            high_missing = [col for col, pct in missing_percentage.items() if pct > 50]
            if high_missing:
                insights.append(f"Columns with >50% missing data: {', '.join(high_missing)}")
            
            # Data type insights
            numeric_count = len([col for col, dtype in data_types.items() if pd.api.types.is_numeric_dtype(dtype)])
            text_count = len([col for col, dtype in data_types.items() if dtype == 'object'])
            insights.append(f"Data types: {numeric_count} numeric, {text_count} text columns")
            
            # Potential medical/patient data detection
            medical_keywords = ['patient', 'diagnosis', 'treatment', 'medication', 'prescription', 'doctor', 'hospital', 'clinic', 'age', 'gender', 'dob', 'birth', 'disease', 'symptom']
            medical_columns = [col for col in columns if any(keyword in col.lower() for keyword in medical_keywords)]
            if medical_columns:
                insights.append(f"Potential medical data columns detected: {', '.join(medical_columns)}")
            
            # Generate summary
            summary = f"Tabular data from {filename}: {shape[0]} rows × {shape[1]} columns"
            if medical_columns:
                summary += f" (Medical data detected in: {', '.join(medical_columns)})"
            
            # Create contextual text for chat
            contextual_text = self._generate_contextual_text(df, filename, insights, categorical_info)
            
            return {
                "summary": summary,
                "data_preview": preview,
                "insights": insights,
                "shape": shape,
                "columns": columns,
                "data_types": {k: str(v) for k, v in data_types.items()},
                "missing_data": missing_data,
                "missing_percentage": missing_percentage,
                "categorical_info": categorical_info,
                "statistical_summary": stats_summary,
                "contextual_text": contextual_text,
                "filename": filename
            }
            
        except Exception as e:
            logger.error(f"Error analyzing DataFrame: {str(e)}")
            return {
                "summary": f"Error analyzing {filename}",
                "data_preview": "",
                "insights": [f"Analysis failed: {str(e)}"],
                "error": str(e)
            }
    
    def _generate_contextual_text(self, df: pd.DataFrame, filename: str, insights: List[str], categorical_info: Dict) -> str:
        """Generate text suitable for chat context"""
        context_parts = [
            f"File: {filename}",
            f"Shape: {df.shape[0]} rows × {df.shape[1]} columns",
            f"Columns: {', '.join(df.columns.tolist())}"
        ]
        
        # Add sample data
        if not df.empty:
            context_parts.append("Sample data:")
            sample_rows = min(3, len(df))
            for i in range(sample_rows):
                row_data = []
                for col in df.columns[:5]:  # Limit to first 5 columns
                    value = df.iloc[i][col]
                    if pd.isna(value):
                        value = "N/A"
                    row_data.append(f"{col}: {value}")
                context_parts.append(f"Row {i+1}: {', '.join(row_data)}")
        
        # Add insights
        context_parts.extend(insights)
        
        # Add categorical summaries
        for col, info in categorical_info.items():
            if "unique_values" in info:
                top_values = list(info["unique_values"].keys())[:3]
                context_parts.append(f"{col} top values: {', '.join(map(str, top_values))}")
        
        return "\n".join(context_parts)
    
    async def query_dataframe(self, df: pd.DataFrame, query: str) -> str:
        """Process natural language queries about the DataFrame"""
        try:
            # Simple query processing - can be enhanced with pandas AI
            query_lower = query.lower()
            
            if 'summary' in query_lower or 'describe' in query_lower:
                return df.describe().to_string()
            elif 'columns' in query_lower:
                return f"Columns: {', '.join(df.columns.tolist())}"
            elif 'shape' in query_lower or 'size' in query_lower:
                return f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns"
            elif 'missing' in query_lower or 'null' in query_lower:
                missing = df.isnull().sum()
                missing_info = missing[missing > 0]
                if missing_info.empty:
                    return "No missing values found in the dataset"
                else:
                    return f"Missing values:\n{missing_info.to_string()}"
            else:
                return "I can help you with queries about: summary, columns, shape, missing values, or general questions about the data."
                
        except Exception as e:
            return f"Error processing query: {str(e)}"