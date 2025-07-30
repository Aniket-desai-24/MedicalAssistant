// Medical AI Assistant - Frontend JavaScript

class MedicalAIAssistant {
    constructor() {
        this.init();
    }

    init() {
        this.loadPatients();
        this.bindEvents();
    }

    bindEvents() {
        // Form submission
        document.getElementById('prescriptionForm').addEventListener('submit', (e) => {
            e.preventDefault();
            this.checkPrescription();
        });

        // Patient name input for autocomplete
        document.getElementById('patientName').addEventListener('input', (e) => {
            this.filterPatients(e.target.value);
        });

        // Add drug autocomplete for medicine inputs
        this.setupDrugAutocomplete();
        
        // Setup file upload form
        this.setupFileUpload();
    }

    async loadPatients() {
        try {
            const response = await fetch('/patients');
            if (!response.ok) {
                throw new Error('Failed to load patients');
            }
            
            const patients = await response.json();
            this.displayPatients(patients);
        } catch (error) {
            console.error('Error loading patients:', error);
            document.getElementById('patientsList').innerHTML = `
                <div class="text-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Error loading patients
                </div>
            `;
        }
    }

    displayPatients(patients) {
        const patientsList = document.getElementById('patientsList');
        
        if (patients.length === 0) {
            patientsList.innerHTML = `
                <div class="text-muted">
                    <i class="fas fa-info-circle me-2"></i>
                    No patients found
                </div>
            `;
            return;
        }

        patientsList.innerHTML = patients.map(patient => `
            <div class="patient-item" onclick="selectPatient('${patient.name}')">
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <strong>${patient.name}</strong>
                        <br>
                        <small class="text-muted">ID: ${patient.patient_id}</small>
                    </div>
                    <div>
                        <small class="text-muted">
                            ${patient.date_of_birth ? new Date(patient.date_of_birth).toLocaleDateString() : 'DOB not available'}
                        </small>
                    </div>
                </div>
            </div>
        `).join('');
    }

    filterPatients(searchTerm) {
        const patientItems = document.querySelectorAll('.patient-item');
        
        patientItems.forEach(item => {
            const patientName = item.querySelector('strong').textContent.toLowerCase();
            if (patientName.includes(searchTerm.toLowerCase())) {
                item.style.display = 'block';
            } else {
                item.style.display = 'none';
            }
        });
    }

    async checkPrescription() {
        const patientName = document.getElementById('patientName').value.trim();
        const medicineInputs = document.querySelectorAll('.medicine-input');
        
        // Validate inputs
        if (!patientName) {
            this.showError('Please enter a patient name');
            return;
        }

        const medicines = Array.from(medicineInputs)
            .map(input => input.value.trim())
            .filter(value => value !== '');

        if (medicines.length === 0) {
            this.showError('Please enter at least one medicine');
            return;
        }

        // Show loading
        this.showLoading();

        try {
            const response = await fetch('/check_prescription', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    patient_name: patientName,
                    medicines: medicines
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to check prescription');
            }

            const results = await response.json();
            this.displayResults(results);

        } catch (error) {
            console.error('Error checking prescription:', error);
            this.showError(error.message);
        }
    }

    displayResults(results) {
        // Hide loading and error sections
        document.getElementById('loadingSection').classList.add('d-none');
        document.getElementById('errorSection').classList.add('d-none');
        
        // Show results section with animation
        const resultsSection = document.getElementById('resultsSection');
        resultsSection.classList.remove('d-none');
        resultsSection.classList.add('results-enter');
        
        // Show success message if all clear
        if (results.is_safe && (!results.warnings || results.warnings.length === 0)) {
            this.showSuccessMessage('All medicines are safe for this patient!');
        }

        // Update safety status
        this.updateSafetyStatus(results);

        // Update contraindications
        this.updateContraindications(results.contraindications);

        // Update warnings
        this.updateWarnings(results.warnings);

        // Update safe medicines
        this.updateSafeMedicines(results.safe_medicines);

        // Update AI analysis
        this.updateAIAnalysis(results.ai_analysis);
    }

