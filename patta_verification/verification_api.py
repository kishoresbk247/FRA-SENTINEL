"""
API Integration for Patta Document Verification System
Integrates the comprehensive verification system with the existing web application
"""

from flask import Blueprint, request, jsonify, current_app
import os
import json
from datetime import datetime
import logging
from werkzeug.utils import secure_filename
from patta_verifier import PattaVerifier

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create Blueprint for verification API
verification_bp = Blueprint('verification', __name__, url_prefix='/api/verification')

# Initialize verifier
verifier = PattaVerifier()

# Allowed file extensions
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'tiff', 'bmp'}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@verification_bp.route('/upload_and_verify', methods=['POST'])
def upload_and_verify():
    """
    Upload Patta document and perform complete verification
    
    Expected form data:
    - file: Patta document (PDF/image)
    - state: State for portal verification (optional, defaults to Tamil Nadu)
    - verification_type: Type of verification (full, quick, basic)
    """
    try:
        # Check if file is present
        if 'file' not in request.files:
            return jsonify({
                'success': False,
                'error': 'No file provided',
                'error_code': 'NO_FILE'
            }), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({
                'success': False,
                'error': 'No file selected',
                'error_code': 'NO_FILE_SELECTED'
            }), 400
        
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': 'Invalid file type. Allowed: PDF, PNG, JPG, JPEG, TIFF, BMP',
                'error_code': 'INVALID_FILE_TYPE'
            }), 400
        
        # Get additional parameters
        state = request.form.get('state', 'Tamil Nadu')
        verification_type = request.form.get('verification_type', 'full')
        
        # Secure filename and save
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'patta_verification')
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, unique_filename)
        file.save(file_path)
        
        logger.info(f"File uploaded: {file_path}")
        
        # Perform verification based on type
        if verification_type == 'quick':
            results = perform_quick_verification(file_path, state)
        elif verification_type == 'basic':
            results = perform_basic_verification(file_path, state)
        else:  # full verification
            results = verifier.verify_patta_document(file_path, state)
        
        # Add file information to results
        results['file_info'] = {
            'original_filename': file.filename,
            'saved_filename': unique_filename,
            'file_size': os.path.getsize(file_path),
            'upload_timestamp': datetime.now().isoformat()
        }
        
        # Save verification results
        results_file = os.path.join(upload_dir, f"{timestamp}_results.json")
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Clean up file if verification failed
        if not results.get('success', False):
            try:
                os.remove(file_path)
            except:
                pass
        
        return jsonify({
            'success': True,
            'verification_results': results,
            'message': 'Verification completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Upload and verification error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'VERIFICATION_ERROR'
        }), 500

@verification_bp.route('/verify_existing', methods=['POST'])
def verify_existing():
    """
    Verify an already uploaded document
    
    Expected JSON data:
    - file_path: Path to the document
    - state: State for portal verification
    - verification_type: Type of verification
    """
    try:
        data = request.get_json()
        
        if not data or 'file_path' not in data:
            return jsonify({
                'success': False,
                'error': 'File path not provided',
                'error_code': 'NO_FILE_PATH'
            }), 400
        
        file_path = data['file_path']
        state = data.get('state', 'Tamil Nadu')
        verification_type = data.get('verification_type', 'full')
        
        # Check if file exists
        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'File not found',
                'error_code': 'FILE_NOT_FOUND'
            }), 404
        
        # Perform verification
        if verification_type == 'quick':
            results = perform_quick_verification(file_path, state)
        elif verification_type == 'basic':
            results = perform_basic_verification(file_path, state)
        else:  # full verification
            results = verifier.verify_patta_document(file_path, state)
        
        return jsonify({
            'success': True,
            'verification_results': results,
            'message': 'Verification completed successfully'
        })
        
    except Exception as e:
        logger.error(f"Verification error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'VERIFICATION_ERROR'
        }), 500

@verification_bp.route('/get_verification_status/<verification_id>', methods=['GET'])
def get_verification_status(verification_id):
    """
    Get verification status for a specific verification ID
    
    Args:
        verification_id: Unique identifier for the verification
    """
    try:
        # Look for results file
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'patta_verification')
        results_file = os.path.join(upload_dir, f"{verification_id}_results.json")
        
        if not os.path.exists(results_file):
            return jsonify({
                'success': False,
                'error': 'Verification not found',
                'error_code': 'VERIFICATION_NOT_FOUND'
            }), 404
        
        with open(results_file, 'r') as f:
            results = json.load(f)
        
        return jsonify({
            'success': True,
            'verification_results': results
        })
        
    except Exception as e:
        logger.error(f"Status retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'STATUS_ERROR'
        }), 500

