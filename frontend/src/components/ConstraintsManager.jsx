import React, {useState} from 'react';
import {X, Plus} from 'lucide-react';

export default function ConstraintsManager({
                                               hardConstraints,
                                               setHardConstraints,
                                               softConstraints,
                                               setSoftConstraints,
                                               domains,
                                               strands
                                           }) {
    const [isHard, setIsHard] = useState(true);
    const [constraintType, setConstraintType] = useState('Pattern');
    const [params, setParams] = useState({});

    const hardTypes = ['Match', 'Complementarity', 'Similarity', 'Library', 'Window', 'Pattern', 'Diversity'];
    const softTypes = ['Pattern', 'Similarity', 'SSM', 'EnergyMatch'];

    const constraintSpecs = {
        Pattern: [
            {
                name: 'patterns',
                type: 'text',
                placeholder: 'e.g., A4,C4,G4,U4',
                help: 'Comma-separated patterns'
            },
            {
                name: 'scope',
                type: 'domains',
                placeholder: 'comma sep list of domains',
                help: 'Optional scope domains'
            },
            {
                name: 'weight',
                type: 'number',
                placeholder: 'weight (e.g.,1.0)',
                help: 'Soft only'
            }
        ],
        Diversity: [
            {
                name: 'word',
                type: 'number',
                placeholder: 'Word length e.g., 4',
                help: 'Word length'
            },
            {
                name: 'types',
                type: 'number',
                placeholder: 'Nucleotide types e.g., 2',
                help: 'Number of types'
            },
            {
                name: 'scope',
                type: 'domains',
                placeholder: 'comma sep list of domains',
                help: 'Optional scope'
            }
        ],
        Match: [
            {
                name: 'domains1',
                type: 'domains',
                placeholder: 'First domain list',
                help: 'Domains to match'
            },
            {
                name: 'domains2',
                type: 'domains',
                placeholder: 'Second domain list',
                help: 'Domains to match'
            }
        ],
        Complementarity: [
            {
                name: 'domains1',
                type: 'domains',
                placeholder: 'First domain list'
            },
            {
                name: 'domains2',
                type: 'domains',
                placeholder: 'Second domain list'
            },
            {
                name: 'wobble_mutations',
                type: 'checkbox',
                help: 'Allow wobble mutations'
            }
        ],
        Similarity: [
            {name: 'domains', type: 'domains', placeholder: 'comma sep domain list'},
            {
                name: 'source',
                type: 'text',
                placeholder: 'Source pattern (e.g., S5)',
                help: 'Source pattern'
            },
            {
                name: 'limits',
                type: 'text',
                placeholder: 'Min,Max limits (e.g., 0.2,0.8)',
                help: 'Min,Max limits'
            },
            {
                name: 'weight',
                type: 'number',
                placeholder: 'Weight; Soft only (e.g., 1.0)',
                help: 'Soft only'
            }
        ],
        SSM: [
            {name: 'word', type: 'number', placeholder: 'e.g., 4'},
            {
                name: 'scope',
                type: 'domains',
                placeholder: '(Optional) Comma separated list of Domain names',
                help: 'Optional'
            },
            {name: 'weight', type: 'number', placeholder: 'Weight; Soft' +
                    ' (e.g., 0.3)'}
        ],
        EnergyMatch: [
            {name: 'domains', type: 'domains', placeholder: 'comma sep domain list'},
            {
                name: 'energy_ref',
                type: 'number',
                placeholder: 'energy_reference',
                help: 'Optional reference'
            },
            {
                name: 'weight',
                type: 'number',
                placeholder: 'Soft only (e.g., 1.0)',
                help: 'Soft only'
            }
        ],
        Library: [
            {name: 'domains', type: 'domains', placeholder: 'comma sep domain list'},
            {
                name: 'catalog',
                type: 'text',
                placeholder: 'CTAC,TAAT',
                help: 'Sequence catalog'
            }
        ],
        Window: [
            {
                name: 'domains',
                type: 'domains',
                placeholder: 'Domain list with ~'
            },
            {name: 'sources', type: 'strands', placeholder: 'Source strands'}
        ]
    };

    const addConstraint = () => {
        const constraint = {
            type: constraintType,
            is_hard: isHard,
            params: {...params},
            id: Date.now().toString()
        };

        if (isHard) {
            setHardConstraints([...hardConstraints, constraint]);
        } else {
            setSoftConstraints([...softConstraints, constraint]);
        }

        setParams({});
    };

    const removeConstraint = (id, hard) => {
        if (hard) {
            setHardConstraints(hardConstraints.filter(c => c.id !== id));
        } else {
            setSoftConstraints(softConstraints.filter(c => c.id !== id));
        }
    };

    const currentSpecs = constraintSpecs[constraintType] || [];
    const availableTypes = isHard ? hardTypes : softTypes;

    return (
        <div className="card">
            <h3 className="mb-3">4. Constraints</h3>

            <div className="row g-2 mb-3">
                <div className="col-md-2">
                    <div className="btn-group w-100" role="group">
                        <button
                            className={`btn btn-sm ${isHard ? 'btn-primary' : 'btn-outline-primary'}`}
                            onClick={() => setIsHard(true)}
                        >
                            Hard
                        </button>
                        <button
                            className={`btn btn-sm ${!isHard ? 'btn-primary' : 'btn-outline-primary'}`}
                            onClick={() => setIsHard(false)}
                        >
                            Soft
                        </button>
                    </div>
                </div>
                <div className="col-md-2">
                    <select
                        className="form-select form-select-sm"
                        value={constraintType}
                        onChange={(e) => {
                            setConstraintType(e.target.value);
                            setParams({});
                        }}
                    >
                        {availableTypes.map(t => (
                            <option key={t} value={t}>{t}</option>
                        ))}
                    </select>
                </div>
                {currentSpecs.map(spec => (
                    <div key={spec.name} className="col-md-2">
                        {spec.type === 'checkbox' ? (
                            <div className="form-check mt-1">
                                <input
                                    type="checkbox"
                                    className="form-check-input"
                                    checked={params[spec.name] || false}
                                    onChange={(e) => setParams({
                                        ...params,
                                        [spec.name]: e.target.checked
                                    })}
                                />
                                <label
                                    className="form-check-label small">{spec.help}</label>
                            </div>
                        ) : (
                            <input
                                type={spec.type === 'number' ? 'number' : 'text'}
                                className="form-control form-control-sm"
                                placeholder={spec.placeholder}
                                title={spec.help}
                                value={params[spec.name] || ''}
                                onChange={(e) => setParams({
                                    ...params,
                                    [spec.name]: e.target.value
                                })}
                            />
                        )}
                    </div>
                ))}
                <div className="col-md-2">
                    <button className="btn btn-primary btn-sm w-100"
                            onClick={addConstraint}>
                        <Plus size={16}/> Add
                    </button>
                </div>
            </div>

            <div className="row">
                <div className="col-md-6">
                    <h6>Hard Constraints</h6>
                    <div className="d-flex flex-wrap gap-2">
                        {hardConstraints.map(c => (
                            <span key={c.id}
                                  className="badge bg-info text-dark">
                {c.type} {JSON.stringify(c.params)}
                                <X
                                    size={14}
                                    className="ms-1"
                                    style={{cursor: 'pointer'}}
                                    onClick={() => removeConstraint(c.id, true)}
                                />
              </span>
                        ))}
                    </div>
                </div>
                <div className="col-md-6">
                    <h6>Soft Constraints</h6>
                    <div className="d-flex flex-wrap gap-2">
                        {softConstraints.map(c => (
                            <span key={c.id}
                                  className="badge bg-warning text-dark">
                {c.type} {JSON.stringify(c.params)}
                                <X
                                    size={14}
                                    className="ms-1"
                                    style={{cursor: 'pointer'}}
                                    onClick={() => removeConstraint(c.id, false)}
                                />
              </span>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}