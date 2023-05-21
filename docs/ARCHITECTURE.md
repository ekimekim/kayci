
The controller is conceptually split into several components.

### Trigger handler

* Watches `Triggers`
* Maintains other watchers or endpoints to external services that can activate triggers
* When a `Trigger` is activated, looks up the associated `Pipeline` and creates a `Run`

### Run manager

* Watches `Runs` and labelled `Jobs`.
* Updates `RunStatus` to indicate `Job` state, one of:
	* `Waiting` - Job dependencies have not yet completed
	* `Active` - Job is ready to run / is running
	* `Completed` - Job has completed
  A `Run` is complete when all `Jobs` in it are complete.
* Creates or deletes `Jobs` so that they exist if and only if they are in a `Run` and are `Active` or `Completed`

### Web interface

Maybe?
