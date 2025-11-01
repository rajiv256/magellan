import React, {useRef} from 'react';
import {Download, Upload} from 'lucide-react';

/**
 * ImportExportManager component for importing and exporting design data
 * Supports JSON and XML formats
 */
const ImportExportManager = ({
                                 designData,
                                 onImport,
                                 format = 'json', // Default format is JSON, alternative is 'xml'
                                 onFormatChange
                             }) => {
    const fileInputRef = useRef(null);

    // Convert JS object to XML string
    const objectToXML = (obj, rootName = 'magellanDesign') => {
        // Helper function to convert an individual element
        const createElement = (key, value) => {
            if (value === null || value === undefined) {
                return `<${key}></${key}>`;
            }

            if (typeof value === 'object' && !Array.isArray(value)) {
                let childXml = '';
                for (const childKey in value) {
                    if (Object.prototype.hasOwnProperty.call(value, childKey)) {
                        childXml += createElement(childKey, value[childKey]);
                    }
                }
                return `<${key}>${childXml}</${key}>`;
            }

            if (Array.isArray(value)) {
                let arrayXml = '';
                const singularKey = key.endsWith('s') ? key.slice(0, -1) : `${key}Item`;
                for (const item of value) {
                    arrayXml += createElement(singularKey, item);
                }
                return `<${key}>${arrayXml}</${key}>`;
            }

            // Handle basic types - escape XML special characters
            const escapedValue = String(value)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&apos;');

            return `<${key}>${escapedValue}</${key}>`;
        };

        return `<?xml version="1.0" encoding="UTF-8"?>\n${createElement(rootName, obj)}`;
    };

    // Convert XML string to JS object
    const xmlToObject = (xmlStr) => {
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlStr, 'text/xml');

        // Helper function to convert an XML node to JS object
        const parseNode = (node) => {
            // If node has no children, return its text content
            if (node.childNodes.length === 0 ||
                (node.childNodes.length === 1 && node.childNodes[0].nodeType === 3)) {
                const textContent = node.textContent.trim();

                // Try to convert to number if possible
                if (/^[-+]?[0-9]*\.?[0-9]+([eE][-+]?[0-9]+)?$/.test(textContent)) {
                    return parseFloat(textContent);
                }

                // True/false conversion
                if (textContent.toLowerCase() === 'true') return true;
                if (textContent.toLowerCase() === 'false') return false;

                return textContent;
            }

            // Handle element nodes
            const result = {};
            const childElements = Array.from(node.children);

            // Check if this is an array by looking for repeated element names
            const elementNames = childElements.map(el => el.tagName);
            const isArray = elementNames.some((name, i) => elementNames.indexOf(name) !== i);

            if (isArray) {
                // Group elements by tag name
                const grouped = {};
                childElements.forEach(child => {
                    const tagName = child.tagName;
                    if (!grouped[tagName]) grouped[tagName] = [];
                    grouped[tagName].push(parseNode(child));
                });

                // Return arrays for each group
                for (const key in grouped) {
                    if (Object.prototype.hasOwnProperty.call(grouped, key)) {
                        result[key] = grouped[key];
                    }
                }
            } else {
                // Regular object with unique keys
                childElements.forEach(child => {
                    result[child.tagName] = parseNode(child);
                });
            }

            return result;
        };

        // Check for parsing errors
        const parseError = xmlDoc.querySelector('parsererror');
        if (parseError) {
            throw new Error('XML parsing error: ' + parseError.textContent);
        }

        // Start parsing from root element
        return parseNode(xmlDoc.documentElement);
    };

    const downloadData = () => {
        let content, fileName, contentType;

        if (format.toLowerCase() === 'xml') {
            content = objectToXML(designData);
            fileName = `${designData.name || 'magellan_design'}.xml`;
            contentType = 'application/xml';
        } else {
            // Default to JSON
            content = JSON.stringify(designData, null, 2);
            fileName = `${designData.name || 'magellan_design'}.json`;
            contentType = 'application/json';
        }

        const blob = new Blob([content], {type: contentType});
        const url = URL.createObjectURL(blob);

        const link = document.createElement('a');
        link.href = url;
        link.download = fileName;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    };

    const handleFileChange = (event) => {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            try {
                let importedData;

                if (file.name.endsWith('.xml')) {
                    importedData = xmlToObject(e.target.result);
                } else {
                    // Assume JSON for all other files
                    importedData = JSON.parse(e.target.result);
                }

                onImport(importedData);
            } catch (error) {
                console.error('Error parsing imported file:', error);
                alert(`Failed to import file: ${error.message}`);
            }
        };

        reader.readAsText(file);
        // Clear the input so the same file can be selected again
        event.target.value = '';
    };

    const triggerFileInput = () => {
        if (fileInputRef.current) {
            fileInputRef.current.click();
        }
    };

    return (
        <div className="card mb-4">
            <h3 className="mb-3">Design Import/Export</h3>
            <div className="row g-3 align-items-center">
                <div className="col-md-3">
                    <div className="input-group">
                        <label className="input-group-text" htmlFor="formatSelect">Format</label>
                        <select
                            className="form-select"
                            id="formatSelect"
                            value={format}
                            onChange={(e) => onFormatChange(e.target.value)}
                        >
                            <option value="json">JSON</option>
                            <option value="xml">XML</option>
                        </select>
                    </div>
                </div>
                <div className="col-md-9 d-flex gap-2">
                    <button
                        className="btn btn-primary"
                        onClick={downloadData}
                        title={`Export design as ${format.toUpperCase()}`}
                    >
                        <Download size={16} className="me-2"/> Export {format.toUpperCase()}
                    </button>

                    <button
                        className="btn btn-secondary"
                        onClick={triggerFileInput}
                        title="Import design from file"
                    >
                        <Upload size={16} className="me-2"/> Import Design
                    </button>
                    <input
                        type="file"
                        ref={fileInputRef}
                        style={{display: 'none'}}
                        onChange={handleFileChange}
                        accept=".json,.xml"
                    />
                </div>
            </div>
            <div className="mt-2 text-muted small">
                <p>Import/Export your design to share or save for later use. Supports both JSON and XML formats.</p>
            </div>
        </div>
    );
};

export default ImportExportManager;