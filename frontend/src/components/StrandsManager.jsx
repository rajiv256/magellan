import React, {useState} from 'react';
import {X, Plus} from 'lucide-react';

export default function StrandsManager({strands, setStrands, domains}) {
    const [name, setName] = useState('');
    const [domainSeq, setDomainSeq] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [error, setError] = useState('');

    const handleDomainInput = (value) => {
        setDomainSeq(value);

        const lastComma = value.lastIndexOf(',');
        const currentInput = lastComma >= 0 ? value.slice(lastComma + 1) : value;

        if (currentInput.trim()) {
            const filtered = domains
                .map(d => d.name)
                .filter(n => n.toLowerCase().includes(currentInput.trim().toLowerCase()));
            setSuggestions(filtered.slice(0, 5));
        } else {
            setSuggestions([]);
        }
    };

    const selectSuggestion = (suggestion) => {
        const lastComma = domainSeq.lastIndexOf(',');
        const newValue = lastComma >= 0
            ? domainSeq.slice(0, lastComma + 1) + suggestion + ','
            : suggestion + ',';
        setDomainSeq(newValue);
        setSuggestions([]);
    };

    const addStrand = () => {
        if (!name || !domainSeq) {
            setError('Name and domain sequence are required');
            return;
        }

        if (strands.some(s => s.name === name)) {
            setError('Strand name already exists');
            return;
        }

        const domainList = domainSeq.split(',').map(d => d.trim()).filter(d => d);
        const invalidDomains = domainList.filter(d => !domains.some(dom => dom.name === d));

        if (invalidDomains.length > 0) {
            setError(`Invalid domains: ${invalidDomains.join(', ')}`);
            return;
        }

        setStrands([...strands, {
            name,
            domains: domainList.join(','),
            id: Date.now().toString()
        }]);
        setName('');
        setDomainSeq('');
        setError('');
    };

    const removeStrand = (id) => {
        setStrands(strands.filter(s => s.id !== id));
    };

    return (
        <div className="card">
            <h3 className="mb-3">2. Strands</h3>

            <div className="row g-2 mb-3">
                <div className="col-md-3">
                    <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="Name (e.g., base1)"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                </div>
                <div className="col-md-7 position-relative">
                    <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="Domains (e.g., dx,~dy,dz)"
                        value={domainSeq}
                        onChange={(e) => handleDomainInput(e.target.value)}
                    />
                    {suggestions.length > 0 && (
                        <div className="autocomplete-suggestions">
                            {suggestions.map((s, i) => (
                                <div
                                    key={i}
                                    className="suggestion-item"
                                    onClick={() => selectSuggestion(s)}
                                >
                                    {s}
                                </div>
                            ))}
                        </div>
                    )}
                </div>
                <div className="col-md-2">
                    <button className="btn btn-success btn-sm w-100"
                            onClick={addStrand}>
                        <Plus size={16}/> Add
                    </button>
                </div>
            </div>

            {error &&
                <div className="alert alert-danger py-1 small">{error}</div>}

            <div className="d-flex flex-wrap gap-2">
                {strands.map(s => (
                    <span key={s.id} className="badge bg-success">
            {s.name}: {s.domains}
                        <X
                            size={14}
                            className="ms-1"
                            style={{cursor: 'pointer'}}
                            onClick={() => removeStrand(s.id)}
                        />
          </span>
                ))}
            </div>
        </div>
    );
}