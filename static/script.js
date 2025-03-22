// Global Variables
let globalUID = null;
let globalTarget = null;

// Form Submission
function submitForm(event) {
    event.preventDefault();
    const form = event.target;
    const formData = new FormData(form);
    fetch(form.action, {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById("message").innerText = data.message;
    })
    .catch(error => console.error("Error saving configuration:", error));
}

// Feature Handling
function toggleSensitive(element) {
    const featureInput = element.parentElement.previousElementSibling;
    if (element.checked) {
        featureInput.classList.add("sensitive-overlay");
    } else {
        featureInput.classList.remove("sensitive-overlay");
    }
    updateVisualization();
}
function toggleTarget(element) {
    const allTargetRadios = document.querySelectorAll("input[type='radio'][name='target']");
    const featureName = element.closest('.feature-item').querySelector('input[type="text"]').value;

    console.log("Toggle Target called:");
    console.log("Feature Name:", featureName);
    console.log("Current Global Target:", globalTarget);

    // Uncheck any other selected targets
    allTargetRadios.forEach((radio) => {
        if (radio !== element && radio.checked) {
            radio.checked = false;
            console.log("Unchecking previous target:", radio);
        }
    });

    // Set the global target to the new feature name
    globalTarget = featureName;
    console.log("Setting Global Target to:", globalTarget);

    updateVisualization();
}

function addFeature(sourceId) {
    const featureContainer = document.getElementById(`features_${sourceId}`);
    const featureCount = featureContainer.children.length + 1;

    const featureDiv = document.createElement('div');
    featureDiv.className = 'feature-item';
    featureDiv.innerHTML = `
        <input type="text" name="feature_name_${sourceId}_${featureCount}" placeholder="Enter feature name" required>
        <label class="sensitive-label">
            <input type="checkbox" name="sensitive_${sourceId}_${featureCount}" onclick="toggleSensitive(this)">
            <i class="fa-solid fa-lock" style="color: red;"></i> Sensitive
        </label>
        <label class="identifier-label">
            <input type="checkbox" name="identifier_${sourceId}_${featureCount}" onclick="toggleIdentifier(this, this.parentElement.previousElementSibling.value)">
            <i class="fa-solid fa-key"></i> UID
        </label>
        <label class="target-label">
            <input type="radio" name="target" onclick="toggleTarget(this)">
            <i class="fa-solid fa-bullseye"></i> Target
        </label>
        <button class="delete-button" onclick="deleteFeature(this)">
            <i class="fa-solid fa-trash"></i>
        </button>
    `;
    featureContainer.appendChild(featureDiv);
    updateTargetAndIdentifierOptions();
    updateVisualization();
}
function deleteFeature(button) {
    button.parentElement.remove();
    updateTargetAndIdentifierOptions();
    updateVisualization();
}

// Data Source Handling
function addDataSource() {
    const container = document.getElementById('dataSources');
    const sourceCount = container.children.length + 1;
    const sourceDiv = document.createElement('div');
    sourceDiv.className = 'collapsible-card';
    sourceDiv.innerHTML = `
        <div class="collapsible-header" onclick="toggleCollapse(this)">
            <h3><i class="fa-solid fa-database"></i> Data Source ${sourceCount}</h3>
            <i class="fa-solid fa-chevron-down"></i>
            <button class="delete-button" onclick="deleteDataSource(this)">
                <i class="fa-solid fa-trash"></i>
            </button>
        </div>
        <div class="collapsible-content">
            <label>Source Name:</label>
            <input type="text" name="source_name_${sourceCount}" placeholder="Enter source name" required>
            <label>Number of Features:</label>
            <input type="number" name="feature_count_${sourceCount}" placeholder="Number of features" min="1" required>
            <button class="btn-secondary" onclick="addFeature(${sourceCount})">
                <i class="fa-solid fa-plus"></i> Add Feature
            </button>
            <div class="features" id="features_${sourceCount}"></div>
        </div>
    `;
    container.appendChild(sourceDiv);
    updateVisualization();
}

function deleteDataSource(button) {
    const card = button.closest('.collapsible-card');
    card.remove();
    updateVisualization();
}

function toggleCollapse(header) {
    const content = header.nextElementSibling;
    content.style.display = content.style.display === "none" ? "block" : "none";
}

// UID Handling

