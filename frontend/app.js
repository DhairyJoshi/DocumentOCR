document.addEventListener('DOMContentLoaded', () => {
    const uploadForm = document.getElementById('upload-form');
    if (!uploadForm) return;

    const fileInput = document.getElementById('file-input');
    const dropZone = document.getElementById('drop-zone');
    const browseBtn = document.getElementById('browse-btn');
    const submitBtn = document.getElementById('submit-btn');
    const btnText = submitBtn.querySelector('.btn-text');
    const spinner = submitBtn.querySelector('.spinner');
    
    const stateEmpty = document.getElementById('drop-state-empty');
    const stateSelected = document.getElementById('drop-state-selected');
    const previewImg = document.getElementById('preview-img');
    const previewDoc = document.getElementById('preview-doc');
    const filenameDisplay = document.getElementById('selected-filename');
    const filesizeDisplay = document.getElementById('selected-filesize');
    const removeBtn = document.getElementById('remove-file-btn');
    const errorToast = document.getElementById('error-message');

    let currentFile = null;

    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('drag-active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('drag-active'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });

    browseBtn.addEventListener('click', () => fileInput.click());
    
    dropZone.addEventListener('click', (e) => {
        if (!currentFile && e.target === dropZone || e.target.closest('#drop-state-empty')) {
            fileInput.click();
        }
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    removeBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        clearFile();
    });

    function handleFiles(files) {
        hideError();
        if (files.length === 0) return;
        
        const file = files[0];
        
        const validTypes = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp', 'application/pdf'];
        const ext = file.name.split('.').pop().toLowerCase();
        const validExts = ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'tif', 'webp', 'pdf'];
        
        if (!validTypes.includes(file.type) && !validExts.includes(ext)) {
            showError("Please upload a valid image or PDF document.");
            return;
        }

        if (file.size > 25 * 1024 * 1024) {
            showError("File is too large. Maximum size is 25MB.");
            return;
        }

        currentFile = file;
        
        filenameDisplay.textContent = file.name;
        filesizeDisplay.textContent = formatBytes(file.size);
        
        if (file.type.startsWith('image/')) {
            const reader = new FileReader();
            reader.onload = (e) => {
                previewImg.src = e.target.result;
                previewImg.style.display = 'block';
                previewDoc.style.display = 'none';
            };
            reader.readAsDataURL(file);
        } else {
            previewImg.style.display = 'none';
            previewDoc.style.display = 'block';
        }

        stateEmpty.classList.add('hidden');
        stateSelected.classList.remove('hidden');
        submitBtn.disabled = false;
    }

    function clearFile() {
        currentFile = null;
        fileInput.value = '';
        previewImg.src = '';
        stateSelected.classList.add('hidden');
        stateEmpty.classList.remove('hidden');
        submitBtn.disabled = true;
        hideError();
    }

    function formatBytes(bytes, decimals = 1) {
        if (bytes === 0) return '0 Bytes';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function showError(msg) {
        errorToast.textContent = msg;
        errorToast.classList.remove('hidden');
    }

    function hideError() {
        errorToast.classList.add('hidden');
    }

    function setLoading(isLoading) {
        if (isLoading) {
            submitBtn.disabled = true;
            btnText.classList.add('hidden');
            spinner.classList.remove('hidden');
            removeBtn.style.pointerEvents = 'none';
            removeBtn.style.opacity = '0.5';
        } else {
            submitBtn.disabled = false;
            btnText.classList.remove('hidden');
            spinner.classList.add('hidden');
            removeBtn.style.pointerEvents = 'auto';
            removeBtn.style.opacity = '1';
        }
    }

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        if (!currentFile) {
            showError("Please select a file first.");
            return;
        }

        hideError();
        setLoading(true);

        const formData = new FormData();
        formData.append('file', currentFile);
        formData.append('language', document.getElementById('language-select').value);

        try {
            const response = await fetch('/api/ocr/extract', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to extract text. Please try again.');
            }

            const result = await response.json();
            
            sessionStorage.setItem('ocrResult', JSON.stringify(result));
            window.location.href = '/result';
            
        } catch (error) {
            console.error("OCR Error:", error);
            showError(error.message);
            setLoading(false);
        }
    });
});