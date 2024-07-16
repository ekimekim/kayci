

def do_run_manager():
	pipelines = # TODO list pipelines
	runs = # TODO list runs
	jobs = {
		(job.metadata.namespace, job.metadata.name)
		for job in # TODO list jobs with label
	}
	deletable_runs = defaultdict(list) # {(pipeline namespace, pipeline name): [runs]}
	for run in runs:
		status = process_run(run, jobs)
		if status == "Active":
			continue
		for owner in run.metadata.ownerReferences:
			if owner.apiVersion != OUR_API_VERSION or owner.kind != "Pipeline":
				continue
			deletable_runs[run.metadata.namespace, owner.name].append(run)
	for pipeline in pipelines:
		retention_policy = pipeline.retentionPolicy
		if retention_policy is None:
			retention_policy = {"maxCount": 10}
		max_count = retention_policy.get("maxCount")
		max_age = retention_policy.get("maxAge")
		min_created = None if max_age is None else now() - max_age
		candidates = deletable_runs[pipeline.metadata.namespace, pipeline.metadata.name]
		candidates.sort(key=lambda run: run.metadata.creationTimestamp)
		to_delete = [
			run for i, run in enumerate(candidates)
			if (max_count is not None and i >= max_count)
			or (min_created is not None and run.metadata.creationTimestamp < min_created)
		]
		for run in to_delete:
			# TODO delete run


def process_run(run, jobs):
	"""
	- Processes each job in run, in dep order (so we update dependencies before
	  their dependents)
	- Determine overall status, in priority order:
		- All jobs completed -> Completed
		- Any jobs failed -> Failed
		- Is cancelled -> Cancelled
		- Otherwise -> Active
	- Updates RunStatus with status + all jobs status
	- Writes run status back
	Returns status.
	"""
	statuses = {}
	# Note spec.jobs is required to be in dep order.
	for job_spec in run.spec.jobs:
		dep_statuses = [
			statuses[dep] for dep in job_spec.deps or []
		]
		statuses[job_spec.name] = process_job(run, jobs, job_spec.name, dep_statuses)
	if all(s == "Completed" for s in statuses.values()):
		status = "Completed"
	elif any(s == "Failed" for s in statuses.values()):
		status = "Failed"
	elif run.spec.cancelled:
		status = "Cancelled"
	else:
		status = "Active"
	update_run_status(run, {
		"status": status,
		"jobStatus": [
			{"name": name, "status": status}
			for name, status in statuses.items()
		],
	})
	return status
	

def process_job(run, jobs, job_name, dep_statuses):
	"""
	- Determine job status, in priority order:
		- Job completed -> Completed
		- Job failed -> Failed
		- Any deps not Completed -> Waiting
		- Run is cancelled -> Waiting
		- Otherwise -> Active
	- Create job if it doesn't exist, otherwise write suspend state
		Suspend = (status == Waiting)
	Returns status.
	"""
	job = jobs.get((run.metdata.namespace, job_name))
	# TODO check completed
	# TODO check failed
	if run.spec.cancelled or any(s != "Completed" for s in dep_statuses):
		status = "Waiting"
	else:
		status = "Active"
	if job is None:
		create_job(run, job_name, status == "Waiting")
	else:
		update_job_suspend(job, status == "Waiting")
	return status

def create_job(run, job_name, suspend):
	# TODO

def main():
	pass