// UID Handling with Debugging
// UID Handling with Debugging
function toggleIdentifier(element) {
    const allCheckboxes = document.querySelectorAll(`input[type="checkbox"][name^="identifier_"]`);

    // Dynamically get the feature name from the checkbox's sibling input field
    const featureName = element.closest('.feature-item').querySelector('input[type="text"]').value;

    console.log("Toggle Identifier called:");
    console.log("Feature Name:", featureName);
    console.log("Current Global UID:", globalUID);

    // If there is already a global UID and it does not match the current feature name, prevent setting
    if (globalUID && globalUID !== featureName) {
        console.warn("UID conflict detected! Current UID:", globalUID, "| New UID:", featureName);
        alert("Error: UID must be consistent across all data sources! The UID field name should match.");
        element.checked = false;
        return;
    }

    // Set the global UID if checked
    if (element.checked) {
        globalUID = featureName;
        console.log("Setting Global UID to:", globalUID);
        allCheckboxes.forEach((checkbox) => {
            const checkboxName = checkbox.closest('.feature-item').querySelector('input[type="text"]').value;
            console.log("Comparing:", checkboxName, "with", featureName);
            if (checkbox !== element && checkbox.checked && checkboxName !== featureName) {
                console.warn("Conflict detected between:", checkboxName, "and", featureName);
                alert("Error: UID must be the same field name across all data sources!");
                element.checked = false;
                return;
            }
        });
    } else {
        globalUID = null;
        console.log("Global UID cleared");
    }

    updateVisualization();
    updateTargetAndIdentifierOptions();
}

// Visualization Update
function updateVisualization() {
    const visualization = document.getElementById('visualization');
    visualization.innerHTML = '';
    const sources = document.querySelectorAll('.collapsible-card');
    const visualizationWrapper = document.createElement('div');
    visualizationWrapper.style.display = 'flex';
    visualizationWrapper.style.flexWrap = 'wrap';
    visualizationWrapper.style.gap = '10px';
    visualizationWrapper.style.position = 'relative';

    sources.forEach((source, index) => {
        const sourceName = source.querySelector('input[type="text"]').value;
        const features = source.querySelectorAll('.feature-item');
        const featureList = Array.from(features).map((feature) => {
            const featureName = feature.querySelector('input[type="text"]').value;
            const isUID = feature.querySelector('input[type="checkbox"][name^="identifier_"]').checked;
            const isTarget = feature.querySelector('input[type="radio"][name="target"]').checked;
            const isSensitive = feature.querySelector('input[type="checkbox"][name^="sensitive_"]').checked;

            let icon = '';
            let color = 'black';
            if (isUID) { icon = '🔑'; color = 'blue'; }
            if (isTarget) { icon = '🎯'; color = 'green'; }
            if (isSensitive) { icon = '🔒'; color = 'red'; }

            return `<li style="color: ${color};">${icon} ${featureName}</li>`;
        }).join('');

        const sourceDiv = document.createElement('div');
        sourceDiv.className = 'visualization-table';
        sourceDiv.style.backgroundColor = '#f0f0f0';
        sourceDiv.style.padding = '10px';
        sourceDiv.style.margin = '5px';
        sourceDiv.style.borderRadius = '8px';
        sourceDiv.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
        sourceDiv.style.border = '1px solid #d0d0d0';
        sourceDiv.style.minWidth = '200px';
        sourceDiv.style.flex = '1';
        sourceDiv.innerHTML = `<h4>${sourceName}</h4><ul>${featureList}</ul>`;
        visualizationWrapper.appendChild(sourceDiv);
    });

    visualization.appendChild(visualizationWrapper);
}

// Update Target and Identifier Options
function updateTargetAndIdentifierOptions() {
    const targetSelect = document.getElementById("targetVariable");
    const identifierSelect = document.getElementById("identifierVariable");
    const features = document.querySelectorAll(".feature-item input[type='text']");

    targetSelect.innerHTML = "";
    identifierSelect.innerHTML = "";

    features.forEach((feature) => {
        const featureName = feature.value;
        if (featureName) {
            const targetOption = document.createElement("option");
            targetOption.value = featureName;
            targetOption.textContent = featureName;

            const identifierOption = document.createElement("option");
            identifierOption.value = featureName;
            identifierOption.textContent = featureName;

            targetSelect.appendChild(targetOption);
            identifierSelect.appendChild(identifierOption);
        }
    });
}
