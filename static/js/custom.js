// recipe-form.js

// Add a new ingredient input field
function addIngredient() {
    const container = document.getElementById('ingredient-list');
    const div = document.createElement('div');
    div.className = 'input-group mb-2';
    div.innerHTML = `
        <input type="text" class="form-control" name="ingredients[]" placeholder="e.g., 1 cup flour">
        <button type="button" class="btn btn-outline-danger remove-btn" onclick="removeIngredient(this)">
            <i class="fa-solid fa-xmark"></i>
        </button>
    `;
    container.appendChild(div);
}

// Remove an ingredient input group
function removeIngredient(button) {
    button.closest('.input-group').remove();
}

// Add a new step input group (text + optional image upload)
function addStep() {
    const container = document.getElementById('step-list');
    const stepWrapper = document.createElement('div');
    stepWrapper.className = 'mb-3';

    stepWrapper.innerHTML = `
        <div class="input-group mb-2">
            <input type="text" class="form-control" name="steps[]" placeholder="Describe this step...">
            <button type="button" class="btn btn-outline-danger remove-btn" onclick="removeStep(this)">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
        <div class="input-group mb-2">
            <input type="file" class="form-control" name="steps_images[]" accept="image/*">
            <button type="button" class="btn btn-outline-danger remove-btn" onclick="removeStepImage(this)">
                <i class="fa-solid fa-xmark"></i>
            </button>
        </div>
    `;

    container.appendChild(stepWrapper);
}

// Remove the step text input group
function removeStep(button) {
    button.closest('.input-group').parentElement.remove();
}

// Remove only the image input field for a step
function removeStepImage(button) {
    button.closest('.input-group').remove();
}

// Remove current image preview and set hidden delete flag
function removeCurrentImage(button) {
    const container = button.closest('.current-image');
    const hiddenInput = container.querySelector("input[type='hidden']");
    const image = container.querySelector("img");

    if (image) image.style.display = "none";  // hide the image
    if (button) button.style.display = "none"; // hide the X button
    if (hiddenInput) hiddenInput.value = "1";  // mark for deletion
}

function enablePasswordFields(btnId, oldPwdId, newPwdId) {
    const btn = document.getElementById(btnId);
    const oldPwd = document.getElementById(oldPwdId);
    const newPwd = document.getElementById(newPwdId);

    if (btn && oldPwd && newPwd) {
        btn.addEventListener('click', function() {
            oldPwd.disabled = false;
            newPwd.disabled = false;
        });
    }
}