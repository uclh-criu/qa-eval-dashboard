// Admin panel functionalities

// User editing functionality
function editUser(userId, username, accessLevel) {
    // Create modal if it doesn't exist
    if (!document.getElementById('editUserModal')) {
        const modalHtml = `
        <div class="modal fade" id="editUserModal" tabindex="-1" aria-labelledby="editUserModalLabel" aria-hidden="true">
            <div class="modal-dialog">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="editUserModalLabel">Edit User</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <form id="editUserForm">
                            <input type="hidden" id="editUserId">
                            <div class="mb-3">
                                <label for="editUsername" class="form-label">Username</label>
                                <input type="text" class="form-control" id="editUsername" required>
                            </div>
                            <div class="mb-3">
                                <label for="editAccessLevel" class="form-label">Access Level</label>
                                <select class="form-select" id="editAccessLevel" required>
                                    <option value="user">User</option>
                                    <option value="admin">Admin</option>
                                </select>
                            </div>
                        </form>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                        <button type="button" class="btn btn-primary" onclick="saveUserChanges()">Save Changes</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Populate modal
    document.getElementById('editUserId').value = userId;
    document.getElementById('editUsername').value = username;
    document.getElementById('editAccessLevel').value = accessLevel;

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('editUserModal'));
    modal.show();
}

function saveUserChanges() {
    const userId = document.getElementById('editUserId').value;
    const username = document.getElementById('editUsername').value;
    const accessLevel = document.getElementById('editAccessLevel').value;

    if (!username.trim()) {
        showAlert('Username cannot be empty', 'error');
        return;
    }

    const userData = {
        username: username,
        access_level: accessLevel
    };

    // Show loading state
    const saveBtn = document.querySelector('#editUserModal .btn-primary');
    const originalBtnText = saveBtn.innerHTML;
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Saving...';
    saveBtn.disabled = true;

    fetch(`/api/admin/user/${userId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('User updated successfully', 'success');
            // Close modal
            bootstrap.Modal.getInstance(document.getElementById('editUserModal')).hide();
            // Reload the page to show updated data
            setTimeout(() => window.location.reload(), 1000);
        } else {
            showAlert(data.message || 'Error updating user', 'error');
        }
    })
    .catch(error => {
        console.error('Error updating user:', error);
        showAlert('Error updating user', 'error');
    })
    .finally(() => {
        // Reset button
        saveBtn.innerHTML = originalBtnText;
        saveBtn.disabled = false;
    });
}

// Dataset user management functionality
function manageDatasetUsers(datasetId, datasetName) {
    // Create modal if it doesn't exist
    if (!document.getElementById('manageDatasetUsersModal')) {
        const modalHtml = `
        <div class="modal fade" id="manageDatasetUsersModal" tabindex="-1" aria-labelledby="manageDatasetUsersModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="manageDatasetUsersModalLabel">Manage Dataset Users</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <label for="datasetUserSearch" class="form-label">Add User to Dataset</label>
                            <div class="input-group">
                                <input type="text" class="form-control" id="datasetUserSearch" placeholder="Search users...">
                                <button class="btn btn-outline-secondary" type="button" onclick="searchUsersForDataset()">
                                    <i class="fas fa-search"></i>
                                </button>
                            </div>
                        </div>
                        <div id="userSearchResults" class="mb-3"></div>
                        <hr>
                        <h6>Current Users with Access</h6>
                        <div id="currentDatasetUsers" class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Username</th>
                                        <th>Access Level</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="datasetUsersList">
                                    <tr>
                                        <td colspan="3" class="text-center">Loading users...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Set dataset context
    currentDatasetId = datasetId;
    document.getElementById('manageDatasetUsersModalLabel').textContent = `Manage Users for Dataset: ${datasetName}`;

    // Load current dataset users
    loadDatasetUsers(datasetId);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('manageDatasetUsersModal'));
    modal.show();
}

function loadDatasetUsers(datasetId) {
    const usersList = document.getElementById('datasetUsersList');
    usersList.innerHTML = '<tr><td colspan="3" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading users...</td></tr>';

    fetch(`/api/admin/dataset/${datasetId}/users`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.users.length === 0) {
                    usersList.innerHTML = '<tr><td colspan="3" class="text-center">No users have access to this dataset</td></tr>';
                    return;
                }

                usersList.innerHTML = '';
                data.users.forEach(user => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${user.username}</td>
                        <td>
                            <span class="badge ${user.access_level === 'admin' ? 'bg-danger' : 'bg-secondary'}">
                                ${user.access_level === 'admin' ? 'Admin' : 'User'}
                            </span>
                        </td>
                        <td>
                            <button class="btn btn-sm btn-outline-danger" onclick="removeUserFromDataset(${datasetId}, ${user.id})">
                                <i class="fas fa-trash-alt"></i> Remove
                            </button>
                        </td>
                    `;
                    usersList.appendChild(row);
                });
            } else {
                usersList.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading users</td></tr>';
                showAlert(data.message || 'Error loading dataset users', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading dataset users:', error);
            usersList.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading users</td></tr>';
            showAlert('Error loading dataset users', 'error');
        });
}

