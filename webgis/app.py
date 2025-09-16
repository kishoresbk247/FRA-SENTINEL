from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
import sys

app = Flask(__name__)
app.secret_key = "supersecretfra2025"

# Re-enable OCR/NER integration so uploads can add villages to map
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.append(PROJECT_ROOT)
try:
    from digitization.simple_ocr_ner import pdf_to_text, extract_entities
    print("✅ OCR/NER integration loaded successfully")
except Exception as e:
    pdf_to_text = None
    extract_entities = None
    print(f"⚠️ OCR/NER not available: {e}")

# Import Patta API (after PROJECT_ROOT is added to sys.path)
try:
    from webgis.api.patta_api import patta_bp
    PATTA_API_AVAILABLE = True
    print("✅ Patta API loaded successfully")
except ImportError as e:
    PATTA_API_AVAILABLE = False
    print(f"⚠️ Patta API not available: {e}")

# Import Demo Data for Hackathon Presentation
try:
    from webgis.demo_data import (
        get_demo_patta_metrics, get_demo_system_stats, 
        get_demo_success_stories, get_demo_patta_documents,
        get_demo_ai_prediction, get_demo_chatbot_response
    )
    DEMO_DATA_AVAILABLE = True
    print("✅ Demo data loaded successfully")
except ImportError as e:
    DEMO_DATA_AVAILABLE = False
    print(f"⚠️ Demo data not available: {e}")

# Register Patta API Blueprint
if PATTA_API_AVAILABLE:
    app.register_blueprint(patta_bp)

# Comprehensive FRA Atlas Data Structure
FRA_ATLAS_DATA = {
    "states": {
        "Madhya Pradesh": {
            "districts": {
                "Khargone": {
                    "blocks": {
                        "Khargone": {
                            "villages": {
                                "Khargone": {
                                    "patta_holders": [
                                        {
                                            "id": "FRA001",
                                            "name": "Ram Singh",
                                            "tribal_group": "Bhil",
                                            "claim_type": "IFR",
                                            "area_hectares": 2.5,
                                            "status": "Approved",
                                            "coordinates": [75.6102, 21.8225],
                                            "socio_economic": {
                                                "literacy": "Primary",
                                                "livelihood": "Agriculture",
                                                "assets": ["Land", "Livestock"]
                                            }
                                        }
                                    ],
                                    "forest_cover": 65.2,
                                    "water_bodies": 3,
                                    "agricultural_land": 28.8,
                                    "coordinates": [75.6102, 21.8225]
                                }
                            }
                        }
                    }
                },
                "Jhabua": {
                    "blocks": {
                        "Jhabua": {
                            "villages": {
                                "Jhabua": {
                                    "patta_holders": [
                                        {
                                            "id": "FRA002",
                                            "name": "Sita Devi",
                                            "tribal_group": "Bhil",
                                            "claim_type": "CR",
                                            "area_hectares": 1.8,
                                            "status": "Pending",
                                            "coordinates": [74.5902, 22.7677],
                                            "socio_economic": {
                                                "literacy": "Illiterate",
                                                "livelihood": "Forest Produce",
                                                "assets": ["Land"]
                                            }
                                        }
                                    ],
                                    "forest_cover": 78.5,
                                    "water_bodies": 2,
                                    "agricultural_land": 15.3,
                                    "coordinates": [74.5902, 22.7677]
                                }
                            }
                        }
                    }
                }
            }
        },
        "Odisha": {
            "districts": {
                "Koraput": {
                    "blocks": {
                        "Koraput": {
                            "villages": {
                                "Koraput": {
                                    "patta_holders": [
                                        {
                                            "id": "FRA003",
                                            "name": "Ganga Ram",
                                            "tribal_group": "Gond",
                                            "claim_type": "CFR",
                                            "area_hectares": 5.2,
                                            "status": "Verified",
                                            "coordinates": [82.7202, 18.8102],
                                            "socio_economic": {
                                                "literacy": "Secondary",
                                                "livelihood": "Mixed Farming",
                                                "assets": ["Land", "Livestock", "Tools"]
                                            }
                                        }
                                    ],
                                    "forest_cover": 82.1,
                                    "water_bodies": 4,
                                    "agricultural_land": 12.7,
                                    "coordinates": [82.7202, 18.8102]
                                }
                            }
                        }
                    }
                }
            }
        }
    }
}

# Legacy data for backward compatibility
TEST_VILLAGES = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {
                "village": "Khargone",
                "patta_holder": "Ram Singh",
                "latitude": 21.8225,
                "longitude": 75.6102,
                "area_hectares": 2.5,
                "claim_status": "Approved"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [75.6102, 21.8225]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "village": "Mandla",
                "patta_holder": "Sita Devi",
                "latitude": 22.6000,
                "longitude": 80.3667,
                "area_hectares": 3.2,
                "claim_status": "Verified",
                "uploaded_by": "dcf.mandla@fra.gov.in",
                "file_id": "FRA12345678",
                "tribal_group": "Gond",
                "family_size": 5,
                "file_name": "mandla_patta_001.pdf",
                "upload_date": "2025-09-16T10:27:00"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [80.3667, 22.6000]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "village": "Dindori",
                "patta_holder": "Ganga Ram",
                "latitude": 22.9500,
                "longitude": 81.0833,
                "area_hectares": 4.1,
                "claim_status": "Verified",
                "uploaded_by": "rfo.dindori@fra.gov.in",
                "file_id": "FRA87654321",
                "tribal_group": "Baiga",
                "family_size": 7,
                "file_name": "dindori_claim_002.pdf",
                "upload_date": "2025-09-16T10:32:00"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [81.0833, 22.9500]
            }
        },
        {
            "type": "Feature",
            "properties": {
                "village": "Barwani",
                "patta_holder": "Kavita Bai",
                "latitude": 22.0333,
                "longitude": 74.9000,
                "area_hectares": 2.8,
                "claim_status": "Verified",
                "uploaded_by": "ccf.admin@fra.gov.in",
                "file_id": "FRA11223344",
                "tribal_group": "Bhil",
                "family_size": 4,
                "file_name": "barwani_survey_003.pdf",
                "upload_date": "2025-09-16T10:35:00"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [74.9000, 22.0333]
            }
        }
    ],
    "metadata": {
        "total_records": 4,
        "last_updated": "2025-09-16T10:35:00"
    }
}

