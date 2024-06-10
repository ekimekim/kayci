

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
	job = jobs.get(job_name)
	# TODO check completed
	# TODO check failed
	if run.spec.cancelled or any(s != "Completed" for s in dep_statuses):
		status = "Waiting"
	else:
		status = "Active"
	if job is None:
		create_job(run, job_name)
	else:
		update_job_suspend(job, status == "Waiting")
	return status

def create_job(run, job_name):
	# TODO

def main():
	pass
