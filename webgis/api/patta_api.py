"""
Patta Document API Endpoints
Handles PDF upload and data extraction
"""

import os
import sys
import json
import tempfile
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import logging

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)

try:
    from digitization.patta_extractor import extract_patta_data
    PATTA_EXTRACTOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Patta extractor not available: {e}")
    extract_patta_data = None
    PATTA_EXTRACTOR_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint
patta_bp = Blueprint('patta_api', __name__, url_prefix='/api/patta')

# Configuration
ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
UPLOAD_FOLDER = 'uploads/patta_documents'

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def ensure_upload_folder():
    """Ensure upload folder exists"""
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@patta_bp.route('/upload', methods=['POST'])
def upload_and_extract():
    """
    Upload Patta PDF and extract structured data
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file uploaded',
                'message': 'Please select a PDF file to upload'
            }), 400
        
        file = request.files['file']
        
        # Check if file is selected
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'message': 'Please select a PDF file'
            }), 400
        
        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type',
                'message': 'Only PDF files are allowed'
            }), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({
                'success': False,
                'error': 'File too large',
                'message': f'File size must be less than {MAX_FILE_SIZE // (1024*1024)}MB'
            }), 400
        
        # Ensure upload folder exists
        ensure_upload_folder()
        
        # Secure filename
        filename = secure_filename(file.filename)
        
        # Create unique filename to avoid conflicts
        import uuid
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        # Save file
        file.save(file_path)
        logger.info(f"File saved: {file_path}")
        
        # Extract data from PDF
        logger.info("Starting data extraction...")
        if not PATTA_EXTRACTOR_AVAILABLE:
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': 'Patta extractor not available',
                'message': 'Required dependencies not installed'
            }), 500
        
        extraction_result = extract_patta_data(file_path)
        
        # Check if extraction was successful
        if 'error' in extraction_result:
            # Clean up uploaded file
            try:
                os.remove(file_path)
            except:
                pass
            
            return jsonify({
                'success': False,
                'error': extraction_result['error'],
                'message': 'Failed to extract data from PDF'
            }), 500
        
        # Prepare response
        response_data = {
            'success': True,
            'message': 'Data extracted successfully',
            'filename': filename,
            'file_size': file_size,
            'extracted_data': {
                'name': extraction_result.get('name', ''),
                'father_or_husband': extraction_result.get('father_or_husband', ''),
                'patta_no': extraction_result.get('patta_no', ''),
                'survey_no': extraction_result.get('survey_no', ''),
                'dag_no': extraction_result.get('dag_no', ''),
                'khasra': extraction_result.get('khasra', ''),
                'area': extraction_result.get('area', ''),
                'village': extraction_result.get('village', ''),
                'taluk': extraction_result.get('taluk', ''),
                'district': extraction_result.get('district', ''),
                'date': extraction_result.get('date', '')
            },
            'extraction_summary': extraction_result.get('extraction_summary', {}),
            'file_path': file_path  # For admin reference
        }
        
        logger.info("Data extraction completed successfully")
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error during upload and extraction: {str(e)}")
        
        # Clean up file if it was saved
        try:
            if 'file_path' in locals():
                os.remove(file_path)
        except:
            pass
        
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': f'An error occurred: {str(e)}'
        }), 500

@patta_bp.route('/validate', methods=['POST'])
def validate_extracted_data():
    """
    Validate extracted data and provide suggestions
    """
    try:
        data = request.get_json()
        
        if not data or 'extracted_data' not in data:
            return jsonify({
                'success': False,
                'error': 'No data provided',
                'message': 'Please provide extracted data for validation'
            }), 400
        
        extracted_data = data['extracted_data']
        validation_results = {}
        suggestions = []
        
        # Validate each field
        required_fields = ['name', 'patta_no', 'village', 'district']
        
        for field in required_fields:
            value = extracted_data.get(field, '').strip()
            if not value:
                validation_results[field] = {
                    'status': 'missing',
                    'message': f'{field.replace("_", " ").title()} is required'
                }
                suggestions.append(f"Please verify {field.replace('_', ' ')} field")
            else:
                validation_results[field] = {
                    'status': 'present',
                    'message': f'{field.replace("_", " ").title()} found'
                }
        
        # Additional validations
        if extracted_data.get('area'):
            area = extracted_data['area']
            if not re.search(r'\d+', area):
                validation_results['area'] = {
                    'status': 'warning',
                    'message': 'Area should contain a number'
                }
                suggestions.append("Please verify area measurement")
        
        if extracted_data.get('date'):
            date = extracted_data['date']
            if not re.search(r'\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}', date):
                validation_results['date'] = {
                    'status': 'warning',
                    'message': 'Date format may be incorrect'
                }
                suggestions.append("Please verify date format")
        
        # Calculate overall validation score
        total_fields = len(validation_results)
        valid_fields = sum(1 for v in validation_results.values() if v['status'] == 'present')
        validation_score = round((valid_fields / total_fields) * 100, 2) if total_fields > 0 else 0
        
        response_data = {
            'success': True,
            'validation_results': validation_results,
            'validation_score': validation_score,
            'suggestions': suggestions,
            'is_valid': validation_score >= 70  # 70% threshold for validity
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error during validation: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'message': f'An error occurred during validation: {str(e)}'
        }), 500

@patta_bp.route('/batch-extract', methods=['POST'])
def batch_extract():
    """
    Extract data from multiple PDF files
    """
    try:
        files = request.files.getlist('files')
        
        if not files:
            return jsonify({
                'success': False,
                'error': 'No files uploaded',
                'message': 'Please select PDF files to upload'
            }), 400
        
        if len(files) > 10:  # Limit batch size
            return jsonify({
                'success': False,
                'error': 'Too many files',
                'message': 'Maximum 10 files allowed per batch'
            }), 400
        
        results = []
        errors = []
        
        ensure_upload_folder()
        
        for i, file in enumerate(files):
            try:
                if not allowed_file(file.filename):
                    errors.append({
                        'file': file.filename,
                        'error': 'Invalid file type'
                    })
                    continue
                
                # Save file temporarily
                filename = secure_filename(file.filename)
                unique_filename = f"batch_{i}_{filename}"
                file_path = os.path.join(UPLOAD_FOLDER, unique_filename)
                file.save(file_path)
                
                # Extract data
                extraction_result = extract_patta_data(file_path)
                
                if 'error' in extraction_result:
                    errors.append({
                        'file': file.filename,
                        'error': extraction_result['error']
                    })
                else:
                    results.append({
                        'filename': file.filename,
                        'extracted_data': {
                            'name': extraction_result.get('name', ''),
                            'father_or_husband': extraction_result.get('father_or_husband', ''),
                            'patta_no': extraction_result.get('patta_no', ''),
                            'survey_no': extraction_result.get('survey_no', ''),
                            'dag_no': extraction_result.get('dag_no', ''),
                            'khasra': extraction_result.get('khasra', ''),
                            'area': extraction_result.get('area', ''),
                            'village': extraction_result.get('village', ''),
                            'taluk': extraction_result.get('taluk', ''),
                            'district': extraction_result.get('district', ''),
                            'date': extraction_result.get('date', '')
                        },
                        'extraction_summary': extraction_result.get('extraction_summary', {})
                    })
                
                # Clean up file
                try:
                    os.remove(file_path)
                except:
                    pass
                    
            except Exception as e:
                errors.append({
                    'file': file.filename,
                    'error': str(e)
                })
        
        response_data = {
            'success': True,
            'message': f'Processed {len(files)} files',
            'results': results,
            'errors': errors,
            'summary': {
                'total_files': len(files),
                'successful_extractions': len(results),
                'failed_extractions': len(errors)
            }
        }
        
        return jsonify(response_data), 200
        
    except Exception as e:
        logger.error(f"Error during batch extraction: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Batch extraction failed',
            'message': f'An error occurred: {str(e)}'
        }), 500

@patta_bp.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    try:
        # Check if required dependencies are available
        dependencies_status = {}
        
        try:
            import pdfplumber
            dependencies_status['pdfplumber'] = 'available'
        except ImportError:
            dependencies_status['pdfplumber'] = 'missing'
        
        try:
            import pytesseract
            dependencies_status['pytesseract'] = 'available'
        except ImportError:
            dependencies_status['pytesseract'] = 'missing'
        
        try:
            from pdf2image import convert_from_path
            dependencies_status['pdf2image'] = 'available'
        except ImportError:
            dependencies_status['pdf2image'] = 'missing'
        
        # Check if patta extractor is available
        patta_extractor_status = 'available' if PATTA_EXTRACTOR_AVAILABLE else 'missing'
        
        all_available = all(status == 'available' for status in dependencies_status.values()) and PATTA_EXTRACTOR_AVAILABLE
        
        return jsonify({
            'success': all_available,
            'status': 'healthy' if all_available else 'unhealthy',
            'dependencies': dependencies_status,
            'patta_extractor': patta_extractor_status,
            'upload_folder': UPLOAD_FOLDER,
            'max_file_size': f"{MAX_FILE_SIZE // (1024*1024)}MB"
        }), 200
        
    except ImportError as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': f'Missing dependency: {str(e)}',
            'message': 'Required packages not installed'
        }), 500
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'message': 'Health check failed'
        }), 500

# Import regex for validation
import re