    updateSafetyStatus(results) {
        const safetyStatus = document.getElementById('safetyStatus');
        
        if (results.is_safe) {
            safetyStatus.className = 'alert alert-success';
            safetyStatus.innerHTML = `
                <h6 class="alert-heading">
                    <i class="fas fa-check-circle me-2"></i>
                    Prescription is Safe
                </h6>
                <p class="mb-0">
                    No critical allergy conflicts detected for patient <strong>${results.patient_name}</strong>.
                </p>
            `;
        } else {
            safetyStatus.className = 'alert alert-danger';
            safetyStatus.innerHTML = `
                <h6 class="alert-heading">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Allergy Conflicts Detected
                </h6>
                <p class="mb-0">
                    <strong>WARNING:</strong> Potential allergy conflicts found for patient <strong>${results.patient_name}</strong>. 
                    Review contraindications and warnings below.
                </p>
            `;
        }
    }

    updateContraindications(contraindications) {
        const section = document.getElementById('contraindicationsSection');
        const list = document.getElementById('contraindicationsList');

        if (contraindications && contraindications.length > 0) {
            section.classList.remove('d-none');
            list.innerHTML = contraindications.map(item => `
                <div class="contraindication-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong class="text-danger">${item.medicine}</strong>
                            <br>
                            <small class="text-muted">Allergen: ${item.allergen}</small>
                        </div>
                        <span class="badge severity-${item.severity}">${item.severity.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <p class="mt-2 mb-0">${item.reason}</p>
                </div>
            `).join('');
        } else {
            section.classList.add('d-none');
        }
    }

    updateWarnings(warnings) {
        const section = document.getElementById('warningsSection');
        const list = document.getElementById('warningsList');

        if (warnings && warnings.length > 0) {
            section.classList.remove('d-none');
            list.innerHTML = warnings.map(item => `
                <div class="warning-item">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <strong class="text-warning">${item.medicine || 'General Warning'}</strong>
                            ${item.allergen ? `<br><small class="text-muted">Allergen: ${item.allergen}</small>` : ''}
                            ${item.confidence ? `<br><small class="text-muted">Confidence: ${item.confidence}</small>` : ''}
                        </div>
                        ${item.severity ? `<span class="badge severity-${item.severity}">${item.severity.replace('_', ' ').toUpperCase()}</span>` : ''}
                    </div>
                    <p class="mt-2 mb-0">${item.reason}</p>
                </div>
            `).join('');
        } else {
            section.classList.add('d-none');
        }
    }

    updateSafeMedicines(safeMedicines) {
        const section = document.getElementById('safeMedicinesSection');
        const list = document.getElementById('safeMedicinesList');

        if (safeMedicines && safeMedicines.length > 0) {
            section.classList.remove('d-none');
            list.innerHTML = safeMedicines.map(medicine => `
                <span class="safe-medicine-item">
                    <i class="fas fa-check me-1"></i>
                    ${medicine}
                </span>
            `).join('');
        } else {
            section.classList.add('d-none');
        }
    }

    updateAIAnalysis(aiAnalysis) {
        const section = document.getElementById('aiAnalysisSection');
        const content = document.getElementById('aiAnalysisContent');

        if (aiAnalysis) {
            section.classList.remove('d-none');
            
            const riskClass = `risk-${aiAnalysis.risk_level}`;
            
            content.innerHTML = `
                <div class="ai-summary">
                    <h6 class="mb-2">Summary</h6>
                    <p class="mb-2">${aiAnalysis.summary}</p>
                    <div class="d-flex align-items-center">
                        <span class="me-2">Risk Level:</span>
                        <span class="badge ${riskClass} ${aiAnalysis.risk_level}">
                            ${aiAnalysis.risk_level.toUpperCase()}
                        </span>
                    </div>
                </div>
                ${aiAnalysis.recommendations && aiAnalysis.recommendations.length > 0 ? `
                    <div class="ai-recommendations">
                        <h6 class="mb-2">Recommendations</h6>
                        ${aiAnalysis.recommendations.map(rec => `
                            <div class="recommendation-item">
                                <i class="fas fa-lightbulb me-2 text-warning"></i>
                                ${rec}
                            </div>
                        `).join('')}
                    </div>
                ` : ''}
            `;
        } else {
            section.classList.add('d-none');
        }
    }