# Boundary data for states, districts, villages, and tribal areas
BOUNDARY_DATA = {
    "states": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Madhya Pradesh", "type": "state"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [74.0, 21.0], [74.5, 20.8], [75.0, 20.5], [75.5, 20.8], [76.0, 21.0],
                        [76.5, 21.2], [77.0, 21.5], [77.5, 21.8], [78.0, 22.0], [78.5, 22.2],
                        [79.0, 22.5], [79.5, 22.8], [80.0, 23.0], [80.5, 23.2], [81.0, 23.5],
                        [81.5, 23.8], [82.0, 24.0], [82.5, 24.2], [83.0, 24.5], [82.5, 25.0],
                        [82.0, 25.5], [81.5, 26.0], [81.0, 26.2], [80.5, 26.0], [80.0, 25.8],
                        [79.5, 25.5], [79.0, 25.2], [78.5, 25.0], [78.0, 24.8], [77.5, 24.5],
                        [77.0, 24.2], [76.5, 24.0], [76.0, 23.8], [75.5, 23.5], [75.0, 23.2],
                        [74.5, 23.0], [74.0, 22.8], [73.5, 22.5], [73.0, 22.2], [72.5, 22.0],
                        [72.0, 21.8], [72.5, 21.5], [73.0, 21.2], [73.5, 21.0], [74.0, 21.0]
                    ]]
                }
            },
            {
                "type": "Feature", 
                "properties": {"name": "Odisha", "type": "state"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [81.0, 17.0], [81.5, 16.8], [82.0, 16.5], [82.5, 16.8], [83.0, 17.0],
                        [83.5, 17.2], [84.0, 17.5], [84.5, 17.8], [85.0, 18.0], [85.5, 18.2],
                        [86.0, 18.5], [86.5, 18.8], [87.0, 19.0], [87.5, 19.2], [88.0, 19.5],
                        [88.5, 19.8], [89.0, 20.0], [89.5, 20.2], [90.0, 20.5], [89.5, 21.0],
                        [89.0, 21.5], [88.5, 22.0], [88.0, 22.2], [87.5, 22.0], [87.0, 21.8],
                        [86.5, 21.5], [86.0, 21.2], [85.5, 21.0], [85.0, 20.8], [84.5, 20.5],
                        [84.0, 20.2], [83.5, 20.0], [83.0, 19.8], [82.5, 19.5], [82.0, 19.2],
                        [81.5, 19.0], [81.0, 18.8], [80.5, 18.5], [80.0, 18.2], [79.5, 18.0],
                        [79.0, 17.8], [79.5, 17.5], [80.0, 17.2], [80.5, 17.0], [81.0, 17.0]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Tripura", "type": "state"},
                "geometry": {
                    "type": "Polygon", 
                    "coordinates": [[
                        [91.0, 23.0], [91.2, 22.8], [91.4, 22.6], [91.6, 22.8], [91.8, 23.0],
                        [92.0, 23.2], [92.2, 23.4], [92.4, 23.6], [92.6, 23.8], [92.8, 24.0],
                        [93.0, 24.2], [92.8, 24.4], [92.6, 24.2], [92.4, 24.0], [92.2, 23.8],
                        [92.0, 23.6], [91.8, 23.4], [91.6, 23.2], [91.4, 23.0], [91.2, 22.8],
                        [91.0, 23.0]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Telangana", "type": "state"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [77.0, 15.0], [77.5, 14.8], [78.0, 14.5], [78.5, 14.8], [79.0, 15.0],
                        [79.5, 15.2], [80.0, 15.5], [80.5, 15.8], [81.0, 16.0], [81.5, 16.2],
                        [82.0, 16.5], [81.5, 17.0], [81.0, 17.5], [80.5, 18.0], [80.0, 18.2],
                        [79.5, 18.0], [79.0, 17.8], [78.5, 17.5], [78.0, 17.2], [77.5, 17.0],
                        [77.0, 16.8], [76.5, 16.5], [76.0, 16.2], [75.5, 16.0], [75.0, 15.8],
                        [74.5, 15.5], [74.0, 15.2], [74.5, 15.0], [75.0, 14.8], [75.5, 15.0],
                        [76.0, 15.2], [76.5, 15.0], [77.0, 15.0]
                    ]]
                }
            }
        ]
    },
    "districts": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Khargone", "state": "Madhya Pradesh", "type": "district"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [75.0, 21.5], [75.2, 21.4], [75.4, 21.3], [75.6, 21.4], [75.8, 21.5],
                        [76.0, 21.6], [76.2, 21.7], [76.4, 21.8], [76.6, 21.9], [76.8, 22.0],
                        [76.6, 22.1], [76.4, 22.0], [76.2, 21.9], [76.0, 21.8], [75.8, 21.7],
                        [75.6, 21.6], [75.4, 21.7], [75.2, 21.8], [75.0, 21.7], [74.8, 21.6],
                        [74.6, 21.5], [74.8, 21.4], [75.0, 21.5]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Jhabua", "state": "Madhya Pradesh", "type": "district"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [74.0, 22.5], [74.2, 22.4], [74.4, 22.3], [74.6, 22.4], [74.8, 22.5],
                        [75.0, 22.6], [75.2, 22.7], [75.4, 22.8], [75.6, 22.9], [75.8, 23.0],
                        [75.6, 23.1], [75.4, 23.0], [75.2, 22.9], [75.0, 22.8], [74.8, 22.7],
                        [74.6, 22.6], [74.4, 22.7], [74.2, 22.8], [74.0, 22.7], [73.8, 22.6],
                        [73.6, 22.5], [73.8, 22.4], [74.0, 22.5]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Mandla", "state": "Madhya Pradesh", "type": "district"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [80.0, 22.0], [80.2, 21.9], [80.4, 21.8], [80.6, 21.9], [80.8, 22.0],
                        [81.0, 22.1], [81.2, 22.2], [81.4, 22.3], [81.6, 22.4], [81.8, 22.5],
                        [82.0, 22.6], [81.8, 22.7], [81.6, 22.8], [81.4, 22.9], [81.2, 23.0],
                        [81.0, 22.9], [80.8, 22.8], [80.6, 22.7], [80.4, 22.6], [80.2, 22.5],
                        [80.0, 22.4], [79.8, 22.3], [79.6, 22.2], [79.8, 22.1], [80.0, 22.0]
                    ]]
                }
            }
        ]
    },
    "villages": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Khargone Village", "district": "Khargone", "type": "village"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [75.5, 21.7], [75.52, 21.68], [75.54, 21.66], [75.56, 21.68], [75.58, 21.7],
                        [75.6, 21.72], [75.62, 21.74], [75.64, 21.76], [75.66, 21.78], [75.68, 21.8],
                        [75.66, 21.82], [75.64, 21.8], [75.62, 21.78], [75.6, 21.76], [75.58, 21.74],
                        [75.56, 21.72], [75.54, 21.74], [75.52, 21.76], [75.5, 21.74], [75.48, 21.72],
                        [75.46, 21.7], [75.48, 21.68], [75.5, 21.7]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Jhabua Village", "district": "Jhabua", "type": "village"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [74.5, 22.7], [74.52, 22.68], [74.54, 22.66], [74.56, 22.68], [74.58, 22.7],
                        [74.6, 22.72], [74.62, 22.74], [74.64, 22.76], [74.66, 22.78], [74.68, 22.8],
                        [74.66, 22.82], [74.64, 22.8], [74.62, 22.78], [74.6, 22.76], [74.58, 22.74],
                        [74.56, 22.72], [74.54, 22.74], [74.52, 22.76], [74.5, 22.74], [74.48, 22.72],
                        [74.46, 22.7], [74.48, 22.68], [74.5, 22.7]
                    ]]
                }
            }
        ]
    },
    "tribal_areas": {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"name": "Bhil Tribal Area", "tribe": "Bhil", "type": "tribal"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [74.0, 22.0], [74.3, 21.8], [74.6, 21.6], [74.9, 21.8], [75.2, 22.0],
                        [75.5, 22.2], [75.8, 22.4], [76.1, 22.6], [76.4, 22.8], [76.7, 23.0],
                        [77.0, 23.2], [76.7, 23.4], [76.4, 23.6], [76.1, 23.8], [75.8, 24.0],
                        [75.5, 24.2], [75.2, 24.4], [74.9, 24.6], [74.6, 24.8], [74.3, 25.0],
                        [74.0, 24.8], [73.7, 24.6], [73.4, 24.4], [73.1, 24.2], [72.8, 24.0],
                        [72.5, 23.8], [72.2, 23.6], [71.9, 23.4], [71.6, 23.2], [71.3, 23.0],
                        [71.6, 22.8], [71.9, 22.6], [72.2, 22.4], [72.5, 22.2], [72.8, 22.0],
                        [73.1, 21.8], [73.4, 21.6], [73.7, 21.8], [74.0, 22.0]
                    ]]
                }
            },
            {
                "type": "Feature",
                "properties": {"name": "Gond Tribal Area", "tribe": "Gond", "type": "tribal"},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [[
                        [79.5, 21.5], [79.8, 21.3], [80.1, 21.1], [80.4, 21.3], [80.7, 21.5],
                        [81.0, 21.7], [81.3, 21.9], [81.6, 22.1], [81.9, 22.3], [82.2, 22.5],
                        [82.5, 22.7], [82.2, 22.9], [81.9, 23.1], [81.6, 23.3], [81.3, 23.5],
                        [81.0, 23.7], [80.7, 23.9], [80.4, 24.1], [80.1, 24.3], [79.8, 24.5],
                        [79.5, 24.3], [79.2, 24.1], [78.9, 23.9], [78.6, 23.7], [78.3, 23.5],
                        [78.0, 23.3], [77.7, 23.1], [77.4, 22.9], [77.1, 22.7], [76.8, 22.5],
                        [77.1, 22.3], [77.4, 22.1], [77.7, 21.9], [78.0, 21.7], [78.3, 21.5],
                        [78.6, 21.3], [78.9, 21.1], [79.2, 21.3], [79.5, 21.5]
                    ]]
                }
            }
        ]
    }
}

