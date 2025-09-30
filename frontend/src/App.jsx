import React, {useState} from 'react';
import {Play} from 'lucide-react';
import DomainsManager from './components/DomainsManager';
import StrandsManager from './components/StrandsManager';
import ComplexesManager from './components/ComplexesManager';
import ConstraintsManager from './components/ConstraintsManager';
import OffTargetsManager from './components/OffTargetsManager';
import JobsViewer from './components/JobsViewer';
import './App.css';

const API_URL = 'http://localhost:8000';

export default function App() {
    const [activeTab, setActiveTab] = useState('design');
    const [domains, setDomains] = useState([]);
    const [strands, setStrands] = useState([]);
    const [complexes, setComplexes] = useState([]);
    const [hardConstraints, setHardConstraints] = useState([]);
    const [softConstraints, setSoftConstraints] = useState([]);
    const [offTargets, setOffTargets] = useState({max_size: 3, excludes: []});
    const [jobs, setJobs] = useState([]);
    const [jobName, setJobName] = useState('');
    const [baseConc, setBaseConc] = useState('1e-7');
    const [trials, setTrials] = useState(3);
    const [fStop, setFStop] = useState(0.01);
    const [seed, setSeed] = useState(93);

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
        // Load all inputs from the job
        setDomains(job.input_data.domains || []);
        setStrands(job.input_data.strands || []);
        setComplexes(job.input_data.complexes || []);
        setHardConstraints(job.input_data.hard_constraints || []);
        setSoftConstraints(job.input_data.soft_constraints || []);
        setOffTargets(job.input_data.off_targets || {
            max_size: 3,
            excludes: []
        });
        setBaseConc(job.input_data.base_concentration?.toString() || '1e-7');
        setTrials(job.input_data.trials || 3);
        setFStop(job.input_data.f_stop || 0.01);
        setSeed(job.input_data.seed || 93);
        setJobName(job.name + '_clone');

        // Switch to design tab
        setActiveTab('design');
        alert('Job inputs loaded! You can now modify and re-run.');
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

        const jobData = {
            name: jobName,
            domains: domains,
            strands: strands,
            complexes: complexes,
            base_concentration: parseFloat(baseConc),
            hard_constraints: hardConstraints,
            soft_constraints: softConstraints,
            off_targets: offTargets,
            trials: parseInt(trials),
            f_stop: parseFloat(fStop),
            seed: parseInt(seed)
        };

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

    return (
        <div className="container-fluid py-4">
            <h1 className="mb-4">DNA Circuit Design Tool</h1>

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
                        <h3 className="mb-3">6. Run Design</h3>
                        <div className="row g-2 mb-3">
                            <div className="col-md-3">
                                <label className="form-label small">Job
                                    Name</label>
                                <input
                                    type="text"
                                    className="form-control form-control-sm"
                                    value={jobName}
                                    onChange={(e) => setJobName(e.target.value)}
                                    placeholder="My design job"
                                />
                            </div>
                            <div className="col-md-2">
                                <label className="form-label small">Base
                                    Conc</label>
                                <input
                                    type="text"
                                    className="form-control form-control-sm"
                                    value={baseConc}
                                    onChange={(e) => setBaseConc(e.target.value)}
                                />
                            </div>
                            <div className="col-md-2">
                                <label
                                    className="form-label small">Trials</label>
                                <input
                                    type="number"
                                    className="form-control form-control-sm"
                                    value={trials}
                                    onChange={(e) => setTrials(e.target.value)}
                                />
                            </div>
                            <div className="col-md-2">
                                <label className="form-label small">F
                                    Stop</label>
                                <input
                                    type="number"
                                    step="0.001"
                                    className="form-control form-control-sm"
                                    value={fStop}
                                    onChange={(e) => setFStop(e.target.value)}
                                />
                            </div>
                            <div className="col-md-2">
                                <label className="form-label small">Seed</label>
                                <input
                                    type="number"
                                    className="form-control form-control-sm"
                                    value={seed}
                                    onChange={(e) => setSeed(e.target.value)}
                                />
                            </div>
                            <div className="col-md-1 d-flex align-items-end">
                                <button className="btn btn-success w-100"
                                        onClick={runDesignJob}>
                                    <Play size={16}/> Run
                                </button>
                            </div>
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