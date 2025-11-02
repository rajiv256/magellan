import React, {useState, useEffect} from 'react';
import {
    BarChart,
    LineChart,
    Line,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    Legend,
    ResponsiveContainer
} from 'recharts';
import {
    Download,
    Play,
    X,
    Plus,
    Thermometer,
    Droplet,
    Activity,
    Database,
    Upload,
    ChevronDown,
    ChevronUp,
    ZoomIn
} from 'lucide-react';

const API_URL = 'http://localhost:8000';

const getHeatmapColor = (value) => {
    if (value === null || isNaN(value) || value >= 0) {
        return '#f8f9fa';
    }

    // Calculate which color region (0-5) this value falls into
    const region = Math.min(5, Math.floor((-value - 0.001) / 5));

    // Define distinct hues for each 5-unit region
    const hues = [
        240, // Deep blue for -30 to -25
        190, // Blue-cyan for -25 to -20
        130, // Green for -20 to -15
        70,  // Yellow-green for -15 to -10
        40,  // Orange for -10 to -5
        0    // Red for -5 to 0
    ];

    // Get the base hue for this region
    const hue = hues[region];

    // Calculate position within the region (0-1) for smooth transitions
    const positionInRegion = ((-value) % 5) / 5;

    // Small variation within region (10 degrees) for smooth transition
    // while maintaining distinct colors between regions
    const finalHue = hue - (positionInRegion * 10);

    return `hsl(${finalHue}, 100%, 50%)`;
};


