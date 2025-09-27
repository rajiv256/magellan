import React, {useState, useEffect} from 'react';
import {Play, Settings, AlertCircle, CheckCircle, Database} from 'lucide-react';
import './OligoDesigner.css';

const OligoDesigner = () => {
    const [domains, setDomains] = useState([]);
    const [strands, setStrands] = useState([]);
    const [newDomainInput, setNewDomainInput] = useState({name: '', length: 20});
    const [newStrandInput, setNewStrandInput] = useState('');
    const [strandInputFocus, setStrandInputFocus] = useState(false);
    const [autocompleteIndex, setAutocompleteIndex] = useState(-1);

    const [settings, setSettings] = useState({
        reactionTemp: 37,
        saltConc: 50,
        mgConc: 2,
        hairpinTm: 32,                    // Updated: max 32°C
        selfDimerTm: 32,                  // Updated: max 32°C
        crossDimerDgMin: -5,              // New: min -5 kcal/mol
        hybridizationTmMin: 42,           // New: min 42°C
        hybridizationTmMax: 60,           // New: max 60°C
        gcContentMin: 30,                 // Updated: min 30%
        gcContentMax: 70,                 // Updated: max 70%
        threePrimeSelfDimerTm: 27,        // Updated: max 27°C
        threePrimeHairpinTm: 27,          // Updated: max 27°C
        threePrimeCrossDimerDgMin: -2,    // New: min -2 kcal/mol
        threePrimeLength: 6,
        redisHost: 'localhost',
        redisPort: 6379,
        cacheTimeout: 3600,
        maxSequencesPerDomain: 10,
        orthogonalityThreshold: 0.8
    });

    const [validationResults, setValidationResults] = useState({});
    const [isGenerating, setIsGenerating] = useState(false);
    const [showSettings, setShowSettings] = useState(false);
    const [availableSequences, setAvailableSequences] = useState({});

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
            const data = await response.json();
            setAvailableSequences(data);
        } catch (error) {
            console.error('Failed to fetch sequences:', error);
        }
    };

    useEffect(() => {
        if (domains.length > 0) {
            fetchAvailableSequences();
        }
    }, [domains, settings.gcContentMin, settings.gcContentMax]);

    const addDomain = () => {
        if (!newDomainInput.name.trim()) return;

        const existingNames = domains.map(d => d.name.toLowerCase());
        if (existingNames.includes(newDomainInput.name.toLowerCase()) ||
            existingNames.includes(`${newDomainInput.name.toLowerCase()}*`)) {
            alert('Domain name already exists!');
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
    };

    const removeDomain = (id) => {
        const domainToRemove = domains.find(d => d.id === id);
        if (!domainToRemove) return;

        let idsToRemove = [id];

        if (!domainToRemove.isComplement) {
            const complementId = domains.find(d => d.complementOf === id)?.id;
            if (complementId) idsToRemove.push(complementId);
        } else {
            const forwardId = domainToRemove.complementOf;
            if (forwardId) idsToRemove.push(forwardId);
        }

        setDomains(domains.filter(d => !idsToRemove.includes(d.id)));
        setStrands(strands.map(s => ({
            ...s,
            domainIds: s.domainIds.filter(did => !idsToRemove.includes(did))
        })));
    };

    const addStrand = () => {
        if (!newStrandInput.trim()) return;

        const domainNames = newStrandInput.trim().split(/\s+/);
        const domainIds = [];

        for (const name of domainNames) {
            const domain = domains.find(d => d.name.toLowerCase() === name.toLowerCase());
            if (domain) {
                domainIds.push(domain.id);
            } else {
                alert(`Domain "${name}" not found!`);
                return;
            }
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
    };

    const removeStrand = (id) => {
        setStrands(strands.filter(s => s.id !== id));
    };

    const updateStrand = (id, field, value) => {
        setStrands(strands.map(s =>
            s.id === id ? {...s, [field]: value} : s
        ));
    };

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

    const generateAndValidate = async () => {
        setIsGenerating(true);
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
            } else {
                console.error('Generation failed:', data.error);
            }
        } catch (error) {
            console.error('API call failed:', error);
        } finally {
            setIsGenerating(false);
        }
    };

    const getValidationIcon = (strandId) => {
        const result = validationResults[strandId];
        if (!result) return <AlertCircle className="icon text-gray-400"/>;

        const allPassed = Object.values(result).every(check => check.passed);
        return allPassed
            ? <CheckCircle className="icon text-green-500"/>
            : <AlertCircle className="icon text-red-500"/>;
    };

    const ValidationDetail = ({strandId}) => {
        const result = validationResults[strandId];
        if (!result) return null;

        return (
            <div className="validation-detail">
                {Object.entries(result).map(([check, data]) => (
                    <div key={check} className={`validation-item ${data.passed ? 'passed' : 'failed'}`}>
                        <span className="validation-check">{check.replace(/([A-Z])/g, ' $1').toLowerCase()}:</span>
                        <span className="validation-value">{data.passed ? '✓' : '✗'} {data.value}</span>
                    </div>
                ))}
            </div>
        );
    };

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
                    <button
                        onClick={generateAndValidate}
                        disabled={isGenerating}
                        className="btn btn-primary"
                    >
                        <Play className="icon"/>
                        {isGenerating ? 'Generating...' : 'Generate & Validate'}
                    </button>
                </div>
            </header>

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

            <div className="main-content">
                <section className="domains-section">
                    <h2>Domains</h2>

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
                                min="5"
                                max="100"
                                className="domain-length-input"
                            />
                            <button onClick={addDomain} className="btn btn-primary">
                                Add Domain Pair
                            </button>
                        </div>
                        <p className="help-text">Creates both forward domain and reverse complement (*)</p>
                    </div>

                    {domains.length > 0 ? (
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
                                            ×
                                        </button>
                                    )}
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="empty-state">Add domains to get started</div>
                    )}

                    {availableSequences && Object.keys(availableSequences).length > 0 && (
                        <div className="cache-status">
                            <Database className="icon"/>
                            <span>
                {Object.values(availableSequences).reduce((sum, seqs) => sum + seqs.length, 0)} sequences cached
              </span>
                        </div>
                    )}
                </section>

                <section className="strands-section">
                    <h2>Strands</h2>

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
                                Add Strand
                            </button>
                        </div>

                        <div className="available-domains">
                            Available: {domains.map(d => d.name).join(', ')}
                        </div>
                    </div>

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
                                            ×
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
                        <div className="empty-state">Add strands using domain names</div>
                    )}
                </section>
            </div>
        </div>
    );
};

export default OligoDesigner;