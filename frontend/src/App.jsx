import React, {useState} from 'react';
import {Play} from 'lucide-react';
import DomainsManager from './components/DomainsManager';
import StrandsManager from './components/StrandsManager';
import ComplexesManager from './components/ComplexesManager';
import ConstraintsManager from './components/ConstraintsManager';
import OffTargetsManager from './components/OffTargetsManager';
import JobsViewer from './components/JobsViewer';
import ImportExportManager from './components/ImportExportManager';
import './App.css';

const API_URL = 'http://localhost:8000';

export default function App() {
    const [activeTab, setActiveTab] = useState('design');
    const [domains, setDomains] = useState([]);
    const [strands, setStrands] = useState([]);
    const [complexes, setComplexes] = useState([]);
    const [hardConstraints, setHardConstraints] = useState([]);
    const [softConstraints, setSoftConstraints] = useState([]);
    const [customConcentrations, setCustomConcentrations] = useState({});
    const [offTargets, setOffTargets] = useState({max_size: 3, excludes: []});
    const [jobs, setJobs] = useState([]);
    const [jobName, setJobName] = useState('');
    const [baseConc, setBaseConc] = useState('1e-7');
    const [trials, setTrials] = useState(3);
    const [fStop, setFStop] = useState(0.01);
    const [seed, setSeed] = useState(93);
    const [exportFormat, setExportFormat] = useState('json');

    const refreshJobs = async () => {
        try {
            const response = await fetch(`${API_URL}/jobs`);
            const data = await response.json();
            setJobs(data);
        } catch (error) {
            console.error('Failed to fetch jobs:', error);
        }
    };

    const cloneJob = (job) => {
        setDomains(job.domains || []);
        setStrands(job.strands || []);
        setComplexes(job.complexes || []);
        setHardConstraints(job.hard_constraints || []);
        setSoftConstraints(job.soft_constraints || []);
        setCustomConcentrations(job.custom_concentrations || {});
        setOffTargets(job.off_targets || {max_size: 3, excludes: []});
        setBaseConc(job.base_concentration?.toString() || '1e-7');
        setTrials(job.trials || 3);
        setFStop(job.f_stop || 0.01);
        setSeed(job.seed || 93);
        setJobName(job.name + '_clone');
        setActiveTab('design');
        alert('Job inputs loaded! You can now modify and re-run.');
    };

    // Get current design data for export/import
    const getCurrentDesignData = () => {
        return {
            name: jobName || 'unnamed_design',
            domains: domains,
            strands: strands,
            complexes: complexes,
            base_concentration: parseFloat(baseConc) || 1e-7,
            custom_concentrations: customConcentrations,
            hard_constraints: hardConstraints,
            soft_constraints: softConstraints,
            off_targets: offTargets,
            trials: parseInt(trials) || 3,
            f_stop: parseFloat(fStop) || 0.01,
            seed: parseInt(seed) || 93
        };
    };

    // Handle importing design data
    const handleImportDesign = (importedData) => {
        try {
            // Set all the form states from the imported data
            setJobName(importedData.name || '');

            // Support different key naming conventions in imports
            setDomains(importedData.domains || []);
            setStrands(importedData.strands || []);
            setComplexes(importedData.complexes || []);

            // Handle different key naming in different formats
            setHardConstraints(importedData.hard_constraints || importedData.hardConstraints || []);
            setSoftConstraints(importedData.soft_constraints || importedData.softConstraints || []);
            setCustomConcentrations(importedData.custom_concentrations || importedData.customConcentrations || {});
            setOffTargets(importedData.off_targets || importedData.offTargets || {max_size: 3, excludes: []});

            // Handle numeric values with parsing and fallbacks
            setBaseConc(((importedData.base_concentration !== undefined) ? importedData.base_concentration :
                (importedData.baseConcentration !== undefined) ? importedData.baseConcentration : 1e-7).toString());
            setTrials(importedData.trials || 3);
            setFStop((importedData.f_stop !== undefined) ? importedData.f_stop :
                (importedData.fStop !== undefined) ? importedData.fStop : 0.01);
            setSeed(importedData.seed || 93);

            alert('Design imported successfully!');
        } catch (error) {
            console.error('Error importing design:', error);
            alert(`Failed to import design: ${error.message}`);
        }
    };

    const runDesignJob = async () => {
        if (!jobName) {
            alert('Please enter a job name');
            return;
        }

        if (complexes.length === 0) {
            alert('Please add at least one complex');
            return;
        }

        const jobData = getCurrentDesignData();

        try {
            const response = await fetch(`${API_URL}/design`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(jobData)
            });

            if (response.ok) {
                alert('Design job submitted!');
                setActiveTab('jobs');
                refreshJobs();
            } else {
                const error = await response.json();
                alert(`Failed to submit job: ${error.detail}`);
            }
        } catch (error) {
            alert(`Error: ${error.message}`);
        }
    };

    // Reset the form to initial state
    const resetDesign = () => {
        if (window.confirm('Are you sure you want to reset all design inputs? This action cannot be undone.')) {
            setDomains([]);
            setStrands([]);
            setComplexes([]);
            setHardConstraints([]);
            setSoftConstraints([]);
            setCustomConcentrations({});
            setOffTargets({max_size: 3, excludes: []});
            setJobName('');
            setBaseConc('1e-7');
            setTrials(3);
            setFStop(0.01);
            setSeed(93);
        }
    };

    return (
        <div className="container-fluid py-4">
            <div className="mb-5 py-5 text-center bg-slate-50">
                <h1 className="display-4 font-weight-bold text-gray-900">
                    Magellan
                </h1>
                <div className="w-24 h-1 bg-blue-600 mx-auto mb-4"></div>
                <p className="lead text-gray-600">A wrapper over NUPACK</p>
            </div>

            <ul className="nav nav-tabs mb-4">
                <li className="nav-item">
                    <button
                        className={`nav-link ${activeTab === 'design' ? 'active' : ''}`}
                        onClick={() => setActiveTab('design')}
                    >
                        Design
                    </button>
                </li>
                <li className="nav-item">
                    <button
                        className={`nav-link ${activeTab === 'jobs' ? 'active' : ''}`}
                        onClick={() => {
                            setActiveTab('jobs');
                            refreshJobs();
                        }}
                    >
                        Jobs
                    </button>
                </li>
            </ul>

            {activeTab === 'design' ? (
                <div className="design-tab">
                    {/* Add the ImportExportManager component near the top */}
                    <ImportExportManager
                        designData={getCurrentDesignData()}
                        onImport={handleImportDesign}
                        format={exportFormat}
                        onFormatChange={setExportFormat}
                    />

                    <div className="row mb-4">
                        <div className="col-12">
                            <div className="card">
                                <h3 className="mb-3">Design Parameters</h3>
                                <div className="row g-3">
                                    <div className="col-md-4">
                                        <label className="form-label">Job Name</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={jobName}
                                            onChange={(e) => setJobName(e.target.value)}
                                            placeholder="My design job"
                                        />
                                    </div>
                                    <div className="col-md-2">
                                        <label className="form-label">Base Concentration</label>
                                        <input
                                            type="text"
                                            className="form-control"
                                            value={baseConc}
                                            onChange={(e) => setBaseConc(e.target.value)}
                                            placeholder="1e-7"
                                        />
                                    </div>
                                    <div className="col-md-2">
                                        <label className="form-label">Trials</label>
                                        <input
                                            type="number"
                                            className="form-control"
                                            value={trials}
                                            onChange={(e) => setTrials(e.target.value)}
                                        />
                                    </div>
                                    <div className="col-md-2">
                                        <label className="form-label">F Stop</label>
                                        <input
                                            type="number"
                                            step="0.001"
                                            className="form-control"
                                            value={fStop}
                                            onChange={(e) => setFStop(e.target.value)}
                                        />
                                    </div>
                                    <div className="col-md-2">
                                        <label className="form-label">Seed</label>
                                        <input
                                            type="number"
                                            className="form-control"
                                            value={seed}
                                            onChange={(e) => setSeed(e.target.value)}
                                        />
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>

                    <DomainsManager domains={domains} setDomains={setDomains}/>
                    <StrandsManager strands={strands} setStrands={setStrands}
                                    domains={domains}/>
                    <ComplexesManager complexes={complexes}
                                      setComplexes={setComplexes}
                                      strands={strands}/>
                    <ConstraintsManager
                        hardConstraints={hardConstraints}
                        setHardConstraints={setHardConstraints}
                        softConstraints={softConstraints}
                        setSoftConstraints={setSoftConstraints}
                        domains={domains}
                        strands={strands}
                    />
                    <OffTargetsManager
                        offTargets={offTargets}
                        setOffTargets={setOffTargets}
                        strands={strands}
                    />
                    <div className="card">
                        <h3 className="mb-3">6. Custom Concentrations
                            (Optional)</h3>
                        <p className="text-muted small">Override base
                            concentration for specific complexes</p>
                        {complexes.length === 0 ? (
                            <p className="text-muted small">Add complexes first
                                to set custom concentrations</p>
                        ) : (
                            complexes.map((complex, idx) => (
                                <div key={idx}
                                     className="row g-2 mb-2 align-items-center">
                                    <div className="col-md-3">
                                        <label
                                            className="form-label small mb-0">{complex.name}</label>
                                    </div>
                                    <div className="col-md-4">
                                        <input
                                            type="text"
                                            className="form-control form-control-sm"
                                            placeholder={`Default: ${baseConc}`}
                                            value={customConcentrations[complex.name] || ''}
                                            onChange={(e) => {
                                                const newConc = {...customConcentrations};
                                                if (e.target.value) {
                                                    newConc[complex.name] = e.target.value;
                                                } else {
                                                    delete newConc[complex.name];
                                                }
                                                setCustomConcentrations(newConc);
                                            }}
                                        />
                                    </div>
                                </div>
                            ))
                        )}
                    </div>

                    <div className="card">
                        <h3 className="mb-3">7. Run Design</h3>
                        <div className="d-flex gap-2">
                            <button
                                className="btn btn-success"
                                onClick={runDesignJob}
                            >
                                <Play size={16} className="me-2"/> Run Design
                            </button>

                            <button
                                className="btn btn-outline-danger"
                                onClick={resetDesign}
                            >
                                Reset All Inputs
                            </button>
                        </div>
                    </div>
                </div>
            ) : (
                <JobsViewer jobs={jobs} refreshJobs={refreshJobs}
                            onCloneJob={cloneJob}/>
            )}
        </div>
    );
}