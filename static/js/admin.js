/**
 * IEEE 2030.5 Admin Interface JavaScript
 * Provides Show Code feature, form validation, and dynamic form handling
 */

// =============================================================================
// SHOW CODE FEATURE
// =============================================================================

/**
 * Toggle the Show Code section visibility
 */
function toggleShowCode(button) {
    const content = button.nextElementSibling;
    const arrow = button.querySelector('.arrow');

    button.classList.toggle('active');
    content.classList.toggle('active');

    if (content.classList.contains('active')) {
        updateGeneratedCode();
    }
}

/**
 * Copy code to clipboard
 */
function copyCode(button) {
    const codeBlock = button.parentElement.querySelector('pre');
    const text = codeBlock.textContent;

    navigator.clipboard.writeText(text).then(() => {
        const originalText = button.textContent;
        button.textContent = 'Copied!';
        button.classList.add('copied');

        setTimeout(() => {
            button.textContent = originalText;
            button.classList.remove('copied');
        }, 2000);
    }).catch(err => {
        console.error('Failed to copy:', err);
        alert('Failed to copy code to clipboard');
    });
}

/**
 * Generate Python httpx code for the current form
 */
function generateHttpxCode(formData, endpoint, method = 'POST') {
    const useAuth = document.getElementById('useAuth')?.checked ?? false;

    // Build XML from form data
    const xmlContent = generateXmlFromForm(formData);

    let code = `import httpx

# IEEE 2030.5 API Request
url = "${window.location.origin}${endpoint}"
`;

    if (useAuth) {
        code += `
# TLS Client Certificate Authentication
cert = ("path/to/client.crt", "path/to/client.key")
ca_cert = "path/to/ca.crt"

`;
    }

    code += `# XML Payload
xml_data = """${xmlContent}"""

headers = {
    "Content-Type": "application/sep+xml",
    "Accept": "application/sep+xml"
}

`;

    if (useAuth) {
        code += `# Create client with TLS authentication
with httpx.Client(cert=cert, verify=ca_cert) as client:
    response = client.${method.toLowerCase()}(
        url,
        content=xml_data.encode('utf-8'),
        headers=headers
    )
`;
    } else {
        code += `# Create client (no authentication)
with httpx.Client(verify=False) as client:
    response = client.${method.toLowerCase()}(
        url,
        content=xml_data.encode('utf-8'),
        headers=headers
    )
`;
    }

    code += `
# Check response
print(f"Status: {response.status_code}")
print(f"Response: {response.text}")

if response.status_code in [200, 201, 204]:
    print("Success!")
else:
    print(f"Error: {response.status_code}")
`;

    return code;
}

/**
 * Generate XML from form data - override this function per form type
 * This is a base implementation that should be overridden
 */
function generateXmlFromForm(formData) {
    // Default implementation - should be overridden per form
    return '<?xml version="1.0" encoding="UTF-8"?>\n<!-- Override generateXmlFromForm for specific form -->';
}

/**
 * Update the generated code display
 */
function updateGeneratedCode() {
    const form = document.querySelector('form');
    if (!form) return;

    const formData = new FormData(form);
    const endpoint = form.action || window.location.pathname;
    const method = form.method?.toUpperCase() || 'POST';

    const code = generateHttpxCode(formData, endpoint, method);

    const codeElement = document.getElementById('generatedCode');
    if (codeElement) {
        codeElement.textContent = code;
    }
}

// =============================================================================
// FORM VALIDATION
// =============================================================================

/**
 * Validate a single form field
 */
function validateField(field) {
    const formGroup = field.closest('.form-group');
    if (!formGroup) return true;

    let isValid = true;
    let errorMessage = '';

    // Required validation
    if (field.required && !field.value.trim()) {
        isValid = false;
        errorMessage = 'This field is required';
    }

    // Number validation
    if (field.type === 'number' && field.value) {
        const value = parseFloat(field.value);
        if (isNaN(value)) {
            isValid = false;
            errorMessage = 'Must be a valid number';
        } else {
            if (field.min && value < parseFloat(field.min)) {
                isValid = false;
                errorMessage = `Value must be at least ${field.min}`;
            }
            if (field.max && value > parseFloat(field.max)) {
                isValid = false;
                errorMessage = `Value must be at most ${field.max}`;
            }
        }
    }

    // Pattern validation
    if (field.pattern && field.value) {
        const regex = new RegExp(field.pattern);
        if (!regex.test(field.value)) {
            isValid = false;
            errorMessage = field.title || 'Invalid format';
        }
    }

    // Custom IEEE 2030.5 validations based on field name/id
    if (isValid && field.value) {
        const fieldName = field.name || field.id || '';

        // Certificate name validation (alphanumeric, underscores, hyphens)
        if (fieldName === 'cert_name') {
            if (!/^[a-zA-Z0-9_-]+$/.test(field.value)) {
                isValid = false;
                errorMessage = 'Certificate name can only contain letters, numbers, underscores, and hyphens';
            }
        }

        // PIN validation (numeric only)
        if (fieldName === 'pin' && field.value) {
            if (!/^\d+$/.test(field.value)) {
                isValid = false;
                errorMessage = 'PIN must contain only numbers';
            }
        }

        // mRID validation (hex string)
        if (fieldName === 'mRID' && field.value) {
            if (!/^[0-9A-Fa-f]+$/.test(field.value.replace(/-/g, ''))) {
                isValid = false;
                errorMessage = 'mRID must be a valid hexadecimal string';
            }
        }

        // Duration validation (positive integer)
        if (fieldName === 'duration' && field.value) {
            const duration = parseInt(field.value);
            if (isNaN(duration) || duration < 0) {
                isValid = false;
                errorMessage = 'Duration must be a positive number';
            }
        }

        // Power values (can be negative for import/export)
        if ((fieldName.includes('MaxW') || fieldName.includes('MaxVar') || fieldName.includes('MaxVA')) && field.value) {
            const power = parseInt(field.value);
            if (isNaN(power)) {
                isValid = false;
                errorMessage = 'Power values must be valid integers';
            }
        }
    }

    // Update UI
    updateFieldValidation(formGroup, isValid, errorMessage);

    return isValid;
}

