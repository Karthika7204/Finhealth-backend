from datetime import datetime
from database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    business_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    analyses = db.relationship('Analysis', backref='user', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'business_name': self.business_name,
            'email': self.email,
            'phone': self.phone_number,
            'created_at': self.created_at.isoformat()
        }

class Analysis(db.Model):
    __tablename__ = 'analyses'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    credit_score = db.Column(db.Integer, nullable=False)
    risk_level = db.Column(db.String(50), nullable=False)
    confidence_score = db.Column(db.Integer, nullable=False)
    raw_result = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # New metrics
    total_revenue = db.Column(db.Float, default=0.0)
    total_expenses = db.Column(db.Float, default=0.0)
    net_profit = db.Column(db.Float, default=0.0)
    current_assets = db.Column(db.Float, default=0.0)
    current_liabilities = db.Column(db.Float, default=0.0)

    def to_dict(self):
        return {
            'id': self.id,
            'credit_score': self.credit_score,
            'riskLevel': self.risk_level,
            'confidence': self.confidence_score,
            'totalRevenue': self.total_revenue,
            'totalExpenses': self.total_expenses,
            'netProfit': self.net_profit,
            'currentAssets': self.current_assets,
            'currentLiabilities': self.current_liabilities,
            'rawResult': self.raw_result,
            'createdAt': self.created_at.isoformat()
        }