function searchUsersForDataset() {
    const searchTerm = document.getElementById('datasetUserSearch').value.trim();
    if (!searchTerm) {
        showAlert('Please enter a search term', 'warning');
        return;
    }

    const resultsContainer = document.getElementById('userSearchResults');
    resultsContainer.innerHTML = '<div class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Searching users...</div>';

    fetch(`/api/admin/users/search?q=${encodeURIComponent(searchTerm)}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.users.length === 0) {
                    resultsContainer.innerHTML = '<div class="alert alert-info">No users found</div>';
                    return;
                }

                resultsContainer.innerHTML = '<div class="list-group">';
                data.users.forEach(user => {
                    resultsContainer.innerHTML += `
                        <div class="list-group-item d-flex justify-content-between align-items-center">
                            <div>
                                <strong>${user.username}</strong>
                                <span class="badge ${user.access_level === 'admin' ? 'bg-danger' : 'bg-secondary'} ms-2">
                                    ${user.access_level === 'admin' ? 'Admin' : 'User'}
                                </span>
                                ${user.has_access ? '<span class="badge bg-success ms-2">Already has access</span>' : ''}
                            </div>
                            <button class="btn btn-sm btn-primary" ${user.has_access ? 'disabled' : ''} onclick="addUserToDataset(${currentDatasetId}, ${user.id})">
                                <i class="fas fa-plus"></i> Add
                            </button>
                        </div>
                    `;
                });
                resultsContainer.innerHTML += '</div>';
            } else {
                resultsContainer.innerHTML = '<div class="alert alert-danger">Error searching users</div>';
                showAlert(data.message || 'Error searching users', 'error');
            }
        })
        .catch(error => {
            console.error('Error searching users:', error);
            resultsContainer.innerHTML = '<div class="alert alert-danger">Error searching users</div>';
            showAlert('Error searching users', 'error');
        });
}

function addUserToDataset(datasetId, userId) {
    // Show loading state
    const btn = document.querySelector(`#userSearchResults button[onclick*="${userId}"]`);
    const originalBtnText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;

    fetch(`/api/admin/dataset/${datasetId}/users`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            user_ids: [userId]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('User added to dataset successfully', 'success');
            // Reload dataset users
            loadDatasetUsers(datasetId);
            // Clear search results
            document.getElementById('userSearchResults').innerHTML = '';
            document.getElementById('datasetUserSearch').value = '';
        } else {
            showAlert(data.message || 'Error adding user to dataset', 'error');
            btn.innerHTML = originalBtnText;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error adding user to dataset:', error);
        showAlert('Error adding user to dataset', 'error');
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
    });
}