const Analysis = () => {
    const [strands, setStrands] = useState([
        {id: 1, name: '', sequence: ''}
    ]);
    const [temperature, setTemperature] = useState(37.0);
    const [naConcentration, setNaConcentration] = useState(50.0); // Default to 50mM monovalent ions
    const [mgConcentration, setMgConcentration] = useState(1.5);  // Default to 1.5mM divalent ions
    const [dntpConcentration, setDntpConcentration] = useState(0.6); // Default to 0.6mM dNTP
    const [dnaConcentration, setDnaConcentration] = useState(50.0); // Default to 50nM DNA
    const [maxLoopSize, setMaxLoopSize] = useState(30); // Default to 30 for max loop size
    const [strandConcentrations, setStrandConcentrations] = useState({});
    const [material, setMaterial] = useState('dna');
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [activeTab, setActiveTab] = useState('pairwise');
    const [error, setError] = useState(null);
    const [showBulkInput, setShowBulkInput] = useState(false);
    const [bulkInputText, setBulkInputText] = useState('');
    const [selectedCell, setSelectedCell] = useState(null);
    const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
    const [analysisCancelled, setAnalysisCancelled] = useState(false);

    // Add a new empty strand
    const addStrand = () => {
        setStrands([
            ...strands,
            {
                id: strands.length + 1,
                name: '',
                sequence: ''
            }
        ]);
    };

    // Remove a strand by id
    const removeStrand = (id) => {
        if (strands.length > 1) {
            setStrands(strands.filter(strand => strand.id !== id));
            // Also remove from concentrations if exists
            const newConcentrations = {...strandConcentrations};
            delete newConcentrations[id];
            setStrandConcentrations(newConcentrations);
        }
    };

    // Update strand name or sequence
    const updateStrand = (id, field, value) => {
        setStrands(strands.map(strand =>
            strand.id === id ? {...strand, [field]: value} : strand
        ));
    };

    // Update strand concentration
    const updateStrandConcentration = (id, value) => {
        setStrandConcentrations({
            ...strandConcentrations,
            [id]: value
        });
    };

    // Process bulk strand input
    const processBulkInput = () => {
        try {
            setError(null);

            // Split into lines
            const lines = bulkInputText.trim().split('\n').filter(line => line.trim());
            if (lines.length === 0) {
                setError('No valid strands found in bulk input');
                return;
            }

            const newStrands = [];
            const errors = [];
            let nextId = strands.length + 1;

            // Process each line
            for (let i = 0; i < lines.length; i++) {
                const line = lines[i].trim();

                // Split by whitespace
                const parts = line.split(/\s+/);

                if (parts.length < 2) {
                    errors.push(`Line ${i + 1}: Need at least a name and sequence`);
                    continue;
                }

                const name = parts[0];
                const sequence = parts[1];

                // Validate sequence format
                const validRegex = material === 'dna'
                    ? /^[ATGCatgc]+$/
                    : /^[AUGCaugc]+$/;

                if (!validRegex.test(sequence)) {
                    errors.push(`Line ${i + 1}: Invalid ${material.toUpperCase()} sequence for ${name}`);
                    continue;
                }

                // Create new strand
                newStrands.push({
                    id: nextId++,
                    name,
                    sequence: sequence.toUpperCase()
                });
            }

            // Check if there are any valid strands
            if (newStrands.length === 0) {
                setError('No valid strands found. Please check your input format.');
                return;
            }

            // If there were some errors, show them but continue with valid strands
            if (errors.length > 0) {
                setError(`Processed with warnings:\n${errors.join('\n')}`);
            }

            // Set the new strands, replacing existing ones
            setStrands(newStrands);

            // Set default concentrations for all new strands
            const newConcentrations = {};
            newStrands.forEach(strand => {
                newConcentrations[strand.id] = "1e-7";
            });
            setStrandConcentrations(newConcentrations);

            // Hide bulk input
            setShowBulkInput(false);
            setBulkInputText('');

        } catch (e) {
            setError(`Error processing bulk input: ${e.message}`);
        }
    };

    // Run the analysis
    const runAnalysis = async () => {
        // Validate inputs
        if (!validateInputs()) {
            return;
        }

        setLoading(true);
        setError(null);
        setAnalysisCancelled(false);
        const startTime = Date.now();  // Add this line
        try {
            // Prepare strand data for the API
            const strandData = strands.map(s => ({
                name: s.name.trim() || `strand${s.id}`,
                sequence: s.sequence.toUpperCase().trim()
            }));

            // Calculate number of comparisons (for progress tracking)
            const totalComparisons = strandData.length * strandData.length;

            // Create the pairwise matrix data structure
            const pairwiseMatrix = [];
            const strandNames = strandData.map(s => s.name);

            // For each pair of strands
            for (let i = 0; i < strandData.length; i++) {
                // Check if analysis was cancelled
                if (analysisCancelled) {
                    throw new Error("Analysis cancelled");
                }

                const row = [];

                for (let j = 0; j < strandData.length; j++) {
                    // Check if analysis was cancelled
                    if (analysisCancelled) {
                        throw new Error("Analysis cancelled");
                    }

                    try {
                        // Use homodimer calculation for diagonal entries
                        const isSelf = i === j;
                        const endpoint = isSelf ? 'homodimer' : 'heterodimer';

                        // Call the backend API to calculate thermodynamics
                        const response = await fetch(`${API_URL}/analyze/${endpoint}`, {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify({
                                seq1: strandData[i].sequence,
                                seq2: strandData[j].sequence,
                                mv_conc: naConcentration,
                                dv_conc: mgConcentration,
                                dntp_conc: dntpConcentration,
                                dna_conc: dnaConcentration,
                                temp_c: temperature,
                                max_loop: maxLoopSize,
                                output_structure: true,
                                material: material
                            })
                        });

                        if (!response.ok) {
                            throw new Error(`API request failed: ${response.status}`);
                        }

                        // Parse the ThermoResult object
                        const thermoResult = await response.json();

                        // Add to matrix
                        row.push({
                            strand1: strandData[i].name,
                            strand2: strandData[j].name,
                            interaction_type: isSelf ? 'homodimer' : 'heterodimer',
                            tm: thermoResult.tm,
                            dg: thermoResult.dg,
                            dh: thermoResult.dh,
                            ds: thermoResult.ds,
                            structure_found: thermoResult.structure_found,
                            ascii_structure: thermoResult.ascii_structure_lines
                        });

                    } catch (error) {
                        console.error(`Error analyzing ${strandData[i].name} + ${strandData[j].name}:`, error);

                        // Add placeholder for failed calculation
                        row.push({
                            strand1: strandData[i].name,
                            strand2: strandData[j].name,
                            interaction_type: i === j ? 'homodimer' : 'heterodimer',
                            tm: 0,
                            dg: 0,
                            dh: 0,
                            ds: 0,
                            structure_found: false,
                            ascii_structure: null,
                            error: error.message
                        });
                    }
                }

                pairwiseMatrix.push(row);
            }

            // Set the results object
            setResults({
                pairwise: {
                    matrix: pairwiseMatrix,
                    strandNames: strandNames,
                    parameters: {
                        temperature: temperature,
                        na_concentration: naConcentration,
                        mg_concentration: mgConcentration,
                        dntp_concentration: dntpConcentration,
                        dna_concentration: dnaConcentration,
                        max_loop: maxLoopSize,
                        material: material
                    }
                },
                execution_time: Date.now() - startTime
            });

            setActiveTab('pairwise');  // Set to pairwise comparison tab by default
            setSelectedCell(null);     // Reset selected cell when running new analysis
        } catch (error) {
            if (error.message !== "Analysis cancelled") {
                console.error('Analysis error:', error);
                setError(error.message || 'An error occurred during analysis');
            }
        } finally {
            setLoading(false);
            setAnalysisCancelled(false);
        }
    };

    // Cancel ongoing analysis
    const cancelAnalysis = () => {
        setAnalysisCancelled(true);
    };

    // Validate user inputs
    const validateInputs = () => {
        // Check if any strand is empty
        if (strands.some(s => !s.sequence.trim())) {
            setError('All strands must have sequences');
            return false;
        }

        // Check for valid DNA/RNA sequences
        const validRegex = material === 'dna'
            ? /^[ATGCatgc]+$/
            : /^[AUGCaugc]+$/;

        for (const strand of strands) {
            if (!validRegex.test(strand.sequence)) {
                setError(`Invalid ${material.toUpperCase()} sequence for ${strand.name || `strand${strand.id}`}. Only valid nucleotides are allowed.`);
                return false;
            }

            // Check sequence length (Primer3 requirement for heterodimer calculations)
            if (strand.sequence.length > 60 && strands.length > 1) {
                setError(`Warning: Sequence "${strand.name || `strand${strand.id}`}" is longer than 60bp. Primer3 requires at least one sequence to be <60 bp for reliable two-state NN model results.`);
                // Don't return false, just a warning
            }
        }

        // Check temperature is within reasonable range
        if (temperature < 0 || temperature > 100) {
            setError('Temperature must be between 0 and 100°C');
            return false;
        }

        // Check concentrations are positive
        if (naConcentration < 0 || mgConcentration < 0 || dntpConcentration < 0 || dnaConcentration < 0) {
            setError('All concentration values must be non-negative');
            return false;
        }

        return true;
    };

    // Handle clicking on a matrix cell to show structure details
    const handleCellClick = (rowIdx, cellIdx) => {
        if (results && results.pairwise && results.pairwise.matrix) {
            setSelectedCell({
                rowIdx,
                cellIdx,
                data: results.pairwise.matrix[rowIdx][cellIdx]
            });
        }
    };

    // Export results to a JSON file
    const exportResults = () => {
        if (!results) return;

        const blob = new Blob([JSON.stringify(results, null, 2)], {type: 'application/json'});
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'primer3_analysis_results.json';
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    };

    // Format dG value for display
    const formatDeltaG = (dg) => {
        // Convert from cal/mol to kcal/mol for display
        const dgKcal = dg / 1000;
        return dgKcal.toFixed(1);
    };

    return (
        <div className="container-fluid py-4">
            <h2 className="mb-4">Primer3 DNA/RNA Analysis</h2>

            <div className="card mb-4">
                <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center mb-3">
                        <h3 className="card-title mb-0">Strand Input</h3>
                        <button
                            className="btn btn-outline-primary"
                            onClick={() => setShowBulkInput(!showBulkInput)}
                        >
                            <Upload size={16} className="me-2"/>
                            {showBulkInput ? 'Individual Entry' : 'Bulk Import'}
                        </button>
                    </div>

                    {!showBulkInput ? (
                        // Individual strand entry
                        <div className="mb-3">
                            {strands.map((strand) => (
                                <div key={strand.id} className="row mb-2 align-items-center">
                                    <div className="col-md-3">
                                        <input
                                            type="text"
                                            className="form-control"
                                            placeholder="Strand Name"
                                            value={strand.name}
                                            onChange={(e) => updateStrand(strand.id, 'name', e.target.value)}
                                        />
                                    </div>
                                    <div className="col-md-7">
                                        <input
                                            type="text"
                                            className="form-control font-monospace"
                                            placeholder="Sequence (e.g., ATGCATGC)"
                                            value={strand.sequence}
                                            onChange={(e) => updateStrand(strand.id, 'sequence', e.target.value)}
                                        />
                                    </div>
                                    <div className="col-md-1">
                                        <input
                                            type="text"
                                            className="form-control"
                                            placeholder="Conc."
                                            value={strandConcentrations[strand.id] || "1e-7"}
                                            onChange={(e) => updateStrandConcentration(strand.id, e.target.value)}
                                        />
                                    </div>
                                    <div className="col-md-1">
                                        <button
                                            className="btn btn-outline-danger"
                                            onClick={() => removeStrand(strand.id)}
                                            disabled={strands.length <= 1}
                                        >
                                            <X size={16}/>
                                        </button>
                                    </div>
                                </div>
                            ))}

                            <div className="mt-3">
                                <button className="btn btn-outline-primary" onClick={addStrand}>
                                    <Plus size={16} className="me-1"/> Add Strand
                                </button>
                            </div>
                        </div>
                    ) : (
                        // Bulk strand import
                        <div className="mb-3">
                            <div className="mb-3">
                                <label className="form-label">
                                    Bulk Strand Import (one strand per line, format: name sequence)
                                </label>
                                <textarea
                                    className="form-control font-monospace"
                                    rows="6"
                                    placeholder="strand1 ATGCATGC
strand2 GCATGCAT
strand3 CGATCGAT"
                                    value={bulkInputText}
                                    onChange={(e) => setBulkInputText(e.target.value)}
                                />
                                <small className="text-muted">
                                    Each line should contain a strand name and sequence separated by space.
                                    All concentrations will be set to 1e-7 M by default and can be edited individually
                                    afterward.
                                </small>
                            </div>
                            <div className="d-flex gap-2">
                                <button className="btn btn-primary" onClick={processBulkInput}>
                                    <Plus size={16} className="me-1"/> Process Bulk Input
                                </button>
                                <button
                                    className="btn btn-outline-secondary"
                                    onClick={() => {
                                        setShowBulkInput(false);
                                        setBulkInputText('');
                                    }}
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    )}
                </div>
            </div>

            <div className="card mb-4">
                <div className="card-body">
                    <div className="d-flex justify-content-between align-items-center mb-3">
                        <h3 className="card-title mb-0">Analysis Parameters</h3>
                        <button
                            className="btn btn-sm btn-outline-secondary"
                            onClick={() => setShowAdvancedSettings(!showAdvancedSettings)}
                        >
                            {showAdvancedSettings ? <ChevronUp size={16} className="me-1"/> :
                                <ChevronDown size={16} className="me-1"/>}
                            {showAdvancedSettings ? 'Hide Advanced Settings' : 'Show Advanced Settings'}
                        </button>
                    </div>

                    <div className="row">
                        <div className="col-md-3 mb-3">
                            <label className="form-label">Material</label>
                            <select
                                className="form-select"
                                value={material}
                                onChange={(e) => setMaterial(e.target.value)}
                            >
                                <option value="dna">DNA</option>
                                <option value="rna">RNA</option>
                            </select>
                        </div>

                        <div className="col-md-3 mb-3">
                            <label className="form-label">Temperature (°C)</label>
                            <div className="input-group">
                                <span className="input-group-text">
                                    <Thermometer size={16}/>
                                </span>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={temperature}
                                    onChange={(e) => setTemperature(parseFloat(e.target.value))}
                                    min="0"
                                    max="100"
                                    step="0.1"
                                />
                            </div>
                        </div>

                        <div className="col-md-3 mb-3">
                            <label className="form-label">[Na+] (mM)</label>
                            <div className="input-group">
                                <span className="input-group-text">
                                    <Droplet size={16}/>
                                </span>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={naConcentration}
                                    onChange={(e) => setNaConcentration(parseFloat(e.target.value))}
                                    min="0"
                                    step="1"
                                />
                            </div>
                        </div>

                        <div className="col-md-3 mb-3">
                            <label className="form-label">[Mg++] (mM)</label>
                            <div className="input-group">
                                <span className="input-group-text">
                                    <Droplet size={16}/>
                                </span>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={mgConcentration}
                                    onChange={(e) => setMgConcentration(parseFloat(e.target.value))}
                                    min="0"
                                    step="0.1"
                                />
                            </div>
                        </div>
                    </div>

                    {showAdvancedSettings && (
                        <div className="row mt-3 bg-light p-3 rounded">
                            <h5>Advanced Primer3 Settings</h5>

                            <div className="col-md-4 mb-3">
                                <label className="form-label">[dNTP] (mM)</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={dntpConcentration}
                                    onChange={(e) => setDntpConcentration(parseFloat(e.target.value))}
                                    min="0"
                                    step="0.1"
                                />
                                <small className="text-muted">dNTP concentration</small>
                            </div>

                            <div className="col-md-4 mb-3">
                                <label className="form-label">[DNA] (nM)</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={dnaConcentration}
                                    onChange={(e) => setDnaConcentration(parseFloat(e.target.value))}
                                    min="0"
                                    step="1"
                                />
                                <small className="text-muted">DNA concentration</small>
                            </div>

                            <div className="col-md-4 mb-3">
                                <label className="form-label">Max Loop Size</label>
                                <input
                                    type="number"
                                    className="form-control"
                                    value={maxLoopSize}
                                    onChange={(e) => setMaxLoopSize(parseInt(e.target.value))}
                                    min="1"
                                    max="100"
                                    step="1"
                                />
                                <small className="text-muted">Maximum size of loops in structures</small>
                            </div>
                        </div>
                    )}

                    <div className="mt-3">
                        <button
                            className="btn btn-primary"
                            onClick={runAnalysis}
                            disabled={loading}
                        >
                            {loading ? (
                                <>
                                    <span className="spinner-border spinner-border-sm me-2" role="status"
                                          aria-hidden="true"></span>
                                    Analyzing...
                                </>
                            ) : (
                                <>
                                    <Play size={16} className="me-2"/> Run Analysis
                                </>
                            )}
                        </button>

                        {loading && (
                            <button
                                className="btn btn-outline-danger ms-2"
                                onClick={cancelAnalysis}
                            >
                                <X size={16} className="me-2"/> Cancel
                            </button>
                        )}

                        {results && (
                            <button
                                className="btn btn-outline-secondary ms-2"
                                onClick={exportResults}
                            >
                                <Download size={16} className="me-2"/> Export Results
                            </button>
                        )}
                    </div>

                    {error && (
                        <div className="alert alert-danger mt-3" style={{whiteSpace: 'pre-line'}}>
                            {error}
                        </div>
                    )}
                </div>
            </div>

            {results && (
                <div className="card">
                    <div className="card-body">
                        <h3 className="card-title mb-3">Analysis Results</h3>

                        <ul className="nav nav-tabs mb-4">
                            <li className="nav-item">
                                <button
                                    className={`nav-link ${activeTab === 'pairwise' ? 'active' : ''}`}
                                    onClick={() => setActiveTab('pairwise')}
                                >
                                    Strand Interactions
                                </button>
                            </li>
                            {/* Other tabs can be added here for additional analysis types */}
                        </ul>

                        {/* Pairwise Strand Interaction Tab */}
                        {activeTab === 'pairwise' && (
                            <div className="row">
                                <div className="col-md-7">
                                    <h4>Pairwise Interaction ΔG Values (kcal/mol)</h4>
                                    <p className="text-muted">
                                        This matrix shows the Gibbs free energy (ΔG) in kcal/mol for interactions
                                        between each pair of strands.
                                        More negative values (darker blue) indicate stronger binding potential. Click on
                                        any cell to see structure details.
                                    </p>

                                    <div className="mt-4 table-responsive">
                                        <table className="table table-bordered">
                                            <thead>
                                            <tr>
                                                <th></th>
                                                {results.pairwise.strandNames.map((name, idx) => (
                                                    <th key={idx}
                                                        className="text-center">{name || `strand${idx + 1}`}</th>
                                                ))}
                                            </tr>
                                            </thead>
                                            <tbody>
                                            {results.pairwise.matrix.map((row, rowIdx) => (
                                                <tr key={rowIdx}>
                                                    <th>{results.pairwise.strandNames[rowIdx] || `strand${rowIdx + 1}`}</th>
                                                    {row.map((cell, cellIdx) => (
                                                        <td
                                                            key={cellIdx}
                                                            className="text-center"
                                                            style={{
                                                                backgroundColor: getHeatmapColor(cell.dg),
                                                                minWidth: '80px',
                                                                cursor: 'pointer',
                                                                border: selectedCell && selectedCell.rowIdx === rowIdx && selectedCell.cellIdx === cellIdx
                                                                    ? '2px solid black' : undefined
                                                            }}
                                                            title="Click for structure details"
                                                            onClick={() => handleCellClick(rowIdx, cellIdx)}
                                                        >
                                                            {cell.structure_found ? formatDeltaG(cell.dg) : '—'}
                                                        </td>
                                                    ))}
                                                </tr>
                                            ))}
                                            </tbody>
                                        </table>
                                    </div>

                                    <div className="mt-3 d-flex align-items-center">
                                        <span className="me-2">Color scale:</span>
                                        <div style={{
                                            width: '200px',
                                            height: '20px',
                                            background: 'linear-gradient(to right, #f8f9fa, rgb(128, 128, 255), rgb(0, 0, 255))'
                                        }}></div>
                                        <span className="ms-2">Weaker</span>
                                        <span className="mx-2">to</span>
                                        <span>Stronger binding</span>
                                    </div>
                                </div>

                                <div className="col-md-5">
                                    {selectedCell ? (
                                        <div className="card">
                                            <div
                                                className="card-header d-flex justify-content-between align-items-center">
                                                <h5 className="mb-0">
                                                    {selectedCell.data.interaction_type === 'homodimer' ? 'Self-Interaction' : 'Strand Interaction'} Details
                                                </h5>
                                                <button
                                                    className="btn btn-sm btn-outline-secondary"
                                                    onClick={() => setSelectedCell(null)}
                                                >
                                                    <X size={14}/>
                                                </button>
                                            </div>
                                            <div className="card-body">
                                                <table className="table table-sm">
                                                    <tbody>
                                                    <tr>
                                                        <th>Interaction</th>
                                                        <td>
                                                            {selectedCell.data.strand1 || `strand${selectedCell.rowIdx + 1}`} + {selectedCell.data.strand2 || `strand${selectedCell.cellIdx + 1}`}
                                                        </td>
                                                    </tr>
                                                    <tr>
                                                        <th>Type</th>
                                                        <td>{selectedCell.data.interaction_type}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>ΔG (kcal/mol)</th>
                                                        <td>{formatDeltaG(selectedCell.data.dg)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>Tm (°C)</th>
                                                        <td>{selectedCell.data.tm.toFixed(1)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>ΔH (kcal/mol)</th>
                                                        <td>{(selectedCell.data.dh / 1000).toFixed(1)}</td>
                                                    </tr>
                                                    <tr>
                                                        <th>ΔS (cal/K*mol)</th>
                                                        <td>{selectedCell.data.ds.toFixed(1)}</td>
                                                    </tr>
                                                    </tbody>
                                                </table>

                                                {selectedCell.data.structure_found && selectedCell.data.ascii_structure ? (
                                                    <>
                                                        <h6>Predicted Structure</h6>
                                                        <div className="bg-light p-3 rounded font-monospace"
                                                             style={{overflowX: 'auto', whiteSpace: 'pre'}}>
                                                            {selectedCell.data.ascii_structure.map((line, idx) => (
                                                                <div key={idx}>{line}</div>
                                                            ))}
                                                        </div>
                                                    </>
                                                ) : (
                                                    <div className="alert alert-info">
                                                        No significant interaction structure found.
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="card">
                                            <div className="card-body text-center py-5">
                                                <ZoomIn size={48} className="mb-3 text-muted"/>
                                                <h5>Click on any matrix cell</h5>
                                                <p className="text-muted">
                                                    Click on any cell in the interaction matrix to see detailed
                                                    structure information.
                                                </p>
                                            </div>
                                        </div>
                                    )}

                                    <div className="card mt-4">
                                        <div className="card-body">
                                            <h5>Analysis Parameters</h5>
                                            <table className="table table-sm">
                                                <tbody>
                                                <tr>
                                                    <th>Temperature</th>
                                                    <td>{results.pairwise.parameters.temperature}°C</td>
                                                </tr>
                                                <tr>
                                                    <th>[Na+]</th>
                                                    <td>{results.pairwise.parameters.na_concentration} mM</td>
                                                </tr>
                                                <tr>
                                                    <th>[Mg++]</th>
                                                    <td>{results.pairwise.parameters.mg_concentration} mM</td>
                                                </tr>
                                                <tr>
                                                    <th>[dNTP]</th>
                                                    <td>{results.pairwise.parameters.dntp_concentration} mM</td>
                                                </tr>
                                                <tr>
                                                    <th>[DNA]</th>
                                                    <td>{results.pairwise.parameters.dna_concentration} nM</td>
                                                </tr>
                                                <tr>
                                                    <th>Max loop</th>
                                                    <td>{results.pairwise.parameters.max_loop}</td>
                                                </tr>
                                                <tr>
                                                    <th>Material</th>
                                                    <td>{results.pairwise.parameters.material.toUpperCase()}</td>
                                                </tr>
                                                </tbody>
                                            </table>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default Analysis;