TEST_STATS = {
    "farmland": {"percentage": 35.5, "pixels": 3550},
    "forest": {"percentage": 42.3, "pixels": 4230},
    "water": {"percentage": 7.8, "pixels": 780},
    "homestead": {"percentage": 14.4, "pixels": 1440}
}

# Dummy users DB for demo
USERS = {
    "ccf.admin@fra.gov.in": {"password": "fra2025ccf", "role": "official"},
    "dcf.admin@fra.gov.in": {"password": "fra2025dcf", "role": "official"},
    "rfo.admin@fra.gov.in": {"password": "fra2025rfo", "role": "official"},
    "sarpanch.admin@fra.gov.in": {"password": "fra2025gram", "role": "official"},
    "public@fra.gov.in": {"password": "public2025", "role": "public"}
}

# Example patta claims database
PATTA_CLAIMS = [
    {
        "id": "MP001234",
        "applicant_name": "Ramesh Kumar Bhil",
        "village": "Khargone",
        "district": "Khargone",
        "state": "Madhya Pradesh",
        "claim_type": "IFR",
        "area_hectares": 2.5,
        "status": "Approved",
        "coordinates": [21.8245, 75.6102],
        "verified_by": "ccf.admin@fra.gov.in",
        "document": None
    },
    {
        "id": "OD005678",
        "applicant_name": "Sita Devi Santhal",
        "village": "Mayurbhanj",
        "district": "Mayurbhanj",
        "state": "Odisha",
        "claim_type": "CFR",
        "area_hectares": 15.0,
        "status": "Pending",
        "coordinates": [21.9270, 86.7470],
        "verified_by": None,
        "document": None
    }
]