function removeUserFromDataset(datasetId, userId) {
    if (!confirm('Are you sure you want to remove this user from the dataset?')) {
        return;
    }

    fetch(`/api/admin/dataset/${datasetId}/users/${userId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('User removed from dataset successfully', 'success');
            // Reload dataset users
            loadDatasetUsers(datasetId);
        } else {
            showAlert(data.message || 'Error removing user from dataset', 'error');
        }
    })
    .catch(error => {
        console.error('Error removing user from dataset:', error);
        showAlert('Error removing user from dataset', 'error');
    });
}

// User dataset management functionality
function manageUserDatasets(userId, username) {
    // Create modal if it doesn't exist
    if (!document.getElementById('manageUserDatasetsModal')) {
        const modalHtml = `
        <div class="modal fade" id="manageUserDatasetsModal" tabindex="-1" aria-labelledby="manageUserDatasetsModalLabel" aria-hidden="true">
            <div class="modal-dialog modal-lg">
                <div class="modal-content">
                    <div class="modal-header">
                        <h5 class="modal-title" id="manageUserDatasetsModalLabel">Manage User Datasets</h5>
                        <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                    </div>
                    <div class="modal-body">
                        <div class="mb-3">
                            <h6>Available Datasets</h6>
                            <div id="availableDatasets" class="table-responsive">
                                <table class="table table-hover">
                                    <thead>
                                        <tr>
                                            <th>Dataset</th>
                                            <th>Description</th>
                                            <th>Actions</th>
                                        </tr>
                                    </thead>
                                    <tbody id="availableDatasetsList">
                                        <tr>
                                            <td colspan="3" class="text-center">Loading datasets...</td>
                                        </tr>
                                    </tbody>
                                </table>
                            </div>
                        </div>
                        <hr>
                        <h6>Current User Datasets</h6>
                        <div id="currentUserDatasets" class="table-responsive">
                            <table class="table table-hover">
                                <thead>
                                    <tr>
                                        <th>Dataset</th>
                                        <th>Description</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="userDatasetsList">
                                    <tr>
                                        <td colspan="3" class="text-center">Loading datasets...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                    <div class="modal-footer">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                    </div>
                </div>
            </div>
        </div>
        `;
        document.body.insertAdjacentHTML('beforeend', modalHtml);
    }

    // Set user context
    currentUserId = userId;
    document.getElementById('manageUserDatasetsModalLabel').textContent = `Manage Datasets for User: ${username}`;

    // Load user datasets and available datasets
    loadUserDatasets(userId);

    // Show modal
    const modal = new bootstrap.Modal(document.getElementById('manageUserDatasetsModal'));
    modal.show();
}

function loadUserDatasets(userId) {
    const userDatasetsList = document.getElementById('userDatasetsList');
    const availableDatasetsList = document.getElementById('availableDatasetsList');

    userDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading datasets...</td></tr>';
    availableDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center"><i class="fas fa-spinner fa-spin me-2"></i>Loading datasets...</td></tr>';

    // Load user's current datasets
    fetch(`/api/admin/user/${userId}/datasets`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                if (data.user_datasets.length === 0) {
                    userDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center">User does not have access to any datasets</td></tr>';
                } else {
                    userDatasetsList.innerHTML = '';
                    data.user_datasets.forEach(dataset => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${dataset.name}</td>
                            <td>${dataset.description || '<em>No description</em>'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger" onclick="removeDatasetFromUser(${userId}, ${dataset.id})">
                                    <i class="fas fa-trash-alt"></i> Remove
                                </button>
                            </td>
                        `;
                        userDatasetsList.appendChild(row);
                    });
                }

                // Now load available datasets
                if (data.available_datasets.length === 0) {
                    availableDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center">No additional datasets available</td></tr>';
                } else {
                    availableDatasetsList.innerHTML = '';
                    data.available_datasets.forEach(dataset => {
                        const row = document.createElement('tr');
                        row.innerHTML = `
                            <td>${dataset.name}</td>
                            <td>${dataset.description || '<em>No description</em>'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-primary" onclick="addDatasetToUser(${userId}, ${dataset.id})">
                                    <i class="fas fa-plus"></i> Add
                                </button>
                            </td>
                        `;
                        availableDatasetsList.appendChild(row);
                    });
                }
            } else {
                userDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading datasets</td></tr>';
                availableDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading datasets</td></tr>';
                showAlert(data.message || 'Error loading user datasets', 'error');
            }
        })
        .catch(error => {
            console.error('Error loading user datasets:', error);
            userDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading datasets</td></tr>';
            availableDatasetsList.innerHTML = '<tr><td colspan="3" class="text-center text-danger">Error loading datasets</td></tr>';
            showAlert('Error loading user datasets', 'error');
        });
}

function addDatasetToUser(userId, datasetId) {
    // Show loading state
    const btn = document.querySelector(`#availableDatasetsList button[onclick*="${datasetId}"]`);
    const originalBtnText = btn.innerHTML;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    btn.disabled = true;

    fetch(`/api/admin/user/${userId}/datasets`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            dataset_ids: [datasetId]
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Dataset added to user successfully', 'success');
            // Reload user datasets
            loadUserDatasets(userId);
        } else {
            showAlert(data.message || 'Error adding dataset to user', 'error');
            btn.innerHTML = originalBtnText;
            btn.disabled = false;
        }
    })
    .catch(error => {
        console.error('Error adding dataset to user:', error);
        showAlert('Error adding dataset to user', 'error');
        btn.innerHTML = originalBtnText;
        btn.disabled = false;
    });
}

function removeDatasetFromUser(userId, datasetId) {
    if (!confirm('Are you sure you want to remove this dataset from the user?')) {
        return;
    }

    fetch(`/api/admin/user/${userId}/datasets/${datasetId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showAlert('Dataset removed from user successfully', 'success');
            // Reload user datasets
            loadUserDatasets(userId);
        } else {
            showAlert(data.message || 'Error removing dataset from user', 'error');
        }
    })
    .catch(error => {
        console.error('Error removing dataset from user:', error);
        showAlert('Error removing dataset from user', 'error');
    });
}

// Helper function for showing alerts (reuse from main scripts.js)
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

// Initialize global variables
let currentDatasetId = null;
let currentUserId = null;
