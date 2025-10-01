import React, {useState} from 'react';
import {ChevronDown, ChevronRight} from 'lucide-react';

export default function JobsViewer({jobs, refreshJobs, onCloneJob}) {
    const [expandedJob, setExpandedJob] = useState(null);

    const statusColors = {
        Pending: 'secondary',
        Running: 'primary',
        Completed: 'success',
        Failed: 'danger'
    };

    return (
        <div className="card">
            <div
                className="d-flex justify-content-between align-items-center mb-3">
                <h3 className="mb-0">Design Jobs</h3>
                <button className="btn btn-sm btn-outline-primary"
                        onClick={refreshJobs}>
                    Refresh
                </button>
            </div>

            {jobs.length === 0 ? (
                <p className="text-muted">No jobs yet</p>
            ) : (
                <div className="jobs-list">
                    {jobs.map(job => (
                        <div key={job.job_id} className="job-item mb-2">
                            <div
                                className="d-flex justify-content-between align-items-center p-2 bg-light rounded"
                                style={{cursor: 'pointer'}}
                                onClick={() => setExpandedJob(expandedJob === job.job_id ? null : job.job_id)}
                            >
                                <div
                                    className="d-flex align-items-center gap-2">
                                    {expandedJob === job.job_id ?
                                        <ChevronDown size={16}/> :
                                        <ChevronRight size={16}/>}
                                    <strong>{job.name}</strong>
                                    <span
                                        className={`badge bg-${statusColors[job.status]}`}>{job.status}</span>
                                </div>
                                <div
                                    className="d-flex align-items-center gap-2">
                                    <button
                                        className="btn btn-sm btn-outline-primary"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            onCloneJob(job);
                                        }}
                                    >
                                        Load Params
                                    </button>
                                </div>
                                <small
                                    className="text-muted">{new Date(job.created_at).toLocaleString()}</small>
                            </div>

                            {expandedJob === job.job_id && (

                                <div className="p-3 border rounded mt-2">
                                    {job.status === 'Failed' && job.error && (
                                        <div
                                            className="alert alert-danger">{job.error}</div>
                                    )}

                                    {job.status === 'Completed' && (
                                        <>
                                            <h6>Result Domains</h6>
                                            {job.result_domains && job.result_domains.length > 0 ? (
                                                <div className="mb-3">
                                                    {job.result_domains.map((d, i) => (
                                                        <div key={i}
                                                             className="small">
                                                            <strong>{d.name}:</strong>
                                                            <code>{d.sequence}</code>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-muted small">No
                                                    domains</p>
                                            )}

                                            <h6>Result Strands</h6>
                                            {job.result_strands && job.result_strands.length > 0 ? (
                                                <div className="mb-3">
                                                    {job.result_strands.map((s, i) => (
                                                        <div key={i}
                                                             className="small">
                                                            <strong>{s.name}:</strong>
                                                            <code>{s.sequence}</code>
                                                        </div>
                                                    ))}
                                                </div>
                                            ) : (
                                                <p className="text-muted small">No
                                                    strands</p>
                                            )}

                                            {job.raw_output && (
                                                <>
                                                    <h6>Raw Output</h6>
                                                    <pre
                                                        className="small bg-light p-2 rounded"
                                                        style={{
                                                            maxHeight: '200px',
                                                            overflow: 'auto'
                                                        }}>
                            {job.raw_output}
                          </pre>
                                                </>
                                            )}
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}