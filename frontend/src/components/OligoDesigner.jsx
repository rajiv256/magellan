import React, {useState, useCallback} from 'react';
import {Plus, Trash2, Search, ChevronDown, ChevronUp, Play, Zap, X} from 'lucide-react';
import './OligoDesigner.css'

const OligoDesigner = () => {
    const [activeTab, setActiveTab] = useState('domains');
    const [domains, setDomains] = useState([]);
    const [strands, setStrands] = useState([]);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState(null);
    const [optimizedResults, setOptimizedResults] = useState(null);
    const [statusMessage, setStatusMessage] = useState(null);
    const [showStatus, setShowStatus] = useState(false);
    const [newDomain, setNewDomain] = useState({name: '', length: ''});
    const [newStrand, setNewStrand] = useState({name: '', domains: ''});
    const [suggestions, setSuggestions] = useState([]);
    const [showSuggestions, setShowSuggestions] = useState(false);

    // Add domain
    const addDomain = () => {
        if (!newDomain.name || !newDomain.length) return;

        const length = parseInt(newDomain.length);
        if (length < 1 || length > 50) {
            setStatusMessage({type: 'error', message: 'Domain length must be between 1 and 50 nucleotides'});
            setShowStatus(true);
            return;
        }

        const domain = {
            id: Date.now(),
            name: newDomain.name,
            length: length,
            isComplement: false
        };

        // Add complement domain with asterisk
        const complement = {
            id: Date.now() + 1,
            name: newDomain.name + '*',
            length: length,
            isComplement: true
        };

        setDomains([...domains, domain, complement]);
        setNewDomain({name: '', length: ''});
        setStatusMessage({
            type: 'success',
            message: `Added domain ${newDomain.name} and its complement ${newDomain.name}*`
        });
        setShowStatus(true);
    };

    // Delete domain
    const deleteDomain = (id) => {
        const domain = domains.find(d => d.id === id);
        if (domain) {
            // Remove both domain and its complement
            const nameToRemove = domain.isComplement ? domain.name.slice(0, -1) : domain.name;
            setDomains(domains.filter(d =>
                d.name !== nameToRemove && d.name !== nameToRemove + '*'
            ));
            setStatusMessage({type: 'success', message: `Removed domain ${nameToRemove} and its complement`});
            setShowStatus(true);
        }
    };

    // Handle domain input with autocomplete
    const handleDomainInput = (value) => {
        setNewStrand({...newStrand, domains: value});

        if (value.length > 0) {
            const lastToken = value.split(/[\s,]+/).pop();
            if (lastToken) {
                const filtered = domains
                    .filter(d => d.name.toLowerCase().includes(lastToken.toLowerCase()))
                    .slice(0, 5);
                setSuggestions(filtered);
                setShowSuggestions(filtered.length > 0);
            } else {
                setShowSuggestions(false);
            }
        } else {
            setShowSuggestions(false);
        }
    };

    // Select suggestion
    const selectSuggestion = (domainName) => {
        const tokens = newStrand.domains.split(/[\s,]+/);
        tokens[tokens.length - 1] = domainName;
        setNewStrand({...newStrand, domains: tokens.join(' ')});
        setShowSuggestions(false);
    };

    // Convert domains to sequence
    const convertToSequence = (domainString) => {
        const domainNames = domainString.split(/[\s,]+/).filter(name => name.trim());
        let sequence = '';

        for (const name of domainNames) {
            const domain = domains.find(d => d.name === name.trim());
            if (domain) {
                // Generate placeholder sequence based on length
                sequence += 'N'.repeat(domain.length);
            }
        }

        return sequence;
    };

    // Add strand
    const addStrand = () => {
        if (!newStrand.name || !newStrand.domains) return;

        const sequence = convertToSequence(newStrand.domains);
        if (sequence.length === 0) {
            setStatusMessage({type: 'error', message: 'Invalid domain specification. Check domain names.'});
            setShowStatus(true);
            return;
        }

        const strand = {
            id: Date.now(),
            name: newStrand.name,
            domains: newStrand.domains,
            sequence: sequence
        };

        setStrands([...strands, strand]);
        setNewStrand({name: '', domains: ''});
        setStatusMessage({type: 'success', message: `Added strand ${strand.name}`});
        setShowStatus(true);
    };

    // Delete strand
    const deleteStrand = (id) => {
        setStrands(strands.filter(s => s.id !== id));
    };

    // Generate strand sets
    const generateStrandSets = async () => {
        if (strands.length === 0) {
            setStatusMessage({type: 'error', message: 'No strands to generate'});
            setShowStatus(true);
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('http://localhost:5000/api/generate-strand-sets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strands: strands.map(s => ({
                        name: s.name,
                        domains: s.domains.split(/[\s,]+/).filter(d => d.trim()),
                        sequence: s.sequence
                    })),
                    max_sets: 1000
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setResults(data);
            setStatusMessage({type: 'success', message: `Generated ${data.strand_sets?.length || 0} strand sets`});
            setShowStatus(true);
        } catch (error) {
            setStatusMessage({type: 'error', message: `Generation failed: ${error.message}`});
            setShowStatus(true);
        } finally {
            setLoading(false);
        }
    };

    // Optimize strand sets
    const optimizeStrandSets = async () => {
        if (strands.length === 0) {
            setStatusMessage({type: 'error', message: 'No strands to optimize'});
            setShowStatus(true);
            return;
        }

        setLoading(true);
        try {
            const response = await fetch('http://localhost:5000/api/generate-optimized-strand-sets', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    strands: strands.map(s => ({
                        name: s.name,
                        domains: s.domains.split(/[\s,]+/).filter(d => d.trim()),
                        sequence: s.sequence
                    })),
                    max_sets: 1000
                }),
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            setOptimizedResults(data);
            setStatusMessage({type: 'success', message: `Optimized ${data.optimized_sets?.length || 0} strand sets`});
            setShowStatus(true);
        } catch (error) {
            setStatusMessage({type: 'error', message: `Optimization failed: ${error.message}`});
            setShowStatus(true);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="max-w-6xl mx-auto p-6 bg-white">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">OligoDesigner</h1>

            {/* Status Messages */}
            {statusMessage && (
                <div className={`mb-4 p-3 rounded-lg border ${
                    statusMessage.type === 'success' ? 'bg-green-50 border-green-200 text-green-800' :
                        statusMessage.type === 'error' ? 'bg-red-50 border-red-200 text-red-800' :
                            'bg-blue-50 border-blue-200 text-blue-800'
                }`}>
                    <div className="flex justify-between items-center">
                        <span>{statusMessage.message}</span>
                        <button
                            onClick={() => {
                                setShowStatus(!showStatus);
                                if (!showStatus) setStatusMessage(null);
                            }}
                            className="text-gray-500 hover:text-gray-700"
                        >
                            {showStatus ? <ChevronUp size={16}/> : <ChevronDown size={16}/>}
                        </button>
                    </div>
                </div>
            )}

            {/* Tabs */}
            <div className="flex border-b border-gray-200 mb-6">
                <button
                    onClick={() => setActiveTab('domains')}
                    className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                        activeTab === 'domains'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                >
                    Domains
                </button>
                <button
                    onClick={() => setActiveTab('strands')}
                    className={`px-6 py-3 font-medium border-b-2 transition-colors ${
                        activeTab === 'strands'
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700'
                    }`}
                >
                    Strands
                </button>
            </div>

            {/* Domains Tab */}
            {activeTab === 'domains' && (
                <div className="space-y-6">
                    {/* Add Domain Form */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-lg font-semibold mb-4">Add Domain</h3>
                        <div className="flex gap-4 items-end">
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Domain Name
                                </label>
                                <input
                                    type="text"
                                    value={newDomain.name}
                                    onChange={(e) => setNewDomain({...newDomain, name: e.target.value})}
                                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="e.g., a, b, c"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Length (nt)
                                </label>
                                <input
                                    type="number"
                                    value={newDomain.length}
                                    onChange={(e) => setNewDomain({...newDomain, length: e.target.value})}
                                    className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="1-50"
                                    min="1"
                                    max="50"
                                />
                            </div>
                            <button
                                onClick={addDomain}
                                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 flex items-center gap-2"
                            >
                                <Plus size={16}/>
                                Add Domain
                            </button>
                        </div>
                    </div>

                    {/* Domain List */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Domains ({domains.length})</h3>
                        <div className="flex flex-wrap gap-2">
                            {domains.map((domain) => (
                                <div
                                    key={domain.id}
                                    className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm border ${
                                        domain.isComplement
                                            ? 'bg-orange-100 border-orange-300 text-orange-800'
                                            : 'bg-blue-100 border-blue-300 text-blue-800'
                                    }`}
                                >
                                    <span>{domain.name} ({domain.length}nt)</span>
                                    <button
                                        onClick={() => deleteDomain(domain.id)}
                                        className="text-red-500 hover:text-red-700"
                                    >
                                        <X size={14}/>
                                    </button>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Strands Tab */}
            {activeTab === 'strands' && (
                <div className="space-y-6">
                    {/* Add Strand Form */}
                    <div className="bg-gray-50 p-4 rounded-lg">
                        <h3 className="text-lg font-semibold mb-4">Add Strand</h3>
                        <div className="space-y-4">
                            <div className="flex gap-4">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-gray-700 mb-1">
                                        Strand Name
                                    </label>
                                    <input
                                        type="text"
                                        value={newStrand.name}
                                        onChange={(e) => setNewStrand({...newStrand, name: e.target.value})}
                                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                        placeholder="e.g., Input, Output, Helper"
                                    />
                                </div>
                            </div>
                            <div className="relative">
                                <label className="block text-sm font-medium text-gray-700 mb-1">
                                    Domain Sequence (5' to 3')
                                </label>
                                <input
                                    type="text"
                                    value={newStrand.domains}
                                    onChange={(e) => handleDomainInput(e.target.value)}
                                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                                    placeholder="e.g., a b* c"
                                />
                                {showSuggestions && suggestions.length > 0 && (
                                    <div
                                        className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg">
                                        {suggestions.map((domain) => (
                                            <div
                                                key={domain.id}
                                                onClick={() => selectSuggestion(domain.name)}
                                                className="px-3 py-2 hover:bg-gray-100 cursor-pointer"
                                            >
                                                {domain.name} ({domain.length}nt)
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                            <button
                                onClick={addStrand}
                                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center gap-2"
                            >
                                <Plus size={16}/>
                                Add Strand
                            </button>
                        </div>
                    </div>

                    {/* Strand List */}
                    <div>
                        <h3 className="text-lg font-semibold mb-4">Strands ({strands.length})</h3>
                        <div className="space-y-3">
                            {strands.map((strand) => (
                                <div key={strand.id} className="bg-white border border-gray-200 rounded-lg p-4">
                                    <div className="flex justify-between items-start">
                                        <div className="flex-1">
                                            <h4 className="font-medium text-gray-900">{strand.name}</h4>
                                            <p className="text-sm text-gray-600 mt-1">Domains: {strand.domains}</p>
                                            <p className="text-xs text-gray-500 mt-1 font-mono">
                                                Sequence: {strand.sequence} ({strand.sequence.length}nt)
                                            </p>
                                        </div>
                                        <button
                                            onClick={() => deleteStrand(strand.id)}
                                            className="text-red-500 hover:text-red-700"
                                        >
                                            <Trash2 size={16}/>
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Action Buttons */}
                    {strands.length > 0 && (
                        <div className="flex gap-4">
                            <button
                                onClick={generateStrandSets}
                                disabled={loading}
                                className="px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <div
                                            className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                        Generating...
                                    </>
                                ) : (
                                    <>
                                        <Play size={16}/>
                                        Generate Strand Sets
                                    </>
                                )}
                            </button>

                            <button
                                onClick={optimizeStrandSets}
                                disabled={loading}
                                className="px-6 py-3 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2"
                            >
                                {loading ? (
                                    <>
                                        <div
                                            className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                                        Optimizing...
                                    </>
                                ) : (
                                    <>
                                        <Zap size={16}/>
                                        Optimize Strand Sets
                                    </>
                                )}
                            </button>
                        </div>
                    )}

                    {/* Basic Generation Results */}
                    {results && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-semibold text-blue-800">Generation Results</h3>
                                <button
                                    onClick={() => setResults(null)}
                                    className="text-blue-600 hover:text-blue-800"
                                >
                                    <X size={16}/>
                                </button>
                            </div>
                            <p className="text-blue-700 mb-4">
                                Generated {results.strand_sets?.length || 0} strand sets successfully.
                            </p>

                            {/* Show first few sets */}
                            {results.strand_sets && results.strand_sets.slice(0, 3).map((set, index) => (
                                <div key={index} className="bg-white border border-blue-200 rounded-md p-3 mb-3">
                                    <h4 className="font-medium text-gray-900 mb-2">Set #{index + 1}</h4>
                                    <div className="space-y-1">
                                        {Object.entries(set.strands).map(([strandName, sequence]) => (
                                            <div key={strandName} className="text-sm">
                                                <span className="font-medium text-gray-700">{strandName}:</span>
                                                <span className="font-mono text-gray-600 ml-2">{sequence}</span>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            ))}

                            {results.strand_sets && results.strand_sets.length > 3 && (
                                <p className="text-sm text-blue-600">
                                    ... and {results.strand_sets.length - 3} more sets
                                </p>
                            )}
                        </div>
                    )}

                    {/* Optimized Results with Scoring */}
                    {optimizedResults && (
                        <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
                            <div className="flex justify-between items-center mb-4">
                                <h3 className="text-lg font-semibold text-purple-800">Optimization Results (Ranked by
                                    Score)</h3>
                                <button
                                    onClick={() => setOptimizedResults(null)}
                                    className="text-purple-600 hover:text-purple-800"
                                >
                                    <X size={16}/>
                                </button>
                            </div>
                            <p className="text-purple-700 mb-4">
                                Optimized {optimizedResults.total_generated || 0} strand sets, showing
                                top {optimizedResults.returned || 0} ranked by penalty-based scoring.
                            </p>

                            {/* Ranked Sets with Detailed Scoring */}
                            {optimizedResults.optimized_sets && optimizedResults.optimized_sets.map((set, index) => (
                                <div key={index} className="bg-white border border-purple-200 rounded-md p-4 mb-4">
                                    {/* Header with Rank and Score */}
                                    <div className="flex justify-between items-center mb-3">
                                        <div className="flex items-center gap-3">
                                            <span
                                                className="bg-purple-600 text-white px-2 py-1 rounded-full text-sm font-bold">
                                                #{index + 1}
                                            </span>
                                            <span className="text-lg font-semibold text-gray-900">
                                                Score: {set.score?.toFixed(1) || 'N/A'}/100
                                            </span>
                                        </div>
                                        <div className={`px-3 py-1 rounded-full text-sm font-medium ${
                                            set.score >= 90 ? 'bg-green-100 text-green-800' :
                                                set.score >= 70 ? 'bg-yellow-100 text-yellow-800' :
                                                    'bg-red-100 text-red-800'
                                        }`}>
                                            {set.score >= 90 ? 'Excellent' : set.score >= 70 ? 'Good' : 'Needs Improvement'}
                                        </div>
                                    </div>

                                    {/* Penalty Breakdown */}
                                    {set.details && set.details.penalties && set.details.penalties.length > 0 && (
                                        <div className="mb-3">
                                            <h5 className="text-sm font-semibold text-red-700 mb-2">
                                                ⚠️ Penalty Breakdown ({set.details.penalties.length} issues found):
                                            </h5>
                                            <div className="bg-red-50 border border-red-200 rounded-md p-2">
                                                {set.details.penalties.map((penalty, pIndex) => (
                                                    <div key={pIndex} className="text-sm text-red-700 mb-1">
                                                        • {penalty}
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    {/* Perfect Score Indicator */}
                                    {(!set.details?.penalties || set.details.penalties.length === 0) && (
                                        <div className="mb-3">
                                            <div className="bg-green-50 border border-green-200 rounded-md p-2">
                                                <span className="text-sm text-green-700 font-medium">
                                                    ✅ Perfect Score - No penalties detected!
                                                </span>
                                            </div>
                                        </div>
                                    )}

                                    {/* Thermodynamic Details */}
                                    {set.details && (
                                        <div className="mb-3">
                                            <h5 className="text-sm font-semibold text-gray-700 mb-2">Thermodynamic
                                                Analysis:</h5>
                                            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-xs">
                                                {set.details.hairpin_scores && (
                                                    <div className="bg-gray-50 p-2 rounded">
                                                        <div className="font-medium text-gray-700">Hairpin Tm</div>
                                                        <div className="text-gray-600">
                                                            {set.details.hairpin_scores.map(score => score.toFixed(1)).join(', ')}°C
                                                        </div>
                                                    </div>
                                                )}
                                                {set.details.self_dimer_scores && (
                                                    <div className="bg-gray-50 p-2 rounded">
                                                        <div className="font-medium text-gray-700">Self-Dimer Tm</div>
                                                        <div className="text-gray-600">
                                                            {set.details.self_dimer_scores.map(score => score.toFixed(1)).join(', ')}°C
                                                        </div>
                                                    </div>
                                                )}
                                                {set.details.cross_dimer_scores && (
                                                    <div className="bg-gray-50 p-2 rounded">
                                                        <div className="font-medium text-gray-700">Cross-Dimer Tm</div>
                                                        <div className="text-gray-600">
                                                            {set.details.cross_dimer_scores.map(score => score.toFixed(1)).join(', ')}°C
                                                        </div>
                                                    </div>
                                                )}
                                                {set.details.gc_content_scores && (
                                                    <div className="bg-gray-50 p-2 rounded">
                                                        <div className="font-medium text-gray-700">GC Content</div>
                                                        <div className="text-gray-600">
                                                            {set.details.gc_content_scores.map(score => score.toFixed(1)).join(', ')}%
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}

                                    {/* Strand Sequences */}
                                    <div>
                                        <h5 className="text-sm font-semibold text-gray-700 mb-2">Strand Sequences:</h5>
                                        <div className="space-y-2">
                                            {Object.entries(set.strands).map(([strandName, sequence]) => (
                                                <div key={strandName} className="bg-gray-50 p-2 rounded">
                                                    <div className="flex justify-between items-center">
                                                        <span className="font-medium text-gray-700">{strandName}</span>
                                                        <span
                                                            className="text-xs text-gray-500">{sequence.length} nt</span>
                                                    </div>
                                                    <div className="font-mono text-xs text-gray-600 mt-1 break-all">
                                                        {sequence}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Use This Set Button */}
                                    <div className="mt-3 pt-3 border-t border-gray-200">
                                        <button
                                            onClick={() => {
                                                // Update strands with optimized sequences
                                                const updatedStrands = strands.map(strand => {
                                                    if (set.strands[strand.name]) {
                                                        return {...strand, sequence: set.strands[strand.name]};
                                                    }
                                                    return strand;
                                                });
                                                setStrands(updatedStrands);
                                                setStatusMessage({
                                                    type: 'success',
                                                    message: `Applied optimized sequences from Set #${index + 1} (Score: ${set.score?.toFixed(1)})`
                                                });
                                                setShowStatus(true);
                                            }}
                                            className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 text-sm font-medium"
                                        >
                                            Use This Set
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default OligoDesigner;