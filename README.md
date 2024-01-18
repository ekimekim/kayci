
# WORK IN PROGRESS - NOT USABLE YET

KayCI is a Kubernetes-native CI system.
You define your pipelines as kubernetes objects, and KayCI acts as a controller to run them.

A **Pipeline** consists of a collection of kubernetes Jobs to run.
The jobs can be augmented with some extra metadata such as conditions or dependency info.

A **Trigger** details circumstances under which a **Pipeline** should be run.
An instance of a triggered pipeline, including any metadata given by the trigger, is known
as a **Run**.

All the above objects are namespaced and can only interact with other objects in their namespace.
ie:
* a Trigger in namespace A cannot trigger a Pipeline in namespace B
* a Pipeline can only create Jobs in the same namespace
However a single instance of the controller may manage pipelines across many or all namespaces.

Because the jobs specified in a pipeline can end up quite verbose and repetitive,
we highly recommend using some way to define them programmatically when creating your pipeline manifest,
for example using [jsonnet](https://jsonnet.org).

### Signifigant differences from typical CI systems

#### Pipeline is defined in cluster, not in code

While of course it is possible (and recommended) for you to store your pipeline manifests
in your codebase, KayCI will always follow the pipeline object that is defined in the kubernetes API,
not a local version from the codebase itself. This is important when running against untrusted codebases.
In typical CI systems that look for a file in the branch being run against, care must be taken
that an untrusted committer can't push a branch that tells CI to do nefarious things, or limits
the permissions that can be granted based on the source of the branch.

You should still consider what happens if your pipeline is run against a branch with arbitrary code
(for example, if you use a helper script to run things, that script may be controlled by an attacker),
but at the very least all user-controlled code will run inside a pod where (depending on the service
account you have given it) damage will hopefully be limited.

Of course, this setup may be harder to use as changes to the CI pipeline cannot be tested
without updating the CI pipeline. We suggest in these cases to manually apply a test pipeline
under a different name that is only triggered by your test branch.

#### Very limited feature set

KayCI is intended to be as thin a wrapper around kubernetes Jobs as is practical.
It's really more of an orchestrator for running Jobs, and those Jobs are then responsible
for other tasks that most CI systems would come with "out of the box". For example:
* Grabbing a local checkout of the branch being built. Your Job will need a script or similar to do this itself.
* Acquiring secrets. We suggest using kubernetes Secrets for this purpose and including them in your Jobs
  via a mount or environment variable.

### development notes

#### on failure handling

We want a job to be able to fail at the application level (eg. tests failed, program crashed) and
have this consider the job failed, without a retry (by default).

However we don't want disruptions like node losses or evictions to cause the whole job to fail.

In k8s 1.26+ there is a good solution for this: the JobPodFailurePolicy feature (beta).
If this feature is enabled, we can set rules on the job via spec.podFailurePolicy to
say that disruptions shouldn't be counted against retries, then default retries to 1:
	podFailurePolicy:
	- onPodConditions:
	  - type: DisruptionTarget
	  action: Ignore
Note this requires setting the pod restart policy to Never (all retries are at the job level).
For maximum flexibility, we should *append* this policy rule to any existing ones
(they are processed in order, allowing others to override this one) and document the approach.

If we do not have this feature, the only thing we can really do is explicitly restart the job
in the controller if the state is failed but the failed pod is due to a disruption.
This is a lot of work and we may instead simply say that pre-1.26 just needs to deal with occasional
false failures.

#### suspend?

We may want to create all jobs immediately on a pipeline, but suspended, and unsuspend when
ready to run. This is mostly a UX thing.

#### job cleanup

Jobs should register a Run as their owner. k8s will automatically delete them when the run is deleted.
We should allow the user to configure a run retention policy,
probably on the Pipeline.

#### runs in the presence of pipeline changes

A run should create a copy of the pipeline spec as it was on run creation,
isolating it from further changes.

A run should list a pipeline as an owner to prevent orphaned runs and provide a way
to stop all runs for a pipeline (by deleting it). A pipeline can be "deactivated" without
removing its run by removing all triggers that refer to it.

#### how to provide trigger metadata to jobs?

options:

Insert as prefixed environment variables, eg. `KAYCI_{key}={value}`.
This is simple and easy but may require translation work inside the container.
We would also need to put it in ALL containers which may not always be desired.
However as long as we have a suitable prefix it shouldn't ever conflict with anything else.
We could also provide an opt-out (or container whitelist) via pod annotation.

Insert as pod annotations, allowing the user to reference them via the pod downward API.
This is annoying to have to write out and doesn't provide much flexibility over having
them as env vars to begin with.

Provide as a ConfigMap, allowing users to set env vars, mount files, etc as required.
The thorny issue here is the configmap name. It needs to be unique per run, so
we would need to give users a placeholder name that we look for and replace in any place
that expects a configmap name. This smells like text substitution which I want to avoid.

Text substitution, more like traditional CI systems where any instance of some template
string is substituted in ANY field of the job spec. This is highly flexible but can cause
nasty bugs if people happen to write the template string inadvertently.

Overall I think the env var option is cleanest. Probably implemented as a configmap with envFrom
to keep the generated pod specs cleaner.

#### notifications

We need an ability to run some sort of action in response to changes in run state.
The main use case for this is notifications of pipeline completion or failure.

This *could* be done as part of the normal job sequence, except we would need some ability
to run a job even if its dependencies fail. This is some extra complexity but doable.
We would need to define that the run overall is failed if any job is failed.
We also need some way to communicate the state to the notifier. Maybe a generic way for
a job to be notified of its dependencies' state?
This can lead to weirdness though, eg. A -> B -> C. A fails, B runs anyway and succeeds,
C sees B succeeded but not that A failed, but the whole Run is still failed.

Also, what happens if a job is retried? Do we re-run dependents?
If dependents only run on success, this is easy as they run only once their dependents succeed,
then never again. But what if we fail then succeed? Or succeed then fail then succeed?
Do we re-run on every state change?

A conceptually simpler option might be to have a dedicated "notifier" job that runs explicitly
on Run state changes.

### triggers

Should trigger mechanisms be hard-coded, or be pluggable?
Probably hard-coded for now, we can add plugins later if desired.

Minimum viable trigger types:
- Webhook

...that's it really. You can manually trigger by calling the same webhook endpoint.