@app.route('/', methods=['GET'])
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = ""
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "").strip()
        
        # Simple email format validation
        if '@' not in email:
            error = "Invalid email format. Please include '@' in the email address."
            return render_template("login.html", error=error)
        
        user = USERS.get(email)
        if user and user["password"] == password:
            session["user"] = email
            session["role"] = user["role"]
            # Derive display name and fine-grained role for UI
            session["user_name"] = email.split("@")[0]
            local = email.split("@")[0]
            if local.startswith("ccf"):
                session["user_role"] = "CCF"
            elif local.startswith("dcf"):
                session["user_role"] = "DCF"
            elif local.startswith("rfo"):
                session["user_role"] = "RFO"
            elif local.startswith("sarpanch"):
                session["user_role"] = "GRAM_SABHA"
            else:
                session["user_role"] = "PUBLIC"
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid credentials. Please check email and password."
    return render_template("login.html", error=error)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Additional Portal Routes
@app.route('/public-portal')
def public_portal():
    """Public portal for general access"""
    return render_template('public_portal.html')

@app.route('/departmental-portal')
def departmental_portal():
    """Departmental portal for government officials"""
    if not session.get('user'):
        return redirect(url_for('login'))
    if session.get('user_role') not in ['CCF', 'DCF', 'RFO']:
        flash('Access denied. This portal is for government officials only.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('departmental_portal.html')

@app.route('/village-portal')
def village_portal():
    """Village portal for local communities"""
    return render_template('village_portal.html')

# AI Features Pages
@app.route('/ai-predictions')
def ai_predictions():
    """AI Predictions page"""
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('ai_predictions.html')

@app.route('/ai-chatbot')
def ai_chatbot():
    """AI Chatbot page"""
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('ai_chatbot.html')

@app.route('/analytics')
def analytics():
    """Analytics page"""
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('analytics.html')

@app.route('/reports')
def reports():
    """Reports page"""
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('reports.html')

@app.route('/patta-extractor')
def patta_extractor():
    """Patta Document Extractor page"""
    if not session.get('user'):
        return redirect(url_for('login'))
    return render_template('patta_extractor.html')

# Language support routes
@app.route('/set_language/<language>')
def set_language(language):
    """Set user's preferred language"""
    session['language'] = language
    return redirect(request.referrer or url_for('dashboard'))

@app.route('/api/translations/<language>')
def get_translations(language):
    """Get translations for specified language"""
    translations = {
        'tamil': {
            'dashboard_title': 'FRA சென்டினல் - முதன்மை கட்டுப்பாட்டு பலகை',
            'welcome': 'வரவேற்கிறோம்',
            'map': 'வரைபடம்',
            'admin': 'நிர்வாகம்',
            'logout': 'வெளியேறு',
            'language': 'மொழி',
            'states': 'மாநிலங்கள்',
            'districts': 'மாவட்டங்கள்',
            'villages': 'கிராமங்கள்',
            'tribal_areas': 'பழங்குடி பகுதிகள்'
        },
        'hindi': {
            'dashboard_title': 'FRA सेंटिनल - मुख्य डैशबोर्ड',
            'welcome': 'स्वागत है',
            'map': 'नक्शा',
            'admin': 'प्रशासन',
            'logout': 'लॉग आउट',
            'language': 'भाषा',
            'states': 'राज्य',
            'districts': 'जिले',
            'villages': 'गांव',
            'tribal_areas': 'आदिवासी क्षेत्र'
        },
        'telugu': {
            'dashboard_title': 'FRA సెంటినెల్ - ప్రధాన డ్యాష్‌బోర్డ్',
            'welcome': 'స్వాగతం',
            'map': 'మ్యాప్',
            'admin': 'అడ్మిన్',
            'logout': 'లాగ్ అవుట్',
            'language': 'భాష',
            'states': 'రాష్ట్రాలు',
            'districts': 'జిల్లాలు',
            'villages': 'గ్రామాలు',
            'tribal_areas': 'ఆదివాసీ ప్రాంతాలు'
        },
        'kannada': {
            'dashboard_title': 'FRA ಸೆಂಟಿನೆಲ್ - ಮುಖ್ಯ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್',
            'welcome': 'ಸ್ವಾಗತ',
            'map': 'ನಕ್ಷೆ',
            'admin': 'ಅಡ್ಮಿನ್',
            'logout': 'ಲಾಗ್ ಔಟ್',
            'language': 'ಭಾಷೆ',
            'states': 'ರಾಜ್ಯಗಳು',
            'districts': 'ಜಿಲ್ಲೆಗಳು',
            'villages': 'ಗ್ರಾಮಗಳು',
            'tribal_areas': 'ಆದಿವಾಸಿ ಪ್ರದೇಶಗಳು'
        },
        'malayalam': {
            'dashboard_title': 'FRA സെന്റിനൽ - പ്രധാന ഡാഷ്‌ബോർഡ്',
            'welcome': 'സ്വാഗതം',
            'map': 'മാപ്പ്',
            'admin': 'അഡ്മിൻ',
            'logout': 'ലോഗ് ഔട്ട്',
            'language': 'ഭാഷ',
            'states': 'സംസ്ഥാനങ്ങൾ',
            'districts': 'ജില്ലകൾ',
            'villages': 'ഗ്രാമങ്ങൾ',
            'tribal_areas': 'ആദിവാസി പ്രദേശങ്ങൾ'
        },
        'odia': {
            'dashboard_title': 'FRA ସେଣ୍ଟିନେଲ୍ - ମୁଖ୍ୟ ଡ୍ୟାସବୋର୍ଡ',
            'welcome': 'ସ୍ୱାଗତ',
            'map': 'ମାନଚିତ୍ର',
            'admin': 'ପ୍ରଶାସନ',
            'logout': 'ଲଗ୍ ଆଉଟ୍',
            'language': 'ଭାଷା',
            'states': 'ରାଜ୍ୟ',
            'districts': 'ଜିଲ୍ଲା',
            'villages': 'ଗ୍ରାମ',
            'tribal_areas': 'ଆଦିବାସୀ ଅଞ୍ଚଳ'
        },
        'bengali': {
            'dashboard_title': 'FRA সেন্টিনেল - মূল ড্যাশবোর্ড',
            'welcome': 'স্বাগতম',
            'map': 'মানচিত্র',
            'admin': 'প্রশাসন',
            'logout': 'লগ আউট',
            'language': 'ভাষা',
            'states': 'রাজ্য',
            'districts': 'জেলা',
            'villages': 'গ্রাম',
            'tribal_areas': 'আদিবাসী অঞ্চল'
        },
        'english': {
            'dashboard_title': 'FRA Sentinel - Main Dashboard',
            'welcome': 'Welcome',
            'map': 'Map',
            'admin': 'Admin',
            'logout': 'Logout',
            'language': 'Language',
            'states': 'States',
            'districts': 'Districts',
            'villages': 'Villages',
            'tribal_areas': 'Tribal Areas'
        }
    }
    return jsonify(translations.get(language, translations['english']))

# ----- Admin-only routes -----
def _is_admin_user():
    return session.get("user_role") in {"CCF", "DCF", "RFO"}

@app.route('/admin')
def admin():
    if not session.get("user"):
        return redirect(url_for("login"))
    if not _is_admin_user():
        return "Unauthorized", 403
    # Minimal example list (wire to DB if needed)
    files = []
    return render_template("manage_files.html", files=files)

@app.route('/upload_patta', methods=['GET', 'POST'])
def upload_patta():
    if not session.get("user"):
        return redirect(url_for("login"))
    if not _is_admin_user():
        return "Unauthorized", 403
    if request.method == 'POST':
        village = request.form.get('village', '').strip()
        patta_holder = request.form.get('patta_holder', '').strip()
        latitude = request.form.get('latitude')
        longitude = request.form.get('longitude')
        area_hectares = request.form.get('area_hectares')
        tribal_group = request.form.get('tribal_group', '').strip()
        family_size = request.form.get('family_size', '').strip()
        file = request.files.get('patta_file')

        if not file or not file.filename.lower().endswith('.pdf'):
            flash(('error', 'Please upload a PDF file.'))
            return render_template('admin_panel.html')

        os.makedirs(os.path.join(os.path.dirname(__file__), 'uploads'), exist_ok=True)
        save_path = os.path.join(os.path.dirname(__file__), 'uploads', file.filename)
        file.save(save_path)

        # Default values from form
        new_village = village
        new_holder = patta_holder
        try:
            new_lat = float(latitude)
            new_lon = float(longitude)
        except Exception:
            new_lat, new_lon = 0.0, 0.0
        try:
            new_area = float(area_hectares)
        except Exception:
            new_area = 0.0
        try:
            new_family_size = int(family_size) if family_size else 0
        except Exception:
            new_family_size = 0

        # Try OCR extraction if tools are available
        if pdf_to_text and extract_entities:
            try:
                text = pdf_to_text(save_path)
                ovillage, oholder, olat, olon = extract_entities(text)
                if ovillage:
                    new_village = ovillage
                if oholder:
                    new_holder = oholder
                if olat and olon:
                    new_lat, new_lon = float(olat), float(olon)
            except Exception:
                pass

        # Generate unique file ID
        import uuid
        file_id = f"FRA{str(uuid.uuid4())[:8].upper()}"

        # Append to map data so it shows immediately
        new_feature = {
            "type": "Feature",
            "properties": {
                "village": new_village or "Unknown",
                "patta_holder": new_holder or "Unknown",
                "latitude": new_lat,
                "longitude": new_lon,
                "area_hectares": new_area,
                "claim_status": "Verified",
                "uploaded_by": session.get("user"),
                "file_id": file_id,
                "tribal_group": tribal_group or "Unknown",
                "family_size": new_family_size,
                "file_name": file.filename,
                "upload_date": "2025-09-16T10:20:00"
            },
            "geometry": {
                "type": "Point",
                "coordinates": [new_lon, new_lat]
            }
        }
        
        TEST_VILLAGES["features"].append(new_feature)
        
        # Update metadata
        TEST_VILLAGES["metadata"]["total_records"] = len(TEST_VILLAGES["features"])
        TEST_VILLAGES["metadata"]["last_updated"] = "2025-09-16T10:20:00"

        flash(('success', f'✅ File {file.filename} uploaded successfully! Added {new_village} to map with coordinates ({new_lat}, {new_lon}).'))
        return redirect(url_for('admin_panel'))
    return render_template('admin_panel.html')

@app.route("/dashboard")
def dashboard():
    """Unified main dashboard for all users"""
    user = session.get("user")
    role = session.get("role")
    if not user:
        return redirect(url_for("login"))
    return render_template("dashboard.html", user=user, role=role, claims=PATTA_CLAIMS, enumerate=enumerate)

@app.route('/admin-dashboard')
def admin_dashboard():
    """Admin-only dashboard for CCF, DCF, RFO"""
    if not session.get('user'):
        return redirect(url_for('login'))
    if session.get('user_role') not in ['CCF', 'DCF', 'RFO']:
        flash('Access denied. Admin dashboard is only for CCF, DCF, and RFO officials.', 'error')
        return redirect(url_for('dashboard'))
    
    # Define role information
    role_info = {
        'name': session.get('user_role', 'Unknown'),
        'level': {'CCF': 3, 'DCF': 2, 'RFO': 1}.get(session.get('user_role'), 0)
    }
    
    return render_template('admin_dashboard.html', role_info=role_info)

@app.route('/admin_panel')
def admin_panel():
    """Admin panel for file management"""
    if not session.get('user'):
        return redirect(url_for('login'))
    if session.get('user_role') not in ['CCF', 'DCF', 'RFO']:
        flash('Access denied. Admin panel is only for CCF, DCF, and RFO officials.', 'error')
        return redirect(url_for('dashboard'))
    return render_template('admin_panel.html')

# Removed conflicting /upload route - using /upload_patta instead

@app.route('/api/claims', methods=['GET'])
def api_claims():
    role = session.get("role")
    if role == "public":
        # Only minimal view for public
        return jsonify([
            {
                "id": c["id"],
                "applicant_name": c["applicant_name"],
                "village": c["village"],
                "district": c["district"],
                "state": c["state"],
                "coordinates": c["coordinates"]
            } for c in PATTA_CLAIMS
        ])
    else:
        # Officials get full data
        return jsonify(PATTA_CLAIMS)

# ====== Dashboard API endpoints (to avoid 404s) ======
@app.route("/api/fra_data")
def api_fra_data():
    return jsonify(TEST_VILLAGES)

@app.route("/api/classification_stats")
def api_classification_stats():
    return jsonify(TEST_STATS)

@app.route("/api/dss_recommendation/<village>")
def api_dss_recommendation(village):
    # Minimal mocked recommendation
    return jsonify({
        "village_info": TEST_VILLAGES["features"][0]["properties"],
        "recommendations": [
            {
                "scheme": "PM-KISAN",
                "priority": "High",
                "reasons": ["Sufficient agricultural area", "Approved claim"],
                "benefit": "Rs. 6,000 annual support",
                "ministry": "Ministry of Agriculture",
                "eligibility_score": 85.0
            }
        ]
    })

@app.route("/api/system_status")
def api_system_status():
    return jsonify({
        "status": "online",
        "villages_loaded": len(TEST_VILLAGES.get("features", [])),
        "stats_loaded": len(TEST_STATS.keys()),
        "timestamp": "2025-09-01T12:31:00"
    })

# Boundary layer API endpoints
@app.route("/api/boundaries/<layer_type>")
def api_boundaries(layer_type):
    """Get boundary data for states, districts, villages, or tribal areas"""
    if layer_type in BOUNDARY_DATA:
        return jsonify(BOUNDARY_DATA[layer_type])
    return jsonify({"error": "Invalid layer type"}), 404

# FRA Atlas Drill-down API endpoints
@app.route("/api/fra-atlas/states")
def api_fra_states():
    """Get all states with summary statistics"""
    states_data = []
    for state_name, state_data in FRA_ATLAS_DATA["states"].items():
        total_pattas = 0
        total_area = 0
        districts_count = len(state_data["districts"])
        
        for district_name, district_data in state_data["districts"].items():
            for block_name, block_data in district_data["blocks"].items():
                for village_name, village_data in block_data["villages"].items():
                    total_pattas += len(village_data["patta_holders"])
                    total_area += sum(patta["area_hectares"] for patta in village_data["patta_holders"])
        
        states_data.append({
            "name": state_name,
            "districts_count": districts_count,
            "total_pattas": total_pattas,
            "total_area_hectares": total_area,
            "avg_forest_cover": 70.2  # Mock data
        })
    
    return jsonify({"states": states_data})

@app.route("/api/fra-atlas/states/<state_name>/districts")
def api_fra_districts(state_name):
    """Get districts for a specific state"""
    if state_name not in FRA_ATLAS_DATA["states"]:
        return jsonify({"error": "State not found"}), 404
    
    districts_data = []
    for district_name, district_data in FRA_ATLAS_DATA["states"][state_name]["districts"].items():
        total_pattas = 0
        total_area = 0
        blocks_count = len(district_data["blocks"])
        
        for block_name, block_data in district_data["blocks"].items():
            for village_name, village_data in block_data["villages"].items():
                total_pattas += len(village_data["patta_holders"])
                total_area += sum(patta["area_hectares"] for patta in village_data["patta_holders"])
        
        districts_data.append({
            "name": district_name,
            "blocks_count": blocks_count,
            "total_pattas": total_pattas,
            "total_area_hectares": total_area
        })
    
    return jsonify({"districts": districts_data})

@app.route("/api/fra-atlas/states/<state_name>/districts/<district_name>/blocks")
def api_fra_blocks(state_name, district_name):
    """Get blocks for a specific district"""
    if state_name not in FRA_ATLAS_DATA["states"]:
        return jsonify({"error": "State not found"}), 404
    if district_name not in FRA_ATLAS_DATA["states"][state_name]["districts"]:
        return jsonify({"error": "District not found"}), 404
    
    blocks_data = []
    for block_name, block_data in FRA_ATLAS_DATA["states"][state_name]["districts"][district_name]["blocks"].items():
        total_pattas = 0
        total_area = 0
        villages_count = len(block_data["villages"])
        
        for village_name, village_data in block_data["villages"].items():
            total_pattas += len(village_data["patta_holders"])
            total_area += sum(patta["area_hectares"] for patta in village_data["patta_holders"])
        
        blocks_data.append({
            "name": block_name,
            "villages_count": villages_count,
            "total_pattas": total_pattas,
            "total_area_hectares": total_area
        })
    
    return jsonify({"blocks": blocks_data})

@app.route("/api/fra-atlas/states/<state_name>/districts/<district_name>/blocks/<block_name>/villages")
def api_fra_villages(state_name, district_name, block_name):
    """Get villages for a specific block"""
    if state_name not in FRA_ATLAS_DATA["states"]:
        return jsonify({"error": "State not found"}), 404
    if district_name not in FRA_ATLAS_DATA["states"][state_name]["districts"]:
        return jsonify({"error": "District not found"}), 404
    if block_name not in FRA_ATLAS_DATA["states"][state_name]["districts"][district_name]["blocks"]:
        return jsonify({"error": "Block not found"}), 404
    
    villages_data = []
    for village_name, village_data in FRA_ATLAS_DATA["states"][state_name]["districts"][district_name]["blocks"][block_name]["villages"].items():
        villages_data.append({
            "name": village_name,
            "patta_holders_count": len(village_data["patta_holders"]),
            "total_area_hectares": sum(patta["area_hectares"] for patta in village_data["patta_holders"]),
            "forest_cover_percent": village_data["forest_cover"],
            "water_bodies_count": village_data["water_bodies"],
            "agricultural_land_percent": village_data["agricultural_land"],
            "coordinates": village_data["coordinates"]
        })
    
    return jsonify({"villages": villages_data})

@app.route("/api/fra-atlas/states/<state_name>/districts/<district_name>/blocks/<block_name>/villages/<village_name>/patta-holders")
def api_fra_patta_holders(state_name, district_name, block_name, village_name):
    """Get patta holders for a specific village"""
    if state_name not in FRA_ATLAS_DATA["states"]:
        return jsonify({"error": "State not found"}), 404
    if district_name not in FRA_ATLAS_DATA["states"][state_name]["districts"]:
        return jsonify({"error": "District not found"}), 404
    if block_name not in FRA_ATLAS_DATA["states"][state_name]["districts"][district_name]["blocks"]:
        return jsonify({"error": "Block not found"}), 404
    if village_name not in FRA_ATLAS_DATA["states"][state_name]["districts"][district_name]["blocks"][block_name]["villages"]:
        return jsonify({"error": "Village not found"}), 404
    
    village_data = FRA_ATLAS_DATA["states"][state_name]["districts"][district_name]["blocks"][block_name]["villages"][village_name]
    
    return jsonify({
        "village": village_name,
        "patta_holders": village_data["patta_holders"],
        "village_stats": {
            "forest_cover_percent": village_data["forest_cover"],
            "water_bodies_count": village_data["water_bodies"],
            "agricultural_land_percent": village_data["agricultural_land"]
        }
    })

# FRA Atlas Filters and Search API
@app.route("/api/fra-atlas/search")
def api_fra_search():
    """Search FRA data by various criteria"""
    query = request.args.get('q', '')
    filter_type = request.args.get('type', 'all')  # all, patta_holder, village, tribal_group
    status_filter = request.args.get('status', 'all')  # all, pending, verified, approved
    
    results = []
    
    for state_name, state_data in FRA_ATLAS_DATA["states"].items():
        for district_name, district_data in state_data["districts"].items():
            for block_name, block_data in district_data["blocks"].items():
                for village_name, village_data in block_data["villages"].items():
                    for patta in village_data["patta_holders"]:
                        # Apply filters
                        if status_filter != 'all' and patta["status"].lower() != status_filter.lower():
                            continue
                        
                        # Apply search query
                        if query.lower() in patta["name"].lower() or \
                           query.lower() in village_name.lower() or \
                           query.lower() in patta["tribal_group"].lower():
                            
                            results.append({
                                "patta_id": patta["id"],
                                "patta_holder": patta["name"],
                                "village": village_name,
                                "block": block_name,
                                "district": district_name,
                                "state": state_name,
                                "tribal_group": patta["tribal_group"],
                                "claim_type": patta["claim_type"],
                                "area_hectares": patta["area_hectares"],
                                "status": patta["status"],
                                "coordinates": patta["coordinates"]
                            })
    
    return jsonify({"results": results, "total": len(results)})

@app.route('/api/admin/real_stats')
def admin_real_stats():
    """Get real admin statistics"""
    # Count actual data from FRA_ATLAS_DATA
    total_claims = 0
    approved_claims = 0
    pending_claims = 0
    rejected_claims = 0
    
    for state_data in FRA_ATLAS_DATA["states"].values():
        for district_data in state_data["districts"].values():
            for block_data in district_data["blocks"].values():
                for village_data in block_data["villages"].values():
                    for patta_holder in village_data["patta_holders"]:
                        total_claims += 1
                        if patta_holder["status"] == "Approved":
                            approved_claims += 1
                        elif patta_holder["status"] == "Pending":
                            pending_claims += 1
                        else:
                            rejected_claims += 1
    
    return jsonify({
        "total_claims": total_claims,
        "approved_claims": approved_claims,
        "pending_claims": pending_claims,
        "rejected_claims": rejected_claims,
        "approval_rate": round((approved_claims / total_claims * 100) if total_claims > 0 else 0, 1),
        "system_uptime": 99.8,
        "response_time": 2.3,
        "storage_used": 1.2,
        "active_users": 45
    })

# Demo API endpoints for Hackathon Presentation
@app.route('/api/demo/patta-metrics')
def demo_patta_metrics():
    """Demo API for Patta document metrics"""
    if DEMO_DATA_AVAILABLE:
        return jsonify(get_demo_patta_metrics())
    else:
        return jsonify({"error": "Demo data not available"}), 500

@app.route('/api/demo/system-stats')
def demo_system_stats():
    """Demo API for system statistics"""
    if DEMO_DATA_AVAILABLE:
        return jsonify(get_demo_system_stats())
    else:
        return jsonify({"error": "Demo data not available"}), 500

@app.route('/api/demo/success-stories')
def demo_success_stories():
    """Demo API for success stories"""
    if DEMO_DATA_AVAILABLE:
        return jsonify(get_demo_success_stories())
    else:
        return jsonify({"error": "Demo data not available"}), 500

@app.route('/api/demo/patta-documents')
def demo_patta_documents():
    """Demo API for sample Patta documents"""
    if DEMO_DATA_AVAILABLE:
        return jsonify(get_demo_patta_documents())
    else:
        return jsonify({"error": "Demo data not available"}), 500

@app.route('/api/demo/ai-prediction')
def demo_ai_prediction():
    """Demo API for AI prediction results"""
    if DEMO_DATA_AVAILABLE:
        return jsonify(get_demo_ai_prediction())
    else:
        return jsonify({"error": "Demo data not available"}), 500

@app.route('/api/demo/chatbot-response')
def demo_chatbot_response():
    """Demo API for chatbot responses"""
    query_type = request.args.get('type', 'greeting')
    if DEMO_DATA_AVAILABLE:
        return jsonify({"response": get_demo_chatbot_response(query_type)})
    else:
        return jsonify({"error": "Demo data not available"}), 500

@app.route('/hackathon-demo')
def hackathon_demo():
    """Hackathon presentation demo page"""
    return render_template('hackathon_demo.html')

@app.route('/api/user_stats')
def user_stats():
    """API endpoint for user statistics"""
    try:
        # Get current user info
        user = session.get('user', 'Unknown')
        user_role = session.get('user_role', 'Unknown')
        
        # Calculate user-specific stats
        stats = {
            "user": user,
            "role": user_role,
            "login_time": session.get('login_time', 'Unknown'),
            "session_duration": "Active",
            "permissions": {
                "can_upload": user_role in ['CCF', 'DCF', 'RFO'],
                "can_manage": user_role in ['CCF', 'DCF'],
                "can_admin": user_role == 'CCF'
            },
            "activity": {
                "uploads_today": 0,
                "reports_generated": 0,
                "last_activity": "Just now"
            }
        }
        
        return jsonify(stats)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    try:
        app.run(debug=True, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Server error: {e}")