    showLoading() {
        document.getElementById('resultsSection').classList.add('d-none');
        document.getElementById('errorSection').classList.add('d-none');
        document.getElementById('loadingSection').classList.remove('d-none');
    }

    showError(message) {
        document.getElementById('resultsSection').classList.add('d-none');
        document.getElementById('loadingSection').classList.add('d-none');
        
        const errorSection = document.getElementById('errorSection');
        const errorMessage = document.getElementById('errorMessage');
        
        errorMessage.textContent = message;
        errorSection.classList.remove('d-none');
    }

    setupDrugAutocomplete() {
        // Add autocomplete functionality to medicine inputs
        document.addEventListener('input', async (e) => {
            if (e.target.classList.contains('medicine-input')) {
                console.log('Input detected on medicine field'); // Debug
                await this.handleDrugAutocomplete(e.target);
            }
        });
        
        // Also handle dynamically added inputs
        document.addEventListener('click', (e) => {
            if (e.target.closest('.autocomplete-item')) {
                return; // Handle autocomplete clicks
            }
            // Clear autocomplete when clicking elsewhere
            document.querySelectorAll('.autocomplete-dropdown').forEach(dropdown => {
                dropdown.remove();
            });
        });
    }

    async handleDrugAutocomplete(input) {
        const query = input.value.trim();
        console.log('Autocomplete triggered for:', query); // Debug log
        
        if (query.length < 2) {
            this.clearAutocomplete(input);
            return;
        }

        try {
            const response = await fetch(`/drugs?search=${encodeURIComponent(query)}`);
            if (response.ok) {
                const drugs = await response.json();
                console.log('Found drugs:', drugs.length); // Debug log
                this.showAutocomplete(input, drugs);
            }
        } catch (error) {
            console.error('Error fetching drug suggestions:', error);
        }
    }

    showAutocomplete(input, drugs) {
        console.log('Showing autocomplete for', drugs.length, 'drugs'); // Debug
        
        // Remove existing autocomplete
        this.clearAutocomplete(input);

        if (drugs.length === 0) return;

        const dropdown = document.createElement('div');
        dropdown.className = 'autocomplete-dropdown';
        dropdown.style.cssText = `
            position: absolute;
            top: 100%;
            left: 0;
            right: 0;
            background: white;
            border: 1px solid #ccc;
            border-top: none;
            max-height: 200px;
            overflow-y: auto;
            z-index: 1000;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            border-radius: 0 0 0.375rem 0.375rem;
        `;

        drugs.slice(0, 5).forEach(drug => {
            const item = document.createElement('div');
            item.className = 'autocomplete-item';
            item.style.cssText = `
                padding: 10px;
                cursor: pointer;
                border-bottom: 1px solid #eee;
            `;
            item.innerHTML = `
                <strong>${drug.drug_name}</strong>
                ${drug.generic_name ? `<br><small class="text-muted">Generic: ${drug.generic_name}</small>` : ''}
            `;
            
            item.addEventListener('mouseenter', () => {
                item.style.backgroundColor = '#f8f9fa';
            });
            
            item.addEventListener('mouseleave', () => {
                item.style.backgroundColor = 'white';
            });
            
            item.addEventListener('click', () => {
                input.value = drug.drug_name;
                this.clearAutocomplete(input);
            });

            dropdown.appendChild(item);
        });

        // Position dropdown relative to input
        const inputContainer = input.parentElement;
        if (!inputContainer.style.position) {
            inputContainer.style.position = 'relative';
        }
        inputContainer.appendChild(dropdown);
        console.log('Dropdown added to container'); // Debug
    }

    clearAutocomplete(input) {
        const container = input.parentElement;
        const existing = container.querySelector('.autocomplete-dropdown');
        if (existing) {
            existing.remove();
        }
    }

