
This document provides reference docs for API objects.
It will probably be replaced by an OpenAPI spec later,
though we may still want to generate an equivalent file for human readability.

### Pipeline

A Pipeline describes a set of Jobs to run when the pipeline is triggered.

- `spec.jobs`: Required. List of PipelineJob.
- `spec.runRetentionPolicy`: TODO

#### PipelineJob

- `name`: Required. Human-readable job name. Must be unique within the Pipeline.
- `depends`: Optional. List of names of jobs in this pipeline.
  All listed jobs must complete successfully before this job will be started.
  Only job names defined by previous PipelineJob entries can be listed
  (ie. the list of PipelineJobs must be a topological sort of the job graph).
  This helps readability and prevents cyclic dependencies.
  If not given, defaults to `[]`.
- `template`: Required. A PipelineJobTemplate.

#### PipelineJobTemplate

A batch.v1/Job with the following differences:
- `metadata.name`: The name is auto-generated and cannot be given.
- `metadata.namespace`: The namespace is inherited from the Pipeline and cannot be given.
- `spec.backoffLimit`: The default is set to 1, so failed jobs are not retried.
- `spec.ttlSecondsAfterFinished`: Deleting a job early will cause it to be re-created
by the controller, so setting this field is not supported.
and in addition if the `JobPodFailurePolicy` feature is enabled:
- `spec.podFailurePolicy` will have the following policy appended automatically:
`{"onPodConditions": [{"type": "DisruptionTarget"}], "action": "Ignore"}`
This ensures that pod disruptions (evictions, node loss, etc) are not considered to
be a job failure and will be retried.
- `spec.template.spec.restartPolicy`: This is set to `Never` and cannot be changed,
as it is a requirement for `podFailurePolicy` to work.

In addition to the above, all containers will have certain environment variables inserted
in the form of `KAYCI_{key}={value}` corresponding to the run parameters.
This behaviour can be modified by annotating a pod with the `kayci.invalid/inject-parameter-containers`
annotation. This is a comma-seperated list of container names within the pod for which parameters
should be injected, and can be blank to disable injection entirely.

### Run

A Run is a KayCI-managed object that tracks a particular triggered instance of a pipeline.
It can be cancelled, which suspends all jobs but leaves them available for introspection,
or deleted, which also deletes all jobs.

- `spec.cancelled`: Boolean, initially false. When set to true, all jobs will be suspended and
  the run will enter a cancelled state.
- `spec.jobs`: Read only. A copy of the pipeline's `spec.jobs` field made when the Run was created.
  Any subsequent changes to the Pipeline are *not* reflected in this Run.
- `spec.parameters`: Read only. A set of string key-value pairs that describe information specific
  to this Run, for example what event triggered it, or a git commit id to build.

TODO status

### Trigger

A Trigger is a set of circumstances under which a Pipeline should be triggered (a Run should be created).

TODO
