import os
import json
import logging
import pandas as pd

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity
)

# Load .env ONLY for local development (NOT on Render)
if os.getenv("RENDER") is None:
    from dotenv import load_dotenv
    load_dotenv()

from database import init_db, db
from models import User, Analysis
from services.ai_service import analyze_financial_data
from services.data_service import extract_text_from_file


# --------------------------------------------------
# App & Config
# --------------------------------------------------

app = Flask(__name__)

# CORS (lock to frontend URL later)
CORS(app)

app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = os.environ.get("JWT_SECRET_KEY", "dev-secret")

# --------------------------------------------------
# Extensions
# --------------------------------------------------

bcrypt = Bcrypt(app)
jwt = JWTManager(app)
init_db(app)

# --------------------------------------------------
# Logging (Render-safe: stdout only)
# --------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)

# --------------------------------------------------
# JWT Error Handlers
# --------------------------------------------------

@jwt.invalid_token_loader
def invalid_token_callback(error):
    logging.warning(f"JWT INVALID: {error}")
    return jsonify({"message": f"Invalid token: {error}"}), 422

@jwt.unauthorized_loader
def missing_token_callback(error):
    logging.warning(f"JWT MISSING: {error}")
    return jsonify({"message": f"Missing token: {error}"}), 401

@jwt.expired_token_loader
def expired_token_callback(jwt_header, jwt_payload):
    logging.warning(f"JWT EXPIRED: {jwt_payload}")
    return jsonify({"message": "Token has expired"}), 401


# --------------------------------------------------
# AUTH ROUTES
# --------------------------------------------------


@app.route("/")
def home():
    return {"status": "FinHealth Backend is running"}

@app.route("/api/auth/register", methods=["POST"])
def register():
    data = request.get_json()

    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"message": "Email already exists"}), 400

    hashed_password = bcrypt.generate_password_hash(
        data["password"]
    ).decode("utf-8")

    new_user = User(
        business_name=data["businessName"],
        email=data["email"],
        phone_number=data.get("phone"),
        password_hash=hashed_password
    )

    try:
        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))

        return jsonify({
            "message": "Registration successful",
            "token": access_token,
            "user": new_user.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        logging.error(f"Registration error: {e}")
        return jsonify({"message": "Registration failed"}), 500


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if user and bcrypt.check_password_hash(user.password_hash, data["password"]):
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "message": "Login successful",
            "token": access_token,
            "user": user.to_dict()
        }), 200

    return jsonify({"message": "Invalid credentials"}), 401


# --------------------------------------------------
# CSV → Pandas Processing
# --------------------------------------------------

def process_csv_stats(file_storage):
    try:
        file_storage.seek(0)
        df = pd.read_csv(file_storage)
        file_storage.seek(0)

        df.columns = [c.strip().lower() for c in df.columns]
        logging.info(f"CSV columns: {df.columns.tolist()}")

        if "category" not in df.columns or "amount" not in df.columns:
            return None

        df["amount"] = (
            df["amount"]
            .astype(str)
            .str.replace(r"[$,]", "", regex=True)
        )
        df["amount"] = pd.to_numeric(df["amount"], errors="coerce").fillna(0)

        def sum_cat(keyword):
            return float(
                df[df["category"].str.contains(keyword, case=False, na=False)]
                ["amount"].sum()
            )

        stats = {
            "currentAssets": abs(sum_cat("assets")),
            "currentLiabilities": abs(sum_cat("liabilities")),
            "totalRevenue": abs(sum_cat("revenue"))
        }

        mask = df["category"].str.contains(
            "Revenue|Assets|Liabilities", case=False, na=False
        )
        stats["totalExpenses"] = abs(float(df[~mask]["amount"].sum()))
        stats["netProfit"] = stats["totalRevenue"] - stats["totalExpenses"]

        logging.info(f"Pandas stats: {stats}")
        return stats

    except Exception as e:
        logging.error(f"CSV processing error: {e}")
        return None


# --------------------------------------------------
# ANALYSIS ROUTES
# --------------------------------------------------

@app.route("/api/analyze", methods=["POST"])
@jwt_required()
def analyze():
    if "files" not in request.files:
        return jsonify({"message": "No files uploaded"}), 400

    files = request.files.getlist("files")
    combined_text = ""
    pandas_stats = None

    for file in files:
        if not file.filename:
            continue

        if file.filename.lower().endswith(".csv"):
            stats = process_csv_stats(file)
            if stats:
                pandas_stats = stats

        text = extract_text_from_file(file)
        combined_text += f"\n--- {file.filename} ---\n{text}\n"

    if not combined_text.strip():
        return jsonify({"message": "No extractable content"}), 400

    if pandas_stats:
        combined_text += (
            "\n--- TRUSTED FINANCIAL METRICS ---\n"
            + json.dumps(pandas_stats, indent=2)
        )

    try:
        analysis_result = analyze_financial_data(combined_text)

        if pandas_stats:
            analysis_result.update({
                "currentAssets": pandas_stats.get("currentAssets", 0),
                "currentLiabilities": pandas_stats.get("currentLiabilities", 0)
            })

        user_id = get_jwt_identity()

        new_analysis = Analysis(
            user_id=user_id,
            credit_score=analysis_result.get("creditScore", 0),
            risk_level=analysis_result.get("riskLevel", "unknown"),
            confidence_score=analysis_result.get("confidence", 0),
            total_revenue=analysis_result.get("totalRevenue", 0),
            total_expenses=analysis_result.get("totalExpenses", 0),
            net_profit=analysis_result.get("netProfit", 0),
            current_assets=analysis_result.get("currentAssets", 0),
            current_liabilities=analysis_result.get("currentLiabilities", 0),
            raw_result=analysis_result
        )

        db.session.add(new_analysis)
        db.session.commit()

        return jsonify(analysis_result), 200

    except Exception as e:
        logging.error(f"Analysis failed: {e}")
        return jsonify({"message": "Analysis failed"}), 500


# --------------------------------------------------
# REPORTS & DASHBOARD
# --------------------------------------------------

@app.route("/api/reports", methods=["GET"])
@jwt_required()
def get_reports():
    user_id = get_jwt_identity()
    analyses = Analysis.query.filter_by(user_id=user_id)\
        .order_by(Analysis.created_at.desc()).all()
    return jsonify([a.to_dict() for a in analyses])


@app.route("/api/reports/<int:report_id>/download", methods=["GET"])
@jwt_required()
def download_report(report_id):
    user_id = get_jwt_identity()
    analysis = Analysis.query.filter_by(
        id=report_id,
        user_id=user_id
    ).first()

    if not analysis:
        return jsonify({"message": "Report not found"}), 404

    from services.pdf_service import generate_report_pdf

    pdf_content = generate_report_pdf(
        db.session.get(User, user_id),
        analysis
    )

    response = make_response(
        pdf_content.encode("latin-1", errors="replace")
    )
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = \
        f"attachment; filename=report_{report_id}.pdf"

    return response


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


# --------------------------------------------------
# Local Dev Only
# --------------------------------------------------

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
