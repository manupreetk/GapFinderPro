#!/usr/bin/env python3
"""
GapFinderPro Server
Main Flask application for role gap analysis
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import logging
from extractor import ResumeExtractor
from analyzer import GapAnalyzer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize components
extractor = ResumeExtractor()
analyzer = GapAnalyzer()

@app.route('/')
def index():
    """Serve the main application"""
    return send_from_directory('../client', 'index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "GapFinderPro"})

@app.route('/api/analyze', methods=['POST'])
def analyze_resume():
    """
    Analyze resume against job role
    Expected JSON payload:
    {
        "resume_text": "...",
        "target_role": "software_engineer"
    }
    """
    try:
        data = request.get_json()
        
        if not data or 'resume_text' not in data or 'target_role' not in data:
            return jsonify({
                "error": "Missing required fields: resume_text and target_role"
            }), 400
        
        resume_text = data['resume_text']
        target_role = data['target_role']
        
        # Extract skills from resume
        extracted_skills = extractor.extract_skills(resume_text)
        
        # Analyze gaps
        analysis = analyzer.analyze_gaps(extracted_skills, target_role)
        
        return jsonify({
            "success": True,
            "extracted_skills": extracted_skills,
            "analysis": analysis
        })
        
    except Exception as e:
        logger.error(f"Error in analyze_resume: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.route('/api/roles')
def get_available_roles():
    """Get list of available job roles for analysis"""
    try:
        roles = analyzer.get_available_roles()
        return jsonify({
            "success": True,
            "roles": roles
        })
    except Exception as e:
        logger.error(f"Error in get_available_roles: {str(e)}")
        return jsonify({
            "error": "Internal server error",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Endpoint not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"error": "Internal server error"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting GapFinderPro server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