    showSuccessMessage(message) {
        const toast = document.createElement('div');
        toast.className = 'toast-message success';
        toast.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
        `;
        toast.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            background: #d4edda;
            color: #155724;
            padding: 15px 20px;
            border-radius: 5px;
            border-left: 4px solid #27ae60;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 9999;
            animation: slideInRight 0.3s ease-out;
        `;

        document.body.appendChild(toast);

        setTimeout(() => {
            toast.style.animation = 'slideOutRight 0.3s ease-in';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }

    setupFileUpload() {
        const uploadForm = document.getElementById('uploadForm');
        if (uploadForm) {
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.handleFileUpload();
            });
        }
    }

    async handleFileUpload() {
        const patientName = document.getElementById('uploadPatientName').value.trim();
        const fileInput = document.getElementById('prescriptionFile');
        const file = fileInput.files[0];

        if (!patientName || !file) {
            this.showError('Please enter patient name and select a prescription file');
            return;
        }

        this.showLoading();

        try {
            const formData = new FormData();
            formData.append('patient_name', patientName);
            formData.append('file', file);

            const response = await fetch('/upload_prescription', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                if (result.prescription_analysis) {
                    // File processed successfully and prescription analyzed
                    this.displayResults(result.prescription_analysis);
                    this.showExtractedInfo(result);
                } else {
                    // File processed but no medicines found
                    this.showError(result.message || 'No medicines found in the prescription file');
                    if (result.extracted_text_preview) {
                        this.showExtractedText(result.extracted_text_preview);
                    }
                }
            } else {
                this.showError(result.error || 'Failed to process prescription file');
            }

        } catch (error) {
            console.error('Upload error:', error);
            this.showError('Error uploading file: ' + error.message);
        }
    }

    showExtractedInfo(result) {
        const resultsSection = document.getElementById('resultsSection');
        
        // Remove any existing OCR results to prevent duplicates
        const existingOCR = resultsSection.querySelector('.ocr-results');
        if (existingOCR) {
            existingOCR.remove();
        }
        
        const extractedDiv = document.createElement('div');
        extractedDiv.className = 'alert alert-info mt-3 ocr-results';
        extractedDiv.innerHTML = `
            <h6><i class="fas fa-eye me-2"></i>OCR Extraction Results</h6>
            <p><strong>Extracted Medicines:</strong> ${result.extracted_medicines.join(', ')}</p>
            <p><strong>Text Preview:</strong></p>
            <pre class="small">${result.extracted_text_preview}</pre>
        `;
        resultsSection.appendChild(extractedDiv);
    }

    showExtractedText(textPreview) {
        const errorSection = document.getElementById('errorSection');
        const extractedDiv = document.createElement('div');
        extractedDiv.className = 'mt-3 p-3 bg-light rounded';
        extractedDiv.innerHTML = `
            <h6>Extracted Text:</h6>
            <pre class="small">${textPreview}</pre>
            <p class="text-muted small mt-2">
                Please verify the text extraction quality. You may need to:
                <br>• Use a higher quality image
                <br>• Ensure the prescription is clearly visible
                <br>• Try a different file format
            </p>
        `;
        errorSection.appendChild(extractedDiv);
    }
}

// Global functions
function selectPatient(patientName) {
    document.getElementById('patientName').value = patientName;
}

function addMedicineField() {
    const container = document.getElementById('medicinesContainer');
    const newField = document.createElement('div');
    newField.className = 'input-group mb-2';
    newField.innerHTML = `
        <input 
            type="text" 
            class="form-control medicine-input" 
            placeholder="Enter medicine name"
        >
        <button 
            class="btn btn-outline-danger" 
            type="button" 
            onclick="removeMedicineField(this)"
        >
            <i class="fas fa-minus"></i>
        </button>
    `;
    container.appendChild(newField);
}

function removeMedicineField(button) {
    const container = document.getElementById('medicinesContainer');
    if (container.children.length > 1) {
        button.parentElement.remove();
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new MedicalAIAssistant();
});
