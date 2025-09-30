import React, {useState} from 'react';
import {X, Plus} from 'lucide-react';

export default function ComplexesManager({complexes, setComplexes, strands}) {
    const [name, setName] = useState('');
    const [strandSeq, setStrandSeq] = useState('');
    const [structure, setStructure] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [error, setError] = useState('');

    const handleStrandInput = (value) => {
        setStrandSeq(value);

        const lastComma = value.lastIndexOf(',');
        const currentInput = lastComma >= 0 ? value.slice(lastComma + 1) : value;

        if (currentInput.trim()) {
            const filtered = strands
                .map(s => s.name)
                .filter(n => n.toLowerCase().includes(currentInput.trim().toLowerCase()));
            setSuggestions(filtered.slice(0, 5));
        } else {
            setSuggestions([]);
        }
    };

    const selectSuggestion = (suggestion) => {
        const lastComma = strandSeq.lastIndexOf(',');
        const newValue = lastComma >= 0
            ? strandSeq.slice(0, lastComma + 1) + suggestion + ','
            : suggestion + ',';
        setStrandSeq(newValue);
        setSuggestions([]);
    };

    const addComplex = () => {
        if (!name || !strandSeq || !structure) {
            setError('All fields are required');
            return;
        }

        if (complexes.some(c => c.name === name)) {
            setError('Complex name already exists');
            return;
        }

        const strandList = strandSeq.split(',').map(s => s.trim()).filter(s => s);
        const invalidStrands = strandList.filter(s => !strands.some(st => st.name === s));

        if (invalidStrands.length > 0) {
            setError(`Invalid strands: ${invalidStrands.join(', ')}`);
            return;
        }

        // const structRegex = /^[DU+()\s]*$/;
        // if (!structRegex.test(structure)) {
        //     setError('Structure must use DU+ notation');
        //     return;
        // }

        setComplexes([...complexes, {
            name,
            strands: strandList.join(','),
            structure,
            id: Date.now().toString()
        }]);
        setName('');
        setStrandSeq('');
        setStructure('');
        setError('');
    };

    const removeComplex = (id) => {
        setComplexes(complexes.filter(c => c.id !== id));
    };

    return (
        <div className="card">
            <h3 className="mb-3">3. Complexes</h3>

            <div className="row g-2 mb-3">
                <div className="col-md-2">
                    <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="Name"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                    />
                </div>
                <div className="col-md-4 position-relative">
                    <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="Strands (e.g., base1,x)"
                        value={strandSeq}
                        onChange={(e) => handleStrandInput(e.target.value)}
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
                <div className="col-md-4">
                    <input
                        type="text"
                        className="form-control form-control-sm"
                        placeholder="Structure: use one of the available notations on Nupack. (e.g., DU+)"
                        value={structure}
                        onChange={(e) => setStructure(e.target.value)}
                    />
                </div>
                <div className="col-md-2">
                    <button className="btn btn-danger btn-sm w-100"
                            onClick={addComplex}>
                        <Plus size={16}/> Add
                    </button>
                </div>
            </div>

            {error &&
                <div className="alert alert-danger py-1 small">{error}</div>}

            <div className="d-flex flex-wrap gap-2">
                {complexes.map(c => (
                    <span key={c.id} className="badge bg-danger">
            {c.name}: [{c.strands}] {c.structure}
                        <X
                            size={14}
                            className="ms-1"
                            style={{cursor: 'pointer'}}
                            onClick={() => removeComplex(c.id)}
                        />
          </span>
                ))}
            </div>
        </div>
    );
}