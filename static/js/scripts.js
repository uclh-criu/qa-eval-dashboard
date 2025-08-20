// Custom JavaScript for Medical Q&A Feedback System

// Global variables
let currentQAData = {};
let isEditMode = false;
let currentDatasetId = null;
let currentUserId = null;

document.addEventListener('DOMContentLoaded', function() {
    // Get current user ID
    const userIdInput = document.getElementById('current-user-id');
    if (userIdInput) {
        currentUserId = parseInt(userIdInput.value);
    }
    
    // Initialize the interface
    initializeInterface();
    
    // Setup Q&A item click handlers
    setupQAItemHandlers();
    
    // Setup dataset switching
    setupDatasetSwitching();
    
    // Load initial datasets
    loadDatasets();
    
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-dismiss alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
    
    // Setup feedback form submission
    setupFeedbackForm();
});

// Setup Q&A item click handlers
function setupQAItemHandlers() {
    const qaContainer = document.querySelector('.qa-list-container');
    if (qaContainer) {
        qaContainer.addEventListener('click', function(e) {
            const qaItem = e.target.closest('.qa-list-item');
            if (qaItem) {
                const qaId = qaItem.dataset.qaId;
                console.log('Clicking QA item:', qaId); // Debug log
                selectQA(qaId);
            }
        });
    } else {
        console.log('QA container not found'); // Debug log
    }
}

// Setup dataset switching
function setupDatasetSwitching() {
    const datasetSelect = document.getElementById('dataset-select');
    if (datasetSelect) {
        datasetSelect.addEventListener('change', function() {
            switchDataset(this.value);
        });
    }
}

// Load available datasets
function loadDatasets() {
    fetch('/api/datasets')
        .then(response => response.json())
        .then(datasets => {
            const select = document.getElementById('dataset-select');
            select.innerHTML = '<option value="">Select a dataset...</option>';
            
            if (datasets.length === 0) {
                select.innerHTML = '<option value="">No datasets available</option>';
                select.disabled = true;
                return;
            }
            
            datasets.forEach(dataset => {
                const option = document.createElement('option');
                option.value = dataset.id;
                option.textContent = dataset.name;
                select.appendChild(option);
            });
            
            // Auto-select first dataset if available
            if (datasets.length > 0) {
                select.value = datasets[0].id;
                switchDataset(datasets[0].id);
            }
        })
        .catch(error => {
            console.error('Error loading datasets:', error);
            showAlert('Error loading datasets', 'error');
        });
}

// Switch to a different dataset
function switchDataset(datasetId) {
    if (!datasetId) return;
    
    currentDatasetId = datasetId;
    
    // Load Q&A pairs for this dataset
    fetch(`/api/dataset/${datasetId}/qa`)
        .then(response => response.json())
        .then(qaList => {
            updateQAList(qaList);
            updateStatusCounts(qaList);
            
            // Auto-select first Q&A if available
            if (qaList.length > 0) {
                selectQA(qaList[0].id);
            }
        })
        .catch(error => {
            console.error('Error loading Q&A pairs:', error);
            showAlert('Error loading Q&A pairs for dataset', 'error');
        });
}

