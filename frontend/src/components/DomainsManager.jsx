import React, {useState} from 'react';
import {X, Plus} from 'lucide-react';

export default function DomainsManager({domains, setDomains}) {
    const [name, setName] = useState('');
    const [code, setCode] = useState('');
    const [error, setError] = useState('');

    const addDomain = () => {
        if (!name || !code) {
            setError('Name and code are required');
            return;
        }

        const codeRegex = /^([MRWSYKVHDBNATGCU][0-9]+)*$/;
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

    const removeDomain = (domainName) => {
        const baseName = domainName.replace('~', '');
        setDomains(domains.filter(d => d.name !== baseName && d.name !== `~${baseName}`));
    };

    return (
        <div className="card">
            <h3 className="mb-3">1. Domains</h3>

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
                        placeholder="Code (e.g., N20)"
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

            {error &&
                <div className="alert alert-danger py-1 small">{error}</div>}

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