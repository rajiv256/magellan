import React, {useState, useEffect} from 'react';
import {Play, Settings, AlertCircle, CheckCircle, Database, Plus, Minus, X} from 'lucide-react';
import './OligoDesigner.css';

const OligoDesigner = () => {
    // State management
    const [activeTab, setActiveTab] = useState('domains');
    const [domains, setDomains] = useState([]);
    const [strands, setStrands] = useState([]);
    const [newDomainInput, setNewDomainInput] = useState({name: '', length: 20});
    const [newStrandInput, setNewStrandInput] = useState('');
    const [strandInputFocus, setStrandInputFocus] = useState(false);
    const [autocompleteIndex, setAutocompleteIndex] = useState(-1);
    const [statusMessage, setStatusMessage] = useState(null);
    const [validationResults, setValidationResults] = useState({});
    const [isGenerating, setIsGenerating] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [availableSequences, setAvailableSequences] = useState({});

    // Settings state
    const [settings, setSettings] = useState({
        reactionTemp: 37,
        saltConc: 50,
        mgConc: 2,
        hairpinTm: 32,
        selfDimerTm: 32,
        crossDimerDgMin: -5,
        hybridizationTmMin: 42,
        hybridizationTmMax: 60,
        gcContentMin: 30,
        gcContentMax: 70,
        threePrimeSelfDimerTm: 27,
        threePrimeHairpinTm: 27,
        threePrimeCrossDimerDgMin: -2,
        threePrimeLength: 6,
        redisHost: 'localhost',
        redisPort: 6379,
        cacheTimeout: 3600,
        maxSequencesPerDomain: 10,
        orthogonalityThreshold: 0.8
    });

    // Status message functions
    const showStatus = (message, type = 'info', duration = 5000) => {
        setStatusMessage({message, type, id: Date.now()});
        if (duration > 0) {
            setTimeout(() => setStatusMessage(null), duration);
        }
    };

    const dismissStatus = () => {
        setStatusMessage(null);
    };

    // API functions
    const fetchAvailableSequences = async () => {
        if (domains.length === 0) return;

        try {
            const response = await fetch('/api/sequences/available', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    domains: domains.map(d => ({
                        length: d.length,
                        gcMin: settings.gcContentMin,
                        gcMax: settings.gcContentMax
                    }))
                })
            });

            if (response.ok) {
                const data = await response.json();
                setAvailableSequences(data);
            }
        } catch (error) {
            console.error('Failed to fetch sequences:', error);
            showStatus('Failed to fetch available sequences from cache', 'error');
        }
    };

    // Domain management
    const addDomain = () => {
        if (!newDomainInput.name.trim()) {
            showStatus('Please enter a domain name', 'warning');
            return;
        }

        if (newDomainInput.length < 7 || newDomainInput.length > 25) {
            showStatus('Domain length must be between 7 and 25 nucleotides', 'warning');
            return;
        }

        const existingNames = domains.map(d => d.name.toLowerCase());
        if (existingNames.includes(newDomainInput.name.toLowerCase()) ||
            existingNames.includes(`${newDomainInput.name.toLowerCase()}*`)) {
            showStatus('Domain name already exists! Please choose a different name.', 'error');
            return;
        }

        const newId = domains.length > 0 ? Math.max(...domains.map(d => d.id)) + 1 : 1;

        const forwardDomain = {
            id: newId,
            name: newDomainInput.name,
            length: newDomainInput.length,
            sequence: '',
            role: 'binding',
            isComplement: false
        };

        const complementDomain = {
            id: newId + 1,
            name: `${newDomainInput.name}*`,
            length: newDomainInput.length,
            sequence: '',
            role: 'binding',
            isComplement: true,
            complementOf: newId
        };

        setDomains([...domains, forwardDomain, complementDomain]);
        setNewDomainInput({name: '', length: 20});
        showStatus(`Added domain pair: ${newDomainInput.name} and ${newDomainInput.name}*`, 'success');
    };

    const removeDomain = (id) => {
        const domainToRemove = domains.find(d => d.id === id);
        if (!domainToRemove) return;

        let idsToRemove = [id];
        let removedNames = [domainToRemove.name];

        if (!domainToRemove.isComplement) {
            const complementId = domains.find(d => d.complementOf === id)?.id;
            if (complementId) {
                idsToRemove.push(complementId);
                removedNames.push(`${domainToRemove.name}*`);
            }
        } else {
            const forwardId = domainToRemove.complementOf;
            if (forwardId) {
                const forwardDomain = domains.find(d => d.id === forwardId);
                idsToRemove.push(forwardId);
                removedNames = [forwardDomain?.name, domainToRemove.name];
            }
        }

        setDomains(domains.filter(d => !idsToRemove.includes(d.id)));
        setStrands(strands.map(s => ({
            ...s,
            domainIds: s.domainIds.filter(did => !idsToRemove.includes(did))
        })));

        showStatus(`Removed domain pair: ${removedNames.join(' and ')}`, 'info');
    };

    // Strand management
    const addStrand = () => {
        if (!newStrandInput.trim()) {
            showStatus('Please enter domain names for the strand', 'warning');
            return;
        }

        const domainNames = newStrandInput.trim().split(/\s+/);
        const domainIds = [];
        const missingDomains = [];

        for (const name of domainNames) {
            const domain = domains.find(d => d.name.toLowerCase() === name.toLowerCase());
            if (domain) {
                domainIds.push(domain.id);
            } else {
                missingDomains.push(name);
            }
        }

        if (missingDomains.length > 0) {
            showStatus(`Domain(s) not found: ${missingDomains.join(', ')}. Please add them first.`, 'error');
            return;
        }

        const existingStrandNames = strands.map(s => s.name.toLowerCase());
        let strandName = domainNames.join(' ');
        let counter = 1;
        let uniqueName = strandName;

        while (existingStrandNames.includes(uniqueName.toLowerCase())) {
            uniqueName = `${strandName} (${counter})`;
            counter++;
        }

        const newId = strands.length > 0 ? Math.max(...strands.map(s => s.id)) + 1 : 1;
        const newStrand = {
            id: newId,
            name: uniqueName,
            domainIds: domainIds,
            sequence: '',
            validated: false
        };

        setStrands([...strands, newStrand]);
        setNewStrandInput('');
        showStatus(`Added strand: ${uniqueName}`, 'success');
    };

    const removeStrand = (id) => {
        const strandToRemove = strands.find(s => s.id === id);
        setStrands(strands.filter(s => s.id !== id));
        if (strandToRemove) {
            showStatus(`Removed strand: ${strandToRemove.name}`, 'info');
        }
    };

    const updateStrand = (id, field, value) => {
        setStrands(strands.map(s =>
            s.id === id ? {...s, [field]: value} : s
        ));
    };

    // Autocomplete functionality
    const getAvailableDomainSuggestions = (input) => {
        if (!input) return [];
        const inputWords = input.toLowerCase().split(/\s+/);
        const lastWord = inputWords[inputWords.length - 1];

        if (!lastWord) return [];

        return domains
            .map(d => d.name)
            .filter(name => name.toLowerCase().startsWith(lastWord))
            .slice(0, 5);
    };

    const handleStrandInputKeyDown = (e) => {
        const suggestions = getAvailableDomainSuggestions(newStrandInput);

        if (e.key === 'ArrowDown') {
            e.preventDefault();
            setAutocompleteIndex(prev => Math.min(prev + 1, suggestions.length - 1));
        } else if (e.key === 'ArrowUp') {
            e.preventDefault();
            setAutocompleteIndex(prev => Math.max(prev - 1, -1));
        } else if (e.key === 'Tab' || e.key === 'Enter') {
            if (autocompleteIndex >= 0 && suggestions[autocompleteIndex]) {
                e.preventDefault();
                const words = newStrandInput.split(/\s+/);
                words[words.length - 1] = suggestions[autocompleteIndex];
                setNewStrandInput(words.join(' ') + ' ');
                setAutocompleteIndex(-1);
            } else if (e.key === 'Enter') {
                addStrand();
            }
        } else if (e.key === 'Escape') {
            setAutocompleteIndex(-1);
        }
    };

    // Generation and validation
    const generateAndValidate = async () => {
        if (strands.length === 0) {
            showStatus('Please add at least one strand before generating', 'warning');
            return;
        }

        setIsGenerating(true);
        showStatus('Generating sequences from Redis cache...', 'info', 0);

        try {
            const response = await fetch('/api/design/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    domains,
                    strands,
                    settings
                })
            });

            const data = await response.json();

            if (data.success) {
                setDomains(data.domains);
                setStrands(data.strands);
                setValidationResults(data.validation);

                const totalValidated = data.strands.filter(s => s.validated).length;
                showStatus(`Successfully generated and validated ${totalValidated} strands`, 'success');
            } else {
                showStatus(`Generation failed: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('API call failed:', error);
            showStatus('Failed to connect to the server. Please check your connection.', 'error');
        } finally {
            setIsGenerating(false);
        }
    };

    // Validation display functions
    const getValidationIcon = (strandId) => {
        const result = validationResults.strand_validation?.[strandId];
        if (!result) return <AlertCircle className="icon text-gray-400"/>;

        const allPassed = Object.values(result).every(check => check.passed);
        return allPassed
            ? <CheckCircle className="icon text-green-500"/>
            : <AlertCircle className="icon text-red-500"/>;
    };

    // Status Message Component
    const StatusMessage = () => {
        if (!statusMessage) return null;

        const getStatusIcon = () => {
            switch (statusMessage.type) {
                case 'success':
                    return <CheckCircle className="icon"/>;
                case 'error':
                    return <AlertCircle className="icon"/>;
                case 'warning':
                    return <AlertCircle className="icon"/>;
                default:
                    return <AlertCircle className="icon"/>;
            }
        };

        return (
            <div className={`status-message status-${statusMessage.type}`}>
                <div className="status-content">
                    {getStatusIcon()}
                    <span className="status-text">{statusMessage.message}</span>
                </div>
                <button onClick={dismissStatus} className="status-dismiss">
                    <X className="icon"/>
                </button>
            </div>
        );
    };

    // Validation Detail Component
    const ValidationDetail = ({strandId}) => {
        const result = validationResults.strand_validation?.[strandId];
        if (!result) return null;

        return (
            <div className="validation-detail">
                {Object.entries(result).map(([check, data]) => (
                    <div key={check} className={`validation-item ${data.passed ? 'passed' : 'failed'}`}>
                        <span className="validation-check">
                            {check.replace(/([A-Z])/g, ' $1').toLowerCase()}:
                        </span>
                        <span className="validation-value">
                            {data.passed ? '✓' : '✗'} {data.value}
                        </span>
                    </div>
                ))}
            </div>
        );
    };

    // Tab rendering functions
    const renderDomainsTab = () => (
        <div className="tab-content">
            <div className="domains-section">
                <h2>Domain Management</h2>

                <div className="add-domain">
                    <div className="domain-inputs">
                        <input
                            type="text"
                            placeholder="Domain name (e.g., a, b, c)"
                            value={newDomainInput.name}
                            onChange={(e) => setNewDomainInput({...newDomainInput, name: e.target.value})}
                            onKeyPress={(e) => e.key === 'Enter' && addDomain()}
                            className="domain-name-input"
                        />
                        <input
                            type="number"
                            placeholder="Length"
                            value={newDomainInput.length}
                            onChange={(e) => setNewDomainInput({...newDomainInput, length: Number(e.target.value)})}
                            min="7"
                            max="25"
                            className="domain-length-input"
                        />
                        <button onClick={addDomain} className="btn btn-primary">
                            <Plus className="icon"/>
                            Add Domain Pair
                        </button>
                    </div>
                    <p className="help-text">Creates both forward domain and reverse complement (*)</p>
                    <p className="help-text">Valid lengths: 7-25 nucleotides</p>
                </div>

                {domains.length > 0 ? (
                    <div className="domain-list">
                        <h3>Current Domains ({domains.length})</h3>
                        <div className="domain-tags">
                            {domains.map(domain => (
                                <div key={domain.id}
                                     className={`domain-tag ${domain.isComplement ? 'complement' : 'forward'}`}>
                                    <span className="domain-name">{domain.name}</span>
                                    <span className="domain-length">{domain.length}nt</span>
                                    {domain.sequence && (
                                        <span className="domain-sequence">{domain.sequence}</span>
                                    )}
                                    {!domain.isComplement && (
                                        <button
                                            onClick={() => removeDomain(domain.id)}
                                            className="remove-btn"
                                            title="Remove domain pair"
                                        >
                                            <Minus className="icon"/>
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    </div>
                ) : (
                    <div className="empty-state">
                        <p>No domains added yet</p>
                        <p>Add domains to start designing oligonucleotides</p>
                    </div>
                )}

                {availableSequences && Object.keys(availableSequences).length > 0 && (
                    <div className="cache-status">
                        <Database className="icon"/>
                        <span>
                            Redis Cache: {Object.values(availableSequences.available_sequences || {})
                            .reduce((sum, domain) => sum + (domain.count || 0), 0)} sequences available
                        </span>
                    </div>
                )}
            </div>
        </div>
    );

    const renderStrandsTab = () => (
        <div className="tab-content">
            <div className="strands-section">
                <h2>Strand Design & Generation</h2>

                {domains.length === 0 ? (
                    <div className="warning-box">
                        <AlertCircle className="icon"/>
                        <p>Please add domains in the Domains tab before creating strands</p>
                    </div>
                ) : (
                    <>
                        <div className="add-strand">
                            <div className="strand-input-container">
                                <input
                                    type="text"
                                    placeholder="e.g., a b* c (space-separated)"
                                    value={newStrandInput}
                                    onChange={(e) => {
                                        setNewStrandInput(e.target.value);
                                        setAutocompleteIndex(-1);
                                    }}
                                    onKeyDown={handleStrandInputKeyDown}
                                    onFocus={() => setStrandInputFocus(true)}
                                    onBlur={() => setTimeout(() => setStrandInputFocus(false), 200)}
                                    className="strand-input"
                                />

                                {strandInputFocus && newStrandInput && (
                                    <div className="autocomplete-dropdown">
                                        {getAvailableDomainSuggestions(newStrandInput).map((suggestion, index) => (
                                            <div
                                                key={suggestion}
                                                className={`autocomplete-item ${index === autocompleteIndex ? 'active' : ''}`}
                                                onClick={() => {
                                                    const words = newStrandInput.split(/\s+/);
                                                    words[words.length - 1] = suggestion;
                                                    setNewStrandInput(words.join(' ') + ' ');
                                                    setAutocompleteIndex(-1);
                                                }}
                                            >
                                                {suggestion}
                                            </div>
                                        ))}
                                    </div>
                                )}

                                <button onClick={addStrand} className="btn btn-primary">
                                    <Plus className="icon"/>
                                    Add Strand
                                </button>
                            </div>

                            <div className="available-domains">
                                Available domains: {domains.map(d => d.name).join(', ')}
                            </div>
                        </div>

                        {strands.length > 0 && (
                            <div className="generation-section">
                                <div className="generation-header">
                                    <h3>Strands ({strands.length})</h3>
                                    <button
                                        onClick={generateAndValidate}
                                        disabled={isGenerating || strands.length === 0}
                                        className="btn btn-primary btn-large"
                                    >
                                        <Play className="icon"/>
                                        {isGenerating ? 'Generating from Redis...' : 'Generate & Validate'}
                                    </button>
                                </div>
                            </div>
                        )}

                        {strands.length > 0 ? (
                            <div className="strand-list">
                                {strands.map(strand => (
                                    <div key={strand.id} className="strand-item">
                                        <div className="strand-header">
                                            <input
                                                type="text"
                                                value={strand.name}
                                                onChange={(e) => updateStrand(strand.id, 'name', e.target.value)}
                                                className="strand-name-input"
                                            />
                                            <div className="strand-validation">
                                                {getValidationIcon(strand.id)}
                                            </div>
                                            <button
                                                onClick={() => removeStrand(strand.id)}
                                                className="remove-btn"
                                                title="Remove strand"
                                            >
                                                <Minus className="icon"/>
                                            </button>
                                        </div>

                                        <div className="strand-composition">
                                            {strand.domainIds.map(domainId => {
                                                const domain = domains.find(d => d.id === domainId);
                                                return domain ? (
                                                    <span key={domainId} className="domain-tag-small">
                                                        {domain.name}
                                                    </span>
                                                ) : null;
                                            })}
                                            <span className="strand-length">
                                                ({strand.domainIds.reduce((total, id) => {
                                                const domain = domains.find(d => d.id === id);
                                                return total + (domain ? domain.length : 0);
                                            }, 0)}nt)
                                            </span>
                                        </div>

                                        {strand.sequence && (
                                            <div className="strand-sequence">
                                                {strand.sequence}
                                            </div>
                                        )}

                                        <ValidationDetail strandId={strand.id}/>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <div className="empty-state">
                                <p>No strands added yet</p>
                                <p>Use domain names to create strands (e.g., "a b* c")</p>
                            </div>
                        )}
                    </>
                )}
            </div>
        </div>
    );

    // Effects
    useEffect(() => {
        if (domains.length > 0) {
            fetchAvailableSequences();
        }
    }, [domains, settings.gcContentMin, settings.gcContentMax]);

    // Main render
    return (
        <div className="oligo-designer">
            <header className="header">
                <h1>OligoDesigner</h1>
                <div className="header-controls">
                    <button
                        onClick={() => setShowSettings(!showSettings)}
                        className="btn btn-secondary"
                    >
                        <Settings className="icon"/>
                        Settings
                    </button>
                </div>
            </header>

            <StatusMessage/>

            {showSettings && (
                <div className="settings-panel">
                    <h3>Validation Settings</h3>
                    <div className="settings-grid">
                        <div className="setting-group">
                            <label>Reaction Temp (°C)</label>
                            <input
                                type="number"
                                value={settings.reactionTemp}
                                onChange={(e) => setSettings({...settings, reactionTemp: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>Hairpin Tm Max (°C)</label>
                            <input
                                type="number"
                                value={settings.hairpinTm}
                                onChange={(e) => setSettings({...settings, hairpinTm: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>Self-Dimer Tm Max (°C)</label>
                            <input
                                type="number"
                                value={settings.selfDimerTm}
                                onChange={(e) => setSettings({...settings, selfDimerTm: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>Cross-Dimer ΔG Min (kcal/mol)</label>
                            <input
                                type="number"
                                value={settings.crossDimerDgMin}
                                onChange={(e) => setSettings({...settings, crossDimerDgMin: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>Hybridization Tm Min (°C)</label>
                            <input
                                type="number"
                                value={settings.hybridizationTmMin}
                                onChange={(e) => setSettings({...settings, hybridizationTmMin: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>Hybridization Tm Max (°C)</label>
                            <input
                                type="number"
                                value={settings.hybridizationTmMax}
                                onChange={(e) => setSettings({...settings, hybridizationTmMax: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>GC Content Min (%)</label>
                            <input
                                type="number"
                                value={settings.gcContentMin}
                                onChange={(e) => setSettings({...settings, gcContentMin: Number(e.target.value)})}
                            />
                        </div>

                        <div className="setting-group">
                            <label>GC Content Max (%)</label>
                            <input
                                type="number"
                                value={settings.gcContentMax}
                                onChange={(e) => setSettings({...settings, gcContentMax: Number(e.target.value)})}
                            />
                        </div>
                    </div>

                    <div className="stringent-checks">
                        <h4>3' End Checks (More Stringent)</h4>
                        <div className="settings-grid">
                            <div className="setting-group">
                                <label>3' Self-Dimer Tm Max (°C)</label>
                                <input
                                    type="number"
                                    value={settings.threePrimeSelfDimerTm}
                                    onChange={(e) => setSettings({
                                        ...settings,
                                        threePrimeSelfDimerTm: Number(e.target.value)
                                    })}
                                />
                            </div>
                            <div className="setting-group">
                                <label>3' Hairpin Tm Max (°C)</label>
                                <input
                                    type="number"
                                    value={settings.threePrimeHairpinTm}
                                    onChange={(e) => setSettings({
                                        ...settings,
                                        threePrimeHairpinTm: Number(e.target.value)
                                    })}
                                />
                            </div>
                            <div className="setting-group">
                                <label>3' Cross-Dimer ΔG Min (kcal/mol)</label>
                                <input
                                    type="number"
                                    value={settings.threePrimeCrossDimerDgMin}
                                    onChange={(e) => setSettings({
                                        ...settings,
                                        threePrimeCrossDimerDgMin: Number(e.target.value)
                                    })}
                                />
                            </div>
                            <div className="setting-group">
                                <label>3' Check Length</label>
                                <input
                                    type="number"
                                    value={settings.threePrimeLength}
                                    onChange={(e) => setSettings({
                                        ...settings,
                                        threePrimeLength: Number(e.target.value)
                                    })}
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}

            <div className="tab-navigation">
                <button
                    className={`tab-button ${activeTab === 'domains' ? 'active' : ''}`}
                    onClick={() => setActiveTab('domains')}
                >
                    Domains ({domains.length})
                </button>
                <button
                    className={`tab-button ${activeTab === 'strands' ? 'active' : ''}`}
                    onClick={() => setActiveTab('strands')}
                >
                    Strands ({strands.length})
                </button>
            </div>

            <div className="main-content">
                {activeTab === 'domains' ? renderDomainsTab() : renderStrandsTab()}
            </div>
        </div>
    );
};

export default OligoDesigner;