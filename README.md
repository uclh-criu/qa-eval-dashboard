# Medical Q&A Feedback System

A web application designed for clinicians and medical professionals to provide feedback on AI-generated medical question-answer pairs. This system facilitates the collection of expert feedback to improve medical AI systems through structured evaluation and gold-standard answer creation.

## Features

- **Clean, Professional Interface**: Bootstrap-based UI designed for healthcare professionals
- **Structured Feedback Collection**: 
  - Text-based feedback
  - Numerical scoring (1-5 scale) for accuracy, completeness, clarity, and clinical relevance
  - Gold standard answer editing capabilities
- **Data Management**: 
  - SQLite database for development (easily upgradeable to PostgreSQL)
  - Data export functionality for ML pipelines
  - Admin dashboard with analytics
- **User-Friendly Design**: 
  - Responsive design for various devices
  - Intuitive navigation and feedback forms
  - Real-time validation and feedback

## Project Structure

```
medical-qa-feedback/
├── app.py                  # Main Flask application
├── models.py              # Database models (Q&A pairs, feedback, users)
├── routes.py              # Application routes and view functions
├── forms.py               # WTForms for feedback submission
├── populate_sample_data.py # Script to add sample medical Q&A data
├── requirements.txt       # Python dependencies
├── static/
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/
│       └── scripts.js    # Custom JavaScript
└── templates/
    ├── base.html         # Base template with navigation
    ├── index.html        # Main page listing Q&A pairs
    ├── feedback.html     # Feedback submission page
    └── admin.html        # Admin dashboard
```

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip (Python package installer)

### Quick Start

1. **Clone or download the project files**
   ```bash
   cd medical-qa-feedback
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database with sample data**
   ```bash
   python populate_sample_data.py
   ```

5. **Run the application**
   ```bash
   python app.py
   ```

6. **Open your browser** and navigate to `http://localhost:5000`

## Usage Guide

### For Clinicians (End Users)

1. **View Q&A Pairs**: The home page displays all available medical Q&A pairs
2. **Provide Feedback**: Click "Review & Provide Feedback" on any question to:
   - Read the medical question and AI-generated answer
   - Provide general text feedback
   - Score the answer on multiple criteria (1-5 scale)
   - Edit the answer to create a "gold standard" response
3. **Submit Feedback**: Your feedback is immediately saved and can be viewed by administrators

### For Administrators

1. **Admin Dashboard**: Access via the navigation menu to view:
   - Overall system statistics
   - Detailed feedback analytics per Q&A pair
   - Average scores across different criteria
2. **Data Export**: Export all feedback data as JSON for ML model training
3. **Data Management**: Monitor feedback collection progress

## Database Schema

### QuestionAnswerPair
- `id`: Primary key
- `question_text`: The medical question
- `system_answer_text`: AI-generated answer
- `created_at`: Timestamp

### Feedback
- `id`: Primary key
- `qa_pair_id`: Foreign key to QuestionAnswerPair
- `user_id`: Foreign key to User (optional)
- `text_feedback`: General feedback text
- `accuracy_score`: 1-5 rating for accuracy
- `completeness_score`: 1-5 rating for completeness
- `clarity_score`: 1-5 rating for clarity
- `clinical_relevance_score`: 1-5 rating for clinical relevance
- `gold_standard_answer`: Edited "ideal" answer
- `submitted_at`: Timestamp

### User
- `id`: Primary key
- `username`: Unique username
- `email`: Email address
- `role`: User role (clinician, admin)
- `created_at`: Timestamp

## Data Pipeline

### Adding New Q&A Pairs
You can add new medical Q&A pairs by:
1. Creating a custom script similar to `populate_sample_data.py`
2. Directly inserting into the database
3. Extending the application with file upload functionality

### Exporting Feedback Data
- Visit `/export_data` endpoint or use the "Export Data" button in the admin panel
- Data is exported as JSON with the following structure:
```json
[
  {
    "id": 1,
    "question": "Medical question text...",
    "system_answer": "AI generated answer...",
    "feedback": [
      {
        "text_feedback": "Expert feedback...",
        "accuracy_score": 4,
        "completeness_score": 3,
        "clarity_score": 5,
        "clinical_relevance_score": 4,
        "gold_standard_answer": "Improved answer...",
        "submitted_at": "2024-01-15T10:30:00"
      }
    ]
  }
]
```

## Customization

### Adding New Scoring Criteria
1. Add new columns to the `Feedback` model in `models.py`
2. Update the `FeedbackForm` in `forms.py`
3. Modify the feedback template in `templates/feedback.html`
4. Update the admin dashboard to display new metrics

### Changing the UI Theme
- Modify `static/css/style.css` for custom styling
- Update Bootstrap classes in templates for different color schemes
- Add custom JavaScript in `static/js/scripts.js` for enhanced interactions

### Database Configuration
For production use:
1. Change the database URI in `app.py` to PostgreSQL:
   ```python
   app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:password@localhost/medical_qa_db'
   ```
2. Install PostgreSQL adapter: `pip install psycopg2-binary`
3. Create the PostgreSQL database and run the application

## Security Considerations

- Change the `SECRET_KEY` in `app.py` for production
- Implement proper user authentication if deploying publicly
- Consider HTTPS for production deployment
- Validate and sanitize all user inputs
- Implement rate limiting for form submissions

## Deployment

For production deployment, consider:
- Using a WSGI server like Gunicorn
- Setting up a reverse proxy with Nginx
- Using environment variables for configuration
- Implementing proper logging
- Setting up database backups

## Contributing

This is a basic implementation designed to be extended. Potential improvements include:
- User authentication and authorization
- File upload functionality for bulk Q&A import
- Advanced analytics and reporting
- API endpoints for programmatic access
- Real-time collaboration features
- Integration with external medical databases

## License

This project is provided as-is for educational and development purposes. Please ensure compliance with medical data regulations (HIPAA, GDPR, etc.) when handling real patient data.

## Support

For issues or questions about this application, please refer to the code comments and this documentation. The application is designed to be self-contained and easy to modify for specific requirements.
