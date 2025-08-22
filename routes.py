from flask import render_template, request, redirect, url_for, flash, jsonify, abort, send_file
from flask_login import login_user, login_required, logout_user, current_user
from models import QuestionAnswerPair, Feedback, User, Dataset, db
from forms import FeedbackForm, LoginForm, RegisterForm
from functools import wraps
from datetime import datetime
import json
import csv
import io
import os
from werkzeug.utils import secure_filename

def admin_required(f):
    """Decorator to require admin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            abort(403)  # Forbidden
        return f(*args, **kwargs)
    return decorated_function

# This will be imported by app.py and the routes will be registered with the app
def register_routes(app):
    # Admin API endpoints
    @app.route('/api/admin/user/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    @admin_required
    def api_admin_user(user_id):
        """Get or update user details (admin only)"""
        user = User.query.get_or_404(user_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'access_level': user.access_level,
                    'created_at': user.created_at.isoformat() if user.created_at else None
                }
            })
        elif request.method == 'DELETE':
            try:
                # Prevent deleting the last admin user
                if user.is_admin():
                    admin_count = User.query.filter_by(access_level='admin').count()
                    if admin_count <= 1:
                        return jsonify({
                            'success': False,
                            'message': 'Cannot delete the last admin user'
                        })

                # Delete user's feedback
                Feedback.query.filter_by(user_id=user.id).delete()
                
                # Remove user from datasets
                for dataset in user.accessible_datasets:
                    dataset.authorized_users.remove(user)
                
                # Delete the user
                db.session.delete(user)
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'User deleted successfully'
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'message': f'Error deleting user: {str(e)}'
                })
        
        else:  # PUT
            try:
                data = request.get_json()
                
                # Validate required data
                if not data:
                    return jsonify({'success': False, 'message': 'No data provided'})
                
                # Update username if provided
                if 'username' in data:
                    new_username = data['username'].strip()
                    if not new_username:
                        return jsonify({'success': False, 'message': 'Username cannot be empty'})
                    
                    # Check if username already exists (for a different user)
                    existing_user = User.query.filter_by(username=new_username).first()
                    if existing_user and existing_user.id != user_id:
                        return jsonify({'success': False, 'message': 'Username already exists'})
                    
                    user.username = new_username
                
                # Update access level if provided
                if 'access_level' in data:
                    access_level = data['access_level']
                    if access_level not in ['user', 'admin']:
                        return jsonify({'success': False, 'message': 'Invalid access level'})
                    
                    user.access_level = access_level
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'User updated successfully',
                    'user': {
                        'id': user.id,
                        'username': user.username,
                        'access_level': user.access_level
                    }
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error updating user: {str(e)}'})
    
    @app.route('/api/admin/user/<int:user_id>/datasets', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def api_admin_user_datasets(user_id):
        """Get or update datasets accessible to a user (admin only)"""
        user = User.query.get_or_404(user_id)
        
        if request.method == 'GET':
            # Get user's current datasets
            user_datasets = user.accessible_datasets
            
            # Get datasets user doesn't have access to
            all_datasets = Dataset.query.all()
            available_datasets = [d for d in all_datasets if d not in user_datasets]
            
            return jsonify({
                'success': True,
                'user_datasets': [{
                    'id': dataset.id,
                    'name': dataset.name,
                    'description': dataset.description
                } for dataset in user_datasets],
                'available_datasets': [{
                    'id': dataset.id,
                    'name': dataset.name,
                    'description': dataset.description
                } for dataset in available_datasets]
            })
        else:  # POST
            try:
                data = request.get_json()
                
                # Validate required data
                if not data or 'dataset_ids' not in data:
                    return jsonify({'success': False, 'message': 'Dataset IDs required'})
                
                dataset_ids = data['dataset_ids']
                if not isinstance(dataset_ids, list):
                    return jsonify({'success': False, 'message': 'Dataset IDs must be an array'})
                
                # Add datasets to user
                for dataset_id in dataset_ids:
                    dataset = Dataset.query.get(dataset_id)
                    if dataset and dataset not in user.accessible_datasets:
                        user.accessible_datasets.append(dataset)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Datasets added to user successfully'
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error adding datasets: {str(e)}'})
    
    @app.route('/api/admin/user/<int:user_id>/datasets/<int:dataset_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def api_admin_user_dataset_delete(user_id, dataset_id):
        """Remove dataset access from a user (admin only)"""
        try:
            user = User.query.get_or_404(user_id)
            dataset = Dataset.query.get_or_404(dataset_id)
            
            if dataset in user.accessible_datasets:
                user.accessible_datasets.remove(dataset)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Dataset removed from user successfully'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error removing dataset: {str(e)}'})
    
    @app.route('/api/admin/dataset/<int:dataset_id>/users', methods=['GET', 'POST'])
    @login_required
    @admin_required
    def api_admin_dataset_users(dataset_id):
        """Get or update users with access to a dataset (admin only)"""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        if request.method == 'GET':
            return jsonify({
                'success': True,
                'users': [{
                    'id': user.id,
                    'username': user.username,
                    'access_level': user.access_level
                } for user in dataset.authorized_users]
            })
        else:  # POST
            try:
                data = request.get_json()
                
                # Validate required data
                if not data or 'user_ids' not in data:
                    return jsonify({'success': False, 'message': 'User IDs required'})
                
                user_ids = data['user_ids']
                if not isinstance(user_ids, list):
                    return jsonify({'success': False, 'message': 'User IDs must be an array'})
                
                # Add users to dataset
                for user_id in user_ids:
                    user = User.query.get(user_id)
                    if user and user not in dataset.authorized_users:
                        dataset.authorized_users.append(user)
                
                db.session.commit()
                
                return jsonify({
                    'success': True,
                    'message': 'Users added to dataset successfully'
                })
            except Exception as e:
                db.session.rollback()
                return jsonify({'success': False, 'message': f'Error adding users: {str(e)}'})
    
    @app.route('/api/admin/dataset/<int:dataset_id>/users/<int:user_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def api_admin_dataset_user_delete(dataset_id, user_id):
        """Remove user access from a dataset (admin only)"""
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            user = User.query.get_or_404(user_id)
            
            if user in dataset.authorized_users:
                dataset.authorized_users.remove(user)
                db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'User removed from dataset successfully'
            })
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error removing user: {str(e)}'})
    
    @app.route('/api/admin/users/search')
    @login_required
    @admin_required
    def api_admin_users_search():
        """Search for users (admin only)"""
        search_term = request.args.get('q', '').strip()
        dataset_id = request.args.get('dataset_id')
        
        if not search_term:
            return jsonify({
                'success': False,
                'message': 'Search term required'
            })
        
        # Search users by username
        users = User.query.filter(User.username.ilike(f'%{search_term}%')).all()
        
        # If dataset_id provided, check which users already have access
        if dataset_id:
            dataset = Dataset.query.get(dataset_id)
            if dataset:
                dataset_users = dataset.authorized_users
                result = [{
                    'id': user.id,
                    'username': user.username,
                    'access_level': user.access_level,
                    'has_access': user in dataset_users
                } for user in users]
            else:
                result = [{
                    'id': user.id,
                    'username': user.username,
                    'access_level': user.access_level,
                    'has_access': False
                } for user in users]
        else:
            result = [{
                'id': user.id,
                'username': user.username,
                'access_level': user.access_level
            } for user in users]
        
        return jsonify({
            'success': True,
            'users': result
        })
        
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            if user and user.check_password(form.password.data):
                login_user(user)
                flash('Logged in successfully!', 'success')
                next_page = request.args.get('next')
                return redirect(next_page) if next_page else redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('auth/login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        """User logout"""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))
    
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page"""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = RegisterForm()
        if form.validate_on_submit():
            # Check if username already exists
            if User.query.filter_by(username=form.username.data).first():
                flash('Username already exists', 'error')
                return render_template('auth/register.html', form=form)
            
            # Create new user - make first user admin
            user_count = User.query.count()
            user = User(
                username=form.username.data,
                password=form.password.data,
                access_level='admin' if user_count == 0 else 'user'
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        
        return render_template('auth/register.html', form=form)

    @app.route('/')
    @app.route('/dataset/<int:dataset_id>')
    @login_required
    def index(dataset_id=None):
        """Main page showing list of Q&A pairs"""
        # Get datasets user has access to
        user_datasets = current_user.accessible_datasets
        
        if not user_datasets:
            flash('You do not have access to any datasets. Please contact an administrator.', 'warning')
            return render_template('index.html', qa_pairs=[], datasets=[], current_dataset=None)
        
        if dataset_id is None:
            dataset_id = user_datasets[0].id
        else:
            # Check if user has access to this dataset
            if not current_user.has_dataset_access(dataset_id):
                flash('You do not have access to this dataset.', 'error')
                return redirect(url_for('index'))
        
        current_dataset = Dataset.query.get_or_404(dataset_id)
        qa_pairs = QuestionAnswerPair.query.filter_by(dataset_id=dataset_id).order_by(QuestionAnswerPair.created_at.desc()).all()
        
        # Add user-specific feedback information to each Q&A pair
        qa_pairs_with_user_feedback = []
        for qa in qa_pairs:
            user_feedback = [f for f in qa.feedback if f.user_id == current_user.id]
            qa.user_feedback_count = len(user_feedback)
            qa.user_has_gold_standard = any(f.gold_standard_answer for f in user_feedback)
            qa_pairs_with_user_feedback.append(qa)
        
        return render_template('index.html', qa_pairs=qa_pairs_with_user_feedback, datasets=user_datasets, current_dataset=current_dataset)

    @app.route('/qa/<int:qa_id>')
    def view_qa(qa_id):
        """View a specific Q&A pair with feedback form"""
        qa_pair = QuestionAnswerPair.query.get_or_404(qa_id)
        form = FeedbackForm()
        
        # Get existing feedback for this Q&A pair
        existing_feedback = Feedback.query.filter_by(qa_pair_id=qa_id).order_by(Feedback.submitted_at.desc()).all()
        
        return render_template('feedback.html', qa_pair=qa_pair, form=form, existing_feedback=existing_feedback)

    @app.route('/submit_feedback/<int:qa_id>', methods=['POST'])
    def submit_feedback(qa_id):
        """Submit feedback for a Q&A pair"""
        qa_pair = QuestionAnswerPair.query.get_or_404(qa_id)
        form = FeedbackForm()
        
        if form.validate_on_submit():
            feedback = Feedback(
                qa_pair_id=qa_id,
                text_feedback=form.text_feedback.data,
                accuracy_score=form.accuracy_score.data,
                completeness_score=form.completeness_score.data,
                clarity_score=form.clarity_score.data,
                clinical_relevance_score=form.clinical_relevance_score.data,
                gold_standard_answer=form.gold_standard_answer.data
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            flash('Thank you! Your feedback has been submitted successfully.', 'success')
            return redirect(url_for('view_qa', qa_id=qa_id))
        else:
            flash('Please check your input and try again.', 'error')
            existing_feedback = Feedback.query.filter_by(qa_pair_id=qa_id).order_by(Feedback.submitted_at.desc()).all()
            return render_template('feedback.html', qa_pair=qa_pair, form=form, existing_feedback=existing_feedback)

    @app.route('/admin')
    @login_required
    @admin_required
    def admin():
        """Admin dashboard showing datasets and user management"""
        # Get all datasets with stats
        datasets = Dataset.query.all()
        dataset_stats = []
        for dataset in datasets:
            qa_count = len(dataset.qa_pairs)
            feedback_count = sum(len(qa.feedback) for qa in dataset.qa_pairs)
            user_count = len(dataset.authorized_users)
            dataset_stats.append({
                'dataset': dataset,
                'qa_count': qa_count,
                'feedback_count': feedback_count,
                'user_count': user_count
            })
        
        # Get all users with stats
        users = User.query.order_by(User.created_at.desc()).all()
        user_stats = []
        for user in users:
            feedback_count = len(user.feedback)
            dataset_count = len(user.accessible_datasets)
            user_stats.append({
                'user': user,
                'feedback_count': feedback_count,
                'dataset_count': dataset_count
            })
        
        # Overall stats
        total_users = User.query.count()
        total_datasets = Dataset.query.count()
        total_qa_pairs = QuestionAnswerPair.query.count()
        total_feedback = Feedback.query.count()
        
        return render_template('admin.html', 
                             dataset_stats=dataset_stats,
                             user_stats=user_stats,
                             total_users=total_users,
                             total_datasets=total_datasets,
                             total_qa_pairs=total_qa_pairs,
                             total_feedback=total_feedback)

    @app.route('/datasets')
    @login_required
    def datasets():
        """Datasets management page"""
        # Admins can see all datasets, regular users see only their accessible datasets
        if current_user.is_admin():
            user_datasets = Dataset.query.all()
        else:
            user_datasets = current_user.accessible_datasets
        
        # Calculate statistics for each dataset
        datasets_info = []
        total_qa_pairs = 0
        user_feedback_count = 0
        user_gold_standards = 0
        
        for dataset in user_datasets:
            qa_count = len(dataset.qa_pairs)
            total_qa_pairs += qa_count
            
            # Count user's feedback for this dataset
            user_feedback_for_dataset = 0
            user_gold_standards_for_dataset = 0
            
            for qa in dataset.qa_pairs:
                user_feedback_list = [f for f in qa.feedback if f.user_id == current_user.id]
                if user_feedback_list:
                    user_feedback_for_dataset += len(user_feedback_list)
                    if any(f.gold_standard_answer for f in user_feedback_list):
                        user_gold_standards_for_dataset += 1
            
            user_feedback_count += user_feedback_for_dataset
            user_gold_standards += user_gold_standards_for_dataset
            
            datasets_info.append({
                'dataset': dataset,
                'qa_count': qa_count,
                'user_feedback_count': user_feedback_for_dataset,
                'user_gold_standards': user_gold_standards_for_dataset
            })
        
        return render_template('datasets.html', 
                             datasets=datasets_info,
                             total_qa_pairs=total_qa_pairs,
                             user_feedback_count=user_feedback_count,
                             user_gold_standards=user_gold_standards)

    @app.route('/api/upload_dataset', methods=['POST'])
    @login_required
    def api_upload_dataset():
        """Upload and process a new dataset"""
        try:
            # Validate form data
            if 'dataset_file' not in request.files:
                return jsonify({'success': False, 'message': 'No file uploaded'})
            
            file = request.files['dataset_file']
            dataset_name = request.form.get('dataset_name', '').strip()
            dataset_description = request.form.get('dataset_description', '').strip()
            
            if not file or file.filename == '':
                return jsonify({'success': False, 'message': 'No file selected'})
            
            if not dataset_name:
                return jsonify({'success': False, 'message': 'Dataset name is required'})
            
            # Check if dataset name already exists
            if Dataset.query.filter_by(name=dataset_name).first():
                return jsonify({'success': False, 'message': 'Dataset name already exists'})
            
            # Validate file type
            filename = secure_filename(file.filename)
            if not filename.lower().endswith(('.json', '.csv')):
                return jsonify({'success': False, 'message': 'Only JSON and CSV files are supported'})
            
            # Read and parse file content
            file_content = file.read().decode('utf-8')
            qa_pairs_data = []
            
            if filename.lower().endswith('.json'):
                try:
                    data = json.loads(file_content)
                    if not isinstance(data, list):
                        return jsonify({'success': False, 'message': 'JSON must be an array of objects'})
                    
                    for item in data:
                        if not isinstance(item, dict) or 'question' not in item or 'answer' not in item:
                            return jsonify({'success': False, 'message': 'Each JSON object must have "question" and "answer" fields'})
                        
                        # Parse optional fields
                        original_id = item.get('id', item.get('original_id'))
                        timestamp_str = item.get('timestamp', item.get('created_at'))
                        timestamp = None
                        if timestamp_str:
                            try:
                                from dateutil import parser
                                timestamp = parser.parse(timestamp_str)
                            except:
                                # If parsing fails, use current time
                                timestamp = datetime.utcnow()
                        
                        qa_pairs_data.append({
                            'question': str(item['question']).strip(),
                            'answer': str(item['answer']).strip(),
                            'original_id': str(original_id).strip() if original_id else None,
                            'timestamp': timestamp
                        })
                except json.JSONDecodeError as e:
                    return jsonify({'success': False, 'message': f'Invalid JSON format: {str(e)}'})
            
            elif filename.lower().endswith('.csv'):
                try:
                    csv_reader = csv.DictReader(io.StringIO(file_content))
                    
                    # Check if required columns exist
                    if 'question' not in csv_reader.fieldnames or 'answer' not in csv_reader.fieldnames:
                        return jsonify({'success': False, 'message': 'CSV must have "question" and "answer" columns'})
                    
                    for row in csv_reader:
                        if not row['question'].strip() or not row['answer'].strip():
                            continue  # Skip empty rows
                        
                        # Parse optional fields
                        original_id = row.get('id', row.get('original_id', ''))
                        timestamp_str = row.get('timestamp', row.get('created_at', ''))
                        timestamp = None
                        if timestamp_str.strip():
                            try:
                                from dateutil import parser
                                timestamp = parser.parse(timestamp_str.strip())
                            except:
                                # If parsing fails, use current time
                                timestamp = datetime.utcnow()
                        
                        qa_pairs_data.append({
                            'question': row['question'].strip(),
                            'answer': row['answer'].strip(),
                            'original_id': original_id.strip() if original_id.strip() else None,
                            'timestamp': timestamp
                        })
                except Exception as e:
                    return jsonify({'success': False, 'message': f'Error reading CSV: {str(e)}'})
            
            if not qa_pairs_data:
                return jsonify({'success': False, 'message': 'No valid Q&A pairs found in the file'})
            
            # Create new dataset
            new_dataset = Dataset(
                name=dataset_name,
                description=dataset_description if dataset_description else None
            )
            db.session.add(new_dataset)
            db.session.flush()  # Get the dataset ID
            
            # Add Q&A pairs to the dataset
            for qa_data in qa_pairs_data:
                qa_pair = QuestionAnswerPair(
                    dataset_id=new_dataset.id,
                    question_text=qa_data['question'],
                    system_answer_text=qa_data['answer'],
                    original_qa_id=qa_data.get('original_id'),
                    created_at=qa_data.get('timestamp') or datetime.utcnow()
                )
                db.session.add(qa_pair)
            
            # Grant access to the current user (and admins get access to everything)
            new_dataset.authorized_users.append(current_user)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Dataset "{dataset_name}" uploaded successfully with {len(qa_pairs_data)} Q&A pairs',
                'dataset_id': new_dataset.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Upload failed: {str(e)}'})

    @app.route('/api/download_dataset/<int:dataset_id>')
    @login_required
    def api_download_dataset(dataset_id):
        """Download dataset in JSON or CSV format with customizable options"""
        try:
            # Check access permission
            if not current_user.has_dataset_access(dataset_id):
                return jsonify({'error': 'Access denied'}), 403
            
            dataset = Dataset.query.get_or_404(dataset_id)
            format_type = request.args.get('format', 'json').lower()
            
            if format_type not in ['json', 'csv']:
                return jsonify({'error': 'Invalid format. Use json or csv'}), 400
            
            # Parse download options
            include_gold_standards = request.args.get('include_gold_standards', 'false').lower() == 'true'
            include_scores = request.args.get('include_scores', 'false').lower() == 'true'
            include_text_feedback = request.args.get('include_text_feedback', 'false').lower() == 'true'
            user_ids_param = request.args.get('user_ids', '')
            
            # Parse user IDs filter
            selected_user_ids = None
            if user_ids_param and user_ids_param != 'all':
                try:
                    selected_user_ids = [int(uid.strip()) for uid in user_ids_param.split(',') if uid.strip()]
                except ValueError:
                    return jsonify({'error': 'Invalid user_ids format'}), 400
            
            qa_pairs = QuestionAnswerPair.query.filter_by(dataset_id=dataset_id).all()
            
            if format_type == 'json':
                # Generate JSON export
                export_data = []
                for qa in qa_pairs:
                    qa_data = {
                        'id': qa.id,
                        'question': qa.question_text,
                        'answer': qa.system_answer_text,
                        'created_at': qa.created_at.isoformat()
                    }
                    
                    # Add original_qa_id if it exists
                    if qa.original_qa_id:
                        qa_data['original_qa_id'] = qa.original_qa_id
                    
                    # Add feedback if any options are selected
                    if include_gold_standards or include_scores or include_text_feedback:
                        qa_data['feedback_entries'] = []
                        
                        # Filter feedback by user IDs if specified
                        feedback_list = qa.feedback
                        if selected_user_ids is not None:
                            feedback_list = [f for f in feedback_list if f.user_id in selected_user_ids]
                        
                        for feedback in feedback_list:
                            feedback_data = {
                            'feedback_id': feedback.id,
                            'user_id': feedback.user_id,
                            'username': feedback.user.username if feedback.user else None,
                            'submitted_at': feedback.submitted_at.isoformat() if feedback.submitted_at else None
                            }
                            
                            if include_text_feedback and feedback.text_feedback:
                                feedback_data['text_feedback'] = feedback.text_feedback
                            
                            if include_scores:
                                if feedback.accuracy_score:
                                    feedback_data['accuracy_score'] = feedback.accuracy_score
                                if feedback.completeness_score:
                                    feedback_data['completeness_score'] = feedback.completeness_score
                                if feedback.clarity_score:
                                    feedback_data['clarity_score'] = feedback.clarity_score
                                if feedback.clinical_relevance_score:
                                    feedback_data['clinical_relevance_score'] = feedback.clinical_relevance_score
                            
                            if include_gold_standards and feedback.gold_standard_answer:
                                feedback_data['gold_standard_answer'] = feedback.gold_standard_answer
                            
                            qa_data['feedback_entries'].append(feedback_data)
                    
                    export_data.append(qa_data)
                
                # Create file-like object
                output = io.StringIO()
                json.dump(export_data, output, indent=2)
                output.seek(0)
                
                # Convert to bytes
                output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
                output_bytes.seek(0)
                
                return send_file(
                    output_bytes,
                    mimetype='application/json',
                    as_attachment=True,
                    download_name=f'{dataset.name}_feedback.json'
                )
            
            else:  # CSV format
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Determine if we're doing individual feedback rows or aggregated
                has_feedback_options = include_gold_standards or include_scores or include_text_feedback
                multiple_users = selected_user_ids is None or len(selected_user_ids) != 1
                
                if has_feedback_options and multiple_users:
                    # Individual feedback rows (one row per QA-user pair)
                    headers = ['qa_id', 'question', 'answer', 'created_at']
                    has_original_ids = any(qa.original_qa_id for qa in qa_pairs)
                    if has_original_ids:
                        headers.append('original_qa_id')
                    headers.extend(['user_id', 'username', 'submitted_at'])
                    
                    if include_text_feedback:
                        headers.append('text_feedback')
                    if include_scores:
                        headers.extend(['accuracy_score', 'completeness_score', 'clarity_score', 'clinical_relevance_score'])
                    if include_gold_standards:
                        headers.append('gold_standard_answer')
                    
                    writer.writerow(headers)
                    
                    # Write data rows
                    for qa in qa_pairs:
                        # Filter feedback by user IDs if specified
                        feedback_list = qa.feedback
                        if selected_user_ids is not None:
                            feedback_list = [f for f in feedback_list if f.user_id in selected_user_ids]
                        
                        for feedback in feedback_list:
                            row = [
                        qa.id,
                        qa.question_text,
                        qa.system_answer_text,
                                qa.created_at.strftime('%Y-%m-%d %H:%M:%S')
                            ]
                            
                            if has_original_ids:
                                row.append(qa.original_qa_id or '')
                            
                            row.extend([
                                feedback.user_id,
                                feedback.user.username if feedback.user else '',
                                feedback.submitted_at.strftime('%Y-%m-%d %H:%M:%S') if feedback.submitted_at else ''
                            ])
                            
                            if include_text_feedback:
                                row.append(feedback.text_feedback or '')
                            if include_scores:
                                row.extend([
                                    feedback.accuracy_score or '',
                                    feedback.completeness_score or '',
                                    feedback.clarity_score or '',
                                    feedback.clinical_relevance_score or ''
                                ])
                            if include_gold_standards:
                                row.append(feedback.gold_standard_answer or '')
                            
                            writer.writerow(row)
                else:
                    # Aggregated format (one row per QA pair)
                    headers = ['id', 'question', 'answer', 'created_at']
                    has_original_ids = any(qa.original_qa_id for qa in qa_pairs)
                    if has_original_ids:
                        headers.append('original_qa_id')
                    
                    if has_feedback_options:
                        headers.append('feedback_count')
                        if include_scores:
                            headers.extend(['avg_accuracy', 'avg_completeness', 'avg_clarity', 'avg_clinical_relevance'])
                        if include_text_feedback:
                            headers.append('text_feedback_combined')
                        if include_gold_standards:
                            headers.append('gold_standards_combined')
                    
                    writer.writerow(headers)
                    
                    # Write data
                    for qa in qa_pairs:
                        row = [qa.id, qa.question_text, qa.system_answer_text, qa.created_at.strftime('%Y-%m-%d %H:%M:%S')]
                        
                        if has_original_ids:
                            row.append(qa.original_qa_id or '')
                        
                        if has_feedback_options:
                            # Filter feedback by user IDs if specified
                            feedback_list = qa.feedback
                            if selected_user_ids is not None:
                                feedback_list = [f for f in feedback_list if f.user_id in selected_user_ids]
                            
                            row.append(len(feedback_list))
                            
                            if include_scores:
                                feedback_scores = {
                                    'accuracy': [f.accuracy_score for f in feedback_list if f.accuracy_score],
                                    'completeness': [f.completeness_score for f in feedback_list if f.completeness_score],
                                    'clarity': [f.clarity_score for f in feedback_list if f.clarity_score],
                                    'clinical_relevance': [f.clinical_relevance_score for f in feedback_list if f.clinical_relevance_score]
                                }
                                
                                for score_type in ['accuracy', 'completeness', 'clarity', 'clinical_relevance']:
                                    scores = feedback_scores[score_type]
                                    avg_score = round(sum(scores) / len(scores), 2) if scores else ''
                                    row.append(avg_score)
                            
                            if include_text_feedback:
                                text_feedback = [f.text_feedback for f in feedback_list if f.text_feedback]
                                combined_text = ' | '.join(text_feedback) if text_feedback else ''
                                row.append(combined_text)
                            
                            if include_gold_standards:
                                gold_standards = [f.gold_standard_answer for f in feedback_list if f.gold_standard_answer]
                                combined_gold = ' | '.join(gold_standards) if gold_standards else ''
                                row.append(combined_gold)
                        
                        writer.writerow(row)
                
                output.seek(0)
                output_bytes = io.BytesIO(output.getvalue().encode('utf-8'))
                output_bytes.seek(0)
                
                return send_file(
                    output_bytes,
                    mimetype='text/csv',
                    as_attachment=True,
                    download_name=f'{dataset.name}_feedback.csv'
                )
        
        except Exception as e:
            return jsonify({'error': f'Download failed: {str(e)}'}), 500

    @app.route('/api/delete_dataset/<int:dataset_id>', methods=['DELETE'])
    @login_required
    @admin_required
    def api_delete_dataset(dataset_id):
        """Delete a dataset (admin only)"""
        try:
            dataset = Dataset.query.get_or_404(dataset_id)
            
            # Delete all associated Q&A pairs and feedback
            qa_pairs = QuestionAnswerPair.query.filter_by(dataset_id=dataset_id).all()
            for qa in qa_pairs:
                # Delete all feedback for this Q&A pair
                Feedback.query.filter_by(qa_pair_id=qa.id).delete()
                db.session.delete(qa)
            
            # Delete the dataset
            db.session.delete(dataset)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Dataset "{dataset.name}" deleted successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Delete failed: {str(e)}'})

    @app.route('/export_data')
    def export_data():
        """Export feedback data as JSON for ML pipeline"""
        qa_pairs = QuestionAnswerPair.query.all()
        data = []
        
        for qa in qa_pairs:
            qa_data = {
                'id': qa.id,
                'question': qa.question_text,
                'system_answer': qa.system_answer_text,
                'feedback': []
            }
            
            for feedback in qa.feedback:
                feedback_data = {
                    'text_feedback': feedback.text_feedback,
                    'accuracy_score': feedback.accuracy_score,
                    'completeness_score': feedback.completeness_score,
                    'clarity_score': feedback.clarity_score,
                    'clinical_relevance_score': feedback.clinical_relevance_score,
                    'gold_standard_answer': feedback.gold_standard_answer,
                    'submitted_at': feedback.submitted_at.isoformat() if feedback.submitted_at else None
                }
                qa_data['feedback'].append(feedback_data)
            
            data.append(qa_data)
        
        return jsonify(data)

    # API endpoints for AJAX functionality
    @app.route('/api/datasets')
    @login_required
    def api_get_datasets():
        """Get datasets user has access to"""
        datasets = current_user.accessible_datasets
        return jsonify([{
            'id': dataset.id,
            'name': dataset.name,
            'description': dataset.description
        } for dataset in datasets])

    @app.route('/api/dataset/<int:dataset_id>/users')
    @login_required
    def api_get_dataset_users(dataset_id):
        """Get users who have provided feedback for a specific dataset"""
        # Check if user has access to this dataset
        if not current_user.has_dataset_access(dataset_id):
            return jsonify({'error': 'Access denied'}), 403
        
        # Get all users who have provided feedback for this dataset
        feedback_user_ids = db.session.query(Feedback.user_id).distinct().\
            join(QuestionAnswerPair, Feedback.qa_pair_id == QuestionAnswerPair.id).\
            filter(QuestionAnswerPair.dataset_id == dataset_id).\
            filter(Feedback.user_id.isnot(None)).all()
        
        user_ids = [uid[0] for uid in feedback_user_ids]
        users = User.query.filter(User.id.in_(user_ids)).all() if user_ids else []
        
        return jsonify([{
            'id': user.id,
            'username': user.username
        } for user in users])

    @app.route('/api/dataset/<int:dataset_id>/qa')
    @login_required
    def api_get_dataset_qa(dataset_id):
        """Get Q&A pairs for a specific dataset"""
        # Check if user has access to this dataset
        if not current_user.has_dataset_access(dataset_id):
            return jsonify({'error': 'Access denied'}), 403
            
        qa_pairs = QuestionAnswerPair.query.filter_by(dataset_id=dataset_id).order_by(QuestionAnswerPair.created_at.desc()).all()
        
        data = []
        for qa in qa_pairs:
            # Get current user's feedback for this Q&A
            user_feedback = [f for f in qa.feedback if f.user_id == current_user.id]
            qa_data = {
                'id': qa.id,
                'question_text': qa.question_text,
                'system_answer_text': qa.system_answer_text,
                'feedback_count': len(user_feedback),
                'has_gold_standard': any(f.gold_standard_answer for f in user_feedback),
                'created_at': qa.created_at.isoformat()
            }
            data.append(qa_data)
        
        return jsonify(data)

    @app.route('/api/qa/<int:qa_id>')
    @login_required
    def api_get_qa(qa_id):
        """Get Q&A pair data as JSON with feedback"""
        qa_pair = QuestionAnswerPair.query.get_or_404(qa_id)
        
        # Include current user's feedback data only
        feedback_data = []
        user_feedback = [f for f in qa_pair.feedback if f.user_id == current_user.id]
        for feedback in user_feedback:
            feedback_data.append({
                'id': feedback.id,
                'user_id': feedback.user_id,
                'text_feedback': feedback.text_feedback,
                'accuracy_score': feedback.accuracy_score,
                'completeness_score': feedback.completeness_score,
                'clarity_score': feedback.clarity_score,
                'clinical_relevance_score': feedback.clinical_relevance_score,
                'gold_standard_answer': feedback.gold_standard_answer,
                'submitted_at': feedback.submitted_at.isoformat() if feedback.submitted_at else None
            })
        
        return jsonify({
            'id': qa_pair.id,
            'question_text': qa_pair.question_text,
            'system_answer_text': qa_pair.system_answer_text,
            'feedback': feedback_data,
            'created_at': qa_pair.created_at.isoformat()
        })

    @app.route('/api/feedback/<int:qa_id>')
    @login_required
    def api_get_feedback(qa_id):
        """Get current user's feedback for a Q&A pair as JSON"""
        feedback_list = Feedback.query.filter_by(qa_pair_id=qa_id, user_id=current_user.id).order_by(Feedback.submitted_at.desc()).all()
        
        feedback_data = []
        for feedback in feedback_list:
            feedback_data.append({
                'id': feedback.id,
                'user_id': feedback.user_id,
                'text_feedback': feedback.text_feedback,
                'accuracy_score': feedback.accuracy_score,
                'completeness_score': feedback.completeness_score,
                'clarity_score': feedback.clarity_score,
                'clinical_relevance_score': feedback.clinical_relevance_score,
                'gold_standard_answer': feedback.gold_standard_answer,
                'submitted_at': feedback.submitted_at.isoformat() if feedback.submitted_at else None
            })
        
        return jsonify(feedback_data)

    @app.route('/api/save_gold_standard', methods=['POST'])
    @login_required
    def api_save_gold_standard():
        """Save or update gold standard response for a Q&A pair"""
        try:
            data = request.get_json()
            
            # Validate required data
            if not data or 'qa_id' not in data or 'gold_standard_answer' not in data:
                return jsonify({'success': False, 'message': 'Missing required data'})
            
            qa_id = data.get('qa_id')
            gold_standard_text = data.get('gold_standard_answer')
            
            if not gold_standard_text.strip():
                return jsonify({'success': False, 'message': 'Gold standard answer cannot be empty'})
            
            # Check if Q&A pair exists
            qa_pair = QuestionAnswerPair.query.get(qa_id)
            if not qa_pair:
                return jsonify({'success': False, 'message': 'Q&A pair not found'})
            
            # Check if user already has feedback for this Q&A pair
            existing_feedback = Feedback.query.filter_by(qa_pair_id=qa_id, user_id=current_user.id).first()
            
            if existing_feedback:
                # Update existing feedback with gold standard
                existing_feedback.gold_standard_answer = gold_standard_text
            else:
                # Create new feedback record with just the gold standard
                feedback = Feedback(
                    qa_pair_id=qa_id,
                    user_id=current_user.id,
                    gold_standard_answer=gold_standard_text
                )
                db.session.add(feedback)
            
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': 'Gold standard response saved successfully'
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error saving gold standard: {str(e)}'})

    @app.route('/api/submit_feedback', methods=['POST'])
    @login_required
    def api_submit_feedback():
        """Submit feedback via AJAX"""
        try:
            data = request.get_json()
            
            # Validate required data
            if not data or 'qa_id' not in data:
                return jsonify({'success': False, 'message': 'Missing Q&A ID'})
            
            qa_id = data['qa_id']
            qa_pair = QuestionAnswerPair.query.get(qa_id)
            if not qa_pair:
                return jsonify({'success': False, 'message': 'Q&A pair not found'})
            
            # Find existing feedback record or create new one
            feedback = Feedback.query.filter_by(qa_pair_id=qa_id, user_id=current_user.id).first()
            
            if feedback:
                # Update existing feedback (preserve gold standard)
                feedback.text_feedback = data.get('text_feedback')
                feedback.accuracy_score = data.get('accuracy_score')
                feedback.completeness_score = data.get('completeness_score')
                feedback.clarity_score = data.get('clarity_score')
                feedback.clinical_relevance_score = data.get('clinical_relevance_score')
                # Don't update gold_standard_answer - it's handled separately
                feedback.submitted_at = datetime.utcnow()
            else:
                # Create new feedback record (without gold standard)
                feedback = Feedback(
                    qa_pair_id=qa_id,
                    user_id=current_user.id,
                    text_feedback=data.get('text_feedback'),
                    accuracy_score=data.get('accuracy_score'),
                    completeness_score=data.get('completeness_score'),
                    clarity_score=data.get('clarity_score'),
                    clinical_relevance_score=data.get('clinical_relevance_score')
                    # Don't set gold_standard_answer - it's handled separately
                )
                db.session.add(feedback)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': 'Feedback submitted successfully',
                'feedback_id': feedback.id
            })
            
        except Exception as e:
            db.session.rollback()
            return jsonify({'success': False, 'message': f'Error: {str(e)}'})