/**
 * Update field validation UI
 */
function updateFieldValidation(formGroup, isValid, errorMessage) {
    formGroup.classList.remove('error', 'success');

    // Remove existing error message
    const existingError = formGroup.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }

    if (!isValid) {
        formGroup.classList.add('error');
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = errorMessage;
        formGroup.appendChild(errorDiv);
    } else if (formGroup.querySelector('input, select, textarea')?.value) {
        formGroup.classList.add('success');
    }
}

/**
 * Validate entire form
 */
function validateForm(form) {
    const fields = form.querySelectorAll('input, select, textarea');
    let isValid = true;

    fields.forEach(field => {
        if (!validateField(field)) {
            isValid = false;
        }
    });

    return isValid;
}

/**
 * Initialize form validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');

    forms.forEach(form => {
        // Add real-time validation
        const fields = form.querySelectorAll('input, select, textarea');
        fields.forEach(field => {
            field.addEventListener('blur', () => validateField(field));
            field.addEventListener('input', () => {
                // Clear error on input
                const formGroup = field.closest('.form-group');
                if (formGroup) {
                    formGroup.classList.remove('error');
                    const errorMsg = formGroup.querySelector('.error-message');
                    if (errorMsg) errorMsg.remove();
                }

                // Update generated code
                updateGeneratedCode();
            });
        });

        // Validate on submit
        form.addEventListener('submit', (e) => {
            if (!validateForm(form)) {
                e.preventDefault();
                alert('Please fix the validation errors before submitting.');
            }
        });
    });
}

// =============================================================================
// DYNAMIC FORM FIELDS
// =============================================================================

/**
 * Add a new dynamic field row (for curve points, etc.)
 */
function addDynamicField(containerId, template) {
    const container = document.getElementById(containerId);
    if (!container) return;

    const index = container.children.length;
    const newRow = document.createElement('div');
    newRow.className = 'dynamic-field-row';
    newRow.innerHTML = template.replace(/\{index\}/g, index);

    container.appendChild(newRow);
    updateGeneratedCode();
}

/**
 * Remove a dynamic field row
 */
function removeDynamicField(button) {
    const row = button.closest('.dynamic-field-row');
    if (row) {
        row.remove();
        updateGeneratedCode();
    }
}

// =============================================================================
// UTILITY FUNCTIONS
// =============================================================================

/**
 * Format date for IEEE 2030.5 (Unix timestamp)
 */
function dateToTimestamp(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return Math.floor(date.getTime() / 1000);
}

/**
 * Format timestamp to datetime-local input
 */
function timestampToDate(timestamp) {
    if (!timestamp) return '';
    const date = new Date(timestamp * 1000);
    return date.toISOString().slice(0, 16);
}

/**
 * Escape XML special characters
 */
function escapeXml(str) {
    if (!str) return '';
    return str.toString()
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&apos;');
}

/**
 * Generate UUID for mRID
 */
function generateUUID() {
    return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        const r = Math.random() * 16 | 0;
        const v = c === 'x' ? r : (r & 0x3 | 0x8);
        return v.toString(16).toUpperCase();
    });
}

/**
 * Convert hex string to bytes representation
 */
function hexToBytes(hex) {
    return hex.replace(/(.{2})/g, '$1 ').trim();
}

// =============================================================================
// INITIALIZATION
// =============================================================================

document.addEventListener('DOMContentLoaded', () => {
    // Initialize form validation
    initFormValidation();

    // Initialize Show Code toggle
    const showCodeToggles = document.querySelectorAll('.show-code-toggle');
    showCodeToggles.forEach(toggle => {
        toggle.addEventListener('click', () => toggleShowCode(toggle));
    });

    // Initialize copy buttons
    const copyButtons = document.querySelectorAll('.copy-btn');
    copyButtons.forEach(button => {
        button.addEventListener('click', () => copyCode(button));
    });

    // Update code on auth toggle change
    const authToggle = document.getElementById('useAuth');
    if (authToggle) {
        authToggle.addEventListener('change', updateGeneratedCode);
    }
});
