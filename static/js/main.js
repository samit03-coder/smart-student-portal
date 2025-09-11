// Smart Student Portal - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Form validation enhancement
    const forms = document.querySelectorAll('.needs-validation');
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // Search functionality
    const searchInput = document.querySelector('input[name="query"]');
    if (searchInput) {
        let searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => {
                // Implement live search here
                console.log('Searching for:', this.value);
            }, 300);
        });
    }

    // File upload preview
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            const file = this.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('filePreview');
                    if (preview) {
                        preview.innerHTML = `
                            <div class="alert alert-info">
                                <i class="bi bi-file-earmark me-2"></i>
                                Selected: ${file.name} (${formatFileSize(file.size)})
                            </div>
                        `;
                    }
                };
                reader.readAsDataURL(file);
            }
        });
    });

    // Theme toggle functionality
    const themeToggle = document.getElementById('themeToggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('theme', newTheme);
        });

        // Load saved theme
        const savedTheme = localStorage.getItem('theme');
        if (savedTheme) {
            document.documentElement.setAttribute('data-bs-theme', savedTheme);
        }
    }

    // Notification system
    window.showNotification = function(message, type = 'info', duration = 5000) {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(notification);
        
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(notification);
            bsAlert.close();
        }, duration);
    };

    // Loading states for buttons
    window.setButtonLoading = function(button, loading = true) {
        if (loading) {
            button.disabled = true;
            button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
        } else {
            button.disabled = false;
            button.innerHTML = button.getAttribute('data-original-text') || 'Submit';
        }
    };

    // Save original button text
    document.querySelectorAll('button[type="submit"]').forEach(button => {
        button.setAttribute('data-original-text', button.innerHTML);
    });
});

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric'
    });
}

function formatDateTime(dateString) {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

// AJAX helper functions
function makeRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        }
    };

    const mergedOptions = { ...defaultOptions, ...options };
    
    return fetch(url, mergedOptions)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .catch(error => {
            console.error('Request failed:', error);
            showNotification('Request failed. Please try again.', 'danger');
            throw error;
        });
}

// Material sharing functions
function shareMaterial(id, name, link) {
    document.getElementById('shareMaterialId').value = id;
    document.getElementById('shareMaterialName').value = name;
    document.getElementById('shareMaterialLink').value = link;
    
    const modal = new bootstrap.Modal(document.getElementById('shareModal'));
    modal.show();
}

// Download functionality
function downloadMaterial(materialId, materialName) {
    makeRequest(`/api/download/${materialId}`, {
        method: 'GET'
    })
    .then(data => {
        if (data.success && data.download_url) {
            // Create a temporary link and trigger download
            const link = document.createElement('a');
            link.href = data.download_url;
            link.download = data.filename || materialName + '.pdf';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            
            showNotification(`Downloaded: ${materialName}`, 'success');
        } else {
            showNotification(data.error || 'Download failed', 'danger');
        }
    })
    .catch(error => {
        showNotification('Download failed. Please try again.', 'danger');
    });
}

function sendEmail() {
    const materialName = document.getElementById('shareMaterialName').value;
    const materialLink = document.getElementById('shareMaterialLink').value;
    
    const button = event.target;
    setButtonLoading(button, true);
    
    makeRequest('/api/send_email', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            material_name: materialName,
            material_link: materialLink
        })
    })
    .then(data => {
        if (data.success && data.mailto_url) {
            // Open user's email app with pre-filled content
            window.location.href = data.mailto_url;
            showNotification(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('shareModal')).hide();
        } else {
            showNotification(data.error || 'Failed to open email app', 'danger');
        }
    })
    .finally(() => {
        setButtonLoading(button, false);
    });
}

function sendWhatsApp() {
    const materialName = document.getElementById('shareMaterialName').value;
    const materialLink = document.getElementById('shareMaterialLink').value;
    
    const button = event.target;
    setButtonLoading(button, true);
    
    makeRequest('/api/send_whatsapp', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            material_name: materialName,
            material_link: materialLink
        })
    })
    .then(data => {
        if (data.success && data.whatsapp_url) {
            // Open user's WhatsApp app with pre-filled message
            window.open(data.whatsapp_url, '_blank');
            showNotification(data.message, 'success');
            bootstrap.Modal.getInstance(document.getElementById('shareModal')).hide();
        } else {
            showNotification(data.error || 'Failed to open WhatsApp', 'danger');
        }
    })
    .finally(() => {
        setButtonLoading(button, false);
    });
}

// Search and filter functions
function toggleView(view) {
    const listView = document.getElementById('listView');
    const gridView = document.getElementById('gridView');
    const buttons = document.querySelectorAll('.btn-group .btn');
    
    buttons.forEach(btn => btn.classList.remove('active'));
    
    if (view === 'list') {
        listView.style.display = 'block';
        gridView.style.display = 'none';
        buttons[0].classList.add('active');
    } else {
        listView.style.display = 'none';
        gridView.style.display = 'block';
        buttons[1].classList.add('active');
    }
}

function clearFilters() {
    document.querySelectorAll('input[type="checkbox"]').forEach(checkbox => {
        checkbox.checked = true;
    });
    document.querySelector('select').selectedIndex = 0;
    showNotification('Filters cleared', 'info');
}

// Favorites functionality
function addToFavorites(materialId) {
    makeRequest(`/api/favorites/${materialId}`, {
        method: 'POST'
    })
    .then(data => {
        showNotification(data.message, 'success');
    })
    .catch(error => {
        showNotification('Favorites feature coming soon!', 'info');
    });
}

// Preview functionality
function previewMaterial(id, name, link) {
    showNotification('Preview feature coming soon!', 'info');
}

// Upload functionality
function showUploadModal() {
    showNotification('Upload feature coming soon!', 'info');
}

// Notifications functionality
function showNotifications() {
    showNotification('Notifications feature coming soon!', 'info');
}

// Keyboard shortcuts
document.addEventListener('keydown', function(e) {
    // Ctrl/Cmd + K for search
    if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
        e.preventDefault();
        const searchInput = document.querySelector('input[name="query"]');
        if (searchInput) {
            searchInput.focus();
        }
    }
    
    // Escape to close modals
    if (e.key === 'Escape') {
        const modals = document.querySelectorAll('.modal.show');
        modals.forEach(modal => {
            const bsModal = bootstrap.Modal.getInstance(modal);
            if (bsModal) {
                bsModal.hide();
            }
        });
    }
});

// Performance monitoring
window.addEventListener('load', function() {
    // Log page load time
    const loadTime = performance.now();
    console.log(`Page loaded in ${loadTime.toFixed(2)}ms`);
    
    // Lazy load images
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.classList.remove('lazy');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
});

// Error handling
window.addEventListener('error', function(e) {
    console.error('JavaScript error:', e.error);
    showNotification('An error occurred. Please refresh the page.', 'danger');
});

// Service Worker registration (for PWA features)
if ('serviceWorker' in navigator) {
    window.addEventListener('load', function() {
        navigator.serviceWorker.register('/sw.js')
            .then(registration => {
                console.log('SW registered: ', registration);
            })
            .catch(registrationError => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
