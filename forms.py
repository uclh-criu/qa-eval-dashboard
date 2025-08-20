from flask_wtf import FlaskForm
from wtforms import TextAreaField, IntegerField, SubmitField, StringField, PasswordField
from wtforms.validators import DataRequired, NumberRange, Optional, Length

class FeedbackForm(FlaskForm):
    # Text feedback
    text_feedback = TextAreaField('General Feedback', 
                                validators=[Optional()],
                                render_kw={"placeholder": "Provide any general feedback about this answer...", "rows": 4})
    
    # Structured feedback (1-5 scale)
    accuracy_score = IntegerField('Accuracy Score (1-5)', 
                                validators=[Optional(), NumberRange(min=1, max=5)],
                                render_kw={"placeholder": "Rate accuracy from 1 (poor) to 5 (excellent)"})
    
    completeness_score = IntegerField('Completeness Score (1-5)', 
                                    validators=[Optional(), NumberRange(min=1, max=5)],
                                    render_kw={"placeholder": "Rate completeness from 1 (poor) to 5 (excellent)"})
    
    clarity_score = IntegerField('Clarity Score (1-5)', 
                               validators=[Optional(), NumberRange(min=1, max=5)],
                               render_kw={"placeholder": "Rate clarity from 1 (poor) to 5 (excellent)"})
    
    clinical_relevance_score = IntegerField('Clinical Relevance Score (1-5)', 
                                          validators=[Optional(), NumberRange(min=1, max=5)],
                                          render_kw={"placeholder": "Rate clinical relevance from 1 (poor) to 5 (excellent)"})
    
    # Gold standard answer
    gold_standard_answer = TextAreaField('Gold Standard Answer', 
                                       validators=[Optional()],
                                       render_kw={"placeholder": "Edit the answer to provide what you think the ideal response should be...", "rows": 6})
    
    submit = SubmitField('Submit Feedback')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Sign In')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Register')