// Update the Q&A list in the left panel
function updateQAList(qaList) {
    const container = document.querySelector('.qa-list-container');
    
    if (qaList.length === 0) {
        container.innerHTML = `
            <div class="text-center p-4">
                <i class="fas fa-inbox fa-2x text-muted mb-2"></i>
                <p class="text-muted">No Q&A pairs in this dataset</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = '';
    
    qaList.forEach((qa, index) => {
        const qaItem = document.createElement('div');
        qaItem.className = `qa-list-item ${index === 0 ? 'active' : ''}`;
        qaItem.dataset.qaId = qa.id;
        
        let status, statusBadge;
        
        if (qa.feedback_count > 0 && qa.has_gold_standard) {
            status = 'completed';
            statusBadge = '<span class="badge bg-success">Completed</span>';
        } else if (qa.has_gold_standard) {
            status = 'gold';
            statusBadge = '<span class="badge bg-warning">Gold Standard</span>';
        } else if (qa.feedback_count > 0) {
            status = 'feedback';
            statusBadge = '<span class="badge bg-info">Feedback</span>';
        } else {
            status = 'pending';
            statusBadge = '<span class="badge bg-danger">Pending</span>';
        }
        
        qa.status = status; // Store for status counting
        
        qaItem.innerHTML = `
            <div class="qa-item-header">
                <span class="qa-number">Q${qa.id}</span>
                <span class="feedback-count">
                    <i class="fas fa-comments"></i> ${qa.feedback_count}
                </span>
            </div>
            <div class="qa-item-preview">
                ${qa.question_text.substring(0, 100)}${qa.question_text.length > 100 ? '...' : ''}
            </div>
            <div class="qa-item-status">
                ${statusBadge}
            </div>
        `;
        
        container.appendChild(qaItem);
    });
}

// Update status counts
function updateStatusCounts(qaList) {
    let pending = 0, goldStandard = 0, feedback = 0, completed = 0;
    
    qaList.forEach(qa => {
        if (qa.feedback_count > 0 && qa.has_gold_standard) {
            completed++;
        } else if (qa.has_gold_standard) {
            goldStandard++;
        } else if (qa.feedback_count > 0) {
            feedback++;
        } else {
            pending++;
        }
    });
    
    document.getElementById('pending-count').textContent = pending;
    document.getElementById('gold-count').textContent = goldStandard;
    document.getElementById('feedback-count').textContent = feedback;
    document.getElementById('completed-count').textContent = completed;
}

// Initialize the three-panel interface
function initializeInterface() {
    // Calculate initial status counts from existing Q&A items
    updateInitialStatusCounts();
    
    // Load first Q&A pair if available
    const firstQAItem = document.querySelector('.qa-list-item');
    if (firstQAItem) {
        const qaId = firstQAItem.dataset.qaId;
        selectQA(qaId);
    }
}

// Calculate initial status counts from server-rendered Q&A items
function updateInitialStatusCounts() {
    const qaItems = document.querySelectorAll('.qa-list-item');
    let pending = 0, goldStandard = 0, feedback = 0, completed = 0;
    
    qaItems.forEach(item => {
        const badge = item.querySelector('.qa-item-status .badge');
        if (badge) {
            const status = badge.textContent.trim();
            if (status === 'Pending') {
                pending++;
            } else if (status === 'Gold Standard') {
                goldStandard++;
            } else if (status === 'Feedback') {
                feedback++;
            } else if (status === 'Completed') {
                completed++;
            }
        }
    });
    
    document.getElementById('pending-count').textContent = pending;
    document.getElementById('gold-count').textContent = goldStandard;
    document.getElementById('feedback-count').textContent = feedback;
    document.getElementById('completed-count').textContent = completed;
}

// Function to select a Q&A pair
function selectQA(qaId) {
    // Update active state in left panel
    document.querySelectorAll('.qa-list-item').forEach(item => {
        item.classList.remove('active');
    });
    
    const selectedItem = document.querySelector(`[data-qa-id="${qaId}"]`);
    if (selectedItem) {
        selectedItem.classList.add('active');
    }
    
    // Load Q&A data via AJAX
    loadQAData(qaId);
    
    // Update current QA ID
    document.getElementById('current-qa-id').value = qaId;
    
    // Reset edit mode
    cancelEdit();
    
    // Load previous feedback (this will populate the form with latest values)
    loadPreviousFeedback(qaId);
}

// Load Q&A data via AJAX
function loadQAData(qaId) {
    fetch(`/api/qa/${qaId}`)
        .then(response => response.json())
        .then(data => {
            currentQAData = data;
            updateMainContent(data);
        })
        .catch(error => {
            console.error('Error loading Q&A data:', error);
            showAlert('Error loading Q&A data', 'error');
        });
}

// Update the main content panel
function updateMainContent(qaData) {
    document.getElementById('question-display').textContent = qaData.question_text;
    document.getElementById('answer-display').textContent = qaData.system_answer_text;
    document.getElementById('answer-edit').value = qaData.system_answer_text;
    
    // Update gold standard display for this specific Q&A pair
    updateGoldStandardDisplay(qaData);
}

// Update gold standard display based on Q&A data
function updateGoldStandardDisplay(qaData) {
    const goldStandardTextElem = document.getElementById('gold-standard-text');
    if (!goldStandardTextElem) return;
    
    // Find the latest feedback with a gold standard answer
    let latestGoldStandard = null;
    if (qaData.feedback && qaData.feedback.length > 0) {
        // Sort feedback by submission date (newest first) and find first with gold standard
        const sortedFeedback = qaData.feedback.sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at));
        latestGoldStandard = sortedFeedback.find(f => f.gold_standard_answer);
    }
    
    if (latestGoldStandard && latestGoldStandard.gold_standard_answer) {
        goldStandardTextElem.textContent = latestGoldStandard.gold_standard_answer;
    } else {
        goldStandardTextElem.innerHTML = '<em class="text-muted">No gold standard response provided yet. Click the edit button to create one.</em>';
    }
}

// Gold standard editing functions

function editGoldStandard() {
    const goldEditor = document.getElementById('gold-standard-editor');
    const goldText = document.getElementById('gold-standard-text');
    const textarea = document.getElementById('answer-edit');
    const goldBtn = document.getElementById('edit-gold-btn');
    
    // Copy current gold standard to editor (or system answer if no gold standard exists)
    const currentGoldText = goldText.textContent.trim();
    if (currentGoldText && !currentGoldText.includes('No gold standard')) {
        textarea.value = currentGoldText;
    } else {
        // Default to copying the system answer as a starting point
        const systemText = document.getElementById('answer-display').textContent;
        textarea.value = systemText;
    }
    
    // Show editor and hide text display
    goldEditor.classList.remove('d-none');
    goldText.classList.add('d-none');
    
    // Focus the textarea
    textarea.focus();
    isEditMode = true;
}

function cancelEdit() {
    const goldEditor = document.getElementById('gold-standard-editor');
    const goldText = document.getElementById('gold-standard-text');
    
    if (goldEditor) goldEditor.classList.add('d-none');
    if (goldText) goldText.classList.remove('d-none');
    
    isEditMode = false;
}

function saveGoldStandard() {
    const goldEditor = document.getElementById('gold-standard-editor');
    const goldText = document.getElementById('gold-standard-text');
    const textarea = document.getElementById('answer-edit');
    const goldBtn = document.getElementById('edit-gold-btn');
    const qaId = document.getElementById('current-qa-id').value;
    
    const goldStandardAnswer = textarea.value.trim();
    
    if (!goldStandardAnswer) {
        showAlert('Gold standard answer cannot be empty', 'error');
        return;
    }
    
    // Save to database immediately
    const formData = {
        qa_id: qaId,
        gold_standard_answer: goldStandardAnswer
    };
    
    // Store the current status to determine the transition
    const qaItem = document.querySelector(`[data-qa-id="${qaId}"]`);
    const currentStatus = qaItem ? qaItem.querySelector('.qa-item-status .badge').textContent.trim() : null;
    
    // Show loading state on button
    if (goldBtn) goldBtn.disabled = true;
    
    fetch('/api/save_gold_standard', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update gold standard display
            goldText.innerHTML = goldStandardAnswer;
            
            // Show display and hide editor
            goldEditor.classList.add('d-none');
            goldText.classList.remove('d-none');
            
            // Reset edit mode since it's now saved
            isEditMode = false;
            
            // Update the Q&A item status in the left panel
            updateQAItemStatus(qaId, 'gold', currentStatus);
            
            // Reload the Q&A data to refresh the feedback array
            loadQAData(qaId);
            
            showAlert('Gold standard response saved successfully!', 'success');
        } else {
            showAlert(data.message || 'Error saving gold standard response', 'error');
        }
    })
    .catch(error => {
        console.error('Error saving gold standard:', error);
        showAlert('Error saving gold standard response', 'error');
    })
    .finally(() => {
        // Re-enable button
        if (goldBtn) goldBtn.disabled = false;
    });
}

// Update score value display
function updateScoreValue(slider, valueId) {
    const value = document.getElementById(valueId);
    value.textContent = slider.value;
    value.className = 'score-value score-' + slider.value;
}

// Setup feedback form
function setupFeedbackForm() {
    const form = document.getElementById('feedback-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            e.preventDefault();
            submitFeedback();
        });
    }
}

// Submit feedback via AJAX
function submitFeedback() {
    const qaId = document.getElementById('current-qa-id').value;
    const submitBtn = document.querySelector('#feedback-form button[type="submit"]');
    
    // Get form data (excluding gold standard - that's saved separately)
    const formData = {
        qa_id: qaId,
        text_feedback: document.getElementById('text_feedback').value,
        accuracy_score: document.getElementById('accuracy_score').value || null,
        completeness_score: document.getElementById('completeness_score').value || null,
        clarity_score: document.getElementById('clarity_score').value || null,
        clinical_relevance_score: document.getElementById('clinical_relevance_score').value || null
    };
    
    // Show loading state
    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Submitting...';
    submitBtn.disabled = true;
    
    // Submit via AJAX
    fetch('/api/submit_feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Store the current status to determine the transition
            const qaItem = document.querySelector(`[data-qa-id="${qaId}"]`);
            const currentStatus = qaItem ? qaItem.querySelector('.qa-item-status .badge').textContent.trim() : null;
            
            showAlert('Feedback submitted successfully!', 'success');
            clearFeedbackForm();
            loadPreviousFeedback(qaId);
            updateQAItemStatus(qaId, 'feedback', currentStatus);
            // Reload the Q&A data to refresh gold standard display
            loadQAData(qaId);
            cancelEdit();
        } else {
            showAlert(data.message || 'Error submitting feedback', 'error');
        }
    })
    .catch(error => {
        console.error('Error submitting feedback:', error);
        showAlert('Error submitting feedback', 'error');
    })
    .finally(() => {
        // Reset button state
        submitBtn.innerHTML = '<i class="fas fa-save me-2"></i>Submit Feedback';
        submitBtn.disabled = false;
    });
}

// Clear feedback form
function clearFeedbackForm() {
    document.getElementById('text_feedback').value = '';
    
    // Reset sliders to default value (3) and update displays
    const scoreFields = [
        'accuracy_score',
        'completeness_score', 
        'clarity_score',
        'clinical_relevance_score'
    ];
    
    scoreFields.forEach(field => {
        const slider = document.getElementById(field);
        if (slider) {
            slider.value = 3; // Default middle value
            // Update the value display
            updateScoreValue(slider, field.replace('_score', '_value'));
        }
    });
}

// Load previous feedback
function loadPreviousFeedback(qaId) {
    fetch(`/api/feedback/${qaId}`)
        .then(response => response.json())
        .then(data => {
            updatePreviousFeedbackDisplay(data);
        })
        .catch(error => {
            console.error('Error loading previous feedback:', error);
        });
}

// Update previous feedback display
function updatePreviousFeedbackDisplay(feedbackList) {
    const container = document.getElementById('previous-feedback');
    
    // First, populate the form with the latest feedback values
    populateFeedbackForm(feedbackList);
    
    if (feedbackList.length === 0) {
        container.innerHTML = '<p class="text-muted text-center"><i class="fas fa-info-circle me-1"></i>No previous feedback</p>';
        return;
    }
    
    container.innerHTML = '<h6 class="text-muted mb-2">Your Previous Feedback:</h6>';
    
    feedbackList.forEach(feedback => {
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'previous-feedback-item';
        
        let html = `<small class="text-muted">${new Date(feedback.submitted_at).toLocaleString()}</small>`;
        
        if (feedback.text_feedback) {
            html += `<p class="mb-1">${feedback.text_feedback}</p>`;
        }
        
        if (feedback.accuracy_score || feedback.completeness_score || feedback.clarity_score || feedback.clinical_relevance_score) {
            html += '<div class="feedback-scores">';
            if (feedback.accuracy_score) html += `<span class="badge bg-primary">Acc: ${feedback.accuracy_score}</span>`;
            if (feedback.completeness_score) html += `<span class="badge bg-secondary">Comp: ${feedback.completeness_score}</span>`;
            if (feedback.clarity_score) html += `<span class="badge bg-success">Clarity: ${feedback.clarity_score}</span>`;
            if (feedback.clinical_relevance_score) html += `<span class="badge bg-info">Relevance: ${feedback.clinical_relevance_score}</span>`;
            html += '</div>';
        }
        
        feedbackDiv.innerHTML = html;
        container.appendChild(feedbackDiv);
    });
    
    // Also update the main gold standard display based on latest feedback
    updateGoldStandardFromFeedback(feedbackList);
}

// Populate feedback form with latest values
function populateFeedbackForm(feedbackList) {
    // Clear form first
    clearFeedbackForm();
    
    if (feedbackList.length === 0) return;
    
    // Get the latest feedback (API now only returns current user's feedback)
    const latestFeedback = feedbackList[0];
    
    // Populate text feedback
    if (latestFeedback.text_feedback) {
        document.getElementById('text_feedback').value = latestFeedback.text_feedback;
    }
    
    // Populate score sliders and update their displays
    const scoreFields = [
        'accuracy_score',
        'completeness_score', 
        'clarity_score',
        'clinical_relevance_score'
    ];
    
    scoreFields.forEach(field => {
        if (latestFeedback[field]) {
            const slider = document.getElementById(field);
            const valueDisplay = document.getElementById(field.replace('_score', '_value'));
            
            if (slider) {
                slider.value = latestFeedback[field];
                // Update the value display and color
                if (valueDisplay) {
                    updateScoreValue(slider, field.replace('_score', '_value'));
                }
            }
        }
    });
}

// Update gold standard display from feedback list
function updateGoldStandardFromFeedback(feedbackList) {
    const goldStandardTextElem = document.getElementById('gold-standard-text');
    if (!goldStandardTextElem) return;
    
    // Find the latest feedback with a gold standard answer
    let latestGoldStandard = null;
    if (feedbackList && feedbackList.length > 0) {
        // Sort feedback by submission date (newest first) and find first with gold standard
        const sortedFeedback = feedbackList.sort((a, b) => new Date(b.submitted_at) - new Date(a.submitted_at));
        latestGoldStandard = sortedFeedback.find(f => f.gold_standard_answer);
    }
    
    if (latestGoldStandard && latestGoldStandard.gold_standard_answer) {
        goldStandardTextElem.textContent = latestGoldStandard.gold_standard_answer;
    } else {
        goldStandardTextElem.innerHTML = '<em class="text-muted">No gold standard response provided yet. Click the edit button to create one.</em>';
    }
}

// Update Q&A item status in left panel
function updateQAItemStatus(qaId, action = 'feedback', currentStatus = null) {
    const qaItem = document.querySelector(`[data-qa-id="${qaId}"]`);
    if (!qaItem) return;
    
    const statusBadge = qaItem.querySelector('.qa-item-status .badge');
    const feedbackCount = qaItem.querySelector('.feedback-count');
    
    // Get current status from badge text if not provided
    if (!currentStatus) {
        currentStatus = statusBadge.textContent.trim();
    }
    
    console.log(`Updating status for QA ${qaId}, action: ${action}, current status: ${currentStatus}`);
    
    // Update the status badge and counts based on the current status and action
    if (action === 'feedback') {
        // User submitted feedback
        if (currentStatus === 'Pending') {
            // Change from Pending to Feedback
            statusBadge.className = 'badge bg-info';
            statusBadge.textContent = 'Feedback';
            
            // Update feedback count
            updateFeedbackCount(feedbackCount);
            
            // Update status counts
            incrementStatusCount('feedback');
            decrementStatusCount('pending');
        } else if (currentStatus === 'Gold Standard') {
            // Change from Gold Standard to Completed
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = 'Completed';
            
            // Update feedback count
            updateFeedbackCount(feedbackCount);
            
            // Update status counts
            incrementStatusCount('completed');
            decrementStatusCount('gold');
        }
        // No action needed for Feedback -> Feedback or Completed -> Completed transitions
    } else if (action === 'gold') {
        // User submitted gold standard
        if (currentStatus === 'Pending') {
            // Change from Pending to Gold Standard
            statusBadge.className = 'badge bg-warning';
            statusBadge.textContent = 'Gold Standard';
            
            // Update status counts
            incrementStatusCount('gold');
            decrementStatusCount('pending');
        } else if (currentStatus === 'Feedback') {
            // Change from Feedback to Completed
            statusBadge.className = 'badge bg-success';
            statusBadge.textContent = 'Completed';
            
            // Update status counts
            incrementStatusCount('completed');
            decrementStatusCount('feedback');
        }
        // No action needed for Gold Standard -> Gold Standard or Completed -> Completed transitions
    }
}

// Helper function to update the feedback count
function updateFeedbackCount(feedbackCountElement) {
    if (!feedbackCountElement) return;
    
    // Parse current count
    const countMatch = feedbackCountElement.textContent.match(/\d+/);
    if (!countMatch) return;
    
    const currentCount = parseInt(countMatch[0]);
    feedbackCountElement.innerHTML = `<i class="fas fa-comments"></i> ${currentCount + 1}`;
}

// Helper functions to update status counts
function incrementStatusCount(status) {
    const countElement = document.getElementById(`${status}-count`);
    if (countElement) {
        countElement.textContent = (parseInt(countElement.textContent) || 0) + 1;
    }
}

function decrementStatusCount(status) {
    const countElement = document.getElementById(`${status}-count`);
    if (countElement && parseInt(countElement.textContent) > 0) {
        countElement.textContent = parseInt(countElement.textContent) - 1;
    }
}

// Form submission loading state
var forms = document.querySelectorAll('form:not(#feedback-form)');
forms.forEach(function(form) {
    form.addEventListener('submit', function(e) {
        var submitBtn = form.querySelector('input[type="submit"], button[type="submit"]');
        if (submitBtn) {
            submitBtn.classList.add('loading');
            submitBtn.disabled = true;
        }
    });
});

    // Auto-resize textareas
    var textareas = document.querySelectorAll('textarea');
    textareas.forEach(function(textarea) {
        // Initial resize
        autoResize(textarea);
        
        // Resize on input
        textarea.addEventListener('input', function() {
            autoResize(this);
        });
    });

    function autoResize(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = textarea.scrollHeight + 'px';
    }

    // Score input validation and styling
    var scoreInputs = document.querySelectorAll('input[type="number"][max="5"]');
    scoreInputs.forEach(function(input) {
        input.addEventListener('input', function() {
            var value = parseInt(this.value);
            var parent = this.closest('.col-md-6');
            
            // Remove existing classes
            parent.classList.remove('score-excellent', 'score-good', 'score-fair', 'score-poor');
            
            // Add appropriate class based on score
            if (value >= 4) {
                parent.classList.add('score-excellent');
            } else if (value === 3) {
                parent.classList.add('score-good');
            } else if (value === 2) {
                parent.classList.add('score-fair');
            } else if (value === 1) {
                parent.classList.add('score-poor');
            }
        });
    });

    // Character counter for textareas
    var textFeedback = document.querySelector('#text_feedback');
    if (textFeedback) {
        addCharacterCounter(textFeedback, 1000);
    }
    
    var goldStandard = document.querySelector('#gold_standard_answer');
    if (goldStandard) {
        addCharacterCounter(goldStandard, 2000);
    }

    function addCharacterCounter(textarea, maxLength) {
        var counter = document.createElement('small');
        counter.className = 'form-text text-muted character-counter';
        textarea.parentNode.appendChild(counter);
        
        function updateCounter() {
            var remaining = maxLength - textarea.value.length;
            counter.textContent = remaining + ' characters remaining';
            
            if (remaining < 0) {
                counter.className = 'form-text text-danger character-counter';
            } else if (remaining < 100) {
                counter.className = 'form-text text-warning character-counter';
            } else {
                counter.className = 'form-text text-muted character-counter';
            }
        }
        
        textarea.addEventListener('input', updateCounter);
        updateCounter(); // Initial update
    }

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // Confirmation for export data
    var exportBtn = document.querySelector('a[href*="export_data"]');
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            // Show a brief loading message
            var originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Exporting...';
            
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        });
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter to submit form
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            var form = document.querySelector('form');
            if (form) {
                form.submit();
            }
        }
        
        // ESC to go back to home
        if (e.key === 'Escape') {
            window.location.href = '/';
        }
    });

    // Add visual feedback for score inputs
    function addScoreStyles() {
        var style = document.createElement('style');
        style.textContent = `
            .score-excellent { background-color: rgba(40, 167, 69, 0.1); border-radius: 4px; }
            .score-good { background-color: rgba(0, 123, 255, 0.1); border-radius: 4px; }
            .score-fair { background-color: rgba(255, 193, 7, 0.1); border-radius: 4px; }
            .score-poor { background-color: rgba(220, 53, 69, 0.1); border-radius: 4px; }
            .character-counter { font-size: 0.8em; }
        `;
        document.head.appendChild(style);
    }
    
    addScoreStyles();

// Global alert display function
function showAlert(message, type = 'info') {
    var toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
    toast.innerHTML = `
        <i class="fas fa-${type === 'success' ? 'check-circle' : 'exclamation-circle'} me-2"></i>
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 3000);
}

// Utility function to copy text to clipboard
function copyToClipboard(text) {
    navigator.clipboard.writeText(text).then(function() {
        // Show toast notification
        showToast('Text copied to clipboard!', 'success');
    }, function(err) {
        console.error('Could not copy text: ', err);
        showToast('Failed to copy text', 'error');
    });
}

// Simple toast notification function
function showToast(message, type = 'info') {
    var toast = document.createElement('div');
    toast.className = `alert alert-${type === 'error' ? 'danger' : type} position-fixed`;
    toast.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 250px;';
    toast.innerHTML = `
        ${message}
        <button type="button" class="btn-close" onclick="this.parentElement.remove()"></button>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 3 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 3000);
}
