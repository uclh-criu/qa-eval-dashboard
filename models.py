from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# Association table for user-dataset access
user_dataset_access = db.Table('user_dataset_access',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id'), primary_key=True),
    db.Column('dataset_id', db.Integer, db.ForeignKey('dataset.id'), primary_key=True)
)

class Dataset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to Q&A pairs
    qa_pairs = db.relationship('QuestionAnswerPair', backref='dataset', lazy=True)
    
    # Relationship to users who have access to this dataset
    authorized_users = db.relationship('User', secondary=user_dataset_access, back_populates='accessible_datasets')
    
    def __repr__(self):
        return f'<Dataset {self.name}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    access_level = db.Column(db.String(20), nullable=False, default='user')  # 'user' or 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to feedback
    feedback = db.relationship('Feedback', backref='user', lazy=True)
    
    # Relationship to accessible datasets
    accessible_datasets = db.relationship('Dataset', secondary=user_dataset_access, back_populates='authorized_users')
    
    def check_password(self, password):
        """Check if provided password matches"""
        return self.password == password
    
    def has_dataset_access(self, dataset_id):
        """Check if user has access to a specific dataset"""
        # Admins have access to all datasets
        if self.is_admin():
            return True
        return any(dataset.id == dataset_id for dataset in self.accessible_datasets)
    
    def is_admin(self):
        """Check if user has admin access"""
        return self.access_level == 'admin'
    
    def __repr__(self):
        return f'<User {self.username}>'

class QuestionAnswerPair(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    system_answer_text = db.Column(db.Text, nullable=False)
    original_qa_id = db.Column(db.String(255), nullable=True)  # User-provided ID
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to feedback
    feedback = db.relationship('Feedback', backref='qa_pair', lazy=True)
    
    def __repr__(self):
        return f'<QuestionAnswerPair {self.id}>'

class Feedback(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    qa_pair_id = db.Column(db.Integer, db.ForeignKey('question_answer_pair.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)  # Optional for now
    
    # Text feedback
    text_feedback = db.Column(db.Text, nullable=True)
    
    # Structured feedback (1-5 scale)
    accuracy_score = db.Column(db.Integer, nullable=True)
    completeness_score = db.Column(db.Integer, nullable=True)
    clarity_score = db.Column(db.Integer, nullable=True)
    clinical_relevance_score = db.Column(db.Integer, nullable=True)
    
    # Gold standard answer (edited version)
    gold_standard_answer = db.Column(db.Text, nullable=True)
    
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Feedback {self.id} for QA {self.qa_pair_id}>'
