import React, {useState} from 'react';
import {Trash2, Plus} from 'lucide-react';

export default function OffTargetsManager({
                                              offTargets,
                                              setOffTargets,
                                              strands
                                          }) {
    const [selectedStrands, setSelectedStrands] = useState([]);

    const addExclude = () => {
        if (selectedStrands.length === 0) {
            alert('Please select at least one strand to exclude');
            return;
        }
        setOffTargets({
            ...offTargets,
            excludes: [...offTargets.excludes, [...selectedStrands]]
        });
        setSelectedStrands([]);
    };

    const removeExclude = (index) => {
        const newExcludes = offTargets.excludes.filter((_, i) => i !== index);
        setOffTargets({...offTargets, excludes: newExcludes});
    };

    const toggleStrand = (strandName) => {
        if (selectedStrands.includes(strandName)) {
            setSelectedStrands(selectedStrands.filter(s => s !== strandName));
        } else {
            setSelectedStrands([...selectedStrands, strandName]);
        }
    };

    return (
        <div className="card mb-4">
            <h3 className="mb-3">5. Off-Targets Configuration</h3>

            <div className="mb-3">
                <label className="form-label small">Max Size</label>
                <input
                    type="number"
                    className="form-control form-control-sm"
                    style={{width: '150px'}}
                    value={offTargets.max_size}
                    onChange={(e) => setOffTargets({
                        ...offTargets,
                        max_size: parseInt(e.target.value) || 3
                    })}
                    min="1"
                />
                <small className="text-muted">Maximum number of strands in
                    off-target complexes</small>
            </div>

            <div className="mb-3">
                <label className="form-label small fw-bold">Excludes (select
                    strands to exclude as off-targets)</label>

                <div className="border rounded p-2 mb-2"
                     style={{maxHeight: '150px', overflowY: 'auto'}}>
                    {strands.length === 0 ? (
                        <small className="text-muted">No strands available. Add
                            strands first.</small>
                    ) : (
                        <div className="d-flex flex-wrap gap-2">
                            {strands.map((strand) => (
                                <div key={strand.name} className="form-check">
                                    <input
                                        className="form-check-input"
                                        type="checkbox"
                                        id={`strand-${strand.name}`}
                                        checked={selectedStrands.includes(strand.name)}
                                        onChange={() => toggleStrand(strand.name)}
                                    />
                                    <label className="form-check-label small"
                                           htmlFor={`strand-${strand.name}`}>
                                        {strand.name}
                                    </label>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <button
                    className="btn btn-sm btn-primary"
                    onClick={addExclude}
                    disabled={selectedStrands.length === 0}
                >
                    <Plus size={14}/> Add Exclude Group
                </button>
            </div>

            {offTargets.excludes.length > 0 && (
                <div>
                    <label className="form-label small fw-bold">Current
                        Excludes</label>
                    <div className="list-group">
                        {offTargets.excludes.map((exclude, index) => (
                            <div key={index}
                                 className="list-group-item d-flex justify-content-between align-items-center">
                                <span className="small">
                                    <strong>Group {index + 1}:</strong> [{exclude.join(', ')}]
                                </span>
                                <button
                                    className="btn btn-sm btn-danger"
                                    onClick={() => removeExclude(index)}
                                >
                                    <Trash2 size={14}/>
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
}