@verification_bp.route('/get_verification_history', methods=['GET'])
def get_verification_history():
    """
    Get verification history for the current session or user
    """
    try:
        upload_dir = os.path.join(current_app.root_path, 'uploads', 'patta_verification')
        
        if not os.path.exists(upload_dir):
            return jsonify({
                'success': True,
                'verifications': []
            })
        
        # Get all result files
        result_files = [f for f in os.listdir(upload_dir) if f.endswith('_results.json')]
        
        verifications = []
        for result_file in sorted(result_files, reverse=True)[:50]:  # Last 50 verifications
            try:
                with open(os.path.join(upload_dir, result_file), 'r') as f:
                    result = json.load(f)
                
                # Extract summary information
                summary = {
                    'verification_id': result_file.replace('_results.json', ''),
                    'timestamp': result.get('verification_timestamp', ''),
                    'filename': result.get('file_info', {}).get('original_filename', ''),
                    'state': result.get('state', ''),
                    'status': result.get('status', ''),
                    'final_decision': result.get('final_decision', {}).get('status', ''),
                    'confidence': result.get('final_decision', {}).get('confidence', 0)
                }
                verifications.append(summary)
                
            except Exception as e:
                logger.warning(f"Error reading result file {result_file}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'verifications': verifications,
            'total_count': len(verifications)
        })
        
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'HISTORY_ERROR'
        }), 500

@verification_bp.route('/get_supported_states', methods=['GET'])
def get_supported_states():
    """
    Get list of supported states for portal verification
    """
    try:
        states = list(verifier.state_portals.keys())
        
        return jsonify({
            'success': True,
            'supported_states': states,
            'state_details': verifier.state_portals
        })
        
    except Exception as e:
        logger.error(f"States retrieval error: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'error_code': 'STATES_ERROR'
        }), 500

def perform_quick_verification(file_path: str, state: str) -> dict:
    """
    Perform quick verification (OCR + basic validation only)
    """
    logger.info("Performing quick verification")
    
    try:
        # Step 1: OCR Extraction
        ocr_result = verifier.extract_document_data(file_path)
        
        # Step 2: Basic validation
        validation_result = {
            'status': 'completed',
            'success': True,
            'verification_type': 'quick',
            'ocr_extraction': ocr_result,
            'basic_validation': {
                'required_fields_present': ocr_result.get('validation_status', {}).get('all_present', False),
                'ocr_quality': ocr_result.get('ocr_quality', {}).get('score', 0),
                'confidence_threshold_met': ocr_result.get('ocr_quality', {}).get('score', 0) >= 70
            },
            'quick_decision': {
                'status': 'ACCEPTED' if ocr_result.get('validation_status', {}).get('all_present', False) else 'REJECTED',
                'reason': 'All required fields present' if ocr_result.get('validation_status', {}).get('all_present', False) else 'Missing required fields',
                'confidence': ocr_result.get('ocr_quality', {}).get('score', 0)
            }
        }
        
        return validation_result
        
    except Exception as e:
        logger.error(f"Quick verification error: {e}")
        return {
            'status': 'error',
            'success': False,
            'error': str(e),
            'verification_type': 'quick'
        }

def perform_basic_verification(file_path: str, state: str) -> dict:
    """
    Perform basic verification (OCR + Portal verification)
    """
    logger.info("Performing basic verification")
    
    try:
        # Step 1: OCR Extraction
        ocr_result = verifier.extract_document_data(file_path)
        
        # Step 2: Portal Verification
        portal_result = verifier.verify_with_portal(ocr_result, state)
        
        # Step 3: Basic decision
        basic_decision = {
            'status': 'PENDING',
            'confidence': 0,
            'reasoning': []
        }
        
        # Decision logic
        if ocr_result.get('validation_status', {}).get('all_present', False):
            basic_decision['confidence'] += 50
            basic_decision['reasoning'].append("✅ All required fields present")
        else:
            basic_decision['reasoning'].append("❌ Missing required fields")
        
        if portal_result.get('verified', False):
            basic_decision['confidence'] += 40
            basic_decision['reasoning'].append("✅ Portal verification successful")
        else:
            basic_decision['reasoning'].append("❌ Portal verification failed")
        
        if basic_decision['confidence'] >= 80:
            basic_decision['status'] = 'ACCEPTED'
        elif basic_decision['confidence'] >= 50:
            basic_decision['status'] = 'FLAGGED_FOR_REVIEW'
        else:
            basic_decision['status'] = 'REJECTED'
        
        return {
            'status': 'completed',
            'success': True,
            'verification_type': 'basic',
            'ocr_extraction': ocr_result,
            'portal_verification': portal_result,
            'basic_decision': basic_decision
        }
        
    except Exception as e:
        logger.error(f"Basic verification error: {e}")
        return {
            'status': 'error',
            'success': False,
            'error': str(e),
            'verification_type': 'basic'
        }

# Error handlers
@verification_bp.errorhandler(413)
def too_large(e):
    return jsonify({
        'success': False,
        'error': 'File too large. Maximum size is 10MB.',
        'error_code': 'FILE_TOO_LARGE'
    }), 413

@verification_bp.errorhandler(400)
def bad_request(e):
    return jsonify({
        'success': False,
        'error': 'Bad request. Please check your input.',
        'error_code': 'BAD_REQUEST'
    }), 400

@verification_bp.errorhandler(500)
def internal_error(e):
    return jsonify({
        'success': False,
        'error': 'Internal server error. Please try again.',
        'error_code': 'INTERNAL_ERROR'
    }), 500

