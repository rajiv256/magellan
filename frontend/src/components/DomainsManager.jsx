import React, {useState} from 'react';
import {X, Plus, Upload} from 'lucide-react';

export default function DomainsManager({domains, setDomains}) {
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [error, setError] = useState('');
    const [bulkInput, setBulkInput] = useState('');
    const [showBulkInput, setShowBulkInput] = useState(false);

    const addDomain = () => {
        if (!name || !code) {
            setError('Name and code are required');
            return;
        }

        const codeRegex = /^([MRWSYKVHDBNATGCU]+|([MRWSYKVHDBNATGCU][0-9]+)+)$/;
        if (!codeRegex.test(code)) {
            setError('Invalid code format. Use pattern like N20, A10, etc.');
            return;
        }

        if (domains.some(d => d.name === name || d.name === `~${name}`)) {
            setError('Domain name already exists');
            return;
        }

        const newDomains = [
            ...domains,
            {name, code, id: Date.now().toString()},
            {name: `~${name}`, code, id: (Date.now() + 1).toString()}
        ];

        setDomains(newDomains);
        setName('');
        setCode('');
        setError('');
    };

    const addBulkDomains = () => {
        const lines = bulkInput.trim().split('\n').filter(line => line.trim());
        const errors = [];
        const newDomains = [...domains];
        const codeRegex = /^([MRWSYKVHDBNATGCU][0-9]+)*$/;

        let idCounter = Date.now();

        for (let i = 0; i < lines.length; i++) {
            const line = lines[i].trim();
            // Support both tab and space separation
            const parts = line.split(/[\t\s]+/).filter(p => p);

            if (parts.length !== 2) {
                errors.push(`Line ${i + 1}: Expected 2 columns (name, code), got ${parts.length}`);
                continue;
            }

            const [domainName, domainCode] = parts;

            if (!codeRegex.test(domainCode)) {
                errors.push(`Line ${i + 1}: Invalid code format for "${domainName}"`);
                continue;
            }

            if (newDomains.some(d => d.name === domainName || d.name === `~${domainName}`)) {
                errors.push(`Line ${i + 1}: Domain "${domainName}" already exists`);
                continue;
            }

            // Add domain and its complement
            newDomains.push({
                name: domainName,
                code: domainCode,
                id: (idCounter++).toString()
            });
            newDomains.push({
                name: `~${domainName}`,
                code: domainCode,
                id: (idCounter++).toString()
            });
        }

        if (errors.length > 0) {
            setError(errors.join('\n'));
            return;
        }

        setDomains(newDomains);
        setBulkInput('');
        setShowBulkInput(false);
        setError('');
    };

    const removeDomain = (domainName) => {
        const baseName = domainName.replace('~', '');
        setDomains(domains.filter(d => d.name !== baseName && d.name !== `~${baseName}`));
    };

    return (
        <div className="card">
            <div
                className="d-flex justify-content-between align-items-center mb-3">
                <h3 className="mb-0">1. Domains</h3>
                <button
                    className="btn btn-outline-primary btn-sm"
                    onClick={() => setShowBulkInput(!showBulkInput)}
                >
                    <Upload
                        size={16}/> {showBulkInput ? 'Single Entry' : 'Bulk Import'}
                </button>
            </div>

            {!showBulkInput ? (
                <div className="row g-2 mb-3">
                    <div className="col-md-4">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            placeholder="Name (e.g., dx)"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                        />
                    </div>
                    <div className="col-md-6">
                        <input
                            type="text"
                            className="form-control form-control-sm"
                            placeholder="Code (e.g., N20). Regex: ^([MRWSYKVHDBNATGCU][0-9]+)*$"
                            value={code}
                            onChange={(e) => setCode(e.target.value)}
                        />
                    </div>
                    <div className="col-md-2">
                        <button className="btn btn-primary btn-sm w-100"
                                onClick={addDomain}>
                            <Plus size={16}/> Add
                        </button>
                    </div>
                </div>
            ) : (
                <div className="mb-3">
                    <label className="form-label small">
                        Bulk Import (TSV format: name&lt;tab&gt;code, one per
                        line)
                    </label>
                    <textarea
                        className="form-control form-control-sm font-monospace"
                        rows="6"
                        placeholder={'dx\tN20\ndy\tN15\ndz\tN10'}
                        value={bulkInput}
                        onChange={(e) => setBulkInput(e.target.value)}
                    />
                    <div className="mt-2">
                        <button className="btn btn-success btn-sm"
                                onClick={addBulkDomains}>
                            <Plus size={16}/> Add All
                        </button>
                        <button
                            className="btn btn-outline-secondary btn-sm ms-2"
                            onClick={() => {
                                setBulkInput('');
                                setShowBulkInput(false);
                                setError('');
                            }}
                        >
                            Cancel
                        </button>
                    </div>
                </div>
            )}

            {error && (
                <div className="alert alert-danger py-1 small"
                     style={{whiteSpace: 'pre-line'}}>
                    {error}
                </div>
            )}

            <div className="d-flex flex-wrap gap-2">
                {domains.map(d => (
                    <span key={d.id} className="badge bg-primary">
            {d.name} ({d.code})
            <X
                size={14}
                className="ms-1"
                style={{cursor: 'pointer'}}
                onClick={() => removeDomain(d.name)}
            />
          </span>
                ))}
            </div>
        </div>
    );
}